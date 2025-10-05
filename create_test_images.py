#!/usr/bin/env python3
"""
Créer des images de test plus réalistes pour les produits
"""

import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QBrush, QLinearGradient
from PyQt6.QtCore import Qt

def create_realistic_product_images():
    """Créer plusieurs images de test réalistes"""
    app = QApplication([])  # Nécessaire pour QPixmap
    
    try:
        # Créer le dossier images s'il n'existe pas
        images_dir = os.path.join("data", "images", "produits")
        os.makedirs(images_dir, exist_ok=True)
        
        # Image 1: Produit électronique (bleu)
        create_product_image(
            os.path.join(images_dir, "smartphone.png"),
            "📱", "SMARTPHONE", 
            QColor("#3498DB"), QColor("#2980B9")
        )
        
        # Image 2: Produit alimentaire (vert)
        create_product_image(
            os.path.join(images_dir, "pomme.png"),
            "🍎", "POMME BIO", 
            QColor("#27AE60"), QColor("#229954")
        )
        
        # Image 3: Vêtement (violet)
        create_product_image(
            os.path.join(images_dir, "tshirt.png"),
            "👕", "T-SHIRT", 
            QColor("#9B59B6"), QColor("#8E44AD")
        )
        
        # Image 4: Livre (orange)
        create_product_image(
            os.path.join(images_dir, "livre.png"),
            "📚", "LIVRE", 
            QColor("#E67E22"), QColor("#D35400")
        )
        
        print("✅ Images de test créées avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des images: {e}")
    finally:
        app.quit()

def create_product_image(filepath, emoji, text, color1, color2):
    """Créer une image de produit avec dégradé et emoji"""
    pixmap = QPixmap(200, 200)
    painter = QPainter(pixmap)
    
    # Dégradé de fond
    gradient = QLinearGradient(0, 0, 200, 200)
    gradient.setColorAt(0, color1)
    gradient.setColorAt(1, color2)
    painter.fillRect(pixmap.rect(), QBrush(gradient))
    
    # Emoji en grand
    painter.setPen(QColor("white"))
    font = QFont()
    font.setPointSize(48)
    painter.setFont(font)
    painter.drawText(50, 80, emoji)
    
    # Texte du produit
    font.setPointSize(14)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect().adjusted(10, 120, -10, -20), Qt.AlignmentFlag.AlignCenter, text)
    
    painter.end()
    pixmap.save(filepath)
    print(f"📷 Image créée: {filepath}")

if __name__ == "__main__":
    create_realistic_product_images()