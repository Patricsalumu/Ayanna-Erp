import sys
sys.path.append('.')
from ayanna_erp.database.database_manager import DatabaseManager
from sqlalchemy import text

with DatabaseManager().get_session() as session:
    # Vérifier le service avec ID 1
    service_query = text('SELECT id, name, price, pos_id FROM shop_services WHERE id = 1')
    service = session.execute(service_query).fetchone()
    if service:
        print(f'Service ID 1: name="{service.name}", price={service.price}, pos_id={service.pos_id}')
    else:
        print('Service ID 1 n\'existe pas')

    # Vérifier tous les services pour tous les pos_id
    all_services_query = text('SELECT id, name, pos_id FROM shop_services ORDER BY id')
    all_services = session.execute(all_services_query).fetchall()
    print(f'\nTotal services: {len(all_services)}')
    for svc in all_services:
        print(f'  ID {svc.id}: pos_id={svc.pos_id}, "{svc.name}"')