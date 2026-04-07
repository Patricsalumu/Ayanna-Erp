#!/usr/bin/env python3
"""Génère un fichier de log détaillé des variations de stock après le dernier inventaire (restaurant/POS_4).

Le rapport est écrit dans `./logges/restaurantloggers.text` et contient, pour chaque produit
- le nom et l'id
- la quantité comptée dans le dernier inventaire (si disponible)
- sommes des mouvements APRES la date de l'inventaire: ENTREE, TRANSFERT_IN, TRANSFERT_OUT, AJUSTEMENT, SORTIE
- la variation calculée comme (ENTREE + TRANSFERT_IN + AJUSTEMENT) - (SORTIE + TRANSFERT_OUT)
"""
import os
import sys
# Ensure project root (parent of "scripts/") is on sys.path so the script can be
# executed directly (e.g. from the UI subprocess) and still import the
# `ayanna_erp` package. This avoids ModuleNotFoundError when PYTHONPATH isn't set.
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from datetime import datetime
from sqlalchemy import text

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.core.session_manager import SessionManager


def generate_log(out_path=None, d1=None, d2=None):
    db = DatabaseManager()
    # legacy folder used earlier
    out_dir = os.path.join(os.getcwd(), 'logges')
    os.makedirs(out_dir, exist_ok=True)
    # new required folder (user expects 'logs' at repo root)
    logs_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    if out_path is None:
        out_path = os.path.join(out_dir, 'restaurantloggers.text')
    # also prepare the user-expected path
    logs_out_path = os.path.join(logs_dir, 'restaurantLoggers.txt')

    enterprise_id = SessionManager.get_current_enterprise_id() or None
    wh_code = 'POS_4'  # restaurant
    wid = None
    inv_id = None
    inv_completed_dt = None
    inv_counts = {}

    try:
        # Interpret provided d1/d2 or default to today
        if d1 is None:
            d1 = datetime.now()
        else:
            # if d1 is a string, parse it; if date, convert to datetime at midnight
            if isinstance(d1, str):
                try:
                    d1 = datetime.fromisoformat(d1)
                except Exception:
                    # fallback: date-only format YYYY-MM-DD
                    d1 = datetime.fromisoformat(d1 + 'T00:00:00')
            else:
                # assume date-like
                try:
                    d1 = datetime(d1.year, d1.month, d1.day)
                except Exception:
                    d1 = datetime.now()

        if d2 is None:
            # end of day for d1
            d2 = datetime(d1.year, d1.month, d1.day, 23, 59, 59, 999999)
        else:
            if isinstance(d2, str):
                try:
                    d2 = datetime.fromisoformat(d2)
                except Exception:
                    d2 = datetime.fromisoformat(d2 + 'T23:59:59')
            else:
                try:
                    d2 = datetime(d2.year, d2.month, d2.day, 23, 59, 59, 999999)
                except Exception:
                    d2 = datetime(d1.year, d1.month, d1.day, 23, 59, 59, 999999)
        with db.get_session() as session:
            # warehouse id
            try:
                r_wh = session.execute(text("SELECT id FROM stock_warehouses WHERE code = :code AND entreprise_id = :eid LIMIT 1"), {'code': wh_code, 'eid': enterprise_id}).fetchone()
                wid = int(r_wh.id) if r_wh else None
            except Exception:
                wid = None

            # latest completed inventory for this warehouse (<= d1)
            if wid:
                try:
                    r_inv = session.execute(text("""
                        SELECT id, completed_date
                        FROM stock_inventaire
                        WHERE warehouse_id = :wid AND status = 'COMPLETED' AND completed_date <= :d1
                        ORDER BY completed_date DESC
                        LIMIT 1
                    """), {'wid': wid, 'd1': d1}).fetchone()
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
                    rows = session.execute(text("SELECT DISTINCT product_id FROM stock_mouvements WHERE movement_date > :inv_dt AND movement_date < :d1 AND (warehouse_id = :wid OR destination_warehouse_id = :wid)"), {'inv_dt': inv_completed_dt, 'd1': d1, 'wid': wid}).fetchall()
                    product_ids |= {int(r.product_id) for r in rows}
                except Exception:
                    pass

            # fallback: include some products if none found
            if not product_ids:
                try:
                    rows = session.execute(text("SELECT id FROM core_products LIMIT 100")) .fetchall()
                    product_ids = {int(r.id) for r in rows}
                except Exception:
                    product_ids = set()

            # write report to the legacy path
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

                    # Calculate initial quantity following the same logic as export_products_summary
                    initial_q = None
                    entree = transfert_in = transfert_out = ajustement = sortie = 0.0
                    if inv_id and wid:
                        # If this product was counted in the inventory, use base + variation
                        if counted is not None and inv_completed_dt:
                            # variation between inv_completed_dt and d1
                            q_var = text("""
                                SELECT COALESCE(SUM(CASE
                                    WHEN movement_type = 'ENTREE' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity
                                    WHEN movement_type = 'SORTIE' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN -quantity
                                    WHEN movement_type = 'AJUSTEMENT' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity
                                    WHEN movement_type = 'TRANSFERT' AND destination_warehouse_id = :wid THEN ABS(quantity)
                                    WHEN movement_type = 'TRANSFERT' AND warehouse_id = :wid THEN -ABS(quantity)
                                    ELSE 0 END),0) as var
                                FROM stock_mouvements
                                WHERE product_id = :pid AND movement_date > :inv_dt AND movement_date < :d1
                                AND (warehouse_id = :wid OR destination_warehouse_id = :wid)
                            """)
                            try:
                                r_var = session.execute(q_var, {'pid': pid, 'inv_dt': inv_completed_dt, 'd1': d1, 'wid': wid}).fetchone()
                                variation = float(r_var.var or 0)
                                initial_q = float(counted + variation)
                            except Exception:
                                initial_q = float(counted or 0)
                        else:
                            # Not counted in inventory: fallback to signed sum before d1
                            try:
                                q_init = text("""
                                    SELECT COALESCE(SUM(CASE
                                        WHEN movement_type = 'ENTREE' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity
                                        WHEN movement_type = 'SORTIE' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN -quantity
                                        WHEN movement_type = 'AJUSTEMENT' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity
                                        WHEN movement_type = 'TRANSFERT' AND destination_warehouse_id = :wid THEN ABS(quantity)
                                        WHEN movement_type = 'TRANSFERT' AND warehouse_id = :wid THEN -ABS(quantity)
                                        ELSE 0 END),0) as qty
                                    FROM stock_mouvements
                                    WHERE product_id = :pid AND movement_date < :d1
                                    AND (warehouse_id = :wid OR destination_warehouse_id = :wid)
                                """)
                                r_init = session.execute(q_init, {'pid': pid, 'd1': d1, 'wid': wid}).fetchone()
                                initial_q = float(r_init.qty or 0)
                            except Exception:
                                initial_q = 0.0
                        # Also compute breakdown of movements AFTER inventory up to d1
                        try:
                            q = text("""
                                SELECT
                                    COALESCE(SUM(CASE WHEN movement_type = 'ENTREE' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity ELSE 0 END),0) as entree,
                                    COALESCE(SUM(CASE WHEN movement_type = 'TRANSFERT' AND destination_warehouse_id = :wid THEN ABS(quantity) ELSE 0 END),0) as transfert_in,
                                    COALESCE(SUM(CASE WHEN movement_type = 'TRANSFERT' AND warehouse_id = :wid THEN ABS(quantity) ELSE 0 END),0) as transfert_out,
                                    COALESCE(SUM(CASE WHEN movement_type = 'AJUSTEMENT' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity ELSE 0 END),0) as ajustement,
                                    COALESCE(SUM(CASE WHEN movement_type = 'SORTIE' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity ELSE 0 END),0) as sortie
                                FROM stock_mouvements
                                WHERE product_id = :pid AND movement_date > :inv_dt AND movement_date < :d1
                                  AND (warehouse_id = :wid OR destination_warehouse_id = :wid)
                            """)
                            rsum = session.execute(q, {'pid': pid, 'inv_dt': inv_completed_dt, 'd1': d1, 'wid': wid}).fetchone()
                            entree = float(rsum.entree or 0)
                            transfert_in = float(rsum.transfert_in or 0)
                            transfert_out = float(rsum.transfert_out or 0)
                            ajustement = float(rsum.ajustement or 0)
                            sortie = float(rsum.sortie or 0)
                        except Exception:
                            entree = transfert_in = transfert_out = ajustement = sortie = 0.0

                        # additionally, compute movements in the reporting period [d1, d2]
                        period_entree = period_transfert_in = period_transfert_out = period_ajustement = period_sortie = 0.0
                        try:
                            q_period = text("""
                                SELECT
                                    COALESCE(SUM(CASE WHEN movement_type = 'ENTREE' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity ELSE 0 END),0) as entree,
                                    COALESCE(SUM(CASE WHEN movement_type = 'TRANSFERT' AND destination_warehouse_id = :wid THEN ABS(quantity) ELSE 0 END),0) as transfert_in,
                                    COALESCE(SUM(CASE WHEN movement_type = 'TRANSFERT' AND warehouse_id = :wid THEN ABS(quantity) ELSE 0 END),0) as transfert_out,
                                    COALESCE(SUM(CASE WHEN movement_type = 'AJUSTEMENT' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity ELSE 0 END),0) as ajustement,
                                    COALESCE(SUM(CASE WHEN movement_type = 'SORTIE' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity ELSE 0 END),0) as sortie
                                FROM stock_mouvements
                                WHERE product_id = :pid AND movement_date >= :d1 AND movement_date <= :d2
                                  AND (warehouse_id = :wid OR destination_warehouse_id = :wid)
                            """)
                            rper = session.execute(q_period, {'pid': pid, 'd1': d1, 'd2': d2, 'wid': wid}).fetchone()
                            period_entree = float(rper.entree or 0)
                            period_transfert_in = float(rper.transfert_in or 0)
                            period_transfert_out = float(rper.transfert_out or 0)
                            period_ajustement = float(rper.ajustement or 0)
                            period_sortie = float(rper.sortie or 0)
                        except Exception:
                            period_entree = period_transfert_in = period_transfert_out = period_ajustement = period_sortie = 0.0
                    else:
                        # No inventory found: fallback to signed sum before d1 (with or without wid)
                        try:
                            if wid:
                                q_init = text("""
                                    SELECT COALESCE(SUM(CASE
                                        WHEN movement_type = 'ENTREE' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity
                                        WHEN movement_type = 'SORTIE' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN -quantity
                                        WHEN movement_type = 'AJUSTEMENT' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity
                                        WHEN movement_type = 'TRANSFERT' AND destination_warehouse_id = :wid THEN ABS(quantity)
                                        WHEN movement_type = 'TRANSFERT' AND warehouse_id = :wid THEN -ABS(quantity)
                                        ELSE 0 END),0) as qty
                                    FROM stock_mouvements
                                    WHERE product_id = :pid AND movement_date < :d1
                                    AND (warehouse_id = :wid OR destination_warehouse_id = :wid)
                                """)
                                r_init = session.execute(q_init, {'pid': pid, 'd1': d1, 'wid': wid}).fetchone()
                            else:
                                q_init = text("""
                                    SELECT COALESCE(SUM(CASE
                                        WHEN movement_type = 'ENTREE' THEN quantity
                                        WHEN movement_type = 'SORTIE' THEN -quantity
                                        WHEN movement_type = 'AJUSTEMENT' THEN quantity
                                        WHEN movement_type = 'TRANSFERT' THEN ABS(quantity)
                                        ELSE 0 END),0) as qty
                                    FROM stock_mouvements
                                    WHERE product_id = :pid AND movement_date < :d1
                                """)
                                r_init = session.execute(q_init, {'pid': pid, 'd1': d1}).fetchone()
                            initial_q = float(r_init.qty or 0)
                        except Exception:
                            initial_q = 0.0

                    variation = (entree + transfert_in + ajustement) - (sortie + transfert_out)
                    period_variation = (period_entree + period_transfert_in + period_ajustement) - (period_sortie + period_transfert_out)

                    f.write(f"Produit: {pname} (id={pid})\n")
                    f.write(f"  Quantité inventaire (comptée): {counted if counted is not None else 'N/A'}\n")
                    f.write(f"  Quantité initiale calculée (base+variation ou fallback): {initial_q:.3f}\n")
                    f.write(f"  ENTREE après inventaire: {entree:.3f}\n")
                    f.write(f"  TRANSFERT_IN après inventaire: {transfert_in:.3f}\n")
                    f.write(f"  TRANSFERT_OUT après inventaire: {transfert_out:.3f}\n")
                    f.write(f"  AJUSTEMENT après inventaire: {ajustement:.3f}\n")
                    f.write(f"  SORTIE après inventaire: {sortie:.3f}\n")
                    f.write(f"  VARIATION: {variation:.3f}\n")
                    f.write(f"  --- Mouvements dans la période d'export ({d1.isoformat()} -> {d2.isoformat()}):\n")
                    f.write(f"     ENTREE: {period_entree:.3f}, TRANSFERT_IN: {period_transfert_in:.3f}, TRANSFERT_OUT: {period_transfert_out:.3f}, AJUSTEMENT: {period_ajustement:.3f}, SORTIE: {period_sortie:.3f}\n")
                    f.write(f"     VARIATION période: {period_variation:.3f}\n")
                    f.write("-----------------------------------------------------\n")

            # duplicate the same content into the user-expected logs folder
            try:
                with open(logs_out_path, 'w', encoding='utf-8') as f2:
                    f2.write(f"Rapport généré: {datetime.now().isoformat()}\n")
                    f2.write(f"Entreprise id: {enterprise_id}\n")
                    f2.write(f"Entrepôt code: {wh_code} id: {wid}\n")
                    if inv_id:
                        f2.write(f"Dernier inventaire id: {inv_id}, completed_date: {inv_completed_dt}\n")
                    else:
                        f2.write("Aucun inventaire complété trouvé pour cet entrepôt.\n")
                    f2.write("\nDétails par produit (mouvements APRES la date d'inventaire)\n")
                    f2.write("-----------------------------------------------------\n")

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

                        # compute period movements between d1 and d2 for this product as well
                        period_entree = period_transfert_in = period_transfert_out = period_ajustement = period_sortie = 0.0
                        try:
                            q_period = text("""
                                SELECT
                                    COALESCE(SUM(CASE WHEN movement_type = 'ENTREE' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity ELSE 0 END),0) as entree,
                                    COALESCE(SUM(CASE WHEN movement_type = 'TRANSFERT' AND destination_warehouse_id = :wid THEN ABS(quantity) ELSE 0 END),0) as transfert_in,
                                    COALESCE(SUM(CASE WHEN movement_type = 'TRANSFERT' AND warehouse_id = :wid THEN ABS(quantity) ELSE 0 END),0) as transfert_out,
                                    COALESCE(SUM(CASE WHEN movement_type = 'AJUSTEMENT' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity ELSE 0 END),0) as ajustement,
                                    COALESCE(SUM(CASE WHEN movement_type = 'SORTIE' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity ELSE 0 END),0) as sortie
                                FROM stock_mouvements
                                WHERE product_id = :pid AND movement_date >= :d1 AND movement_date <= :d2
                                  AND (warehouse_id = :wid OR destination_warehouse_id = :wid)
                            """)
                            rper = session.execute(q_period, {'pid': pid, 'd1': d1, 'd2': d2, 'wid': wid}).fetchone()
                            period_entree = float(rper.entree or 0)
                            period_transfert_in = float(rper.transfert_in or 0)
                            period_transfert_out = float(rper.transfert_out or 0)
                            period_ajustement = float(rper.ajustement or 0)
                            period_sortie = float(rper.sortie or 0)
                        except Exception:
                            period_entree = period_transfert_in = period_transfert_out = period_ajustement = period_sortie = 0.0

                        f2.write(f"Produit: {pname} (id={pid})\n")
                        f2.write(f"  Quantité inventaire: {counted if counted is not None else 'N/A'}\n")
                        f2.write(f"  ENTREE après inventaire: {entree:.3f}\n")
                        f2.write(f"  TRANSFERT_IN après inventaire: {transfert_in:.3f}\n")
                        f2.write(f"  TRANSFERT_OUT après inventaire: {transfert_out:.3f}\n")
                        f2.write(f"  AJUSTEMENT après inventaire: {ajustement:.3f}\n")
                        f2.write(f"  SORTIE après inventaire: {sortie:.3f}\n")
                        f2.write(f"  VARIATION: {variation:.3f}\n")
                        f2.write(f"  --- Mouvements dans la période d'export ({d1.isoformat()} -> {d2.isoformat()}):\n")
                        f2.write(f"     ENTREE: {period_entree:.3f}, TRANSFERT_IN: {period_transfert_in:.3f}, TRANSFERT_OUT: {period_transfert_out:.3f}, AJUSTEMENT: {period_ajustement:.3f}, SORTIE: {period_sortie:.3f}\n")
                        f2.write(f"     VARIATION période: {((period_entree + period_transfert_in + period_ajustement) - (period_sortie + period_transfert_out)):.3f}\n")
                        f2.write("-----------------------------------------------------\n")
            except Exception as e:
                # if duplication fails, continue silently; primary file still written
                print(f"Warning: impossible d'écrire dans {logs_out_path}: {e}")

    except Exception as e:
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(f"Erreur lors de la génération du rapport: {e}\n")

    print(f"Wrote report to: {out_path}")
    print(f"Also attempted to write user-expected file: {logs_out_path}")


if __name__ == '__main__':
    # Accept optional --from and --to arguments (ISO date or YYYY-MM-DD)
    try:
        import argparse
        parser = argparse.ArgumentParser(description='Générer le log restaurant (restaurantLoggers.txt)')
        parser.add_argument('--from', dest='d1', help='Date de début (YYYY-MM-DD or ISO)')
        parser.add_argument('--to', dest='d2', help='Date de fin (YYYY-MM-DD or ISO)')
        parser.add_argument('--out', dest='out', help='Chemin de sortie optionnel')
        args = parser.parse_args()
        generate_log(out_path=args.out, d1=args.d1, d2=args.d2)
    except Exception:
        # fallback simple call
        generate_log()
