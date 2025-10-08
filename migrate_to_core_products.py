# -*- coding: utf-8 -*-
"""
Script de migration de shop_products vers core_products
Centralise les produits par entreprise au lieu de par POS
"""

import sys
import os
sys.path.append(os.path.abspath('.'))

from ayanna_erp.database.database_manager import DatabaseManager, POSPoint
from ayanna_erp.modules.boutique.model.models import ShopProduct
from ayanna_erp.modules.core.models import CoreProduct, CoreProductCategory, POSProductAccess
from sqlalchemy import text


def migrate_products_to_centralized():
    """
    Migre les produits de shop_products vers core_products
    Logique:
    1. Récupérer tous les produits shop_products
    2. Pour chaque produit, déterminer l'entreprise_id via le POS
    3. Créer le produit dans core_products
    4. Créer la liaison POS-Produit dans pos_product_access
    """
    
    print("=== MIGRATION SHOP_PRODUCTS VERS CORE_PRODUCTS ===")
    
    try:
        db_manager = DatabaseManager()
        
        with db_manager.get_session() as session:
            # 1. Récupérer tous les produits existants
            shop_products = session.query(ShopProduct).all()
            print(f"Produits à migrer: {len(shop_products)}")
            
            if not shop_products:
                print("Aucun produit à migrer")
                return
            
            # 2. Créer une catégorie par défaut si nécessaire
            default_category = session.query(CoreProductCategory).filter_by(
                name="Produits Généraux"
            ).first()
            
            if not default_category:
                # Déterminer l'entreprise_id (on prend celui du premier POS)
                first_pos = session.query(POSPoint).first()
                if not first_pos:
                    print("ERREUR: Aucun POS trouvé pour déterminer l'entreprise")
                    return
                
                default_category = CoreProductCategory(
                    entreprise_id=first_pos.enterprise_id,
                    name="Produits Généraux",
                    description="Catégorie par défaut pour les produits migrés"
                )
                session.add(default_category)
                session.flush()  # Pour récupérer l'ID
                print(f"Catégorie par défaut créée: {default_category.name}")
            
            # 3. Migrer chaque produit
            migrated_count = 0
            pos_access_count = 0
            
            for shop_product in shop_products:
                try:
                    # Récupérer les infos du POS
                    pos = session.query(POSPoint).filter_by(id=shop_product.pos_id).first()
                    if not pos:
                        print(f"  AVERTISSEMENT: POS {shop_product.pos_id} non trouvé pour le produit {shop_product.name}")
                        continue
                    
                    # Vérifier si le produit existe déjà dans core_products
                    existing_product = session.query(CoreProduct).filter_by(
                        entreprise_id=pos.enterprise_id,
                        code=shop_product.code
                    ).first()
                    
                    if existing_product:
                        print(f"  Produit existant: {shop_product.name} (utilisé)")
                        core_product = existing_product
                    else:
                        # Créer le nouveau produit centralisé
                        core_product = CoreProduct(
                            entreprise_id=pos.enterprise_id,
                            category_id=default_category.id,
                            code=shop_product.code,
                            name=shop_product.name,
                            description=shop_product.description,
                            image=shop_product.image,
                            barcode=shop_product.barcode,
                            cost=shop_product.cost,
                            cost_price=shop_product.cost_price,
                            price_unit=shop_product.price_unit,
                            sale_price=shop_product.sale_price,
                            unit=shop_product.unit,
                            account_id=shop_product.account_id,
                            is_active=shop_product.is_active,
                            created_at=shop_product.created_at
                        )
                        
                        session.add(core_product)
                        session.flush()  # Pour récupérer l'ID
                        migrated_count += 1
                        print(f"  Migré: {shop_product.name} -> Entreprise {pos.enterprise_id}")
                    
                    # Créer la liaison POS-Produit
                    existing_access = session.query(POSProductAccess).filter_by(
                        pos_id=shop_product.pos_id,
                        product_id=core_product.id
                    ).first()
                    
                    if not existing_access:
                        pos_access = POSProductAccess(
                            pos_id=shop_product.pos_id,
                            product_id=core_product.id,
                            is_available=shop_product.is_active
                        )
                        session.add(pos_access)
                        pos_access_count += 1
                        print(f"    Liaison créée: POS {shop_product.pos_id} <-> Produit {core_product.id}")
                    
                except Exception as e:
                    print(f"  ERREUR avec le produit {shop_product.name}: {e}")
                    continue
            
            # 4. Migrer aussi les données de stock de shop_products vers stock_produits_entrepot
            print(f"\n--- Migration des stocks ---")
            migrated_stocks = 0
            
            for shop_product in shop_products:
                if shop_product.stock_quantity and shop_product.stock_quantity > 0:
                    try:
                        pos = session.query(POSPoint).filter_by(id=shop_product.pos_id).first()
                        if not pos:
                            continue
                        
                        # Trouver le produit migré
                        core_product = session.query(CoreProduct).filter_by(
                            entreprise_id=pos.enterprise_id,
                            code=shop_product.code
                        ).first()
                        
                        if core_product:
                            # Trouver l'entrepôt associé au POS
                            from ayanna_erp.modules.stock.helpers import POSWarehouseHelper
                            warehouse = POSWarehouseHelper.get_main_warehouse_for_pos(shop_product.pos_id)
                            
                            if warehouse:
                                from ayanna_erp.modules.stock.models import StockProduitEntrepot
                                
                                # Vérifier si l'entrée existe déjà
                                existing_stock = session.query(StockProduitEntrepot).filter_by(
                                    product_id=core_product.id,
                                    warehouse_id=warehouse.id
                                ).first()
                                
                                if not existing_stock:
                                    stock_entry = StockProduitEntrepot(
                                        product_id=core_product.id,
                                        warehouse_id=warehouse.id,
                                        quantity=shop_product.stock_quantity,
                                        min_stock_level=shop_product.stock_min or 0,
                                        unit_cost=shop_product.cost or 0
                                    )
                                    session.add(stock_entry)
                                    migrated_stocks += 1
                                    print(f"    Stock migré: {core_product.name} -> {shop_product.stock_quantity} unités")
                    
                    except Exception as e:
                        print(f"    ERREUR migration stock pour {shop_product.name}: {e}")
                        continue
            
            # 5. Valider les changements
            session.commit()
            
            print(f"\n=== RESUME MIGRATION ===")
            print(f"Produits migrés vers core_products: {migrated_count}")
            print(f"Liaisons POS-Produits créées: {pos_access_count}")
            print(f"Stocks migrés: {migrated_stocks}")
            print(f"Catégorie par défaut: {default_category.name}")
            
            return True
            
    except Exception as e:
        print(f"ERREUR lors de la migration: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_migration():
    """Vérifie que la migration s'est bien passée"""
    
    print("\n=== VERIFICATION MIGRATION ===")
    
    try:
        db_manager = DatabaseManager()
        
        with db_manager.get_session() as session:
            # Compter les produits
            core_products_count = session.query(CoreProduct).count()
            shop_products_count = session.query(ShopProduct).count()
            pos_access_count = session.query(POSProductAccess).count()
            
            print(f"Produits dans core_products: {core_products_count}")
            print(f"Produits dans shop_products (origine): {shop_products_count}")
            print(f"Liaisons POS-Produits: {pos_access_count}")
            
            # Vérifier quelques produits
            core_products = session.query(CoreProduct).limit(3).all()
            for product in core_products:
                print(f"\nProduit: {product.name}")
                print(f"  Entreprise ID: {product.entreprise_id}")
                print(f"  Code: {product.code}")
                print(f"  Prix: {product.price_unit}")
                
                # Vérifier les POS associés
                pos_links = session.query(POSProductAccess).filter_by(product_id=product.id).all()
                for link in pos_links:
                    print(f"  Disponible sur POS: {link.pos_id}")
            
            return True
            
    except Exception as e:
        print(f"ERREUR lors de la vérification: {e}")
        return False


if __name__ == "__main__":
    print("Démarrage de la migration shop_products -> core_products")
    
    # Effectuer la migration
    if migrate_products_to_centralized():
        print("\n✓ Migration réussie")
        
        # Vérifier
        if verify_migration():
            print("✓ Vérification réussie")
        else:
            print("✗ Problème lors de la vérification")
    else:
        print("✗ Échec de la migration")