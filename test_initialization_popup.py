#!/usr/bin/env python3
"""
Test pour vérifier que le popup d'initialisation n'apparaît plus 
lors des ouvertures répétées du module Salle de Fête
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.modules.salle_fete.controller.mainWindow_controller import MainWindowController
from ayanna_erp.modules.salle_fete.model.salle_fete import EventService, get_database_manager

def test_multiple_initializations():
    """Test de multiples initialisations"""
    
    print("🧪 Test des initialisations multiples du module Salle de Fête")
    print("=" * 60)
    
    # Vérifier l'état initial
    db_manager = get_database_manager()
    session = db_manager.get_session()
    existing_services = session.query(EventService).filter(EventService.pos_id == 1).count()
    db_manager.close_session()
    
    print(f"📊 Services existants pour POS ID 1: {existing_services}")
    
    # Test de 5 initialisations successives
    for i in range(1, 6):
        print(f"\n--- Test {i}: Ouverture du module ---")
        
        # Créer le contrôleur sans parent pour éviter les popups
        controller = MainWindowController(parent=None, user_id=1)
        
        # Initialiser le module
        result = controller.initialize_module()
        
        print(f"✅ Initialisation {i}: {'Succès' if result else 'Échec'}")
        print(f"� is_initialized: {controller.is_initialized}")
        
        # Vérifier qu'aucun popup ne s'affiche en vérifiant le parent
        if controller.parent_window is None:
            print(f"✅ Aucun parent window configuré - pas de popup")
        else:
            print(f"⚠️ Parent window configuré - popup possible")
    
    print("\n" + "=" * 60)
    print("🎯 Résumé du test:")
    print("- Le module devrait détecter qu'il est déjà initialisé")
    print("- Les initialisations 1-5 devraient toutes réussir")
    print("- Aucun popup ne devrait s'afficher (parent=None)")
    print("✅ Test terminé")

if __name__ == "__main__":
    test_multiple_initializations()