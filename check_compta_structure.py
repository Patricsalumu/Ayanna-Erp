#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vérifier la structure des tables comptables
"""

import sqlite3

def check_compta_tables():
    conn = sqlite3.connect('ayanna_erp.db')
    cursor = conn.cursor()
    
    print("=== STRUCTURE COMPTA_ECRITURES ===")
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='compta_ecritures'")
    result = cursor.fetchone()
    if result:
        print("Définition SQL:")
        print(result[0])
    
    print("\n=== COLONNES COMPTA_ECRITURES ===")
    cursor.execute("PRAGMA table_info(compta_ecritures)")
    for col in cursor.fetchall():
        print(f"  {col[1]}: {col[2]} (NOT NULL: {bool(col[3])})")
    
    print("\n=== STRUCTURE COMPTA_JOURNAUX ===")
    cursor.execute("PRAGMA table_info(compta_journaux)")
    for col in cursor.fetchall():
        if 'date' in col[1]:
            print(f"  {col[1]}: {col[2]} (NOT NULL: {bool(col[3])})")
    
    conn.close()

if __name__ == "__main__":
    check_compta_tables()