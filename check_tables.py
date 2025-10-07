import sqlite3

conn = sqlite3.connect('ayanna_erp.db')
cursor = conn.cursor()

# Lister toutes les tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
all_tables = cursor.fetchall()

print("Toutes les tables:")
for table in all_tables:
    print(f"  - {table[0]}")

print("\nTables liées aux produits/boutiques:")
for table in all_tables:
    if any(word in table[0].lower() for word in ['product', 'boutique', 'shop', 'pos']):
        print(f"  - {table[0]}")

conn.close()