#!/usr/bin/env python3
"""
Script pour corriger toutes les références EventProduct -> CoreProduct dans le module salle de fête
"""

import os
import re

def fix_event_product_references():
    """Corrige toutes les références EventProduct dans le module salle de fête"""
    
    # Chemin du module salle de fête
    salle_fete_path = "ayanna_erp/modules/salle_fete"
    
    files_to_fix = []
    
    # Parcourir tous les fichiers Python du module salle de fête
    for root, dirs, files in os.walk(salle_fete_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                files_to_fix.append(file_path)
    
    print("=== CORRECTION DES REFERENCES EVENTPRODUCT -> COREPRODUCT ===")
    
    for file_path in files_to_fix:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Vérifier si le fichier contient des références EventProduct
            if 'EventProduct' in content:
                print(f"\n📁 Traitement de {file_path}")
                
                # Remplacements
                new_content = content.replace('EventProduct', 'CoreProduct')
                
                # Ajouter import CoreProduct si nécessaire
                if 'from ayanna_erp.modules.core.models import' not in new_content and 'CoreProduct' in new_content:
                    # Trouver les imports existants et ajouter CoreProduct
                    import_pattern = r'(from ayanna_erp\.modules\.salle_fete\.model\.salle_fete import.*?)\n'
                    match = re.search(import_pattern, new_content, re.MULTILINE)
                    if match:
                        # Ajouter l'import après les imports du modèle
                        insertion_point = match.end()
                        import_line = "from ayanna_erp.modules.core.models import CoreProduct, CoreProductCategory\n"
                        new_content = new_content[:insertion_point] + import_line + new_content[insertion_point:]
                
                # Écrire le fichier modifié
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print(f"✅ Fichier corrigé: {file_path}")
            
        except Exception as e:
            print(f"❌ Erreur avec {file_path}: {e}")
    
    print("\n🎉 CORRECTION TERMINÉE")
    print("Toutes les références EventProduct ont été remplacées par CoreProduct")

if __name__ == "__main__":
    fix_event_product_references()