"""
Widget pour la gestion des inventaires et corrections de stock
"""

from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy import text
from sqlalchemy import text
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton, 
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, 
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout, QTextEdit, 
    QDoubleSpinBox, QSpinBox, QCheckBox, QTabWidget, QTreeWidget, 
    QTreeWidgetItem, QSplitter, QProgressBar, QFrame, QDateEdit, QFileDialog
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QDate
from PyQt6.QtGui import QFont, QColor, QPixmap, QIcon

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.stock.controllers.inventaire_controller import InventaireController
from ayanna_erp.modules.stock.models import StockWarehouse, StockInventaire
from ayanna_erp.core.entreprise_controller import EntrepriseController
from sqlalchemy.orm import joinedload


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
        # Afficher la sélection de produits seulement si 'Inventaire Partiel' est choisi
        self.inventory_type.currentTextChanged.connect(self.on_inventory_type_changed)
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
        # Zone de sélection des produits (visible pour inventaire partiel)
        self.products_selection_group = QGroupBox("Sélection des Produits (Inventaire Partiel)")
        products_layout = QVBoxLayout(self.products_selection_group)
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(4)
        self.products_table.setHorizontalHeaderLabels(["Produit", "Code", "Stock Actuel", "Entrepôt"])
        self.products_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.products_table.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)
        self.products_table.setAlternatingRowColors(True)
        products_layout.addWidget(self.products_table)
        self.products_selection_group.setVisible(False)
        layout.addWidget(self.products_selection_group)
        
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
    
    def on_inventory_type_changed(self, text: str):
        """Afficher / masquer la sélection de produits selon le type d'inventaire."""
        if text and 'Partiel' in text:
            self.products_selection_group.setVisible(True)
            # Précharger les produits si un entrepôt est sélectionné
            wid = self.warehouse_combo.currentData()
            if wid:
                try:
                    self.load_products_for_selection(wid)
                except Exception:
                    pass
        else:
            self.products_selection_group.setVisible(False)

    def load_products_for_selection(self, warehouse_id: int):
        """Charger les produits (pour sélection) depuis le controller pour un entrepôt donné."""
        try:
            products = self.controller.get_products_for_inventory(warehouse_id)
            # Normaliser la liste et remplir le tableau
            self.products_table.setRowCount(len(products))
            for row, p in enumerate(products):
                name_item = QTableWidgetItem(p.get('product_name', f"Produit {p.get('product_id')}") )
                code_item = QTableWidgetItem(p.get('product_code', ''))
                stock_val = p.get('current_quantity') if 'current_quantity' in p else p.get('quantity', 0)
                stock_item = QTableWidgetItem(str(stock_val))
                warehouse_name = p.get('warehouse_name', '')
                warehouse_item = QTableWidgetItem(warehouse_name)

                # Store product_id in UserRole for later retrieval
                name_item.setData(Qt.ItemDataRole.UserRole, p.get('product_id'))

                self.products_table.setItem(row, 0, name_item)
                self.products_table.setItem(row, 1, code_item)
                self.products_table.setItem(row, 2, stock_item)
                self.products_table.setItem(row, 3, warehouse_item)

            self.products_table.resizeColumnsToContents()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des produits pour sélection:\n{str(e)}")
    def load_warehouses(self):
        """Charger la liste des entrepôts"""
        try:
            with self.db_manager.get_session() as session:
                warehouses = session.query(StockWarehouse).filter(
                    StockWarehouse.entreprise_id == self.entreprise_id,
                    StockWarehouse.is_active == True
                ).order_by(StockWarehouse.name).all()
                
                self.warehouse_combo.clear()
                self.warehouse_combo.addItem("-- Sélectionner un entrepôt --", None)
                for warehouse in warehouses:
                    self.warehouse_combo.addItem(f"{warehouse.name} ({warehouse.code})", warehouse.id)
                # si inventaire partiel et un entrepôt est déjà sélectionné, précharger les produits
                if 'Partiel' in self.inventory_type.currentText() and self.warehouse_combo.currentData():
                    try:
                        self.load_products_for_selection(self.warehouse_combo.currentData())
                    except Exception:
                        pass
                    
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
                    'scheduled_date': self.scheduled_date.date().toPyDate(),
                    'notes': self.notes.toPlainText().strip() or None,
                    'include_zero_stock': self.include_zero_stock.isChecked(),
                    'auto_freeze_stock': self.auto_freeze_stock.isChecked(),
                    'send_notifications': self.send_notifications.isChecked()
                }
                
                # Pour inventaire partiel, collecter les produits sélectionnés
                if 'Partiel' in inventory_data['inventory_type']:
                    selected_rows = self.products_table.selectionModel().selectedRows()
                    selected_product_ids = []
                    for index in selected_rows:
                        row = index.row()
                        name_item = self.products_table.item(row, 0)
                        if name_item:
                            pid = name_item.data(Qt.ItemDataRole.UserRole)
                            if pid:
                                selected_product_ids.append(pid)
                    inventory_data['product_ids'] = selected_product_ids
                
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
        
        # Validation pour inventaire partiel
        if 'Partiel' in self.inventory_type.currentText():
            selected_rows = self.products_table.selectionModel().selectedRows()
            if not selected_rows:
                QMessageBox.warning(self, "Validation", "Veuillez sélectionner au moins un produit pour l'inventaire partiel.")
                return False
        
        return True


