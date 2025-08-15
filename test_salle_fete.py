"""
Script de test pour la nouvelle structure modulaire du module Salle de Fête
"""

import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from PyQt6.QtWidgets import QApplication, QMessageBox
from ayanna_erp.modules.salle_fete.view.salle_fete_window import SalleFeteWindow

def test_salle_fete_module():
    """Tester le module Salle de Fête avec la nouvelle structure"""
    
    # Créer l'application Qt
    app = QApplication(sys.argv)
    
    try:
        # Simuler un utilisateur connecté
        current_user = {
            'id': 1,
            'nom': 'Administrateur',
            'email': 'admin@ayanna.com'
        }
        
        # Créer la fenêtre principale
        window = SalleFeteWindow(current_user)
        window.show()
        
        print("✅ Module Salle de Fête chargé avec succès !")
        print("📋 Onglets disponibles :")
        
        # Lister tous les onglets
        for i in range(window.tab_widget.count()):
            tab_text = window.tab_widget.tabText(i)
            print(f"   - {tab_text}")
        
        # Afficher un message de succès
        QMessageBox.information(
            window,
            "Test réussi !",
            "La nouvelle structure modulaire du module Salle de Fête fonctionne correctement !\n\n"
            "Chaque onglet est maintenant dans son propre fichier :\n"
            "• calendrier_index.py\n"
            "• reservation_index.py\n"
            "• client_index.py\n"
            "• service_index.py\n"
            "• produit_index.py\n"
            "• entreSortie_index.py\n"
            "• paiement_index.py\n"
            "• rapport_index.py\n\n"
            "Les formulaires modaux sont séparés :\n"
            "• reservation_form.py\n"
            "• client_form.py\n"
            "• etc.\n\n"
            "Vous pouvez maintenant tester les fonctionnalités !"
        )
        
        # Lancer l'application
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ Erreur lors du chargement : {e}")
        QMessageBox.critical(
            None,
            "Erreur",
            f"Erreur lors du chargement du module :\n{str(e)}"
        )
        sys.exit(1)

if __name__ == "__main__":
    test_salle_fete_module()
