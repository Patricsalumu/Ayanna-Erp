"""
Test simple du widget Commandes
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from ayanna_erp.modules.boutique.view.commandes_index import CommandesIndexWidget
from ayanna_erp.modules.boutique.controller.boutique_controller import BoutiqueController

def test_commandes_widget():
    """Test simple du widget Commandes"""
    
    print("🧪 Test du widget Commandes")
    print("=" * 30)
    
    app = QApplication(sys.argv)
    
    try:
        # Créer un utilisateur de test
        test_user = type('User', (), {
            'id': 1, 
            'username': 'test_user',
            'role': 'admin'
        })()
        
        # Créer le contrôleur boutique
        print("🛠️ Création du contrôleur boutique...")
        boutique_controller = BoutiqueController(pos_id=1)
        
        # Créer le widget Commandes
        print("📋 Création du widget Commandes...")
        commandes_widget = CommandesIndexWidget(boutique_controller, test_user)
        
        # Créer une fenêtre de test
        window = QMainWindow()
        window.setWindowTitle("Test - Onglet Commandes")
        window.setCentralWidget(commandes_widget)
        window.resize(1200, 800)
        
        print("✅ Widget Commandes créé avec succès")
        print("📊 Interface de gestion des commandes prête")
        
        # Afficher la fenêtre
        window.show()
        
        # Test de chargement des données
        try:
            commandes_widget.load_commandes()
            print("✅ Chargement des commandes réussi")
        except Exception as e:
            print(f"⚠️ Erreur lors du chargement: {e}")
        
        # Fermer après 5 secondes
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(5000, app.quit)
        
        app.exec()
        
        print("✅ Test du widget terminé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_commandes_widget()
    sys.exit(0 if success else 1)