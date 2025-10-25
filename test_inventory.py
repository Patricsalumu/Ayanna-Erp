#!/usr/bin/env python3
"""
Tester la création d'un inventaire
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from ayanna_erp.modules.stock.controllers.inventaire_controller import InventaireController

def test_create_inventory():
    controller = InventaireController(entreprise_id=1)

    # Tester la création d'un inventaire pour l'entrepôt 1
    inventory_data = {
        'session_name': 'Test inventaire complet',
        'warehouse_id': 1,
        'inventory_type': 'inventaire complet',
        'notes': 'Test automatique'
    }

    print("Création d'un inventaire...")
    from ayanna_erp.database.database_manager import DatabaseManager
    db_manager = DatabaseManager()

    with db_manager.get_session() as session:
        # D'abord, testons get_products_for_inventory
        print("Récupération des produits pour l'entrepôt 1...")
        all_products = controller.get_products_for_inventory(1)
        print(f"📦 Produits disponibles: {len(all_products)}")
        for p in all_products[:3]:  # Afficher les 3 premiers
            print(f"  - {p['product_name']} (ID: {p['product_id']})")

        inventory = controller.create_inventory_session(session, inventory_data)
        session.commit()  # S'assurer que tout est sauvegardé

        if inventory:
            print(f"✅ Inventaire créé: {inventory.reference} (ID: {inventory.id})")

            # Récupérer les produits
            products = controller.get_inventory_products(session, inventory.id)
            print(f"📦 Produits dans l'inventaire: {len(products)}")
            for p in products:
                print(f"  - {p['product_name']} (Stock sys: {p['system_stock']}, Prix vente: {p.get('selling_price', 0)})")

        else:
            print("❌ Échec de création de l'inventaire")

if __name__ == "__main__":
    test_create_inventory()