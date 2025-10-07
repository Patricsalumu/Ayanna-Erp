"""
Widget pour la gestion des stocks par entrepôt
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton, 
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, 
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout, QTextEdit, 
    QDoubleSpinBox, QSpinBox, QCheckBox, QTabWidget, QTreeWidget, 
    QTreeWidgetItem, QSplitter, QProgressBar, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPixmap, QIcon

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.stock.controllers.stock_controller import StockController


class StockLevelsDialog(QDialog):
    """Dialog pour configurer les niveaux de stock (min/max)"""
    
    def __init__(self, parent=None, warehouse_id=None, product_id=None, current_min=0, current_max=0):
        super().__init__(parent)
        self.warehouse_id = warehouse_id
        self.product_id = product_id
        self.setWindowTitle("Configuration des Niveaux de Stock")
        self.setFixedSize(400, 200)
        self.setup_ui(current_min, current_max)
    
    def setup_ui(self, current_min, current_max):
        """Configuration de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # Titre
        title = QLabel("Configurer les Niveaux de Stock")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Formulaire
        form_layout = QFormLayout()
        
        # Stock minimum
        self.min_spinbox = QDoubleSpinBox()
        self.min_spinbox.setRange(0, 999999)
        self.min_spinbox.setDecimals(2)
        self.min_spinbox.setValue(current_min)
        self.min_spinbox.setSuffix(" unités")
        form_layout.addRow("Stock minimum:", self.min_spinbox)
        
        # Stock maximum
        self.max_spinbox = QDoubleSpinBox()
        self.max_spinbox.setRange(0, 999999)
        self.max_spinbox.setDecimals(2)
        self.max_spinbox.setValue(current_max)
        self.max_spinbox.setSuffix(" unités")
        form_layout.addRow("Stock maximum:", self.max_spinbox)
        
        layout.addLayout(form_layout)
        
        # Note explicative
        note = QLabel("Le stock minimum déclenche une alerte de réapprovisionnement.\n"
                     "Le stock maximum aide à détecter les surstocks.")
        note.setStyleSheet("color: #666; font-style: italic;")
        note.setWordWrap(True)
        layout.addWidget(note)
        
        # Boutons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept_if_valid)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def accept_if_valid(self):
        """Valider et accepter le formulaire"""
        min_value = self.min_spinbox.value()
        max_value = self.max_spinbox.value()
        
        if max_value > 0 and min_value >= max_value:
            QMessageBox.warning(self, "Validation", "Le stock minimum doit être inférieur au stock maximum.")
            return
        
        self.accept()
    
    def get_levels(self):
        """Récupérer les niveaux configurés"""
        return {
            'minimum': self.min_spinbox.value(),
            'maximum': self.max_spinbox.value()
        }


