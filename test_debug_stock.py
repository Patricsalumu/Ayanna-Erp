#!/usr/bin/env python3
"""
Test rapide pour diagnostiquer les problèmes de stock
"""

import sys
import os

# Configuration du path
sys.path.insert(0, os.path.abspath('.'))

from ayanna_erp.database.database_manager import DatabaseManager
from sqlalchemy import text

def test_stock_tables():
    """Test de l'existence des tables de stock"""
    print("=== TEST DES TABLES DE STOCK ===\n")
    
    db_manager = DatabaseManager()
    
    try:
        with db_manager.get_session() as session:
            # Test 1: Vérifier l'existence de la table stock_mouvements
            print("1. Test table stock_mouvements...")
            try:
                result = session.execute(text("SELECT COUNT(*) FROM stock_mouvements"))
                count = result.scalar()
                print(f"✅ Table stock_mouvements existe avec {count} enregistrements")
            except Exception as e:
                print(f"❌ Erreur table stock_mouvements: {e}")
            
            # Test 2: Vérifier l'existence de la table stock_warehouses
            print("\n2. Test table stock_warehouses...")
            try:
                result = session.execute(text("SELECT COUNT(*) FROM stock_warehouses"))
                count = result.scalar()
                print(f"✅ Table stock_warehouses existe avec {count} enregistrements")
            except Exception as e:
                print(f"❌ Erreur table stock_warehouses: {e}")
            
            # Test 3: Vérifier l'existence de la table stock_produits_entrepot
            print("\n3. Test table stock_produits_entrepot...")
            try:
                result = session.execute(text("SELECT COUNT(*) FROM stock_produits_entrepot"))
                count = result.scalar()
                print(f"✅ Table stock_produits_entrepot existe avec {count} enregistrements")
            except Exception as e:
                print(f"❌ Erreur table stock_produits_entrepot: {e}")
            
            # Test 4: Vérifier les colonnes de stock_mouvements
            print("\n4. Test colonnes stock_mouvements...")
            try:
                result = session.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'stock_mouvements'
                    ORDER BY ordinal_position
                """))
                columns = result.fetchall()
                print("✅ Colonnes de stock_mouvements:")
                for col in columns:
                    print(f"   - {col[0]}: {col[1]}")
            except Exception as e:
                print(f"❌ Erreur colonnes stock_mouvements: {e}")
                
                # Test alternatif pour SQLite
                try:
                    result = session.execute(text("PRAGMA table_info(stock_mouvements)"))
                    columns = result.fetchall()
                    print("✅ Colonnes de stock_mouvements (SQLite):")
                    for col in columns:
                        print(f"   - {col[1]}: {col[2]}")
                except Exception as e2:
                    print(f"❌ Erreur SQLite: {e2}")
            
            # Test 5: Test requête simple de mouvements
            print("\n5. Test requête mouvements simple...")
            try:
                result = session.execute(text("""
                    SELECT 
                        movement_date,
                        movement_type,
                        quantity
                    FROM stock_mouvements 
                    LIMIT 5
                """))
                movements = result.fetchall()
                print(f"✅ {len(movements)} mouvements récupérés:")
                for mov in movements[:3]:  # Afficher les 3 premiers
                    print(f"   - Date: {mov[0]}, Type: {mov[1]}, Quantité: {mov[2]}")
            except Exception as e:
                print(f"❌ Erreur requête simple: {e}")
            
    except Exception as e:
        print(f"❌ Erreur de connexion DB: {e}")

if __name__ == "__main__":
    test_stock_tables()