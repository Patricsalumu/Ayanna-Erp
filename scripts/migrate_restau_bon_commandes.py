"""
Script pour créer ou mettre à jour la table restau_bon_commandes dans les bases de données SQLite.
Compatible avec toutes les bases de données du projet.
"""

import sqlite3
import os
from pathlib import Path

# Définir le SQL amélioré
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS restau_bon_commandes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entreprise_id INTEGER NOT NULL,
    numero_bon INTEGER NOT NULL,
    restau_panier_id INTEGER NOT NULL,
    serveuse_id INTEGER,
    client_id INTEGER NOT NULL,
    user_id INTEGER,
    produits_json TEXT NOT NULL,
    montant_total FLOAT DEFAULT 0.0,
    statut VARCHAR(50) DEFAULT 'valide',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY(restau_panier_id) REFERENCES restau_paniers(id) ON DELETE CASCADE,
    FOREIGN KEY(entreprise_id) REFERENCES entreprises(id) ON DELETE CASCADE,
    FOREIGN KEY(serveuse_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY(client_id) REFERENCES shop_clients(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Créer les indices pour optimiser les requêtes
CREATE INDEX IF NOT EXISTS idx_restau_bon_commandes_entreprise_id 
    ON restau_bon_commandes(entreprise_id);
CREATE INDEX IF NOT EXISTS idx_restau_bon_commandes_restau_panier_id 
    ON restau_bon_commandes(restau_panier_id);
CREATE INDEX IF NOT EXISTS idx_restau_bon_commandes_numero_bon 
    ON restau_bon_commandes(numero_bon);
CREATE INDEX IF NOT EXISTS idx_restau_bon_commandes_statut 
    ON restau_bon_commandes(statut);
CREATE INDEX IF NOT EXISTS idx_restau_bon_commandes_client_id 
    ON restau_bon_commandes(client_id);
CREATE INDEX IF NOT EXISTS idx_restau_bon_commandes_created_at 
    ON restau_bon_commandes(created_at);
"""

def find_sqlite_databases():
    """Trouver toutes les bases de données SQLite du projet"""
    root_path = Path(__file__).parent.parent
    db_files = []
    
    # Chemins connus des bases de données
    known_db_paths = [
        root_path / 'ayanna_erp' / 'database' / 'database.db',
        root_path / 'ayanna_erp' / 'ayanna_erp.sqbpro',
        root_path / 'ayanna_erp' / 'ss.sqbpro',
    ]
    
    for db_path in known_db_paths:
        if db_path.exists():
            db_files.append(db_path)
    
    # Chercher aussi les fichiers .db et .sqbpro récursivement
    for root, dirs, files in os.walk(root_path):
        # Ignorer node_modules et autres dossiers non pertinents
        if any(ignore in root for ignore in ['node_modules', 'venv', '.git', '__pycache__', 'vendor']):
            continue
        
        for file in files:
            if file.endswith('.db') or file.endswith('.sqbpro'):
                full_path = Path(root) / file
                if full_path not in db_files:
                    db_files.append(full_path)
    
    return db_files

def apply_migration(db_path):
    """Appliquer la migration à une base de données"""
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Exécuter le SQL
        for statement in CREATE_TABLE_SQL.split(';'):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        
        conn.commit()
        conn.close()
        return True, "✅ Succès"
    except sqlite3.OperationalError as e:
        return False, f"❌ Erreur: {str(e)}"
    except Exception as e:
        return False, f"❌ Erreur inattendue: {str(e)}"

def main():
    print("=" * 70)
    print("MIGRATION: Création table restau_bon_commandes")
    print("=" * 70)
    
    db_files = find_sqlite_databases()
    
    if not db_files:
        print("❌ Aucune base de données SQLite trouvée!")
        return
    
    print(f"\n📊 {len(db_files)} base(s) de données trouvée(s):\n")
    
    results = {}
    for i, db_path in enumerate(db_files, 1):
        print(f"{i}. {db_path.relative_to(db_path.parent.parent.parent)}")
        success, message = apply_migration(db_path)
        results[str(db_path)] = (success, message)
        print(f"   {message}\n")
    
    # Résumé
    print("\n" + "=" * 70)
    print("RÉSUMÉ")
    print("=" * 70)
    success_count = sum(1 for success, _ in results.values() if success)
    total_count = len(results)
    print(f"✅ Succès: {success_count}/{total_count}")
    
    if success_count < total_count:
        print("\n⚠️  Erreurs détectées:")
        for db_path, (success, message) in results.items():
            if not success:
                print(f"  - {Path(db_path).name}: {message}")

if __name__ == '__main__':
    main()
