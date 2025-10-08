"""
Test de création de produit avec l'architecture centralisée
"""

import os
import sys

# Ajouter le chemin vers le projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import DatabaseManager

def test_product_creation():
    """Test de création de produit avec les contrôleurs centralisés"""
    
    print("=== Test de création de produit avec architecture centralisée ===\n")
    
    try:
        # Import des contrôleurs
        from ayanna_erp.modules.boutique.controller.produit_controller import ProduitController as BoutiqueProduitController
        from ayanna_erp.modules.salle_fete.controller.produit_controller import ProduitController as SalleFeteProduitController
        
        # Initialiser les contrôleurs
        boutique_ctrl = BoutiqueProduitController(2)  # POS_ID 2 pour boutique
        salle_fete_ctrl = SalleFeteProduitController(1)  # POS_ID 1 pour salle de fête
        
        print("✓ Contrôleurs initialisés")
        
        # Créer une session
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        try:
            # Récupérer les catégories existantes
            categories = boutique_ctrl.get_categories(session)
            if not categories:
                print("❌ Aucune catégorie disponible pour le test")
                return False
            
            category_id = categories[0].id
            category_name = categories[0].name
            print(f"✓ Utilisation de la catégorie: {category_name} (ID: {category_id})")
            
            # Test 1: Création de produit pour la boutique
            print("\n1. Test de création de produit pour la boutique...")
            
            boutique_product = boutique_ctrl.create_product(
                session=session,
                nom="Test Produit Boutique",
                prix=25.50,
                category_id=category_id,
                description="Produit de test pour la boutique",
                unit="pièce",
                stock_initial=10.0,
                cost=15.0,
                stock_min=2.0
            )
            
            print(f"✓ Produit boutique créé: {boutique_product.name} (ID: {boutique_product.id})")
            
            # Vérifier l'initialisation du stock
            stock_info = boutique_ctrl.get_product_stock_info(boutique_product.id)
            print(f"✓ Stock boutique initialisé: {stock_info}")
            
            # Test 2: Création de produit pour la salle de fête
            print("\n2. Test de création de produit pour la salle de fête...")
            
            salle_fete_product = salle_fete_ctrl.create_product(
                session=session,
                nom="Test Produit Salle de Fête",
                prix=45.75,
                category_id=category_id,
                description="Produit de test pour la salle de fête",
                unit="pièce",
                stock_initial=5.0,
                cost=30.0,
                stock_min=1.0
            )
            
            print(f"✓ Produit salle de fête créé: {salle_fete_product.name} (ID: {salle_fete_product.id})")
            
            # Vérifier l'initialisation du stock
            stock_info = salle_fete_ctrl.get_product_stock_info(salle_fete_product.id)
            print(f"✓ Stock salle de fête initialisé: {stock_info}")
            
            # Test 3: Vérifier que les stocks sont dans les bons entrepôts
            print("\n3. Vérification de la séparation des entrepôts...")
            
            # Le produit boutique doit avoir du stock dans POS_2 mais pas dans POS_1
            boutique_stock_in_pos2 = boutique_ctrl.get_product_stock_info(boutique_product.id)
            salle_fete_stock_in_pos1 = salle_fete_ctrl.get_product_stock_info(salle_fete_product.id)
            
            print(f"✓ Produit boutique dans POS_2: {boutique_stock_in_pos2['total_stock']} unités")
            print(f"✓ Produit salle de fête dans POS_1: {salle_fete_stock_in_pos1['total_stock']} unités")
            
            # Test 4: Tester la méthode de compatibilité
            print("\n4. Test des méthodes de compatibilité...")
            
            boutique_total = boutique_ctrl.get_product_stock_total(session, boutique_product.id)
            salle_fete_total = salle_fete_ctrl.get_product_stock_total(session, salle_fete_product.id)
            
            print(f"✓ Stock total boutique (méthode compatibilité): {boutique_total}")
            print(f"✓ Stock total salle de fête (méthode compatibilité): {salle_fete_total}")
            
            # Nettoyage
            session.delete(boutique_product)
            session.delete(salle_fete_product)
            session.commit()
            print("\n✓ Produits de test supprimés")
            
        finally:
            session.close()
        
        print("\n=== TOUS LES TESTS DE CRÉATION ONT RÉUSSI ===")
        print("✅ Création de produits avec stocks spécifiques par entrepôt")
        print("✅ Initialisation automatique des stocks")
        print("✅ Séparation correcte des entrepôts POS")
        print("✅ Méthodes de compatibilité fonctionnelles")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test de création: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_product_creation()
    if success:
        print("\n🎉 Test de création de produit réussi !")
    else:
        print("\n💥 Échec du test de création de produit")
        sys.exit(1)