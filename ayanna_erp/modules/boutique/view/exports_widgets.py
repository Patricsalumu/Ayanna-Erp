from ayanna_erp.core.session_manager import SessionManager
from ayanna_erp.utils.formatting import get_currency
from sqlalchemy import text, inspect


def export_products_summary(self, date_debut, date_fin, include_services: bool = True, module: str = 'boutique') -> str:
        """
        Génère un fichier CSV listant chaque produit/service vendu sur la période avec colonnes:
        No, name, quantite_initiale, quantite_ajoutee, quantite_achats_transferts, total_initial_plus_ajoute,
        reste, vendu, prix_unitaire, total

        Hypothèses raisonnables:
        - Les ventes produits sont issues de `shop_paniers_products` (boutique) et `restau_produit_panier` (restaurant).
        - Les services viennent de `shop_paniers_services`.
        - Les mouvements de stock sont pris depuis `stock_mouvements` pour calculer quantités initiales et ajouts.
        - Si la table des mouvements ou des stocks est absente, les valeurs liées au stock seront à 0.

        Retourne le chemin du fichier CSV généré.
        """
        import os
        from datetime import datetime

        # Normaliser bornes
        from datetime import datetime as _dt
        if isinstance(date_debut, _dt):
            d1 = date_debut
        else:
            d1 = datetime.combine(date_debut, datetime.min.time())
        if isinstance(date_fin, _dt):
            d2 = date_fin
        else:
            d2 = datetime.combine(date_fin, datetime.max.time())

        try:
            with self.db_manager.get_session() as session:
                # Déterminer l'entrepôt global pour cet export (module -> POS code)
                enterprise_id = SessionManager.get_current_enterprise_id() or None
                # module param can be 'boutique' or 'restaurant' (restau)
                if isinstance(module, str) and module.lower() in ('restaurant', 'restau'):
                    wh_code = 'POS_4'
                else:
                    wh_code = 'POS_2'  # default for boutique exports
                wid = None
                try:
                    r_wh = session.execute(text("SELECT id FROM stock_warehouses WHERE code = :code AND entreprise_id = :eid LIMIT 1"), {'code': wh_code, 'eid': enterprise_id}).fetchone()
                    wid = int(r_wh.id) if r_wh else None
                except Exception:
                    wid = None

                # (La recherche d'inventaire se fera par produit dans la boucle ci-dessous)
                # Rassembler ventes produits (boutique)
                q_products = text("""
                    SELECT cp.id as product_id, cp.name as product_name,
                           COALESCE(SUM(spp.quantity),0) as sold_qty,
                           COALESCE(MAX(cp.price_unit),0) as unit_price,
                           COALESCE(MAX(cp.cost),0) as cost_price
                    FROM shop_paniers_products spp
                    LEFT JOIN shop_paniers p ON spp.panier_id = p.id
                    LEFT JOIN core_products cp ON spp.product_id = cp.id
                    WHERE p.created_at >= :d1 AND p.created_at <= :d2
                    AND LOWER(COALESCE(p.status,'')) NOT IN ('cancelled', 'annule', 'canceled')
                    GROUP BY cp.id, cp.name
                """)
                prod_rows = session.execute(q_products, {'d1': d1, 'd2': d2}).fetchall()

                # Ventes restaurant
                q_restau = text("""
                    SELECT cp.id as product_id, cp.name as product_name,
                           COALESCE(SUM(rpp.quantity),0) as sold_qty,
                           COALESCE(MAX(cp.price_unit),0) as unit_price,
                           COALESCE(MAX(cp.cost),0) as cost_price
                    FROM restau_produit_panier rpp
                    LEFT JOIN restau_paniers rp ON rpp.panier_id = rp.id
                    LEFT JOIN core_products cp ON rpp.product_id = cp.id
                    WHERE rp.created_at >= :d1 AND rp.created_at <= :d2
                    AND LOWER(COALESCE(rp.status,'')) NOT IN ('annule', 'cancelled', 'canceled')
                    GROUP BY cp.id, cp.name
                """)
                restau_rows = session.execute(q_restau, {'d1': d1, 'd2': d2}).fetchall()

                # Services (shop)
                service_map = []
                if include_services:
                    service_name_sql = "COALESCE(ss.name, ss.nom, 'Service')"
                    service_price_sql = "COALESCE(ss.price, ss.prix, ss.price_unit, ss.unit_price, 0)"
                    try:
                        columns = {col.get('name') for col in inspect(session.bind).get_columns('shop_services')}
                        if 'name' not in columns and 'nom' not in columns:
                            service_name_sql = "CONCAT('Service-', ss.id)"
                        if 'price' not in columns and 'prix' not in columns and 'price_unit' not in columns and 'unit_price' not in columns:
                            service_price_sql = "0"
                    except Exception:
                        pass
                    q_services = text(f"""
                        SELECT ss.id as service_id, {service_name_sql} as service_name,
                               COALESCE(SUM(sps.quantity),0) as sold_qty,
                               COALESCE(MAX({service_price_sql}),0) as unit_price
                        FROM shop_paniers_services sps
                        LEFT JOIN shop_paniers p ON sps.panier_id = p.id
                        LEFT JOIN shop_services ss ON sps.service_id = ss.id
                        WHERE p.created_at >= :d1 AND p.created_at <= :d2
                        AND LOWER(COALESCE(p.status,'')) NOT IN ('cancelled', 'annule', 'canceled')
                        GROUP BY ss.id, {service_name_sql}
                    """)
                    service_map = session.execute(q_services, {'d1': d1, 'd2': d2}).fetchall()

                # Agréger produits (boutique + restaurant) et tracer ventes par canal
                items = {}
                for r in prod_rows:
                    pid = f"P-{r.product_id}"
                    items[pid] = {
                        'name': r.product_name,
                        'sold': float(r.sold_qty or 0),
                        'sold_boutique': float(r.sold_qty or 0),
                        'sold_restau': 0.0,
                        'unit_price': float(r.unit_price or 0),
                        'cost_price': float(r.cost_price or 0),
                        'product_id': r.product_id,
                        'is_service': False
                    }
                for r in restau_rows:
                    pid = f"P-{r.product_id}"
                    if pid in items:
                        items[pid]['sold'] += float(r.sold_qty or 0)
                        items[pid]['sold_restau'] += float(r.sold_qty or 0)
                    else:
                        items[pid] = {
                            'name': r.product_name,
                            'sold': float(r.sold_qty or 0),
                            'sold_boutique': 0.0,
                            'sold_restau': float(r.sold_qty or 0),
                            'unit_price': float(r.unit_price or 0),
                            'cost_price': float(r.cost_price or 0),
                            'product_id': r.product_id,
                            'is_service': False
                        }
                # Services
                for s in service_map:
                    sid = f"S-{s.service_id}"
                    items[sid] = {
                        'name': s.service_name,
                        'sold': float(s.sold_qty or 0),
                        'unit_price': float(s.unit_price or 0),
                        'service_id': s.service_id,
                        'is_service': True
                    }

                # Préparer enterprise context et cache des entrepôts POS
                enterprise_id = SessionManager.get_current_enterprise_id() or None
                warehouse_cache = {}

                # Pour chaque produit/service, calculer quantités stock via stock_mouvements
                rows_out = []
                for idx, (key, it) in enumerate(items.items(), start=1):
                    print("DEBUG 1 : Verifier si on entre dans la boucle")
                    if it.get('is_service'):
                        # Pas de stock pour les services -> pas d'initial
                        initial_q = None
                        added_q = 0.0
                        purchases_q = 0.0
                    else:
                        pid = it.get('product_id')
                        # quantité initiale : PRIMER INVENTAIRE DE LA JOURNÉE (le premier inventaire complété
                        # sur la journée de d1 sera considéré comme quantité initiale). Si aucun inventaire
                        # ce jour-là pour le produit, laisser `initial_q` à None.
                        try:
                            # Chercher le premier inventaire COMPLETED de la journée de d1 qui contient CE produit
                            initial_q = None
                            try:
                                start_day = datetime.combine(d1.date(), datetime.min.time())
                                end_day = datetime.combine(d1.date(), datetime.max.time())
                                if wid:
                                    r_prod_inv = session.execute(text("""
                                        SELECT sii.counted_stock, si.completed_date
                                        FROM stock_inventaire_item sii
                                        JOIN stock_inventaire si ON sii.inventory_id = si.id
                                        WHERE sii.product_id = :pid
                                          AND si.warehouse_id = :wid
                                          AND si.status = 'COMPLETED'
                                          AND si.completed_date >= :start_day
                                          AND si.completed_date <= :end_day
                                        ORDER BY si.completed_date ASC
                                        LIMIT 1
                                    """), {'pid': pid, 'wid': wid, 'start_day': start_day, 'end_day': end_day}).fetchone()
                                else:
                                    r_prod_inv = session.execute(text("""
                                        SELECT sii.counted_stock, si.completed_date
                                        FROM stock_inventaire_item sii
                                        JOIN stock_inventaire si ON sii.inventory_id = si.id
                                        WHERE sii.product_id = :pid
                                          AND si.status = 'COMPLETED'
                                          AND si.completed_date >= :start_day
                                          AND si.completed_date <= :end_day
                                        ORDER BY si.completed_date ASC
                                        LIMIT 1
                                    """), {'pid': pid, 'start_day': start_day, 'end_day': end_day}).fetchone()
                                if r_prod_inv:
                                    initial_q = float(r_prod_inv.counted_stock)
                            except Exception:
                                initial_q = None
                        except Exception:
                            initial_q = None

                        # quantité ajoutée pendant l'intervalle (ENTREE, TRANSFERT)
                        try:
                            if wid:
                                q_added = text("""
                                    SELECT COALESCE(SUM(CASE
                                        WHEN movement_type = 'ENTREE' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity
                                        WHEN movement_type = 'TRANSFERT' AND destination_warehouse_id = :wid THEN ABS(quantity)
                                        WHEN movement_type = 'AJUSTEMENT' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity
                                        ELSE 0 END),0) as qty
                                    FROM stock_mouvements
                                    WHERE product_id = :pid
                                    AND movement_date >= :d1
                                    AND movement_date <= :d2
                                    AND (warehouse_id = :wid OR destination_warehouse_id = :wid)
                                """)
                                r_added = session.execute(q_added, {'pid': pid, 'd1': d1, 'd2': d2, 'wid': wid}).fetchone()
                            else:
                                q_added = text("SELECT COALESCE(SUM(quantity),0) as qty FROM stock_mouvements WHERE product_id = :pid AND movement_date >= :d1 AND movement_date <= :d2 AND movement_type IN ('ENTREE','TRANSFERT','AJUSTEMENT')")
                                r_added = session.execute(q_added, {'pid': pid, 'd1': d1, 'd2': d2}).fetchone()
                            added_q = float(r_added.qty or 0)
                        except Exception:
                            added_q = 0.0

                        # achats/transferts (ENTREE or TRANSFERT)
                        try:
                            if wid:
                                q_purch = text("""
                                    SELECT COALESCE(SUM(CASE
                                        WHEN movement_type = 'ENTREE' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity
                                        WHEN movement_type = 'TRANSFERT' AND destination_warehouse_id = :wid THEN ABS(quantity)
                                        ELSE 0 END),0) as qty
                                    FROM stock_mouvements
                                    WHERE product_id = :pid
                                    AND movement_date >= :d1
                                    AND movement_date <= :d2
                                    AND (warehouse_id = :wid OR destination_warehouse_id = :wid)
                                """)
                                r_purch = session.execute(q_purch, {'pid': pid, 'd1': d1, 'd2': d2, 'wid': wid}).fetchone()
                            else:
                                q_purch = text("SELECT COALESCE(SUM(quantity),0) as qty FROM stock_mouvements WHERE product_id = :pid AND movement_date >= :d1 AND movement_date <= :d2 AND movement_type IN ('ENTREE','TRANSFERT')")
                                r_purch = session.execute(q_purch, {'pid': pid, 'd1': d1, 'd2': d2}).fetchone()
                            purchases_q = float(r_purch.qty or 0)
                        except Exception:
                            purchases_q = 0.0

                    sold = float(it.get('sold', 0.0))
                    total_initial_plus = initial_q + added_q
                    reste = total_initial_plus - sold
                    unit_price = float(it.get('unit_price', 0.0))
                    total_amount = sold * unit_price

                    rows_out.append({
                        'no': idx,
                        'name': it['name'],
                        'initial_quantity': initial_q,
                        'quantity_added': added_q,
                        'purchases_transfers': purchases_q,
                        'product_id': it.get('product_id'),
                        'service_id': it.get('service_id'),
                        'total_initial_plus_added': total_initial_plus,
                        'reste': reste,
                        'sold': sold,
                        'unit_price': unit_price,
                        'total': total_amount
                    })

                # Générer CSV
                export_dir = os.path.join(os.getcwd(), 'exports')
                os.makedirs(export_dir, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"produits_vendus_{timestamp}.csv"
                path = os.path.join(export_dir, filename)
                import csv
                # Si aucun produit n'a d'inventaire initial pour la période, masquer les colonnes Initial/Remaining
                any_initial = any((r.get('initial_quantity') is not None) for r in rows_out)
                with open(path, 'w', newline='', encoding='utf-8') as csvfile:
                    if any_initial:
                        fieldnames = ['No', 'Name', 'Initial Quantity', 'Quantity Added', 'Purchases/Transfers', 'Total Initial+Added', 'Remaining', 'Sold', 'Unit Price', 'Total']
                    else:
                        fieldnames = ['No', 'Name', 'Quantity Added', 'Purchases/Transfers', 'Total Initial+Added', 'Sold', 'Unit Price', 'Total']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    # Totals accumulator
                    total_row = { 'Initial Quantity':0, 'Quantity Added':0, 'Purchases/Transfers':0, 'Total Initial+Added':0, 'Remaining':0, 'Sold':0, 'Total':0 }
                    for r in rows_out:
                        if any_initial:
                            init_val = '' if r['initial_quantity'] is None else f"{r['initial_quantity']:.3f}"
                            remaining_val = '' if r['initial_quantity'] is None else f"{r['reste']:.3f}"
                            row_dict = {
                                'No': r['no'],
                                'Name': r['name'],
                                'Initial Quantity': init_val,
                                'Quantity Added': f"{r['quantity_added']:.3f}",
                                'Purchases/Transfers': f"{r['purchases_transfers']:.3f}",
                                'Total Initial+Added': f"{r['total_initial_plus_added']:.3f}",
                                'Remaining': remaining_val,
                                'Sold': f"{r['sold']:.3f}",
                                'Unit Price': f"{r['unit_price']:.2f}",
                                'Total': f"{r['total']:.2f}"
                            }
                        else:
                            row_dict = {
                                'No': r['no'],
                                'Name': r['name'],
                                'Quantity Added': f"{r['quantity_added']:.3f}",
                                'Purchases/Transfers': f"{r['purchases_transfers']:.3f}",
                                'Total Initial+Added': f"{r['total_initial_plus_added']:.3f}",
                                'Sold': f"{r['sold']:.3f}",
                                'Unit Price': f"{r['unit_price']:.2f}",
                                'Total': f"{r['total']:.2f}"
                            }
                        writer.writerow(row_dict)
                        total_row['Initial Quantity'] += (r.get('initial_quantity') or 0)
                        total_row['Quantity Added'] += r['quantity_added']
                        total_row['Purchases/Transfers'] += r['purchases_transfers']
                        total_row['Total Initial+Added'] += r['total_initial_plus_added']
                        total_row['Remaining'] += (r.get('reste') or 0)
                        total_row['Sold'] += r['sold']
                        total_row['Total'] += r['total']

                    # Totals line
                    if any_initial:
                        writer.writerow({})
                        writer.writerow({
                            'No': '',
                            'Name': 'TOTALS',
                            'Initial Quantity': f"{total_row['Initial Quantity']:.3f}",
                            'Quantity Added': f"{total_row['Quantity Added']:.3f}",
                            'Purchases/Transfers': f"{total_row['Purchases/Transfers']:.3f}",
                            'Total Initial+Added': f"{total_row['Total Initial+Added']:.3f}",
                            'Remaining': f"{total_row['Remaining']:.3f}",
                            'Sold': f"{total_row['Sold']:.3f}",
                            'Unit Price': '',
                            'Total': f"{total_row['Total']:.2f}"
                        })
                    else:
                        writer.writerow({})
                        writer.writerow({
                            'No': '',
                            'Name': 'TOTALS',
                            'Quantity Added': f"{total_row['Quantity Added']:.3f}",
                            'Purchases/Transfers': f"{total_row['Purchases/Transfers']:.3f}",
                            'Total Initial+Added': f"{total_row['Total Initial+Added']:.3f}",
                            'Sold': f"{total_row['Sold']:.3f}",
                            'Unit Price': '',
                            'Total': f"{total_row['Total']:.2f}"
                        })

                return path

        except Exception as e:
            print(f"❌ Erreur export_products_summary: {e}")
            return ''

def get_products_summary(self, date_debut, date_fin, include_services: bool = True, module: str = None, pos_id: int = None, search_term: str = None, selected_product_ids: list = None, selected_category_ids: list = None):
        """
        Retourne la liste des produits/services vendus (rows_out) pour la période donnée.
        Même logique qu'export_products_summary mais renvoie les lignes au lieu d'écrire un CSV.
        """
        from datetime import datetime as _dt
        # Normaliser bornes
        if isinstance(date_debut, _dt):
            d1 = date_debut
        else:
            d1 = datetime.combine(date_debut, datetime.min.time())
        if isinstance(date_fin, _dt):
            d2 = date_fin
        else:
            d2 = datetime.combine(date_fin, datetime.max.time())

        try:
            with self.db_manager.get_session() as session:
                # Rassembler ventes produits (boutique) avec filtres optionnels
                prod_base = """
                    SELECT cp.id as product_id, cp.name as product_name,
                           COALESCE(SUM(spp.quantity),0) as sold_qty,
                           COALESCE(MAX(cp.price_unit),0) as unit_price
                    FROM shop_paniers_products spp
                    LEFT JOIN shop_paniers p ON spp.panier_id = p.id
                    LEFT JOIN core_products cp ON spp.product_id = cp.id
                    WHERE p.created_at >= :d1 AND p.created_at <= :d2
                    AND LOWER(COALESCE(p.status,'')) NOT IN ('cancelled', 'annule', 'canceled')
                """
                prod_params = {'d1': d1, 'd2': d2}
                # Apply search term filter
                if search_term:
                    prod_base += " AND (cp.name LIKE :search OR CAST(cp.id AS CHAR) LIKE :search)"
                    prod_params['search'] = f"%{search_term}%"
                # Apply selected product ids filter
                if selected_product_ids:
                    # ensure list of ints
                    ids = tuple(int(x) for x in selected_product_ids)
                    if len(ids) == 1:
                        prod_base += " AND cp.id = :pid_filter"
                        prod_params['pid_filter'] = ids[0]
                    else:
                        prod_base += f" AND cp.id IN :pids"
                        prod_params['pids'] = ids
                # Apply category filter if provided (core_products.category_id)
                if selected_category_ids:
                    cats = tuple(int(x) for x in selected_category_ids)
                    if len(cats) == 1:
                        prod_base += " AND cp.category_id = :cat_filter"
                        prod_params['cat_filter'] = cats[0]
                    else:
                        prod_base += f" AND cp.category_id IN :cats"
                        prod_params['cats'] = cats

                prod_base += " GROUP BY cp.id, cp.name"
                q_products = text(prod_base)
                prod_rows = session.execute(q_products, prod_params).fetchall()

                # Ventes restaurant (avec mêmes filtres)
                rest_base = """
                    SELECT cp.id as product_id, cp.name as product_name,
                           COALESCE(SUM(rpp.quantity),0) as sold_qty,
                           COALESCE(MAX(cp.price_unit),0) as unit_price
                    FROM restau_produit_panier rpp
                    LEFT JOIN restau_paniers rp ON rpp.panier_id = rp.id
                    LEFT JOIN core_products cp ON rpp.product_id = cp.id
                    WHERE rp.created_at >= :d1 AND rp.created_at <= :d2
                    AND LOWER(COALESCE(rp.status,'')) NOT IN ('annule', 'cancelled', 'canceled')
                """
                rest_params = {'d1': d1, 'd2': d2}
                if search_term:
                    rest_base += " AND (cp.name LIKE :search OR CAST(cp.id AS CHAR) LIKE :search)"
                    rest_params['search'] = f"%{search_term}%"
                if selected_product_ids:
                    ids = tuple(int(x) for x in selected_product_ids)
                    if len(ids) == 1:
                        rest_base += " AND cp.id = :pid_filter"
                        rest_params['pid_filter'] = ids[0]
                    else:
                        rest_base += f" AND cp.id IN :pids"
                        rest_params['pids'] = ids
                if selected_category_ids:
                    cats = tuple(int(x) for x in selected_category_ids)
                    if len(cats) == 1:
                        rest_base += " AND cp.category_id = :cat_filter"
                        rest_params['cat_filter'] = cats[0]
                    else:
                        rest_base += f" AND cp.category_id IN :cats"
                        rest_params['cats'] = cats

                rest_base += " GROUP BY cp.id, cp.name"
                q_restau = text(rest_base)
                restau_rows = session.execute(q_restau, rest_params).fetchall()

                # Services (shop)
                service_map = []
                if include_services:
                    service_name_sql = "COALESCE(ss.name, ss.nom, 'Service')"
                    service_price_sql = "COALESCE(ss.price, ss.prix, ss.price_unit, ss.unit_price, 0)"
                    try:
                        columns = {col.get('name') for col in inspect(session.bind).get_columns('shop_services')}
                        if 'name' not in columns and 'nom' not in columns:
                            service_name_sql = "CONCAT('Service-', ss.id)"
                        if 'price' not in columns and 'prix' not in columns and 'price_unit' not in columns and 'unit_price' not in columns:
                            service_price_sql = "0"
                    except Exception:
                        pass
                    q_services = text(f"""
                        SELECT ss.id as service_id, {service_name_sql} as service_name,
                               COALESCE(SUM(sps.quantity),0) as sold_qty,
                               COALESCE(MAX({service_price_sql}),0) as unit_price
                        FROM shop_paniers_services sps
                        LEFT JOIN shop_paniers p ON sps.panier_id = p.id
                        LEFT JOIN shop_services ss ON sps.service_id = ss.id
                        WHERE p.created_at >= :d1 AND p.created_at <= :d2
                        AND LOWER(COALESCE(p.status,'')) NOT IN ('cancelled', 'annule', 'canceled')
                        GROUP BY ss.id, {service_name_sql}
                    """)
                    service_map = session.execute(q_services, {'d1': d1, 'd2': d2}).fetchall()

                # Agréger produits (boutique + restaurant)
                items = {}
                for r in prod_rows:
                    pid = f"P-{r.product_id}"
                    items[pid] = {
                        'name': r.product_name,
                        'sold': float(r.sold_qty or 0),
                        'unit_price': float(r.unit_price or 0),
                        'cost_price': float(r.cost_price or 0),
                        'product_id': r.product_id,
                        'is_service': False
                    }
                for r in restau_rows:
                    pid = f"P-{r.product_id}"
                    if pid in items:
                        items[pid]['sold'] += float(r.sold_qty or 0)
                    else:
                        items[pid] = {
                            'name': r.product_name,
                            'sold': float(r.sold_qty or 0),
                            'unit_price': float(r.unit_price or 0),
                            'product_id': r.product_id,
                            'is_service': False
                        }
                # Services
                for s in service_map:
                    sid = f"S-{s.service_id}"
                    items[sid] = {
                        'name': s.service_name,
                        'sold': float(s.sold_qty or 0),
                        'unit_price': float(s.unit_price or 0),
                        'service_id': s.service_id,
                        'is_service': True
                    }

                # Si on a un pos_id (ou un module connu), tenter de résoudre l'entrepôt ciblé
                warehouse_id = None
                try:
                    if pos_id:
                        from ayanna_erp.modules.core.controllers.product_controller import CoreProductController
                        from ayanna_erp.modules.stock.models import StockWarehouse
                        core_ctrl = CoreProductController(pos_id)
                        pos_code = getattr(core_ctrl, 'pos_code', None)
                        if pos_code:
                            wh = session.query(StockWarehouse).filter_by(code=pos_code).first()
                            if wh:
                                warehouse_id = wh.id
                    elif module:
                        # Heuristiques: si module == 'restaurant' -> pos_id 4
                        if module == 'restaurant':
                            from ayanna_erp.modules.core.controllers.product_controller import CoreProductController
                            from ayanna_erp.modules.stock.models import StockWarehouse
                            core_ctrl = CoreProductController(4)
                            pos_code = getattr(core_ctrl, 'pos_code', None)
                            if pos_code:
                                wh = session.query(StockWarehouse).filter_by(code=pos_code).first()
                                if wh:
                                    warehouse_id = wh.id
                except Exception:
                    warehouse_id = None

                # AJOUTER TOUS LES PRODUITS ACTIFS (même non vendus) pour avoir une vue complète
                # Récupérer tous les produits actifs
                q_all_products = text("""
                    SELECT id as product_id, name as product_name, price_unit
                    FROM core_products
                    WHERE is_active = 1
                    ORDER BY name
                """)
                all_products_rows = session.execute(q_all_products).fetchall()
                
                # Ajouter les produits non vendus à items
                for prod in all_products_rows:
                    pid = f"P-{prod.product_id}"
                    if pid not in items:
                        # Produit actif mais non vendu pendant la période
                        items[pid] = {
                            'name': prod.product_name,
                            'sold': 0.0,
                            'unit_price': float(prod.price_unit or 0),
                            'cost_price': float(prod.cost or 0),
                            'product_id': prod.product_id,
                            'is_service': False
                        }

                # Pour chaque produit/service, calculer quantités stock via stock_mouvements
                rows_out = []
                for idx, (key, it) in enumerate(items.items(), start=1):
                    if it.get('is_service'):
                        # Pas de stock pour les services -> pas d'initial
                        initial_q = None
                        added_q = 0.0
                        adjustments_q = 0.0
                    else:
                        pid = it.get('product_id')
                        # QUANTITÉ INITIALE = dernier inventaire COMPLETED qui contient CE produit spécifiquement
                        try:
                            start_day = datetime.combine(d1.date(), datetime.min.time())
                            end_day = datetime.combine(d1.date(), datetime.max.time())
                            if warehouse_id:
                                r_prod_inv = session.execute(text("""
                                    SELECT sii.counted_stock, si.completed_date
                                    FROM stock_inventaire_item sii
                                    JOIN stock_inventaire si ON sii.inventory_id = si.id
                                    WHERE sii.product_id = :pid
                                      AND si.warehouse_id = :wid
                                      AND si.status = 'COMPLETED'
                                      AND si.completed_date >= :start_day
                                      AND si.completed_date <= :end_day
                                    ORDER BY si.completed_date ASC
                                    LIMIT 1
                                """), {'pid': pid, 'wid': warehouse_id, 'start_day': start_day, 'end_day': end_day}).fetchone()
                            else:
                                r_prod_inv = session.execute(text("""
                                    SELECT sii.counted_stock, si.completed_date
                                    FROM stock_inventaire_item sii
                                    JOIN stock_inventaire si ON sii.inventory_id = si.id
                                    WHERE sii.product_id = :pid
                                      AND si.status = 'COMPLETED'
                                      AND si.completed_date >= :start_day
                                      AND si.completed_date <= :end_day
                                    ORDER BY si.completed_date ASC
                                    LIMIT 1
                                """), {'pid': pid, 'start_day': start_day, 'end_day': end_day}).fetchone()
                            if r_prod_inv:
                                initial_q = float(r_prod_inv.counted_stock or 0)
                            else:
                                initial_q = None
                        except Exception as e:
                            print(f"⚠️ Erreur calcul Q initiale pour produit {pid}: {e}")
                            initial_q = None

                        # AJOUTS DU JOUR = ENTREE + TRANSFERT IN (reçus uniquement)
                        # On ne compte que les entrées réelles (achats) et les transferts entrants
                        if warehouse_id:
                            q_added_sql = text("""
                                SELECT COALESCE(SUM(CASE 
                                    WHEN movement_type = 'ENTREE' AND warehouse_id = :wid THEN quantity
                                    WHEN movement_type = 'ENTREE' AND destination_warehouse_id = :wid THEN quantity
                                        WHEN movement_type = 'TRANSFERT' AND destination_warehouse_id = :wid THEN ABS(quantity)
                                    ELSE 0
                                END), 0) as qty
                                FROM stock_mouvements
                                WHERE product_id = :pid 
                                AND movement_date >= :d1 
                                AND movement_date <= :d2
                                AND (warehouse_id = :wid OR destination_warehouse_id = :wid)
                            """)
                        else:
                            q_added_sql = text("""
                                SELECT COALESCE(SUM(CASE 
                                    WHEN movement_type = 'ENTREE' THEN quantity
                                        WHEN movement_type = 'TRANSFERT' THEN 0
                                    ELSE 0
                                END), 0) as qty
                                FROM stock_mouvements
                                WHERE product_id = :pid 
                                AND movement_date >= :d1 
                                AND movement_date <= :d2
                            """)
                        
                        try:
                            params_added = {'pid': pid, 'd1': d1, 'd2': d2}
                            if warehouse_id:
                                params_added['wid'] = warehouse_id
                            r_added = session.execute(q_added_sql, params_added).fetchone()
                            added_q = float(r_added.qty or 0)
                        except Exception as e:
                            print(f"⚠️ Erreur calcul ajouts pour produit {pid}: {e}")
                            added_q = 0.0

                        # On ne renvoie plus les ajustements comme colonne séparée dans l'export.
                        adjustments_q = 0.0

                    sold = float(it.get('sold', 0.0))
                    # Quantité finale = Q_initiale + Ajouts - Ventes
                    final_q = (initial_q if initial_q is not None else 0) + added_q - sold
                    unit_price = float(it.get('unit_price', 0.0))
                    total_amount = sold * unit_price
                    
                    # PRODUITS SEULEMENT
                    if not it.get('is_service'):
                        cost_price = float(it.get('cost_price', 0.0))
                        total_cost = sold * cost_price
                        margin = total_amount - total_cost
                    else:
                        cost_price = None
                        total_cost = None
                        margin = None
                        
                    print(f"DEBUG 5  : Je compte voir la marge et le cout de {margin} pour le produit {cost_price}")

                    rows_out.append({
                        'no': idx,
                        'name': it['name'],
                        'initial_quantity': initial_q,
                        'quantity_added': added_q,
                        # adjustments removed on request
                        'product_id': it.get('product_id'),
                        'service_id': it.get('service_id'),
                        'sold': sold,
                        'final_quantity': final_q,
                        'unit_price': unit_price,
                        'cost_price': cost_price,
                        'margin': margin,
                        'total': total_amount
                    })

                # If at least one product has an initial inventory (not None),
                # set initial_quantity to 0 for products without inventory so column appears.
                any_initial = any((r.get('initial_quantity') is not None) for r in rows_out)
                if any_initial:
                    for r in rows_out:
                        if r.get('initial_quantity') is None:
                            r['initial_quantity'] = 0.0

                return rows_out

        except Exception as e:
            print(f"❌ Erreur get_products_summary: {e}")
            
def print_products_report(self, date_debut, date_fin, paper: str = 'A4', include_services: bool = True, module: str = None, pos_id: int = None, search_term: str = None, selected_product_ids: list = None, selected_category_ids: list = None, rows: list = None):
    """Génère et ouvre un PDF du rapport produits.
    - `paper` peut être 'A4' (tableau complet) ou '80mm' (format ticket thermique simplifié).
    Pour 80mm, on affiche seulement: Q.init, Ajouts, Ventes, Reste, Montant total vendu.
    """
    try:
        from PyQt6.QtGui import QPdfWriter, QTextDocument
        from PyQt6.QtCore import QSizeF
        from PyQt6.QtGui import QPageSize
        from PyQt6.QtGui import QPdfWriter as _QPdfWriter
        from PyQt6.QtGui import QPagedPaintDevice
        from PyQt6.QtCore import QMarginsF
        import tempfile, subprocess, os
        from datetime import datetime

        # Prefer using an existing controller attached to the caller widget (has db_manager).
        # If caller provided rows, use them directly (keeps A4 selection behaviour)
        if rows is None:
            try:
                controller = getattr(self, 'commande_controller', None)
                if controller and hasattr(controller, 'get_products_summary'):
                    rows = controller.get_products_summary(date_debut, date_fin, include_services=include_services, module=module, pos_id=pos_id, search_term=search_term, selected_product_ids=selected_product_ids, selected_category_ids=selected_category_ids) or []
                else:
                    from ayanna_erp.modules.boutique.controller.commande_controller import CommandeController
                    commande_controller = CommandeController()
                    if hasattr(commande_controller, 'get_products_summary'):
                        rows = commande_controller.get_products_summary(date_debut, date_fin, include_services=include_services, module=module, pos_id=pos_id, search_term=search_term, selected_product_ids=selected_product_ids, selected_category_ids=selected_category_ids) or []
                    else:
                        rows = get_products_summary(self, date_debut, date_fin, include_services=include_services, module=module, pos_id=pos_id, search_term=search_term, selected_product_ids=selected_product_ids, selected_category_ids=selected_category_ids) or []
            except Exception:
                rows = []

        # Company header/footer
        try:
            from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
            enterprise_id = SessionManager.get_current_enterprise_id() or None
            ent_ctrl = EntrepriseController()
            company_info = ent_ctrl.get_company_info_for_pdf(enterprise_id)
        except Exception:
            company_info = {'name': 'Entreprise', 'address': '', 'phone': '', 'logo': None}

        # Determine first COMPLETED inventory name for the date (NB)
        inventory_note = None
        try:
            from ayanna_erp.database.database_manager import DatabaseManager
            from sqlalchemy import text
            dbm = DatabaseManager()
            # normalize to day
            try:
                sd = date_debut if isinstance(date_debut, datetime) else datetime.combine(date_debut, datetime.min.time())
                start_day = datetime.combine(sd.date(), datetime.min.time())
                end_day = datetime.combine(sd.date(), datetime.max.time())
            except Exception:
                start_day = datetime.combine(datetime.now().date(), datetime.min.time())
                end_day = datetime.combine(datetime.now().date(), datetime.max.time())

            with dbm.get_session() as sess:
                q = text("""
                    SELECT session_name FROM stock_inventaire
                    WHERE status = 'COMPLETED' AND completed_date >= :start_day AND completed_date <= :end_day
                    ORDER BY completed_date ASC LIMIT 1
                """)
                r = sess.execute(q, {'start_day': start_day, 'end_day': end_day}).fetchone()
                if r and getattr(r, 'session_name', None):
                    inventory_note = r.session_name
        except Exception:
            inventory_note = None

        # Sort rows alphabetically by product/service name so exports are ordered
        try:
            rows = sorted(rows or [], key=lambda r: (str(r.get('name') if isinstance(r, dict) else getattr(r, 'name', '') or '')).lower())
        except Exception:
            rows = rows or []

        # Assign sequential numbers for A4 display (used as 'no' column)
        try:
            for idx, rr in enumerate(rows, start=1):
                if isinstance(rr, dict):
                    rr['no'] = idx
        except Exception:
            pass

        # Construire HTML
        currency = get_currency(SessionManager.get_current_enterprise_id()) if 'get_currency' in globals() else ''
        import tempfile
        logo_path = None
        try:
            if company_info.get('logo'):
                tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                tmp.write(company_info.get('logo'))
                tmp.flush()
                tmp.close()
                logo_path = tmp.name
        except Exception:
            logo_path = None

        html = '<html><head><meta charset="utf-8"><style>body{font-family:Arial,Helvetica,sans-serif;}table{width:100%;border-collapse:collapse;}td,th{padding:6px;border:1px solid #ddd;font-size:11px;}th{background:#f2f2f2;font-weight:bold;font-size:12px;}</style></head><body>'
        # Header
        if logo_path:
            html += f"<div style='text-align:center'><img src='file://{logo_path}' style='width:50px;height:50px;'/><div><b>{company_info.get('name','')}</b><br/>{company_info.get('address','')}<br/>Tel: {company_info.get('phone','')}</div></div><hr/>"
        else:
            html += f"<div style='text-align:center'><b>{company_info.get('name','')}</b><br/>{company_info.get('address','')}<br/>Tel: {company_info.get('phone','')}</div><hr/>"

        title = f"RAPPORT PRODUITS {date_debut} → {date_fin}"
        html += f"<h2 style='text-align:center'>{title}</h2>"

        # Detecter si on a des qtes initiales pour afficher/masquer colonnes
        has_initials = any((r.get('initial_quantity') is not None) for r in rows)

        if paper == '80mm':
            # Generate a proper 80mm ticket using ReportLab (like other receipts)
            try:
                from reportlab.lib.units import mm
                from reportlab.lib import colors
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                from reportlab.lib.enums import TA_CENTER, TA_RIGHT

                page_width = 80 * mm
                page_height = 297 * mm

                temp_dir = tempfile.gettempdir()
                filename = f"rapport_produits_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                pdf_path = os.path.join(temp_dir, filename)

                doc = SimpleDocTemplate(
                    pdf_path,
                    pagesize=(page_width, page_height),
                    rightMargin=2*mm, leftMargin=2*mm, topMargin=3*mm, bottomMargin=3*mm
                )

                styles = getSampleStyleSheet()
                style_title = ParagraphStyle('Title80', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, alignment=TA_CENTER, spaceAfter=2)
                style_normal = ParagraphStyle('Normal80', parent=styles['Normal'], fontName='Helvetica', fontSize=10, alignment=TA_CENTER, spaceAfter=1)
                style_small = ParagraphStyle('Small80', parent=styles['Normal'], fontName='Helvetica', fontSize=9, alignment=TA_CENTER)
                style_line = ParagraphStyle('Line80', parent=styles['Normal'], fontName='Helvetica', fontSize=9)

                flow = []

                # Header company
                # Determine display name: prefer company_info, fallback to core_entreprises table
                company_display_name = company_info.get('name') if company_info and company_info.get('name') else None
                if not company_display_name:
                    try:
                        from ayanna_erp.database.database_manager import DatabaseManager
                        from sqlalchemy import text
                        dbm2 = DatabaseManager()
                        with dbm2.get_session() as s2:
                            rname = s2.execute(text("SELECT name FROM core_entreprises LIMIT 1")).fetchone()
                            if rname:
                                # rname may be Row or tuple
                                company_display_name = getattr(rname, 'name', None) or (rname[0] if len(rname) > 0 else None)
                    except Exception:
                        company_display_name = None
                if not company_display_name:
                    company_display_name = 'Entreprise'

                flow.append(Paragraph(f"<b>{company_display_name}</b>", style_title))
                if company_info.get('address'):
                    flow.append(Paragraph(company_info.get('address',''), style_small))
                if company_info.get('phone'):
                    flow.append(Paragraph(f"Tél: {company_info.get('phone','')}", style_small))
                flow.append(Spacer(1, 2*mm))
                flow.append(Paragraph("=" * 40, style_normal))

                # Title and date range (use 'RAPPORT VENTE')
                flow.append(Paragraph(f"<b>RAPPORT VENTE</b>", style_title))
                flow.append(Paragraph(f"{date_debut} → {date_fin}", style_small))
                flow.append(Spacer(1, 1*mm))
                flow.append(Paragraph("-" * 40, style_normal))

                # Table header with abbreviated column names (QI, QA, QV, RST, TT)
                if has_initials:
                    table_header = [Paragraph("<b>Nom</b>", style_line), Paragraph("<b>QI</b>", style_line), Paragraph("<b>QA</b>", style_line), Paragraph("<b>QV</b>", style_line), Paragraph("<b>RST</b>", style_line), Paragraph("<b>TT</b>", style_line)]
                    # Reduce name column, enlarge total column
                    col_widths = [25*mm, 8*mm, 8*mm, 8*mm, 8*mm, 23*mm]
                else:
                    # No initial inventories -> only show Sold (QV) and Total (TT)
                    table_header = [Paragraph("<b>Nom</b>", style_line), Paragraph("<b>QV</b>", style_line), Paragraph("<b>TT</b>", style_line)]
                    col_widths = [35*mm, 12*mm, (page_width - (35+12)*mm - 4*mm)]

                # Rows
                total_amount = 0.0
                articles = []
                for r in rows:
                    name = str(r.get('name',''))
                    # Truncate product name to 15 characters
                    if len(name) > 15:
                        name = name[:13] + '..'
                    sold = float(r.get('sold', 0) or 0)
                    amount = float(r.get('total', 0) or 0)
                    qty_added = float(r.get('quantity_added', 0) or 0)
                    final_q = r.get('final_quantity')
                    init_q = r.get('initial_quantity')
                    total_amount += amount

                    # Format amounts without trailing .00 and with space thousands separator
                    def fmt(v):
                        try:
                            iv = int(round(float(v or 0)))
                        except Exception:
                            iv = 0
                        return f"{iv:,}".replace(",", " ")

                    if has_initials:
                        init_val = '' if init_q is None else f"{int(round(init_q))}"
                        reste_val = '' if init_q is None else f"{int(round(final_q or 0))}"
                        articles.append([Paragraph(name, style_line), Paragraph(init_val, style_line), Paragraph(f"{int(round(qty_added))}", style_line), Paragraph(f"{int(round(sold))}", style_line), Paragraph(reste_val, style_line), Paragraph(fmt(amount), style_line)])
                    else:
                        # Only show sold and total when no initial exist
                        articles.append([Paragraph(name, style_line), Paragraph(f"{int(round(sold))}", style_line), Paragraph(fmt(amount), style_line)])

                if len(articles) == 0:
                    flow.append(Paragraph("Aucun produit vendu.", style_line))
                else:
                    # Build table
                    if has_initials:
                        tbl = Table([table_header] + articles, colWidths=col_widths)
                    else:
                        tbl = Table([table_header] + articles, colWidths=col_widths)
                    tbl.setStyle(TableStyle([
                        ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
                        ('FONTSIZE', (0,0), (-1,-1), 9),
                        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                        ('LEFTPADDING', (0,0), (-1,-1), 2),
                        ('RIGHTPADDING', (0,0), (-1,-1), 2),
                    ]))
                    flow.append(tbl)

                flow.append(Spacer(1, 2*mm))
                flow.append(Paragraph("-" * 40, style_normal))
                # Total formatted without decimals and with space separators
                try:
                    total_fmt = f"{int(round(total_amount)):,}".replace(",", " ")
                except Exception:
                    total_fmt = str(total_amount)
                flow.append(Paragraph(f"Total ventes: {total_fmt} {currency}", style_line))
                flow.append(Spacer(1, 2*mm))
                note_text = f"NB: Inventaire pris en compte pour Q.init: {inventory_note}" if inventory_note else "NB: Aucun inventaire complété ce jour"
                flow.append(Paragraph(note_text, style_small))
                flow.append(Paragraph("Généré par Ayanna ERP", style_small))
                flow.append(Paragraph(f"Imprimé le {datetime.now().strftime('%d/%m/%Y %H:%M')}", style_small))

                doc.build(flow)
                return pdf_path
            except Exception as e:
                print(f"Erreur génération PDF 80mm produits: {e}")
                return None
        else:
            # A4 full
            html += '<table>'
            if has_initials:
                html += '<tr><th>N°</th><th>Nom</th><th>Q.init</th><th>Ajouts</th><th>Reste</th><th>Vendu</th><th>P.U</th><th>Total</th></tr>'
            else:
                # If no initial inventories for the period, show only Sold and Total columns
                html += '<tr><th>N°</th><th>Nom</th><th>Vendu</th><th>Total</th></tr>'
            for r in rows:
                if has_initials:
                    init_val = '' if r.get('initial_quantity') is None else f"{r.get('initial_quantity'):.3f}"
                    reste_val = '' if r.get('initial_quantity') is None else f"{r.get('final_quantity'):.3f}"
                    html += f"<tr><td>{r.get('no','')}</td><td>{r.get('name','')}</td><td align='right'>{init_val}</td><td align='right'>{r.get('quantity_added',0):.3f}</td><td align='right'>{reste_val}</td><td align='right'>{r.get('sold',0):.3f}</td><td align='right'>{r.get('unit_price',0):.2f}</td><td align='right'>{r.get('total',0):.2f}</td></tr>"
                else:
                    # Only sold and total
                    html += f"<tr><td>{r.get('no','')}</td><td>{r.get('name','')}</td><td align='right'>{r.get('sold',0):.3f}</td><td align='right'>{r.get('total',0):.2f}</td></tr>"
            html += '</table>'
            page_mm = QSizeF(210, 297)  # A4 portrait

        html += '</body></html>'

        # Footer
        printed_ts = datetime.now().strftime('%d/%m/%Y %H:%M')
        footer_html = "<hr/>"
        note_text = f"NB: Inventaire pris en compte pour Q.init: {inventory_note}" if inventory_note else "NB: Aucun inventaire complété ce jour"
        footer_html += f"<div style='text-align:center;font-size:10px;font-weight:bold;'>{note_text}</div>"
        footer_html += f"<div style='text-align:center;font-size:10px;'>Informatisé par Ayanna ERP — www.ayanna.top</div>"
        footer_html += f"<div style='text-align:center;font-size:9px;'>Imprimé le {printed_ts}</div>"

        # PDF temp file
        temp_dir = tempfile.gettempdir()
        filename = f"rapport_produits_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(temp_dir, filename)

        doc = QTextDocument()
        # attach footer
        html += footer_html
        doc.setHtml(html)

        pdf_writer = QPdfWriter(pdf_path)
        pdf_writer.setPageSize(QPageSize(page_mm, QPageSize.Unit.Millimeter))
        try:
            pdf_writer.setPageMargins(QMarginsF(5,5,5,5), QPageLayout.Unit.Millimeter)
        except Exception:
            try:
                pdf_writer.setPageMargins(QMarginsF(5,5,5,5))
            except Exception:
                pass
        pdf_writer.setResolution(300)

        doc.print(pdf_writer)

        # Ouvrir le PDF
        try:
            if os.name == 'nt':
                os.startfile(pdf_path)
            else:
                subprocess.run(['xdg-open', pdf_path])
        except Exception:
            pass

        # cleanup logo temp
        try:
            if logo_path and os.path.exists(logo_path):
                os.unlink(logo_path)
        except Exception:
            pass

        return pdf_path
    except Exception as e:
        print(f"Erreur génération PDF produits: {e}")
        return None
            
def export_daily_report(date_debut, date_fin, module=None, pos_id=None, search_term=None, payment_filter=None, currency_symbol=None, selected_categories=None):
    """Génère un PDF quotidien (CA, Remises, Créances, Dépenses, Espèces, Marge) aligné avec export produits.
    Retourne le chemin du PDF.
    """
    try:
        from datetime import timedelta
        from ayanna_erp.modules.boutique.controller.commande_controller import CommandeController
        from ayanna_erp.modules.salle_fete.controller.entre_sortie_controller import EntreSortieController
        from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaConfig

        commande_controller = CommandeController()

        # Préparer un cache des coûts unitaires des produits pour calculer la marge
        product_costs = {}
        try:
            from ayanna_erp.modules.core.models import CoreProduct
            with commande_controller.db_manager.get_session() as session:
                all_products = session.query(CoreProduct).all()
                for prod in all_products:
                    product_costs[prod.id] = float(getattr(prod, 'cost', 0) or 0)
        except Exception:
            product_costs = {}

        # Jours FR
        days_fr = {0: "Lun", 1: "Mar", 2: "Mer", 3: "Jeu", 4: "Ven", 5: "Sam", 6: "Dim"}
        rows = []
        current = date_debut

        selected_set = set(selected_categories or [])

        # Mapping produit -> catégorie (pour filtrer les calculs du rapport)
        product_categories = {}
        try:
            from ayanna_erp.modules.core.models import CoreProduct, CoreProductCategory
            with commande_controller.db_manager.get_session() as session:
                all_products = session.query(CoreProduct).all()
                for prod in all_products:
                    category_name = 'Sans catégorie'
                    if getattr(prod, 'category_id', None):
                        cat = session.query(CoreProductCategory).get(prod.category_id)
                        if cat and getattr(cat, 'name', None):
                            category_name = cat.name
                    product_categories[prod.id] = category_name
        except Exception:
            product_categories = {}

        while current <= date_fin:
            label = f"{days_fr.get(current.weekday(), '')} {current.strftime('%d/%m')}"

            # Marge/CA via résumé produits/services filtré par catégories
            products_all = commande_controller.get_products_summary(
                current, current, include_services=True, module=module, pos_id=pos_id
            ) or []

            # Enrichir catégorie pour chaque ligne
            for it in products_all:
                if it.get('is_service'):
                    it['category_name'] = 'Services'
                else:
                    pid = it.get('product_id')
                    it['category_name'] = product_categories.get(pid, 'Sans catégorie')

            # Filtrage categories (si fourni)
            if selected_set:
                products = [it for it in products_all if str(it.get('category_name') or 'Sans catégorie') in selected_set]
            else:
                products = list(products_all)

            marge = 0.0
            for it in products:
                sold = float(it.get('sold', 0) or 0)
                unit_price = float(it.get('unit_price', 0) or 0)
                pid = it.get('product_id')
                # Pour les services, aucun coût connu -> coût 0
                cost = 0.0
                try:
                    if pid is not None:
                        cost = float(product_costs.get(pid, 0) or 0)
                except Exception:
                    cost = 0.0
                marge += sold * unit_price - sold * cost

            # CA filtré catégories = somme des ventes des lignes filtrées
            ca = sum(float(it.get('total', 0) or 0) for it in products)
            ca_all = sum(float(it.get('total', 0) or 0) for it in products_all)
            ratio_filtered = (ca / ca_all) if ca_all > 0 else 0.0

            # Remises, Créances via commandes du jour
            commandes_day = commande_controller.get_commandes(
                date_debut=current, date_fin=current, search_term=search_term, payment_filter=payment_filter
            ) or []
            remises = 0.0
            creances = 0.0
            for cmd in commandes_day:
                # Exclure explicitement les commandes annulées
                status_val = str(cmd.get('status', '') or '').strip().lower()
                numero_val = str(cmd.get('numero_commande', '') or '').strip().lower()
                if (
                    'annule' in status_val or 'annulé' in status_val or 'cancelled' in status_val or 'canceled' in status_val
                    or '(annule' in numero_val or 'annule)' in numero_val or 'annulé' in numero_val
                ):
                    continue

                remises += float(cmd.get('remise_amount', cmd.get('discount_amount', 0)) or 0)
                total_final = float(cmd.get('total_final', 0) or 0)
                montant_paye = float(cmd.get('montant_paye', 0) or 0)
                creances += max(total_final - montant_paye, 0)

            # Réduire proportionnellement les indicateurs si filtrage catégories actif
            if selected_set:
                remises *= ratio_filtered
                creances *= ratio_filtered

            # Calculer l'espèce = CA - Remises - Créances
            espece = ca - remises - creances

            # Dépenses (sorties caisse) du jour
            depenses = 0.0
            try:
                entre_sortie_controller = EntreSortieController()
                db_manager = entre_sortie_controller.get_database_manager() if hasattr(entre_sortie_controller, 'get_database_manager') else None
                if db_manager is None:
                    from ayanna_erp.modules.salle_fete.model.salle_fete import get_database_manager
                    db_manager = get_database_manager()
                sess = None
                try:
                    sess = db_manager.get_session()
                    config = sess.query(ComptaConfig).filter_by(pos_id=1).first()
                    compte_caisse_id = getattr(config, 'compte_caisse_id', None) if config else None
                finally:
                    try:
                        if sess is not None:
                            sess.close()
                    except Exception:
                        pass
                if compte_caisse_id:
                    journal_entries = entre_sortie_controller.load_account_journal(compte_caisse_id, date_from=current, date_to=current)
                    depenses = sum(entry.get('montant_sortie', 0) for entry in journal_entries)
            except Exception:
                depenses = 0.0

            rows.append({
                'label': label,
                'ca': ca,
                'remises': remises,
                'creances': creances,
                'depenses': depenses,
                'espece': espece,
                'marge': marge
            })

            current = current + timedelta(days=1)

        # Log pour vérifier le contenu des lignes
        # Générer PDF avec entête harmonisée
        return generate_daily_report_pdf(rows, date_debut, date_fin, currency_symbol, selected_categories=selected_categories)
    except Exception as e:
        print(f"❌ Erreur export_daily_report: {e}")
        return ''

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, NextPageTemplate, PageTemplate
from reportlab.platypus.frames import Frame
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.lib.enums import TA_CENTER
from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
import os
from datetime import datetime

def _build_company_header(styles, enterprise_id=None):
    enterprise_controller = EntrepriseController()
    company_info = enterprise_controller.get_company_info_for_pdf(enterprise_id)

    temp_logo = None
    logo_path = None
    header_data = []

    company_text = (
        f"<b>{company_info.get('name','AYANNA ERP')}</b><br/>{company_info.get('address','')}<br/>"
        f"{company_info.get('city','')}<br/>Tel: {company_info.get('phone','')}"
    )

    if company_info.get('logo'):
        try:
            import tempfile
            temp_logo = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
            temp_logo.write(company_info['logo'])
            logo_path = temp_logo.name
            temp_logo.close()
            logo = Image(logo_path, width=2.3*cm, height=2.3*cm)
            header_data.append([logo, Paragraph(company_text, styles['Normal'])])
        except Exception:
            header_data.append([Paragraph(company_text, styles['Normal']), ''])
    else:
        header_data.append([Paragraph(company_text, styles['Normal']), ''])

    header_table = Table(header_data, colWidths=[3*cm, 12*cm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP')
    ]))

    return header_table, logo_path, company_info

