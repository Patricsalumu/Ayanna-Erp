#!/usr/bin/env python3
"""
Script de test pour l'interface Service avec les statistiques intégrées
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

# Ajouter le chemin vers le module
sys.path.append(os.path.dirname(__file__))

from ayanna_erp.modules.salle_fete.view.service_index import ServiceIndex

class MockMainController:
    """Mock controller pour les tests"""
    def __init__(self):
        self.pos_id = 1

class MockUser:
    """Mock user pour les tests"""
    def __init__(self):
        self.id = 1
        self.name = "Test User"

def test_service_interface():
    """Test de l'interface des services avec statistiques"""
    
    print("🧪 Test de l'interface Service avec statistiques")
    print("=" * 60)
    
    # Créer l'application Qt
    app = QApplication(sys.argv)
    
    # Créer les mocks
    main_controller = MockMainController()
    current_user = MockUser()
    
    try:
        # Créer l'interface
        print("🏗️ Création de l'interface ServiceIndex...")
        service_widget = ServiceIndex(main_controller, current_user)
        
        # Afficher la fenêtre
        print("✅ Interface créée avec succès")
        print("🚀 Ouverture de la fenêtre...")
        
        service_widget.show()
        service_widget.resize(1200, 800)
        service_widget.setWindowTitle("Test - Gestion des Services avec Statistiques")
        
        print("✅ Interface ouverte - vous pouvez maintenant tester:")
        print("  - Sélection d'un service dans le tableau")
        print("  - Affichage des statistiques d'utilisation")
        print("  - Liste des dernières utilisations")
        print("  - Filtres et recherche")
        
        # Lancer l'application
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_service_interface()
