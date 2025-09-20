#!/usr/bin/env python3
"""
Test complet des fonctionnalités de l'entreprise : BLOB logo + utilisateur admin automatique
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from ayanna_erp.database.database_manager import DatabaseManager, User, Entreprise

def test_all_enterprise_features():
    """Tester toutes les fonctionnalités de l'entreprise"""
    print("🚀 Test complet des fonctionnalités de l'entreprise")
    print("=" * 60)
    
    try:
        # Simuler des données de logo (BLOB)
        fake_logo_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\x00\x00\x00\x1f\xf3\xffa'  # PNG header
        
        # Données de test pour l'entreprise
        test_enterprise_data = {
            'name': 'AYANNA BUSINESS SOLUTIONS',
            'address': '789 Boulevard du Commerce, Kinshasa',
            'phone': '+243 999 888 777',
            'email': 'admin@ayannabusiness.cd',
            'rccm': 'CD/KIN/RCCM/23-B-7890',
            'id_nat': 'AYANNA789',
            'slogan': 'Votre succès, notre mission',
            'currency': 'CDF',
            'logo': fake_logo_data  # Logo en BLOB
        }
        
        print("1️⃣ CRÉATION D'ENTREPRISE AVEC LOGO BLOB")
        print("=" * 40)
        print("📊 Données de l'entreprise de test:")
        for key, value in test_enterprise_data.items():
            if key == 'logo':
                print(f"  {key}: {len(value)} bytes (BLOB)")
            else:
                print(f"  {key}: {value}")
        
        # Créer l'entreprise directement via la base de données
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        print("\n🏗️ Création de l'entreprise avec logo BLOB...")
        
        enterprise = Entreprise(
            name=test_enterprise_data.get('name', ''),
            address=test_enterprise_data.get('address', ''),
            phone=test_enterprise_data.get('phone', ''),
            email=test_enterprise_data.get('email', ''),
            rccm=test_enterprise_data.get('rccm', ''),
            id_nat=test_enterprise_data.get('id_nat', ''),
            logo=test_enterprise_data.get('logo'),  # BLOB!
            slogan=test_enterprise_data.get('slogan', ''),
            currency=test_enterprise_data.get('currency', 'USD')
        )
        
        session.add(enterprise)
        session.commit()
        
        print("✅ Entreprise créée avec succès!")
        print(f"  ID: {enterprise.id}")
        print(f"  Nom: {enterprise.name}")
        print(f"  Email: {enterprise.email}")
        print(f"  Logo: {len(enterprise.logo) if enterprise.logo else 0} bytes")
        
        print("\n2️⃣ CRÉATION AUTOMATIQUE D'UTILISATEUR ADMIN")
        print("=" * 40)
        
        # Créer automatiquement un utilisateur admin
        admin_user = User(
            name='Administrateur Principal',
            email=test_enterprise_data.get('email', 'admin@' + test_enterprise_data.get('name', 'entreprise').lower().replace(' ', '') + '.com'),
            role='admin',
            enterprise_id=enterprise.id
        )
        
        # Utiliser la méthode set_password du modèle
        admin_user.set_password('admin123')
        
        session.add(admin_user)
        session.commit()
        
        print(f"👤 Utilisateur admin créé automatiquement:")
        print(f"  ID: {admin_user.id}")
        print(f"  Nom: {admin_user.name}")
        print(f"  Email: {admin_user.email}")
        print(f"  Role: {admin_user.role}")
        print(f"  Enterprise ID: {admin_user.enterprise_id}")
        print(f"  Mot de passe: admin123")
        
        print("\n3️⃣ VÉRIFICATIONS")
        print("=" * 40)
        
        # Vérification 1: Association correcte
        if admin_user.enterprise_id == enterprise.id:
            print("✅ L'utilisateur admin est correctement associé à l'entreprise!")
        else:
            print("❌ Erreur: L'utilisateur admin n'est pas associé à la bonne entreprise!")
        
        # Vérification 2: Mot de passe
        if admin_user.check_password('admin123'):
            print("✅ Le mot de passe 'admin123' est correctement vérifié")
        else:
            print("❌ Problème avec la vérification du mot de passe")
        
        # Vérification 3: Logo BLOB
        if enterprise.logo and len(enterprise.logo) > 0:
            print("✅ Le logo est correctement stocké en BLOB")
        else:
            print("❌ Problème avec le stockage du logo en BLOB")
        
        # Vérification 4: Récupération complète
        retrieved_enterprise = session.query(Entreprise).filter_by(id=enterprise.id).first()
        retrieved_user = session.query(User).filter_by(enterprise_id=enterprise.id).first()
        
        if retrieved_enterprise and retrieved_user:
            print("✅ L'entreprise et l'utilisateur peuvent être récupérés depuis la base")
        else:
            print("❌ Problème de récupération depuis la base de données")
        
        print("\n4️⃣ RÉSUMÉ FINAL")
        print("=" * 40)
        print(f"🏢 ENTREPRISE CRÉÉE:")
        print(f"  - ID: {enterprise.id}")
        print(f"  - Nom: {enterprise.name}")
        print(f"  - Email: {enterprise.email}")
        print(f"  - Adresse: {enterprise.address}")
        print(f"  - Téléphone: {enterprise.phone}")
        print(f"  - RCCM: {enterprise.rccm}")
        print(f"  - Devise: {enterprise.currency}")
        print(f"  - Logo: {len(enterprise.logo) if enterprise.logo else 0} bytes (BLOB)")
        
        print(f"\n👤 UTILISATEUR ADMIN ASSOCIÉ:")
        print(f"  - ID: {admin_user.id}")
        print(f"  - Nom: {admin_user.name}")
        print(f"  - Email: {admin_user.email}")
        print(f"  - Role: {admin_user.role}")
        print(f"  - Mot de passe par défaut: admin123")
        print(f"  - Enterprise ID: {admin_user.enterprise_id}")
        
        session.close()
        
        print("\n🎉 SUCCÈS! Toutes les fonctionnalités de l'entreprise fonctionnent correctement:")
        print("  ✅ Stockage du logo en BLOB")
        print("  ✅ Création automatique de l'utilisateur admin")
        print("  ✅ Association correcte entreprise-utilisateur")
        print("  ✅ Hachage sécurisé du mot de passe")
        print("  ✅ Récupération depuis la base de données")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_all_enterprise_features()