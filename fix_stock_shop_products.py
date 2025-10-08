#!/usr/bin/env python3
"""
Script pour corriger toutes les références shop_products -> core_products dans le module stock
"""

import os
import re

def fix_shop_products_references():
    """Corrige toutes les références shop_products dans le module stock"""
    
    # Chemin du module stock
    stock_path = "ayanna_erp/modules/stock"
    
    # Pattern pour trouver les références shop_products
    pattern = r'LEFT JOIN shop_products'
    replacement = 'LEFT JOIN core_products'
    
    files_to_fix = []
    
    # Parcourir tous les fichiers Python du module stock
    for root, dirs, files in os.walk(stock_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                files_to_fix.append(file_path)
    
    print("=== CORRECTION DES REFERENCES SHOP_PRODUCTS -> CORE_PRODUCTS ===")
    
    for file_path in files_to_fix:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Vérifier si le fichier contient des références shop_products
            if 'shop_products' in content:
                print(f"\n📁 Traitement de {file_path}")
                
                # Remplacer shop_products par core_products
                new_content = content.replace('shop_products', 'core_products')
                
                # Écrire le fichier modifié
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print(f"✅ Fichier corrigé: {file_path}")
            
        except Exception as e:
            print(f"❌ Erreur avec {file_path}: {e}")
    
    print("\n🎉 CORRECTION TERMINÉE")
    print("Toutes les références shop_products ont été remplacées par core_products")

if __name__ == "__main__":
    fix_shop_products_references()