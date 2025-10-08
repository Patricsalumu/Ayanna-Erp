"""
Script pour migrer la table shop_clients et rendre le prénom optionnel
"""

import sqlite3
import os

def migrate_shop_clients():
    """Migrer la table shop_clients pour rendre prenom nullable"""
    
    db_path = "ayanna_erp.db"
    
    if not os.path.exists(db_path):
        print("❌ Base de données introuvable")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Migration de la table shop_clients...")
        
        # 1. Créer une nouvelle table avec le schéma corrigé
        cursor.execute("""
            CREATE TABLE shop_clients_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pos_id INTEGER NOT NULL,
                nom VARCHAR(100) NOT NULL,
                prenom VARCHAR(100),  -- Maintenant nullable
                telephone VARCHAR(20),  -- Maintenant nullable
                email VARCHAR(150),
                adresse TEXT,
                ville VARCHAR(100),
                code_postal VARCHAR(10),
                date_naissance DATETIME,
                type_client VARCHAR(50) DEFAULT 'Particulier',
                credit_limit DECIMAL(15,2) DEFAULT 0.0,
                balance DECIMAL(15,2) DEFAULT 0.0,
                notes TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Copier les données de l'ancienne table vers la nouvelle
        cursor.execute("""
            INSERT INTO shop_clients_new 
            SELECT * FROM shop_clients
        """)
        
        # 3. Supprimer l'ancienne table
        cursor.execute("DROP TABLE shop_clients")
        
        # 4. Renommer la nouvelle table
        cursor.execute("ALTER TABLE shop_clients_new RENAME TO shop_clients")
        
        conn.commit()
        print("✅ Migration terminée avec succès!")
        print("✅ Les champs 'prenom' et 'telephone' sont maintenant optionnels")
        
        # Vérifier la structure
        cursor.execute("PRAGMA table_info(shop_clients)")
        columns = cursor.fetchall()
        print("\n📋 Structure de la table shop_clients:")
        for col in columns:
            nullable = "NULL" if col[3] == 0 else "NOT NULL"
            print(f"  - {col[1]} ({col[2]}) {nullable}")
        
    except sqlite3.Error as e:
        print(f"❌ Erreur lors de la migration: {e}")
        conn.rollback()
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_shop_clients()