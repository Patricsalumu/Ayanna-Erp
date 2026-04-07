import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ayanna_erp.database.database_manager import get_database_manager
from ayanna_erp.modules.core.models import CoreProduct

db = get_database_manager()
session = db.get_session()
prods = session.query(CoreProduct).order_by(CoreProduct.id.asc()).all()
print(f"Total core_products: {len(prods)}")
for p in prods:
    print(f"id={p.id} name={p.name!r} entreprise_id={p.entreprise_id} category_id={p.category_id} price={getattr(p,'price_unit',None)} image={getattr(p,'image',None)}")
session.close()
