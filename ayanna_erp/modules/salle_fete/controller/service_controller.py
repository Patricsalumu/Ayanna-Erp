"""
Contrôleur pour la gestion des services du module Salle de Fête
Gère toutes les opérations CRUD pour les services
"""

import sys
import os
from PyQt6.QtCore import QObject, pyqtSignal
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text, literal

# Ajouter le chemin vers le modèle
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ayanna_erp.modules.salle_fete.model.salle_fete import EventService, EventReservation, EventReservationService, get_database_manager
from ayanna_erp.modules.boutique.model.models import ShopPanier, ShopPanierService, ShopClient, ShopService


class ServiceController(QObject):
    """Contrôleur pour la gestion des services"""
    
    # Signaux pour la communication avec la vue
    service_added = pyqtSignal(object)
    service_updated = pyqtSignal(object)
    service_deleted = pyqtSignal(int)
    services_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, pos_id=1):
        super().__init__()
        self.pos_id = pos_id
        
    def set_pos_id(self, pos_id):
        """Définir l'ID de l'entreprise"""
        self.pos_id = pos_id
        
    def create_service(self, service_data):
        """
        Créer un nouveau service
        
        Args:
            service_data (dict): Données du service
            
        Returns:
            EventService: Le service créé ou None
        """
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            
            service = EventService(
                pos_id=self.pos_id,
                name=service_data.get('name', ''),
                description=service_data.get('description', ''),
                cost=service_data.get('cost', 0.0),
                price=service_data.get('price', 0.0),
                compte_produit_id=service_data.get('compte_produit_id'),
                compte_charge_id=service_data.get('compte_charge_id'),
                is_active=service_data.get('is_active', True)
            )
            
            session.add(service)
            session.commit()
            session.refresh(service)
            
            print(f"✅ Service créé: {service.name}")
            self.service_added.emit(service)
            return service
            
        except IntegrityError as e:
            session.rollback()
            error_msg = f"Erreur d'intégrité: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
            
        except Exception as e:
            session.rollback()
            error_msg = f"Erreur lors de la création du service: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
            
        finally:
            db_manager.close_session()
    
    def load_services(self):
        """Charger tous les services de l'entreprise"""
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            
            # Récupérer tous les services
            services = session.query(EventService).filter(
                EventService.pos_id == self.pos_id
            ).order_by(EventService.name).all()
            
            print(f"✅ {len(services)} services chargés")
            self.services_loaded.emit(services)
            return services
            
        except Exception as e:
            error_msg = f"Erreur lors du chargement des services: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
            
        finally:
            db_manager.close_session()
            
    def get_service(self, service_id):
        """Récupérer un service par ID"""
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            service = session.query(EventService).filter(
                EventService.id == service_id,
                EventService.pos_id == self.pos_id
            ).first()
            return service
            
        except Exception as e:
            error_msg = f"Erreur lors de la récupération du service: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
            
        finally:
            db_manager.close_session()
            
    def get_all_services(self, active_only=True):
        """Récupérer tous les services"""
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            query = session.query(EventService).filter(EventService.pos_id == self.pos_id)
            
            if active_only:
                query = query.filter(EventService.is_active == True)
                
            services = query.order_by(EventService.name).all()
            
            self.services_loaded.emit(services)
            return services
            
        except Exception as e:
            error_msg = f"Erreur lors du chargement des services: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
            
        finally:
            db_manager.close_session()
            
    def add_service(self, service_data):
        """Ajouter un nouveau service"""
        try:
            # Utiliser la méthode create_service existante
            service = self.create_service(service_data)
            if service:
                self.service_added.emit(service)
                return True
            return False
            
        except Exception as e:
            error_msg = f"Erreur lors de l'ajout du service: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
            
    def update_service(self, service_id, service_data):
        """Mettre à jour un service"""
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            service = session.query(EventService).filter(
                EventService.id == service_id,
                EventService.pos_id == self.pos_id
            ).first()
            
            if not service:
                error_msg = f"Service avec l'ID {service_id} non trouvé"
                self.error_occurred.emit(error_msg)
                return None
                
            # Mettre à jour les champs
            for field, value in service_data.items():
                if hasattr(service, field):
                    setattr(service, field, value)
                    
            session.commit()
            session.refresh(service)
            
            print(f"✅ Service modifié: {service.name}")
            self.service_updated.emit(service)
            return service
            
        except Exception as e:
            session.rollback()
            error_msg = f"Erreur lors de la modification du service: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
            
        finally:
            db_manager.close_session()
            
    def delete_service(self, service_id):
        """Supprimer un service (suppression logique)"""
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            service = session.query(EventService).filter(
                EventService.id == service_id,
                EventService.pos_id == self.pos_id
            ).first()
            
            if not service:
                error_msg = f"Service avec l'ID {service_id} non trouvé"
                self.error_occurred.emit(error_msg)
                return False
                
            # Suppression logique
            service.is_active = False
            session.commit()
            
            print(f"✅ Service désactivé: {service.name}")
            self.service_deleted.emit(service_id)
            return True
            
        except Exception as e:
            session.rollback()
            error_msg = f"Erreur lors de la suppression du service: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
            
        finally:
            db_manager.close_session()
            
    def search_services(self, search_term):
        """Rechercher des services par nom ou description"""
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            search_pattern = f"%{search_term}%"
            
            services = session.query(EventService).filter(
                EventService.pos_id == self.pos_id,
                EventService.is_active == True,
                (EventService.name.ilike(search_pattern) |
                 EventService.description.ilike(search_pattern))
            ).order_by(EventService.name).all()
            
            self.services_loaded.emit(services)
            return services
            
        except Exception as e:
            error_msg = f"Erreur lors de la recherche: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
            
        finally:
            db_manager.close_session()
            
    def calculate_margin(self, service_id):
        """Calculer la marge d'un service"""
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            service = session.query(EventService).filter(
                EventService.id == service_id,
                EventService.pos_id == self.pos_id
            ).first()
            
            if service and service.cost > 0:
                margin_amount = service.price - service.cost
                margin_percent = (margin_amount / service.cost) * 100
                return {
                    'margin_amount': margin_amount,
                    'margin_percent': margin_percent,
                    'cost': service.cost,
                    'price': service.price
                }
            return None
            
        except Exception as e:
            error_msg = f"Erreur lors du calcul de la marge: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
            
        finally:
            db_manager.close_session()
    
    def get_service_usage_statistics(self, service_id):
        """
        Récupère les statistiques d'utilisation pour un service donné
        Inclut les données des événements (salle de fête) et de la boutique
        Retourne: dict avec total_uses, total_quantity, total_revenue, average_quantity, last_used
        """
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            # Récupérer le nom du service pour faire correspondre avec les services boutique
            event_service = session.query(EventService).filter(EventService.id == service_id).first()
            if not event_service:
                return {
                    'total_uses': 0,
                    'total_quantity': 0,
                    'total_revenue': 0.0,
                    'average_quantity': 0.0,
                    'last_used': None
                }
            
            # Données des événements (salle de fête)
            event_usage_data = (session.query(
                    EventReservationService.quantity,
                    (EventReservationService.quantity * EventReservationService.unit_price).label('revenue'),
                    EventReservation.event_date
                )
                .join(EventReservation, EventReservationService.reservation_id == EventReservation.id)
                .filter(EventReservationService.service_id == service_id)
                .all()
            )
            
            # Données de la boutique - chercher les services avec le même ID (services partagés)
            shop_usage_data = (session.query(
                    ShopPanierService.quantity,
                    (ShopPanierService.quantity * ShopPanierService.price_unit).label('revenue'),
                    ShopPanier.created_at.label('event_date')
                )
                .join(ShopPanier, ShopPanierService.panier_id == ShopPanier.id)
                .filter(ShopPanierService.service_id == service_id, ShopPanier.status.in_(['validé', 'payé', 'completed']))
                .all()
            )
            
            # Combiner les données
            all_usage_data = event_usage_data + shop_usage_data
            
            if not all_usage_data:
                return {
                    'total_uses': 0,
                    'total_quantity': 0,
                    'total_revenue': 0.0,
                    'average_quantity': 0.0,
                    'last_used': None
                }
            
            # Calcul des statistiques
            total_uses = len(all_usage_data)
            total_quantity = sum(float(usage.quantity) for usage in all_usage_data)
            total_revenue = sum(float(usage.revenue) for usage in all_usage_data)
            average_quantity = total_quantity / total_uses if total_uses > 0 else 0.0
            last_used = max(usage.event_date for usage in all_usage_data)
            
            return {
                'total_uses': total_uses,
                'total_quantity': total_quantity,
                'total_revenue': total_revenue,
                'average_quantity': round(average_quantity, 2),
                'last_used': last_used
            }
            
        except Exception as e:
            error_msg = f"Erreur lors de la récupération des statistiques: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
            
        finally:
            db_manager.close_session()
    
    def get_service_recent_usage(self, service_id, limit=10):
        """
        Récupère les dernières utilisations d'un service
        Inclut les données des événements (salle de fête) et de la boutique
        Retourne: liste des dernières utilisations avec date, client et quantité
        """
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            # Récupérer le nom du service pour faire correspondre avec les services boutique
            event_service = session.query(EventService).filter(EventService.id == service_id).first()
            if not event_service:
                return []
            
            # Données des événements (salle de fête)
            event_usage = (session.query(
                    EventReservation.event_date,
                    EventReservation.client_nom.label('nom'),
                    EventReservation.client_prenom.label('prenom'),
                    EventReservation.client_telephone.label('telephone'),
                    EventReservationService.quantity,
                    EventReservationService.unit_price,
                    EventReservationService.reservation_id.label('reference_id'),
                                        literal('event').label('source')  # Pour identifier la source
                )
                .join(EventReservationService, EventReservation.id == EventReservationService.reservation_id)
                .filter(EventReservationService.service_id == service_id)
                .all()
            )
            
            # Convertir en dictionnaires pour éviter les problèmes de mélange d'objets
            event_dicts = []
            for usage in event_usage:
                event_dicts.append({
                    'event_date': usage.event_date,
                    'nom': usage.nom,
                    'prenom': usage.prenom,
                    'telephone': usage.telephone,
                    'quantity': usage.quantity,
                    'unit_price': usage.unit_price,
                    'reference_id': usage.reference_id,
                    'source': usage.source
                })
            
            # Données de la boutique - chercher les services avec le même ID (services partagés)
            shop_usage = (session.query(
                    ShopPanier.created_at.label('event_date'),
                    ShopClient.nom,
                    ShopClient.prenom,
                    ShopClient.telephone,
                    ShopPanierService.quantity,
                    ShopPanierService.price_unit,
                    ShopPanier.id.label('reference_id'),
                    literal('shop').label('source')
                )
                .join(ShopPanierService, ShopPanier.id == ShopPanierService.panier_id)
                .outerjoin(ShopClient, ShopPanier.client_id == ShopClient.id)
                .filter(ShopPanierService.service_id == service_id, ShopPanier.status.in_(['validé', 'payé', 'completed']))
                .all()
            )
            
            # Convertir en dictionnaires
            shop_dicts = []
            for usage in shop_usage:
                shop_dicts.append({
                    'event_date': usage.event_date,
                    'nom': usage.nom,
                    'prenom': usage.prenom,
                    'telephone': usage.telephone,
                    'quantity': usage.quantity,
                    'unit_price': usage.price_unit,  # Renommé pour uniformité
                    'reference_id': usage.reference_id,
                    'source': usage.source
                })
            
            # Combiner et trier par date décroissante
            all_usage = event_dicts + shop_dicts
            all_usage_sorted = sorted(all_usage, key=lambda x: x['event_date'], reverse=True)[:limit]
            
            # Formatage des résultats
            usage_list = []
            for usage in all_usage_sorted:
                client_name = f"{usage['nom'] or ''} {usage['prenom'] or ''}".strip() or "Client non spécifié"
                usage_list.append({
                    'event_date': usage['event_date'],
                    'client_name': client_name,
                    'client_telephone': usage['telephone'],
                    'quantity': float(usage['quantity']),
                    'unit_price': float(usage['unit_price']),
                    'total_line': float(usage['quantity']) * float(usage['unit_price']),
                    'source': usage['source'],
                    'reference_id': usage['reference_id']
                })
            
            return usage_list
            
        except Exception as e:
            error_msg = f"Erreur lors de la récupération des dernières utilisations: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
            
        finally:
            db_manager.close_session()
