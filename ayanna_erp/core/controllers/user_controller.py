"""
Contrôleur pour la gestion des utilisateurs
Gère la création, modification, suppression et authentification des utilisateurs
"""

import sys
import os
import hashlib
import secrets
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc, or_
from PyQt6.QtCore import QObject, pyqtSignal

# Import du gestionnaire de base de données et des modèles
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from ayanna_erp.database.database_manager import DatabaseManager, User


class UserController(QObject):
    """Contrôleur pour la gestion des utilisateurs"""
    
    # Signaux pour la communication avec l'interface
    user_created = pyqtSignal(object)
    user_updated = pyqtSignal(object)
    user_deleted = pyqtSignal(int)
    users_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    authentication_result = pyqtSignal(bool, object)
    
    # Rôles disponibles
    ROLES = {
        'super_admin': 'Super Administrateur',
        'admin': 'Administrateur',
        'manager': 'Manager',
        'user': 'Utilisateur',
        'guest': 'Invité'
    }
    
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self._current_user = None
        
    def get_session(self):
        """Créer une nouvelle session de base de données"""
        return self.db_manager.get_session()
    
    def hash_password(self, password):
        """
        Hasher un mot de passe avec salt
        
        Args:
            password (str): Mot de passe en clair
            
        Returns:
            tuple: (hashed_password, salt)
        """
        # Générer un salt unique
        salt = secrets.token_hex(32)
        
        # Hasher le mot de passe avec le salt
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # 100,000 iterations
        )
        
        return password_hash.hex(), salt
    
    def verify_password(self, password, hashed_password, salt):
        """
        Vérifier un mot de passe
        
        Args:
            password (str): Mot de passe en clair
            hashed_password (str): Mot de passe hashé
            salt (str): Salt utilisé
            
        Returns:
            bool: True si le mot de passe est correct
        """
        try:
            # Recalculer le hash avec le salt stocké
            password_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            )
            
            return password_hash.hex() == hashed_password
        except Exception as e:
            print(f"Erreur lors de la vérification du mot de passe: {e}")
            return False
    
    def authenticate_user(self, username, password):
        """
        Authentifier un utilisateur
        
        Args:
            username (str): Nom d'utilisateur ou email
            password (str): Mot de passe
            
        Returns:
            dict: Informations utilisateur ou None si échec
        """
        try:
            session = self.get_session()
            
            # Chercher par username ou email
            user = session.query(User).filter(
                or_(User.username == username, User.email == username)
            ).first()
            
            if not user:
                session.close()
                self.authentication_result.emit(False, None)
                return None
            
            # Vérifier si l'utilisateur est actif
            if not user.is_active:
                session.close()
                self.error_occurred.emit("Compte utilisateur désactivé")
                self.authentication_result.emit(False, None)
                return None
            
            # Vérifier le mot de passe
            if self.verify_password(password, user.password_hash, user.salt):
                # Mettre à jour la dernière connexion
                user.last_login = datetime.now()
                session.commit()
                
                user_info = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role,
                    'is_active': user.is_active,
                    'created_at': user.created_at,
                    'last_login': user.last_login
                }
                
                session.close()
                self._current_user = user_info
                # Suppression de l'appel à set_current_user (obsolète)
                self.authentication_result.emit(True, user_info)
                return user_info
            else:
                session.close()
                self.authentication_result.emit(False, None)
                return None
                
        except Exception as e:
            self.error_occurred.emit(f"Erreur lors de l'authentification: {str(e)}")
            self.authentication_result.emit(False, None)
            return None
    
    def create_user(self, data, creator_role=None):
        """
        Créer un nouvel utilisateur
        
        Args:
            data (dict): Données utilisateur
            creator_role (str): Rôle de l'utilisateur qui crée (pour vérification des permissions)
            
        Returns:
            dict: Informations de l'utilisateur créé ou None
        """
        try:
            # Vérification des permissions pour la création d'entreprise
            if data.get('role') == 'super_admin' and creator_role != 'super_admin':
                self.error_occurred.emit("Seul un super administrateur peut créer d'autres super administrateurs")
                return None
            
            session = self.get_session()
            
            # Vérifier si le nom d'utilisateur existe déjà
            existing_user = session.query(User).filter(
                or_(User.username == data['username'], User.email == data['email'])
            ).first()
            
            if existing_user:
                session.close()
                self.error_occurred.emit("Nom d'utilisateur ou email déjà utilisé")
                return None
            
            # Hasher le mot de passe
            password_hash, salt = self.hash_password(data['password'])
            
            # Créer l'utilisateur
            user = User(
                username=data['username'],
                email=data['email'],
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                password_hash=password_hash,
                salt=salt,
                role=data.get('role', 'user'),
                is_active=data.get('is_active', True)
            )
            
            session.add(user)
            session.commit()
            
            user_info = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'is_active': user.is_active,
                'created_at': user.created_at,
                'last_login': user.last_login
            }
            
            session.close()
            self.user_created.emit(user_info)
            return user_info
            
        except Exception as e:
            self.error_occurred.emit(f"Erreur lors de la création de l'utilisateur: {str(e)}")
            return None
    
    def update_user(self, user_id, data, updater_role=None):
        """
        Mettre à jour un utilisateur
        
        Args:
            user_id (int): ID de l'utilisateur
            data (dict): Données à mettre à jour
            updater_role (str): Rôle de l'utilisateur qui modifie
            
        Returns:
            bool: True si la mise à jour a réussi
        """
        try:
            session = self.get_session()
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                session.close()
                self.error_occurred.emit("Utilisateur non trouvé")
                return False
            
            # Vérifications de permissions
            if 'role' in data and data['role'] == 'super_admin' and updater_role != 'super_admin':
                session.close()
                self.error_occurred.emit("Seul un super administrateur peut attribuer le rôle super administrateur")
                return False
            
            # Mettre à jour les champs autorisés
            allowed_fields = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active']
            for key, value in data.items():
                if key in allowed_fields and hasattr(user, key):
                    setattr(user, key, value)
            
            # Mettre à jour le mot de passe si fourni
            if 'password' in data and data['password']:
                password_hash, salt = self.hash_password(data['password'])
                user.password_hash = password_hash
                user.salt = salt
            
            session.commit()
            
            user_info = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'is_active': user.is_active,
                'created_at': user.created_at,
                'last_login': user.last_login
            }
            
            session.close()
            self.user_updated.emit(user_info)
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Erreur lors de la mise à jour de l'utilisateur: {str(e)}")
            return False
    
    def delete_user(self, user_id, deleter_role=None):
        """
        Supprimer un utilisateur
        
        Args:
            user_id (int): ID de l'utilisateur
            deleter_role (str): Rôle de l'utilisateur qui supprime
            
        Returns:
            bool: True si la suppression a réussi
        """
        try:
            if user_id == 1:
                self.error_occurred.emit("Impossible de supprimer l'utilisateur principal")
                return False
            
            session = self.get_session()
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                session.close()
                self.error_occurred.emit("Utilisateur non trouvé")
                return False
            
            # Vérifier les permissions
            if user.role == 'super_admin' and deleter_role != 'super_admin':
                session.close()
                self.error_occurred.emit("Seul un super administrateur peut supprimer un autre super administrateur")
                return False
            
            session.delete(user)
            session.commit()
            session.close()
            
            self.user_deleted.emit(user_id)
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Erreur lors de la suppression de l'utilisateur: {str(e)}")
            return False
    
    def get_all_users(self):
        """
        Récupérer tous les utilisateurs
        
        Returns:
            list: Liste des utilisateurs
        """
        try:
            session = self.get_session()
            users = session.query(User).order_by(desc(User.created_at)).all()
            session.close()
            
            result = []
            for user in users:
                result.append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'full_name': f"{user.first_name} {user.last_name}".strip(),
                    'role': user.role,
                    'role_display': self.ROLES.get(user.role, user.role),
                    'is_active': user.is_active,
                    'created_at': user.created_at,
                    'last_login': user.last_login
                })
            
            self.users_loaded.emit(result)
            return result
            
        except Exception as e:
            self.error_occurred.emit(f"Erreur lors de la récupération des utilisateurs: {str(e)}")
            return []
    
    def get_user_by_id(self, user_id):
        """
        Récupérer un utilisateur par son ID
        
        Args:
            user_id (int): ID de l'utilisateur
            
        Returns:
            dict: Informations de l'utilisateur ou None
        """
        try:
            session = self.get_session()
            user = session.query(User).filter(User.id == user_id).first()
            session.close()
            
            if user:
                return {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role,
                    'is_active': user.is_active,
                    'created_at': user.created_at,
                    'last_login': user.last_login
                }
            
            return None
            
        except Exception as e:
            self.error_occurred.emit(f"Erreur lors de la récupération de l'utilisateur: {str(e)}")
            return None
    
    def get_current_user(self):
        """
        Récupérer l'utilisateur actuellement connecté
        
        Returns:
            dict: Informations de l'utilisateur connecté ou None
        """
        return self._current_user
    
    def logout(self):
        """Déconnecter l'utilisateur actuel"""
        self._current_user = None
    
    def has_permission(self, user_role, required_role):
        """
        Vérifier si un utilisateur a les permissions requises
        
        Args:
            user_role (str): Rôle de l'utilisateur
            required_role (str): Rôle requis
            
        Returns:
            bool: True si l'utilisateur a les permissions
        """
        role_hierarchy = {
            'super_admin': 5,
            'admin': 4,
            'manager': 3,
            'user': 2,
            'guest': 1
        }
        
        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    def create_default_admin(self):
        """Créer un administrateur par défaut si aucun n'existe"""
        try:
            session = self.get_session()
            admin_exists = session.query(User).filter(User.role == 'super_admin').first()
            
            if not admin_exists:
                default_admin_data = {
                    'username': 'admin',
                    'email': 'admin@ayanna-erp.com',
                    'first_name': 'Super',
                    'last_name': 'Admin',
                    'password': 'admin123',  # À changer immédiatement
                    'role': 'super_admin',
                    'is_active': True
                }
                
                session.close()
                self.create_user(default_admin_data, 'super_admin')
                return True
            
            session.close()
            return False
            
        except Exception as e:
            self.error_occurred.emit(f"Erreur lors de la création de l'admin par défaut: {str(e)}")
            return False