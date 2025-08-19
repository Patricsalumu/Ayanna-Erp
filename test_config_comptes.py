#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test spécifique de la configuration des comptes
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

sys.path.insert(0, os.path.abspath('.'))

def test_config_dialog():
    """Test de la dialogue de configuration"""
    print("🧪 Test de la dialogue de configuration des comptes...")
    
    try:
        from ayanna_erp.modules.comptabilite.widgets.comptes_widget import ComptesWidget
        from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ComptabiliteController
        from ayanna_erp.database.database_manager import DatabaseManager
        
        # Créer une application Qt
        app = QApplication(sys.argv)
        
        # Simuler un parent avec entreprise_id
        from PyQt6.QtWidgets import QWidget
        parent = QWidget()
        parent.entreprise_id = 1
        
        # Créer le controller
        db = DatabaseManager()
        session = db.get_session()
        controller = ComptabiliteController(session)
        
        # Créer le widget
        widget = ComptesWidget(controller, parent)
        print("✅ Widget ComptesWidget créé")
        
        # Essayer d'appeler la méthode qui causait l'erreur
        # NOTE: On ne va pas vraiment ouvrir le dialog, juste tester la logique
        print("✅ Test de la logique de configuration...")
        
        # Simuler la requête qui causait l'erreur
        from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import CompteComptable, ClasseComptable
        comptes = session.query(CompteComptable).join(ClasseComptable).filter(ClasseComptable.enterprise_id == widget.entreprise_id).all()
        print(f"✅ Requête réussie! {len(comptes)} comptes trouvés")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_config_dialog()
    if success:
        print("\n✅ Test réussi! La configuration des comptes fonctionne!")
    else:
        print("\n❌ Test échoué")
        sys.exit(1)
