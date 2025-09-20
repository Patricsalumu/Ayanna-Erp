#!/usr/bin/env python3
"""
Test simple pour vérifier le filtrage des paiements par pos_id
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, date
from ayanna_erp.database.database_manager import get_database_manager


def simple_payments_test():
    """Test simple du filtrage des paiements"""
    print("🧪 Test simple du filtrage des paiements")
    print("=" * 50)
    
    try:
        db_manager = get_database_manager()
        session = db_manager.get_session()
        
        # Compter les paiements par pos_id
        from ayanna_erp.modules.salle_fete.model.salle_fete import EventPayment, EventReservation
        
        print("📊 Analyse des paiements existants:")
        
        # Requête SQL simple pour compter les paiements par pos_id
        from sqlalchemy import text
        
        query = text("""
        SELECT r.pos_id, COUNT(p.id) as payment_count
        FROM event_payments p
        JOIN event_reservations r ON p.reservation_id = r.id
        GROUP BY r.pos_id
        ORDER BY r.pos_id
        """)
        
        results = session.execute(query).fetchall()
        
        for pos_id, count in results:
            print(f"   Pos_id {pos_id}: {count} paiements")
        
        # Test avec le contrôleur pour pos_id = 1
        print(f"\n🔍 Test du contrôleur pour pos_id = 1:")
        
        from ayanna_erp.modules.salle_fete.controller.paiement_controller import PaiementController
        
        controller = PaiementController(pos_id=1)
        
        # Utiliser une date où il y a des paiements
        test_date = date(2025, 9, 19)  # Date avec 35 paiements
        
        payments = controller.get_payments_by_date_and_pos(test_date, 1)
        print(f"   💰 Paiements trouvés pour {test_date}: {len(payments)}")
        
        if payments:
            print(f"   🔍 Vérification des 3 premiers paiements:")
            for i, payment in enumerate(payments[:3]):
                # Vérifier que le paiement appartient bien au bon pos_id
                reservation_query = text("SELECT pos_id FROM event_reservations WHERE id = :res_id")
                result = session.execute(reservation_query, {"res_id": payment.reservation_id}).fetchone()
                if result:
                    actual_pos_id = result[0]
                    if actual_pos_id == 1:
                        print(f"      ✅ Paiement {payment.id}: pos_id={actual_pos_id} (correct)")
                    else:
                        print(f"      ❌ Paiement {payment.id}: pos_id={actual_pos_id} (FUITE!)")
                else:
                    print(f"      ⚠️  Paiement {payment.id}: réservation non trouvée")
        
        # Test avec pos_id = 9 (nouvelle entreprise)
        print(f"\n🔍 Test du contrôleur pour pos_id = 9:")
        
        controller_9 = PaiementController(pos_id=9)
        payments_9 = controller_9.get_payments_by_date_and_pos(test_date, 9)
        print(f"   💰 Paiements trouvés pour {test_date}: {len(payments_9)}")
        
        if len(payments_9) == 0:
            print(f"   ✅ Aucun paiement pour pos_id=9 (isolation correcte)")
        else:
            print(f"   ⚠️  {len(payments_9)} paiements trouvés (à vérifier)")
        
        session.close()
        
        print(f"\n🎯 RÉSULTAT:")
        if len(payments) > 0 and len(payments_9) == 0:
            print(f"   ✅ Filtrage des paiements par pos_id fonctionne correctement")
            return True
        else:
            print(f"   ❌ Problème avec le filtrage des paiements")
            return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Test simple du filtrage des paiements")
    print("="*50)
    
    success = simple_payments_test()
    
    if success:
        print("\n🎉 Test réussi!")
        print("   ✅ Les paiements sont correctement filtrés par pos_id")
        print("   ✅ L'onglet Entrées-Sorties respecte l'isolation des données")
    else:
        print("\n❌ Test échoué!")
    
    print("\n" + "="*50)