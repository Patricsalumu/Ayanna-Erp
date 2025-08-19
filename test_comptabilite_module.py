#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test d'import et d'initialisation du module Comptabilité
"""

import sys
import os

# Ajouter le répertoire racine au PYTHONPATH
sys.path.insert(0, os.path.abspath('.'))

def test_comptabilite_import():
    """Test d'import du module comptabilité"""
    try:
        from ayanna_erp.modules.comptabilite.comptabilite_window import ComptabiliteWindow
        print("✅ Import de ComptabiliteWindow réussi")
        return True
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False

def test_comptabilite_creation():
    """Test de création d'une instance de ComptabiliteWindow"""
    try:
        from PyQt6.QtWidgets import QApplication, QWidget
        from ayanna_erp.modules.comptabilite.comptabilite_window import ComptabiliteWindow
        
        # Créer une application Qt si elle n'existe pas
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Créer un widget parent
        parent = QWidget()
        
        # Créer la fenêtre comptabilité
        window = ComptabiliteWindow(parent=parent, session=None, entreprise_id=1)
        print("✅ Création de ComptabiliteWindow réussie")
        print(f"   - Type: {type(window)}")
        print(f"   - Parent: {window.parent()}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur de création: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Test du module Comptabilité...")
    
    success = True
    success &= test_comptabilite_import()
    success &= test_comptabilite_creation()
    
    if success:
        print("\n✅ Tous les tests sont passés!")
    else:
        print("\n❌ Certains tests ont échoué")
        sys.exit(1)
