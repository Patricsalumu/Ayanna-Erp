#!/usr/bin/env python3
"""
Test de l'affichage des détails complets de réservation
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from ayanna_erp.modules.salle_fete.model.salle_fete import get_database_manager
from ayanna_erp.modules.salle_fete.controller.reservation_controller import ReservationController
from datetime import datetime

def test_reservation_details():
    """Tester la récupération complète des détails de réservation"""
    
    print("🔍 Test des détails de réservation...")
    
    # Créer le contrôleur
    controller = ReservationController(pos_id=1)
    
    # Récupérer toutes les réservations
    reservations = controller.get_all_reservations()
    print(f"📋 {len(reservations)} réservations trouvées")
    
    if reservations:
        # Tester la première réservation
        first_reservation = reservations[0]
        reservation_id = first_reservation.id
        
        print(f"\n🎯 Test des détails pour la réservation #{reservation_id}")
        
        # Récupérer les détails complets
        details = controller.get_reservation(reservation_id)
        
        if details:
            print("✅ Détails récupérés avec succès:")
            print(f"   - Client: {details['client_nom']}")
            print(f"   - Téléphone: {details['client_telephone']}")
            print(f"   - Thème: {details['theme']}")
            print(f"   - Type: {details['event_type']}")
            print(f"   - Invités: {details['guests_count']}")
            print(f"   - Date événement: {details['event_date']}")
            print(f"   - Statut: {details['status']}")
            print(f"   - Notes: {details['notes']}")
            print(f"   - Total: {details['total_amount']:.2f}€")
            print(f"   - Payé: {details['total_paid']:.2f}€")
            print(f"   - Restant: {details['remaining_amount']:.2f}€")
            print(f"   - Services: {len(details['services'])} service(s)")
            print(f"   - Produits: {len(details['products'])} produit(s)")
            print(f"   - Paiements: {len(details['payments'])} paiement(s)")
            
            # Afficher les services en détail
            if details['services']:
                print("\n🛠️ Services sélectionnés:")
                for service in details['services']:
                    print(f"   • {service['name']} - Qté: {service['quantity']} - Prix: {service['unit_price']:.2f}€ - Total: {service['line_total']:.2f}€")
            
            # Afficher les produits en détail
            if details['products']:
                print("\n📦 Produits sélectionnés:")
                for product in details['products']:
                    print(f"   • {product['name']} - Qté: {product['quantity']} - Prix: {product['unit_price']:.2f}€ - Total: {product['line_total']:.2f}€")
            
            # Afficher les paiements en détail
            if details['payments']:
                print("\n💰 Paiements:")
                for payment in details['payments']:
                    print(f"   • {payment['amount']:.2f}€ - {payment['payment_method']} - {payment['status']} - {payment['payment_date']}")
            
            return True
        else:
            print("❌ Impossible de récupérer les détails")
            return False
    else:
        print("ℹ️ Aucune réservation trouvée pour tester")
        return True

if __name__ == "__main__":
    success = test_reservation_details()
    sys.exit(0 if success else 1)
