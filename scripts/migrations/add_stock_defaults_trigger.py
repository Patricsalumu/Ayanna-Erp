"""
Migration permanente : ajoute un trigger SQLite qui garantit que
reserved_quantity, min_stock_level, unit_cost, total_cost, quantity
ne peuvent jamais être NULL dans stock_produits_entrepot.

Ce script est idempotent (peut être relancé sans risque).
"""
import sqlite3

DB_PATH = r'c:\Ayanna Mode avion\ayanna_erp.db'

TRIGGER_SQL = """
CREATE TRIGGER IF NOT EXISTS trg_stock_entrepot_no_nulls
AFTER INSERT ON stock_produits_entrepot
WHEN NEW.quantity IS NULL
  OR NEW.reserved_quantity IS NULL
  OR NEW.unit_cost IS NULL
  OR NEW.total_cost IS NULL
  OR NEW.min_stock_level IS NULL
BEGIN
    UPDATE stock_produits_entrepot
    SET quantity          = COALESCE(quantity, 0),
        reserved_quantity = COALESCE(reserved_quantity, 0),
        unit_cost         = COALESCE(unit_cost, 0),
        total_cost        = COALESCE(total_cost, 0),
        min_stock_level   = COALESCE(min_stock_level, 0)
    WHERE id = NEW.id;
END
"""

conn = sqlite3.connect(DB_PATH)
try:
    conn.execute("DROP TRIGGER IF EXISTS trg_stock_entrepot_no_nulls")
    conn.execute(TRIGGER_SQL)
    conn.commit()
    
    # Vérifier
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='trigger' AND name='trg_stock_entrepot_no_nulls'"
    ).fetchone()
    print(f"Trigger créé : {row[0]}" if row else "ERREUR : trigger non trouvé")
    
    # Aussi corriger tous les NULLs existants dans toute la table
    conn.execute("""
        UPDATE stock_produits_entrepot
        SET quantity          = COALESCE(quantity, 0),
            reserved_quantity = COALESCE(reserved_quantity, 0),
            unit_cost         = COALESCE(unit_cost, 0),
            total_cost        = COALESCE(total_cost, 0),
            min_stock_level   = COALESCE(min_stock_level, 0)
        WHERE quantity IS NULL
           OR reserved_quantity IS NULL
           OR unit_cost IS NULL
           OR total_cost IS NULL
           OR min_stock_level IS NULL
    """)
    count = conn.execute("SELECT changes()").fetchone()[0]
    conn.commit()
    print(f"Lignes existantes corrigées : {count}")
    print("Migration terminée avec succès.")
finally:
    conn.close()
