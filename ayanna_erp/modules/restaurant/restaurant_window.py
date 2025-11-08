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


class TableLayoutWidget(QGraphicsView):
    """Widget pour la disposition des tables dans une salle"""
    
    table_selected = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setup_ui()
    
    def setup_ui(self):
        """Configuration de l'interface"""
        self.setStyleSheet("""
            QGraphicsView {
                border: 2px solid #BDC3C7;
                border-radius: 5px;
                background-color: #F8F9FA;
            }
        """)
        
        # Charger la disposition des tables
        self.load_tables()
    
    def load_tables(self):
        """Charger les tables dans la vue"""
        # Exemple de tables pour la démonstration
        tables_data = [
            {"id": 1, "number": "T1", "x": 50, "y": 50, "width": 80, "height": 60, "status": "free"},
            {"id": 2, "number": "T2", "x": 200, "y": 50, "width": 80, "height": 60, "status": "occupied"},
            {"id": 3, "number": "T3", "x": 350, "y": 50, "width": 80, "height": 60, "status": "reserved"},
            {"id": 4, "number": "T4", "x": 50, "y": 200, "width": 120, "height": 80, "status": "free"},
            {"id": 5, "number": "T5", "x": 250, "y": 200, "width": 120, "height": 80, "status": "occupied"},
        ]
        
        for table_data in tables_data:
            self.add_table_to_scene(table_data)
    
    def add_table_to_scene(self, table_data):
        """Ajouter une table à la scène"""
        # Couleur selon le statut
        status_colors = {
            "free": QColor("#27AE60"),      # Vert - libre
            "occupied": QColor("#E74C3C"),   # Rouge - occupée
            "reserved": QColor("#F39C12"),   # Orange - réservée
            "cleaning": QColor("#95A5A6")    # Gris - nettoyage
        }
        
        color = status_colors.get(table_data["status"], QColor("#BDC3C7"))
        
        # Créer le rectangle de la table
        rect = QRectF(table_data["x"], table_data["y"], 
                     table_data["width"], table_data["height"])
        
        table_rect = self.scene.addRect(rect, QPen(QColor("#2C3E50"), 2), QBrush(color))
        
        # Ajouter le texte du numéro de table
        text_item = self.scene.addText(table_data["number"], QFont("Arial", 12, QFont.Weight.Bold))
        text_item.setPos(table_data["x"] + 10, table_data["y"] + 20)
        text_item.setDefaultTextColor(QColor("white"))
        
        # Stocker les données de la table
        table_rect.setData(0, table_data)


