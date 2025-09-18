#!/usr/bin/env python3
"""
Test d'ouverture du module comptabilité pour diagnostiquer l'erreur
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_comptabilite_module():
    """Test d'ouverture du module comptabilité"""
    
    print("=== Test Module Comptabilité ===\n")
    
    try:
        # Simuler un utilisateur avec enterprise_id
        class MockUser:
            def __init__(self):
                self.enterprise_id = 1
        
        current_user = MockUser()
        
        # Tenter d'importer et instancier ComptabiliteWindow
        from ayanna_erp.modules.comptabilite.comptabilite_window import ComptabiliteWindow
        print("✅ Import ComptabiliteWindow réussi")
        
        # Créer la fenêtre (ne pas l'afficher)
        window = ComptabiliteWindow(current_user)
        print("✅ Instanciation ComptabiliteWindow réussie")
        
        # Vérifier que le controller est bien créé
        if window.controller:
            print("✅ Controller créé avec succès")
        else:
            print("⚠️ Controller est None")
        
        print("\n🎉 Module comptabilité fonctionne correctement !")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_comptabilite_module()