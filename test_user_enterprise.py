"""
Test pour vérifier l'enterprise_id de l'utilisateur admin
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ayanna_erp.core.controllers.simple_user_controller import SimpleUserController
from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController

def test_user_enterprise():
    """Test de l'entreprise de l'utilisateur"""
    print("=== Test de l'entreprise utilisateur ===")
    
    # Contrôleurs
    user_controller = SimpleUserController()
    enterprise_controller = EntrepriseController()
    
    # Récupérer l'utilisateur admin
    admin_user = user_controller.authenticate_user('Super Administrateur', 'admin123')
    
    if admin_user:
        print(f"✓ Utilisateur admin trouvé: {admin_user.get('name')}")
        print(f"  - ID: {admin_user.get('id')}")
        print(f"  - Role: {admin_user.get('role')}")
        print(f"  - Enterprise ID: {admin_user.get('enterprise_id')}")
        
        # Test récupération de l'entreprise
        enterprise_id = admin_user.get('enterprise_id')
        if enterprise_id:
            enterprise = enterprise_controller.get_current_enterprise(enterprise_id)
            if enterprise:
                print(f"✓ Entreprise trouvée:")
                print(f"  - ID: {enterprise.get('id')}")
                print(f"  - Nom: {enterprise.get('nom')}")
                print(f"  - Description: {enterprise.get('description', 'N/A')}")
                print(f"  - Email: {enterprise.get('email', 'N/A')}")
                print(f"  - Téléphone: {enterprise.get('telephone', 'N/A')}")
            else:
                print("✗ Aucune entreprise trouvée avec cet ID")
        else:
            print("✗ Aucun enterprise_id trouvé pour cet utilisateur")
    else:
        print("✗ Impossible de récupérer l'utilisateur admin")

if __name__ == "__main__":
    test_user_enterprise()