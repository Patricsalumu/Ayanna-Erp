import sqlite3

def main():
    conn = sqlite3.connect('ayanna_erp.db')
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'licen%';")
    tbls = [r[0] for r in cur.fetchall()]
    print('tables:', tbls)
    for t in ['licences', 'licence']:
        try:
            cur.execute(f'SELECT COUNT(*) FROM {t}')
            cnt = cur.fetchone()[0]
            print(f"{t} count= {cnt}")
            cur.execute(f'SELECT * FROM {t} LIMIT 5')
            rows = cur.fetchall()
            print('sample rows:', rows)
        except Exception as e:
            print(f"{t} error: {e}")
    conn.close()

if __name__ == '__main__':
    main()
