"""
Test de l'intégration dans la fenêtre principale
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def test_main_window_integration():
    """Test de l'intégration dans main_window"""
    print("=== Test d'intégration main_window ===")
    
    try:
        # Import de la fenêtre principale
        from ayanna_erp.ui.main_window import MainWindow
        
        print("✓ Import MainWindow réussi")
        
        # Créer l'application
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Simuler un utilisateur connecté
        class SimpleUser:
            def __init__(self, user_data):
                self.id = user_data['id']
                self.username = user_data['username']
                self.name = user_data['name']
                self.role = user_data['role']
                self.email = user_data.get('email', '')
        
        admin_user = SimpleUser({
            'id': 1,
            'username': 'Super Administrateur',
            'name': 'Super Administrateur',
            'role': 'super_admin',
            'email': 'admin@ayanna.com'
        })
        
        # Créer la fenêtre principale
        main_window = MainWindow(current_user=admin_user)
        print("✓ MainWindow créée avec succès")
        
        # Vérifier que les méthodes de configuration existent
        if hasattr(main_window, 'open_user_management'):
            print("✓ Méthode open_user_management disponible")
        else:
            print("✗ Méthode open_user_management manquante")
        
        if hasattr(main_window, 'open_enterprise_management'):
            print("✓ Méthode open_enterprise_management disponible")
        else:
            print("✗ Méthode open_enterprise_management manquante")
        
        print("✓ Test d'intégration réussi")
        
    except Exception as e:
        print(f"✗ Erreur d'intégration: {e}")

if __name__ == "__main__":
    test_main_window_integration()