#!/usr/bin/env python3
"""
Test des corrections apportées pour les erreurs dict et available_quantity
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from ayanna_erp.core.session_manager import SessionManager
from ayanna_erp.modules.stock.controllers.entrepot_controller import EntrepotController
from ayanna_erp.modules.stock.controllers.stock_controller import StockController

def test_corrections():
    """Test des corrections des erreurs dict et available_quantity"""
    print("=== Test des corrections ===")
    
    # Initialiser une session
    session_manager = SessionManager()
    
    try:
        # Test 1: Contrôleur entrepôt - doit retourner des dictionnaires
        print("\n1. Test contrôleur entrepôt...")
        entrepot_controller = EntrepotController(entreprise_id=1)
        warehouses = entrepot_controller.get_all_warehouses()
        
        if warehouses and len(warehouses) > 0:
            warehouse = warehouses[0]
            print(f"   ✅ Type retourné: {type(warehouse)}")
            print(f"   ✅ Clés disponibles: {list(warehouse.keys())}")
            print(f"   ✅ Nom: {warehouse['name']}")
            print(f"   ✅ Code: {warehouse['code']}")
        else:
            print("   ❌ Aucun entrepôt trouvé")
        
        # Test 2: Contrôleur stock - doit inclure available_quantity
        print("\n2. Test contrôleur stock...")
        stock_controller = StockController(entreprise_id=1)
        result = stock_controller.get_stock_overview()
        
        if result['stocks'] and len(result['stocks']) > 0:
            stock = result['stocks'][0]
            print(f"   ✅ Type retourné: {type(stock)}")
            print(f"   ✅ Clés disponibles: {list(stock.keys())}")
            
            # Vérifier available_quantity
            if 'available_quantity' in stock:
                print(f"   ✅ available_quantity présent: {stock['available_quantity']}")
            else:
                print("   ❌ available_quantity manquant")
                
            # Vérifier reserved_quantity
            if 'reserved_quantity' in stock:
                print(f"   ✅ reserved_quantity présent: {stock['reserved_quantity']}")
            else:
                print("   ❌ reserved_quantity manquant")
        else:
            print("   ❌ Aucun stock trouvé")
            
        # Test 3: Configuration entrepôt - doit retourner des dictionnaires
        print("\n3. Test configuration entrepôt...")
        config = entrepot_controller.get_warehouse_configuration()
        
        if config and 'default_warehouse' in config and config['default_warehouse']:
            default_warehouse = config['default_warehouse']
            print(f"   ✅ Type default_warehouse: {type(default_warehouse)}")
            if isinstance(default_warehouse, dict):
                print(f"   ✅ Nom entrepôt par défaut: {default_warehouse['name']}")
            else:
                print("   ❌ default_warehouse n'est pas un dictionnaire")
        else:
            print("   ⚠️ Aucun entrepôt par défaut configuré")
            
        print("\n=== Tests terminés ===")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_corrections()