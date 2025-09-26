"""
Script de test pour vérifier l'intégration du module Boutique
"""

import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from ayanna_erp.ui.main_window import MainWindow
from ayanna_erp.database.database_manager import DatabaseManager


def test_boutique_integration():
    """Tester l'intégration du module Boutique avec le main_window"""
    
    app = QApplication(sys.argv)
    
    try:
        # Créer un utilisateur fictif pour le test
        class MockUser:
            def __init__(self):
                self.id = 1
                self.username = "admin"
                self.name = "Administrateur Test"
                self.role = "admin"
                self.email = "admin@ayanna.com"
                self.enterprise_id = 1
        
        current_user = MockUser()
        
        # Créer la fenêtre principale
        print("🚀 Lancement de la fenêtre principale...")
        main_window = MainWindow(current_user)
        main_window.show()
        
        # Afficher un message d'information
        QMessageBox.information(
            main_window,
            "Test d'Intégration Boutique",
            "🎉 Fenêtre principale lancée avec succès!\n\n"
            "Pour tester l'intégration du module Boutique :\n"
            "1. Cliquez sur le bouton 'Boutique' dans la grille\n"
            "2. Le module sera automatiquement enregistré\n"
            "3. Les données par défaut seront initialisées\n"
            "4. L'interface Boutique s'ouvrira\n\n"
            "Note: Au premier clic, l'initialisation peut prendre quelques secondes."
        )
        
        # Lancer l'application
        sys.exit(app.exec())
        
    except Exception as e:
        QMessageBox.critical(None, "Erreur", f"Erreur lors du test: {str(e)}")
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_boutique_integration()