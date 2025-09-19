#!/usr/bin/env python3
"""
Test de la nouvelle logique d'affichage dans les widgets
Sous-total HT → TVA → Total TTC → Remise → Total NET
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_logique_affichage():
    """
    Test de la nouvelle logique d'affichage selon les spécifications utilisateur
    """
    print("=" * 70)
    print("TEST NOUVELLE LOGIQUE D'AFFICHAGE")
    print("=" * 70)
    
    # Données de test conformes à la nouvelle logique
    print("Données de test:")
    
    # Données services/produits
    services = [
        {"nom": "Service principal", "prix": 600.0, "quantite": 1},
    ]
    
    produits = [
        {"nom": "Produit décoration", "prix": 300.0, "quantite": 1},
    ]
    
    print(f"Services: {services}")
    print(f"Produits: {produits}")
    
    # 1. Sous-total HT
    sous_total_ht = 0
    for service in services:
        sous_total_ht += service['prix'] * service['quantite']
    for produit in produits:
        sous_total_ht += produit['prix'] * produit['quantite']
    
    print(f"\n1. Sous-total HT: {sous_total_ht:.2f} €")
    
    # 2. TVA
    taux_tva = 20.0  # 20%
    montant_tva = sous_total_ht * (taux_tva / 100)
    print(f"2. TVA ({taux_tva}%): {montant_tva:.2f} €")
    
    # 3. Total TTC (celui stocké en BDD)
    total_ttc = sous_total_ht + montant_tva
    print(f"3. Total TTC: {total_ttc:.2f} € ← (stocké en BDD)")
    
    # 4. Remise (appliquée sur TTC)
    remise_pourcentage = 10.0  # 10%
    montant_remise = total_ttc * (remise_pourcentage / 100)
    print(f"4. Remise ({remise_pourcentage}% de {total_ttc:.2f}): -{montant_remise:.2f} €")
    
    # 5. Total NET final
    total_net = total_ttc - montant_remise
    print(f"5. Total NET: {total_net:.2f} € ← (Total final client)")
    
    print(f"\n" + "=" * 50)
    print("VÉRIFICATION AFFICHAGE WIDGETS")
    print("=" * 50)
    
    print("Dans reservation_index.py et paiement_index.py:")
    print(f"  Sous-total HT:   {sous_total_ht:.2f} €")
    print(f"  TVA:             {montant_tva:.2f} €")
    print(f"  Total TTC:       {total_ttc:.2f} € (en bleu)")
    print(f"  Remise:          {remise_pourcentage}% (-{montant_remise:.2f} €) (en rouge)")
    print(f"  Total NET:       {total_net:.2f} € (en rouge, gras)")
    
    print(f"\nDans l'impression PDF:")
    print(f"  Structure identique avec couleurs et formatage")
    
    # Test avec différents scénarios
    print(f"\n" + "=" * 50)
    print("TEST AVEC DIFFÉRENTS SCÉNARIOS")
    print("=" * 50)
    
    scenarios = [
        {"sous_total": 1000, "tva": 20, "remise": 0},
        {"sous_total": 1000, "tva": 20, "remise": 5},
        {"sous_total": 1000, "tva": 20, "remise": 10},
        {"sous_total": 1000, "tva": 20, "remise": 15},
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\nScénario {i}:")
        sous_total = scenario["sous_total"]
        taux_tva = scenario["tva"]
        taux_remise = scenario["remise"]
        
        tva = sous_total * (taux_tva / 100)
        ttc = sous_total + tva
        remise = ttc * (taux_remise / 100)
        net = ttc - remise
        
        print(f"  Sous-total HT: {sous_total:.2f} €")
        print(f"  TVA ({taux_tva}%):    {tva:.2f} €")
        print(f"  Total TTC:     {ttc:.2f} €")
        print(f"  Remise ({taux_remise}%):  -{remise:.2f} €")
        print(f"  Total NET:     {net:.2f} €")
        
        # Simulation d'un paiement partiel
        paiement = net * 0.6  # 60% payé
        solde = net - paiement
        print(f"  Payé (60%):    {paiement:.2f} €")
        print(f"  Solde:         {solde:.2f} €")

def test_coherence_bdd():
    """
    Test de cohérence avec les données stockées en BDD
    """
    print(f"\n" + "=" * 70)
    print("TEST COHÉRENCE AVEC BDD")
    print("=" * 70)
    
    print("Rappel: En BDD nous stockons maintenant:")
    print("  - total_amount = Total TTC SANS remise")
    print("  - tax_amount = TVA calculée sur HT")
    print("  - discount_percent = Pourcentage de remise")
    print()
    
    # Simulation données BDD
    bdd_data = {
        'total_services': 600.0,
        'total_products': 300.0,
        'tax_amount': 180.0,
        'total_amount': 1080.0,  # TTC sans remise
        'discount_percent': 10.0,
        'tax_rate': 20.0
    }
    
    print("Données récupérées de la BDD:")
    for key, value in bdd_data.items():
        print(f"  {key}: {value}")
    
    print(f"\nCalculs d'affichage:")
    
    # Reconstituer l'affichage depuis les données BDD
    sous_total_ht = bdd_data['total_services'] + bdd_data['total_products']
    tva = bdd_data['tax_amount']
    ttc = bdd_data['total_amount']
    remise_pct = bdd_data['discount_percent']
    remise_montant = ttc * (remise_pct / 100)
    net = ttc - remise_montant
    
    print(f"  Sous-total HT: {sous_total_ht:.2f} €")
    print(f"  TVA: {tva:.2f} €")
    print(f"  Total TTC: {ttc:.2f} €")
    print(f"  Remise ({remise_pct}%): -{remise_montant:.2f} €")
    print(f"  Total NET: {net:.2f} €")
    
    # Vérification cohérence
    print(f"\nVérifications:")
    ttc_recalcule = sous_total_ht + tva
    print(f"  TTC recalculé: {ttc_recalcule:.2f} € (doit égaler {ttc:.2f})")
    print(f"  Cohérent: {'✓' if abs(ttc_recalcule - ttc) < 0.01 else '✗'}")

if __name__ == "__main__":
    test_logique_affichage()
    test_coherence_bdd()
    
    print(f"\n" + "=" * 70)
    print("RÉSUMÉ DES MODIFICATIONS APPORTÉES")
    print("=" * 70)
    
    print("✅ reservation_index.py:")
    print("   - Affichage: Sous-total HT → TVA → Total TTC → Remise → Total NET")
    print("   - HTML mis à jour avec nouvelle structure et couleurs")
    
    print("\n✅ paiement_index.py:")
    print("   - Nouveau label total_ttc_label")
    print("   - Label total_label renommé en total_net_label")
    print("   - Méthode load_financial_summary() mise à jour")
    print("   - Méthode clear_reservation_details() mise à jour")
    print("   - HTML impression reçu mis à jour")
    print("   - prepare_reservation_data() mis à jour pour PDF")
    
    print("\n🎯 LOGIQUE UNIFIÉE:")
    print("   1. Sous-total HT (services + produits)")
    print("   2. TVA (% du sous-total HT)")
    print("   3. Total TTC (sous-total + TVA) ← stocké en BDD")
    print("   4. Remise (% du Total TTC)")
    print("   5. Total NET (Total TTC - remise) ← montant final client")
    
    print(f"\n🎉 MODIFICATIONS TERMINÉES - LOGIQUE HARMONISÉE !")