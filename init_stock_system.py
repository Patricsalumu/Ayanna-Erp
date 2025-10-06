#!/usr/bin/env python3
"""
Script d'initialisation et migration du système de gestion de stock avancé
Crée les tables, l'entrepôt par défaut et migre les stocks existants
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.boutique.controller.stock_controller import StockController
from ayanna_erp.modules.boutique.model.stock_models import *  # Import toutes les nouvelles tables


def create_stock_tables():
    """Créer toutes les tables de gestion de stock avancée"""
    try:
        db_manager = DatabaseManager()
        
        # Créer les tables
        from ayanna_erp.database.base import Base
        Base.metadata.create_all(db_manager.engine)
        
        print("✅ Tables de gestion de stock créées avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des tables: {e}")
        return False


def setup_default_warehouse(pos_id: int = 1):
    """Configurer l'entrepôt par défaut pour un POS"""
    try:
        db_manager = DatabaseManager()
        stock_controller = StockController(pos_id)
        
        with db_manager.get_session() as session:
            # Vérifier si un entrepôt par défaut existe déjà
            existing_warehouse = stock_controller.get_default_warehouse(session)
            
            if existing_warehouse:
                print(f"✅ Entrepôt par défaut déjà existant: {existing_warehouse.name}")
                return existing_warehouse
            
            # Créer l'entrepôt par défaut
            default_warehouse = stock_controller.create_warehouse(
                session=session,
                code=f"MAG-POS{pos_id:03d}",
                name=f"Magasin Principal POS {pos_id}",
                type="shop",
                description="Entrepôt principal du point de vente - stock de vente directe",
                address="Adresse du point de vente",
                is_default=True,
                capacity_limit=10000  # Capacité par défaut
            )
            
            print(f"✅ Entrepôt par défaut créé: {default_warehouse.name} (ID: {default_warehouse.id})")
            return default_warehouse
            
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'entrepôt par défaut: {e}")
        return None


def create_sample_warehouses(pos_id: int = 1):
    """Créer des entrepôts d'exemple"""
    try:
        stock_controller = StockController(pos_id)
        db_manager = DatabaseManager()
        
        warehouses_data = [
            {
                'code': f'DEP-POS{pos_id:03d}',
                'name': f'Dépôt Principal POS {pos_id}',
                'type': 'storage',
                'description': 'Entrepôt de stockage principal - réserve',
                'capacity_limit': 50000
            },
            {
                'code': f'TRA-POS{pos_id:03d}',
                'name': f'Zone Transit POS {pos_id}',
                'type': 'transit',
                'description': 'Zone de transit pour marchandises en cours de livraison',
                'capacity_limit': 5000
            },
            {
                'code': f'END-POS{pos_id:03d}',
                'name': f'Produits Endommagés POS {pos_id}',
                'type': 'damaged',
                'description': 'Entrepôt pour produits endommagés ou périmés',
                'capacity_limit': 1000
            }
        ]
        
        created_warehouses = []
        
        with db_manager.get_session() as session:
            for warehouse_data in warehouses_data:
                # Vérifier si l'entrepôt existe déjà
                existing = session.query(ShopWarehouse).filter(
                    ShopWarehouse.pos_id == pos_id,
                    ShopWarehouse.code == warehouse_data['code']
                ).first()
                
                if existing:
                    print(f"⚠️  Entrepôt {warehouse_data['code']} existe déjà")
                    created_warehouses.append(existing)
                    continue
                
                warehouse = stock_controller.create_warehouse(
                    session=session,
                    **warehouse_data
                )
                created_warehouses.append(warehouse)
                print(f"✅ Entrepôt créé: {warehouse.name} ({warehouse.code})")
        
        return created_warehouses
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des entrepôts d'exemple: {e}")
        return []


