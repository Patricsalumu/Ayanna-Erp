#!/usr/bin/env python3
"""
Test de l'erreur corrigée dans le controller comptabilité
"""
import sys
sys.path.insert(0, '.')

from PyQt6.QtWidgets import QApplication

print("🔍 Test de l'erreur corrigée dans le controller...")

try:
    app = QApplication(sys.argv)
    
    # Test direct du controller
    from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ComptabiliteController
    from ayanna_erp.database.database_manager import DatabaseManager
    
    # Créer un controller
    controller = ComptabiliteController()
    
    print("✅ Controller créé avec succès")
    
    # Tester get_compte_config qui était problématique
    print("🔍 Test de get_compte_config...")
    try:
        config = controller.get_compte_config(1)
        print(f"✅ get_compte_config réussi: {config}")
    except Exception as e:
        print(f"❌ Erreur dans get_compte_config: {e}")
        import traceback
        traceback.print_exc()
    
    # Tester le widget complet
    print("🔍 Test du widget comptes...")
    try:
        from ayanna_erp.modules.comptabilite.widgets.comptes_widget import ComptesWidget
        
        class MockParent:
            def __init__(self):
                self.entreprise_id = 1
        
        # Créer un mock parent qui hérite de QWidget
        from PyQt6.QtWidgets import QWidget
        parent = QWidget()
        parent.entreprise_id = 1
        
        widget = ComptesWidget(controller, parent)
        print("✅ Widget créé avec succès")
        
        # Tester open_config_dialog qui était problématique
        print("🔍 Test de open_config_dialog...")
        try:
            widget.open_config_dialog()
            print("✅ open_config_dialog réussi - pas d'erreur!")
        except Exception as e:
            print(f"❌ Erreur dans open_config_dialog: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Erreur dans le widget: {e}")
        import traceback
        traceback.print_exc()
    
    print("✅ Test terminé!")
    
except Exception as e:
    print(f"❌ Erreur générale: {e}")
    import traceback
    traceback.print_exc()
