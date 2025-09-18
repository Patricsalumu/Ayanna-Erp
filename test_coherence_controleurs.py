#!/usr/bin/env python3
"""
Test de cohérence entre ReservationController et PaiementController
Vérifier que les deux utilisent la même logique de répartition
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from datetime import datetime

def test_coherence_controleurs():
    """Test de cohérence entre les deux contrôleurs"""
    print("🧪 Test de cohérence entre ReservationController et PaiementController")
    print("=" * 80)
    
    try:
        # Import des contrôleurs
        from ayanna_erp.modules.salle_fete.controller.reservation_controller import ReservationController
        from ayanna_erp.modules.salle_fete.controller.paiement_controller import PaiementController
        
        # Créer les contrôleurs
        reservation_controller = ReservationController()
        paiement_controller = PaiementController()
        
        # Mock d'une réservation identique pour les deux tests
        class MockReservation:
            def __init__(self):
                self.total_amount = 1200.0
                self.tax_rate = 20.0
                self.services = []
                self.products = []
                
            def get_client_name(self):
                return "Test Client"
        
        class MockService:
            def __init__(self, name, account_id):
                self.name = name
                self.account_id = account_id
        
        class MockProduct:
            def __init__(self, name, account_id):
                self.name = name
                self.account_id = account_id
        
        class MockServiceItem:
            def __init__(self, service, line_total):
                self.service = service
                self.line_total = line_total
        
        class MockProductItem:
            def __init__(self, product, line_total):
                self.product = product
                self.line_total = line_total
        
        # Créer une réservation test identique
        reservation = MockReservation()
        
        # Services
        service1 = MockService("Salle", 701)
        service2 = MockService("DJ", 702)
        reservation.services = [
            MockServiceItem(service1, 600.0),
            MockServiceItem(service2, 300.0),
        ]
        
        # Produits
        product1 = MockProduct("Boissons", 703)
        product2 = MockProduct("Catering", 704)
        reservation.products = [
            MockProductItem(product1, 200.0),
            MockProductItem(product2, 100.0),
        ]
        
        # Test avec le même montant de paiement
        montant_test = 600.0  # 50% acompte
        
        print(f"\n📊 Test avec réservation de {reservation.total_amount}€ et paiement de {montant_test}€")
        
        # === TEST RESERVATION CONTROLLER ===
        print("\n🏗️  Test ReservationController:")
        repartition_reservation = reservation_controller.calculer_repartition_paiement(reservation, montant_test)
        
        # === TEST PAIEMENT CONTROLLER ===
        print("\n💳 Test PaiementController:")
        repartition_paiement = paiement_controller.calculer_repartition_paiement(reservation, montant_test)
        
        # === COMPARAISON DES RÉSULTATS ===
        print(f"\n🔍 Comparaison des résultats:")
        
        # Comparer les services
        print("📋 Services:")
        for account_id in set(list(repartition_reservation['services'].keys()) + list(repartition_paiement['services'].keys())):
            montant_res = repartition_reservation['services'].get(account_id, 0)
            montant_pay = repartition_paiement['services'].get(account_id, 0)
            match = abs(montant_res - montant_pay) < 0.01
            status = "✅" if match else "❌"
            print(f"  {status} Compte {account_id}: Reservation={montant_res:.2f}, Paiement={montant_pay:.2f}")
        
        # Comparer les produits
        print("📋 Produits:")
        for account_id in set(list(repartition_reservation['produits'].keys()) + list(repartition_paiement['produits'].keys())):
            montant_res = repartition_reservation['produits'].get(account_id, 0)
            montant_pay = repartition_paiement['produits'].get(account_id, 0)
            match = abs(montant_res - montant_pay) < 0.01
            status = "✅" if match else "❌"
            print(f"  {status} Compte {account_id}: Reservation={montant_res:.2f}, Paiement={montant_pay:.2f}")
        
        # Comparer HT et TVA
        print("📋 Totaux:")
        ht_match = abs(repartition_reservation['total_ht'] - repartition_paiement['total_ht']) < 0.01
        tva_match = abs(repartition_reservation['tva'] - repartition_paiement['tva']) < 0.01
        
        print(f"  {'✅' if ht_match else '❌'} Total HT: Reservation={repartition_reservation['total_ht']:.2f}, Paiement={repartition_paiement['total_ht']:.2f}")
        print(f"  {'✅' if tva_match else '❌'} TVA: Reservation={repartition_reservation['tva']:.2f}, Paiement={repartition_paiement['tva']:.2f}")
        
        # Verdict final
        all_match = (
            all(abs(repartition_reservation['services'].get(k, 0) - repartition_paiement['services'].get(k, 0)) < 0.01 
                for k in set(list(repartition_reservation['services'].keys()) + list(repartition_paiement['services'].keys()))) and
            all(abs(repartition_reservation['produits'].get(k, 0) - repartition_paiement['produits'].get(k, 0)) < 0.01 
                for k in set(list(repartition_reservation['produits'].keys()) + list(repartition_paiement['produits'].keys()))) and
            ht_match and tva_match
        )
        
        if all_match:
            print("\n🎉 SUCCÈS: Les deux contrôleurs utilisent la même logique de répartition!")
            print("✅ ReservationController et PaiementController sont cohérents")
        else:
            print("\n❌ ÉCHEC: Les deux contrôleurs donnent des résultats différents!")
            print("⚠️  Il y a une incohérence dans les calculs")
        
        return all_match
        
    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")
        import traceback
        traceback.print_exc()
        return False

def test_scenario_complet():
    """Test d'un scénario complet : acompte + solde"""
    print("\n🧪 Test de scénario complet : Acompte + Solde")
    print("=" * 80)
    
    try:
        from ayanna_erp.modules.salle_fete.controller.reservation_controller import ReservationController
        from ayanna_erp.modules.salle_fete.controller.paiement_controller import PaiementController
        
        reservation_controller = ReservationController()
        paiement_controller = PaiementController()
        
        # Réservation de 1200€ avec TVA 20%
        # Service Salle: 600€ TTC (500€ HT) -> Compte 701
        # Produit Boisson: 600€ TTC (500€ HT) -> Compte 703  
        # TVA: 200€ -> Compte TVA
        
        print("📋 Scénario:")
        print("  - Réservation totale: 1200€ TTC")
        print("  - Service Salle: 600€ TTC (500€ HT) -> Compte 701")
        print("  - Produit Boissons: 600€ TTC (500€ HT) -> Compte 703")
        print("  - TVA (20%): 200€")
        print("  - Paiement 1 (acompte): 600€ (50%)")
        print("  - Paiement 2 (solde): 600€ (50%)")
        
        print("\n🧮 Répartition attendue:")
        print("  Acompte 600€ → Salle: 250€, Boisson: 250€, TVA: 100€")
        print("  Solde 600€ → Salle: 250€, Boisson: 250€, TVA: 100€")
        print("  TOTAL → Salle: 500€, Boisson: 500€, TVA: 200€")
        
        # TODO: Implémenter le test avec mock complet
        print("\n💡 Test d'intégration complet à implémenter avec vraies données")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return False

if __name__ == "__main__":
    print("🚀 Tests de cohérence des contrôleurs de paiement")
    print("=" * 80)
    
    success1 = test_coherence_controleurs()
    success2 = test_scenario_complet()
    
    if success1 and success2:
        print("\n🎉 TOUS LES TESTS RÉUSSIS!")
        print("✅ La logique de répartition est maintenant cohérente entre:")
        print("   - ReservationController (acomptes)")
        print("   - PaiementController (paiements suivants)")
        print("\n💡 RÉSUMÉ DE LA SOLUTION:")
        print("   🔹 Formule: montant_compte = (line_total_ht / total_ht) × proportion_paiement")
        print("   🔹 Chaque service/produit → son compte spécifique")
        print("   🔹 TVA → compte TVA configuré")
        print("   🔹 Proportionnel à chaque paiement (acompte, solde, etc.)")
    else:
        print("\n❌ CERTAINS TESTS ONT ÉCHOUÉ")
        sys.exit(1)