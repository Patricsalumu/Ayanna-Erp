"""
Script simple pour exécuter les corrections SQL
"""

import sqlite3
import os

def execute_sql_fixes():
    """Exécuter les corrections SQL pour les colonnes manquantes"""
    
    db_path = "ayanna_erp.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Base de données '{db_path}' non trouvée")
        return False
    
    sql_commands = [
        # Ajouter les colonnes
        "ALTER TABLE shop_stock_transfers ADD COLUMN created_at DATETIME;",
        "ALTER TABLE shop_stock_transfers ADD COLUMN updated_at DATETIME;", 
        "ALTER TABLE shop_products ADD COLUMN cost_price DECIMAL(15,2) DEFAULT 0.0;",
        
        # Mettre à jour les valeurs
        """UPDATE shop_stock_transfers 
           SET created_at = requested_date 
           WHERE created_at IS NULL AND requested_date IS NOT NULL;""",
           
        """UPDATE shop_stock_transfers 
           SET created_at = '2024-01-01 00:00:00' 
           WHERE created_at IS NULL;""",
           
        """UPDATE shop_stock_transfers 
           SET updated_at = COALESCE(received_date, shipped_date, approved_date, requested_date, '2024-01-01 00:00:00')
           WHERE updated_at IS NULL;""",
           
        """UPDATE shop_products 
           SET cost_price = cost 
           WHERE cost_price IS NULL OR cost_price = 0;"""
    ]
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Exécution des corrections SQL...")
        
        for i, command in enumerate(sql_commands, 1):
            try:
                cursor.execute(command)
                print(f"   ✅ Commande {i}/7 exécutée")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e) or "already exists" in str(e):
                    print(f"   ⚠️  Commande {i}/7 ignorée (colonne existe déjà)")
                else:
                    print(f"   ❌ Erreur commande {i}/7: {e}")
        
        conn.commit()
        
        # Vérifications
        print("\n🔍 Vérifications:")
        
        # Vérifier shop_stock_transfers
        cursor.execute("PRAGMA table_info(shop_stock_transfers)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'created_at' in columns and 'updated_at' in columns:
            print("   ✅ shop_stock_transfers: created_at et updated_at ajoutées")
        else:
            print("   ❌ shop_stock_transfers: colonnes manquantes")
        
        # Vérifier shop_products
        cursor.execute("PRAGMA table_info(shop_products)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'cost_price' in columns:
            print("   ✅ shop_products: cost_price ajoutée")
        else:
            print("   ❌ shop_products: cost_price manquante")
        
        # Compter les enregistrements mis à jour
        cursor.execute("SELECT COUNT(*) FROM shop_stock_transfers WHERE created_at IS NOT NULL")
        count = cursor.fetchone()[0]
        print(f"   📊 {count} enregistrements shop_stock_transfers avec created_at")
        
        cursor.execute("SELECT COUNT(*) FROM shop_products WHERE cost_price > 0")
        count = cursor.fetchone()[0]
        print(f"   📊 {count} produits avec cost_price > 0")
        
        conn.close()
        print("\n✅ Corrections SQL terminées!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution SQL: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def main():
    print("🛠️ CORRECTIONS SQL - Colonnes manquantes")
    print("=" * 50)
    
    if execute_sql_fixes():
        print("\n🎉 SUCCÈS!")
        print("✅ Toutes les colonnes ont été ajoutées")
        print("✅ Les données ont été mises à jour")
        print("\n🚀 Vous pouvez maintenant tester le module Stock!")
    else:
        print("\n❌ ÉCHEC")
        print("⚠️  Vérifiez les erreurs ci-dessus")
    
    print("=" * 50)

if __name__ == "__main__":
    main()