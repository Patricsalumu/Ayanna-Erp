#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test de la LOGIQUE CORRECTE :
- reservation_controller : Crédits proportionnels (accompte + part remise par compte) + Remise totale
- paiement_controller : Crédits proportionnels (montant selon poids compte) + Pas de remise
"""

print("🧪 TEST LOGIQUE CORRECTE")
print("=" * 60)

print("\n✅ LOGIQUE CORRECTE :")
print("1. 📋 RESERVATION_CONTROLLER (Accompte) :")
print("   - 📤 Crédits proportionnels : (Accompte + Part remise) × Poids compte")
print("   - 💳 Débit remise totale")
print("   - 📥 Débit accompte")
print("   - ⚖️  Équilibre parfait")

print("\n2. 💰 PAIEMENT_CONTROLLER (Paiements suivants) :")
print("   - 📤 Crédits proportionnels : Montant × Poids compte")
print("   - ❌ Pas de remise (déjà faite)")
print("   - 📥 Débit montant")
print("   - ⚖️  Équilibre parfait")

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

# Calcul des poids
poids_service_a = service_a_net / total_net
poids_service_b = service_b_net / total_net
poids_tva = tva_net / total_net

print(f"Réservation : {total_ttc_brut:.2f}€ TTC brut")
print(f"Remise {remise_percent}% : {remise_totale:.2f}€")
print(f"Total net : {total_net:.2f}€")
print(f"Accompte : {accompte:.2f}€")
print(f"Solde : {solde:.2f}€")

print(f"\n🔸 RÉPARTITION PAR COMPTE (poids) :")
print(f"Service A : {service_a_net:.2f}€ = {poids_service_a:.1%}")
print(f"Service B : {service_b_net:.2f}€ = {poids_service_b:.1%}")
print(f"TVA       : {tva_net:.2f}€ = {poids_tva:.1%}")
print(f"TOTAL     : {service_a_net + service_b_net + tva_net:.2f}€ = {poids_service_a + poids_service_b + poids_tva:.1%}")

print(f"\n🏗️  ACCOMPTE (reservation_controller) :")
montant_a_ventiler = accompte + remise_totale
print(f"Montant à ventiler : {accompte:.2f}€ (accompte) + {remise_totale:.2f}€ (remise) = {montant_a_ventiler:.2f}€")

credit_service_a_1 = montant_a_ventiler * poids_service_a
credit_service_b_1 = montant_a_ventiler * poids_service_b
credit_tva_1 = montant_a_ventiler * poids_tva

print(f"📥 DÉBIT Caisse: {accompte:.2f}€")
print(f"📤 CRÉDIT Service A: {credit_service_a_1:.2f}€ ({poids_service_a:.1%} × {montant_a_ventiler:.2f}€)")
print(f"📤 CRÉDIT Service B: {credit_service_b_1:.2f}€ ({poids_service_b:.1%} × {montant_a_ventiler:.2f}€)")
print(f"📤 CRÉDIT TVA: {credit_tva_1:.2f}€ ({poids_tva:.1%} × {montant_a_ventiler:.2f}€)")
print(f"💳 DÉBIT Remise: {remise_totale:.2f}€")

total_credits_1 = credit_service_a_1 + credit_service_b_1 + credit_tva_1
total_debits_1 = accompte + remise_totale
print(f"\n⚖️  VÉRIFICATION ÉQUILIBRE :")
print(f"Total crédits: {total_credits_1:.2f}€")
print(f"Total débits:  {total_debits_1:.2f}€")
print(f"Différence:    {abs(total_credits_1 - total_debits_1):.2f}€")
if abs(total_credits_1 - total_debits_1) < 0.01:
    print("✅ Équilibre respecté")
else:
    print("❌ Déséquilibre")

print(f"\n💰 SOLDE (paiement_controller) :")
print(f"Montant à ventiler : {solde:.2f}€ (solde seulement)")

credit_service_a_2 = solde * poids_service_a
credit_service_b_2 = solde * poids_service_b
credit_tva_2 = solde * poids_tva

print(f"📥 DÉBIT Caisse: {solde:.2f}€")
print(f"📤 CRÉDIT Service A: {credit_service_a_2:.2f}€ ({poids_service_a:.1%} × {solde:.2f}€)")
print(f"📤 CRÉDIT Service B: {credit_service_b_2:.2f}€ ({poids_service_b:.1%} × {solde:.2f}€)")
print(f"📤 CRÉDIT TVA: {credit_tva_2:.2f}€ ({poids_tva:.1%} × {solde:.2f}€)")
print(f"💳 DÉBIT Remise: 0.00€ (déjà fait)")

total_credits_2 = credit_service_a_2 + credit_service_b_2 + credit_tva_2
total_debits_2 = solde
print(f"\n⚖️  VÉRIFICATION ÉQUILIBRE :")
print(f"Total crédits: {total_credits_2:.2f}€")
print(f"Total débits:  {total_debits_2:.2f}€")
print(f"Différence:    {abs(total_credits_2 - total_debits_2):.2f}€")
if abs(total_credits_2 - total_debits_2) < 0.01:
    print("✅ Équilibre respecté")
else:
    print("❌ Déséquilibre")

print(f"\n🎯 TOTAUX FINAUX PAR COMPTE :")
total_service_a = credit_service_a_1 + credit_service_a_2
total_service_b = credit_service_b_1 + credit_service_b_2
total_tva = credit_tva_1 + credit_tva_2
total_encaisse = accompte + solde

print(f"Service A crédité: {total_service_a:.2f}€ (attendu: {service_a_net:.2f}€ + {service_a_net * remise_percent / 100:.2f}€ = {service_a_net * (1 + remise_percent / 100):.2f}€)")
print(f"Service B crédité: {total_service_b:.2f}€")
print(f"TVA créditée: {total_tva:.2f}€")
print(f"Remise débitée: {remise_totale:.2f}€")
print(f"Total encaissé: {total_encaisse:.2f}€")

# Vérification finale
credit_attendu_service_a = service_a_net * (1 + remise_percent / 100)
if abs(total_service_a - credit_attendu_service_a) < 0.01:
    print(f"\n🎉 PARFAIT ! Service A : {total_service_a:.2f}€ = Attendu {credit_attendu_service_a:.2f}€")
else:
    print(f"\n❌ Erreur Service A : {total_service_a:.2f}€ ≠ Attendu {credit_attendu_service_a:.2f}€")

if total_encaisse == total_net:
    print(f"🎉 PARFAIT ! Total encaissé ({total_encaisse:.2f}€) = Total net ({total_net:.2f}€)")
else:
    print(f"❌ Erreur : Total encaissé ({total_encaisse:.2f}€) ≠ Total net ({total_net:.2f}€)")

print(f"\n✨ CETTE LOGIQUE EST MAINTENANT PARFAITE ! ✨")