#!/usr/bin/env python3
"""
Script de test pour vérifier la configuration des comptes avec TVA
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ComptabiliteController
from ayanna_erp.database.database_manager import DatabaseManager

def test_compte_config_with_tva():
    """Test de la configuration des comptes avec TVA"""
    print("=== Test de la configuration des comptes avec TVA ===")
    
    controller = ComptabiliteController()
    
    # ID d'entreprise test (supposons 1)
    enterprise_id = 1
    pos_id = 1
    
    try:
        # 1. Récupérer les comptes TVA (classe 44)
        print("\n1. Récupération des comptes TVA (classe 44)...")
        comptes_tva = controller.get_comptes_par_classe(enterprise_id, '44')
        print(f"   Nombre de comptes TVA trouvés: {len(comptes_tva)}")
        for compte in comptes_tva:
            print(f"   - {compte.numero}: {compte.nom}")
        
        # 2. Tester la création/mise à jour d'une configuration avec TVA
        print("\n2. Test de création d'une configuration avec TVA...")
        tva_account_id = comptes_tva[0].id if comptes_tva else None
        
        controller.set_compte_config(
            enterprise_id=enterprise_id,
            pos_id=pos_id,
            compte_tva_id=tva_account_id
        )
        print("   Configuration avec TVA créée avec succès")
        
        # 3. Récupérer la configuration pour vérifier
        print("\n3. Vérification de la configuration sauvegardée...")
        config = controller.get_compte_config(enterprise_id, pos_id)
        if config:
            print(f"   Configuration trouvée:")
            print(f"   - Compte TVA ID: {config.compte_tva_id}")
            print(f"   - Compte vente ID (devrait être None ou absent): {getattr(config, 'compte_vente_id', 'ABSENT')}")
        else:
            print("   Aucune configuration trouvée")
        
        print("\n✅ Test terminé avec succès!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_compte_config_with_tva()