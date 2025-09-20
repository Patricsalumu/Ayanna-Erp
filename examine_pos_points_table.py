#!/usr/bin/env python3
"""
Script pour examiner la table core_pos_points et sa structure
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from ayanna_erp.database.database_manager import DatabaseManager
from sqlalchemy import text, inspect

def examine_pos_points_table():
    """Examiner la table core_pos_points"""
    print("🔍 Examen de la table core_pos_points")
    print("=" * 60)
    
    try:
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        # Vérifier l'existence de la table
        inspector = inspect(db_manager.engine)
        tables = inspector.get_table_names()
        
        if 'core_pos_points' in tables:
            print("✅ Table core_pos_points trouvée")
            
            # Examiner la structure de la table
            columns = inspector.get_columns('core_pos_points')
            print(f"\n📊 Structure de la table:")
            print("-" * 40)
            for column in columns:
                nullable = "NULL" if column['nullable'] else "NOT NULL"
                print(f"  {column['name']}: {column['type']} {nullable}")
            
            # Examiner les données existantes
            result = session.execute(text("SELECT * FROM core_pos_points"))
            rows = result.fetchall()
            
            print(f"\n📋 Données existantes ({len(rows)} lignes):")
            print("-" * 40)
            
            if rows:
                # Afficher les en-têtes
                column_names = [column['name'] for column in columns]
                print("  " + " | ".join(f"{name:15}" for name in column_names))
                print("  " + "-" * (16 * len(column_names)))
                
                # Afficher les données
                for row in rows:
                    print("  " + " | ".join(f"{str(value):15}" for value in row))
            else:
                print("  Aucune donnée trouvée")
            
            # Vérifier les clés étrangères
            foreign_keys = inspector.get_foreign_keys('core_pos_points')
            if foreign_keys:
                print(f"\n🔗 Clés étrangères:")
                print("-" * 40)
                for fk in foreign_keys:
                    print(f"  {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
            
            # Analyser la répartition par entreprise
            result = session.execute(text("""
                SELECT enterprise_id, COUNT(*) as count_pos
                FROM core_pos_points 
                GROUP BY enterprise_id
            """))
            enterprise_stats = result.fetchall()
            
            print(f"\n📈 Répartition par entreprise:")
            print("-" * 40)
            for stat in enterprise_stats:
                print(f"  Entreprise {stat[0]}: {stat[1]} point(s) de vente")
                
        else:
            print("❌ Table core_pos_points non trouvée")
            print("📋 Tables disponibles:")
            for table in sorted(tables):
                if 'pos' in table.lower() or 'point' in table.lower():
                    print(f"  - {table}")
        
        session.close()
        
    except Exception as e:
        print(f"❌ Erreur lors de l'examen: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    examine_pos_points_table()