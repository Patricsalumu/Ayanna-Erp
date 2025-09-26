"""
Widget de l'onglet Panier - Interface principale de vente pour la boutique
Affiche le catalogue des produits/services et la gestion du panier
"""

import sys
from typing import Optional, List, Dict, Any
from decimal import Decimal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QPushButton, QLineEdit, QComboBox, QSpinBox, QTableWidget, 
    QTableWidgetItem, QHeaderView, QMessageBox, QScrollArea, QFrame,
    QSplitter, QTextEdit, QCheckBox, QButtonGroup, QRadioButton,
    QDialog, QDialogButtonBox, QFormLayout, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor

from ayanna_erp.database.database_manager import DatabaseManager
from ..model.models import ShopClient, ShopCategory, ShopProduct, ShopService, ShopComptesConfig


class PanierIndex(QWidget):
    """Widget principal pour la gestion du panier et catalogue"""
    
    # Signaux
    product_selected = pyqtSignal(int, int)  # product_id, quantity
    service_selected = pyqtSignal(int, int)  # service_id, quantity
    
    def __init__(self, boutique_controller, current_user):
        super().__init__()
        self.boutique_controller = boutique_controller
        self.current_user = current_user
        self.db_manager = DatabaseManager()
        
        # Variables d'état
        self.selected_category_id = None
        self.selected_client_id = None
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        
        self.setup_ui()
        self.load_initial_data()
        
        # Connecter les signaux du contrôleur
        self.boutique_controller.panier_updated.connect(self.refresh_panier)
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Splitter principal (catalogue à gauche, panier à droite)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # === SECTION CATALOGUE (GAUCHE) ===
        catalog_widget = self.create_catalog_section()
        splitter.addWidget(catalog_widget)
        
        # === SECTION PANIER (DROITE) ===
        panier_widget = self.create_panier_section()
        splitter.addWidget(panier_widget)
        
        # Définir les proportions du splitter (catalogue 60%, panier 40%)
        splitter.setSizes([600, 400])
        
        main_layout.addWidget(splitter)
    
    def create_catalog_section(self):
        """Créer la section catalogue des produits/services"""
        catalog_widget = QWidget()
        catalog_layout = QVBoxLayout(catalog_widget)
        
        # === HEADER ET FILTRES ===
        header_group = QGroupBox("🛍️ Catalogue - Produits & Services")
        header_layout = QVBoxLayout(header_group)
        
        # Ligne 1: Recherche et filtres
        filter_layout = QHBoxLayout()
        
        # Recherche
        filter_layout.addWidget(QLabel("Recherche:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher un produit ou service...")
        self.search_input.textChanged.connect(self.on_search_changed)
        filter_layout.addWidget(self.search_input)
        
        # Filtre par catégorie
        filter_layout.addWidget(QLabel("Catégorie:"))
        self.category_combo = QComboBox()
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        filter_layout.addWidget(self.category_combo)
        
        # Bouton actualiser
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.clicked.connect(self.refresh_catalog)
        filter_layout.addWidget(refresh_btn)
        
        header_layout.addLayout(filter_layout)
        
        # Ligne 2: Sélection type (Produits/Services)
        type_layout = QHBoxLayout()
        self.type_button_group = QButtonGroup()
        
        self.products_radio = QRadioButton("Produits")
        self.products_radio.setChecked(True)
        self.products_radio.toggled.connect(self.on_type_changed)
        self.type_button_group.addButton(self.products_radio)
        type_layout.addWidget(self.products_radio)
        
        self.services_radio = QRadioButton("Services")
        self.services_radio.toggled.connect(self.on_type_changed)
        self.type_button_group.addButton(self.services_radio)
        type_layout.addWidget(self.services_radio)
        
        type_layout.addStretch()
        header_layout.addLayout(type_layout)
        
        catalog_layout.addWidget(header_group)
        
        # === LISTE DES ARTICLES ===
        self.catalog_table = QTableWidget()
        self.catalog_table.setColumnCount(6)
        self.catalog_table.setHorizontalHeaderLabels([
            "Nom", "Description", "Prix", "Stock", "Quantité", "Action"
        ])
        
        # Configuration des colonnes
        header = self.catalog_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Nom
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Description
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Prix
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Stock
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Quantité
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Action
        
        self.catalog_table.setAlternatingRowColors(True)
        self.catalog_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        catalog_layout.addWidget(self.catalog_table)
        
        return catalog_widget
    
    def create_panier_section(self):
        """Créer la section panier et paiement"""
        panier_widget = QWidget()
        panier_layout = QVBoxLayout(panier_widget)
        
        # === CLIENT SELECTION ===
        client_group = QGroupBox("👤 Client")
        client_layout = QHBoxLayout(client_group)
        
        self.client_combo = QComboBox()
        self.client_combo.setEditable(False)
        self.client_combo.currentTextChanged.connect(self.on_client_changed)
        client_layout.addWidget(self.client_combo)
        
        new_client_btn = QPushButton("+ Nouveau")
        new_client_btn.clicked.connect(self.create_new_client)
        client_layout.addWidget(new_client_btn)
        
        panier_layout.addWidget(client_group)
        
        # === CONTENU DU PANIER ===
        panier_group = QGroupBox("🛒 Panier")
        panier_group_layout = QVBoxLayout(panier_group)
        
        # Table du panier
        self.panier_table = QTableWidget()
        self.panier_table.setColumnCount(5)
        self.panier_table.setHorizontalHeaderLabels([
            "Article", "Prix unit.", "Qté", "Sous-total", "Action"
        ])
        
        # Configuration des colonnes du panier
        panier_header = self.panier_table.horizontalHeader()
        panier_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Article
        panier_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Prix
        panier_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Qté
        panier_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Sous-total
        panier_header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Action
        
        self.panier_table.setMaximumHeight(300)
        panier_group_layout.addWidget(self.panier_table)
        
        # Actions du panier
        panier_actions_layout = QHBoxLayout()
        
        clear_panier_btn = QPushButton("🗑️ Vider panier")
        clear_panier_btn.clicked.connect(self.clear_panier)
        panier_actions_layout.addWidget(clear_panier_btn)
        
        panier_actions_layout.addStretch()
        
        # Total
        self.total_label = QLabel("Total: 0,00 €")
        self.total_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        panier_actions_layout.addWidget(self.total_label)
        
        panier_group_layout.addLayout(panier_actions_layout)
        panier_layout.addWidget(panier_group)
        
        # === PAIEMENT ===
        payment_group = QGroupBox("💳 Paiement")
        payment_layout = QVBoxLayout(payment_group)
        
        # Méthodes de paiement disponibles
        self.payment_methods_layout = QVBoxLayout()
        payment_layout.addLayout(self.payment_methods_layout)
        
        # Notes de paiement
        payment_layout.addWidget(QLabel("Notes (optionnel):"))
        self.payment_notes = QTextEdit()
        self.payment_notes.setMaximumHeight(60)
        payment_layout.addWidget(self.payment_notes)
        
        # Bouton de paiement
        self.pay_button = QPushButton("💰 Effectuer le paiement")
        self.pay_button.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #BDC3C7;
            }
        """)
        self.pay_button.clicked.connect(self.process_payment)
        self.pay_button.setEnabled(False)
        payment_layout.addWidget(self.pay_button)
        
        panier_layout.addWidget(payment_group)
        
        # Stretch pour pousser tout vers le haut
        panier_layout.addStretch()
        
        return panier_widget
    
    def load_initial_data(self):
        """Charger les données initiales"""
        self.load_categories()
        self.load_clients()
        self.load_payment_methods()
        self.refresh_catalog()
        self.refresh_panier()
    
    def load_categories(self):
        """Charger les catégories dans le combo box"""
        try:
            with self.db_manager.get_session() as session:
                categories = self.boutique_controller.get_categories(session)
                
                self.category_combo.clear()
                self.category_combo.addItem("Toutes les catégories", None)
                
                for category in categories:
                    self.category_combo.addItem(category.name, category.id)
                    
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des catégories: {str(e)}")
    
    def load_clients(self):
        """Charger les clients dans le combo box"""
        try:
            with self.db_manager.get_session() as session:
                clients = self.boutique_controller.get_clients(session)
                
                self.client_combo.clear()
                self.client_combo.addItem("Sélectionner un client", None)
                self.client_combo.addItem("🆕 Client anonyme", 0)  # 0 pour client anonyme
                
                for client in clients:
                    display_name = f"{client.nom}"
                    if client.prenom:
                        display_name += f" {client.prenom}"
                    if client.telephone:
                        display_name += f" ({client.telephone})"
                    
                    self.client_combo.addItem(display_name, client.id)
                    
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des clients: {str(e)}")
    
    def load_payment_methods(self):
        """Charger les méthodes de paiement disponibles"""
        try:
            # Nettoyer le layout existant
            for i in reversed(range(self.payment_methods_layout.count())):
                child = self.payment_methods_layout.itemAt(i).widget()
                if child:
                    child.setParent(None)
            
            # Ajouter les méthodes de paiement par défaut
            self.payment_inputs = {}  # Stocker les widgets de saisie des montants
            
            default_methods = [
                {"id": "cash", "nom": "Espèces", "description": "Paiement en espèces"},
                {"id": "mobile", "nom": "Mobile Money", "description": "Paiement mobile"},
                {"id": "bank", "nom": "Banque", "description": "Virement/Carte bancaire"}
            ]
            
            for method in default_methods:
                method_layout = QHBoxLayout()
                
                checkbox = QCheckBox(method["nom"])
                method_layout.addWidget(checkbox)
                
                amount_input = QDoubleSpinBox()
                amount_input.setRange(0, 999999.99)
                amount_input.setDecimals(2)
                amount_input.setSuffix(" €")
                amount_input.setEnabled(False)
                method_layout.addWidget(amount_input)
                
                # Connecter les événements
                checkbox.toggled.connect(lambda checked, inp=amount_input: inp.setEnabled(checked))
                checkbox.toggled.connect(self.update_payment_total)
                amount_input.valueChanged.connect(self.update_payment_total)
                
                self.payment_inputs[method["id"]] = {
                    "checkbox": checkbox,
                    "amount_input": amount_input,
                    "method_data": method
                }
                
                self.payment_methods_layout.addLayout(method_layout)
                
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des méthodes de paiement: {str(e)}")
    
    def refresh_catalog(self):
        """Actualiser l'affichage du catalogue"""
        try:
            with self.db_manager.get_session() as session:
                if self.products_radio.isChecked():
                    # Afficher les produits
                    search_term = self.search_input.text().strip() if self.search_input.text() else None
                    products = self.boutique_controller.get_products(
                        session, 
                        category_id=self.selected_category_id,
                        search_term=search_term
                    )
                    self.populate_catalog_with_products(products)
                else:
                    # Afficher les services
                    search_term = self.search_input.text().strip() if self.search_input.text() else None
                    services = self.boutique_controller.get_services(
                        session,
                        search_term=search_term
                    )
                    self.populate_catalog_with_services(services)
                    
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement du catalogue: {str(e)}")
    
    def populate_catalog_with_products(self, products: List[ShopProduct]):
        """Peupler le catalogue avec les produits"""
        self.catalog_table.setRowCount(len(products))
        
        for row, product in enumerate(products):
            # Nom
            self.catalog_table.setItem(row, 0, QTableWidgetItem(product.name))
            
            # Description
            description = product.description if product.description else "-"
            self.catalog_table.setItem(row, 1, QTableWidgetItem(description))
            
            # Prix
            price_item = QTableWidgetItem(f"{product.price_unit:.2f} €")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.catalog_table.setItem(row, 2, price_item)
            
            # Stock (simulé pour l'instant)
            stock_total = 50  # Valeur par défaut
            stock_item = QTableWidgetItem(str(stock_total))
            stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Colorer selon le stock
            if stock_total == 0:
                stock_item.setBackground(QColor("#E74C3C"))  # Rouge
                stock_item.setForeground(QColor("white"))
            elif stock_total < 10:
                stock_item.setBackground(QColor("#F39C12"))  # Orange
                stock_item.setForeground(QColor("white"))
            
            self.catalog_table.setItem(row, 3, stock_item)
            
            # Quantité (SpinBox)
            quantity_spin = QSpinBox()
            quantity_spin.setMinimum(1)
            quantity_spin.setMaximum(stock_total if stock_total > 0 else 1)
            quantity_spin.setValue(1)
            self.catalog_table.setCellWidget(row, 4, quantity_spin)
            
            # Action (Bouton Ajouter)
            add_btn = QPushButton("➕ Ajouter")
            add_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498DB;
                    color: white;
                    font-weight: bold;
                    padding: 5px 10px;
                    border: none;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #2980B9;
                }
                QPushButton:disabled {
                    background-color: #BDC3C7;
                }
            """)
            
            # Désactiver si pas de stock
            if stock_total <= 0:
                add_btn.setEnabled(False)
                add_btn.setText("Rupture")
            
            # Connecter l'événement
            add_btn.clicked.connect(
                lambda checked, pid=product.id, row=row: self.add_product_to_panier_from_catalog(pid, row)
            )
            
            self.catalog_table.setCellWidget(row, 5, add_btn)
    
    def populate_catalog_with_services(self, services: List[ShopService]):
        """Peupler le catalogue avec les services"""
        self.catalog_table.setRowCount(len(services))
        
        for row, service in enumerate(services):
            # Nom
            self.catalog_table.setItem(row, 0, QTableWidgetItem(service.name))
            
            # Description
            description = service.description if service.description else "-"
            self.catalog_table.setItem(row, 1, QTableWidgetItem(description))
            
            # Prix
            price_item = QTableWidgetItem(f"{service.price:.2f} €")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.catalog_table.setItem(row, 2, price_item)
            
            # Stock (N/A pour les services)
            stock_item = QTableWidgetItem("Illimité")
            stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            stock_item.setBackground(QColor("#27AE60"))  # Vert
            stock_item.setForeground(QColor("white"))
            self.catalog_table.setItem(row, 3, stock_item)
            
            # Quantité (SpinBox)
            quantity_spin = QSpinBox()
            quantity_spin.setMinimum(1)
            quantity_spin.setMaximum(999)
            quantity_spin.setValue(1)
            self.catalog_table.setCellWidget(row, 4, quantity_spin)
            
            # Action (Bouton Ajouter)
            add_btn = QPushButton("➕ Ajouter")
            add_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498DB;
                    color: white;
                    font-weight: bold;
                    padding: 5px 10px;
                    border: none;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #2980B9;
                }
            """)
            
            # Connecter l'événement
            add_btn.clicked.connect(
                lambda checked, sid=service.id, row=row: self.add_service_to_panier_from_catalog(sid, row)
            )
            
            self.catalog_table.setCellWidget(row, 5, add_btn)
    
    def add_product_to_panier_from_catalog(self, product_id: int, row: int):
        """Ajouter un produit au panier depuis le catalogue"""
        try:
            quantity_spin = self.catalog_table.cellWidget(row, 4)
            quantity = quantity_spin.value()
            
            with self.db_manager.get_session() as session:
                success, message = self.boutique_controller.add_product_to_panier(session, product_id, quantity)
                
                if success:
                    QMessageBox.information(self, "Succès", message)
                    self.refresh_panier()
                else:
                    QMessageBox.warning(self, "Erreur", message)
                    
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ajout du produit: {str(e)}")
    
    def add_service_to_panier_from_catalog(self, service_id: int, row: int):
        """Ajouter un service au panier depuis le catalogue"""
        try:
            quantity_spin = self.catalog_table.cellWidget(row, 4)
            quantity = quantity_spin.value()
            
            with self.db_manager.get_session() as session:
                success, message = self.boutique_controller.add_service_to_panier(session, service_id, quantity)
                
                if success:
                    QMessageBox.information(self, "Succès", message)
                    self.refresh_panier()
                else:
                    QMessageBox.warning(self, "Erreur", message)
                    
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ajout du service: {str(e)}")
    
    def refresh_panier(self):
        """Actualiser l'affichage du panier"""
        try:
            with self.db_manager.get_session() as session:
                panier_content = self.boutique_controller.get_panier_content(session)
                
                # Vider la table
                self.panier_table.setRowCount(0)
                
                row = 0
                total = Decimal('0.00')
                
                # Ajouter les produits
                for panier_product in panier_content.get("products", []):
                    self.panier_table.insertRow(row)
                    
                    # Nom du produit
                    product_name = f"[P] {panier_product.product.name}"
                    self.panier_table.setItem(row, 0, QTableWidgetItem(product_name))
                    
                    # Prix unitaire
                    price_item = QTableWidgetItem(f"{panier_product.prix_unitaire:.2f} €")
                    price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.panier_table.setItem(row, 1, price_item)
                    
                    # Quantité
                    qty_item = QTableWidgetItem(str(panier_product.quantite))
                    qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.panier_table.setItem(row, 2, qty_item)
                    
                    # Sous-total
                    subtotal_item = QTableWidgetItem(f"{panier_product.sous_total:.2f} €")
                    subtotal_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.panier_table.setItem(row, 3, subtotal_item)
                    
                    # Bouton supprimer
                    remove_btn = QPushButton("🗑️")
                    remove_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #E74C3C;
                            color: white;
                            font-weight: bold;
                            padding: 3px;
                            border: none;
                            border-radius: 3px;
                        }
                        QPushButton:hover {
                            background-color: #C0392B;
                        }
                    """)
                    remove_btn.clicked.connect(
                        lambda checked, item_id=panier_product.id: self.remove_item_from_panier("product", item_id)
                    )
                    self.panier_table.setCellWidget(row, 4, remove_btn)
                    
                    total += panier_product.sous_total
                    row += 1
                
                # Ajouter les services
                for panier_service in panier_content.get("services", []):
                    self.panier_table.insertRow(row)
                    
                    # Nom du service
                    service_name = f"[S] {panier_service.service.name}"
                    self.panier_table.setItem(row, 0, QTableWidgetItem(service_name))
                    
                    # Prix unitaire
                    price_item = QTableWidgetItem(f"{panier_service.prix_unitaire:.2f} €")
                    price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.panier_table.setItem(row, 1, price_item)
                    
                    # Quantité
                    qty_item = QTableWidgetItem(str(panier_service.quantite))
                    qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.panier_table.setItem(row, 2, qty_item)
                    
                    # Sous-total
                    subtotal_item = QTableWidgetItem(f"{panier_service.sous_total:.2f} €")
                    subtotal_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.panier_table.setItem(row, 3, subtotal_item)
                    
                    # Bouton supprimer
                    remove_btn = QPushButton("🗑️")
                    remove_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #E74C3C;
                            color: white;
                            font-weight: bold;
                            padding: 3px;
                            border: none;
                            border-radius: 3px;
                        }
                        QPushButton:hover {
                            background-color: #C0392B;
                        }
                    """)
                    remove_btn.clicked.connect(
                        lambda checked, item_id=panier_service.id: self.remove_item_from_panier("service", item_id)
                    )
                    self.panier_table.setCellWidget(row, 4, remove_btn)
                    
                    total += panier_service.sous_total
                    row += 1
                
                # Mettre à jour le total
                self.total_label.setText(f"Total: {total:.2f} €")
                
                # Activer/désactiver le bouton de paiement
                self.pay_button.setEnabled(total > 0)
                
                # Mettre à jour les montants de paiement suggérés
                self.update_payment_suggestions(total)
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du rafraîchissement du panier: {str(e)}")
    
    def update_payment_suggestions(self, total_amount: Decimal):
        """Mettre à jour les suggestions de montants de paiement"""
        # Si une seule méthode de paiement est cochée, pré-remplir avec le montant total
        checked_methods = [method for method in self.payment_inputs.values() 
                          if method["checkbox"].isChecked()]
        
        if len(checked_methods) == 1:
            checked_methods[0]["amount_input"].setValue(float(total_amount))
    
    def remove_item_from_panier(self, item_type: str, item_id: int):
        """Supprimer un article du panier"""
        try:
            with self.db_manager.get_session() as session:
                success, message = self.boutique_controller.remove_item_from_panier(session, item_type, item_id)
                
                if success:
                    self.refresh_panier()
                else:
                    QMessageBox.warning(self, "Erreur", message)
                    
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression: {str(e)}")
    
    def clear_panier(self):
        """Vider complètement le panier"""
        reply = QMessageBox.question(
            self, "Confirmation", 
            "Êtes-vous sûr de vouloir vider le panier ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with self.db_manager.get_session() as session:
                    success, message = self.boutique_controller.clear_panier(session)
                    
                    if success:
                        self.refresh_panier()
                    else:
                        QMessageBox.warning(self, "Erreur", message)
                        
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors du vidage du panier: {str(e)}")
    
    def update_payment_total(self):
        """Mettre à jour le total des paiements sélectionnés"""
        total_payment = Decimal('0.00')
        
        for method_data in self.payment_inputs.values():
            if method_data["checkbox"].isChecked():
                amount = Decimal(str(method_data["amount_input"].value()))
                total_payment += amount
    
    def process_payment(self):
        """Traiter le paiement (version simplifiée)"""
        try:
            with self.db_manager.get_session() as session:
                panier_content = self.boutique_controller.get_panier_content(session)
                
                if not panier_content.get("panier") or panier_content.get("total", Decimal('0.00')) <= 0:
                    QMessageBox.warning(self, "Erreur", "Le panier est vide.")
                    return
                
                # Collecter les paiements sélectionnés
                payments_data = []
                total_payment = Decimal('0.00')
                
                for method_id, method_data in self.payment_inputs.items():
                    if method_data["checkbox"].isChecked():
                        amount = Decimal(str(method_data["amount_input"].value()))
                        if amount > 0:
                            payments_data.append({
                                'method': method_data["method_data"]["nom"],
                                'montant': amount
                            })
                            total_payment += amount
                
                if not payments_data:
                    QMessageBox.warning(self, "Erreur", "Aucune méthode de paiement sélectionnée.")
                    return
                
                panier_total = panier_content.get("total", Decimal('0.00'))
                
                if abs(total_payment - panier_total) > Decimal('0.01'):
                    QMessageBox.warning(
                        self, "Erreur de montant", 
                        f"Le total des paiements ({total_payment:.2f}€) ne correspond pas au total du panier ({panier_total:.2f}€)."
                    )
                    return
                
                # Simulation du paiement réussi
                QMessageBox.information(
                    self, "Paiement réussi", 
                    f"Paiement de {total_payment:.2f}€ effectué avec succès!"
                )
                
                # Réinitialiser l'interface
                self.refresh_panier()
                self.reset_payment_form()
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du traitement du paiement: {str(e)}")
    
    def reset_payment_form(self):
        """Réinitialiser le formulaire de paiement"""
        for method_data in self.payment_inputs.values():
            method_data["checkbox"].setChecked(False)
            method_data["amount_input"].setValue(0.00)
            method_data["amount_input"].setEnabled(False)
        
        self.payment_notes.clear()
    
    def create_new_client(self):
        """Ouvrir le dialog de création d'un nouveau client"""
        dialog = ClientCreationDialog(self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            client_data = dialog.get_client_data()
            
            try:
                with self.db_manager.get_session() as session:
                    new_client = self.boutique_controller.create_client(
                        session,
                        nom=client_data["nom"],
                        prenom=client_data.get("prenom"),
                        email=client_data.get("email"),
                        telephone=client_data.get("telephone"),
                        adresse=client_data.get("adresse")
                    )
                    
                    QMessageBox.information(self, "Succès", f"Client {new_client.nom} créé avec succès!")
                    
                    # Actualiser la liste des clients
                    self.load_clients()
                    
                    # Sélectionner le nouveau client
                    for i in range(self.client_combo.count()):
                        if self.client_combo.itemData(i) == new_client.id:
                            self.client_combo.setCurrentIndex(i)
                            break
                            
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la création du client: {str(e)}")
    
    # === ÉVÉNEMENTS ===
    
    def on_search_changed(self):
        """Gestionnaire du changement de recherche (avec délai)"""
        self.search_timer.stop()
        self.search_timer.start(300)  # Attendre 300ms avant de chercher
    
    def perform_search(self):
        """Effectuer la recherche"""
        self.refresh_catalog()
    
    def on_category_changed(self):
        """Gestionnaire du changement de catégorie"""
        current_data = self.category_combo.currentData()
        self.selected_category_id = current_data if current_data is not None else None
        self.refresh_catalog()
    
    def on_type_changed(self):
        """Gestionnaire du changement de type (Produits/Services)"""
        self.refresh_catalog()
    
    def on_client_changed(self):
        """Gestionnaire du changement de client"""
        client_id = self.client_combo.currentData()
        
        if client_id and client_id > 0:  # Exclure "Sélectionner" (None) et "Anonyme" (0)
            try:
                with self.db_manager.get_session() as session:
                    success, message = self.boutique_controller.set_panier_client(session, client_id)
                    
                    if not success:
                        QMessageBox.warning(self, "Erreur", message)
                        
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'association du client: {str(e)}")
    
    def add_product_to_panier(self, product_id: int, quantity: int = 1):
        """Méthode publique pour ajouter un produit au panier"""
        try:
            with self.db_manager.get_session() as session:
                success, message = self.boutique_controller.add_product_to_panier(session, product_id, quantity)
                
                if success:
                    self.refresh_panier()
                    return True
                else:
                    QMessageBox.warning(self, "Erreur", message)
                    return False
                    
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ajout du produit: {str(e)}")
            return False


class ClientCreationDialog(QDialog):
    """Dialog pour créer un nouveau client"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nouveau Client")
        self.setModal(True)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Formulaire
        form_layout = QFormLayout()
        
        self.nom_input = QLineEdit()
        self.nom_input.setPlaceholderText("Nom du client (obligatoire)")
        form_layout.addRow("Nom *:", self.nom_input)
        
        self.prenom_input = QLineEdit()
        self.prenom_input.setPlaceholderText("Prénom du client")
        form_layout.addRow("Prénom:", self.prenom_input)
        
        self.telephone_input = QLineEdit()
        self.telephone_input.setPlaceholderText("+243 XXX XXX XXX")
        form_layout.addRow("Téléphone:", self.telephone_input)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email@example.com")
        form_layout.addRow("Email:", self.email_input)
        
        self.adresse_input = QTextEdit()
        self.adresse_input.setMaximumHeight(80)
        self.adresse_input.setPlaceholderText("Adresse complète")
        form_layout.addRow("Adresse:", self.adresse_input)
        
        layout.addLayout(form_layout)
        
        # Boutons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Validation
        buttons.button(QDialogButtonBox.StandardButton.Ok).clicked.connect(self.validate_form)
    
    def validate_form(self):
        """Valider le formulaire avant acceptation"""
        if not self.nom_input.text().strip():
            QMessageBox.warning(self, "Erreur", "Le nom du client est obligatoire.")
            return False
        return True
    
    def get_client_data(self):
        """Récupérer les données du client"""
        return {
            "nom": self.nom_input.text().strip(),
            "prenom": self.prenom_input.text().strip() or None,
            "telephone": self.telephone_input.text().strip() or None,
            "email": self.email_input.text().strip() or None,
            "adresse": self.adresse_input.toPlainText().strip() or None
        }
    
    def accept(self):
        """Accepter le dialog après validation"""
        if self.validate_form():
            super().accept()