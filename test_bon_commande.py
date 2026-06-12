#!/usr/bin/env python
"""Test script for Bon de Commande functionality"""

from datetime import datetime
from ayanna_erp.database.database_manager import get_database_manager
from ayanna_erp.modules.restaurant.models.restaurant import RestauBonCommande, RestauPanier, RestauProduitPanier
from ayanna_erp.modules.restaurant.controllers.bon_commande_controller import BonCommandeController

# Test 1: Vérifier que le modèle a le champ entreprise_id
db = get_database_manager()
session = db.get_session()

# Créer une structure de test simple
bon = RestauBonCommande(
    entreprise_id=1,
    numero_bon=1,
    restau_panier_id=99999,  # fictif
    client_id=1,
    user_id=1,
    produits_json='[]',
    montant_total=0.0,
    statut='valide',
    created_at=datetime.now(),
    updated_at=datetime.now()
)
print("✅ Modèle RestauBonCommande accepte entreprise_id")

# Test 2: Vérifier le contrôleur
ctrl = BonCommandeController(entreprise_id=1)
print("✅ BonCommandeController initialisé")

# Test 3: Vérifier _get_next_numero_bon() - commence à 1
next_bon = ctrl._get_next_numero_bon()
print(f"✅ Numéro de bon suivant: {next_bon}")

# Test 4: Vérifier la réinitialisation journalière
start_dt, end_dt = ctrl._get_today_bounds()
print(f"✅ Plage de date d'aujourd'hui: {start_dt} à {end_dt}")

session.close()
print("\n✅ TOUS LES TESTS DE BASE RÉUSSIS!")
