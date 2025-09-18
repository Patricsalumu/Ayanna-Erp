#!/usr/bin/env python3
"""
Script de test pour vérifier la répartition avec TVA
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ayanna_erp.modules.salle_fete.controller.reservation_controller import ReservationController
from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ComptabiliteController
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaConfig

def test_repartition_tva():
    """Test de la répartition avec TVA"""
    print("=== Test de la répartition avec TVA ===")
    
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    try:
        # 1. Vérifier la configuration du POS 1
        print("\n1. Vérification de la configuration comptable...")
        config = session.query(ComptaConfig).filter_by(pos_id=1).first()
        if config:
            print(f"   ✅ Configuration trouvée pour POS 1")
            print(f"   - Compte caisse ID: {config.compte_caisse_id}")
            print(f"   - Compte TVA ID: {getattr(config, 'compte_tva_id', 'NON CONFIGURÉ')}")
            print(f"   - Compte vente ID (obsolète): {getattr(config, 'compte_vente_id', 'ABSENT')}")
        else:
            print("   ❌ Aucune configuration trouvée pour POS 1")
            return
        
        # 2. Créer un contrôleur de réservation
        print("\n2. Création du contrôleur de réservation...")
        reservation_controller = ReservationController(pos_id=1)
        
        # 3. Créer une réservation de test simple
        print("\n3. Simulation d'une répartition de paiement...")
        
        # Simuler une réservation avec services et produits ayant des comptes différents
        class MockReservation:
            def __init__(self):
                self.id = 999
                self.client_nom = "Test"
                self.client_prenom = "Client"
                self.total_amount = 1000.0  # 1000€ TTC
        
        class MockService:
            def __init__(self, compte_id, prix_unitaire, quantite=1):
                self.compte_comptable_id = compte_id
                self.prix_unitaire = prix_unitaire
                self.quantite = quantite
        
        class MockProduct:
            def __init__(self, compte_id, prix_unitaire, quantite=1):
                self.compte_comptable_id = compte_id
                self.prix_unitaire = prix_unitaire
                self.quantite = quantite
        
        # Créer une réservation avec services et produits
        mock_reservation = MockReservation()
        mock_reservation.services = [
            MockService(compte_id=10, prix_unitaire=400.0),  # Service 400€
            MockService(compte_id=11, prix_unitaire=200.0)   # Service 200€
        ]
        mock_reservation.produits = [
            MockProduct(compte_id=15, prix_unitaire=300.0),  # Produit 300€
            MockProduct(compte_id=16, prix_unitaire=100.0)   # Produit 100€
        ]
        
        # 4. Tester la répartition
        print("\n4. Test de la répartition...")
        montant_paiement = 500.0  # Paiement partiel de 500€
        
        repartition = reservation_controller.calculer_repartition_paiement(mock_reservation, montant_paiement)
        
        print(f"   Montant du paiement: {montant_paiement:.2f}€")
        print(f"   Total réservation: {mock_reservation.total_amount:.2f}€")
        print(f"   Répartition calculée:")
        print(f"   - Services: {repartition['services']}")
        print(f"   - Produits: {repartition['produits']}")
        print(f"   - TVA: {repartition['tva']:.2f}€")
        print(f"   - Total réparti: {sum(repartition['services'].values()) + sum(repartition['produits'].values()) + repartition['tva']:.2f}€")
        
        # 5. Vérifier que la TVA est bien prise en compte
        if repartition['tva'] > 0:
            print(f"   ✅ TVA calculée: {repartition['tva']:.2f}€")
        else:
            print(f"   ⚠️  Aucune TVA calculée (normal si pas de compte TVA configuré)")
        
        # Vérifier l'équilibre
        total_reparti = sum(repartition['services'].values()) + sum(repartition['produits'].values()) + repartition['tva']
        if abs(total_reparti - montant_paiement) < 0.01:
            print(f"   ✅ Répartition équilibrée")
        else:
            print(f"   ❌ Déséquilibre: {total_reparti:.2f} vs {montant_paiement:.2f}")
        
        print("\n✅ Test terminé")
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_repartition_tva()