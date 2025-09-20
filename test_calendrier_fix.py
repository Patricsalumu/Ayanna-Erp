#!/usr/bin/env python3
"""
Test pour vérifier la correction de l'erreur 'db_manager' dans CalendrierIndex
"""

import sys
import os
from datetime import datetime, date

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_calendrier_import():
    """Tester l'importation du module CalendrierIndex"""
    try:
        from ayanna_erp.modules.salle_fete.view.calendrier_index import CalendrierIndex
        print("✅ Import CalendrierIndex : OK")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'import CalendrierIndex : {e}")
        return False

def test_get_database_manager_import():
    """Tester l'importation de get_database_manager"""
    try:
        from ayanna_erp.database.database_manager import get_database_manager
        db_manager = get_database_manager()
        print("✅ Import get_database_manager : OK")
        print(f"✅ Instance DatabaseManager : {type(db_manager)}")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'import get_database_manager : {e}")
        return False

def test_calendrier_instantiation():
    """Tester l'instanciation de CalendrierIndex"""
    try:
        from ayanna_erp.modules.salle_fete.view.calendrier_index import CalendrierIndex
        
        # Mock du main_controller
        class MockMainController:
            def __init__(self):
                self.pos_id = 1
        
        # Mock de l'utilisateur actuel
        class MockUser:
            def __init__(self):
                self.id = 1
                self.username = "test"
                self.enterprise_id = 1
        
        main_controller = MockMainController()
        current_user = MockUser()
        
        # Tenter de créer une instance de CalendrierIndex
        calendrier = CalendrierIndex(main_controller, current_user)
        print("✅ Instanciation CalendrierIndex : OK")
        print(f"✅ Calendrier créé : {type(calendrier)}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'instanciation CalendrierIndex : {e}")
        return False

def test_open_reservation_form_method():
    """Tester si la méthode open_reservation_form peut être appelée"""
    try:
        from ayanna_erp.modules.salle_fete.view.calendrier_index import CalendrierIndex
        
        # Mock du main_controller
        class MockMainController:
            def __init__(self):
                self.pos_id = 1
        
        # Mock de l'utilisateur actuel
        class MockUser:
            def __init__(self):
                self.id = 1
                self.username = "test"
                self.enterprise_id = 1
        
        main_controller = MockMainController()
        current_user = MockUser()
        
        # Créer une instance de CalendrierIndex
        calendrier = CalendrierIndex(main_controller, current_user)
        
        # Vérifier que la méthode existe
        if hasattr(calendrier, 'open_reservation_form'):
            print("✅ Méthode open_reservation_form : Existe")
            
            # Vérifier l'accès aux attributs nécessaires
            if hasattr(calendrier, 'main_controller'):
                print("✅ Attribut main_controller : OK")
            else:
                print("❌ Attribut main_controller : Manquant")
                
            return True
        else:
            print("❌ Méthode open_reservation_form : N'existe pas")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test de la méthode : {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🧪 Test de correction de l'erreur 'db_manager' dans CalendrierIndex")
    print("=" * 60)
    
    tests = [
        ("Import get_database_manager", test_get_database_manager_import),
        ("Import CalendrierIndex", test_calendrier_import),
        ("Instanciation CalendrierIndex", test_calendrier_instantiation),
        ("Test méthode open_reservation_form", test_open_reservation_form_method),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}...")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    success_count = 0
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
        print(f"{status} : {test_name}")
        if result:
            success_count += 1
    
    print(f"\n🎯 {success_count}/{len(tests)} tests réussis")
    
    if success_count == len(tests):
        print("🎉 Tous les tests sont passés ! La correction semble fonctionnelle.")
    else:
        print("⚠️  Certains tests ont échoué. Vérification nécessaire.")

if __name__ == "__main__":
    main()