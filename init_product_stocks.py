#!/usr/bin/env python3
"""
Script d'initialisation des stocks pour tous les produits existants
Crée les entrées StockProduitEntrepot pour tous les produits dans tous les entrepôts
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.stock.models import StockWarehouse, StockProduitEntrepot, StockMovement
from ayanna_erp.modules.boutique.model.models import ShopProduct
from ayanna_erp.modules.boutique.helpers.stock_helper import BoutiqueStockHelper
from sqlalchemy import text
from decimal import Decimal
from datetime import datetime


def init_all_product_stocks():
    """Initialise les stocks pour tous les produits existants dans tous les entrepôts"""
    
    db_manager = DatabaseManager()
    
    with db_manager.get_session() as session:
        try:
            print("🔄 Initialisation des stocks pour tous les produits...")
            
            # Récupérer toutes les entreprises
            enterprises = session.execute(text("SELECT DISTINCT enterprise_id FROM core_pos_points")).fetchall()
            
            for enterprise_row in enterprises:
                enterprise_id = enterprise_row[0]
                print(f"\n📊 Traitement de l'entreprise ID: {enterprise_id}")
                
                # Récupérer tous les entrepôts de cette entreprise
                warehouses = session.query(StockWarehouse).filter(
                    StockWarehouse.entreprise_id == enterprise_id,
                    StockWarehouse.is_active == True
                ).all()
                
                print(f"   📦 {len(warehouses)} entrepôts trouvés")
                
                # Récupérer tous les produits boutique
                products = session.query(ShopProduct).filter(
                    ShopProduct.is_active == True
                ).all()
                
                print(f"   🛍️ {len(products)} produits trouvés")
                
                stock_helper = BoutiqueStockHelper(entreprise_id=enterprise_id)
                
                created_entries = 0
                updated_entries = 0
                
                for product in products:
                    for warehouse in warehouses:
                        # Vérifier si l'entrée existe déjà
                        existing_stock = session.query(StockProduitEntrepot).filter(
                            StockProduitEntrepot.product_id == product.id,
                            StockProduitEntrepot.warehouse_id == warehouse.id
                        ).first()
                        
                        if not existing_stock:
                            # Créer nouvelle entrée avec quantité 0
                            stock_entry = StockProduitEntrepot(
                                product_id=product.id,
                                warehouse_id=warehouse.id,
                                quantity=Decimal('0'),
                                reserved_quantity=Decimal('0'),
                                unit_cost=Decimal(str(product.price_unit)) if product.price_unit else Decimal('0'),
                                total_cost=Decimal('0'),
                                min_stock_level=Decimal('0'),
                                last_movement_date=None
                            )
                            session.add(stock_entry)
                            created_entries += 1
                            
                            print(f"   ✅ Créé: {product.name} -> {warehouse.name}")
                        else:
                            # Mettre à jour le coût unitaire si nécessaire
                            if existing_stock.unit_cost == 0 and product.price_unit:
                                existing_stock.unit_cost = Decimal(str(product.price_unit))
                                updated_entries += 1
                
                session.commit()
                print(f"   📈 Résultats: {created_entries} créées, {updated_entries} mises à jour")
            
            print(f"\n🎉 Initialisation terminée avec succès!")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
            session.rollback()
            raise


def verify_stock_initialization():
    """Vérifie que l'initialisation s'est bien passée"""
    
    db_manager = DatabaseManager()
    
    with db_manager.get_session() as session:
        # Compter les produits
        product_count = session.query(ShopProduct).filter(ShopProduct.is_active == True).count()
        
        # Compter les entrepôts
        warehouse_count = session.query(StockWarehouse).filter(StockWarehouse.is_active == True).count()
        
        # Compter les entrées stock
        stock_entries_count = session.query(StockProduitEntrepot).count()
        
        expected_entries = product_count * warehouse_count
        
        print(f"\n📊 Vérification:")
        print(f"   🛍️ Produits actifs: {product_count}")
        print(f"   📦 Entrepôts actifs: {warehouse_count}")
        print(f"   📈 Entrées stock créées: {stock_entries_count}")
        print(f"   🎯 Attendu: {expected_entries}")
        
        if stock_entries_count >= expected_entries:
            print("   ✅ Initialisation complète!")
        else:
            print("   ⚠️ Initialisation incomplète")
            
        # Afficher quelques exemples
        sample_stocks = session.query(StockProduitEntrepot).limit(5).all()
        print(f"\n📋 Exemples d'entrées créées:")
        for stock in sample_stocks:
            product = session.query(ShopProduct).get(stock.product_id)
            warehouse = session.query(StockWarehouse).get(stock.warehouse_id)
            print(f"   • {product.name if product else 'N/A'} -> {warehouse.name if warehouse else 'N/A'} (Qt: {stock.quantity})")


if __name__ == "__main__":
    print("🚀 Initialisation des stocks pour tous les produits...")
    
    # Initialiser les stocks
    init_all_product_stocks()
    
    # Vérifier le résultat
    verify_stock_initialization()
    
    print("\n✅ Script terminé!")