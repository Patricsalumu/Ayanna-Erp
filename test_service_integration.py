#!/usr/bin/env python3
"""
Script de vérification des fonctionnalités de l'interface Service
"""

import sys
import os

# Ajouter le chemin vers le module
sys.path.append(os.path.dirname(__file__))

from ayanna_erp.modules.salle_fete.controller.service_controller import ServiceController

def test_service_integration():
    """Test de l'intégration des statistiques"""
    
    print("🔧 Test d'intégration des statistiques Service")
    print("=" * 60)
    
    # Initialiser le contrôleur
    controller = ServiceController(pos_id=1)
    
    # Charger les services
    print("📋 Chargement des services...")
    services = controller.get_all_services(active_only=False)
    
    if not services:
        print("❌ Aucun service trouvé")
        return
    
    print(f"✅ {len(services)} service(s) chargé(s)")
    
    # Tester avec chaque service
    for i, service in enumerate(services[:3], 1):  # Limiter à 3 services pour le test
        print(f"\n📊 Service #{i}: {service.name}")
        print("-" * 40)
        
        # Test des statistiques
        stats = controller.get_service_usage_statistics(service.id)
        if stats:
            print(f"  ✅ Statistiques: {stats['total_uses']} utilisations, {stats['total_revenue']:.2f} € de revenus")
        else:
            print("  ❌ Erreur de statistiques")
        
        # Test des dernières utilisations
        recent = controller.get_service_recent_usage(service.id, limit=3)
        if recent is not None:
            print(f"  ✅ Dernières utilisations: {len(recent)} enregistrement(s)")
            for usage in recent[:2]:  # Afficher les 2 premières
                print(f"    - {usage['event_date']} - {usage['client_name']}")
        else:
            print("  ❌ Erreur des dernières utilisations")
    
    print(f"\n🎉 Test d'intégration terminé avec succès !")

if __name__ == "__main__":
    try:
        test_service_integration()
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()
