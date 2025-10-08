#!/usr/bin/env python3
"""
Script de test pour vérifier que les entrepôts ne sont créés que pour les modules appropriés
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.stock.models import StockWarehouse
from ayanna_erp.database.base import POSPoint, Module

def test_warehouse_creation():
    """Tester que les entrepôts ne sont créés que pour les bons modules"""
    print("🧪 Test de création des entrepôts par module")
    print("=" * 60)
    
    db_manager = DatabaseManager()
    
    try:
        with db_manager.get_session() as session:
            # Récupérer toutes les entreprises
            enterprises = session.execute("SELECT DISTINCT enterprise_id FROM core_pos_points").fetchall()
            
            if not enterprises:
                print("⚠️  Aucune entreprise trouvée")
                return
            
            # Modules qui devraient avoir des entrepôts
            modules_with_warehouses = {"Boutique", "Pharmacie", "Restaurant"}
            
            for enterprise_row in enterprises:
                enterprise_id = enterprise_row[0]
                print(f"\n📋 Entreprise {enterprise_id}:")
                
                # Récupérer tous les POS de cette entreprise avec leurs modules
                pos_points = session.query(POSPoint).join(Module).filter(
                    POSPoint.enterprise_id == enterprise_id
                ).all()
                
                for pos in pos_points:
                    module = session.query(Module).filter_by(id=pos.module_id).first()
                    
                    # Compter les entrepôts pour ce POS
                    warehouse_count = session.query(StockWarehouse).filter_by(
                        entreprise_id=enterprise_id
                    ).filter(
                        StockWarehouse.code.like(f"%_{pos.id}")
                    ).count()
                    
                    should_have_warehouses = module.name in modules_with_warehouses
                    has_warehouses = warehouse_count > 0
                    
                    # Status de la vérification
                    if should_have_warehouses and has_warehouses:
                        status = "✅ OK"
                    elif not should_have_warehouses and not has_warehouses:
                        status = "✅ OK"
                    elif should_have_warehouses and not has_warehouses:
                        status = "❌ MANQUE"
                    else:  # not should_have_warehouses and has_warehouses
                        status = "⚠️  TROP"
                    
                    print(f"  {status} - {pos.name} ({module.name}): {warehouse_count} entrepôts")
                    
                    # Détail des entrepôts si il y en a
                    if has_warehouses:
                        warehouses = session.query(StockWarehouse).filter_by(
                            entreprise_id=enterprise_id
                        ).filter(
                            StockWarehouse.code.like(f"%_{pos.id}")
                        ).all()
                        
                        for warehouse in warehouses:
                            print(f"    • {warehouse.name} ({warehouse.code})")
    
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_warehouse_creation()