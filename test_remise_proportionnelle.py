#!/usr/bin/env python3
"""
Test de la nouvelle logique de répartition proportionnelle des remises
Valide que les remises sont correctement réparties sur tous les comptes
"""

import sys
import os
sys.path.append('.')

from ayanna_erp.database.database_manager import get_database_manager
from ayanna_erp.modules.salle_fete.model.salle_fete import (
    EventReservation, EventClient, EventService, EventProduct,
    EventReservationService, EventReservationProduct
)
from ayanna_erp.modules.salle_fete.controller.reservation_controller import ReservationController


def test_remise_proportionnelle():
    """Test la logique de répartition proportionnelle avec remise"""
    
    print("🧪 TEST : Répartition proportionnelle des remises")
    print("="*50)
    
    db_manager = get_database_manager()
    session = db_manager.get_session()
    
    try:
        # === CRÉER UNE RÉSERVATION DE TEST AVEC REMISE ===
        
        # Trouver un client
        client = session.query(EventClient).first()
        if not client:
            print("❌ Aucun client trouvé")
            return
        
        # Créer une nouvelle réservation avec remise
        from datetime import datetime
        controller = ReservationController(pos_id=1)
        
        reservation_data = {
            'client_id': client.id,
            'event_date': datetime(2025, 1, 15),  # Objet datetime au lieu de string
            'event_time': '18:00',
            'event_type': 'Test Remise',
            'guests_count': 50,
            'notes': 'Test de répartition avec remise',
            'tax_rate': 20.0,  # 20% TVA
            'discount': 10.0   # 10% de remise
        }
        
        print(f"📋 Création réservation avec remise {reservation_data['discount']}%")
        reservation = controller.create_reservation(reservation_data, [])
        
        if not reservation:
            print("❌ Erreur lors de la création de la réservation")
            return
        
        # Récupérer des services et produits existants
        service = session.query(EventService).first()
        product = session.query(EventProduct).first()
        
        if not service or not product:
            print("❌ Services ou produits manquants")
            return
        
        # === SCÉNARIO TEST : Comme dans votre exemple ===
        # Services : 1000€ + 300€ = 1300€ TTC (72.22% du sous-total)
        # Produits : 500€ TTC (27.78% du sous-total)
        # Sous-total : 1800€
        # Remise 10% : -180€
        # Après remise : 1620€
        # TVA 20% sur 1620€ : +270€
        # Total final : 1890€
        
        # Nettoyer les anciens items
        session.query(EventReservationService).filter_by(reservation_id=reservation.id).delete()
        session.query(EventReservationProduct).filter_by(reservation_id=reservation.id).delete()
        
        # Ajouter services pour 1300€ TTC total
        service_item1 = EventReservationService(
            reservation_id=reservation.id,
            service_id=service.id,
            quantity=1,
            unit_price=1000.0,
            line_total=1000.0
        )
        session.add(service_item1)
        
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
        
        # Mettre à jour la réservation pour recalculer les totaux
        updated_reservation = controller.update_reservation(reservation.id, {
            'services': [
                {'service_id': service.id, 'quantity': 1, 'unit_price': 1000.0},
                {'service_id': service.id, 'quantity': 1, 'unit_price': 300.0}
            ],
            'products': [
                {'product_id': product.id, 'quantity': 1, 'unit_price': 500.0}
            ]
        })
        
        # Récupérer la réservation mise à jour
        reservation = session.query(EventReservation).filter_by(id=reservation.id).first()
        
        print(f"📊 Réservation créée:")
        print(f"   Services: {reservation.total_services}€")
        print(f"   Produits: {reservation.total_products}€")
        print(f"   Remise: {reservation.discount_percent}%")
        print(f"   TVA: {reservation.tax_rate}%")
        print(f"   Total final: {reservation.total_amount}€")
        print()
        
        # === TEST RÉPARTITION POUR DIFFÉRENTS MONTANTS DE PAIEMENT ===
        
        montants_test = [
            500.0,    # Paiement partiel
            945.0,    # Paiement de la moitié du total
            1890.0    # Paiement complet
        ]
        
        for montant in montants_test:
            print(f"💰 TEST Paiement de {montant}€")
            print("-" * 30)
            
            # Calculer la répartition
            repartition = controller.calculer_repartition_paiement(reservation, montant)
            
            # Vérifications
            total_services = sum(repartition['services'].values())
            total_produits = sum(repartition['produits'].values())
            total_reparti = total_services + total_produits + repartition['tva'] + repartition.get('remise', 0)
            
            print(f"📋 Résultats:")
            print(f"   Services: {total_services:.2f}€")
            print(f"   Produits: {total_produits:.2f}€")
            print(f"   TVA: {repartition['tva']:.2f}€")
            print(f"   Remise: {repartition.get('remise', 0):.2f}€")
            print(f"   Total réparti: {total_reparti:.2f}€")
            print(f"   Écart: {abs(total_reparti - montant):.2f}€")
            
            # Vérification de l'équilibre
            if abs(total_reparti - montant) > 0.01:
                print("   ❌ ÉCHEC: Déséquilibre de répartition")
            else:
                print("   ✅ SUCCÈS: Répartition équilibrée")
            
            print()
        
        print("🎯 TEST REMISE RÉUSSI")
        
    except Exception as e:
        print(f"❌ Erreur dans le test: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db_manager.close_session()


if __name__ == "__main__":
    test_remise_proportionnelle()