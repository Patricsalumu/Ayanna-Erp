import sqlite3
from pathlib import Path

SQL_FILE = Path(__file__).with_name('populate_total_counted_purchase.sql')
DB_PATH = Path(__file__).parent.parent / 'ayanna_erp.db'

if not SQL_FILE.exists():
    print('SQL file not found:', SQL_FILE)
    raise SystemExit(1)
if not DB_PATH.exists():
    print('Database file not found:', DB_PATH)
    raise SystemExit(1)

sql = SQL_FILE.read_text(encoding='utf-8')

print('Connecting to DB:', DB_PATH)
conn = sqlite3.connect(str(DB_PATH))
try:
    # Ensure column exists in stock_inventaire
    cur = conn.cursor()
    cur.execute("PRAGMA table_info('stock_inventaire')")
    cols = [r[1] for r in cur.fetchall()]
    if 'total_counted_purchase_value' not in cols:
        print('Adding column total_counted_purchase_value to stock_inventaire')
        cur.execute("ALTER TABLE stock_inventaire ADD COLUMN total_counted_purchase_value NUMERIC(15,2) DEFAULT 0.0")
        conn.commit()

    conn.executescript(sql)
    conn.commit()
    print('Population completed successfully')
except Exception as e:
    print('Error executing SQL:', e)
    raise
finally:
    conn.close()
