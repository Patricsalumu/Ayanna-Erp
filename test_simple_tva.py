#!/usr/bin/env python3
"""
Test simple pour vérifier la configuration TVA
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaConfig, ComptaComptes

def test_configuration_tva():
    """Test de la configuration TVA"""
    print("=== Test de la configuration TVA ===")
    
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    try:
        # 1. Vérifier les configurations existantes
        print("\n1. Configurations existantes:")
        configs = session.query(ComptaConfig).all()
        for config in configs:
            print(f"   POS {config.pos_id}:")
            print(f"     - Compte caisse: {config.compte_caisse_id}")
            print(f"     - Compte TVA: {getattr(config, 'compte_tva_id', 'NON DÉFINI')}")
            print(f"     - Compte vente (obsolète): {getattr(config, 'compte_vente_id', 'ABSENT')}")
            
            # Vérifier si le compte TVA existe
            if hasattr(config, 'compte_tva_id') and config.compte_tva_id:
                compte_tva = session.query(ComptaComptes).filter_by(id=config.compte_tva_id).first()
                if compte_tva:
                    print(f"     ✅ Compte TVA existant: {compte_tva.numero} - {compte_tva.nom}")
                else:
                    print(f"     ❌ Compte TVA configuré mais inexistant")
            else:
                print(f"     ⚠️  Aucun compte TVA configuré")
            print()
        
        # 2. Lister tous les comptes TVA disponibles (classe 44)
        print("2. Comptes TVA disponibles (classe 44):")
        from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ComptabiliteController
        comptabilite_controller = ComptabiliteController()
        
        comptes_tva = comptabilite_controller.get_comptes_par_classe(1, '44')
        if comptes_tva:
            for compte in comptes_tva:
                print(f"   - {compte.numero}: {compte.nom} (ID: {compte.id})")
        else:
            print("   ❌ Aucun compte TVA trouvé")
        
        # 3. Tester la mise à jour de la configuration pour ajouter un compte TVA
        if comptes_tva and configs:
            print(f"\n3. Test de mise à jour de configuration avec compte TVA...")
            config = configs[0]  # Premier POS
            compte_tva = comptes_tva[0]  # Premier compte TVA
            
            print(f"   Ajout du compte TVA {compte_tva.numero} au POS {config.pos_id}")
            
            comptabilite_controller.set_compte_config(
                enterprise_id=1,  # TODO: récupérer depuis le POS
                pos_id=config.pos_id,
                compte_tva_id=compte_tva.id
            )
            
            # Vérifier la mise à jour
            config_updated = session.query(ComptaConfig).filter_by(pos_id=config.pos_id).first()
            if config_updated and hasattr(config_updated, 'compte_tva_id') and config_updated.compte_tva_id == compte_tva.id:
                print(f"   ✅ Configuration mise à jour avec succès")
            else:
                print(f"   ❌ Échec de la mise à jour")
        
        print("\n✅ Test terminé")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_configuration_tva()