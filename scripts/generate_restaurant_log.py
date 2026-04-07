#!/usr/bin/env python3
"""Génère un fichier de log détaillé des variations de stock après le dernier inventaire (restaurant/POS_4).

Le rapport est écrit dans `./logges/restaurantloggers.text` et contient, pour chaque produit
- le nom et l'id
- la quantité comptée dans le dernier inventaire (si disponible)
- sommes des mouvements APRES la date de l'inventaire: ENTREE, TRANSFERT_IN, TRANSFERT_OUT, AJUSTEMENT, SORTIE
- la variation calculée comme (ENTREE + TRANSFERT_IN + AJUSTEMENT) - (SORTIE + TRANSFERT_OUT)
"""
import os
from datetime import datetime
from sqlalchemy import text

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.core.session_manager import SessionManager


def generate_log():
    db = DatabaseManager()
    out_dir = os.path.join(os.getcwd(), 'logges')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'restaurantloggers.text')

    enterprise_id = SessionManager.get_current_enterprise_id() or None
    wh_code = 'POS_4'  # restaurant
    wid = None
    inv_id = None
    inv_completed_dt = None
    inv_counts = {}

    try:
        with db.get_session() as session:
            # warehouse id
            try:
                r_wh = session.execute(text("SELECT id FROM stock_warehouses WHERE code = :code AND entreprise_id = :eid LIMIT 1"), {'code': wh_code, 'eid': enterprise_id}).fetchone()
                wid = int(r_wh.id) if r_wh else None
            except Exception:
                wid = None

            # latest completed inventory for this warehouse
            if wid:
                try:
                    r_inv = session.execute(text("""
                        SELECT id, completed_date
                        FROM stock_inventaire
                        WHERE warehouse_id = :wid AND status = 'COMPLETED'
                        ORDER BY completed_date DESC
                        LIMIT 1
                    """), {'wid': wid}).fetchone()
                    if r_inv:
                        inv_id = int(r_inv.id)
                        inv_completed_dt = r_inv.completed_date
                except Exception:
                    inv_id = None
                    inv_completed_dt = None

            # inventory item counts
            if inv_id:
                try:
                    rows = session.execute(text("SELECT product_id, counted_stock FROM stock_inventaire_item WHERE inventory_id = :inv_id"), {'inv_id': inv_id}).fetchall()
                    inv_counts = {int(r.product_id): float(r.counted_stock or 0) for r in rows}
                except Exception:
                    inv_counts = {}

            # products to inspect: union of inventory products and products with movements after inventory
            product_ids = set(inv_counts.keys())
            if inv_completed_dt and wid:
                try:
                    rows = session.execute(text("SELECT DISTINCT product_id FROM stock_mouvements WHERE movement_date > :inv_dt AND (warehouse_id = :wid OR destination_warehouse_id = :wid)"), {'inv_dt': inv_completed_dt, 'wid': wid}).fetchall()
                    product_ids |= {int(r.product_id) for r in rows}
                except Exception:
                    pass

            # fallback: include some products if none found
            if not product_ids:
                try:
                    rows = session.execute(text("SELECT id FROM core_products LIMIT 100")).fetchall()
                    product_ids = {int(r.id) for r in rows}
                except Exception:
                    product_ids = set()

            # write report
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(f"Rapport généré: {datetime.now().isoformat()}\n")
                f.write(f"Entreprise id: {enterprise_id}\n")
                f.write(f"Entrepôt code: {wh_code} id: {wid}\n")
                if inv_id:
                    f.write(f"Dernier inventaire id: {inv_id}, completed_date: {inv_completed_dt}\n")
                else:
                    f.write("Aucun inventaire complété trouvé pour cet entrepôt.\n")
                f.write("\nDétails par produit (mouvements APRES la date d'inventaire)\n")
                f.write("-----------------------------------------------------\n")

                for pid in sorted(product_ids):
                    try:
                        r = session.execute(text("SELECT name FROM core_products WHERE id = :pid LIMIT 1"), {'pid': pid}).fetchone()
                        pname = r.name if r else f'Product-{pid}'
                    except Exception:
                        pname = f'Product-{pid}'

                    counted = inv_counts.get(pid, None)

                    entree = transfert_in = transfert_out = ajustement = sortie = 0.0
                    if inv_completed_dt and wid:
                        q = text("""
                            SELECT
                                COALESCE(SUM(CASE WHEN movement_type = 'ENTREE' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity ELSE 0 END),0) as entree,
                                COALESCE(SUM(CASE WHEN movement_type = 'TRANSFERT' AND destination_warehouse_id = :wid THEN ABS(quantity) ELSE 0 END),0) as transfert_in,
                                COALESCE(SUM(CASE WHEN movement_type = 'TRANSFERT' AND warehouse_id = :wid THEN ABS(quantity) ELSE 0 END),0) as transfert_out,
                                COALESCE(SUM(CASE WHEN movement_type = 'AJUSTEMENT' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity ELSE 0 END),0) as ajustement,
                                COALESCE(SUM(CASE WHEN movement_type = 'SORTIE' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity ELSE 0 END),0) as sortie
                            FROM stock_mouvements
                            WHERE product_id = :pid AND movement_date > :inv_dt
                              AND (warehouse_id = :wid OR destination_warehouse_id = :wid)
                        """)
                        try:
                            rsum = session.execute(q, {'pid': pid, 'inv_dt': inv_completed_dt, 'wid': wid}).fetchone()
                            entree = float(rsum.entree or 0)
                            transfert_in = float(rsum.transfert_in or 0)
                            transfert_out = float(rsum.transfert_out or 0)
                            ajustement = float(rsum.ajustement or 0)
                            sortie = float(rsum.sortie or 0)
                        except Exception:
                            entree = transfert_in = transfert_out = ajustement = sortie = 0.0

                    variation = (entree + transfert_in + ajustement) - (sortie + transfert_out)

                    f.write(f"Produit: {pname} (id={pid})\n")
                    f.write(f"  Quantité inventaire: {counted if counted is not None else 'N/A'}\n")
                    f.write(f"  ENTREE après inventaire: {entree:.3f}\n")
                    f.write(f"  TRANSFERT_IN après inventaire: {transfert_in:.3f}\n")
                    f.write(f"  TRANSFERT_OUT après inventaire: {transfert_out:.3f}\n")
                    f.write(f"  AJUSTEMENT après inventaire: {ajustement:.3f}\n")
                    f.write(f"  SORTIE après inventaire: {sortie:.3f}\n")
                    f.write(f"  VARIATION: {variation:.3f}\n")
                    f.write("-----------------------------------------------------\n")

    except Exception as e:
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(f"Erreur lors de la génération du rapport: {e}\n")

    print(f"Wrote report to: {out_path}")


