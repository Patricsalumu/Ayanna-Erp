"""
Contrôleur pour la gestion du calendrier des événements
Gère l'affichage du calendrier et des événements associés
"""

from PyQt6.QtCore import QObject, pyqtSignal, QDate
from datetime import datetime, timedelta
from ayanna_erp.database.database_manager import get_database_manager
from ayanna_erp.modules.salle_fete.model.salle_fete import EventReservation


class CalendrierController(QObject):
    """Contrôleur pour la gestion du calendrier"""
    
    # Signaux
    events_loaded = pyqtSignal(list)  # Liste des événements chargés
    event_details_loaded = pyqtSignal(dict)  # Détails d'un événement spécifique
    error_occurred = pyqtSignal(str)  # Signal d'erreur
    
    def __init__(self, pos_id=1):
        super().__init__()
        self.pos_id = pos_id
    
    def get_events_for_month(self, year, month):
        """
        Récupérer tous les événements d'un mois donné
        
        Args:
            year (int): Année
            month (int): Mois (1-12)
            
        Returns:
            dict: Dictionnaire avec date comme clé et liste d'événements comme valeur
        """
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            # Calculer le début et la fin du mois
            start_date = datetime(year, month, 1)
            if month == 12:
                # Fin du mois de décembre = 31/12 23:59:59
                end_date = datetime(year, 12, 31, 23, 59, 59)
            else:
                # Dernier jour du mois à 23:59:59
                next_month_start = datetime(year, month + 1, 1)
                last_day = next_month_start - timedelta(days=1)
                end_date = datetime(last_day.year, last_day.month, last_day.day, 23, 59, 59)
            
            # Requête pour récupérer les événements du mois
            events = session.query(EventReservation).filter(
                EventReservation.pos_id == self.pos_id,
                EventReservation.event_date >= start_date,
                EventReservation.event_date <= end_date
            ).order_by(EventReservation.event_date).all()
            
            # Organiser les événements par date
            events_by_date = {}
            for event in events:
                event_date = event.event_date.date()
                if event_date not in events_by_date:
                    events_by_date[event_date] = []
                
                events_by_date[event_date].append({
                    'id': event.id,
                    'client_name': event.get_client_name(),
                    'theme': event.theme or '',
                    'event_type': event.event_type or '',
                    'status': event.status,
                    'datetime': event.event_date,
                    'guests_count': event.guests_count
                })
            
            session.close()
            print(f"📅 Événements chargés pour {month}/{year}: {len(events)} événements")
            return events_by_date
            
        except Exception as e:
            error_msg = f"Erreur lors du chargement des événements: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return {}
    
    def get_upcoming_events(self, limit=7):
        """
        Récupérer les prochains événements à venir
        
        Args:
            limit (int): Nombre maximum d'événements à retourner
            
        Returns:
            list: Liste des prochains événements
        """
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            # Requête pour les événements futurs
            now = datetime.now()
            upcoming_events = session.query(EventReservation).filter(
                EventReservation.pos_id == self.pos_id,
                EventReservation.event_date >= now,
                EventReservation.status.in_(['draft', 'confirmed', 'En attente', 'Annulée', 'Annuller', 'Confirmée'])
            ).order_by(EventReservation.event_date).limit(limit).all()
            
            events_data = []
            for event in upcoming_events:
                events_data.append({
                    'id': event.id,
                    'client_name': event.get_client_name(),
                    'theme': event.theme or '',
                    'event_type': event.event_type or '',
                    'status': event.status,
                    'datetime': event.event_date,
                    'guests_count': event.guests_count,
                    'phone': event.client_telephone or (event.client.telephone if event.client else '')
                })
            
            session.close()
            print(f"📋 Prochains événements chargés: {len(events_data)} événements")
            self.events_loaded.emit(events_data)
            return events_data
            
        except Exception as e:
            error_msg = f"Erreur lors du chargement des événements à venir: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
    
    def get_event_details(self, event_id):
        """
        Récupérer les détails d'un événement spécifique
        
        Args:
            event_id (int): ID de l'événement
            
        Returns:
            dict: Détails de l'événement
        """
        try:
            # Utiliser la méthode du contrôleur de réservation
            from ayanna_erp.modules.salle_fete.controller.reservation_controller import ReservationController
            
            reservation_controller = ReservationController(self.pos_id)
            reservation_details = reservation_controller.get_reservation(event_id)
            
            if reservation_details:
                # Extraire les informations demandées depuis le format retourné par get_reservation
                details = {
                    'id': reservation_details['id'],
                    'client_name': reservation_details.get('client_nom', ''),
                    'phone': reservation_details.get('client_telephone', ''),
                    'event_type': reservation_details.get('event_type', ''),
                    'theme': reservation_details.get('theme', ''),
                    'status': reservation_details.get('status', ''),
                    'datetime': reservation_details.get('event_date'),
                    'guests_count': reservation_details.get('guests_count', 0)
                }
                
                print(f"📋 Détails de l'événement {event_id} chargés")
                self.event_details_loaded.emit(details)
                return details
            else:
                error_msg = f"Événement {event_id} non trouvé"
                self.error_occurred.emit(error_msg)
                return None
                
        except Exception as e:
            error_msg = f"Erreur lors du chargement des détails de l'événement: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
    
    def get_events_for_date(self, date):
        """
        Récupérer les événements pour une date spécifique
        
        Args:
            date (QDate ou datetime.date): Date à vérifier
            
        Returns:
            list: Liste des événements pour cette date
        """
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            # Convertir QDate en datetime si nécessaire
            if hasattr(date, 'toPyDate'):
                target_date = date.toPyDate()
            else:
                target_date = date
            
            # Requête pour les événements de cette date
            start_datetime = datetime.combine(target_date, datetime.min.time())
            end_datetime = datetime.combine(target_date, datetime.max.time())
            
            events = session.query(EventReservation).filter(
                EventReservation.pos_id == self.pos_id,
                EventReservation.event_date >= start_datetime,
                EventReservation.event_date <= end_datetime
            ).order_by(EventReservation.event_date).all()
            
            events_data = []
            for event in events:
                events_data.append({
                    'id': event.id,
                    'client_name': event.get_client_name(),
                    'theme': event.theme or '',
                    'event_type': event.event_type or '',
                    'status': event.status,
                    'datetime': event.event_date,
                    'guests_count': event.guests_count,
                    'phone': event.client_telephone or (event.client.telephone if event.client else '')
                })
            
            session.close()
            print(f"📅 Événements pour {target_date}: {len(events_data)} événements")
            return events_data
            
        except Exception as e:
            error_msg = f"Erreur lors du chargement des événements de la date: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
    
    def get_calendar_color_for_status(self, status):
        """
        Retourner la couleur appropriée pour le statut d'un événement
        
        Args:
            status (str): Statut de l'événement
            
        Returns:
            str: Code couleur CSS
        """
        status_colors = {
            'draft': '#F39C12',        # Orange pour en attente
            'En attente': '#F39C12',   # Orange pour en attente
            'confirmed': '#27AE60',    # Vert pour confirmé
            'Confirmée': '#27AE60',    # Vert pour confirmé
            'cancelled': '#E74C3C',    # Rouge pour annulé
            'Annulée': '#E74C3C',      # Rouge pour annulé
            'completed': '#3498DB',    # Bleu pour terminé/passé
            'Terminée': '#3498DB'      # Bleu pour terminé/passé
        }
        
        return status_colors.get(status, '#95A5A6')  # Gris par défaut
