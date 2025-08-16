"""
Contrôleur principal pour la fenêtre Salle de Fête
Gère l'initialisation de la base de données et la coordination des modules
"""

import sys
import os
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal

# Ajouter le chemin vers le modèle
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ayanna_erp.modules.salle_fete.model.salle_fete import initialize_salle_fete_module, get_database_manager


class MainWindowController(QObject):
    """Contrôleur principal pour la fenêtre Salle de Fête"""
    
    # Signaux pour communiquer avec la vue
    initialization_completed = pyqtSignal(bool)
    database_ready = pyqtSignal()
    
    def __init__(self, parent=None, user_id=1):
        super().__init__(parent)
        self.parent_window = parent
        self.user_id = user_id
        self.pos_id = self._get_pos_for_user()
        self.is_initialized = False
        
    def _get_pos_for_user(self):
        """Récupérer l'ID du POS Salle de Fête pour l'entreprise de l'utilisateur"""
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            # Importer les modèles nécessaires
            from ayanna_erp.database.database_manager import POSPoint, User
            
            # Récupérer l'utilisateur
            user = session.query(User).filter_by(id=self.user_id).first()
            if not user:
                print(f"❌ Utilisateur avec ID {self.user_id} non trouvé")
                db_manager.close_session()
                return 1  # Valeur par défaut
            
            # Chercher le POS du module Salle de Fête (module_id=1) pour cette entreprise
            pos = session.query(POSPoint).filter_by(
                enterprise_id=user.enterprise_id,
                module_id=1  # Module Salle de Fête
            ).first()
            
            if pos:
                print(f"✅ POS trouvé pour l'entreprise: {pos.name} (ID: {pos.id})")
                db_manager.close_session()
                return pos.id
            else:
                print(f"❌ Aucun POS Salle de Fête trouvé pour l'entreprise {user.enterprise_id}")
                db_manager.close_session()
                return 1  # Valeur par défaut
                
        except Exception as e:
            print(f"❌ Erreur lors de la recherche du POS: {e}")
            try:
                db_manager.close_session()
            except:
                pass
            return 1  # Valeur par défaut
        
    def set_pos_id(self, pos_id):
        """Définir l'ID du POS"""
        self.pos_id = pos_id
        
    def initialize_module(self):
        """
        Initialiser le module Salle de Fête
        À appeler au premier accès à la fenêtre
        """
        if self.is_initialized:
            self.database_ready.emit()
            return True
            
        try:
            # Vérifier d'abord si le module est déjà initialisé dans la base de données
            from ayanna_erp.modules.salle_fete.model.salle_fete import EventService, get_database_manager
            
            db_manager = get_database_manager()
            session = db_manager.get_session()
            existing_services = session.query(EventService).filter(EventService.pos_id == self.pos_id).first()
            db_manager.close_session()
            
            # Si les données existent déjà, pas besoin d'afficher la popup
            is_first_time = existing_services is None
            
            print("🎪 Initialisation du module Salle de Fête...")
            
            # Initialiser les tables et données
            success = initialize_salle_fete_module(self.pos_id)
            
            if success:
                self.is_initialized = True
                print("✅ Module Salle de Fête initialisé avec succès")
                self.initialization_completed.emit(True)
                self.database_ready.emit()
                
                # Afficher un message de confirmation SEULEMENT si c'est la première fois
                if is_first_time and self.parent_window:
                    QMessageBox.information(
                        self.parent_window,
                        "Initialisation réussie",
                        "Le module Salle de Fête a été initialisé avec succès !\n\n"
                        "✅ Base de données créée\n"
                        "✅ Tables initialisées\n"
                        "✅ Données d'exemple ajoutées"
                    )
                return True
            else:
                print("❌ Échec de l'initialisation")
                self.initialization_completed.emit(False)
                
                if self.parent_window:
                    QMessageBox.critical(
                        self.parent_window,
                        "Erreur d'initialisation",
                        "Impossible d'initialiser le module Salle de Fête.\n"
                        "Veuillez vérifier les permissions et réessayer."
                    )
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
            self.initialization_completed.emit(False)
            
            if self.parent_window:
                QMessageBox.critical(
                    self.parent_window,
                    "Erreur critique",
                    f"Une erreur s'est produite lors de l'initialisation :\n{str(e)}"
                )
            return False
    
    def initialize_database(self):
        """Initialiser la base de données (alias pour initialize_module)"""
        return self.initialize_module()
            
    def check_database_connection(self):
        """Vérifier la connexion à la base de données"""
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            if session:
                db_manager.close_session()
                return True
            return False
        except Exception as e:
            print(f"❌ Erreur de connexion BDD: {e}")
            return False
            
    def get_database_instance(self):
        """Retourner l'instance de la base de données"""
        return get_database_manager()
        
    def cleanup(self):
        """Nettoyer les ressources au moment de la fermeture"""
        try:
            db_manager = get_database_manager()
            db_manager.close_session()
            print("🧹 Ressources nettoyées")
        except Exception as e:
            print(f"⚠️ Erreur lors du nettoyage: {e}")