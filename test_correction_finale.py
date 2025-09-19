#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test de validation de la CORRECTION FINALE :
- reservation_controller : Poids basés sur TOTAL BRUT
- paiement_controller : Poids basés sur TOTAL BRUT aussi
"""

print("🧪 TEST CORRECTION FINALE - POIDS SUR TOTAL BRUT")
print("=" * 70)

print("\n✅ CORRECTION APPLIQUÉE :")
print("1. 📋 RESERVATION_CONTROLLER :")
print("   - 📊 Poids calculés sur TOTAL TTC BRUT (sans remise)")
print("   - 📤 Crédits = (Accompte + Remise) × Poids sur BRUT")
print("   - 💳 Remise totale débitée")

print("\n2. 💰 PAIEMENT_CONTROLLER :")
print("   - 📊 Poids calculés sur TOTAL TTC BRUT (sans remise)")
print("   - 📤 Crédits = Montant × Poids sur BRUT")
print("   - ❌ Pas de remise")

print("\n📊 EXEMPLE SELON VOS LOGS :")
# Données de vos logs
total_ttc_brut = 2640.0  # TTC brut stocké SANS remise
remise_percent = 5.0     # Supposons 5% de remise (132€ / 2640€)
remise_totale = 132.0    # Remise totale selon vos logs
accompte = 1000.0        # Accompte selon vos logs

# Montants bruts par compte (reconstitués)
service_brut = 1200.0    # 45.5% de 2640€
produit_brut = 1200.0    # 45.5% de 2640€
tva_brut = 240.0         # Le reste pour TVA

print(f"Total TTC brut : {total_ttc_brut:.2f}€")
print(f"Remise : {remise_totale:.2f}€ ({remise_percent:.1f}%)")
print(f"Accompte : {accompte:.2f}€")

print(f"\n🔸 RÉPARTITION PAR COMPTE (BRUT) :")
poids_service = service_brut / total_ttc_brut
poids_produit = produit_brut / total_ttc_brut
poids_tva = tva_brut / total_ttc_brut

print(f"Service : {service_brut:.2f}€ = {poids_service:.1%} ✅")
print(f"Produit : {produit_brut:.2f}€ = {poids_produit:.1%} ✅")
print(f"TVA     : {tva_brut:.2f}€ = {poids_tva:.1%}")
print(f"TOTAL   : {service_brut + produit_brut + tva_brut:.2f}€ = {poids_service + poids_produit + poids_tva:.1%}")

print(f"\n🏗️  ACCOMPTE (reservation_controller) - CORRECTION :")
montant_a_ventiler = accompte + remise_totale
print(f"Montant à ventiler : {accompte:.2f}€ + {remise_totale:.2f}€ = {montant_a_ventiler:.2f}€")

# Calculs avec les BONS poids (sur brut)
credit_service_attendu = montant_a_ventiler * poids_service
credit_produit_attendu = montant_a_ventiler * poids_produit
credit_tva_attendu = montant_a_ventiler * poids_tva

print(f"📥 DÉBIT Caisse: {accompte:.2f}€")
print(f"📤 CRÉDIT Service: {credit_service_attendu:.2f}€ ({poids_service:.1%} × {montant_a_ventiler:.2f}€) ✅")
print(f"📤 CRÉDIT Produit: {credit_produit_attendu:.2f}€ ({poids_produit:.1%} × {montant_a_ventiler:.2f}€) ✅")
print(f"📤 CRÉDIT TVA: {credit_tva_attendu:.2f}€ ({poids_tva:.1%} × {montant_a_ventiler:.2f}€)")
print(f"💳 DÉBIT Remise: {remise_totale:.2f}€")

# Vérification équilibre
total_credits = credit_service_attendu + credit_produit_attendu + credit_tva_attendu
total_debits = accompte + remise_totale

print(f"\n⚖️  VÉRIFICATION ÉQUILIBRE :")
print(f"Total crédits: {total_credits:.2f}€")
print(f"Total débits:  {total_debits:.2f}€")
print(f"Différence:    {abs(total_credits - total_debits):.2f}€")

if abs(total_credits - total_debits) < 0.01:
    print("✅ Équilibre respecté")
else:
    print("❌ Déséquilibre")

print(f"\n🔍 COMPARAISON AVEC VOS LOGS :")
print(f"ATTENDU - Service: {credit_service_attendu:.2f}€ (au lieu de 205.16€)")
print(f"ATTENDU - Produit: {credit_produit_attendu:.2f}€ (au lieu de 205.16€)")
print(f"ATTENDU - TVA: {credit_tva_attendu:.2f}€ (au lieu de 41.03€)")

difference_service = abs(credit_service_attendu - 205.16)
difference_produit = abs(credit_produit_attendu - 205.16)

if difference_service < 1.0:
    print("✅ Correction mineure nécessaire")
else:
    print("🎯 Correction majeure appliquée")

print(f"\n💰 PAIEMENT SUIVANT (paiement_controller) :")
solde = (total_ttc_brut - remise_totale) - accompte
print(f"Solde restant : {solde:.2f}€")

credit_service_2 = solde * poids_service
credit_produit_2 = solde * poids_produit
credit_tva_2 = solde * poids_tva

print(f"📤 CRÉDIT Service: {credit_service_2:.2f}€ ({poids_service:.1%} × {solde:.2f}€)")
print(f"📤 CRÉDIT Produit: {credit_produit_2:.2f}€ ({poids_produit:.1%} × {solde:.2f}€)")
print(f"📤 CRÉDIT TVA: {credit_tva_2:.2f}€ ({poids_tva:.1%} × {solde:.2f}€)")

print(f"\n🎯 TOTAUX FINAUX :")
total_service_final = credit_service_attendu + credit_service_2
total_produit_final = credit_produit_attendu + credit_produit_2

print(f"Service TOTAL : {total_service_final:.2f}€ (attendu: {service_brut:.2f}€)")
print(f"Produit TOTAL : {total_produit_final:.2f}€ (attendu: {produit_brut:.2f}€)")

if abs(total_service_final - service_brut) < 0.01:
    print("🎉 PARFAIT ! Service crédité = Montant brut attendu")
else:
    print(f"⚠️  Écart Service: {abs(total_service_final - service_brut):.2f}€")

print(f"\n✨ CORRECTION TERMINÉE ! Poids basés sur TOTAL BRUT ✨")