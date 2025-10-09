"""
Widget pour la gestion des entrepôts
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
    QTreeWidgetItem, QSplitter, QProgressBar, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPixmap, QIcon

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.stock.controllers.entrepot_controller import EntrepotController


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
        
        # Bloquer le champ code si on édite un entrepôt existant
        if self.warehouse is not None:
            self.code_edit.setReadOnly(True)
            self.code_edit.setStyleSheet("background-color: #f0f0f0; color: #666;")
            self.code_edit.setToolTip("Le code ne peut pas être modifié après création")
        
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
        
        # Statut actif
        self.is_active_checkbox = QCheckBox("Entrepôt actif")
        self.is_active_checkbox.setChecked(True)  # Par défaut actif
        self.is_active_checkbox.setToolTip("Décocher pour désactiver l'entrepôt sans le supprimer")
        
        # Assemblage
        layout.addLayout(form_layout)
        layout.addWidget(contact_group)
        layout.addWidget(self.is_default_checkbox)
        layout.addWidget(self.is_active_checkbox)
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
            
        self.code_edit.setText(self.warehouse['code'] or "")
        self.name_edit.setText(self.warehouse['name'] or "")
        
        # Type
        type_index = self.type_combo.findText(self.warehouse['type'] or "Principal")
        if type_index >= 0:
            self.type_combo.setCurrentIndex(type_index)
        
        self.description_edit.setPlainText(self.warehouse['description'] or "")
        self.address_edit.setPlainText(self.warehouse['address'] or "")
        
        if self.warehouse['capacity_limit']:
            try:
                self.capacity_spinbox.setValue(int(self.warehouse['capacity_limit']))
            except (ValueError, TypeError):
                self.capacity_spinbox.setValue(0)
        
        self.contact_person_edit.setText(self.warehouse['contact_person'] or "")
        self.contact_phone_edit.setText(self.warehouse['contact_phone'] or "")
        self.contact_email_edit.setText(self.warehouse['contact_email'] or "")
        self.is_default_checkbox.setChecked(self.warehouse['is_default'] or False)
        self.is_active_checkbox.setChecked(self.warehouse.get('is_active', True))
    
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
            "is_default": self.is_default_checkbox.isChecked(),
            "is_active": self.is_active_checkbox.isChecked()
        }


class EntrepotWidget(QWidget):
    """Widget principal pour la gestion des entrepôts"""
    
    # Signaux
    warehouse_selected = pyqtSignal(int)  # ID de l'entrepôt sélectionné
    warehouse_updated = pyqtSignal()  # Quand un entrepôt est mis à jour
    warehouse_created = pyqtSignal()  # Quand un entrepôt est créé
    
    def __init__(self, pos_id: int, current_user):
        super().__init__()
        self.pos_id = pos_id
        self.current_user = current_user
        self.db_manager = DatabaseManager()
        # Récupérer entreprise_id depuis pos_id
        self.entreprise_id = self.get_entreprise_id_from_pos(pos_id)
        self.controller = EntrepotController(pos_id)
        self.current_warehouses = []
        
        self.setup_ui()
        self.connect_signals()
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
        
        # En-tête avec titre et actions
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🏭 Gestion des Entrepôts")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Actions principales
        self.new_warehouse_btn = QPushButton("➕ Nouvel Entrepôt")
        self.new_warehouse_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.new_warehouse_btn.clicked.connect(self.create_new_warehouse)
        header_layout.addWidget(self.new_warehouse_btn)
        
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.clicked.connect(self.load_data)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
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
                padding: 12px 20px;
                margin-right: 2px;
                font-weight: bold;
                color: #2C3E50;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                min-width: 150px;
            }
            QTabBar::tab:selected {
                background-color: #3498DB;
                color: white;
            }
        """)
        
        # Onglet Liste des Entrepôts
        self.warehouses_list_tab = self.create_warehouses_list_tab()
        self.tab_widget.addTab(self.warehouses_list_tab, "📋 Liste des Entrepôts")
        
        # Onglet Configuration par POS
        self.config_tab = self.create_configuration_tab()
        self.tab_widget.addTab(self.config_tab, "⚙️ Configuration POS")
        
        layout.addWidget(self.tab_widget)
    
    def create_warehouses_list_tab(self) -> QWidget:
        """Créer l'onglet de liste des entrepôts"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Partie gauche - Liste des entrepôts
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Barre de recherche
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Recherche:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nom ou code d'entrepôt...")
        self.search_input.textChanged.connect(self.filter_warehouses)
        search_layout.addWidget(self.search_input)
        left_layout.addLayout(search_layout)
        
        # Tableau des entrepôts (colonnes simplifiées)
        self.warehouses_table = QTableWidget()
        self.warehouses_table.setColumnCount(4)
        self.warehouses_table.setHorizontalHeaderLabels([
            "Code", "Nom", "Stock Total Vente", "Stock Total Achat"
        ])
        self.warehouses_table.setAlternatingRowColors(True)
        self.warehouses_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.warehouses_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Désactiver l'édition directe
        self.warehouses_table.cellClicked.connect(self.on_warehouse_selected)
        self.warehouses_table.cellDoubleClicked.connect(self.on_warehouse_double_clicked)  # Double-clic pour édition
        self.warehouses_table.horizontalHeader().setStretchLastSection(True)
        left_layout.addWidget(self.warehouses_table)
        
        # Partie droite - Détails de l'entrepôt
        right_widget = QGroupBox("Détails de l'entrepôt sélectionné")
        right_widget.setMinimumWidth(350)
        right_layout = QVBoxLayout(right_widget)
        
        # Zone d'affichage des détails
        self.details_scroll_area = QTextEdit()
        self.details_scroll_area.setReadOnly(True)
        self.details_scroll_area.setPlaceholderText("Sélectionnez un entrepôt pour voir les détails...")
        right_layout.addWidget(self.details_scroll_area)
        
        # Graphique de capacité
        capacity_frame = QFrame()
        capacity_layout = QVBoxLayout(capacity_frame)
        capacity_layout.addWidget(QLabel("Utilisation de la capacité:"))
        self.capacity_progress = QProgressBar()
        self.capacity_progress.setVisible(False)
        capacity_layout.addWidget(self.capacity_progress)
        right_layout.addWidget(capacity_frame)
        
        # Layout principal avec splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([600, 350])
        layout.addWidget(splitter)
        
        return widget
    
    def create_configuration_tab(self) -> QWidget:
        """Créer l'onglet de configuration par POS"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Résumé de configuration
        summary_group = QGroupBox("Résumé de la Configuration")
        summary_layout = QFormLayout(summary_group)
        
        self.total_warehouses_label = QLabel("0")
        summary_layout.addRow("Total des entrepôts:", self.total_warehouses_label)
        
        self.active_warehouses_label = QLabel("0")
        summary_layout.addRow("Entrepôts actifs:", self.active_warehouses_label)
        
        self.default_warehouse_label = QLabel("Aucun")
        summary_layout.addRow("Entrepôt par défaut:", self.default_warehouse_label)
        
        layout.addWidget(summary_group)
        
        # Groupement par type
        types_group = QGroupBox("Entrepôts par Type")
        types_layout = QVBoxLayout(types_group)
        
        self.types_tree = QTreeWidget()
        self.types_tree.setHeaderLabels(["Type", "Nombre", "Entrepôts"])
        types_layout.addWidget(self.types_tree)
        
        layout.addWidget(types_group)
        layout.addStretch()
        
        return widget
    
    def load_data(self):
        """Charger les données des entrepôts"""
        try:
            with self.db_manager.get_session() as session:
                self.current_warehouses = self.controller.get_all_warehouses(session)
                self.populate_warehouses_table()
                self.update_configuration_summary()
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des entrepôts:\n{str(e)}")
    
    def populate_warehouses_table(self):
        """Peupler le tableau des entrepôts avec la structure simplifiée"""
        self.warehouses_table.setRowCount(len(self.current_warehouses))
        
        for row, warehouse in enumerate(self.current_warehouses):
            # Code
            self.warehouses_table.setItem(row, 0, QTableWidgetItem(warehouse['code']))
            
            # Nom (avec indicateur par défaut)
            name_item = QTableWidgetItem(warehouse['name'])
            if warehouse['is_default']:
                name_item.setBackground(QColor("#E8F5E8"))
                name_item.setText(f"⭐ {warehouse['name']}")
            self.warehouses_table.setItem(row, 1, name_item)
            
            # Stock Total Vente (sera calculé)
            self.warehouses_table.setItem(row, 2, QTableWidgetItem("Calcul..."))
            
            # Stock Total Achat (sera calculé)
            self.warehouses_table.setItem(row, 3, QTableWidgetItem("Calcul..."))
            
            # Calculer les valeurs en arrière-plan
            QTimer.singleShot(100 * row, lambda r=row, w=warehouse: self.update_warehouse_values(r, w))
        
        # Ajuster les colonnes
        self.warehouses_table.resizeColumnsToContents()
    
    def update_warehouse_values(self, row: int, warehouse):
        """Mettre à jour les valeurs de stock pour un entrepôt"""
        try:
            with self.db_manager.get_session() as session:
                stats = self.controller.get_warehouse_detailed_stats(session, warehouse['id'])
                
                # Stock Total Vente
                sale_value_item = QTableWidgetItem(f"{stats['total_sale_value']:.2f} €")
                sale_value_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.warehouses_table.setItem(row, 2, sale_value_item)
                
                # Stock Total Achat (prix d'achat depuis core_products.cost)
                cost_value_item = QTableWidgetItem(f"{stats['total_purchase_value']:.2f} €")
                cost_value_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.warehouses_table.setItem(row, 3, cost_value_item)
                
        except Exception as e:
            # En cas d'erreur, afficher des valeurs par défaut
            self.warehouses_table.setItem(row, 2, QTableWidgetItem("0.00 €"))
            self.warehouses_table.setItem(row, 3, QTableWidgetItem("0.00 €"))
    
    def on_warehouse_double_clicked(self, row: int, column: int):
        """Gestionnaire de double-clic pour édition"""
        if row < len(self.current_warehouses):
            warehouse = self.current_warehouses[row]
            self.edit_warehouse(warehouse)
    
    def update_stock_total(self, row: int, warehouse):
        """Méthode dépréciée - utiliser update_warehouse_values"""
        self.update_warehouse_values(row, warehouse)
    
    def connect_signals(self):
        """Connecter tous les signaux"""
        # Les signaux de base sont déjà connectés dans setup_ui
        pass
        
    def filter_warehouses(self):
        """Filtrer les entrepôts selon la recherche"""
        search_text = self.search_input.text().lower()
        
        for row in range(self.warehouses_table.rowCount()):
            should_show = False
            
            # Vérifier le code et le nom
            for col in [0, 1]:  # Code et Nom
                item = self.warehouses_table.item(row, col)
                if item and search_text in item.text().lower():
                    should_show = True
                    break
            
            self.warehouses_table.setRowHidden(row, not should_show)
    
    def on_warehouse_selected(self, row: int, column: int):
        """Gestionnaire de sélection d'entrepôt"""
        if row < len(self.current_warehouses):
            warehouse = self.current_warehouses[row]
            self.show_warehouse_details(warehouse)
            self.warehouse_selected.emit(warehouse['id'])  # Utiliser dict au lieu d'attribut
    
    def show_warehouse_details(self, warehouse):
        """Afficher les détails d'un entrepôt"""
        try:
            # Affichage simplifié selon les colonnes de stock_warehouse
            details_html = f"""
            <h3>🏭 {warehouse['name']}</h3>
            <p><b>Code:</b> {warehouse['code']}</p>
            <p><b>Type:</b> {warehouse['type']}</p>
            <p><b>Statut:</b> {"✅ Actif" if warehouse['is_active'] else "❌ Inactif"}</p>
            <p><b>Par défaut:</b> {"⭐ Oui" if warehouse['is_default'] else "Non"}</p>
            """
            
            # Informations optionnelles
            if warehouse.get('description'):
                details_html += f"<hr><h4>📝 Description</h4><p>{warehouse['description']}</p>"
            
            if warehouse.get('address'):
                details_html += f"<hr><h4>📍 Adresse</h4><p>{warehouse['address']}</p>"
            
            if warehouse.get('contact_person') or warehouse.get('contact_phone') or warehouse.get('contact_email'):
                details_html += "<hr><h4>👤 Contact</h4>"
                if warehouse.get('contact_person'):
                    details_html += f"<p><b>Responsable:</b> {warehouse['contact_person']}</p>"
                if warehouse.get('contact_phone'):
                    details_html += f"<p><b>Téléphone:</b> {warehouse['contact_phone']}</p>"
                if warehouse.get('contact_email'):
                    details_html += f"<p><b>Email:</b> {warehouse['contact_email']}</p>"
            
            if warehouse.get('capacity_limit'):
                details_html += f"<hr><h4>📦 Capacité</h4><p><b>Limite:</b> {warehouse['capacity_limit']}</p>"
            
            if warehouse.get('created_at'):
                details_html += f"<hr><h4>📅 Informations</h4><p><b>Créé le:</b> {warehouse['created_at']}</p>"
            
            self.details_scroll_area.setHtml(details_html)
            
        except Exception as e:
            self.details_scroll_area.setPlainText(f"Erreur lors du chargement des détails:\n{str(e)}")
    
    def update_configuration_summary(self):
        """Mettre à jour le résumé de configuration"""
        try:
            with self.db_manager.get_session() as session:
                config = self.controller.get_warehouse_configuration_by_pos(session)
                
                self.total_warehouses_label.setText(str(config['total_warehouses']))
                self.active_warehouses_label.setText(str(config['active_warehouses']))
                
                if config['default_warehouse']:
                    self.default_warehouse_label.setText(f"⭐ {config['default_warehouse']['name']}")
                else:
                    self.default_warehouse_label.setText("❌ Aucun défini")
                
                # Mise à jour de l'arbre des types
                self.types_tree.clear()
                for warehouse_type, warehouses in config['warehouses_by_type'].items():
                    type_item = QTreeWidgetItem([warehouse_type, str(len(warehouses)), ""])
                    
                    for warehouse in warehouses:
                        warehouse_item = QTreeWidgetItem([
                            warehouse['name'], 
                            "✅" if warehouse['is_active'] else "❌",
                            "⭐" if warehouse['is_default'] else ""
                        ])
                        type_item.addChild(warehouse_item)
                    
                    self.types_tree.addTopLevelItem(type_item)
                
                self.types_tree.expandAll()
                
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de la mise à jour de la configuration:\n{str(e)}")
    
    def create_new_warehouse(self):
        """Créer un nouvel entrepôt"""
        dialog = WarehouseFormDialog(self, pos_id=self.pos_id)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            warehouse_data = dialog.get_warehouse_data()
            
            try:
                with self.db_manager.get_session() as session:
                    new_warehouse = self.controller.create_warehouse(session, warehouse_data)
                    session.commit()
                    
                    QMessageBox.information(
                        self, "Succès", 
                        f"L'entrepôt '{new_warehouse['name']}' a été créé avec succès!"
                    )
                    
                    self.load_data()
                    self.warehouse_created.emit()  # Signal pour nouvel entrepôt
                    self.warehouse_updated.emit()  # Signal général de mise à jour
                    
            except ValueError as e:
                QMessageBox.warning(self, "Erreur de validation", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la création de l'entrepôt:\n{str(e)}")
    
    def edit_warehouse(self, warehouse):
        """Modifier un entrepôt"""
        dialog = WarehouseFormDialog(self, warehouse=warehouse, pos_id=self.pos_id)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            warehouse_data = dialog.get_warehouse_data()
            
            try:
                with self.db_manager.get_session() as session:
                    updated_warehouse = self.controller.update_warehouse(session, warehouse['id'], warehouse_data)
                    session.commit()
                    
                    QMessageBox.information(
                        self, "Succès", 
                        f"L'entrepôt '{updated_warehouse['name']}' a été mis à jour avec succès!"
                    )
                    
                    self.load_data()
                    self.warehouse_updated.emit()
                    
            except ValueError as e:
                QMessageBox.warning(self, "Erreur de validation", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la mise à jour de l'entrepôt:\n{str(e)}")
    
    def show_warehouse_stats(self, warehouse):
        """Afficher les statistiques détaillées d'un entrepôt"""
        try:
            with self.db_manager.get_session() as session:
                stats = self.controller.get_warehouse_statistics(session, warehouse.id)
                
                stats_text = f"""
Statistiques détaillées pour: {warehouse['name']}

📊 RÉSUMÉ GÉNÉRAL:
• Total des produits référencés: {stats['total_products']}
• Produits avec stock > 0: {stats['products_with_stock']}
• Produits en rupture (stock = 0): {stats['out_of_stock']}
• Quantité totale en stock: {stats['total_quantity']:.2f} unités
• Valeur totale du stock: {stats['total_value']:.2f} €

📈 UTILISATION:
• Capacité configurée: {warehouse.capacity_limit if warehouse.capacity_limit else 'Illimitée'}
• Pourcentage d'utilisation: {stats['capacity_used_percentage']:.1f}%" if stats['capacity_used_percentage'] is not None else "N/A"

🏢 INFORMATIONS:
• Type d'entrepôt: {warehouse.type}
• Statut: {"Actif" if warehouse['is_active'] else "Inactif"}
• Entrepôt par défaut: {"Oui" if warehouse.is_default else "Non"}
• Date de création: {warehouse.created_at.strftime('%d/%m/%Y %H:%M') if warehouse.created_at else 'N/A'}
                """
                
                QMessageBox.information(self, f"Statistiques - {warehouse['name']}", stats_text)
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des statistiques:\n{str(e)}")
    
    def link_all_products_to_warehouses(self):
        """Lier tous les produits à tous les entrepôts"""
        reply = QMessageBox.question(
            self, "Confirmation",
            "Cette opération va associer tous les produits à tous les entrepôts avec une quantité de 0.\n\n"
            "Cela peut prendre du temps si vous avez beaucoup de produits.\n\n"
            "Continuer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with self.db_manager.get_session() as session:
                    result = self.controller.link_all_products_to_warehouses(session)
                    session.commit()
                    
                    QMessageBox.information(
                        self, "Succès", 
                        f"Liaison terminée!\n\n"
                        f"• Produits traités: {result['products_count']}\n"
                        f"• Entrepôts: {result['warehouses_count']}\n"
                        f"• Nouvelles associations créées: {result['associations_created']}\n"
                        f"• Associations mises à jour: {result['associations_updated']}"
                    )
                    
                    self.load_data()
                    
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la liaison:\n{str(e)}")