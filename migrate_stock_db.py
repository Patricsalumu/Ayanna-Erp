"""
Script de migration pour ajouter les colonnes created_at et updated_at 
à la table shop_stock_transfers
"""

import sys
import os
import sqlite3
from datetime import datetime

# Ajouter le chemin racine au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def migrate_shop_stock_transfers():
    """Ajouter les colonnes created_at et updated_at à shop_stock_transfers"""
    
    db_path = "ayanna_erp.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Base de données '{db_path}' non trouvée")
        return False
    
    try:
        print("🔄 Migration de la table shop_stock_transfers...")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier si les colonnes existent déjà
        cursor.execute("PRAGMA table_info(shop_stock_transfers)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"📋 Colonnes existantes: {columns}")
        
        migrations_needed = []
        
        if 'created_at' not in columns:
            migrations_needed.append('created_at')
        
        if 'updated_at' not in columns:
            migrations_needed.append('updated_at')
        
        if not migrations_needed:
            print("✅ Les colonnes created_at et updated_at existent déjà")
            conn.close()
            return True
        
        # Ajouter les colonnes manquantes
        for column in migrations_needed:
            if column == 'created_at':
                print("➕ Ajout de la colonne 'created_at'...")
                cursor.execute("""
                    ALTER TABLE shop_stock_transfers 
                    ADD COLUMN created_at DATETIME
                """)
                
                # Mettre à jour les enregistrements existants avec requested_date
                print("🔄 Mise à jour des enregistrements existants...")
                cursor.execute("""
                    UPDATE shop_stock_transfers 
                    SET created_at = requested_date 
                    WHERE requested_date IS NOT NULL
                """)
                
                cursor.execute("""
                    UPDATE shop_stock_transfers 
                    SET created_at = '2024-01-01 00:00:00' 
                    WHERE created_at IS NULL
                """)
                
            elif column == 'updated_at':
                print("➕ Ajout de la colonne 'updated_at'...")
                cursor.execute("""
                    ALTER TABLE shop_stock_transfers 
                    ADD COLUMN updated_at DATETIME
                """)
                
                # Mettre à jour avec la dernière date disponible
                cursor.execute("""
                    UPDATE shop_stock_transfers 
                    SET updated_at = COALESCE(received_date, shipped_date, approved_date, requested_date, '2024-01-01 00:00:00')
                """)
        
        conn.commit()
        print("✅ Migration terminée avec succès!")
        
        # Vérifier les résultats
        cursor.execute("PRAGMA table_info(shop_stock_transfers)")
        new_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Nouvelles colonnes: {new_columns}")
        
        # Compter les enregistrements
        cursor.execute("SELECT COUNT(*) FROM shop_stock_transfers")
        count = cursor.fetchone()[0]
        print(f"📊 {count} enregistrements dans la table")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def migrate_shop_products_cost_price():
    """Ajouter la colonne cost_price à shop_products"""
    
    db_path = "ayanna_erp.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Base de données '{db_path}' non trouvée")
        return False
    
    try:
        print("\n🔄 Migration de la table shop_products...")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier si la colonne existe déjà
        cursor.execute("PRAGMA table_info(shop_products)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'cost_price' not in columns:
            print("➕ Ajout de la colonne 'cost_price'...")
            cursor.execute("""
                ALTER TABLE shop_products 
                ADD COLUMN cost_price DECIMAL(15,2) DEFAULT 0.0
            """)
            
            # Copier les valeurs de 'cost' vers 'cost_price'
            print("🔄 Copie des valeurs de 'cost' vers 'cost_price'...")
            cursor.execute("""
                UPDATE shop_products 
                SET cost_price = cost 
                WHERE cost_price IS NULL OR cost_price = 0
            """)
            
            conn.commit()
            print("✅ Migration shop_products terminée!")
        else:
            print("✅ La colonne cost_price existe déjà dans shop_products")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration shop_products: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def main():
    """Fonction principale"""
    print("🛠️ SCRIPT DE MIGRATION - Corrections Base de Données")
    print("=" * 60)
    
    success = True
    
    # Migration 1: shop_stock_transfers
    if not migrate_shop_stock_transfers():
        success = False
    
    # Migration 2: shop_products
    if not migrate_shop_products_cost_price():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TOUTES LES MIGRATIONS RÉUSSIES!")
        print("✅ shop_stock_transfers.created_at et updated_at ajoutées")
        print("✅ shop_products.cost_price ajoutée")
        print("")
        print("🚀 La base de données est maintenant compatible!")
    else:
        print("❌ CERTAINES MIGRATIONS ONT ÉCHOUÉ")
        print("⚠️  Vérifiez les erreurs ci-dessus")
    
    print("=" * 60)

if __name__ == "__main__":
    main()