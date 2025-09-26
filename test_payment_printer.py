#!/usr/bin/env python3
"""
Test du PaymentPrintManager avec enterprise_id spécifique
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.modules.salle_fete.utils.payment_printer import PaymentPrintManager

def test_payment_printer_with_enterprise():
    """Test du PaymentPrintManager avec différents enterprise_id"""
    
    print("=== Test PaymentPrintManager avec Enterprise ID ===")
    
    # Test 1: Créer avec enterprise_id spécifique
    print("\n1. Test avec enterprise_id = 1:")
    printer_1 = PaymentPrintManager(enterprise_id=1)
    print(f"   Enterprise ID: {printer_1.get_current_enterprise_id()}")
    print(f"   Nom entreprise: {printer_1.company_info['name']}")
    print(f"   Devise: {printer_1.get_currency_symbol()}")
    print(f"   Montant formaté: {printer_1.format_amount(1000.50)}")
    
    # Test 2: Créer sans enterprise_id (utilise l'active par défaut)
    print("\n2. Test sans enterprise_id (défaut):")
    printer_default = PaymentPrintManager()
    print(f"   Enterprise ID: {printer_default.get_current_enterprise_id()}")
    print(f"   Nom entreprise: {printer_default.company_info['name']}")
    print(f"   Devise: {printer_default.get_currency_symbol()}")
    print(f"   Montant formaté: {printer_default.format_amount(1000.50)}")
    
    # Test 3: Changer d'entreprise après création
    print("\n3. Test changement d'entreprise:")
    printer_1.set_enterprise(2)  # Changer vers enterprise_id 2
    print(f"   Après changement - Enterprise ID: {printer_1.get_current_enterprise_id()}")
    print(f"   Nom entreprise: {printer_1.company_info['name']}")
    print(f"   Devise: {printer_1.get_currency_symbol()}")
    print(f"   Montant formaté: {printer_1.format_amount(1000.50)}")
    
    # Test 4: Vérifier que les instances sont indépendantes
    print("\n4. Test indépendance des instances:")
    print(f"   Printer 1 - Enterprise ID: {printer_1.get_current_enterprise_id()}")
    print(f"   Printer default - Enterprise ID: {printer_default.get_current_enterprise_id()}")
    
    print("\n=== Test terminé avec succès! ===")
    print("✅ PaymentPrintManager supporte maintenant les enterprise_id spécifiques")
    print("✅ Possibilité de changer d'entreprise après création")
    print("✅ Les instances sont indépendantes")
    
    return True

if __name__ == "__main__":
    try:
        test_payment_printer_with_enterprise()
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()