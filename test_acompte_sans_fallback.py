#!/usr/bin/env python3
"""
Test de création d'acompte pour vérifier que le fallback ne s'exécute plus
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.salle_fete.model.salle_fete import EventReservation
from ayanna_erp.modules.salle_fete.controller.reservation_controller import ReservationController

def test_acompte_sans_fallback():
    """Test d'acompte pour vérifier que la répartition fonctionne"""
    print("=== Test acompte sans fallback ===")
    
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    try:
        # 1. Créer une nouvelle réservation de test
        print("1. Création d'une réservation de test...")
        
        reservation = EventReservation(
            pos_id=1,
            client_nom="Test",
            client_prenom="Fallback", 
            client_telephone="0123456789",
            client_email="test@test.com",
            event_date="2024-01-01",
            start_time="18:00",
            end_time="23:00",
            number_of_guests=10,
            event_type="Test",
            total_amount=200.0,
            deposit_amount=50.0,
            tax_rate=20.0,
            status="confirmed"
        )
        
        session.add(reservation)
        session.flush()  # Pour avoir l'ID
        
        print(f"✅ Réservation créée: ID {reservation.id}, Total: {reservation.total_amount}€")
        
        # 2. Ajouter des services à cette réservation
        from ayanna_erp.modules.salle_fete.model.salle_fete import EventReservationService, EventService
        
        # Récupérer un service existant
        service = session.query(EventService).first()
        if service:
            service_item = EventReservationService(
                reservation_id=reservation.id,
                service_id=service.id,
                quantity=1,
                unit_price=150.0,
                line_total=150.0
            )
            session.add(service_item)
            print(f"✅ Service ajouté: {service.name} - 150€")
        
        # Ajouter un produit
        from ayanna_erp.modules.salle_fete.model.salle_fete import EventReservationProduct, EventProduct
        
        product = session.query(EventProduct).first()
        if product:
            product_item = EventReservationProduct(
                reservation_id=reservation.id,
                product_id=product.id,
                quantity=1,
                unit_price=50.0,
                line_total=50.0
            )
            session.add(product_item)
            print(f"✅ Produit ajouté: {product.name} - 50€")
        
        session.commit()
        
        # 3. Tester la création d'acompte
        print(f"\n2. Test de création d'acompte avec répartition...")
        
        controller = ReservationController(pos_id=1)
        
        try:
            success = controller.create_deposit(reservation.id, 100.0)
            
            if success:
                print(f"✅ Acompte créé avec succès!")
                print(f"   Si vous voyez '📊 X écritures comptables créées avec répartition', c'est que ça marche!")
                print(f"   Si vous voyez '⚠️ Fallback: création d'écriture simple', il y a encore un problème.")
            else:
                print(f"❌ Échec de création d'acompte")
        
        except Exception as e:
            print(f"❌ Erreur lors de la création d'acompte: {e}")
            import traceback
            traceback.print_exc()
        
        # 4. Nettoyer la réservation test
        print(f"\n3. Nettoyage...")
        session.delete(reservation)
        session.commit()
        print(f"✅ Réservation test supprimée")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    test_acompte_sans_fallback()