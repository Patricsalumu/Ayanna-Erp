"""
Script de nettoyage des anciens modèles de stock
Supprime les anciennes tables et garde uniquement les modèles nécessaires
"""

import re
import os

def clean_old_stock_models():
    """Supprimer les anciennes classes de stock du fichier models.py"""
    
    file_path = r"c:\Ayanna ERP\Ayanna-Erp\ayanna_erp\modules\boutique\model\models.py"
    
    # Classes à supprimer (avec leurs noms exacts)
    classes_to_remove = [
        'ShopStock',
        'ShopWarehouse', 
        'ShopWarehouseStock',
        'ShopStockMovementNew',
        'ShopStockTransfer',
        'ShopStockTransferItem',
        'ShopInventory',
        'ShopInventoryItem',
        'ShopStockAlert',
        'ShopStockMovement'
    ]
    
    # Lire le fichier
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern pour détecter une classe complète
    for class_name in classes_to_remove:
        # Pattern pour capturer toute la classe depuis 'class' jusqu'à la prochaine classe ou fin de fichier
        pattern = rf'class {class_name}\(Base\):.*?(?=\n\nclass|\n\n$|\Z)'
        content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    # Nettoyer les lignes vides multiples
    content = re.sub(r'\n\n\n+', '\n\n', content)
    
    # Sauvegarder le fichier nettoyé
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Anciennes classes de stock supprimées de {file_path}")
    print(f"Classes supprimées: {', '.join(classes_to_remove)}")

if __name__ == "__main__":
    clean_old_stock_models()