#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vérifier les entrepôts et stock POS
"""

import sqlite3

def check_stock_tables():
    conn = sqlite3.connect('ayanna_erp.db')
    cursor = conn.cursor()
    
    # Tables de stock
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%stock%'")
    stock_tables = [t[0] for t in cursor.fetchall()]
    print("=== TABLES DE STOCK ===")
    for table in stock_tables:
        print(f"  - {table}")
    
    # Structure stock_warehouses
    print("\n=== STRUCTURE STOCK_WAREHOUSES ===")
    cursor.execute("PRAGMA table_info(stock_warehouses)")
    for col in cursor.fetchall():
        print(f"  - {col[1]}: {col[2]}")
    
    # Entrepôts POS
    print("\n=== ENTREPÔTS POS ===")
    cursor.execute("SELECT id, name, code FROM stock_warehouses WHERE name LIKE '%POS%' OR code LIKE '%POS%'")
    pos_warehouses = cursor.fetchall()
    for wh in pos_warehouses:
        print(f"  - ID: {wh[0]}, Nom: {wh[1]}, Code: {wh[2]}")
    
    # Si pas d'entrepôt POS_2, le créer
    if not any('POS_2' in str(wh) for wh in pos_warehouses):
        print("\n=== CRÉATION ENTREPÔT POS_2 ===")
        cursor.execute("""
            INSERT INTO stock_warehouses (name, code, location, is_active)
            VALUES ('Boutique POS 2', 'POS_2', 'Point de vente 2', 1)
        """)
        conn.commit()
        print("✅ Entrepôt POS_2 créé")
    
    # Stock dans POS_2
    print("\n=== STOCK POS_2 ===")
    cursor.execute("""
        SELECT p.name, spe.quantity
        FROM stock_produits_entrepot spe
        JOIN core_products p ON spe.product_id = p.id
        JOIN stock_warehouses sw ON spe.warehouse_id = sw.id
        WHERE sw.code = 'POS_2'
        LIMIT 5
    """)
    stocks = cursor.fetchall()
    for stock in stocks:
        print(f"  - {stock[0]}: {stock[1]}")
    
    if not stocks:
        print("  Aucun stock trouvé dans POS_2")
    
    conn.close()

if __name__ == "__main__":
    check_stock_tables()