"""
Test complet du système de gestion des utilisateurs et entreprises
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import des contrôleurs
from ayanna_erp.core.controllers.simple_user_controller import SimpleUserController
from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController

def test_user_system():
    """Test du système utilisateur"""
    print("=== Test du système utilisateur ===")
    
    controller = SimpleUserController()
    
    # Test des utilisateurs existants
    users = controller.get_all_users()
    print(f"Nombre d'utilisateurs: {len(users)}")
    
    for user in users[:3]:  # Afficher les 3 premiers
        print(f"- {user.get('username')} ({user.get('role')})")
    
    # Test d'authentification avec admin
    admin_auth = controller.authenticate_user('Super Administrateur', 'admin123')
    print(f"\nAuthentification admin réussie: {admin_auth is not None}")
    
    if admin_auth:
        print(f"Admin connecté: {admin_auth.get('username')} - {admin_auth.get('role')}")
    
    return admin_auth

def test_enterprise_system():
    """Test du système entreprise"""
    print("\n=== Test du système entreprise ===")
    
    controller = EntrepriseController()
    
    # Test des entreprises
    try:
        if hasattr(controller, 'get_all_enterprises'):
            enterprises = controller.get_all_enterprises()
            print(f"Nombre d'entreprises: {len(enterprises)}")
        else:
            print("Méthode get_all_enterprises non disponible")
    except Exception as e:
        print(f"Erreur lors du chargement des entreprises: {e}")

def test_ui_integration():
    """Test d'intégration UI"""
    print("\n=== Test d'intégration UI ===")
    
    try:
        # Import des vues
        from ayanna_erp.core.view.user_index import UserIndexView
        from ayanna_erp.core.view.enterprise_index import EnterpriseIndexView
        from ayanna_erp.core.view.simple_user_widget import SimpleUserWidget
        from ayanna_erp.core.view.simple_enterprise_widget import SimpleEnterpriseWidget
        
        print("✓ Import des vues utilisateur réussi")
        print("✓ Import des widgets réussi")
        
        # Test de création d'instance (sans affichage)
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Simuler un utilisateur admin
        admin_user = {
            'id': 1,
            'username': 'admin',
            'name': 'Administrateur',
            'role': 'admin'
        }
        
        # Test création des vues
        user_index = UserIndexView(current_user=admin_user)
        print("✓ UserIndexView créé avec succès")
        
        enterprise_index = EnterpriseIndexView(current_user=admin_user)
        print("✓ EnterpriseIndexView créé avec succès")
        
        print("✓ Tous les tests UI passés")
        
    except Exception as e:
        print(f"✗ Erreur dans les tests UI: {e}")

def main():
    """Fonction principale de test"""
    print("Test complet du système Ayanna ERP")
    print("=" * 50)
    
    # Test utilisateurs
    admin_user = test_user_system()
    
    # Test entreprises
    test_enterprise_system()
    
    # Test UI
    test_ui_integration()
    
    print("\n" + "=" * 50)
    print("Tests terminés")

if __name__ == "__main__":
    main()