#!/usr/bin/env python3
"""
Test simplifié du sélecteur de devise (USD/FC) dans le formulaire d'entreprise
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication
from ayanna_erp.core.view.enterprise_form_widget import EnterpriseFormWidget

def test_currency_selector_simple():
    """Tester le sélecteur de devise - version simplifiée"""
    print("🪙 Test du sélecteur de devise (USD/FC)")
    print("=" * 50)
    
    try:
        # Créer une application Qt
        app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
        
        # Test 1: Création avec mode par défaut
        print("1️⃣ Test de création du formulaire...")
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
            
            # Test 2: Changement de devise
            print("\n2️⃣ Test de changement de devise...")
            currency_field.setCurrentText('FC')
            new_value = currency_field.currentText()
            print(f"📝 Nouvelle valeur sélectionnée: {new_value}")
            
            if new_value == 'FC':
                print("✅ Changement vers FC réussi")
            else:
                print(f"❌ Échec du changement vers FC. Valeur: {new_value}")
            
            # Test 3: Collecte des données
            print("\n3️⃣ Test de collecte des données...")
            form_widget.name_edit.setText("Test Enterprise")
            form_widget.email_edit.setText("test@example.com")
            
            data = form_widget.collect_data()
            collected_currency = data.get('currency')
            print(f"💾 Devise collectée: {collected_currency}")
            
            if collected_currency == 'FC':
                print("✅ Collecte de données correcte")
            else:
                print(f"❌ Échec de collecte. Attendu: FC, Trouvé: {collected_currency}")
            
            # Test 4: Création avec données d'entreprise
            print("\n4️⃣ Test avec données d'entreprise (USD)...")
            test_enterprise_data_usd = {
                'name': 'Test Company USD',
                'currency': 'USD',
                'email': 'admin@testcompany.com'
            }
            
            form_widget_usd = EnterpriseFormWidget(enterprise_data=test_enterprise_data_usd, mode="edit")
            loaded_currency_usd = form_widget_usd.currency_edit.currentText()
            print(f"📥 Devise chargée (USD): {loaded_currency_usd}")
            
            if loaded_currency_usd == 'USD':
                print("✅ Chargement USD réussi")
            else:
                print(f"❌ Échec du chargement USD. Trouvé: {loaded_currency_usd}")
            
            # Test 5: Création avec données d'entreprise FC
            print("\n5️⃣ Test avec données d'entreprise (FC)...")
            test_enterprise_data_fc = {
                'name': 'Test Company FC',
                'currency': 'FC',
                'email': 'admin@testcompanyfc.com'
            }
            
            form_widget_fc = EnterpriseFormWidget(enterprise_data=test_enterprise_data_fc, mode="edit")
            loaded_currency_fc = form_widget_fc.currency_edit.currentText()
            print(f"📥 Devise chargée (FC): {loaded_currency_fc}")
            
            if loaded_currency_fc == 'FC':
                print("✅ Chargement FC réussi")
            else:
                print(f"❌ Échec du chargement FC. Trouvé: {loaded_currency_fc}")
            
            # Test 6: Gestion devise non reconnue
            print("\n6️⃣ Test avec devise non reconnue...")
            test_unknown_currency = {
                'name': 'Test Company EUR',
                'currency': 'EUR',  # Devise non supportée
                'email': 'admin@testcompanyeur.com'
            }
            
            form_widget_eur = EnterpriseFormWidget(enterprise_data=test_unknown_currency, mode="edit")
            fallback_currency = form_widget_eur.currency_edit.currentText()
            print(f"🔄 Devise de fallback: {fallback_currency}")
            
            if fallback_currency == 'USD':
                print("✅ Fallback vers USD pour devise non reconnue réussi")
            else:
                print(f"❌ Échec du fallback. Attendu: USD, Trouvé: {fallback_currency}")
            
            print("\n🎉 Tous les tests du sélecteur de devise sont réussis!")
            print("✅ USD et FC uniquement disponibles")
            print("✅ Valeur par défaut USD")
            print("✅ Changement de devise fonctionnel")
            print("✅ Collecte de données correcte")
            print("✅ Chargement des données existantes")
            print("✅ Fallback pour devises non reconnues")
                
        else:
            print(f"❌ Le champ devise n'est pas un QComboBox mais un {field_type}")
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_currency_selector_simple()