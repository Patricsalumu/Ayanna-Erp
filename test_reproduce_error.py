#!/usr/bin/env python3
"""
Test de reproduction exacte de l'erreur utilisateur
"""
import sys
sys.path.insert(0, '.')

from PyQt6.QtWidgets import QApplication, QWidget

print("🔍 Test de reproduction de l'erreur utilisateur...")

try:
    app = QApplication(sys.argv)
    
    # Créer exactement le même setup que dans l'erreur
    from ayanna_erp.modules.comptabilite.widgets.comptes_widget import ComptesWidget
    from ayanna_erp.database.database_manager import DatabaseManager
    
    # Mock controller simple
    class SimpleController:
        def __init__(self):
            self.db_manager = DatabaseManager()
            self.session = self.db_manager.get_session()
        
        def get_comptes(self, entreprise_id):
            return []
            
        def get_compte_config(self, entreprise_id):
            return None
            
        def set_compte_config(self, entreprise_id, caisse_id, frais_id, client_id):
            pass
    
    # Parent widget simple
    class SimpleParent(QWidget):
        def __init__(self):
            super().__init__()
            self.entreprise_id = 1
    
    controller = SimpleController()
    parent = SimpleParent()
    widget = ComptesWidget(controller, parent)
    
    print("✅ Widget créé avec succès")
    
    # Maintenant essayons d'appeler open_config_dialog directement
    print("🔍 Test de open_config_dialog...")
    try:
        widget.open_config_dialog()
        print("✅ open_config_dialog réussi")
    except Exception as e:
        print(f"❌ Erreur dans open_config_dialog: {e}")
        # Afficher la trace complète pour voir où ça plante vraiment
        import traceback
        traceback.print_exc()
        
        # Afficher les infos sur l'erreur pour debug
        print(f"\n🔍 Debug de l'erreur:")
        print(f"Type d'erreur: {type(e)}")
        print(f"Message: {e}")
        if hasattr(e, 'args'):
            print(f"Args: {e.args}")
    
except Exception as e:
    print(f"❌ Erreur générale: {e}")
    import traceback
    traceback.print_exc()
