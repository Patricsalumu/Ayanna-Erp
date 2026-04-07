#!/usr/bin/env python3
import sqlite3
import pprint
from pathlib import Path

db = Path(__file__).parent.parent / 'ayanna_erp.db'
if not db.exists():
    print('DB not found:', db)
    raise SystemExit(1)
conn = sqlite3.connect(str(db))
rows = conn.execute('PRAGMA table_info(restau_paniers)').fetchall()
conn.close()
print('restau_paniers schema:')
pprint.pprint(rows)