def generate_daily_report_pdf(rows, date_debut, date_fin, currency_symbol, enterprise_id=None, selected_categories=None):
    export_dir = os.path.join(os.getcwd(), "exports_commandes")
    os.makedirs(export_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(export_dir, f"rapport_quotidien_{timestamp}.pdf")

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=4*cm,
        rightMargin=4*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='ReportTitle', fontSize=15, fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=10))
    styles.add(ParagraphStyle(name='SmallInfo', fontSize=9, fontName='Helvetica', textColor="grey"))

    story = []

    header_table, logo_path, company_info = _build_company_header(styles, enterprise_id)
    story.append(header_table)
    story.append(Spacer(1, 0.6*cm))

    story.append(Paragraph("RAPPORT QUOTIDIEN DES VENTES", styles['ReportTitle']))
    story.append(Paragraph(f"Période : <b>{date_debut.strftime('%d/%m/%Y')}</b> - <b>{date_fin.strftime('%d/%m/%Y')}</b>", styles['Normal']))
    if selected_categories:
        story.append(Paragraph(f"Catégories sélectionnées : <b>{', '.join(selected_categories)}</b>", styles['Normal']))
    story.append(Spacer(1, 0.4*cm))

    headers = ["Date", "Chiffre d'affaires", "Remises", "Créances", "Espèces", "Marge"]

    def fmt(amount):
        try:
            from ayanna_erp.utils.formatting import format_amount_for_pdf as _fmt_pdf
            return _fmt_pdf(amount, currency_symbol)
        except Exception:
            return f"{amount:,.0f} {currency_symbol or ''}"

    data = [headers]
    totals = {k: 0.0 for k in ['ca','remises','creances','espece','marge']}
    for r in rows:
        data.append([
            r.get('label',''), fmt(r.get('ca',0)), fmt(r.get('remises',0)), fmt(r.get('creances',0)), fmt(r.get('espece',0)), fmt(r.get('marge',0))
        ])
        for k in totals:
            try:
                totals[k] += float(r.get(k, 0.0) or 0.0)
            except Exception:
                pass

    data.append(["Total", fmt(totals['ca']), fmt(totals['remises']), fmt(totals['creances']), fmt(totals['espece']), fmt(totals['marge'])])

    table = Table(data, colWidths=[3*cm, 3*cm, 2.5*cm, 2.5*cm, 2.5*cm, 3*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HexColor('#2C3E50')),
        ('TEXTCOLOR', (0,0), (-1,0), white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('BACKGROUND', (0,-1), (-1,-1), HexColor('#eaeaea')),
        ('GRID', (0,0), (-1,-1), 0.4, black),
        ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))

    story.append(table)
    story.append(Spacer(1, 0.6*cm))

    story.append(Paragraph(f"Informatisé par Ayanna Erp - {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['SmallInfo']))

    # Page graphique des courbes CA, Remises, Créances, Marge (en paysage)
    try:
        story.append(PageBreak())
        
        # Créer une page en paysage pour le graphique
        landscape_width, landscape_height = landscape(A4)
        landscape_content_width = landscape_width - 4*cm  # marges gauche + droite
        landscape_content_height = landscape_height - 4*cm  # marges haut + bas
        
        # Titre amélioré avec les dates
        titre_graphique = f"Courbe d'évolution du Chiffre d'Affaires, Remises, Créances, Espèces et Marge du {date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')}"
        story.append(Paragraph(titre_graphique, styles['ReportTitle']))

        labels = [r.get('label','') for r in rows]
        series_ca = [float(r.get('ca',0) or 0) for r in rows]
        series_rem = [float(r.get('remises',0) or 0) for r in rows]
        series_cre = [float(r.get('creances',0) or 0) for r in rows]
        series_esp = [float(r.get('espece',0) or 0) for r in rows]
        series_mar = [float(r.get('marge',0) or 0) for r in rows]

        # Adapter le graphique à la largeur utile de la page (paysage)
        chart_margin_left = 70  # Plus d'espace pour les labels Y avec devise
        chart_margin_right = 30
        chart_margin_bottom = 50
        chart_height = 280  # Ajusté pour laisser place au footer sur même page
        chart_width = max(400, landscape_content_width - (chart_margin_left + chart_margin_right))

        d = Drawing(landscape_content_width, chart_height + chart_margin_bottom + 40)
        lc = HorizontalLineChart()
        lc.x = chart_margin_left
        lc.y = chart_margin_bottom
        lc.height = chart_height
        lc.width = chart_width
        lc.data = [series_ca, series_rem, series_cre, series_esp, series_mar]
        lc.categoryAxis.categoryNames = labels
        lc.categoryAxis.labels.angle = 25
        lc.categoryAxis.labels.boxAnchor = 'ne'
        lc.valueAxis.valueMin = 0
        
        # Formater les labels de l'axe Y avec la devise
        class CurrencyAxisLabelFormatter:
            def __init__(self, currency):
                self.currency = currency or ''
            def __call__(self, value):
                # Formater avec espaces milliers et devise
                try:
                    formatted = f"{value:,.0f}".replace(",", " ")
                    return f"{formatted} {self.currency}".strip()
                except:
                    return str(value)
        
        lc.valueAxis.labelTextFormat = CurrencyAxisLabelFormatter(currency_symbol)
        
        # Couleurs/markers
        from reportlab.lib import colors
        lc.lines[0].strokeColor = colors.HexColor('#1976D2')  # CA
        lc.lines[1].strokeColor = colors.HexColor('#F39C12')  # Remises
        lc.lines[2].strokeColor = colors.HexColor('#E74C3C')  # Créances
        lc.lines[3].strokeColor = colors.HexColor('#9B59B6')  # Espèces
        lc.lines[4].strokeColor = colors.HexColor('#27AE60')  # Marge
        for i in range(len(lc.data)):
            lc.lines[i].symbol = makeMarker('Circle')

        d.add(lc)

        # Légende
        legend = Legend()
        legend.alignment = 'right'
        # Placer la légende dans le coin supérieur droit du dessin
        legend.x = chart_margin_left + chart_width - 10
        legend.y = chart_margin_bottom + chart_height
        legend.boxAnchor = 'ne'
        legend.columnMaximum = 1
        legend.colorNamePairs = [
            (lc.lines[0].strokeColor, "Chiffre d'affaires"),
            (lc.lines[1].strokeColor, "Remises"),
            (lc.lines[2].strokeColor, "Créances"),
            (lc.lines[3].strokeColor, "Espèces"),
            (lc.lines[4].strokeColor, "Marge"),
        ]
        d.add(legend)
        
        # Ajouter le texte "Informatisé par Ayanna Erp" directement dans le Drawing (en bas)
        from reportlab.graphics.shapes import String
        footer_text = f"Informatisé par Ayanna Erp © - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        footer_string = String(landscape_content_width / 2, 10, footer_text, 
                               textAnchor='middle', fontSize=9, fillColor=colors.grey)
        d.add(footer_string)

        story.append(d)
    except Exception as e:
        # En cas de problème de chart, on continue sans bloquer le PDF
        story.append(Paragraph(f"(Graphiques non disponibles) - Informatisé par Ayanna Erp © - {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['SmallInfo']))

    # Construire le PDF avec template paysage pour la page du graphique
    from reportlab.platypus import BaseDocTemplate
    
    # Reconstruire le document avec deux templates (portrait + paysage)
    doc2 = BaseDocTemplate(
        filename,
        pagesize=A4,
    )
    
    # Frame portrait (première page)
    frame_portrait = Frame(
        4*cm, 2*cm,
        A4[0] - 8*cm, A4[1] - 4*cm,
        id='portrait'
    )
    
    # Frame paysage (page graphique)
    landscape_page = landscape(A4)
    frame_landscape = Frame(
        2*cm, 2*cm,
        landscape_page[0] - 4*cm, landscape_page[1] - 4*cm,
        id='landscape'
    )
    
    template_portrait = PageTemplate(id='Portrait', frames=[frame_portrait], pagesize=A4)
    template_landscape = PageTemplate(id='Landscape', frames=[frame_landscape], pagesize=landscape_page)
    
    doc2.addPageTemplates([template_portrait, template_landscape])
    
    # Insérer la directive de changement de template avant le PageBreak du graphique
    # On reconstruit story avec NextPageTemplate
    story_final = []
    found_chart_break = False
    for i, elem in enumerate(story):
        if isinstance(elem, PageBreak) and not found_chart_break:
            # C'est le PageBreak avant le graphique
            story_final.append(NextPageTemplate('Landscape'))
            story_final.append(elem)
            found_chart_break = True
        else:
            story_final.append(elem)
    
    doc2.build(story_final)

    if logo_path and os.path.exists(logo_path):
        try:
            os.unlink(logo_path)
        except Exception:
            pass

    return filename