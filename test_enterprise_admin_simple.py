#!/usr/bin/env python3
"""
Test simple de création automatique d'un utilisateur admin lors de la création d'une entreprise
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from ayanna_erp.database.database_manager import DatabaseManager, User, Entreprise

def test_enterprise_admin_creation():
    """Tester la création automatique d'un utilisateur admin"""
    print("🔥 Test de création d'entreprise avec utilisateur admin automatique")
    
    try:
        # Données de test pour l'entreprise
        test_enterprise_data = {
            'name': 'Test Enterprise Admin',
            'address': '123 Test Street',
            'phone': '+243 123 456 789',
            'email': 'test@testenterprise.com',
            'rccm': 'CD/KIN/RCCM/23-B-5678',
            'id_nat': 'TEST123',
            'slogan': 'Test Enterprise Slogan',
            'currency': 'USD'
        }
        
        print("📊 Données de l'entreprise de test:")
        for key, value in test_enterprise_data.items():
            print(f"  {key}: {value}")
        
        # Créer l'entreprise directement via la base de données
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        print("\n🏗️ Création de l'entreprise...")
        
        enterprise = Entreprise(
            name=test_enterprise_data.get('name', ''),
            address=test_enterprise_data.get('address', ''),
            phone=test_enterprise_data.get('phone', ''),
            email=test_enterprise_data.get('email', ''),
            rccm=test_enterprise_data.get('rccm', ''),
            id_nat=test_enterprise_data.get('id_nat', ''),
            logo=test_enterprise_data.get('logo'),
            slogan=test_enterprise_data.get('slogan', ''),
            currency=test_enterprise_data.get('currency', 'USD')
        )
        
        session.add(enterprise)
        session.commit()
        
        print("✅ Entreprise créée avec succès!")
        print(f"  ID: {enterprise.id}")
        print(f"  Nom: {enterprise.name}")
        print(f"  Email: {enterprise.email}")
        
        # Créer automatiquement un utilisateur admin
        admin_user = User(
            name='Administrateur Système',
            email=test_enterprise_data.get('email', 'admin@' + test_enterprise_data.get('name', 'entreprise').lower().replace(' ', '') + '.com'),
            role='admin',
            enterprise_id=enterprise.id
        )
        
        # Utiliser la méthode set_password du modèle
        admin_user.set_password('admin123')
        
        session.add(admin_user)
        session.commit()
        
        print(f"\n👤 Utilisateur admin créé automatiquement:")
        print(f"  ID: {admin_user.id}")
        print(f"  Nom: {admin_user.name}")
        print(f"  Email: {admin_user.email}")
        print(f"  Role: {admin_user.role}")
        print(f"  Enterprise ID: {admin_user.enterprise_id}")
        print(f"  Mot de passe: admin123")
        
        # Vérifier que l'enterprise_id correspond
        if admin_user.enterprise_id == enterprise.id:
            print("✅ L'utilisateur admin est correctement associé à l'entreprise!")
        else:
            print("❌ Erreur: L'utilisateur admin n'est pas associé à la bonne entreprise!")
        
        # Vérifier le mot de passe
        if admin_user.check_password('admin123'):
            print("✅ Le mot de passe 'admin123' est correctement vérifié")
        else:
            print("❌ Problème avec la vérification du mot de passe")
            
        session.close()
        print("\n🎉 Test réussi! L'entreprise et l'utilisateur admin ont été créés automatiquement.")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enterprise_admin_creation()