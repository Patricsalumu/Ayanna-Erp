"""
Widget pour créer une nouvelle commande d'achat
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QMessageBox, QDialog,
    QDialogButtonBox, QHeaderView, QDateEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont
from decimal import Decimal
from datetime import datetime

from ayanna_erp.modules.achats.controllers import AchatController
from ayanna_erp.modules.achats.models import CoreFournisseur, EtatCommande
from ayanna_erp.modules.core.models import CoreProduct
from ayanna_erp.modules.stock.models import StockWarehouse
from ayanna_erp.core.entreprise_controller import EntrepriseController


class ProductSelectionDialog(QDialog):
    """Dialog pour sélectionner des produits à ajouter à la commande"""
    
    def __init__(self, achat_controller: AchatController, parent=None):
        super().__init__(parent)
        self.achat_controller = achat_controller
        self.selected_products = []
        try:
            self.entreprise_ctrl = EntrepriseController()
            self.currency = self.entreprise_ctrl.get_currency_symbol()
        except Exception:
            self.currency = "FC"
        
        self.setWindowTitle("Sélectionner des produits")
        self.setModal(True)
        self.setMinimumSize(600, 400)
        
        self.setup_ui()
        self.load_products()
    
    def setup_ui(self):
        """Configuration de l'interface"""
        layout = QVBoxLayout(self)
        
        # Recherche
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Recherche:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Nom ou code du produit...")
        self.search_edit.textChanged.connect(self.filter_products)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)
        
        # Table des produits
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(4)
        self.products_table.setHorizontalHeaderLabels([
            "Code", "Nom", "Prix", "Sélectionner"
        ])
        self.products_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.products_table)
        
        # Boutons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_products(self):
        """Charge la liste des produits"""
        try:
            session = self.achat_controller.db_manager.get_session()
            self.all_products = self.achat_controller.get_produits_disponibles(session)
            self.populate_products_table()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement: {str(e)}")
        finally:
            session.close()
    
    def populate_products_table(self):
        """Remplit la table des produits"""
        products_to_show = getattr(self, 'filtered_products', self.all_products)
        self.products_table.setRowCount(len(products_to_show))
        
        for row, product in enumerate(products_to_show):
            # Code
            self.products_table.setItem(row, 0, QTableWidgetItem(product.code or ""))
            
            # Nom
            self.products_table.setItem(row, 1, QTableWidgetItem(product.name))
            
            # Prix
            prix_str = self.entreprise_ctrl.format_amount(product.price_unit) if product.price_unit else self.entreprise_ctrl.format_amount(0)
            self.products_table.setItem(row, 2, QTableWidgetItem(prix_str))
            
            # Checkbox pour sélection
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            
            select_btn = QPushButton("Ajouter")
            select_btn.clicked.connect(lambda checked, p=product: self.select_product(p))
            checkbox_layout.addWidget(select_btn)
            
            self.products_table.setCellWidget(row, 3, checkbox_widget)
    
    def filter_products(self):
        """Filtre les produits selon la recherche"""
        search_text = self.search_edit.text().lower()
        if search_text:
            self.filtered_products = [
                p for p in self.all_products
                if search_text in p.name.lower() or 
                   (p.code and search_text in p.code.lower())
            ]
        else:
            self.filtered_products = self.all_products
        
        self.populate_products_table()
    
    def select_product(self, product):
        """Sélectionne un produit"""
        if product not in self.selected_products:
            self.selected_products.append(product)
            QMessageBox.information(self, "Produit ajouté", f"Produit '{product.name}' ajouté à la sélection")


