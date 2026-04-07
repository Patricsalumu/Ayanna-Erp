import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parents[1] / 'ayanna_erp.db'
print('DB path:', db_path)
conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

print('\n---- shop_services ----')
try:
    cur.execute('SELECT id, pos_id, name, price, is_active FROM shop_services ORDER BY id')
    rows = cur.fetchall()
    for r in rows:
        print({'id': r[0], 'pos_id': r[1], 'name': r[2], 'price': r[3], 'is_active': r[4]})
except Exception as e:
    print('shop_services error:', e)

print('\n---- event_services ----')
try:
    cur.execute('SELECT id, pos_id, name, price, is_active FROM event_services ORDER BY id')
    rows = cur.fetchall()
    for r in rows:
        print({'id': r[0], 'pos_id': r[1], 'name': r[2], 'price': r[3], 'is_active': r[4]})
except Exception as e:
    print('event_services error:', e)

conn.close()
