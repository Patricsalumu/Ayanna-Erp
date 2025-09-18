#!/usr/bin/env python3
"""
Script pour diagnostiquer et corriger la logique de répartition
"""
import sys
sys.path.append(r'c:\Ayanna ERP\Ayanna-Erp')

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.salle_fete.model.salle_fete import ReservationSalleFete, EventReservationService, EventReservationProduct
from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaConfig

def analyser_reservation_test():
    """Analyse la structure des montants dans une réservation"""
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # Créer une réservation de test simple
        print("=== ANALYSE DE LA STRUCTURE DES MONTANTS ===")
        
        # Exemple: Service 1000€, Produit 500€, TVA 20%, Remise 10%
        # Calcul théorique:
        # - Total HT brut: 1500€
        # - Remise 10%: -150€
        # - Total HT net: 1350€
        # - TVA 20% sur HT net: 270€
        # - Total TTC final: 1620€
        
        print("🔍 CALCUL THÉORIQUE:")
        total_ht_brut = 1500
        remise_percent = 10
        tva_percent = 20
        
        montant_remise = total_ht_brut * (remise_percent / 100)
        total_ht_net = total_ht_brut - montant_remise
        montant_tva = total_ht_net * (tva_percent / 100)
        total_ttc_final = total_ht_net + montant_tva
        
        print(f"  Total HT brut: {total_ht_brut:.2f}€")
        print(f"  Remise {remise_percent}%: -{montant_remise:.2f}€")
        print(f"  Total HT net: {total_ht_net:.2f}€")
        print(f"  TVA {tva_percent}%: {montant_tva:.2f}€")
        print(f"  Total TTC final: {total_ttc_final:.2f}€")
        
        print("\n🎯 PROPORTIONS ATTENDUES:")
        prop_service = (1000 * (1 - remise_percent/100)) / total_ht_net  # Service après remise / HT net
        prop_produit = (500 * (1 - remise_percent/100)) / total_ht_net   # Produit après remise / HT net
        prop_tva = montant_tva / total_ttc_final                        # TVA / TTC final
        
        print(f"  Service (900€ net): {prop_service:.4f} ({prop_service*100:.2f}%)")
        print(f"  Produit (450€ net): {prop_produit:.4f} ({prop_produit*100:.2f}%)")
        print(f"  TVA (270€): {prop_tva:.4f} ({prop_tva*100:.2f}%)")
        print(f"  Total: {prop_service + prop_produit + prop_tva:.4f}")
        
        print("\n💰 TEST PAIEMENT DE 1000€:")
        paiement = 1000
        allocation_service = paiement * (900 / total_ttc_final)  # 900€ net sur 1620€ total
        allocation_produit = paiement * (450 / total_ttc_final)  # 450€ net sur 1620€ total
        allocation_tva = paiement * (270 / total_ttc_final)      # 270€ TVA sur 1620€ total
        
        print(f"  Service: {allocation_service:.2f}€")
        print(f"  Produit: {allocation_produit:.2f}€")
        print(f"  TVA: {allocation_tva:.2f}€")
        print(f"  Total: {allocation_service + allocation_produit + allocation_tva:.2f}€")
        
        print("\n📊 RÉPARTITION CORRECTE:")
        print("  Pour répartir un paiement, il faut utiliser les MONTANTS NETS individuels")
        print("  divisés par le TOTAL TTC FINAL")
        print("  ✅ Service: 900€ net / 1620€ total = 55.56%")
        print("  ✅ Produit: 450€ net / 1620€ total = 27.78%")
        print("  ✅ TVA: 270€ / 1620€ total = 16.67%")
        
    finally:
        session.close()

if __name__ == "__main__":
    analyser_reservation_test()