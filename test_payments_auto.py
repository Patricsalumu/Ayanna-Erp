#!/usr/bin/env python
"""
Test de vérification des paiements automatiques
"""

import sys
import os
from datetime import datetime

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import get_database_manager

def test_payments_and_reservations():
    """Tester et afficher les réservations et paiements en base"""
    try:
        print("🔍 Vérification des réservations et paiements...")
        
        db_manager = get_database_manager()
        session = db_manager.get_session()
        
        from ayanna_erp.modules.salle_fete.model.salle_fete import EventReservation, EventPayment
        
        # Récupérer les réservations
        reservations = session.query(EventReservation).all()
        print(f"\n📋 {len(reservations)} réservation(s) en base :")
        
        for i, reservation in enumerate(reservations, 1):
            print(f"\n--- Réservation #{i} ---")
            print(f"   ID: {reservation.id}")
            print(f"   Référence: {reservation.reference}")
            print(f"   Client: {reservation.partner_id}")
            print(f"   Montant total: {reservation.total_amount}€")
            print(f"   POS ID: {reservation.pos_id}")
            
            # Vérifier les paiements associés
            payments = session.query(EventPayment).filter(
                EventPayment.reservation_id == reservation.id
            ).all()
            
            if payments:
                print(f"   💰 {len(payments)} paiement(s) :")
                for j, payment in enumerate(payments, 1):
                    print(f"      Paiement #{j}: {payment.amount}€ ({payment.payment_type}) - {payment.status}")
                    print(f"      Date: {payment.payment_date}")
                    print(f"      Méthode: {payment.payment_method}")
                    print(f"      Notes: {payment.notes}")
            else:
                print("   💰 Aucun paiement associé")
        
        # Statistiques globales
        total_payments = session.query(EventPayment).count()
        print(f"\n📊 Total des paiements en base: {total_payments}")
        
        session.close()
        
    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_payments_and_reservations()
