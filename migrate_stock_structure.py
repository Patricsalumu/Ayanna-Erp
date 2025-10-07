"""
Script de migration vers la nouvelle structure de stock simplifiée
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from datetime import datetime
from ayanna_erp.database.database_manager import DatabaseManager


def create_new_tables():
    """Créer les nouvelles tables"""
    print("🔨 Création des nouvelles tables...")
    
    db_path = "ayanna_erp.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Table stock_warehouses
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_warehouses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entreprise_id INTEGER NOT NULL,
                code VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                type VARCHAR(50) DEFAULT 'Principal',
                description TEXT,
                address TEXT,
                contact_person VARCHAR(255),
                contact_phone VARCHAR(50),
                contact_email VARCHAR(255),
                is_default BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                capacity_limit DECIMAL(15,2),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Index pour optimisation
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_warehouses_entreprise ON stock_warehouses(entreprise_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_warehouses_code ON stock_warehouses(code)")
        
        # 2. Table stock_config
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pos_id INTEGER NOT NULL,
                warehouse_id INTEGER NOT NULL,
                entreprise_id INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (warehouse_id) REFERENCES stock_warehouses(id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_config_pos ON stock_config(pos_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_config_entreprise ON stock_config(entreprise_id)")
        
        # 3. Table stock_produits_entrepot
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_produits_entrepot (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                warehouse_id INTEGER NOT NULL,
                quantity DECIMAL(15,3) DEFAULT 0,
                unit_cost DECIMAL(15,2) DEFAULT 0,
                total_cost DECIMAL(15,2) DEFAULT 0,
                min_stock_level DECIMAL(15,3) DEFAULT 0,
                last_movement_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                reference VARCHAR(255),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (warehouse_id) REFERENCES stock_warehouses(id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_produits_product ON stock_produits_entrepot(product_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_produits_warehouse ON stock_produits_entrepot(warehouse_id)")
        
        # 4. Table stock_mouvements
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_mouvements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                warehouse_id_depart VARCHAR(50) NOT NULL,
                warehouse_id_destination VARCHAR(50) NOT NULL,
                product_id INTEGER NOT NULL,
                quantity DECIMAL(15,3) NOT NULL,
                unit_cost DECIMAL(15,2) NOT NULL,
                total_cost DECIMAL(15,2) NOT NULL,
                quantity_before DECIMAL(15,3) DEFAULT 0,
                quantity_after DECIMAL(15,3) DEFAULT 0,
                reference_document VARCHAR(255),
                mouvement_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_by INTEGER
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_mouvements_product ON stock_mouvements(product_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_mouvements_date ON stock_mouvements(mouvement_date)")
        
        conn.commit()
        print("✅ Nouvelles tables créées avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur création tables: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def migrate_warehouses():
    """Migrer shop_warehouses vers stock_warehouses"""
    print("\n🏪 Migration des entrepôts...")
    
    db_path = "ayanna_erp.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Vérifier si shop_warehouses existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shop_warehouses'")
        if not cursor.fetchone():
            print("⚠️  Table shop_warehouses non trouvée")
            return True
        
        # Récupérer les données existantes
        cursor.execute("""
            SELECT id, pos_id, code, name, type, description, address, 
                   contact_person, contact_phone, contact_email, 
                   is_default, is_active, capacity_limit, created_at
            FROM shop_warehouses
        """)
        
        warehouses = cursor.fetchall()
        migrated_count = 0
        
        for warehouse in warehouses:
            try:
                # Convertir pos_id en entreprise_id (assumons que pos_id = 1 correspond à entreprise_id = 1)
                entreprise_id = warehouse[1] if warehouse[1] else 1
                
                # Insérer dans la nouvelle table
                cursor.execute("""
                    INSERT OR IGNORE INTO stock_warehouses 
                    (id, entreprise_id, code, name, type, description, address,
                     contact_person, contact_phone, contact_email, is_default, 
                     is_active, capacity_limit, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    warehouse[0],  # id
                    entreprise_id,  # entreprise_id (ex pos_id)
                    warehouse[2],  # code
                    warehouse[3],  # name
                    warehouse[4] or 'Principal',  # type
                    warehouse[5],  # description
                    warehouse[6],  # address
                    warehouse[7],  # contact_person
                    warehouse[8],  # contact_phone
                    warehouse[9],  # contact_email
                    warehouse[10] or 0,  # is_default
                    warehouse[11] if warehouse[11] is not None else 1,  # is_active
                    warehouse[12],  # capacity_limit
                    warehouse[13] or datetime.now().isoformat()  # created_at
                ))
                
                migrated_count += 1
                
            except Exception as e:
                print(f"❌ Erreur migration entrepôt {warehouse[2]}: {e}")
        
        conn.commit()
        print(f"✅ {migrated_count} entrepôts migrés vers stock_warehouses")
        return True
        
    except Exception as e:
        print(f"❌ Erreur migration entrepôts: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def migrate_warehouse_stocks():
    """Migrer shop_warehouse_stocks vers stock_produits_entrepot"""
    print("\n📦 Migration des stocks produits-entrepôts...")
    
    db_path = "ayanna_erp.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Vérifier si shop_warehouse_stocks existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shop_warehouse_stocks'")
        if not cursor.fetchone():
            print("⚠️  Table shop_warehouse_stocks non trouvée")
            return True
        
        # Récupérer les données existantes (colonnes simplifiées)
        cursor.execute("""
            SELECT product_id, warehouse_id, quantity, unit_cost, 
                   min_stock_level, updated_at
            FROM shop_warehouse_stocks
            WHERE quantity > 0 OR min_stock_level > 0
        """)
        
        stocks = cursor.fetchall()
        migrated_count = 0
        
        for stock in stocks:
            try:
                quantity = float(stock[2]) if stock[2] else 0
                unit_cost = float(stock[3]) if stock[3] else 0
                total_cost = quantity * unit_cost
                
                # Insérer dans la nouvelle table
                cursor.execute("""
                    INSERT OR IGNORE INTO stock_produits_entrepot 
                    (product_id, warehouse_id, quantity, unit_cost, total_cost,
                     min_stock_level, last_movement_date, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (
                    stock[0],  # product_id
                    stock[1],  # warehouse_id
                    quantity,  # quantity
                    unit_cost,  # unit_cost
                    total_cost,  # total_cost
                    float(stock[4]) if stock[4] else 0,  # min_stock_level
                    stock[5] or datetime.now().isoformat()  # last_movement_date
                ))
                
                migrated_count += 1
                
            except Exception as e:
                print(f"❌ Erreur migration stock produit {stock[0]}: {e}")
        
        conn.commit()
        print(f"✅ {migrated_count} stocks produits migrés vers stock_produits_entrepot")
        return True
        
    except Exception as e:
        print(f"❌ Erreur migration stocks: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def create_default_configurations():
    """Créer des configurations par défaut pour les POS"""
    print("\n⚙️ Création des configurations par défaut...")
    
    db_path = "ayanna_erp.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Récupérer les entrepôts disponibles
        cursor.execute("SELECT id, entreprise_id, name FROM stock_warehouses WHERE is_active = 1")
        warehouses = cursor.fetchall()
        
        if not warehouses:
            print("⚠️  Aucun entrepôt trouvé pour la configuration")
            return True
        
        # Créer une configuration par défaut pour chaque entreprise
        entreprises = set(w[1] for w in warehouses)
        config_count = 0
        
        for entreprise_id in entreprises:
            # Trouver l'entrepôt principal de cette entreprise
            warehouse = next((w for w in warehouses if w[1] == entreprise_id), None)
            
            if warehouse:
                # Créer config pour POS par défaut (assumons POS ID = entreprise_id)
                cursor.execute("""
                    INSERT OR IGNORE INTO stock_config 
                    (pos_id, warehouse_id, entreprise_id, is_active)
                    VALUES (?, ?, ?, 1)
                """, (entreprise_id, warehouse[0], entreprise_id))
                
                config_count += 1
        
        conn.commit()
        print(f"✅ {config_count} configurations par défaut créées")
        return True
        
    except Exception as e:
        print(f"❌ Erreur création configurations: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def main():
    """Migration complète"""
    print("🚀 MIGRATION VERS NOUVELLE STRUCTURE STOCK")
    print("=" * 50)
    
    steps = [
        ("Création des nouvelles tables", create_new_tables),
        ("Migration des entrepôts", migrate_warehouses),
        ("Migration des stocks", migrate_warehouse_stocks),
        ("Configurations par défaut", create_default_configurations)
    ]
    
    all_success = True
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}...")
        if not step_func():
            all_success = False
            print(f"❌ Échec: {step_name}")
            break
        else:
            print(f"✅ Réussi: {step_name}")
    
    print("\n" + "=" * 50)
    if all_success:
        print("🎉 MIGRATION TERMINÉE AVEC SUCCÈS!")
        print("\n✅ Nouvelles tables créées:")
        print("   • stock_warehouses (entreprise_id)")
        print("   • stock_config (POS → entrepôt)")
        print("   • stock_produits_entrepot (simplifié)")
        print("   • stock_mouvements (traçabilité)")
        print("\n📊 Données migrées et configurations créées")
    else:
        print("❌ MIGRATION ÉCHOUÉE")
        print("⚠️  Vérifiez les erreurs ci-dessus")


if __name__ == "__main__":
    main()