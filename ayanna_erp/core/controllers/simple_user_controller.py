"""
Contrôleur adapté pour utiliser la structure User existante
"""

import sys
import os
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc, or_
from PyQt6.QtCore import QObject, pyqtSignal
import bcrypt

# Import du gestionnaire de base de données et des modèles existants
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from ayanna_erp.database.database_manager import DatabaseManager, User, Entreprise


class SimpleUserController(QObject):
    """Contrôleur adapté pour la structure User existante"""
    
    # Signaux pour la communication avec l'interface
    user_created = pyqtSignal(object)
    user_updated = pyqtSignal(object)
    user_deleted = pyqtSignal(int)
    users_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    authentication_result = pyqtSignal(bool, object)
    
    # Rôles disponibles (adaptés à la structure existante)
    ROLES = {
        'super_admin': 'Super Administrateur',
        'admin': 'Administrateur',
        'manager': 'Manager',
        'user': 'Utilisateur'
    }
    
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self._current_user = None
        
    def get_session(self):
        """Créer une nouvelle session de base de données"""
        return self.db_manager.get_session()
    
    def authenticate_user(self, username_or_email, password):
        """
        Authentifier un utilisateur avec la structure existante
        """
        try:
            session = self.get_session()
            
            # Chercher par nom ou email
            user = session.query(User).filter(
                or_(User.name == username_or_email, User.email == username_or_email)
            ).first()
            
            if not user:
                session.close()
                self.authentication_result.emit(False, None)
                return None
            
            # Vérifier le mot de passe avec bcrypt
            if user.check_password(password):
                user_info = {
                    'id': user.id,
                    'username': user.name,  # Adapter name -> username
                    'name': user.name,
                    'email': user.email,
                    'role': user.role,
                    'enterprise_id': user.enterprise_id,
                    'created_at': user.created_at
                }
                
                session.close()
                self._current_user = user_info
                self.authentication_result.emit(True, user_info)
                return user_info
            else:
                session.close()
                self.authentication_result.emit(False, None)
                return None
                
        except Exception as e:
            print(f"Erreur lors de l'authentification: {e}")
            self.error_occurred.emit(f"Erreur lors de l'authentification: {str(e)}")
            self.authentication_result.emit(False, None)
            return None
    
    def create_user(self, data, creator_role=None):
        """
        Créer un nouvel utilisateur avec la structure existante
        """
        try:
            session = self.get_session()
            
            # Vérifier si l'email existe déjà
            existing_user = session.query(User).filter(User.email == data['email']).first()
            
            if existing_user:
                session.close()
                self.error_occurred.emit("Email déjà utilisé")
                return None
            
            # Obtenir l'entreprise par défaut (la première disponible)
            enterprise = session.query(Entreprise).first()
            if not enterprise:
                session.close()
                self.error_occurred.emit("Aucune entreprise configurée")
                return None
            
            # Créer l'utilisateur
            user = User(
                enterprise_id=enterprise.id,
                name=data.get('username', data.get('name', '')),
                email=data['email'],
                role=data.get('role', 'user')
            )
            
            # Hasher le mot de passe
            user.set_password(data['password'])
            
            session.add(user)
            session.commit()
            
            user_info = {
                'id': user.id,
                'username': user.name,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'enterprise_id': user.enterprise_id,
                'created_at': user.created_at
            }
            
            session.close()
            self.user_created.emit(user_info)
            return user_info
            
        except Exception as e:
            print(f"Erreur lors de la création de l'utilisateur: {e}")
            self.error_occurred.emit(f"Erreur lors de la création de l'utilisateur: {str(e)}")
            return None
    
    def get_all_users(self, enterprise_id=None):
        """
        Récupérer tous les utilisateurs (filtrés par entreprise si spécifié)
        
        Args:
            enterprise_id (int, optional): ID de l'entreprise pour filtrer les utilisateurs
        """
        try:
            session = self.get_session()
            
            # Si un enterprise_id est fourni, filtrer par entreprise
            if enterprise_id:
                users = session.query(User).filter(User.enterprise_id == enterprise_id).order_by(desc(User.created_at)).all()
            else:
                users = session.query(User).order_by(desc(User.created_at)).all()
            
            session.close()
            
            result = []
            for user in users:
                result.append({
                    'id': user.id,
                    'username': user.name,
                    'name': user.name,
                    'email': user.email,
                    'role': user.role,
                    'role_display': self.ROLES.get(user.role, user.role),
                    'enterprise_id': user.enterprise_id,
                    'created_at': user.created_at,
                    'is_active': True  # Par défaut actif dans l'ancien modèle
                })
            
            self.users_loaded.emit(result)
            return result
            
        except Exception as e:
            print(f"Erreur lors de la récupération des utilisateurs: {e}")
            self.error_occurred.emit(f"Erreur lors de la récupération des utilisateurs: {str(e)}")
            return []
    
    def get_current_user(self):
        """Récupérer l'utilisateur actuellement connecté"""
        return self._current_user
    
    def has_permission(self, user_role, required_role):
        """Vérifier si un utilisateur a les permissions requises"""
        role_hierarchy = {
            'super_admin': 4,
            'admin': 3,
            'manager': 2,
            'user': 1
        }
        
        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    def create_default_admin(self):
        """Créer un administrateur par défaut avec la structure existante"""
        try:
            session = self.get_session()
            
            # Vérifier s'il y a déjà un super admin
            admin_exists = session.query(User).filter(User.role == 'super_admin').first()
            
            if not admin_exists:
                # Obtenir l'entreprise par défaut
                enterprise = session.query(Entreprise).first()
                if not enterprise:
                    session.close()
                    print("Aucune entreprise trouvée pour créer l'admin")
                    return False
                
                # Créer l'admin
                admin_data = {
                    'username': 'admin',
                    'email': 'admin@ayanna-erp.com',
                    'password': 'admin123',
                    'role': 'super_admin'
                }
                
                session.close()
                result = self.create_user(admin_data, 'super_admin')
                return result is not None
            
            session.close()
            return False
            
        except Exception as e:
            print(f"Erreur lors de la création de l'admin par défaut: {e}")
            self.error_occurred.emit(f"Erreur lors de la création de l'admin par défaut: {str(e)}")
            return False