"""
Script de test rapide pour le module Boutique
"""
import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.modules.boutique.register_boutique_module import register_boutique_module
from ayanna_erp.modules.boutique.check_boutique_status import check_boutique_status
from ayanna_erp.database.database_manager import DatabaseManager

def test_boutique_integration():
    """Test rapide de l'intégration du module Boutique"""
    
    print("🧪 Test de l'intégration du module Boutique")
    print("-" * 50)
    
    try:
        # 1. Vérifier la base de données
        db_manager = DatabaseManager()
        db_manager.connect()
        print("✅ Connexion à la base de données réussie")
        
        # 2. Vérifier le statut du module
        status = check_boutique_status()
        print(f"📊 Statut actuel du module : {status}")
        
        # 3. Si pas enregistré, l'enregistrer
        if not status['module_registered']:
            print("⏳ Enregistrement du module...")
            success = register_boutique_module()
            if success:
                print("✅ Module enregistré avec succès")
            else:
                print("❌ Erreur lors de l'enregistrement")
                return
        
        # 4. Vérifier les tables créées
        from ayanna_erp.modules.boutique.model.models import (
            ShopCategory, ShopProduct, ShopService, ShopClient,
            ShopPanier, ShopPayment, ShopStock
        )
        
        session = db_manager.get_session()
        
        # Compter les enregistrements
        categories_count = session.query(ShopCategory).count()
        products_count = session.query(ShopProduct).count()
        services_count = session.query(ShopService).count()
        clients_count = session.query(ShopClient).count()
        
        print(f"📂 Catégories : {categories_count}")
        print(f"📦 Produits : {products_count}")
        print(f"🔧 Services : {services_count}")
        print(f"👥 Clients : {clients_count}")
        
        session.close()
        
        # 5. Test d'import du widget principal
        try:
            from ayanna_erp.modules.boutique.view.boutique_window import BoutiqueWindow
            print("✅ Import de BoutiqueWindow réussi")
        except ImportError as e:
            print(f"❌ Erreur import BoutiqueWindow : {e}")
        
        print("\n🎉 Test d'intégration terminé avec succès !")
        print("🚀 Vous pouvez maintenant lancer main_window.py et cliquer sur Boutique")
        
    except Exception as e:
        print(f"❌ Erreur durante le test : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_boutique_integration()