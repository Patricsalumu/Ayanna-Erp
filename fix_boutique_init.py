#!/usr/bin/env python3
"""
Script pour corriger pos_id -> entreprise_id dans init_boutique_data.py
"""

import re

def fix_pos_id_to_entreprise_id():
    file_path = "ayanna_erp/modules/boutique/init_boutique_data.py"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remplacer pos_id par entreprise_id dans les dictionnaires de données
        content = content.replace("'pos_id': 1,", "'entreprise_id': 1,")
        
        # Remplacer ShopCategory par CoreProductCategory
        content = content.replace("ShopCategory", "CoreProductCategory")
        
        # Remplacer ShopProduct par CoreProduct  
        content = content.replace("ShopProduct", "CoreProduct")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Fichier corrigé avec succès")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    fix_pos_id_to_entreprise_id()