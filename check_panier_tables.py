#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vérifier les tables de panier existantes
"""

import sqlite3

def check_panier_tables():
    conn = sqlite3.connect('ayanna_erp.db')
    cursor = conn.cursor()
    
    # Chercher toutes les tables contenant "panier"
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%panier%'")
    panier_tables = [t[0] for t in cursor.fetchall()]
    
    print("=== TABLES PANIER EXISTANTES ===")
    for table in panier_tables:
        print(f"  - {table}")
    
    # Vérifier la structure de chaque table
    for table in panier_tables:
        print(f"\n=== STRUCTURE {table} ===")
        cursor.execute(f"PRAGMA table_info({table})")
        for col in cursor.fetchall():
            print(f"  {col[1]}: {col[2]}")
    
    conn.close()

if __name__ == "__main__":
    check_panier_tables()