#!/usr/bin/env python3
"""
Script de migration pour convertir le champ logo de TEXT vers BLOB
"""

import sys
import os
import sqlite3
from pathlib import Path

# Ajouter le chemin du projet
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from ayanna_erp.database.database_manager import DatabaseManager

def migrate_logo_to_blob():
    """Migrer le champ logo de TEXT vers BLOB"""
    print("=== Migration du champ logo vers BLOB ===")
    
    # Chemin vers la base de données
    db_path = "ayanna_erp.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Base de données {db_path} non trouvée")
        return False
    
    try:
        # Connexion directe SQLite pour la migration
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("1. Sauvegarde des données existantes...")
        
        # Vérifier si la table existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='core_enterprises'
        """)
        
        if not cursor.fetchone():
            print("❌ Table core_enterprises non trouvée")
            return False
        
        # Vérifier la structure actuelle
        cursor.execute("PRAGMA table_info(core_enterprises)")
        columns = cursor.fetchall()
        print(f"Structure actuelle: {len(columns)} colonnes")
        
        # Sauvegarder les données existantes (sans le logo pour l'instant)
        cursor.execute("""
            SELECT id, name, address, phone, email, rccm, id_nat, slogan, currency, created_at
            FROM core_enterprises
        """)
        existing_data = cursor.fetchall()
        print(f"Données sauvegardées: {len(existing_data)} entreprises")
        
        print("2. Recréation de la table avec le nouveau schéma...")
        
        # Supprimer l'ancienne table
        cursor.execute("DROP TABLE IF EXISTS core_enterprises_backup")
        cursor.execute("ALTER TABLE core_enterprises RENAME TO core_enterprises_backup")
        
        # Créer la nouvelle table avec BLOB
        cursor.execute("""
            CREATE TABLE core_enterprises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255) NOT NULL,
                address TEXT,
                phone VARCHAR(50),
                email VARCHAR(100),
                rccm VARCHAR(100),
                id_nat VARCHAR(100),
                logo BLOB,
                slogan TEXT,
                currency VARCHAR(10) DEFAULT 'USD',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        print("3. Restauration des données...")
        
        # Insérer les données sauvegardées
        for row in existing_data:
            cursor.execute("""
                INSERT INTO core_enterprises 
                (id, name, address, phone, email, rccm, id_nat, slogan, currency, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, row)
        
        print("4. Suppression de la table de sauvegarde...")
        cursor.execute("DROP TABLE core_enterprises_backup")
        
        # Valider les changements
        conn.commit()
        conn.close()
        
        print("✅ Migration terminée avec succès!")
        
        # Vérifier que la migration a fonctionné
        print("5. Vérification de la migration...")
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        from ayanna_erp.database.database_manager import Entreprise
        enterprises = session.query(Entreprise).all()
        
        print(f"✅ {len(enterprises)} entreprises trouvées après migration")
        for enterprise in enterprises:
            print(f"   - {enterprise.name} (ID: {enterprise.id})")
            print(f"     Logo: {'BLOB vide' if enterprise.logo is None else f'BLOB {len(enterprise.logo)} bytes'}")
        
        db_manager.close_session()
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    migrate_logo_to_blob()