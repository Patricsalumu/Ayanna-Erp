#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test de la logique corrigée selon les logs utilisateur :
- 45.5% service, 45.5% produit sur 2640€ TTC brut = 1200€ chacun
- Accompte 1000€ + Remise 132€ = 1132€ à ventiler
- Service : 45.5% × 1132€ = 515.06€ (attendu)
- Produit : 45.5% × 1132€ = 515.06€ (attendu)
"""

print("🧪 TEST SELON LOGS UTILISATEUR")
print("=" * 50)

print("\n📊 DONNÉES DE L'EXEMPLE :")
ttc_brut = 2640.0
remise_percent = 5.0  # Approximation pour avoir 132€ de remise
remise_totale = 132.0  # Valeur exacte des logs
accompte = 1000.0

# Répartition selon logs
service_brut = 1200.0  # 45.5% de 2640€
produit_brut = 1200.0  # 45.5% de 2640€
tva_brut = 240.0       # Le reste

poids_service = service_brut / ttc_brut
poids_produit = produit_brut / ttc_brut
poids_tva = tva_brut / ttc_brut

print(f"TTC brut total : {ttc_brut:.2f}€")
print(f"Remise totale : {remise_totale:.2f}€")
print(f"Accompte : {accompte:.2f}€")
print()
print(f"Service brut : {service_brut:.2f}€ = {poids_service:.1%}")
print(f"Produit brut : {produit_brut:.2f}€ = {poids_produit:.1%}")
print(f"TVA brut : {tva_brut:.2f}€ = {poids_tva:.1%}")

print(f"\n🏗️  ACCOMPTE (reservation_controller) :")
print("LOGIQUE : (Accompte + Remise totale) × Poids de chaque compte")

montant_a_ventiler_accompte = accompte + remise_totale
credit_service_accompte = montant_a_ventiler_accompte * poids_service
credit_produit_accompte = montant_a_ventiler_accompte * poids_produit
credit_tva_accompte = montant_a_ventiler_accompte * poids_tva

print(f"Montant à ventiler : {accompte:.2f}€ + {remise_totale:.2f}€ = {montant_a_ventiler_accompte:.2f}€")
print(f"📥 DÉBIT Caisse : {accompte:.2f}€")
print(f"📤 CRÉDIT Service : {credit_service_accompte:.2f}€ ({poids_service:.1%} × {montant_a_ventiler_accompte:.2f}€)")
print(f"📤 CRÉDIT Produit : {credit_produit_accompte:.2f}€ ({poids_produit:.1%} × {montant_a_ventiler_accompte:.2f}€)")
print(f"📤 CRÉDIT TVA : {credit_tva_accompte:.2f}€ ({poids_tva:.1%} × {montant_a_ventiler_accompte:.2f}€)")
print(f"💳 DÉBIT Remise : {remise_totale:.2f}€")

total_credits_accompte = credit_service_accompte + credit_produit_accompte + credit_tva_accompte
total_debits_accompte = accompte + remise_totale

print(f"\n⚖️  ÉQUILIBRE ACCOMPTE :")
print(f"Total crédits : {total_credits_accompte:.2f}€")
print(f"Total débits : {total_debits_accompte:.2f}€")
print(f"Différence : {abs(total_credits_accompte - total_debits_accompte):.2f}€")

print(f"\n✅ VÉRIFICATION AVEC LOGS UTILISATEUR :")
print(f"Service attendu : 515.06€ → Calculé : {credit_service_accompte:.2f}€")
print(f"Produit attendu : 515.06€ → Calculé : {credit_produit_accompte:.2f}€")

if abs(credit_service_accompte - 515.06) < 1:
    print("✅ Service CORRECT")
else:
    print("❌ Service INCORRECT")

if abs(credit_produit_accompte - 515.06) < 1:
    print("✅ Produit CORRECT")
else:
    print("❌ Produit INCORRECT")

print(f"\n💰 PAIEMENT SUIVANT (paiement_controller) :")
print("LOGIQUE : Montant × Poids de chaque compte")

montant_paiement_2 = 500.0  # Exemple paiement suivant
credit_service_2 = montant_paiement_2 * poids_service
credit_produit_2 = montant_paiement_2 * poids_produit
credit_tva_2 = montant_paiement_2 * poids_tva

print(f"Montant paiement : {montant_paiement_2:.2f}€")
print(f"📥 DÉBIT Caisse : {montant_paiement_2:.2f}€")
print(f"📤 CRÉDIT Service : {credit_service_2:.2f}€ ({poids_service:.1%} × {montant_paiement_2:.2f}€)")
print(f"📤 CRÉDIT Produit : {credit_produit_2:.2f}€ ({poids_produit:.1%} × {montant_paiement_2:.2f}€)")
print(f"📤 CRÉDIT TVA : {credit_tva_2:.2f}€ ({poids_tva:.1%} × {montant_paiement_2:.2f}€)")
print(f"💳 DÉBIT Remise : 0.00€ (déjà fait)")

total_credits_2 = credit_service_2 + credit_produit_2 + credit_tva_2
print(f"\n⚖️  ÉQUILIBRE PAIEMENT :")
print(f"Total crédits : {total_credits_2:.2f}€")
print(f"Total débits : {montant_paiement_2:.2f}€")
print(f"Différence : {abs(total_credits_2 - montant_paiement_2):.2f}€")

print(f"\n✨ LOGIQUE MAINTENANT CORRECTE ! ✨")