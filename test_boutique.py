"""
Script de test pour le module Boutique
"""

import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from ayanna_erp.modules.boutique.view.boutique_window import BoutiqueWindow
from ayanna_erp.modules.boutique.init_boutique_data import initialize_boutique_data


def test_boutique_module():
    """Tester le module boutique"""
    
    app = QApplication(sys.argv)
    
    try:
        # Initialiser les données par défaut
        print("🚀 Initialisation des données de test...")
        initialize_boutique_data()
        
        # Créer un utilisateur fictif
        class MockUser:
            def __init__(self):
                self.id = 1
                self.username = "test"
                self.nom = "Admin"
                self.prenom = "Test"
        
        current_user = MockUser()
        
        # Créer la fenêtre boutique
        print("🏪 Lancement de l'interface boutique...")
        boutique_window = BoutiqueWindow(current_user, pos_id=1)
        boutique_window.show()
        
        # Afficher un message de bienvenue
        QMessageBox.information(
            boutique_window, 
            "Module Boutique", 
            "🎉 Module Boutique initialisé avec succès!\n\n"
            "Fonctionnalités disponibles:\n"
            "• 🛒 Panier avec catalogue produits/services\n"
            "• 📦 Gestion des produits\n"
            "• 📂 Gestion des catégories\n"
            "• 👥 Gestion des clients\n"
            "• 📊 Gestion du stock\n"
            "• 📈 Rapports de vente\n\n"
            "Testez les différents onglets!"
        )
        
        sys.exit(app.exec())
        
    except Exception as e:
        QMessageBox.critical(None, "Erreur", f"Erreur lors du lancement: {str(e)}")
        print(f"❌ Erreur: {e}")


if __name__ == "__main__":
    test_boutique_module()