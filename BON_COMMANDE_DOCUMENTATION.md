# 📋 Documentation - Fonctionnalité Bon de Commande (Cuisine/Bar)

## Vue d'ensemble

La fonctionnalité **Bon de Commande** permet aux serveurs et caissiers du restaurant d'imprimer des bons destinés à la cuisine ou au bar, uniquement pour les **nouvelles quantités ajoutées** depuis le dernier bon.

## ✨ Fonctionnalités Implémentées

### 1. **Génération Intelligente de Bons**
- Calcule automatiquement les quantités déjà envoyées à la cuisine
- N'imprime que les **nouvelles quantités** (différence entre actuel et envoyé)
- Empêche de réimprimer les mêmes quantités plusieurs fois
- Ne crée pas de bon vide

### 2. **Numérotation Journalière**
- Chaque bon porte un numéro qui recommence à 1 chaque jour
- Exemple: 
  - 10/06/2026: Bon 1, 2, 3
  - 11/06/2026: Bon 1, 2

### 3. **Impressions Thermiques Optimisées**
- Format compact pour impression sur papier thermique
- Affiche:
  - ✅ Nom entreprise
  - ✅ "BON DE COMMANDE" en titre
  - ✅ Numéro du bon (très gros et gras)
  - ✅ Nom du serveur (gras)
  - ✅ Numéro table
  - ✅ ID du panier
  - ✅ Date et heure d'impression
  - ✅ Liste des produits avec quantités
- N'affiche PAS:
  - ❌ Nom du client
  - ❌ Nom utilisateur connecté
  - ❌ Prix
  - ❌ Totaux/Montants

### 4. **Widget de Suivi des Bons**
- Filtrage par date (par défaut: bons du jour)
- Filtrage par statut (Valide/Annulé)
- Recherche par ID panier
- Affichage:
  - Numéro du bon
  - Date et heure
  - ID panier et table
  - Nom du client
  - Nom du serveur
  - Montant total
  - Statut et produits
  - Bouton d'annulation pour bons valides
- Totaux: nombre de bons et montant global

## 🎯 Flux d'Utilisation

### Scenario 1: Premier bon avec 2 Simba
```
1. Serveur ajoute 2 x Simba au panier de la table
2. Sélectionne un client
3. Clique sur bouton "Bon commande"
4. ✅ Bon N°1 créé avec: Simba x2
5. 🖨️ Impression automatique du bon thermique
```

### Scenario 2: Ajout de nouvelles quantités
```
1. Plus tard, serveur ajoute 2 x Simba supplémentaires (panier: 4 total)
2. Clique sur "Bon commande"
3. 🧮 Système calcule:
   - Quantité actuelle: 4
   - Quantité envoyée: 2
   - Différence: 2
4. ✅ Bon N°2 créé avec: Simba x2 (seulement le complément)
5. 🖨️ Impression
```

### Scenario 3: Aucune nouvelle quantité
```
1. Panier: Simba x4 (inchangé depuis bon précédent)
2. Serveur clique sur "Bon commande"
3. ⚠️ Message d'information: "Aucun nouveau produit à envoyer en cuisine"
4. ❌ Pas de bon créé
5. ❌ Pas d'impression
```

## 🗂️ Structure Base de Données

### Table: `restau_bon_commandes`

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | Integer | Clé primaire |
| `entreprise_id` | Integer | ID entreprise (nouvel champ ajouté) |
| `numero_bon` | Integer | Numéro journalier (1, 2, 3...) |
| `restau_panier_id` | Integer FK | Référence panier restaurant |
| `serveuse_id` | Integer | ID du serveur (nullable) |
| `client_id` | Integer | ID client (obligatoire) |
| `user_id` | Integer | ID utilisateur connecté (nullable) |
| `produits_json` | Text | JSON des produits imprimés |
| `montant_total` | Float | Montant total du bon |
| `statut` | String | 'valide' ou 'annule' |
| `created_at` | DateTime | Date création |
| `updated_at` | DateTime | Date modification |

### Format `produits_json`
```json
[
  {
    "produit_id": 1,
    "nom": "Simba",
    "quantite": 2,
    "prix_vente": 8000
  },
  {
    "produit_id": 5,
    "nom": "Fanta",
    "quantite": 1,
    "prix_vente": 5000
  }
]
```

## 🏗️ Composants Implémentés

### 1. **Modèles ORM** (`ayanna_erp/modules/restaurant/models/restaurant.py`)
- `RestauBonCommande`: Modèle principal avec tous les champs
- Relation: `RestauPanier.bon_commandes` (one-to-many)

### 2. **Contrôleur** (`ayanna_erp/modules/restaurant/controllers/bon_commande_controller.py`)
- **`create_bon_commande()`**: Crée un nouveau bon
  - Valide la présence du client
  - Calcule les quantités à envoyer
  - Stocke le bon en base
  - Retourne (success, result, items)

- **`get_pending_bon_items()`**: Retourne les items à imprimer
  - Récupère panier actuel
  - Calcule différence avec bons précédents
  - Retourne liste des nouvelles quantités

- **`cancel_bon()`**: Annule un bon
  - Marque le bon comme 'annule'
  - Permet une réimpression si nécessaire

