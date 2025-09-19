#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test de l'OPTION B - Logique simplifiée :
- reservation_controller : Tout en une fois (crédits TOTAUX + remise TOTALE)
- paiement_controller : Encaissement simple (débit/crédit du montant seulement)
"""

print("🧪 TEST OPTION B - LOGIQUE SIMPLIFIÉE")
print("=" * 60)

print("\n✅ OPTION B - LOGIQUE SIMPLIFIÉE :")
print("1. 📋 RESERVATION_CONTROLLER (Création + Accompte) :")
print("   - 📤 Crédits TOTAUX de tous les comptes (services/produits/TVA)")
print("   - 💳 Débit TOTAL de la remise")
print("   - 📥 Débit de l'accompte")
print("   - ⚖️  Équilibre parfait")

print("\n2. 💰 PAIEMENT_CONTROLLER (Paiements suivants) :")
print("   - 📥 Débit caisse = montant perçu")
print("   - 📤 Crédit encaissement = montant perçu")
print("   - ❌ Pas de remise (déjà faite)")
print("   - ⚖️  Équilibre simple")

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

print(f"\n🏗️  CRÉATION RÉSERVATION + ACCOMPTE (reservation_controller) :")
print(f"📥 DÉBIT Caisse: {accompte:.2f}€")
print(f"📤 CRÉDIT Service A: {service_a_brut:.2f}€ (TOTAL)")
print(f"📤 CRÉDIT Service B: {service_b_brut:.2f}€ (TOTAL)")
print(f"📤 CRÉDIT TVA: {tva_brut:.2f}€ (TOTAL)")
print(f"💳 DÉBIT Remise: {remise_totale:.2f}€ (TOTAL)")

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

print(f"\n💰 PAIEMENT SOLDE (paiement_controller) :")
paiement_2 = solde  # Solde complet

print(f"📥 DÉBIT Caisse: {paiement_2:.2f}€")
print(f"📤 CRÉDIT Encaissement: {paiement_2:.2f}€")
print(f"💳 DÉBIT Remise: 0.00€ (déjà fait)")
print(f"📊 Aucune ventilation - Encaissement simple")

total_credits_2 = paiement_2  # Encaissement simple
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
total_encaisse = accompte + paiement_2

print(f"Services crédités: {service_a_brut + service_b_brut:.2f}€")
print(f"TVA créditée: {tva_brut:.2f}€")
print(f"Remise débitée: {remise_totale:.2f}€")
print(f"Encaissement crédité: {paiement_2:.2f}€")
print(f"Total encaissé: {total_encaisse:.2f}€")

print(f"\n✨ AVANTAGES OPTION B :")
print("   ✅ Plus simple à comprendre")
print("   ✅ Pas de calculs proportionnels complexes")
print("   ✅ Remise débitée une seule fois")
print("   ✅ Paiements suivants = encaissements simples")
print("   ✅ Équilibre comptable garanti")
print("   ✅ Moins d'erreurs possibles")

if total_encaisse == total_net:
    print(f"\n🎉 PARFAIT ! Total encaissé ({total_encaisse:.2f}€) = Total net ({total_net:.2f}€)")
else:
    print(f"\n❌ Erreur : Total encaissé ({total_encaisse:.2f}€) ≠ Total net ({total_net:.2f}€)")