#!/usr/bin/env python3
"""
Test rapide pour vérifier le ComboBox des comptes comptables
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from ayanna_erp.modules.boutique.view.produit_index import ProductFormDialog
from ayanna_erp.modules.boutique.controller.produit_controller import ProduitController
from ayanna_erp.database.database_manager import DatabaseManager

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test ComboBox Comptes Comptables")
        self.setGeometry(100, 100, 300, 200)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Bouton pour ouvrir le formulaire
        btn = QPushButton("Ouvrir Formulaire Produit")
        btn.clicked.connect(self.open_product_form)
        layout.addWidget(btn)
        
        # Simuler un pos_id et contrôleur
        self.pos_id = 1  # ID fictif
        self.produit_controller = ProduitController(self.pos_id)
    
    def open_product_form(self):
        """Ouvrir le formulaire de produit pour tester le ComboBox"""
        try:
            dialog = ProductFormDialog(self, self.produit_controller)
            dialog.exec()
        except Exception as e:
            print(f"❌ Erreur lors de l'ouverture du formulaire: {e}")
            import traceback
            traceback.print_exc()

def main():
    app = QApplication(sys.argv)
    
    # Tester la base de données
    try:
        db_manager = DatabaseManager()
        print("✅ Connexion à la base de données réussie")
    except Exception as e:
        print(f"❌ Erreur de connexion à la base de données: {e}")
        return
    
    # Créer et afficher la fenêtre de test
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()