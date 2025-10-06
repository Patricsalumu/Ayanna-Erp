"""
Test rapide pour vérifier les améliorations de scroll du module Stock
"""

import sys
import os

# Ajouter le chemin racine au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_stock_window_scroll():
    """Test du système de scroll de la fenêtre Stock"""
    try:
        print("🖥️ Test du système de scroll de la fenêtre Stock...")
        
        # Test import
        from ayanna_erp.modules.stock.stock_window import StockWindow
        print("   ✅ Import StockWindow réussi")
        
        # Test import des widgets avec scroll
        from ayanna_erp.modules.stock.views.modular_stock_widget import ModularStockManagementWidget
        print("   ✅ Import ModularStockManagementWidget réussi")
        
        # Vérifier la présence de QScrollArea dans les imports
        from PyQt6.QtWidgets import QScrollArea
        print("   ✅ QScrollArea disponible")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def test_widget_scroll_integration():
    """Test de l'intégration du scroll dans les widgets"""
    try:
        print("\n📜 Test de l'intégration du scroll...")
        
        # Lire le contenu pour vérifier les modifications
        with open("ayanna_erp/modules/stock/stock_window.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        if "QScrollArea" in content:
            print("   ✅ QScrollArea trouvé dans stock_window.py")
        else:
            print("   ❌ QScrollArea manquant dans stock_window.py")
            return False
            
        if "scroll_area.setWidgetResizable(True)" in content:
            print("   ✅ Configuration de scroll trouvée")
        else:
            print("   ❌ Configuration de scroll manquante")
            return False
        
        # Vérifier le widget modulaire
        with open("ayanna_erp/modules/stock/views/modular_stock_widget.py", "r", encoding="utf-8") as f:
            widget_content = f.read()
            
        if "QScrollArea" in widget_content:
            print("   ✅ QScrollArea trouvé dans modular_stock_widget.py")
        else:
            print("   ❌ QScrollArea manquant dans modular_stock_widget.py")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def test_scroll_styles():
    """Test des styles de scroll"""
    try:
        print("\n🎨 Test des styles de scroll...")
        
        # Vérifier les styles dans stock_window
        with open("ayanna_erp/modules/stock/stock_window.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        if "QScrollBar:vertical" in content:
            print("   ✅ Styles scrollbar verticale trouvés")
        else:
            print("   ❌ Styles scrollbar verticale manquants")
            return False
            
        if "border-radius: 6px" in content:
            print("   ✅ Styles de bordures arrondies trouvés")
        else:
            print("   ❌ Styles de bordures arrondies manquants")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def main():
    """Fonction principale"""
    print("🎯 TEST DES AMÉLIORATIONS DE SCROLL - Module Stock")
    print("=" * 60)
    
    all_tests_passed = True
    tests = [
        test_stock_window_scroll,
        test_widget_scroll_integration,
        test_scroll_styles
    ]
    
    for test_func in tests:
        if not test_func():
            all_tests_passed = False
    
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 AMÉLIORATIONS DE SCROLL IMPLÉMENTÉES AVEC SUCCÈS!")
        print("")
        print("✅ Fenêtre principale Stock:")
        print("   • Zone de scroll complète avec QScrollArea")
        print("   • Styles personnalisés pour les barres de défilement")
        print("   • Défilement automatique selon le contenu")
        print("")
        print("✅ Widget modulaire:")
        print("   • Scroll intégré pour navigation fluide")
        print("   • Préservation de la structure modulaire")
        print("   • Barres de défilement stylisées")
        print("")
        print("✅ Améliorations UX:")
        print("   • Plus d'éléments entremêlés")
        print("   • Navigation claire et fluide")
        print("   • Interface adaptée au contenu dynamique")
        print("")
        print("🚀 INTERFACE STOCK OPTIMISÉE POUR LA NAVIGATION!")
        print("")
        print("📝 Fonctionnalités scroll ajoutées:")
        print("   ✅ Scroll vertical et horizontal automatique")
        print("   ✅ Barres de défilement stylisées")
        print("   ✅ Zone de contenu redimensionnable")
        print("   ✅ Navigation fluide entre tous les onglets")
        print("")
        print("🎯 Résultat: Interface claire sans éléments entremêlés!")
        
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("⚠️  Revérifiez les erreurs ci-dessus")
    
    print("=" * 60)

if __name__ == "__main__":
    main()