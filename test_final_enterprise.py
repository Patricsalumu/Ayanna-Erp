"""
Test final de l'interface entreprise
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def test_final_enterprise():
    """Test final de l'interface entreprise"""
    print("=== Test final de l'interface entreprise ===")
    
    try:
        # Récupérer les vraies données utilisateur
        from ayanna_erp.core.controllers.simple_user_controller import SimpleUserController
        from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
        
        user_controller = SimpleUserController()
        enterprise_controller = EntrepriseController()
        
        # Authentifier l'utilisateur admin
        admin_user = user_controller.authenticate_user('Super Administrateur', 'admin123')
        
        if not admin_user:
            print("✗ Impossible d'authentifier l'utilisateur admin")
            return
        
        print(f"✓ Utilisateur admin: {admin_user.get('name')}")
        print(f"  - Enterprise ID: {admin_user.get('enterprise_id')}")
        
        # Récupérer l'entreprise
        enterprise = enterprise_controller.get_current_enterprise(admin_user.get('enterprise_id', 1))
        
        if enterprise:
            print(f"✓ Entreprise trouvée:")
            print(f"  - Name: {enterprise.get('name')}")
            print(f"  - Address: {enterprise.get('address')}")
            print(f"  - Phone: {enterprise.get('phone')}")
            print(f"  - Email: {enterprise.get('email')}")
            print(f"  - RCCM: {enterprise.get('rccm')}")
            print(f"  - Slogan: {enterprise.get('slogan')}")
        else:
            print("✗ Aucune entreprise trouvée")
            return
        
        # Test de l'interface
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        from ayanna_erp.core.view.enterprise_index import EnterpriseIndexView
        
        enterprise_view = EnterpriseIndexView(None, admin_user)
        print("✓ EnterpriseIndexView créée avec succès")
        
        print("✓ Test complet réussi!")
        
    except Exception as e:
        print(f"✗ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_final_enterprise()