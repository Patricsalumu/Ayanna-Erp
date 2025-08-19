#!/usr/bin/env python3
"""
Test direct de la méthode open_config_dialog
"""
import sys
sys.path.insert(0, '.')

from PyQt6.QtWidgets import QApplication

print("🔍 Test direct de open_config_dialog...")

try:
    app = QApplication(sys.argv)
    
    # Importer directement les modèles et créer une session
    from ayanna_erp.database.database_manager import DatabaseManager
    from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ClasseComptable, CompteComptable
    
    db = DatabaseManager()
    session = db.get_session()
    
    print("✅ Session créée")
    
    # Tester la requête exacte qui cause l'erreur selon le traceback
    print("🔍 Test de la requête problématique...")
    
    # Simuler entreprise_id = 1
    entreprise_id = 1
    
    try:
        # Cette requête est celle de la ligne 234 dans open_config_dialog
        comptes = session.query(CompteComptable).join(ClasseComptable).filter(ClasseComptable.enterprise_id == entreprise_id).all()
        print(f"✅ Requête réussie! {len(comptes)} comptes trouvés")
        
        # Tester les autres parties de la méthode
        comptes_caisse = [c for c in comptes if str(c.numero).startswith('5')]
        comptes_frais = [c for c in comptes if str(c.numero).startswith('7')]
        comptes_client = [c for c in comptes if str(c.numero).startswith('4')]
        
        print(f"✅ Comptes caisse: {len(comptes_caisse)}")
        print(f"✅ Comptes frais: {len(comptes_frais)}")
        print(f"✅ Comptes client: {len(comptes_client)}")
        
    except Exception as e:
        print(f"❌ Erreur dans la requête: {e}")
        import traceback
        traceback.print_exc()
    
    # Tester avec l'ancien nom pour confirmer l'erreur
    try:
        print("🔍 Test avec entreprise_id (devrait échouer)...")
        comptes = session.query(CompteComptable).join(ClasseComptable).filter(ClasseComptable.entreprise_id == entreprise_id).all()
        print("⚠️ Requête réussie avec entreprise_id (ne devrait pas)")
    except Exception as e:
        print(f"✅ Erreur attendue avec entreprise_id: {e}")
    
    session.close()
    print("✅ Test terminé")
        
except Exception as e:
    print(f"❌ Erreur générale: {e}")
    import traceback
    traceback.print_exc()
