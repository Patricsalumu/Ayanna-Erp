"""
Migration 0010 – Ajout de la colonne `modules` (TEXT) dans `core_users`.

Ce script parcourt les bases SQLite du projet et ajoute la colonne `modules`
si elle n'existe pas encore. La colonne contiendra une liste JSON de noms de
modules autorisés pour l'utilisateur — ex: ["Restaurant", "Vente"].

Usage:
    python scripts/migrations/0010_add_user_modules.py

La migration est idempotente.
"""

import sqlite3
from pathlib import Path
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SEARCH_DIRS = [PROJECT_ROOT, PROJECT_ROOT / "data"]
TABLE_NAME = "core_users"
COLUMN_NAME = "modules"


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cursor.fetchone() is not None


def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cursor = conn.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cursor.fetchall()]
    return column in cols


def migrate_db(db_path: Path) -> str:
    try:
        conn = sqlite3.connect(str(db_path))
        try:
            if not table_exists(conn, TABLE_NAME):
                return "no_table"
            if column_exists(conn, TABLE_NAME, COLUMN_NAME):
                return "already_exists"
            conn.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN {COLUMN_NAME} TEXT")
            conn.commit()
            return "migrated"
        finally:
            conn.close()
    except Exception as exc:
        return f"error: {exc}"


def find_sqlite_dbs() -> list:
    found = []
    for search_dir in SEARCH_DIRS:
        if not search_dir.exists():
            continue
        for path in search_dir.rglob("*.db"):
            if path not in found:
                found.append(path)
        for path in search_dir.rglob("*.sqlite"):
            if path not in found:
                found.append(path)
    return found


def main():
    dbs = find_sqlite_dbs()
    if not dbs:
        print("[INFO] Aucune base de données SQLite trouvée.")
        return

    migrated = 0
    skipped = 0
    errors = 0

    for db in dbs:
        result = migrate_db(db)
        rel = db.relative_to(PROJECT_ROOT) if PROJECT_ROOT in db.parents else db
        if result == "migrated":
            print(f"  ✓ Migré   : {rel}")
            migrated += 1
        elif result == "already_exists":
            print(f"  - Ignoré  : {rel}  (colonne déjà présente)")
            skipped += 1
        elif result == "no_table":
            print(f"  ~ Ignoré  : {rel}  (table '{TABLE_NAME}' absente)")
            skipped += 1
        else:
            print(f"  ✗ Erreur  : {rel}  → {result}")
            errors += 1

    print(f"\n[RÉSUMÉ] migré={migrated}  ignoré={skipped}  erreur={errors}")


if __name__ == "__main__":
    main()
