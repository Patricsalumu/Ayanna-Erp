"""
Système d'auto-initialisation pour la nouvelle structure de stock
Créé automatiquement les associations produit-entrepôt nécessaires
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from datetime import datetime
from typing import Dict, Any
from ayanna_erp.database.database_manager import DatabaseManager


class StockAutoInitializer:
    """Système d'auto-initialisation pour les stocks"""
    
    def __init__(self, entreprise_id: int):
        self.entreprise_id = entreprise_id
        self.db_path = "ayanna_erp.db"
    
    def initialize_product_warehouse_links(self) -> Dict[str, int]:
        """Créer automatiquement les liens produit-entrepôt manquants"""
        print(f"🔗 Initialisation des liens produit-entrepôt pour l'entreprise {self.entreprise_id}...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Récupérer tous les entrepôts de l'entreprise
            cursor.execute("""
                SELECT id, name FROM stock_warehouses 
                WHERE entreprise_id = ? AND is_active = 1
            """, (self.entreprise_id,))
            warehouses = cursor.fetchall()
            
            if not warehouses:
                print("⚠️  Aucun entrepôt trouvé pour cette entreprise")
                return {'warehouses': 0, 'products': 0, 'links_created': 0}
            
            # Récupérer tous les produits de l'entreprise (via boutique)
            cursor.execute("""
                SELECT DISTINCT p.id, p.name, p.cost_price, p.stock_min, p.stock_quantity 
                FROM shop_products p 
                JOIN core_pos_points pos ON p.pos_id = pos.id 
                WHERE pos.enterprise_id = ?
            """, (self.entreprise_id,))
            products = cursor.fetchall()
            
            if not products:
                print("⚠️  Aucun produit trouvé pour cette entreprise")
                return {'warehouses': len(warehouses), 'products': 0, 'links_created': 0}
            
            links_created = 0
            
            # Créer les associations produit-entrepôt manquantes
            for product in products:
                product_id, product_name, cost_price, min_stock, max_stock = product
                
                for warehouse in warehouses:
                    warehouse_id, warehouse_name = warehouse
                    
                    # Vérifier si l'association existe déjà
                    cursor.execute("""
                        SELECT COUNT(*) FROM stock_produits_entrepot 
                        WHERE product_id = ? AND warehouse_id = ?
                    """, (product_id, warehouse_id))
                    
                    if cursor.fetchone()[0] == 0:
                        # Créer l'association avec quantité 0
                        cursor.execute("""
                            INSERT INTO stock_produits_entrepot 
                            (product_id, warehouse_id, quantity, unit_cost, total_cost,
                             min_stock_level, created_at, updated_at, last_movement_date)
                            VALUES (?, ?, 0, ?, 0, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """, (
                            product_id, 
                            warehouse_id,
                            float(cost_price) if cost_price else 0.0,
                            float(min_stock) if min_stock else 0.0
                        ))
                        
                        links_created += 1
            
            conn.commit()
            
            print(f"✅ {links_created} nouvelles associations produit-entrepôt créées")
            print(f"📊 Résumé: {len(warehouses)} entrepôts × {len(products)} produits")
            
            return {
                'warehouses': len(warehouses),
                'products': len(products),
                'links_created': links_created
            }
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
            conn.rollback()
            return {'warehouses': 0, 'products': 0, 'links_created': 0, 'error': str(e)}
        finally:
            conn.close()
    
    def initialize_warehouse_config(self) -> Dict[str, int]:
        """Créer les configurations POS-entrepôt manquantes"""
        print(f"⚙️ Initialisation des configurations POS-entrepôt pour l'entreprise {self.entreprise_id}...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Récupérer tous les POS de l'entreprise
            cursor.execute("""
                SELECT id, name FROM core_pos_points 
                WHERE enterprise_id = ?
            """, (self.entreprise_id,))
            pos_list = cursor.fetchall()
            
            if not pos_list:
                print("⚠️  Aucun POS trouvé pour cette entreprise")
                return {'pos_count': 0, 'configs_created': 0}
            
            # Récupérer l'entrepôt par défaut
            cursor.execute("""
                SELECT id FROM stock_warehouses 
                WHERE entreprise_id = ? AND is_default = 1 AND is_active = 1
                LIMIT 1
            """, (self.entreprise_id,))
            
            default_warehouse = cursor.fetchone()
            if not default_warehouse:
                # Prendre le premier entrepôt actif
                cursor.execute("""
                    SELECT id FROM stock_warehouses 
                    WHERE entreprise_id = ? AND is_active = 1
                    ORDER BY created_at
                    LIMIT 1
                """, (self.entreprise_id,))
                default_warehouse = cursor.fetchone()
            
            if not default_warehouse:
                print("⚠️  Aucun entrepôt trouvé pour cette entreprise")
                return {'pos_count': len(pos_list), 'configs_created': 0}
            
            warehouse_id = default_warehouse[0]
            configs_created = 0
            
            # Créer les configurations manquantes
            for pos in pos_list:
                pos_id, pos_name = pos
                
                # Vérifier si la configuration existe déjà
                cursor.execute("""
                    SELECT COUNT(*) FROM stock_config 
                    WHERE pos_id = ? AND entreprise_id = ?
                """, (pos_id, self.entreprise_id))
                
                if cursor.fetchone()[0] == 0:
                    # Créer la configuration
                    cursor.execute("""
                        INSERT INTO stock_config 
                        (pos_id, warehouse_id, entreprise_id, is_active, created_at, updated_at)
                        VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """, (pos_id, warehouse_id, self.entreprise_id))
                    
                    configs_created += 1
            
            conn.commit()
            
            print(f"✅ {configs_created} nouvelles configurations POS-entrepôt créées")
            
            return {
                'pos_count': len(pos_list),
                'configs_created': configs_created
            }
            
        except Exception as e:
            print(f"❌ Erreur lors de la création des configurations: {e}")
            conn.rollback()
            return {'pos_count': 0, 'configs_created': 0, 'error': str(e)}
        finally:
            conn.close()
    
    def full_initialization(self) -> Dict[str, Any]:
        """Initialisation complète pour une entreprise"""
        print(f"🚀 INITIALISATION COMPLÈTE ENTREPRISE {self.entreprise_id}")
        print("=" * 50)
        
        # 1. Initialiser les liens produit-entrepôt
        product_results = self.initialize_product_warehouse_links()
        
        # 2. Initialiser les configurations POS
        config_results = self.initialize_warehouse_config()
        
        # 3. Résumé final
        print("\n" + "=" * 50)
        print("🎉 INITIALISATION TERMINÉE")
        print(f"✅ Associations produit-entrepôt: {product_results.get('links_created', 0)}")
        print(f"✅ Configurations POS: {config_results.get('configs_created', 0)}")
        
        return {
            'entreprise_id': self.entreprise_id,
            'product_warehouse_links': product_results,
            'pos_configurations': config_results,
            'status': 'completed'
        }


def initialize_all_enterprises():
    """Initialiser toutes les entreprises"""
    print("🌍 INITIALISATION GLOBALE DE TOUTES LES ENTREPRISES")
    print("=" * 60)
    
    conn = sqlite3.connect("ayanna_erp.db")
    cursor = conn.cursor()
    
    try:
        # Récupérer toutes les entreprises avec des entrepôts
        cursor.execute("""
            SELECT DISTINCT entreprise_id FROM stock_warehouses 
            WHERE is_active = 1
        """)
        entreprises = cursor.fetchall()
        
        if not entreprises:
            print("⚠️  Aucune entreprise trouvée avec des entrepôts")
            return
        
        total_links = 0
        total_configs = 0
        
        for (entreprise_id,) in entreprises:
            print(f"\n📋 Traitement entreprise {entreprise_id}...")
            
            initializer = StockAutoInitializer(entreprise_id)
            results = initializer.full_initialization()
            
            total_links += results['product_warehouse_links'].get('links_created', 0)
            total_configs += results['pos_configurations'].get('configs_created', 0)
        
        print("\n" + "=" * 60)
        print("🎊 INITIALISATION GLOBALE TERMINÉE")
        print(f"📊 Total associations créées: {total_links}")
        print(f"⚙️ Total configurations créées: {total_configs}")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation globale: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    from typing import Dict, Any
    
    parser = argparse.ArgumentParser(description="Auto-initialisation du système de stock")
    parser.add_argument("--entreprise", type=int, help="ID de l'entreprise à initialiser")
    parser.add_argument("--all", action="store_true", help="Initialiser toutes les entreprises")
    
    args = parser.parse_args()
    
    if args.all:
        initialize_all_enterprises()
    elif args.entreprise:
        initializer = StockAutoInitializer(args.entreprise)
        initializer.full_initialization()
    else:
        print("Utilisation:")
        print("  python auto_initializer.py --entreprise 1  # Initialiser entreprise 1")
        print("  python auto_initializer.py --all           # Initialiser toutes les entreprises")