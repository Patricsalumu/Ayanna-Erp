#!/usr/bin/env python3
"""
Script de migration pour corriger la contrainte d'unicité des classes comptables.
Passe d'une contrainte unique sur 'code' à une contrainte composite sur ('code', 'enterprise_id').
"""

import sys
import os
import sqlite3

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import get_database_manager


def migrate_classes_constraints():
    """Migrer les contraintes de la table compta_classes"""
    print("🔧 Migration des contraintes de classes comptables")
    print("="*50)
    
    db_manager = get_database_manager()
    
    # Pour SQLite, on doit recréer la table car on ne peut pas modifier les contraintes directement
    try:
        # Connexion directe SQLite pour plus de contrôle
        db_path = "ayanna_erp.db"
        if not os.path.exists(db_path):
            print(f"❌ Base de données non trouvée: {db_path}")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("1️⃣ Vérification de la structure actuelle...")
        
        # Vérifier la structure actuelle
        cursor.execute("PRAGMA table_info(compta_classes)")
        columns_info = cursor.fetchall()
        
        print("📊 Colonnes actuelles:")
        for col in columns_info:
            print(f"   - {col[1]}: {col[2]} {'(PRIMARY KEY)' if col[5] else ''}")
        
        # Vérifier les contraintes actuelles
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='compta_classes'")
        current_schema = cursor.fetchone()
        
        if current_schema:
            print(f"\n📋 Schéma actuel:")
            print(f"   {current_schema[0]}")
        
        # Vérifier s'il y a déjà des données
        cursor.execute("SELECT COUNT(*) FROM compta_classes")
        count = cursor.fetchone()[0]
        print(f"\n📊 Nombre d'enregistrements existants: {count}")
        
        if count > 0:
            print("\n2️⃣ Sauvegarde des données existantes...")
            
            # Sauvegarder les données existantes
            cursor.execute("""
                CREATE TABLE compta_classes_backup AS 
                SELECT * FROM compta_classes
            """)
            print("✅ Données sauvegardées dans compta_classes_backup")
        
        print("\n3️⃣ Recréation de la table avec la nouvelle contrainte...")
        
        # Supprimer l'ancienne table
        cursor.execute("DROP TABLE compta_classes")
        
        # Créer la nouvelle table avec la contrainte corrigée
        cursor.execute("""
            CREATE TABLE compta_classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code VARCHAR(10) NOT NULL,
                nom VARCHAR(100) NOT NULL,
                libelle VARCHAR(255) NOT NULL,
                type VARCHAR(20) NOT NULL,
                document VARCHAR(50) NOT NULL,
                enterprise_id INTEGER NOT NULL,
                actif BOOLEAN DEFAULT 1,
                date_creation DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                date_modification DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                FOREIGN KEY (enterprise_id) REFERENCES core_enterprises(id),
                UNIQUE (code, enterprise_id)
            )
        """)
        print("✅ Nouvelle table créée avec contrainte composite (code, enterprise_id)")
        
        if count > 0:
            print("\n4️⃣ Restauration des données...")
            
            # Restaurer les données
            cursor.execute("""
                INSERT INTO compta_classes 
                (id, code, nom, libelle, type, document, enterprise_id, actif, date_creation, date_modification)
                SELECT id, code, nom, libelle, type, document, enterprise_id, actif, date_creation, date_modification
                FROM compta_classes_backup
            """)
            
            # Supprimer la table de sauvegarde
            cursor.execute("DROP TABLE compta_classes_backup")
            print("✅ Données restaurées")
        
        print("\n5️⃣ Vérification de la nouvelle structure...")
        
        # Vérifier la nouvelle structure
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='compta_classes'")
        new_schema = cursor.fetchone()
        
        if new_schema:
            print(f"📋 Nouveau schéma:")
            print(f"   {new_schema[0]}")
        
        # Vérifier que les données sont toujours là
        cursor.execute("SELECT COUNT(*) FROM compta_classes")
        new_count = cursor.fetchone()[0]
        print(f"\n📊 Nombre d'enregistrements après migration: {new_count}")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Migration terminée avec succès !")
        print("🎯 Les entreprises peuvent maintenant avoir les mêmes codes de classes")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur durant la migration: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    print("🚀 Migration des contraintes de classes comptables\n")
    
    success = migrate_classes_constraints()
    
    if success:
        print("\n🎉 Migration réussie !")
        print("✅ Contrainte d'unicité corrigée")
        print("✅ Multi-entreprises supporté")
        sys.exit(0)
    else:
        print("\n💥 Migration échouée !")
        sys.exit(1)