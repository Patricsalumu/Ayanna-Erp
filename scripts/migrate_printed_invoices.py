"""
Script de migration automatique pour ajouter les colonnes customer_id et index à restau_printed_invoices

Execute cette migration pour ajouter la colonne customer_id à la table restau_printed_invoices
si elle n'existe pas déjà dans la base de données.

Usage:
    python scripts/migrate_printed_invoices.py
    python scripts/migrate_printed_invoices.py --db path/to/database.sqlite
"""

import os
import sys
import sqlite3
import argparse
from pathlib import Path

def get_db_path():
    """Récupère le chemin par défaut de la base de données"""
    project_root = Path(__file__).parent.parent
    return project_root / 'data' / 'sqlite.db'

def column_exists(connection, table_name, column_name):
    """Vérifie si une colonne existe dans une table SQLite"""
    cursor = connection.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = {row[1] for row in cursor.fetchall()}
    return column_name in columns

def migrate_printed_invoices(db_path):
    """Applique la migration pour ajouter customer_id à restau_printed_invoices"""
    
    if not os.path.exists(db_path):
        print(f"❌ Base de données introuvable: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier si la table existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='restau_printed_invoices'")
        if not cursor.fetchone():
            print("⚠️  La table restau_printed_invoices n'existe pas encore.")
            print("Elle sera créée automatiquement lors du premier usage.")
            conn.close()
            return True
        
        # Vérifier si customer_id existe déjà
        if column_exists(conn, 'restau_printed_invoices', 'customer_id'):
            print("✅ La colonne customer_id existe déjà dans restau_printed_invoices")
            conn.close()
            return True
        
        print("⏳ Ajout de la colonne customer_id à restau_printed_invoices...")
        
        # Ajouter la colonne customer_id
        cursor.execute("""
            ALTER TABLE restau_printed_invoices 
            ADD COLUMN customer_id INTEGER
        """)
        
        # Créer les indexes pour les performances
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_restau_printed_invoices_customer_id 
            ON restau_printed_invoices(customer_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_restau_printed_invoices_printed_by_user_id 
            ON restau_printed_invoices(printed_by_user_id)
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Migration réussie!")
        print("   - Colonne customer_id ajoutée")
        print("   - Index sur customer_id créé")
        print("   - Index sur printed_by_user_id créé")
        return True
        
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            print("✅ La colonne customer_id existe déjà (colonne dupliquée détectée)")
            return True
        else:
            print(f"❌ Erreur lors de la migration: {e}")
            return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Migrer la base de données pour ajouter customer_id à restau_printed_invoices'
    )
    parser.add_argument(
        '--db',
        type=str,
        default=None,
        help='Chemin vers la base de données SQLite (par défaut: data/sqlite.db)'
    )
    
    args = parser.parse_args()
    
    db_path = args.db or str(get_db_path())
    
    print(f"📦 Migration de la base de données: {db_path}")
    print("-" * 60)
    
    success = migrate_printed_invoices(db_path)
    
    sys.exit(0 if success else 1)
