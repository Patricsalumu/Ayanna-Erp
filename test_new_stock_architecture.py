"""
Script de test pour la nouvelle architecture de stock simplifiée
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from decimal import Decimal
from datetime import datetime
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.stock.controllers.entrepot_controller import EntrepotController
from ayanna_erp.modules.stock.controllers.stock_controller import StockController


def test_new_architecture():
    """Test complet de la nouvelle architecture"""
    print("🧪 TEST DE LA NOUVELLE ARCHITECTURE STOCK")
    print("=" * 50)
    
    entreprise_id = 1
    test_results = []
    
    # Test 1: Initialisation des contrôleurs
    print("\n📋 Test 1: Initialisation des contrôleurs...")
    try:
        entrepot_controller = EntrepotController(entreprise_id)
        stock_controller = StockController(entreprise_id)
        print("✅ Contrôleurs initialisés avec succès")
        test_results.append(("Initialisation contrôleurs", "✅ Réussi"))
    except Exception as e:
        print(f"❌ Erreur initialisation: {e}")
        test_results.append(("Initialisation contrôleurs", f"❌ Échec: {e}"))
        return test_results
    
    # Test 2: Récupération des entrepôts
    print("\n📋 Test 2: Récupération des entrepôts...")
    try:
        db_manager = DatabaseManager()
        with db_manager.get_session() as session:
            warehouses = entrepot_controller.get_all_warehouses(session)
            print(f"✅ {len(warehouses)} entrepôts récupérés")
            
            if warehouses:
                print("   Entrepôts trouvés:")
                for wh in warehouses[:3]:  # Afficher les 3 premiers
                    print(f"     - {wh['name']} ({wh['code']}) - {'Défaut' if wh['is_default'] else 'Standard'}")
            
            test_results.append(("Récupération entrepôts", f"✅ {len(warehouses)} trouvés"))
    except Exception as e:
        print(f"❌ Erreur récupération entrepôts: {e}")
        test_results.append(("Récupération entrepôts", f"❌ Échec: {e}"))
    
    # Test 3: Vue d'ensemble des stocks
    print("\n📋 Test 3: Vue d'ensemble des stocks...")
    try:
        with db_manager.get_session() as session:
            stock_overview = stock_controller.get_stock_overview(session)
            print(f"✅ Vue d'ensemble: {stock_overview['total_items']} éléments")
            
            if stock_overview['stocks']:
                print("   Premiers stocks:")
                for stock in stock_overview['stocks'][:3]:
                    print(f"     - Produit {stock['product_id']}: {stock['quantity']} unités")
            
            test_results.append(("Vue d'ensemble stocks", f"✅ {stock_overview['total_items']} éléments"))
    except Exception as e:
        print(f"❌ Erreur vue d'ensemble: {e}")
        test_results.append(("Vue d'ensemble stocks", f"❌ Échec: {e}"))
    
    # Test 4: Création d'un nouvel entrepôt
    print("\n📋 Test 4: Création d'un nouvel entrepôt...")
    try:
        with db_manager.get_session() as session:
            warehouse_data = {
                'code': f'TEST_{datetime.now().strftime("%H%M%S")}',
                'name': f'Entrepôt Test {datetime.now().strftime("%H:%M:%S")}',
                'type': 'Test',
                'description': 'Entrepôt créé pour les tests'
            }
            
            new_warehouse = entrepot_controller.create_warehouse(session, warehouse_data)
            if new_warehouse:
                print(f"✅ Nouvel entrepôt créé: {new_warehouse['name']} (ID: {new_warehouse['id']})")
                test_results.append(("Création entrepôt", f"✅ ID: {new_warehouse['id']}"))
                
                # Test 4b: Statistiques de l'entrepôt
                stats = entrepot_controller.get_warehouse_stats(session, new_warehouse['id'])
                print(f"   Statistiques: {stats['total_products']} produits, valeur: {stats['total_value']:.2f}€")
            else:
                test_results.append(("Création entrepôt", "❌ Échec: Aucun retour"))
    except Exception as e:
        print(f"❌ Erreur création entrepôt: {e}")
        test_results.append(("Création entrepôt", f"❌ Échec: {e}"))
    
    # Test 5: Mise à jour de stock
    print("\n📋 Test 5: Mise à jour de stock...")
    try:
        with db_manager.get_session() as session:
            # Prendre le premier entrepôt et le premier produit
            warehouses = entrepot_controller.get_all_warehouses(session)
            if warehouses:
                warehouse_id = warehouses[0]['id']
                product_id = 1  # Assumons que le produit 1 existe
                
                # Mettre à jour le stock
                update_result = stock_controller.update_stock(
                    session, product_id, warehouse_id, 
                    Decimal('100.0'), Decimal('5.50'), 
                    'Test mise à jour', 1
                )
                
                print(f"✅ Stock mis à jour: Produit {product_id} → {update_result['new_quantity']} unités")
                test_results.append(("Mise à jour stock", f"✅ {update_result['new_quantity']} unités"))
            else:
                test_results.append(("Mise à jour stock", "❌ Aucun entrepôt disponible"))
    except Exception as e:
        print(f"❌ Erreur mise à jour stock: {e}")
        test_results.append(("Mise à jour stock", f"❌ Échec: {e}"))
    
    # Test 6: Détails stock produit
    print("\n📋 Test 6: Détails stock d'un produit...")
    try:
        with db_manager.get_session() as session:
            product_details = stock_controller.get_product_stock_details(session, 1)
            print(f"✅ Détails produit 1: {len(product_details['warehouses'])} entrepôts")
            print(f"   Quantité totale: {product_details['total_quantity']}")
            print(f"   Valeur totale: {product_details['total_value']:.2f}€")
            
            test_results.append(("Détails stock produit", f"✅ {len(product_details['warehouses'])} entrepôts"))
    except Exception as e:
        print(f"❌ Erreur détails produit: {e}")
        test_results.append(("Détails stock produit", f"❌ Échec: {e}"))
    
    # Test 7: Historique des mouvements
    print("\n📋 Test 7: Historique des mouvements...")
    try:
        with db_manager.get_session() as session:
            movements = stock_controller.get_stock_movements(session, limit=5)
            print(f"✅ {len(movements)} mouvements récupérés")
            
            if movements:
                print("   Derniers mouvements:")
                for mov in movements[:3]:
                    print(f"     - Produit {mov['product_id']}: {mov['quantity']} unités ({mov['movement_date']})")
            
            test_results.append(("Historique mouvements", f"✅ {len(movements)} trouvés"))
    except Exception as e:
        print(f"❌ Erreur historique: {e}")
        test_results.append(("Historique mouvements", f"❌ Échec: {e}"))
    
    # Test 8: Statistiques globales
    print("\n📋 Test 8: Statistiques globales...")
    try:
        with db_manager.get_session() as session:
            stats = stock_controller.get_stock_statistics(session)
            print(f"✅ Statistiques globales:")
            print(f"   Valeur totale: {stats['total_value']:.2f}€")
            print(f"   Produits uniques: {stats['unique_products']}")
            print(f"   Produits en rupture: {stats['out_of_stock_products']}")
            print(f"   Alertes stock faible: {stats['low_stock_alerts']}")
            
            test_results.append(("Statistiques globales", f"✅ {stats['unique_products']} produits"))
    except Exception as e:
        print(f"❌ Erreur statistiques: {e}")
        test_results.append(("Statistiques globales", f"❌ Échec: {e}"))
    
    # Résumé final
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    success_count = 0
    for test_name, result in test_results:
        print(f"{result:25} {test_name}")
        if result.startswith("✅"):
            success_count += 1
    
    print(f"\n🎯 Résultat: {success_count}/{len(test_results)} tests réussis")
    
    if success_count == len(test_results):
        print("🎉 TOUS LES TESTS RÉUSSIS! Architecture fonctionnelle.")
    elif success_count >= len(test_results) * 0.75:
        print("⚠️  Architecture majoritairement fonctionnelle, quelques ajustements nécessaires.")
    else:
        print("❌ Architecture nécessite des corrections importantes.")
    
    return test_results


if __name__ == "__main__":
    test_new_architecture()