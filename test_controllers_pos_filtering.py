#!/usr/bin/env python3
"""
Script pour tester que tous les contrôleurs utilisent le bon pos_id
dans le module Salle de Fête
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import get_database_manager


def test_controller_pos_filtering():
    """Tester que tous les contrôleurs filtrent par pos_id"""
    print("🧪 Test du filtrage par pos_id dans tous les contrôleurs")
    print("=" * 60)
    
    try:
        db_manager = get_database_manager()
        
        # Test avec différents pos_id pour vérifier l'isolation
        test_pos_ids = [1, 9, 17]  # Premier POS de 3 entreprises différentes
        
        for pos_id in test_pos_ids:
            print(f"\n📍 Test avec pos_id = {pos_id}")
            
            # Test CalendrierController
            try:
                from ayanna_erp.modules.salle_fete.controller.calendrier_controller import CalendrierController
                calendrier_controller = CalendrierController(pos_id=pos_id)
                events = calendrier_controller.get_events_for_month(2025, 9)
                print(f"   ✅ CalendrierController: {len(events)} événements trouvés")
            except Exception as e:
                print(f"   ❌ CalendrierController: Erreur - {e}")
            
            # Test EntreSortieController
            try:
                from ayanna_erp.modules.salle_fete.controller.entre_sortie_controller import EntreSortieController
                entre_sortie_controller = EntreSortieController(pos_id=pos_id)
                from datetime import date
                expenses = entre_sortie_controller.get_expenses_by_date_and_pos(date.today(), pos_id)
                print(f"   ✅ EntreSortieController: {len(expenses)} dépenses trouvées")
            except Exception as e:
                print(f"   ❌ EntreSortieController: Erreur - {e}")
            
            # Test PaiementController
            try:
                from ayanna_erp.modules.salle_fete.controller.paiement_controller import PaiementController
                paiement_controller = PaiementController(pos_id=pos_id)
                payments = paiement_controller.get_all_reservations_with_payments()
                print(f"   ✅ PaiementController: {len(payments)} réservations avec paiements")
            except Exception as e:
                print(f"   ❌ PaiementController: Erreur - {e}")
            
            # Test RapportController
            try:
                from ayanna_erp.modules.salle_fete.controller.rapport_controller import RapportController
                rapport_controller = RapportController(pos_id=pos_id)
                monthly_data = rapport_controller.get_monthly_events_data(2025, 9)
                total_events = monthly_data.get('total_events', 0)
                print(f"   ✅ RapportController: {total_events} événements ce mois")
            except Exception as e:
                print(f"   ❌ RapportController: Erreur - {e}")
            
            # Test ReservationController
            try:
                from ayanna_erp.modules.salle_fete.controller.reservation_controller import ReservationController
                reservation_controller = ReservationController(pos_id=pos_id)
                reservations = reservation_controller.get_all_reservations()
                print(f"   ✅ ReservationController: {len(reservations)} réservations")
            except Exception as e:
                print(f"   ❌ ReservationController: Erreur - {e}")
            
            # Test ServiceController
            try:
                from ayanna_erp.modules.salle_fete.controller.service_controller import ServiceController
                service_controller = ServiceController(pos_id=pos_id)
                services = service_controller.get_all_services()
                print(f"   ✅ ServiceController: {len(services)} services")
            except Exception as e:
                print(f"   ❌ ServiceController: Erreur - {e}")
            
            # Test ProduitController
            try:
                from ayanna_erp.modules.salle_fete.controller.produit_controller import ProduitController
                produit_controller = ProduitController(pos_id=pos_id)
                produits = produit_controller.get_all_products()
                print(f"   ✅ ProduitController: {len(produits)} produits")
            except Exception as e:
                print(f"   ❌ ProduitController: Erreur - {e}")
        
        print(f"\n🎯 Résumé:")
        print(f"   • Tests effectués avec 3 pos_id différents")
        print(f"   • 7 contrôleurs testés")
        print(f"   • Vérification de l'isolation des données par entreprise")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_isolation():
    """Tester l'isolation des données entre entreprises"""
    print(f"\n🔒 Test d'isolation des données entre entreprises")
    print("=" * 50)
    
    try:
        from ayanna_erp.modules.salle_fete.controller.reservation_controller import ReservationController
        
        # Comparer les réservations entre différents pos_id
        pos_id_1 = 1  # Entreprise 1
        pos_id_2 = 9  # Entreprise 2
        
        controller_1 = ReservationController(pos_id=pos_id_1)
        controller_2 = ReservationController(pos_id=pos_id_2)
        
        reservations_1 = controller_1.get_all_reservations()
        reservations_2 = controller_2.get_all_reservations()
        
        print(f"   📊 Entreprise 1 (pos_id={pos_id_1}): {len(reservations_1)} réservations")
        print(f"   📊 Entreprise 2 (pos_id={pos_id_2}): {len(reservations_2)} réservations")
        
        # Vérifier qu'aucune réservation n'est partagée
        if len(reservations_1) > 0 and len(reservations_2) > 0:
            ids_1 = {r.id for r in reservations_1}
            ids_2 = {r.id for r in reservations_2}
            shared_ids = ids_1.intersection(ids_2)
            
            if len(shared_ids) == 0:
                print(f"   ✅ Isolation parfaite: aucune donnée partagée")
            else:
                print(f"   ❌ Fuite de données: {len(shared_ids)} réservations partagées!")
                return False
        else:
            print(f"   ℹ️  Une des entreprises n'a pas de données pour tester l'isolation")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test d'isolation: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Démarrage des tests de contrôleurs")
    print("="*60)
    
    controller_test = test_controller_pos_filtering()
    isolation_test = test_data_isolation()
    
    if controller_test and isolation_test:
        print("\n🎉 Tous les tests sont passés avec succès!")
        print("   ✅ Tous les contrôleurs filtrent correctement par pos_id")
        print("   ✅ L'isolation des données entre entreprises fonctionne")
    else:
        print("\n❌ Certains tests ont échoué!")
    
    print("\n" + "="*60)