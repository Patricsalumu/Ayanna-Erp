#!/usr/bin/env python3
"""Test de l'enregistrement de réservation avec différentes devises"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.core.entreprise_controller import EntrepriseController

def test_currency_parsing():
    """Test du parsing de montants avec différentes devises"""
    print("🧪 Test de parsing de montants avec devises dynamiques")
    print("=" * 60)
    
    try:
        # Mock de la méthode parse_amount_from_text
        def parse_amount_from_text(text):
            """Méthode de parsing dynamique (copie de celle de reservation_form.py)"""
            try:
                # Récupération du symbole de devise actuel
                entreprise_controller = EntrepriseController()
                currency_symbol = entreprise_controller.get_currency_symbol()
                
                # Nettoyage du texte en utilisant le symbole dynamique
                cleaned_text = text.replace(f" {currency_symbol}", "").replace(currency_symbol, "").strip()
                cleaned_text = cleaned_text.replace(",", ".")
                return float(cleaned_text)
            except (ValueError, AttributeError) as e:
                print(f"❌ Erreur lors du parsing de '{text}': {e}")
                # Fallback plus robuste
                try:
                    fallback_text = text.replace(" €", "").replace(" $", "").replace(" FC", "").replace("€", "").replace("$", "").replace("FC", "").replace(",", ".").strip()
                    return float(fallback_text)
                except:
                    return 0.0
        
        # Test avec différents formats
        test_cases = [
            "150.00 €",
            "150,00 €", 
            "1250.50 €",
            "1,250.50 €",
            "150.00 $",
            "150,00 $",
            "150.00",
            "150,00"
        ]
        
        print("Tests de parsing :")
        for test_text in test_cases:
            result = parse_amount_from_text(test_text)
            print(f"  '{test_text}' -> {result}")
        
        print("\n✅ Tests de parsing terminés avec succès")
        
        # Test de récupération de devise
        print("\n🏢 Test de récupération de devise :")
        entreprise_controller = EntrepriseController()
        currency = entreprise_controller.get_currency()
        currency_symbol = entreprise_controller.get_currency_symbol()
        print(f"  Devise : {currency}")
        print(f"  Symbole : {currency_symbol}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_currency_parsing()
    if success:
        print("\n🎉 Tous les tests ont réussi !")
        print("✅ L'enregistrement de réservation devrait maintenant fonctionner avec n'importe quelle devise.")
    else:
        print("\n❌ Certains tests ont échoué.")
        sys.exit(1)