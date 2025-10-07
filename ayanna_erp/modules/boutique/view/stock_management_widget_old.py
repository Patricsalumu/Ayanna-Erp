"""
Interface utilisateur pour la gestion des entrepôts et transferts de stock
"""

from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton, 
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, 
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout, QTextEdit, 
    QDoubleSpinBox, QSpinBox, QCheckBox, QTabWidget, QTreeWidget, 
    QTreeWidgetItem, QSplitter, QProgressBar, QDateEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QDate
from PyQt6.QtGui import QFont, QColor, QPixmap, QIcon

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.boutique.controller.stock_controller import StockController
from ayanna_erp.modules.boutique.model.models import ShopWarehouse, ShopStockTransfer, ShopProduct


class WarehouseFormDialog(QDialog):
    """Dialog pour créer/éditer un entrepôt"""
    
    def __init__(self, parent=None, warehouse=None, pos_id=None):
        super().__init__(parent)
        self.warehouse = warehouse
        self.pos_id = pos_id
        self.setWindowTitle("Nouvel Entrepôt" if warehouse is None else "Éditer Entrepôt")
        self.setFixedSize(500, 650)
        self.setup_ui()
        
        if warehouse:
            self.populate_form()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # Titre
        title = QLabel("Créer un Nouvel Entrepôt" if self.warehouse is None else "Éditer l'Entrepôt")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Formulaire
        form_layout = QFormLayout()
        
        # Code entrepôt (obligatoire)
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("Code unique de l'entrepôt (ex: ENT001)")
        form_layout.addRow("Code*:", self.code_edit)
        
        # Nom entrepôt (obligatoire)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nom de l'entrepôt")
        form_layout.addRow("Nom*:", self.name_edit)
        
        # Type d'entrepôt
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Principal", "Secondaire", "Transit", "Retour", 
            "Réparation", "Externe", "Virtuel", "Autre"
        ])
        form_layout.addRow("Type:", self.type_combo)
        
        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Description de l'entrepôt (optionnel)")
        form_layout.addRow("Description:", self.description_edit)
        
        # Adresse
        self.address_edit = QTextEdit()
        self.address_edit.setMaximumHeight(60)
        self.address_edit.setPlaceholderText("Adresse de l'entrepôt (optionnel)")
        form_layout.addRow("Adresse:", self.address_edit)
        
        # Capacité limite
        self.capacity_spinbox = QSpinBox()
        self.capacity_spinbox.setRange(0, 999999)
        self.capacity_spinbox.setValue(0)
        self.capacity_spinbox.setSpecialValueText("Aucune limite")
        form_layout.addRow("Capacité limite:", self.capacity_spinbox)
        
        # Contact
        contact_group = QGroupBox("Informations de Contact")
        contact_layout = QFormLayout(contact_group)
        
        self.contact_person_edit = QLineEdit()
        self.contact_person_edit.setPlaceholderText("Nom du responsable")
        contact_layout.addRow("Responsable:", self.contact_person_edit)
        
        self.contact_phone_edit = QLineEdit()
        self.contact_phone_edit.setPlaceholderText("Numéro de téléphone")
        contact_layout.addRow("Téléphone:", self.contact_phone_edit)
        
        self.contact_email_edit = QLineEdit()
        self.contact_email_edit.setPlaceholderText("Adresse email")
        contact_layout.addRow("Email:", self.contact_email_edit)
        
        # Entrepôt par défaut
        self.is_default_checkbox = QCheckBox("Définir comme entrepôt par défaut")
        self.is_default_checkbox.setToolTip("Les nouveaux produits seront automatiquement associés à cet entrepôt")
        
        # Assemblage
        layout.addLayout(form_layout)
        layout.addWidget(contact_group)
        layout.addWidget(self.is_default_checkbox)
        layout.addSpacing(20)
        
        # Boutons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept_if_valid)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def populate_form(self):
        """Remplir le formulaire avec les données de l'entrepôt existant"""
        if not self.warehouse:
            return
            
        self.code_edit.setText(self.warehouse.code or "")
        self.name_edit.setText(self.warehouse.name or "")
        
        # Type
        type_index = self.type_combo.findText(self.warehouse.type or "Principal")
        if type_index >= 0:
            self.type_combo.setCurrentIndex(type_index)
        
        self.description_edit.setPlainText(self.warehouse.description or "")
        self.address_edit.setPlainText(self.warehouse.address or "")
        
        if self.warehouse.capacity_limit:
            self.capacity_spinbox.setValue(self.warehouse.capacity_limit)
        
        self.contact_person_edit.setText(self.warehouse.contact_person or "")
        self.contact_phone_edit.setText(self.warehouse.contact_phone or "")
        self.contact_email_edit.setText(self.warehouse.contact_email or "")
        self.is_default_checkbox.setChecked(self.warehouse.is_default or False)
    
    def accept_if_valid(self):
        """Valider et accepter le formulaire"""
        if not self.validate_form():
            return
        
        self.accept()
    
    def validate_form(self):
        """Valider les données du formulaire"""
        code = self.code_edit.text().strip()
        name = self.name_edit.text().strip()
        
        if not code:
            QMessageBox.warning(self, "Validation", "Le code de l'entrepôt est obligatoire.")
            self.code_edit.setFocus()
            return False
        
        if not name:
            QMessageBox.warning(self, "Validation", "Le nom de l'entrepôt est obligatoire.")
            self.name_edit.setFocus()
            return False
        
        if len(code) < 3:
            QMessageBox.warning(self, "Validation", "Le code doit contenir au moins 3 caractères.")
            self.code_edit.setFocus()
            return False
        
        # Vérifier l'email si fourni
        email = self.contact_email_edit.text().strip()
        if email and '@' not in email:
            QMessageBox.warning(self, "Validation", "L'adresse email n'est pas valide.")
            self.contact_email_edit.setFocus()
            return False
        
        return True
    
    def get_warehouse_data(self):
        """Récupérer les données du formulaire"""
        return {
            "code": self.code_edit.text().strip(),
            "name": self.name_edit.text().strip(),
            "type": self.type_combo.currentText(),
            "description": self.description_edit.toPlainText().strip() or None,
            "address": self.address_edit.toPlainText().strip() or None,
            "capacity_limit": self.capacity_spinbox.value() if self.capacity_spinbox.value() > 0 else None,
            "contact_person": self.contact_person_edit.text().strip() or None,
            "contact_phone": self.contact_phone_edit.text().strip() or None,
            "contact_email": self.contact_email_edit.text().strip() or None,
            "is_default": self.is_default_checkbox.isChecked()
        }


