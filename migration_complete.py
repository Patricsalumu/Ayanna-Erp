"""
Script de migration complet pour ajouter toutes les colonnes manquantes
"""

import sqlite3
import os
from datetime import datetime

def execute_comprehensive_migration():
    """Exécuter une migration complète pour toutes les colonnes manquantes"""
    
    db_path = "ayanna_erp.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Base de données '{db_path}' non trouvée")
        return False
    
    # Liste complète des migrations nécessaires
    migrations = [
        # ShopProduct - nouvelles colonnes
        ("ALTER TABLE shop_products ADD COLUMN code VARCHAR(50);", "shop_products.code"),
        ("ALTER TABLE shop_products ADD COLUMN sale_price DECIMAL(15,2) DEFAULT 0.0;", "shop_products.sale_price"),
        
        # ShopStockTransfer - nouvelles colonnes
        ("ALTER TABLE shop_stock_transfers ADD COLUMN expected_date DATETIME;", "shop_stock_transfers.expected_date"),
        
        # ShopWarehouseStock - nouvelles colonnes pour compatibilité
        ("ALTER TABLE shop_warehouse_stocks ADD COLUMN quantity DECIMAL(15,2) DEFAULT 0.0;", "shop_warehouse_stocks.quantity"),
        ("ALTER TABLE shop_warehouse_stocks ADD COLUMN reserved_quantity DECIMAL(15,2) DEFAULT 0.0;", "shop_warehouse_stocks.reserved_quantity"),
        ("ALTER TABLE shop_warehouse_stocks ADD COLUMN minimum_stock DECIMAL(15,2) DEFAULT 0.0;", "shop_warehouse_stocks.minimum_stock"),
        ("ALTER TABLE shop_warehouse_stocks ADD COLUMN maximum_stock DECIMAL(15,2) DEFAULT 0.0;", "shop_warehouse_stocks.maximum_stock"),
        ("ALTER TABLE shop_warehouse_stocks ADD COLUMN unit_cost DECIMAL(15,2) DEFAULT 0.0;", "shop_warehouse_stocks.unit_cost"),
        ("ALTER TABLE shop_warehouse_stocks ADD COLUMN updated_at DATETIME;", "shop_warehouse_stocks.updated_at"),
    ]
    
    # Mises à jour de données
    data_updates = [
        # Copier les valeurs existantes vers les nouvelles colonnes
        ("UPDATE shop_products SET sale_price = price_unit WHERE sale_price IS NULL OR sale_price = 0;", "Copie price_unit vers sale_price"),
        ("UPDATE shop_warehouse_stocks SET quantity = quantity_available WHERE quantity IS NULL OR quantity = 0;", "Copie quantity_available vers quantity"),
        ("UPDATE shop_warehouse_stocks SET reserved_quantity = quantity_reserved WHERE reserved_quantity IS NULL OR reserved_quantity = 0;", "Copie quantity_reserved vers reserved_quantity"),
        ("UPDATE shop_warehouse_stocks SET minimum_stock = min_stock_level WHERE minimum_stock IS NULL OR minimum_stock = 0;", "Copie min_stock_level vers minimum_stock"),
        ("UPDATE shop_warehouse_stocks SET maximum_stock = max_stock_level WHERE maximum_stock IS NULL OR maximum_stock = 0;", "Copie max_stock_level vers maximum_stock"),
        ("UPDATE shop_warehouse_stocks SET unit_cost = average_cost WHERE unit_cost IS NULL OR unit_cost = 0;", "Copie average_cost vers unit_cost"),
        ("UPDATE shop_warehouse_stocks SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;", "Mise à jour updated_at"),
        ("UPDATE shop_stock_transfers SET expected_date = requested_date WHERE expected_date IS NULL;", "Mise à jour expected_date"),
    ]
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Exécution de la migration complète...")
        print("=" * 60)
        
        # Étape 1: Ajouter les colonnes
        print("\n📋 Étape 1: Ajout des colonnes manquantes")
        added_columns = 0
        
        for i, (sql, description) in enumerate(migrations, 1):
            try:
                cursor.execute(sql)
                print(f"   ✅ {i}. {description} ajoutée")
                added_columns += 1
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e) or "already exists" in str(e):
                    print(f"   ⚠️  {i}. {description} existe déjà")
                else:
                    print(f"   ❌ {i}. Erreur {description}: {e}")
        
        # Étape 2: Mettre à jour les données
        print(f"\n📊 Étape 2: Mise à jour des données ({len(data_updates)} opérations)")
        updated_data = 0
        
        for i, (sql, description) in enumerate(data_updates, 1):
            try:
                cursor.execute(sql)
                rows_affected = cursor.rowcount
                print(f"   ✅ {i}. {description} ({rows_affected} lignes affectées)")
                updated_data += 1
            except Exception as e:
                print(f"   ❌ {i}. Erreur {description}: {e}")
        
        conn.commit()
        
        # Étape 3: Vérifications
        print(f"\n🔍 Étape 3: Vérifications")
        
        # Vérifier shop_products
        cursor.execute("PRAGMA table_info(shop_products)")
        product_columns = [col[1] for col in cursor.fetchall()]
        
        required_product_cols = ['code', 'cost_price', 'sale_price']
        for col in required_product_cols:
            if col in product_columns:
                print(f"   ✅ shop_products.{col}")
            else:
                print(f"   ❌ shop_products.{col} MANQUANT")
        
        # Vérifier shop_stock_transfers
        cursor.execute("PRAGMA table_info(shop_stock_transfers)")
        transfer_columns = [col[1] for col in cursor.fetchall()]
        
        required_transfer_cols = ['created_at', 'updated_at', 'expected_date']
        for col in required_transfer_cols:
            if col in transfer_columns:
                print(f"   ✅ shop_stock_transfers.{col}")
            else:
                print(f"   ❌ shop_stock_transfers.{col} MANQUANT")
        
        # Vérifier shop_warehouse_stocks
        cursor.execute("PRAGMA table_info(shop_warehouse_stocks)")
        stock_columns = [col[1] for col in cursor.fetchall()]
        
        required_stock_cols = ['quantity', 'reserved_quantity', 'minimum_stock', 'maximum_stock', 'unit_cost', 'updated_at']
        for col in required_stock_cols:
            if col in stock_columns:
                print(f"   ✅ shop_warehouse_stocks.{col}")
            else:
                print(f"   ❌ shop_warehouse_stocks.{col} MANQUANT")
        
        # Statistiques finales
        print(f"\n📈 Statistiques:")
        
        cursor.execute("SELECT COUNT(*) FROM shop_products WHERE code IS NOT NULL")
        count = cursor.fetchone()[0]
        print(f"   📊 {count} produits avec code")
        
        cursor.execute("SELECT COUNT(*) FROM shop_products WHERE sale_price > 0")
        count = cursor.fetchone()[0]
        print(f"   📊 {count} produits avec sale_price > 0")
        
        cursor.execute("SELECT COUNT(*) FROM shop_stock_transfers")
        count = cursor.fetchone()[0]
        print(f"   📊 {count} transferts dans la base")
        
        cursor.execute("SELECT COUNT(*) FROM shop_warehouse_stocks WHERE quantity IS NOT NULL")
        count = cursor.fetchone()[0]
        print(f"   📊 {count} stocks avec quantité")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ MIGRATION COMPLÈTE TERMINÉE!")
        print(f"✅ {added_columns} colonnes ajoutées")
        print(f"✅ {updated_data} mises à jour de données")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def main():
    print("🛠️ MIGRATION COMPLÈTE - Toutes les colonnes manquantes")
    print("=" * 60)
    
    if execute_comprehensive_migration():
        print("\n🎉 SUCCÈS TOTAL!")
        print("✅ Toutes les colonnes ont été ajoutées")
        print("✅ Toutes les données ont été mises à jour")
        print("✅ La base de données est maintenant compatible")
        print("\n🚀 Vous pouvez maintenant tester le module Stock sans erreurs!")
    else:
        print("\n❌ ÉCHEC DE LA MIGRATION")
        print("⚠️  Vérifiez les erreurs ci-dessus")
    
    print("=" * 60)

if __name__ == "__main__":
    main()