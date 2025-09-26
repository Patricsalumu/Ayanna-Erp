#!/usr/bin/env python3
"""
Script de test pour vérifier le fonctionnement du contrôleur d'entreprise dynamique
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController

def test_dynamic_enterprise_controller():
    """Test du contrôleur d'entreprise avec gestion dynamique"""
    
    print("=== Test du Contrôleur d'Entreprise Dynamique ===")
    
    # Créer une instance du contrôleur
    controller = EntrepriseController()
    
    # 1. Test de l'entreprise par défaut
    print("\n1. Test de l'entreprise active par défaut:")
    default_enterprise = controller.get_active_enterprise()
    print(f"   Entreprise active: ID {default_enterprise['id']} - {default_enterprise['name']}")
    
    # 2. Test du résumé du système
    print("\n2. Résumé du système:")
    summary = controller.get_enterprise_summary()
    print(f"   Entreprise active: {summary['active_enterprise_id']}")
    print(f"   Entreprises en cache: {summary['cached_enterprises']}")
    print(f"   Nombre d'entreprises en cache: {summary['cache_count']}")
    print(f"   Nom de l'entreprise active: {summary['active_enterprise_name']}")
    
    # 3. Test de récupération d'entreprise spécifique
    print("\n3. Test de récupération d'entreprise spécifique:")
    enterprise_1 = controller.get_current_enterprise(1)
    print(f"   Entreprise ID 1: {enterprise_1['name']}")
    
    # 4. Test de toutes les entreprises disponibles
    print("\n4. Test de toutes les entreprises:")
    all_enterprises = controller.get_all_enterprises()
    print(f"   Nombre total d'entreprises: {len(all_enterprises)}")
    for ent in all_enterprises:
        print(f"   - ID {ent['id']}: {ent['name']}")
    
    # 5. Test de changement d'entreprise active (si plusieurs existent)
    if len(all_enterprises) > 1:
        print(f"\n5. Test de changement d'entreprise active:")
        second_enterprise_id = all_enterprises[1]['id']
        success = controller.set_active_enterprise(second_enterprise_id)
        if success:
            print(f"   ✅ Entreprise active changée vers ID {second_enterprise_id}")
            active_enterprise = controller.get_active_enterprise()
            print(f"   Nouvelle entreprise active: {active_enterprise['name']}")
        else:
            print(f"   ❌ Échec du changement d'entreprise active")
    else:
        print("\n5. Test de changement d'entreprise active:")
        print("   ⚠️  Une seule entreprise disponible, pas de changement possible")
    
    # 6. Test du cache
    print("\n6. Test du cache:")
    summary_after = controller.get_enterprise_summary()
    print(f"   Entreprises en cache après tests: {summary_after['cached_enterprises']}")
    print(f"   Cache count: {summary_after['cache_count']}")
    
    # 7. Test de rafraîchissement du cache
    print("\n7. Test de rafraîchissement du cache:")
    controller.refresh_cache(1)
    summary_after_refresh = controller.get_enterprise_summary()
    print(f"   Entreprises en cache après refresh de l'ID 1: {summary_after_refresh['cached_enterprises']}")
    
    # 8. Test des méthodes de devise
    print("\n8. Test des méthodes de devise:")
    currency = controller.get_currency()
    currency_symbol = controller.get_currency_symbol()
    formatted_amount = controller.format_amount(1250.50)
    print(f"   Devise: {currency}")
    print(f"   Symbole: {currency_symbol}")
    print(f"   Montant formaté: {formatted_amount}")
    
    print("\n=== Tests terminés ===")

if __name__ == "__main__":
    try:
        test_dynamic_enterprise_controller()
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()