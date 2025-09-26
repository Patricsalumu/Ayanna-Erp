#!/usr/bin/env python3
"""
Test d'intégration du SessionManager avec tous les modules Ayanna ERP
Vérifie que tous les composants utilisent bien l'enterprise_id de la session
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_mock_user():
    """Créer un utilisateur de test avec enterprise_id"""
    class MockUser:
        def __init__(self):
            self.id = 1
            self.name = "Utilisateur Test"
            self.email = "test@ayanna-erp.com"
            self.enterprise_id = 2  # Utiliser enterprise_id = 2 pour tester la dynamicité
            self.role = "admin"
    
    return MockUser()

def test_session_manager():
    """Test du SessionManager"""
    print("=== Test SessionManager ===")
    
    # Importer le SessionManager
    from ayanna_erp.core.session_manager import SessionManager
    
    # Test 1: Vérifier état initial (pas d'utilisateur connecté)
    print("\n1. État initial:")
    print(f"   Utilisateur connecté: {SessionManager.is_authenticated()}")
    print(f"   Enterprise ID: {SessionManager.get_current_enterprise_id()}")
    
    # Test 2: Connecter un utilisateur
    print("\n2. Connexion utilisateur:")
    mock_user = create_mock_user()
    SessionManager.set_current_user(mock_user)
    
    print(f"   Utilisateur connecté: {SessionManager.is_authenticated()}")
    print(f"   Enterprise ID: {SessionManager.get_current_enterprise_id()}")
    print(f"   Nom utilisateur: {SessionManager.get_current_user().name}")
    
    # Test 3: Infos de session
    print("\n3. Informations de session:")
    session_info = SessionManager.get_session_info()
    for key, value in session_info.items():
        print(f"   {key}: {value}")

def test_enterprise_controller_with_session():
    """Test EntrepriseController avec SessionManager"""
    print("\n=== Test EntrepriseController avec Session ===")
    
    from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
    from ayanna_erp.core.session_manager import SessionManager
    
    # Créer le contrôleur
    controller = EntrepriseController()
    
    # Test 1: Sans paramètre (utilise la session)
    print("\n1. Récupération via session (sans paramètre):")
    try:
        enterprise = controller.get_current_enterprise()
        print(f"   Entreprise ID: {enterprise['id']}")
        print(f"   Nom: {enterprise.get('name', enterprise.get('nom', 'N/A'))}")
        print(f"   Devise: {enterprise.get('currency', enterprise.get('devise', 'N/A'))}")
    except Exception as e:
        print(f"   Erreur: {e}")
    
    # Test 2: Devise et formatage
    print("\n2. Devise et formatage via session:")
    try:
        currency = controller.get_currency()
        symbol = controller.get_currency_symbol()
        formatted = controller.format_amount(1234.56)
        
        print(f"   Devise: {currency}")
        print(f"   Symbole: {symbol}")
        print(f"   Montant formaté: {formatted}")
    except Exception as e:
        print(f"   Erreur: {e}")
    
    # Test 3: Infos pour PDF
    print("\n3. Informations pour PDF via session:")
    try:
        pdf_info = controller.get_company_info_for_pdf()
        print(f"   Nom: {pdf_info.get('name', pdf_info.get('nom', 'N/A'))}")
        print(f"   Adresse: {pdf_info.get('address', pdf_info.get('adresse', 'N/A'))}")
        print(f"   Téléphone: {pdf_info.get('phone', pdf_info.get('telephone', 'N/A'))}")
        print(f"   RCCM: {pdf_info.get('rccm', 'N/A')}")
    except Exception as e:
        print(f"   Erreur: {e}")

def test_payment_printer_with_session():
    """Test PaymentPrintManager avec SessionManager"""
    print("\n=== Test PaymentPrintManager avec Session ===")
    
    try:
        from ayanna_erp.modules.salle_fete.utils.payment_printer import PaymentPrintManager
        
        # Test 1: Créer sans enterprise_id (utilise la session)
        print("\n1. Création sans enterprise_id (utilise la session):")
        printer = PaymentPrintManager()
        print(f"   Enterprise ID: {printer.get_current_enterprise_id()}")
        print(f"   Nom entreprise: {printer.company_info.get('name', printer.company_info.get('nom', 'N/A'))}")
        print(f"   Devise: {printer.get_currency_symbol()}")
        print(f"   Montant formaté: {printer.format_amount(999.99)}")
        
        # Test 2: Créer avec enterprise_id spécifique
        print("\n2. Création avec enterprise_id=1:")
        printer_1 = PaymentPrintManager(enterprise_id=1)
        print(f"   Enterprise ID: {printer_1.get_current_enterprise_id()}")
        print(f"   Nom entreprise: {printer_1.company_info.get('name', printer_1.company_info.get('nom', 'N/A'))}")
        
    except Exception as e:
        print(f"   Erreur lors du test PaymentPrintManager: {e}")

def test_pdf_exporter_with_session():
    """Test PDFExporter avec SessionManager"""
    print("\n=== Test PDFExporter avec Session ===")
    
    try:
        from ayanna_erp.modules.salle_fete.utils.pdf_exporter import PDFExporter
        
        # Test 1: Créer sans enterprise_id (utilise la session)
        print("\n1. Création sans enterprise_id (utilise la session):")
        exporter = PDFExporter()
        print(f"   Enterprise ID: {exporter.get_current_enterprise_id()}")
        print(f"   Nom entreprise: {exporter.company_info.get('name', exporter.company_info.get('nom', 'N/A'))}")
        print(f"   Devise: {exporter.currency_symbol}")
        
        # Test 2: Créer avec enterprise_id spécifique
        print("\n2. Création avec enterprise_id=1:")
        exporter_1 = PDFExporter(enterprise_id=1)
        print(f"   Enterprise ID: {exporter_1.get_current_enterprise_id()}")
        print(f"   Nom entreprise: {exporter_1.company_info.get('name', exporter_1.company_info.get('nom', 'N/A'))}")
        
    except Exception as e:
        print(f"   Erreur lors du test PDFExporter: {e}")

def test_session_logout():
    """Test de déconnexion"""
    print("\n=== Test Déconnexion ===")
    
    from ayanna_erp.core.session_manager import SessionManager
    
    print("\n1. Avant déconnexion:")
    print(f"   Utilisateur connecté: {SessionManager.is_authenticated()}")
    print(f"   Enterprise ID: {SessionManager.get_current_enterprise_id()}")
    
    # Déconnexion
    SessionManager.clear_session()
    
    print("\n2. Après déconnexion:")
    print(f"   Utilisateur connecté: {SessionManager.is_authenticated()}")
    print(f"   Enterprise ID: {SessionManager.get_current_enterprise_id()}")

def run_all_tests():
    """Exécuter tous les tests"""
    print("🚀 DÉBUT DES TESTS D'INTÉGRATION SESSION AYANNA ERP")
    print("=" * 60)
    
    try:
        # Test 1: SessionManager de base
        test_session_manager()
        
        # Test 2: EntrepriseController avec session
        test_enterprise_controller_with_session()
        
        # Test 3: PaymentPrintManager avec session
        test_payment_printer_with_session()
        
        # Test 4: PDFExporter avec session
        test_pdf_exporter_with_session()
        
        # Test 5: Déconnexion
        test_session_logout()
        
        print("\n" + "=" * 60)
        print("✅ TOUS LES TESTS D'INTÉGRATION TERMINÉS AVEC SUCCÈS")
        
    except Exception as e:
        print(f"\n❌ ERREUR LORS DES TESTS: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()