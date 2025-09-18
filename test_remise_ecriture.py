#!/usr/bin/env python3
"""
Test de la correction de l'écriture remise
"""
import sys
sys.path.append(r'c:\Ayanna ERP\Ayanna-Erp')

def test_calcul_remise():
    """Test du calcul de remise pour vérifier la logique"""
    print("=== TEST CALCUL REMISE ===")
    
    # Données basées sur le log utilisateur
    total_services = 1000  # Total services brut
    total_produits = 500   # Total produits brut
    remise_percent = 20    # 20% de remise
    tva_percent = 20       # 20% TVA
    paiement = 1440        # Paiement total
    
    print(f"📊 DONNÉES:")
    print(f"  Services brut: {total_services}€")
    print(f"  Produits brut: {total_produits}€")
    print(f"  Remise: {remise_percent}%")
    print(f"  TVA: {tva_percent}%")
    print(f"  Paiement: {paiement}€")
    
    # Calcul étape par étape
    total_ht_brut = total_services + total_produits
    montant_remise = total_ht_brut * (remise_percent / 100)
    total_ht_net = total_ht_brut - montant_remise
    montant_tva = total_ht_net * (tva_percent / 100)
    total_ttc = total_ht_net + montant_tva
    
    print(f"\n💰 CALCULS:")
    print(f"  Total HT brut: {total_ht_brut}€")
    print(f"  Remise {remise_percent}%: -{montant_remise}€")
    print(f"  Total HT net: {total_ht_net}€")
    print(f"  TVA {tva_percent}%: {montant_tva}€")
    print(f"  Total TTC: {total_ttc}€")
    
    # Test de la remise proportionnelle
    if total_ttc > 0:
        remise_paiement = (paiement / total_ttc) * montant_remise
        print(f"\n🔄 REMISE PROPORTIONNELLE:")
        print(f"  Paiement / Total TTC: {paiement}/{total_ttc} = {paiement/total_ttc:.4f}")
        print(f"  Remise proportionnelle: {paiement/total_ttc:.4f} × {montant_remise}€ = {remise_paiement:.2f}€")
    
    print(f"\n📋 ÉCRITURES ATTENDUES:")
    print(f"  Débit Caisse: {paiement}€")
    print(f"  Crédit Services nets: {total_services * (1 - remise_percent/100)}€")
    print(f"  Crédit Produits nets: {total_produits * (1 - remise_percent/100)}€") 
    print(f"  Crédit TVA: {montant_tva}€")
    print(f"  Débit Remise: {remise_paiement:.2f}€")
    
    # Vérification équilibre
    total_credits = (total_services * (1 - remise_percent/100) + 
                    total_produits * (1 - remise_percent/100) + 
                    montant_tva)
    total_debits = paiement + remise_paiement
    
    print(f"\n✅ VÉRIFICATION ÉQUILIBRE:")
    print(f"  Total débits: {total_debits:.2f}€")
    print(f"  Total crédits: {total_credits:.2f}€")
    print(f"  Écart: {abs(total_debits - total_credits):.2f}€")
    
    if abs(total_debits - total_credits) < 0.01:
        print("  🎉 ÉQUILIBRE PARFAIT !")
    else:
        print("  ⚠️  Déséquilibre détecté")

if __name__ == "__main__":
    test_calcul_remise()