"""
Fenêtre du module Restaurant/Bar pour Ayanna ERP
Gestion des salles, tables, commandes et POS
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTabWidget, QTableWidget, QTableWidgetItem, 
                            QPushButton, QLineEdit, QLabel, QComboBox, 
                            QSpinBox, QDoubleSpinBox, QTextEdit, QMessageBox,
                            QGroupBox, QGridLayout, QListWidget, QSplitter,
                            QFrame, QScrollArea, QFormLayout, QCheckBox,
                            QGraphicsView, QGraphicsScene, QGraphicsRectItem)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF
from PyQt6.QtGui import QFont, QPixmap, QIcon, QBrush, QPen, QColor
from decimal import Decimal
from datetime import datetime
from ayanna_erp.database.database_manager import get_database_manager
from ayanna_erp.modules.restaurant.views.salle_view import SalleView
from ayanna_erp.modules.restaurant.views.vente_view import VenteView
from ayanna_erp.modules.restaurant.views.commandes_view import CommandesView
from ayanna_erp.modules.salle_fete.view.entreSortie_index import EntreeSortieIndex
from ayanna_erp.modules.boutique.view.client_index import ClientIndex
from ayanna_erp.modules.boutique.view.commandes_index import CommandesIndexWidget
from ayanna_erp.modules.boutique.view.categorie_index import CategorieIndex
from ayanna_erp.modules.boutique.view.produit_index import ProduitIndex

#import du controlleur principale de la boutique
from ayanna_erp.modules.boutique.controller.boutique_controller import BoutiqueController


class RestaurantWindow(QMainWindow):
    """Fenêtre principale du module Restaurant/Bar"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        # Utiliser l'instance globale de DatabaseManager partagée par l'application
        self.pos_id = 1
        self.db_manager = get_database_manager()
        self.boutique_controller = BoutiqueController(self.pos_id)
        
        self.setWindowTitle("Ayanna ERP - Restaurant/Bar")
        self.setMinimumSize(1200, 650)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal avec onglets
        main_layout = QVBoxLayout(central_widget)
        
        # Widget à onglets
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #BDC3C7;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ECF0F1;
                padding: 10px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #28a745;
                color: white;
            }
        """)
        
        # Onglet POS Restaurant
        self.setup_pos_tab()
        
        # Onglet Commandes
        self.setup_orders_tab()
        
        # Onglet Categories
        self.setup_categories_tab()
        
        # Onglet Produits
        self.setup_produits_tab()
        
        # Onglet Gestion des salles
        self.setup_halls_tab()
        
        # Onglet Gestion des tables
        # self.setup_tables_tab()
        
        
        # Onglet Clients
        self.setup_clients_tab()
        
        
        # Onglet Rapports
        self.setup_caisse_tab()
        
        main_layout.addWidget(self.tab_widget)
    
    def setup_pos_tab(self):
        """Configuration de l'onglet POS en réutilisant la vue du module (VenteView)"""
        pos_view = VenteView(entreprise_id=1, parent=self)
        self.tab_widget.addTab(pos_view, "🍽️ Point de Vente")
    
    def setup_halls_tab(self):
        """Onglet Salles — utiliser la vue de gestion des salles (SalleView)"""
        salle_view = SalleView(entreprise_id=1, parent=self)
        self.tab_widget.addTab(salle_view, "🏢 Salles")
    
    def setup_tables_tab(self):
        """Onglet Tables — réutilise `SalleView` (plan et édition des tables)"""
        tables_view = SalleView(entreprise_id=1, parent=self)
        self.tab_widget.addTab(tables_view, "🪑 Tables")
    
    def setup_categories_tab(self):
        """Configuration de l'onglet Menu"""
        categorie_widget = CategorieIndex(1, 1)
        self.tab_widget.addTab(categorie_widget, "📂 Categories")
        
    def setup_produits_tab(self):
        """Configuration de l'onglet Paiements"""
        produit_widget = ProduitIndex(1, 1)
        self.tab_widget.addTab(produit_widget, "📦 Produits")
    
    def setup_orders_tab(self):
        """Onglet Commandes — utiliser la vue de commandes du module"""
        commandes_view = CommandesIndexWidget(self.boutique_controller, 1)
        self.tab_widget.addTab(commandes_view, "📝 Commandes")
    
    def setup_clients_tab(self):
        """Configuration de l'onglet Clients"""
        clients_widget = ClientIndex(self.boutique_controller, 1) #TODO A implementer
        self.tab_widget.addTab(clients_widget, "👥 Clients")    
    
    def setup_caisse_tab(self):
        """Configuration de l'onglet caisse"""

        caisses_view = EntreeSortieIndex(self.boutique_controller, 1) #TODO A implementer
        self.tab_widget.addTab(caisses_view, "📊 Caisse")
    
    def closeEvent(self, event):
        """Gérer la fermeture de la fenêtre"""
        self.db_manager.close_session()
        event.accept()
