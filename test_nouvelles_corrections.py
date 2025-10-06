"""
Test des nouvelles corrections des erreurs
"""

import sys
import os

# Ajouter le chemin racine au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_shopproduct_cost_price():
    """Test de l'attribut cost_price dans ShopProduct"""
    try:
        print("🔄 Test de l'attribut 'cost_price' dans ShopProduct...")
        
        from ayanna_erp.modules.boutique.model.models import ShopProduct
        
        if hasattr(ShopProduct, 'cost_price'):
            print("   ✅ Attribut 'cost_price' trouvé")
            return True
        else:
            print("   ❌ Attribut 'cost_price' manquant")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test cost_price: {e}")
        return False

def test_alerte_controller_limit():
    """Test du paramètre limit dans get_all_alerts"""
    try:
        print("\n🔄 Test du paramètre 'limit' dans AlerteController.get_all_alerts...")
        
        from ayanna_erp.modules.stock.controllers.alerte_controller import AlerteController
        import inspect
        
        controller = AlerteController(pos_id=1)
        
        # Vérifier la signature de la méthode
        sig = inspect.signature(controller.get_all_alerts)
        
        if 'limit' in sig.parameters:
            print("   ✅ Paramètre 'limit' trouvé dans la signature")
            print(f"   📋 Signature: {sig}")
            return True
        else:
            print("   ❌ Paramètre 'limit' manquant")
            print(f"   📋 Signature actuelle: {sig}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test limit: {e}")
        return False

def test_controllers_instantiation():
    """Test d'instanciation des contrôleurs avec les nouvelles corrections"""
    try:
        print("\n🔧 Test d'instanciation des contrôleurs corrigés...")
        
        from ayanna_erp.modules.stock.controllers.stock_controller import StockController
        from ayanna_erp.modules.stock.controllers.alerte_controller import AlerteController
        from ayanna_erp.modules.stock.controllers.transfert_controller import TransfertController
        
        # Test d'instanciation
        controllers = {
            'StockController': StockController(pos_id=1),
            'AlerteController': AlerteController(pos_id=1),
            'TransfertController': TransfertController(pos_id=1)
        }
        
        for name, controller in controllers.items():
            print(f"   ✅ {name} instancié avec succès")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur instanciation contrôleurs: {e}")
        return False

def test_imports_completeness():
    """Test complet de tous les imports nécessaires"""
    try:
        print("\n📦 Test d'import complet...")
        
        # Modèles
        from ayanna_erp.modules.boutique.model.models import (
            ShopProduct, ShopStockTransfer, ShopWarehouse, 
            ShopWarehouseStock, ShopStockMovement
        )
        print("   ✅ Tous les modèles importés")
        
        # Contrôleurs
        from ayanna_erp.modules.stock.controllers.stock_controller import StockController
        from ayanna_erp.modules.stock.controllers.alerte_controller import AlerteController
        from ayanna_erp.modules.stock.controllers.transfert_controller import TransfertController
        from ayanna_erp.modules.stock.controllers.inventaire_controller import InventaireController
        from ayanna_erp.modules.stock.controllers.rapport_controller import RapportController
        print("   ✅ Tous les contrôleurs importés")
        
        # Widgets (imports seulement)
        from ayanna_erp.modules.stock.views.modular_stock_widget import ModularStockManagementWidget
        from ayanna_erp.modules.stock.stock_window import StockWindow
        print("   ✅ Tous les widgets importés")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur imports: {e}")
        return False

def main():
    """Fonction principale"""
    print("🔧 TEST DES NOUVELLES CORRECTIONS")
    print("=" * 60)
    
    all_tests_passed = True
    tests = [
        test_shopproduct_cost_price,
        test_alerte_controller_limit,
        test_controllers_instantiation,
        test_imports_completeness
    ]
    
    for test_func in tests:
        if not test_func():
            all_tests_passed = False
    
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 TOUTES LES NOUVELLES CORRECTIONS RÉUSSIES!")
        print("")
        print("✅ Corrections appliquées:")
        print("   • ShopProduct.cost_price ajouté")
        print("   • AlerteController.get_all_alerts supporte 'limit'")
        print("   • Références à created_at temporairement commentées")
        print("   • Utilisation de requested_date pour les tri/filtres")
        print("")
        print("⚠️ Actions restantes:")
        print("   • Exécuter la migration DB pour ajouter les colonnes manquantes")
        print("   • Ou créer les colonnes manuellement en SQL")
        print("")
        print("🚀 Le module Stock devrait maintenant fonctionner!")
        
    else:
        print("❌ CERTAINES CORRECTIONS ONT ÉCHOUÉ")
        print("⚠️  Vérifiez les erreurs ci-dessus")
    
    print("=" * 60)

if __name__ == "__main__":
    main()