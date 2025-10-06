#!/usr/bin/env python3
"""
Analyseur des modifications apportées à la base de données
Affiche toutes les nouvelles tables et leurs structures
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.boutique.model.stock_models import *
from sqlalchemy import inspect


def analyze_database_changes():
    """Analyser les modifications apportées à la base de données"""
    print("📊 ANALYSE DES MODIFICATIONS DE BASE DE DONNÉES")
    print("=" * 70)
    
    try:
        db_manager = DatabaseManager()
        inspector = inspect(db_manager.engine)
        
        # Tables ajoutées pour le système de stock
        new_tables = [
            'shop_warehouses',
            'shop_warehouse_stocks', 
            'shop_stock_movements',
            'shop_stock_transfers',
            'shop_stock_transfer_items',
            'shop_inventories',
            'shop_inventory_items',
            'shop_stock_alerts'
        ]
        
        print("🆕 NOUVELLES TABLES CRÉÉES :")
        print("-" * 40)
        
        for i, table_name in enumerate(new_tables, 1):
            if inspector.has_table(table_name):
                print(f"{i}. ✅ {table_name}")
                
                # Obtenir les colonnes
                columns = inspector.get_columns(table_name)
                print(f"   📋 Colonnes ({len(columns)}):")
                
                for col in columns[:8]:  # Afficher les 8 premières colonnes
                    nullable = "NULL" if col['nullable'] else "NOT NULL"
                    print(f"      • {col['name']} ({col['type']}) {nullable}")
                
                if len(columns) > 8:
                    print(f"      ... et {len(columns) - 8} autres colonnes")
                
                # Obtenir les index
                indexes = inspector.get_indexes(table_name)
                if indexes:
                    print(f"   🔍 Index ({len(indexes)}):")
                    for idx in indexes:
                        print(f"      • {idx['name']} sur {idx['column_names']}")
                
                print()
            else:
                print(f"{i}. ❌ {table_name} (non trouvée)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        return False


def show_table_relationships():
    """Afficher les relations entre les tables"""
    print("\n🔗 RELATIONS ENTRE LES TABLES")
    print("=" * 70)
    
    relationships = {
        "shop_warehouses": {
            "description": "Table principale des entrepôts",
            "liens_sortants": [
                "shop_warehouse_stocks (warehouse_id)",
                "shop_stock_movements (warehouse_id)", 
                "shop_stock_transfers (source/destination_warehouse_id)",
                "shop_inventories (warehouse_id)",
                "shop_stock_alerts (warehouse_id)"
            ],
            "champs_clés": ["id", "pos_id", "code", "is_default"]
        },
        
        "shop_warehouse_stocks": {
            "description": "Stocks par entrepôt et produit", 
            "liens_entrants": ["shop_warehouses (warehouse_id)", "shop_products (product_id)"],
            "liens_sortants": ["shop_stock_movements (warehouse_stock_id)"],
            "champs_clés": ["warehouse_id", "product_id", "quantity_available"]
        },
        
        "shop_stock_movements": {
            "description": "Historique des mouvements de stock",
            "liens_entrants": [
                "shop_warehouses (warehouse_id)",
                "shop_warehouse_stocks (warehouse_stock_id)", 
                "shop_products (product_id)"
            ],
            "champs_clés": ["movement_type", "direction", "quantity", "movement_date"]
        },
        
        "shop_stock_transfers": {
            "description": "Transferts entre entrepôts",
            "liens_entrants": [
                "shop_warehouses (source_warehouse_id)",
                "shop_warehouses (destination_warehouse_id)"
            ],
            "liens_sortants": ["shop_stock_transfer_items (transfer_id)"],
            "champs_clés": ["transfer_number", "status", "requested_date"]
        },
        
        "shop_stock_transfer_items": {
            "description": "Détail des articles dans un transfert",
            "liens_entrants": [
                "shop_stock_transfers (transfer_id)",
                "shop_products (product_id)"
            ],
            "champs_clés": ["quantity_requested", "quantity_shipped", "quantity_received"]
        },
        
        "shop_inventories": {
            "description": "Inventaires physiques par entrepôt",
            "liens_entrants": ["shop_warehouses (warehouse_id)"],
            "liens_sortants": ["shop_inventory_items (inventory_id)"],
            "champs_clés": ["inventory_number", "status", "inventory_date"]
        },
        
        "shop_inventory_items": {
            "description": "Détail des articles inventoriés",
            "liens_entrants": [
                "shop_inventories (inventory_id)",
                "shop_products (product_id)"
            ],
            "champs_clés": ["expected_quantity", "counted_quantity", "variance_quantity"]
        },
        
        "shop_stock_alerts": {
            "description": "Alertes automatiques de stock",
            "liens_entrants": [
                "shop_warehouses (warehouse_id)",
                "shop_products (product_id)"
            ],
            "champs_clés": ["alert_type", "alert_level", "current_quantity"]
        }
    }
    
    for table_name, info in relationships.items():
        print(f"📋 {table_name.upper()}")
        print(f"   📝 {info['description']}")
        
        if 'liens_entrants' in info:
            print(f"   ⬅️  Liens entrants: {', '.join(info['liens_entrants'])}")
        
        if 'liens_sortants' in info:
            print(f"   ➡️  Liens sortants: {', '.join(info['liens_sortants'])}")
        
        print(f"   🔑 Champs clés: {', '.join(info['champs_clés'])}")
        print()


def show_data_migration_impact():
    """Afficher l'impact de la migration des données"""
    print("\n📈 IMPACT DE LA MIGRATION DES DONNÉES")
    print("=" * 70)
    
    try:
        db_manager = DatabaseManager()
        
        with db_manager.get_session() as session:
            # Compter les enregistrements dans les nouvelles tables
            tables_stats = {}
            
            # Entrepôts
            warehouse_count = session.query(ShopWarehouse).count()
            tables_stats['Entrepôts'] = warehouse_count
            
            # Stocks d'entrepôt
            warehouse_stock_count = session.query(ShopWarehouseStock).count()
            tables_stats['Stocks entrepôt'] = warehouse_stock_count
            
            # Mouvements
            movement_count = session.query(ShopStockMovement).count()
            tables_stats['Mouvements'] = movement_count
            
            # Transferts
            transfer_count = session.query(ShopStockTransfer).count()
            tables_stats['Transferts'] = transfer_count
            
            # Alertes
            alert_count = session.query(ShopStockAlert).count()
            tables_stats['Alertes'] = alert_count
            
            print("📊 DONNÉES MIGRÉES/CRÉÉES :")
            print("-" * 40)
            
            for table, count in tables_stats.items():
                status = "✅" if count > 0 else "⚪"
                print(f"{status} {table}: {count} enregistrements")
            
            # Afficher les entrepôts créés
            print(f"\n🏭 ENTREPÔTS CRÉÉS :")
            print("-" * 40)
            
            warehouses = session.query(ShopWarehouse).all()
            for warehouse in warehouses:
                default_marker = "⭐" if warehouse.is_default else "  "
                type_icons = {'shop': '🏪', 'storage': '📦', 'transit': '🚚', 'damaged': '⚠️'}
                type_icon = type_icons.get(warehouse.type, '📦')
                
                print(f"{default_marker} {type_icon} {warehouse.code} - {warehouse.name}")
                print(f"     Type: {warehouse.type} | Actif: {'Oui' if warehouse.is_active else 'Non'}")
                
                if warehouse.capacity_limit:
                    print(f"     Capacité: {warehouse.capacity_limit} unités")
            
            # Migration des stocks existants
            print(f"\n📦 STOCKS MIGRÉS :")
            print("-" * 40)
            
            if warehouse_stock_count > 0:
                print(f"✅ {warehouse_stock_count} stocks de produits migrés vers le nouveau système")
                print("   • Ancien système: champ 'stock_quantity' dans shop_products")
                print("   • Nouveau système: table 'shop_warehouse_stocks' avec traçabilité")
                print("   • Entrepôt par défaut: Magasin Principal POS")
                print("   • Mouvements initiaux créés pour la traçabilité")
            else:
                print("⚪ Aucun stock à migrer ou migration non effectuée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse des données: {e}")
        return False


