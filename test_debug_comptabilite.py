# Test diagnostic écritures comptables
import sqlite3
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=== DIAGNOSTIC ÉCRITURES COMPTABLES ===\n")

try:
    from ayanna_erp.database.database_manager import DatabaseManager
    from sqlalchemy import text
    
    db_manager = DatabaseManager()
    
    with db_manager.get_session() as session:
        
        # 1. Vérifier si les tables comptables existent
        print("1. Vérification des tables comptables...")
        
        tables_comptables = [
            'compta_config',
            'compta_journaux', 
            'compta_ecritures',
            'compta_comptes'
        ]
        
        for table in tables_comptables:
            try:
                result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.fetchone()[0]
                print(f"✅ Table {table}: {count} enregistrements")
            except Exception as e:
                print(f"❌ Table {table}: {e}")
        
        # 2. Vérifier la configuration comptable
        print("\n2. Vérification configuration comptable...")
        
        try:
            result = session.execute(text("""
                SELECT enterprise_id, compte_achat_id, compte_vente_id, compte_caisse_id
                FROM compta_config
            """))
            configs = result.fetchall()
            
            if configs:
                for config in configs:
                    print(f"✅ Config trouvée - Entreprise: {config[0]}, Achat: {config[1]}, Vente: {config[2]}, Caisse: {config[3]}")
            else:
                print("❌ AUCUNE CONFIGURATION COMPTABLE TROUVÉE!")
                print("   → C'est probablement pourquoi les écritures ne sont pas créées")
                
        except Exception as e:
            print(f"❌ Erreur config comptable: {e}")
        
        # 3. Vérifier les journaux comptables existants
        print("\n3. Vérification journaux comptables...")
        
        try:
            result = session.execute(text("""
                SELECT COUNT(*) FROM compta_journaux 
                WHERE type_operation = 'sortie' AND libelle LIKE '%Achat%'
            """))
            count = result.fetchone()[0]
            print(f"✅ Journaux d'achat trouvés: {count}")
            
            # Afficher les derniers journaux
            result = session.execute(text("""
                SELECT id, date_operation, libelle, montant, reference
                FROM compta_journaux 
                ORDER BY id DESC LIMIT 5
            """))
            journaux = result.fetchall()
            
            if journaux:
                print("   Derniers journaux:")
                for j in journaux:
                    print(f"     ID:{j[0]} - {j[1]} - {j[2]} - {j[3]}€ - Ref:{j[4]}")
            else:
                print("   Aucun journal trouvé")
                
        except Exception as e:
            print(f"❌ Erreur journaux: {e}")
        
        # 4. Vérifier les écritures comptables
        print("\n4. Vérification écritures comptables...")
        
        try:
            result = session.execute(text("SELECT COUNT(*) FROM compta_ecritures"))
            count = result.fetchone()[0]
            print(f"✅ Total écritures: {count}")
            
        except Exception as e:
            print(f"❌ Erreur écritures: {e}")
        
        # 5. Vérifier les comptes comptables
        print("\n5. Vérification comptes comptables...")
        
        try:
            result = session.execute(text("""
                SELECT numero, nom, libelle
                FROM compta_comptes 
                WHERE numero LIKE '6%' OR numero LIKE '4%' OR numero LIKE '5%'
                ORDER BY numero
            """))
            comptes = result.fetchall()
            
            if comptes:
                print("✅ Comptes comptables trouvés:")
                for c in comptes:
                    print(f"     {c[0]} - {c[1]} - {c[2]}")
            else:
                print("❌ AUCUN COMPTE COMPTABLE TROUVÉ!")
                print("   → Les comptes doivent être configurés avant les achats")
                
        except Exception as e:
            print(f"❌ Erreur comptes: {e}")
            
    print("\n" + "="*60)
    print("DIAGNOSTIC TERMINÉ")
    print("="*60)
    
    print("\n💡 RECOMMANDATIONS:")
    print("  1. Vérifier que compta_config est configuré pour l'entreprise")
    print("  2. Vérifier que les comptes comptables existent (classe 6, 4, 5)")
    print("  3. Regarder les logs lors des achats pour voir les erreurs")
    
except Exception as e:
    print(f"❌ Erreur générale: {e}")
    import traceback
    traceback.print_exc()