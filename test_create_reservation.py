#!/usr/bin/env python
"""
Test de création d'une réservation pour vérifier que la sauvegarde fonctionne
"""

import sys
import os
from datetime import datetime

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import get_database_manager
from ayanna_erp.modules.salle_fete.controller.reservation_controller import ReservationController

def test_create_reservation():
    """Tester la création d'une réservation"""
    try:
        print("🧪 Test de création d'une réservation...")
        
        # Données de test
        reservation_data = {
            'reference': 'TEST001',
            'event_date': datetime(2025, 8, 20, 14, 0),  # 20 août 2025, 14h00
            'event_type': 'Test',
            'guests_count': 50,
            'status': 'En attente',
            'notes': 'Réservation de test',
            'discount_percent': 0.0,
            'tax_rate': 20.0,
            'created_by': 1
        }
        
        services_data = []  # Aucun service pour ce test
        products_data = []  # Aucun produit pour ce test
        
        # Créer la réservation
        controller = ReservationController()
        result = controller.create_reservation(reservation_data, services_data, products_data)
        
        if result:
            print(f"✅ Réservation créée avec succès ! ID: {result.id}")
            print(f"   Référence: {result.reference}")
            print(f"   Type: {result.event_type}")
            print(f"   Date: {result.event_date}")
            print(f"   Invités: {result.guests_count}")
            print(f"   Statut: {result.status}")
            
            # Vérifier en base
            from ayanna_erp.modules.salle_fete.model.salle_fete import EventReservation
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            # Compter les réservations
            count = session.query(EventReservation).count()
            print(f"📊 Total réservations en base : {count}")
            
            session.close()
            
        else:
            print("❌ Échec de la création de la réservation")
        
    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_create_reservation()
