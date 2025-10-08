# Guide d'utilisation : Gestion des stocks dans le module Boutique

## Vue d'ensemble

Le système de stock est maintenant centralisé et unifié. Chaque point de vente (POS) a ses propres entrepôts associés, et l'affichage des quantités se fait via la table `stock_produits_entrepot` plutôt que via la colonne `stock_quantity` des tables de produits.

## Architecture des entrepôts par POS

### Identification automatique des entrepôts

Chaque POS a deux types d'entrepôts associés :

1. **Entrepôt Principal** (Type: "Principal")
   - Code: `MAIN_{pos_id}`
   - Utilisé pour le stock principal du POS
   - Champ `is_default=True`

2. **Entrepôt Point de Vente** (Type: "Point de Vente")
   - Code: `POS_{pos_id}`
   - Utilisé pour le stock de vente directe

### Exemple pour POS Boutique (ID=2)
- Entrepôt Principal: `Entrepôt Principal - POS Boutique Centrale` (MAIN_2)
- Entrepôt POS: `Entrepôt Point de Vente - POS Boutique Centrale` (POS_2)

## Helpers disponibles

### 1. POSWarehouseHelper

```python
from ayanna_erp.modules.stock.helpers import POSWarehouseHelper

# Récupérer l'entrepôt principal d'un POS
main_warehouse = POSWarehouseHelper.get_main_warehouse_for_pos(pos_id=2)

# Récupérer l'entrepôt POS
pos_warehouse = POSWarehouseHelper.get_pos_warehouse(pos_id=2)

# Informations complètes
info = POSWarehouseHelper.get_warehouse_info_for_pos(pos_id=2)
```

### 2. BoutiqueStockHelper

```python
from ayanna_erp.modules.boutique.helpers import BoutiqueStockHelper

# Récupérer tous les stocks pour un POS Boutique
result = BoutiqueStockHelper.get_product_stock_for_pos(pos_id=2)

# Récupérer le stock d'un produit spécifique
product_stock = BoutiqueStockHelper.get_product_stock_for_pos(pos_id=2, product_id=1)

# Récupérer seulement les produits avec stock > 0
available_products = BoutiqueStockHelper.get_products_with_stock_for_pos(pos_id=2, include_zero_stock=False)

# Alertes de stock faible/rupture
alerts = BoutiqueStockHelper.get_low_stock_alerts_for_pos(pos_id=2)
```

## Structure des données retournées

### Format des stocks de produits

```python
{
    'error': None,
    'warehouse_info': {
        'id': 3,
        'name': 'Entrepôt Principal - POS Boutique Centrale',
        'code': 'MAIN_2'
    },
    'products': [
        {
            'id': 1,
            'name': 'Nom du produit',
            'price_unit': 15.50,
            'cost': 10.00,
            'stock_quantity': 25.0,          # Depuis stock_produits_entrepot.quantity
            'stock_min': 5.0,                # Depuis stock_produits_entrepot.min_stock_level
            'reserved_quantity': 2.0,         # Quantité réservée
            'stock_status': 'ok'             # 'ok', 'low', 'out'
        }
    ],
    'total_products': 10,
    'low_stock_count': 2,
    'out_of_stock_count': 1
}
```

### Statuts de stock

- `'ok'` : Stock normal (quantité > minimum)
- `'low'` : Stock faible (0 < quantité ≤ minimum)
- `'out'` : Rupture de stock (quantité = 0)

## Intégration dans l'interface Boutique

### Affichage des produits avec stock

```python
# Dans votre widget Boutique
def load_products_with_stock(self):
    products = BoutiqueStockHelper.get_products_with_stock_for_pos(
        pos_id=self.pos_id,
        include_zero_stock=False  # Masquer les produits sans stock
    )
    
    for product in products:
        # Afficher dans votre interface
        self.add_product_to_catalog(
            name=product['name'],
            price=product['price_unit'],
            stock=product['stock_quantity'],
            status=product['stock_status']
        )
```

### Alertes de stock

```python
def check_stock_alerts(self):
    alerts = BoutiqueStockHelper.get_low_stock_alerts_for_pos(self.pos_id)
    
    if alerts['alerts']['total_alerts'] > 0:
        self.show_stock_warning(
            low_stock=alerts['alerts']['low_stock_count'],
            out_of_stock=alerts['alerts']['out_of_stock_count']
        )
```

## Points clés

1. **Plus de colonne stock_quantity dans shop_products** : Utiliser uniquement `stock_produits_entrepot.quantity`

2. **Identification automatique des entrepôts** : Le système trouve automatiquement l'entrepôt associé au POS

3. **Gestion centralisée** : Tous les mouvements de stock passent par le système centralisé

4. **Cohérence des données** : Les quantités affichées sont toujours synchronisées avec le stock réel

## Migration des données existantes

Si vous avez des données existantes dans `shop_products.stock_quantity`, vous devrez les migrer vers `stock_produits_entrepot` :

```python
# Script de migration (à exécuter une seule fois)
def migrate_boutique_stock_to_centralized():
    # Récupérer tous les produits boutique avec stock > 0
    # Créer les entrées correspondantes dans stock_produits_entrepot
    # Remettre à zéro shop_products.stock_quantity
    pass
```

Ce système assure une gestion cohérente et centralisée des stocks pour tous les modules de l'ERP.