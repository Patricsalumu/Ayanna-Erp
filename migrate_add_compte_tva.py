#!/usr/bin/env python3
"""
Migration : Ajouter le compte TVA à la configuration comptable
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from sqlalchemy import text, inspect
from ayanna_erp.database.database_manager import DatabaseManager

def migrate_add_compte_tva():
    """Ajouter la colonne compte_tva_id à la table compta_config"""
    print("🔄 Migration : Ajout du compte TVA à la configuration comptable")
    print("=" * 60)
    
    try:
        # Connexion à la base de données
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        # Vérifier si la colonne existe déjà
        inspector = inspect(db_manager.engine)
        columns = [col['name'] for col in inspector.get_columns('compta_config')]
        
        if 'compte_tva_id' in columns:
            print("✅ La colonne compte_tva_id existe déjà dans compta_config")
            return True
        
        # Ajouter la colonne compte_tva_id
        print("📝 Ajout de la colonne compte_tva_id...")
        session.execute(text("""
            ALTER TABLE compta_config 
            ADD COLUMN compte_tva_id INTEGER REFERENCES compta_comptes(id);
        """))
        
        session.commit()
        print("✅ Colonne compte_tva_id ajoutée avec succès")
        
        # Vérification
        columns_after = [col['name'] for col in inspector.get_columns('compta_config')]
        if 'compte_tva_id' in columns_after:
            print("✅ Vérification réussie : colonne présente")
        else:
            print("❌ Erreur : colonne non trouvée après ajout")
            return False
        
        db_manager.close_session()
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration : {e}")
        if 'session' in locals():
            session.rollback()
            db_manager.close_session()
        import traceback
        traceback.print_exc()
        return False

def test_compte_tva_config():
    """Test de l'ajout et de la récupération du compte TVA"""
    print("\n🧪 Test de configuration du compte TVA")
    print("=" * 60)
    
    try:
        from ayanna_erp.modules.comptabilite.comptabilite_controller import ComptabiliteController
        
        # Test de récupération de la configuration
        comptabilite_controller = ComptabiliteController()
        config = comptabilite_controller.get_config_by_pos(pos_id=1)
        
        if config:
            print(f"✅ Configuration trouvée pour POS 1")
            print(f"  - Compte caisse: {config.compte_caisse_id}")
            print(f"  - Compte vente: {config.compte_vente_id}")
            print(f"  - Compte TVA: {config.compte_tva_id}")
            
            # Tester l'accès au compte TVA via la relation
            if hasattr(config, 'compte_tva') and config.compte_tva:
                print(f"  - TVA : {config.compte_tva.numero} - {config.compte_tva.nom}")
            else:
                print("  - TVA : Non configuré")
        else:
            print("❌ Aucune configuration trouvée pour POS 1")
            
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Exécuter la migration
    success_migration = migrate_add_compte_tva()
    
    if success_migration:
        # Test de la nouvelle fonctionnalité
        success_test = test_compte_tva_config()
        
        if success_migration and success_test:
            print("\n🎉 Migration et tests réussis !")
            print("✅ Le compte TVA peut maintenant être configuré dans ComptaConfig")
            print("💡 Prochaine étape : Modifier l'interface de configuration pour permettre la sélection du compte TVA")
        else:
            print("\n⚠️ Migration réussie mais tests partiels")
    else:
        print("\n❌ Échec de la migration")
        sys.exit(1)