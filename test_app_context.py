#!/usr/bin/env python3
"""
Test simulation du click sur 'Configurer comptes' dans l'app principale
"""
import sys
sys.path.insert(0, '.')

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

print("🔍 Test de simulation du clique sur 'Configurer comptes'...")

try:
    app = QApplication(sys.argv)
    
    # Simuler un utilisateur connecté
    class MockUser:
        def __init__(self):
            self.enterprise_id = 1
            self.username = 'admin'
            self.id = 1
            self.role = 'admin'
    
    user = MockUser()
    
    # Créer la fenêtre comptabilité
    from ayanna_erp.modules.comptabilite.comptabilite_window import ComptabiliteWindow
    
    window = ComptabiliteWindow(user)
    print("✅ Fenêtre comptabilité créée")
    
    # Aller à l'onglet Comptes comptables (index 5 selon les tests précédents)
    window.tabs.setCurrentIndex(5)
    print("✅ Onglet comptes sélectionné")
    
    # Récupérer le widget comptes
    comptes_widget = window.tabs.widget(5)
    print(f"✅ Widget comptes récupéré: {type(comptes_widget)}")
    
    # Simuler le clique sur "Configurer comptes"
    print("🔍 Simulation du clique sur 'Configurer comptes'...")
    try:
        comptes_widget.open_config_dialog()
        print("✅ open_config_dialog réussi dans le contexte de l'app")
    except Exception as e:
        print(f"❌ Erreur dans open_config_dialog: {e}")
        import traceback
        traceback.print_exc()
        
        # Afficher des infos sur le widget et ses attributs
        print(f"\n🔍 Debug du widget:")
        print(f"Type: {type(comptes_widget)}")
        print(f"Session: {getattr(comptes_widget, 'session', 'Non défini')}")
        print(f"Entreprise ID: {getattr(comptes_widget, 'entreprise_id', 'Non défini')}")
        
        # Vérifier les imports du widget
        print(f"\n🔍 Debug des imports:")
        from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ClasseComptable
        print(f"ClasseComptable: {ClasseComptable}")
        print(f"Attributs de ClasseComptable: {[attr for attr in dir(ClasseComptable) if 'enterprise' in attr or 'entreprise' in attr]}")
    
    print("✅ Test terminé")
    
except Exception as e:
    print(f"❌ Erreur générale: {e}")
    import traceback
    traceback.print_exc()
