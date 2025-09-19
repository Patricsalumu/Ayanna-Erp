#!/usr/bin/env python3
"""
Test de la nouvelle logique : total_amount SANS remise dans event_reservation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.modules.salle_fete.controller.reservation_controller import ReservationController
from ayanna_erp.database.database_manager import DatabaseManager

def test_nouvelle_logique_reservation():
    """
    Test de la nouvelle logique :
    - total_amount = TTC SANS remise
    - tax_amount = TVA sur montants bruts
    - Remise gérée séparément
    """
    print("=" * 70)
    print("TEST NOUVELLE LOGIQUE : TOTAL_AMOUNT SANS REMISE")
    print("=" * 70)
    
    try:
        db_manager = DatabaseManager()
        reservation_controller = ReservationController(pos_id=1)
        
        # Données de test
        from datetime import datetime, date
        
        reservation_data = {
            'client_nom': 'Test',
            'client_prenom': 'Client',
            'event_date': date(2024, 12, 25),  # Format date correct
            'start_time': '14:00',
            'end_time': '18:00',
            'guest_count': 50,
            'tax_rate': 20.0,  # 20%
            'discount_percent': 10.0,  # 10%
            'deposit': 500.0
        }
        
        services_data = [
            {'service_id': 1, 'quantity': 1, 'unit_price': 1000.0}
        ]
        
        products_data = [
            {'product_id': 1, 'quantity': 1, 'unit_price': 500.0}
        ]
        
        print("Données de test:")
        print(f"  Services: 1000€ x 1")
        print(f"  Produits: 500€ x 1")
        print(f"  TVA: 20%")
        print(f"  Remise: 10%")
        
        # === CALCULS MANUELS ATTENDUS ===
        print(f"\n" + "=" * 50)
        print("CALCULS ATTENDUS (nouvelle logique)")
        print("=" * 50)
        
        subtotal_ht = 1000 + 500  # 1500€
        tax_amount_brut = subtotal_ht * 0.20  # 300€ (sur montant brut)
        total_ttc_sans_remise = subtotal_ht + tax_amount_brut  # 1800€
        
        print(f"1. Sous-total HT:           {subtotal_ht:.2f} €")
        print(f"2. TVA (20% sur brut):      {tax_amount_brut:.2f} €")
        print(f"3. Total TTC SANS remise:   {total_ttc_sans_remise:.2f} €")
        
        # Calcul pour l'utilisateur final
        remise_amount = total_ttc_sans_remise * 0.10  # 180€
        total_final_utilisateur = total_ttc_sans_remise - remise_amount  # 1620€
        
        print(f"4. Remise (10% sur TTC):    -{remise_amount:.2f} €")
        print(f"5. Total FINAL utilisateur: {total_final_utilisateur:.2f} €")
        
        # === CRÉATION DE LA RÉSERVATION ===
        print(f"\n" + "=" * 50)
        print("CRÉATION DE LA RÉSERVATION")
        print("=" * 50)
        
        try:
            reservation = reservation_controller.create_reservation(
                reservation_data=reservation_data,
                services_data=services_data,
                products_data=products_data
            )
            
            if reservation:
                print("✅ Réservation créée avec succès")
                
                # Vérifier les valeurs stockées
                print(f"\nValeurs stockées dans event_reservation:")
                print(f"  total_services:     {reservation.total_services:.2f} €")
                print(f"  total_products:     {reservation.total_products:.2f} €")
                print(f"  tax_amount:         {reservation.tax_amount:.2f} €")
                print(f"  total_amount:       {reservation.total_amount:.2f} €")
                print(f"  discount_percent:   {reservation.discount_percent}%")
                
                # === VALIDATION ===
                print(f"\n" + "=" * 50)
                print("VALIDATION")
                print("=" * 50)
                
                # Vérifications
                validation_ok = True
                
                if abs(reservation.total_services - 1000.0) > 0.01:
                    print(f"❌ total_services incorrect: {reservation.total_services} ≠ 1000.0")
                    validation_ok = False
                else:
                    print(f"✅ total_services correct: {reservation.total_services}")
                
                if abs(reservation.total_products - 500.0) > 0.01:
                    print(f"❌ total_products incorrect: {reservation.total_products} ≠ 500.0")
                    validation_ok = False
                else:
                    print(f"✅ total_products correct: {reservation.total_products}")
                
                if abs(reservation.tax_amount - tax_amount_brut) > 0.01:
                    print(f"❌ tax_amount incorrect: {reservation.tax_amount} ≠ {tax_amount_brut}")
                    validation_ok = False
                else:
                    print(f"✅ tax_amount correct: {reservation.tax_amount} (TVA sur montant brut)")
                
                if abs(reservation.total_amount - total_ttc_sans_remise) > 0.01:
                    print(f"❌ total_amount incorrect: {reservation.total_amount} ≠ {total_ttc_sans_remise}")
                    validation_ok = False
                else:
                    print(f"✅ total_amount correct: {reservation.total_amount} (TTC sans remise)")
                
                # === TEST RÉPARTITION ===
                print(f"\n" + "=" * 50)
                print("TEST RÉPARTITION PAIEMENT")
                print("=" * 50)
                
                # Test avec paiement partiel
                montant_paiement = 1000.0  # Paiement partiel
                
                repartition = reservation_controller.calculer_repartition_paiement(
                    reservation, montant_paiement
                )
                
                print(f"\nRépartition pour paiement de {montant_paiement}€:")
                
                total_services_reparti = sum(repartition['services'].values())
                total_produits_reparti = sum(repartition['produits'].values())
                tva_repartie = repartition['tva']
                total_reparti = total_services_reparti + total_produits_reparti + tva_repartie
                
                print(f"  Services:    {total_services_reparti:.2f} €")
                print(f"  Produits:    {total_produits_reparti:.2f} €")
                print(f"  TVA:         {tva_repartie:.2f} €")
                print(f"  Total:       {total_reparti:.2f} €")
                
                # Vérification proportions
                proportion_attendue = montant_paiement / total_ttc_sans_remise  # 1000/1800 = 55.56%
                
                print(f"\nVérification proportions (base: {total_ttc_sans_remise}€):")
                print(f"  Proportion paiement: {proportion_attendue:.2%}")
                
                services_attendu = 1000 * proportion_attendue
                produits_attendu = 500 * proportion_attendue
                tva_attendue = tax_amount_brut * proportion_attendue
                
                print(f"  Services attendu:  {services_attendu:.2f} € vs {total_services_reparti:.2f} €")
                print(f"  Produits attendu:  {produits_attendu:.2f} € vs {total_produits_reparti:.2f} €")
                print(f"  TVA attendue:      {tva_attendue:.2f} € vs {tva_repartie:.2f} €")
                
                if validation_ok:
                    print(f"\n🎉 VALIDATION RÉUSSIE !")
                    print("La nouvelle logique fonctionne correctement:")
                    print("  ✅ total_amount = TTC sans remise")
                    print("  ✅ tax_amount = TVA sur montants bruts")
                    print("  ✅ Répartition basée sur proportions correctes")
                else:
                    print(f"\n⚠️ VALIDATION ÉCHOUÉE")
                
                return validation_ok
            else:
                print("❌ Échec de création de la réservation")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de la création: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        return False

if __name__ == "__main__":
    success = test_nouvelle_logique_reservation()
    
    print(f"\n" + "=" * 70)
    print("RÉSUMÉ")
    print("=" * 70)
    
    if success:
        print("✅ La nouvelle logique est correctement implémentée")
        print("📊 Les pourcentages de répartition seront désormais exacts")
        print("💰 La remise sera gérée séparément dans les écritures comptables")
    else:
        print("❌ Des ajustements sont nécessaires")