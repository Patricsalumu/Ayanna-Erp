"""
Test pour voir les clés disponibles dans les données entreprise
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ayanna_erp.core.controllers.simple_user_controller import SimpleUserController
from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController

def test_enterprise_keys():
    """Test pour voir les clés disponibles"""
    print("=== Test des clés entreprise disponibles ===")
    
    try:
        user_controller = SimpleUserController()
        enterprise_controller = EntrepriseController()
        
        # Authentifier l'utilisateur admin
        admin_user = user_controller.authenticate_user('Super Administrateur', 'admin123')
        enterprise_id = admin_user.get('enterprise_id', 1)
        
        # Récupérer l'entreprise
        enterprise = enterprise_controller.get_current_enterprise(enterprise_id)
        
        if enterprise:
            print("✓ Clés disponibles dans l'entreprise :")
            for key, value in enterprise.items():
                print(f"  - '{key}': {repr(value)}")
        else:
            print("✗ Aucune entreprise trouvée")
        
    except Exception as e:
        print(f"✗ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enterprise_keys()