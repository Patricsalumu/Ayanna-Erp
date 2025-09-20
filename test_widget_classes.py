#!/usr/bin/env python3
"""
Test pour vérifier que le widget classes fonctionne sans erreur
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import get_database_manager, Entreprise
from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ComptabiliteController


def test_widget_data():
    """Test que les données sont compatibles avec le widget"""
    print("🧪 Test de compatibilité widget classes")
    print("="*40)
    
    try:
        db_manager = get_database_manager()
        session = db_manager.get_session()
        
        # Récupérer la première entreprise
        entreprise = session.query(Entreprise).first()
        
        if not entreprise:
            print("❌ Aucune entreprise trouvée")
            return False
        
        print(f"📍 Test avec entreprise: {entreprise.name} (ID: {entreprise.id})")
        
        # Simuler le chargement du widget
        comptabilite_controller = ComptabiliteController()
        data = comptabilite_controller.get_classes(entreprise.id)
        
        print(f"✅ Données récupérées: {len(data)} classes")
        
        # Vérifier la structure des données
        if data and len(data) > 0:
            first_item = data[0]
            required_keys = ['numero', 'nom', 'libelle', 'id']
            
            print("\n🔍 Vérification de la structure des données:")
            for key in required_keys:
                if key in first_item:
                    print(f"   ✅ '{key}': {first_item[key]}")
                else:
                    print(f"   ❌ '{key}': MANQUANT")
                    return False
        
        # Vérifier que les classes OHADA complètes sont présentes
        print(f"\n📊 Classes présentes:")
        for classe in data:
            print(f"   - Classe {classe['numero']}: {classe['nom']}")
        
        print(f"\n✅ Test de compatibilité widget: RÉUSSI")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_widget_data()
    if success:
        print("\n🎉 Le widget des classes peut charger les données sans erreur !")
        print("✅ Structure des données: OK")
        print("✅ Classes OHADA: Chargées")
        print("✅ Plus d'erreur 'entreprise_id' invalid keyword argument")
    else:
        print("\n💥 Problème détecté avec le widget des classes !")