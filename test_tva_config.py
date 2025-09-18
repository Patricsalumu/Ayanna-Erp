#!/usr/bin/env python3
"""
Test pour vérifier la configuration et l'utilisation du compte TVA
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ComptabiliteController

def test_tva_configuration():
    """Test la configuration du compte TVA"""
    print("🔍 Test de la configuration du compte TVA")
    print("=" * 50)
    
    # Initialiser les composants
    controller = ComptabiliteController()
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    try:
        # Test 1: Vérifier qu'il y a des comptes TVA (classe 44)
        print("\n1️⃣ Vérification des comptes TVA disponibles...")
        comptes_tva = controller.get_comptes_par_classe(1, '44')  # Enterprise ID = 1
        print(f"   Comptes TVA trouvés: {len(comptes_tva)}")
        for compte in comptes_tva:
            print(f"   - {compte.numero} - {compte.nom}")
        
        # Test 2: Vérifier la configuration actuelle
        print("\n2️⃣ Vérification de la configuration actuelle...")
        config = controller.get_compte_config(1, 1)  # Enterprise ID = 1, POS ID = 1
        if config:
            print(f"   Configuration trouvée:")
            print(f"   - Compte caisse: {config.compte_caisse_id}")
            print(f"   - Compte banque: {config.compte_banque_id}")
            print(f"   - Compte client: {config.compte_client_id}")
            print(f"   - Compte fournisseur: {config.compte_fournisseur_id}")
            print(f"   - Compte TVA: {config.compte_tva_id}")
            print(f"   - Compte achat: {config.compte_achat_id}")
            
            # Vérifier le compte vente (devrait être None ou absent)
            if hasattr(config, 'compte_vente_id'):
                print(f"   - Compte vente (obsolète): {config.compte_vente_id}")
            else:
                print(f"   ✅ Compte vente supprimé comme prévu")
        else:
            print("   ❌ Aucune configuration trouvée")
        
        # Test 3: Tester la configuration du compte TVA
        if comptes_tva and config:
            print("\n3️⃣ Test de configuration du compte TVA...")
            premier_compte_tva = comptes_tva[0]
            controller.set_compte_config(
                1, 1,  # Enterprise ID = 1, POS ID = 1
                compte_tva_id=premier_compte_tva.id
            )
            
            # Vérifier que la configuration a été sauvegardée
            config_updated = controller.get_compte_config(1, 1)
            if config_updated and config_updated.compte_tva_id == premier_compte_tva.id:
                print(f"   ✅ Compte TVA configuré avec succès: {premier_compte_tva.numero} - {premier_compte_tva.nom}")
            else:
                print(f"   ❌ Échec de la configuration du compte TVA")
        
        # Test 4: Vérifier que la méthode set_compte_config ne gère plus compte_vente_id
        print("\n4️⃣ Test de suppression du compte vente...")
        import inspect
        sig = inspect.signature(controller.set_compte_config)
        params = list(sig.parameters.keys())
        print(f"   Paramètres de set_compte_config: {params}")
        
        if 'compte_vente_id' in params:
            print("   ❌ compte_vente_id encore présent dans set_compte_config")
        else:
            print("   ✅ compte_vente_id supprimé de set_compte_config")
            
        if 'compte_tva_id' in params:
            print("   ✅ compte_tva_id présent dans set_compte_config")
        else:
            print("   ❌ compte_tva_id manquant dans set_compte_config")
        
        print("\n" + "=" * 50)
        print("✅ Test terminé avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_tva_configuration()