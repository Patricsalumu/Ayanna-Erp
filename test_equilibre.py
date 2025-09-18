#!/usr/bin/env python3
"""
Test de l'équilibre comptable avec la nouvelle logique
"""
def test_equilibre_comptable():
    """Test de l'équilibre des écritures"""
    print("=== TEST ÉQUILIBRE COMPTABLE ===")
    
    # Données réelles
    total_ttc = 1620.0
    remise_percent = 10
    paiement = 1620.0  # Paiement complet
    
    print(f"📊 DONNÉES:")
    print(f"  Total TTC: {total_ttc}€")
    print(f"  Remise: {remise_percent}%")
    print(f"  Paiement: {paiement}€")
    
    # Simulation des calculs
    remise_totale = total_ttc * (remise_percent / 100)
    facteur_remise = 1 - (remise_percent / 100)
    
    # Supposons répartition 60% services, 30% produits, 10% TVA (sur montants nets)
    services_net = total_ttc * 0.60
    produits_net = total_ttc * 0.30
    tva_net = total_ttc * 0.10
    
    print(f"\n💰 MONTANTS NETS (utilisés pour répartition):")
    print(f"  Services net: {services_net:.2f}€")
    print(f"  Produits net: {produits_net:.2f}€")
    print(f"  TVA net: {tva_net:.2f}€")
    print(f"  Total net: {services_net + produits_net + tva_net:.2f}€")
    
    # Reconstitution des montants bruts pour écritures
    services_brut = services_net / facteur_remise
    produits_brut = produits_net / facteur_remise
    tva_brut = tva_net / facteur_remise
    
    print(f"\n📋 ÉCRITURES COMPTABLES (montants bruts):")
    print(f"  Débit Caisse: {paiement:.2f}€")
    print(f"  Débit Remise: {remise_totale:.2f}€")
    print(f"      Crédit Services: {services_brut:.2f}€")
    print(f"      Crédit Produits: {produits_brut:.2f}€")
    print(f"      Crédit TVA: {tva_brut:.2f}€")
    
    # Vérification équilibre
    total_debits = paiement + remise_totale
    total_credits = services_brut + produits_brut + tva_brut
    
    print(f"\n✅ VÉRIFICATION ÉQUILIBRE:")
    print(f"  Total débits: {total_debits:.2f}€")
    print(f"  Total crédits: {total_credits:.2f}€")
    print(f"  Écart: {abs(total_debits - total_credits):.4f}€")
    
    if abs(total_debits - total_credits) < 0.01:
        print("  🎉 ÉQUILIBRE PARFAIT !")
    else:
        print("  ⚠️  Déséquilibre détecté")
    
    print(f"\n🔍 EXPLICATION:")
    print(f"  - On encaisse {paiement}€")
    print(f"  - On accorde {remise_totale}€ de remise (charge)")
    print(f"  - On reconnaît {total_credits:.2f}€ de ventes (au prix brut)")
    print(f"  - Total des mouvements: {total_debits:.2f}€ = {total_credits:.2f}€")

if __name__ == "__main__":
    test_equilibre_comptable()