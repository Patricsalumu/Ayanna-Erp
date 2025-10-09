#!/usr/bin/env python3
"""
Test spécifique du widget de mouvements
"""

import sys
import os

# Configuration du path
sys.path.insert(0, os.path.abspath('.'))

from ayanna_erp.database.database_manager import DatabaseManager
from sqlalchemy import text

def test_movement_query():
    """Test de la requête des mouvements"""
    print("=== TEST REQUÊTE MOUVEMENTS ===\n")
    
    db_manager = DatabaseManager()
    entreprise_id = 1
    
    try:
        with db_manager.get_session() as session:
            print("1. Test requête simplifiée...")
            try:
                result = session.execute(text("""
                    SELECT 
                        sm.movement_date,
                        sm.movement_type,
                        sm.quantity
                    FROM stock_mouvements sm
                    LIMIT 5
                """))
                movements = result.fetchall()
                print(f"✅ {len(movements)} mouvements récupérés")
                
                for i, mov in enumerate(movements):
                    print(f"   Mouvement {i+1}:")
                    print(f"   - Date: {mov[0]} (type: {type(mov[0])})")
                    print(f"   - Type: {mov[1]}")
                    print(f"   - Quantité: {mov[2]}")
                    
                    # Test du formatage de date
                    date_value = mov[0]
                    if date_value:
                        if hasattr(date_value, 'strftime'):
                            formatted = date_value.strftime("%d/%m/%Y %H:%M")
                            print(f"   - Date formatée: {formatted}")
                        else:
                            print(f"   - Date (string): {str(date_value)}")
                    print()
                    
            except Exception as e:
                print(f"❌ Erreur requête simple: {e}")
                import traceback
                traceback.print_exc()
            
            print("\n2. Test requête avec jointures...")
            try:
                result = session.execute(text("""
                    SELECT 
                        sm.movement_date,
                        sm.movement_type,
                        cp.name as product_name,
                        sw_origin.name as origin_warehouse,
                        sw_dest.name as dest_warehouse,
                        sm.quantity
                    FROM stock_mouvements sm
                    LEFT JOIN core_products cp ON sm.product_id = cp.id
                    LEFT JOIN stock_warehouses sw_origin ON sm.warehouse_id = sw_origin.id
                    LEFT JOIN stock_warehouses sw_dest ON sm.destination_warehouse_id = sw_dest.id
                    LIMIT 5
                """))
                movements = result.fetchall()
                print(f"✅ {len(movements)} mouvements avec jointures récupérés")
                
                for mov in movements:
                    print(f"   - Date: {mov[0]}, Produit: {mov[2]}, Origine: {mov[3]}, Dest: {mov[4]}")
                    
            except Exception as e:
                print(f"❌ Erreur requête avec jointures: {e}")
                import traceback
                traceback.print_exc()
            
            print("\n3. Test requête complète avec filtres...")
            try:
                result = session.execute(text("""
                    SELECT 
                        sm.movement_date,
                        sm.movement_type,
                        cp.name as product_name,
                        sw_origin.name as origin_warehouse,
                        sw_dest.name as dest_warehouse,
                        sm.quantity,
                        sm.unit_cost,
                        sm.total_cost,
                        sm.reference,
                        sm.description,
                        'Utilisateur ' || COALESCE(sm.user_id, 0) as user_name
                    FROM stock_mouvements sm
                    LEFT JOIN core_products cp ON sm.product_id = cp.id
                    LEFT JOIN stock_warehouses sw_origin ON sm.warehouse_id = sw_origin.id
                    LEFT JOIN stock_warehouses sw_dest ON sm.destination_warehouse_id = sw_dest.id
                    WHERE (sw_origin.entreprise_id = :entreprise_id OR sw_dest.entreprise_id = :entreprise_id
                           OR sw_origin.id IS NULL OR sw_dest.id IS NULL)
                    ORDER BY sm.movement_date DESC
                    LIMIT 5
                """), {"entreprise_id": entreprise_id})
                movements = result.fetchall()
                print(f"✅ {len(movements)} mouvements complets récupérés")
                
                for mov in movements:
                    print(f"   - {mov[0]} | {mov[1]} | {mov[2]} | Qté: {mov[5]}")
                    
            except Exception as e:
                print(f"❌ Erreur requête complète: {e}")
                import traceback
                traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")

if __name__ == "__main__":
    test_movement_query()