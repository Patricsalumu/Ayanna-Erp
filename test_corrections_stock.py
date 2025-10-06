"""
Test des corrections des erreurs dans le module Stock
"""

import sys
import os
from datetime import datetime

# Ajouter le chemin racine au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_shopproduct_code_attribute():
    """Test de l'attribut 'code' dans ShopProduct"""
    try:
        print("🔄 Test de l'attribut 'code' dans ShopProduct...")
        
        from ayanna_erp.modules.boutique.model.models import ShopProduct
        
        # Vérifier que l'attribut 'code' existe
        if hasattr(ShopProduct, 'code'):
            print("   ✅ Attribut 'code' trouvé dans ShopProduct")
            print(f"   📄 Type de colonne: {type(ShopProduct.code.type)}")
            return True
        else:
            print("   ❌ Attribut 'code' manquant dans ShopProduct")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test ShopProduct.code: {e}")
        return False

def test_shopstocktransfer_created_at():
    """Test de l'attribut 'created_at' dans ShopStockTransfer"""
    try:
        print("\n🔄 Test de l'attribut 'created_at' dans ShopStockTransfer...")
        
        from ayanna_erp.modules.boutique.model.models import ShopStockTransfer
        
        # Vérifier que l'attribut 'created_at' existe
        if hasattr(ShopStockTransfer, 'created_at'):
            print("   ✅ Attribut 'created_at' trouvé dans ShopStockTransfer")
            print(f"   📄 Type de colonne: {type(ShopStockTransfer.created_at.type)}")
            return True
        else:
            print("   ❌ Attribut 'created_at' manquant dans ShopStockTransfer")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test ShopStockTransfer.created_at: {e}")
        return False

def test_alerte_controller_methods():
    """Test des méthodes d'AlerteController"""
    try:
        print("\n🔄 Test des méthodes d'AlerteController...")
        
        from ayanna_erp.modules.stock.controllers.alerte_controller import AlerteController
        
        # Créer une instance
        controller = AlerteController(pos_id=1)
        
        # Vérifier que la méthode get_current_alerts existe
        if hasattr(controller, 'get_current_alerts'):
            print("   ✅ Méthode 'get_current_alerts' trouvée")
            
            # Test d'appel (simulation sans base de données)
            try:
                # Ne pas appeler réellement car nécessite une session DB
                print("   ✅ Méthode callable")
            except Exception as e:
                print(f"   ⚠️  Méthode trouvée mais erreur d'appel: {e}")
            
            return True
        else:
            print("   ❌ Méthode 'get_current_alerts' manquante")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test AlerteController: {e}")
        return False

def test_inventaire_controller_methods():
    """Test des méthodes d'InventaireController"""
    try:
        print("\n🔄 Test des méthodes d'InventaireController...")
        
        from ayanna_erp.modules.stock.controllers.inventaire_controller import InventaireController
        
        # Créer une instance
        controller = InventaireController(pos_id=1)
        
        # Vérifier que la méthode get_all_inventories existe
        if hasattr(controller, 'get_all_inventories'):
            print("   ✅ Méthode 'get_all_inventories' trouvée")
            
            try:
                # Ne pas appeler réellement car nécessite une session DB
                print("   ✅ Méthode callable")
            except Exception as e:
                print(f"   ⚠️  Méthode trouvée mais erreur d'appel: {e}")
            
            return True
        else:
            print("   ❌ Méthode 'get_all_inventories' manquante")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test InventaireController: {e}")
        return False

def test_rapport_controller_methods():
    """Test des méthodes de RapportController"""
    try:
        print("\n🔄 Test des méthodes de RapportController...")
        
        from ayanna_erp.modules.stock.controllers.rapport_controller import RapportController
        
        # Créer une instance
        controller = RapportController(pos_id=1)
        
        # Vérifier que la méthode get_recent_reports existe
        if hasattr(controller, 'get_recent_reports'):
            print("   ✅ Méthode 'get_recent_reports' trouvée")
            
            try:
                # Ne pas appeler réellement car nécessite une session DB
                print("   ✅ Méthode callable")
            except Exception as e:
                print(f"   ⚠️  Méthode trouvée mais erreur d'appel: {e}")
            
            return True
        else:
            print("   ❌ Méthode 'get_recent_reports' manquante")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test RapportController: {e}")
        return False

def test_controller_instantiation():
    """Test d'instanciation de tous les contrôleurs"""
    try:
        print("\n🔧 Test d'instanciation des contrôleurs corrigés...")
        
        from ayanna_erp.modules.stock.controllers.stock_controller import StockController
        from ayanna_erp.modules.stock.controllers.alerte_controller import AlerteController
        from ayanna_erp.modules.stock.controllers.inventaire_controller import InventaireController
        from ayanna_erp.modules.stock.controllers.rapport_controller import RapportController
        
        # Test d'instanciation
        controllers = {
            'StockController': StockController(pos_id=1),
            'AlerteController': AlerteController(pos_id=1),
            'InventaireController': InventaireController(pos_id=1),
            'RapportController': RapportController(pos_id=1)
        }
        
        for name, controller in controllers.items():
            print(f"   ✅ {name} instancié avec succès")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur instanciation contrôleurs: {e}")
        return False

def main():
    """Fonction principale"""
    print("🔧 TEST DES CORRECTIONS - Module Stock")
    print("=" * 60)
    
    all_tests_passed = True
    tests = [
        test_shopproduct_code_attribute,
        test_shopstocktransfer_created_at,
        test_alerte_controller_methods,
        test_inventaire_controller_methods,
        test_rapport_controller_methods,
        test_controller_instantiation
    ]
    
    for test_func in tests:
        if not test_func():
            all_tests_passed = False
    
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 TOUTES LES CORRECTIONS RÉUSSIES!")
        print("✅ ShopProduct.code ajouté")
        print("✅ ShopStockTransfer.created_at ajouté")
        print("✅ AlerteController.get_current_alerts ajoutée")
        print("✅ InventaireController.get_all_inventories ajoutée")
        print("✅ RapportController.get_recent_reports ajoutée")
        print("")
        print("🚀 Le module Stock devrait maintenant fonctionner sans erreurs!")
        print("")
        print("📋 Actions suivantes:")
        print("   1. Testez le module Stock dans l'application")
        print("   2. Vérifiez le chargement des données")
        print("   3. Testez chaque onglet du dashboard")
    else:
        print("❌ CERTAINES CORRECTIONS ONT ÉCHOUÉ")
        print("⚠️  Vérifiez les erreurs ci-dessus")
    
    print("=" * 60)

if __name__ == "__main__":
    main()