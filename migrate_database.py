# -*- coding: utf-8 -*-
"""
Script de migration pour mettre à jour le schéma de base de données
Migration: account_id -> compte_produit_id + compte_charge_id
"""

import sqlite3
import os
import sys
from datetime import datetime

def migrate_database():
    """Effectue la migration du schéma de base de données"""

    db_path = os.path.join(os.path.dirname(__file__), 'ayanna_erp.db')

    if not os.path.exists(db_path):
        print(f"❌ Base de données non trouvée: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("🔄 Démarrage de la migration de base de données...")

        # Tables à migrer
        tables_to_migrate = [
            ('core_products', 'account_id'),
            ('event_services', 'account_id'),
            ('event_products', 'account_id'),
            ('shop_services', 'account_id'),  # Pour boutique et vente
        ]

        for table_name, old_column in tables_to_migrate:
            print(f"\n📋 Migration de la table: {table_name}")

            # Vérifier si la table existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                print(f"  ⚠️  Table {table_name} n'existe pas, ignorée")
                continue

            # Vérifier si l'ancienne colonne existe
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            if old_column not in column_names:
                print(f"  ⚠️  Colonne {old_column} n'existe pas dans {table_name}, ignorée")
                continue

            # Vérifier si les nouvelles colonnes existent déjà
            if 'compte_produit_id' in column_names and 'compte_charge_id' in column_names:
                print(f"  ✅ Table {table_name} déjà migrée")
                continue

            print(f"  🔄 Migration en cours pour {table_name}...")

            # Étape 1: Renommer l'ancienne colonne en compte_produit_id
            try:
                cursor.execute(f"ALTER TABLE {table_name} RENAME COLUMN {old_column} TO compte_produit_id")
                print(f"  ✅ Colonne {old_column} renommée en compte_produit_id")
            except sqlite3.OperationalError as e:
                print(f"  ❌ Erreur lors du renommage: {e}")
                continue

            # Étape 2: Ajouter la colonne compte_charge_id
            try:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN compte_charge_id INTEGER")
                print(f"  ✅ Colonne compte_charge_id ajoutée")
            except sqlite3.OperationalError as e:
                print(f"  ❌ Erreur lors de l'ajout de compte_charge_id: {e}")
                continue

            # Étape 3: Créer les index si nécessaire (optionnel)
            try:
                # Vérifier si les index existent déjà
                cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE ?", (f'ix_{table_name}_compte%',))
                existing_indexes = cursor.fetchall()

                if not any('compte_produit_id' in idx[0] for idx in existing_indexes):
                    cursor.execute(f"CREATE INDEX ix_{table_name}_compte_produit_id ON {table_name}(compte_produit_id)")
                    print(f"  ✅ Index créé pour compte_produit_id")

                if not any('compte_charge_id' in idx[0] for idx in existing_indexes):
                    cursor.execute(f"CREATE INDEX ix_{table_name}_compte_charge_id ON {table_name}(compte_charge_id)")
                    print(f"  ✅ Index créé pour compte_charge_id")

            except sqlite3.OperationalError as e:
                print(f"  ⚠️  Erreur lors de la création des index: {e}")

        # Sauvegarder les changements
        conn.commit()
        print("\n✅ Migration terminée avec succès!")
        print(f"📅 Date de migration: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Vérifier le résultat
        print("\n🔍 Vérification des tables migrées:")
        for table_name, _ in tables_to_migrate:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            compte_cols = [col for col in columns if 'compte_' in col[1]]
            if compte_cols:
                print(f"  📊 {table_name}: {len(compte_cols)} colonnes comptables")
                for col in compte_cols:
                    print(f"    - {col[1]} (type: {col[2]})")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def create_backup():
    """Créer une sauvegarde de la base de données avant migration"""
    db_path = os.path.join(os.path.dirname(__file__), 'ayanna_erp.db')
    backup_path = os.path.join(os.path.dirname(__file__), f'ayanna_erp_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')

    if os.path.exists(db_path):
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"💾 Sauvegarde créée: {backup_path}")
        return backup_path
    else:
        print("❌ Base de données non trouvée pour la sauvegarde")
        return None

if __name__ == "__main__":
    print("🚀 Script de migration Ayanna ERP")
    print("=" * 50)

    # Créer une sauvegarde automatiquement
    backup_path = create_backup()
    if not backup_path:
        sys.exit(1)

    print()

    # Effectuer la migration automatiquement
    print("🔄 Démarrage de la migration automatique...")
    success = migrate_database()

    if success:
        print("\n🎉 Migration réussie !")
        print(f"📁 Sauvegarde disponible: {backup_path}")
    else:
        print("\n💥 Migration échouée !")
        print("🔄 Vous pouvez restaurer la sauvegarde si nécessaire")
        sys.exit(1)