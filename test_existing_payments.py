#!/usr/bin/env python3
"""
Script pour tester avec des paiements existants dans la base
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import get_database_manager


def test_existing_payments():
    """Tester avec les paiements existants"""
    print("🧪 Test avec les paiements existants")
    print("=" * 50)
    
    try:
        db_manager = get_database_manager()
        session = db_manager.get_session()
        
        # Compter tous les paiements par pos_id via les réservations
        from ayanna_erp.modules.salle_fete.model.salle_fete import EventPayment, EventReservation
        
        query = session.query(
            EventReservation.pos_id,
            session.query(EventPayment).join(EventReservation).filter(
                EventReservation.pos_id == EventReservation.pos_id
            ).count().label('payment_count')
        ).distinct()
        
        # Approche plus simple : compter directement
        pos_payment_counts = {}
        
        # Récupérer tous les paiements avec leur pos_id via la réservation
        payments_with_pos = session.query(EventPayment, EventReservation.pos_id).join(EventReservation).all()
        
        for payment, pos_id in payments_with_pos:
            if pos_id not in pos_payment_counts:
                pos_payment_counts[pos_id] = 0
            pos_payment_counts[pos_id] += 1
        
        print(f"📊 Paiements par pos_id:")
        for pos_id, count in sorted(pos_payment_counts.items()):
            print(f"   Pos_id {pos_id}: {count} paiements")
        
        # Test du filtrage avec le contrôleur
        print(f"\n🔍 Test du filtrage avec PaiementController:")
        
        from ayanna_erp.modules.salle_fete.controller.paiement_controller import PaiementController
        
        for pos_id in sorted(pos_payment_counts.keys())[:3]:  # Tester les 3 premiers
            controller = PaiementController(pos_id=pos_id)
            
            # Récupérer toutes les réservations avec paiements pour ce pos_id
            reservations = controller.get_all_reservations()
            reservations_with_payments = [r for r in reservations if r.payments]
            total_payments = sum(len(r.payments) for r in reservations_with_payments)
            
            print(f"   Pos_id {pos_id}: {total_payments} paiements via contrôleur")
            
            # Vérifier la cohérence
            expected = pos_payment_counts.get(pos_id, 0)
            if total_payments == expected:
                print(f"      ✅ Cohérent avec la base de données")
            else:
                print(f"      ❌ Incohérent: attendu {expected}, obtenu {total_payments}")
        
        session.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_payments_by_date():
    """Tester le filtrage par date"""
    print(f"\n📅 Test du filtrage par date")
    print("=" * 30)
    
    try:
        db_manager = get_database_manager()
        session = db_manager.get_session()
        
        # Trouver les dates de paiements existants
        from ayanna_erp.modules.salle_fete.model.salle_fete import EventPayment
        from sqlalchemy import func
        
        payment_dates = session.query(
            func.date(EventPayment.payment_date).label('payment_date'),
            func.count(EventPayment.id).label('count')
        ).group_by(func.date(EventPayment.payment_date)).order_by('payment_date').all()
        
        print(f"📊 Dates avec paiements:")
        for date_obj, count in payment_dates:
            print(f"   {date_obj}: {count} paiements")
        
        # Tester avec une date qui a des paiements
        if payment_dates:
            test_date = payment_dates[0][0]  # Prendre la première date
            print(f"\n🧪 Test avec la date: {test_date}")
            
            from ayanna_erp.modules.salle_fete.controller.paiement_controller import PaiementController
            
            # Tester avec pos_id = 1
            controller = PaiementController(pos_id=1)
            payments = controller.get_payments_by_date_and_pos(test_date, 1)
            
            print(f"   💰 Paiements trouvés pour pos_id=1: {len(payments)}")
            
            if payments:
                print(f"   🔍 Vérification du premier paiement:")
                payment = payments[0]
                from ayanna_erp.modules.salle_fete.model.salle_fete import EventReservation
                reservation = session.query(EventReservation).filter_by(id=payment.reservation_id).first()
                if reservation:
                    print(f"      Paiement {payment.id} -> Réservation {reservation.id} (pos_id={reservation.pos_id})")
                    if reservation.pos_id == 1:
                        print(f"      ✅ Filtrage correct")
                    else:
                        print(f"      ❌ Filtrage incorrect!")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Test avec paiements existants")
    print("="*50)
    
    test1 = test_existing_payments()
    test2 = test_payments_by_date()
    
    if test1 and test2:
        print("\n🎉 Tests terminés avec succès!")
    else:
        print("\n❌ Certains tests ont échoué!")
    
    print("\n" + "="*50)