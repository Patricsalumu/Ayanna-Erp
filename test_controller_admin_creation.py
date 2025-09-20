#!/usr/bin/env python3
"""
Test du contrôleur EntrepriseController avec création automatique d'utilisateur admin
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
from ayanna_erp.database.database_manager import DatabaseManager, User
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject

def test_controller_admin_creation():
    """Tester la création automatique d'un utilisateur admin via le contrôleur"""
    print("🔥 Test du contrôleur EntrepriseController avec utilisateur admin automatique")
    
    try:
        # Créer une application Qt pour les signaux
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Créer le contrôleur
        controller = EntrepriseController()
        
        # Données de test pour l'entreprise
        test_enterprise_data = {
            'name': 'Ma Super Entreprise',
            'address': '456 Avenue des Affaires',
            'phone': '+243 987 654 321',
            'email': 'contact@masuperentreprise.com',
            'rccm': 'CD/KIN/RCCM/23-B-9999',
            'id_nat': 'SUPER456',
            'slogan': 'Excellence et Innovation',
            'currency': 'CDF'
        }
        
        print("📊 Données de l'entreprise de test:")
        for key, value in test_enterprise_data.items():
            print(f"  {key}: {value}")
        
        # Créer l'entreprise (et l'admin automatiquement) via le contrôleur
        print("\n🏗️ Création de l'entreprise via le contrôleur...")
        result = controller.create_enterprise(test_enterprise_data)
        
        if result:
            print("✅ Entreprise créée avec succès via le contrôleur!")
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
                    print(f"  Nom: {admin_user.name}")
                    print(f"  Email: {admin_user.email}")
                    print(f"  Role: {admin_user.role}")
                    print(f"  Enterprise ID: {admin_user.enterprise_id}")
                    
                    # Vérifier que l'enterprise_id correspond
                    if admin_user.enterprise_id == result['id']:
                        print("✅ L'utilisateur admin est correctement associé à l'entreprise!")
                    else:
                        print("❌ Erreur: L'utilisateur admin n'est pas associé à la bonne entreprise!")
                    
                    # Vérifier le mot de passe
                    if admin_user.check_password('admin123'):
                        print("✅ Le mot de passe 'admin123' est correctement vérifié")
                    else:
                        print("❌ Problème avec la vérification du mot de passe")
                    
                    print(f"\n📋 Résumé de l'utilisateur admin créé:")
                    print(f"  - Nom complet: {admin_user.name}")
                    print(f"  - Email: {admin_user.email}")
                    print(f"  - Role: {admin_user.role}")
                    print(f"  - Mot de passe par défaut: admin123")
                    print(f"  - Associé à l'entreprise ID: {admin_user.enterprise_id}")
                        
                else:
                    print("❌ Utilisateur admin non trouvé en base de données!")
                
                session.close()
            else:
                print("❌ Aucun utilisateur admin créé automatiquement!")
                
        else:
            print("❌ Échec de la création de l'entreprise!")
            
        print("\n🎉 Test terminé!")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_controller_admin_creation()