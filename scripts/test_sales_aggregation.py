import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ayanna_erp.modules.stock.controllers.inventaire_controller import InventaireController
from ayanna_erp.database.database_manager import DatabaseManager
from sqlalchemy import text

dbm = DatabaseManager()
with dbm.get_session() as session:
    # Trouver la dernière session d'inventaire avec items
    inv = session.execute(text("SELECT id, warehouse_id, completed_date, created_at FROM stock_inventaire ORDER BY id DESC LIMIT 1")).fetchone()
    if not inv:
        print('Aucune session d\'inventaire trouvée')
    else:
        inv_id = inv[0]
        wh_id = inv[1]
        datecol = inv[2] or inv[3]
        if datecol is None:
            print('La session n\'a pas de date associée, utiliser la date du jour')
        print('Testing inventory id:', inv_id, 'warehouse_id:', wh_id, 'date:', datecol)

        # Récupérer product_ids
        rows = session.execute(text('SELECT product_id FROM stock_inventaire_item WHERE inventory_id = :inv_id'), {'inv_id': inv_id}).fetchall()
        product_ids = [r[0] for r in rows]
        print('Product ids count:', len(product_ids))

        ctrl = InventaireController(1)
        sales_map = ctrl.get_sales_on_date(session, wh_id, product_ids, datecol.date() if hasattr(datecol, 'date') else None)
        print('Sales map sample (first 10):')
        for k in list(sales_map.keys())[:10]:
            print(k, sales_map[k])
