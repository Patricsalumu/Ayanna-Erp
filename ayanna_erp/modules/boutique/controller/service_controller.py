"""
Contrôleur pour la gestion des services du module Boutique
Gère toutes les opérations CRUD pour les services (table shop_services)
"""

import sys
import os
from PyQt6.QtCore import QObject, pyqtSignal
from sqlalchemy.exc import IntegrityError
from datetime import datetime

# Import du modèle shop_services
from ayanna_erp.modules.boutique.model.models import ShopService
from ayanna_erp.database.database_manager import DatabaseManager


class ServiceController(QObject):
    """Contrôleur pour la gestion des services boutique"""
    
    # Signaux pour la communication avec la vue
    service_added = pyqtSignal(object)
    service_updated = pyqtSignal(object)
    service_deleted = pyqtSignal(int)
    services_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, pos_id=1):
        super().__init__()
        self.pos_id = pos_id
        self.db_manager = DatabaseManager()
        
    def set_pos_id(self, pos_id):
        """Définir l'ID de l'entreprise"""
        self.pos_id = pos_id
        
    def create_service(self, service_data):
        """
        Créer un nouveau service
        
        Args:
            service_data (dict): Données du service
            
        Returns:
            ShopService: Le service créé ou None
        """
        try:
            with self.db_manager.get_session() as session:
                service = ShopService(
                    pos_id=self.pos_id,
                    nom=service_data.get('nom', service_data.get('name', '')),
                    description=service_data.get('description', ''),
                    prix=float(service_data.get('prix', service_data.get('price', 0.0))),
                    actif=service_data.get('actif', service_data.get('is_active', True)),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                session.add(service)
                session.commit()
                session.refresh(service)
                
                print(f"✅ Service créé: {service.nom}")
                self.service_added.emit(service)
                return service
                
        except IntegrityError as e:
            error_msg = f"Erreur d'intégrité: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
            
        except Exception as e:
            error_msg = f"Erreur lors de la création du service: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
    
    def load_services(self):
        """Charger tous les services de l'entreprise"""
        try:
            with self.db_manager.get_session() as session:
                # Récupérer tous les services
                services = session.query(ShopService).filter(
                    ShopService.pos_id == self.pos_id
                ).order_by(ShopService.name).all()
                
                print(f"✅ {len(services)} services chargés")
                self.services_loaded.emit(services)
                return services
                
        except Exception as e:
            error_msg = f"Erreur lors du chargement des services: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
            
    def get_service(self, service_id):
        """Récupérer un service par ID"""
        try:
            with self.db_manager.get_session() as session:
                service = session.query(ShopService).filter(
                    ShopService.id == service_id,
                    ShopService.pos_id == self.pos_id
                ).first()
                return service
                
        except Exception as e:
            error_msg = f"Erreur lors de la récupération du service: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
            
    def get_all_services(self, active_only=True):
        """Récupérer tous les services"""
        try:
            with self.db_manager.get_session() as session:
                query = session.query(ShopService).filter(ShopService.pos_id == self.pos_id)
                
                if active_only:
                    query = query.filter(ShopService.is_active == True)
                    
                services = query.order_by(ShopService.name).all()
                
                self.services_loaded.emit(services)
                return services
                
        except Exception as e:
            error_msg = f"Erreur lors du chargement des services: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
            
    def update_service(self, service_id, service_data):
        """
        Mettre à jour un service existant
        
        Args:
            service_id (int): ID du service
            service_data (dict): Nouvelles données
            
        Returns:
            bool: True si succès
        """
        try:
            with self.db_manager.get_session() as session:
                service = session.query(ShopService).filter(
                    ShopService.id == service_id,
                    ShopService.pos_id == self.pos_id
                ).first()
                
                if not service:
                    self.error_occurred.emit("Service introuvable")
                    return False
                
                # Mettre à jour les champs
                service.nom = service_data.get('nom', service_data.get('name', service.nom))
                service.description = service_data.get('description', service.description)
                service.prix = float(service_data.get('prix', service_data.get('price', service.prix)))
                service.actif = service_data.get('actif', service_data.get('is_active', service.actif))
                service.updated_at = datetime.now()
                
                session.commit()
                session.refresh(service)
                
                print(f"✅ Service modifié: {service.nom}")
                self.service_updated.emit(service)
                return True
                
        except Exception as e:
            error_msg = f"Erreur lors de la modification du service: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
    
    def delete_service(self, service_id):
        """
        Supprimer un service
        
        Args:
            service_id (int): ID du service
            
        Returns:
            bool: True si succès
        """
        try:
            with self.db_manager.get_session() as session:
                service = session.query(ShopService).filter(
                    ShopService.id == service_id,
                    ShopService.pos_id == self.pos_id
                ).first()
                
                if not service:
                    self.error_occurred.emit("Service introuvable")
                    return False
                
                service_name = service.nom
                session.delete(service)
                session.commit()
                
                print(f"✅ Service supprimé: {service_name}")
                self.service_deleted.emit(service_id)
                return True
                
        except Exception as e:
            error_msg = f"Erreur lors de la suppression du service: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
    
    def search_services(self, query, active_only=True):
        """
        Rechercher des services
        
        Args:
            query (str): Terme de recherche
            active_only (bool): Seulement les services actifs
            
        Returns:
            list: Liste des services correspondants
        """
        try:
            with self.db_manager.get_session() as session:
                db_query = session.query(ShopService).filter(
                    ShopService.pos_id == self.pos_id
                )
                
                if active_only:
                    db_query = db_query.filter(ShopService.is_active == True)
                
                if query:
                    search_pattern = f"%{query}%"
                    db_query = db_query.filter(
                        (ShopService.name.ilike(search_pattern)) |
                        (ShopService.description.ilike(search_pattern))
                    )
                
                services = db_query.order_by(ShopService.name).all()
                return services
                
        except Exception as e:
            error_msg = f"Erreur lors de la recherche: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
    
    def get_services_statistics(self):
        """Récupérer les statistiques des services"""
        try:
            with self.db_manager.get_session() as session:
                # Total des services
                total = session.query(ShopService).filter(
                    ShopService.pos_id == self.pos_id
                ).count()
                
                # Services actifs
                active = session.query(ShopService).filter(
                    ShopService.pos_id == self.pos_id,
                    ShopService.actif == True
                ).count()
                
                # Prix moyen
                from sqlalchemy import func
                avg_price = session.query(func.avg(ShopService.prix)).filter(
                    ShopService.pos_id == self.pos_id,
                    ShopService.actif == True
                ).scalar() or 0
                
                return {
                    'total': total,
                    'active': active,
                    'inactive': total - active,
                    'average_price': float(avg_price)
                }
                
        except Exception as e:
            error_msg = f"Erreur lors du calcul des statistiques: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return {
                'total': 0,
                'active': 0,
                'inactive': 0,
                'average_price': 0.0
            }