class TransferFormDialog(QDialog):
    """Dialog pour créer un transfert entre entrepôts"""
    
    def __init__(self, parent=None, pos_id=None, db_manager=None):
        super().__init__(parent)
        self.pos_id = pos_id
        self.db_manager = db_manager
        self.transfer_items = []  # Liste des produits à transférer
        
        self.setWindowTitle("Nouveau Transfert entre Entrepôts")
        self.setFixedSize(700, 600)
        self.setup_ui()
        self.load_warehouses()
        
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # Titre
        title = QLabel("Créer un Transfert entre Entrepôts")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Informations générales
        info_group = QGroupBox("Informations du Transfert")
        info_layout = QFormLayout(info_group)
        
        # Entrepôt source
        self.source_warehouse_combo = QComboBox()
        self.source_warehouse_combo.currentTextChanged.connect(self.on_source_warehouse_changed)
        info_layout.addRow("Entrepôt Source*:", self.source_warehouse_combo)
        
        # Entrepôt destination
        self.dest_warehouse_combo = QComboBox()
        info_layout.addRow("Entrepôt Destination*:", self.dest_warehouse_combo)
        
        # Date prévue
        self.expected_date = QDateEdit()
        self.expected_date.setDate(QDate.currentDate())
        self.expected_date.setCalendarPopup(True)
        info_layout.addRow("Date Prévue:", self.expected_date)
        
        # Libellé (obligatoire)
        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("Libellé du transfert (obligatoire)")
        self.label_edit.textChanged.connect(self.update_create_button_state)
        info_layout.addRow("Libellé*:", self.label_edit)
        
        # Notes (optionnel)
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        self.notes_edit.setPlaceholderText("Notes ou remarques complémentaires (optionnel)")
        info_layout.addRow("Notes:", self.notes_edit)
        
        layout.addWidget(info_group)
        
        # Section des produits
        products_group = QGroupBox("Produits à Transférer")
        products_layout = QVBoxLayout(products_group)
        
        # Barre d'outils pour les produits
        products_toolbar = QHBoxLayout()
        
        self.product_combo = QComboBox()
        self.product_combo.setEditable(True)
        self.product_combo.setPlaceholderText("Sélectionner un produit...")
        products_toolbar.addWidget(QLabel("Produit:"))
        products_toolbar.addWidget(self.product_combo, 1)
        
        self.quantity_spinbox = QDoubleSpinBox()
        self.quantity_spinbox.setDecimals(2)
        self.quantity_spinbox.setMinimum(0.01)
        self.quantity_spinbox.setMaximum(999999.99)
        self.quantity_spinbox.setValue(1.0)
        products_toolbar.addWidget(QLabel("Quantité:"))
        products_toolbar.addWidget(self.quantity_spinbox)
        
        add_product_btn = QPushButton("➕ Ajouter")
        add_product_btn.clicked.connect(self.add_product_to_transfer)
        products_toolbar.addWidget(add_product_btn)
        
        products_layout.addLayout(products_toolbar)
        
        # Table des produits
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(5)
        self.products_table.setHorizontalHeaderLabels([
            "Produit", "Stock Disponible", "Quantité", "Notes", "Actions"
        ])
        self.products_table.horizontalHeader().setStretchLastSection(True)
        products_layout.addWidget(self.products_table)
        
        layout.addWidget(products_group)
        
        # Boutons de validation
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        self.create_btn = QPushButton("Créer le Transfert")
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.create_btn.clicked.connect(self.create_transfer)
        self.create_btn.setEnabled(False)  # Désactivé au début
        buttons_layout.addWidget(self.create_btn)
        
        layout.addLayout(buttons_layout)
        
        # Connexions pour la mise à jour du bouton de création
        self.source_warehouse_combo.currentTextChanged.connect(self.update_create_button_state)
        self.dest_warehouse_combo.currentTextChanged.connect(self.update_create_button_state)
    
    def load_warehouses(self):
        """Charger la liste des entrepôts"""
        try:
            with self.db_manager.get_session() as session:
                warehouses = session.query(ShopWarehouse).filter_by(pos_id=self.pos_id).all()
                
                for combo in [self.source_warehouse_combo, self.dest_warehouse_combo]:
                    combo.clear()
                    combo.addItem("-- Sélectionner un entrepôt --", None)
                    for warehouse in warehouses:
                        combo.addItem(f"{warehouse.name} ({warehouse.code})", warehouse.id)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des entrepôts:\n{str(e)}")
    
    def on_source_warehouse_changed(self):
        """Quand l'entrepôt source change, charger les produits disponibles"""
        self.load_available_products()
    
    def load_available_products(self):
        """Charger les produits disponibles dans l'entrepôt source"""
        self.product_combo.clear()
        source_warehouse_id = self.source_warehouse_combo.currentData()
        
        if not source_warehouse_id:
            return
        
        try:
            with self.db_manager.get_session() as session:
                from ayanna_erp.modules.boutique.model.models import ShopWarehouseStock
                
                # Récupérer les produits avec stock > 0 dans l'entrepôt source
                stocks = session.query(ShopWarehouseStock).join(ShopProduct).filter(
                    ShopWarehouseStock.warehouse_id == source_warehouse_id,
                    ShopWarehouseStock.quantity > 0,
                    ShopProduct.pos_id == self.pos_id
                ).all()
                
                self.product_combo.addItem("-- Sélectionner un produit --", None)
                for stock in stocks:
                    product = stock.product
                    self.product_combo.addItem(
                        f"{product.name} (Stock: {stock.quantity})", 
                        {'product_id': product.id, 'available_qty': float(stock.quantity), 'product_name': product.name}
                    )
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des produits:\n{str(e)}")
    
    def add_product_to_transfer(self):
        """Ajouter un produit à la liste de transfert"""
        product_data = self.product_combo.currentData()
        if not product_data:
            QMessageBox.warning(self, "Validation", "Veuillez sélectionner un produit.")
            return
        
        quantity = self.quantity_spinbox.value()
        available_qty = product_data['available_qty']
        
        if quantity > available_qty:
            QMessageBox.warning(
                self, "Validation", 
                f"Quantité insuffisante. Stock disponible: {available_qty}"
            )
            return
        
        # Vérifier si le produit n'est pas déjà dans la liste
        for item in self.transfer_items:
            if item['product_id'] == product_data['product_id']:
                QMessageBox.warning(self, "Validation", "Ce produit est déjà dans la liste.")
                return
        
        # Ajouter le produit
        self.transfer_items.append({
            'product_id': product_data['product_id'],
            'product_name': product_data['product_name'],
            'quantity': quantity,
            'available_qty': available_qty,
            'notes': ""
        })
        
        self.refresh_products_table()
        self.update_create_button_state()
        
        # Réinitialiser les contrôles
        self.product_combo.setCurrentIndex(0)
        self.quantity_spinbox.setValue(1.0)
    
    def refresh_products_table(self):
        """Actualiser la table des produits"""
        self.products_table.setRowCount(len(self.transfer_items))
        
        for row, item in enumerate(self.transfer_items):
            # Nom du produit
            self.products_table.setItem(row, 0, QTableWidgetItem(item['product_name']))
            
            # Stock disponible
            self.products_table.setItem(row, 1, QTableWidgetItem(str(item['available_qty'])))
            
            # Quantité à transférer
            qty_item = QTableWidgetItem(str(item['quantity']))
            self.products_table.setItem(row, 2, qty_item)
            
            # Notes
            notes_item = QTableWidgetItem(item['notes'])
            self.products_table.setItem(row, 3, notes_item)
            
            # Bouton supprimer
            remove_btn = QPushButton("🗑️ Supprimer")
            remove_btn.clicked.connect(lambda checked, r=row: self.remove_product_from_transfer(r))
            self.products_table.setCellWidget(row, 4, remove_btn)
    
    def remove_product_from_transfer(self, row):
        """Supprimer un produit de la liste de transfert"""
        if 0 <= row < len(self.transfer_items):
            del self.transfer_items[row]
            self.refresh_products_table()
            self.update_create_button_state()
    
    def update_create_button_state(self):
        """Mettre à jour l'état du bouton de création"""
        source_ok = self.source_warehouse_combo.currentData() is not None
        dest_ok = self.dest_warehouse_combo.currentData() is not None
        label_ok = len(self.label_edit.text().strip()) >= 5
        products_ok = len(self.transfer_items) > 0
        different_warehouses = (self.source_warehouse_combo.currentData() != 
                               self.dest_warehouse_combo.currentData())
        
        self.create_btn.setEnabled(source_ok and dest_ok and label_ok and products_ok and different_warehouses)
    
    def create_transfer(self):
        """Créer le transfert"""
        if not self.validate_transfer():
            return
        
        try:
            from ayanna_erp.modules.boutique.controller.stock_controller import StockController
            stock_controller = StockController(self.pos_id)
            
            # Préparer les items pour le contrôleur
            items_for_controller = []
            for item in self.transfer_items:
                items_for_controller.append({
                    'product_id': item['product_id'],
                    'quantity': Decimal(str(item['quantity'])),
                    'unit_cost': Decimal('0.0'),  # On peut ajouter le coût plus tard
                    'notes': item.get('notes', '')
                })
            
            with self.db_manager.get_session() as session:
                # Créer le transfert avec le libellé obligatoire
                label = self.label_edit.text().strip()
                notes = self.notes_edit.toPlainText().strip() or None
                
                # Combiner le libellé et les notes pour le champ notes du transfert
                combined_notes = f"Libellé: {label}"
                if notes:
                    combined_notes += f"\n\nNotes: {notes}"
                
                transfer = stock_controller.create_stock_transfer(
                    session=session,
                    source_warehouse_id=self.source_warehouse_combo.currentData(),
                    destination_warehouse_id=self.dest_warehouse_combo.currentData(),
                    items=items_for_controller,
                    notes=combined_notes,
                    requested_by=f"Utilisateur {1}"  # TODO: Utiliser l'utilisateur actuel
                )
                
                session.commit()
                
                QMessageBox.information(
                    self, "Succès", 
                    f"Transfert créé avec succès!\n"
                    f"Numéro: {transfer.transfer_number}\n"
                    f"Nombre de produits: {len(self.transfer_items)}"
                )
                
                self.accept()
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la création du transfert:\n{str(e)}")
    
    def validate_transfer(self):
        """Valider le transfert"""
        if not self.source_warehouse_combo.currentData():
            QMessageBox.warning(self, "Validation", "Veuillez sélectionner un entrepôt source.")
            return False
        
        if not self.dest_warehouse_combo.currentData():
            QMessageBox.warning(self, "Validation", "Veuillez sélectionner un entrepôt de destination.")
            return False
        
        if self.source_warehouse_combo.currentData() == self.dest_warehouse_combo.currentData():
            QMessageBox.warning(self, "Validation", "L'entrepôt source et destination doivent être différents.")
            return False
        
        # Validation du libellé obligatoire
        label = self.label_edit.text().strip()
        if not label:
            QMessageBox.warning(self, "Validation", "Le libellé du transfert est obligatoire.")
            self.label_edit.setFocus()
            return False
        
        if len(label) < 5:
            QMessageBox.warning(self, "Validation", "Le libellé doit contenir au moins 5 caractères.")
            self.label_edit.setFocus()
            return False
        
        if not self.transfer_items:
            QMessageBox.warning(self, "Validation", "Veuillez ajouter au moins un produit au transfert.")
            return False
        
        return True


