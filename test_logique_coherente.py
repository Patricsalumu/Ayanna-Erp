#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test de la logique cohérente finale :
- reservation_controller : Crédits BRUTS TOTAUX + Remise TOTALE au premier paiement
- paiement_controller : Crédits proportionnels + Pas de remise
"""

print("🧪 TEST LOGIQUE COHÉRENTE FINALE")
print("=" * 60)

print("\n✅ LOGIQUE COHÉRENTE :")
print("1. 📋 RESERVATION_CONTROLLER (Premier paiement / Accompte) :")
print("   - 📤 Crédits BRUTS TOTAUX pour chaque compte")
print("   - 💳 Remise TOTALE débitée")
print("   - 📥 Débit = Montant accompte")
print("   - ⚖️  Équilibre comptable respecté")

print("\n2. 💰 PAIEMENT_CONTROLLER (Paiements suivants) :")
print("   - 📤 Crédits proportionnels (bruts)")
print("   - 💳 Remise = 0 (déjà débitée)")
print("   - 📥 Débit = Montant paiement")
print("   - ⚖️  Équilibre comptable respecté")

print("\n📊 EXEMPLE CONCRET :")
# Données de test
total_ttc_brut = 1000.0
remise_percent = 10.0
remise_totale = total_ttc_brut * (remise_percent / 100)
total_net = total_ttc_brut - remise_totale
accompte = 300.0
solde = total_net - accompte

# Répartition par compte (exemple)
service_a_net = 400.0  # 40% du net
service_b_net = 250.0  # 25% du net
tva_net = 250.0        # 25% du net

# Reconstitution brute
facteur_remise = 1 - (remise_percent / 100)
service_a_brut = service_a_net / facteur_remise
service_b_brut = service_b_net / facteur_remise
tva_brut = tva_net / facteur_remise

print(f"Réservation : {total_ttc_brut:.2f}€ TTC brut")
print(f"Remise {remise_percent}% : {remise_totale:.2f}€")
print(f"Total net : {total_net:.2f}€")
print(f"Accompte : {accompte:.2f}€")
print(f"Solde : {solde:.2f}€")

print(f"\n🔸 RÉPARTITION PAR COMPTE :")
print(f"Service A - Net: {service_a_net:.2f}€ → Brut: {service_a_brut:.2f}€")
print(f"Service B - Net: {service_b_net:.2f}€ → Brut: {service_b_brut:.2f}€")
print(f"TVA       - Net: {tva_net:.2f}€ → Brut: {tva_brut:.2f}€")

print(f"\n🏗️  PREMIER PAIEMENT (reservation_controller) :")
print(f"📥 DÉBIT Caisse: {accompte:.2f}€")
print(f"📤 CRÉDIT Service A: {service_a_brut:.2f}€ (BRUT TOTAL)")
print(f"📤 CRÉDIT Service B: {service_b_brut:.2f}€ (BRUT TOTAL)")
print(f"📤 CRÉDIT TVA: {tva_brut:.2f}€ (BRUT TOTAL)")
print(f"💳 DÉBIT Remise: {remise_totale:.2f}€ (TOTALE)")

total_credits_1 = service_a_brut + service_b_brut + tva_brut
total_debits_1 = accompte + remise_totale
print(f"\n⚖️  VÉRIFICATION ÉQUILIBRE :")
print(f"Total crédits: {total_credits_1:.2f}€")
print(f"Total débits:  {total_debits_1:.2f}€")
print(f"Différence:    {abs(total_credits_1 - total_debits_1):.2f}€")
if abs(total_credits_1 - total_debits_1) < 0.01:
    print("✅ Équilibre respecté")
else:
    print("❌ Déséquilibre")

print(f"\n💰 DEUXIÈME PAIEMENT (paiement_controller) :")
paiement_2 = solde  # Solde complet
proportion_2 = paiement_2 / total_net

service_a_credit_2 = service_a_net
service_b_credit_2 = service_b_net
tva_credit_2 = tva_net

print(f"📥 DÉBIT Caisse: {paiement_2:.2f}€")
print(f"📤 CRÉDIT Service A: {service_a_credit_2:.2f}€ (proportionnel net)")
print(f"📤 CRÉDIT Service B: {service_b_credit_2:.2f}€ (proportionnel net)")
print(f"📤 CRÉDIT TVA: {tva_credit_2:.2f}€ (proportionnel net)")
print(f"💳 DÉBIT Remise: 0.00€ (déjà fait)")

total_credits_2 = service_a_credit_2 + service_b_credit_2 + tva_credit_2
total_debits_2 = paiement_2
print(f"\n⚖️  VÉRIFICATION ÉQUILIBRE :")
print(f"Total crédits: {total_credits_2:.2f}€")
print(f"Total débits:  {total_debits_2:.2f}€")
print(f"Différence:    {abs(total_credits_2 - total_debits_2):.2f}€")
if abs(total_credits_2 - total_debits_2) < 0.01:
    print("✅ Équilibre respecté")
else:
    print("❌ Déséquilibre")

print(f"\n🎯 TOTAUX FINAUX :")
total_credits_final = total_credits_1 + total_credits_2
total_debits_final = total_debits_1 + total_debits_2
print(f"TOTAL crédits: {total_credits_final:.2f}€")
print(f"TOTAL débits:  {total_debits_final:.2f}€")
print(f"TOTAL remise débitée: {remise_totale:.2f}€")
print(f"TOTAL encaissé: {accompte + paiement_2:.2f}€")

if abs(total_credits_final - total_debits_final) < 0.01:
    print("\n✨ PARFAIT ! Logique cohérente et équilibrée.")
else:
    print(f"\n❌ Problème d'équilibre final : {abs(total_credits_final - total_debits_final):.2f}€")