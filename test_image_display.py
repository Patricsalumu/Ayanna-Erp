#!/usr/bin/env python3
"""
Test pour vérifier l'affichage des images dans les détails de produit
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter, QColor
from ayanna_erp.modules.boutique.view.produit_index import ProduitIndex
from ayanna_erp.database.database_manager import DatabaseManager

def create_test_image():
    """Créer une image de test simple"""
    try:
        # Créer le dossier images s'il n'existe pas
        images_dir = os.path.join("data", "images", "produits")
        os.makedirs(images_dir, exist_ok=True)
        
        # Créer une image de test simple avec QPixmap
        test_image_path = os.path.join(images_dir, "test_produit.png")
        
        # Créer un QPixmap de 200x200 pixels
        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("#3498DB"))  # Fond bleu
        
        # Dessiner quelque chose dessus
        painter = QPainter(pixmap)
        painter.setPen(QColor("white"))
        painter.setFont(painter.font())
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "PRODUIT\nTEST")
        painter.end()
        
        # Sauvegarder l'image
        pixmap.save(test_image_path)
        print(f"✅ Image de test créée: {test_image_path}")
        
        return test_image_path
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'image de test: {e}")
        return None

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Affichage Images Produits")
        self.setGeometry(100, 100, 1000, 700)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Boutons de test
        buttons_layout = QHBoxLayout()
        
        create_image_btn = QPushButton("📷 Créer Image Test")
        create_image_btn.clicked.connect(self.create_test_image)
        buttons_layout.addWidget(create_image_btn)
        
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.clicked.connect(self.refresh_products)
        buttons_layout.addWidget(refresh_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        # Widget produits
        try:
            self.pos_id = 1  # ID fictif
            self.current_user = {"id": 1, "name": "Test User"}  # Utilisateur fictif
            self.produit_widget = ProduitIndex(self.pos_id, self.current_user)
            layout.addWidget(self.produit_widget)
        except Exception as e:
            print(f"❌ Erreur lors de la création du widget produits: {e}")
    
    def create_test_image(self):
        """Créer une image de test"""
        image_path = create_test_image()
        if image_path:
            print(f"Image créée: {image_path}")
        else:
            print("Échec de création de l'image")
    
    def refresh_products(self):
        """Actualiser la liste des produits"""
        if hasattr(self, 'produit_widget'):
            self.produit_widget.refresh_products()

def main():
    app = QApplication(sys.argv)
    
    # Tester la base de données
    try:
        db_manager = DatabaseManager()
        print("✅ Connexion à la base de données réussie")
    except Exception as e:
        print(f"❌ Erreur de connexion à la base de données: {e}")
        return
    
    # Créer une image de test automatiquement
    create_test_image()
    
    # Créer et afficher la fenêtre de test
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()