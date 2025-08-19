#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test final du module Comptabilité
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

# Ajouter le répertoire racine au PYTHONPATH
sys.path.insert(0, os.path.abspath('.'))

def test_comptabilite_final():
    """Test final du module comptabilité"""
    try:
        from ayanna_erp.modules.comptabilite.comptabilite_window import ComptabiliteWindow
        from ayanna_erp.database.database_manager import DatabaseManager
        
        # Créer une application Qt
        app = QApplication(sys.argv)
        
        # Simuler un utilisateur
        class MockUser:
            def __init__(self):
                self.enterprise_id = 1
                self.username = "admin"
                
        user = MockUser()
        
        # Créer la fenêtre comptabilité
        window = ComptabiliteWindow(user)
        print("✅ ComptabiliteWindow créée avec succès")
        print(f"   - Type: {type(window)}")
        print(f"   - Titre: {window.windowTitle()}")
        print(f"   - Taille: {window.size()}")
        print(f"   - Nombre d'onglets: {window.tabs.count()}")
        
        # Lister les onglets
        for i in range(window.tabs.count()):
            tab_text = window.tabs.tabText(i)
            print(f"   - Onglet {i+1}: {tab_text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Test final du module Comptabilité...")
    
    success = test_comptabilite_final()
    
    if success:
        print("\n✅ Test réussi! Le module Comptabilité est prêt!")
    else:
        print("\n❌ Test échoué")
        sys.exit(1)
