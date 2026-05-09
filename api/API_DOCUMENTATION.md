# Ayanna ERP — Documentation API & Interconnexion

**Base URL :** `http://votre-serveur/api`  
**Authentification :** Bearer token (Laravel Sanctum)  
**Format :** JSON (`Content-Type: application/json`)  
**Encodage :** UTF-8

---

## Table des matières

1. [Architecture generale](#1-architecture-generale)
2. [Authentification](#2-authentification)
3. [Envoyer des donnees au serveur](#3-envoyer-des-donnees-au-serveur)
4. [Lire des donnees du serveur](#4-lire-des-donnees-du-serveur)
5. [Synchronisation bidirectionnelle](#5-synchronisation-bidirectionnelle)
6. [Exemples Python (application locale)](#6-exemples-python-application-locale)
7. [Reference des endpoints CRUD](#7-reference-des-endpoints-crud)
8. [Codes d'erreur](#8-codes-derreur)
9. [Deploiement et configuration](#9-deploiement-et-configuration)

---

## 1. Architecture generale

```
+-----------------------------+         HTTPS/HTTP          +----------------------+
|  Application locale         |  <---------------------->  |  Serveur Ayanna API  |
|  Ayanna ERP (Python/SQLite) |                             |  Laravel + MySQL     |
+-----------------------------+                             +----------------------+
         |  SQLite local                                             |  MySQL central
         |  (fonctionne hors-ligne)                                 |  (source de verite)
         +------------------ SYNC PUSH/PULL -------------------------+
```

**Principe de fonctionnement :**

| Scenario | Comportement |
|----------|-------------|
| Application locale **sans connexion** | Travaille sur SQLite local normalement |
| Connexion disponible | L'app pousse (`push`) ses changements locaux vers le serveur |
| Apres un push | L'app tire (`pull`) les donnees nouvelles du serveur |
| Strategie de conflit | **Le client gagne** (last-write-wins) — tout conflit est logge |

---

## 2. Authentification

### 2.1 Obtenir un token

```
POST /api/auth/login
```

**Corps :**
```json
{
  "email": "admin@ayanna.com",
  "password": "secret123"
}
```

**Reponse 200 :**
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Admin",
    "email": "admin@ayanna.com",
    "role": "admin",
    "enterprise_id": "..."
  },
  "token": "1|abcdefghij1234567890"
}
```

> **Stocker ce token** cote client. Il est valide jusqu'a deconnexion explicite.

### 2.2 Utiliser le token

Ajouter dans **tous** les appels suivants :

```
Authorization: Bearer 1|abcdefghij1234567890
Content-Type: application/json
```

### 2.3 Creer un compte

```
POST /api/auth/register
```

```json
{
  "name": "Jean Dupont",
  "email": "jean@example.com",
  "password": "secret123",
  "password_confirmation": "secret123",
  "enterprise_id": "<uuid>",
  "role": "admin"
}
```

### 2.4 Se deconnecter

```
POST /api/auth/logout         (token requis)
```

Revoque le token actuel.

### 2.5 Profil connecte

```
GET /api/auth/me              (token requis)
```

---

## 3. Envoyer des donnees au serveur

### Methode 1 — CRUD direct (donnees en temps reel)

Pour chaque ressource, les quatre operations standards sont disponibles.

#### Creer une ressource

```
POST /api/{ressource}         (token requis)
```

**Exemple — creer un client boutique :**
```
POST /api/shop/clients
```
```json
{
  "pos_id": "uuid-du-pos",
  "nom": "Marie Kamga",
  "prenom": "Marie",
  "telephone": "+237 6XX XXX XXX",
  "email": "marie@example.com",
  "adresse": "Douala, Akwa",
  "ville": "Douala",
  "type_client": "Particulier",
  "pays": "Cameroun"
}
```

**Reponse 201 :**
```json
{
  "id": "nouveau-uuid",
  "nom": "Marie Kamga",
  "created_at": "2026-05-01T10:00:00.000000Z"
}
```

#### Modifier une ressource

```
PUT /api/{ressource}/{id}     (token requis)
```

Envoyer uniquement les champs a modifier (patch partiel accepte).

#### Supprimer (soft-delete)

```
DELETE /api/{ressource}/{id}  (token requis)
```

La ressource n'est pas physiquement supprimee — `deleted_at` est renseigne.

---

### Methode 2 — Sync Push (envoi par lots depuis l'app locale)

```
POST /api/sync/push           (token requis)
```

Envoie **un lot d'operations** en une seule requete. C'est la methode recommandee pour synchroniser l'app locale.

**Corps :**
```json
{
  "operations": [
    {
      "table": "shop_clients",
      "operation": "INSERT",
      "data": {
        "id": "uuid-genere-cote-client",
        "pos_id": "uuid-pos",
        "nom": "Marie Kamga",
        "telephone": "+237 6XX XXX XXX",
        "type_client": "Particulier"
      },
      "client_updated_at": "2026-05-01T09:45:00Z"
    },
    {
      "table": "shop_paniers",
      "operation": "UPDATE",
      "data": {
        "id": "uuid-panier-existant",
        "statut": "ferme",
        "montant_total": 15000.00
      },
      "client_updated_at": "2026-05-01T09:50:00Z"
    },
    {
      "table": "shop_paniers",
      "operation": "DELETE",
      "data": { "id": "uuid-panier-annule" },
      "client_updated_at": "2026-05-01T09:52:00Z"
    }
  ]
}
```

**Champs d'une operation :**

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| `table` | string | oui | Nom de la table (voir liste complete section 5) |
| `operation` | string | oui | `INSERT`, `UPDATE` ou `DELETE` |
| `data` | object | oui | Donnees de l'enregistrement. `id` obligatoire |
| `client_updated_at` | ISO 8601 | oui | Timestamp de la modification cote client |

**Reponse 200 — tout succes :**
```json
{ "success": 3, "errors": [] }
```

**Reponse 207 — succes partiel :**
```json
{
  "success": 2,
  "errors": [
    {
      "table": "shop_paniers",
      "id": "uuid-panier-annule",
      "operation": "DELETE",
      "error": "Record not found"
    }
  ]
}
```

> **Important :** meme en cas d'erreur partielle (207), les operations reussies sont **commitees**. Traiter les erreurs localement avant de retenter.

---

## 4. Lire des donnees du serveur

### Methode 1 — Lecture directe d'une ressource

```
GET /api/{ressource}          (token requis)   -> liste paginee
GET /api/{ressource}/{id}     (token requis)   -> un enregistrement
```

**Exemple — liste des produits :**
```
GET /api/products?enterprise_id=uuid&page=1
```

**Reponse :**
```json
{
  "data": [
    {
      "id": "...",
      "name": "Eau minerale",
      "price_unit": 500.00,
      "unit": "bouteille",
      "is_active": true,
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "current_page": 1,
  "last_page": 4,
  "total": 87
}
```

**Filtres disponibles (selon l'endpoint) :**

| Parametre | Endpoints concernes |
|-----------|-------------------|
| `enterprise_id` | products, product-categories, pos-points... |
| `pos_id` | shop/paniers, restau/paniers, hotel/rooms... |
| `statut` | paniers, reservations... |
| `warehouse_id` | stock/mouvements, stock/produits |
| `date_from` / `date_to` | compta/journaux, achat/commandes |

---

### Methode 2 — Sync Pull (recuperer tous les changements depuis une date)

```
GET /api/sync/pull?last_sync=2026-05-01T00:00:00Z    (token requis)
```

Retourne **toutes les tables** modifiees depuis `last_sync`. Si `last_sync` est omis -> synchronisation complete (premier lancement).

**Reponse 200 :**
```json
{
  "server_time": "2026-05-01T12:00:00+00:00",
  "data": {
    "core_products": [
      {
        "id": "...",
        "name": "Eau minerale",
        "price_unit": 500.00,
        "deleted_at": null,
        "updated_at": "2026-05-01T11:30:00Z"
      }
    ],
    "shop_clients": [
      {
        "id": "...",
        "nom": "Marie Kamga",
        "deleted_at": null
      }
    ],
    "shop_paniers": [
      {
        "id": "...",
        "statut": "ferme",
        "deleted_at": "2026-05-01T11:45:00Z"
      }
    ]
  }
}
```

**Regles importantes :**
- Seules les tables ayant des enregistrements modifies apparaissent dans `data`
- Les enregistrements **supprimes** (soft-delete) sont inclus avec `deleted_at` non null -> les supprimer localement
- Stocker `server_time` comme nouvelle valeur de `last_sync` pour le prochain pull

---

## 5. Synchronisation bidirectionnelle

### Flux recommande (cycle complet)

```
+------------------------------------------------------------------+
|  1. Travailler localement (sans connexion si necessaire)         |
|                                                                   |
|  2. Connexion disponible -> PUSH                                 |
|     POST /api/sync/push                                          |
|     -> Envoyer toutes les modifications locales                  |
|                                                                   |
|  3. PULL                                                          |
|     GET /api/sync/pull?last_sync=<last_pull_timestamp>           |
|     -> Recuperer les changements du serveur                       |
|     -> Appliquer localement (upsert SQLite)                       |
|                                                                   |
|  4. Stocker le nouveau last_sync = server_time recu              |
|                                                                   |
|  5. Repeter a chaque reconnexion ou periodiquement               |
+------------------------------------------------------------------+
```

### Tables synchronisables

Toutes les tables suivantes sont supportees dans `push` et `pull` :

```
Core          : core_enterprises, core_users, modules, core_pos_points,
                core_payment_modes, core_product_categories, core_products,
                pos_product_access
Comptabilite  : compta_classes, compta_comptes, compta_journaux,
                compta_ecritures, compta_config
Achats/Stock  : core_fournisseurs, achat_commandes, achat_commande_lignes,
                achat_depenses, stock_warehouses, stock_produits_entrepot,
                stock_mouvements, stock_config, stock_inventaire,
                stock_inventaire_items
Boutique      : shop_clients, shop_services, shop_paniers, shop_panier_products,
                shop_panier_services, shop_payments, shop_expenses
Restaurant    : restau_salles, restau_tables, restau_paniers,
                restau_produit_panier, restau_payments, restau_expenses,
                restau_printed_invoices
Hotel         : hotel_categories, hotel_rooms, hotel_reservations, hotel_payments
Salle de Fete : event_clients, event_services, event_products, event_reservations,
                event_reservation_services, event_reservation_products,
                event_payments, event_stock_movements
Licences      : licences
```

---

## 6. Exemples Python (application locale)

### 6.1 Classe client API de base

```python
# ayanna_erp/utils/api_client.py
import requests
from datetime import datetime, timezone

class AyannaApiClient:
    def __init__(self, base_url: str, token: str = None):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = requests.Session()

    def _headers(self):
        h = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        if self.token:
            h['Authorization'] = f'Bearer {self.token}'
        return h

    def login(self, email: str, password: str) -> str:
        """Retourne le token. Leve une exception si echec."""
        resp = self.session.post(
            f'{self.base_url}/api/auth/login',
            json={'email': email, 'password': password},
            headers={'Content-Type': 'application/json'}
        )
        resp.raise_for_status()
        self.token = resp.json()['token']
        return self.token

    def push(self, operations: list) -> dict:
        """Envoie un lot d'operations. Retourne {success, errors}."""
        resp = self.session.post(
            f'{self.base_url}/api/sync/push',
            json={'operations': operations},
            headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()

    def pull(self, last_sync: str = None) -> dict:
        """
        Recupere les changements depuis last_sync (ISO 8601).
        Retourne {server_time, data: {table: [records]}}.
        """
        params = {}
        if last_sync:
            params['last_sync'] = last_sync
        resp = self.session.get(
            f'{self.base_url}/api/sync/pull',
            params=params,
            headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()
```

### 6.2 Envoyer des donnees (push)

```python
import uuid
from datetime import datetime, timezone

client = AyannaApiClient('http://votre-serveur')
client.login('admin@ayanna.com', 'secret123')

now = datetime.now(timezone.utc).isoformat()

operations = [
    {
        'table': 'shop_clients',
        'operation': 'INSERT',
        'data': {
            'id': str(uuid.uuid4()),    # UUID genere cote client
            'pos_id': 'uuid-du-pos',
            'nom': 'Marie Kamga',
            'telephone': '+237 6XX XXX XXX',
            'type_client': 'Particulier',
            'pays': 'Cameroun',
            'is_active': True,
        },
        'client_updated_at': now,
    },
    {
        'table': 'shop_paniers',
        'operation': 'UPDATE',
        'data': {
            'id': 'uuid-panier-existant',
            'statut': 'ferme',
            'montant_total': 25000.00,
        },
        'client_updated_at': now,
    },
]

result = client.push(operations)
print(f"Succes: {result['success']}, Erreurs: {len(result['errors'])}")

for err in result['errors']:
    print(f"  ERREUR {err['table']} [{err['id']}] -- {err['error']}")
```

### 6.3 Lire des donnees (pull)

```python
from sqlalchemy import text

def sync_depuis_serveur(db_session, api_client, last_sync: str):
    """
    Tire les changements serveur et les applique a la base SQLite locale.
    Retourne le nouveau timestamp a stocker comme last_sync.
    """
    result = api_client.pull(last_sync=last_sync)
    server_time = result['server_time']
    data = result.get('data', {})

    for table_name, records in data.items():
        for record in records:
            if record.get('deleted_at'):
                # Supprimer localement
                db_session.execute(
                    text(f"DELETE FROM {table_name} WHERE id = :id"),
                    {'id': record['id']}
                )
            else:
                # Upsert : inserer ou mettre a jour
                cols = list(record.keys())
                placeholders = ', '.join([f':{c}' for c in cols])
                updates = ', '.join([f'{c} = :{c}' for c in cols if c != 'id'])
                db_session.execute(
                    text(f"""
                        INSERT INTO {table_name} ({', '.join(cols)})
                        VALUES ({placeholders})
                        ON CONFLICT(id) DO UPDATE SET {updates}
                    """),
                    record
                )

    db_session.commit()
    return server_time  # Stocker comme nouveau last_sync


# Utilisation
last_sync = load_last_sync()        # ex: "2026-04-30T23:59:00Z" depuis un fichier de config
new_last_sync = sync_depuis_serveur(db, client, last_sync)
save_last_sync(new_last_sync)
```

### 6.4 Cycle de sync complet

```python
def synchroniser(db_session, base_url, email, password, last_sync_file='last_sync.txt'):
    """Cycle complet : login -> push modifications locales -> pull serveur."""

    # 1. Connexion
    client = AyannaApiClient(base_url)
    try:
        client.login(email, password)
    except Exception as e:
        print(f"Connexion impossible: {e}")
        return

    # 2. Recuperer les modifications locales non synchronisees
    operations = get_pending_local_operations(db_session)  # votre logique

    # 3. Push
    if operations:
        result = client.push(operations)
        print(f"Push: {result['success']} envoyes, {len(result['errors'])} erreurs")
        mark_operations_synced(db_session, operations, result['errors'])

    # 4. Pull
    try:
        with open(last_sync_file) as f:
            last_sync = f.read().strip()
    except FileNotFoundError:
        last_sync = None  # sync complete au premier run

    new_last_sync = sync_depuis_serveur(db_session, client, last_sync)

    # 5. Sauvegarder le timestamp
    with open(last_sync_file, 'w') as f:
        f.write(new_last_sync)

    print(f"Sync terminee. Prochain last_sync: {new_last_sync}")
```

---

## 7. Reference des endpoints CRUD

> Toutes les routes necessitent `Authorization: Bearer <token>` sauf `/auth/login` et `/auth/register`.
> Toutes les ressources supportent GET (liste), GET/{id}, POST, PUT/{id}, DELETE/{id} sauf mention contraire.

### Core

| Ressource | Endpoint | Champs principaux |
|-----------|----------|-------------------|
| Entreprises | `/api/entreprises` | `nom`, `adresse`, `telephone`, `email`, `devise`, `pays`, `secteur` |
| Utilisateurs | `/api/users` | `name`, `email`, `password`, `enterprise_id`, `pos_id`, `role` |
| Points de vente | `/api/pos-points` | `enterprise_id`, `nom`, `type` (boutique/restaurant/hotel/salle_fete), `actif` |
| Categories produits | `/api/product-categories` | `enterprise_id`, `name`, `description`, `parent_id`, `is_active` |
| Produits | `/api/products` | `enterprise_id`, `category_id`, `code`, `name`, `barcode`, `cost`, `price_unit`, `unit`, `is_active` |

### Comptabilite

| Ressource | Endpoint | Champs principaux |
|-----------|----------|-------------------|
| Classes | `/api/compta/classes` | `code`, `nom`, `type`, `document`, `enterprise_id` |
| Comptes | `/api/compta/comptes` | `numero`, `nom`, `libelle`, `actif`, `classe_comptable_id` |
| Journaux | `/api/compta/journaux` | `date_operation`, `libelle`, `montant`, `type_operation`, `enterprise_id` |
| Config | `/api/compta/config` | GET/{id}, GET/pos/{pos_id}, POST, PUT/{id} |

Filtres journaux : `?enterprise_id=&date_from=&date_to=`

### Achats et Stock

| Ressource | Endpoint | Champs principaux |
|-----------|----------|-------------------|
| Fournisseurs | `/api/fournisseurs` | `nom`, `telephone`, `adresse`, `email` |
| Commandes achat | `/api/achat/commandes` | `numero`, `fournisseur_id`, `entrepot_id`, `date_commande`, `montant_total`, `etat` |
| Entrepots | `/api/stock/warehouses` | `entreprise_id`, `code`, `name`, `type`, `is_default` |
| Stock produits | `/api/stock/produits` | `product_id`, `warehouse_id`, `quantity`, `reserved_quantity`, `unit_cost` |
| Mouvements | `/api/stock/mouvements` (pas de PUT) | `product_id`, `warehouse_id`, `type_mouvement`, `quantity`, `date_mouvement` |
| Inventaires | `/api/stock/inventaires` | `warehouse_id`, `reference`, `date_inventaire`, `statut` |

### Boutique

| Ressource | Endpoint | Champs principaux |
|-----------|----------|-------------------|
| Clients | `/api/shop/clients` | `pos_id`, `nom`, `prenom`, `telephone`, `email`, `adresse`, `ville`, `pays`, `type_client`, `credit_limit`, `balance`, `carte_identite`, `type_carte`, `is_active` |
| Paniers/Ventes | `/api/shop/paniers` | `pos_id`, `client_id`, `montant_total`, `montant_paye`, `remise`, `statut`, `date_vente` |
| Depenses | `/api/shop/depenses` | `pos_id`, `user_id`, `libelle`, `montant`, `date_depense` |

Filtres paniers : `?pos_id=&statut=`

### Restaurant

| Ressource | Endpoint |
|-----------|----------|
| Salles | `/api/restau/salles` |
| Tables | `/api/restau/tables` |
| Paniers/Commandes | `/api/restau/paniers` |
| Depenses | `/api/restau/depenses` |

### Hotel

| Ressource | Endpoint |
|-----------|----------|
| Categories chambres | `/api/hotel/categories` |
| Chambres | `/api/hotel/rooms` |
| Reservations | `/api/hotel/reservations` |

Filtres rooms : `?pos_id=&statut=`  
Filtres reservations : `?pos_id=&statut=`

### Salle de Fete

| Ressource | Endpoint |
|-----------|----------|
| Clients | `/api/event/clients` |
| Services | `/api/event/services` |
| Reservations | `/api/event/reservations` |

---

## 8. Codes d'erreur

| Code HTTP | Signification | Action recommandee |
|-----------|--------------|-------------------|
| `200` | Succes | -- |
| `201` | Cree | -- |
| `207` | Multi-status (sync partielle) | Traiter le tableau `errors` |
| `401` | Token absent ou invalide | Re-authentifier |
| `403` | Acces refuse | Verifier les droits du role |
| `404` | Ressource introuvable | Verifier l'UUID |
| `422` | Erreur de validation | Lire le champ `errors` |
| `500` | Erreur serveur | Contacter l'admin |

**Format erreur 422 :**
```json
{
  "message": "The nom field is required.",
  "errors": {
    "nom": ["The nom field is required."]
  }
}
```

---

## 9. Deploiement et configuration

### Installation du serveur

```bash
cd api
composer install

# Configurer .env
cp .env.example .env
php artisan key:generate

# Parametres DB dans .env :
# DB_CONNECTION=mysql
# DB_HOST=127.0.0.1
# DB_PORT=3306
# DB_DATABASE=ayanna_erp
# DB_USERNAME=root
# DB_PASSWORD=

# Creer la base de donnees
mysql -u root -e "CREATE DATABASE IF NOT EXISTS ayanna_erp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Lancer les migrations
php artisan migrate

# Demarrer (dev)
php artisan serve --port=8000

# Production : Nginx/Apache + PHP-FPM
```

### Premiere utilisation

```
1. POST /api/auth/register  ->  creer le premier compte admin
2. Recuperer le token dans la reponse
3. Utiliser Authorization: Bearer <token> pour tous les appels suivants
4. Premier sync pull (sans last_sync) pour charger toutes les donnees
```

### Variables d'environnement importantes

```ini
APP_URL=http://votre-domaine.com
SANCTUM_STATEFUL_DOMAINS=votre-domaine.com
SESSION_LIFETIME=120
```

### Securite

- HTTPS obligatoire en production
- Le token ne contient pas les donnees utilisateur — utiliser `GET /api/auth/me` pour les recuperer
- Les tokens sont revoques proprement via `POST /api/auth/logout`
- Les suppressions sont toujours des **soft-deletes** — les donnees sont recuperables
