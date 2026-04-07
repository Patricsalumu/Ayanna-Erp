"""
Contrôleur pour la gestion des utilisateurs
Adapté au schéma réel de la table core_users:
  id, enterprise_id, name, email, password, role, created_at
Le mot de passe est hashé via bcrypt (méthodes set_password / check_password sur le modèle User).
"""

import sys
import os
from datetime import datetime
from sqlalchemy import desc, or_
from PyQt6.QtCore import QObject, pyqtSignal

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from ayanna_erp.database.database_manager import DatabaseManager, User


class UserController(QObject):
    """Contrôleur pour la gestion des utilisateurs"""

    # Signaux
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
        'caissier': 'Caissier',
        'user': 'Utilisateur',
        'guest': 'Invité',
    }

    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self._current_user = None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def get_session(self):
        return self.db_manager.get_session()

    @staticmethod
    def _user_to_dict(user) -> dict:
        """Convertir un objet User ORM en dictionnaire."""
        return {
            'id': user.id,
            'enterprise_id': user.enterprise_id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'role_display': UserController.ROLES.get(user.role, user.role),
            'created_at': user.created_at,
        }

    # ------------------------------------------------------------------
    # Authentification
    # ------------------------------------------------------------------
    def authenticate_user(self, email_or_name, password):
        """Authentifier un utilisateur par email ou nom."""
        try:
            session = self.get_session()
            user = session.query(User).filter(
                or_(User.email == email_or_name, User.name == email_or_name)
            ).first()

            if not user:
                session.close()
                self.authentication_result.emit(False, None)
                return None

            if user.check_password(password):
                user_info = self._user_to_dict(user)
                session.close()
                self._current_user = user_info
                self.authentication_result.emit(True, user_info)
                return user_info
            else:
                session.close()
                self.authentication_result.emit(False, None)
                return None

        except Exception as e:
            self.error_occurred.emit(f"Erreur lors de l'authentification: {e}")
            self.authentication_result.emit(False, None)
            return None

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def create_user(self, data, creator_role=None):
        """Créer un nouvel utilisateur.

        data attendu : name, email, password, role, enterprise_id (optionnel)
        """
        try:
            if data.get('role') == 'super_admin' and creator_role != 'super_admin':
                self.error_occurred.emit("Seul un super administrateur peut créer d'autres super administrateurs")
                return None

            session = self.get_session()

            # Vérifier unicité email
            existing = session.query(User).filter(User.email == data['email']).first()
            if existing:
                session.close()
                self.error_occurred.emit("Un utilisateur avec cet email existe déjà")
                return None

            user = User(
                enterprise_id=data.get('enterprise_id', 1),
                name=data['name'],
                email=data['email'],
                role=data.get('role', 'user'),
                created_at=datetime.now(),
            )
            user.set_password(data['password'])

            session.add(user)
            session.commit()

            user_info = self._user_to_dict(user)
            session.close()
            self.user_created.emit(user_info)
            return user_info

        except Exception as e:
            self.error_occurred.emit(f"Erreur lors de la création de l'utilisateur: {e}")
            return None

    def update_user(self, user_id, data, updater_role=None):
        """Mettre à jour un utilisateur.

        data peut contenir : name, email, role, password (optionnel)
        """
        try:
            session = self.get_session()
            user = session.query(User).filter(User.id == user_id).first()

            if not user:
                session.close()
                self.error_occurred.emit("Utilisateur non trouvé")
                return False

            if 'role' in data and data['role'] == 'super_admin' and updater_role != 'super_admin':
                session.close()
                self.error_occurred.emit("Seul un super administrateur peut attribuer le rôle super administrateur")
                return False

            # Vérifier unicité email si changé
            if 'email' in data and data['email'] != user.email:
                existing = session.query(User).filter(User.email == data['email']).first()
                if existing:
                    session.close()
                    self.error_occurred.emit("Un utilisateur avec cet email existe déjà")
                    return False

            # Mettre à jour les champs
            if 'name' in data:
                user.name = data['name']
            if 'email' in data:
                user.email = data['email']
            if 'role' in data:
                user.role = data['role']

            # Mot de passe (optionnel)
            if data.get('password'):
                user.set_password(data['password'])

            session.commit()

            user_info = self._user_to_dict(user)
            session.close()
            self.user_updated.emit(user_info)
            return True

        except Exception as e:
            self.error_occurred.emit(f"Erreur lors de la mise à jour de l'utilisateur: {e}")
            return False

    def delete_user(self, user_id, deleter_role=None):
        """Supprimer un utilisateur."""
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
            self.error_occurred.emit(f"Erreur lors de la suppression de l'utilisateur: {e}")
            return False

    def get_all_users(self):
        """Récupérer tous les utilisateurs."""
        try:
            session = self.get_session()
            users = session.query(User).order_by(desc(User.created_at)).all()

            result = [self._user_to_dict(u) for u in users]
            session.close()

            self.users_loaded.emit(result)
            return result

        except Exception as e:
            self.error_occurred.emit(f"Erreur lors de la récupération des utilisateurs: {e}")
            return []

    def get_user_by_id(self, user_id):
        """Récupérer un utilisateur par son ID."""
        try:
            session = self.get_session()
            user = session.query(User).filter(User.id == user_id).first()
            session.close()

            if user:
                return self._user_to_dict(user)
            return None

        except Exception as e:
            self.error_occurred.emit(f"Erreur: {e}")
            return None

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------
    def get_current_user(self):
        return self._current_user

    def logout(self):
        self._current_user = None

    def has_permission(self, user_role, required_role):
        """Vérifier si un rôle a les permissions requises."""
        hierarchy = {
            'super_admin': 6,
            'admin': 5,
            'manager': 4,
            'caissier': 3,
            'user': 2,
            'guest': 1,
        }
        return hierarchy.get(user_role, 0) >= hierarchy.get(required_role, 0)

    def create_default_admin(self):
        """Créer un administrateur par défaut si aucun n'existe."""
        try:
            session = self.get_session()
            admin_exists = session.query(User).filter(User.role == 'super_admin').first()

            if not admin_exists:
                session.close()
                self.create_user({
                    'name': 'Super Administrateur',
                    'email': 'admin@ayanna-erp.com',
                    'password': 'admin123',
                    'role': 'super_admin',
                    'enterprise_id': 1,
                }, 'super_admin')
                return True

            session.close()
            return False

        except Exception as e:
            self.error_occurred.emit(f"Erreur: {e}")
            return False