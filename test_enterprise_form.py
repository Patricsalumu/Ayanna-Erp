#!/usr/bin/env python3
"""
Test du nouveau formulaire d'entreprise
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from PyQt6.QtWidgets import QApplication
from ayanna_erp.core.view.enterprise_form_widget import EnterpriseFormWidget
from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController

def test_enterprise_form():
    """Test du formulaire d'entreprise"""
    print("=== Test du Formulaire d'Entreprise ===")
    
    app = QApplication(sys.argv)
    
    try:
        # Test 1: Récupérer l'entreprise existante
        controller = EntrepriseController()
        enterprise_data = controller.get_current_enterprise(1)
        
        if enterprise_data:
            print("Données d'entreprise trouvées:")
            print(f"- Nom: {enterprise_data.get('name')}")
            print(f"- Adresse: {enterprise_data.get('address')}")
            print(f"- Email: {enterprise_data.get('email')}")
            print(f"- Logo: {enterprise_data.get('logo')}")
            
            # Test 2: Ouvrir le formulaire d'édition
            print("\nOuverture du formulaire d'édition...")
            form = EnterpriseFormWidget(
                enterprise_data=enterprise_data,
                mode="edit"
            )
            
            # Vérifier que les champs sont bien remplis
            print(f"Nom dans le formulaire: {form.name_edit.text()}")
            print(f"Email dans le formulaire: {form.email_edit.text()}")
            
            print("\nFormulaire créé avec succès!")
            
        else:
            print("Aucune entreprise trouvée - Test du formulaire de création")
            form = EnterpriseFormWidget(mode="create")
            print("Formulaire de création créé avec succès!")
        
        print("\n✅ Test du formulaire réussi!")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enterprise_form()