"""
Module Boutique/Pharmacie pour Ayanna ERP
Interface POS avec gestion des produits, services, ventes et paiements
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTabWidget, QTableWidget, QTableWidgetItem, 
                            QPushButton, QLineEdit, QLabel, QComboBox, 
                            QSpinBox, QDoubleSpinBox, QTextEdit, QMessageBox,
                            QGroupBox, QGridLayout, QListWidget, QSplitter,
                            QFrame, QScrollArea, QFormLayout, QCheckBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon
from decimal import Decimal
from datetime import datetime
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.boutique.models import ShopProduct, ShopService, ShopSale


class ProductCatalogWidget(QWidget):
    """Widget pour le catalogue de produits dans le POS"""
    
    product_selected = pyqtSignal(object)  # Signal émis lors de la sélection d'un produit
    
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.setup_ui()
        self.load_products()
    
    def setup_ui(self):
        """Configuration de l'interface"""
        layout = QVBoxLayout()
        
        # Barre de recherche
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher un produit...")
        self.search_input.textChanged.connect(self.filter_products)
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("Toutes catégories")
        self.category_combo.currentTextChanged.connect(self.filter_products)
        
        search_layout.addWidget(QLabel("Recherche:"))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(QLabel("Catégorie:"))
        search_layout.addWidget(self.category_combo)
        
        # Zone de produits avec scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.products_widget = QWidget()
        self.products_layout = QGridLayout(self.products_widget)
        self.products_layout.setSpacing(10)
        
        scroll_area.setWidget(self.products_widget)
        
        layout.addLayout(search_layout)
        layout.addWidget(scroll_area)
        self.setLayout(layout)
    
    def load_products(self):
        """Charger les produits"""
        try:
            session = self.db_manager.get_session()
            products = session.query(ShopProduct).filter_by(is_active=True).all()
            
            self.display_products(products)
            
        except Exception as e:
            print(f"Erreur lors du chargement des produits: {e}")
    
    def display_products(self, products):
        """Afficher les produits dans la grille"""
        # Nettoyer la grille existante
        for i in reversed(range(self.products_layout.count())): 
            self.products_layout.itemAt(i).widget().setParent(None)
        
        # Afficher les produits
        row, col = 0, 0
        for product in products:
            product_button = self.create_product_button(product)
            self.products_layout.addWidget(product_button, row, col)
            
            col += 1
            if col >= 4:  # 4 colonnes
                col = 0
                row += 1
    
    def create_product_button(self, product):
        """Créer un bouton pour un produit"""
        button = QPushButton()
        button.setFixedSize(180, 120)
        button.setText(f"{product.name}\n{product.price_unit:.2f} {product.pos.enterprise.currency}")
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
                border-color: #3498DB;
                background-color: #EBF5FB;
            }
            QPushButton:pressed {
                background-color: #D5DBDB;
            }
        """)
        
        button.clicked.connect(lambda: self.product_selected.emit(product))
        return button
    
    def filter_products(self):
        """Filtrer les produits selon la recherche et catégorie"""
        # Implémentation du filtrage
        pass


class ShoppingCartWidget(QWidget):
    """Widget pour le panier d'achat"""
    
    def __init__(self):
        super().__init__()
        self.cart_items = []
        self.setup_ui()
    
    def setup_ui(self):
        """Configuration de l'interface"""
        layout = QVBoxLayout()
        
        # Titre
        title_label = QLabel("Panier")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2C3E50;")
        layout.addWidget(title_label)
        
        # Table du panier
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(["Produit", "Prix", "Qté", "Total", "Action"])
        self.cart_table.horizontalHeader().setStretchLastSection(True)
        
        # Totaux
        totals_frame = QFrame()
        totals_frame.setStyleSheet("background-color: #F8F9FA; border-radius: 5px; padding: 10px;")
        totals_layout = QFormLayout(totals_frame)
        
        self.subtotal_label = QLabel("0.00")
        self.tax_label = QLabel("0.00")
        self.total_label = QLabel("0.00")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #E74C3C;")
        
        totals_layout.addRow("Sous-total:", self.subtotal_label)
        totals_layout.addRow("TVA:", self.tax_label)
        totals_layout.addRow("TOTAL:", self.total_label)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        self.clear_cart_button = QPushButton("Vider le panier")
        self.clear_cart_button.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        self.clear_cart_button.clicked.connect(self.clear_cart)
        
        self.checkout_button = QPushButton("Procéder au paiement")
        self.checkout_button.setStyleSheet("""
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
        
        buttons_layout.addWidget(self.clear_cart_button)
        buttons_layout.addWidget(self.checkout_button)
        
        layout.addWidget(self.cart_table)
        layout.addWidget(totals_frame)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
    
    def add_product(self, product, quantity=1):
        """Ajouter un produit au panier"""
        # Vérifier si le produit existe déjà
        for item in self.cart_items:
            if item['product'].id == product.id:
                item['quantity'] += quantity
                self.update_cart_display()
                return
        
        # Ajouter nouveau produit
        self.cart_items.append({
            'product': product,
            'quantity': quantity,
            'price': product.price_unit
        })
        self.update_cart_display()
    
    def update_cart_display(self):
        """Mettre à jour l'affichage du panier"""
        self.cart_table.setRowCount(len(self.cart_items))
        
        subtotal = 0
        for i, item in enumerate(self.cart_items):
            product = item['product']
            quantity = item['quantity']
            price = item['price']
            line_total = quantity * price
            subtotal += line_total
            
            # Remplir les colonnes
            self.cart_table.setItem(i, 0, QTableWidgetItem(product.name))
            self.cart_table.setItem(i, 1, QTableWidgetItem(f"{price:.2f}"))
            
            # Spinbox pour la quantité
            qty_spinbox = QSpinBox()
            qty_spinbox.setMinimum(1)
            qty_spinbox.setValue(quantity)
            qty_spinbox.valueChanged.connect(lambda val, idx=i: self.update_quantity(idx, val))
            self.cart_table.setCellWidget(i, 2, qty_spinbox)
            
            self.cart_table.setItem(i, 3, QTableWidgetItem(f"{line_total:.2f}"))
            
            # Bouton supprimer
            remove_button = QPushButton("Supprimer")
            remove_button.setStyleSheet("background-color: #E74C3C; color: white; border: none; padding: 5px;")
            remove_button.clicked.connect(lambda checked, idx=i: self.remove_item(idx))
            self.cart_table.setCellWidget(i, 4, remove_button)
        
        # Mettre à jour les totaux
        tax = subtotal * 0.18  # TVA 18%
        total = subtotal + tax
        
        self.subtotal_label.setText(f"{subtotal:.2f}")
        self.tax_label.setText(f"{tax:.2f}")
        self.total_label.setText(f"{total:.2f}")
    
    def update_quantity(self, index, new_quantity):
        """Mettre à jour la quantité d'un article"""
        if 0 <= index < len(self.cart_items):
            self.cart_items[index]['quantity'] = new_quantity
            self.update_cart_display()
    
    def remove_item(self, index):
        """Supprimer un article du panier"""
        if 0 <= index < len(self.cart_items):
            del self.cart_items[index]
            self.update_cart_display()
    
    def clear_cart(self):
        """Vider le panier"""
        self.cart_items.clear()
        self.update_cart_display()
    
    def get_total(self):
        """Obtenir le total du panier"""
        subtotal = sum(item['quantity'] * item['price'] for item in self.cart_items)
        tax = subtotal * 0.18
        return subtotal + tax


class BoutiqueWindow(QMainWindow):
    """Fenêtre principale du module Boutique/Pharmacie"""
    
    def __init__(self, current_user, is_pharmacy=False):
        super().__init__()
        self.current_user = current_user
        self.is_pharmacy = is_pharmacy
        self.db_manager = DatabaseManager()
        
        module_name = "Pharmacie" if is_pharmacy else "Boutique"
        self.setWindowTitle(f"Ayanna ERP - {module_name}")
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
                background-color: #3498DB;
                color: white;
            }
        """)
        
        # Onglet POS
        self.setup_pos_tab()
        
        # Onglet Produits
        self.setup_products_tab()
        
        # Onglet Services
        self.setup_services_tab()
        
        # Onglet Ventes
        self.setup_sales_tab()
        
        # Onglet Clients
        self.setup_clients_tab()
        
        # Onglet Paiements
        self.setup_payments_tab()
        
        # Onglet Rapports
        self.setup_reports_tab()
        
        main_layout.addWidget(self.tab_widget)
    
    def setup_pos_tab(self):
        """Configuration de l'onglet POS"""
        pos_widget = QWidget()
        pos_layout = QHBoxLayout(pos_widget)
        
        # Splitter pour diviser l'écran
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Catalogue de produits (à gauche)
        self.product_catalog = ProductCatalogWidget()
        self.product_catalog.product_selected.connect(self.add_to_cart)
        
        # Panier d'achat (à droite)
        self.shopping_cart = ShoppingCartWidget()
        
        splitter.addWidget(self.product_catalog)
        splitter.addWidget(self.shopping_cart)
        splitter.setSizes([700, 400])  # Répartition de l'espace
        
        pos_layout.addWidget(splitter)
        self.tab_widget.addTab(pos_widget, "🛒 Point de Vente")
    
    def setup_products_tab(self):
        """Configuration de l'onglet Produits"""
        products_widget = QWidget()
        products_layout = QVBoxLayout(products_widget)
        
        # Barre d'outils
        toolbar_layout = QHBoxLayout()
        
        add_product_button = QPushButton("➕ Nouveau Produit")
        add_product_button.setStyleSheet("""
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
        
        edit_product_button = QPushButton("✏️ Modifier")
        delete_product_button = QPushButton("🗑️ Supprimer")
        
        toolbar_layout.addWidget(add_product_button)
        toolbar_layout.addWidget(edit_product_button)
        toolbar_layout.addWidget(delete_product_button)
        toolbar_layout.addStretch()
        
        # Table des produits
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(7)
        self.products_table.setHorizontalHeaderLabels([
            "ID", "Nom", "Description", "Coût", "Prix", "Stock", "Statut"
        ])
        self.products_table.horizontalHeader().setStretchLastSection(True)
        
        products_layout.addLayout(toolbar_layout)
        products_layout.addWidget(self.products_table)
        
        self.tab_widget.addTab(products_widget, "📦 Produits")
    
    def setup_services_tab(self):
        """Configuration de l'onglet Services"""
        services_widget = QWidget()
        services_layout = QVBoxLayout(services_widget)
        
        # Barre d'outils
        toolbar_layout = QHBoxLayout()
        
        add_service_button = QPushButton("➕ Nouveau Service")
        add_service_button.setStyleSheet("""
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
        
        edit_service_button = QPushButton("✏️ Modifier")
        delete_service_button = QPushButton("🗑️ Supprimer")
        
        toolbar_layout.addWidget(add_service_button)
        toolbar_layout.addWidget(edit_service_button)
        toolbar_layout.addWidget(delete_service_button)
        toolbar_layout.addStretch()
        
        # Table des services
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(6)
        self.services_table.setHorizontalHeaderLabels([
            "ID", "Nom", "Description", "Coût", "Prix", "Statut"
        ])
        self.services_table.horizontalHeader().setStretchLastSection(True)
        
        services_layout.addLayout(toolbar_layout)
        services_layout.addWidget(self.services_table)
        
        self.tab_widget.addTab(services_widget, "🔧 Services")
    
    def setup_sales_tab(self):
        """Configuration de l'onglet Ventes"""
        sales_widget = QWidget()
        sales_layout = QVBoxLayout(sales_widget)
        
        # Filtre par date
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Du:"))
        # Ajouter des widgets de date ici
        filter_layout.addStretch()
        
        # Table des ventes
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(7)
        self.sales_table.setHorizontalHeaderLabels([
            "ID", "Référence", "Client", "Date", "Total", "Statut", "Actions"
        ])
        self.sales_table.horizontalHeader().setStretchLastSection(True)
        
        sales_layout.addLayout(filter_layout)
        sales_layout.addWidget(self.sales_table)
        
        self.tab_widget.addTab(sales_widget, "💰 Ventes")
    
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
            "Date", "Vente", "Moyen", "Montant", "Statut"
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
        monthly_sales_button = QPushButton("📉 Ventes du mois")
        top_products_button = QPushButton("🏆 Produits les plus vendus")
        stock_report_button = QPushButton("📦 État des stocks")
        
        selection_layout.addWidget(daily_sales_button, 0, 0)
        selection_layout.addWidget(weekly_sales_button, 0, 1)
        selection_layout.addWidget(monthly_sales_button, 1, 0)
        selection_layout.addWidget(top_products_button, 1, 1)
        selection_layout.addWidget(stock_report_button, 2, 0)
        
        # Zone d'affichage des rapports
        self.reports_display = QTextEdit()
        self.reports_display.setReadOnly(True)
        
        reports_layout.addWidget(reports_selection)
        reports_layout.addWidget(self.reports_display)
        
        self.tab_widget.addTab(reports_widget, "📊 Rapports")
    
    def add_to_cart(self, product):
        """Ajouter un produit au panier"""
        self.shopping_cart.add_product(product)
    
    def closeEvent(self, event):
        """Gérer la fermeture de la fenêtre"""
        self.db_manager.close_session()
        event.accept()
