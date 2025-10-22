import sys
sys.path.append('.')
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.core.models import CoreProduct
import os

print('=== Diagnostic des images produits ===')

# Vérifier le répertoire des images
image_dir = os.path.join(os.getcwd(), 'data', 'images', 'produits')
print(f'Répertoire images: {image_dir}')
print(f'Existe: {os.path.exists(image_dir)}')
if os.path.exists(image_dir):
    files = os.listdir(image_dir)
    print(f'Fichiers dans le répertoire: {files}')
else:
    print('❌ Répertoire n\'existe pas !')

print()

# Vérifier les produits dans la base
with DatabaseManager().get_session() as session:
    products = session.query(CoreProduct).filter_by(is_active=True).all()

    print(f'Nombre total de produits: {len(products)}')
    print()

    products_with_images = []
    products_without_images = []

    for product in products:
        if hasattr(product, 'image') and product.image and product.image.strip():
            products_with_images.append(product)
        else:
            products_without_images.append(product)

    print(f'Produits AVEC image: {len(products_with_images)}')
    for p in products_with_images:
        print(f'  - {p.name}: {repr(p.image)}')

    print()
    print(f'Produits SANS image: {len(products_without_images)}')
    for p in products_without_images[:5]:  # Montrer seulement les 5 premiers
        print(f'  - {p.name}: {repr(getattr(p, "image", None))}')
    if len(products_without_images) > 5:
        print(f'  ... et {len(products_without_images) - 5} autres')