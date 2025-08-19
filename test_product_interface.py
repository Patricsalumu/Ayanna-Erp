#!/usr/bin/env python3
"""
Script de test pour l'interface Produit avec les statistiques intégrées
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

# Ajouter le chemin vers le module
sys.path.append(os.path.dirname(__file__))

from ayanna_erp.modules.salle_fete.view.produit_index import ProduitIndex

class MockMainController:
    """Mock controller pour les tests"""
    def __init__(self):
        self.pos_id = 1

class MockUser:
    """Mock user pour les tests"""
    def __init__(self):
        self.id = 1
        self.name = "Test User"

def test_product_interface():
    """Test de l'interface des produits avec statistiques"""
    
    print("🧪 Test de l'interface Produit avec statistiques")
    print("=" * 60)
    
    # Créer l'application Qt
    app = QApplication(sys.argv)
    
    # Créer les mocks
    main_controller = MockMainController()
    current_user = MockUser()
    
    try:
        # Créer l'interface
        print("🏗️ Création de l'interface ProduitIndex...")
        product_widget = ProduitIndex(main_controller, current_user)
        
        # Afficher la fenêtre
        print("✅ Interface créée avec succès")
        print("🚀 Ouverture de la fenêtre...")
        
        product_widget.show()
        product_widget.resize(1200, 800)
        product_widget.setWindowTitle("Test - Gestion des Produits avec Statistiques")
        
        print("✅ Interface ouverte - vous pouvez maintenant tester:")
        print("  - Sélection d'un produit dans le tableau")
        print("  - Affichage des statistiques de vente")
        print("  - Liste des mouvements de stock récents")
        print("  - Filtres et recherche")
        
        # Lancer l'application
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_product_interface()
