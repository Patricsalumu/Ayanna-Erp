"""
Script de test pour vérifier le système de gestion des utilisateurs et entreprises
"""

import sys
import os

# Ajouter le répertoire racine au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.core.controllers.user_controller import UserController
from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController

def test_user_system():
    """Tester le système utilisateur"""
    print("=== Test du système de gestion des utilisateurs ===")
    
    try:
        # Initialiser le contrôleur
        user_controller = UserController()
        print("✓ UserController initialisé avec succès")
        
        # Créer un admin par défaut si nécessaire
        admin_created = user_controller.create_default_admin()
        if admin_created:
            print("✓ Utilisateur admin par défaut créé")
        else:
            print("! Utilisateur admin déjà existant")
        
        # Récupérer tous les utilisateurs
        users = user_controller.get_all_users()
        print(f"✓ {len(users)} utilisateur(s) trouvé(s)")
        
        for user in users:
            print(f"  - {user['username']} ({user['role']}) - {'Actif' if user['is_active'] else 'Inactif'}")
        
        # Test d'authentification
        if users:
            admin_user = next((u for u in users if u['role'] == 'super_admin'), None)
            if admin_user:
                print(f"\n--- Test d'authentification pour {admin_user['username']} ---")
                auth_result = user_controller.authenticate_user(admin_user['username'], 'admin123')
                if auth_result:
                    print("✓ Authentification réussie")
                    print(f"  Utilisateur connecté: {auth_result['username']}")
                else:
                    print("✗ Échec de l'authentification")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur lors du test du système utilisateur: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enterprise_system():
    """Tester le système entreprise"""
    print("\n=== Test du système de gestion des entreprises ===")
    
    try:
        # Initialiser le contrôleur
        entreprise_controller = EntrepriseController()
        print("✓ EntrepriseController initialisé avec succès")
        
        # Récupérer toutes les entreprises
        enterprises = entreprise_controller.get_all_enterprises()
        print(f"✓ {len(enterprises)} entreprise(s) trouvée(s)")
        
        for enterprise in enterprises:
            print(f"  - {enterprise.get('nom', enterprise.get('name', 'Nom non défini'))} ({enterprise.get('type_entreprise', 'N/A')})")
            print(f"    Devise: {enterprise.get('devise', 'EUR')}")
        
        # Test des fonctions utilitaires
        currency = entreprise_controller.get_currency()
        currency_symbol = entreprise_controller.get_currency_symbol()
        print(f"✓ Devise système: {currency} ({currency_symbol})")
        
        # Test de formatage de montant
        test_amount = 1234.56
        formatted = entreprise_controller.format_amount(test_amount)
        print(f"✓ Formatage de montant: {test_amount} -> {formatted}")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur lors du test du système entreprise: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_imports():
    """Tester que tous les imports fonctionnent"""
    print("\n=== Test des imports ===")
    
    try:
        # Test des vues
        from ayanna_erp.core.view.enterprise_index import EnterpriseIndexView
        print("✓ EnterpriseIndexView importé")
        
        from ayanna_erp.core.view.user_index import UserIndexView
        print("✓ UserIndexView importé")
        
        from ayanna_erp.core.view.enterprise_widget import EnterpriseWidget
        print("✓ EnterpriseWidget importé")
        
        from ayanna_erp.core.view.user_widget import UserWidget
        print("✓ UserWidget importé")
        
        # Test des contrôleurs
        from ayanna_erp.core.controllers.user_controller import UserController
        print("✓ UserController importé")
        
        from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
        print("✓ EntrepriseController importé")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur lors du test des imports: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Démarrage des tests du système Ayanna ERP\n")
    
    # Tests
    imports_ok = test_imports()
    users_ok = test_user_system()
    enterprises_ok = test_enterprise_system()
    
    # Résumé
    print("\n" + "="*50)
    print("RÉSUMÉ DES TESTS")
    print("="*50)
    print(f"Imports: {'✓ OK' if imports_ok else '✗ ÉCHEC'}")
    print(f"Système utilisateurs: {'✓ OK' if users_ok else '✗ ÉCHEC'}")
    print(f"Système entreprises: {'✓ OK' if enterprises_ok else '✗ ÉCHEC'}")
    
    if all([imports_ok, users_ok, enterprises_ok]):
        print("\n🎉 Tous les tests sont passés avec succès!")
        print("\nLe système de gestion des utilisateurs et entreprises est prêt!")
        print("\nVous pouvez maintenant:")
        print("- Accéder à la gestion des entreprises via Configuration > Entreprise")
        print("- Accéder à la gestion des utilisateurs via Configuration > Utilisateurs")
        print("- Utiliser les contrôles d'accès basés sur les rôles")
    else:
        print("\n❌ Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
    
    print("\nMot de passe admin par défaut: admin123")
    print("⚠️  N'oubliez pas de changer le mot de passe par défaut !")