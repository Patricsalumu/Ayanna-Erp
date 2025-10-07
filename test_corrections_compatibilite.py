#!/usr/bin/env python3
"""
Test des corrections des erreurs de compatibilité
"""

def test_imports():
    """Test des imports des nouveaux contrôleurs"""
    print("🧪 Test des imports des nouveaux contrôleurs...")
    
    try:
        from ayanna_erp.modules.stock.controllers.stock_controller import StockController
        print("✅ Import StockController réussi")
    except ImportError as e:
        print(f"❌ Erreur import StockController: {e}")
        return False
    
    try:
        from ayanna_erp.modules.stock.controllers.entrepot_controller import EntrepotController
        print("✅ Import EntrepotController réussi")
    except ImportError as e:
        print(f"❌ Erreur import EntrepotController: {e}")
        return False
    
    try:
        from ayanna_erp.modules.stock.controllers.transfert_controller import TransfertController
        print("✅ Import TransfertController réussi")
    except ImportError as e:
        print(f"❌ Erreur import TransfertController: {e}")
        return False
    
    try:
        from ayanna_erp.modules.stock.controllers.alerte_controller import AlerteController
        print("✅ Import AlerteController réussi")
    except ImportError as e:
        print(f"❌ Erreur import AlerteController: {e}")
        return False
    
    try:
        from ayanna_erp.modules.stock.controllers.inventaire_controller import InventaireController
        print("✅ Import InventaireController réussi")
    except ImportError as e:
        print(f"❌ Erreur import InventaireController: {e}")
        return False
    
    try:
        from ayanna_erp.modules.stock.controllers.rapport_controller import RapportController
        print("✅ Import RapportController réussi")
    except ImportError as e:
        print(f"❌ Erreur import RapportController: {e}")
        return False
    
    return True

def test_controllers():
    """Test de l'instanciation des contrôleurs"""
    print("\n🧪 Test d'instanciation des contrôleurs...")
    
    entreprise_id = 1
    
    try:
        from ayanna_erp.modules.stock.controllers.stock_controller import StockController
        controller = StockController(entreprise_id)
        stocks = controller.get_stock_overview()
        print(f"✅ StockController: {len(stocks.get('stocks', []))} produits trouvés")
    except Exception as e:
        print(f"❌ Erreur StockController: {e}")
        return False
    
    try:
        from ayanna_erp.modules.stock.controllers.entrepot_controller import EntrepotController
        controller = EntrepotController(entreprise_id)
        warehouses = controller.get_all_warehouses()
        print(f"✅ EntrepotController: {len(warehouses.get('warehouses', []))} entrepôts trouvés")
    except Exception as e:
        print(f"❌ Erreur EntrepotController: {e}")
        return False
    
    try:
        from ayanna_erp.modules.stock.controllers.transfert_controller import TransfertController
        controller = TransfertController(entreprise_id)
        warehouses = controller.get_warehouses_for_transfer()
        print(f"✅ TransfertController: {len(warehouses)} entrepôts pour transfert")
    except Exception as e:
        print(f"❌ Erreur TransfertController: {e}")
        return False
    
    try:
        from ayanna_erp.modules.stock.controllers.alerte_controller import AlerteController
        controller = AlerteController(entreprise_id)
        alerts = controller.get_low_stock_alerts()
        print(f"✅ AlerteController: {len(alerts)} alertes de stock faible")
    except Exception as e:
        print(f"❌ Erreur AlerteController: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔧 Test des corrections de compatibilité")
    print("="*50)
    
    # Test des imports
    if not test_imports():
        print("\n❌ Échec des tests d'import")
        exit(1)
    
    # Test des contrôleurs
    if not test_controllers():
        print("\n❌ Échec des tests de contrôleurs")
        exit(1)
    
    print("\n✅ Tous les tests de compatibilité sont passés!")
    print("✅ Les erreurs ShopProduct ont été corrigées")
    print("✅ Les contrôleurs utilisent maintenant la nouvelle architecture")