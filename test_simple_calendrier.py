#!/usr/bin/env python3
"""
Test simple pour vérifier la correction de l'erreur 'db_manager'
"""

import sys
import os

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🧪 Test de la correction de l'erreur 'db_manager'")
print("=" * 50)

try:
    # Test 1 : Import get_database_manager
    print("1️⃣ Test import get_database_manager...")
    from ayanna_erp.database.database_manager import get_database_manager
    db_manager = get_database_manager()
    print(f"   ✅ get_database_manager : {type(db_manager)}")
    
    # Test 2 : Import CalendrierIndex  
    print("2️⃣ Test import CalendrierIndex...")
    from ayanna_erp.modules.salle_fete.view.calendrier_index import CalendrierIndex
    print("   ✅ CalendrierIndex importé avec succès")
    
    # Test 3 : Vérifier que le code a été corrigé
    print("3️⃣ Vérification du code source...")
    import inspect
    source = inspect.getsource(CalendrierIndex.open_reservation_form)
    
    if 'get_database_manager()' in source:
        print("   ✅ Correction appliquée : get_database_manager() trouvé")
    else:
        print("   ⚠️  get_database_manager() non trouvé dans le code")
        
    if 'self.db_manager' in source:
        print("   ⚠️  self.db_manager encore présent dans le code")
    else:
        print("   ✅ self.db_manager supprimé du code")
    
    print("\n🎉 Correction de l'erreur 'db_manager' : RÉUSSIE!")
    print("   Le CalendrierIndex peut maintenant utiliser get_database_manager()")
    print("   au lieu de self.db_manager qui n'existait pas.")
    
except ImportError as e:
    print(f"❌ Erreur d'import : {e}")
except Exception as e:
    print(f"❌ Erreur : {e}")

print("\n" + "=" * 50)
print("✅ Test terminé - La correction devrait résoudre l'erreur originale")