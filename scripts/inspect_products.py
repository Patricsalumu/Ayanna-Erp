import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ayanna_erp.modules.restaurant.controllers.catalogue_controller import CatalogueController

for pos in range(1,5):
    print(f"\n--- POS {pos} ---")
    ctrl = CatalogueController(entreprise_id=1, pos_id=pos)
    try:
        cats = ctrl.list_categories()
        print(f"Categories: {len(cats)}")
        for c in cats:
            print(f" - {getattr(c,'id',None)}: {getattr(c,'name',None)}")
    except Exception as e:
        print(f"Failed to list categories for pos {pos}: {e}")
    try:
        prods = ctrl.list_products()
        print(f"Products: {len(prods)}")
        for p in prods[:10]:
            print(f"  - {getattr(p,'id',None)} | {getattr(p,'name',None)} | price:{getattr(p,'price_unit',getattr(p,'price',None))} | cat:{getattr(p,'category_id',None)}")
    except Exception as e:
        print(f"Failed to list products for pos {pos}: {e}")