class ProductStockDetailDialog(QDialog):
    """Dialog pour afficher les détails du stock d'un produit dans tous les entrepôts"""
    
    def __init__(self, parent=None, product_id=None, controller=None):
        super().__init__(parent)
        self.product_id = product_id
        self.controller = controller
        self.setWindowTitle("Détails du Stock par Entrepôt")
        self.setFixedSize(800, 600)
        self.setup_ui()
        self.load_product_details()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # En-tête
        header_layout = QHBoxLayout()
        self.product_title = QLabel("Chargement...")
        self.product_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(self.product_title)
        header_layout.addStretch()
        
        close_btn = QPushButton("❌ Fermer")
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        layout.addLayout(header_layout)
        
        # Résumé global
        summary_group = QGroupBox("Résumé Global")
        summary_layout = QHBoxLayout(summary_group)
        
        self.total_qty_label = QLabel("Total: 0")
        self.total_qty_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        summary_layout.addWidget(self.total_qty_label)
        
        self.total_reserved_label = QLabel("Réservé: 0")
        summary_layout.addWidget(self.total_reserved_label)
        
        self.total_available_label = QLabel("Disponible: 0")
        summary_layout.addWidget(self.total_available_label)
        
        self.total_value_label = QLabel("Valeur: 0.00 €")
        summary_layout.addWidget(self.total_value_label)
        
        summary_layout.addStretch()
        layout.addWidget(summary_group)
        
        # Tableau des entrepôts
        self.warehouses_table = QTableWidget()
        self.warehouses_table.setColumnCount(7)
        self.warehouses_table.setHorizontalHeaderLabels([
            "Entrepôt", "Type", "Quantité", "Réservé", "Disponible", "Min", "Statut"
        ])
        self.warehouses_table.setAlternatingRowColors(True)
        layout.addWidget(self.warehouses_table)
    
    def load_product_details(self):
        """Charger les détails du produit"""
        try:
            with self.controller.db_manager.get_session() as session:
                details = self.controller.get_product_stock_by_warehouses(session, self.product_id)
                
                # Mise à jour du titre
                product = details['product']
                self.product_title.setText(f"📦 {product['name']} ({product['code']})")
                
                # Mise à jour du résumé
                totals = details['totals']
                self.total_qty_label.setText(f"Total: {totals['total_quantity']:.2f}")
                self.total_reserved_label.setText(f"Réservé: {totals['total_reserved']:.2f}")
                self.total_available_label.setText(f"Disponible: {totals['total_available']:.2f}")
                
                # Calculer la valeur totale
                total_value = sum(
                    stock['quantity'] * stock['unit_cost'] 
                    for stock in details['warehouse_stocks']
                )
                self.total_value_label.setText(f"Valeur: {total_value:.2f} €")
                
                # Remplir le tableau
                self.populate_warehouses_table(details['warehouse_stocks'])
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des détails:\n{str(e)}")
    
    def populate_warehouses_table(self, warehouse_stocks):
        """Peupler le tableau des entrepôts"""
        self.warehouses_table.setRowCount(len(warehouse_stocks))
        
        for row, stock in enumerate(warehouse_stocks):
            # Entrepôt
            warehouse_item = QTableWidgetItem(f"{stock['warehouse_name']} ({stock['warehouse_code']})")
            self.warehouses_table.setItem(row, 0, warehouse_item)
            
            # Type
            type_item = QTableWidgetItem(stock['warehouse_type'])
            self.warehouses_table.setItem(row, 1, type_item)
            
            # Quantité
            qty_item = QTableWidgetItem(f"{stock['quantity']:.2f}")
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.warehouses_table.setItem(row, 2, qty_item)
            
            # Réservé
            reserved_item = QTableWidgetItem(f"{stock['reserved_quantity']:.2f}")
            reserved_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.warehouses_table.setItem(row, 3, reserved_item)
            
            # Disponible
            available_item = QTableWidgetItem(f"{stock['available_quantity']:.2f}")
            available_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if stock['available_quantity'] <= 0:
                available_item.setBackground(QColor("#FFE6E6"))  # Rouge clair
            self.warehouses_table.setItem(row, 4, available_item)
            
            # Min
            min_item = QTableWidgetItem(f"{stock['minimum_stock']:.2f}")
            min_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.warehouses_table.setItem(row, 5, min_item)
            
            # Statut
            status = stock['status']
            status_icons = {
                'NORMAL': '✅ Normal',
                'FAIBLE': '⚠️ Faible',
                'RUPTURE': '🔴 Rupture',
                'EXCES': '📈 Excès'
            }
            status_item = QTableWidgetItem(status_icons.get(status, status))
            
            # Coloration selon le statut
            status_colors = {
                'NORMAL': QColor("#E8F5E8"),     # Vert clair
                'FAIBLE': QColor("#FFF3CD"),     # Jaune clair
                'RUPTURE': QColor("#F8D7DA"),    # Rouge clair
                'EXCES': QColor("#D1ECF1")       # Bleu clair
            }
            if status in status_colors:
                status_item.setBackground(status_colors[status])
            
            self.warehouses_table.setItem(row, 6, status_item)
        
        # Ajuster les colonnes
        self.warehouses_table.resizeColumnsToContents()


