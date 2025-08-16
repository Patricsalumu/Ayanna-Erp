"""
Contrôleur pour la gestion des services du module Salle de Fête
Gère toutes les opérations CRUD pour les services
"""

import sys
import os
from PyQt6.QtCore import QObject, pyqtSignal
from sqlalchemy.exc import IntegrityError

# Ajouter le chemin vers le modèle
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ayanna_erp.modules.salle_fete.model.salle_fete import EventService, get_database_manager


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
                account_id=service_data.get('account_id'),
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
            
            # Convertir en dictionnaires pour la vue
            services_data = []
            for service in services:
                services_data.append({
                    'id': service.id,
                    'name': service.name or '',
                    'description': service.description or '',
                    'category': getattr(service, 'category', ''),  # Si le champ existe
                    'cost': float(service.cost or 0),
                    'price': float(service.price or 0),
                    'is_active': service.is_active,
                    'created_at': service.created_at
                })
            
            print(f"✅ {len(services_data)} services chargés")
            self.services_loaded.emit(services_data)
            return services_data
            
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
