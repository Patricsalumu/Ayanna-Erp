Migration: ajouter la colonne `compte_variation_id` à `compta_config`

But: Cette migration ajoute la colonne `compte_variation_id` qui sera utilisée comme "compte de variation" débité lors des sorties de stock (COGS/variation de stock).

Fichiers fournis:
- 0001_add_compte_variation_id.sql : script SQL pour SQLite et PostgreSQL (commenté)

Exécution (PowerShell) :

- SQLite (fichier DB: data/sqlite.db par exemple) :
```powershell
sqlite3 path\to\your\db.sqlite < scripts\migrations\0001_add_compte_variation_id.sql
```

- PostgreSQL (via psql) :
```powershell
psql -h <host> -U <user> -d <database> -f scripts\migrations\0001_add_compte_variation_id.sql
```

Notes et recommandations :
- Vérifiez d'abord la structure actuelle de `compta_config` avant d'exécuter la migration.
- Si vous utilisez SQLite et souhaitez rendre la colonne NOT NULL, il faudra créer une table temporaire, copier les données en fournissant une valeur par défaut, puis renommer les tables (procédure plus longue).
- Après avoir ajouté la colonne, complétez la table `compta_config` avec l'ID du compte de variation pour chaque `pos_id` concerné.

Exemple SQL pour renseigner la valeur (Postgres / SQLite) :
```sql
UPDATE compta_config SET compte_variation_id = 123 WHERE pos_id = 1;
```

Besoin d'aide pour :
- générer une migration adaptée à votre moteur exact (SQLite, Postgres, MySQL)
- appliquer la valeur par défaut pour les anciens enregistrements
- ajouter une migration Alembic si vous utilisez Alembic
