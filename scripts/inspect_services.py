from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.boutique.model.models import ShopService
from ayanna_erp.modules.salle_fete.model.salle_fete import EventService

db = DatabaseManager(database_url='sqlite:///ayanna_erp.db')
s = db.get_session()

print('---- shop_services ----')
for s in s.query(ShopService).order_by(ShopService.id).all():
    print({'id': s.id, 'name': getattr(s,'name',None), 'price': float(getattr(s,'price',0)), 'pos_id': getattr(s,'pos_id',None)})

print('\n---- event_services ----')
for e in s.query(EventService).order_by(EventService.id).all():
    print({'id': e.id, 'name': getattr(e,'name',None), 'price': float(getattr(e,'price',0)), 'pos_id': getattr(e,'pos_id',None)})

s.close()
