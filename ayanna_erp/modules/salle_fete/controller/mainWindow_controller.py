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
from ayanna_erp.modules.salle_fete.model.salle_fete import get_database_manager


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
            
            # Importer les modèles nécessaires
            from ayanna_erp.database.database_manager import User
            
            session = db_manager.get_session()
            # Récupérer l'utilisateur
            user = session.query(User).filter_by(id=self.user_id).first()
            session.close()
            
            if not user:
                print(f"❌ Utilisateur avec ID {self.user_id} non trouvé")
                return 1  # Valeur par défaut
            
            # Utiliser la nouvelle méthode pour récupérer le pos_id
            pos_id = db_manager.get_pos_id_for_enterprise_module(user.enterprise_id, "SalleFete")
            
            if pos_id:
                print(f"✅ POS trouvé pour l'entreprise: POS ID {pos_id}")
                return pos_id
            else:
                print(f"❌ Aucun POS Salle de Fête trouvé pour l'entreprise {user.enterprise_id}")
                return 1  # Valeur par défaut
                
        except Exception as e:
            print(f"❌ Erreur lors de la recherche du POS: {e}")
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
            
            # Si les données existent déjà, ne pas réinitialiser
            if existing_services is not None:
                print("✅ Module Salle de Fête déjà initialisé")
                self.is_initialized = True
                self.initialization_completed.emit(True)
                self.database_ready.emit()
                return True
            
            # Les tables du module sont désormais créées lors de l'initialisation
            # globale de l'application (DatabaseManager.initialize_database()).
            # Ne pas exécuter d'initialisation supplémentaire au premier clic.
            print("ℹ️ Les tables et la configuration du module Salle de Fête sont gérées au démarrage de l'application.")
            self.is_initialized = True
            self.initialization_completed.emit(True)
            self.database_ready.emit()
            return True
                
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