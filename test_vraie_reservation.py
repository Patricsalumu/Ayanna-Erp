#!/usr/bin/env python3
"""
Test avec une vraie réservation existante
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.salle_fete.model.salle_fete import EventReservation, EventService, EventProduct
from ayanna_erp.modules.salle_fete.controller.reservation_controller import ReservationController

def test_vraie_reservation():
    """Test avec une vraie réservation"""
    print("=== Test avec une vraie réservation ===")
    
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    try:
        # 1. Récupérer une réservation existante
        print("\n1. Recherche d'une réservation existante...")
        reservation = session.query(EventReservation).first()
        
        if not reservation:
            print("   ❌ Aucune réservation trouvée")
            return
        
        print(f"   ✅ Réservation trouvée: ID {reservation.id}")
        print(f"      Client: {reservation.client_nom} {reservation.client_prenom}")
        print(f"      Total: {reservation.total_amount}€")
        print(f"      Taux TVA: {reservation.tax_rate}%")
        
        # 2. Vérifier les services de la réservation
        print(f"\n2. Services de la réservation:")
        if hasattr(reservation, 'services') and reservation.services:
            for i, service_item in enumerate(reservation.services):
                service = service_item.service if hasattr(service_item, 'service') else None
                if service:
                    account_id = getattr(service, 'account_id', 'NON DÉFINI')
                    print(f"   - Service {i+1}: {service.name}")
                    print(f"     Prix unitaire: {service_item.unit_price}€")
                    print(f"     Quantité: {service_item.quantity}")
                    print(f"     Total ligne: {service_item.line_total}€")
                    print(f"     Compte comptable: {account_id}")
                else:
                    print(f"   - Service {i+1}: PROBLÈME - pas d'objet service")
        else:
            print("   ❌ Aucun service trouvé")
        
        # 3. Vérifier les produits de la réservation
        print(f"\n3. Produits de la réservation:")
        if hasattr(reservation, 'products') and reservation.products:
            for i, product_item in enumerate(reservation.products):
                product = product_item.product if hasattr(product_item, 'product') else None
                if product:
                    account_id = getattr(product, 'account_id', 'NON DÉFINI')
                    print(f"   - Produit {i+1}: {product.name}")
                    print(f"     Prix unitaire: {product_item.unit_price}€")
                    print(f"     Quantité: {product_item.quantity}")
                    print(f"     Total ligne: {product_item.line_total}€")
                    print(f"     Compte comptable: {account_id}")
                else:
                    print(f"   - Produit {i+1}: PROBLÈME - pas d'objet produit")
        else:
            print("   ❌ Aucun produit trouvé")
        
        # 4. Tester la répartition si possible
        if hasattr(reservation, 'services') and reservation.services:
            print(f"\n4. Test de répartition...")
            controller = ReservationController(pos_id=1)
            
            montant_test = 100.0  # Test avec 100€
            
            try:
                repartition = controller.calculer_repartition_paiement(reservation, montant_test)
                print(f"   Répartition pour {montant_test}€:")
                print(f"   - Services: {repartition['services']}")
                print(f"   - Produits: {repartition['produits']}")
                print(f"   - TVA: {repartition['tva']:.2f}€")
                
                total_reparti = sum(repartition['services'].values()) + sum(repartition['produits'].values()) + repartition['tva']
                print(f"   - Total réparti: {total_reparti:.2f}€")
                
                if abs(total_reparti - montant_test) < 0.01:
                    print(f"   ✅ Répartition équilibrée")
                else:
                    print(f"   ❌ Déséquilibre détecté")
                    
            except Exception as e:
                print(f"   ❌ Erreur lors du calcul: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n✅ Test terminé")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_vraie_reservation()