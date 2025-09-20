#!/usr/bin/env python3
"""
Script pour créer les POS manquants pour toutes les entreprises existantes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import get_database_manager


def create_missing_pos():
    """Créer les POS manquants pour toutes les entreprises"""
    print("🏭 Création des POS manquants pour toutes les entreprises")
    print("=" * 60)
    
    try:
        db_manager = get_database_manager()
        session = db_manager.get_session()
        
        from ayanna_erp.database.database_manager import Entreprise, POSPoint
        
        # Lister toutes les entreprises
        enterprises = session.query(Entreprise).all()
        print(f"📊 {len(enterprises)} entreprises trouvées")
        
        # Créer une liste des entreprises qui ont besoin de POS
        enterprises_needing_pos = []
        
        for enterprise in enterprises:
            enterprise_id = enterprise.id
            enterprise_name = enterprise.name
            
            # Vérifier les POS existants
            existing_pos = session.query(POSPoint).filter_by(enterprise_id=enterprise_id).count()
            print(f"\n🏢 {enterprise_name} (ID: {enterprise_id})")
            print(f"   POS existants: {existing_pos}")
            
            if existing_pos == 0:
                enterprises_needing_pos.append((enterprise_id, enterprise_name))
            else:
                print(f"   ✅ L'entreprise a déjà des POS configurés")
        
        session.close()
        
        # Créer les POS pour les entreprises qui en ont besoin
        for enterprise_id, enterprise_name in enterprises_needing_pos:
            print(f"\n➡️ Création des POS pour l'entreprise {enterprise_name}")
            
            # Utiliser la méthode existante pour créer les POS
            success = db_manager.create_pos_for_new_enterprise(enterprise_id)
            
            if success:
                print(f"   ✅ POS créés avec succès pour {enterprise_name}")
                
                # Vérifier les POS créés avec une nouvelle session
                new_session = db_manager.get_session()
                new_pos = new_session.query(POSPoint).filter_by(enterprise_id=enterprise_id).all()
                print(f"   📋 {len(new_pos)} POS créés:")
                for pos in new_pos:
                    print(f"      - {pos.name} (Module ID: {pos.module_id})")
                new_session.close()
            else:
                print(f"   ❌ Échec de la création des POS pour {enterprise_name}")
        
        print(f"\n🎯 Traitement terminé pour {len(enterprises)} entreprises")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des POS: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_pos_creation():
    """Vérifier que tous les POS ont été créés"""
    print("\n🔍 Vérification des POS créés")
    print("=" * 40)
    
    try:
        db_manager = get_database_manager()
        session = db_manager.get_session()
        
        from ayanna_erp.database.database_manager import Entreprise, POSPoint
        
        enterprises = session.query(Entreprise).all()
        total_enterprises = len(enterprises)
        enterprises_with_pos = 0
        
        for enterprise in enterprises:
            pos_count = session.query(POSPoint).filter_by(enterprise_id=enterprise.id).count()
            if pos_count > 0:
                enterprises_with_pos += 1
                print(f"   ✅ {enterprise.name}: {pos_count} POS")
            else:
                print(f"   ❌ {enterprise.name}: 0 POS")
        
        session.close()
        
        print(f"\n📊 Résumé:")
        print(f"   • Total entreprises: {total_enterprises}")
        print(f"   • Entreprises avec POS: {enterprises_with_pos}")
        print(f"   • Taux de couverture: {(enterprises_with_pos/total_enterprises)*100:.1f}%")
        
        return enterprises_with_pos == total_enterprises
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Démarrage de la création des POS manquants")
    print("="*60)
    
    success = create_missing_pos()
    
    if success:
        verification_success = verify_pos_creation()
        if verification_success:
            print("\n🎉 Tous les POS ont été créés avec succès!")
        else:
            print("\n⚠️ Certains POS n'ont pas pu être créés")
    else:
        print("\n❌ Échec de la création des POS!")
    
    print("\n" + "="*60)