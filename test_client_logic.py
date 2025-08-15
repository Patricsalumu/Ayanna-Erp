#!/usr/bin/env python3
"""
Script de test pour vérifier la nouvelle logique de gestion des clients
dans les réservations de salle de fête
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from ayanna_erp.modules.salle_fete.model.salle_fete import get_database_manager, EventReservation, EventClient
from datetime import datetime

def test_client_logic():
    """Test de la logique client (pré-enregistré vs saisi directement)"""
    print("🧪 Test de la logique client dans les réservations")
    
    try:
        db_manager = get_database_manager()
        session = db_manager.get_session()
        
        # 1. Test avec client pré-enregistré
        print("\n1️⃣ Test avec client pré-enregistré")
        client = session.query(EventClient).first()
        if client:
            print(f"   Client trouvé: {client.nom} {client.prenom} - {client.telephone}")
            
            reservation1 = EventReservation(
                pos_id=1,
                partner_id=client.id,  # Client pré-enregistré
                reference="TEST001",
                event_date=datetime.now(),
                event_type="Test avec client pré-enregistré",
                guests_count=50
            )
            session.add(reservation1)
            session.flush()
            
            print(f"   Nom du client: {reservation1.get_client_name()}")
            print(f"   Téléphone: {reservation1.get_client_phone()}")
            print(f"   Email: {reservation1.get_client_email()}")
        
        # 2. Test avec client saisi directement
        print("\n2️⃣ Test avec client saisi directement")
        reservation2 = EventReservation(
            pos_id=1,
            partner_id=None,  # Pas de client pré-enregistré
            client_nom="Nouveau",
            client_prenom="Client",
            client_telephone="06.12.34.56.78",
            client_email="nouveau.client@example.com",
            reference="TEST002",
            event_date=datetime.now(),
            event_type="Test avec client nouveau",
            guests_count=30
        )
        session.add(reservation2)
        session.flush()
        
        print(f"   Nom du client: {reservation2.get_client_name()}")
        print(f"   Téléphone: {reservation2.get_client_phone()}")
        print(f"   Email: {reservation2.get_client_email()}")
        
        # 3. Test avec client mixte (pré-enregistré + infos supplémentaires)
        print("\n3️⃣ Test avec client mixte")
        if client:
            reservation3 = EventReservation(
                pos_id=1,
                partner_id=client.id,  # Client pré-enregistré
                client_telephone="06.99.88.77.66",  # Téléphone différent pour cet événement
                client_email="autre.email@example.com",  # Email différent
                reference="TEST003",
                event_date=datetime.now(),
                event_type="Test mixte",
                guests_count=100
            )
            session.add(reservation3)
            session.flush()
            
            print(f"   Nom du client: {reservation3.get_client_name()}")
            print(f"   Téléphone: {reservation3.get_client_phone()}")
            print(f"   Email: {reservation3.get_client_email()}")
        
        # 4. Lister toutes les réservations
        print("\n📋 Résumé de toutes les réservations:")
        reservations = session.query(EventReservation).all()
        for i, reservation in enumerate(reservations, 1):
            print(f"   {i}. {reservation.reference} - {reservation.get_client_name()}")
            print(f"      📞 {reservation.get_client_phone()}")
            print(f"      📧 {reservation.get_client_email()}")
            print(f"      🎉 {reservation.event_type}")
        
        session.rollback()  # Ne pas sauvegarder les tests
        print("\n✅ Test terminé avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur pendant le test: {e}")
        session.rollback()
        
    finally:
        db_manager.close_session()

if __name__ == "__main__":
    test_client_logic()
