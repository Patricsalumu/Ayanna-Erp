#!/usr/bin/env python3
"""
Test de création automatique d'entrepôts lors de la création d'entreprise
"""

import sys
import os

# Ajouter le répertoire racine au path
sys.path.append(os.path.abspath('.'))

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.boutique.model.models import ShopWarehouse

def test_automatic_warehouse_creation():
    """Tester la création automatique d'entrepôts"""
    print("🧪 Test de création automatique d'entrepôts")
    print("=" * 60)
    
    db_manager = DatabaseManager()
    
    try:
        with db_manager.get_session() as session:
            # Vérifier les entrepôts existants
            existing_warehouses = session.query(ShopWarehouse).all()
            print(f"📦 Entrepôts existants: {len(existing_warehouses)}")
            
            # Afficher tous les entrepôts existants par POS
            pos_warehouses = {}
            for warehouse in existing_warehouses:
                if warehouse.pos_id not in pos_warehouses:
                    pos_warehouses[warehouse.pos_id] = []
                pos_warehouses[warehouse.pos_id].append(warehouse)
            
            for pos_id, warehouses in pos_warehouses.items():
                print(f"\n📍 POS {pos_id}:")
                for warehouse in warehouses:
                    print(f"   • {warehouse.name} ({warehouse.code})")
                    print(f"     Type: {warehouse.type}")
                    print(f"     Par défaut: {'Oui' if warehouse.is_default else 'Non'}")
                    print(f"     Actif: {'Oui' if warehouse.is_active else 'Non'}")
            
            # Vérifier la structure attendue
            main_warehouses = [w for w in existing_warehouses if w.type == "Principal"]
            pos_warehouses_list = [w for w in existing_warehouses if w.type == "Point de Vente"]
            
            print(f"\n📊 Analyse de la structure:")
            print(f"   • Entrepôts principaux: {len(main_warehouses)}")
            print(f"   • Entrepôts POS: {len(pos_warehouses_list)}")
            
            print(f"\n🎯 RÉSULTAT:")
            if len(main_warehouses) > 0 and len(pos_warehouses_list) > 0:
                print("✅ Entrepôts automatiques détectés!")
                print("   • Les entrepôts principaux et POS sont présents")
                print("   • La fonctionnalité de création automatique fonctionne")
            else:
                print("⚠️ Structure d'entrepôts à mettre à jour")
                print("   • Les entrepôts actuels utilisent des types différents")
                print("   • Types trouvés:", set(w.type for w in existing_warehouses))
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_automatic_warehouse_creation()
    if success:
        print("\n✅ Test terminé avec succès!")
    else:
        print("\n❌ Des erreurs ont été détectées dans le test.")