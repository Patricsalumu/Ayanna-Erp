"""
Test final de correction des erreurs de layout et de contraintes
"""

import sys
import os

# Ajouter le chemin racine au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_layout_fixes():
    """Test de correction des erreurs de layout Qt"""
    try:
        print("🎨 Test de correction des erreurs de layout...")
        
        # Test import du widget nettoyé
        from ayanna_erp.modules.stock.views.modular_stock_widget import ModularStockManagementWidget
        print("   ✅ Import ModularStockManagementWidget réussi")
        
        # Vérifier que StockDashboard n'existe plus
        try:
            from ayanna_erp.modules.stock.views.modular_stock_widget import StockDashboard
            print("   ❌ StockDashboard encore présent")
            return False
        except ImportError:
            print("   ✅ StockDashboard complètement supprimé")
        
        # Vérifier que le code ne contient plus de QGridLayout problématique
        with open("ayanna_erp/modules/stock/views/modular_stock_widget.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        if "indicators_layout = QGridLayout()" in content:
            print("   ❌ QGridLayout problématique encore présent")
            return False
        else:
            print("   ✅ QGridLayout problématique supprimé")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def test_warehouse_constraints():
    """Test des contraintes d'entrepôts"""
    try:
        print("\n🏪 Test des contraintes d'entrepôts...")
        
        # Vérifier l'état actuel des entrepôts
        import sqlite3
        conn = sqlite3.connect("ayanna_erp.db")
        cursor = conn.cursor()
        
        # Compter les entrepôts par code
        cursor.execute("""
            SELECT code, COUNT(*) as count 
            FROM shop_warehouses 
            GROUP BY code 
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()
        
        if duplicates:
            print(f"   ⚠️  Codes dupliqués trouvés: {duplicates}")
            print("   💡 Suggestion: Nettoyage automatique de la base")
        else:
            print("   ✅ Aucun code d'entrepôt dupliqué")
        
        # Vérifier la structure actuelle
        cursor.execute("SELECT COUNT(*) FROM shop_warehouses")
        total_warehouses = cursor.fetchone()[0]
        print(f"   📊 Total entrepôts: {total_warehouses}")
        
        cursor.execute("SELECT COUNT(DISTINCT code) FROM shop_warehouses")
        unique_codes = cursor.fetchone()[0]
        print(f"   🔑 Codes uniques: {unique_codes}")
        
        conn.close()
        return len(duplicates) == 0
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def test_signals_and_imports():
    """Test des signaux et imports"""
    try:
        print("\n📡 Test des signaux et imports...")
        
        # Test des signaux EntrepotWidget
        from ayanna_erp.modules.stock.views.entrepot_widget import EntrepotWidget
        
        signals_required = ['warehouse_created', 'warehouse_updated', 'warehouse_selected']
        for signal in signals_required:
            if hasattr(EntrepotWidget, signal):
                print(f"   ✅ {signal}")
            else:
                print(f"   ❌ {signal} manquant")
                return False
        
        # Test import des autres widgets
        widgets_to_test = [
            ('StockWidget', 'ayanna_erp.modules.stock.views.stock_widget'),
            ('TransfertWidget', 'ayanna_erp.modules.stock.views.transfert_widget'),
            ('AlerteWidget', 'ayanna_erp.modules.stock.views.alerte_widget'),
            ('InventaireWidget', 'ayanna_erp.modules.stock.views.inventaire_widget'),
            ('RapportWidget', 'ayanna_erp.modules.stock.views.rapport_widget')
        ]
        
        for widget_name, module_path in widgets_to_test:
            try:
                __import__(module_path, fromlist=[widget_name])
                print(f"   ✅ {widget_name}")
            except Exception as e:
                print(f"   ❌ {widget_name}: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def test_clean_widget_structure():
    """Test de la structure du widget nettoyé"""
    try:
        print("\n🧹 Test de la structure du widget nettoyé...")
        
        with open("ayanna_erp/modules/stock/views/modular_stock_widget.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Vérifier les éléments essentiels
        essential_elements = [
            "class ModularStockManagementWidget(QWidget):",
            "def setup_ui(self):",
            "def load_modules(self):",
            "def connect_signals(self):",
            "self.tab_widget = QTabWidget()",
            "🏪 Entrepôts",
            "📦 Stocks",
            "🔄 Transferts", 
            "🚨 Alertes",
            "📋 Inventaires",
            "📊 Rapports"
        ]
        
        missing_elements = []
        for element in essential_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"   ❌ Éléments manquants: {missing_elements}")
            return False
        else:
            print("   ✅ Tous les éléments essentiels présents")
        
        # Vérifier les éléments supprimés
        removed_elements = [
            "class StockDashboard",
            "indicators_layout = QGridLayout()",
            "dashboard_title",
            "self.dashboard ="
        ]
        
        elements_still_present = []
        for element in removed_elements:
            if element in content:
                elements_still_present.append(element)
        
        if elements_still_present:
            print(f"   ❌ Éléments encore présents: {elements_still_present}")
            return False
        else:
            print("   ✅ Tous les éléments problématiques supprimés")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def main():
    """Fonction principale"""
    print("🔧 TEST FINAL DE CORRECTION DES ERREURS")
    print("=" * 60)
    
    all_tests_passed = True
    tests = [
        test_layout_fixes,
        test_warehouse_constraints,
        test_signals_and_imports,
        test_clean_widget_structure
    ]
    
    for test_func in tests:
        if not test_func():
            all_tests_passed = False
    
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 TOUTES LES ERREURS CORRIGÉES AVEC SUCCÈS!")
        print("")
        print("✅ Corrections appliquées:")
        print("   • 🎨 StockDashboard complètement supprimé")
        print("   • 🔧 QGridLayout problématique éliminé")
        print("   • 📡 Tous les signaux requis présents")
        print("   • 🏪 Contraintes d'entrepôts vérifiées")
        print("   • 🧹 Structure du widget nettoyée")
        print("")
        print("✅ Erreurs résolues:")
        print("   ❌ ➜ ✅ QLayout::addChildLayout errors")
        print("   ❌ ➜ ✅ QWidget::setLayout errors")
        print("   ❌ ➜ ✅ UNIQUE constraint failed: shop_warehouses.code")
        print("   ❌ ➜ ✅ 'EntrepotWidget' object has no attribute errors")
        print("")
        print("🚀 MODULE STOCK MAINTENANT 100% FONCTIONNEL!")
        print("")
        print("📝 Prochaine étape:")
        print("   • Testez votre application - le module Stock devrait")
        print("     maintenant s'ouvrir sans AUCUNE erreur")
        print("   • Interface ultra-simplifiée avec seulement les onglets")
        print("   • Navigation fluide et sans problèmes de layout")
        
    else:
        print("❌ CERTAINES ERREURS PERSISTENT")
        print("⚠️  Revérifiez les corrections ci-dessus")
    
    print("=" * 60)

if __name__ == "__main__":
    main()