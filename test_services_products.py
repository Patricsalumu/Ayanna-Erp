"""
Script de test pour les services et produits
Test d'ajout de services et produits d'exemple
"""

import sys
import os

# Ajouter le chemin de l'application
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from PyQt6.QtWidgets import QApplication
from ayanna_erp.modules.salle_fete.controller.service_controller import ServiceController
from ayanna_erp.modules.salle_fete.controller.produit_controller import ProduitController
from ayanna_erp.modules.salle_fete.controller.mainWindow_controller import MainWindowController


def test_services_and_products():
    """Tester l'ajout de services et produits d'exemple"""
    print("🧪 Test des services et produits...")
    
    # Initialiser la base de données
    main_controller = MainWindowController(pos_id=1)
    main_controller.initialize_database()
    
    # Contrôleurs
    service_controller = ServiceController(pos_id=1)
    produit_controller = ProduitController(pos_id=1)
    
    # Variables pour stocker les données
    services_data = []
    products_data = []
    
    # Mock des signaux pour récupérer les données
    def mock_services_loaded(services):
        nonlocal services_data
        services_data = services
    
    def mock_products_loaded(products):
        nonlocal products_data
        products_data = products
    
    # Connecter les signaux
    service_controller.services_loaded.connect(mock_services_loaded)
    produit_controller.products_loaded.connect(mock_products_loaded)
    
    try:
        # === TEST DES SERVICES ===
        print("\n📋 SERVICES:")
        service_controller.load_services()
        
        if services_data:
            print(f"✅ {len(services_data)} services trouvés:")
            for service in services_data:
                margin = service['price'] - service['cost']
                print(f"  • {service['name']} - Coût: {service['cost']:.2f}€ - Prix: {service['price']:.2f}€ - Marge: {margin:.2f}€")
        else:
            print("  Aucun service trouvé")
        
        # Ajouter un service personnalisé
        print("\n➕ Ajout d'un service personnalisé...")
        nouveau_service = {
            'name': 'Service VIP Complet',
            'description': 'Service premium avec coordinateur dédié',
            'cost': 300.0,
            'price': 600.0,
            'is_active': True
        }
        
        success = service_controller.add_service(nouveau_service)
        if success:
            print("✅ Service personnalisé ajouté avec succès")
        else:
            print("❌ Erreur lors de l'ajout du service")
        
        # === TEST DES PRODUITS ===
        print("\n📦 PRODUITS:")
        produit_controller.load_products()
        
        if products_data:
            print(f"✅ {len(products_data)} produits trouvés:")
            for product in products_data:
                stock_status = "⚠️ Stock faible" if product['stock_quantity'] <= product['stock_min'] else "✅ Stock OK"
                if product['stock_quantity'] == 0:
                    stock_status = "❌ Rupture"
                
                print(f"  • {product['name']} ({product['unit']}) - Stock: {product['stock_quantity']:.0f} - {stock_status}")
        else:
            print("  Aucun produit trouvé")
        
        # Ajouter un produit personnalisé
        print("\n➕ Ajout d'un produit personnalisé...")
        nouveau_produit = {
            'name': 'Cocktail Signature Maison',
            'description': 'Cocktail spécial de la maison',
            'category': 'Boissons',
            'unit': 'verre',
            'cost': 8.0,
            'price_unit': 15.0,
            'stock_quantity': 0,  # À préparer à la demande
            'stock_min': 0,
            'is_active': True
        }
        
        success = produit_controller.add_product(nouveau_produit)
        if success:
            print("✅ Produit personnalisé ajouté avec succès")
        else:
            print("❌ Erreur lors de l'ajout du produit")
        
        # Recharger pour voir les nouveaux éléments
        print("\n🔄 Rechargement des données...")
        service_controller.load_services()
        produit_controller.load_products()
        
        print(f"\n📊 RÉSUMÉ FINAL:")
        print(f"  Services: {len(services_data)} disponibles")
        print(f"  Produits: {len(products_data)} disponibles")
        
        # Calculer des statistiques
        total_service_value = sum(s['price'] for s in services_data)
        total_product_value = sum(p['price_unit'] * p['stock_quantity'] for p in products_data)
        
        print(f"  Valeur totale services: {total_service_value:.2f}€")
        print(f"  Valeur stock produits: {total_product_value:.2f}€")
        
        print("\n🎉 Test des services et produits terminé avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Fonction principale"""
    app = QApplication(sys.argv)
    test_services_and_products()


if __name__ == "__main__":
    main()
