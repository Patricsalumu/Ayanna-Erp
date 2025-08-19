#!/usr/bin/env python3
"""
Test pour reproduire l'erreur du widget comptes
"""
import sys
sys.path.insert(0, '.')

from PyQt6.QtWidgets import QApplication

print("🔍 Test du widget comptes...")

try:
    app = QApplication(sys.argv)
    
    # Simuler un utilisateur 
    class MockUser:
        def __init__(self):
            self.enterprise_id = 1
            self.username = 'admin'
    
    user = MockUser()
    
    # Importer le widget
    from ayanna_erp.modules.comptabilite.widgets.comptes_widget import ComptesWidget
    from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ComptabiliteController
    from ayanna_erp.database.database_manager import DatabaseManager
    
    print("✅ Imports réussis")
    
    # Créer directement le widget sans controller pour tester l'erreur
    from ayanna_erp.database.database_manager import DatabaseManager
    
    class MockParent:
        def __init__(self):
            self.entreprise_id = 1
    
    class MockController:
        def __init__(self):
            self.db_manager = DatabaseManager()
            self.session = self.db_manager.get_session()
            
        def get_comptes(self, entreprise_id):
            return []
            
        def get_compte_config(self, entreprise_id):
            return None
            
        def set_compte_config(self, entreprise_id, caisse_id, frais_id, client_id):
            pass
    
    parent = MockParent()
    controller = MockController()
    widget = ComptesWidget(controller, parent)
    
    print("✅ Widget créé avec succès")
    
    # Tester open_config_dialog qui est mentionné dans l'erreur
    print("🔍 Test de open_config_dialog...")
    try:
        widget.open_config_dialog()
        print("✅ open_config_dialog réussi")
    except Exception as e:
        print(f"❌ Erreur dans open_config_dialog: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"❌ Erreur générale: {e}")
    import traceback
    traceback.print_exc()
