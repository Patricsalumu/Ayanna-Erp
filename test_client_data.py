#!/usr/bin/env python3
"""
Script pour vérifier que les données client sont bien enregistrées
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from ayanna_erp.modules.salle_fete.model.salle_fete import EventReservation, get_database_manager

def test_client_data():
    """Vérifier les données client dans les réservations"""
    db_manager = get_database_manager()
    session = db_manager.get_session()
    
    try:
        # Récupérer toutes les réservations
        reservations = session.query(EventReservation).all()
        
        print(f"🔍 {len(reservations)} réservation(s) trouvée(s) :\n")
        
        for i, reservation in enumerate(reservations, 1):
            print(f"--- Réservation {i} (ID: {reservation.id}) ---")
            print(f"Référence: {reservation.reference}")
            print(f"Date événement: {reservation.event_date}")
            print(f"Type: {reservation.event_type}")
            print(f"Statut: {reservation.status}")
            
            # Données client
            print(f"\n📋 Données client:")
            print(f"   - Client pré-enregistré ID: {reservation.partner_id}")
            print(f"   - Nom direct: '{reservation.client_nom}'")
            print(f"   - Prénom direct: '{reservation.client_prenom}'")
            print(f"   - Téléphone: '{reservation.client_telephone}'")
            print(f"   - Email: '{reservation.client_email}'")
            
            # Utiliser la méthode du modèle pour récupérer le nom complet
            print(f"   - Nom complet calculé: '{reservation.get_client_name()}'")
            print(f"   - Téléphone calculé: '{reservation.get_client_phone()}'")
            print(f"   - Email calculé: '{reservation.get_client_email()}'")
            
            print(f"\n💰 Données financières:")
            print(f"   - Total services: {reservation.total_services}€")
            print(f"   - Total produits: {reservation.total_products}€")
            print(f"   - Total général: {reservation.total_amount}€")
            
            # Vérifier les paiements
            if hasattr(reservation, 'payments') and reservation.payments:
                print(f"\n💳 Paiements ({len(reservation.payments)}):")
                for payment in reservation.payments:
                    print(f"   - {payment.amount}€ ({payment.payment_method}) - {payment.status}")
            else:
                print(f"\n💳 Aucun paiement")
            
            print("=" * 60)
        
        if not reservations:
            print("Aucune réservation trouvée.")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
    finally:
        db_manager.close_session()

if __name__ == "__main__":
    test_client_data()
