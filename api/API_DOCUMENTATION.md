# Ayanna ERP — REST API Documentation

**Base URL:** `http://your-server/api`  
**Auth:** Bearer token (Laravel Sanctum)  
**Content-Type:** `application/json`

---

## Authentication

### POST `/api/auth/register`
Register a new user.

**Body:**
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

**Response 201:**
```json
{ "user": { ... }, "token": "1|abc..." }
```

---

### POST `/api/auth/login`
**Body:** `{ "email": "...", "password": "..." }`  
**Response 200:** `{ "user": {...}, "token": "..." }`

---

### POST `/api/auth/logout` 🔒
Revokes the current token.

---

### GET `/api/auth/me` 🔒
Returns the authenticated user with enterprise.

---

## Core

### Entreprises
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/entreprises` | List all (paginated) |
| POST | `/api/entreprises` | Create |
| GET | `/api/entreprises/{id}` | Show |
| PUT | `/api/entreprises/{id}` | Update |
| DELETE | `/api/entreprises/{id}` | Soft-delete |

**Fields:** `id (uuid)`, `nom`, `adresse`, `telephone`, `email`, `logo`, `devise`, `pays`, `secteur`, `is_active`

---

### Users
Same CRUD pattern: `/api/users`  
**Fields:** `id`, `name`, `email`, `password`, `enterprise_id`, `pos_id`, `role`

---

### POS Points
`/api/pos-points`  
**Fields:** `id`, `enterprise_id`, `nom`, `type` (boutique|restaurant|hotel|salle_fete), `adresse`, `telephone`, `actif`

---

### Product Categories
`/api/product-categories`  
**Fields:** `id`, `enterprise_id`, `nom`, `description`, `parent_id`, `actif`

---

### Products
`/api/products`  
**Fields:** `id`, `enterprise_id`, `category_id`, `code`, `name`, `description`, `barcode`, `cost`, `price_unit`, `unit`, `compte_produit_id`, `compte_charge_id`, `is_active`

---

## Comptabilité

### Classes Comptables
`/api/compta/classes`  
**Fields:** `id`, `code`, `nom`, `libelle`, `type`, `document`, `enterprise_id`, `actif`

---

### Comptes Comptables
`/api/compta/comptes`  
**Fields:** `id`, `numero`, `nom`, `libelle`, `actif`, `is_default`, `classe_comptable_id`

---

### Journaux
`/api/compta/journaux`  
**Query filters:** `enterprise_id`, `date_from`, `date_to`  
**Fields:** `id`, `date_operation`, `libelle`, `montant`, `type_operation`, `reference`, `enterprise_id`, `user_id`, `valide`, `valide_by`, `date_validation`

---

### Config Comptable
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/compta/config/{id}` | Show by id |
| GET | `/api/compta/config/pos/{pos_id}` | Show for a POS |
| POST | `/api/compta/config` | Create |
| PUT | `/api/compta/config/{id}` | Update |

---

## Achats

### Fournisseurs
`/api/fournisseurs` — `nom`, `telephone`, `adresse`, `email`

### Commandes d'Achat
`/api/achat/commandes`  
**Query filters:** `fournisseur_id`, `etat`  
**Fields:** `id`, `numero`, `fournisseur_id`, `entrepot_id`, `utilisateur_id`, `date_commande`, `remise_global`, `montant_total`, `etat`, `statut_paiement`

---

## Stock

### Warehouses
`/api/stock/warehouses`  
**Fields:** `id`, `entreprise_id`, `code`, `name`, `type`, `is_default`, `is_active`

### Mouvements
`/api/stock/mouvements` (no update)  
**Query filters:** `warehouse_id`, `product_id`  
**Fields:** `id`, `product_id`, `warehouse_id`, `type_mouvement`, `quantity`, `unit_cost`, `reference_document`, `date_mouvement`

### Inventaires
`/api/stock/inventaires`  
**Fields:** `id`, `warehouse_id`, `user_id`, `reference`, `date_inventaire`, `statut`

### Produits en Entrepôt
`/api/stock/produits`  
**Query filters:** `warehouse_id`, `product_id`  
**Fields:** `id`, `product_id`, `warehouse_id`, `quantity`, `reserved_quantity`, `unit_cost`, `min_stock_level`

---

## Boutique

### Clients
`/api/shop/clients` — `nom`, `telephone`, `adresse`, `email`

### Paniers (Ventes)
`/api/shop/paniers`  
**Query filters:** `pos_id`, `statut`  
**Fields:** `id`, `pos_id`, `client_id`, `user_id`, `reference`, `montant_total`, `montant_paye`, `remise`, `statut`, `date_vente`

### Dépenses
`/api/shop/depenses` — `pos_id`, `user_id`, `libelle`, `montant`, `date_depense`

---

## Restaurant

### Salles
`/api/restau/salles` — `pos_id`, `nom`, `capacite`, `actif`

### Tables
`/api/restau/tables` — `salle_id`, `numero`, `nom`, `capacite`, `statut`

