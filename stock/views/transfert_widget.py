"""
Widget pour la gestion des transferts entre entrepôts
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy import text
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton, 
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, 
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout, QTextEdit, 
    QDoubleSpinBox, QSpinBox, QCheckBox, QTabWidget, QTreeWidget, 
    QTreeWidgetItem, QSplitter, QProgressBar, QFrame, QDateEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QDate
from PyQt6.QtGui import QFont, QColor, QPixmap, QIcon

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.stock.controllers.transfert_controller import TransfertController
from ayanna_erp.modules.stock.models import StockWarehouse


class TransferFormDialog(QDialog):
    """Dialog pour créer un nouveau transfert"""
    
    def __init__(self, parent=None, pos_id=None):
        super().__init__(parent)
        self.pos_id = pos_id
        # Récupérer entreprise_id depuis pos_id
        self.entreprise_id = self.get_entreprise_id_from_pos(pos_id)
        self.controller = TransfertController(self.entreprise_id)
        self.db_manager = DatabaseManager()
        self.transfer_items = []

    def get_entreprise_id_from_pos(self, pos_id):
        """Récupérer l'entreprise_id depuis le pos_id"""
        try:
            with self.db_manager.get_session() as session:
                result = session.execute(text("SELECT enterprise_id FROM core_pos_points WHERE id = :pos_id"), {"pos_id": pos_id})
                row = result.fetchone()
                return row[0] if row else 1  # Par défaut entreprise 1
        except:
            return 1  # Par défaut entreprise 1
        
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
        self.create_btn.setEnabled(False)
        buttons_layout.addWidget(self.create_btn)
        
        layout.addLayout(buttons_layout)
        
        # Connexions pour la mise à jour du bouton de création
        self.source_warehouse_combo.currentTextChanged.connect(self.update_create_button_state)
        self.dest_warehouse_combo.currentTextChanged.connect(self.update_create_button_state)
    
    def load_warehouses(self):
        """Charger la liste des entrepôts"""
        try:
            with self.db_manager.get_session() as session:
                warehouses = session.query(StockWarehouse).filter(
                    StockWarehouse.entreprise_id == self.entreprise_id,
                    StockWarehouse.is_active == True
                ).order_by(StockWarehouse.name).all()
                
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
            # TODO: Adapter à la nouvelle architecture
            self.product_combo.addItem("-- Fonction en cours d'adaptation --", None)
            return
            
            # Code temporairement désactivé - à adapter à la nouvelle architecture
            """
                
                # Récupérer les produits avec stock > 0 dans l'entrepôt source
                stocks = session.query(ShopWarehouseStock).join(ShopProduct).filter(
                    ShopWarehouseStock.warehouse_id == source_warehouse_id,
                    ShopWarehouseStock.quantity > 0,
                    ShopProduct.pos_id == self.pos_id
                ).all()
                
                self.product_combo.addItem("-- Sélectionner un produit --", None)
                for stock in stocks:
                    available_qty = float(stock.quantity) - float(stock.reserved_quantity or 0)
                    if available_qty > 0:
                        self.product_combo.addItem(
                            f"{stock.product.name} (Dispo: {available_qty:.2f})",
                            {
                                'product_id': stock.product_id,
                                'product_name': stock.product.name,
                                'product_code': stock.product.code,
                                'available_qty': available_qty
                            }
                        )
            """
                        
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
            'product_code': product_data['product_code'],
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
            product_text = f"{item['product_name']}"
            if item['product_code']:
                product_text += f" ({item['product_code']})"
            self.products_table.setItem(row, 0, QTableWidgetItem(product_text))
            
            # Stock disponible
            self.products_table.setItem(row, 1, QTableWidgetItem(str(item['available_qty'])))
            
            # Quantité à transférer
            qty_item = QTableWidgetItem(str(item['quantity']))
            self.products_table.setItem(row, 2, qty_item)
            
            # Notes
            notes_item = QTableWidgetItem(item['notes'])
            self.products_table.setItem(row, 3, notes_item)
            
            # Bouton supprimer
            remove_btn = QPushButton("🗑️")
            remove_btn.setToolTip("Supprimer ce produit")
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
            # Préparer les items pour le contrôleur
            items_for_controller = []
            for item in self.transfer_items:
                items_for_controller.append({
                    'product_id': item['product_id'],
                    'quantity': Decimal(str(item['quantity'])),
                    'unit_cost': Decimal('0.0'),  # Sera récupéré du stock
                    'notes': item.get('notes', '')
                })
            
            with self.db_manager.get_session() as session:
                # Créer le transfert
                transfer = self.controller.create_transfer(
                    session=session,
                    source_warehouse_id=self.source_warehouse_combo.currentData(),
                    destination_warehouse_id=self.dest_warehouse_combo.currentData(),
                    items=items_for_controller,
                    label=self.label_edit.text().strip(),
                    notes=self.notes_edit.toPlainText().strip() or None,
                    expected_date=self.expected_date.date().toPython(),
                    requested_by=f"Utilisateur {1}"  # À adapter selon l'utilisateur connecté
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


class TransferDetailDialog(QDialog):
    """Dialog pour afficher les détails d'un transfert"""
    
    def __init__(self, parent=None, transfer_id=None, controller=None):
        super().__init__(parent)
        self.transfer_id = transfer_id
        self.controller = controller
        self.setWindowTitle("Détails du Transfert")
        self.setFixedSize(700, 500)
        self.setup_ui()
        self.load_transfer_details()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # En-tête
        header_layout = QHBoxLayout()
        self.transfer_title = QLabel("Chargement...")
        self.transfer_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(self.transfer_title)
        header_layout.addStretch()
        
        close_btn = QPushButton("❌ Fermer")
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        layout.addLayout(header_layout)
        
        # Informations du transfert
        info_group = QGroupBox("Informations Générales")
        info_layout = QFormLayout(info_group)
        
        self.status_label = QLabel("...")
        info_layout.addRow("Statut:", self.status_label)
        
        self.warehouses_label = QLabel("...")
        info_layout.addRow("Transfert:", self.warehouses_label)
        
        self.dates_label = QLabel("...")
        info_layout.addRow("Dates:", self.dates_label)
        
        self.requester_label = QLabel("...")
        info_layout.addRow("Demandé par:", self.requester_label)
        
        layout.addWidget(info_group)
        
        # Tableau des articles
        items_group = QGroupBox("Articles du Transfert")
        items_layout = QVBoxLayout(items_group)
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels([
            "Produit", "Code", "Demandé", "Expédié", "Reçu", "Notes"
        ])
        self.items_table.setAlternatingRowColors(True)
        items_layout.addWidget(self.items_table)
        
        layout.addWidget(items_group)
        
        # Actions selon le statut
        self.actions_frame = QFrame()
        self.actions_layout = QHBoxLayout(self.actions_frame)
        layout.addWidget(self.actions_frame)
    
    def load_transfer_details(self):
        """Charger les détails du transfert"""
        try:
            with self.controller.db_manager.get_session() as session:
                transfer_data = self.controller.get_transfer_by_id(session, self.transfer_id)
                
                if not transfer_data:
                    QMessageBox.critical(self, "Erreur", "Transfert non trouvé.")
                    self.close()
                    return
                
                # Mise à jour du titre
                self.transfer_title.setText(f"🔄 Transfert {transfer_data['transfer_number']}")
                
                # Mise à jour des informations
                status_icons = {
                    'PENDING': '⏳ En Attente',
                    'IN_TRANSIT': '🚛 En Transit',
                    'RECEIVED': '✅ Reçu',
                    'CANCELLED': '❌ Annulé'
                }
                self.status_label.setText(status_icons.get(transfer_data['status'], transfer_data['status']))
                
                source = transfer_data['source_warehouse']['name']
                dest = transfer_data['destination_warehouse']['name']
                self.warehouses_label.setText(f"{source} → {dest}")
                
                created = transfer_data['created_at'].strftime('%d/%m/%Y %H:%M')
                dates_text = f"Créé: {created}"
                if transfer_data['expected_date']:
                    expected = transfer_data['expected_date'].strftime('%d/%m/%Y')
                    dates_text += f"\nPrévu: {expected}"
                if transfer_data['shipped_date']:
                    shipped = transfer_data['shipped_date'].strftime('%d/%m/%Y %H:%M')
                    dates_text += f"\nExpédié: {shipped}"
                if transfer_data['received_date']:
                    received = transfer_data['received_date'].strftime('%d/%m/%Y %H:%M')
                    dates_text += f"\nReçu: {received}"
                self.dates_label.setText(dates_text)
                
                self.requester_label.setText(transfer_data['requested_by'])
                
                # Remplir le tableau des articles
                self.populate_items_table(transfer_data['items'])
                
                # Configurer les actions selon le statut
                self.setup_actions(transfer_data['status'])
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des détails:\n{str(e)}")
    
    def populate_items_table(self, items):
        """Peupler le tableau des articles"""
        self.items_table.setRowCount(len(items))
        
        for row, item in enumerate(items):
            # Produit
            self.items_table.setItem(row, 0, QTableWidgetItem(item['product_name']))
            
            # Code
            self.items_table.setItem(row, 1, QTableWidgetItem(item['product_code'] or ""))
            
            # Quantité demandée
            requested_item = QTableWidgetItem(f"{item['quantity_requested']:.2f}")
            requested_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.items_table.setItem(row, 2, requested_item)
            
            # Quantité expédiée
            shipped_item = QTableWidgetItem(f"{item['quantity_shipped']:.2f}")
            shipped_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.items_table.setItem(row, 3, shipped_item)
            
            # Quantité reçue
            received_item = QTableWidgetItem(f"{item['quantity_received']:.2f}")
            received_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.items_table.setItem(row, 4, received_item)
            
            # Notes
            self.items_table.setItem(row, 5, QTableWidgetItem(item['notes'] or ""))
        
        self.items_table.resizeColumnsToContents()
    
    def setup_actions(self, status):
        """Configurer les actions selon le statut"""
        # Nettoyer les actions existantes
        for i in reversed(range(self.actions_layout.count())):
            self.actions_layout.itemAt(i).widget().setParent(None)
        
        if status == 'PENDING':
            ship_btn = QPushButton("🚛 Expédier")
            ship_btn.setStyleSheet("background-color: #3498db; color: white; padding: 8px 16px; border-radius: 4px;")
            ship_btn.clicked.connect(self.ship_transfer)
            self.actions_layout.addWidget(ship_btn)
            
            cancel_btn = QPushButton("❌ Annuler")
            cancel_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 8px 16px; border-radius: 4px;")
            cancel_btn.clicked.connect(self.cancel_transfer)
            self.actions_layout.addWidget(cancel_btn)
        
        elif status == 'IN_TRANSIT':
            receive_btn = QPushButton("📦 Recevoir")
            receive_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 8px 16px; border-radius: 4px;")
            receive_btn.clicked.connect(self.receive_transfer)
            self.actions_layout.addWidget(receive_btn)
        
        self.actions_layout.addStretch()
    
    def ship_transfer(self):
        """Expédier le transfert"""
        reply = QMessageBox.question(
            self, "Confirmation",
            "Confirmer l'expédition de ce transfert?\n\n"
            "Cette action va retirer les produits du stock source.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with self.controller.db_manager.get_session() as session:
                    self.controller.update_transfer_status(session, self.transfer_id, 'IN_TRANSIT')
                    session.commit()
                    
                    QMessageBox.information(self, "Succès", "Transfert expédié avec succès!")
                    self.load_transfer_details()
                    
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'expédition:\n{str(e)}")
    
    def receive_transfer(self):
        """Recevoir le transfert"""
        reply = QMessageBox.question(
            self, "Confirmation",
            "Confirmer la réception de ce transfert?\n\n"
            "Cette action va ajouter les produits au stock destination.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with self.controller.db_manager.get_session() as session:
                    self.controller.update_transfer_status(session, self.transfer_id, 'RECEIVED')
                    session.commit()
                    
                    QMessageBox.information(self, "Succès", "Transfert reçu avec succès!")
                    self.load_transfer_details()
                    
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la réception:\n{str(e)}")
    
    def cancel_transfer(self):
        """Annuler le transfert"""
        reply = QMessageBox.question(
            self, "Confirmation",
            "Confirmer l'annulation de ce transfert?\n\n"
            "Cette action va libérer les réservations de stock.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with self.controller.db_manager.get_session() as session:
                    self.controller.update_transfer_status(session, self.transfer_id, 'CANCELLED')
                    session.commit()
                    
                    QMessageBox.information(self, "Succès", "Transfert annulé avec succès!")
                    self.load_transfer_details()
                    
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'annulation:\n{str(e)}")


class TransfertWidget(QWidget):
    """Widget principal pour la gestion des transferts"""
    
    # Signaux
    transfer_created = pyqtSignal()  # Quand un transfert est créé
    transfer_updated = pyqtSignal()  # Quand un transfert est mis à jour
    
    def __init__(self, pos_id: int, current_user):
        super().__init__()
        self.pos_id = pos_id
        self.current_user = current_user
        # Récupérer entreprise_id depuis pos_id
        self.entreprise_id = self.get_entreprise_id_from_pos(pos_id)
        self.controller = TransfertController(self.entreprise_id)
        self.db_manager = DatabaseManager()
        self.current_transfers = []
        
        self.setup_ui()
        self.load_data()

    def get_entreprise_id_from_pos(self, pos_id):
        """Récupérer l'entreprise_id depuis le pos_id"""
        try:
            with self.db_manager.get_session() as session:
                result = session.execute(text("SELECT enterprise_id FROM core_pos_points WHERE id = :pos_id"), {"pos_id": pos_id})
                row = result.fetchone()
                return row[0] if row else 1  # Par défaut entreprise 1
        except:
            return 1  # Par défaut entreprise 1
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # En-tête
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🔄 Gestion des Transferts")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Actions
        self.new_transfer_btn = QPushButton("➕ Nouveau Transfert")
        self.new_transfer_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        self.new_transfer_btn.clicked.connect(self.create_new_transfer)
        header_layout.addWidget(self.new_transfer_btn)
        
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.clicked.connect(self.load_data)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Statistiques rapides
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        stats_layout = QHBoxLayout(stats_frame)
        
        self.pending_label = QLabel("⏳ En Attente: 0")
        self.pending_label.setStyleSheet("font-weight: bold; color: #f39c12;")
        stats_layout.addWidget(self.pending_label)
        
        self.in_transit_label = QLabel("🚛 En Transit: 0")
        self.in_transit_label.setStyleSheet("font-weight: bold; color: #3498db;")
        stats_layout.addWidget(self.in_transit_label)
        
        self.received_label = QLabel("✅ Reçus: 0")
        self.received_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        stats_layout.addWidget(self.received_label)
        
        self.cancelled_label = QLabel("❌ Annulés: 0")
        self.cancelled_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        stats_layout.addWidget(self.cancelled_label)
        
        stats_layout.addStretch()
        layout.addWidget(stats_frame)
        
        # Filtres
        filters_layout = QHBoxLayout()
        
        filters_layout.addWidget(QLabel("Statut:"))
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(["Tous", "En Attente", "En Transit", "Reçus", "Annulés"])
        self.status_filter_combo.currentTextChanged.connect(self.filter_transfers)
        filters_layout.addWidget(self.status_filter_combo)
        
        filters_layout.addWidget(QLabel("Recherche:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Numéro de transfert ou notes...")
        self.search_input.textChanged.connect(self.search_transfers)
        filters_layout.addWidget(self.search_input)
        
        filters_layout.addStretch()
        layout.addLayout(filters_layout)
        
        # Tableau des transferts
        self.transfers_table = QTableWidget()
        self.transfers_table.setColumnCount(8)
        self.transfers_table.setHorizontalHeaderLabels([
            "Numéro", "Source", "Destination", "Statut", "Articles", "Demandé le", "Libellé", "Actions"
        ])
        self.transfers_table.setAlternatingRowColors(True)
        self.transfers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.transfers_table.doubleClicked.connect(self.view_transfer_details)
        
        layout.addWidget(self.transfers_table)
        
        # Tableau des transferts récents (en bas)
        recent_group = QGroupBox("Transferts Récents")
        recent_layout = QVBoxLayout(recent_group)
        
        self.recent_transfers_table = QTableWidget()
        self.recent_transfers_table.setColumnCount(6)
        self.recent_transfers_table.setHorizontalHeaderLabels([
            "Numéro", "Direction", "Statut", "Articles", "Date", "Libellé"
        ])
        self.recent_transfers_table.setMaximumHeight(200)
        self.recent_transfers_table.setAlternatingRowColors(True)
        recent_layout.addWidget(self.recent_transfers_table)
        
        layout.addWidget(recent_group)
    
    def load_data(self):
        """Charger les données des transferts"""
        try:
            with self.db_manager.get_session() as session:
                # Charger tous les transferts
                self.current_transfers = self.controller.get_all_transfers(session)
                
                # Charger les transferts récents
                recent_transfers = self.controller.get_recent_transfers(session, limit=10)
                
                self.populate_transfers_table()
                self.populate_recent_transfers_table(recent_transfers)
                self.update_statistics()
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des transferts:\n{str(e)}")
    
    def populate_transfers_table(self):
        """Peupler le tableau des transferts"""
        # Filtrer les transferts
        filtered_transfers = self.filter_transfers_data(self.current_transfers)
        
        self.transfers_table.setRowCount(len(filtered_transfers))
        
        for row, transfer in enumerate(filtered_transfers):
            # Numéro
            self.transfers_table.setItem(row, 0, QTableWidgetItem(transfer['transfer_number']))
            
            # Source
            source_text = f"{transfer['source_warehouse']['name']} ({transfer['source_warehouse']['code']})"
            self.transfers_table.setItem(row, 1, QTableWidgetItem(source_text))
            
            # Destination
            dest_text = f"{transfer['destination_warehouse']['name']} ({transfer['destination_warehouse']['code']})"
            self.transfers_table.setItem(row, 2, QTableWidgetItem(dest_text))
            
            # Statut
            status_icons = {
                'PENDING': '⏳ En Attente',
                'IN_TRANSIT': '🚛 En Transit',
                'RECEIVED': '✅ Reçu',
                'CANCELLED': '❌ Annulé'
            }
            status_item = QTableWidgetItem(status_icons.get(transfer['status'], transfer['status']))
            
            # Coloration selon le statut
            status_colors = {
                'PENDING': QColor("#FFF3CD"),     # Jaune clair
                'IN_TRANSIT': QColor("#D1ECF1"),  # Bleu clair
                'RECEIVED': QColor("#D4EDDA"),    # Vert clair
                'CANCELLED': QColor("#F8D7DA")    # Rouge clair
            }
            if transfer['status'] in status_colors:
                status_item.setBackground(status_colors[transfer['status']])
            
            self.transfers_table.setItem(row, 3, status_item)
            
            # Nombre d'articles
            articles_item = QTableWidgetItem(str(transfer['items_count']))
            articles_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.transfers_table.setItem(row, 4, articles_item)
            
            # Date de demande
            date_str = transfer['created_at'].strftime('%d/%m/%Y %H:%M')
            self.transfers_table.setItem(row, 5, QTableWidgetItem(date_str))
            
            # Libellé
            self.transfers_table.setItem(row, 6, QTableWidgetItem(transfer['label']))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            
            view_btn = QPushButton("👁️")
            view_btn.setToolTip("Voir les détails")
            view_btn.setMaximumWidth(30)
            view_btn.clicked.connect(lambda checked, t=transfer: self.view_transfer_details_by_id(t['id']))
            actions_layout.addWidget(view_btn)
            
            # Actions selon le statut
            if transfer['status'] == 'PENDING':
                ship_btn = QPushButton("🚛")
                ship_btn.setToolTip("Expédier")
                ship_btn.setMaximumWidth(30)
                ship_btn.clicked.connect(lambda checked, t=transfer: self.quick_ship_transfer(t['id']))
                actions_layout.addWidget(ship_btn)
            elif transfer['status'] == 'IN_TRANSIT':
                receive_btn = QPushButton("📦")
                receive_btn.setToolTip("Recevoir")
                receive_btn.setMaximumWidth(30)
                receive_btn.clicked.connect(lambda checked, t=transfer: self.quick_receive_transfer(t['id']))
                actions_layout.addWidget(receive_btn)
            
            self.transfers_table.setCellWidget(row, 7, actions_widget)
        
        # Ajuster les colonnes
        self.transfers_table.resizeColumnsToContents()
    
    def populate_recent_transfers_table(self, recent_transfers):
        """Peupler le tableau des transferts récents"""
        self.recent_transfers_table.setRowCount(len(recent_transfers))
        
        for row, transfer in enumerate(recent_transfers):
            # Numéro
            self.recent_transfers_table.setItem(row, 0, QTableWidgetItem(transfer['transfer_number']))
            
            # Direction
            direction = f"{transfer['source_warehouse']['code']} → {transfer['destination_warehouse']['code']}"
            self.recent_transfers_table.setItem(row, 1, QTableWidgetItem(direction))
            
            # Statut
            status_icons = {
                'PENDING': '⏳',
                'IN_TRANSIT': '🚛',
                'RECEIVED': '✅',
                'CANCELLED': '❌'
            }
            status_item = QTableWidgetItem(status_icons.get(transfer['status'], transfer['status']))
            self.recent_transfers_table.setItem(row, 2, status_item)
            
            # Articles
            articles_item = QTableWidgetItem(str(transfer['items_count']))
            articles_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.recent_transfers_table.setItem(row, 3, articles_item)
            
            # Date
            date_str = transfer['created_at'].strftime('%d/%m %H:%M')
            self.recent_transfers_table.setItem(row, 4, QTableWidgetItem(date_str))
            
            # Libellé (tronqué)
            label = transfer['label'][:30] + "..." if len(transfer['label']) > 30 else transfer['label']
            self.recent_transfers_table.setItem(row, 5, QTableWidgetItem(label))
        
        self.recent_transfers_table.resizeColumnsToContents()
    
    def filter_transfers_data(self, transfers):
        """Filtrer les données de transferts"""
        filtered = transfers.copy()
        
        # Filtre par statut
        status_filter = self.status_filter_combo.currentText()
        if status_filter != "Tous":
            status_map = {
                "En Attente": "PENDING",
                "En Transit": "IN_TRANSIT",
                "Reçus": "RECEIVED",
                "Annulés": "CANCELLED"
            }
            target_status = status_map.get(status_filter)
            if target_status:
                filtered = [t for t in filtered if t['status'] == target_status]
        
        # Filtre par recherche
        search_term = self.search_input.text().lower()
        if search_term:
            filtered = [
                t for t in filtered 
                if search_term in t['transfer_number'].lower() or 
                   search_term in (t['label'] or "").lower() or
                   search_term in (t['notes'] or "").lower()
            ]
        
        return filtered
    
    def filter_transfers(self):
        """Filtrer les transferts"""
        self.populate_transfers_table()
    
    def search_transfers(self):
        """Rechercher dans les transferts"""
        self.populate_transfers_table()
    
    def update_statistics(self):
        """Mettre à jour les statistiques"""
        stats = {
            'PENDING': 0,
            'IN_TRANSIT': 0,
            'RECEIVED': 0,
            'CANCELLED': 0
        }
        
        for transfer in self.current_transfers:
            status = transfer['status']
            if status in stats:
                stats[status] += 1
        
        self.pending_label.setText(f"⏳ En Attente: {stats['PENDING']}")
        self.in_transit_label.setText(f"🚛 En Transit: {stats['IN_TRANSIT']}")
        self.received_label.setText(f"✅ Reçus: {stats['RECEIVED']}")
        self.cancelled_label.setText(f"❌ Annulés: {stats['CANCELLED']}")
    
    def create_new_transfer(self):
        """Créer un nouveau transfert"""
        dialog = TransferFormDialog(self, pos_id=self.pos_id)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()
            self.transfer_created.emit()
            
            QMessageBox.information(
                self, "Succès", 
                "Le transfert a été créé avec succès!\n"
                "Il apparaît maintenant dans la liste."
            )
    
    def view_transfer_details(self):
        """Voir les détails du transfert sélectionné"""
        selected_rows = self.transfers_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            filtered_transfers = self.filter_transfers_data(self.current_transfers)
            if row < len(filtered_transfers):
                transfer = filtered_transfers[row]
                self.view_transfer_details_by_id(transfer['id'])
    
    def view_transfer_details_by_id(self, transfer_id):
        """Voir les détails d'un transfert par son ID"""
        dialog = TransferDetailDialog(self, transfer_id=transfer_id, controller=self.controller)
        dialog.exec()
        
        # Recharger les données au cas où le transfert aurait été modifié
        self.load_data()
        self.transfer_updated.emit()
    
    def quick_ship_transfer(self, transfer_id):
        """Expédition rapide d'un transfert"""
        reply = QMessageBox.question(
            self, "Confirmation",
            "Expédier ce transfert?\n\n"
            "Cette action retirera les produits du stock source.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with self.db_manager.get_session() as session:
                    self.controller.update_transfer_status(session, transfer_id, 'IN_TRANSIT')
                    session.commit()
                    
                    QMessageBox.information(self, "Succès", "Transfert expédié avec succès!")
                    self.load_data()
                    self.transfer_updated.emit()
                    
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'expédition:\n{str(e)}")
    
    def quick_receive_transfer(self, transfer_id):
        """Réception rapide d'un transfert"""
        reply = QMessageBox.question(
            self, "Confirmation",
            "Recevoir ce transfert?\n\n"
            "Cette action ajoutera les produits au stock destination.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with self.db_manager.get_session() as session:
                    self.controller.update_transfer_status(session, transfer_id, 'RECEIVED')
                    session.commit()
                    
                    QMessageBox.information(self, "Succès", "Transfert reçu avec succès!")
                    self.load_data()
                    self.transfer_updated.emit()
                    
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la réception:\n{str(e)}")