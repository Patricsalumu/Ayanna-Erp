#!/usr/bin/env python3
"""
Test rapide pour vérifier la création de produit avec tous les paramètres
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.modules.boutique.controller.boutique_controller import BoutiqueController
from ayanna_erp.modules.boutique.controller.produit_controller import ProduitController
from ayanna_erp.database.database_manager import DatabaseManager

def test_create_product():
    """Test de création de produit avec tous les paramètres"""
    try:
        # Initialisation
        db_manager = DatabaseManager()
        pos_id = 1  # ID fictif pour test
        boutique_controller = BoutiqueController(pos_id)
        produit_controller = ProduitController(pos_id)
        
        # Test de création de produit
        with db_manager.get_session() as session:
            # Créer d'abord une catégorie
            category = boutique_controller.create_category(
                session=session,
                nom="Électronique"
            )
            
            # Créer le produit
            test_product = produit_controller.create_product(
                session=session,
                nom="Smartphone Test",
                description="Un téléphone pour test",
                prix=500.0,
                category_id=category.id,
                image="test.jpg",
                stock_min=5,
                account_id=1,
                is_active=True
            )
            
            print(f"✅ Produit créé avec succès!")
            print(f"   ID: {test_product.id}")
            print(f"   Nom: {test_product.name}")
            print(f"   Prix: {test_product.price_unit} USD")
            print(f"   Catégorie ID: {test_product.category_id}")
            print(f"   POS ID: {test_product.pos_id}")
            print(f"   Stock Min: {test_product.stock_min}")
            print(f"   Actif: {test_product.is_active}")
            print(f"   Image: {test_product.image}")
            print(f"   Description: {test_product.description}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la création du produit: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🧪 Test de création de produit avec tous les paramètres")
    print("=" * 60)
    
    test_create_product()

if __name__ == "__main__":
    main()