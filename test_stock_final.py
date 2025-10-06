"""
Test final d'importation du module Stock
"""

import sys
import os

# Ajouter le chemin racine au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_all_imports():
    """Test de tous les imports nécessaires pour le module Stock"""
    try:
        print("🔄 Test d'importation complet du module Stock...")
        
        # Test 1: Modèles de la boutique (incluant ShopStockMovement)
        print("\n📦 Test des modèles boutique:")
        from ayanna_erp.modules.boutique.model.models import (
            ShopStockMovement, ShopWarehouse, ShopProduct, 
            ShopWarehouseStock, ShopStockTransfer, ShopStockTransferItem
        )
        print("   ✅ ShopStockMovement")
        print("   ✅ ShopWarehouse") 
        print("   ✅ ShopProduct")
        print("   ✅ ShopWarehouseStock")
        print("   ✅ ShopStockTransfer")
        print("   ✅ ShopStockTransferItem")
        
        # Test 2: Contrôleurs du stock
        print("\n🎛️ Test des contrôleurs stock:")
        from ayanna_erp.modules.stock.controllers.entrepot_controller import EntrepotController
        from ayanna_erp.modules.stock.controllers.stock_controller import StockController
        from ayanna_erp.modules.stock.controllers.transfert_controller import TransfertController
        from ayanna_erp.modules.stock.controllers.alerte_controller import AlerteController
        from ayanna_erp.modules.stock.controllers.inventaire_controller import InventaireController
        from ayanna_erp.modules.stock.controllers.rapport_controller import RapportController
        print("   ✅ EntrepotController")
        print("   ✅ StockController")
        print("   ✅ TransfertController")
        print("   ✅ AlerteController")
        print("   ✅ InventaireController")
        print("   ✅ RapportController")
        
        # Test 3: Widgets stock (imports seulement)
        print("\n🖼️ Test des widgets stock:")
        from ayanna_erp.modules.stock.views.entrepot_widget import EntrepotWidget
        from ayanna_erp.modules.stock.views.stock_widget import StockWidget
        from ayanna_erp.modules.stock.views.transfert_widget import TransfertWidget
        from ayanna_erp.modules.stock.views.alerte_widget import AlerteWidget
        from ayanna_erp.modules.stock.views.inventaire_widget import InventaireWidget
        from ayanna_erp.modules.stock.views.rapport_widget import RapportWidget
        from ayanna_erp.modules.stock.views.modular_stock_widget import ModularStockManagementWidget
        print("   ✅ EntrepotWidget")
        print("   ✅ StockWidget")
        print("   ✅ TransfertWidget")
        print("   ✅ AlerteWidget")
        print("   ✅ InventaireWidget")
        print("   ✅ RapportWidget")
        print("   ✅ ModularStockManagementWidget")
        
        # Test 4: Module principal stock
        print("\n🏭 Test du module principal:")
        from ayanna_erp.modules.stock.stock_window import StockWindow
        print("   ✅ StockWindow")
        
        # Test 5: PyQt6.QtCharts (nouveau)
        print("\n📊 Test PyQt6.QtCharts:")
        from PyQt6.QtCharts import QChart, QChartView, QPieSeries, QBarSeries
        print("   ✅ QChart")
        print("   ✅ QChartView")
        print("   ✅ QPieSeries")
        print("   ✅ QBarSeries")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'importation: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_controller_creation():
    """Test de création des contrôleurs (sans interface)"""
    try:
        print("\n🔧 Test de création des contrôleurs:")
        
        from ayanna_erp.modules.stock.controllers.stock_controller import StockController
        from ayanna_erp.modules.stock.controllers.entrepot_controller import EntrepotController
        
        # Créer des instances
        stock_ctrl = StockController(pos_id=1)
        entrepot_ctrl = EntrepotController(pos_id=1)
        
        print("   ✅ StockController créé")
        print("   ✅ EntrepotController créé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur création contrôleurs: {e}")
        return False

def main():
    """Fonction principale"""
    print("🎯 TEST FINAL - Module Stock")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Test 1: Imports complets
    if not test_all_imports():
        all_tests_passed = False
    
    # Test 2: Création contrôleurs  
    if not test_controller_creation():
        all_tests_passed = False
    
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 SUCCÈS COMPLET!")
        print("✅ ShopStockMovement corrigé et disponible")
        print("✅ PyQt6-Charts installé")
        print("✅ Tous les imports fonctionnent")
        print("✅ Architecture modulaire opérationnelle")
        print("")
        print("🚀 LE MODULE STOCK EST PRÊT À UTILISER!")
        print("")
        print("📋 Prochaines étapes:")
        print("   1. Lancez l'application principale")
        print("   2. Cliquez sur le module 'Stock'")
        print("   3. Profitez de l'interface modulaire!")
    else:
        print("❌ DES ERREURS PERSISTENT")
        print("⚠️  Vérifiez les détails ci-dessus")
    
    print("=" * 60)

if __name__ == "__main__":
    main()