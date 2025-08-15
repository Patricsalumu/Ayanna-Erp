"""
Fenêtre principale d'Ayanna ERP avec grille des modules
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QGridLayout, QPushButton, QLabel, QMenuBar, 
                            QStatusBar, QFrame, QMessageBox, QApplication)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QAction, QFont
from ayanna_erp.database.database_manager import DatabaseManager, Module, POSPoint


class ModuleButton(QPushButton):
    """Bouton personnalisé pour les modules"""
    
    def __init__(self, module_name, description, icon_path=None):
        super().__init__()
        self.module_name = module_name
        self.description = description
        self.setup_ui(icon_path)
    
    def setup_ui(self, icon_path):
        """Configuration de l'interface du bouton"""
        self.setFixedSize(200, 150)
        self.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498DB, stop:1 #2980B9);
                border: none;
                border-radius: 10px;
                color: white;
                font-weight: bold;
                font-size: 14px;
                text-align: center;
                padding: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5DADE2, stop:1 #3498DB);
                transform: scale(1.05);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2980B9, stop:1 #21618C);
            }
        """)
        
        # Layout vertical pour organiser le contenu
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Icône (si disponible)
        if icon_path:
            icon_label = QLabel()
            pixmap = QPixmap(icon_path).scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio)
            icon_label.setPixmap(pixmap)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label)
        
        # Titre du module
        title_label = QLabel(self.module_name)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(self.description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("font-size: 12px; color: #ECF0F1;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Appliquer le layout (Note: QPushButton ne supporte pas directement setLayout)
        # On utilisera setText pour afficher le nom du module
        self.setText(f"{self.module_name}\n\n{self.description}")


class MainWindow(QMainWindow):
    """Fenêtre principale d'Ayanna ERP"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.db_manager = DatabaseManager()
        self.module_windows = {}  # Stockage des fenêtres de modules ouvertes
        
        self.setup_ui()
        self.load_modules()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        self.setWindowTitle(f"Ayanna ERP - Bienvenue {self.current_user.name}")
        self.setMinimumSize(1200, 750)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ECF0F1;
            }
        """)
        
        # Menu bar
        self.setup_menu_bar()
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # En-tête
        self.setup_header(main_layout)
        
        # Grille des modules
        self.setup_modules_grid(main_layout)
        
        # Status bar
        self.setup_status_bar()
    
    def setup_menu_bar(self):
        """Configuration de la barre de menu"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #34495E;
                color: white;
                border-bottom: 2px solid #2C3E50;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 8px 16px;
            }
            QMenuBar::item:selected {
                background-color: #3498DB;
            }
        """)
        
        # Menu Fichier
        file_menu = menubar.addMenu("Fichier")
        
        logout_action = QAction("Déconnexion", self)
        logout_action.triggered.connect(self.logout)
        file_menu.addAction(logout_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction("Quitter", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Menu Configuration
        config_menu = menubar.addMenu("Configuration")
        
        enterprise_action = QAction("Entreprise", self)
        enterprise_action.triggered.connect(self.open_enterprise_config)
        config_menu.addAction(enterprise_action)
        
        users_action = QAction("Utilisateurs", self)
        users_action.triggered.connect(self.open_users_config)
        config_menu.addAction(users_action)
        
        # Menu Aide
        help_menu = menubar.addMenu("Aide")
        
        about_action = QAction("À propos", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_header(self, layout):
        """Configuration de l'en-tête"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2C3E50, stop:1 #34495E);
                border-radius: 10px;
                padding: 20px;
            }
        """)
        header_frame.setFixedHeight(140)
        
        header_layout = QHBoxLayout(header_frame)
        
        # Titre principal
        title_label = QLabel("AYANNA ERP")
        title_label.setStyleSheet("""
            color: white;
            font-size: 24px;
            font-weight: bold;
        """)
        
        # Information utilisateur
        user_info_label = QLabel(f"Connecté en tant que: {self.current_user.name}")
        user_info_label.setStyleSheet("""
            color: #BDC3C7;
            font-size: 14px;
        """)
        user_info_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(user_info_label)
        
        layout.addWidget(header_frame)
    
    def setup_modules_grid(self, layout):
        """Configuration de la grille des modules"""
        # Frame pour la grille
        grid_frame = QFrame()
        grid_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 30px;
            }
        """)
        
        # Layout en grille
        self.grid_layout = QGridLayout(grid_frame)
        self.grid_layout.setSpacing(20)
        
        # Titre de la section
        modules_title = QLabel("Modules Disponibles")
        modules_title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #2C3E50;
            margin-bottom: 20px;
        """)
        modules_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Layout principal pour le frame
        grid_main_layout = QVBoxLayout()
        grid_main_layout.addWidget(modules_title)
        grid_main_layout.addLayout(self.grid_layout)
        
        grid_frame.setLayout(grid_main_layout)
        layout.addWidget(grid_frame)
    
    def setup_status_bar(self):
        """Configuration de la barre de statut"""
        self.statusBar().showMessage("Prêt")
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #34495E;
                color: white;
                border-top: 2px solid #2C3E50;
            }
        """)
    
    def load_modules(self):
        """Charger et afficher les modules disponibles"""
        try:
            session = self.db_manager.get_session()
            modules = session.query(Module).all()
            
            # Configuration des modules avec leurs descriptions et couleurs
            module_configs = {
                "SalleFete": {
                    "description": "Gestion des événements\net salles de fête",
                    "color": "#E74C3C"
                },
                "Boutique": {
                    "description": "Gestion de la boutique\net des ventes",
                    "color": "#3498DB"
                },
                "Pharmacie": {
                    "description": "Gestion de la pharmacie\net des médicaments",
                    "color": "#2ECC71"
                },
                "Restaurant": {
                    "description": "Gestion du restaurant\net du bar",
                    "color": "#F39C12"
                },
                "Hotel": {
                    "description": "Gestion de l'hôtel\net des réservations",
                    "color": "#9B59B6"
                },
                "Achats": {
                    "description": "Gestion des achats\net fournisseurs",
                    "color": "#1ABC9C"
                },
                "Stock": {
                    "description": "Gestion des stocks\net inventaires",
                    "color": "#34495E"
                },
                "Comptabilite": {
                    "description": "Comptabilité\nSYSCOHADA",
                    "color": "#8E44AD"
                }
            }
            
            # Créer les boutons des modules
            row, col = 0, 0
            for i, module in enumerate(modules):
                config = module_configs.get(module.name, {
                    "description": module.description or "Module",
                    "color": "#3498DB"
                })
                
                button = self.create_module_button(
                    module.name, 
                    config["description"],
                    config["color"]
                )
                button.clicked.connect(lambda checked, name=module.name: self.open_module(name))
                
                self.grid_layout.addWidget(button, row, col)
                
                col += 1
                if col >= 4:  # 4 colonnes par ligne
                    col = 0
                    row += 1
            
        except Exception as e:
            print(f"Erreur lors du chargement des modules: {e}")
    
    def create_module_button(self, name, description, color):
        """Créer un bouton de module personnalisé"""
        button = QPushButton()
        button.setFixedSize(250, 150)
        button.setText(f"{name}\n\n{description}")
        button.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {color}, stop:1 {self.darken_color(color)});
                border: none;
                border-radius: 15px;
                color: white;
                font-weight: bold;
                font-size: 14px;
                text-align: center;
                padding: 15px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.lighten_color(color)}, stop:1 {color});
                transform: scale(1.05);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.darken_color(color)}, stop:1 {self.darken_color(color, 0.3)});
            }}
        """)
        return button
    
    def darken_color(self, color, factor=0.2):
        """Assombrir une couleur"""
        # Implémentation simple - dans un vrai projet, utiliser QColor
        return color  # Pour l'instant, retourne la même couleur
    
    def lighten_color(self, color, factor=0.2):
        """Éclaircir une couleur"""
        # Implémentation simple - dans un vrai projet, utiliser QColor
        return color  # Pour l'instant, retourne la même couleur
    
    def open_module(self, module_name):
        """Ouvrir un module spécifique"""
        try:
            # Vérifier si le module est déjà ouvert
            if module_name in self.module_windows:
                window = self.module_windows[module_name]
                if window.isVisible():
                    window.raise_()
                    window.activateWindow()
                    return
            
            # Importer et ouvrir le module approprié
            if module_name == "SalleFete":
                from ..modules.salle_fete.view.salle_fete_window import SalleFeteWindow
                window = SalleFeteWindow(self.current_user)
            elif module_name == "Boutique":
                from ayanna_erp.modules.boutique.boutique_window import BoutiqueWindow
                window = BoutiqueWindow(self.current_user)
            elif module_name == "Pharmacie":
                from ayanna_erp.modules.boutique.boutique_window import BoutiqueWindow
                window = BoutiqueWindow(self.current_user, is_pharmacy=True)
            elif module_name == "Restaurant":
                from ayanna_erp.modules.restaurant.restaurant_window import RestaurantWindow
                window = RestaurantWindow(self.current_user)
            elif module_name == "Hotel":
                from ayanna_erp.modules.hotel.hotel_window import HotelWindow
                window = HotelWindow(self.current_user)
            elif module_name == "Achats":
                from ayanna_erp.modules.achats.achats_window import AchatsWindow
                window = AchatsWindow(self.current_user)
            elif module_name == "Stock":
                from ayanna_erp.modules.stock.stock_window import StockWindow
                window = StockWindow(self.current_user)
            elif module_name == "Comptabilite":
                from ayanna_erp.modules.comptabilite.comptabilite_window import ComptabiliteWindow
                window = ComptabiliteWindow(self.current_user)
            else:
                QMessageBox.information(self, "Information", f"Module {module_name} en cours de développement.")
                return
            
            self.module_windows[module_name] = window
            window.show()
            
        except ImportError as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de charger le module {module_name}:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ouverture du module {module_name}:\n{str(e)}")
    
    def logout(self):
        """Déconnexion"""
        # Fermer toutes les fenêtres de modules ouvertes
        for window in self.module_windows.values():
            if window.isVisible():
                window.close()
        
        # Afficher la fenêtre de connexion
        from ayanna_erp.ui.login_window import LoginWindow
        self.login_window = LoginWindow()
        self.login_window.show()
        
        # Fermer la fenêtre principale
        self.close()
    
    def open_enterprise_config(self):
        """Ouvrir la configuration de l'entreprise"""
        QMessageBox.information(self, "Information", "Configuration de l'entreprise en cours de développement.")
    
    def open_users_config(self):
        """Ouvrir la gestion des utilisateurs"""
        QMessageBox.information(self, "Information", "Gestion des utilisateurs en cours de développement.")
    
    def show_about(self):
        """Afficher les informations sur l'application"""
        QMessageBox.about(self, "À propos d'Ayanna ERP", 
                         "Ayanna ERP v1.0.0\n\n"
                         "Système de gestion intégré pour :\n"
                         "• Salle de Fête\n"
                         "• Boutique / Pharmacie\n"
                         "• Hôtel\n"
                         "• Restaurant / Bar\n"
                         "• Achats\n"
                         "• Stock / Inventaire\n"
                         "• Comptabilité SYSCOHADA\n\n"
                         "© 2024 Ayanna Solutions")
    
    def closeEvent(self, event):
        """Gérer la fermeture de l'application"""
        # Fermer toutes les fenêtres de modules
        for window in self.module_windows.values():
            if window.isVisible():
                window.close()
        
        # Fermer la session de base de données
        self.db_manager.close_session()
        
        event.accept()