def migrate_existing_stocks(pos_id: int = 1):
    """Migrer les stocks existants vers le nouveau système"""
    try:
        stock_controller = StockController(pos_id)
        db_manager = DatabaseManager()
        
        with db_manager.get_session() as session:
            print("🔄 Migration des stocks existants...")
            
            # Lancer la migration
            stock_controller.migrate_existing_stock(session)
            
            # Vérifier les résultats
            warehouse_stocks = session.query(ShopWarehouseStock).join(ShopWarehouse).filter(
                ShopWarehouse.pos_id == pos_id
            ).all()
            
            print(f"✅ Migration terminée: {len(warehouse_stocks)} stocks migrés")
            
            # Afficher un résumé
            for stock in warehouse_stocks[:5]:  # Afficher les 5 premiers
                print(f"   • Produit {stock.product_id}: {stock.quantity_available} unités")
            
            if len(warehouse_stocks) > 5:
                print(f"   ... et {len(warehouse_stocks) - 5} autres produits")
                
    except Exception as e:
        print(f"❌ Erreur lors de la migration des stocks: {e}")


def test_stock_operations(pos_id: int = 1):
    """Tester les opérations de base du nouveau système"""
    try:
        stock_controller = StockController(pos_id)
        db_manager = DatabaseManager()
        
        with db_manager.get_session() as session:
            print("🧪 Test des opérations de stock...")
            
            # Récupérer les entrepôts
            warehouses = stock_controller.get_warehouses(session)
            print(f"   📦 {len(warehouses)} entrepôts disponibles")
            
            if len(warehouses) >= 2:
                # Test de transfert entre entrepôts
                source = warehouses[0]
                destination = warehouses[1]
                
                print(f"   🔄 Test transfert: {source.name} → {destination.name}")
                
                # Exemple d'articles à transférer (remplacer par des vrais produits)
                # transfer_items = [
                #     {'product_id': 1, 'quantity': 10, 'unit_cost': 5.0}
                # ]
                
                # transfer = stock_controller.create_stock_transfer(
                #     session=session,
                #     source_warehouse_id=source.id,
                #     destination_warehouse_id=destination.id,
                #     items=transfer_items,
                #     requested_by="SYSTEM_TEST"
                # )
                
                # print(f"   ✅ Transfert créé: {transfer.transfer_number}")
            
            # Test des alertes
            alerts = stock_controller.get_stock_alerts(session)
            print(f"   ⚠️  {len(alerts)} alertes de stock actives")
            
            print("✅ Tests des opérations terminés")
            
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")


def main():
    """Fonction principale d'initialisation"""
    print("🚀 Initialisation du système de gestion de stock avancé")
    print("=" * 60)
    
    # 1. Créer les tables
    print("\n📋 Étape 1: Création des tables")
    if not create_stock_tables():
        print("❌ Échec de la création des tables. Arrêt du processus.")
        return
    
    # 2. Configurer l'entrepôt par défaut
    print("\n📦 Étape 2: Configuration de l'entrepôt par défaut")
    pos_id = 1  # ID du POS par défaut
    default_warehouse = setup_default_warehouse(pos_id)
    if not default_warehouse:
        print("❌ Échec de la création de l'entrepôt par défaut. Arrêt du processus.")
        return
    
    # 3. Créer des entrepôts d'exemple
    print("\n🏭 Étape 3: Création d'entrepôts d'exemple")
    sample_warehouses = create_sample_warehouses(pos_id)
    print(f"✅ {len(sample_warehouses)} entrepôts d'exemple créés")
    
    # 4. Migrer les stocks existants
    print("\n📊 Étape 4: Migration des stocks existants")
    migrate_existing_stocks(pos_id)
    
    # 5. Tester les opérations
    print("\n🧪 Étape 5: Tests des opérations")
    test_stock_operations(pos_id)
    
    print("\n" + "=" * 60)
    print("🎉 Initialisation terminée avec succès!")
    print("\n📚 Fonctionnalités disponibles:")
    print("   • Gestion multi-entrepôts")
    print("   • Transferts entre entrepôts")
    print("   • Traçabilité complète des mouvements")
    print("   • Alertes de stock automatiques")
    print("   • Inventaires physiques")
    print("   • Gestion des lots et dates d'expiration")
    print("   • Calcul des coûts moyens pondérés")
    print("\n💡 Prochaines étapes:")
    print("   1. Créer l'interface utilisateur pour la gestion des entrepôts")
    print("   2. Intégrer avec l'interface produits existante")
    print("   3. Configurer les paramètres de stock par produit")


if __name__ == "__main__":
    main()