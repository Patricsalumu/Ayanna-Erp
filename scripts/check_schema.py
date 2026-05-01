import sqlite3
conn = sqlite3.connect(r'c:\Ayanna Mode avion\ayanna_erp.db')
sql = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='stock_produits_entrepot'").fetchone()[0]
print(sql)
conn.close()
