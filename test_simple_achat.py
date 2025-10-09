# Test simple achat
from ayanna_erp.database.database_manager import DatabaseManager
from sqlalchemy import text

print("=== TEST ACHAT AVEC NOUVELLE LOGIQUE ===")

try:
    db = DatabaseManager()
    with db.get_session() as session:
        # Test insertion achat
        result = session.execute(text("""
            INSERT INTO stock_mouvements 
            (product_id, warehouse_id, destination_warehouse_id, movement_type, quantity, 
             unit_cost, total_cost, reference, description, movement_date)
            VALUES (1, 1, NULL, 'ENTREE', 5.0, 3.0, 15.0, 'TEST-ACHAT', 'Test achat corrigé', CURRENT_TIMESTAMP)
        """))
        session.commit()
        print('✅ Achat inséré avec succès!')
        
        # Vérifier l'insertion
        result = session.execute(text("SELECT * FROM stock_mouvements WHERE reference = 'TEST-ACHAT'"))
        movement = result.fetchone()
        if movement:
            print(f'✅ Mouvement créé: warehouse_id={movement[2]}, destination_warehouse_id={movement[8]}')
        
        # Nettoyer
        session.execute(text("DELETE FROM stock_mouvements WHERE reference = 'TEST-ACHAT'"))
        session.commit()
        print('✅ Test nettoyé')

except Exception as e:
    print(f'❌ Erreur: {e}')
    import traceback
    traceback.print_exc()