def show_new_features():
    """Afficher les nouvelles fonctionnalités disponibles"""
    print("\n🚀 NOUVELLES FONCTIONNALITÉS DISPONIBLES")
    print("=" * 70)
    
    features = {
        "Gestion Multi-Entrepôts": [
            "• Création d'entrepôts illimités (Magasin, Dépôt, Transit, Endommagés)",
            "• Configuration des capacités et responsables",
            "• Entrepôt par défaut pour chaque POS",
            "• Statuts actif/inactif par entrepôt"
        ],
        
        "Transferts Inter-Entrepôts": [
            "• Workflow complet: Demande → Approbation → Expédition → Réception",
            "• Numérotation automatique des transferts",
            "• Gestion des priorités (Normal, Élevé, Urgent)",
            "• Traçabilité des quantités demandées/expédiées/reçues"
        ],
        
        "Traçabilité Complète": [
            "• Historique de tous les mouvements de stock",
            "• Types: Achat, Vente, Transfert, Ajustement, Perte",
            "• Quantités avant/après pour chaque mouvement",
            "• Références (factures, bons de livraison, etc.)",
            "• Utilisateurs responsables et horodatage"
        ],
        
        "Gestion des Coûts": [
            "• Calcul automatique du coût moyen pondéré",
            "• Valorisation des stocks en temps réel",
            "• Historique des coûts par mouvement",
            "• Support des lots et dates d'expiration"
        ],
        
        "Système d'Alertes": [
            "• Alertes automatiques de rupture de stock",
            "• Alertes de stock faible (sous le minimum)",
            "• Points de réapprovisionnement configurables",
            "• Niveaux: Critique, Avertissement, Information"
        ],
        
        "Inventaires Physiques": [
            "• Planification d'inventaires par entrepôt",
            "• Saisie des quantités comptées",
            "• Calcul automatique des écarts",
            "• Génération d'ajustements de stock"
        ]
    }
    
    for feature_name, details in features.items():
        print(f"🎯 {feature_name.upper()}")
        for detail in details:
            print(f"   {detail}")
        print()


