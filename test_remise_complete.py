#!/usr/bin/env python3
"""
Test de la création d'écriture de remise
"""
import sys
sys.path.append(r'c:\Ayanna ERP\Ayanna-Erp')

def test_creation_reservation_avec_remise():
    """Test de création de réservation avec remise"""
    try:
        print("🧪 TEST : Création de réservation avec écriture de remise")
        print("=" * 55)
        
        from ayanna_erp.database.database_manager import DatabaseManager
        from ayanna_erp.modules.salle_fete.controller.reservation_controller import ReservationController
        
        # Initialiser le contrôleur
        controller = ReservationController()
        controller.pos_id = 1
        
        # Données de test avec remise
        reservation_data = {
            'client_nom': 'Test',
            'client_prenom': 'Remise',
            'client_telephone': '123456789',
            'event_date': '2026-01-15',
            'event_time': '18:00',
            'event_type': 'Mariage',
            'duration': 6,
            'guest_count': 100,
            'services': [
                {'service_id': 1, 'quantity': 1, 'unit_price': 1000.0}
            ],
            'products': [
                {'product_id': 1, 'quantity': 1, 'unit_price': 500.0}
            ],
            'discount_percent': 20.0,  # 20% de remise
            'tax_rate': 20.0,         # 20% TVA
            'down_payment': 1440.0    # Paiement total
        }
        
        print(f"📋 Création réservation avec remise {reservation_data['discount_percent']}%")
        print(f"  Services: {sum(s['unit_price'] * s['quantity'] for s in reservation_data['services'])}€")
        print(f"  Produits: {sum(p['unit_price'] * p['quantity'] for p in reservation_data['products'])}€")
        print(f"  Acompte: {reservation_data['down_payment']}€")
        
        # Créer la réservation
        result = controller.create_reservation(reservation_data)
        
        if result:
            print("✅ Réservation créée avec succès")
            print("📊 Vérifiez dans les logs les écritures comptables créées")
            print("   On doit voir:")
            print("   - Débit Caisse: 1440€")
            print("   - Crédit Services: 800€")
            print("   - Crédit Produits: 400€") 
            print("   - Crédit TVA: 240€")
            print("   - Débit Remise: 300€")
            print("\n🎯 TOTAL DÉBITS = TOTAL CRÉDITS = 1740€")
        else:
            print("❌ Erreur lors de la création")
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_creation_reservation_avec_remise()