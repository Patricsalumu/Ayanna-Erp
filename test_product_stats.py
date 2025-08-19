#!/usr/bin/env python3
"""
Script de test pour les nouvelles fonctionnalités de statistiques des produits
"""

import sys
import os

# Ajouter le chemin vers le module
sys.path.append(os.path.dirname(__file__))

from ayanna_erp.modules.salle_fete.controller.produit_controller import ProduitController

def test_product_statistics():
    """Test les nouvelles méthodes de statistiques des produits"""
    
    print("🧪 Test des statistiques et mouvements des produits")
    print("=" * 60)
    
    # Initialiser le contrôleur
    controller = ProduitController()
    
    # Récupérer la liste des produits
    print("📋 Récupération des produits disponibles...")
    products = controller.get_all_products()
    
    if not products:
        print("❌ Aucun produit trouvé dans la base de données")
        return
    
    print(f"✅ {len(products)} produit(s) trouvé(s)")
    
    # Tester avec le premier produit
    product = products[0]
    product_id = product.id
    product_name = product.name
    
    print(f"\n🔍 Test avec le produit: {product_name} (ID: {product_id})")
    print("-" * 40)
    
    # Test des statistiques de vente
    print("📊 Test des statistiques de vente...")
    stats = controller.get_product_sales_statistics(product_id)
    
    if stats is not None:
        print("✅ Statistiques de vente récupérées avec succès:")
        print(f"  - Quantité totale vendue: {stats['total_sold']}")
        print(f"  - Nombre de ventes: {stats['total_sales']}")
        print(f"  - Revenus totaux: {stats['total_revenue']:.2f} €")
        print(f"  - Quantité moyenne par vente: {stats['average_quantity']}")
        print(f"  - Dernière vente: {stats['last_sale']}")
    else:
        print("❌ Erreur lors de la récupération des statistiques de vente")
    
    # Test des mouvements récents
    print("\n📦 Test des mouvements de stock récents...")
    movements = controller.get_product_recent_movements(product_id, limit=5)
    
    if movements is not None:
        print(f"✅ {len(movements)} mouvement(s) récent(s) récupéré(s):")
        for i, movement in enumerate(movements, 1):
            movement_type = movement['type']
            date = movement['date']
            client = movement['client_name']
            quantity = movement['quantity']
            reason = movement['reason']
            
            print(f"  {i}. {date} - {movement_type} - {client}")
            print(f"     Quantité: {quantity}, Motif: {reason}")
            if movement['total_line'] > 0:
                print(f"     Total: {movement['total_line']:.2f} €")
    else:
        print("❌ Erreur lors de la récupération des mouvements")
    
    print("\n🎉 Test terminé!")

if __name__ == "__main__":
    try:
        test_product_statistics()
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()
