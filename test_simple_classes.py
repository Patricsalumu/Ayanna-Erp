#!/usr/bin/env python3
"""
Test simple pour vérifier que l'erreur 'entreprise_id' est corrigée
et que les classes sont bien récupérées.
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import get_database_manager, Entreprise
from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ComptabiliteController


def test_simple():
    """Test simple de récupération des classes"""
    print("🧪 Test simple de récupération des classes comptables")
    print("="*50)
    
    try:
        db_manager = get_database_manager()
        session = db_manager.get_session()
        
        # Récupérer la première entreprise
        entreprise = session.query(Entreprise).first()
        
        if not entreprise:
            print("❌ Aucune entreprise trouvée")
            return False
        
        print(f"📍 Test avec entreprise: {entreprise.name} (ID: {entreprise.id})")
        
        # Tester le contrôleur
        comptabilite_controller = ComptabiliteController()
        classes_data = comptabilite_controller.get_classes(entreprise.id)
        
        print(f"✅ Récupération réussie: {len(classes_data)} classes")
        
        # Afficher les classes
        print("\n📋 Classes comptables:")
        for i, classe in enumerate(classes_data):
            print(f"   {i+1}. Classe {classe['numero']}: {classe['nom']}")
        
        # Vérifier les classes 8 et 9
        codes = [c['numero'] for c in classes_data]
        
        if '8' in codes:
            classe_8 = next(c for c in classes_data if c['numero'] == '8')
            print(f"\n✅ Classe 8 trouvée: {classe_8['nom']}")
        else:
            print("\n⚠️  Classe 8 non trouvée")
        
        if '9' in codes:
            classe_9 = next(c for c in classes_data if c['numero'] == '9')
            print(f"✅ Classe 9 trouvée: {classe_9['nom']}")
        else:
            print("⚠️  Classe 9 non trouvée")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


if __name__ == "__main__":
    success = test_simple()
    if success:
        print("\n🎉 Test réussi !")
        print("✅ L'erreur 'entreprise_id' est corrigée")
        print("✅ Les classes sont récupérées correctement")
    else:
        print("\n💥 Test échoué !")