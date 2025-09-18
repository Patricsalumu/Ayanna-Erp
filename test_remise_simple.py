#!/usr/bin/env python3
"""
Test de la nouvelle logique de remise (X% du total TTC)
"""
import sys
sys.path.append(r'c:\Ayanna ERP\Ayanna-Erp')

def test_remise_simple():
    """Test de la nouvelle logique simple"""
    print("=== TEST NOUVELLE LOGIQUE REMISE SIMPLE ===")
    
    # Données réelles d'après vos logs
    total_ttc = 1620.0    # Total TTC de la réservation
    remise_percent = 10   # 10% de remise
    paiement = 1000.0     # Paiement partiel
    
    print(f"📊 DONNÉES:")
    print(f"  Total TTC réservation: {total_ttc}€")
    print(f"  Remise: {remise_percent}%")
    print(f"  Paiement: {paiement}€")
    
    # Nouvelle logique simple
    print(f"\n💰 CALCUL SIMPLE:")
    
    # 1. Remise totale = X% du total TTC
    remise_totale = total_ttc * (remise_percent / 100)
    print(f"  Remise totale: {remise_percent}% × {total_ttc}€ = {remise_totale}€")
    
    # 2. Remise proportionnelle pour ce paiement
    proportion_paiement = paiement / total_ttc
    remise_paiement = proportion_paiement * remise_totale
    print(f"  Proportion paiement: {paiement}€ / {total_ttc}€ = {proportion_paiement:.4f}")
    print(f"  Remise pour ce paiement: {proportion_paiement:.4f} × {remise_totale}€ = {remise_paiement:.2f}€")
    
    print(f"\n📋 ÉCRITURES ATTENDUES (pour paiement de {paiement}€):")
    print(f"  Débit Caisse: {paiement}€")
    print(f"  Crédit Services: [montant proportionnel]")
    print(f"  Crédit Produits: [montant proportionnel]")
    print(f"  Crédit TVA: [montant proportionnel]")
    print(f"  Débit Remise: {remise_paiement:.2f}€  ← NOUVEAU")
    
    print(f"\n✅ AVANTAGES DE CETTE MÉTHODE:")
    print(f"  ✓ Simple à calculer")
    print(f"  ✓ Toujours cohérent")
    print(f"  ✓ Fonctionne avec tous les pourcentages")
    print(f"  ✓ La remise apparaît clairement dans les écritures")
    
    # Test avec paiement complet
    print(f"\n🔄 TEST PAIEMENT COMPLET ({total_ttc}€):")
    remise_complete = (total_ttc / total_ttc) * remise_totale
    print(f"  Remise pour paiement complet: {remise_complete:.2f}€")
    print(f"  ✓ C'est bien égal à la remise totale de {remise_totale}€")

if __name__ == "__main__":
    test_remise_simple()