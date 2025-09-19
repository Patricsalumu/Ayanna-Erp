#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test de la nouvelle logique simplifiée :
- Côté crédit : montants bruts (déjà correct)
- Côté débit remise : TOUTE la remise au premier paiement
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.salle_fete.controller.paiement_controller import PaiementController
from sqlalchemy.orm import sessionmaker

def test_remise_premier_paiement():
    """Test : remise complète débitée au premier paiement"""
    
    print("🧪 TEST : Remise complète au premier paiement")
    print("=" * 60)
    
    # Configuration de la base de données
    db_manager = DatabaseManager()
    engine = db_manager.get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Importer les modèles
        from ayanna_erp.modules.salle_fete.model.salle_fete import EventReservation, EventPayment
        from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaEcritures as EcritureComptable
        
        # Trouver une réservation avec remise
        reservation = session.query(EventReservation)\
            .filter(EventReservation.discount_percent.isnot(None),
                   EventReservation.discount_percent > 0)\
            .first()
        
        if not reservation:
            print("❌ Aucune réservation avec remise trouvée")
            return
        
        print(f"📋 Réservation trouvée: ID {reservation.id}")
        print(f"   Client: {reservation.get_client_name()}")
        print(f"   Total TTC (sans remise): {reservation.total_amount:.2f}€")
        print(f"   Remise: {reservation.discount_percent}%")
        
        remise_totale = float(reservation.total_amount) * (reservation.discount_percent / 100)
        total_net = float(reservation.total_amount) - remise_totale
        
        print(f"   Remise totale: {remise_totale:.2f}€")
        print(f"   Total net: {total_net:.2f}€")
        print()
        
        # Vérifier les paiements existants
        paiements = session.query(EventPayment)\
            .filter(EventPayment.reservation_id == reservation.id,
                   EventPayment.status == 'validated')\
            .order_by(EventPayment.id)\
            .all()
        
        if not paiements:
            print("❌ Aucun paiement validé trouvé")
            return
        
        print(f"💰 Paiements trouvés: {len(paiements)}")
        
        # Controller pour test
        controller = PaiementController()
        
        # Analyser chaque paiement
        total_debits_remise = 0
        
        for i, paiement in enumerate(paiements, 1):
            print(f"\n--- PAIEMENT {i} (ID: {paiement.id}) ---")
            print(f"   Montant: {paiement.amount:.2f}€")
            
            # Chercher les écritures de remise pour ce paiement
            from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaConfig
            config = session.query(ComptaConfig).first()
            
            if config and config.compte_remise_id:
                ecritures_remise = session.query(EcritureComptable)\
                    .filter(EcritureComptable.compte_comptable_id == config.compte_remise_id,
                           EcritureComptable.debit > 0,
                           EcritureComptable.libelle.like(f"%{reservation.get_client_name()}%"))\
                    .all()
                
                # Trouver l'écriture de ce paiement (approximation par montant et timing)
                for ecriture in ecritures_remise:
                    if ecriture.debit > 0:
                        print(f"   💳 Remise débitée: {ecriture.debit:.2f}€")
                        total_debits_remise += ecriture.debit
                        
                        # Vérifier si c'est le premier paiement qui a TOUTE la remise
                        if abs(ecriture.debit - remise_totale) < 0.01:
                            print(f"   ✅ TOUTE la remise débitée d'un coup ({remise_totale:.2f}€)")
                        elif i == 1 and ecriture.debit > 0:
                            print(f"   💡 Premier paiement avec remise partielle: {ecriture.debit:.2f}€")
                        else:
                            print(f"   📊 Remise partielle: {ecriture.debit:.2f}€")
        
        print(f"\n📊 RÉSUMÉ:")
        print(f"   Remise totale théorique: {remise_totale:.2f}€")
        print(f"   Total débits remise: {total_debits_remise:.2f}€")
        print(f"   Différence: {abs(remise_totale - total_debits_remise):.2f}€")
        
        if abs(remise_totale - total_debits_remise) < 0.01:
            print(f"   ✅ Cohérence: La remise totale a bien été débitée")
        else:
            print(f"   ⚠️  Incohérence dans les débits de remise")
        
        # Test de la nouvelle logique avec simulation
        print(f"\n🔮 SIMULATION NOUVELLE LOGIQUE:")
        print(f"   Premier paiement: {paiements[0].amount:.2f}€")
        print(f"   → Remise complète débitée: {remise_totale:.2f}€")
        
        if len(paiements) > 1:
            for i, paiement in enumerate(paiements[1:], 2):
                print(f"   Paiement {i}: {paiement.amount:.2f}€")
                print(f"   → Remise débitée: 0.00€ (déjà fait)")
        
        print(f"   ✅ Solution simple et efficace!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_remise_premier_paiement()