if __name__ == '__main__':
    generate_log()
                                            product_ids = {int(r.id) for r in rows}
                                        except Exception:
                                            product_ids = set()

                                    # write report
                                    with open(out_path, 'w', encoding='utf-8') as f:
                                        f.write(f"Rapport généré: {datetime.now().isoformat()}\n")
                                        f.write(f"Entreprise id: {enterprise_id}\n")
                                        f.write(f"Entrepôt code: {wh_code} id: {wid}\n")
                                        if inv_id:
                                            f.write(f"Dernier inventaire id: {inv_id}, completed_date: {inv_completed_dt}\n")
                                        #!/usr/bin/env python3
                                        """Génère un fichier de log détaillé des variations de stock après le dernier inventaire (restaurant/POS_4).

                                        Le rapport est écrit dans `./logges/restaurantloggers.text` et contient, pour chaque produit
                                        - le nom et l'id
                                        - la quantité comptée dans le dernier inventaire (si disponible)
                                        - sommes des mouvements APRES la date de l'inventaire: ENTREE, TRANSFERT_IN, TRANSFERT_OUT, AJUSTEMENT, SORTIE
                                        - la variation calculée comme (ENTREE + TRANSFERT_IN + AJUSTEMENT) - (SORTIE + TRANSFERT_OUT)
                                        """
                                        import os
                                        from datetime import datetime
                                        from sqlalchemy import text

                                        from ayanna_erp.database.database_manager import DatabaseManager
                                        from ayanna_erp.core.session_manager import SessionManager


                                        def generate_log():
                                            db = DatabaseManager()
                                            out_dir = os.path.join(os.getcwd(), 'logges')
                                            os.makedirs(out_dir, exist_ok=True)
                                            out_path = os.path.join(out_dir, 'restaurantloggers.text')

                                            enterprise_id = SessionManager.get_current_enterprise_id() or None
                                            wh_code = 'POS_4'  # restaurant
                                            wid = None
                                            inv_id = None
                                            inv_completed_dt = None
                                            inv_counts = {}

                                            try:
                                                with db.get_session() as session:
                                                    # warehouse id
                                                    try:
                                                        r_wh = session.execute(text("SELECT id FROM stock_warehouses WHERE code = :code AND entreprise_id = :eid LIMIT 1"), {'code': wh_code, 'eid': enterprise_id}).fetchone()
                                                        wid = int(r_wh.id) if r_wh else None
                                                    except Exception:
                                                        wid = None

                                                    # latest completed inventory for this warehouse
                                                    if wid:
                                                        try:
                                                            r_inv = session.execute(text("""
                                                                SELECT id, completed_date
                                                                FROM stock_inventaire
                                                                WHERE warehouse_id = :wid AND status = 'COMPLETED'
                                                                ORDER BY completed_date DESC
                                                                LIMIT 1
                                                            """), {'wid': wid}).fetchone()
                                                            if r_inv:
                                                                inv_id = int(r_inv.id)
                                                                inv_completed_dt = r_inv.completed_date
                                                        except Exception:
                                                            inv_id = None
                                                            inv_completed_dt = None

                                                    # inventory item counts
                                                    if inv_id:
                                                        try:
                                                            rows = session.execute(text("SELECT product_id, counted_stock FROM stock_inventaire_item WHERE inventory_id = :inv_id"), {'inv_id': inv_id}).fetchall()
                                                            inv_counts = {int(r.product_id): float(r.counted_stock or 0) for r in rows}
                                                        except Exception:
                                                            inv_counts = {}

                                                    # products to inspect: union of inventory products and products with movements after inventory
                                                    product_ids = set(inv_counts.keys())
                                                    if inv_completed_dt and wid:
                                                        try:
                                                            rows = session.execute(text("SELECT DISTINCT product_id FROM stock_mouvements WHERE movement_date > :inv_dt AND (warehouse_id = :wid OR destination_warehouse_id = :wid)"), {'inv_dt': inv_completed_dt, 'wid': wid}).fetchall()
                                                            product_ids |= {int(r.product_id) for r in rows}
                                                        except Exception:
                                                            pass

                                                    # fallback: include some products if none found
                                                    if not product_ids:
                                                        try:
                                                            rows = session.execute(text("SELECT id FROM core_products LIMIT 100")).fetchall()
                                                            product_ids = {int(r.id) for r in rows}
                                                        except Exception:
                                                            product_ids = set()

                                                    # write report
                                                    with open(out_path, 'w', encoding='utf-8') as f:
                                                        f.write(f"Rapport généré: {datetime.now().isoformat()}\n")
                                                        f.write(f"Entreprise id: {enterprise_id}\n")
                                                        f.write(f"Entrepôt code: {wh_code} id: {wid}\n")
                                                        if inv_id:
                                                            f.write(f"Dernier inventaire id: {inv_id}, completed_date: {inv_completed_dt}\n")
                                                        #!/usr/bin/env python3
                                                        """Génère un fichier de log détaillé des variations de stock après le dernier inventaire (restaurant/POS_4).

                                                        Le rapport est écrit dans `./logges/restaurantloggers.text` et contient, pour chaque produit
                                                        - le nom et l'id
                                                        - la quantité comptée dans le dernier inventaire (si disponible)
                                                        - sommes des mouvements APRES la date de l'inventaire: ENTREE, TRANSFERT_IN, TRANSFERT_OUT, AJUSTEMENT, SORTIE
                                                        - la variation calculée comme (ENTREE + TRANSFERT_IN + AJUSTEMENT) - (SORTIE + TRANSFERT_OUT)
                                                        """
                                                        import os
                                                        from datetime import datetime
                                                        from sqlalchemy import text

                                                        from ayanna_erp.database.database_manager import DatabaseManager
                                                        from ayanna_erp.core.session_manager import SessionManager


                                                        def generate_log():
                                                            db = DatabaseManager()
                                                            out_dir = os.path.join(os.getcwd(), 'logges')
                                                            os.makedirs(out_dir, exist_ok=True)
                                                            out_path = os.path.join(out_dir, 'restaurantloggers.text')

                                                            enterprise_id = SessionManager.get_current_enterprise_id() or None
                                                            wh_code = 'POS_4'  # restaurant
                                                            wid = None
                                                            inv_id = None
                                                            inv_completed_dt = None
                                                            inv_counts = {}

                                                            try:
                                                                with db.get_session() as session:
                                                                    # warehouse id
                                                                    try:
                                                                        r_wh = session.execute(text("SELECT id FROM stock_warehouses WHERE code = :code AND entreprise_id = :eid LIMIT 1"), {'code': wh_code, 'eid': enterprise_id}).fetchone()
                                                                        wid = int(r_wh.id) if r_wh else None
                                                                    except Exception:
                                                                        wid = None

                                                                    # latest completed inventory for this warehouse
                                                                    if wid:
                                                                        try:
                                                                            r_inv = session.execute(text("""
                                                                                SELECT id, completed_date
                                                                                FROM stock_inventaire
                                                                                WHERE warehouse_id = :wid AND status = 'COMPLETED'
                                                                                ORDER BY completed_date DESC
                                                                                LIMIT 1
                                                                            """), {'wid': wid}).fetchone()
                                                                            if r_inv:
                                                                                inv_id = int(r_inv.id)
                                                                                inv_completed_dt = r_inv.completed_date
                                                                        except Exception:
                                                                            inv_id = None
                                                                            inv_completed_dt = None

                                                                    # inventory item counts
                                                                    if inv_id:
                                                                        try:
                                                                            rows = session.execute(text("SELECT product_id, counted_stock FROM stock_inventaire_item WHERE inventory_id = :inv_id"), {'inv_id': inv_id}).fetchall()
                                                                            inv_counts = {int(r.product_id): float(r.counted_stock or 0) for r in rows}
                                                                        except Exception:
                                                                            inv_counts = {}

                                                                    # products to inspect: union of inventory products and products with movements after inventory
                                                                    product_ids = set(inv_counts.keys())
                                                                    if inv_completed_dt and wid:
                                                                        try:
                                                                            rows = session.execute(text("SELECT DISTINCT product_id FROM stock_mouvements WHERE movement_date > :inv_dt AND (warehouse_id = :wid OR destination_warehouse_id = :wid)"), {'inv_dt': inv_completed_dt, 'wid': wid}).fetchall()
                                                                            product_ids |= {int(r.product_id) for r in rows}
                                                                        except Exception:
                                                                            pass

                                                                    # fallback: include some products if none found
                                                                    if not product_ids:
                                                                        try:
                                                                            rows = session.execute(text("SELECT id FROM core_products LIMIT 100")).fetchall()
                                                                            product_ids = {int(r.id) for r in rows}
                                                                        except Exception:
                                                                            product_ids = set()

                                                                    # write report
                                                                    with open(out_path, 'w', encoding='utf-8') as f:
                                                                        f.write(f"Rapport généré: {datetime.now().isoformat()}\n")
                                                                        f.write(f"Entreprise id: {enterprise_id}\n")
                                                                        f.write(f"Entrepôt code: {wh_code} id: {wid}\n")
                                                                        if inv_id:
                                                                            f.write(f"Dernier inventaire id: {inv_id}, completed_date: {inv_completed_dt}\n")
                                                                        else:
                                                                            f.write("Aucun inventaire complété trouvé pour cet entrepôt.\n")
                                                                        f.write("\nDétails par produit (mouvements APRES la date d'inventaire)\n")
                                                                        f.write("-----------------------------------------------------\n")

                                                                        for pid in sorted(product_ids):
                                                                            try:
                                                                                r = session.execute(text("SELECT name FROM core_products WHERE id = :pid LIMIT 1"), {'pid': pid}).fetchone()
                                                                                pname = r.name if r else f'Product-{pid}'
                                                                            except Exception:
                                                                                pname = f'Product-{pid}'

                                                                            counted = inv_counts.get(pid, None)

                                                                            entree = transfert_in = transfert_out = ajustement = sortie = 0.0
                                                                            if inv_completed_dt and wid:
                                                                                q = text("""
                                                                                    SELECT
                                                                                        COALESCE(SUM(CASE WHEN movement_type = 'ENTREE' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity ELSE 0 END),0) as entree,
                                                                                        COALESCE(SUM(CASE WHEN movement_type = 'TRANSFERT' AND destination_warehouse_id = :wid THEN ABS(quantity) ELSE 0 END),0) as transfert_in,
                                                                                        COALESCE(SUM(CASE WHEN movement_type = 'TRANSFERT' AND warehouse_id = :wid THEN ABS(quantity) ELSE 0 END),0) as transfert_out,
                                                                                        COALESCE(SUM(CASE WHEN movement_type = 'AJUSTEMENT' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity ELSE 0 END),0) as ajustement,
                                                                                        COALESCE(SUM(CASE WHEN movement_type = 'SORTIE' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity ELSE 0 END),0) as sortie
                                                                                    FROM stock_mouvements
                                                                                    WHERE product_id = :pid AND movement_date > :inv_dt
                                                                                      AND (warehouse_id = :wid OR destination_warehouse_id = :wid)
                                                                                """)
                                                                                try:
                                                                                    rsum = session.execute(q, {'pid': pid, 'inv_dt': inv_completed_dt, 'wid': wid}).fetchone()
                                                                                    entree = float(rsum.entree or 0)
                                                                                    transfert_in = float(rsum.transfert_in or 0)
                                                                                    transfert_out = float(rsum.transfert_out or 0)
                                                                                    ajustement = float(rsum.ajustement or 0)
                                                                                    sortie = float(rsum.sortie or 0)
                                                                                except Exception:
                                                                                    entree = transfert_in = transfert_out = ajustement = sortie = 0.0

                                                                            variation = (entree + transfert_in + ajustement) - (sortie + transfert_out)

                                                                            f.write(f"Produit: {pname} (id={pid})\n")
                                                                            f.write(f"  Quantité inventaire: {counted if counted is not None else 'N/A'}\n")
                                                                            f.write(f"  ENTREE après inventaire: {entree:.3f}\n")
                                                                            f.write(f"  TRANSFERT_IN après inventaire: {transfert_in:.3f}\n")
                                                                            f.write(f"  TRANSFERT_OUT après inventaire: {transfert_out:.3f}\n")
                                                                            f.write(f"  AJUSTEMENT après inventaire: {ajustement:.3f}\n")
                                                                            f.write(f"  SORTIE après inventaire: {sortie:.3f}\n")
                                                                            f.write(f"  VARIATION: {variation:.3f}\n")
                                                                            f.write("-----------------------------------------------------\n")

                                                            except Exception as e:
                                                                with open(out_path, 'w', encoding='utf-8') as f:
                                                                    f.write(f"Erreur lors de la génération du rapport: {e}\n")

                                                            print(f"Wrote report to: {out_path}")


                                                        if __name__ == '__main__':
                                                            generate_log()
