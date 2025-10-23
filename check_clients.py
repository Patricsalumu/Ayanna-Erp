import sqlite3

conn = sqlite3.connect('ayanna_erp.db')
c = conn.cursor()

print('=== VÉRIFICATION CLIENTS ===')
print('Clients (tous):')
try:
    c.execute('SELECT id, nom, prenom, telephone, pos_id, is_active FROM shop_clients')
    rows = c.fetchall()
    if not rows:
        print('  (aucun client dans shop_clients)')
    else:
        for r in rows[:10]:  # Premiers 10 seulement
            print(f'  {r}')
        if len(rows) > 10:
            print(f'  ... et {len(rows)-10} autres')
except Exception as e:
    print(f'Erreur: {e}')

print(f'\nTotal clients: {len(rows) if "rows" in locals() else 0}')

print('\nClients actifs par pos_id:')
try:
    c.execute('SELECT pos_id, COUNT(*) FROM shop_clients WHERE is_active=1 GROUP BY pos_id')
    rows = c.fetchall()
    for r in rows:
        print(f'  pos_id={r[0]}: {r[1]} clients actifs')
    if not rows:
        print('  (aucun client actif)')
except Exception as e:
    print(f'Erreur: {e}')

conn.close()