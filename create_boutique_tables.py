"""
Script pour créer les tables du module Boutique
"""

import sys
import os

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_boutique_tables():
    """Crée toutes les tables du module Boutique"""
    try:
        print("🚀 Création des tables du module Boutique...")
        
        # Importer les modèles pour les enregistrer dans Base.metadata
        from ayanna_erp.modules.boutique.model.models import (
            ShopClient, ShopCategory, ShopProduct, ShopService, 
            ShopPanier, ShopPanierProduct, ShopPanierService,
            ShopPayment, ShopStock, ShopExpense, ShopComptesConfig
        )
        
        # Importer DatabaseManager pour créer les tables
        from ayanna_erp.database.database_manager import DatabaseManager, Base
        
        # Créer une instance du gestionnaire de DB
        db_manager = DatabaseManager()
        
        # Créer toutes les tables
        Base.metadata.create_all(db_manager.engine)
        
        print("✅ Tables créées avec succès!")
        
        # Vérifier les tables créées
        from sqlalchemy import inspect
        inspector = inspect(db_manager.engine)
        tables = inspector.get_table_names()
        
        boutique_tables = [table for table in tables if table.startswith('shop_')]
        
        print(f"\n📋 Tables du module Boutique créées ({len(boutique_tables)}):")
        for table in sorted(boutique_tables):
            print(f"   ✓ {table}")
            
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des tables: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_boutique_tables()
    if success:
        print("\n🎉 Tables du module Boutique prêtes!")
    else:
        print("\n💥 Échec de la création des tables.")