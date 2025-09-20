#!/usr/bin/env python3
"""
Test de création automatique d'un utilisateur admin lors de la création d'une entreprise
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
from ayanna_erp.database.database_manager import DatabaseManager, User
from PyQt5.QtWidgets import QApplication

def test_enterprise_admin_creation():
    """Tester la création automatique d'un utilisateur admin"""
    print("🔥 Test de création d'entreprise avec utilisateur admin automatique")
    
    try:
        # Créer une application Qt pour les signaux
        app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
        
        # Créer le contrôleur
        controller = EntrepriseController()
        
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
        
        # Créer l'entreprise (et l'admin automatiquement)
        print("\n🏗️ Création de l'entreprise...")
        result = controller.create_enterprise(test_enterprise_data)
        
        if result:
            print("✅ Entreprise créée avec succès!")
            print(f"  ID: {result['id']}")
            print(f"  Nom: {result['name']}")
            print(f"  Email: {result['email']}")
            
            # Vérifier si l'admin a été créé
            if 'admin_user_id' in result:
                print(f"\n👤 Utilisateur admin créé automatiquement:")
                print(f"  ID: {result['admin_user_id']}")
                print(f"  Identifiants: {result['admin_credentials']}")
                
                # Vérifier dans la base de données
                db_manager = DatabaseManager()
                session = db_manager.get_session()
                
                admin_user = session.query(User).filter_by(id=result['admin_user_id']).first()
                
                if admin_user:
                    print(f"\n✅ Vérification en base de données:")
                    print(f"  Username: {admin_user.username}")
                    print(f"  Email: {admin_user.email}")
                    print(f"  Role: {admin_user.role}")
                    print(f"  Enterprise ID: {admin_user.enterprise_id}")
                    print(f"  Is Active: {admin_user.is_active}")
                    print(f"  First Name: {admin_user.first_name}")
                    print(f"  Last Name: {admin_user.last_name}")
                    
                    # Vérifier que l'enterprise_id correspond
                    if admin_user.enterprise_id == result['id']:
                        print("✅ L'utilisateur admin est correctement associé à l'entreprise!")
                    else:
                        print("❌ Erreur: L'utilisateur admin n'est pas associé à la bonne entreprise!")
                    
                    # Vérifier le mot de passe (on ne peut que vérifier qu'il est hashé)
                    if admin_user.password_hash and len(admin_user.password_hash) > 50:
                        print("✅ Le mot de passe est correctement hashé")
                    else:
                        print("❌ Problème avec le hachage du mot de passe")
                        
                else:
                    print("❌ Utilisateur admin non trouvé en base de données!")
                
                session.close()
            else:
                print("❌ Aucun utilisateur admin créé automatiquement!")
                
        else:
            print("❌ Échec de la création de l'entreprise!")
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enterprise_admin_creation()