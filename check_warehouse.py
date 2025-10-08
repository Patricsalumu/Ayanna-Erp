#!/usr/bin/env python3
"""
Script pour vérifier les entrepôts et tester l'initialisation des stocks
"""

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.stock.models import StockWarehouse, StockProduitEntrepot

def check_warehouses():
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        print("=== VÉRIFICATION DES ENTREPÔTS ===")
        
        # Lister tous les entrepôts
        warehouses = session.query(StockWarehouse).all()
        print(f"Total entrepôts: {len(warehouses)}")
        
        for w in warehouses:
            print(f"  - Code: {w.code} | Nom: {w.name} | Type: {w.type} | ID: {w.id}")
        
        print("\n=== RECHERCHE ENTREPÔT POS_2 ===")
        # Vérifier si l'entrepôt POS_2 existe
        warehouse = session.query(StockWarehouse).filter_by(code='POS_2').first()
        if warehouse:
            print(f"✅ Entrepôt POS_2 trouvé: {warehouse.name} (ID: {warehouse.id})")
        else:
            print("❌ Entrepôt POS_2 non trouvé")
            
        print("\n=== VÉRIFICATION DES STOCKS ===")
        # Vérifier les stocks existants
        stocks = session.query(StockProduitEntrepot).all()
        print(f"Total stocks: {len(stocks)}")
        
        for stock in stocks:
            print(f"  - Produit {stock.product_id} dans entrepôt {stock.warehouse_id}: {stock.quantity}")
        
    finally:
        session.close()

if __name__ == "__main__":
    check_warehouses()