import sys, sqlite3, os
sys.path.insert(0, '.')

from ayanna_erp.database import database_manager as dm
dm.DatabaseManager._migrations_executed = False

from ayanna_erp.database.database_manager import DatabaseManager, Base

# Audit chaque fichier .db trouve dans le dossier courant
db_files = [f for f in os.listdir('.') if f.endswith('.db')]
print(f"Fichiers DB trouves: {db_files}")

for db_file in db_files:
    print(f"\n{'='*60}")
    print(f"  Audit: {db_file}")
    print(f"{'='*60}")

    dm.DatabaseManager._migrations_executed = False

    con = sqlite3.connect(db_file)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    db_tables = {r[0]: [] for r in cur.fetchall()}
    for tbl in db_tables:
        cur.execute(f'PRAGMA table_info({tbl})')
        db_tables[tbl] = [r[1] for r in cur.fetchall()]
    con.close()

    model_tables = {}
    for mapper in Base.registry.mappers:
        try:
            tbl = mapper.persist_selectable.name
        except AttributeError:
            tbl = mapper.mapped_table.name
        model_tables[tbl] = [c.key for c in mapper.columns]

    print('--- Colonnes modele ABSENTES de la BDD ---')
    missing_any = False
    for tbl, model_cols in sorted(model_tables.items()):
        if tbl not in db_tables:
            print(f'  TABLE ENTIERE ABSENTE: {tbl}')
            missing_any = True
            continue
        db_cols = db_tables[tbl]
        missing = [c for c in model_cols if c not in db_cols]
        if missing:
            print(f'  {tbl}: manquant -> {missing}')
            missing_any = True

    if not missing_any:
        print('  Aucun probleme!')

sys.exit(0)

con = sqlite3.connect('ayanna_erp.db')
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
db_tables = {r[0]: [] for r in cur.fetchall()}
for tbl in db_tables:
    cur.execute(f'PRAGMA table_info({tbl})')
    db_tables[tbl] = [r[1] for r in cur.fetchall()]
con.close()

model_tables = {}
for mapper in Base.registry.mappers:
    tbl = mapper.mapped_table.name
    model_tables[tbl] = [c.key for c in mapper.columns]

print('=== Colonnes modele ABSENTES de la BDD ===')
missing_any = False
for tbl, model_cols in sorted(model_tables.items()):
    if tbl not in db_tables:
        print(f'  TABLE ENTIERE ABSENTE: {tbl}')
        missing_any = True
        continue
    db_cols = db_tables[tbl]
    missing = [c for c in model_cols if c not in db_cols]
    if missing:
        print(f'  {tbl}: manquant -> {missing}')
        missing_any = True

if not missing_any:
    print('  Aucun probleme detecte!')

print()
print('=== Tables presentes en BDD mais pas dans le modele ===')
for tbl in sorted(db_tables):
    if tbl not in model_tables:
        print(f'  {tbl} (pas de modele SQLAlchemy)')
