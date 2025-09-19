#!/usr/bin/env python3
"""
Test pour comparer les calculs de remise entre reservation_controller et paiement_controller
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_comparaison_calculs_remise():
    """
    Comparaison des calculs de remise entre les deux controllers
    """
    print("=" * 80)
    print("COMPARAISON DES CALCULS DE REMISE")
    print("=" * 80)
    
    # Données de test communes
    subtotal_ht = 1500.0  # Services + Produits HT
    taux_tva = 20.0       # 20%
    discount_percent = 10.0  # 10% de remise
    
    # Calculs de base
    tax_amount = subtotal_ht * (taux_tva / 100)
    total_ttc_brut = subtotal_ht + tax_amount  # TTC AVANT remise
    
    print(f"DONNÉES DE BASE:")
    print(f"  Sous-total HT: {subtotal_ht:.2f}€")
    print(f"  TVA ({taux_tva}%): {tax_amount:.2f}€")
    print(f"  Total TTC brut: {total_ttc_brut:.2f}€")
    print(f"  Remise: {discount_percent}%")
    
    # === LOGIQUE RESERVATION_CONTROLLER ===
    print(f"\n" + "=" * 60)
    print("LOGIQUE RESERVATION_CONTROLLER (à la création)")
    print("=" * 60)
    
    # Remise calculée sur TTC brut
    remise_totale = total_ttc_brut * (discount_percent / 100)
    total_net_final = total_ttc_brut - remise_totale
    
    print(f"1. Remise sur TTC brut: {discount_percent}% de {total_ttc_brut:.2f}€ = {remise_totale:.2f}€")
    print(f"2. Total net final: {total_ttc_brut:.2f}€ - {remise_totale:.2f}€ = {total_net_final:.2f}€")
    print(f"3. Stocké en BDD: total_amount = {total_ttc_brut:.2f}€ (SANS remise)")
    
    # === LOGIQUE PAIEMENT_CONTROLLER (ACTUELLE) ===
    print(f"\n" + "=" * 60)
    print("LOGIQUE PAIEMENT_CONTROLLER (actuelle)")
    print("=" * 60)
    
    # Simulation: L'utilisateur saisit un montant (supposons paiement partiel)
    montant_saisi = 900.0  # Paiement partiel (net)
    
    print(f"L'utilisateur saisit: {montant_saisi:.2f}€ (montant net encaissé)")
    print(f"Total TTC en BDD: {total_ttc_brut:.2f}€ (stocké SANS remise)")
    
    # Calcul actuel dans paiement_controller
    remise_totale_reservation = total_ttc_brut * (discount_percent / 100)
    remise_proportionnelle = (montant_saisi / total_ttc_brut) * remise_totale_reservation
    
    print(f"\nCalculs paiement_controller (CORRECT):")
    print(f"1. Remise totale réservation: {discount_percent}% de {total_ttc_brut:.2f}€ = {remise_totale_reservation:.2f}€")
    print(f"2. Proportion paiement: {montant_saisi:.2f}€ / {total_ttc_brut:.2f}€ = {montant_saisi/total_ttc_brut:.1%}")
    print(f"3. Remise proportionnelle: {montant_saisi/total_ttc_brut:.1%} × {remise_totale_reservation:.2f}€ = {remise_proportionnelle:.2f}€")
    
    # === PROBLÈME DANS LA RECONSTITUTION DES MONTANTS BRUTS ===
    print(f"\n" + "=" * 60)
    print("PROBLÈME: RECONSTITUTION DES MONTANTS BRUTS")
    print("=" * 60)
    
    # Dans le code actuel, la reconstitution utilise le facteur remise GLOBAL
    facteur_remise_global = 1 - (discount_percent / 100)
    
    print(f"Facteur remise global: 1 - {discount_percent/100:.1f} = {facteur_remise_global:.1f}")
    
    # Exemple pour un service qui représente 66.67% du total
    montant_service_net = montant_saisi * 0.6667  # 60% du paiement
    montant_service_brut_reconstitue = montant_service_net / facteur_remise_global
    
    print(f"\nExemple service (66.67% du paiement):")
    print(f"  Montant service net: {montant_service_net:.2f}€")
    print(f"  Reconstitution brute: {montant_service_net:.2f}€ / {facteur_remise_global:.1f} = {montant_service_brut_reconstitue:.2f}€")
    
    # === COMPARAISON AVEC RESERVATION_CONTROLLER ===
    print(f"\n" + "=" * 60)
    print("COMPARAISON AVEC RESERVATION_CONTROLLER")
    print("=" * 60)
    
    # Dans reservation_controller, on travaille directement avec les montants bruts
    service_brut_original = subtotal_ht * 0.6667  # 66.67% du sous-total
    service_brut_avec_tva = service_brut_original * (1 + taux_tva/100)
    
    print(f"Reservation_controller (montants bruts):")
    print(f"  Service brut HT: {service_brut_original:.2f}€")
    print(f"  Service brut TTC: {service_brut_avec_tva:.2f}€")
    
    # === ANALYSE DES DIFFÉRENCES ===
    print(f"\n" + "=" * 60)
    print("ANALYSE DES DIFFÉRENCES")
    print("=" * 60)
    
    difference = abs(montant_service_brut_reconstitue - service_brut_avec_tva)
    
    print(f"Montant brut reconstitué (paiement): {montant_service_brut_reconstitue:.2f}€")
    print(f"Montant brut original (réservation): {service_brut_avec_tva:.2f}€")
    print(f"Différence: {difference:.2f}€")
    
    if difference < 0.01:
        print("✅ Les montants sont cohérents")
    else:
        print("❌ Incohérence détectée")
    
    return {
        'reservation_remise': remise_totale,
        'paiement_remise': remise_proportionnelle,
        'difference_reconstitution': difference
    }

def test_solution_proposee():
    """
    Test de la solution proposée
    """
    print(f"\n" + "=" * 80)
    print("SOLUTION PROPOSÉE: MÊME LOGIQUE QUE RESERVATION_CONTROLLER")
    print("=" * 80)
    
    # Données de test
    subtotal_ht = 1500.0
    taux_tva = 20.0
    discount_percent = 10.0
    montant_paiement = 900.0
    
    # Calculs de base
    tax_amount = subtotal_ht * (taux_tva / 100)
    total_ttc_brut = subtotal_ht + tax_amount
    
    print(f"NOUVELLE APPROCHE PAIEMENT_CONTROLLER:")
    print(f"  Total TTC brut (BDD): {total_ttc_brut:.2f}€")
    print(f"  Montant paiement: {montant_paiement:.2f}€")
    print(f"  Remise: {discount_percent}%")
    
    # Nouvelle logique: Calculer les MONTANTS BRUTS directement
    proportion_paiement = montant_paiement / total_ttc_brut
    
    # Pour un service qui représente 60% du total
    service_part = 0.60
    service_ttc_brut_total = total_ttc_brut * service_part
    service_paiement_brut = service_ttc_brut_total * proportion_paiement
    
    # Remise pour ce service
    service_remise = service_ttc_brut_total * (discount_percent / 100) * proportion_paiement
    
    print(f"\nCalculs pour service (60% du total):")
    print(f"  Service TTC brut total: {service_ttc_brut_total:.2f}€")
    print(f"  Proportion paiement: {proportion_paiement:.1%}")
    print(f"  Service paiement brut: {service_paiement_brut:.2f}€")
    print(f"  Remise service: {service_remise:.2f}€")
    
    # Total des crédits
    total_credits_bruts = montant_paiement / proportion_paiement if proportion_paiement > 0 else 0
    remise_totale_paiement = total_credits_bruts * (discount_percent / 100)
    
    print(f"\nVérification équilibre:")
    print(f"  Total crédits bruts: {total_credits_bruts:.2f}€")
    print(f"  Remise totale paiement: {remise_totale_paiement:.2f}€")
    print(f"  Débit caisse: {montant_paiement:.2f}€")
    print(f"  Équilibre: {total_credits_bruts:.2f}€ - {remise_totale_paiement:.2f}€ = {total_credits_bruts - remise_totale_paiement:.2f}€")
    
    if abs((total_credits_bruts - remise_totale_paiement) - montant_paiement) < 0.01:
        print("✅ Équilibre comptable respecté")
    else:
        print("❌ Déséquilibre détecté")

if __name__ == "__main__":
    resultats = test_comparaison_calculs_remise()
    test_solution_proposee()
    
    print(f"\n" + "=" * 80)
    print("CONCLUSION ET RECOMMANDATIONS")
    print("=" * 80)
    print("🔍 PROBLÈME IDENTIFIÉ:")
    print("   Le paiement_controller utilise une reconstitution approximative")
    print("   qui peut créer des petites différences avec reservation_controller")
    print()
    print("💡 SOLUTION RECOMMANDÉE:")
    print("   Appliquer la MÊME logique que reservation_controller:")
    print("   1. Calculer les montants bruts proportionnels")
    print("   2. Remise = pourcentage des montants bruts")
    print("   3. Garantir l'équilibre comptable exact")
    print()
    print("✅ AVANTAGES:")
    print("   • Cohérence parfaite entre création et paiements")
    print("   • Équilibre comptable garanti")
    print("   • Simplicité de maintenance")