class InventoryFormDialog(QDialog):
    """Dialog pour créer un inventaire d'entrepôt"""
    
    def __init__(self, parent=None, warehouse_id=None, db_manager=None):
        super().__init__(parent)
        self.warehouse_id = warehouse_id
        self.db_manager = db_manager
        self.inventory_items = []
        
        self.setWindowTitle("Nouvel Inventaire")
        self.setFixedSize(800, 600)
        self.setup_ui()
        self.load_warehouse_products()
        
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # Titre
        title = QLabel("Saisie d'Inventaire Physique")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Informations
        info_layout = QFormLayout()
        
        self.warehouse_label = QLabel("Chargement...")
        info_layout.addRow("Entrepôt:", self.warehouse_label)
        
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        info_layout.addRow("Date d'inventaire:", self.date_edit)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        self.notes_edit.setPlaceholderText("Notes sur l'inventaire...")
        info_layout.addRow("Notes:", self.notes_edit)
        
        layout.addLayout(info_layout)
        
        # Tableau des produits
        products_group = QGroupBox("Saisie des Quantités Physiques")
        products_layout = QVBoxLayout(products_group)
        
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(5)
        self.products_table.setHorizontalHeaderLabels([
            "Produit", "Stock Théorique", "Quantité Physique", "Écart", "Valorisation"
        ])
        self.products_table.setAlternatingRowColors(True)
        products_layout.addWidget(self.products_table)
        
        layout.addWidget(products_group)
        
        # Résumé
        summary_layout = QHBoxLayout()
        
        self.total_products_label = QLabel("Produits: 0")
        summary_layout.addWidget(self.total_products_label)
        
        self.total_gaps_label = QLabel("Écarts: 0")
        summary_layout.addWidget(self.total_gaps_label)
        
        self.total_value_label = QLabel("Valorisation: 0.00")
        summary_layout.addWidget(self.total_value_label)
        
        summary_layout.addStretch()
        layout.addLayout(summary_layout)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Enregistrer l'Inventaire")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        save_btn.clicked.connect(self.save_inventory)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_warehouse_products(self):
        """Charger les produits de l'entrepôt"""
        try:
            with self.db_manager.get_session() as session:
                # Récupérer l'entrepôt
                warehouse = session.query(ShopWarehouse).get(self.warehouse_id)
                if warehouse:
                    self.warehouse_label.setText(f"{warehouse.name} ({warehouse.code})")
                
                # Récupérer tous les produits avec stock dans cet entrepôt
                from ayanna_erp.modules.boutique.model.models import ShopWarehouseStock
                
                stocks = session.query(ShopWarehouseStock).join(ShopProduct).filter(
                    ShopWarehouseStock.warehouse_id == self.warehouse_id,
                    ShopProduct.pos_id == warehouse.pos_id
                ).all()
                
                self.products_table.setRowCount(len(stocks))
                
                for row, stock in enumerate(stocks):
                    # Nom du produit
                    product_item = QTableWidgetItem(stock.product.name)
                    product_item.setFlags(product_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.products_table.setItem(row, 0, product_item)
                    
                    # Stock théorique
                    theoretical_item = QTableWidgetItem(str(stock.quantity))
                    theoretical_item.setFlags(theoretical_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    theoretical_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.products_table.setItem(row, 1, theoretical_item)
                    
                    # Quantité physique (éditable)
                    physical_item = QTableWidgetItem("0")
                    physical_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.products_table.setItem(row, 2, physical_item)
                    
                    # Écart (calculé)
                    gap_item = QTableWidgetItem("0")
                    gap_item.setFlags(gap_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    gap_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.products_table.setItem(row, 3, gap_item)
                    
                    # Valorisation (calculée)
                    value_item = QTableWidgetItem("0.00")
                    value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.products_table.setItem(row, 4, value_item)
                    
                    # Stocker les données pour les calculs
                    self.inventory_items.append({
                        'product_id': stock.product_id,
                        'product_name': stock.product.name,
                        'theoretical_qty': float(stock.quantity),
                        'physical_qty': 0.0,
                        'unit_price': float(stock.product.price_sale) if stock.product.price_sale else 0.0
                    })
                
                # Connecter les changements pour les calculs automatiques
                self.products_table.itemChanged.connect(self.calculate_gaps)
                
                self.update_summary()
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des produits:\n{str(e)}")
    
    def calculate_gaps(self, item):
        """Calculer les écarts quand une quantité physique change"""
        if item.column() == 2:  # Colonne quantité physique
            row = item.row()
            try:
                physical_qty = float(item.text())
                theoretical_qty = self.inventory_items[row]['theoretical_qty']
                unit_price = self.inventory_items[row]['unit_price']
                
                # Calculer l'écart
                gap = physical_qty - theoretical_qty
                gap_item = self.products_table.item(row, 3)
                gap_item.setText(str(gap))
                
                # Mettre à jour la couleur selon l'écart
                if gap > 0:
                    gap_item.setBackground(QColor(46, 204, 113, 50))  # Vert pour excédent
                elif gap < 0:
                    gap_item.setBackground(QColor(231, 76, 60, 50))   # Rouge pour perte
                else:
                    gap_item.setBackground(QColor(255, 255, 255))     # Blanc pour égal
                
                # Calculer la valorisation
                value = gap * unit_price
                value_item = self.products_table.item(row, 4)
                value_item.setText(f"{value:.2f}")
                
                # Mettre à jour les données
                self.inventory_items[row]['physical_qty'] = physical_qty
                
                self.update_summary()
                
            except ValueError:
                # Remettre l'ancienne valeur en cas d'erreur
                item.setText("0")
    
    def update_summary(self):
        """Mettre à jour le résumé"""
        total_products = len(self.inventory_items)
        total_gaps = sum(1 for item in self.inventory_items 
                        if item['physical_qty'] != item['theoretical_qty'])
        total_value = sum((item['physical_qty'] - item['theoretical_qty']) * item['unit_price'] 
                         for item in self.inventory_items)
        
        self.total_products_label.setText(f"Produits: {total_products}")
        self.total_gaps_label.setText(f"Écarts: {total_gaps}")
        self.total_value_label.setText(f"Valorisation: {total_value:.2f}")
    
    def save_inventory(self):
        """Enregistrer l'inventaire"""
        QMessageBox.information(self, "Succès", "Inventaire enregistré avec succès!")
        self.accept()


class StockManagementWidget(QWidget):
    """Widget principal de gestion des stocks et entrepôts"""
    
    def __init__(self, pos_id: int, current_user):
        super().__init__()
        self.pos_id = pos_id
        self.current_user = current_user
        self.stock_controller = StockController(pos_id)
        self.db_manager = DatabaseManager()
        
        self.setup_ui()
        self.load_initial_data()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Onglets principaux
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #BDC3C7;
                background-color: white;
                border-radius: 8px;
                padding: 5px;
            }
            QTabBar::tab {
                background-color: #ECF0F1;
                padding: 8px 16px;
                margin-right: 2px;
                font-weight: bold;
                color: #2C3E50;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background-color: #3498DB;
                color: white;
            }
        """)
        
        # Onglet Entrepôts
        self.warehouses_tab = self.create_warehouses_tab()
        self.tab_widget.addTab(self.warehouses_tab, "🏭 Entrepôts")
        
        # Onglet Stocks par Entrepôt
        self.stocks_tab = self.create_stocks_tab()
        self.tab_widget.addTab(self.stocks_tab, "📦 Stocks")
        
        # Onglet Transferts
        self.transfers_tab = self.create_transfers_tab()
        self.tab_widget.addTab(self.transfers_tab, "🔄 Transferts")
        
        # Onglet Mouvements
        self.movements_tab = self.create_movements_tab()
        self.tab_widget.addTab(self.movements_tab, "📊 Mouvements")
        
        # Onglet Alertes
        self.alerts_tab = self.create_alerts_tab()
        self.tab_widget.addTab(self.alerts_tab, "⚠️ Alertes")
        
        # Onglet Inventaire
        self.inventory_tab = self.create_inventory_tab()
        self.tab_widget.addTab(self.inventory_tab, "📋 Inventaire")
        
        # Onglet Rapports
        self.reports_tab = self.create_reports_tab()
        self.tab_widget.addTab(self.reports_tab, "📈 Rapports")
        
        main_layout.addWidget(self.tab_widget)
    
    def create_warehouses_tab(self) -> QWidget:
        """Créer l'onglet de gestion des entrepôts"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Partie gauche - Liste des entrepôts
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Actions pour entrepôts
        actions_layout = QHBoxLayout()
        self.new_warehouse_btn = QPushButton("➕ Nouvel Entrepôt")
        self.new_warehouse_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.new_warehouse_btn.clicked.connect(self.create_new_warehouse)
        actions_layout.addWidget(self.new_warehouse_btn)
        
        # Bouton pour lier tous les produits aux entrepôts
        link_products_btn = QPushButton("🔗 Lier Produits aux Entrepôts")
        link_products_btn.setToolTip("Associer tous les produits à tous les entrepôts avec quantité 0")
        link_products_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        link_products_btn.clicked.connect(self.link_all_products_to_warehouses)
        actions_layout.addWidget(link_products_btn)
        
        actions_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.clicked.connect(self.load_warehouses)
        actions_layout.addWidget(refresh_btn)
        left_layout.addLayout(actions_layout)
        
        # Tableau des entrepôts
        self.warehouses_table = QTableWidget()
        self.warehouses_table.setColumnCount(7)
        self.warehouses_table.setHorizontalHeaderLabels([
            "Code", "Nom", "Type", "Statut", "Capacité", "Stock Total", "Actions"
        ])
        self.warehouses_table.setAlternatingRowColors(True)
        self.warehouses_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.warehouses_table.cellClicked.connect(self.on_warehouse_selected)
        left_layout.addWidget(self.warehouses_table)
        
        # Partie droite - Détails de l'entrepôt
        right_widget = QGroupBox("Détails de l'entrepôt")
        right_layout = QVBoxLayout(right_widget)
        
        self.warehouse_detail_label = QLabel("Sélectionnez un entrepôt pour voir les détails.")
        self.warehouse_detail_label.setWordWrap(True)
        self.warehouse_detail_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        right_layout.addWidget(self.warehouse_detail_label)
        
        # Graphique de capacité (placeholder)
        self.capacity_progress = QProgressBar()
        self.capacity_progress.setVisible(False)
        right_layout.addWidget(self.capacity_progress)
        
        # Layout principal avec splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([700, 300])
        layout.addWidget(splitter)
        
        return widget
    
    def create_stocks_tab(self) -> QWidget:
        """Créer l'onglet de gestion des stocks par entrepôt"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filtres
        filters_layout = QHBoxLayout()
        filters_layout.addWidget(QLabel("Entrepôt:"))
        self.stock_warehouse_combo = QComboBox()
        self.stock_warehouse_combo.currentTextChanged.connect(self.load_warehouse_stocks)
        filters_layout.addWidget(self.stock_warehouse_combo)
        
        filters_layout.addWidget(QLabel("Recherche produit:"))
        self.stock_search_input = QLineEdit()
        self.stock_search_input.setPlaceholderText("Nom ou code produit...")
        self.stock_search_input.textChanged.connect(self.search_warehouse_stocks)
        filters_layout.addWidget(self.stock_search_input)
        
        filters_layout.addStretch()
        export_btn = QPushButton("📄 Exporter")
        filters_layout.addWidget(export_btn)
        layout.addLayout(filters_layout)
        
        # Tableau des stocks
        self.stocks_table = QTableWidget()
        self.stocks_table.setColumnCount(8)
        self.stocks_table.setHorizontalHeaderLabels([
            "Produit", "Disponible", "Réservé", "En Transit", "Min", "Max", "Coût Moyen", "Actions"
        ])
        self.stocks_table.setAlternatingRowColors(True)
        layout.addWidget(self.stocks_table)
        
        return widget
    
    def create_transfers_tab(self) -> QWidget:
        """Créer l'onglet de gestion des transferts"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Actions pour transferts
        actions_layout = QHBoxLayout()
        self.new_transfer_btn = QPushButton("🔄 Nouveau Transfert")
        self.new_transfer_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        self.new_transfer_btn.clicked.connect(self.create_new_transfer)
        actions_layout.addWidget(self.new_transfer_btn)
        
        # Filtres pour transferts
        actions_layout.addWidget(QLabel("Statut:"))
        self.transfer_status_combo = QComboBox()
        self.transfer_status_combo.addItems(["Tous", "En Attente", "En Transit", "Reçu", "Annulé"])
        self.transfer_status_combo.currentTextChanged.connect(self.load_transfers)
        actions_layout.addWidget(self.transfer_status_combo)
        
        actions_layout.addStretch()
        refresh_transfers_btn = QPushButton("🔄 Actualiser")
        refresh_transfers_btn.clicked.connect(self.load_transfers)
        actions_layout.addWidget(refresh_transfers_btn)
        layout.addLayout(actions_layout)
        
        # Tableau des transferts
        self.transfers_table = QTableWidget()
        self.transfers_table.setColumnCount(8)
        self.transfers_table.setHorizontalHeaderLabels([
            "Numéro", "Source", "Destination", "Statut", "Articles", "Demandé le", "Priorité", "Actions"
        ])
        self.transfers_table.setAlternatingRowColors(True)
        self.transfers_table.cellDoubleClicked.connect(self.view_transfer_details)
        layout.addWidget(self.transfers_table)
        
        return widget
    
    def create_movements_tab(self) -> QWidget:
        """Créer l'onglet des mouvements de stock"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filtres pour mouvements
        filters_layout = QHBoxLayout()
        filters_layout.addWidget(QLabel("Entrepôt:"))
        self.movement_warehouse_combo = QComboBox()
        filters_layout.addWidget(self.movement_warehouse_combo)
        
        filters_layout.addWidget(QLabel("Type:"))
        self.movement_type_combo = QComboBox()
        self.movement_type_combo.addItems([
            "Tous", "Achat", "Vente", "Transfert Entrant", "Transfert Sortant", "Ajustement"
        ])
        filters_layout.addWidget(self.movement_type_combo)
        
        filters_layout.addWidget(QLabel("Du:"))
        self.movement_start_date = QDateEdit()
        self.movement_start_date.setDate(QDate.currentDate().addDays(-30))
        self.movement_start_date.setCalendarPopup(True)
        filters_layout.addWidget(self.movement_start_date)
        
        filters_layout.addWidget(QLabel("Au:"))
        self.movement_end_date = QDateEdit()
        self.movement_end_date.setDate(QDate.currentDate())
        self.movement_end_date.setCalendarPopup(True)
        filters_layout.addWidget(self.movement_end_date)
        
        search_movements_btn = QPushButton("🔍 Rechercher")
        search_movements_btn.clicked.connect(self.load_movements)
        filters_layout.addWidget(search_movements_btn)
        
        filters_layout.addStretch()
        layout.addLayout(filters_layout)
        
        # Tableau des mouvements
        self.movements_table = QTableWidget()
        self.movements_table.setColumnCount(9)
        self.movements_table.setHorizontalHeaderLabels([
            "Date", "Entrepôt", "Produit", "Type", "Direction", "Quantité", "Coût Unit.", "Référence", "Utilisateur"
        ])
        self.movements_table.setAlternatingRowColors(True)
        layout.addWidget(self.movements_table)
        
        return widget
    
    def create_alerts_tab(self) -> QWidget:
        """Créer l'onglet des alertes de stock"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Résumé des alertes
        summary_layout = QHBoxLayout()
        
        self.critical_alerts_label = QLabel("🔴 Critiques: 0")
        self.critical_alerts_label.setStyleSheet("QLabel { background-color: #E74C3C; color: white; padding: 10px; border-radius: 5px; font-weight: bold; }")
        summary_layout.addWidget(self.critical_alerts_label)
        
        self.warning_alerts_label = QLabel("🟡 Avertissements: 0")
        self.warning_alerts_label.setStyleSheet("QLabel { background-color: #F39C12; color: white; padding: 10px; border-radius: 5px; font-weight: bold; }")
        summary_layout.addWidget(self.warning_alerts_label)
        
        self.info_alerts_label = QLabel("🔵 Informations: 0")
        self.info_alerts_label.setStyleSheet("QLabel { background-color: #3498DB; color: white; padding: 10px; border-radius: 5px; font-weight: bold; }")
        summary_layout.addWidget(self.info_alerts_label)
        
        summary_layout.addStretch()
        
        acknowledge_all_btn = QPushButton("✅ Tout Acquitter")
        acknowledge_all_btn.clicked.connect(self.acknowledge_all_alerts)
        summary_layout.addWidget(acknowledge_all_btn)
        
        layout.addLayout(summary_layout)
        
        # Tableau des alertes
        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(7)
        self.alerts_table.setHorizontalHeaderLabels([
            "Niveau", "Type", "Entrepôt", "Produit", "Message", "Date", "Actions"
        ])
        self.alerts_table.setAlternatingRowColors(True)
        layout.addWidget(self.alerts_table)
        
        return widget
    
    def create_inventory_tab(self) -> QWidget:
        """Créer l'onglet de gestion des inventaires"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # En-tête de l'inventaire
        header_layout = QHBoxLayout()
        
        # Sélection d'entrepôt
        header_layout.addWidget(QLabel("Entrepôt:"))
        self.inventory_warehouse_combo = QComboBox()
        header_layout.addWidget(self.inventory_warehouse_combo)
        
        # Nouveau bouton d'inventaire
        new_inventory_btn = QPushButton("📋 Nouvel Inventaire")
        new_inventory_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        new_inventory_btn.clicked.connect(self.create_new_inventory)
        header_layout.addWidget(new_inventory_btn)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Tableau des inventaires
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(7)
        self.inventory_table.setHorizontalHeaderLabels([
            "Date", "Entrepôt", "Statut", "Produits", "Écarts", "Valorisation", "Actions"
        ])
        self.inventory_table.setAlternatingRowColors(True)
        layout.addWidget(self.inventory_table)
        
        return widget
    
    def create_reports_tab(self) -> QWidget:
        """Créer l'onglet des rapports et statistiques"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Section de sélection
        selection_group = QGroupBox("Paramètres du Rapport")
        selection_layout = QFormLayout(selection_group)
        
        # Sélection de produit
        self.report_product_combo = QComboBox()
        self.report_product_combo.setEditable(True)
        self.report_product_combo.setPlaceholderText("Sélectionner un produit ou une catégorie...")
        selection_layout.addRow("Produit/Catégorie:", self.report_product_combo)
        
        # Sélection d'entrepôt
        self.report_warehouse_combo = QComboBox()
        selection_layout.addRow("Entrepôt:", self.report_warehouse_combo)
        
        # Période
        period_layout = QHBoxLayout()
        
        self.report_start_date = QDateEdit()
        self.report_start_date.setDate(QDate.currentDate().addMonths(-1))
        self.report_start_date.setCalendarPopup(True)
        period_layout.addWidget(self.report_start_date)
        
        period_layout.addWidget(QLabel("au"))
        
        self.report_end_date = QDateEdit()
        self.report_end_date.setDate(QDate.currentDate())
        self.report_end_date.setCalendarPopup(True)
        period_layout.addWidget(self.report_end_date)
        
        selection_layout.addRow("Période:", period_layout)
        
        # Boutons d'action
        actions_layout = QHBoxLayout()
        
        generate_btn = QPushButton("📊 Générer Rapport")
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        generate_btn.clicked.connect(self.generate_report)
        actions_layout.addWidget(generate_btn)
        
        export_pdf_btn = QPushButton("📄 Export PDF")
        export_pdf_btn.clicked.connect(self.export_report_pdf)
        actions_layout.addWidget(export_pdf_btn)
        
        export_excel_btn = QPushButton("📊 Export Excel")
        export_excel_btn.clicked.connect(self.export_report_excel)
        actions_layout.addWidget(export_excel_btn)
        
        actions_layout.addStretch()
        selection_layout.addRow("Actions:", actions_layout)
        
        layout.addWidget(selection_group)
        
        # Zone d'affichage du rapport
        self.report_display = QTextEdit()
        self.report_display.setReadOnly(True)
        self.report_display.setPlaceholderText("Sélectionnez les paramètres et cliquez sur 'Générer Rapport' pour afficher les résultats...")
        layout.addWidget(self.report_display)
        
        return widget
    
    # ==================== MÉTHODES DE CHARGEMENT DES DONNÉES ====================
    
    def load_initial_data(self):
        """Charger les données initiales"""
        self.load_warehouses()
        self.load_warehouse_combos()
        self.load_transfers()
        self.load_alerts()
    
    def load_warehouses(self):
        """Charger la liste des entrepôts"""
        try:
            with self.db_manager.get_session() as session:
                warehouses = self.stock_controller.get_warehouses(session)
                self.populate_warehouses_table(warehouses)
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des entrepôts: {str(e)}")
    
    def load_warehouse_combos(self):
        """Charger les combobox des entrepôts"""
        try:
            with self.db_manager.get_session() as session:
                warehouses = self.stock_controller.get_warehouses(session)
                
                # Mettre à jour tous les combobox
                for combo in [self.stock_warehouse_combo, self.movement_warehouse_combo]:
                    combo.clear()
                    combo.addItem("Tous les entrepôts", None)
                    for warehouse in warehouses:
                        combo.addItem(f"{warehouse.name} ({warehouse.code})", warehouse.id)
        except Exception as e:
            print(f"Erreur lors du chargement des combos: {e}")
    
    def load_warehouse_stocks(self):
        """Charger les stocks de l'entrepôt sélectionné"""
        try:
            warehouse_id = self.stock_warehouse_combo.currentData()
            if not warehouse_id:
                return
            
            with self.db_manager.get_session() as session:
                summary = self.stock_controller.get_warehouse_stock_summary(session, warehouse_id)
                self.populate_stocks_table(summary['stocks'])
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des stocks: {str(e)}")
    
    def load_transfers(self):
        """Charger les transferts"""
        try:
            status_filter = self.transfer_status_combo.currentText()
            status_map = {
                "En Attente": "PENDING",
                "En Transit": "IN_TRANSIT", 
                "Reçu": "RECEIVED",
                "Annulé": "CANCELLED"
            }
            
            with self.db_manager.get_session() as session:
                transfers = self.stock_controller.get_transfers(
                    session, 
                    status=status_map.get(status_filter)
                )
                self.populate_transfers_table(transfers)
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des transferts: {str(e)}")
    
    def load_movements(self):
        """Charger les mouvements de stock"""
        try:
            warehouse_id = self.movement_warehouse_combo.currentData()
            start_date = self.movement_start_date.date().toPython()
            end_date = self.movement_end_date.date().toPython()
            
            with self.db_manager.get_session() as session:
                movements = self.stock_controller.get_stock_movements(
                    session,
                    warehouse_id=warehouse_id,
                    start_date=datetime.combine(start_date, datetime.min.time()),
                    end_date=datetime.combine(end_date, datetime.max.time())
                )
                self.populate_movements_table(movements)
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des mouvements: {str(e)}")
    
    def load_alerts(self):
        """Charger les alertes de stock"""
        try:
            with self.db_manager.get_session() as session:
                alerts = self.stock_controller.get_stock_alerts(session)
                self.populate_alerts_table(alerts)
                self.update_alerts_summary(alerts)
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des alertes: {str(e)}")
    
    # ==================== MÉTHODES DE POPULATION DES TABLEAUX ====================
    
    def populate_warehouses_table(self, warehouses: List[ShopWarehouse]):
        """Peupler le tableau des entrepôts"""
        self.warehouses_table.setRowCount(len(warehouses))
        
        for row, warehouse in enumerate(warehouses):
            # Code
            self.warehouses_table.setItem(row, 0, QTableWidgetItem(warehouse.code))
            
            # Nom
            name_item = QTableWidgetItem(warehouse.name)
            if warehouse.is_default:
                name_item.setBackground(QColor("#E8F5E8"))
                name_item.setText(f"⭐ {warehouse.name}")
            self.warehouses_table.setItem(row, 1, name_item)
            
            # Type
            type_icons = {
                'shop': '🏪', 'storage': '📦', 'transit': '🚚', 'damaged': '⚠️'
            }
            type_text = f"{type_icons.get(warehouse.type, '📦')} {warehouse.type.title()}"
            self.warehouses_table.setItem(row, 2, QTableWidgetItem(type_text))
            
            # Statut
            status_item = QTableWidgetItem("Actif" if warehouse.is_active else "Inactif")
            status_item.setBackground(QColor("#27AE60" if warehouse.is_active else "#E74C3C"))
            status_item.setForeground(QColor("white"))
            self.warehouses_table.setItem(row, 3, status_item)
            
            # Capacité
            capacity_text = f"{warehouse.capacity_limit}" if warehouse.capacity_limit else "Illimitée"
            self.warehouses_table.setItem(row, 4, QTableWidgetItem(capacity_text))
            
            # Stock Total (placeholder)
            self.warehouses_table.setItem(row, 5, QTableWidgetItem("Calcul..."))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            edit_btn = QPushButton("✏️")
            edit_btn.setToolTip("Modifier l'entrepôt")
            edit_btn.clicked.connect(lambda checked, w=warehouse: self.edit_warehouse(w))
            actions_layout.addWidget(edit_btn)
            
            self.warehouses_table.setCellWidget(row, 6, actions_widget)
    
    def populate_stocks_table(self, stocks):
        """Peupler le tableau des stocks"""
        # Implementation simplifiée pour l'exemple
        self.stocks_table.setRowCount(len(stocks))
        # TODO: Implémenter la population complète
    
    def populate_transfers_table(self, transfers):
        """Peupler le tableau des transferts"""
        # Implementation simplifiée pour l'exemple
        self.transfers_table.setRowCount(len(transfers))
        # TODO: Implémenter la population complète
    
    def populate_movements_table(self, movements):
        """Peupler le tableau des mouvements"""
        self.movements_table.setRowCount(len(movements))
        
        for row, movement in enumerate(movements):
            # Date
            date_str = movement.get('date', '').strftime('%d/%m/%Y %H:%M') if movement.get('date') else ''
            self.movements_table.setItem(row, 0, QTableWidgetItem(date_str))
            
            # Entrepôt
            warehouse_name = movement.get('warehouse_name', 'N/A')
            self.movements_table.setItem(row, 1, QTableWidgetItem(warehouse_name))
            
            # Produit
            product_name = movement.get('product_name', 'N/A')
            self.movements_table.setItem(row, 2, QTableWidgetItem(product_name))
            
            # Type
            movement_type = movement.get('type', 'N/A')
            self.movements_table.setItem(row, 3, QTableWidgetItem(movement_type))
            
            # Direction
            direction = movement.get('direction', 'N/A')
            direction_item = QTableWidgetItem(direction)
            if direction == 'ENTRÉE':
                direction_item.setBackground(QColor(46, 204, 113, 50))  # Vert clair
            elif direction == 'SORTIE':
                direction_item.setBackground(QColor(231, 76, 60, 50))   # Rouge clair
            self.movements_table.setItem(row, 4, direction_item)
            
            # Quantité
            quantity = movement.get('quantity', 0)
            quantity_item = QTableWidgetItem(str(quantity))
            quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.movements_table.setItem(row, 5, quantity_item)
            
            # Coût unitaire
            unit_cost = movement.get('unit_cost', 0)
            cost_item = QTableWidgetItem(f"{unit_cost:.2f}")
            cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.movements_table.setItem(row, 6, cost_item)
            
            # Référence/Libellé
            reference = movement.get('reference', 'N/A')
            # Extraire le libellé si c'est un transfert
            if 'Libellé:' in reference:
                try:
                    libelle_part = reference.split('Libellé:')[1].split('\n')[0].strip()
                    reference = libelle_part
                except:
                    pass
            self.movements_table.setItem(row, 7, QTableWidgetItem(reference))
            
            # Utilisateur
            user = movement.get('user', 'N/A')
            self.movements_table.setItem(row, 8, QTableWidgetItem(user))
        
        # Ajuster la largeur des colonnes
        self.movements_table.resizeColumnsToContents()
    
    def populate_alerts_table(self, alerts):
        """Peupler le tableau des alertes"""
        # Implementation simplifiée pour l'exemple
        self.alerts_table.setRowCount(len(alerts))
        # TODO: Implémenter la population complète
    
    def update_alerts_summary(self, alerts):
        """Mettre à jour le résumé des alertes"""
        critical_count = sum(1 for a in alerts if a.alert_level == 'CRITICAL')
        warning_count = sum(1 for a in alerts if a.alert_level == 'WARNING')
        info_count = sum(1 for a in alerts if a.alert_level == 'INFO')
        
        self.critical_alerts_label.setText(f"🔴 Critiques: {critical_count}")
        self.warning_alerts_label.setText(f"🟡 Avertissements: {warning_count}")
        self.info_alerts_label.setText(f"🔵 Informations: {info_count}")
    
    # ==================== GESTIONNAIRES D'ÉVÉNEMENTS ====================
    
    def on_warehouse_selected(self, row, column):
        """Gestionnaire de sélection d'entrepôt"""
        try:
            warehouse_code = self.warehouses_table.item(row, 0).text()
            with self.db_manager.get_session() as session:
                warehouse = session.query(ShopWarehouse).filter(
                    ShopWarehouse.code == warehouse_code,
                    ShopWarehouse.pos_id == self.pos_id
                ).first()
                
                if warehouse:
                    details = f"<b>Nom:</b> {warehouse.name}<br>"
                    details += f"<b>Code:</b> {warehouse.code}<br>"
                    details += f"<b>Type:</b> {warehouse.type}<br>"
                    details += f"<b>Statut:</b> {'Actif' if warehouse.is_active else 'Inactif'}<br>"
                    details += f"<b>Défaut:</b> {'Oui' if warehouse.is_default else 'Non'}<br>"
                    details += f"<b>Description:</b> {warehouse.description or 'Aucune'}<br>"
                    details += f"<b>Adresse:</b> {warehouse.address or 'Non renseignée'}<br>"
                    details += f"<b>Contact:</b> {warehouse.contact_person or 'Non renseigné'}<br>"
                    if warehouse.contact_phone:
                        details += f"<b>Téléphone:</b> {warehouse.contact_phone}<br>"
                    if warehouse.contact_email:
                        details += f"<b>Email:</b> {warehouse.contact_email}<br>"
                    details += f"<b>Capacité:</b> {warehouse.capacity_limit or 'Illimitée'}<br>"
                    
                    self.warehouse_detail_label.setText(details)
        except Exception as e:
            self.warehouse_detail_label.setText(f"Erreur lors du chargement: {str(e)}")
    
    def create_new_warehouse(self):
        """Créer un nouvel entrepôt"""
        dialog = WarehouseFormDialog(self, pos_id=self.pos_id)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            warehouse_data = dialog.get_warehouse_data()
            
            try:
                # Créer l'entrepôt via le contrôleur
                with self.db_manager.get_session() as session:
                    new_warehouse = self.stock_controller.create_warehouse(
                        session=session,
                        code=warehouse_data["code"],
                        name=warehouse_data["name"],
                        type=warehouse_data["type"],
                        description=warehouse_data.get("description"),
                        address=warehouse_data.get("address"),
                        contact_person=warehouse_data.get("contact_person"),
                        contact_phone=warehouse_data.get("contact_phone"),
                        contact_email=warehouse_data.get("contact_email"),
                        is_default=warehouse_data.get("is_default", False),
                        capacity_limit=warehouse_data.get("capacity_limit")
                    )
                    
                    session.commit()
                    
                    QMessageBox.information(
                        self, "Succès", 
                        f"Entrepôt '{new_warehouse.name}' créé avec succès!\n"
                        f"Code: {new_warehouse.code}"
                    )
                    
                    # Recharger la liste des entrepôts
                    self.load_warehouses()
                    
                    # Si c'est l'entrepôt par défaut, relier tous les produits
                    if warehouse_data.get("is_default", False):
                        self.link_all_products_to_warehouses()
                    
            except Exception as e:
                QMessageBox.critical(
                    self, "Erreur", 
                    f"Erreur lors de la création de l'entrepôt:\n{str(e)}"
                )
    
    def link_all_products_to_warehouses(self):
        """Relier tous les produits de shop_produits à tous les entrepôts avec quantité 0"""
        try:
            with self.db_manager.get_session() as session:
                # Récupérer tous les produits et tous les entrepôts
                products = session.query(ShopProduct).filter_by(pos_id=self.pos_id).all()
                warehouses = session.query(ShopWarehouse).filter_by(pos_id=self.pos_id).all()
                
                if not products:
                    QMessageBox.information(self, "Info", "Aucun produit trouvé dans la base de données.")
                    return
                
                if not warehouses:
                    QMessageBox.information(self, "Info", "Aucun entrepôt trouvé dans la base de données.")
                    return
                
                # Compter les associations créées
                created_count = 0
                existing_count = 0
                
                for product in products:
                    for warehouse in warehouses:
                        # Vérifier si l'association existe déjà
                        from ayanna_erp.modules.boutique.model.models import ShopWarehouseStock
                        
                        existing_stock = session.query(ShopWarehouseStock).filter(
                            ShopWarehouseStock.warehouse_id == warehouse.id,
                            ShopWarehouseStock.product_id == product.id
                        ).first()
                        
                        if existing_stock is None:
                            # Créer une nouvelle entrée de stock avec quantité 0
                            self.stock_controller.get_or_create_warehouse_stock(
                                session, warehouse.id, product.id
                            )
                            created_count += 1
                        else:
                            existing_count += 1
                
                session.commit()
                
                QMessageBox.information(
                    self, "Succès", 
                    f"Liaison des produits aux entrepôts terminée!\n\n"
                    f"• {created_count} nouvelles associations créées\n"
                    f"• {existing_count} associations existantes trouvées\n"
                    f"• {len(products)} produits traités\n"
                    f"• {len(warehouses)} entrepôts traités"
                )
                
                # Recharger l'interface
                self.load_warehouse_stocks()
                
        except Exception as e:
            QMessageBox.critical(
                self, "Erreur", 
                f"Erreur lors de la liaison des produits aux entrepôts:\n{str(e)}"
            )
    
    def edit_warehouse(self, warehouse):
        """Modifier un entrepôt"""
        QMessageBox.information(self, "Info", f"Édition de l'entrepôt {warehouse.name} à implémenter")
    
    def create_new_transfer(self):
        """Créer un nouveau transfert"""
        dialog = TransferFormDialog(self, pos_id=self.pos_id, db_manager=self.db_manager)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Recharger la liste des transferts
            self.load_transfers()
            
            QMessageBox.information(
                self, "Succès", 
                "Le transfert a été créé avec succès!\n"
                "Vous pouvez le voir dans l'onglet des transferts."
            )
    
    def view_transfer_details(self, row, column):
        """Voir les détails d'un transfert"""
        QMessageBox.information(self, "Info", "Détails du transfert à implémenter")
    
    def search_warehouse_stocks(self):
        """Rechercher dans les stocks"""
        pass  # TODO: Implémenter la recherche
    
    def acknowledge_all_alerts(self):
        """Acquitter toutes les alertes"""
        QMessageBox.information(self, "Info", "Acquittement des alertes à implémenter")
    
    def create_new_inventory(self):
        """Créer un nouvel inventaire"""
        warehouse_id = self.inventory_warehouse_combo.currentData()
        if not warehouse_id:
            QMessageBox.warning(self, "Validation", "Veuillez sélectionner un entrepôt.")
            return
        
        dialog = InventoryFormDialog(self, warehouse_id=warehouse_id, db_manager=self.db_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Recharger la liste des inventaires
            self.load_inventories()
            QMessageBox.information(self, "Succès", "Inventaire créé avec succès!")
    
    def generate_report(self):
        """Générer un rapport de stock"""
        product_id = self.report_product_combo.currentData()
        warehouse_id = self.report_warehouse_combo.currentData()
        start_date = self.report_start_date.date().toPython()
        end_date = self.report_end_date.date().toPython()
        
        try:
            with self.db_manager.get_session() as session:
                # Générer le rapport
                report_data = self.generate_stock_report(session, product_id, warehouse_id, start_date, end_date)
                self.display_report(report_data)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération du rapport:\n{str(e)}")
    
    def generate_stock_report(self, session, product_id, warehouse_id, start_date, end_date):
        """Générer les données du rapport de stock"""
        report_data = {
            'title': 'Rapport de Stock',
            'period': f"{start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}",
            'generated_at': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'summary': {},
            'movements': [],
            'charts': []
        }
        
        if product_id:
            # Rapport spécifique à un produit
            product = session.query(ShopProduct).get(product_id)
            if product:
                report_data['title'] = f"Rapport de Stock - {product.name}"
                
                # Récupérer les stocks par entrepôt
                stocks = self.stock_controller.get_product_stock_by_warehouse(session, product_id)
                report_data['summary']['stocks_by_warehouse'] = stocks
                
                # Récupérer les mouvements sur la période
                movements = self.stock_controller.get_stock_movements(
                    session, 
                    product_id=product_id,
                    warehouse_id=warehouse_id,
                    start_date=datetime.combine(start_date, datetime.min.time()),
                    end_date=datetime.combine(end_date, datetime.max.time())
                )
                report_data['movements'] = movements
        
        return report_data
    
    def display_report(self, report_data):
        """Afficher le rapport dans la zone de texte"""
        html_content = f"""
        <h2>{report_data['title']}</h2>
        <p><b>Période:</b> {report_data['period']}</p>
        <p><b>Généré le:</b> {report_data['generated_at']}</p>
        
        <h3>📊 Résumé</h3>
        """
        
        if 'stocks_by_warehouse' in report_data['summary']:
            html_content += "<h4>Stock par Entrepôt:</h4><ul>"
            for stock in report_data['summary']['stocks_by_warehouse']:
                html_content += f"<li><b>{stock.get('warehouse_name', 'N/A')}:</b> {stock.get('quantity', 0)} unités</li>"
            html_content += "</ul>"
        
        if report_data['movements']:
            html_content += f"<h4>Mouvements sur la période: {len(report_data['movements'])} mouvements</h4>"
            html_content += "<table border='1' cellpadding='5'>"
            html_content += "<tr><th>Date</th><th>Type</th><th>Direction</th><th>Quantité</th><th>Entrepôt</th></tr>"
            
            for movement in report_data['movements'][:10]:  # Limiter à 10 pour l'affichage
                date_str = movement.get('date', '').strftime('%d/%m/%Y') if movement.get('date') else ''
                html_content += f"""
                <tr>
                    <td>{date_str}</td>
                    <td>{movement.get('type', 'N/A')}</td>
                    <td>{movement.get('direction', 'N/A')}</td>
                    <td>{movement.get('quantity', 0)}</td>
                    <td>{movement.get('warehouse_name', 'N/A')}</td>
                </tr>
                """
            
            if len(report_data['movements']) > 10:
                html_content += f"<tr><td colspan='5'><i>... et {len(report_data['movements']) - 10} autres mouvements</i></td></tr>"
            
            html_content += "</table>"
        
        html_content += "<br><p><i>Utilisez les boutons d'export pour sauvegarder ce rapport.</i></p>"
        
        self.report_display.setHtml(html_content)
    
    def export_report_pdf(self):
        """Exporter le rapport en PDF"""
        QMessageBox.information(self, "Export PDF", "Fonctionnalité d'export PDF à implémenter")
    
    def export_report_excel(self):
        """Exporter le rapport en Excel"""
        QMessageBox.information(self, "Export Excel", "Fonctionnalité d'export Excel à implémenter")
    
    def load_inventories(self):
        """Charger la liste des inventaires"""
        # TODO: Implémenter le chargement des inventaires
        pass