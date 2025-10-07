"""
Script de migration pour nettoyer la base de données
- Supprime les anciennes tables de stock  
- Garde uniquement nos 4 tables optimisées
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Migration complète de la base de données"""
    
    db_path = r"c:\Ayanna ERP\Ayanna-Erp\ayanna_erp.db"
    
    try:
        # Se connecter à la base
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Début de la migration...")
        
        # 1. Supprimer les anciennes tables
        old_tables = [
            'shop_stock',
            'shop_stock_alerts', 
            'shop_stock_movements',
            'shop_stock_movements_new',
            'shop_stock_transfers',
            'shop_stock_transfer_items',
            'shop_warehouse_stocks',
            'shop_inventories',
            'shop_inventory_items'
        ]
        
        for table in old_tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table};")
            print(f"🗑️  Table supprimée: {table}")
        
        print("✅ Migration terminée!")
        
        # Valider les changements
        conn.commit()
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Démarrage du nettoyage de la base de données...")
    success = migrate_database()
    
    if success:
        print("\n✅ Nettoyage terminé avec succès!")
        print("📋 Tables conservées: stock_warehouses, stock_config, stock_produits_entrepot, stock_mouvements")
    else:
        print("\n❌ Nettoyage échoué")