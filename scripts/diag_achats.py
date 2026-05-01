import sqlite3
db = r'c:\Ayanna Mode avion\ayanna_erp.db'
conn = sqlite3.connect(db)
cur = conn.cursor()

# Check core_products code for simba/tembo
print("core_products simba/tembo:")
cur.execute("SELECT id, name, code, cost, price_unit FROM core_products WHERE id IN (7,8)")
for r in cur.fetchall():
    print(r)

# Check achat commandes schema
print("\nachat_commandes schema:")
cur.execute("PRAGMA table_info(achat_commandes)")
for r in cur.fetchall():
    print(r)

# Check achat commandes with their warehouse destination
print("\nachat_commandes:")
cur.execute("SELECT * FROM achat_commandes ORDER BY id")
rows = cur.fetchall()
for r in rows:
    print(r)

# Check achat_commande_lignes for simba/tembo  
print("\nachat lignes for simba/tembo:")
cur.execute("""
    SELECT acl.commande_id, acl.product_id, p.name, acl.quantite, acl.prix_unitaire
    FROM achat_commande_lignes acl
    JOIN core_products p ON p.id = acl.product_id
    WHERE acl.product_id IN (7,8)
""")
for r in cur.fetchall():
    print(r)

conn.close()
