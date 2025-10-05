#!/usr/bin/env python3
"""
Test rapide pour vérifier la création de client avec pos_id
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.modules.boutique.controller.boutique_controller import BoutiqueController
from ayanna_erp.database.database_manager import DatabaseManager

def test_create_client():
    """Test de création de client avec pos_id"""
    try:
        # Initialisation
        db_manager = DatabaseManager()
        pos_id = 1  # ID fictif pour test
        controller = BoutiqueController(pos_id)
        
        # Test de création de client
        with db_manager.get_session() as session:
            test_client = controller.create_client(
                session=session,
                nom="Mbalu",
                prenom="Deborah",
                telephone="+243997554905",
                email="deborah@example.com",
                adresse="123 Rue Test, Kinshasa"
            )
            
            print(f"✅ Client créé avec succès!")
            print(f"   ID: {test_client.id}")
            print(f"   Nom: {test_client.nom} {test_client.prenom}")
            print(f"   POS ID: {test_client.pos_id}")
            print(f"   Téléphone: {test_client.telephone}")
            print(f"   Email: {test_client.email}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la création du client: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🧪 Test de création de client avec pos_id")
    print("=" * 50)
    
    test_create_client()

if __name__ == "__main__":
    main()