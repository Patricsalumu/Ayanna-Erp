"""
Test de validation de la création de clients
"""

import os
import sys

# Ajouter le chemin vers le projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.boutique.controller.boutique_controller import BoutiqueController

def test_client_creation():
    """Test de création de clients avec différents scénarios"""
    
    print("=== Test de création de clients ===\n")
    
    try:
        db_manager = DatabaseManager()
        controller = BoutiqueController(pos_id=1)
        
        # Test 1: Client avec tous les champs
        print("1. Test avec tous les champs...")
        with db_manager.get_session() as session:
            client1 = controller.create_client(
                session,
                nom="Dupont",
                prenom="Jean",
                email="jean.dupont@email.com",
                telephone="+243 123 456 789",
                adresse="123 Rue de la Paix, Kinshasa"
            )
            print(f"✅ Client complet créé: {client1.nom} {client1.prenom} (ID: {client1.id})")
        
        # Test 2: Client avec seulement le nom (champs optionnels vides)
        print("\n2. Test avec nom seulement...")
        with db_manager.get_session() as session:
            client2 = controller.create_client(
                session,
                nom="Mbala"
            )
            print(f"✅ Client minimal créé: {client2.nom} (ID: {client2.id})")
        
        # Test 3: Client avec nom et email seulement
        print("\n3. Test avec nom et email...")
        with db_manager.get_session() as session:
            client3 = controller.create_client(
                session,
                nom="Tshimanga",
                email="tshimanga@email.com"
            )
            print(f"✅ Client partiel créé: {client3.nom} (ID: {client3.id})")
        
        # Test 4: Vérifier la récupération des clients
        print("\n4. Test de récupération des clients...")
        with db_manager.get_session() as session:
            clients = controller.get_clients(session)
            print(f"✅ {len(clients)} clients récupérés:")
            for client in clients:
                prenom = client.prenom if client.prenom else "(pas de prénom)"
                telephone = client.telephone if client.telephone else "(pas de téléphone)"
                email = client.email if client.email else "(pas d'email)"
                print(f"   - {client.nom} {prenom} | {telephone} | {email}")
        
        print("\n=== TOUS LES TESTS ONT RÉUSSI ===")
        print("✅ Création de clients avec champs optionnels fonctionnelle")
        print("✅ Les champs prenom et telephone peuvent être NULL")
        print("✅ La récupération des clients fonctionne correctement")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_client_creation()
    if success:
        print("\n🎉 Validation des clients réussie !")
    else:
        print("\n💥 Échec de la validation des clients")
        sys.exit(1)