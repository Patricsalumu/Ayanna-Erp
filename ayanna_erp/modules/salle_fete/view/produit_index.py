"""
Onglet Produits pour le module Salle de Fête
Gestion et affichage des produits via contrôleur MVC
"""

import sys
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QTableWidget, QTableWidgetItem, 
                            QPushButton, QLineEdit, QLabel, QComboBox, 
                            QSpinBox, QDoubleSpinBox, QTextEdit, QMessageBox,
                            QGroupBox, QGridLayout, QListWidget, QSplitter,
                            QFrame, QScrollArea, QFormLayout, QCheckBox,
                            QDateTimeEdit, QHeaderView)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDateTime
from PyQt6.QtGui import QFont, QPixmap, QIcon
from decimal import Decimal
from datetime import datetime, timedelta

# Import du contrôleur produit et du formulaire modal
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from controller.produit_controller import ProduitController
from .produit_form import ProduitForm
from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController


class ProduitIndex(QWidget):
    """Onglet pour la gestion des produits"""
    
    def __init__(self, main_controller, current_user):
        super().__init__()
        self.main_controller = main_controller
        self.current_user = current_user
        
        # Initialiser le contrôleur produit
        self.produit_controller = ProduitController(pos_id=getattr(main_controller, 'pos_id', 1))
        
        # Initialiser le contrôleur entreprise pour les devises
        self.entreprise_controller = EntrepriseController()
        
        # Connecter les signaux du contrôleur
        self.produit_controller.products_loaded.connect(self.on_products_loaded)
        self.produit_controller.product_added.connect(self.on_product_added)
        self.produit_controller.product_updated.connect(self.on_product_updated)
        self.produit_controller.product_deleted.connect(self.on_product_deleted)
        self.produit_controller.error_occurred.connect(self.on_error_occurred)
        
        self.selected_product = None
        self.products_data = []
        
        self.setup_ui()
        self.connect_signals()
        
        # Charger les produits après initialisation
        QTimer.singleShot(100, self.load_products)
    
    def get_currency_symbol(self):
        """Récupère le symbole de devise depuis l'entreprise"""
        try:
            return self.entreprise_controller.get_currency_symbol()
        except:
            return "€"  # Fallback
    
    def format_amount(self, amount):
        """Formate un montant avec la devise de l'entreprise"""
        try:
            return self.entreprise_controller.format_amount(amount)
        except:
            return f"{amount:.2f} €"  # Fallback
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # Barre d'outils
        toolbar_layout = QHBoxLayout()
        
        # Boutons d'action
        self.add_product_button = QPushButton("➕ Nouveau produit")
        self.add_product_button.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #219A52;
            }
        """)
        
        self.edit_product_button = QPushButton("✏️ Modifier")
        self.edit_product_button.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        
        self.delete_product_button = QPushButton("🗑️ Supprimer")
        self.delete_product_button.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        
        # Bouton de gestion du stock
        self.stock_button = QPushButton("📦 Gestion stock")
        self.stock_button.setStyleSheet("""
            QPushButton {
                background-color: #9B59B6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8E44AD;
            }
        """)
        
        # Barre de recherche et filtres
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Rechercher un produit...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498DB;
            }
        """)
        
        # Filtre par catégorie
        self.category_filter = QComboBox()
        self.category_filter.addItems(["Toutes catégories", "Boissons", "Alimentaire", "Matériel", "Décoration", "Autre"])
        self.category_filter.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: white;
            }
        """)
        
        # Filtre par stock
        self.stock_filter = QComboBox()
        self.stock_filter.addItems(["Tout le stock", "En stock", "Stock faible", "Rupture"])
        self.stock_filter.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: white;
            }
        """)
        
        toolbar_layout.addWidget(self.add_product_button)
        toolbar_layout.addWidget(self.edit_product_button)
        toolbar_layout.addWidget(self.delete_product_button)
        toolbar_layout.addWidget(self.stock_button)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(QLabel("Catégorie:"))
        toolbar_layout.addWidget(self.category_filter)
        toolbar_layout.addWidget(QLabel("Stock:"))
        toolbar_layout.addWidget(self.stock_filter)
        toolbar_layout.addWidget(self.search_input)
        
        # Splitter pour diviser en deux parties
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Table des produits (côté gauche)
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(10)
        self.products_table.setHorizontalHeaderLabels([
            "ID", "Nom du produit", "Catégorie", "Cout", "Prix unitaire", "Seuil min.", "Unité", "Stock", "Compte", "Statut"
        ])
        
        # Configuration du tableau
        self.products_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: white;
                gridline-color: #ECF0F1;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #E74C3C;
                color: white;
            }
            QHeaderView::section {
                background-color: #34495E;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        
        # Redimensionnement automatique des colonnes
        header = self.products_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Nom du produit
        
        # Zone de détails du produit (côté droit)
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        # Informations du produit
        product_info_group = QGroupBox("Détails du produit")
        product_info_layout = QFormLayout(product_info_group)
        
        self.product_name_label = QLabel("-")
        self.product_category_label = QLabel("-")
        self.product_cost_label = QLabel("-")
        self.product_price_label = QLabel("-")
        self.product_stock_label = QLabel("-")
        self.product_min_threshold_label = QLabel("-")
        self.product_unit_label = QLabel("-")
        self.product_status_label = QLabel("-")
        self.product_description_label = QLabel("-")
        self.product_description_label.setWordWrap(True)
        
        product_info_layout.addRow("Nom:", self.product_name_label)
        product_info_layout.addRow("Catégorie:", self.product_category_label)
        product_info_layout.addRow("Coût:", self.product_price_label)
        product_info_layout.addRow("Prix unitaire:", self.product_stock_label)
        product_info_layout.addRow("Stock actuel:", self.product_status_label)
        product_info_layout.addRow("Seuil minimum:", self.product_min_threshold_label)
        product_info_layout.addRow("Unité:", self.product_unit_label)
        # product_info_layout.addRow("Statut:", "-")
        product_info_layout.addRow("Description:", self.product_description_label)
        
        # Mouvements de stock récents
        stock_movements_group = QGroupBox("Mouvements de stock récents")
        stock_movements_layout = QVBoxLayout(stock_movements_group)
        
        self.stock_movements_list = QListWidget()
        self.stock_movements_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ECF0F1;
            }
            QListWidget::item:selected {
                background-color: #3498DB;
                color: white;
            }
        """)
        
        stock_movements_layout.addWidget(self.stock_movements_list)
        
        # Statistiques de vente
        sales_stats_group = QGroupBox("Statistiques de vente")
        sales_stats_layout = QFormLayout(sales_stats_group)
        
        self.times_sold_label = QLabel("0")
        self.total_sold_label = QLabel("0")
        self.total_revenue_label = QLabel(f"0.00 {self.get_currency_symbol()}")
        self.last_sold_label = QLabel("-")
        self.avg_quantity_label = QLabel("-")
        
        sales_stats_layout.addRow("Fois vendu:", self.times_sold_label)
        sales_stats_layout.addRow("Quantité totale vendue:", self.total_sold_label)
        sales_stats_layout.addRow("Revenus générés:", self.total_revenue_label)
        sales_stats_layout.addRow("Dernière vente:", self.last_sold_label)
        sales_stats_layout.addRow("Quantité moyenne:", self.avg_quantity_label)
        
        # Assemblage du layout des détails
        details_layout.addWidget(product_info_group)
        details_layout.addWidget(stock_movements_group)
        details_layout.addWidget(sales_stats_group)
        details_layout.addStretch()
        
        # Ajout au splitter
        splitter.addWidget(self.products_table)
        splitter.addWidget(details_widget)
        splitter.setSizes([600, 400])
        
        # Assemblage du layout principal
        layout.addLayout(toolbar_layout)
        layout.addWidget(splitter)
        
        # Chargement des données
        self.load_products()
        
        # Connexion des signaux
        self.products_table.itemSelectionChanged.connect(self.on_product_selected)
        self.search_input.textChanged.connect(self.filter_products)
        self.category_filter.currentTextChanged.connect(self.filter_products)
        self.stock_filter.currentTextChanged.connect(self.filter_products)
    
    def load_products(self):
        """Charger les produits depuis la base de données"""
        # TODO: Implémenter le chargement depuis la base de données
        # Pour l'instant, on utilise des données de test
        sample_data = [
            ["001", "Champagne Moët & Chandon", "Boissons", "45.00 $", "25", "10", "bouteille", "En stock"],
            ["002", "Petits fours assortis", "Alimentaire", "12.00 $", "5", "20", "plateau", "Stock faible"],
            ["003", "Nappe blanche 3m", "Matériel", "15.00 $", "30", "5", "pièce", "En stock"],
            ["004", "Bouquet de roses", "Décoration", "35.00 $", "0", "5", "bouquet", "Rupture"],
            ["005", "Assiettes jetables", "Matériel", "8.00 $", "100", "50", "lot de 20", "En stock"],
            ["006", "Vin rouge Bordeaux", "Boissons", "25.00 $", "15", "10", "bouteille", "En stock"],
        ]
        
        self.products_table.setRowCount(len(sample_data))
        
        for row, data in enumerate(sample_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                
                # Couleur selon le stock
                if col == 4:  # Colonne stock
                    stock_value = int(value)
                    min_threshold = int(data[5])
                    
                    if stock_value == 0:
                        item.setBackground(Qt.GlobalColor.red)
                        item.setForeground(Qt.GlobalColor.white)
                    elif stock_value <= min_threshold:
                        item.setBackground(Qt.GlobalColor.yellow)
                    else:
                        item.setBackground(Qt.GlobalColor.green)
                        item.setForeground(Qt.GlobalColor.white)
                
                # Couleur selon le statut
                elif col == 7:  # Colonne statut
                    if value == "En stock":
                        item.setBackground(Qt.GlobalColor.green)
                        item.setForeground(Qt.GlobalColor.white)
                    elif value == "Stock faible":
                        item.setBackground(Qt.GlobalColor.yellow)
                    else:  # Rupture
                        item.setBackground(Qt.GlobalColor.red)
                        item.setForeground(Qt.GlobalColor.white)
                
                self.products_table.setItem(row, col, item)
    
    def on_product_selected(self):
        """Gérer la sélection d'un produit"""
        current_row = self.products_table.currentRow()
        if current_row >= 0 and current_row < len(self.products_data):
            # Récupérer le produit depuis les données chargées
            product = self.products_data[current_row]
            self.selected_product = product
            
            # Mettre à jour les détails du produit
            self.product_name_label.setText(product.name)
            self.product_category_label.setText(product.category or "Non spécifiée")
            self.product_price_label.setText(self.format_amount(product.price_unit))
            self.product_stock_label.setText(f"{product.stock_quantity} {product.unit}")
            self.product_min_threshold_label.setText(f"{product.stock_min} {product.unit}")
            self.product_unit_label.setText(product.unit or "Unité")
            self.product_status_label.setText("Actif" if product.is_active else "Inactif")
            self.product_description_label.setText(product.description or "Aucune description")
            
            # Charger les statistiques de vente réelles
            self.load_product_sales_statistics(product.id)
            
            # Charger les mouvements de stock réels
            self.load_stock_movements(product.id)
    
    def load_product_sales_statistics(self, product_id):
        """Charger les statistiques de vente d'un produit"""
        try:
            # Récupérer les statistiques depuis le contrôleur
            stats = self.produit_controller.get_product_sales_statistics(product_id)
            
            if stats:
                # Mettre à jour les labels avec les vraies données
                self.times_sold_label.setText(str(stats['total_sales']))
                self.total_sold_label.setText(str(stats['total_sold']))
                self.total_revenue_label.setText(self.format_amount(stats['total_revenue']))
                
                # Formatage de la dernière vente
                if stats['last_sale']:
                    last_sale = stats['last_sale']
                    if hasattr(last_sale, 'strftime'):
                        self.last_sold_label.setText(last_sale.strftime("%d/%m/%Y"))
                    else:
                        self.last_sold_label.setText(str(last_sale))
                else:
                    self.last_sold_label.setText("Jamais vendu")
                
                # Quantité moyenne
                if stats['average_quantity'] > 0:
                    self.avg_quantity_label.setText(f"{stats['average_quantity']:.1f}")
                else:
                    self.avg_quantity_label.setText("0")
            else:
                # Aucune statistique disponible
                self.times_sold_label.setText("0")
                self.total_sold_label.setText("0")
                self.total_revenue_label.setText(f"0.00 {self.get_currency_symbol()}")
                self.last_sold_label.setText("Jamais vendu")
                self.avg_quantity_label.setText("0")
                
        except Exception as e:
            print(f"❌ Erreur lors du chargement des statistiques de vente: {str(e)}")
            # Valeurs par défaut en cas d'erreur
            self.times_sold_label.setText("Erreur")
            self.total_sold_label.setText("Erreur")
            self.total_revenue_label.setText("Erreur")
            self.last_sold_label.setText("Erreur")
            self.avg_quantity_label.setText("Erreur")
    
    def load_stock_movements(self, product_id):
        """Charger les mouvements de stock d'un produit"""
        try:
            # Vider la liste actuelle
            self.stock_movements_list.clear()
            
            # Récupérer les mouvements récents depuis le contrôleur
            movements = self.produit_controller.get_product_recent_movements(product_id, limit=10)
            
            if movements and len(movements) > 0:
                for movement in movements:
                    # Formatage de la date
                    movement_date = movement['date']
                    if hasattr(movement_date, 'strftime'):
                        date_str = movement_date.strftime("%d/%m/%Y")
                    else:
                        date_str = str(movement_date)
                    
                    # Formatage du mouvement
                    movement_type = movement['type']
                    client_name = movement['client_name'] or "Système"
                    quantity = movement['quantity']
                    reason = movement['reason']
                    
                    # Couleur selon le type de mouvement
                    if movement_type == 'SORTIE':
                        movement_text = f"{date_str} - {movement_type}: -{quantity} ({client_name})"
                    elif movement_type == 'ENTREE':
                        movement_text = f"{date_str} - {movement_type}: +{quantity} ({reason})"
                    else:
                        movement_text = f"{date_str} - {movement_type}: {quantity} ({reason})"
                    
                    if movement['total_line'] > 0:
                        movement_text += f" - {self.format_amount(movement['total_line'])}"
                    
                    self.stock_movements_list.addItem(movement_text)
            else:
                # Aucun mouvement trouvé
                self.stock_movements_list.addItem("Aucun mouvement enregistré")
                
        except Exception as e:
            print(f"❌ Erreur lors du chargement des mouvements: {str(e)}")
            self.stock_movements_list.clear()
            self.stock_movements_list.addItem("Erreur lors du chargement")
    
    def filter_products(self):
        """Filtrer les produits selon les critères"""
        search_text = self.search_input.text().lower()
        category_filter = self.category_filter.currentText()
        stock_filter = self.stock_filter.currentText()
        
        for row in range(self.products_table.rowCount()):
            show_row = True
            
            # Filtre par texte de recherche
            if search_text:
                nom = self.products_table.item(row, 1).text().lower()
                categorie = self.products_table.item(row, 2).text().lower()
                if search_text not in nom and search_text not in categorie:
                    show_row = False
            
            # Filtre par catégorie
            if category_filter != "Toutes catégories":
                categorie = self.products_table.item(row, 2).text()
                if categorie != category_filter:
                    show_row = False
            
            # Filtre par stock
            if stock_filter != "Tout le stock":
                statut = self.products_table.item(row, 7).text()
                if stock_filter == "En stock" and statut != "En stock":
                    show_row = False
                elif stock_filter == "Stock faible" and statut != "Stock faible":
                    show_row = False
                elif stock_filter == "Rupture" and statut != "Rupture":
                    show_row = False
            
            self.products_table.setRowHidden(row, not show_row)
    
    # === MÉTHODES DE CONNEXION AUX CONTRÔLEURS ===
    
    def connect_signals(self):
        """Connecter les signaux des widgets aux méthodes"""
        # Boutons d'action
        self.add_product_button.clicked.connect(self.show_add_product_form)
        self.edit_product_button.clicked.connect(self.show_edit_product_form)
        self.delete_product_button.clicked.connect(self.delete_selected_product)
        
        # Table des produits
        self.products_table.itemSelectionChanged.connect(self.on_product_selection_changed)
        self.products_table.itemDoubleClicked.connect(self.show_edit_product_form)
        
        # Filtres
        self.search_input.textChanged.connect(self.filter_products)
        self.category_filter.currentTextChanged.connect(self.filter_products)
        self.stock_filter.currentTextChanged.connect(self.filter_products)
    
    def load_products(self):
        """Charger la liste des produits depuis le contrôleur"""
        try:
            self.produit_controller.load_products()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des produits: {str(e)}")
    
    def on_products_loaded(self, products):
        """Callback quand les produits sont chargés"""
        self.products_data = products
        self.populate_products_table()
        self.update_statistics()
    
    def on_product_added(self, product):
        """Callback quand un produit est ajouté"""
        self.load_products()  # Recharger la liste
        QMessageBox.information(self, "Succès", "Produit ajouté avec succès !")
    
    def on_product_updated(self, product):
        """Callback quand un produit est modifié"""
        self.load_products()  # Recharger la liste
        QMessageBox.information(self, "Succès", "Produit modifié avec succès !")
    
    def on_product_deleted(self, product_id):
        """Callback quand un produit est supprimé"""
        self.load_products()  # Recharger la liste
        QMessageBox.information(self, "Succès", "Produit supprimé avec succès !")
    
    def on_error_occurred(self, error_message):
        """Callback quand une erreur survient"""
        QMessageBox.critical(self, "Erreur", error_message)
    
    def populate_products_table(self):
        """Remplir le tableau des produits avec les données"""
        self.products_table.setRowCount(len(self.products_data))
        
        for row, product in enumerate(self.products_data):
            # ID (caché)
            self.products_table.setItem(row, 0, QTableWidgetItem(str(product.id)))
            
            # Nom
            self.products_table.setItem(row, 1, QTableWidgetItem(product.name or ''))
            
            # Catégorie
            category = product.category or ''
            self.products_table.setItem(row, 2, QTableWidgetItem(category))
            
            # Coût
            cost = float(product.cost or 0)
            self.products_table.setItem(row, 3, QTableWidgetItem(self.format_amount(cost)))
            
            # Prix
            price = float(product.price_unit or 0)
            self.products_table.setItem(row, 4, QTableWidgetItem(self.format_amount(price)))
            
            # Seuil minimum
            stock_min = float(product.stock_min or 0)
            self.products_table.setItem(row, 5, QTableWidgetItem(f"{stock_min:.0f}"))
            
            #Unite
            unit = product.unit or 'pièce'
            self.products_table.setItem(row, 6, QTableWidgetItem(unit))
            
            # Stock
            stock = float(product.stock_quantity or 0)
            self.products_table.setItem(row, 7, QTableWidgetItem(f"{stock:.0f}"))

            # Compte comptable
            account_text = "Non défini"
            if hasattr(product, 'account_id') and product.account_id:
                try:
                    # Importer ici pour éviter les imports circulaires
                    from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ComptabiliteController
                    comptabilite_controller = ComptabiliteController()
                    compte = comptabilite_controller.get_compte_by_id(product.account_id)
                    if compte:
                        account_text = f"{compte.numero} - {compte.nom}"
                except Exception as e:
                    print(f"Erreur lors de la récupération du compte: {e}")
                    account_text = "Erreur"
            self.products_table.setItem(row, 8, QTableWidgetItem(account_text))
            
            # Statut stock
            if stock == 0:
                status = "Rupture"
                status_color = Qt.GlobalColor.red
            elif stock <= stock_min and stock_min > 0:
                status = "Stock faible"
                status_color = Qt.GlobalColor.yellow
            else:
                status = "En stock"
                status_color = Qt.GlobalColor.green
            
            status_item = QTableWidgetItem(status)
            status_item.setBackground(status_color)
            self.products_table.setItem(row, 9, status_item)
            
        
        # Cacher la colonne ID
        self.products_table.hideColumn(0)
    
    def on_product_selection_changed(self):
        """Gestion de la sélection d'un produit"""
        selected_rows = self.products_table.selectionModel().selectedRows()
        
        if selected_rows:
            row = selected_rows[0].row()
            product_id = int(self.products_table.item(row, 0).text())
            
            # Trouver le produit sélectionné dans les données
            self.selected_product = None
            for product in self.products_data:
                if product.id == product_id:
                    self.selected_product = product
                    break
            
            # Activer les boutons
            self.edit_product_button.setEnabled(True)
            self.delete_product_button.setEnabled(True)
        else:
            self.selected_product = None
            self.edit_product_button.setEnabled(False)
            self.delete_product_button.setEnabled(False)
    
    def show_add_product_form(self):
        """Afficher le formulaire d'ajout de produit"""
        form = ProduitForm(self, controller=self.produit_controller)
        form.produit_saved.connect(self.on_product_form_saved)
        form.exec()
    
    def show_edit_product_form(self):
        """Afficher le formulaire de modification de produit"""
        if not self.selected_product:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un produit à modifier.")
            return
        
        form = ProduitForm(self, produit_data=self.selected_product, controller=self.produit_controller)
        form.produit_saved.connect(self.on_product_form_saved)
        form.exec()
    
    def delete_selected_product(self):
        """Supprimer le produit sélectionné"""
        if not self.selected_product:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un produit à supprimer.")
            return
        
        # Confirmation
        reply = QMessageBox.question(
            self, 
            "Confirmation", 
            f"Êtes-vous sûr de vouloir supprimer le produit '{self.selected_product.get('name', '')}'?\n\n"
            "Cette action est irréversible.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.produit_controller.delete_product(self.selected_product.get('id'))
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression: {str(e)}")
    
    def on_product_form_saved(self, product_data):
        """Callback quand un produit est sauvegardé depuis le formulaire"""
        # Le contrôleur gère déjà les callbacks, pas besoin d'action ici
        pass
    
    def update_statistics(self):
        """Mettre à jour les statistiques des produits"""
        if not hasattr(self, 'products_data'):
            return
        
        total_products = len(self.products_data)
        active_products = sum(1 for p in self.products_data if p.is_active)
        
        # Calcul du stock total et alertes
        total_stock_value = 0
        low_stock_count = 0
        out_of_stock_count = 0
        
        for product in self.products_data:
            stock = float(product.stock_quantity or 0)
            cost = float(product.cost or 0)
            stock_min = float(product.stock_min or 0)
            
            total_stock_value += stock * cost
            
            if stock == 0:
                out_of_stock_count += 1
            elif stock <= stock_min and stock_min > 0:
                low_stock_count += 1
        
        # Mise à jour des labels (si ils existent)
        if hasattr(self, 'stats_label'):
            self.stats_label.setText(
                f"Produits: {active_products}/{total_products} actifs | "
                f"Valeur stock: {self.format_amount(total_stock_value)} | "
                f"Alertes: {low_stock_count} faibles, {out_of_stock_count} ruptures"
            )
