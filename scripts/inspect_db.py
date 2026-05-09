import sqlite3, json

conn = sqlite3.connect('ayanna_erp.db')
cur = conn.cursor()

print('PRAGMA core_users:')
print(cur.execute("PRAGMA table_info(core_users)").fetchall())

print('\ncore_users rows (id,email,password,created_at):')
print(json.dumps(cur.execute("SELECT id,email,password,created_at FROM core_users").fetchall(), ensure_ascii=False, default=str))

print('\nPRAGMA core_enterprises:')
print(cur.execute("PRAGMA table_info(core_enterprises)").fetchall())

print('\ncore_enterprises rows (id,name,email,created_at):')
print(json.dumps(cur.execute("SELECT id,name,email,created_at FROM core_enterprises").fetchall(), ensure_ascii=False, default=str))

conn.close()

print('\n--- core_configsync ---')
conn = sqlite3.connect('ayanna_erp.db')
cur = conn.cursor()
try:
	print(json.dumps(cur.execute("SELECT id, server_url, server_email, server_password, api_token, last_sync_at, last_sync_by, last_sync_status FROM core_configsync").fetchall(), ensure_ascii=False, default=str))
except Exception as e:
	print('core_configsync query failed:', e)
try:
	print('\n--- core_sync_settings ---')
	print(json.dumps(cur.execute("SELECT id, api_url, api_token, last_sync, last_sync_status, last_sync_message FROM core_sync_settings").fetchall(), ensure_ascii=False, default=str))
except Exception as e:
	print('core_sync_settings query failed:', e)
conn.close()