class OrderWidget(QWidget):
    """Widget de gestion des commandes"""
    
    def __init__(self):
        super().__init__()
        self.current_order = None
        self.setup_ui()
    
    def setup_ui(self):
        """Configuration de l'interface"""
        layout = QVBoxLayout()
        
        # En-tête de la commande
        header_layout = QHBoxLayout()
        
        self.table_label = QLabel("Aucune table sélectionnée")
        self.table_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2C3E50;
            padding: 10px;
            background-color: #ECF0F1;
            border-radius: 5px;
        """)
        
        self.order_number_label = QLabel("Commande: #XXXX")
        self.order_number_label.setStyleSheet("font-weight: bold; color: #7F8C8D;")
        
        header_layout.addWidget(self.table_label)
        header_layout.addStretch()
        header_layout.addWidget(self.order_number_label)
        
        # Zone de produits/services
        products_group = QGroupBox("Menu")
        products_layout = QVBoxLayout(products_group)
        
        # Catégories
        categories_layout = QHBoxLayout()
        
        self.appetizers_button = QPushButton("🥗 Entrées")
        self.mains_button = QPushButton("🍽️ Plats")
        self.desserts_button = QPushButton("🍰 Desserts")
        self.drinks_button = QPushButton("🥤 Boissons")
        
        categories_layout.addWidget(self.appetizers_button)
        categories_layout.addWidget(self.mains_button)
        categories_layout.addWidget(self.desserts_button)
        categories_layout.addWidget(self.drinks_button)
        
        # Grille de produits
        self.products_scroll = QScrollArea()
        self.products_widget = QWidget()
        self.products_layout = QGridLayout(self.products_widget)
        self.products_scroll.setWidget(self.products_widget)
        self.products_scroll.setWidgetResizable(True)
        
        products_layout.addLayout(categories_layout)
        products_layout.addWidget(self.products_scroll)
        
        # Commande courante
        order_group = QGroupBox("Commande courante")
        order_layout = QVBoxLayout(order_group)
        
        self.order_table = QTableWidget()
        self.order_table.setColumnCount(4)
        self.order_table.setHorizontalHeaderLabels(["Produit", "Prix", "Qté", "Total"])
        self.order_table.horizontalHeader().setStretchLastSection(True)
        
        # Totaux
        totals_layout = QHBoxLayout()
        self.total_label = QLabel("Total: 0.00 €")
        self.total_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #E74C3C;")
        
        totals_layout.addStretch()
        totals_layout.addWidget(self.total_label)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        self.save_order_button = QPushButton("💾 Enregistrer")
        self.print_order_button = QPushButton("🖨️ Imprimer")
        self.pay_button = QPushButton("💳 Encaisser")
        
        self.save_order_button.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        
        self.print_order_button.setStyleSheet("""
            QPushButton {
                background-color: #95A5A6;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7F8C8D;
            }
        """)
        
        self.pay_button.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        buttons_layout.addWidget(self.save_order_button)
        buttons_layout.addWidget(self.print_order_button)
        buttons_layout.addWidget(self.pay_button)
        
        order_layout.addWidget(self.order_table)
        order_layout.addLayout(totals_layout)
        order_layout.addLayout(buttons_layout)
        
        # Layout principal
        layout.addLayout(header_layout)
        layout.addWidget(products_group)
        layout.addWidget(order_group)
        
        self.setLayout(layout)
        
        # Charger les produits
        self.load_menu_items()
    
    def load_menu_items(self):
        """Charger les éléments du menu"""
        # Exemples de produits pour la démonstration
        menu_items = [
            {"name": "Salade César", "price": 12.50, "category": "appetizers"},
            {"name": "Soupe du jour", "price": 8.00, "category": "appetizers"},
            {"name": "Steak frites", "price": 22.00, "category": "mains"},
            {"name": "Saumon grillé", "price": 25.00, "category": "mains"},
            {"name": "Tiramisu", "price": 8.50, "category": "desserts"},
            {"name": "Tarte au chocolat", "price": 9.00, "category": "desserts"},
            {"name": "Coca-Cola", "price": 3.50, "category": "drinks"},
            {"name": "Café", "price": 2.50, "category": "drinks"},
        ]
        
        # Afficher tous les produits initialement
        self.display_menu_items(menu_items)
    
    def display_menu_items(self, items):
        """Afficher les éléments du menu"""
        # Nettoyer la grille existante
        for i in reversed(range(self.products_layout.count())): 
            self.products_layout.itemAt(i).widget().setParent(None)
        
        # Afficher les produits
        row, col = 0, 0
        for item in items:
            product_button = self.create_menu_button(item)
            self.products_layout.addWidget(product_button, row, col)
            
            col += 1
            if col >= 3:  # 3 colonnes
                col = 0
                row += 1
    
    def create_menu_button(self, item):
        """Créer un bouton pour un élément du menu"""
        button = QPushButton()
        button.setFixedSize(150, 100)
        button.setText(f"{item['name']}\n{item['price']:.2f} €")
        button.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 2px solid #BDC3C7;
                border-radius: 8px;
                font-weight: bold;
                text-align: center;
                padding: 10px;
            }
            QPushButton:hover {
                border-color: #F39C12;
                background-color: #FEF9E7;
            }
            QPushButton:pressed {
                background-color: #F7DC6F;
            }
        """)
        
        # Connecter le clic pour ajouter à la commande
        button.clicked.connect(lambda: self.add_to_order(item))
        return button
    
    def add_to_order(self, item):
        """Ajouter un élément à la commande"""
        # Logique d'ajout à la commande
        pass
    
    def set_table(self, table_data):
        """Définir la table courante"""
        if table_data:
            self.table_label.setText(f"Table {table_data['number']} - {table_data['status'].title()}")
        else:
            self.table_label.setText("Aucune table sélectionnée")


