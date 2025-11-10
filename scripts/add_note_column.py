#!/usr/bin/env python3
"""
Script de migration : ajoute la colonne `note` à la table `restau_paniers` (SQLite).
Usage:
  py -3.12 scripts\add_note_column.py

Ce script effectue une sauvegarde du fichier de base de données avant la modification.
"""
import shutil
import sqlite3
import sys
from pathlib import Path

try:
    from ayanna_erp.core.config import Config
except Exception:
    # fallback: db in project root
    Config = None

# Déterminer le chemin de la base
if Config is not None:
    db_path = Path(Config.get_database_path())
else:
    db_path = Path(__file__).parent.parent / 'ayanna_erp.db'

if not db_path.exists():
    print(f"Fichier DB introuvable: {db_path}")
    sys.exit(1)

backup = db_path.with_suffix('.db.bak')
print(f"Sauvegarde de la base de données -> {backup}")
shutil.copy2(db_path, backup)

conn = sqlite3.connect(str(db_path))
cur = conn.cursor()
try:
    print("Ajout de la colonne 'note' à la table 'restau_paniers'...")
    cur.execute("ALTER TABLE restau_paniers ADD COLUMN note TEXT")
    conn.commit()
    print("✅ Colonne ajoutée avec succès.")
except sqlite3.OperationalError as e:
    msg = str(e).lower()
    if 'duplicate column' in msg or 'already exists' in msg or 'duplicate' in msg:
        print("ℹ️ La colonne 'note' existe déjà (aucune action réalisée).")
    else:
        print(f"❌ Erreur SQLite: {e}")
        print("La base de données a été sauvegardée. Vous pouvez restaurer la sauvegarde si nécessaire.")
        raise
finally:
    conn.close()

print("Terminé.")
