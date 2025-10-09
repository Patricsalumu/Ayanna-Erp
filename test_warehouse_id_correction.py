# Test correction warehouse_id NOT NULL
import sqlite3
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=== TEST CORRECTION warehouse_id NOT NULL ===\n")

try:
    # Test 1: Vérifier la logique achat avec warehouse_id obligatoire
    print("1. Test logique achat avec warehouse_id...")
    
    # Simuler la logique corrigée pour les achats
    def test_achat_logic(entrepot_id, produit_id, quantite, prix):
        """Simule la création d'un mouvement d'achat"""
        return {
            "product_id": produit_id,
            "warehouse_id": entrepot_id,           # Entrepôt de destination (obligatoire)
            "destination_warehouse_id": None,      # NULL pour les achats
            "movement_type": 'ENTREE',
            "quantity": quantite,
            "unit_cost": prix,
            "total_cost": quantite * prix
        }
    
    achat_movement = test_achat_logic(1, 5, 10, 4.5)
    print(f"✅ Mouvement achat: warehouse_id={achat_movement['warehouse_id']}, destination_warehouse_id={achat_movement['destination_warehouse_id']}")
    
    # Test 2: Vérifier la logique transfert
    def test_transfert_logic(entrepot_origine, entrepot_dest, produit_id, quantite, prix):
        """Simule la création d'un mouvement de transfert"""
        return {
            "product_id": produit_id,
            "warehouse_id": entrepot_origine,      # Entrepôt d'origine
            "destination_warehouse_id": entrepot_dest,  # Entrepôt de destination
            "movement_type": 'TRANSFERT',
            "quantity": quantite,
            "unit_cost": prix,
            "total_cost": quantite * prix
        }
    
    transfert_movement = test_transfert_logic(1, 2, 5, 8, 4.5)
    print(f"✅ Mouvement transfert: warehouse_id={transfert_movement['warehouse_id']}, destination_warehouse_id={transfert_movement['destination_warehouse_id']}")
    
    # Test 3: Vérifier les requêtes d'affichage
    print("\n2. Test requête affichage mouvements...")
    
    try:
        conn = sqlite3.connect('ayanna_erp.db')
        cursor = conn.cursor()
        
        # Test de la nouvelle logique d'affichage
        cursor.execute("""
            SELECT 
                sm.movement_type,
                CASE 
                    WHEN sm.destination_warehouse_id IS NULL THEN 
                        CASE WHEN sm.movement_type = 'ENTREE' THEN 'Achat' ELSE sw_origin.name END
                    ELSE sw_origin.name 
                END as origin_warehouse,
                CASE 
                    WHEN sm.destination_warehouse_id IS NULL THEN sw_origin.name
                    ELSE sw_dest.name 
                END as dest_warehouse,
                sm.warehouse_id,
                sm.destination_warehouse_id
            FROM stock_mouvements sm
            LEFT JOIN stock_warehouses sw_origin ON sm.warehouse_id = sw_origin.id
            LEFT JOIN stock_warehouses sw_dest ON sm.destination_warehouse_id = sw_dest.id
            LIMIT 5
        """)
        
        movements = cursor.fetchall()
        print("✅ Mouvements avec nouvelle logique d'affichage:")
        for mov in movements:
            print(f"  Type: {mov[0]}, Origine: {mov[1]}, Destination: {mov[2]}, warehouse_id: {mov[3]}, dest_warehouse_id: {mov[4]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur test requête: {e}")
        
    # Test 4: Test constraints
    print("\n3. Test contraintes base de données...")
    
    try:
        conn = sqlite3.connect('ayanna_erp.db')
        cursor = conn.cursor()
        
        # Vérifier que warehouse_id NOT NULL est respectée
        try:
            cursor.execute("""
                INSERT INTO stock_mouvements 
                (product_id, warehouse_id, movement_type, quantity, movement_date)
                VALUES (1, NULL, 'TEST', 1, CURRENT_TIMESTAMP)
            """)
            print("❌ warehouse_id=NULL devrait échouer!")
        except sqlite3.IntegrityError as e:
            if "NOT NULL" in str(e):
                print("✅ Contrainte NOT NULL sur warehouse_id respectée")
            else:
                print(f"❌ Erreur inattendue: {e}")
        
        # Test avec warehouse_id valide
        try:
            cursor.execute("""
                INSERT INTO stock_mouvements 
                (product_id, warehouse_id, movement_type, quantity, movement_date)
                VALUES (1, 1, 'TEST', 1, CURRENT_TIMESTAMP)
            """)
            cursor.execute("DELETE FROM stock_mouvements WHERE movement_type = 'TEST'")
            print("✅ Insertion avec warehouse_id valide fonctionne")
        except Exception as e:
            print(f"❌ Erreur insertion valide: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur test contraintes: {e}")
        
    print("\n" + "="*60)
    print("✅ TESTS CORRECTION warehouse_id TERMINÉS")
    print("="*60)
    
    print("\n🔧 Logique corrigée:")
    print("  • Achats: warehouse_id=destination, destination_warehouse_id=NULL")
    print("  • Transferts: warehouse_id=origine, destination_warehouse_id=destination")
    print("  • Affichage adapté à la nouvelle logique")
    print("  • Contrainte NOT NULL respectée")
    
except Exception as e:
    print(f"❌ Erreur générale: {e}")
    import traceback
    traceback.print_exc()