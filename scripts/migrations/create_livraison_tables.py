"""
Migration : Création des tables stock_livraisons et stock_livraison_items
Exécuter une seule fois (ou plusieurs fois — le CREATE TABLE IF NOT EXISTS est idempotent).

Usage :
    python scripts/migrations/create_livraison_tables.py
"""

import sys
import os

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ayanna_erp.database.database_manager import DatabaseManager
from sqlalchemy import text


def migrate():
    db = DatabaseManager()
    with db.get_session() as session:
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS stock_livraisons (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                numero              TEXT    NOT NULL UNIQUE,
                entreprise_id       INTEGER NOT NULL,
                entrepot_depart_id  INTEGER NOT NULL REFERENCES stock_warehouses(id),
                entrepot_arrivee_id INTEGER NOT NULL REFERENCES stock_warehouses(id),
                statut              TEXT    NOT NULL DEFAULT 'brouillon',
                valeur_totale       REAL    NOT NULL DEFAULT 0,
                utilisateur_id      INTEGER,
                utilisateur_nom     TEXT,
                date_creation       DATETIME DEFAULT CURRENT_TIMESTAMP,
                date_livraison      DATETIME,
                date_reception      DATETIME,
                notes               TEXT
            )
        """))

        session.execute(text("""
            CREATE TABLE IF NOT EXISTS stock_livraison_items (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                livraison_id  INTEGER NOT NULL REFERENCES stock_livraisons(id) ON DELETE CASCADE,
                product_id    INTEGER NOT NULL,
                product_name  TEXT,
                product_code  TEXT,
                quantite      REAL    NOT NULL,
                cout_unitaire REAL    DEFAULT 0,
                total_ligne   REAL    DEFAULT 0
            )
        """))

        session.commit()
        print("✅ Tables stock_livraisons et stock_livraison_items créées (ou déjà présentes).")


if __name__ == "__main__":
    migrate()
