# Architecture Produits Centralisés - Guide Complet

## Vue d'ensemble

Le système a été refactorisé pour passer d'une approche **produits par POS** (`shop_products`) vers une approche **produits centralisés par entreprise** (`core_products`). Cette nouvelle architecture est beaucoup plus logique et évite la duplication.

## Changements d'architecture

### Ancien système
- `shop_products` : Produits spécifiques à chaque POS
- `pos_id` : Chaque POS avait ses propres produits
- **Problème** : Duplication des produits entre POS de la même entreprise

### Nouveau système  
- `core_products` : Produits centralisés par entreprise
- `entreprise_id` : Tous les produits appartiennent à l'entreprise
- `pos_product_access` : Table de liaison pour définir quels produits sont disponibles sur quels POS

## Structure des nouvelles tables

### 1. core_products
```sql
CREATE TABLE core_products (
    id INTEGER PRIMARY KEY,
    entreprise_id INTEGER NOT NULL,        -- Changé de pos_id vers entreprise_id
    category_id INTEGER,
    code VARCHAR(50) UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    image TEXT,
    barcode VARCHAR(100),
    cost NUMERIC(15,2) DEFAULT 0.0,
    cost_price NUMERIC(15,2) DEFAULT 0.0,
    price_unit NUMERIC(15,2) DEFAULT 0.0,
    sale_price NUMERIC(15,2) DEFAULT 0.0,
    unit VARCHAR(50) DEFAULT 'pièce',
    account_id INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME
);
```

### 2. pos_product_access  
```sql
CREATE TABLE pos_product_access (
    id INTEGER PRIMARY KEY,
    pos_id INTEGER NOT NULL,               -- Quel POS
    product_id INTEGER NOT NULL,           -- Quel produit
    custom_price NUMERIC(15,2),            -- Prix personnalisé pour ce POS (optionnel)
    custom_cost NUMERIC(15,2),             -- Coût personnalisé pour ce POS (optionnel)  
    is_available BOOLEAN DEFAULT TRUE,     -- Produit disponible sur ce POS
    display_order INTEGER DEFAULT 0,       -- Ordre d'affichage
    created_at DATETIME
);
```

### 3. core_product_categories
```sql
CREATE TABLE core_product_categories (
    id INTEGER PRIMARY KEY,
    entreprise_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_id INTEGER,                     -- Catégories hiérarchiques
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME
);
```

## Avantages de la nouvelle architecture

### 1. **Centralisation**
- Un seul produit "Coca Cola" pour toute l'entreprise
- Évite la duplication entre POS Boutique, POS Restaurant, etc.

### 2. **Flexibilité par POS**
- Chaque POS peut avoir ses propres prix (`custom_price`)
- Contrôle fin de la disponibilité par POS
- Ordre d'affichage personnalisé par POS

### 3. **Cohérence des stocks**
- Le stock est géré au niveau entreprise dans `stock_produits_entrepot`
- Référence directe `product_id` vers `core_products.id`

### 4. **Évolutivité**
- Facilite l'ajout de nouveaux POS
- Gestion centralisée des catalogues produits
- Synchronisation automatique entre modules

## Utilisation pratique

### Récupérer les produits d'un POS

```python
from ayanna_erp.modules.boutique.helpers import BoutiqueStockHelper

# Tous les produits disponibles sur POS 2 (Boutique)
result = BoutiqueStockHelper.get_product_stock_for_pos(pos_id=2)

# Produits avec stock > 0 seulement
available_products = BoutiqueStockHelper.get_available_products_for_pos(
    pos_id=2, 
    include_zero_stock=False
)
```

### Récupérer tous les produits d'une entreprise

```python
from ayanna_erp.modules.core.models import CoreProduct
from ayanna_erp.database.database_manager import DatabaseManager

db_manager = DatabaseManager()
with db_manager.get_session() as session:
    # Tous les produits de l'entreprise 1
    products = session.query(CoreProduct).filter_by(
        entreprise_id=1,
        is_active=True
    ).all()
```

### Ajouter un produit à un POS

```python
from ayanna_erp.modules.core.models import POSProductAccess
from ayanna_erp.database.database_manager import DatabaseManager

db_manager = DatabaseManager()
with db_manager.get_session() as session:
    # Rendre le produit 5 disponible sur POS 3 avec prix personnalisé
    pos_access = POSProductAccess(
        pos_id=3,
        product_id=5,
        custom_price=19.99,  # Prix spécial pour ce POS
        is_available=True
    )
    session.add(pos_access)
    session.commit()
```

## Migration des données

La migration automatique a été effectuée :

1. **Produits migrés** : `shop_products` → `core_products`
   - `pos_id` → `entreprise_id` (via la table POS)
   - Tous les autres champs conservés

2. **Liaisons créées** : `pos_product_access`
   - Chaque produit original reste disponible sur son POS d'origine
   - Possibilité d'étendre à d'autres POS

3. **Stocks conservés** : `stock_produits_entrepot`
   - Les références `product_id` pointent maintenant vers `core_products.id`

## Helpers mis à jour

### BoutiqueStockHelper
- **Nouveau** : Utilise `CoreProduct` + `POSProductAccess`
- **Requête optimisée** : JOIN entre core_products, pos_product_access et stock_produits_entrepot
- **Prix intelligent** : Utilise `custom_price` si défini, sinon `price_unit`

### POSWarehouseHelper
- **Inchangé** : Continue de gérer la liaison POS ↔ Entrepôts
- **Compatible** : Fonctionne avec la nouvelle architecture

## Exemple d'utilisation complète

### Dans une interface Boutique

```python
class BoutiqueProductCatalog:
    def __init__(self, pos_id):
        self.pos_id = pos_id
    
    def load_available_products(self):
        """Charge les produits disponibles avec leurs stocks"""
        products = BoutiqueStockHelper.get_product_stock_for_pos(self.pos_id)
        
        if products.get('error'):
            self.show_error(products['error'])
            return
        
        for product in products.get('products', []):
            self.add_product_to_catalog(
                name=product['name'],
                code=product['code'],
                price=product['price_unit'],      # Prix effectif (custom ou standard)
                stock=product['stock_quantity'],   # Stock depuis l'entrepôt associé
                status=product['stock_status'],    # 'ok', 'low', 'out'
                unit=product['unit']
            )
    
    def check_stock_alerts(self):
        """Vérifie les alertes de stock"""
        alerts = BoutiqueStockHelper.get_low_stock_alerts_for_pos(self.pos_id)
        
        if alerts['alerts']['total_alerts'] > 0:
            self.show_stock_warning(
                f"{alerts['alerts']['out_of_stock_count']} produits en rupture, "
                f"{alerts['alerts']['low_stock_count']} en stock faible"
            )
```

## Points clés à retenir

1. **Plus de `shop_products`** : Utiliser uniquement `core_products`
2. **Liaison POS-Produit** : Toujours passer par `pos_product_access`
3. **Stock centralisé** : Géré dans `stock_produits_entrepot` avec `product_id` → `core_products.id`
4. **Prix flexibles** : `custom_price` par POS ou `price_unit` par défaut
5. **Entreprise centralisée** : Tous les produits appartiennent à `entreprise_id`

Cette architecture est maintenant prête pour supporter l'expansion de votre ERP avec de nouveaux modules et POS, tout en maintenant la cohérence des données.