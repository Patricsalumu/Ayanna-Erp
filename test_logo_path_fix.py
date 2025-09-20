#!/usr/bin/env python3
"""
Test de correction de l'erreur logo_path
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

try:
    from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
    
    print("=== Test de Correction de l'Erreur logo_path ===")
    
    # Test 1: get_company_info_for_pdf
    print("1. Test de get_company_info_for_pdf...")
    controller = EntrepriseController()
    
    try:
        company_info = controller.get_company_info_for_pdf()
        print("✅ get_company_info_for_pdf fonctionne")
        print(f"   Clés disponibles: {list(company_info.keys())}")
        print(f"   Logo: {'présent' if company_info.get('logo') else 'absent'}")
    except Exception as e:
        print(f"❌ Erreur get_company_info_for_pdf: {e}")
    
    # Test 2: get_current_enterprise
    print("\n2. Test de get_current_enterprise...")
    try:
        enterprise = controller.get_current_enterprise(1)
        print("✅ get_current_enterprise fonctionne")
        print(f"   Clés disponibles: {list(enterprise.keys())}")
        print(f"   Logo: {'présent' if enterprise.get('logo') else 'absent'}")
        
        # Vérifier qu'il n'y a pas de logo_path
        if 'logo_path' in enterprise:
            print("⚠️  Attention: 'logo_path' encore présent!")
        else:
            print("✅ 'logo_path' correctement supprimé")
            
    except Exception as e:
        print(f"❌ Erreur get_current_enterprise: {e}")
    
    # Test 3: Payment printer (import seulement)
    print("\n3. Test d'import du Payment Printer...")
    try:
        from ayanna_erp.modules.salle_fete.utils.payment_printer import PaymentPrintManager
        printer = PaymentPrintManager()
        print("✅ PaymentPrintManager créé avec succès")
        print(f"   Logo dans company_info: {'présent' if printer.company_info.get('logo') else 'absent'}")
        
        # Nettoyage
        if hasattr(printer, '_cleanup_temp_logo'):
            printer._cleanup_temp_logo()
            
    except Exception as e:
        print(f"❌ Erreur PaymentPrintManager: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎉 Tests de correction terminés!")
    
except Exception as e:
    print(f"❌ Erreur générale: {e}")
    import traceback
    traceback.print_exc()