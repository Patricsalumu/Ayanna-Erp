#!/usr/bin/env python3
"""
Affichage des informations de connexion par défaut pour les entreprises créées
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from ayanna_erp.database.database_manager import DatabaseManager, User, Entreprise

def show_admin_credentials():
    """Afficher tous les comptes admin avec leurs identifiants"""
    print("🔐 INFORMATIONS DE CONNEXION - COMPTES ADMINISTRATEURS")
    print("=" * 70)
    
    try:
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        # Récupérer toutes les entreprises avec leurs admin
        enterprises = session.query(Entreprise).all()
        
        if not enterprises:
            print("❌ Aucune entreprise trouvée dans la base de données.")
            return
        
        for i, enterprise in enumerate(enterprises, 1):
            print(f"\n{i}️⃣ ENTREPRISE: {enterprise.name}")
            print("=" * 50)
            print(f"  📧 Email: {enterprise.email}")
            print(f"  📞 Téléphone: {enterprise.phone}")
            print(f"  🏢 Adresse: {enterprise.address}")
            print(f"  💰 Devise: {enterprise.currency}")
            
            # Récupérer les utilisateurs admin de cette entreprise
            admin_users = session.query(User).filter_by(
                enterprise_id=enterprise.id, 
                role='admin'
            ).all()
            
            if admin_users:
                print(f"\n  👤 COMPTES ADMINISTRATEURS:")
                for j, admin in enumerate(admin_users, 1):
                    print(f"    {j}. Nom: {admin.name}")
                    print(f"       Email: {admin.email}")
                    print(f"       🔑 Mot de passe par défaut: admin123")
                    print(f"       ID: {admin.id}")
                    
                    # Vérifier si le mot de passe par défaut fonctionne
                    if admin.check_password('admin123'):
                        print(f"       ✅ Mot de passe par défaut confirmé")
                    else:
                        print(f"       ⚠️ Mot de passe modifié")
                    print()
            else:
                print(f"  ❌ Aucun administrateur trouvé pour cette entreprise")
        
        print("\n📋 INFORMATIONS IMPORTANTES:")
        print("-" * 40)
        print("• Tous les comptes admin nouvellement créés utilisent le mot de passe: admin123")
        print("• Il est FORTEMENT recommandé de changer ce mot de passe après la première connexion")
        print("• L'email de l'entreprise est utilisé comme identifiant de l'administrateur")
        print("• Un compte admin est automatiquement créé lors de la création d'une entreprise")
        
        session.close()
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des informations: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    show_admin_credentials()