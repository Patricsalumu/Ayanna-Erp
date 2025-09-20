"""
Test du contrôleur utilisateur adapté à la structure existante
"""

import sys
import os

# Ajouter le répertoire racine au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.core.controllers.simple_user_controller import SimpleUserController

def test_simple_user_controller():
    """Tester le contrôleur utilisateur adapté"""
    print("=== Test du contrôleur utilisateur adapté ===")
    
    try:
        user_controller = SimpleUserController()
        print("✓ SimpleUserController initialisé avec succès")
        
        # Vérifier les utilisateurs existants
        users = user_controller.get_all_users()
        print(f"✓ {len(users)} utilisateur(s) trouvé(s)")
        
        # Afficher les utilisateurs existants
        for user in users:
            print(f"  - {user['username']} ({user['role']}) - {user['email']}")
        
        # Chercher un super admin
        super_admins = [u for u in users if u.get('role') == 'super_admin']
        
        if not super_admins:
            print("\nAucun super admin trouvé. Création en cours...")
            admin_created = user_controller.create_default_admin()
            
            if admin_created:
                print("✓ Super admin créé avec succès!")
                # Recharger la liste
                users = user_controller.get_all_users()
                super_admins = [u for u in users if u.get('role') == 'super_admin']
            else:
                print("❌ Erreur lors de la création du super admin")
                return False
        
        # Test d'authentification
        if super_admins:
            admin = super_admins[0]
            print(f"\n--- Test d'authentification pour {admin['username']} ---")
            
            # Test avec le nom d'utilisateur
            auth_result = user_controller.authenticate_user(admin['username'], 'admin123')
            if auth_result:
                print("✓ Authentification réussie avec le nom d'utilisateur")
                print(f"  Utilisateur connecté: {auth_result['username']} ({auth_result['role']})")
            else:
                print("✗ Échec de l'authentification avec le nom d'utilisateur")
            
            # Test avec l'email
            auth_result = user_controller.authenticate_user(admin['email'], 'admin123')
            if auth_result:
                print("✓ Authentification réussie avec l'email")
            else:
                print("✗ Échec de l'authentification avec l'email")
        
        print("\n=== Instructions ===")
        print("Les widgets de gestion sont déjà connectés au menu Configuration:")
        print("- Configuration > Entreprise")
        print("- Configuration > Utilisateurs")
        print("\nIdentifiants de connexion:")
        if super_admins:
            admin = super_admins[0]
            print(f"  - Nom d'utilisateur: {admin['username']}")
            print(f"  - Email: {admin['email']}")
        print("  - Mot de passe: admin123")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_simple_user_controller()