#!/usr/bin/env python3
"""
Test de l'en-tête d'entreprise sur les reçus de vente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.boutique.controller.boutique_controller import BoutiqueController
from ayanna_erp.modules.boutique.view.modern_supermarket_widget import ModernSupermarketWidget
from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController

def test_enterprise_header():
    """Test de l'en-tête d'entreprise"""
    
    app = QApplication(sys.argv)
    
    try:
        # Initialisation des contrôleurs
        db_manager = DatabaseManager()
        boutique_controller = BoutiqueController()
        enterprise_controller = EntrepriseController()
        
        print("=== Test En-tête Entreprise ===")
        
        # Test 1: Vérification des informations d'entreprise
        enterprise_info = enterprise_controller.get_current_enterprise()
        print(f"\n📋 Informations entreprise:")
        print(f"   Nom: {enterprise_info['name']}")
        print(f"   Adresse: {enterprise_info['address']}")
        print(f"   Téléphone: {enterprise_info['phone']}")
        print(f"   Email: {enterprise_info['email']}")
        print(f"   RCCM: {enterprise_info['rccm']}")
        
        # Test 2: Vérification du widget modernisé
        class TestUser:
            def __init__(self):
                self.name = "Testeur Admin"
                self.id = 1
        
        current_user = TestUser()
        widget = ModernSupermarketWidget(boutique_controller, current_user, pos_id=1)
        
        print(f"\n✅ Widget créé avec EntrepriseController intégré")
        print(f"   Controller disponible: {widget.enterprise_controller is not None}")
        
        # Test 3: Simulation d'un reçu avec en-tête
        print(f"\n🧪 Test simulation reçu...")
        
        # Données de test pour le reçu
        from datetime import datetime
        from decimal import Decimal
        
        sale_data = {
            'sale_date': datetime.now(),
            'subtotal': Decimal('15000'),
            'discount_amount': Decimal('1500'),
            'total_amount': Decimal('13500')
        }
        
        payment_data = {
            'method': 'Espèces',
            'amount_received': Decimal('15000'),
            'change': Decimal('1500')
        }
        
        # Ajouter quelques articles au panier pour le test
        widget.current_cart = [
            {
                'product_name': 'Coca-Cola 1.5L',
                'quantity': 2,
                'unit_price': Decimal('3000')
            },
            {
                'product_name': 'Pain de blé',
                'quantity': 3,
                'unit_price': Decimal('3000')
            }
        ]
        
        print(f"   Panier test créé: {len(widget.current_cart)} articles")
        
        # Afficher le widget pour le test visuel
        widget.show()
        
        print(f"\n✅ Interface affichée avec succès")
        print(f"💡 Testez une vente pour voir le reçu avec en-tête d'entreprise")
        print(f"📋 Format attendu:")
        print(f"   - En-tête avec nom de l'entreprise")
        print(f"   - Adresse, téléphone, email")
        print(f"   - RCCM de l'entreprise")
        print(f"   - Signature 'Généré par Ayanna ERP'")
        
        # Lancer l'application
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_enterprise_header()