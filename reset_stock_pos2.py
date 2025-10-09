#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Réinitialiser le stock POS_2 avec des quantités positives pour tests
"""

import sqlite3

def reset_pos2_stock():
    conn = sqlite3.connect('ayanna_erp.db')
    cursor = conn.cursor()
    
    print("=== RÉINITIALISATION STOCK POS_2 ===")
    
    # Mettre à jour les stocks négatifs à 10 unités
    cursor.execute("""
        UPDATE stock_produits_entrepot 
        SET quantity = 10
        WHERE warehouse_id = (SELECT id FROM stock_warehouses WHERE code = 'POS_2')
        AND quantity <= 0
    """)
    
    affected_rows = cursor.rowcount
    conn.commit()
    
    print(f"✅ {affected_rows} produits mis à jour avec 10 unités de stock")
    
    # Afficher l'état actuel
    cursor.execute("""
        SELECT p.name, spe.quantity
        FROM stock_produits_entrepot spe
        JOIN core_products p ON spe.product_id = p.id
        JOIN stock_warehouses sw ON spe.warehouse_id = sw.id
        WHERE sw.code = 'POS_2'
        ORDER BY p.name
        LIMIT 10
    """)
    
    stocks = cursor.fetchall()
    print("\n=== STOCK POS_2 ACTUEL ===")
    for stock in stocks:
        print(f"  - {stock[0]}: {stock[1]}")
    
    conn.close()

if __name__ == "__main__":
    reset_pos2_stock()