"""
Widget pour la gestion des stocks par entrepôt
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from sqlalchemy import text
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
from ayanna_erp.modules.stock.models import StockWarehouse
from ayanna_erp.core.entreprise_controller import EntrepriseController


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
        
        # Formulaire
        form_layout = QFormLayout()
        
        # Stock minimum
        self.min_spinbox = QDoubleSpinBox()
        self.min_spinbox.setRange(0, 999999)
        self.min_spinbox.setDecimals(2)
        self.min_spinbox.setValue(current_min)
        self.min_spinbox.setSuffix(" unités")
        form_layout.addRow("Stock minimum:", self.min_spinbox)
        
        # NOTE: On ne gère que le niveau minimum par entrepôt (pas de maximum)
        
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
        # Aucun contrôle de maximum — on n'autorise que le niveau minimum
        
        self.accept()
    
    def get_levels(self):
        """Récupérer les niveaux configurés"""
        return {
            'minimum': self.min_spinbox.value()
        }


class ProductStockDetailDialog(QDialog):
    """Dialog pour afficher les détails du stock d'un produit dans tous les entrepôts"""
    
    def __init__(self, parent=None, product_id=None, controller=None):
        super().__init__(parent)
        self.product_id = product_id
        self.controller = controller
        self.ent_ctrl = EntrepriseController()
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
        
        # Valeur initiale — sera mise à jour après chargement
        self.total_value_label = QLabel("Valeur: 0")
        summary_layout.addWidget(self.total_value_label)
        
        summary_layout.addStretch()
        layout.addWidget(summary_group)
        
        # Tableau des entrepôts (détails produit)
        self.warehouses_table = QTableWidget()
        # Ajouter une colonne Actions (bouton de configuration) en plus
        self.warehouses_table.setColumnCount(6)
        self.warehouses_table.setHorizontalHeaderLabels([
            "Entrepôt", "Type", "Quantité", "Min", "Statut", "Actions"
        ])
        self.warehouses_table.setAlternatingRowColors(True)
        # Désactiver l'édition directe pour le tableau de détails
        self.warehouses_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    # (Remplacé) utilisation d'un bouton '⚙️' par ligne pour configurer le min
        wh_header = self.warehouses_table.horizontalHeader()
        wh_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.warehouses_table.setColumnWidth(0, 260)
        self.warehouses_table.setColumnWidth(1, 120)
        self.warehouses_table.setColumnWidth(2, 100)
        self.warehouses_table.setColumnWidth(3, 90)
        self.warehouses_table.setColumnWidth(4, 120)
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
                # Quantités : formater sans symbole monétaire
                self.total_qty_label.setText(f"Total: {self.ent_ctrl.format_amount(totals.get('total_quantity', 0), show_symbol=False)}")
                self.total_reserved_label.setText(f"Réservé: {self.ent_ctrl.format_amount(totals.get('total_reserved', 0), show_symbol=False)}")
                self.total_available_label.setText(f"Disponible: {self.ent_ctrl.format_amount(totals.get('total_available', 0), show_symbol=False)}")
                
                # Calculer la valeur totale
                total_value = sum(
                    stock['quantity'] * stock['unit_cost'] 
                    for stock in details['warehouse_stocks']
                )
                # Valeur : formater avec symbole monétaire
                self.total_value_label.setText(f"Valeur: {self.ent_ctrl.format_amount(total_value)}")
                
                # Stocker localement et remplir le tableau
                self.current_warehouse_stocks = details['warehouse_stocks']
                self.populate_warehouses_table(self.current_warehouse_stocks)
                
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
            qty_item = QTableWidgetItem(f"{self.ent_ctrl.format_amount(stock.get('quantity', 0), show_symbol=False)}")
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.warehouses_table.setItem(row, 2, qty_item)
            
            # Min (compatibilité clés)
            min_val = stock.get('min_stock_level', stock.get('minimum_stock', 0))
            min_item = QTableWidgetItem(f"{self.ent_ctrl.format_amount(min_val, show_symbol=False)}")
            min_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.warehouses_table.setItem(row, 3, min_item)
            
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
            
            self.warehouses_table.setItem(row, 4, status_item)

            # Actions (bouton config)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)

            config_btn = QPushButton("⚙️")
            config_btn.setToolTip("Configurer le stock minimum")
            config_btn.setMaximumWidth(30)
            # Capturer la ligne et le stock courant
            config_btn.clicked.connect(lambda checked, s=stock, r=row: self.open_min_dialog_for_warehouse(s, r))
            actions_layout.addWidget(config_btn)

            self.warehouses_table.setCellWidget(row, 5, actions_widget)

        # Ajuster les colonnes
        self.warehouses_table.resizeColumnsToContents()

    def open_min_dialog_for_warehouse(self, stock: dict, row: int):
        """Ouvrir le dialogue de configuration du niveau minimum pour un entrepôt donné (bouton '⚙️')."""
        current_min = stock.get('min_stock_level', stock.get('minimum_stock', 0))
        dialog = StockLevelsDialog(self, warehouse_id=stock.get('warehouse_id'), product_id=self.product_id, current_min=current_min)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            levels = dialog.get_levels()
            new_min = levels.get('minimum', current_min)

            # Persister via le contrôleur si possible
            try:
                with self.controller.db_manager.get_session() as session:
                    if hasattr(self.controller, 'set_min_stock_level'):
                        self.controller.set_min_stock_level(session, self.product_id, stock.get('warehouse_id'), new_min)
                    else:
                        session.execute(text("""
                            UPDATE stock_produit_entrepot SET min_stock_level = :min_stock_level, updated_at = CURRENT_TIMESTAMP
                            WHERE product_id = :product_id AND warehouse_id = :warehouse_id
                        """), {"min_stock_level": float(new_min), "product_id": self.product_id, "warehouse_id": stock.get('warehouse_id')})
                    session.commit()
            except Exception as e:
                QMessageBox.warning(self, "Erreur", f"Impossible de sauvegarder le niveau minimum:\n{e}")

            # Mettre à jour les données locales
            stock['min_stock_level'] = float(new_min)
            stock['minimum_stock'] = float(new_min)

            # Recalculer le statut pour cette ligne
            available = stock.get('quantity', 0) - stock.get('reserved_quantity', 0)
            min_level = float(new_min)
            if available <= 0:
                status = 'RUPTURE'
            elif available <= min_level:
                status = 'FAIBLE'
            elif available <= min_level * 1.5:
                status = 'ALERTE'
            else:
                status = 'NORMAL'

            stock['status'] = status

            # Mettre à jour l'UI: min et statut
            min_item = QTableWidgetItem(f"{self.ent_ctrl.format_amount(min_level, show_symbol=False)}")
            min_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.warehouses_table.setItem(row, 3, min_item)

            status_icons = {
                'NORMAL': '✅ Normal',
                'FAIBLE': '⚠️ Faible',
                'RUPTURE': '🔴 Rupture',
                'EXCES': '📈 Excès'
            }
            status_item = QTableWidgetItem(status_icons.get(status, status))
            status_colors = {
                'NORMAL': QColor("#E8F5E8"),
                'FAIBLE': QColor("#FFF3CD"),
                'RUPTURE': QColor("#F8D7DA"),
                'EXCES': QColor("#D1ECF1")
            }
            if status in status_colors:
                status_item.setBackground(status_colors[status])

            self.warehouses_table.setItem(row, 4, status_item)

            # Recalculer et mettre à jour le résumé global
            total_qty = sum(s.get('quantity', 0) for s in self.current_warehouse_stocks)
            total_reserved = sum(s.get('reserved_quantity', 0) for s in self.current_warehouse_stocks)
            total_available = sum((s.get('quantity', 0) - s.get('reserved_quantity', 0)) for s in self.current_warehouse_stocks)
            total_value = sum((s.get('quantity', 0) * s.get('unit_cost', 0)) for s in self.current_warehouse_stocks)

            self.total_qty_label.setText(f"Total: {self.ent_ctrl.format_amount(total_qty, show_symbol=False)}")
            self.total_reserved_label.setText(f"Réservé: {self.ent_ctrl.format_amount(total_reserved, show_symbol=False)}")
            self.total_available_label.setText(f"Disponible: {self.ent_ctrl.format_amount(total_available, show_symbol=False)}")
            self.total_value_label.setText(f"Valeur: {self.ent_ctrl.format_amount(total_value)}")


