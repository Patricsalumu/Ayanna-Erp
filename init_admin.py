"""
Script d'initialisation pour créer l'utilisateur admin par défaut
"""

import sys
import os

# Ajouter le répertoire racine au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.core.controllers.user_controller import UserController

def initialize_admin_user():
    """Initialiser l'utilisateur admin par défaut"""
    print("=== Initialisation de l'utilisateur administrateur ===")
    
    try:
        user_controller = UserController()
        
        # Vérifier s'il y a déjà un super admin
        users = user_controller.get_all_users()
        super_admins = [u for u in users if u.get('role') == 'super_admin']
        
        if super_admins:
            print(f"✓ {len(super_admins)} super administrateur(s) déjà existant(s):")
            for admin in super_admins:
                print(f"  - {admin['username']} ({admin['email']})")
        else:
            print("Aucun super administrateur trouvé. Création en cours...")
            
            # Créer l'admin par défaut
            admin_created = user_controller.create_default_admin()
            
            if admin_created:
                print("✓ Super administrateur créé avec succès!")
                print("  - Nom d'utilisateur: admin")
                print("  - Email: admin@ayanna-erp.com")
                print("  - Mot de passe: admin123")
                print("")
                print("⚠️  IMPORTANT: Changez le mot de passe par défaut dès votre première connexion!")
            else:
                print("❌ Erreur lors de la création de l'administrateur")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    initialize_admin_user()