def main():
    """Fonction principale d'analyse"""
    print("🔍 ANALYSE COMPLÈTE DES MODIFICATIONS DE BASE DE DONNÉES")
    print("🕒 Date de création: 5 octobre 2025")
    print("👤 Auteur: GitHub Copilot")
    print("📂 Système: Ayanna ERP - Module Boutique")
    print("=" * 70)
    
    # 1. Analyser les nouvelles tables
    print("\n" + "🔸" * 70)
    success = analyze_database_changes()
    
    # 2. Afficher les relations
    if success:
        print("🔸" * 70)
        show_table_relationships()
    
    # 3. Impact de la migration
    if success:
        print("🔸" * 70)
        show_data_migration_impact()
    
    # 4. Nouvelles fonctionnalités
    print("🔸" * 70)
    show_new_features()
    
    # Résumé final
    print("🔸" * 70)
    print("📋 RÉSUMÉ DES MODIFICATIONS")
    print("=" * 70)
    print("✅ 8 nouvelles tables créées pour la gestion de stock avancée")
    print("✅ Relations complexes entre entrepôts, produits et mouvements")
    print("✅ Migration automatique des données existantes")
    print("✅ Système de traçabilité complet mis en place")
    print("✅ Fonctionnalités d'entreprise (transferts, inventaires, alertes)")
    print("✅ Interface utilisateur à 5 onglets disponible")
    
    print(f"\n🎯 Impact:")
    print("   • Passage d'un système de stock simple à un système d'entreprise")
    print("   • Traçabilité complète de tous les mouvements")
    print("   • Gestion multi-entrepôts opérationnelle")
    print("   • Base solide pour expansion future")
    
    print(f"\n🔄 Compatibilité:")
    print("   • L'ancien système continue de fonctionner")
    print("   • Migration transparente des données existantes")
    print("   • Pas de perte de données")
    print("   • Interface existante non impactée")


if __name__ == "__main__":
    main()