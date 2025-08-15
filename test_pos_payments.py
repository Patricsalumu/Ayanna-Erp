#!/usr/bin/env python3
"""
Script de test pour vérifier la création automatique des POS et des paiements
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from ayanna_erp.database.database_manager import DatabaseManager, POSPoint, User
from ayanna_erp.modules.salle_fete.model.salle_fete import EventReservation, EventPayment, get_database_manager


def test_pos_creation():
    """Tester la création automatique des POS"""
    print("=== Test de création automatique des POS ===")
    
    try:
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        # Lister tous les POS créés
        pos_list = session.query(POSPoint).all()
        
        print(f"📍 {len(pos_list)} POS trouvés dans la base de données:")
        for pos in pos_list:
            print(f"  - {pos.name} (ID: {pos.id}, Enterprise: {pos.enterprise_id}, Module: {pos.module_id})")
        
        # Vérifier spécifiquement le POS Salle de Fête (module_id=1)
        salle_fete_pos = session.query(POSPoint).filter_by(module_id=1).first()
        if salle_fete_pos:
            print(f"✅ POS Salle de Fête trouvé: {salle_fete_pos.name} (ID: {salle_fete_pos.id})")
            return salle_fete_pos.id
        else:
            print("❌ Aucun POS Salle de Fête trouvé")
            return None
            
    except Exception as e:
        print(f"❌ Erreur lors du test POS: {e}")
        return None
    finally:
        try:
            db_manager.close_session()
        except:
            pass


def test_user_pos_detection():
    """Tester la détection du POS pour un utilisateur"""
    print("\n=== Test de détection du POS pour l'utilisateur ===")
    
    try:
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        # Récupérer le premier utilisateur
        user = session.query(User).first()
        if not user:
            print("❌ Aucun utilisateur trouvé")
            return None
            
        print(f"👤 Utilisateur: {user.email} (Enterprise: {user.enterprise_id})")
        
        # Chercher le POS du module Salle de Fête pour cette entreprise
        pos = session.query(POSPoint).filter_by(
            enterprise_id=user.enterprise_id,
            module_id=1  # Module Salle de Fête
        ).first()
        
        if pos:
            print(f"✅ POS Salle de Fête pour cet utilisateur: {pos.name} (ID: {pos.id})")
            return pos.id
        else:
            print(f"❌ Aucun POS Salle de Fête trouvé pour l'entreprise {user.enterprise_id}")
            return None
            
    except Exception as e:
        print(f"❌ Erreur lors du test utilisateur: {e}")
        return None
    finally:
        try:
            db_manager.close_session()
        except:
            pass


def test_payments_and_reservations():
    """Tester les réservations et paiements"""
    print("\n=== Test des réservations et paiements ===")
    
    try:
        db_manager = get_database_manager()
        session = db_manager.get_session()
        
        # Lister les réservations existantes
        reservations = session.query(EventReservation).all()
        print(f"📋 {len(reservations)} réservations trouvées:")
        
        for reservation in reservations:
            print(f"  - {reservation.reference} (Total: {reservation.total_amount}€)")
            
            # Lister les paiements pour cette réservation
            payments = session.query(EventPayment).filter_by(reservation_id=reservation.id).all()
            print(f"    💰 {len(payments)} paiements:")
            for payment in payments:
                print(f"      - {payment.amount}€ ({payment.payment_method}) - {payment.status}")
        
        if not reservations:
            print("ℹ️  Aucune réservation trouvée - c'est normal si la base vient d'être initialisée")
            
    except Exception as e:
        print(f"❌ Erreur lors du test paiements: {e}")
    finally:
        try:
            db_manager.close_session()
        except:
            pass


def main():
    """Fonction principale de test"""
    print("🔍 Début des tests...")
    
    # Test 1: Vérifier les POS
    pos_id = test_pos_creation()
    
    # Test 2: Vérifier la détection du POS pour l'utilisateur
    user_pos_id = test_user_pos_detection()
    
    # Test 3: Vérifier les réservations et paiements
    test_payments_and_reservations()
    
    print("\n✅ Tests terminés!")
    
    if pos_id and user_pos_id:
        print(f"📍 POS détecté: {user_pos_id}")
        print("🎯 Le système semble correctement configuré pour récupérer le bon POS")
    else:
        print("⚠️  Il y a des problèmes avec la configuration des POS")


if __name__ == "__main__":
    main()
