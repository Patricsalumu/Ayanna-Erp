#!/usr/bin/env python3
"""
Test rapide pour vérifier la création de produit avec les nouveaux paramètres
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.modules.boutique.controller.produit_controller import ProduitController
from ayanna_erp.database.database_manager import DatabaseManager
from decimal import Decimal

def test_create_product():
    """Test de création de produit avec tous les nouveaux paramètres"""
    try:
        # Initialisation
        db_manager = DatabaseManager()
        pos_id = 1  # ID fictif pour test
        controller = ProduitController(pos_id)
        
        # Test de création avec tous les paramètres
        with db_manager.get_session() as session:
            test_product = controller.create_product(
                session=session,
                nom="Produit Test",
                prix=Decimal("19.99"),
                category_id=1,  # ID fictif
                description="Description test",
                unit="pièce",
                stock_initial=10.0,
                cost=Decimal("10.00"),
                barcode="1234567890",
                image="data/images/produits/test.jpg",
                stock_min=5.0,
                account_id=1,  # ID fictif
                is_active=True
            )
            
            print(f"✅ Produit créé avec succès!")
            print(f"   ID: {test_product.id}")
            print(f"   Nom: {test_product.name}")
            print(f"   Prix: {test_product.price_unit}")
            print(f"   Image: {test_product.image}")
            print(f"   Stock min: {test_product.stock_min}")
            print(f"   Compte: {test_product.account_id}")
            print(f"   Actif: {test_product.is_active}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la création du produit: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🧪 Test de création de produit avec nouveaux paramètres")
    print("=" * 60)
    
    test_create_product()

if __name__ == "__main__":
    main()