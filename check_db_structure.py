#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vérifier la structure de la base de données
"""

import sqlite3

def check_database_structure():
    conn = sqlite3.connect('ayanna_erp.db')
    cursor = conn.cursor()
    
    # Lister toutes les tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    
    print("=== TABLES EXISTANTES ===")
    for table in sorted(tables):
        print(f"  - {table}")
    
    # Chercher tables POS
    pos_tables = [t for t in tables if 'pos' in t.lower()]
    print(f"\n=== TABLES POS ===")
    for table in pos_tables:
        print(f"  - {table}")
    
    # Chercher tables comptabilité
    compta_tables = [t for t in tables if 'compta' in t.lower()]
    print(f"\n=== TABLES COMPTABILITE ===")
    for table in compta_tables:
        print(f"  - {table}")
    
    # Vérifier table enterprises
    if 'enterprises' in tables:
        cursor.execute("SELECT id, name FROM enterprises LIMIT 3")
        enterprises = cursor.fetchall()
        print(f"\n=== ENTREPRISES ===")
        for ent in enterprises:
            print(f"  - ID: {ent[0]}, Nom: {ent[1]}")
    
    # Vérifier table warehouses
    if 'warehouses' in tables:
        cursor.execute("SELECT id, name FROM warehouses")
        warehouses = cursor.fetchall()
        print(f"\n=== ENTREPOTS ===")
        for wh in warehouses:
            print(f"  - ID: {wh[0]}, Nom: {wh[1]}")
    
    conn.close()

if __name__ == "__main__":
    check_database_structure()