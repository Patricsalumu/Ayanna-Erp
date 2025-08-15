"""
Contrôleur pour la gestion des clients du module Salle de Fête
Gère toutes les opérations CRUD pour les clients
"""

import sys
import os
from PyQt6.QtCore import QObject, pyqtSignal
from sqlalchemy.exc import IntegrityError
from datetime import datetime

# Ajouter le chemin vers le modèle
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from model.salle_fete import EventClient, get_database_manager


class ClientController(QObject):
    """Contrôleur pour la gestion des clients"""
    
    # Signaux pour la communication avec la vue
    client_added = pyqtSignal(object)  # Émet le client ajouté
    client_updated = pyqtSignal(object)  # Émet le client modifié
    client_deleted = pyqtSignal(int)  # Émet l'ID du client supprimé
    clients_loaded = pyqtSignal(list)  # Émet la liste des clients
    error_occurred = pyqtSignal(str)  # Émet un message d'erreur
    
    def __init__(self, pos_id=1):
        super().__init__()
        self.pos_id = pos_id
        
    def set_pos_id(self, pos_id):
        """Définir l'ID de l'entreprise"""
        self.pos_id = pos_id
        
    def create_client(self, client_data):
        """
        Créer un nouveau client
        
        Args:
            client_data (dict): Données du client
            
        Returns:
            EventClient: Le client créé ou None en cas d'erreur
        """
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            # Créer le nouveau client
            client = EventClient(
                pos_id=self.pos_id,
                nom=client_data.get('nom', ''),
                prenom=client_data.get('prenom', ''),
                telephone=client_data.get('telephone', ''),
                email=client_data.get('email', ''),
                adresse=client_data.get('adresse', ''),
                ville=client_data.get('ville', ''),
                code_postal=client_data.get('code_postal', ''),
                date_naissance=client_data.get('date_naissance'),
                type_client=client_data.get('type_client', 'Particulier'),
                source=client_data.get('source', ''),
                notes=client_data.get('notes', ''),
                is_active=client_data.get('is_active', True)
            )
            
            session.add(client)
            session.commit()
            
            # Rafraîchir l'objet pour avoir l'ID
            session.refresh(client)
            
            print(f"✅ Client créé: {client.prenom} {client.nom}")
            self.client_added.emit(client)
            return client
            
        except IntegrityError as e:
            session.rollback()
            error_msg = f"Erreur d'intégrité: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
            
        except Exception as e:
            session.rollback()
            error_msg = f"Erreur lors de la création du client: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
            
        finally:
            db_manager.close_session()
    
    def load_clients(self):
        """Charger tous les clients de l'entreprise"""
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            # Récupérer tous les clients
            clients = session.query(EventClient).filter(
                EventClient.pos_id == self.pos_id,
                EventClient.is_active == True
            ).order_by(EventClient.nom, EventClient.prenom).all()
            
            # Convertir en dictionnaires pour la vue
            clients_data = []
            for client in clients:
                clients_data.append({
                    'id': client.id,
                    'nom': client.nom or '',
                    'prenom': client.prenom or '',
                    'telephone': client.telephone or '',
                    'email': client.email or '',
                    'adresse': client.adresse or '',
                    'ville': client.ville or '',
                    'code_postal': client.code_postal or '',
                    'type_client': client.type_client or 'Particulier',
                    'source': client.source or '',
                    'notes': client.notes or '',
                    'is_active': client.is_active,
                    'created_at': client.created_at
                })
            
            print(f"✅ {len(clients_data)} clients chargés")
            self.clients_loaded.emit(clients_data)
            return clients_data
            
        except Exception as e:
            error_msg = f"Erreur lors du chargement des clients: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
            
        finally:
            db_manager.close_session()
            
    def get_client(self, client_id):
        """
        Récupérer un client par son ID
        
        Args:
            client_id (int): ID du client
            
        Returns:
            EventClient: Le client ou None si non trouvé
        """
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            client = session.query(EventClient).filter(
                EventClient.id == client_id,
                EventClient.pos_id == self.pos_id
            ).first()
            return client
            
        except Exception as e:
            error_msg = f"Erreur lors de la récupération du client: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
            
        finally:
            db_manager.close_session()
            
    def get_all_clients(self, active_only=True):
        """
        Récupérer tous les clients
        
        Args:
            active_only (bool): Si True, ne récupère que les clients actifs
            
        Returns:
            list: Liste des clients
        """
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            query = session.query(EventClient).filter(EventClient.pos_id == self.pos_id)
            
            if active_only:
                query = query.filter(EventClient.is_active == True)
                
            clients = query.order_by(EventClient.nom, EventClient.prenom).all()
            
            self.clients_loaded.emit(clients)
            return clients
            
        except Exception as e:
            error_msg = f"Erreur lors du chargement des clients: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
            
        finally:
            db_manager.close_session()
    
    def add_client(self, client_data):
        """Ajouter un nouveau client"""
        try:
            # Utiliser la méthode create_client existante
            client = self.create_client(client_data)
            if client:
                self.client_added.emit(client)
                return True
            return False
            
        except Exception as e:
            error_msg = f"Erreur lors de l'ajout du client: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
            
    def update_client(self, client_id, client_data):
        """
        Mettre à jour un client
        
        Args:
            client_id (int): ID du client à modifier
            client_data (dict): Nouvelles données du client
            
        Returns:
            EventClient: Le client modifié ou None en cas d'erreur
        """
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            client = session.query(EventClient).filter(
                EventClient.id == client_id,
                EventClient.pos_id == self.pos_id
            ).first()
            
            if not client:
                error_msg = f"Client avec l'ID {client_id} non trouvé"
                print(f"❌ {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
                
            # Mettre à jour les champs
            for field, value in client_data.items():
                if hasattr(client, field):
                    setattr(client, field, value)
                    
            session.commit()
            session.refresh(client)
            
            print(f"✅ Client modifié: {client.prenom} {client.nom}")
            self.client_updated.emit(client)
            return client
            
        except Exception as e:
            session.rollback()
            error_msg = f"Erreur lors de la modification du client: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
            
        finally:
            db_manager.close_session()
            
    def delete_client(self, client_id):
        """
        Supprimer un client (suppression logique)
        
        Args:
            client_id (int): ID du client à supprimer
            
        Returns:
            bool: True si succès, False sinon
        """
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            client = session.query(EventClient).filter(
                EventClient.id == client_id,
                EventClient.pos_id == self.pos_id
            ).first()
            
            if not client:
                error_msg = f"Client avec l'ID {client_id} non trouvé"
                print(f"❌ {error_msg}")
                self.error_occurred.emit(error_msg)
                return False
                
            # Suppression logique
            client.is_active = False
            session.commit()
            
            print(f"✅ Client désactivé: {client.prenom} {client.nom}")
            self.client_deleted.emit(client_id)
            return True
            
        except Exception as e:
            session.rollback()
            error_msg = f"Erreur lors de la suppression du client: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
            
        finally:
            db_manager.close_session()
            
    def search_clients(self, search_term):
        """
        Rechercher des clients par nom, prénom, téléphone ou email
        
        Args:
            search_term (str): Terme de recherche
            
        Returns:
            list: Liste des clients correspondants
        """
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            search_pattern = f"%{search_term}%"
            
            clients = session.query(EventClient).filter(
                EventClient.pos_id == self.pos_id,
                EventClient.is_active == True,
                (EventClient.nom.ilike(search_pattern) |
                 EventClient.prenom.ilike(search_pattern) |
                 EventClient.telephone.ilike(search_pattern) |
                 EventClient.email.ilike(search_pattern))
            ).order_by(EventClient.nom, EventClient.prenom).all()
            
            self.clients_loaded.emit(clients)
            return clients
            
        except Exception as e:
            error_msg = f"Erreur lors de la recherche: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
            
        finally:
            db_manager.close_session()
            
    def get_client_statistics(self):
        """
        Obtenir des statistiques sur les clients
        
        Returns:
            dict: Statistiques des clients
        """
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            total_clients = session.query(EventClient).filter(
                EventClient.pos_id == self.pos_id,
                EventClient.is_active == True
            ).count()
            
            clients_by_type = session.query(
                EventClient.type_client,
                session.query(EventClient).filter(
                    EventClient.pos_id == self.pos_id,
                    EventClient.is_active == True,
                    EventClient.type_client == EventClient.type_client
                ).count().label('count')
            ).filter(
                EventClient.pos_id == self.pos_id,
                EventClient.is_active == True
            ).group_by(EventClient.type_client).all()
            
            stats = {
                'total_clients': total_clients,
                'clients_by_type': {item[0]: item[1] for item in clients_by_type}
            }
            
            return stats
            
        except Exception as e:
            error_msg = f"Erreur lors du calcul des statistiques: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return {}
            
        finally:
            db_manager.close_session()
