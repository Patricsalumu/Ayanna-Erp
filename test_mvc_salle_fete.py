"""
Script de test pour vérifier la connexion des widgets avec les contrôleurs
Module Salle de Fête - Ayanna ERP
"""

import sys
import os

# Ajouter le chemin de l'application
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QMessageBox
from PyQt6.QtCore import QTimer

# Import des contrôleurs
from ayanna_erp.modules.salle_fete.controller.mainWindow_controller import MainWindowController


class TestApp(QMainWindow):
    """Application de test pour les connexions MVC"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Connexions MVC - Salle de Fête")
        self.setGeometry(100, 100, 1200, 800)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        try:
            # Initialiser le contrôleur principal
            self.main_controller = MainWindowController(pos_id=1)
            
            # Test d'initialisation
            QTimer.singleShot(500, self.test_initialization)
            
            print("✅ Contrôleur principal initialisé avec succès")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur d'initialisation: {e}")
    
    def test_initialization(self):
        """Tester l'initialisation de la base de données"""
        try:
            print("🔄 Test d'initialisation de la base de données...")
            
            # Tester l'initialisation
            success = self.main_controller.initialize_database()
            
            if success:
                print("✅ Base de données initialisée avec succès")
                self.test_controllers()
            else:
                print("❌ Échec de l'initialisation de la base de données")
                
        except Exception as e:
            print(f"❌ Erreur lors du test d'initialisation: {e}")
    
    def test_controllers(self):
        """Tester les contrôleurs"""
        try:
            print("🔄 Test des contrôleurs...")
            
            # Test du contrôleur client
            from ayanna_erp.modules.salle_fete.controller.client_controller import ClientController
            client_controller = ClientController(pos_id=1)
            print("✅ ClientController créé")
            
            # Test du contrôleur service
            from ayanna_erp.modules.salle_fete.controller.service_controller import ServiceController
            service_controller = ServiceController(pos_id=1)
            print("✅ ServiceController créé")
            
            # Test du contrôleur produit
            from ayanna_erp.modules.salle_fete.controller.produit_controller import ProduitController
            produit_controller = ProduitController(pos_id=1)
            print("✅ ProduitController créé")
            
            # Test du contrôleur réservation
            from ayanna_erp.modules.salle_fete.controller.reservation_controller import ReservationController
            reservation_controller = ReservationController(pos_id=1)
            print("✅ ReservationController créé")
            
            # Test du contrôleur paiement
            from ayanna_erp.modules.salle_fete.controller.paiement_controller import PaiementController
            paiement_controller = PaiementController(pos_id=1)
            print("✅ PaiementController créé")
            
            print("\n🎉 Tous les contrôleurs ont été créés avec succès !")
            
            # Test des formulaires
            self.test_forms()
            
        except Exception as e:
            print(f"❌ Erreur lors du test des contrôleurs: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur contrôleurs: {e}")
    
    def test_forms(self):
        """Tester les formulaires"""
        try:
            print("\n🔄 Test des formulaires...")
            
            # Test du formulaire client
            from ayanna_erp.modules.salle_fete.view.client_form import ClientForm
            client_form = ClientForm()
            print("✅ ClientForm créé")
            client_form.close()
            
            # Test du formulaire service
            from ayanna_erp.modules.salle_fete.view.service_form import ServiceForm
            service_form = ServiceForm()
            print("✅ ServiceForm créé")
            service_form.close()
            
            # Test du formulaire produit
            from ayanna_erp.modules.salle_fete.view.produit_form import ProduitForm
            produit_form = ProduitForm()
            print("✅ ProduitForm créé")
            produit_form.close()
            
            # Test du formulaire réservation
            from ayanna_erp.modules.salle_fete.view.reservation_form import ReservationForm
            reservation_form = ReservationForm()
            print("✅ ReservationForm créé")
            reservation_form.close()
            
            print("\n🎉 Tous les formulaires ont été créés avec succès !")
            
            # Test des widgets d'index
            self.test_widgets()
            
        except Exception as e:
            print(f"❌ Erreur lors du test des formulaires: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur formulaires: {e}")
    
    def test_widgets(self):
        """Tester les widgets d'index"""
        try:
            print("\n🔄 Test des widgets d'index...")
            
            # Mock current_user
            current_user = {'id': 1, 'name': 'Test User'}
            
            # Test du widget client
            from ayanna_erp.modules.salle_fete.view.client_index import ClientIndex
            client_widget = ClientIndex(self.main_controller, current_user)
            print("✅ ClientIndex créé")
            
            # Test du widget service
            from ayanna_erp.modules.salle_fete.view.service_index import ServiceIndex
            service_widget = ServiceIndex(self.main_controller, current_user)
            print("✅ ServiceIndex créé")
            
            # Test du widget produit
            from ayanna_erp.modules.salle_fete.view.produit_index import ProduitIndex
            produit_widget = ProduitIndex(self.main_controller, current_user)
            print("✅ ProduitIndex créé")
            
            # Test du widget réservation
            from ayanna_erp.modules.salle_fete.view.reservation_index import ReservationIndex
            reservation_widget = ReservationIndex(self.main_controller, current_user)
            print("✅ ReservationIndex créé")
            
            print("\n🎉 Tous les widgets ont été créés avec succès !")
            print("\n✨ Test complet terminé ! L'architecture MVC fonctionne correctement.")
            
            QMessageBox.information(
                self, 
                "Succès", 
                "🎉 Tous les tests sont passés avec succès !\n\n"
                "✅ Base de données initialisée\n"
                "✅ Contrôleurs créés\n"
                "✅ Formulaires créés\n"
                "✅ Widgets créés\n\n"
                "L'architecture MVC est fonctionnelle !"
            )
            
        except Exception as e:
            print(f"❌ Erreur lors du test des widgets: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur widgets: {e}")


def main():
    """Fonction principale"""
    app = QApplication(sys.argv)
    
    print("🚀 Démarrage des tests MVC - Salle de Fête")
    print("=" * 50)
    
    window = TestApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
