"""
Test de validation de la récupération de l'enterprise_id de l'utilisateur connecté
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from ayanna_erp.core.session_manager import SessionManager
from ayanna_erp.modules.boutique.controller.boutique_controller import BoutiqueController
from ayanna_erp.modules.achats.controllers.achat_controller import AchatController
from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController

def test_enterprise_id_resolution():
    """Test de résolution de l'enterprise_id depuis l'utilisateur connecté"""
    
    print("🧪 Test récupération enterprise_id utilisateur connecté")
    print("=" * 60)
    
    # Simuler un utilisateur connecté
    test_user = type('User', (), {
        'id': 1,
        'name': 'Test User',
        'email': 'test@example.com',
        'role': 'admin',
        'enterprise_id': 5  # Entreprise différente de 1
    })()
    
    print(f"👤 Simulation utilisateur connecté:")
    print(f"   - Nom: {test_user.name}")
    print(f"   - ID Entreprise: {test_user.enterprise_id}")
    
    # Connecter l'utilisateur
    SessionManager.set_current_user(test_user)
    
    # Vérifier que le SessionManager retourne bien l'enterprise_id
    enterprise_id_from_session = SessionManager.get_current_enterprise_id()
    print(f"\n📊 Enterprise ID depuis SessionManager: {enterprise_id_from_session}")
    
    # Test du contrôleur boutique
    print("\n🛒 Test BoutiqueController:")
    boutique_controller = BoutiqueController(pos_id=2)
    print(f"   - Enterprise ID récupéré: {boutique_controller.entreprise_id}")
    expected_id = test_user.enterprise_id
    if boutique_controller.entreprise_id == expected_id:
        print(f"   ✅ Correct! Enterprise ID = {expected_id}")
    else:
        print(f"   ❌ Erreur! Attendu: {expected_id}, Obtenu: {boutique_controller.entreprise_id}")
    
    # Test du contrôleur d'achats
    print("\n💰 Test AchatController:")
    achat_controller = AchatController(pos_id=2)
    print(f"   - Enterprise ID récupéré: {achat_controller.entreprise_id}")
    if achat_controller.entreprise_id == expected_id:
        print(f"   ✅ Correct! Enterprise ID = {expected_id}")
    else:
        print(f"   ❌ Erreur! Attendu: {expected_id}, Obtenu: {achat_controller.entreprise_id}")
    
    # Test du contrôleur d'entreprise
    print("\n🏢 Test EntrepriseController:")
    entreprise_controller = EntrepriseController()
    enterprise_data = entreprise_controller.get_current_enterprise()
    print(f"   - Enterprise recherchée: ID {expected_id}")
    print(f"   - Enterprise trouvée: {enterprise_data.get('name', 'N/A')} (ID: {enterprise_data.get('id', 'N/A')})")
    
    # Test avec aucun utilisateur connecté
    print("\n🚫 Test sans utilisateur connecté:")
    SessionManager.clear_session()
    
    boutique_controller_no_user = BoutiqueController(pos_id=2)
    print(f"   - BoutiqueController fallback: {boutique_controller_no_user.entreprise_id}")
    
    achat_controller_no_user = AchatController(pos_id=2)
    print(f"   - AchatController fallback: {achat_controller_no_user.entreprise_id}")
    
    if (boutique_controller_no_user.entreprise_id == 1 and 
        achat_controller_no_user.entreprise_id == 1):
        print("   ✅ Fallback correct vers enterprise_id = 1")
    else:
        print("   ❌ Problème de fallback")
    
    print("\n✅ Test terminé")
    return True

if __name__ == "__main__":
    success = test_enterprise_id_resolution()
    sys.exit(0 if success else 1)