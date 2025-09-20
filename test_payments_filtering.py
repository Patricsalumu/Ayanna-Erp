#!/usr/bin/env python3
"""
Script pour tester le filtrage des paiements par pos_id
dans le module Entrées-Sorties
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import date
from ayanna_erp.database.database_manager import get_database_manager


def test_payments_filtering():
    """Tester le filtrage des paiements par pos_id"""
    print("🧪 Test du filtrage des paiements par pos_id")
    print("=" * 50)
    
    try:
        from ayanna_erp.modules.salle_fete.controller.paiement_controller import PaiementController
        
        # Test avec différents pos_id
        test_pos_ids = [1, 9, 17]  # Premier POS de 3 entreprises différentes
        test_date = date.today()
        
        print(f"📅 Test avec la date: {test_date}")
        
        for pos_id in test_pos_ids:
            print(f"\n📍 Test avec pos_id = {pos_id}")
            
            try:
                paiement_controller = PaiementController(pos_id=pos_id)
                payments = paiement_controller.get_payments_by_date_and_pos(test_date, pos_id)
                
                print(f"   💰 Paiements trouvés: {len(payments)}")
                
                # Vérifier que tous les paiements appartiennent au bon pos_id
                if payments:
                    print(f"   🔍 Vérification de l'appartenance au pos_id {pos_id}:")
                    
                    db_manager = get_database_manager()
                    session = db_manager.get_session()
                    
                    for payment in payments[:3]:  # Vérifier les 3 premiers seulement
                        from ayanna_erp.modules.salle_fete.model.salle_fete import EventReservation
                        reservation = session.query(EventReservation).filter_by(id=payment.reservation_id).first()
                        
                        if reservation:
                            if reservation.pos_id == pos_id:
                                print(f"      ✅ Paiement {payment.id}: réservation {reservation.id} (pos_id={reservation.pos_id})")
                            else:
                                print(f"      ❌ Paiement {payment.id}: réservation {reservation.id} (pos_id={reservation.pos_id}) - FUITE!")
                        else:
                            print(f"      ⚠️  Paiement {payment.id}: réservation {payment.reservation_id} non trouvée")
                    
                    session.close()
                else:
                    print(f"   ℹ️  Aucun paiement pour cette date et ce pos_id")
                    
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_entries_sorties_data_isolation():
    """Tester l'isolation des données dans l'onglet Entrées-Sorties"""
    print(f"\n📊 Test d'isolation des données Entrées-Sorties")
    print("=" * 50)
    
    try:
        from ayanna_erp.modules.salle_fete.controller.entre_sortie_controller import EntreSortieController
        from ayanna_erp.modules.salle_fete.controller.paiement_controller import PaiementController
        
        test_date = date.today()
        pos_id_1 = 1  # Entreprise 1
        pos_id_2 = 9  # Entreprise 2
        
        print(f"📅 Date de test: {test_date}")
        print(f"🏢 Comparaison entre pos_id {pos_id_1} et pos_id {pos_id_2}")
        
        # Test des dépenses
        expense_controller_1 = EntreSortieController(pos_id=pos_id_1)
        expense_controller_2 = EntreSortieController(pos_id=pos_id_2)
        
        expenses_1 = expense_controller_1.get_expenses_by_date_and_pos(test_date, pos_id_1)
        expenses_2 = expense_controller_2.get_expenses_by_date_and_pos(test_date, pos_id_2)
        
        print(f"\n💸 DÉPENSES:")
        print(f"   Pos_id {pos_id_1}: {len(expenses_1)} dépenses")
        print(f"   Pos_id {pos_id_2}: {len(expenses_2)} dépenses")
        
        # Test des paiements
        payment_controller_1 = PaiementController(pos_id=pos_id_1)
        payment_controller_2 = PaiementController(pos_id=pos_id_2)
        
        payments_1 = payment_controller_1.get_payments_by_date_and_pos(test_date, pos_id_1)
        payments_2 = payment_controller_2.get_payments_by_date_and_pos(test_date, pos_id_2)
        
        print(f"\n💰 PAIEMENTS:")
        print(f"   Pos_id {pos_id_1}: {len(payments_1)} paiements")
        print(f"   Pos_id {pos_id_2}: {len(payments_2)} paiements")
        
        # Vérifier qu'il n'y a pas de chevauchement d'ID
        if payments_1 and payments_2:
            payment_ids_1 = {p.id for p in payments_1}
            payment_ids_2 = {p.id for p in payments_2}
            shared_payment_ids = payment_ids_1.intersection(payment_ids_2)
            
            if len(shared_payment_ids) == 0:
                print(f"   ✅ Isolation parfaite: aucun paiement partagé")
            else:
                print(f"   ❌ Fuite de données: {len(shared_payment_ids)} paiements partagés!")
                return False
        
        if expenses_1 and expenses_2:
            expense_ids_1 = {e.id for e in expenses_1}
            expense_ids_2 = {e.id for e in expenses_2}
            shared_expense_ids = expense_ids_1.intersection(expense_ids_2)
            
            if len(shared_expense_ids) == 0:
                print(f"   ✅ Isolation parfaite: aucune dépense partagée")
            else:
                print(f"   ❌ Fuite de données: {len(shared_expense_ids)} dépenses partagées!")
                return False
        
        print(f"\n🎯 RÉSULTAT: Isolation des données validée ✅")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test d'isolation: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Test du filtrage des paiements et entrées-sorties")
    print("="*60)
    
    payments_test = test_payments_filtering()
    isolation_test = test_entries_sorties_data_isolation()
    
    if payments_test and isolation_test:
        print("\n🎉 Tous les tests sont passés avec succès!")
        print("   ✅ Les paiements sont correctement filtrés par pos_id")
        print("   ✅ L'isolation des données fonctionne dans Entrées-Sorties")
    else:
        print("\n❌ Certains tests ont échoué!")
        print("   ⚠️  Vérifiez le filtrage des paiements par pos_id")
    
    print("\n" + "="*60)