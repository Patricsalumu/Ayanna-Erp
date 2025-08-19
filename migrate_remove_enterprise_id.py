#!/usr/bin/env python3
"""
Script pour migrer la base de données - Suppression de enterprise_id de compta_comptes
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import sqlite3
from ayanna_erp.database.database_manager import DatabaseManager

print("🔄 Migration de la base de données - Suppression de enterprise_id de compta_comptes...")

# Sauvegarder les données existantes
print("📦 Sauvegarde des données existantes...")

conn = sqlite3.connect('ayanna_erp.db')
cursor = conn.cursor()

# Récupérer les comptes existants avec leur classe
cursor.execute("""
    SELECT c.id, c.numero, c.nom, c.libelle, c.actif, c.classe_comptable_id, 
           c.date_creation, c.date_modification
    FROM compta_comptes c
""")
comptes_data = cursor.fetchall()

print(f"✅ {len(comptes_data)} comptes sauvegardés")

# Supprimer l'ancienne table
cursor.execute("DROP TABLE IF EXISTS compta_comptes")
print("🗑️ Ancienne table compta_comptes supprimée")

conn.close()

# Recréer la base avec le nouveau modèle
print("🔨 Recréation de la base de données...")
db_manager = DatabaseManager()
db_manager.initialize_database()

# Restaurer les données
print("📥 Restauration des données...")
conn = sqlite3.connect('ayanna_erp.db')
cursor = conn.cursor()

for compte in comptes_data:
    try:
        cursor.execute("""
            INSERT INTO compta_comptes (id, numero, nom, libelle, actif, classe_comptable_id, date_creation, date_modification)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, compte)
    except Exception as e:
        print(f"⚠️ Erreur lors de la restauration du compte {compte[1]}: {e}")

conn.commit()
conn.close()

print("✅ Migration terminée avec succès!")
print("✅ Le champ enterprise_id a été supprimé de compta_comptes")
print("✅ L'enterprise_id est maintenant accessible via la relation classe_comptable")
