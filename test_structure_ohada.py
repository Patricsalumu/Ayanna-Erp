#!/usr/bin/env python3
"""
Test pour vérifier que les classes OHADA sont créées avec la structure correcte:
Classes 1 à 8 + classe spéciale 44 pour les taxes
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import get_database_manager, Entreprise
from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ComptabiliteController


def test_correct_structure():
    """Test de la structure correcte des classes OHADA"""
    print("🧪 Test de la structure des classes OHADA (1-8 + 44)")
    print("="*55)
    
    try:
        db_manager = get_database_manager()
        session = db_manager.get_session()
        
        # Récupérer la première entreprise
        entreprise = session.query(Entreprise).first()
        
        if not entreprise:
            print("❌ Aucune entreprise trouvée")
            return False
        
        print(f"📍 Test avec entreprise: {entreprise.name} (ID: {entreprise.id})")
        
        # Récupérer les classes
        comptabilite_controller = ComptabiliteController()
        classes_data = comptabilite_controller.get_classes(entreprise.id)
        
        print(f"✅ Classes récupérées: {len(classes_data)}")
        
        # Structure attendue
        expected_codes = ['1', '2', '3', '4', '5', '6', '7', '8', '44']
        
        print(f"\n📋 Classes attendues: {', '.join(expected_codes)}")
        
        # Vérifier les classes présentes
        codes_presents = [str(c['numero']) for c in classes_data]
        codes_presents.sort(key=lambda x: int(x) if x.isdigit() else 999)  # Tri numérique
        
        print(f"📊 Classes présentes: {', '.join(codes_presents)}")
        
        # Vérifications
        print(f"\n🔍 Vérifications détaillées:")
        
        # 1. Vérifier que nous avons exactement 9 classes
        if len(classes_data) == 9:
            print(f"   ✅ Nombre de classes: 9 (correct)")
        else:
            print(f"   ❌ Nombre de classes: {len(classes_data)} (attendu: 9)")
        
        # 2. Vérifier les classes 1 à 8
        classes_1_8_manquantes = []
        for i in range(1, 9):
            if str(i) not in codes_presents:
                classes_1_8_manquantes.append(str(i))
        
        if not classes_1_8_manquantes:
            print(f"   ✅ Classes 1-8: toutes présentes")
        else:
            print(f"   ❌ Classes 1-8 manquantes: {', '.join(classes_1_8_manquantes)}")
        
        # 3. Vérifier la classe spéciale 44
        if '44' in codes_presents:
            classe_44 = next(c for c in classes_data if str(c['numero']) == '44')
            print(f"   ✅ Classe 44 (taxes): {classe_44['nom']}")
        else:
            print(f"   ❌ Classe 44 (taxes): MANQUANTE")
        
        # 4. Vérifier qu'il n'y a pas de classe 9
        if '9' not in codes_presents:
            print(f"   ✅ Classe 9: absente (correct, remplacée par 44)")
        else:
            print(f"   ⚠️  Classe 9: présente (devrait être remplacée par 44)")
        
        # 5. Afficher les détails de toutes les classes
        print(f"\n📄 Détail des classes:")
        for classe in sorted(classes_data, key=lambda x: int(x['numero']) if str(x['numero']).isdigit() else 999):
            print(f"   Classe {classe['numero']}: {classe['nom']}")
        
        # Vérification finale
        structure_correcte = (
            len(classes_data) == 9 and
            all(str(i) in codes_presents for i in range(1, 9)) and
            '44' in codes_presents and
            '9' not in codes_presents
        )
        
        if structure_correcte:
            print(f"\n✅ Structure des classes: CORRECTE")
            print(f"✅ Classes 1-8 + classe spéciale 44 pour les taxes")
        else:
            print(f"\n❌ Structure des classes: INCORRECTE")
        
        session.close()
        return structure_correcte
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_correct_structure()
    if success:
        print("\n🎉 Test réussi !")
        print("✅ Structure OHADA: Classes 1-8 + 44 (taxes)")
        print("✅ Classe spéciale 44 pour les taxes séparée de la classe 4")
        print("✅ Respect de votre logique comptable personnalisée")
    else:
        print("\n💥 Test échoué !")
        print("❌ La structure ne correspond pas à l'attendu")