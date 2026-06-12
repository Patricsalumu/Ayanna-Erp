# Migration: Table restau_bon_commandes

## Améliorations apportées au code SQL original

### ✅ Améliorations principales

1. **Auto-incrément d'ID**: `INTEGER PRIMARY KEY AUTOINCREMENT` pour éviter les collisions
2. **Clé unique composée**: `UNIQUE(entreprise_id, numero_bon)` pour garantir l'unicité des numéros par entreprise
3. **Valeurs par défaut**: 
   - `montant_total DEFAULT 0.0`
   - `statut DEFAULT 'valide'`
   - `created_at DEFAULT CURRENT_TIMESTAMP`
   - `updated_at DEFAULT CURRENT_TIMESTAMP`

4. **Toutes les clés étrangères**:
   ```sql
   FOREIGN KEY(restau_panier_id) REFERENCES restau_paniers(id) ON DELETE CASCADE
   FOREIGN KEY(entreprise_id) REFERENCES entreprises(id) ON DELETE CASCADE
   FOREIGN KEY(serveuse_id) REFERENCES users(id) ON DELETE SET NULL
   FOREIGN KEY(client_id) REFERENCES shop_clients(id) ON DELETE CASCADE
   FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
   ```

5. **Indices optimisés** pour les requêtes fréquentes:
   - Par panier
   - Par entreprise
   - Par statut
   - Par client
   - Par date de création
   - Indice composite (entreprise + statut)

## 📋 Comment utiliser

### Méthode 1: Script Python (RECOMMANDÉ)
```bash
cd c:\apps\ayannaerp\Ayanna-Erp
python scripts/migrate_restau_bon_commandes.py
```

✅ Avantages:
- Détecte automatiquement toutes les bases de données SQLite
- Applique la migration à toutes les BDD en une seule commande
- Affiche un résumé avec succès/erreurs

### Méthode 2: SQLite CLI directement
```bash
# Pour une base spécifique:
sqlite3 ayanna_erp/database/database.db < scripts/restau_bon_commandes.sql

# Ou via DB Manager (DB Browser for SQLite)
```

### Méthode 3: Depuis Python dans votre code
```python
from scripts.migrate_restau_bon_commandes import apply_migration

success, message = apply_migration('path/to/database.db')
print(message)
```

## 🔍 Vérifier la migration

Après l'exécution, vérifiez dans SQLite:

```sql
-- Vérifier la structure
.schema restau_bon_commandes

-- Vérifier les indices
SELECT name FROM sqlite_master 
WHERE type='index' 
AND tbl_name='restau_bon_commandes';

-- Vérifier les contraintes
PRAGMA foreign_key_list(restau_bon_commandes);
```

## ⚙️ Comportement des clés étrangères

| Colonne | Référence | Comportement |
|---------|-----------|--------------|
| `restau_panier_id` | `restau_paniers.id` | CASCADE (supprime le bon) |
| `entreprise_id` | `entreprises.id` | CASCADE (supprime le bon) |
| `serveuse_id` | `users.id` | SET NULL (vide la référence) |
| `client_id` | `shop_clients.id` | CASCADE (supprime le bon) |
| `user_id` | `users.id` | SET NULL (vide la référence) |

## 📊 Structure des données

```
restau_bon_commandes
├── id (PRIMARY KEY)
├── entreprise_id (NOT NULL) → entreprises.id
├── numero_bon (NOT NULL)
├── restau_panier_id (NOT NULL) → restau_paniers.id
├── serveuse_id → users.id (nullable)
├── client_id (NOT NULL) → shop_clients.id
├── user_id → users.id (nullable)
├── produits_json (TEXT, JSON format)
├── montant_total (FLOAT, défaut 0.0)
├── statut (VARCHAR, défaut 'valide')
├── created_at (DATETIME, auto)
└── updated_at (DATETIME, auto)
```

## ❓ FAQ

**Q: Que se passe-t-il si je supprime une entreprise?**
A: Les bons associés seront supprimés automatiquement (CASCADE)

**Q: Que se passe-t-il si je supprime une serveuse?**
A: La colonne `serveuse_id` sera mise à NULL (SET NULL), le bon reste intact

**Q: Comment gérer les mises à jour futures?**
A: Le script détecte si la table existe déjà avec `IF NOT EXISTS`, donc c'est idempotent

**Q: Les indices ralentissent-ils les insertions?**
A: Non, ils ralentissent un peu l'insertion mais accélèrent énormément les lectures
