#!/usr/bin/env python3
"""
Vérification de la structure de la table compta_config
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from sqlalchemy import text, inspect
from ayanna_erp.database.database_manager import DatabaseManager

def verify_table_structure():
    """Vérifier la structure de la table compta_config"""
    print("🔍 Vérification de la structure de compta_config")
    print("=" * 60)
    
    try:
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        # Méthode 1: Via l'inspector SQLAlchemy
        print("📋 Colonnes via inspector :")
        inspector = inspect(db_manager.engine)
        columns = inspector.get_columns('compta_config')
        for col in columns:
            print(f"  - {col['name']} ({col['type']})")
        
        # Méthode 2: Via requête SQL directe
        print("\n📋 Colonnes via PRAGMA (SQLite) :")
        result = session.execute(text("PRAGMA table_info(compta_config);"))
        for row in result:
            print(f"  - {row[1]} ({row[2]})")
        
        # Vérifier spécifiquement compte_tva_id
        column_names = [col['name'] for col in columns]
        if 'compte_tva_id' in column_names:
            print(f"\n✅ compte_tva_id trouvé dans la table")
        else:
            print(f"\n❌ compte_tva_id NOT FOUND dans la table")
            
        db_manager.close_session()
        return 'compte_tva_id' in column_names
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    verify_table_structure()