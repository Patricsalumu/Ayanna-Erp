"""
Correction des valeurs NULL dans stock_produits_entrepot pour SIMBA et TEMBO
dans l'entrepôt Stock comptoir (id=6)
"""
import sqlite3
from datetime import datetime

db = r'c:\Ayanna Mode avion\ayanna_erp.db'
conn = sqlite3.connect(db)
cur = conn.cursor()

print("=== Avant correction ===")
cur.execute("SELECT id, product_id, quantity, reserved_quantity, unit_cost, total_cost, min_stock_level FROM stock_produits_entrepot WHERE warehouse_id=6 AND product_id IN (7,8)")
for r in cur.fetchall():
    print(r)

# Corriger reserved_quantity NULL → 0 et min_stock_level NULL → 0
# et recalculer total_cost = quantity * unit_cost
cur.execute("""
    UPDATE stock_produits_entrepot
    SET reserved_quantity = COALESCE(reserved_quantity, 0),
        min_stock_level = COALESCE(min_stock_level, 0),
        total_cost = quantity * COALESCE(unit_cost, 0)
    WHERE warehouse_id = 6 AND product_id IN (7, 8)
""")
conn.commit()

print("\n=== Après correction ===")
cur.execute("SELECT id, product_id, quantity, reserved_quantity, unit_cost, total_cost, min_stock_level FROM stock_produits_entrepot WHERE warehouse_id=6 AND product_id IN (7,8)")
for r in cur.fetchall():
    print(r)

# Aussi corriger tous les autres NULL dans l'entrepôt Stock comptoir
print("\n=== Corriger tous NULL dans Stock comptoir ===")
cur.execute("""
    UPDATE stock_produits_entrepot
    SET reserved_quantity = COALESCE(reserved_quantity, 0),
        min_stock_level = COALESCE(min_stock_level, 0)
    WHERE warehouse_id = 6
""")
conn.commit()
print("Correction effectuée.")

conn.close()
print("\nTerminé.")
