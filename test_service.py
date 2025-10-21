import sys
sys.path.insert(0, r'c:\Ayanna ERP\Ayanna-Erp')
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.salle_fete.model.salle_fete import EventService, EventReservation, EventReservationService
from sqlalchemy import text, literal

dm = DatabaseManager()
session = dm.get_session()

print("Testing complex event query...")
try:
    event_usage = (session.query(
            EventReservation.event_date,
            EventReservation.client_nom.label('nom'),
            EventReservation.client_prenom.label('prenom'),
            EventReservation.client_telephone.label('telephone'),
            EventReservationService.quantity,
            EventReservationService.unit_price,
            EventReservationService.reservation_id.label('reference_id'),
            literal('event').label('source')
        )
        .join(EventReservationService, EventReservation.id == EventReservationService.reservation_id)
        .filter(EventReservationService.service_id == 1)
        .all()
    )
    print(f"Event usage count: {len(event_usage)}")
    if event_usage:
        print(f"First result attributes: {dir(event_usage[0])}")
        print(f"Sample: event_date={event_usage[0].event_date}, nom={event_usage[0].nom}, source={event_usage[0].source}")
    
except Exception as e:
    print(f"Event query error: {e}")
    import traceback
    traceback.print_exc()

session.close()