import sqlite3

db_path = 'ayanna_erp.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Obtenir le schéma complet de la table
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='compta_config'")
schema = cursor.fetchone()
print('Schéma actuel de la table compta_config:')
print(schema[0] if schema else 'Table non trouvée')

print("\n" + "="*50)

# Vérifier les colonnes avec PRAGMA
cursor.execute('PRAGMA table_info(compta_config)')
columns = cursor.fetchall()
print('Colonnes selon PRAGMA:')
for col in columns:
    print(f'  {col[1]} ({col[2]}) - PK: {col[5]}, NOT NULL: {col[3]}, DEFAULT: {col[4]}')

print("\n" + "="*50)

# Essayer d'ajouter la colonne si elle n'existe pas
try:
    cursor.execute('SELECT compte_remise_id FROM compta_config LIMIT 1')
    print('✅ La colonne compte_remise_id existe déjà')
except sqlite3.OperationalError:
    print('❌ La colonne compte_remise_id n\'existe pas, ajout en cours...')
    try:
        cursor.execute('ALTER TABLE compta_config ADD COLUMN compte_remise_id INTEGER')
        conn.commit()
        print('✅ Colonne compte_remise_id ajoutée avec succès')
    except Exception as e:
        print(f'❌ Erreur lors de l\'ajout: {e}')

conn.close()