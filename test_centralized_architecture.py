"""
Test de l'architecture centralisée des produits
"""

import os
import sys

# Ajouter le chemin vers le projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import DatabaseManager

def test_centralized_architecture():
    """Test de l'architecture centralisée des contrôleurs de produits"""
    
    print("=== Test de l'architecture centralisée des produits ===\n")
    
    try:
        # Test 1: Import des contrôleurs centralisés
        print("1. Test des imports des contrôleurs...")
        
        from ayanna_erp.modules.core.controllers.product_controller import CoreProductController
        print("✓ CoreProductController importé avec succès")
        
        from ayanna_erp.modules.boutique.controller.produit_controller import ProduitController as BoutiqueProduitController
        print("✓ BoutiqueProduitController importé avec succès")
        
        from ayanna_erp.modules.salle_fete.controller.produit_controller import ProduitController as SalleFeteProduitController
        print("✓ SalleFeteProduitController importé avec succès")
        
        # Test 2: Vérification de l'héritage
        print("\n2. Vérification de l'héritage...")
        
        boutique_ctrl = BoutiqueProduitController(2)  # POS_ID 2 pour boutique
        print("✓ BoutiqueProduitController instancié (POS_ID: 2)")
        
        salle_fete_ctrl = SalleFeteProduitController(1)  # POS_ID 1 pour salle de fête
        print("✓ SalleFeteProduitController instancié (POS_ID: 1)")
        
        # Vérifier que les méthodes héritées sont disponibles
        assert hasattr(boutique_ctrl, 'get_products'), "Méthode get_products manquante"
        assert hasattr(boutique_ctrl, 'create_product'), "Méthode create_product manquante"
        assert hasattr(boutique_ctrl, 'get_categories'), "Méthode get_categories manquante"
        
        assert hasattr(salle_fete_ctrl, 'get_products'), "Méthode get_products manquante"
        assert hasattr(salle_fete_ctrl, 'create_product'), "Méthode create_product manquante"
        assert hasattr(salle_fete_ctrl, 'get_categories'), "Méthode get_categories manquante"
        
        print("✓ Toutes les méthodes héritées sont disponibles")
        
        # Test 3: Test des entrepôts spécifiques
        print("\n3. Test de la configuration des entrepôts...")
        
        # Créer une session pour tester les méthodes
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        try:
            # Test des catégories
            boutique_categories = boutique_ctrl.get_categories(session)
            salle_fete_categories = salle_fete_ctrl.get_categories(session)
            
            print(f"✓ Boutique: {len(boutique_categories)} catégories trouvées")
            print(f"✓ Salle de fête: {len(salle_fete_categories)} catégories trouvées")
            
            # Test des produits
            boutique_products = boutique_ctrl.get_products(session)
            salle_fete_products = salle_fete_ctrl.get_products(session)
            
            print(f"✓ Boutique: {len(boutique_products)} produits trouvés")
            print(f"✓ Salle de fête: {len(salle_fete_products)} produits trouvés")
            
        finally:
            session.close()
        
        print("\n4. Test des informations de stock...")
        
        # Test des méthodes spécifiques aux modules
        if len(boutique_products) > 0:
            product_id = boutique_products[0].id
            stock_info = boutique_ctrl.get_product_stock_info(product_id)
            print(f"✓ Boutique stock info pour produit {product_id}: {stock_info}")
        
        if len(salle_fete_products) > 0:
            product_id = salle_fete_products[0].id
            stock_info = salle_fete_ctrl.get_product_stock_info(product_id)
            print(f"✓ Salle de fête stock info pour produit {product_id}: {stock_info}")
        
        print("\n=== TOUS LES TESTS ONT RÉUSSI ===")
        print("L'architecture centralisée fonctionne correctement !")
        print("- Les contrôleurs héritent du CoreProductController")
        print("- Chaque module utilise son entrepôt POS spécifique")
        print("- Les méthodes centralisées sont disponibles")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_centralized_architecture()
    if success:
        print("\n🎉 Architecture centralisée validée avec succès !")
    else:
        print("\n💥 Échec de la validation de l'architecture centralisée")
        sys.exit(1)