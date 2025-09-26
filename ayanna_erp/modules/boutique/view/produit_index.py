"""
Widget de l'onglet Produits - Gestion des produits de la boutique
"""

from typing import List, Optional
from decimal import Decimal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton, 
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, 
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout, QTextEdit, 
    QDoubleSpinBox, QSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

from ayanna_erp.database.database_manager import DatabaseManager
from ..model.models import ShopProduct, ShopCategory


class ProduitIndex(QWidget):
    """Widget de gestion des produits"""
    
    # Signaux
    product_updated = pyqtSignal(int)  # product_id
    
    def __init__(self, boutique_controller, current_user):
        super().__init__()
        self.boutique_controller = boutique_controller
        self.current_user = current_user
        self.db_manager = DatabaseManager()
        
        # Variables d'état
        self.selected_category_id = None
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        
        self.setup_ui()
        self.load_initial_data()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # === HEADER ET FILTRES ===
        header_group = QGroupBox("📦 Gestion des Produits")
        header_layout = QVBoxLayout(header_group)
        
        # Ligne 1: Actions principales
        actions_layout = QHBoxLayout()
        
        self.new_product_btn = QPushButton("➕ Nouveau Produit")
        self.new_product_btn.setStyleSheet("""
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
        self.new_product_btn.clicked.connect(self.create_new_product)
        actions_layout.addWidget(self.new_product_btn)
        
        actions_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.clicked.connect(self.refresh_products)
        actions_layout.addWidget(refresh_btn)
        
        header_layout.addLayout(actions_layout)
        
        # Ligne 2: Filtres de recherche
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Recherche:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nom ou description du produit...")
        self.search_input.textChanged.connect(self.on_search_changed)
        filter_layout.addWidget(self.search_input)
        
        filter_layout.addWidget(QLabel("Catégorie:"))
        self.category_combo = QComboBox()
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        filter_layout.addWidget(self.category_combo)
        
        # Filtre par statut
        filter_layout.addWidget(QLabel("Statut:"))
        self.status_combo = QComboBox()
        self.status_combo.addItem("Tous", None)
        self.status_combo.addItem("Actifs seulement", True)
        self.status_combo.addItem("Inactifs seulement", False)
        self.status_combo.currentTextChanged.connect(self.refresh_products)
        filter_layout.addWidget(self.status_combo)
        
        header_layout.addLayout(filter_layout)
        main_layout.addWidget(header_group)
        
        # === TABLEAU DES PRODUITS ===
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(8)
        self.products_table.setHorizontalHeaderLabels([
            "ID", "Nom", "Catégorie", "Prix", "Stock", "Unité", "Statut", "Actions"
        ])
        
        # Configuration des colonnes
        header = self.products_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Nom
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Catégorie
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Prix
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Stock
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Unité
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Statut
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Actions
        
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        main_layout.addWidget(self.products_table)
    
    def load_initial_data(self):
        """Charger les données initiales"""
        self.load_categories()
        self.refresh_products()
    
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
    
    def refresh_products(self):
        """Actualiser la liste des produits"""
        try:
            with self.db_manager.get_session() as session:
                search_term = self.search_input.text().strip() if self.search_input.text() else None
                category_id = self.selected_category_id
                active_only = self.status_combo.currentData()
                
                products = self.boutique_controller.get_products(
                    session,
                    category_id=category_id,
                    search_term=search_term,
                    active_only=active_only if active_only is not None else True
                )
                
                self.populate_products_table(products)
                
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des produits: {str(e)}")
    
    def populate_products_table(self, products: List[ShopProduct]):
        """Peupler le tableau des produits"""
        self.products_table.setRowCount(len(products))
        
        from ayanna_erp.modules.boutique.model.models import ShopCategory
        for row, product in enumerate(products):
            # ID
            id_item = QTableWidgetItem(str(product.id))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.products_table.setItem(row, 0, id_item)

            # Nom
            self.products_table.setItem(row, 1, QTableWidgetItem(product.name))

            # Catégorie (recharger l'objet dans la session)
            category_name = "Non assignée"
            if product.category_id:
                with self.db_manager.get_session() as session:
                    cat = session.query(ShopCategory).get(product.category_id)
                    if cat:
                        category_name = cat.name
            self.products_table.setItem(row, 2, QTableWidgetItem(category_name))
            
            # Prix
            price_item = QTableWidgetItem(f"{product.price_unit:.2f} €")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.products_table.setItem(row, 3, price_item)
            
            # Stock (calculer le stock total)
            try:
                with self.db_manager.get_session() as session:
                    stock_total = self.boutique_controller.get_product_stock_total(session, product.id)
                stock_item = QTableWidgetItem(str(stock_total))
                stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Colorer selon le stock
                if stock_total == 0:
                    stock_item.setBackground(QColor("#E74C3C"))  # Rouge
                    stock_item.setForeground(QColor("white"))
                elif stock_total < 10:
                    stock_item.setBackground(QColor("#F39C12"))  # Orange
                    stock_item.setForeground(QColor("white"))
                else:
                    stock_item.setBackground(QColor("#27AE60"))  # Vert
                    stock_item.setForeground(QColor("white"))
                
                self.products_table.setItem(row, 4, stock_item)
            except Exception:
                stock_item = QTableWidgetItem("Err")
                stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.products_table.setItem(row, 4, stock_item)
            
            # Unité
            self.products_table.setItem(row, 5, QTableWidgetItem(getattr(product, "unit", "unité")))
            
            # Statut
            status_item = QTableWidgetItem("Actif" if product.is_active else "Inactif")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if product.is_active:
                status_item.setBackground(QColor("#27AE60"))  # Vert
                status_item.setForeground(QColor("white"))
            else:
                status_item.setBackground(QColor("#E74C3C"))  # Rouge
                status_item.setForeground(QColor("white"))
            self.products_table.setItem(row, 6, status_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            # Bouton modifier
            edit_btn = QPushButton("✏️")
            edit_btn.setToolTip("Modifier le produit")
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498DB;
                    color: white;
                    font-weight: bold;
                    padding: 5px;
                    border: none;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #2980B9;
                }
            """)
            edit_btn.clicked.connect(lambda checked, p=product: self.edit_product(p))
            actions_layout.addWidget(edit_btn)
            
            # Bouton activer/désactiver
            toggle_btn = QPushButton("🔴" if product.is_active else "🟢")
            toggle_btn.setToolTip("Désactiver" if product.is_active else "Activer")
            toggle_btn.clicked.connect(lambda checked, p=product: self.toggle_product_status(p))
            actions_layout.addWidget(toggle_btn)
            
            # Bouton gérer stock
            stock_btn = QPushButton("📊")
            stock_btn.setToolTip("Gérer le stock")
            stock_btn.setStyleSheet("""
                QPushButton {
                    background-color: #9B59B6;
                    color: white;
                    font-weight: bold;
                    padding: 5px;
                    border: none;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #8E44AD;
                }
            """)
            stock_btn.clicked.connect(lambda checked, p=product: self.manage_product_stock(p))
            actions_layout.addWidget(stock_btn)
            
            self.products_table.setCellWidget(row, 7, actions_widget)
    
    def create_new_product(self):
        """Créer un nouveau produit"""
        dialog = ProductFormDialog(self, self.boutique_controller)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            product_data = dialog.get_product_data()
            
            try:
                with self.db_manager.get_session() as session:
                    new_product = self.boutique_controller.create_product(
                        session,
                        nom=product_data["nom"],
                        prix=product_data["prix"],
                        category_id=product_data["category_id"],
                        description=product_data.get("description"),
                        unit=product_data.get("unite", "unité"),
                        stock_initial=product_data.get("stock_initial", 0)
                    )
                    
                    QMessageBox.information(self, "Succès", f"Produit '{new_product.name}' créé avec succès!")
                    self.refresh_products()
                    self.product_updated.emit(new_product.id)
                    
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la création du produit: {str(e)}")
    
    def edit_product(self, product: ShopProduct):
        """Modifier un produit existant"""
        dialog = ProductFormDialog(self, self.boutique_controller, product)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            product_data = dialog.get_product_data()
            
            try:
                with self.db_manager.get_session() as session:
                    # Mise à jour du produit
                    updated_product = session.query(ShopProduct).filter(ShopProduct.id == product.id).first()
                    if updated_product:
                        updated_product.name = product_data["nom"]
                        updated_product.description = product_data.get("description")
                        updated_product.price_unit = product_data["prix"]
                        updated_product.category_id = product_data["category_id"]
                        updated_product.unit = product_data.get("unite", "unité")
                        
                        session.commit()
                        
                        QMessageBox.information(self, "Succès", f"Produit '{updated_product.name}' mis à jour avec succès!")
                        self.refresh_products()
                        self.product_updated.emit(updated_product.id)
                    else:
                        QMessageBox.warning(self, "Erreur", "Produit introuvable.")
                        
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la mise à jour du produit: {str(e)}")
    
    def toggle_product_status(self, product: ShopProduct):
        """Activer/Désactiver un produit"""
        new_status = not product.is_active
        action = "activer" if new_status else "désactiver"
        
        reply = QMessageBox.question(
            self, "Confirmation", 
            f"Êtes-vous sûr de vouloir {action} le produit '{product.name}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with self.db_manager.get_session() as session:
                    updated_product = self.boutique_controller.update_category(
                        session, product.id, is_active=new_status
                    )
                    
                    QMessageBox.information(self, "Succès", f"Produit {action}é avec succès!")
                    self.refresh_products()
                    self.product_updated.emit(product.id)
                    
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la modification du statut: {str(e)}")
    
    def manage_product_stock(self, product: ShopProduct):
        """Gérer le stock d'un produit"""
        # TODO: Ouvrir une interface de gestion de stock
        QMessageBox.information(
            self, "Gestion du Stock", 
            f"Gestion du stock pour '{product.name}'\n\n"
            "Cette fonctionnalité sera implémentée dans l'onglet Stock."
        )
    
    def refresh_product(self, product_id: int):
        """Actualiser un produit spécifique"""
        self.refresh_products()
    
    # === ÉVÉNEMENTS ===
    
    def on_search_changed(self):
        """Gestionnaire du changement de recherche (avec délai)"""
        self.search_timer.stop()
        self.search_timer.start(300)  # Attendre 300ms avant de chercher
    
    def perform_search(self):
        """Effectuer la recherche"""
        self.refresh_products()
    
    def on_category_changed(self):
        """Gestionnaire du changement de catégorie"""
        current_data = self.category_combo.currentData()
        self.selected_category_id = current_data if current_data is not None else None
        self.refresh_products()


class ProductFormDialog(QDialog):
    """Dialog pour créer/modifier un produit"""
    
    def __init__(self, parent=None, boutique_controller=None, product: ShopProduct = None):
        super().__init__(parent)
        self.boutique_controller = boutique_controller
        self.product = product
        self.db_manager = DatabaseManager()
        
        # Mode édition ou création
        self.is_editing = product is not None
        
        title = "Modifier le Produit" if self.is_editing else "Nouveau Produit"
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(400, 500)
        
        self.setup_ui()
        
        if self.is_editing:
            self.load_product_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Formulaire
        form_layout = QFormLayout()
        
        # Nom du produit
        self.nom_input = QLineEdit()
        self.nom_input.setPlaceholderText("Nom du produit (obligatoire)")
        form_layout.addRow("Nom *:", self.nom_input)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setPlaceholderText("Description du produit (optionnel)")
        form_layout.addRow("Description:", self.description_input)
        
        # Catégorie
        self.category_combo = QComboBox()
        self.load_categories()
        form_layout.addRow("Catégorie *:", self.category_combo)
        
        # Prix
        self.prix_input = QDoubleSpinBox()
        self.prix_input.setRange(0.01, 999999.99)
        self.prix_input.setDecimals(2)
        self.prix_input.setSuffix(" €")
        self.prix_input.setValue(1.00)
        form_layout.addRow("Prix *:", self.prix_input)
        
        # Unité
        self.unite_input = QLineEdit()
        self.unite_input.setPlaceholderText("unité")
        self.unite_input.setText("unité")
        form_layout.addRow("Unité:", self.unite_input)
        
        # Stock initial (seulement en mode création)
        if not self.is_editing:
            self.stock_initial_input = QSpinBox()
            self.stock_initial_input.setRange(0, 999999)
            self.stock_initial_input.setValue(0)
            form_layout.addRow("Stock initial:", self.stock_initial_input)
        
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
    
    def load_categories(self):
        """Charger les catégories disponibles"""
        try:
            with self.db_manager.get_session() as session:
                categories = self.boutique_controller.get_categories(session)
                
                self.category_combo.clear()
                
                if not categories:
                    # Ajouter une catégorie par défaut
                    self.category_combo.addItem("Aucune catégorie disponible", None)
                else:
                    for category in categories:
                        self.category_combo.addItem(category.name, category.id)
                        
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des catégories: {str(e)}")
            self.category_combo.addItem("Erreur de chargement", None)
    
    def load_product_data(self):
        """Charger les données du produit pour l'édition"""
        if self.product:
            self.nom_input.setText(self.product.name)
            
            if self.product.description:
                self.description_input.setPlainText(self.product.description)
            
            self.prix_input.setValue(float(self.product.price_unit))
            
            if getattr(self.product, "unit", None):
                self.unite_input.setText(self.product.unit)
            
            # Sélectionner la catégorie
            if self.product.category_id:
                for i in range(self.category_combo.count()):
                    if self.category_combo.itemData(i) == self.product.category_id:
                        self.category_combo.setCurrentIndex(i)
                        break
    
    def validate_form(self):
        """Valider le formulaire avant acceptation"""
        if not self.nom_input.text().strip():
            QMessageBox.warning(self, "Erreur", "Le nom du produit est obligatoire.")
            return False
        
        if self.prix_input.value() <= 0:
            QMessageBox.warning(self, "Erreur", "Le prix doit être supérieur à zéro.")
            return False
        
        if self.category_combo.currentData() is None:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner une catégorie valide.")
            return False
        
        return True
    
    def get_product_data(self):
        """Récupérer les données du produit"""
        data = {
            "nom": self.nom_input.text().strip(),
            "description": self.description_input.toPlainText().strip() or None,
            "prix": Decimal(str(self.prix_input.value())),
            "category_id": self.category_combo.currentData(),
            "unit": self.unite_input.text().strip() or "unité"
        }
        
        # Stock initial seulement en mode création
        if not self.is_editing and hasattr(self, 'stock_initial_input'):
            data["stock_initial"] = self.stock_initial_input.value()
        
        return data
    
    def accept(self):
        """Accepter le dialog après validation"""
        if self.validate_form():
            super().accept()