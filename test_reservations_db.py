#!/usr/bin/env python
"""
Test de vérification des réservations en base de données
"""

import sys
import os
from datetime import datetime

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import get_database_manager
from ayanna_erp.modules.salle_fete.controller.reservation_controller import ReservationController

def test_reservations_in_db():
    """Tester et afficher les réservations en base"""
    try:
        print("🔍 Vérification des réservations en base de données...")
        
        # Récupérer le contrôleur
        reservation_controller = ReservationController()
        
        # Connecter le signal pour recevoir les réservations
        def on_reservations_received(reservations):
            if reservations:
                print(f"✅ {len(reservations)} réservation(s) trouvée(s) en base :")
                for i, reservation in enumerate(reservations, 1):
                    print(f"\n📋 Réservation #{i}:")
                    print(f"   ID: {reservation.id}")
                    print(f"   Client: {reservation.client_name}")
                    print(f"   Date/Heure: {reservation.event_datetime}")
                    print(f"   Type: {reservation.event_type}")
                    print(f"   Invités: {reservation.guests_count}")
                    print(f"   Total: {reservation.total_amount}€")
                    print(f"   Statut: {reservation.status}")
                    print(f"   Créée le: {reservation.created_at}")
            else:
                print("❌ Aucune réservation trouvée en base de données")
                print("💡 Créez une réservation via l'interface pour tester")
        
        # Connecter le signal (temporairement)
        reservation_controller.reservations_loaded.connect(on_reservations_received)
        
        # Récupérer toutes les réservations
        reservation_controller.get_all_reservations()
        
        # Note: Dans un contexte réel, il faudrait attendre le signal
        # Pour ce test, on fait une vérification directe
        
    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_reservations_in_db()
