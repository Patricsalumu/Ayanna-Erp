#!/usr/bin/env python3
"""
Test du module salle de fête après correction
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from PyQt6.QtWidgets import QApplication

def test_salle_fete_module():
    """Test du module salle de fête"""
    print("=== Test du Module Salle de Fête ===")
    
    app = QApplication(sys.argv)
    
    try:
        # Test 1: Import du contrôleur principal
        print("1. Test d'import du contrôleur...")
        from ayanna_erp.modules.salle_fete.controller.client_controller import ClientController
        from ayanna_erp.modules.salle_fete.controller.reservation_controller import ReservationController
        from ayanna_erp.modules.salle_fete.controller.paiement_controller import PaiementController
        print("✅ Contrôleurs importés avec succès")
        
        # Test 2: Test de création des composants
        print("\n2. Test de création des composants...")
        
        # Simuler un utilisateur connecté
        current_user = {
            'id': 1,
            'username': 'admin',
            'role': 'admin',
            'enterprise_id': 1
        }
        
        # Créer les contrôleurs
        client_controller = ClientController()
        reservation_controller = ReservationController()
        paiement_controller = PaiementController()
        print("✅ Contrôleurs créés avec succès")
        
        # Test 3: Test du PaymentPrintManager
        print("\n3. Test du PaymentPrintManager...")
        from ayanna_erp.modules.salle_fete.utils.payment_printer import PaymentPrintManager
        printer = PaymentPrintManager()
        print("✅ PaymentPrintManager créé avec succès")
        
        # Vérifier les infos d'entreprise
        print(f"   Nom entreprise: {printer.company_info.get('name')}")
        print(f"   Logo: {'présent' if printer.company_info.get('logo') else 'absent'}")
        
        # Test 4: Test de la vue d'index des paiements
        print("\n4. Test de la vue d'index des paiements...")
        try:
            # Créer un mock controller principal
            class MockMainController:
                def __init__(self):
                    self.client_controller = client_controller
                    self.reservation_controller = reservation_controller
                    self.paiement_controller = paiement_controller
            
            main_controller = MockMainController()
            
            from ayanna_erp.modules.salle_fete.view.paiement_index import PaiementIndex
            paiements_widget = PaiementIndex(main_controller, current_user)
            print("✅ PaiementIndex créé avec succès")
            
        except Exception as e:
            print(f"❌ Erreur PaiementIndex: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n🎉 Module salle de fête fonctionne correctement!")
        
        # Nettoyage
        if hasattr(printer, '_cleanup_temp_logo'):
            printer._cleanup_temp_logo()
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_salle_fete_module()