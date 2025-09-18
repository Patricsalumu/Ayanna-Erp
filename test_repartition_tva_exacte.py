#!/usr/bin/env python3
"""
Test de la nouvelle logique de répartition avec TVA
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.salle_fete.model.salle_fete import EventReservation, EventReservationService, EventReservationProduct, EventService, EventProduct
from ayanna_erp.modules.salle_fete.controller.reservation_controller import ReservationController

def test_repartition_avec_tva():
    """Test de la répartition avec TVA selon votre exemple"""
    print("=== Test de répartition avec TVA (selon votre exemple) ===")
    
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    try:
        # Utiliser une réservation existante et modifier temporairement la TVA
        reservation = session.query(EventReservation).first()
        if not reservation:
            print("❌ Aucune réservation trouvée")
            return
        
        # Sauvegarder les valeurs originales
        original_tax_rate = reservation.tax_rate
        original_total = reservation.total_amount
        
        # Modifier temporairement pour notre test
        reservation.tax_rate = 20.0
        reservation.total_amount = 1800.0
        session.commit()
        
        print(f"✅ Utilisation de la réservation ID {reservation.id}")
        print(f"   Modifiée pour: Total {reservation.total_amount}€ TTC, TVA {reservation.tax_rate}%")
        
        # Récupérer des services et produits existants
        service = session.query(EventService).first()
        product = session.query(EventProduct).first()
        
        if not service or not product:
            print("❌ Services ou produits manquants")
            return
        
        # Nettoyer les anciens items de cette réservation
        session.query(EventReservationService).filter_by(reservation_id=reservation.id).delete()
        session.query(EventReservationProduct).filter_by(reservation_id=reservation.id).delete()
        
        # Ajouter services pour 1300€ TTC total (2 services)
        service_item = EventReservationService(
            reservation_id=reservation.id,
            service_id=service.id,
            quantity=1,
            unit_price=1000.0,
            line_total=1000.0
        )
        session.add(service_item)
        
        service_item2 = EventReservationService(
            reservation_id=reservation.id,
            service_id=service.id,
            quantity=1,
            unit_price=300.0,
            line_total=300.0
        )
        session.add(service_item2)
        
        # Ajouter produits pour 500€ TTC
        product_item = EventReservationProduct(
            reservation_id=reservation.id,
            product_id=product.id,
            quantity=1,
            unit_price=500.0,
            line_total=500.0
        )
        session.add(product_item)
        
        session.commit()
        
        print(f"   Services: 1000€ + 300€ = 1300€ TTC")
        print(f"   Produits: 500€ TTC")
        print(f"   Total: 1800€ TTC")
        print(f"   TVA théorique: 1800€ - (1800€/1.20) = 1800€ - 1500€ = 300€")
        
        # Test de la répartition
        controller = ReservationController(pos_id=1)
        
        print(f"\n🧪 TEST 1: Premier paiement de 1000€")
        repartition1 = controller.calculer_repartition_paiement(reservation, 1000.0)
        
        print(f"\n📊 Résultats attendus vs obtenus:")
        print(f"   Services: devrait être ~{1300*1000/1800:.2f}€ -> obtenu: {sum(repartition1['services'].values()):.2f}€")
        print(f"   Produits: devrait être ~{500*1000/1800:.2f}€ -> obtenu: {sum(repartition1['produits'].values()):.2f}€")
        print(f"   TVA: devrait être ~{300*1000/1800:.2f}€ -> obtenu: {repartition1['tva']:.2f}€")
        
        print(f"\n🧪 TEST 2: Deuxième paiement de 800€")
        repartition2 = controller.calculer_repartition_paiement(reservation, 800.0)
        
        print(f"\n📊 Résultats attendus vs obtenus:")
        print(f"   Services: devrait être ~{1300*800/1800:.2f}€ -> obtenu: {sum(repartition2['services'].values()):.2f}€")
        print(f"   Produits: devrait être ~{500*800/1800:.2f}€ -> obtenu: {sum(repartition2['produits'].values()):.2f}€")
        print(f"   TVA: devrait être ~{300*800/1800:.2f}€ -> obtenu: {repartition2['tva']:.2f}€")
        
        # Total cumulé
        print(f"\n💰 CUMUL des 2 paiements (1800€):")
        total_services = sum(repartition1['services'].values()) + sum(repartition2['services'].values())
        total_produits = sum(repartition1['produits'].values()) + sum(repartition2['produits'].values())
        total_tva = repartition1['tva'] + repartition2['tva']
        
        print(f"   Services: {total_services:.2f}€ (devrait être 1300€)")
        print(f"   Produits: {total_produits:.2f}€ (devrait être 500€)")
        print(f"   TVA: {total_tva:.2f}€ (devrait être 300€)")
        print(f"   Total: {total_services + total_produits + total_tva:.2f}€ (devrait être 1800€)")
        
        # Vérification
        ecart_services = abs(total_services - 1300)
        ecart_produits = abs(total_produits - 500)
        ecart_tva = abs(total_tva - 300)
        
        if ecart_services < 0.01 and ecart_produits < 0.01 and ecart_tva < 0.01:
            print(f"\n🎉 ✅ SUCCÈS: La répartition est exacte!")
        else:
            print(f"\n⚠️  Écarts détectés:")
            print(f"    Services: {ecart_services:.2f}€")
            print(f"    Produits: {ecart_produits:.2f}€") 
            print(f"    TVA: {ecart_tva:.2f}€")
        
        # Nettoyage
        session.delete(reservation)
        session.commit()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    test_repartition_avec_tva()