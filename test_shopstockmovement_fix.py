"""
Test de vérification du modèle ShopStockMovement
"""

import sys
import os

# Ajouter le chemin racine au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_shop_stock_movement_import():
    """Test d'importation du modèle ShopStockMovement"""
    try:
        print("🔄 Test d'importation du modèle ShopStockMovement...")
        
        from ayanna_erp.modules.boutique.model.models import ShopStockMovement
        
        print("✅ ShopStockMovement importé avec succès!")
        print(f"   Table: {ShopStockMovement.__tablename__}")
        print(f"   Colonnes principales:")
        
        # Vérifier les colonnes importantes
        columns_to_check = [
            'id', 'warehouse_id', 'product_id', 'movement_type', 
            'direction', 'quantity', 'unit_cost', 'movement_date'
        ]
        
        for col_name in columns_to_check:
            if hasattr(ShopStockMovement, col_name):
                print(f"   ✓ {col_name}")
            else:
                print(f"   ❌ {col_name} MANQUANT")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'importation: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_other_models_import():
    """Test d'importation des autres modèles nécessaires"""
    try:
        print("\n🔄 Test d'importation des autres modèles...")
        
        from ayanna_erp.modules.boutique.model.models import (
            ShopWarehouse, ShopProduct, ShopWarehouseStock, 
            ShopStockTransfer, ShopStockTransferItem
        )
        
        print("✅ Tous les modèles importés avec succès!")
        print("   ✓ ShopWarehouse")
        print("   ✓ ShopProduct") 
        print("   ✓ ShopWarehouseStock")
        print("   ✓ ShopStockTransfer")
        print("   ✓ ShopStockTransferItem")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'importation: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_stock_controllers_import():
    """Test d'importation des contrôleurs du stock"""
    try:
        print("\n🔄 Test d'importation des contrôleurs du stock...")
        
        from ayanna_erp.modules.stock.controllers.stock_controller import StockController
        from ayanna_erp.modules.stock.controllers.transfert_controller import TransfertController
        from ayanna_erp.modules.stock.controllers.alerte_controller import AlerteController
        from ayanna_erp.modules.stock.controllers.inventaire_controller import InventaireController
        from ayanna_erp.modules.stock.controllers.rapport_controller import RapportController
        
        print("✅ Tous les contrôleurs importés avec succès!")
        print("   ✓ StockController")
        print("   ✓ TransfertController")
        print("   ✓ AlerteController")
        print("   ✓ InventaireController")
        print("   ✓ RapportController")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'importation contrôleurs: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_stock_module_import():
    """Test d'importation complète du module stock"""
    try:
        print("\n🔄 Test d'importation du module stock...")
        
        from ayanna_erp.modules.stock.views.modular_stock_widget import ModularStockManagementWidget
        from ayanna_erp.modules.stock.stock_window import StockWindow
        
        print("✅ Module stock importé avec succès!")
        print("   ✓ ModularStockManagementWidget")
        print("   ✓ StockWindow")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'importation module stock: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Fonction principale"""
    print("🧪 Test de vérification des modèles et imports")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Test 1: ShopStockMovement
    if not test_shop_stock_movement_import():
        all_tests_passed = False
    
    # Test 2: Autres modèles
    if not test_other_models_import():
        all_tests_passed = False
    
    # Test 3: Contrôleurs stock
    if not test_stock_controllers_import():
        all_tests_passed = False
    
    # Test 4: Module stock complet
    if not test_stock_module_import():
        all_tests_passed = False
    
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 TOUS LES TESTS RÉUSSIS!")
        print("✅ Le modèle ShopStockMovement est disponible")
        print("✅ Tous les imports fonctionnent correctement")
        print("✅ Le module stock peut maintenant se charger")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("⚠️  Vérifiez les erreurs ci-dessus")
    
    print("=" * 60)

if __name__ == "__main__":
    main()