class StockWidget(QWidget):
    """Widget principal pour la gestion des stocks par entrepôt"""
    
    # Signaux
    stock_updated = pyqtSignal()  # Quand le stock est mis à jour
    
    def __init__(self, pos_id: int, current_user):
        super().__init__()
        self.pos_id = pos_id
        self.current_user = current_user
        self.db_manager = DatabaseManager()
        # Récupérer entreprise_id depuis pos_id
        self.entreprise_id = self.get_entreprise_id_from_pos(pos_id)
        self.controller = StockController(pos_id)
        # Contrôleur entreprise pour formatage des montants
        self.ent_ctrl = EntrepriseController()
        self.current_stocks = []
        self.current_warehouse_id = None
        
        self.setup_ui()
        self.load_data()
    
    def get_entreprise_id_from_pos(self, pos_id):
        """Récupérer l'entreprise_id depuis le pos_id"""
        try:
            with self.db_manager.get_session() as session:
                result = session.execute(text("SELECT enterprise_id FROM core_pos_points WHERE id = :pos_id"), {"pos_id": pos_id})
                row = result.fetchone()
                return row[0] if row else None
        except Exception as e:
            print(f"Erreur lors de la récupération de l'entreprise_id: {e}")
            return None
    
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
        self.stocks_table.setColumnCount(8)
        self.stocks_table.setHorizontalHeaderLabels([
            "Produit", "Code", "Entrepôt", "Quantité", 
            "Min", "Coût Unit.", "Valeur", "Statut"
        ])
        self.stocks_table.setAlternatingRowColors(True)
        self.stocks_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.stocks_table.doubleClicked.connect(self.show_product_details)
        self.stocks_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.stocks_table.customContextMenuRequested.connect(self.show_context_menu)
        # Désactiver l'édition directe et rendre les colonnes statiques
        self.stocks_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.stocks_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        # définir des largeurs raisonnables pour chaque colonne
        self.stocks_table.setColumnWidth(0, 220)  # Produit
        self.stocks_table.setColumnWidth(1, 90)   # Code
        self.stocks_table.setColumnWidth(2, 180)  # Entrepôt
        self.stocks_table.setColumnWidth(3, 90)   # Quantité
        self.stocks_table.setColumnWidth(4, 80)   # Min
        self.stocks_table.setColumnWidth(5, 100)  # Coût Unit.
        self.stocks_table.setColumnWidth(6, 100)  # Valeur
        self.stocks_table.setColumnWidth(7, 110)  # Statut

        layout.addWidget(self.stocks_table)
        
        # Barre d'actions en bas
        actions_layout = QHBoxLayout()
        
        
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
                warehouses = session.query(StockWarehouse).filter(
                    StockWarehouse.entreprise_id == self.entreprise_id,
                    StockWarehouse.is_active == True
                ).order_by(StockWarehouse.name).all()
                
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
            qty_item = QTableWidgetItem(f"{self.ent_ctrl.format_amount(stock.get('quantity', 0), show_symbol=False)}")
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.stocks_table.setItem(row, 3, qty_item)
            
            # Min
            min_item = QTableWidgetItem(f"{self.ent_ctrl.format_amount(stock.get('minimum_stock', 0), show_symbol=False)}")
            min_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.stocks_table.setItem(row, 4, min_item)
            
            # Coût unitaire
            cost_item = QTableWidgetItem(f"{self.ent_ctrl.format_amount(stock.get('unit_cost', 0))}")
            cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.stocks_table.setItem(row, 5, cost_item)
            
            # Valeur
            value_item = QTableWidgetItem(f"{self.ent_ctrl.format_amount(stock.get('stock_value', 0))}")
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.stocks_table.setItem(row, 6, value_item)
            
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
            
            self.stocks_table.setItem(row, 7, status_item)
        
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
        # Formater la valeur totale avec la devise de l'entreprise
        self.total_value_label.setText(f"Valeur: {self.ent_ctrl.format_amount(summary.get('total_value', 0))}")
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
        
        
        menu.addSeparator()
        
        
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
                    f"• Valeur totale: {self.ent_ctrl.format_amount(export_data['summary'].get('total_value', 0))}\n\n"
                    f"Note: Fonctionnalité d'export fichier à implémenter"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export:\n{str(e)}")