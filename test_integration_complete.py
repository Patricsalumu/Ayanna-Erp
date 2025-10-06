"""
Test d'intégration complète de l'architecture modulaire du stock
Ce script teste l'intégration dans la fenêtre principale de l'application
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QMessageBox, QPushButton, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Ajouter le chemin racine au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import DatabaseManager


class IntegrationTestWindow(QMainWindow):
    """Fenêtre de test d'intégration complète"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧪 Test Intégration Architecture Modulaire Stock")
        self.setGeometry(50, 50, 800, 600)
        
        # Utilisateur de test
        self.current_user = {"id": 1, "name": "Test User", "username": "testuser"}
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configuration de l'interface de test"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Titre
        title = QLabel("🧪 Test d'Intégration - Architecture Modulaire Stock")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2980b9);
                color: white;
                padding: 15px;
                border-radius: 10px;
                margin: 10px;
            }
        """)
        layout.addWidget(title)
        
        # Informations sur les tests
        info_label = QLabel("""
🎯 Tests disponibles:

1. Test du StockWindow (fenêtre principale)
2. Test de l'architecture modulaire complète  
3. Test des widgets individuels
4. Test des contrôleurs

⚠️ Assurez-vous que la base de données est accessible.
        """)
        info_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
                margin: 10px;
                font-size: 12px;
            }
        """)
        layout.addWidget(info_label)
        
        # Boutons de test
        
        # 1. Test StockWindow
        stock_window_btn = QPushButton("🏭 Tester StockWindow (Fenêtre Principale)")
        stock_window_btn.setStyleSheet(self.get_button_style("#3498db"))
        stock_window_btn.clicked.connect(self.test_stock_window)
        layout.addWidget(stock_window_btn)
        
        # 2. Test Widget Modulaire seul
        modular_widget_btn = QPushButton("🔧 Tester Widget Modulaire Seul")
        modular_widget_btn.setStyleSheet(self.get_button_style("#27ae60"))
        modular_widget_btn.clicked.connect(self.test_modular_widget)
        layout.addWidget(modular_widget_btn)
        
        # 3. Test widgets individuels
        individual_widgets_btn = QPushButton("📦 Tester Widgets Individuels")
        individual_widgets_btn.setStyleSheet(self.get_button_style("#e67e22"))
        individual_widgets_btn.clicked.connect(self.test_individual_widgets)
        layout.addWidget(individual_widgets_btn)
        
        # 4. Test contrôleurs
        controllers_btn = QPushButton("⚙️ Tester Contrôleurs")
        controllers_btn.setStyleSheet(self.get_button_style("#9b59b6"))
        controllers_btn.clicked.connect(self.test_controllers)
        layout.addWidget(controllers_btn)
        
        # 5. Test de connectivité DB
        db_test_btn = QPushButton("🔗 Tester Connexion Base de Données")
        db_test_btn.setStyleSheet(self.get_button_style("#34495e"))
        db_test_btn.clicked.connect(self.test_database_connection)
        layout.addWidget(db_test_btn)
        
        layout.addStretch()
        
        # Statut
        self.status_label = QLabel("✅ Prêt pour les tests")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
                border-radius: 5px;
                padding: 10px;
                margin: 10px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.status_label)
    
    def get_button_style(self, color):
        """Style pour les boutons"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                margin: 5px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 0.1);
            }}
        """
    
    def test_stock_window(self):
        """Tester la fenêtre StockWindow"""
        try:
            self.status_label.setText("🔄 Test de StockWindow en cours...")
            
            from ayanna_erp.modules.stock.stock_window import StockWindow
            
            # Créer et afficher la fenêtre
            self.stock_window = StockWindow(self.current_user)
            self.stock_window.show()
            
            self.status_label.setText("✅ StockWindow ouverte avec succès!")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                    border-radius: 5px;
                    padding: 10px;
                    margin: 10px;
                    font-weight: bold;
                }
            """)
            
            QMessageBox.information(
                self, "Succès",
                "✅ StockWindow lancée avec succès!\n\n"
                "Fonctionnalités à tester:\n"
                "• Dashboard avec indicateurs\n"
                "• Navigation entre les onglets\n"
                "• Actions rapides\n"
                "• Communication entre widgets"
            )
            
        except Exception as e:
            self.status_label.setText(f"❌ Erreur StockWindow: {str(e)}")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                    border-radius: 5px;
                    padding: 10px;
                    margin: 10px;
                    font-weight: bold;
                }
            """)
            QMessageBox.critical(self, "Erreur", f"Erreur lors du test de StockWindow:\n{str(e)}")
    
    def test_modular_widget(self):
        """Tester le widget modulaire seul"""
        try:
            self.status_label.setText("🔄 Test du widget modulaire en cours...")
            
            from ayanna_erp.modules.stock.views.modular_stock_widget import ModularStockManagementWidget
            
            # Créer une fenêtre pour le widget
            widget_window = QMainWindow()
            widget_window.setWindowTitle("🏭 Widget Modulaire Stock")
            widget_window.setGeometry(100, 100, 1400, 900)
            
            # Créer le widget
            modular_widget = ModularStockManagementWidget(pos_id=1, current_user=self.current_user)
            widget_window.setCentralWidget(modular_widget)
            widget_window.show()
            
            # Garder une référence
            self.widget_window = widget_window
            
            self.status_label.setText("✅ Widget modulaire ouvert avec succès!")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                    border-radius: 5px;
                    padding: 10px;
                    margin: 10px;
                    font-weight: bold;
                }
            """)
            
            QMessageBox.information(
                self, "Succès",
                "✅ Widget modulaire lancé avec succès!\n\n"
                "Testez:\n"
                "• Dashboard temps réel\n"
                "• Tous les onglets spécialisés\n"
                "• Actions rapides du dashboard\n"
                "• Synchronisation des données"
            )
            
        except Exception as e:
            self.status_label.setText(f"❌ Erreur Widget Modulaire: {str(e)}")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                    border-radius: 5px;
                    padding: 10px;
                    margin: 10px;
                    font-weight: bold;
                }
            """)
            QMessageBox.critical(self, "Erreur", f"Erreur lors du test du widget modulaire:\n{str(e)}")
    
    def test_individual_widgets(self):
        """Tester les widgets individuels"""
        try:
            self.status_label.setText("🔄 Test des widgets individuels...")
            
            # Lancer le test d'architecture existant
            os.system("python test_stock_architecture.py")
            
            self.status_label.setText("✅ Test des widgets individuels lancé!")
            
            QMessageBox.information(
                self, "Test Lancé",
                "✅ Test des widgets individuels lancé!\n\n"
                "Une nouvelle fenêtre s'ouvre avec tous les widgets séparés.\n"
                "Testez chaque onglet individuellement."
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du test des widgets:\n{str(e)}")
    
    def test_controllers(self):
        """Tester les contrôleurs"""
        try:
            self.status_label.setText("🔄 Test des contrôleurs en cours...")
            
            from ayanna_erp.modules.stock.controllers.entrepot_controller import EntrepotController
            from ayanna_erp.modules.stock.controllers.stock_controller import StockController
            from ayanna_erp.modules.stock.controllers.transfert_controller import TransfertController
            from ayanna_erp.modules.stock.controllers.alerte_controller import AlerteController
            from ayanna_erp.modules.stock.controllers.inventaire_controller import InventaireController
            from ayanna_erp.modules.stock.controllers.rapport_controller import RapportController
            
            # Test d'initialisation
            pos_id = 1
            controllers = []
            
            controllers.append(EntrepotController(pos_id))
            controllers.append(StockController(pos_id))
            controllers.append(TransfertController(pos_id))
            controllers.append(AlerteController(pos_id))
            controllers.append(InventaireController(pos_id))
            controllers.append(RapportController(pos_id))
            
            self.status_label.setText("✅ Tous les contrôleurs initialisés avec succès!")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                    border-radius: 5px;
                    padding: 10px;
                    margin: 10px;
                    font-weight: bold;
                }
            """)
            
            QMessageBox.information(
                self, "Succès",
                f"✅ Tous les contrôleurs testés avec succès!\n\n"
                f"Contrôleurs initialisés: {len(controllers)}\n"
                f"• EntrepotController\n"
                f"• StockController\n"
                f"• TransfertController\n"
                f"• AlerteController\n"
                f"• InventaireController\n"
                f"• RapportController"
            )
            
        except Exception as e:
            self.status_label.setText(f"❌ Erreur Contrôleurs: {str(e)}")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                    border-radius: 5px;
                    padding: 10px;
                    margin: 10px;
                    font-weight: bold;
                }
            """)
            QMessageBox.critical(self, "Erreur", f"Erreur lors du test des contrôleurs:\n{str(e)}")
    
    def test_database_connection(self):
        """Tester la connexion à la base de données"""
        try:
            self.status_label.setText("🔄 Test de connexion DB en cours...")
            
            db_manager = DatabaseManager()
            
            with db_manager.get_session() as session:
                # Test simple
                result = session.execute("SELECT 1").scalar()
                
                if result == 1:
                    self.status_label.setText("✅ Connexion DB réussie!")
                    self.status_label.setStyleSheet("""
                        QLabel {
                            background-color: #d4edda;
                            color: #155724;
                            border: 1px solid #c3e6cb;
                            border-radius: 5px;
                            padding: 10px;
                            margin: 10px;
                            font-weight: bold;
                        }
                    """)
                    
                    QMessageBox.information(
                        self, "Succès",
                        "✅ Connexion à la base de données réussie!\n\n"
                        "La base de données est accessible et fonctionnelle."
                    )
                else:
                    raise Exception("Test de requête échoué")
            
        except Exception as e:
            self.status_label.setText(f"❌ Erreur DB: {str(e)}")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                    border-radius: 5px;
                    padding: 10px;
                    margin: 10px;
                    font-weight: bold;
                }
            """)
            QMessageBox.critical(self, "Erreur DB", f"Erreur de connexion à la base de données:\n{str(e)}")


def main():
    """Fonction principale"""
    print("🧪 Démarrage du test d'intégration complète...")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    # Créer la fenêtre de test
    window = IntegrationTestWindow()
    window.show()
    
    print("🎯 Interface de test d'intégration lancée!")
    print("=" * 60)
    print("Instructions:")
    print("1. Testez d'abord la connexion DB")
    print("2. Testez les contrôleurs")
    print("3. Testez le widget modulaire seul")
    print("4. Testez la StockWindow complète")
    print("5. Fermez les fenêtres pour terminer")
    
    # Exécuter l'application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()