"""
Script pour vérifier l'utilisateur admin et tester la connexion
"""

import sys
import os

# Ajouter le répertoire racine au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.core.controllers.user_controller import UserController

def check_admin_user():
    """Vérifier l'utilisateur admin"""
    print("=== Vérification de l'utilisateur admin ===")
    
    try:
        user_controller = UserController()
        
        # Récupérer tous les utilisateurs
        users = user_controller.get_all_users()
        print(f"✓ {len(users)} utilisateur(s) trouvé(s)")
        
        # Rechercher les super admins
        super_admins = [u for u in users if u.get('role') == 'super_admin']
        
        if super_admins:
            print(f"✓ {len(super_admins)} super administrateur(s) trouvé(s):")
            for admin in super_admins:
                print(f"  - ID: {admin['id']}")
                print(f"  - Nom d'utilisateur: {admin['username']}")
                print(f"  - Email: {admin['email']}")
                print(f"  - Nom complet: {admin.get('first_name', '')} {admin.get('last_name', '')}")
                print(f"  - Actif: {'Oui' if admin.get('is_active', False) else 'Non'}")
                print(f"  - Créé le: {admin.get('created_at', 'N/A')}")
                print("")
                
                # Test d'authentification avec mot de passe par défaut
                print(f"Test d'authentification pour '{admin['username']}'...")
                auth_result = user_controller.authenticate_user(admin['username'], 'admin123')
                
                if auth_result:
                    print("✓ Authentification réussie avec le mot de passe par défaut")
                    print(f"  Utilisateur connecté: {auth_result['username']} ({auth_result['role']})")
                else:
                    print("✗ Échec de l'authentification avec le mot de passe par défaut")
                    
                print("-" * 50)
        else:
            print("❌ Aucun super administrateur trouvé!")
            print("Création de l'utilisateur admin par défaut...")
            
            admin_created = user_controller.create_default_admin()
            if admin_created:
                print("✓ Utilisateur admin créé avec succès!")
                print("  - Nom d'utilisateur: admin")
                print("  - Mot de passe: admin123")
            else:
                print("❌ Erreur lors de la création de l'admin par défaut")
        
        print("\n=== Instructions d'accès ===")
        print("1. Lancez l'application Ayanna ERP")
        print("2. Connectez-vous avec :")
        print("   - Nom d'utilisateur: admin")
        print("   - Mot de passe: admin123")
        print("3. Une fois connecté, accédez aux menus :")
        print("   - Configuration > Entreprise (pour gérer l'entreprise)")
        print("   - Configuration > Utilisateurs (pour gérer les utilisateurs)")
        print("\n⚠️  N'oubliez pas de changer le mot de passe par défaut!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_admin_user()