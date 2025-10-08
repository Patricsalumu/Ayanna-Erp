#!/usr/bin/env python3
"""
Script pour corriger toutes les références ShopCategory -> CoreProductCategory dans le module boutique
"""

import os
import re

def fix_shop_category_references():
    """Corrige toutes les références ShopCategory dans le module boutique"""
    
    # Chemin du module boutique
    boutique_path = "ayanna_erp/modules/boutique"
    
    files_to_fix = []
    
    # Parcourir tous les fichiers Python du module boutique
    for root, dirs, files in os.walk(boutique_path):
        for file in files:
            if file.endswith('.py') and 'models.py' not in file:  # Éviter models.py déjà traité
                file_path = os.path.join(root, file)
                files_to_fix.append(file_path)
    
    print("=== CORRECTION DES REFERENCES SHOPCATEGORY -> COREPRODUCTCATEGORY ===")
    
    for file_path in files_to_fix:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Vérifier si le fichier contient des références ShopCategory
            if 'ShopCategory' in content:
                print(f"\n📁 Traitement de {file_path}")
                
                # Remplacements
                new_content = content.replace('ShopCategory', 'CoreProductCategory')
                new_content = new_content.replace('ShopProduct', 'CoreProduct')
                
                # Ajouter import CoreProductCategory si nécessaire
                if 'from ayanna_erp.modules.core.models import' not in new_content and 'CoreProductCategory' in new_content:
                    # Trouver les imports existants et ajouter CoreProductCategory
                    if 'from ayanna_erp.modules.boutique.model.models import' in new_content:
                        # Ajouter l'import après les imports du modèle
                        import_pattern = r'(from ayanna_erp\.modules\.boutique\.model\.models import.*?)\n'
                        match = re.search(import_pattern, new_content, re.MULTILINE | re.DOTALL)
                        if match:
                            insertion_point = match.end()
                            import_line = "from ayanna_erp.modules.core.models import CoreProduct, CoreProductCategory\n"
                            new_content = new_content[:insertion_point] + import_line + new_content[insertion_point:]
                    else:
                        # Ajouter l'import au début après les imports PyQt
                        lines = new_content.split('\n')
                        insert_line = 0
                        for i, line in enumerate(lines):
                            if line.strip().startswith('from PyQt') or line.strip().startswith('from ayanna_erp'):
                                insert_line = i + 1
                        
                        if insert_line > 0:
                            lines.insert(insert_line, 'from ayanna_erp.modules.core.models import CoreProduct, CoreProductCategory')
                            new_content = '\n'.join(lines)
                
                # Adaptations spécifiques pour les requêtes
                # pos_id -> entreprise_id pour CoreProductCategory
                new_content = re.sub(
                    r'CoreProductCategory\.pos_id\s*==\s*(\w+)',
                    r'CoreProductCategory.entreprise_id == 1',  # Utilise entreprise_id 1
                    new_content
                )
                
                # filter(...pos_id == pos_id) -> filter(...entreprise_id == 1)
                new_content = re.sub(
                    r'filter\(CoreProductCategory\.pos_id\s*==\s*[^,)]+\)',
                    r'filter(CoreProductCategory.entreprise_id == 1)',
                    new_content
                )
                
                # Écrire le fichier modifié
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print(f"✅ Fichier corrigé: {file_path}")
            
        except Exception as e:
            print(f"❌ Erreur avec {file_path}: {e}")
    
    print("\n🎉 CORRECTION TERMINÉE")
    print("Toutes les références ShopCategory ont été remplacées par CoreProductCategory")

if __name__ == "__main__":
    fix_shop_category_references()