class CountingDialog(QDialog):
    """Dialog pour saisir les comptages"""
    
    def __init__(self, parent=None, inventory_id=None, controller=None):
        super().__init__(parent)
        self.inventory_id = inventory_id
        self.controller = controller
        self.products_to_count = []
        self.ent_ctrl = EntrepriseController()
        
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
        
        export_pdf_btn = QPushButton("📄 Exporter PDF")
        export_pdf_btn.clicked.connect(self.export_inventory_pdf)
        header_layout.addWidget(export_pdf_btn)
        
        close_btn = QPushButton("❌ Fermer")
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # Tableau des comptages
        self.counting_table = QTableWidget()
        self.counting_table.setColumnCount(8)
        self.counting_table.setHorizontalHeaderLabels([
            "Produit", "Code", "Stock Système", "Compté", "Écart", "Écart Achat", "Écart Vente", "Notes"
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
            system_item = QTableWidgetItem(f"{self.ent_ctrl.format_amount(system_stock, show_symbol=False)}")
            system_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            system_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Non modifiable
            # Garder la valeur numérique en UserRole pour les calculs
            system_item.setData(Qt.ItemDataRole.UserRole, float(system_stock))
            self.counting_table.setItem(row, 2, system_item)
            
            # Compté (modifiable) - charger la valeur existante si elle existe
            counted_stock = product.get('counted_stock', 0.0)
            counted_item = QTableWidgetItem(f"{self.ent_ctrl.format_amount(counted_stock, show_symbol=False)}")
            counted_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            counted_item.setData(Qt.ItemDataRole.UserRole, float(counted_stock))
            self.counting_table.setItem(row, 3, counted_item)
            
            # Écart (calculé automatiquement)
            variance = product.get('variance', 0.0)
            variance_item = QTableWidgetItem(f"{self.ent_ctrl.format_amount(variance, show_symbol=False)}")
            variance_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            variance_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Non modifiable
            variance_item.setData(Qt.ItemDataRole.UserRole, float(variance))
            self.counting_table.setItem(row, 4, variance_item)
            
            # Écart Achat
            variance_purchase = product.get('variance_value_purchase', 0.0)
            purchase_item = QTableWidgetItem(f"{self.ent_ctrl.format_amount(variance_purchase)}")
            purchase_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            purchase_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Non modifiable
            purchase_item.setData(Qt.ItemDataRole.UserRole, float(variance_purchase))
            self.counting_table.setItem(row, 5, purchase_item)
            
            # Écart Vente
            variance_sale = product.get('variance_value_sale', 0.0)
            sale_item = QTableWidgetItem(f"{self.ent_ctrl.format_amount(variance_sale)}")
            sale_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            sale_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Non modifiable
            sale_item.setData(Qt.ItemDataRole.UserRole, float(variance_sale))
            self.counting_table.setItem(row, 6, sale_item)
            
            # Notes
            notes = product.get('notes', '')
            self.counting_table.setItem(row, 7, QTableWidgetItem(notes))
        
        # Connecter la modification pour recalculer automatiquement
        self.counting_table.itemChanged.connect(self.recalculate_variance)
        self.update_summary()
    
    def recalculate_variance(self, item):
        """Recalculer l'écart quand le comptage change"""
        if item.column() == 3:  # Colonne "Compté"
            row = item.row()
            try:
                # Récupérer les valeurs (préférer les UserRole si disponibles pour éviter le parsing)
                system_item = self.counting_table.item(row, 2)
                if system_item and system_item.data(Qt.ItemDataRole.UserRole) is not None:
                    system_stock = float(system_item.data(Qt.ItemDataRole.UserRole))
                else:
                    # enlever séparateurs d'espaces
                    system_stock = float(self.counting_table.item(row, 2).text().replace(' ', '') or 0)

                # Counted peut provenir d'une saisie utilisateur ; tolérer les espaces
                counted_text = (item.text() or "0").replace(' ', '')
                counted = float(counted_text)
                
                # Stocker la valeur numérique
                item.setData(Qt.ItemDataRole.UserRole, counted)
                
                # Calculer l'écart
                variance = counted - system_stock
                
                # Mettre à jour l'écart
                variance_item = self.counting_table.item(row, 4)
                variance_item.setText(f"{self.ent_ctrl.format_amount(variance, show_symbol=False)}")
                variance_item.setData(Qt.ItemDataRole.UserRole, float(variance))
                
                # Colorer selon l'écart
                if variance > 0:
                    variance_item.setBackground(QColor("#d4edda"))  # Vert clair
                elif variance < 0:
                    variance_item.setBackground(QColor("#f8d7da"))  # Rouge clair
                else:
                    variance_item.setBackground(QColor("#ffffff"))  # Blanc
                
                # Récupérer les prix depuis les données du produit
                product = self.products_to_count[row]
                unit_cost = product.get('unit_cost', 0)
                selling_price = product.get('selling_price', 0)
                
                # Calculer la valeur de l'écart à l'achat
                value_variance_purchase = variance * float(unit_cost)
                purchase_item = self.counting_table.item(row, 5)
                purchase_item.setText(f"{self.ent_ctrl.format_amount(value_variance_purchase)}")
                purchase_item.setData(Qt.ItemDataRole.UserRole, float(value_variance_purchase))
                
                # Calculer la valeur de l'écart à la vente
                value_variance_sale = variance * float(selling_price)
                sale_item = self.counting_table.item(row, 6)
                sale_item.setText(f"{self.ent_ctrl.format_amount(value_variance_sale)}")
                sale_item.setData(Qt.ItemDataRole.UserRole, float(value_variance_sale))
                
                # Mettre à jour le résumé
                self.update_summary()
                
            except ValueError:
                item.setText("0.00")
    
    def update_summary(self):
        """Mettre à jour le résumé"""
        total_products = self.counting_table.rowCount()
        counted_products = 0
        total_variance_value_purchase = 0.0
        total_variance_value_sale = 0.0
        
        for row in range(total_products):
            counted_item = self.counting_table.item(row, 3)
            # Lire la valeur numérique depuis UserRole si présente, sinon parser le texte
            counted_val = None
            if counted_item:
                if counted_item.data(Qt.ItemDataRole.UserRole) is not None:
                    counted_val = float(counted_item.data(Qt.ItemDataRole.UserRole))
                else:
                    try:
                        counted_val = float(counted_item.text().replace(' ', ''))
                    except Exception:
                        counted_val = 0
            if counted_val and counted_val > 0:
                counted_products += 1
            
            # Agréger les écarts à l'achat et à la vente
            purchase_item = self.counting_table.item(row, 5)
            if purchase_item and purchase_item.data(Qt.ItemDataRole.UserRole) is not None:
                total_variance_value_purchase += float(purchase_item.data(Qt.ItemDataRole.UserRole))
            
            sale_item = self.counting_table.item(row, 6)
            if sale_item and sale_item.data(Qt.ItemDataRole.UserRole) is not None:
                total_variance_value_sale += float(sale_item.data(Qt.ItemDataRole.UserRole))
        
        self.total_products_label.setText(f"Total produits: {total_products}")
        self.counted_products_label.setText(f"Comptés: {counted_products}")
        
        # Afficher les écarts totaux (achat et vente)
        purchase_text = f"Écart achat: {self.ent_ctrl.format_amount(total_variance_value_purchase)}"
        sale_text = f"Écart vente: {self.ent_ctrl.format_amount(total_variance_value_sale)}"
        self.total_variance_label.setText(f"{purchase_text} | {sale_text}")
        
        # Colorer selon l'écart (utiliser l'écart à l'achat pour la couleur)
        if total_variance_value_purchase > 0:
            self.total_variance_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        elif total_variance_value_purchase < 0:
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
                notes_item = self.counting_table.item(row, 7)  # Notes sont maintenant en colonne 7
                
                counted_qty = float(counted_item.data(Qt.ItemDataRole.UserRole) or 0) if counted_item else 0
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
                
                # Mettre à jour le statut de l'inventaire à IN_PROGRESS s'il était DRAFT
                inventory = session.query(StockInventaire).filter(StockInventaire.id == self.inventory_id).first()
                if inventory and inventory.status == 'DRAFT':
                    inventory.status = 'IN_PROGRESS'
                    inventory.started_date = datetime.now()
                
                session.commit()
                
                QMessageBox.information(self, "Succès", "Comptages sauvegardés avec succès!")
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde:\n{str(e)}")

    def export_inventory_pdf(self):
        """Exporter l'inventaire en PDF professionnel"""
        try:
            # Sélectionner le fichier de destination
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Exporter l'inventaire en PDF", 
                f"inventaire_{self.inventory_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                "Fichiers PDF (*.pdf)"
            )
            
            if not file_path:
                return
            
            # Récupérer les données de l'inventaire avec les relations
            with self.controller.db_manager.get_session() as session:
                inventory = session.query(StockInventaire).options(
                    joinedload(StockInventaire.warehouse)
                ).filter(StockInventaire.id == self.inventory_id).first()
                if not inventory:
                    QMessageBox.critical(self, "Erreur", "Inventaire non trouvé")
                    return
                
                products = self.controller.get_inventory_products(session, self.inventory_id)
            
            # Récupérer les informations de l'entreprise
            enterprise_info = self.get_enterprise_info()
            
            # Générer le PDF
            self.generate_inventory_pdf(file_path, inventory, products, enterprise_info)
            
            QMessageBox.information(self, "Succès", f"PDF exporté avec succès:\n{file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export PDF:\n{str(e)}")

    def get_enterprise_info(self) -> Dict[str, Any]:
        """Récupérer les informations de l'entreprise"""
        try:
            with self.controller.db_manager.get_session() as session:
                result = session.execute(text("""
                    SELECT name, address, phone, email, rccm, id_nat, logo, slogan, currency
                    FROM core_enterprises 
                    WHERE id = :enterprise_id
                """), {"enterprise_id": self.entreprise_id})
                
                row = result.fetchone()
                if row:
                    return {
                        'name': row[0] or "Entreprise",
                        'address': row[1] or "",
                        'phone': row[2] or "",
                        'email': row[3] or "",
                        'rccm': row[4] or "",
                        'id_nat': row[5] or "",
                        'logo': row[6],  # BLOB
                        'slogan': row[7] or "",
                        'currency': row[8] or "FC"
                    }
                return {
                    'name': "Entreprise",
                    'address': "",
                    'phone': "",
                    'email': "",
                    'rccm': "",
                    'id_nat': "",
                    'logo': None,
                    'slogan': "",
                    'currency': "FC"
                }
        except Exception as e:
            print(f"Erreur récupération entreprise: {e}")
            return {
                'name': "Entreprise",
                'address': "",
                'phone': "",
                'email': "",
                'rccm': "",
                'id_nat': "",
                'logo': None,
                'slogan': "",
                'currency': "FC"
            }

    def generate_inventory_pdf(self, file_path: str, inventory: StockInventaire, products: List[Dict], enterprise: Dict):
        """Générer le PDF de l'inventaire"""
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Style personnalisé pour l'en-tête
        header_style = ParagraphStyle(
            'Header',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Centré
        )
        
        # Style pour les informations
        info_style = ParagraphStyle(
            'Info',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=5
        )
        
        # Style pour le footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            alignment=1  # Centré
        )
        
        # En-tête avec logo et informations entreprise
        # Logo (si disponible)
        if enterprise.get('logo'):
            # Pour simplifier, on ne gère pas le logo BLOB pour l'instant
            pass
        
        # Nom de l'entreprise
        story.append(Paragraph(enterprise['name'], header_style))
        story.append(Spacer(1, 0.2*cm))
        
        # Informations entreprise
        if enterprise['address']:
            story.append(Paragraph(f"Adresse: {enterprise['address']}", info_style))
        if enterprise['phone']:
            story.append(Paragraph(f"Téléphone: {enterprise['phone']}", info_style))
        if enterprise['email']:
            story.append(Paragraph(f"Email: {enterprise['email']}", info_style))
        if enterprise['rccm']:
            story.append(Paragraph(f"RCCM: {enterprise['rccm']}", info_style))
        if enterprise['id_nat']:
            story.append(Paragraph(f"ID National: {enterprise['id_nat']}", info_style))
        
        story.append(Spacer(1, 0.5*cm))
        
        # Titre du rapport
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            alignment=1
        )
        story.append(Paragraph("RAPPORT D'INVENTAIRE", title_style))
        story.append(Spacer(1, 0.3*cm))
        
        # Informations de l'inventaire
        inventory_info = [
            ["Référence:", inventory.reference],
            ["Session:", inventory.session_name],
            ["Entrepôt:", getattr(inventory.warehouse, 'name', 'N/A')],
            ["Date de création:", inventory.created_at.strftime('%d/%m/%Y %H:%M') if inventory.created_at else 'N/A'],
            ["Statut:", inventory.status],
            ["Progression:", f"{inventory.counted_items}/{inventory.total_items}" if inventory.total_items else "0/0"]
        ]
        
        info_table = Table(inventory_info, colWidths=[3*cm, 10*cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Statistiques
        total_purchase_variance = sum(p.get('variance_value_purchase', 0) for p in products)
        total_sale_variance = sum(p.get('variance_value_sale', 0) for p in products)
        total_discrepancies = sum(1 for p in products if p.get('variance', 0) != 0)
        
        stats_data = [
            ["Total produits:", len(products)],
            ["Écarts détectés:", total_discrepancies],
            ["Écart total achat:", f"{enterprise['currency']} {total_purchase_variance:,.2f}"],
            ["Écart total vente:", f"{enterprise['currency']} {total_sale_variance:,.2f}"]
        ]
        
        stats_table = Table(stats_data, colWidths=[4*cm, 9*cm])
        stats_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Tableau des produits
        if products:
            # En-têtes du tableau
            table_data = [["Produit", "Stock Système", "Stock Compté", "Écart", "Écart Achat", "Écart Vente"]]
            
            # Données des produits
            for product in products:
                table_data.append([
                    product.get('product_name', ''),
                    f"{product.get('system_stock', 0):.2f}",
                    f"{product.get('counted_stock', 0):.2f}",
                    f"{product.get('variance', 0):.2f}",
                    f"{enterprise['currency']} {product.get('variance_value_purchase', 0):,.2f}",
                    f"{enterprise['currency']} {product.get('variance_value_sale', 0):,.2f}"
                ])
            
            # Créer le tableau
            col_widths = [4*cm, 2.5*cm, 2.5*cm, 2.5*cm, 3*cm, 3*cm]
            product_table = Table(table_data, colWidths=col_widths, repeatRows=1)
            
            # Style du tableau
            product_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.whitesmoke]),
            ]))
            
            story.append(product_table)
        
        # Footer avec mention Ayanna
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph("Généré par Ayanna ERP - Système de Gestion d'Entreprise", footer_style))
        story.append(Paragraph(f"Le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", footer_style))
        
        # Générer le PDF
        doc.build(story)


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
                
                # Enrichir avec les infos d'entrepôt
                for inv in self.current_inventories:
                    wid = inv.get('warehouse_id')
                    if wid:
                        warehouse = session.query(StockWarehouse).filter(StockWarehouse.id == wid).first()
                        if warehouse:
                            inv['warehouse_name'] = warehouse.name
                            inv['warehouse_code'] = warehouse.code
                        else:
                            inv['warehouse_name'] = 'N/A'
                            inv['warehouse_code'] = 'N/A'
                    else:
                        inv['warehouse_name'] = 'N/A'
                        inv['warehouse_code'] = 'N/A'
                
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
            warehouses = session.query(StockWarehouse).filter(
                StockWarehouse.entreprise_id == self.entreprise_id,
                StockWarehouse.is_active == True
            ).order_by(StockWarehouse.name).all()
            
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
    
    def open_counting(self, inventory):
        """Ouvrir la saisie des comptages"""
        # Si l'inventaire est en DRAFT, le passer à IN_PROGRESS
        if inventory.get('status') == 'DRAFT':
            try:
                with self.db_manager.get_session() as session:
                    inv = session.query(StockInventaire).filter(StockInventaire.id == inventory.get('id')).first()
                    if inv:
                        inv.status = 'IN_PROGRESS'
                        inv.started_date = datetime.now()
                        session.commit()
                        # Mettre à jour les données locales
                        inventory['status'] = 'IN_PROGRESS'
            except Exception as e:
                print(f"Erreur lors de la mise à jour du statut: {e}")
        
        dialog = CountingDialog(self, inventory_id=inventory.get('id'), controller=self.controller)
        dialog.exec()
        
        # Recharger les données après la fermeture du dialog
        self.load_data()
    
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
        
        self.setup_ui()
        self.load_data()

    def get_entreprise_id_from_pos(self, pos_id):
        """Récupérer l'entreprise_id depuis le pos_id"""
        try:
            with self.controller.db_manager.get_session() as session:
                result = session.execute(text("SELECT enterprise_id FROM core_pos_points WHERE id = :pos_id"), {"pos_id": pos_id})
                row = result.fetchone()
                return row[0] if row else 1  # Par défaut entreprise 1
        except Exception as e:
            print(f"Erreur récupération entreprise_id: {e}")
            return 1  # Par défaut entreprise 1

    def setup_ui(self):
        """Configurer l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # En-tête
        header_layout = QHBoxLayout()
        title_label = QLabel("📋 Gestion des Inventaires")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        self.new_inventory_btn = QPushButton("📋 Nouvel Inventaire")
        self.new_inventory_btn.clicked.connect(self.create_new_inventory)
        header_layout.addWidget(self.new_inventory_btn)
        
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.clicked.connect(self.load_data)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Onglets pour organiser les fonctionnalités
        tabs = QTabWidget()
        
        # Onglet Sessions d'inventaire
        sessions_tab = self.create_sessions_tab()
        tabs.addTab(sessions_tab, "📊 Sessions")
        
        # Onglet Corrections
        corrections_tab = self.create_corrections_tab()
        tabs.addTab(corrections_tab, "🔧 Corrections")
        
        # Onglet Historique
        history_tab = self.create_history_tab()
        tabs.addTab(history_tab, "📚 Historique")
        
        layout.addWidget(tabs)

    def create_sessions_tab(self) -> QWidget:
        """Créer l'onglet des sessions d'inventaire"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Table des inventaires
        self.sessions_table = QTableWidget()
        self.sessions_table.setColumnCount(6)
        self.sessions_table.setHorizontalHeaderLabels([
            "Référence", "Session", "Entrepôt", "Statut", "Progression", "Actions"
        ])
        self.sessions_table.setAlternatingRowColors(True)
        self.sessions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.sessions_table)
        return widget

    def create_corrections_tab(self) -> QWidget:
        """Créer l'onglet des corrections"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Boutons de correction
        corrections_layout = QHBoxLayout()
        
        manual_correction_btn = QPushButton("✏️ Correction Manuelle")
        manual_correction_btn.clicked.connect(self.open_manual_correction)
        corrections_layout.addWidget(manual_correction_btn)
        
        import_correction_btn = QPushButton("📥 Import Corrections")
        import_correction_btn.clicked.connect(self.open_import_correction)
        corrections_layout.addWidget(import_correction_btn)
        
        batch_correction_btn = QPushButton("🔧 Correction en Lot")
        batch_correction_btn.clicked.connect(self.open_batch_correction)
        corrections_layout.addWidget(batch_correction_btn)
        
        corrections_layout.addStretch()
        layout.addLayout(corrections_layout)
        
        # Table des corrections récentes
        self.corrections_table = QTableWidget()
        self.corrections_table.setColumnCount(4)
        self.corrections_table.setHorizontalHeaderLabels([
            "Date", "Produit", "Correction", "Utilisateur"
        ])
        self.corrections_table.setAlternatingRowColors(True)
        self.corrections_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.corrections_table)
        return widget

    def create_history_tab(self) -> QWidget:
        """Créer l'onglet historique"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filtres
        filters_layout = QHBoxLayout()
        
        filters_layout.addWidget(QLabel("Période:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Tous", "Aujourd'hui", "Cette semaine", "Ce mois"])
        filters_layout.addWidget(self.period_combo)
        
        filters_layout.addWidget(QLabel("Statut:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Tous", "DRAFT", "IN_PROGRESS", "COMPLETED", "CANCELLED"])
        filters_layout.addWidget(self.status_combo)
        
        filters_layout.addStretch()
        layout.addLayout(filters_layout)
        
        # Table historique
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels([
            "Date", "Référence", "Session", "Entrepôt", "Statut", "Écart Total", "Actions"
        ])
        self.history_table.setAlternatingRowColors(True)
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.history_table)
        return widget

    def load_data(self):
        """Charger les données"""
        self.load_sessions()
        self.load_corrections()
        self.load_history()

    def load_sessions(self):
        """Charger la liste des sessions d'inventaire"""
        try:
            inventories = self.controller.get_inventories()
            
            self.sessions_table.setRowCount(len(inventories))
            
            for row, inv in enumerate(inventories):
                # Référence
                ref_item = QTableWidgetItem(inv.get('reference', ''))
                self.sessions_table.setItem(row, 0, ref_item)
                
                # Session
                session_item = QTableWidgetItem(inv.get('session_name', ''))
                self.sessions_table.setItem(row, 1, session_item)
                
                # Entrepôt
                warehouse_item = QTableWidgetItem(inv.get('warehouse_name', ''))
                self.sessions_table.setItem(row, 2, warehouse_item)
                
                # Statut
                status = inv.get('status', '')
                status_item = QTableWidgetItem(status)
                if status == 'COMPLETED':
                    status_item.setBackground(QColor(144, 238, 144))  # Vert clair
                elif status == 'IN_PROGRESS':
                    status_item.setBackground(QColor(255, 255, 224))  # Jaune clair
                elif status == 'DRAFT':
                    status_item.setBackground(QColor(255, 228, 225))  # Rouge clair
                self.sessions_table.setItem(row, 3, status_item)
                
                # Progression
                counted = inv.get('counted_items', 0)
                total = inv.get('total_items', 0)
                progress_text = f"{counted}/{total}" if total > 0 else "0/0"
                progress_item = QTableWidgetItem(progress_text)
                self.sessions_table.setItem(row, 4, progress_item)
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)
                
                if status in ['DRAFT', 'IN_PROGRESS']:
                    count_btn = QPushButton("📊")
                    count_btn.setToolTip("Commencer/Continuer le comptage")
                    count_btn.clicked.connect(lambda checked, inv_id=inv.get('id'): self.open_counting(inv_id))
                    actions_layout.addWidget(count_btn)
                
                if status == 'IN_PROGRESS':
                    complete_btn = QPushButton("✅")
                    complete_btn.setToolTip("Finaliser l'inventaire")
                    complete_btn.clicked.connect(lambda checked, inv_id=inv.get('id'): self.complete_inventory(inv_id))
                    actions_layout.addWidget(complete_btn)
                
                view_btn = QPushButton("👁️")
                view_btn.setToolTip("Voir les détails")
                view_btn.clicked.connect(lambda checked, inv_id=inv.get('id'): self.view_inventory_details(inv_id))
                actions_layout.addWidget(view_btn)
                
                actions_layout.addStretch()
                self.sessions_table.setCellWidget(row, 5, actions_widget)
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des sessions:\n{str(e)}")

    def load_corrections(self):
        """Charger les corrections récentes"""
        # TODO: Implémenter le chargement des corrections
        self.corrections_table.setRowCount(0)

    def load_history(self):
        """Charger l'historique des inventaires"""
        try:
            # Pour l'instant, charger tous les inventaires comme historique
            inventories = self.controller.get_inventories()
            
            self.history_table.setRowCount(len(inventories))
            
            for row, inv in enumerate(inventories):
                # Date
                created_at = inv.get('created_at', '')
                if hasattr(created_at, 'strftime'):
                    date_str = created_at.strftime('%d/%m/%Y')
                else:
                    date_str = str(created_at)[:10] if created_at else ''
                self.history_table.setItem(row, 0, QTableWidgetItem(date_str))
                
                # Référence
                self.history_table.setItem(row, 1, QTableWidgetItem(inv.get('reference', '')))
                
                # Session
                self.history_table.setItem(row, 2, QTableWidgetItem(inv.get('session_name', '')))
                
                # Entrepôt
                self.history_table.setItem(row, 3, QTableWidgetItem(inv.get('warehouse_name', '')))
                
                # Statut
                status = inv.get('status', '')
                status_item = QTableWidgetItem(status)
                if status == 'COMPLETED':
                    status_item.setBackground(QColor(144, 238, 144))
                elif status == 'IN_PROGRESS':
                    status_item.setBackground(QColor(255, 255, 224))
                elif status == 'DRAFT':
                    status_item.setBackground(QColor(255, 228, 225))
                self.history_table.setItem(row, 4, status_item)
                
                # Écart total
                variance_value = inv.get('total_variance_value', 0)
                variance_item = QTableWidgetItem(f"{variance_value:,.2f} €")
                self.history_table.setItem(row, 5, variance_item)
                
                # Actions
                view_btn = QPushButton("👁️")
                view_btn.setToolTip("Voir les détails")
                view_btn.clicked.connect(lambda checked, inv_id=inv.get('id'): self.view_inventory_details(inv_id))
                self.history_table.setCellWidget(row, 6, view_btn)
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement de l'historique:\n{str(e)}")

    def create_new_inventory(self):
        """Créer un nouvel inventaire"""
        dialog = InventorySessionDialog(self, self.pos_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()
            self.inventory_created.emit()

    def open_counting(self, inventory_id: int):
        """Ouvrir le dialog de comptage pour un inventaire"""
        dialog = CountingDialog(self, inventory_id=inventory_id, controller=self.controller)
        dialog.exec()
        self.load_data()

    def complete_inventory(self, inventory_id: int):
        """Finaliser un inventaire"""
        reply = QMessageBox.question(
            self, "Confirmation",
            "Êtes-vous sûr de vouloir finaliser cet inventaire ?\nCette action ajustera automatiquement les stocks.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with self.controller.db_manager.get_session() as session:
                    self.controller.complete_inventory(session, inventory_id)
                    session.commit()
                
                QMessageBox.information(self, "Succès", "Inventaire finalisé avec succès !")
                self.load_data()
                self.inventory_completed.emit()
                
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la finalisation:\n{str(e)}")

    def view_inventory_details(self, inventory_id: int):
        """Voir les détails d'un inventaire"""
        try:
            with self.controller.db_manager.get_session() as session:
                # Charger l'inventaire avec ses relations
                inventory = session.query(StockInventaire).options(
                    joinedload(StockInventaire.warehouse),
                    joinedload(StockInventaire.items)
                ).filter(StockInventaire.id == inventory_id).first()
                
                if not inventory:
                    QMessageBox.critical(self, "Erreur", "Inventaire non trouvé")
                    return
                
                # Récupérer les produits détaillés
                products = self.controller.get_inventory_products(session, inventory_id)
                
                # Créer la boîte de dialogue de détails
                dialog = InventoryDetailsDialog(inventory, products, self.entreprise_id, self.controller.db_manager, self)
                dialog.exec()
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ouverture des détails:\n{str(e)}")

    def open_manual_correction(self):
        """Ouvrir la correction manuelle"""
        QMessageBox.information(self, "Correction Manuelle", "Fonctionnalité de correction manuelle à implémenter.")

    def open_import_correction(self):
        """Ouvrir l'import de corrections"""
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


class InventoryDetailsDialog(QDialog):
    """Dialog pour afficher les détails complets d'un inventaire"""
    
    def __init__(self, inventory: StockInventaire, products: List[Dict], entreprise_id: int, db_manager, parent=None):
        super().__init__(parent)
        self.inventory = inventory
        self.products = products
        self.entreprise_id = entreprise_id
        self.db_manager = db_manager
        self.ent_ctrl = EntrepriseController()
        
        self.setWindowTitle(f"Détails Inventaire - {inventory.reference}")
        self.setFixedSize(1000, 700)
        self.setup_ui()
        self.load_details()

    def setup_ui(self):
        """Configuration de l'interface"""
        layout = QVBoxLayout(self)
        
        # En-tête avec informations générales
        header_group = QGroupBox("Informations générales")
        header_layout = QFormLayout(header_group)
        
        self.ref_label = QLabel()
        header_layout.addRow("Référence:", self.ref_label)
        
        self.session_label = QLabel()
        header_layout.addRow("Session:", self.session_label)
        
        self.warehouse_label = QLabel()
        header_layout.addRow("Entrepôt:", self.warehouse_label)
        
        self.status_label = QLabel()
        header_layout.addRow("Statut:", self.status_label)
        
        self.created_label = QLabel()
        header_layout.addRow("Créé le:", self.created_label)
        
        self.completed_label = QLabel()
        header_layout.addRow("Terminé le:", self.completed_label)
        
        layout.addWidget(header_group)
        
        # Statistiques
        stats_group = QGroupBox("Statistiques")
        stats_layout = QHBoxLayout(stats_group)
        
        self.total_products_label = QLabel()
        stats_layout.addWidget(self.total_products_label)
        
        self.counted_products_label = QLabel()
        stats_layout.addWidget(self.counted_products_label)
        
        self.discrepancies_label = QLabel()
        stats_layout.addWidget(self.discrepancies_label)
        
        self.total_variance_label = QLabel()
        stats_layout.addWidget(self.total_variance_label)
        
        stats_layout.addStretch()
        layout.addWidget(stats_group)
        
        # Tableau des produits
        products_group = QGroupBox("Détail des produits")
        products_layout = QVBoxLayout(products_group)
        
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(8)
        self.products_table.setHorizontalHeaderLabels([
            "Produit", "Code", "Stock Système", "Stock Compté", "Écart", 
            "Écart Achat", "Écart Vente", "Notes"
        ])
        self.products_table.setAlternatingRowColors(True)
        self.products_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        products_layout.addWidget(self.products_table)
        layout.addWidget(products_group)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        export_btn = QPushButton("📄 Exporter PDF")
        export_btn.clicked.connect(self.export_pdf)
        buttons_layout.addWidget(export_btn)
        
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)

    def load_details(self):
        """Charger les détails de l'inventaire"""
        # Informations générales
        self.ref_label.setText(self.inventory.reference or "")
        self.session_label.setText(self.inventory.session_name or "")
        self.warehouse_label.setText(getattr(self.inventory.warehouse, 'name', 'N/A') if self.inventory.warehouse else 'N/A')
        
        # Statut avec couleur
        status = self.inventory.status or 'DRAFT'
        self.status_label.setText(status)
        if status == 'COMPLETED':
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        elif status == 'IN_PROGRESS':
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
        
        # Dates
        if self.inventory.created_at:
            self.created_label.setText(self.inventory.created_at.strftime('%d/%m/%Y %H:%M'))
        if self.inventory.completed_date:
            self.completed_label.setText(self.inventory.completed_date.strftime('%d/%m/%Y %H:%M'))
        
        # Statistiques
        total_products = len(self.products)
        counted_products = sum(1 for p in self.products if p.get('counted_stock', 0) > 0)
        discrepancies = sum(1 for p in self.products if p.get('variance', 0) != 0)
        total_variance_purchase = sum(p.get('variance_value_purchase', 0) for p in self.products)
        total_variance_sale = sum(p.get('variance_value_sale', 0) for p in self.products)
        
        self.total_products_label.setText(f"Total produits: {total_products}")
        self.counted_products_label.setText(f"Comptés: {counted_products}")
        self.discrepancies_label.setText(f"Écarts: {discrepancies}")
        self.total_variance_label.setText(f"Écart total achat: {self.ent_ctrl.format_amount(total_variance_sale)}")
        
        # Remplir le tableau des produits
        self.products_table.setRowCount(len(self.products))
        
        for row, product in enumerate(self.products):
            # Produit
            self.products_table.setItem(row, 0, QTableWidgetItem(product.get('product_name', '')))
            
            # Code
            self.products_table.setItem(row, 1, QTableWidgetItem(product.get('product_code', '')))
            
            # Stock système
            system_stock = product.get('system_stock', 0)
            system_item = QTableWidgetItem(f"{system_stock:.2f}")
            self.products_table.setItem(row, 2, system_item)
            
            # Stock compté
            counted_stock = product.get('counted_stock', 0)
            counted_item = QTableWidgetItem(f"{counted_stock:.2f}")
            self.products_table.setItem(row, 3, counted_item)
            
            # Écart
            variance = product.get('variance', 0)
            variance_item = QTableWidgetItem(f"{variance:.2f}")
            if variance != 0:
                variance_item.setBackground(QColor(255, 200, 200))  # Rouge clair pour les écarts
            self.products_table.setItem(row, 4, variance_item)
            
            # Écart achat
            variance_purchase = product.get('variance_value_purchase', 0)
            purchase_item = QTableWidgetItem(f"{self.ent_ctrl.format_amount(variance_purchase)}")
            self.products_table.setItem(row, 5, purchase_item)
            
            # Écart vente
            variance_sale = product.get('variance_value_sale', 0)
            sale_item = QTableWidgetItem(f"{self.ent_ctrl.format_amount(variance_sale)}")
            self.products_table.setItem(row, 6, sale_item)
            
            # Notes
            self.products_table.setItem(row, 7, QTableWidgetItem(product.get('notes', '')))

    def export_pdf(self):
        """Exporter les détails en PDF"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Exporter les détails en PDF", 
                f"inventaire_details_{self.inventory.reference}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                "Fichiers PDF (*.pdf)"
            )
            
            if not file_path:
                return
            
            # Récupérer les informations de l'entreprise
            enterprise_info = self.get_enterprise_info()
            
            # Générer le PDF
            self.generate_details_pdf(file_path, enterprise_info)
            
            QMessageBox.information(self, "Succès", f"PDF exporté avec succès:\n{file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export PDF:\n{str(e)}")

    def get_enterprise_info(self) -> Dict[str, Any]:
        """Récupérer les informations de l'entreprise"""
        try:
            with self.db_manager.get_session() as session:
                result = session.execute(text("""
                    SELECT name, address, phone, email, rccm, id_nat, logo, slogan, currency
                    FROM core_enterprises 
                    WHERE id = :enterprise_id
                """), {"enterprise_id": self.entreprise_id})
                
                row = result.fetchone()
                if row:
                    return {
                        'name': row[0] or "Entreprise",
                        'address': row[1] or "",
                        'phone': row[2] or "",
                        'email': row[3] or "",
                        'rccm': row[4] or "",
                        'id_nat': row[5] or "",
                        'logo': row[6],  # BLOB
                        'slogan': row[7] or "",
                        'currency': row[8] or "FC"
                    }
                return {
                    'name': "Entreprise",
                    'address': "",
                    'phone': "",
                    'email': "",
                    'rccm': "",
                    'id_nat': "",
                    'logo': None,
                    'slogan': "",
                    'currency': "FC"
                }
        except Exception as e:
            print(f"Erreur récupération entreprise: {e}")
            return {
                'name': "Entreprise",
                'address': "",
                'phone': "",
                'email': "",
                'rccm': "",
                'id_nat': "",
                'logo': None,
                'slogan': "",
                'currency': "FC"
            }

    def generate_details_pdf(self, file_path: str, enterprise: Dict):
        """Générer le PDF des détails"""
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # En-tête
        header_style = ParagraphStyle(
            'Header',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1
        )
        story.append(Paragraph(enterprise['name'], header_style))
        story.append(Paragraph("RAPPORT DÉTAILLÉ D'INVENTAIRE", header_style))
        story.append(Spacer(1, 0.5*cm))
        
        # Informations générales
        info_data = [
            ["Référence:", self.inventory.reference],
            ["Session:", self.inventory.session_name],
            ["Entrepôt:", getattr(self.inventory.warehouse, 'name', 'N/A')],
            ["Statut:", self.inventory.status],
            ["Date de création:", self.inventory.created_at.strftime('%d/%m/%Y %H:%M') if self.inventory.created_at else 'N/A'],
        ]
        
        if self.inventory.completed_date:
            info_data.append(["Date de finalisation:", self.inventory.completed_date.strftime('%d/%m/%Y %H:%M')])
        
        info_table = Table(info_data, colWidths=[4*cm, 11*cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Statistiques
        total_products = len(self.products)
        counted_products = sum(1 for p in self.products if p.get('counted_stock', 0) > 0)
        discrepancies = sum(1 for p in self.products if p.get('variance', 0) != 0)
        total_variance_purchase = sum(p.get('variance_value_purchase', 0) for p in self.products)
        total_variance_sale = sum(p.get('variance_value_sale', 0) for p in self.products)
        
        stats_data = [
            ["Total produits:", str(total_products)],
            ["Produits comptés:", str(counted_products)],
            ["Écarts détectés:", str(discrepancies)],
            ["Écart total achat:", f"{enterprise['currency']} {total_variance_purchase:,.2f}"],
            ["Écart total vente:", f"{enterprise['currency']} {total_variance_sale:,.2f}"]
        ]
        
        stats_table = Table(stats_data, colWidths=[4*cm, 11*cm])
        stats_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Tableau détaillé des produits
        if self.products:
            table_data = [["Produit", "Code", "Sys", "Compté", "Écart", "Écart Achat", "Écart Vente", "Notes"]]
            
            for product in self.products:
                table_data.append([
                    product.get('product_name', ''),
                    product.get('product_code', ''),
                    f"{product.get('system_stock', 0):.2f}",
                    f"{product.get('counted_stock', 0):.2f}",
                    f"{product.get('variance', 0):.2f}",
                    f"{enterprise['currency']} {product.get('variance_value_purchase', 0):,.2f}",
                    f"{enterprise['currency']} {product.get('variance_value_sale', 0):,.2f}",
                    product.get('notes', '')
                ])
            
            col_widths = [3*cm, 2*cm, 1.5*cm, 1.5*cm, 1.5*cm, 3*cm, 3*cm, 3*cm]
            product_table = Table(table_data, colWidths=col_widths, repeatRows=1)
            
            product_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.whitesmoke]),
            ]))
            
            story.append(product_table)
        
        # Footer
        story.append(Spacer(1, 1*cm))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            alignment=1
        )
        story.append(Paragraph("Généré par Ayanna ERP - Système de Gestion d'Entreprise", footer_style))
        story.append(Paragraph(f"Le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", footer_style))
        
        # Générer le PDF
        doc.build(story)