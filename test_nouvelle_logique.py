#!/usr/bin/env python3
"""
Test de la nouvelle logique de répartition proportionnelle
"""
import sys
sys.path.append(r'c:\Ayanna ERP\Ayanna-Erp')

# Simuler la logique sans importer les modèles
def test_nouvelle_logique():
    """Test de la nouvelle logique de calcul"""
    print("=== TEST NOUVELLE LOGIQUE DE RÉPARTITION ===")
    
    # Données de test (exemple utilisateur)
    services = [
        {'nom': 'Service 1', 'prix_unitaire': 1000, 'quantite': 1, 'account_id': 70611},
        {'nom': 'Service 2', 'prix_unitaire': 300, 'quantite': 1, 'account_id': 70612}
    ]
    
    produits = [
        {'nom': 'Produit 1', 'prix_unitaire': 500, 'quantite': 1, 'account_id': 70701}
    ]
    
    remise_percent = 10
    tva_percent = 20
    
    # === CALCUL ÉTAPE PAR ÉTAPE ===
    
    print("🔢 DONNÉES INITIALES:")
    print(f"  Services: {[f'{s['nom']} {s['prix_unitaire']}€' for s in services]}")
    print(f"  Produits: {[f'{p['nom']} {p['prix_unitaire']}€' for p in produits]}")
    print(f"  Remise: {remise_percent}%")
    print(f"  TVA: {tva_percent}%")
    
    # 1. Calculer montants HT bruts
    total_services_ht_brut = sum(s['prix_unitaire'] * s['quantite'] for s in services)
    total_produits_ht_brut = sum(p['prix_unitaire'] * p['quantite'] for p in produits)
    total_ht_brut = total_services_ht_brut + total_produits_ht_brut
    
    print(f"\n💰 CALCULS:")
    print(f"  Total services HT brut: {total_services_ht_brut}€")
    print(f"  Total produits HT brut: {total_produits_ht_brut}€")
    print(f"  Total HT brut: {total_ht_brut}€")
    
    # 2. Appliquer remise
    montant_remise = total_ht_brut * (remise_percent / 100)
    total_ht_net = total_ht_brut - montant_remise
    
    print(f"  Remise ({remise_percent}%): -{montant_remise}€")
    print(f"  Total HT net: {total_ht_net}€")
    
    # 3. Calculer TVA sur HT net
    montant_tva = total_ht_net * (tva_percent / 100)
    total_ttc_final = total_ht_net + montant_tva
    
    print(f"  TVA ({tva_percent}%): {montant_tva}€")
    print(f"  Total TTC final: {total_ttc_final}€")
    
    # === NOUVELLE LOGIQUE DE RÉPARTITION ===
    
    print(f"\n📊 NOUVELLE RÉPARTITION (sur total TTC final {total_ttc_final}€):")
    
    # Calculer montants nets pour chaque service/produit
    services_nets = []
    for service in services:
        montant_ht_brut = service['prix_unitaire'] * service['quantite']
        montant_ht_net = montant_ht_brut * (1 - remise_percent / 100)
        proportion = montant_ht_net / total_ttc_final
        services_nets.append({
            'nom': service['nom'],
            'account_id': service['account_id'],
            'montant_net': montant_ht_net,
            'proportion': proportion
        })
        print(f"  🛎️  {service['nom']}: {montant_ht_net}€ net ({proportion:.4f} = {proportion*100:.2f}%)")
    
    produits_nets = []
    for produit in produits:
        montant_ht_brut = produit['prix_unitaire'] * produit['quantite']
        montant_ht_net = montant_ht_brut * (1 - remise_percent / 100)
        proportion = montant_ht_net / total_ttc_final
        produits_nets.append({
            'nom': produit['nom'],
            'account_id': produit['account_id'],
            'montant_net': montant_ht_net,
            'proportion': proportion
        })
        print(f"  📦 {produit['nom']}: {montant_ht_net}€ net ({proportion:.4f} = {proportion*100:.2f}%)")
    
    # TVA
    proportion_tva = montant_tva / total_ttc_final
    print(f"  🧾 TVA: {montant_tva}€ ({proportion_tva:.4f} = {proportion_tva*100:.2f}%)")
    
    # Vérification
    total_proportions = sum(s['proportion'] for s in services_nets) + sum(p['proportion'] for p in produits_nets) + proportion_tva
    print(f"  ✅ Total proportions: {total_proportions:.4f} (doit être = 1.0000)")
    
    # === TEST PAIEMENT ===
    
    montant_paiement = 1000
    print(f"\n💸 TEST PAIEMENT DE {montant_paiement}€:")
    
    allocation_services = {}
    for service in services_nets:
        allocation = montant_paiement * service['proportion']
        allocation_services[service['account_id']] = allocation
        print(f"  🛎️  {service['nom']} (compte {service['account_id']}): {allocation:.2f}€")
    
    allocation_produits = {}
    for produit in produits_nets:
        allocation = montant_paiement * produit['proportion']
        allocation_produits[produit['account_id']] = allocation
        print(f"  📦 {produit['nom']} (compte {produit['account_id']}): {allocation:.2f}€")
    
    allocation_tva = montant_paiement * proportion_tva
    print(f"  🧾 TVA: {allocation_tva:.2f}€")
    
    total_alloue = sum(allocation_services.values()) + sum(allocation_produits.values()) + allocation_tva
    print(f"  📊 Total alloué: {total_alloue:.2f}€ (écart: {abs(total_alloue - montant_paiement):.4f}€)")
    
    print(f"\n✅ RÉSULTAT ATTENDU:")
    print(f"  Service 1 (900€/1944€): {900/1944*1000:.2f}€")
    print(f"  Service 2 (270€/1944€): {270/1944*1000:.2f}€")  
    print(f"  Produit 1 (450€/1944€): {450/1944*1000:.2f}€")
    print(f"  TVA (324€/1944€): {324/1944*1000:.2f}€")

if __name__ == "__main__":
    test_nouvelle_logique()