#!/usr/bin/env python3
"""
Test du sélecteur de devise (USD/FC) dans le formulaire d'entreprise
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication
from ayanna_erp.core.view.enterprise_form_widget import EnterpriseFormWidget

def test_currency_selector():
    """Tester le sélecteur de devise dans le formulaire"""
    print("🪙 Test du sélecteur de devise (USD/FC)")
    print("=" * 50)
    
    try:
        # Créer une application Qt
        app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
        
        # Créer le widget de formulaire
        form_widget = EnterpriseFormWidget()
        
        print("✅ Widget de formulaire créé avec succès")
        
        # Vérifier que le champ devise est un QComboBox
        currency_field = form_widget.currency_edit
        field_type = type(currency_field).__name__
        print(f"📊 Type du champ devise: {field_type}")
        
        if field_type == 'QComboBox':
            print("✅ Le champ devise est bien un QComboBox")
            
            # Vérifier les options disponibles
            options = []
            for i in range(currency_field.count()):
                options.append(currency_field.itemText(i))
            
            print(f"💰 Options disponibles: {options}")
            
            # Vérifier que seules USD et FC sont disponibles
            expected_options = ['USD', 'FC']
            if options == expected_options:
                print("✅ Options correctes : USD et FC uniquement")
            else:
                print(f"❌ Options incorrectes. Attendu: {expected_options}, Trouvé: {options}")
            
            # Vérifier la valeur par défaut
            current_value = currency_field.currentText()
            print(f"🎯 Valeur par défaut: {current_value}")
            
            if current_value == 'USD':
                print("✅ Valeur par défaut correcte (USD)")
            else:
                print(f"❌ Valeur par défaut incorrecte. Attendu: USD, Trouvé: {current_value}")
            
            # Test de changement de devise
            print("\n🔄 Test de changement de devise...")
            currency_field.setCurrentText('FC')
            new_value = currency_field.currentText()
            print(f"📝 Nouvelle valeur sélectionnée: {new_value}")
            
            if new_value == 'FC':
                print("✅ Changement vers FC réussi")
            else:
                print(f"❌ Échec du changement vers FC. Valeur: {new_value}")
            
            # Test de collecte des données
            print("\n📋 Test de collecte des données...")
            form_widget.name_edit.setText("Test Enterprise")
            form_widget.email_edit.setText("test@example.com")
            
            data = form_widget.collect_data()
            collected_currency = data.get('currency')
            print(f"💾 Devise collectée: {collected_currency}")
            
            if collected_currency == 'FC':
                print("✅ Collecte de données correcte")
            else:
                print(f"❌ Échec de collecte. Attendu: FC, Trouvé: {collected_currency}")
            
            # Test avec données d'entreprise existante
            print("\n🏢 Test avec données d'entreprise existante...")
            test_enterprise_data = {
                'name': 'Test Company',
                'currency': 'USD',
                'email': 'admin@testcompany.com'
            }
            
            form_widget.load_enterprise_data(test_enterprise_data)
            loaded_currency = form_widget.currency_edit.currentText()
            print(f"📥 Devise chargée: {loaded_currency}")
            
            if loaded_currency == 'USD':
                print("✅ Chargement des données existantes réussi")
            else:
                print(f"❌ Échec du chargement. Attendu: USD, Trouvé: {loaded_currency}")
            
            # Test avec devise non reconnue
            print("\n⚠️ Test avec devise non reconnue...")
            test_unknown_currency = {
                'name': 'Test Company 2',
                'currency': 'EUR',  # Devise non supportée
                'email': 'admin@testcompany2.com'
            }
            
            form_widget.load_enterprise_data(test_unknown_currency)
            fallback_currency = form_widget.currency_edit.currentText()
            print(f"🔄 Devise de fallback: {fallback_currency}")
            
            if fallback_currency == 'USD':
                print("✅ Fallback vers USD pour devise non reconnue réussi")
            else:
                print(f"❌ Échec du fallback. Attendu: USD, Trouvé: {fallback_currency}")
                
        else:
            print(f"❌ Le champ devise n'est pas un QComboBox mais un {field_type}")
            
        print("\n🎉 Test du sélecteur de devise terminé!")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_currency_selector()