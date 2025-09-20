"""
Script pour vérifier et initialiser la base de données avec les tables nécessaires
"""

import sys
import os

# Ajouter le répertoire racine au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.core.controllers.user_controller import UserController

def check_database_structure():
    """Vérifier la structure de la base de données"""
    print("=== Vérification de la structure de la base de données ===")
    
    try:
        db_manager = DatabaseManager()
        
        # Vérifier la connexion
        session = db_manager.get_session()
        print("✓ Connexion à la base de données réussie")
        
        # Vérifier si la table User existe
        from sqlalchemy import inspect
        inspector = inspect(db_manager.engine)
        tables = inspector.get_table_names()
        
        print(f"✓ Tables trouvées dans la base de données: {tables}")
        
        if 'core_users' in tables:
            print("✓ Table 'core_users' trouvée")
            
            # Vérifier la structure de la table users
            columns = inspector.get_columns('core_users')
            print("Colonnes de la table 'core_users':")
            for col in columns:
                print(f"  - {col['name']} ({col['type']})")
                
        else:
            print("❌ Table 'core_users' non trouvée")
            print("Les tables doivent être créées via le système principal")
            return False
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification de la base de données: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_admin_user():
    """Créer l'utilisateur admin"""
    print("\n=== Création de l'utilisateur admin ===")
    
    try:
        user_controller = UserController()
        
        # Données de l'admin par défaut
        admin_data = {
            'username': 'admin',
            'email': 'admin@ayanna-erp.com',
            'first_name': 'Super',
            'last_name': 'Admin',
            'password': 'admin123',
            'role': 'super_admin',
            'is_active': True
        }
        
        print("Création de l'utilisateur admin...")
        result = user_controller.create_user(admin_data, 'super_admin')
        
        if result:
            print("✓ Utilisateur admin créé avec succès!")
            print(f"  - ID: {result['id']}")
            print(f"  - Nom d'utilisateur: {result['username']}")
            print(f"  - Email: {result['email']}")
            print(f"  - Rôle: {result['role']}")
            
            # Test d'authentification
            print("\nTest d'authentification...")
            auth_result = user_controller.authenticate_user('admin', 'admin123')
            
            if auth_result:
                print("✓ Authentification réussie!")
                print(f"  Utilisateur connecté: {auth_result['username']}")
            else:
                print("❌ Échec de l'authentification")
                
            return True
        else:
            print("❌ Erreur lors de la création de l'utilisateur admin")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'admin: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale"""
    print("Initialisation de la base de données et de l'utilisateur admin\n")
    
    # Vérifier la base de données
    db_ok = check_database_structure()
    
    if db_ok:
        # Créer l'utilisateur admin
        admin_ok = create_admin_user()
        
        if admin_ok:
            print("\n" + "="*60)
            print("🎉 INITIALISATION TERMINÉE AVEC SUCCÈS!")
            print("="*60)
            print("\nVous pouvez maintenant :")
            print("1. Lancer l'application Ayanna ERP")
            print("2. Vous connecter avec :")
            print("   - Nom d'utilisateur: admin")
            print("   - Mot de passe: admin123")
            print("3. Accéder aux fonctionnalités via le menu Configuration :")
            print("   - Configuration > Entreprise")
            print("   - Configuration > Utilisateurs")
            print("\n⚠️  IMPORTANT: Changez le mot de passe par défaut!")
        else:
            print("\n❌ Échec de l'initialisation de l'utilisateur admin")
    else:
        print("\n❌ Échec de l'initialisation de la base de données")

if __name__ == "__main__":
    main()