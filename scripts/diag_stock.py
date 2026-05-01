import sqlite3
db = r'c:\Ayanna Mode avion\ayanna_erp.db'
conn = sqlite3.connect(db)
cur = conn.cursor()

# List all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
print("=== Tables ===")
for r in cur.fetchall():
    print(r[0])

# Check schema stock_produits_entrepot
print("\n=== Schema stock_produits_entrepot ===")
cur.execute("PRAGMA table_info(stock_produits_entrepot)")
for r in cur.fetchall():
    print(r)

# Check stock for simba/tembo
print("\n=== Stock simba(7) tembo(8) ===")
cur.execute("""
    SELECT spe.product_id, p.name, sw.name, spe.quantity, spe.reserved_quantity
    FROM stock_produits_entrepot spe
    JOIN stock_warehouses sw ON spe.warehouse_id = sw.id
    LEFT JOIN core_products p ON p.id = spe.product_id
    WHERE spe.product_id IN (7,8)
    ORDER BY spe.product_id, sw.name
""")
for r in cur.fetchall():
    print(r)

# Check livraisons tables
print("\n=== Tables livraisons ===")
cur.execute("SELECT name FROM sqlite_master WHERE name LIKE '%livrai%' OR name LIKE '%mouv%' OR name LIKE '%movement%'")
for r in cur.fetchall():
    print(r[0])

# Check stock movements table name
print("\n=== stock_mouv tables ===")
cur.execute("SELECT name FROM sqlite_master WHERE name LIKE '%stock%'")
for r in cur.fetchall():
    print(r[0])

conn.close()
