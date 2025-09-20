#!/usr/bin/env python3
"""
Test final de la vue d'index d'entreprise mise à jour
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from PyQt6.QtWidgets import QApplication
from ayanna_erp.core.view.enterprise_index import EnterpriseIndexView

def test_enterprise_index():
    """Test de la vue d'index d'entreprise"""
    print("=== Test de la Vue d'Index d'Entreprise ===")
    
    app = QApplication(sys.argv)
    
    try:
        # Simuler un utilisateur connecté
        current_user = {
            'id': 1,
            'username': 'admin',
            'role': 'admin',
            'enterprise_id': 1
        }
        
        print("Création de la vue d'index...")
        view = EnterpriseIndexView(current_user=current_user)
        
        print("Vue créée avec succès!")
        print(f"- Entreprise chargée: {view.enterprise_data is not None}")
        
        if view.enterprise_data:
            print(f"- Nom de l'entreprise: {view.enterprise_data.get('name')}")
            print(f"- Adresse: {view.enterprise_data.get('address')}")
            print(f"- Logo: {view.enterprise_data.get('logo')}")
        
        print("\n✅ Test de la vue d'index réussi!")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enterprise_index()