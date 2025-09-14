#!/usr/bin/env python3
"""
Test pour l'interface des rapports redesignée
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.salle_fete.view.rapport_index import RapportIndex

def test_rapport_interface():
    """Test pour lancer l'interface des rapports"""
    print("=== Test de l'interface des rapports redesignée ===")
    
    app = QApplication(sys.argv)
    
    try:
        # Initialiser la base de données
        db_manager = DatabaseManager()
        
        # Créer et afficher la fenêtre
        current_user = {"id": 1, "nom": "Test User"}
        window = RapportIndex(db_manager, current_user)
        window.resize(1400, 800)
        window.show()
        
        print("✅ Interface des rapports lancée avec succès")
        print("Fonctionnalités disponibles:")
        print("  📅 Événements du mois - Graphique barres + filtres mois/année")
        print("  📊 Événements de l'année - Graphique barres par mois + filtre année")
        print("  💰 Rapport financier - Courbes recettes/dépenses + sélecteur période")
        print("\nChaque onglet contient:")
        print("  - Graphiques interactifs avec matplotlib")
        print("  - Statistiques détaillées")
        print("  - Comparaisons avec périodes précédentes")
        print("  - TOP 5 des services")
        print("  - Analyses financières complètes")
        
        # Lancer l'application
        app.exec()
        
    except Exception as e:
        print(f"❌ Erreur lors du lancement: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rapport_interface()