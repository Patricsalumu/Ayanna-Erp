#!/usr/bin/env python3
"""
Script de test pour vérifier le filtrage par entreprise via pos_id
dans le module Salle de Fête
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import get_database_manager
from ayanna_erp.modules.salle_fete.model.salle_fete import EventReservation, EventClient, EventService, EventProduct, EventExpense


def test_pos_filtering():
    """Test du filtrage des données par pos_id"""
    print("🧪 Test du filtrage des données par entreprise via pos_id")
    print("=" * 60)
    
    try:
        db_manager = get_database_manager()
        
        # Test 1: Vérifier la méthode get_pos_id_for_enterprise_module
        print("\n1️⃣ Test de la méthode get_pos_id_for_enterprise_module:")
        
        enterprise_id = 1  # Entreprise existante
        pos_id = db_manager.get_pos_id_for_enterprise_module(enterprise_id, "SalleFete")
        print(f"   POS ID pour entreprise {enterprise_id}, module SalleFete: {pos_id}")
        
        if pos_id is None:
            print("   ❌ Aucun POS trouvé - le test ne peut pas continuer")
            return False
        
        # Test 2: Compter les données existantes pour ce pos_id
        print(f"\n2️⃣ Analyse des données existantes pour pos_id={pos_id}:")
        
        session = db_manager.get_session()
        
        # Compter les réservations
        reservations_count = session.query(EventReservation).filter_by(pos_id=pos_id).count()
        print(f"   📋 Réservations: {reservations_count}")
        
        # Compter les clients
        clients_count = session.query(EventClient).filter_by(pos_id=pos_id).count()
        print(f"   👥 Clients: {clients_count}")
        
        # Compter les services
        services_count = session.query(EventService).filter_by(pos_id=pos_id).count()
        print(f"   🛎️  Services: {services_count}")
        
        # Compter les produits
        products_count = session.query(EventProduct).filter_by(pos_id=pos_id).count()
        print(f"   📦 Produits: {products_count}")
        
        # Compter les dépenses
        expenses_count = session.query(EventExpense).filter_by(pos_id=pos_id).count()
        print(f"   💰 Dépenses: {expenses_count}")
        
        # Test 3: Vérifier qu'aucune donnée n'existe pour un pos_id différent
        print(f"\n3️⃣ Test d'isolation - Vérification qu'aucune donnée n'existe pour pos_id=999:")
        
        fake_pos_id = 999
        fake_reservations = session.query(EventReservation).filter_by(pos_id=fake_pos_id).count()
        fake_clients = session.query(EventClient).filter_by(pos_id=fake_pos_id).count()
        fake_services = session.query(EventService).filter_by(pos_id=fake_pos_id).count()
        fake_products = session.query(EventProduct).filter_by(pos_id=fake_pos_id).count()
        fake_expenses = session.query(EventExpense).filter_by(pos_id=fake_pos_id).count()
        
        print(f"   📋 Réservations pour pos_id={fake_pos_id}: {fake_reservations}")
        print(f"   👥 Clients pour pos_id={fake_pos_id}: {fake_clients}")
        print(f"   🛎️  Services pour pos_id={fake_pos_id}: {fake_services}")
        print(f"   📦 Produits pour pos_id={fake_pos_id}: {fake_products}")
        print(f"   💰 Dépenses pour pos_id={fake_pos_id}: {fake_expenses}")
        
        total_fake_data = fake_reservations + fake_clients + fake_services + fake_products + fake_expenses
        
        if total_fake_data == 0:
            print("   ✅ Parfait ! Aucune donnée trouvée pour un pos_id inexistant")
        else:
            print(f"   ⚠️  Attention ! {total_fake_data} enregistrements trouvés pour un pos_id inexistant")
        
        # Test 4: Vérifier la relation enterprise -> pos -> données
        print(f"\n4️⃣ Test de la relation complète enterprise -> pos -> données:")
        
        from ayanna_erp.database.database_manager import POSPoint, Entreprise
        
        # Récupérer le POS et l'entreprise
        pos = session.query(POSPoint).filter_by(id=pos_id).first()
        if pos:
            enterprise = session.query(Entreprise).filter_by(id=pos.enterprise_id).first()
            print(f"   🏢 Entreprise: {enterprise.name if enterprise else 'Non trouvée'} (ID: {pos.enterprise_id})")
            print(f"   🏪 POS: {pos.name} (ID: {pos.id})")
            print(f"   📊 Module ID: {pos.module_id}")
            
            # Vérifier que toutes les données appartiennent bien à cette entreprise via le pos_id
            all_data_correct = True
            
            # Vérifier quelques réservations
            sample_reservations = session.query(EventReservation).filter_by(pos_id=pos_id).limit(5).all()
            for reservation in sample_reservations:
                if reservation.pos_id != pos_id:
                    print(f"   ❌ Réservation {reservation.id} a un pos_id incorrect: {reservation.pos_id}")
                    all_data_correct = False
            
            if all_data_correct:
                print("   ✅ Toutes les données vérifiées appartiennent au bon pos_id")
            else:
                print("   ❌ Incohérences détectées dans les données")
        
        session.close()
        
        print(f"\n🎯 Résumé du test:")
        print(f"   • POS ID utilisé: {pos_id}")
        print(f"   • Total des données: {reservations_count + clients_count + services_count + products_count + expenses_count}")
        print(f"   • Isolation vérifiée: {'✅' if total_fake_data == 0 else '❌'}")
        print(f"   • Relation enterprise->pos->données: {'✅' if pos else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_enterprises():
    """Test avec plusieurs entreprises (si elles existent)"""
    print("\n🏢 Test multi-entreprises:")
    print("=" * 40)
    
    try:
        db_manager = get_database_manager()
        session = db_manager.get_session()
        
        from ayanna_erp.database.database_manager import Entreprise, POSPoint
        
        # Lister toutes les entreprises
        enterprises = session.query(Entreprise).all()
        print(f"   Nombre d'entreprises: {len(enterprises)}")
        
        for enterprise in enterprises:
            print(f"\n   🏢 Entreprise: {enterprise.name} (ID: {enterprise.id})")
            
            # Trouver les POS pour cette entreprise
            pos_points = session.query(POSPoint).filter_by(enterprise_id=enterprise.id).all()
            print(f"      POS associés: {len(pos_points)}")
            
            for pos in pos_points:
                print(f"        - {pos.name} (ID: {pos.id}, Module: {pos.module_id})")
                
                # Pour le module SalleFete uniquement
                if pos.module_id == 1:  # Supposons que SalleFete = module_id 1
                    reservations = session.query(EventReservation).filter_by(pos_id=pos.id).count()
                    print(f"          Réservations: {reservations}")
        
        session.close()
        
    except Exception as e:
        print(f"❌ Erreur lors du test multi-entreprises: {e}")


if __name__ == "__main__":
    print("🚀 Démarrage des tests de filtrage par entreprise")
    print("="*60)
    
    success = test_pos_filtering()
    test_multiple_enterprises()
    
    if success:
        print("\n✅ Tests terminés avec succès!")
    else:
        print("\n❌ Tests échoués!")
    
    print("\n" + "="*60)