class RestaurantWindow(QMainWindow):
    """Fenêtre principale du module Restaurant/Bar"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        # Utiliser l'instance globale de DatabaseManager partagée par l'application
        self.db_manager = get_database_manager()
        
        self.setWindowTitle("Ayanna ERP - Restaurant/Bar")
        self.setMinimumSize(1400, 900)
        
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
                background-color: #F39C12;
                color: white;
            }
        """)
        
        # Onglet POS Restaurant
        self.setup_pos_tab()
        
        # Onglet Gestion des salles
        self.setup_halls_tab()
        
        # Onglet Gestion des tables
        self.setup_tables_tab()
        
        # Onglet Menu/Produits
        self.setup_menu_tab()
        
        # Onglet Commandes
        self.setup_orders_tab()
        
        # Onglet Clients
        self.setup_clients_tab()
        
        # Onglet Paiements
        self.setup_payments_tab()
        
        # Onglet Rapports
        self.setup_reports_tab()
        
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
    
    def setup_menu_tab(self):
        """Configuration de l'onglet Menu"""
        menu_widget = QWidget()
        menu_layout = QVBoxLayout(menu_widget)
        
        # Barre d'outils
        toolbar_layout = QHBoxLayout()
        
        add_item_button = QPushButton("➕ Nouvel Article")
        add_item_button.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        edit_item_button = QPushButton("✏️ Modifier")
        delete_item_button = QPushButton("🗑️ Supprimer")
        
        toolbar_layout.addWidget(add_item_button)
        toolbar_layout.addWidget(edit_item_button)
        toolbar_layout.addWidget(delete_item_button)
        toolbar_layout.addStretch()
        
        # Table du menu
        self.menu_table = QTableWidget()
        self.menu_table.setColumnCount(7)
        self.menu_table.setHorizontalHeaderLabels([
            "ID", "Nom", "Catégorie", "Description", "Coût", "Prix", "Statut"
        ])
        self.menu_table.horizontalHeader().setStretchLastSection(True)
        
        menu_layout.addLayout(toolbar_layout)
        menu_layout.addWidget(self.menu_table)
        
        self.tab_widget.addTab(menu_widget, "📋 Menu")
    
    def setup_orders_tab(self):
        """Onglet Commandes — utiliser la vue de commandes du module"""
        commandes_view = CommandesView(entreprise_id=1, parent=self)
        self.tab_widget.addTab(commandes_view, "📝 Commandes")
    
    def setup_clients_tab(self):
        """Configuration de l'onglet Clients"""
        clients_widget = QWidget()
        clients_layout = QVBoxLayout(clients_widget)
        
        # Barre d'outils
        toolbar_layout = QHBoxLayout()
        
        add_client_button = QPushButton("➕ Nouveau Client")
        add_client_button.setStyleSheet("""
            QPushButton {
                background-color: #9B59B6;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8E44AD;
            }
        """)
        
        edit_client_button = QPushButton("✏️ Modifier")
        delete_client_button = QPushButton("🗑️ Supprimer")
        
        toolbar_layout.addWidget(add_client_button)
        toolbar_layout.addWidget(edit_client_button)
        toolbar_layout.addWidget(delete_client_button)
        toolbar_layout.addStretch()
        
        # Table des clients
        self.clients_table = QTableWidget()
        self.clients_table.setColumnCount(5)
        self.clients_table.setHorizontalHeaderLabels([
            "ID", "Nom", "Email", "Téléphone", "Adresse"
        ])
        self.clients_table.horizontalHeader().setStretchLastSection(True)
        
        clients_layout.addLayout(toolbar_layout)
        clients_layout.addWidget(self.clients_table)
        
        self.tab_widget.addTab(clients_widget, "👥 Clients")
    
    def setup_payments_tab(self):
        """Configuration de l'onglet Paiements"""
        payments_widget = QWidget()
        payments_layout = QVBoxLayout(payments_widget)
        
        # Configuration des moyens de paiement
        config_group = QGroupBox("Configuration des moyens de paiement")
        config_layout = QVBoxLayout(config_group)
        
        # Table des moyens de paiement
        self.payment_methods_table = QTableWidget()
        self.payment_methods_table.setColumnCount(4)
        self.payment_methods_table.setHorizontalHeaderLabels([
            "Nom", "Compte comptable", "Par défaut", "Actif"
        ])
        
        config_layout.addWidget(self.payment_methods_table)
        
        # Historique des paiements
        history_group = QGroupBox("Historique des paiements")
        history_layout = QVBoxLayout(history_group)
        
        self.payments_history_table = QTableWidget()
        self.payments_history_table.setColumnCount(5)
        self.payments_history_table.setHorizontalHeaderLabels([
            "Date", "Commande", "Moyen", "Montant", "Statut"
        ])
        
        history_layout.addWidget(self.payments_history_table)
        
        payments_layout.addWidget(config_group)
        payments_layout.addWidget(history_group)
        
        self.tab_widget.addTab(payments_widget, "💳 Paiements")
    
    def setup_reports_tab(self):
        """Configuration de l'onglet Rapports"""
        reports_widget = QWidget()
        reports_layout = QVBoxLayout(reports_widget)
        
        # Zone de sélection des rapports
        reports_selection = QGroupBox("Sélection du rapport")
        selection_layout = QGridLayout(reports_selection)
        
        # Différents types de rapports
        daily_sales_button = QPushButton("📊 Ventes du jour")
        weekly_sales_button = QPushButton("📈 Ventes de la semaine")
        table_turnover_button = QPushButton("🔄 Rotation des tables")
        popular_items_button = QPushButton("🏆 Plats populaires")
        revenue_report_button = QPushButton("💰 Rapport de revenus")
        
        selection_layout.addWidget(daily_sales_button, 0, 0)
        selection_layout.addWidget(weekly_sales_button, 0, 1)
        selection_layout.addWidget(table_turnover_button, 1, 0)
        selection_layout.addWidget(popular_items_button, 1, 1)
        selection_layout.addWidget(revenue_report_button, 2, 0)
        
        # Zone d'affichage des rapports
        self.reports_display = QTextEdit()
        self.reports_display.setReadOnly(True)
        
        reports_layout.addWidget(reports_selection)
        reports_layout.addWidget(self.reports_display)
        
        self.tab_widget.addTab(reports_widget, "📊 Rapports")
    
    def closeEvent(self, event):
        """Gérer la fermeture de la fenêtre"""
        self.db_manager.close_session()
        event.accept()