- **`list_bons_for_date()`**: Liste les bons d'une journée
  - Filtrage par date, statut, panier
  - Enrichissement avec noms client/serveur
  - Utilisé par la widget de suivi

### 3. **Utilitaire Impression** (`ayanna_erp/modules/restaurant/utils/bon_commande_printer.py`)
- `BonCommandePrinter.print_ticket()`: Génère PDF thermique
  - Format optimisé 58mm de largeur
  - Structure compacte
  - Formatage date/heure
  - Gestion hauteur dynamique selon nombre items

### 4. **Widget UI - Catalogue** (`ayanna_erp/modules/restaurant/views/catalogue_widget.py`)
- Bouton "Bon commande" intégré
- Handler `_on_bon_commande_clicked()`:
  - Valide client sélectionné
  - Crée le bon
  - Gère les messages (succès, erreur, info)
  - Ouvre impression système automatique

### 5. **Widget UI - Bons de Commande** (`ayanna_erp/modules/restaurant/views/boncommande_widget.py`)
- Affichage complet des bons
- Filtres: date, statut, panier
- Table avec colonnes: Bon #, Date, Panier, Table, Client, Serveuse, Montant, Statut, Produits, Action
- Boutons annulation
- Totaux: nombre et montant global

### 6. **Intégration Fenêtre Principale** (`ayanna_erp/modules/restaurant/restaurant_window.py`)
- Nouvel onglet "🍳 Bons de Commande" dans la fenêtre principale
- Intégration via `setup_bon_commande_tab()`

## 🔧 API du Contrôleur

### Exemple d'utilisation

```python
from ayanna_erp.modules.restaurant.controllers.bon_commande_controller import BonCommandeController
from ayanna_erp.modules.restaurant.utils.bon_commande_printer import BonCommandePrinter

# Initialiser
ctrl = BonCommandeController(entreprise_id=1)
printer = BonCommandePrinter(enterprise_id=1)

# Créer un bon
success, result, pending_items = ctrl.create_bon_commande(
    panier_id=123,
    user_id=5,
    client_id=10,
    serveuse_id=2
)

if success:
    bon = result
    print(f"Bon {bon.numero_bon} créé")
    # Préparer impression
    ticket_data = {
        'numero_bon': bon.numero_bon,
        'serveuse': 'Marie',
        'table': '5',
        'panier_id': bon.restau_panier_id,
        'created_at': bon.created_at,
        'items': pending_items
    }
    printer.print_ticket(ticket_data, '/tmp/bon.pdf')
else:
    print(f"Erreur: {result}")

# Annuler un bon
success, msg = ctrl.cancel_bon(bon_id=123)

# Lister les bons du jour
from datetime import datetime, date
bons = ctrl.list_bons_for_date(
    target_date=date.today(),
    status_filter='valide'
)
for bon in bons:
    print(f"Bon {bon.numero_bon}: {bon.client_name}")
```

## 🐛 Gestion des Erreurs

| Erreur | Message | Action |
|--------|---------|--------|
| Client non sélectionné | "Veuillez sélectionner un client..." | Aucun bon créé |
| Aucune nouvelle quantité | "Aucun nouveau produit à envoyer en cuisine" | Aucun bon créé, info affichée |
| Bon inexistant | "BON_INEXISTANT" | Retour false |
| Bon déjà annulé | "BON_ALREADY_CANCELLED" | Retour false |

## 📊 Contraintes et Règles

✅ **Contraintes Implémentées:**
1. ✅ Jamais imprimer deux fois les mêmes quantités
2. ✅ Imprimer uniquement les quantités ajoutées depuis le dernier bon
3. ✅ Pas de bon vide
4. ✅ Pas d'impression sans client sélectionné
5. ✅ Calculs basés sur historique des bons créés
6. ✅ Support plusieurs impressions successives sur même panier
7. ✅ Numérotation journalière (1 chaque jour)

## 🧪 Tests

Exécuter:
```bash
cd c:\apps\ayannaerp\Ayanna-Erp
python test_bon_commande.py
```

Résultats attendus:
```
✅ Modèle RestauBonCommande accepte entreprise_id
✅ BonCommandeController initialisé
✅ Numéro de bon suivant: 1
✅ Plage de date d'aujourd'hui: 2026-06-12 00:00:00 à 2026-06-12 23:59:59.999999
✅ TOUS LES TESTS DE BASE RÉUSSIS!
```

## 🚀 Déploiement

1. ✅ Modèle mis à jour avec `entreprise_id`
2. ✅ Tables créées/mises à jour via `initialize_restaurant_tables()`
3. ✅ Contrôleur complètement fonctionnel
4. ✅ Widget bons de commande disponible
5. ✅ Intégration fenêtre principale réalisée
6. ✅ Impression thermique prête

**État: PRÊT POUR PRODUCTION** ✅

## 📝 Notes Importantes

- Les bons sont sauvegardés en base de données (traçabilité complète)
- Le statut peut être 'valide' ou 'annule' (pas de suppression physique)
- Les quantités imprimées sont figées dans `produits_json`
- La numérotation journalière s'auto-réinitialise à minuit
- Les améliorations futures possibles:
  - Réimpression d'un bon existant
  - Fusion de plusieurs paniers
  - Impression en batch
  - Notifications cuisine en temps réel
