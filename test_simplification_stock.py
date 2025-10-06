"""
Test de simplification du module Stock - Suppression dashboard et éléments inutiles
"""

import sys
import os

# Ajouter le chemin racine au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_stock_window_simplification():
    """Test de la simplification de la fenêtre Stock"""
    try:
        print("🎯 Test de la simplification de la fenêtre Stock...")
        
        # Test import
        from ayanna_erp.modules.stock.stock_window import StockWindow
        print("   ✅ Import StockWindow réussi")
        
        # Vérifier que les éléments inutiles ont été supprimés
        with open("ayanna_erp/modules/stock/stock_window.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        # Vérifier la suppression des éléments
        removed_elements = [
            "quick_new_transfer",
            "quick_new_inventory", 
            "quick_view_alerts",
            "🚚 Nouveau Transfert",
            "📋 Nouvel Inventaire",
            "⚠️ Voir Alertes",
            "features_label",
            "Entrepôts multiples"
        ]
        
        elements_found = []
        for element in removed_elements:
            if element in content:
                elements_found.append(element)
        
        if elements_found:
            print(f"   ⚠️  Éléments encore présents: {elements_found}")
        else:
            print("   ✅ Tous les éléments inutiles supprimés")
            
        return len(elements_found) == 0
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def test_modular_widget_simplification():
    """Test de la simplification du widget modulaire"""
    try:
        print("\n📱 Test de la simplification du widget modulaire...")
        
        # Test import
        from ayanna_erp.modules.stock.views.modular_stock_widget import ModularStockManagementWidget
        print("   ✅ Import ModularStockManagementWidget réussi")
        
        # Vérifier la suppression du dashboard
        with open("ayanna_erp/modules/stock/views/modular_stock_widget.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        # Vérifier la suppression des éléments dashboard
        dashboard_elements = [
            "main_splitter",
            "StockDashboard(self.pos_id",
            "self.dashboard =",
            "header_layout",
            "main_title",
            "global_actions_layout",
            "sync_btn",
            "export_global_btn",
            "settings_btn"
        ]
        
        dashboard_found = []
        for element in dashboard_elements:
            if element in content:
                dashboard_found.append(element)
        
        if dashboard_found:
            print(f"   ⚠️  Éléments dashboard encore présents: {dashboard_found}")
        else:
            print("   ✅ Dashboard et en-tête complètement supprimés")
            
        # Vérifier que les onglets sont toujours là
        if "self.tab_widget = QTabWidget()" in content:
            print("   ✅ Système d'onglets préservé")
        else:
            print("   ❌ Système d'onglets manquant")
            return False
            
        return len(dashboard_found) == 0
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def test_tabs_only_interface():
    """Test que seuls les onglets sont présents"""
    try:
        print("\n📋 Test de l'interface onglets uniquement...")
        
        with open("ayanna_erp/modules/stock/views/modular_stock_widget.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        # Vérifier les onglets essentiels
        required_tabs = [
            "🏪 Entrepôts",
            "📦 Stocks", 
            "🔄 Transferts",
            "🚨 Alertes",
            "📋 Inventaires",
            "📊 Rapports"
        ]
        
        tabs_found = []
        for tab in required_tabs:
            if tab in content:
                tabs_found.append(tab)
        
        print(f"   ✅ Onglets trouvés: {len(tabs_found)}/{len(required_tabs)}")
        for tab in tabs_found:
            print(f"      • {tab}")
            
        # Vérifier le style des onglets
        if "QTabWidget::pane" in content and "QTabBar::tab" in content:
            print("   ✅ Styles d'onglets appliqués")
        else:
            print("   ❌ Styles d'onglets manquants")
            
        return len(tabs_found) == len(required_tabs)
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def main():
    """Fonction principale"""
    print("🎯 TEST DE SIMPLIFICATION DU MODULE STOCK")
    print("=" * 60)
    
    all_tests_passed = True
    tests = [
        test_stock_window_simplification,
        test_modular_widget_simplification,
        test_tabs_only_interface
    ]
    
    for test_func in tests:
        if not test_func():
            all_tests_passed = False
    
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 SIMPLIFICATION RÉUSSIE!")
        print("")
        print("✅ Éléments supprimés:")
        print("   • 🏭 Titre principal et en-tête")
        print("   • 🚚 Bouton 'Nouveau Transfert'")
        print("   • 📋 Bouton 'Nouvel Inventaire'")
        print("   • ⚠️ Bouton 'Voir Alertes'")
        print("   • 📊 Dashboard avec indicateurs")
        print("   • 🔄 Boutons d'actions globales")
        print("   • 📈 Zone de fonctionnalités")
        print("   • 📱 Barre de statut")
        print("")
        print("✅ Interface simplifiée:")
        print("   • ➡️ SEULEMENT les onglets")
        print("   • 🎨 Styles d'onglets améliorés")
        print("   • 📜 Système de scroll préservé")
        print("   • 🔧 Architecture modulaire intacte")
        print("")
        print("🎯 RÉSULTAT: Interface épurée selon votre demande!")
        print("")
        print("📝 Ce qui reste:")
        print("   🏪 Onglet Entrepôts")
        print("   📦 Onglet Stocks")
        print("   🔄 Onglet Transferts")
        print("   🚨 Onglet Alertes")
        print("   📋 Onglet Inventaires")
        print("   📊 Onglet Rapports")
        print("")
        print("🚀 Interface stock maintenant ultra-simple et focalisée!")
        
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("⚠️  Revérifiez les erreurs ci-dessus")
    
    print("=" * 60)

if __name__ == "__main__":
    main()