#!/usr/bin/env python3
"""
Script de test pour les nouvelles fonctionnalités de statistiques des services
"""

import sys
import os

# Ajouter le chemin vers le module
sys.path.append(os.path.dirname(__file__))

from ayanna_erp.modules.salle_fete.controller.service_controller import ServiceController

def test_service_statistics():
    """Test les nouvelles méthodes de statistiques"""
    
    print("🧪 Test des statistiques d'utilisation des services")
    print("=" * 60)
    
    # Initialiser le contrôleur
    controller = ServiceController()
    
    # Récupérer la liste des services
    print("📋 Récupération des services disponibles...")
    services = controller.get_all_services()
    
    if not services:
        print("❌ Aucun service trouvé dans la base de données")
        return
    
    print(f"✅ {len(services)} service(s) trouvé(s)")
    
    # Tester avec le premier service
    service = services[0]
    service_id = service.id
    service_name = service.name
    
    print(f"\n🔍 Test avec le service: {service_name} (ID: {service_id})")
    print("-" * 40)
    
    # Test des statistiques d'utilisation
    print("📊 Test des statistiques d'utilisation...")
    stats = controller.get_service_usage_statistics(service_id)
    
    if stats is not None:
        print("✅ Statistiques récupérées avec succès:")
        print(f"  - Nombre total d'utilisations: {stats['total_uses']}")
        print(f"  - Quantité totale: {stats['total_quantity']}")
        print(f"  - Revenus totaux: {stats['total_revenue']:.2f} €")
        print(f"  - Quantité moyenne: {stats['average_quantity']}")
        print(f"  - Dernière utilisation: {stats['last_used']}")
    else:
        print("❌ Erreur lors de la récupération des statistiques")
    
    # Test des dernières utilisations
    print("\n📋 Test des dernières utilisations...")
    recent_usage = controller.get_service_recent_usage(service_id, limit=5)
    
    if recent_usage is not None:
        print(f"✅ {len(recent_usage)} utilisation(s) récente(s) récupérée(s):")
        for i, usage in enumerate(recent_usage, 1):
            print(f"  {i}. {usage['event_date']} - {usage['client_name']} "
                  f"(Qté: {usage['quantity']}, Total: {usage['total_line']:.2f} €)")
    else:
        print("❌ Erreur lors de la récupération des dernières utilisations")
    
    print("\n🎉 Test terminé!")

if __name__ == "__main__":
    try:
        test_service_statistics()
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()
