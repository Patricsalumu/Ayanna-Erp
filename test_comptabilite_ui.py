#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test d'ouverture du module Comptabilité depuis l'interface principale
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer

# Ajouter le répertoire racine au PYTHONPATH
sys.path.insert(0, os.path.abspath('.'))

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Comptabilité")
        self.setGeometry(100, 100, 400, 300)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Bouton pour ouvrir la comptabilité
        btn = QPushButton("Ouvrir Module Comptabilité")
        btn.clicked.connect(self.open_comptabilite)
        layout.addWidget(btn)
        
        # Initialiser la base de données
        from ayanna_erp.database.database_manager import DatabaseManager
        self.db_manager = DatabaseManager()
        
    def open_comptabilite(self):
        print("🔍 Tentative d'ouverture du module Comptabilité...")
        try:
            from ayanna_erp.modules.comptabilite.comptabilite_window import ComptabiliteWindow
            print("✅ Import réussi")
            
            # Créer la fenêtre comptabilité
            self.comptabilite_window = ComptabiliteWindow(
                parent=self, 
                session=self.db_manager.get_session(), 
                entreprise_id=1
            )
            print("✅ Création réussie")
            
            # Afficher la fenêtre
            self.comptabilite_window.show()
            print("✅ Affichage demandé")
            
            # Vérifier si la fenêtre est visible
            QTimer.singleShot(100, self.check_window_visibility)
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
    
    def check_window_visibility(self):
        if hasattr(self, 'comptabilite_window'):
            visible = self.comptabilite_window.isVisible()
            print(f"📊 Fenêtre visible: {visible}")
            if visible:
                print("✅ Module Comptabilité ouvert avec succès!")
            else:
                print("⚠️ Fenêtre créée mais non visible")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    print("🚀 Fenêtre de test ouverte")
    print("Cliquez sur le bouton pour tester l'ouverture du module Comptabilité")
    
    sys.exit(app.exec())
