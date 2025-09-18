#!/usr/bin/env python3
"""
Test de débogage pour la méthode creer_ecritures_comptables_reparties
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.salle_fete.model.salle_fete import EventReservation, EventPayment
from ayanna_erp.modules.salle_fete.controller.reservation_controller import ReservationController
from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaConfig
from datetime import datetime

def test_debug_ecritures():
    """Test de débogage pour les écritures comptables"""
    print("=== Test de débogage des écritures comptables ===")
    
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    try:
        # 1. Récupérer une réservation existante
        reservation = session.query(EventReservation).first()
        if not reservation:
            print("❌ Aucune réservation trouvée")
            return
        
        print(f"✅ Réservation: {reservation.client_nom} - {reservation.total_amount}€")
        
        # 2. Créer un paiement de test
        payment = EventPayment(
            reservation_id=reservation.id,
            amount=100.0,
            payment_method='Test',
            payment_date=datetime.now(),
            status='validated',
            user_id=1,
            notes="Test debug"
        )
        session.add(payment)
        session.flush()  # Pour avoir l'ID
        
        print(f"✅ Paiement test créé: {payment.amount}€")
        
        # 3. Récupérer la configuration
        config = session.query(ComptaConfig).filter_by(pos_id=1).first()
        if not config:
            print("❌ Configuration manquante")
            return
        
        print(f"✅ Configuration: Caisse={config.compte_caisse_id}, TVA={getattr(config, 'compte_tva_id', 'None')}")
        
        # 4. Calculer la répartition
        controller = ReservationController(pos_id=1)
        repartition = controller.calculer_repartition_paiement(reservation, payment.amount)
        
        print(f"✅ Répartition calculée:")
        print(f"   Services: {repartition['services']}")
        print(f"   Produits: {repartition['produits']}")  
        print(f"   TVA: {repartition['tva']}")
        
        # 5. Test de création des écritures avec debug détaillé
        print(f"\n🔍 Test de création des écritures avec debug...")
        
        try:
            ecritures = controller.creer_ecritures_comptables_reparties(
                session=session,
                reservation=reservation,
                payment=payment,
                repartition=repartition,
                compte_debit_id=config.compte_caisse_id,
                compte_tva_id=getattr(config, 'compte_tva_id', None),
                journal_id=1  # Journal test
            )
            
            print(f"✅ Écritures créées: {len(ecritures)}")
            for i, ecriture in enumerate(ecritures):
                print(f"   {i+1}. Compte {ecriture.compte_comptable_id}: Débit={ecriture.debit}, Crédit={ecriture.credit}")
            
            if len(ecritures) == 0:
                print("❌ PROBLÈME: Aucune écriture créée!")
            
        except Exception as e:
            print(f"❌ EXCEPTION dans creer_ecritures_comptables_reparties: {e}")
            import traceback
            traceback.print_exc()
        
        # 6. Nettoyer le paiement test
        session.delete(payment)
        session.commit()
        
        print(f"\n✅ Test terminé")
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_debug_ecritures()