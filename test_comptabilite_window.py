#!/usr/bin/env python3
"""
Test de chargement du module comptabilité
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from PyQt6.QtWidgets import QApplication
from ayanna_erp.database.database_manager import DatabaseManager

def test_comptabilite_window():
    """Test de création de la fenêtre comptabilité"""
    print("🧪 Test de chargement du module comptabilité...")
    
    try:
        # Initialiser la base de données
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        # Importer la classe ComptabiliteWindow
        from ayanna_erp.modules.comptabilite.comptabilite_window import ComptabiliteWindow
        print("✅ Import de ComptabiliteWindow réussi")
        
        # Créer une application Qt
        app = QApplication([])
        
        # Créer la fenêtre comptabilité
        comptabilite_window = ComptabiliteWindow(session=session, entreprise_id=1)
        print("✅ Création de ComptabiliteWindow réussie")
        
        # Afficher la fenêtre
        comptabilite_window.show()
        print("✅ Affichage de la fenêtre réussi")
        
        # Vérifier le nombre d'onglets
        nb_tabs = comptabilite_window.tabs.count()
        print(f"📋 Nombre d'onglets chargés: {nb_tabs}")
        
        # Lister les onglets
        for i in range(nb_tabs):
            tab_name = comptabilite_window.tabs.tabText(i)
            print(f"   - Onglet {i+1}: {tab_name}")
        
        app.quit()
        session.close()
        print("🎉 Test réussi!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_comptabilite_window()