### Paniers (Commandes)
`/api/restau/paniers`  
**Query filters:** `pos_id`, `statut`  
**Fields:** `id`, `pos_id`, `table_id`, `user_id`, `montant_total`, `statut`, `date_ouverture`, `nombre_couverts`

### Dépenses
`/api/restau/depenses` — same as shop

---

## Hôtel

### Catégories de Chambres
`/api/hotel/categories` — `pos_id`, `nom`, `prix_par_nuit`

### Chambres
`/api/hotel/rooms` — `pos_id`, `category_id`, `numero`, `statut`  
**Query filters:** `pos_id`, `statut`

### Réservations
`/api/hotel/reservations`  
**Query filters:** `pos_id`, `statut`  
**Fields:** `id`, `room_id`, `client_nom`, `date_arrivee`, `date_depart`, `nombre_nuits`, `montant_total`, `statut`, `statut_paiement`

---

## Salle de Fête

### Clients Événement
`/api/event/clients` — `nom`, `telephone`, `email`

### Services Événement
`/api/event/services` — `nom`, `prix`, `unite`

### Réservations Événement
`/api/event/reservations`  
**Query filters:** `pos_id`, `statut`  
**Fields:** `id`, `client_id`, `nom_evenement`, `date_evenement`, `montant_total`, `statut`

---

## Synchronisation

### POST `/api/sync/push` 🔒
Push local changes to server. Client-last-write-wins strategy.  
Conflicts are logged in `sync_audit_logs`.

**Body:**
```json
{
  "operations": [
    {
      "table": "core_products",
      "operation": "INSERT",
      "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Produit Test",
        "price_unit": 1500.00,
        "enterprise_id": "..."
      },
      "client_updated_at": "2024-01-15T10:30:00Z"
    },
    {
      "table": "shop_paniers",
      "operation": "UPDATE",
      "data": { "id": "...", "statut": "ferme" },
      "client_updated_at": "2024-01-15T10:31:00Z"
    },
    {
      "table": "compta_journaux",
      "operation": "DELETE",
      "data": { "id": "..." },
      "client_updated_at": "2024-01-15T10:32:00Z"
    }
  ]
}
```

**Response 200** (all success):
```json
{ "success": 3, "errors": [] }
```

**Response 207** (partial failure):
```json
{
  "success": 2,
  "errors": [
    { "table": "compta_journaux", "id": "...", "operation": "DELETE", "error": "..." }
  ]
}
```

**Supported tables for push:**
`core_enterprises`, `core_users`, `modules`, `core_pos_points`, `core_payment_modes`, `core_product_categories`, `core_products`, `pos_product_access`, `compta_classes`, `compta_comptes`, `compta_journaux`, `compta_ecritures`, `compta_config`, `core_fournisseurs`, `stock_warehouses`, `achat_commandes`, `achat_commande_lignes`, `achat_depenses`, `stock_produits_entrepot`, `stock_mouvements`, `stock_config`, `stock_inventaire`, `stock_inventaire_items`, `shop_clients`, `shop_services`, `shop_paniers`, `shop_panier_products`, `shop_panier_services`, `shop_payments`, `shop_expenses`, `restau_salles`, `restau_tables`, `restau_paniers`, `restau_produit_panier`, `restau_payments`, `restau_expenses`, `restau_printed_invoices`, `hotel_categories`, `hotel_rooms`, `hotel_reservations`, `hotel_payments`, `event_clients`, `event_services`, `event_products`, `event_reservations`, `event_reservation_services`, `event_reservation_products`, `event_payments`, `event_stock_movements`, `licences`

---

### GET `/api/sync/pull?last_sync=ISO8601` 🔒
Pull all records modified after `last_sync`.  
Omit `last_sync` for a full sync.

**Response 200:**
```json
{
  "server_time": "2024-01-15T12:00:00+00:00",
  "data": {
    "core_products": [ { "id": "...", "name": "...", "deleted_at": null, ... } ],
    "shop_paniers":  [ ... ],
    "compta_journaux": [ ... ]
  }
}
```
Only tables with changed records are included.  
Soft-deleted records are included (check `deleted_at != null`).

---

## Error Responses

| Code | Meaning |
|------|---------|
| 401 | Unauthenticated — missing or invalid token |
| 403 | Forbidden |
| 404 | Not found |
| 422 | Validation error — body contains `errors` object |
| 207 | Multi-Status — partial success on sync push |
| 500 | Server error |

**Validation error example:**
```json
{
  "message": "The name field is required.",
  "errors": {
    "name": ["The name field is required."]
  }
}
```

---

## Setup

```bash
# 1. Install dependencies
cd api
composer install

# 2. Configure .env (already set for MySQL)
#    DB_DATABASE=ayanna_erp
#    DB_USERNAME=root
#    DB_PASSWORD=

# 3. Create database
mysql -u root -e "CREATE DATABASE IF NOT EXISTS ayanna_erp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 4. Run migrations
php artisan migrate

# 5. Serve
php artisan serve --port=8000
```

**First request:** `POST /api/auth/register` → get token → include as `Authorization: Bearer <token>` on all subsequent requests.
