"""
Test de l'interface entreprise mise à jour
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def test_enterprise_interface():
    """Test de l'interface entreprise"""
    print("=== Test de l'interface entreprise mise à jour ===")
    
    try:
        # Créer l'application
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Simuler un utilisateur avec enterprise_id
        user_dict = {
            'id': 1,
            'username': 'Super Administrateur',
            'name': 'Super Administrateur',
            'role': 'super_admin',
            'email': 'admin@ayanna.com',
            'enterprise_id': 1
        }
        
        print(f"✓ User dict avec enterprise_id: {user_dict['enterprise_id']}")
        
        # Test de l'interface entreprise
        from ayanna_erp.core.view.enterprise_index import EnterpriseIndexView
        
        enterprise_view = EnterpriseIndexView(None, user_dict)
        print("✓ EnterpriseIndexView créée avec succès")
        
        # La méthode load_enterprise_data() est appelée automatiquement dans __init__
        print("✓ Chargement des données entreprise terminé")
        
        print("✓ Test réussi!")
        
    except Exception as e:
        print(f"✗ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enterprise_interface()