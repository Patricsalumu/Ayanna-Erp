#!/usr/bin/env python3
"""
Script de test pour les formulaires Service et Produit avec objets SQLAlchemy
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

# Ajouter le chemin vers le module
sys.path.append(os.path.dirname(__file__))

from ayanna_erp.modules.salle_fete.view.service_form import ServiceForm
from ayanna_erp.modules.salle_fete.view.produit_form import ProduitForm
from ayanna_erp.modules.salle_fete.controller.service_controller import ServiceController
from ayanna_erp.modules.salle_fete.controller.produit_controller import ProduitController

def test_forms_with_objects():
    """Test des formulaires avec des objets SQLAlchemy"""
    
    print("🧪 Test des formulaires avec objets SQLAlchemy")
    print("=" * 60)
    
    # Créer l'application Qt
    app = QApplication(sys.argv)
    
    try:
        # Test du formulaire de service
        print("🏗️ Test du formulaire Service...")
        
        # Récupérer un service depuis la base
        service_controller = ServiceController()
        services = service_controller.get_all_services()
        
        if services:
            service = services[0]  # Premier service
            print(f"✅ Service récupéré: {service.name} (ID: {service.id})")
            
            # Créer le formulaire en mode édition
            service_form = ServiceForm(
                service_data=service, 
                controller=service_controller
            )
            print("✅ Formulaire Service créé avec succès en mode édition")
            
            # Tester l'affichage
            service_form.show()
            service_form.resize(500, 400)
            service_form.setWindowTitle("Test - Formulaire Service")
        else:
            print("❌ Aucun service trouvé pour le test")
        
        # Test du formulaire de produit
        print("\n🏗️ Test du formulaire Produit...")
        
        # Récupérer un produit depuis la base
        produit_controller = ProduitController()
        products = produit_controller.get_all_products()
        
        if products:
            product = products[0]  # Premier produit
            print(f"✅ Produit récupéré: {product.name} (ID: {product.id})")
            
            # Créer le formulaire en mode édition
            produit_form = ProduitForm(
                produit_data=product, 
                controller=produit_controller
            )
            print("✅ Formulaire Produit créé avec succès en mode édition")
            
            # Tester l'affichage
            produit_form.show()
            produit_form.resize(550, 500)
            produit_form.setWindowTitle("Test - Formulaire Produit")
        else:
            print("❌ Aucun produit trouvé pour le test")
        
        print("\n✅ Tests terminés avec succès !")
        print("🚀 Les formulaires sont ouverts - vous pouvez tester l'édition")
        
        # Lancer l'application
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_forms_with_objects()
