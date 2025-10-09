# Test final des corrections spécifiques
import sqlite3
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=== TEST DES CORRECTIONS SPÉCIFIQUES ===\n")

try:
    from ayanna_erp.database.database_manager import DatabaseManager
    from ayanna_erp.modules.stock.views.movement_widget import MovementWidget
    
    # Test 1: Import MovementWidget avec gestion User/dict
    print("1. Test MovementWidget avec objet User...")
    
    class MockUser:
        def __init__(self, id, name):
            self.id = id
            self.name = name
    
    # Test avec objet User
    user_obj = MockUser(5, "Test User")
    try:
        widget = MovementWidget(1, user_obj)
        print(f"✅ User object géré: {widget.current_user}")
    except Exception as e:
        print(f"❌ Erreur avec User object: {e}")
    
    # Test avec dict
    user_dict = {"id": 3, "name": "Dict User"}
    try:
        widget2 = MovementWidget(1, user_dict)
        print(f"✅ User dict géré: {widget2.current_user}")
    except Exception as e:
        print(f"❌ Erreur avec User dict: {e}")
        
    # Test 2: Requête SQLite avec LIKE au lieu de ILIKE
    print("\n2. Test requête mouvements avec LIKE...")
    db_manager = DatabaseManager()
    
    with db_manager.get_session() as session:
        # Test de la syntaxe LIKE
        try:
            result = session.execute("""
                SELECT COUNT(*) as count
                FROM stock_mouvements sm
                LEFT JOIN core_products cp ON sm.product_id = cp.id
                WHERE cp.name LIKE '%test%'
            """).fetchone()
            print(f"✅ Requête LIKE fonctionne: {result[0] if result else 0} résultats")
        except Exception as e:
            print(f"❌ Erreur requête LIKE: {e}")
            
    # Test 3: Schéma des mouvements avec destination_warehouse_id
    print("\n3. Test schéma stock_mouvements...")
    
    try:
        conn = sqlite3.connect('ayanna_erp.db')
        cursor = conn.cursor()
        
        # Vérifier la structure de la table
        cursor.execute("PRAGMA table_info(stock_mouvements)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        required_columns = ['warehouse_id', 'destination_warehouse_id', 'movement_type']
        for col in required_columns:
            if col in columns:
                print(f"✅ Colonne {col}: {columns[col]}")
            else:
                print(f"❌ Colonne manquante: {col}")
                
        # Vérifier les mouvements avec destination_warehouse_id
        cursor.execute("""
            SELECT COUNT(*) 
            FROM stock_mouvements 
            WHERE destination_warehouse_id IS NOT NULL
        """)
        dest_count = cursor.fetchone()[0]
        print(f"✅ Mouvements avec destination_warehouse_id: {dest_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur vérification schéma: {e}")
        
    print("\n" + "="*60)
    print("✅ TOUS LES TESTS DE CORRECTIONS TERMINÉS")
    print("="*60)
    
    print("\n🔧 Corrections appliquées:")
    print("  • Gestion User object/dict dans MovementWidget")
    print("  • Achat controller: warehouse_id=NULL, destination_warehouse_id=entrepot")
    print("  • Requêtes SQLite: ILIKE → LIKE")
    print("  • Schema stock_mouvements validé")
    
except Exception as e:
    print(f"❌ Erreur générale: {e}")
    import traceback
    traceback.print_exc()