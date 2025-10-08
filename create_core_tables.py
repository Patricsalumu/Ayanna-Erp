# -*- coding: utf-8 -*-
"""
Script pour créer les nouvelles tables core_products
"""

import sys
import os
sys.path.append(os.path.abspath('.'))

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.core.models import CoreProduct, CoreProductCategory, POSProductAccess


def create_core_product_tables():
    """Crée les nouvelles tables pour les produits centralisés"""
    
    print("=== CREATION DES TABLES CORE_PRODUCTS ===")
    
    try:
        db_manager = DatabaseManager()
        
        # Créer toutes les tables des modèles
        CoreProduct.metadata.create_all(db_manager.engine)
        CoreProductCategory.metadata.create_all(db_manager.engine)
        POSProductAccess.metadata.create_all(db_manager.engine)
        
        print("OK Tables créées avec succès:")
        print("  - core_products")
        print("  - core_product_categories")
        print("  - pos_product_access")
        
        return True
        
    except Exception as e:
        print(f"ERREUR lors de la création des tables: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if create_core_product_tables():
        print("\nOK Création des tables réussie")
        print("Vous pouvez maintenant exécuter la migration avec: python migrate_to_core_products.py")
    else:
        print("\nERREUR lors de la création des tables")