class StockWidget(QWidget):
    """Widget principal pour la gestion des stocks par entrepôt"""
    
    # Signaux
    stock_updated = pyqtSignal()  # Quand le stock est mis à jour
    
    def __init__(self, pos_id: int, current_user):
        super().__init__()
        self.pos_id = pos_id
        self.current_user = current_user
        self.controller = StockController(pos_id)
        self.db_manager = DatabaseManager()
        self.current_stocks = []
        self.current_warehouse_id = None
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # En-tête avec titre et résumé
        header_layout = QVBoxLayout()
        
        # Titre
        title_layout = QHBoxLayout()
        title_label = QLabel("📦 Gestion des Stocks")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Boutons d'action globaux
        export_btn = QPushButton("📄 Exporter")
        export_btn.clicked.connect(self.export_stock_data)
        title_layout.addWidget(export_btn)
        
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.clicked.connect(self.load_data)
        title_layout.addWidget(refresh_btn)
        
        header_layout.addLayout(title_layout)
        
        # Résumé des stocks
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        summary_layout = QHBoxLayout(summary_frame)
        
        self.total_products_label = QLabel("Produits: 0")
        self.total_products_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        summary_layout.addWidget(self.total_products_label)
        
        self.total_warehouses_label = QLabel("Entrepôts: 0")
        summary_layout.addWidget(self.total_warehouses_label)
        
        self.total_value_label = QLabel("Valeur: 0.00 €")
        summary_layout.addWidget(self.total_value_label)
        
        self.total_items_label = QLabel("Références: 0")
        summary_layout.addWidget(self.total_items_label)
        
        summary_layout.addStretch()
        header_layout.addWidget(summary_frame)
        
        layout.addLayout(header_layout)
        
        # Filtres
        filters_group = QGroupBox("Filtres et Recherche")
        filters_layout = QHBoxLayout(filters_group)
        
        # Filtre par entrepôt
        filters_layout.addWidget(QLabel("Entrepôt:"))
        self.warehouse_combo = QComboBox()
        self.warehouse_combo.setMinimumWidth(200)
        self.warehouse_combo.currentTextChanged.connect(self.filter_by_warehouse)
        filters_layout.addWidget(self.warehouse_combo)
        
        # Filtre par statut
        filters_layout.addWidget(QLabel("Statut:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "Tous", "Normal", "Stock Faible", "Rupture", "Excès"
        ])
        self.status_combo.currentTextChanged.connect(self.filter_by_status)
        filters_layout.addWidget(self.status_combo)
        
        # Recherche produit
        filters_layout.addWidget(QLabel("Recherche:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nom ou code produit...")
        self.search_input.textChanged.connect(self.search_products)
        filters_layout.addWidget(self.search_input)
        
        filters_layout.addStretch()
        layout.addWidget(filters_group)
        
        # Tableau principal des stocks
        self.stocks_table = QTableWidget()
        self.stocks_table.setColumnCount(10)
        self.stocks_table.setHorizontalHeaderLabels([
            "Produit", "Code", "Entrepôt", "Quantité", "Réservé", "Disponible", 
            "Min", "Coût Unit.", "Valeur", "Statut"
        ])
        self.stocks_table.setAlternatingRowColors(True)
        self.stocks_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.stocks_table.doubleClicked.connect(self.show_product_details)
        self.stocks_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.stocks_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Ajuster les colonnes
        header = self.stocks_table.horizontalHeader()
        header.setStretchLastSection(True)
        
        layout.addWidget(self.stocks_table)
        
        # Barre d'actions en bas
        actions_layout = QHBoxLayout()
        
        self.configure_levels_btn = QPushButton("⚙️ Configurer Niveaux")
        self.configure_levels_btn.setToolTip("Configurer les niveaux min/max pour le produit sélectionné")
        self.configure_levels_btn.setEnabled(False)
        self.configure_levels_btn.clicked.connect(self.configure_stock_levels)
        actions_layout.addWidget(self.configure_levels_btn)
        
        self.view_details_btn = QPushButton("🔍 Voir Détails")
        self.view_details_btn.setToolTip("Voir les détails du produit dans tous les entrepôts")
        self.view_details_btn.setEnabled(False)
        self.view_details_btn.clicked.connect(self.show_product_details)
        actions_layout.addWidget(self.view_details_btn)
        
        actions_layout.addStretch()
        
        self.selected_info_label = QLabel("Sélectionnez une ligne pour voir les actions disponibles")
        self.selected_info_label.setStyleSheet("color: #666; font-style: italic;")
        actions_layout.addWidget(self.selected_info_label)
        
        layout.addLayout(actions_layout)
        
        # Connexions
        self.stocks_table.itemSelectionChanged.connect(self.on_selection_changed)
    
    def load_data(self):
        """Charger les données des stocks"""
        try:
            # Charger les entrepôts pour le filtre
            with self.db_manager.get_session() as session:
                from ayanna_erp.modules.boutique.model.models import ShopWarehouse
                warehouses = session.query(ShopWarehouse).filter(
                    ShopWarehouse.pos_id == self.pos_id,
                    ShopWarehouse.is_active == True
                ).order_by(ShopWarehouse.name).all()
                
                self.warehouse_combo.clear()
                self.warehouse_combo.addItem("-- Tous les entrepôts --", None)
                for warehouse in warehouses:
                    self.warehouse_combo.addItem(f"{warehouse.name} ({warehouse.code})", warehouse.id)
                
                # Charger les stocks
                self.load_stocks()
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des données:\n{str(e)}")
    
    def load_stocks(self):
        """Charger les données de stock"""
        try:
            with self.db_manager.get_session() as session:
                warehouse_id = self.warehouse_combo.currentData()
                stock_data = self.controller.get_stock_overview(session, warehouse_id)
                
                self.current_stocks = stock_data['stocks']
                self.populate_stocks_table()
                self.update_summary(stock_data['summary'])
                
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des stocks:\n{str(e)}")
    
    def populate_stocks_table(self):
        """Peupler le tableau des stocks"""
        # Filtrer les stocks selon les critères
        filtered_stocks = self.filter_stocks(self.current_stocks)
        
        self.stocks_table.setRowCount(len(filtered_stocks))
        
        for row, stock in enumerate(filtered_stocks):
            # Produit
            product_item = QTableWidgetItem(stock['product_name'])
            self.stocks_table.setItem(row, 0, product_item)
            
            # Code
            code_item = QTableWidgetItem(stock['product_code'] or "")
            self.stocks_table.setItem(row, 1, code_item)
            
            # Entrepôt
            warehouse_item = QTableWidgetItem(f"{stock['warehouse_name']} ({stock['warehouse_code']})")
            self.stocks_table.setItem(row, 2, warehouse_item)
            
            # Quantité
            qty_item = QTableWidgetItem(f"{stock['quantity']:.2f}")
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.stocks_table.setItem(row, 3, qty_item)
            
            # Réservé
            reserved_item = QTableWidgetItem(f"{stock['reserved_quantity']:.2f}")
            reserved_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.stocks_table.setItem(row, 4, reserved_item)
            
            # Disponible
            available_item = QTableWidgetItem(f"{stock['available_quantity']:.2f}")
            available_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if stock['available_quantity'] <= 0:
                available_item.setBackground(QColor("#FFE6E6"))  # Rouge clair
            self.stocks_table.setItem(row, 5, available_item)
            
            # Min
            min_item = QTableWidgetItem(f"{stock['minimum_stock']:.2f}")
            min_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.stocks_table.setItem(row, 6, min_item)
            
            # Coût unitaire
            cost_item = QTableWidgetItem(f"{stock['unit_cost']:.2f}")
            cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.stocks_table.setItem(row, 7, cost_item)
            
            # Valeur
            value_item = QTableWidgetItem(f"{stock['stock_value']:.2f}")
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.stocks_table.setItem(row, 8, value_item)
            
            # Statut
            status = stock['status']
            status_icons = {
                'NORMAL': '✅ Normal',
                'FAIBLE': '⚠️ Faible',
                'RUPTURE': '🔴 Rupture',
                'EXCES': '📈 Excès'
            }
            status_item = QTableWidgetItem(status_icons.get(status, status))
            
            # Coloration selon le statut
            status_colors = {
                'NORMAL': QColor("#E8F5E8"),     # Vert clair
                'FAIBLE': QColor("#FFF3CD"),     # Jaune clair
                'RUPTURE': QColor("#F8D7DA"),    # Rouge clair
                'EXCES': QColor("#D1ECF1")       # Bleu clair
            }
            if status in status_colors:
                status_item.setBackground(status_colors[status])
            
            self.stocks_table.setItem(row, 9, status_item)
        
        # Ajuster les colonnes
        self.stocks_table.resizeColumnsToContents()
    
    def filter_stocks(self, stocks):
        """Filtrer les stocks selon les critères"""
        filtered = stocks.copy()
        
        # Filtre par statut
        status_filter = self.status_combo.currentText()
        if status_filter != "Tous":
            status_map = {
                "Normal": "NORMAL",
                "Stock Faible": "FAIBLE",
                "Rupture": "RUPTURE",
                "Excès": "EXCES"
            }
            target_status = status_map.get(status_filter)
            if target_status:
                filtered = [s for s in filtered if s['status'] == target_status]
        
        # Filtre par recherche
        search_term = self.search_input.text().lower()
        if search_term:
            filtered = [
                s for s in filtered 
                if search_term in s['product_name'].lower() or 
                   search_term in (s['product_code'] or "").lower()
            ]
        
        return filtered
    
    def update_summary(self, summary):
        """Mettre à jour le résumé"""
        self.total_products_label.setText(f"Produits: {summary['total_products']}")
        self.total_warehouses_label.setText(f"Entrepôts: {summary['total_warehouses']}")
        self.total_value_label.setText(f"Valeur: {summary['total_value']:.2f} €")
        self.total_items_label.setText(f"Références: {summary['total_items']}")
    
    def filter_by_warehouse(self):
        """Filtrer par entrepôt"""
        self.load_stocks()
    
    def filter_by_status(self):
        """Filtrer par statut"""
        self.populate_stocks_table()
    
    def search_products(self):
        """Rechercher des produits"""
        self.populate_stocks_table()
    
    def on_selection_changed(self):
        """Gestionnaire de changement de sélection"""
        selected_rows = self.stocks_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        
        self.configure_levels_btn.setEnabled(has_selection)
        self.view_details_btn.setEnabled(has_selection)
        
        if has_selection:
            row = selected_rows[0].row()
            if row < len(self.filter_stocks(self.current_stocks)):
                stock = self.filter_stocks(self.current_stocks)[row]
                self.selected_info_label.setText(
                    f"Sélectionné: {stock['product_name']} dans {stock['warehouse_name']}"
                )
        else:
            self.selected_info_label.setText("Sélectionnez une ligne pour voir les actions disponibles")
    
    def configure_stock_levels(self):
        """Configurer les niveaux de stock pour le produit sélectionné"""
        selected_rows = self.stocks_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        filtered_stocks = self.filter_stocks(self.current_stocks)
        if row >= len(filtered_stocks):
            return
        
        stock = filtered_stocks[row]
        
        dialog = StockLevelsDialog(
            self, 
            warehouse_id=stock['warehouse_id'],
            product_id=stock['product_id'],
            current_min=stock['minimum_stock'],
            current_max=0  # Pas de maximum stock
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            levels = dialog.get_levels()
            
            try:
                with self.db_manager.get_session() as session:
                    self.controller.update_stock_levels(
                        session,
                        stock['warehouse_id'],
                        stock['product_id'],
                        levels['minimum'],
                        levels['maximum']
                    )
                    session.commit()
                    
                    QMessageBox.information(
                        self, "Succès", 
                        f"Niveaux de stock mis à jour pour {stock['product_name']}"
                    )
                    
                    self.load_stocks()
                    self.stock_updated.emit()
                    
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la mise à jour:\n{str(e)}")
    
    def show_product_details(self):
        """Afficher les détails du produit dans tous les entrepôts"""
        selected_rows = self.stocks_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        filtered_stocks = self.filter_stocks(self.current_stocks)
        if row >= len(filtered_stocks):
            return
        
        stock = filtered_stocks[row]
        
        dialog = ProductStockDetailDialog(
            self,
            product_id=stock['product_id'],
            controller=self.controller
        )
        dialog.exec()
    
    def show_context_menu(self, position):
        """Afficher le menu contextuel"""
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        
        selected_rows = self.stocks_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        menu = QMenu(self)
        
        # Actions disponibles
        details_action = QAction("🔍 Voir les détails", self)
        details_action.triggered.connect(self.show_product_details)
        menu.addAction(details_action)
        
        levels_action = QAction("⚙️ Configurer niveaux", self)
        levels_action.triggered.connect(self.configure_stock_levels)
        menu.addAction(levels_action)
        
        menu.addSeparator()
        
        export_action = QAction("📄 Exporter ce produit", self)
        export_action.triggered.connect(self.export_selected_product)
        menu.addAction(export_action)
        
        # Afficher le menu
        menu.exec(self.stocks_table.mapToGlobal(position))
    
    def export_selected_product(self):
        """Exporter les données du produit sélectionné"""
        selected_rows = self.stocks_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        filtered_stocks = self.filter_stocks(self.current_stocks)
        if row >= len(filtered_stocks):
            return
        
        stock = filtered_stocks[row]
        
        try:
            with self.db_manager.get_session() as session:
                details = self.controller.get_product_stock_by_warehouses(session, stock['product_id'])
                
                # Préparer les données pour export
                export_data = []
                for warehouse_stock in details['warehouse_stocks']:
                    export_data.append({
                        'Produit': details['product']['name'],
                        'Code': details['product']['code'],
                        'Entrepôt': warehouse_stock['warehouse_name'],
                        'Type Entrepôt': warehouse_stock['warehouse_type'],
                        'Quantité': warehouse_stock['quantity'],
                        'Réservé': warehouse_stock['reserved_quantity'],
                        'Disponible': warehouse_stock['available_quantity'],
                        'Minimum': warehouse_stock['minimum_stock'],
                        'Coût Unitaire': warehouse_stock['unit_cost'],
                        'Statut': warehouse_stock['status']
                    })
                
                QMessageBox.information(
                    self, "Export", 
                    f"Export préparé pour {details['product']['name']}\n"
                    f"Données de {len(export_data)} entrepôts\n\n"
                    f"Note: Fonctionnalité d'export fichier à implémenter"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export:\n{str(e)}")
    
    def export_stock_data(self):
        """Exporter toutes les données de stock"""
        try:
            with self.db_manager.get_session() as session:
                warehouse_id = self.warehouse_combo.currentData()
                export_data = self.controller.export_stock_data(session, warehouse_id)
                
                QMessageBox.information(
                    self, "Export", 
                    f"Export préparé:\n\n"
                    f"• Nombre de lignes: {len(export_data['data'])}\n"
                    f"• Produits uniques: {export_data['summary']['total_products']}\n"
                    f"• Entrepôts: {export_data['summary']['total_warehouses']}\n"
                    f"• Valeur totale: {export_data['summary']['total_value']:.2f} €\n\n"
                    f"Note: Fonctionnalité d'export fichier à implémenter"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export:\n{str(e)}")