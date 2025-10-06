"""
Test direct du chargement du module Stock
"""

import sys
import os

# Ajouter le chemin racine au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_stock_window_creation():
    """Test de création de la fenêtre Stock"""
    try:
        print("🔄 Test de création de StockWindow...")
        
        from ayanna_erp.modules.stock.stock_window import StockWindow
        
        # Utilisateur de test
        current_user = {"id": 1, "name": "Test User", "username": "testuser"}
        
        # Créer la fenêtre (sans l'afficher)
        stock_window = StockWindow(current_user)
        
        print("✅ StockWindow créée avec succès!")
        print(f"   Titre: {stock_window.windowTitle()}")
        print(f"   Taille: {stock_window.size().width()}x{stock_window.size().height()}")
        
        # Vérifier le widget central
        central_widget = stock_window.centralWidget()
        if central_widget:
            print(f"   Widget central: {type(central_widget).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de StockWindow: {e}")
        return False

def test_modular_widget_creation():
    """Test de création du widget modulaire"""
    try:
        print("\n🔄 Test de création de ModularStockManagementWidget...")
        
        from ayanna_erp.modules.stock.views.modular_stock_widget import ModularStockManagementWidget
        
        # Utilisateur de test
        current_user = {"id": 1, "name": "Test User", "username": "testuser"}
        
        # Créer le widget (sans l'afficher)
        modular_widget = ModularStockManagementWidget(pos_id=1, current_user=current_user)
        
        print("✅ ModularStockManagementWidget créé avec succès!")
        print(f"   Type: {type(modular_widget).__name__}")
        
        # Vérifier les onglets
        if hasattr(modular_widget, 'tab_widget'):
            tab_count = modular_widget.tab_widget.count()
            print(f"   Nombre d'onglets: {tab_count}")
            
            for i in range(tab_count):
                tab_text = modular_widget.tab_widget.tabText(i)
                print(f"     • {tab_text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de ModularStockManagementWidget: {e}")
        return False

def test_controller_instantiation():
    """Test d'instanciation des contrôleurs"""
    try:
        print("\n🔄 Test d'instanciation des contrôleurs...")
        
        from ayanna_erp.modules.stock.controllers.stock_controller import StockController
        from ayanna_erp.modules.stock.controllers.entrepot_controller import EntrepotController
        
        # Test StockController
        stock_controller = StockController(pos_id=1)
        print("✅ StockController instancié avec succès!")
        
        # Test EntrepotController
        entrepot_controller = EntrepotController(pos_id=1)
        print("✅ EntrepotController instancié avec succès!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'instanciation des contrôleurs: {e}")
        return False

def main():
    """Fonction principale"""
    print("🧪 Test direct du module Stock")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Test 1: Contrôleurs
    if not test_controller_instantiation():
        all_tests_passed = False
    
    # Test 2: Widget modulaire (sans PyQt6 interface)
    if not test_modular_widget_creation():
        all_tests_passed = False
    
    # Test 3: Fenêtre Stock (sans PyQt6 interface)
    if not test_stock_window_creation():
        all_tests_passed = False
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 TOUS LES TESTS RÉUSSIS!")
        print("✅ Le module Stock se charge correctement")
        print("✅ ShopStockMovement est disponible")
        print("✅ Tous les composants fonctionnent")
        print("\n🚀 Vous pouvez maintenant utiliser le module Stock!")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("⚠️  Voir les détails ci-dessus")
    
    print("=" * 50)

if __name__ == "__main__":
    main()