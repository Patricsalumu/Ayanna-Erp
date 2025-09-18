#!/usr/bin/env python3
"""
Test de la nouvelle logique basée sur le montant encaissé
"""
def test_logique_montant_encaisse():
    """Test avec le montant réellement encaissé"""
    print("=== TEST LOGIQUE MONTANT ENCAISSÉ ===")
    
    # Scénario réel
    montant_encaisse = 1458.0  # Ce que l'utilisateur tape (argent reçu)
    remise_percent = 10        # Remise de la réservation
    
    print(f"💰 DONNÉES UTILISATEUR:")
    print(f"  Montant encaissé: {montant_encaisse}€")
    print(f"  Remise réservation: {remise_percent}%")
    
    # Calculs automatiques du système
    facteur_remise = 1 - (remise_percent / 100)
    ttc_brut_reconstitue = montant_encaisse / facteur_remise
    remise_montant = ttc_brut_reconstitue - montant_encaisse
    
    print(f"\n🔄 CALCULS AUTOMATIQUES:")
    print(f"  Facteur remise: {facteur_remise}")
    print(f"  TTC brut reconstitué: {montant_encaisse}€ ÷ {facteur_remise} = {ttc_brut_reconstitue:.2f}€")
    print(f"  Remise calculée: {ttc_brut_reconstitue:.2f}€ - {montant_encaisse}€ = {remise_montant:.2f}€")
    
    # Simulation répartition (proportions fictives)
    prop_services = 0.55  # 55%
    prop_produits = 0.28  # 28%
    prop_tva = 0.17       # 17%
    
    services_encaisse = montant_encaisse * prop_services
    produits_encaisse = montant_encaisse * prop_produits
    tva_encaisse = montant_encaisse * prop_tva
    
    services_credit = ttc_brut_reconstitue * prop_services
    produits_credit = ttc_brut_reconstitue * prop_produits
    tva_credit = ttc_brut_reconstitue * prop_tva
    
    print(f"\n📋 ÉCRITURES COMPTABLES:")
    print(f"  Débit Caisse: {montant_encaisse:.2f}€")
    print(f"  Débit Remise: {remise_montant:.2f}€")
    print(f"      Crédit Services: {services_credit:.2f}€")
    print(f"      Crédit Produits: {produits_credit:.2f}€")
    print(f"      Crédit TVA: {tva_credit:.2f}€")
    
    # Vérification équilibre
    total_debits = montant_encaisse + remise_montant
    total_credits = services_credit + produits_credit + tva_credit
    
    print(f"\n✅ VÉRIFICATION:")
    print(f"  Total débits: {total_debits:.2f}€")
    print(f"  Total crédits: {total_credits:.2f}€")
    print(f"  Écart: {abs(total_debits - total_credits):.4f}€")
    
    if abs(total_debits - total_credits) < 0.01:
        print("  🎉 ÉQUILIBRE PARFAIT !")
    else:
        print("  ⚠️  Déséquilibre détecté")
    
    print(f"\n🎯 AVANTAGES:")
    print(f"  ✓ Utilisateur saisit ce qu'il a vraiment encaissé")
    print(f"  ✓ Système calcule automatiquement la décomposition")
    print(f"  ✓ Écritures équilibrées")
    print(f"  ✓ Remise visible explicitement")

if __name__ == "__main__":
    test_logique_montant_encaisse()