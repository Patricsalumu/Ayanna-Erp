"""
Script pour créer/recréer les tables du module Achats
À exécuter pour initialiser les nouvelles tables
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.database.base import Base

def create_achats_tables():
    """Crée les tables du module Achats"""
    print("🔧 Création des tables du module Achats...")
    
    try:
        # Initialiser le gestionnaire de base de données
        db_manager = DatabaseManager()
        
        # Importer les modèles Achats pour qu'ils soient dans Base.metadata
        from ayanna_erp.modules.achats.models import (
            CoreFournisseur, AchatCommande, AchatCommandeLigne, AchatDepense
        )
        
        print("✅ Modèles Achats importés")
        
        # Créer toutes les tables (y compris les nouvelles)
        Base.metadata.create_all(bind=db_manager.engine)
        
        print("✅ Tables créées avec succès!")
        
        # Initialiser les données de test
        print("\n🏪 Initialisation des données de test...")
        from ayanna_erp.modules.achats.init_achats_data import init_achats_data
        
        session = db_manager.get_session()
        success = init_achats_data(session)
        session.close()
        
        if success:
            print("✅ Données de test initialisées!")
        else:
            print("⚠️  Erreur lors de l'initialisation des données")
        
        print("\n🎉 Module Achats prêt à être utilisé!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des tables: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_tables():
    """Vérifie que les tables existent"""
    print("\n🔍 Vérification des tables...")
    
    try:
        db_manager = DatabaseManager()
        
        # Lister toutes les tables
        from sqlalchemy import inspect
        inspector = inspect(db_manager.engine)
        tables = inspector.get_table_names()
        
        achats_tables = [
            'core_fournisseurs',
            'achat_commandes', 
            'achat_commande_lignes',
            'achat_depenses'
        ]
        
        for table in achats_tables:
            if table in tables:
                print(f"✅ Table '{table}' existe")
            else:
                print(f"❌ Table '{table}' manquante")
        
        return all(table in tables for table in achats_tables)
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

if __name__ == "__main__":
    print("🚀 INITIALISATION DU MODULE ACHATS")
    print("=" * 50)
    
    # Créer les tables
    if create_achats_tables():
        # Vérifier les tables
        if verify_tables():
            print("\n🎊 SUCCÈS - Module Achats complètement initialisé!")
        else:
            print("\n⚠️  ATTENTION - Certaines tables manquent")
    else:
        print("\n💥 ÉCHEC - Erreur lors de l'initialisation")
        sys.exit(1)