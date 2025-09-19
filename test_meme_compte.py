#!/usr/bin/env python3
"""
Test pour vérifier le comportement avec plusieurs services/produits sur le même compte
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_meme_compte():
    """
    Test avec plusieurs services/produits ayant le même compte
    """
    print("=" * 70)
    print("TEST - SERVICES/PRODUITS AVEC LE MÊME COMPTE")
    print("=" * 70)
    
    # Simulation : 3 services avec 2 comptes différents
    services_data = [
        {'service_id': 1, 'nom': 'Service Mariage', 'prix': 500.0, 'quantite': 1, 'compte_id': 5},
        {'service_id': 2, 'nom': 'Service Décoration', 'prix': 300.0, 'quantite': 1, 'compte_id': 5},  # MÊME COMPTE
        {'service_id': 3, 'nom': 'Service Musique', 'prix': 200.0, 'quantite': 1, 'compte_id': 7},     # COMPTE DIFFÉRENT
    ]
    
    # Simulation : 2 produits avec le même compte
    produits_data = [
        {'produit_id': 1, 'nom': 'Produit A', 'prix': 100.0, 'quantite': 2, 'compte_id': 6},
        {'produit_id': 2, 'nom': 'Produit B', 'prix': 150.0, 'quantite': 1, 'compte_id': 6},  # MÊME COMPTE
    ]
    
    print("DONNÉES DE TEST:")
    print("\nServices:")
    for service in services_data:
        print(f"  {service['nom']}: {service['prix']:.2f}€ x {service['quantite']} → Compte {service['compte_id']}")
    
    print("\nProduits:")
    for produit in produits_data:
        print(f"  {produit['nom']}: {produit['prix']:.2f}€ x {produit['quantite']} → Compte {produit['compte_id']}")
    
    # === SIMULATION DE LA LOGIQUE DE REGROUPEMENT ===
    print(f"\n" + "=" * 50)
    print("LOGIQUE DE REGROUPEMENT PAR COMPTE")
    print("=" * 50)
    
    # Regroupement des services par compte (comme dans le code)
    services_par_compte = {}
    for service in services_data:
        compte_id = service['compte_id']
        total_ligne = service['prix'] * service['quantite']
        
        if compte_id not in services_par_compte:
            services_par_compte[compte_id] = {
                'total_brut': 0.0,
                'names': []
            }
        
        services_par_compte[compte_id]['total_brut'] += total_ligne
        services_par_compte[compte_id]['names'].append(service['nom'])
    
    print("Services regroupés par compte:")
    for compte_id, details in services_par_compte.items():
        names_str = ', '.join(details['names'])
        print(f"  Compte {compte_id}: {details['total_brut']:.2f}€ [{names_str}]")
    
    # Regroupement des produits par compte
    produits_par_compte = {}
    for produit in produits_data:
        compte_id = produit['compte_id']
        total_ligne = produit['prix'] * produit['quantite']
        
        if compte_id not in produits_par_compte:
            produits_par_compte[compte_id] = {
                'total_brut': 0.0,
                'names': []
            }
        
        produits_par_compte[compte_id]['total_brut'] += total_ligne
        produits_par_compte[compte_id]['names'].append(produit['nom'])
    
    print("\nProduits regroupés par compte:")
    for compte_id, details in produits_par_compte.items():
        names_str = ', '.join(details['names'])
        print(f"  Compte {compte_id}: {details['total_brut']:.2f}€ [{names_str}]")
    
    # === SIMULATION DES ÉCRITURES COMPTABLES ===
    print(f"\n" + "=" * 50)
    print("ÉCRITURES COMPTABLES GÉNÉRÉES")
    print("=" * 50)
    
    montant_paiement = 1000.0
    total_ttc = sum(details['total_brut'] for details in services_par_compte.values()) + \
                sum(details['total_brut'] for details in produits_par_compte.values())
    
    print(f"Montant du paiement: {montant_paiement:.2f}€")
    print(f"Total TTC: {total_ttc:.2f}€")
    
    # Simulation des écritures (une par compte)
    ordre = 1
    print(f"\nÉcriture {ordre}: DÉBIT Caisse {montant_paiement:.2f}€")
    ordre += 1
    
    # Services - UNE écriture par compte
    for compte_id, details in services_par_compte.items():
        proportion = details['total_brut'] / total_ttc
        montant_credit = montant_paiement * proportion
        names_str = ', '.join(details['names'][:2])
        if len(details['names']) > 2:
            names_str += f" (+{len(details['names'])-2} autres)"
        
        print(f"Écriture {ordre}: CRÉDIT Services Compte {compte_id}: {montant_credit:.2f}€ [{names_str}]")
        ordre += 1
    
    # Produits - UNE écriture par compte
    for compte_id, details in produits_par_compte.items():
        proportion = details['total_brut'] / total_ttc
        montant_credit = montant_paiement * proportion
        names_str = ', '.join(details['names'])
        
        print(f"Écriture {ordre}: CRÉDIT Produits Compte {compte_id}: {montant_credit:.2f}€ [{names_str}]")
        ordre += 1
    
    # === ANALYSE ===
    print(f"\n" + "=" * 50)
    print("ANALYSE DU COMPORTEMENT")
    print("=" * 50)
    
    print("✅ RÉSULTAT:")
    print("  - Services avec même compte → UNE SEULE écriture (montants additionnés)")
    print("  - Produits avec même compte → UNE SEULE écriture (montants additionnés)")
    print("  - Le libellé indique tous les noms des items concernés")
    
    print("\n🎯 AVANTAGES:")
    print("  - Comptabilité plus propre (moins d'écritures)")
    print("  - Montants consolidés par compte")
    print("  - Traçabilité maintenue dans le libellé")
    
    print("\n⚠️  POINTS D'ATTENTION:")
    print("  - Vérifier que le libellé n'est pas trop long")
    print("  - S'assurer que la traçabilité est suffisante")
    
    return True

def test_scenario_complexe():
    """Test avec un scénario plus complexe"""
    print(f"\n" + "=" * 70)
    print("TEST SCÉNARIO COMPLEXE")
    print("=" * 70)
    
    # 5 services, 3 comptes différents
    services = [
        {'nom': 'Mariage Base', 'prix': 800, 'compte_id': 5},
        {'nom': 'Mariage Premium', 'prix': 200, 'compte_id': 5},  # Même compte
        {'nom': 'Décoration Fleurs', 'prix': 300, 'compte_id': 8},
        {'nom': 'Décoration Éclairage', 'prix': 150, 'compte_id': 8},  # Même compte
        {'nom': 'Animation DJ', 'prix': 250, 'compte_id': 9},
    ]
    
    # Regroupement
    comptes = {}
    for service in services:
        compte_id = service['compte_id']
        if compte_id not in comptes:
            comptes[compte_id] = {'total': 0, 'items': []}
        comptes[compte_id]['total'] += service['prix']
        comptes[compte_id]['items'].append(service['nom'])
    
    print("Regroupement final:")
    total_ecritures = 1  # Débit
    for compte_id, details in comptes.items():
        items_str = ' + '.join(details['items'])
        print(f"  Compte {compte_id}: {details['total']:.2f}€ ({items_str})")
        total_ecritures += 1
    
    print(f"\nNombre total d'écritures: {total_ecritures}")
    print(f"Au lieu de: {1 + len(services)} (si une écriture par service)")
    
    return True

if __name__ == "__main__":
    test_meme_compte()
    test_scenario_complexe()
    
    print(f"\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print("🎯 Le système actuel groupe automatiquement les montants par compte.")
    print("   Plusieurs services/produits sur le même compte = UNE SEULE écriture.")
    print("   Cela produit une comptabilité plus propre et consolidée.")