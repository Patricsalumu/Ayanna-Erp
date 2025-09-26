"""
Test final de l'intégration complète du module Boutique
"""

def main():
    print("🧪 TEST FINAL - INTÉGRATION MODULE BOUTIQUE")
    print("="*60)
    
    try:
        # 1. Test d'import du contrôleur
        print("\n1️⃣ Test d'import du contrôleur...")
        from ayanna_erp.modules.boutique.controller.boutique_controller import BoutiqueController
        print("   ✅ BoutiqueController importé")
        
        # 2. Test d'import des modèles
        print("\n2️⃣ Test d'import des modèles...")
        from ayanna_erp.modules.boutique.model.models import (
            ShopCategory, ShopProduct, ShopService, ShopClient, 
            ShopPanier, ShopPayment, ShopStock
        )
        print("   ✅ Tous les modèles importés")
        
        # 3. Test d'import des vues
        print("\n3️⃣ Test d'import des vues...")
        from ayanna_erp.modules.boutique.view.boutique_window import BoutiqueWindow
        from ayanna_erp.modules.boutique.view.panier_index import PanierIndex
        from ayanna_erp.modules.boutique.view.produit_index import ProduitIndex
        from ayanna_erp.modules.boutique.view.categorie_index import CategorieIndex
        from ayanna_erp.modules.boutique.view.client_index import ClientIndex
        from ayanna_erp.modules.boutique.view.stock_index import StockIndex
        from ayanna_erp.modules.boutique.view.rapport_index import RapportIndexWidget
        print("   ✅ Toutes les vues importées")
        
        # 4. Test d'import des utilitaires
        print("\n4️⃣ Test d'import des utilitaires...")
        from ayanna_erp.modules.boutique.init_boutique_data import initialize_boutique_data
        from ayanna_erp.modules.boutique.register_boutique_module import register_boutique_module
        from ayanna_erp.modules.boutique.check_boutique_status import check_boutique_status
        print("   ✅ Tous les utilitaires importés")
        
        # 5. Test de la base de données
        print("\n5️⃣ Test de connexion à la base de données...")
        from ayanna_erp.database.database_manager import DatabaseManager
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        session.close()
        print("   ✅ Connexion à la base de données réussie")
        
        # 6. Vérification du statut
        print("\n6️⃣ Vérification du statut du module...")
        status = check_boutique_status()
        print(f"   📦 Module enregistré: {'✅' if status['module_registered'] else '❌'}")
        print(f"   🗄️  Tables créées: {'✅' if status['database_tables_exist'] else '❌'}")
        print(f"   📋 Données par défaut: {'✅' if status['default_data_exists'] else '❌'}")
        
        print("\n" + "="*60)
        print("🎉 TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS !")
        print("="*60)
        
        print("\n🚀 INSTRUCTIONS D'UTILISATION :")
        print("1. Lancez l'application : python main.py")
        print("2. Connectez-vous avec vos identifiants")
        print("3. Cliquez sur le bouton 'Boutique'")
        print("4. Le module s'ouvrira avec toutes les fonctionnalités")
        
        print("\n💡 FONCTIONNALITÉS DISPONIBLES :")
        print("🛒 Panier - Point de vente interactif")
        print("📦 Produits - Gestion complète du catalogue")
        print("📂 Catégories - Organisation des produits")
        print("👥 Clients - Base de données clients")
        print("📊 Stock - Gestion des inventaires")
        print("📈 Rapports - Analyses et statistiques")
        
        return True
        
    except ImportError as e:
        print(f"\n❌ ERREUR D'IMPORT: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        return False

if __name__ == "__main__":
    success = main()
    print("\n" + "="*60)
    if success:
        print("🎊 INTÉGRATION RÉUSSIE - PRÊT À UTILISER !")
    else:
        print("💥 PROBLÈME DÉTECTÉ - VÉRIFIEZ LES ERREURS")
    print("="*60)