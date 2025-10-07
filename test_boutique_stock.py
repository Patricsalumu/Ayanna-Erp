#!/usr/bin/env python3
"""
Test simple du nouveau système de stock boutique
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.modules.boutique.helpers.stock_helper import BoutiqueStockHelper
from ayanna_erp.database.database_manager import DatabaseManager

def test_boutique_stock():
    """Test de l'affichage des stocks boutique"""
    
    db = DatabaseManager()
    helper = BoutiqueStockHelper(entreprise_id=1)
    
    with db.get_session() as session:
        # Test récupération entrepôt boutique
        warehouse_id = helper.get_boutique_warehouse_id(session)
        print(f"🏪 Entrepôt boutique ID: {warehouse_id}")
        
        # Test récupération produits avec stocks
        products = helper.get_all_products_for_display(session)
        print(f"📦 {len(products)} produits trouvés")
        
        print("\n📋 Détail des stocks:")
        for product in products:
            print(f"  • {product['product_name']}: {product['quantite']} unités")
            print(f"    Prix: {product['product_price']} | Stock min: {product['min_stock_level']}")
            print(f"    Entrepôt: {product['warehouse_id']}")
            print()

if __name__ == "__main__":
    test_boutique_stock()