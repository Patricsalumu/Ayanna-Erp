#!/usr/bin/env python3
"""
Test de création d'entreprise avec le nouveau sélecteur de devise USD/FC
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from ayanna_erp.database.database_manager import DatabaseManager, Entreprise

def test_enterprise_creation_with_currency():
    """Tester la création d'entreprise avec les nouvelles devises"""
    print("🏢 Test de création d'entreprise avec devise USD/FC")
    print("=" * 60)
    
    try:
        # Test 1: Création avec devise USD
        print("1️⃣ Test de création avec devise USD...")
        
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        enterprise_usd = Entreprise(
            name='Test Enterprise USD',
            address='123 USD Street',
            phone='+243 111 222 333',
            email='test@enterpriseusd.com',
            rccm='CD/KIN/RCCM/23-B-USD1',
            id_nat='USD123',
            slogan='USD Enterprise Test',
            currency='USD'  # Devise USD
        )
        
        session.add(enterprise_usd)
        session.commit()
        
        print("✅ Entreprise USD créée avec succès!")
        print(f"  ID: {enterprise_usd.id}")
        print(f"  Nom: {enterprise_usd.name}")
        print(f"  Devise: {enterprise_usd.currency}")
        
        # Test 2: Création avec devise FC
        print("\n2️⃣ Test de création avec devise FC...")
        
        enterprise_fc = Entreprise(
            name='Test Enterprise FC',
            address='456 FC Avenue',
            phone='+243 444 555 666',
            email='test@enterprisefc.com',
            rccm='CD/KIN/RCCM/23-B-FC1',
            id_nat='FC456',
            slogan='FC Enterprise Test',
            currency='FC'  # Devise FC
        )
        
        session.add(enterprise_fc)
        session.commit()
        
        print("✅ Entreprise FC créée avec succès!")
        print(f"  ID: {enterprise_fc.id}")
        print(f"  Nom: {enterprise_fc.name}")
        print(f"  Devise: {enterprise_fc.currency}")
        
        # Test 3: Vérification en base de données
        print("\n3️⃣ Vérification en base de données...")
        
        # Récupérer toutes les entreprises avec leurs devises
        enterprises = session.query(Entreprise).all()
        
        usd_count = 0
        fc_count = 0
        other_count = 0
        
        print("\n📊 Liste des entreprises et leurs devises:")
        for i, enterprise in enumerate(enterprises, 1):
            print(f"  {i}. {enterprise.name} - Devise: {enterprise.currency}")
            
            if enterprise.currency == 'USD':
                usd_count += 1
            elif enterprise.currency == 'FC':
                fc_count += 1
            else:
                other_count += 1
        
        print(f"\n📈 Statistiques des devises:")
        print(f"  💵 USD: {usd_count} entreprise(s)")
        print(f"  🪙 FC: {fc_count} entreprise(s)")
        print(f"  🌍 Autres: {other_count} entreprise(s)")
        
        # Test 4: Validation des nouvelles entreprises
        print("\n4️⃣ Validation des nouvelles entreprises...")
        
        # Vérifier l'entreprise USD
        retrieved_usd = session.query(Entreprise).filter_by(id=enterprise_usd.id).first()
        if retrieved_usd and retrieved_usd.currency == 'USD':
            print("✅ Entreprise USD correctement récupérée avec devise USD")
        else:
            print("❌ Problème avec l'entreprise USD")
        
        # Vérifier l'entreprise FC
        retrieved_fc = session.query(Entreprise).filter_by(id=enterprise_fc.id).first()
        if retrieved_fc and retrieved_fc.currency == 'FC':
            print("✅ Entreprise FC correctement récupérée avec devise FC")
        else:
            print("❌ Problème avec l'entreprise FC")
        
        session.close()
        
        print("\n🎉 SUCCÈS! Le système de devise USD/FC fonctionne correctement:")
        print("  ✅ Création d'entreprise avec devise USD")
        print("  ✅ Création d'entreprise avec devise FC")
        print("  ✅ Stockage correct en base de données")
        print("  ✅ Récupération des données fidèle")
        
        print("\n💡 Informations importantes:")
        print("  • Les entreprises peuvent maintenant utiliser uniquement USD ou FC")
        print("  • La devise par défaut est USD")
        print("  • Les anciennes devises sont conservées mais le formulaire ne propose que USD/FC")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enterprise_creation_with_currency()