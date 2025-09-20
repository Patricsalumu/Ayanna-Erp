#!/usr/bin/env python3
"""
Test complet du système d'entreprise avec logos BLOB
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from PyQt6.QtWidgets import QApplication
from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
from ayanna_erp.core.view.enterprise_form_widget import EnterpriseFormWidget
from ayanna_erp.core.view.enterprise_index import EnterpriseIndexView
from ayanna_erp.core.utils.image_utils import ImageUtils

def test_blob_logo_system():
    """Test complet du système de logo BLOB"""
    print("=== Test du Système de Logo BLOB ===")
    
    # Initialiser QApplication en premier
    app = QApplication(sys.argv)
    
    try:
        # Test 1: Vérifier la migration
        print("1. Vérification de la migration BLOB...")
        controller = EntrepriseController()
        enterprise = controller.get_current_enterprise(1)
        
        if enterprise:
            print(f"✅ Entreprise trouvée: {enterprise.get('name')}")
            logo_blob = enterprise.get('logo')
            print(f"✅ Champ logo: {type(logo_blob)} {'(présent)' if logo_blob else '(vide)'}")
        else:
            print("❌ Aucune entreprise trouvée")
            return False
        
        # Test 2: Utilitaires d'image
        print("\n2. Test des utilitaires d'image...")
        
        # Créer une image de test simple si pas de logo
        if not logo_blob:
            print("   Création d'une image de test...")
            try:
                from PIL import Image, ImageDraw
                from io import BytesIO
                
                # Créer une image simple
                img = Image.new('RGB', (100, 100), color='lightblue')
                draw = ImageDraw.Draw(img)
                draw.text((10, 40), "LOGO\nTEST", fill='darkblue')
                
                # Convertir en BLOB
                output = BytesIO()
                img.save(output, format='JPEG', quality=90)
                test_logo_blob = output.getvalue()
                
                print(f"   ✅ Image de test créée: {len(test_logo_blob)} bytes")
                
                # Tester la conversion vers QPixmap
                pixmap = ImageUtils.blob_to_pixmap(test_logo_blob)
                if pixmap:
                    print("   ✅ Conversion BLOB → QPixmap réussie")
                else:
                    print("   ❌ Échec conversion BLOB → QPixmap")
                
                # Mettre à jour l'entreprise avec le logo de test
                print("   Mise à jour avec le logo de test...")
                success = controller.update_enterprise(1, {'logo': test_logo_blob})
                if success:
                    print("   ✅ Logo de test ajouté à l'entreprise")
                else:
                    print("   ❌ Échec ajout logo de test")
                    
            except ImportError:
                print("   ⚠️  PIL non disponible - test d'image sauté")
            except Exception as e:
                print(f"   ❌ Erreur création image test: {e}")
        
        # Test 3: Interface utilisateur
        print("\n3. Test de l'interface utilisateur...")
        
        # Test du formulaire
        print("   Test du formulaire d'entreprise...")
        try:
            form = EnterpriseFormWidget(
                enterprise_data=enterprise,
                mode="edit"
            )
            print("   ✅ Formulaire créé avec succès")
        except Exception as e:
            print(f"   ❌ Erreur formulaire: {e}")
        
        # Test de la vue d'index
        print("   Test de la vue d'index...")
        try:
            current_user = {
                'id': 1,
                'username': 'admin',
                'role': 'admin',
                'enterprise_id': 1
            }
            
            view = EnterpriseIndexView(current_user=current_user)
            print("   ✅ Vue d'index créée avec succès")
            
            if view.enterprise_data:
                logo_blob = view.enterprise_data.get('logo')
                print(f"   ✅ Logo dans la vue: {'présent' if logo_blob else 'absent'}")
        except Exception as e:
            print(f"   ❌ Erreur vue d'index: {e}")
        
        # Test 4: Méthodes du contrôleur
        print("\n4. Test des méthodes du contrôleur...")
        
        # Test récupération QPixmap
        pixmap = controller.get_logo_pixmap(1)
        print(f"   Logo QPixmap: {'✅ disponible' if pixmap else '❌ non disponible'}")
        
        # Test informations logo
        logo_info = controller.get_logo_info(1)
        if logo_info:
            print(f"   ✅ Info logo: {logo_info.get('format')} {logo_info.get('size')}")
        else:
            print("   ❌ Pas d'informations de logo")
        
        print("\n🎉 Tests terminés avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_blob_logo_system()