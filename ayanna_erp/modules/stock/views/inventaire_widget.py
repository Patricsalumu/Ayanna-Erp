"""
Widget pour la gestion des inventaires et corrections de stock
"""

from typing import List, Optional, Dict, Any, Tuple
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
from ayanna_erp.modules.stock.controllers.inventaire_controller import InventaireController


class InventorySessionDialog(QDialog):
    """Dialog pour créer une nouvelle session d'inventaire"""
    
    def __init__(self, parent=None, pos_id=None):
        super().__init__(parent)
        self.pos_id = pos_id
        # Récupérer entreprise_id depuis pos_id
        self.entreprise_id = self.get_entreprise_id_from_pos(pos_id)
        self.controller = InventaireController(self.entreprise_id)
        self.db_manager = DatabaseManager()
        
        self.setWindowTitle("Nouvelle Session d'Inventaire")
        self.setFixedSize(500, 400)
        self.setup_ui()
        self.load_warehouses()

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
        
        # Titre
        title = QLabel("📋 Créer une Session d'Inventaire")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Configuration de l'inventaire
        config_group = QGroupBox("Configuration de l'Inventaire")
        config_layout = QFormLayout(config_group)
        
        # Nom de la session
        self.session_name = QLineEdit()
        self.session_name.setPlaceholderText("Nom de la session (ex: Inventaire Octobre 2025)")
        config_layout.addRow("Nom de la session*:", self.session_name)
        
        # Entrepôt
        self.warehouse_combo = QComboBox()
        config_layout.addRow("Entrepôt*:", self.warehouse_combo)
        
        # Type d'inventaire
        self.inventory_type = QComboBox()
        self.inventory_type.addItems([
            "Inventaire Complet",
            "Inventaire Partiel",
            "Contrôle Cyclique",
            "Vérification Urgente"
        ])
        config_layout.addRow("Type d'inventaire:", self.inventory_type)
        
        # Date prévue
        self.scheduled_date = QDateEdit()
        self.scheduled_date.setDate(QDate.currentDate())
        self.scheduled_date.setCalendarPopup(True)
        config_layout.addRow("Date prévue:", self.scheduled_date)
        
        # Notes
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        self.notes.setPlaceholderText("Notes ou instructions pour l'inventaire...")
        config_layout.addRow("Notes:", self.notes)
        
        layout.addWidget(config_group)
        
        # Options avancées
        options_group = QGroupBox("Options Avancées")
        options_layout = QVBoxLayout(options_group)
        
        self.include_zero_stock = QCheckBox("Inclure les produits à stock zéro")
        self.include_zero_stock.setChecked(True)
        options_layout.addWidget(self.include_zero_stock)
        
        self.auto_freeze_stock = QCheckBox("Geler automatiquement les mouvements pendant l'inventaire")
        options_layout.addWidget(self.auto_freeze_stock)
        
        self.send_notifications = QCheckBox("Envoyer des notifications aux responsables")
        self.send_notifications.setChecked(True)
        options_layout.addWidget(self.send_notifications)
        
        layout.addWidget(options_group)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("📋 Créer l'Inventaire")
        create_btn.setStyleSheet("""
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
        create_btn.clicked.connect(self.create_inventory)
        buttons_layout.addWidget(create_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_warehouses(self):
        """Charger la liste des entrepôts"""
        try:
            with self.db_manager.get_session() as session:
                from ayanna_erp.modules.boutique.model.models import ShopWarehouse
                warehouses = session.query(ShopWarehouse).filter(
                    ShopWarehouse.pos_id == self.pos_id,
                    ShopWarehouse.is_active == True
                ).order_by(ShopWarehouse.name).all()
                
                self.warehouse_combo.clear()
                self.warehouse_combo.addItem("-- Sélectionner un entrepôt --", None)
                for warehouse in warehouses:
                    self.warehouse_combo.addItem(f"{warehouse.name} ({warehouse.code})", warehouse.id)
                    
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des entrepôts:\n{str(e)}")
    
    def create_inventory(self):
        """Créer la session d'inventaire"""
        if not self.validate_form():
            return
        
        try:
            with self.db_manager.get_session() as session:
                inventory_data = {
                    'session_name': self.session_name.text().strip(),
                    'warehouse_id': self.warehouse_combo.currentData(),
                    'inventory_type': self.inventory_type.currentText(),
                    'scheduled_date': self.scheduled_date.date().toPython(),
                    'notes': self.notes.toPlainText().strip() or None,
                    'include_zero_stock': self.include_zero_stock.isChecked(),
                    'auto_freeze_stock': self.auto_freeze_stock.isChecked(),
                    'send_notifications': self.send_notifications.isChecked()
                }
                
                inventory = self.controller.create_inventory_session(session, inventory_data)
                session.commit()
                
                QMessageBox.information(
                    self, "Succès",
                    f"Session d'inventaire créée avec succès!\n"
                    f"Référence: {inventory.reference}\n"
                    f"Vous pouvez maintenant commencer les comptages."
                )
                
                self.accept()
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la création de l'inventaire:\n{str(e)}")
    
    def validate_form(self):
        """Valider le formulaire"""
        if not self.session_name.text().strip():
            QMessageBox.warning(self, "Validation", "Le nom de la session est obligatoire.")
            self.session_name.setFocus()
            return False
        
        if not self.warehouse_combo.currentData():
            QMessageBox.warning(self, "Validation", "Veuillez sélectionner un entrepôt.")
            return False
        
        return True


class CountingDialog(QDialog):
    """Dialog pour saisir les comptages"""
    
    def __init__(self, parent=None, inventory_id=None, controller=None):
        super().__init__(parent)
        self.inventory_id = inventory_id
        self.controller = controller
        self.products_to_count = []
        
        self.setWindowTitle("Saisie des Comptages")
        self.setFixedSize(800, 600)
        self.setup_ui()
        self.load_products_to_count()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # En-tête
        header_layout = QHBoxLayout()
        title_label = QLabel("📊 Saisie des Comptages")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        save_btn = QPushButton("💾 Sauvegarder")
        save_btn.clicked.connect(self.save_counts)
        header_layout.addWidget(save_btn)
        
        close_btn = QPushButton("❌ Fermer")
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # Tableau des comptages
        self.counting_table = QTableWidget()
        self.counting_table.setColumnCount(7)
        self.counting_table.setHorizontalHeaderLabels([
            "Produit", "Code", "Stock Système", "Compté", "Écart", "Valeur Écart", "Notes"
        ])
        self.counting_table.setAlternatingRowColors(True)
        layout.addWidget(self.counting_table)
        
        # Résumé
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
        
        self.total_products_label = QLabel("Total produits: 0")
        summary_layout.addWidget(self.total_products_label)
        
        self.counted_products_label = QLabel("Comptés: 0")
        summary_layout.addWidget(self.counted_products_label)
        
        self.total_variance_label = QLabel("Écart total: 0.00 €")
        summary_layout.addWidget(self.total_variance_label)
        
        summary_layout.addStretch()
        layout.addWidget(summary_frame)
    
    def load_products_to_count(self):
        """Charger les produits à compter"""
        try:
            with self.controller.db_manager.get_session() as session:
                self.products_to_count = self.controller.get_inventory_products(session, self.inventory_id)
                self.populate_counting_table()
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des produits:\n{str(e)}")
    
    def populate_counting_table(self):
        """Peupler le tableau de comptage"""
        self.counting_table.setRowCount(len(self.products_to_count))
        
        for row, product in enumerate(self.products_to_count):
            # Produit
            self.counting_table.setItem(row, 0, QTableWidgetItem(product['product_name']))
            
            # Code
            self.counting_table.setItem(row, 1, QTableWidgetItem(product.get('product_code', '')))
            
            # Stock système
            system_stock = product['system_stock']
            system_item = QTableWidgetItem(f"{system_stock:.2f}")
            system_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            system_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Non modifiable
            self.counting_table.setItem(row, 2, system_item)
            
            # Compté (modifiable)
            counted_item = QTableWidgetItem("0.00")
            counted_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.counting_table.setItem(row, 3, counted_item)
            
            # Écart (calculé automatiquement)
            variance_item = QTableWidgetItem("0.00")
            variance_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            variance_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Non modifiable
            self.counting_table.setItem(row, 4, variance_item)
            
            # Valeur écart
            value_variance_item = QTableWidgetItem("0.00 €")
            value_variance_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            value_variance_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Non modifiable
            self.counting_table.setItem(row, 5, value_variance_item)
            
            # Notes
            self.counting_table.setItem(row, 6, QTableWidgetItem(""))
        
        # Connecter la modification pour recalculer automatiquement
        self.counting_table.itemChanged.connect(self.recalculate_variance)
        self.update_summary()
    
    def recalculate_variance(self, item):
        """Recalculer l'écart quand le comptage change"""
        if item.column() == 3:  # Colonne "Compté"
            row = item.row()
            try:
                # Récupérer les valeurs
                system_stock = float(self.counting_table.item(row, 2).text())
                counted = float(item.text() or "0")
                
                # Calculer l'écart
                variance = counted - system_stock
                
                # Mettre à jour l'écart
                variance_item = self.counting_table.item(row, 4)
                variance_item.setText(f"{variance:.2f}")
                
                # Colorer selon l'écart
                if variance > 0:
                    variance_item.setBackground(QColor("#d4edda"))  # Vert clair
                elif variance < 0:
                    variance_item.setBackground(QColor("#f8d7da"))  # Rouge clair
                else:
                    variance_item.setBackground(QColor("#ffffff"))  # Blanc
                
                # Calculer la valeur de l'écart (avec coût unitaire si disponible)
                unit_cost = self.products_to_count[row].get('unit_cost', 0)
                value_variance = variance * float(unit_cost)
                value_variance_item = self.counting_table.item(row, 5)
                value_variance_item.setText(f"{value_variance:.2f} €")
                
                # Mettre à jour le résumé
                self.update_summary()
                
            except ValueError:
                item.setText("0.00")
    
    def update_summary(self):
        """Mettre à jour le résumé"""
        total_products = self.counting_table.rowCount()
        counted_products = 0
        total_variance_value = 0.0
        
        for row in range(total_products):
            counted_item = self.counting_table.item(row, 3)
            if counted_item and counted_item.text() and float(counted_item.text()) > 0:
                counted_products += 1
            
            value_variance_item = self.counting_table.item(row, 5)
            if value_variance_item:
                try:
                    value_text = value_variance_item.text().replace(' €', '')
                    total_variance_value += float(value_text)
                except ValueError:
                    pass
        
        self.total_products_label.setText(f"Total produits: {total_products}")
        self.counted_products_label.setText(f"Comptés: {counted_products}")
        self.total_variance_label.setText(f"Écart total: {total_variance_value:.2f} €")
        
        # Colorer l'écart total
        if total_variance_value > 0:
            self.total_variance_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        elif total_variance_value < 0:
            self.total_variance_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        else:
            self.total_variance_label.setStyleSheet("color: #333; font-weight: bold;")
    
    def save_counts(self):
        """Sauvegarder les comptages"""
        try:
            counting_data = []
            
            for row in range(self.counting_table.rowCount()):
                product = self.products_to_count[row]
                counted_item = self.counting_table.item(row, 3)
                notes_item = self.counting_table.item(row, 6)
                
                counted_qty = float(counted_item.text() or "0") if counted_item else 0
                notes = notes_item.text() if notes_item else ""
                
                counting_data.append({
                    'product_id': product['product_id'],
                    'system_stock': product['system_stock'],
                    'counted_stock': counted_qty,
                    'variance': counted_qty - product['system_stock'],
                    'notes': notes
                })
            
            with self.controller.db_manager.get_session() as session:
                self.controller.save_inventory_counts(session, self.inventory_id, counting_data)
                session.commit()
                
                QMessageBox.information(self, "Succès", "Comptages sauvegardés avec succès!")
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde:\n{str(e)}")


class InventaireWidget(QWidget):
    """Widget principal pour la gestion des inventaires"""
    
    # Signaux
    inventory_created = pyqtSignal()  # Quand un inventaire est créé
    inventory_completed = pyqtSignal()  # Quand un inventaire est terminé
    
    def __init__(self, pos_id: int, current_user):
        super().__init__()
        self.pos_id = pos_id
        self.current_user = current_user
        # Récupérer entreprise_id depuis pos_id
        self.entreprise_id = self.get_entreprise_id_from_pos(pos_id)
        self.controller = InventaireController(self.entreprise_id)
        self.db_manager = DatabaseManager()
        self.current_inventories = []
        
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
        
        title_label = QLabel("📋 Gestion des Inventaires")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Actions
        self.new_inventory_btn = QPushButton("📋 Nouvel Inventaire")
        self.new_inventory_btn.setStyleSheet("""
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
        self.new_inventory_btn.clicked.connect(self.create_new_inventory)
        header_layout.addWidget(self.new_inventory_btn)
        
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.clicked.connect(self.load_data)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Onglets
        tabs = QTabWidget()
        
        # Onglet Sessions d'Inventaire
        sessions_tab = self.create_sessions_tab()
        tabs.addTab(sessions_tab, "📋 Sessions d'Inventaire")
        
        # Onglet Corrections de Stock
        corrections_tab = self.create_corrections_tab()
        tabs.addTab(corrections_tab, "🔧 Corrections de Stock")
        
        # Onglet Historique
        history_tab = self.create_history_tab()
        tabs.addTab(history_tab, "📈 Historique")
        
        layout.addWidget(tabs)
    
    def create_sessions_tab(self) -> QWidget:
        """Créer l'onglet des sessions d'inventaire"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filtres
        filters_layout = QHBoxLayout()
        
        filters_layout.addWidget(QLabel("Statut:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Tous", "En Cours", "Terminés", "Annulés"])
        self.status_filter.currentTextChanged.connect(self.filter_inventories)
        filters_layout.addWidget(self.status_filter)
        
        filters_layout.addWidget(QLabel("Entrepôt:"))
        self.warehouse_filter = QComboBox()
        self.warehouse_filter.addItem("Tous les entrepôts", None)
        filters_layout.addWidget(self.warehouse_filter)
        
        filters_layout.addStretch()
        layout.addLayout(filters_layout)
        
        # Tableau des inventaires
        self.inventories_table = QTableWidget()
        self.inventories_table.setColumnCount(8)
        self.inventories_table.setHorizontalHeaderLabels([
            "Référence", "Session", "Entrepôt", "Type", "Statut", "Créé le", "Progression", "Actions"
        ])
        self.inventories_table.setAlternatingRowColors(True)
        self.inventories_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.inventories_table)
        
        return widget
    
    def create_corrections_tab(self) -> QWidget:
        """Créer l'onglet des corrections de stock"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Outils de correction rapide
        tools_group = QGroupBox("Outils de Correction Rapide")
        tools_layout = QHBoxLayout(tools_group)
        
        manual_correction_btn = QPushButton("✏️ Correction Manuelle")
        manual_correction_btn.clicked.connect(self.open_manual_correction)
        tools_layout.addWidget(manual_correction_btn)
        
        import_correction_btn = QPushButton("📥 Import Corrections")
        import_correction_btn.clicked.connect(self.import_corrections)
        tools_layout.addWidget(import_correction_btn)
        
        batch_correction_btn = QPushButton("🔧 Correction en Lot")
        batch_correction_btn.clicked.connect(self.open_batch_correction)
        tools_layout.addWidget(batch_correction_btn)
        
        tools_layout.addStretch()
        layout.addWidget(tools_group)
        
        # Tableau des corrections récentes
        self.corrections_table = QTableWidget()
        self.corrections_table.setColumnCount(7)
        self.corrections_table.setHorizontalHeaderLabels([
            "Date", "Produit", "Entrepôt", "Ancien Stock", "Nouveau Stock", "Écart", "Motif"
        ])
        self.corrections_table.setAlternatingRowColors(True)
        layout.addWidget(self.corrections_table)
        
        return widget
    
    def create_history_tab(self) -> QWidget:
        """Créer l'onglet d'historique"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filtres temporels
        filters_layout = QHBoxLayout()
        
        filters_layout.addWidget(QLabel("Période:"))
        self.period_filter = QComboBox()
        self.period_filter.addItems(["30 derniers jours", "3 derniers mois", "6 derniers mois", "Cette année"])
        filters_layout.addWidget(self.period_filter)
        
        filters_layout.addStretch()
        layout.addLayout(filters_layout)
        
        # Tableau de l'historique
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Date", "Type", "Référence", "Entrepôt", "Responsable", "Résumé"
        ])
        self.history_table.setAlternatingRowColors(True)
        layout.addWidget(self.history_table)
        
        return widget
    
    def load_data(self):
        """Charger les données"""
        try:
            with self.db_manager.get_session() as session:
                # Charger les inventaires
                self.current_inventories = self.controller.get_all_inventories(session)
                
                # Charger les entrepôts pour les filtres
                self.load_warehouses_for_filters(session)
                
                # Peupler les tableaux
                self.populate_inventories_table()
                self.load_recent_corrections()
                self.load_history()
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des données:\n{str(e)}")
    
    def load_warehouses_for_filters(self, session):
        """Charger les entrepôts pour les filtres"""
        try:
            from ayanna_erp.modules.boutique.model.models import ShopWarehouse
            warehouses = session.query(ShopWarehouse).filter(
                ShopWarehouse.pos_id == self.pos_id,
                ShopWarehouse.is_active == True
            ).order_by(ShopWarehouse.name).all()
            
            current_value = self.warehouse_filter.currentData()
            self.warehouse_filter.clear()
            self.warehouse_filter.addItem("Tous les entrepôts", None)
            
            for warehouse in warehouses:
                self.warehouse_filter.addItem(f"{warehouse.name} ({warehouse.code})", warehouse.id)
            
            # Restaurer la sélection si possible
            if current_value:
                index = self.warehouse_filter.findData(current_value)
                if index >= 0:
                    self.warehouse_filter.setCurrentIndex(index)
            
        except Exception as e:
            print(f"Erreur lors du chargement des entrepôts: {e}")
    
    def populate_inventories_table(self):
        """Peupler le tableau des inventaires"""
        filtered_inventories = self.filter_inventories_data()
        
        self.inventories_table.setRowCount(len(filtered_inventories))
        
        for row, inventory in enumerate(filtered_inventories):
            # Référence
            self.inventories_table.setItem(row, 0, QTableWidgetItem(inventory.get('reference', 'N/A')))
            
            # Session
            self.inventories_table.setItem(row, 1, QTableWidgetItem(inventory.get('session_name', 'N/A')))
            
            # Entrepôt
            warehouse_name = f"{inventory.get('warehouse_name', 'N/A')} ({inventory.get('warehouse_code', 'N/A')})"
            self.inventories_table.setItem(row, 2, QTableWidgetItem(warehouse_name))
            
            # Type
            self.inventories_table.setItem(row, 3, QTableWidgetItem(inventory.get('inventory_type', 'N/A')))
            
            # Statut
            status_icons = {
                'DRAFT': '📝 Brouillon',
                'IN_PROGRESS': '🔄 En Cours',
                'COMPLETED': '✅ Terminé',
                'CANCELLED': '❌ Annulé'
            }
            status = status_icons.get(inventory.get('status'), inventory.get('status', 'N/A'))
            status_item = QTableWidgetItem(status)
            
            # Couleur selon le statut
            status_colors = {
                'DRAFT': QColor("#fff3cd"),
                'IN_PROGRESS': QColor("#d1ecf1"),
                'COMPLETED': QColor("#d4edda"),
                'CANCELLED': QColor("#f8d7da")
            }
            if inventory.get('status') in status_colors:
                status_item.setBackground(status_colors[inventory.get('status')])
            
            self.inventories_table.setItem(row, 4, status_item)
            
            # Date de création
            created_date = inventory.get('created_at', datetime.now())
            if isinstance(created_date, datetime):
                date_str = created_date.strftime('%d/%m/%Y %H:%M')
            else:
                date_str = "N/A"
            self.inventories_table.setItem(row, 5, QTableWidgetItem(date_str))
            
            # Progression
            progress = inventory.get('progress_percentage', 0)
            progress_item = QTableWidgetItem(f"{progress:.1f}%")
            progress_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.inventories_table.setItem(row, 6, progress_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            
            if inventory.get('status') in ['DRAFT', 'IN_PROGRESS']:
                count_btn = QPushButton("📊")
                count_btn.setToolTip("Saisir comptages")
                count_btn.setMaximumWidth(30)
                count_btn.clicked.connect(lambda checked, inv=inventory: self.open_counting(inv))
                actions_layout.addWidget(count_btn)
                
                if inventory.get('status') == 'IN_PROGRESS':
                    complete_btn = QPushButton("✅")
                    complete_btn.setToolTip("Terminer l'inventaire")
                    complete_btn.setMaximumWidth(30)
                    complete_btn.clicked.connect(lambda checked, inv=inventory: self.complete_inventory(inv))
                    actions_layout.addWidget(complete_btn)
            
            view_btn = QPushButton("👁️")
            view_btn.setToolTip("Voir les détails")
            view_btn.setMaximumWidth(30)
            view_btn.clicked.connect(lambda checked, inv=inventory: self.view_inventory_details(inv))
            actions_layout.addWidget(view_btn)
            
            self.inventories_table.setCellWidget(row, 7, actions_widget)
        
        self.inventories_table.resizeColumnsToContents()
    
    def filter_inventories_data(self):
        """Filtrer les données d'inventaires"""
        filtered = self.current_inventories.copy()
        
        # Filtre par statut
        status_filter = self.status_filter.currentText()
        if status_filter != "Tous":
            status_map = {
                "En Cours": "IN_PROGRESS",
                "Terminés": "COMPLETED",
                "Annulés": "CANCELLED"
            }
            target_status = status_map.get(status_filter)
            if target_status:
                filtered = [i for i in filtered if i.get('status') == target_status]
        
        # Filtre par entrepôt
        warehouse_id = self.warehouse_filter.currentData()
        if warehouse_id:
            filtered = [i for i in filtered if i.get('warehouse_id') == warehouse_id]
        
        return filtered
    
    def filter_inventories(self):
        """Appliquer les filtres aux inventaires"""
        self.populate_inventories_table()
    
    def create_new_inventory(self):
        """Créer un nouvel inventaire"""
        dialog = InventorySessionDialog(self, pos_id=self.pos_id)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()
            self.inventory_created.emit()
            
            QMessageBox.information(
                self, "Succès",
                "Session d'inventaire créée avec succès!\n"
                "Vous pouvez maintenant commencer les comptages."
            )
    
    def open_counting(self, inventory):
        """Ouvrir la saisie des comptages"""
        dialog = CountingDialog(self, inventory_id=inventory.get('id'), controller=self.controller)
        dialog.exec()
        
        # Recharger les données
        self.load_data()
    
    def complete_inventory(self, inventory):
        """Terminer un inventaire"""
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Terminer l'inventaire '{inventory.get('session_name')}'?\n\n"
            "Cette action appliquera toutes les corrections de stock et ne pourra pas être annulée.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with self.db_manager.get_session() as session:
                    self.controller.complete_inventory(session, inventory.get('id'))
                    session.commit()
                    
                    QMessageBox.information(self, "Succès", "Inventaire terminé avec succès!")
                    self.load_data()
                    self.inventory_completed.emit()
                    
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la finalisation:\n{str(e)}")
    
    def view_inventory_details(self, inventory):
        """Voir les détails d'un inventaire"""
        # TODO: Créer un dialog détaillé pour l'inventaire
        QMessageBox.information(
            self, "Détails de l'Inventaire",
            f"Référence: {inventory.get('reference')}\n"
            f"Session: {inventory.get('session_name')}\n"
            f"Type: {inventory.get('inventory_type')}\n"
            f"Statut: {inventory.get('status')}\n"
            f"Progression: {inventory.get('progress_percentage', 0):.1f}%"
        )
    
    def open_manual_correction(self):
        """Ouvrir la correction manuelle"""
        QMessageBox.information(self, "Correction Manuelle", "Fonctionnalité de correction manuelle à implémenter.")
    
    def import_corrections(self):
        """Importer des corrections depuis un fichier"""
        QMessageBox.information(self, "Import Corrections", "Fonctionnalité d'import de corrections à implémenter.")
    
    def open_batch_correction(self):
        """Ouvrir la correction en lot"""
        QMessageBox.information(self, "Correction en Lot", "Fonctionnalité de correction en lot à implémenter.")
    
    def load_recent_corrections(self):
        """Charger les corrections récentes"""
        # TODO: Implémenter le chargement des corrections récentes
        self.corrections_table.setRowCount(0)
    
    def load_history(self):
        """Charger l'historique"""
        # TODO: Implémenter le chargement de l'historique
        self.history_table.setRowCount(0)