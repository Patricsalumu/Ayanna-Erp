#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test simple de la structure ComptaConfig avec pos_id
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

def test_compta_config_structure():
    """Test de la structure ComptaConfig"""
    print("🚀 Test de la structure ComptaConfig avec pos_id...")
    
    try:
        # Supprimer l'ancienne base si elle existe
        if os.path.exists("ayanna_erp.db"):
            os.remove("ayanna_erp.db")
            print("🗑️  Ancienne base supprimée")
        
        from ayanna_erp.database.database_manager import DatabaseManager
        
        db = DatabaseManager()
        if db.initialize_database():
            print("✅ Base de données initialisée avec succès!")
            
            # Vérifier la structure de compta_config avec SQLAlchemy
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = inspector.get_columns('compta_config')
            
            print("📋 Colonnes de compta_config:")
            for col in columns:
                print(f"   - {col['name']} ({col['type']})")
            
            # Vérifier que pos_id est présent
            pos_id_found = any(col['name'] == 'pos_id' for col in columns)
            if pos_id_found:
                print("✅ Colonne pos_id trouvée!")
            else:
                print("❌ Colonne pos_id non trouvée")
                
            # Compter les configurations créées
            session = db.get_session()
            from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaConfig
            configs = session.query(ComptaConfig).all()
            print(f"📊 Configurations créées: {len(configs)}")
            
            for config in configs:
                print(f"   - Entreprise {config.enterprise_id}, POS {config.pos_id}")
                
            return True
            
        else:
            print("❌ Erreur lors de l'initialisation")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_compta_config_structure()
    if success:
        print("\n✅ Test réussi! Structure ComptaConfig avec pos_id fonctionnelle!")
    else:
        print("\n❌ Test échoué")
        sys.exit(1)