class NouvelleCommandeWidget(QWidget):
    """Widget pour créer une nouvelle commande d'achat"""
    
    commande_created = pyqtSignal(int)
    
    def __init__(self, achat_controller: AchatController):
        super().__init__()
        self.achat_controller = achat_controller
        # Récupérer le symbole de la devise dynamique
        try:
            self.entreprise_ctrl = EntrepriseController()
            self.currency = self.entreprise_ctrl.get_currency_symbol()
        except Exception:
            self.currency = "FC"
        self.current_lines = []
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Configuration de l'interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Titre
        title_label = QLabel("➕ Nouvelle Commande d'Achat")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2C3E50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Informations générales
        info_group = QGroupBox("Informations générales")
        info_layout = QFormLayout(info_group)
        
        # Numéro (auto-généré)
        self.numero_label = QLabel("(Auto-généré)")
        self.numero_label.setStyleSheet("color: #7F8C8D; font-style: italic;")
        info_layout.addRow("Numéro de commande:", self.numero_label)
        
        # Fournisseur
        self.fournisseur_combo = QComboBox()
        self.fournisseur_combo.setEditable(False)
        info_layout.addRow("Fournisseur:", self.fournisseur_combo)
        
        # Entrepôt de destination
        self.entrepot_combo = QComboBox()
        info_layout.addRow("Entrepôt de destination*:", self.entrepot_combo)
        
        # Date de commande
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        info_layout.addRow("Date de commande:", self.date_edit)
        
        # Remise globale
        self.remise_spinbox = QDoubleSpinBox()
        self.remise_spinbox.setRange(0, 999999)
        self.remise_spinbox.setDecimals(2)
        self.remise_spinbox.setSuffix(f" {self.entreprise_ctrl.get_currency_symbol()}")
        self.remise_spinbox.valueChanged.connect(self.calculate_total)
        info_layout.addRow("Remise globale:", self.remise_spinbox)
        
        layout.addWidget(info_group)
        
        # Lignes de commande
        lines_group = QGroupBox("Lignes de commande")
        lines_layout = QVBoxLayout(lines_group)
        
        # Boutons pour gérer les lignes
        lines_buttons_layout = QHBoxLayout()
        
        self.add_product_btn = QPushButton("➕ Ajouter des produits")
        self.add_product_btn.clicked.connect(self.add_products)
        self.add_product_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #219A52;
            }
        """)
        
        self.remove_line_btn = QPushButton("🗑️ Supprimer ligne")
        self.remove_line_btn.clicked.connect(self.remove_selected_line)
        self.remove_line_btn.setEnabled(False)
        
        lines_buttons_layout.addWidget(self.add_product_btn)
        lines_buttons_layout.addWidget(self.remove_line_btn)
        lines_buttons_layout.addStretch()
        
        lines_layout.addLayout(lines_buttons_layout)
        
        # Table des lignes
        self.lines_table = QTableWidget()
        self.lines_table.setColumnCount(6)
        self.lines_table.setHorizontalHeaderLabels([
            "Produit", "Quantité", "Prix unitaire", "Remise ligne", "Total ligne", "Actions"
        ])
        
        # Configuration de la table
        header = self.lines_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        self.lines_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.lines_table.selectionModel().selectionChanged.connect(self.on_line_selection_changed)
        
        lines_layout.addWidget(self.lines_table)
        layout.addWidget(lines_group)
        
        # Totaux et actions
        bottom_layout = QHBoxLayout()
        
        # Totaux
        totals_group = QGroupBox("Totaux")
        totals_layout = QFormLayout(totals_group)
        
        self.subtotal_label = QLabel(self.entreprise_ctrl.format_amount(0))
        self.subtotal_label.setStyleSheet("font-weight: bold;")
        totals_layout.addRow("Sous-total:", self.subtotal_label)
        
        self.remise_label = QLabel(self.entreprise_ctrl.format_amount(0))
        totals_layout.addRow("Remise globale:", self.remise_label)
        
        self.total_label = QLabel(self.entreprise_ctrl.format_amount(0))
        self.total_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2C3E50;")
        totals_layout.addRow("Total:", self.total_label)
        
        # Boutons d'action
        actions_layout = QVBoxLayout()
        
        self.save_draft_btn = QPushButton("💾 Enregistrer en brouillon")
        self.save_draft_btn.clicked.connect(self.save_as_draft)
        
        self.create_btn = QPushButton("✅ Créer la commande")
        self.create_btn.clicked.connect(self.create_commande)
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        
        self.clear_btn = QPushButton("🔄 Effacer tout")
        self.clear_btn.clicked.connect(self.clear_form)
        
        actions_layout.addWidget(self.save_draft_btn)
        actions_layout.addWidget(self.create_btn)
        actions_layout.addWidget(self.clear_btn)
        actions_layout.addStretch()
        
        bottom_layout.addWidget(totals_group)
        bottom_layout.addLayout(actions_layout)
        
        layout.addLayout(bottom_layout)
    
    def load_data(self):
        """Charge les données nécessaires"""
        try:
            session = self.achat_controller.db_manager.get_session()
            
            # Charger les fournisseurs
            self.load_fournisseurs(session)
            
            # Charger les entrepôts
            self.load_entrepots(session)
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement: {str(e)}")
        finally:
            session.close()
    
    def load_fournisseurs(self, session):
        """Charge la liste des fournisseurs"""
        self.fournisseur_combo.clear()
        self.fournisseur_combo.addItem("Aucun fournisseur", None)
        
        fournisseurs = self.achat_controller.get_fournisseurs(session)
        for fournisseur in fournisseurs:
            self.fournisseur_combo.addItem(fournisseur.nom, fournisseur.id)
    
    def load_entrepots(self, session):
        """Charge la liste des entrepôts"""
        try:
            self.entrepot_combo.clear()
            
            entrepots = self.achat_controller.get_entrepots_disponibles(session)
            
            if not entrepots:
                self.entrepot_combo.addItem("Aucun entrepôt disponible", None)
            else:
                for entrepot in entrepots:
                    self.entrepot_combo.addItem(f"{entrepot.name} ({entrepot.code})", entrepot.id)
        except Exception as e:
            print(f"ERREUR load_entrepots: {e}")
            self.entrepot_combo.addItem("Erreur de chargement", None)
    
    def refresh_fournisseurs(self):
        """Actualise la liste des fournisseurs"""
        try:
            session = self.achat_controller.db_manager.get_session()
            self.load_fournisseurs(session)
        except Exception as e:
            print(f"Erreur lors de l'actualisation des fournisseurs: {e}")
        finally:
            session.close()
    
    def add_products(self):
        """Ouvre le dialog de sélection de produits"""
        dialog = ProductSelectionDialog(self.achat_controller, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            for product in dialog.selected_products:
                self.add_product_line(product)
    
    def add_product_line(self, product):
        """Ajoute une ligne de produit à la commande"""
        # Vérifier si le produit n'est pas déjà dans la liste
        for line in self.current_lines:
            if line['product'].id == product.id:
                QMessageBox.warning(self, "Produit déjà ajouté", 
                                  f"Le produit '{product.name}' est déjà dans la commande")
                return
        
        # Ajouter la ligne
        line_data = {
            'product': product,
            'quantite': Decimal('1'),
            'prix_unitaire': Decimal(str(product.price_unit or 0)),
            'remise_ligne': Decimal('0'),
            'total_ligne': Decimal(str(product.price_unit or 0))
        }
        
        self.current_lines.append(line_data)
        self.refresh_lines_table()
        self.calculate_total()
    
    def refresh_lines_table(self):
        """Actualise la table des lignes"""
        self.lines_table.setRowCount(len(self.current_lines))
        
        for row, line in enumerate(self.current_lines):
            # Produit
            self.lines_table.setItem(row, 0, QTableWidgetItem(line['product'].name))
            
            # Quantité (editable)
            qty_spinbox = QSpinBox()
            qty_spinbox.setRange(1, 9999)
            qty_spinbox.setValue(int(line['quantite']))
            qty_spinbox.valueChanged.connect(lambda value, r=row: self.update_line_quantity(r, value))
            self.lines_table.setCellWidget(row, 1, qty_spinbox)
            
            # Prix unitaire (editable)
            price_spinbox = QDoubleSpinBox()
            price_spinbox.setRange(0, 999999)
            price_spinbox.setDecimals(2)
            price_spinbox.setValue(float(line['prix_unitaire']))
            price_spinbox.valueChanged.connect(lambda value, r=row: self.update_line_price(r, value))
            self.lines_table.setCellWidget(row, 2, price_spinbox)
            
            # Remise ligne (editable)
            discount_spinbox = QDoubleSpinBox()
            discount_spinbox.setRange(0, 999999)
            discount_spinbox.setDecimals(2)
            discount_spinbox.setValue(float(line['remise_ligne']))
            discount_spinbox.valueChanged.connect(lambda value, r=row: self.update_line_discount(r, value))
            self.lines_table.setCellWidget(row, 3, discount_spinbox)
            
            # Total ligne
            total_item = QTableWidgetItem(self.entreprise_ctrl.format_amount(line['total_ligne']))
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.lines_table.setItem(row, 4, total_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            remove_btn = QPushButton("🗑️")
            remove_btn.setToolTip("Supprimer cette ligne")
            remove_btn.clicked.connect(lambda checked, r=row: self.remove_line(r))
            actions_layout.addWidget(remove_btn)
            
            self.lines_table.setCellWidget(row, 5, actions_widget)
    
    def update_line_quantity(self, row, value):
        """Met à jour la quantité d'une ligne"""
        if row < len(self.current_lines):
            self.current_lines[row]['quantite'] = Decimal(str(value))
            self.calculate_line_total(row)
            self.calculate_total()
    
    def update_line_price(self, row, value):
        """Met à jour le prix unitaire d'une ligne"""
        if row < len(self.current_lines):
            self.current_lines[row]['prix_unitaire'] = Decimal(str(value))
            self.calculate_line_total(row)
            self.calculate_total()
    
    def update_line_discount(self, row, value):
        """Met à jour la remise d'une ligne"""
        if row < len(self.current_lines):
            self.current_lines[row]['remise_ligne'] = Decimal(str(value))
            self.calculate_line_total(row)
            self.calculate_total()
    
    def calculate_line_total(self, row):
        """Calcule le total d'une ligne"""
        if row < len(self.current_lines):
            line = self.current_lines[row]
            line['total_ligne'] = (line['quantite'] * line['prix_unitaire']) - line['remise_ligne']
            
            # Mettre à jour l'affichage
            total_item = QTableWidgetItem(self.entreprise_ctrl.format_amount(line['total_ligne']))
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.lines_table.setItem(row, 4, total_item)
    
    def remove_line(self, row):
        """Supprime une ligne"""
        if row < len(self.current_lines):
            del self.current_lines[row]
            self.refresh_lines_table()
            self.calculate_total()
    
    def remove_selected_line(self):
        """Supprime la ligne sélectionnée"""
        selected_rows = self.lines_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            self.remove_line(row)
    
    def on_line_selection_changed(self):
        """Gestion de la sélection dans la table des lignes"""
        has_selection = len(self.lines_table.selectionModel().selectedRows()) > 0
        self.remove_line_btn.setEnabled(has_selection)
    
    def calculate_total(self):
        """Calcule les totaux de la commande"""
        subtotal = sum(line['total_ligne'] for line in self.current_lines)
        remise_globale = Decimal(str(self.remise_spinbox.value()))
        total = subtotal - remise_globale
        
        self.subtotal_label.setText(self.entreprise_ctrl.format_amount(subtotal))
        self.remise_label.setText(self.entreprise_ctrl.format_amount(remise_globale))
        self.total_label.setText(self.entreprise_ctrl.format_amount(total))
    
    def validate_form(self):
        """Valide le formulaire"""
        if self.entrepot_combo.currentData() is None:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un entrepôt de destination")
            return False
        
        if not self.current_lines:
            QMessageBox.warning(self, "Erreur", "Veuillez ajouter au moins une ligne de commande")
            return False
        
        return True
    
    def create_commande(self):
        """Crée la commande"""
        if not self.validate_form():
            return
        
        try:
            session = self.achat_controller.db_manager.get_session()
            
            # Préparer les données
            entrepot_id = self.entrepot_combo.currentData()
            fournisseur_id = self.fournisseur_combo.currentData()
            remise_global = Decimal(str(self.remise_spinbox.value()))
            
            # Préparer les lignes
            lignes_data = []
            for line in self.current_lines:
                lignes_data.append({
                    'produit_id': line['product'].id,
                    'quantite': line['quantite'],
                    'prix_unitaire': line['prix_unitaire'],
                    'remise_ligne': line['remise_ligne']
                })
            
            # Créer la commande
            commande = self.achat_controller.create_commande(
                session=session,
                entrepot_id=entrepot_id,
                fournisseur_id=fournisseur_id,
                lignes=lignes_data,
                remise_global=remise_global
            )
            
            QMessageBox.information(
                self,
                "Commande créée",
                f"La commande {commande.numero} a été créée avec succès !"
            )
            
            self.commande_created.emit(commande.id)
            self.clear_form()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la création: {str(e)}")
        finally:
            session.close()
    
    def save_as_draft(self):
        """Enregistre en brouillon"""
        # TODO: Implémenter la sauvegarde en brouillon
        QMessageBox.information(self, "Brouillon", "Sauvegarde en brouillon à implémenter")
    
    def clear_form(self):
        """Efface le formulaire"""
        self.fournisseur_combo.setCurrentIndex(0)
        self.entrepot_combo.setCurrentIndex(0)
        self.date_edit.setDate(QDate.currentDate())
        self.remise_spinbox.setValue(0)
        
        self.current_lines.clear()
        self.refresh_lines_table()
        self.calculate_total()
    
    def focus_form(self):
        """Met le focus sur le formulaire"""
        self.fournisseur_combo.setFocus()