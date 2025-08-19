#!/usr/bin/env python3
"""
Test de debug pour identifier l'erreur dans CompteWidget
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

print("🔍 Test de debug pour l'erreur ComptaClasses...")

try:
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Importer le modèle pour vérifier les attributs
    from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaClasses, ComptaComptes
    print(f"✅ ComptaClasses importé avec succès")
    print(f"✅ Attributs de ComptaClasses: {[attr for attr in dir(ComptaClasses) if not attr.startswith('_')]}")
    
    # Vérifier que enterprise_id existe
    if hasattr(ComptaClasses, 'enterprise_id'):
        print("✅ ComptaClasses.enterprise_id existe")
    else:
        print("❌ ComptaClasses.enterprise_id n'existe pas")
        
    if hasattr(ComptaClasses, 'entreprise_id'):
        print("⚠️ ComptaClasses.entreprise_id existe (ancien nom)")
    else:
        print("✅ ComptaClasses.entreprise_id n'existe pas (correct)")
    
    # Tester les alias
    from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ClasseComptable, CompteComptable
    print(f"✅ Alias importés avec succès")
    print(f"✅ ClasseComptable est: {ClasseComptable}")
    print(f"✅ CompteComptable est: {CompteComptable}")
    
    # Vérifier les attributs de l'alias
    if hasattr(ClasseComptable, 'enterprise_id'):
        print("✅ ClasseComptable.enterprise_id existe")
    else:
        print("❌ ClasseComptable.enterprise_id n'existe pas")
        
    if hasattr(ClasseComptable, 'entreprise_id'):
        print("⚠️ ClasseComptable.entreprise_id existe (ancien nom)")
    else:
        print("✅ ClasseComptable.entreprise_id n'existe pas (correct)")
    
    # Simuler la session de base de données
    from ayanna_erp.database.database_manager import DatabaseManager
    db = DatabaseManager()
    session = db.get_session()
    
    print("✅ Session de base de données créée")
    
    # Tester la requête problématique
    print("🔍 Test de la requête sur CompteComptable avec ClasseComptable...")
    
    try:
        # Cette requête devrait fonctionner avec enterprise_id
        comptes = session.query(CompteComptable).join(ClasseComptable).filter(ClasseComptable.enterprise_id == 1).all()
        print(f"✅ Requête avec ClasseComptable.enterprise_id réussie: {len(comptes)} comptes trouvés")
    except Exception as e:
        print(f"❌ Erreur avec ClasseComptable.enterprise_id: {e}")
    
    try:
        # Cette requête devrait échouer avec entreprise_id
        comptes = session.query(CompteComptable).join(ClasseComptable).filter(ClasseComptable.entreprise_id == 1).all()
        print(f"⚠️ Requête avec ClasseComptable.entreprise_id réussie (ne devrait pas): {len(comptes)} comptes trouvés")
    except Exception as e:
        print(f"✅ Erreur attendue avec ClasseComptable.entreprise_id: {e}")
    
    session.close()
    print("✅ Test terminé avec succès!")
    
except Exception as e:
    print(f"❌ Erreur dans le test: {e}")
    import traceback
    traceback.print_exc()
