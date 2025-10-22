import sys
sys.path.append('.')
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.core.models import CoreProduct
from PyQt6.QtWidgets import QApplication, QLabel
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import os

print('=== Test final du chargement d\'images ===')

app = QApplication([])

with DatabaseManager().get_session() as session:
    # Tester avec Simba qui a maintenant une image
    product = session.query(CoreProduct).filter_by(name='Simba').first()
    if product:
        print(f'Test avec produit: {product.name}')
        print(f'Champ image: {repr(product.image)}')

        # Simuler exactement la logique de create_product_card
        image_loaded = False
        if hasattr(product, 'image') and product.image and product.image.strip():
            image_filename = product.image.strip()
            base_image_dir = os.path.join(os.getcwd(), 'data', 'images', 'produits')

            if image_filename.startswith('data/images/produits/'):
                image_path = os.path.join(os.getcwd(), image_filename)
            elif os.path.isabs(image_filename):
                image_path = image_filename
            else:
                image_path = os.path.join(base_image_dir, image_filename)

            print(f'Chemin calculé: {image_path}')
            print(f'Fichier existe: {os.path.exists(image_path)}')

            if os.path.exists(image_path) and os.path.isfile(image_path):
                pixmap = QPixmap(image_path)
                print(f'Pixmap valide: {not pixmap.isNull()}')
                if not pixmap.isNull():
                    print(f'Taille originale: {pixmap.width()}x{pixmap.height()}')
                    scaled_pixmap = pixmap.scaled(180, 140, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    print(f'Taille redimensionnée: {scaled_pixmap.width()}x{scaled_pixmap.height()}')
                    image_loaded = True
                    print('✅ IMAGE CHARGÉE AVEC SUCCÈS')
                else:
                    print('❌ Pixmap invalide')
            else:
                print('❌ Fichier n\'existe pas')
        else:
            print('❌ Pas de champ image')

        print(f'Résultat final: {"SUCCÈS" if image_loaded else "ÉCHEC"}')
    else:
        print('❌ Produit Simba non trouvé')

print()
print('=== Test terminé ===')