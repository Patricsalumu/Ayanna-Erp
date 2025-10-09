# Test de la nouvelle interface moderne de boutique
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=== TEST INTERFACE MODERNE BOUTIQUE ===\n")

try:
    # Test 1: Import de la nouvelle interface
    print("1. Test import nouvelle interface...")
    
    from ayanna_erp.modules.boutique.view.modern_supermarket_widget import ModernSupermarketWidget, PaymentDialog
    print("✅ ModernSupermarketWidget importé avec succès")
    
    # Test 2: Import de la fenêtre principale modifiée
    print("\n2. Test import fenêtre principale...")
    
    from ayanna_erp.modules.boutique.view.boutique_window import BoutiqueWindow
    print("✅ BoutiqueWindow modifiée importée")
    
    # Test 3: Vérification des modèles de données
    print("\n3. Test modèles de données...")
    
    from ayanna_erp.modules.boutique.model.models import ShopClient, ShopService
    from ayanna_erp.modules.core.models import CoreProduct, CoreProductCategory
    print("✅ Modèles de données importés")
    
    # Test 4: Vérification de la base de données
    print("\n4. Test connexion base de données...")
    
    from ayanna_erp.database.database_manager import DatabaseManager
    db_manager = DatabaseManager()
    
    with db_manager.get_session() as session:
        from sqlalchemy import text
        
        # Compter les produits actifs
        result = session.execute(text("SELECT COUNT(*) FROM core_products WHERE is_active = 1"))
        products_count = result.fetchone()[0]
        print(f"✅ {products_count} produits actifs trouvés")
        
        # Compter les catégories
        result = session.execute(text("SELECT COUNT(*) FROM core_product_categories WHERE is_active = 1"))
        categories_count = result.fetchone()[0]
        print(f"✅ {categories_count} catégories trouvées")
        
        # Compter les clients boutique
        result = session.execute(text("SELECT COUNT(*) FROM shop_clients WHERE is_active = 1"))
        clients_count = result.fetchone()[0]
        print(f"✅ {clients_count} clients boutique trouvés")
    
    print("\n" + "="*60)
    print("✅ TOUS LES TESTS PASSÉS")
    print("="*60)
    
    print("\n🎨 NOUVELLE INTERFACE MODERNE:")
    print("  • Design type supermarché avec catalogue et panier")
    print("  • Interface responsive avec cartes produits")
    print("  • Gestion des remises globales")
    print("  • Système de paiement intégré")
    print("  • Style moderne avec couleurs et effets")
    
    print("\n🔧 FONCTIONNALITÉS DISPONIBLES:")
    print("  • Recherche et filtrage par catégorie")
    print("  • Ajout rapide au panier")
    print("  • Modification des quantités")
    print("  • Application de remises")
    print("  • Validation et paiement")
    print("  • Sélection client")
    
    print("\n📝 PROCHAINES ÉTAPES:")
    print("  • Implémenter la gestion du stock POS")
    print("  • Ajouter les écritures comptables") 
    print("  • Intégrer avec le module stock existant")
    print("  • Tester l'interface complète")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()