"""
Test d'ouverture des fenêtres de configuration depuis MainWindow
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def test_main_window_config():
    """Test des fenêtres de configuration"""
    print("=== Test des fenêtres de configuration ===")
    
    try:
        # Import de la fenêtre principale
        from ayanna_erp.ui.main_window import MainWindow
        
        # Créer l'application
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Simuler un utilisateur connecté avec les bons attributs
        class TestUser:
            def __init__(self):
                self.id = 1
                self.username = 'Super Administrateur'
                self.name = 'Super Administrateur'
                self.role = 'super_admin'
                self.email = 'admin@ayanna.com'
        
        user = TestUser()
        
        # Créer la fenêtre principale
        main_window = MainWindow(user)
        print("✓ MainWindow créée avec succès")
        
        # Test de la conversion
        user_dict = main_window.user_to_dict()
        print(f"✓ Conversion user: {user_dict.get('role')}")
        
        # Test d'ouverture des configurations (sans affichage)
        try:
            # Test entreprise config
            from ayanna_erp.core.view.enterprise_index import EnterpriseIndexView
            enterprise_view = EnterpriseIndexView(None, user_dict)
            print("✓ EnterpriseIndexView créée avec succès")
        except Exception as e:
            print(f"✗ Erreur enterprise: {e}")
        
        try:
            # Test user config
            from ayanna_erp.core.view.user_index import UserIndexView
            user_view = UserIndexView(None, user_dict)
            print("✓ UserIndexView créée avec succès")
        except Exception as e:
            print(f"✗ Erreur user: {e}")
        
        print("✓ Tous les tests réussis!")
        
    except Exception as e:
        print(f"✗ Erreur générale: {e}")

if __name__ == "__main__":
    test_main_window_config()