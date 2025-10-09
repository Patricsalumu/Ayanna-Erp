"""
Interface moderne de type supermarché pour le module Boutique
Design épuré avec catalogue de produits et panier de vente
"""

from decimal import Decimal
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QFrame, QLabel, QPushButton, QLineEdit, QComboBox, QSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QSplitter, QGroupBox, QFormLayout, QDoubleSpinBox, QTextEdit,
    QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.core.models import CoreProduct, CoreProductCategory
from ..model.models import ShopClient, ShopPanier


class ModernSupermarketWidget(QWidget):
    """Interface moderne type supermarché avec catalogue et panier"""
    
    # Signaux
    product_added_to_cart = pyqtSignal(int, int)  # product_id, quantity
    cart_updated = pyqtSignal()
    sale_completed = pyqtSignal(int)  # sale_id
    
    def __init__(self, boutique_controller, current_user, pos_id=1):
        super().__init__()
        self.boutique_controller = boutique_controller
        self.current_user = current_user
        self.pos_id = pos_id
        self.db_manager = DatabaseManager()
        
        # Variables d'état
        self.current_cart = []  # Liste des articles du panier
        self.selected_client = None
        self.global_discount = Decimal('0.00')
        self.categories = []
        self.products = []
        
        self.init_ui()
        self.apply_modern_style()
        self.load_initial_data()
    
    def init_ui(self):
        """Initialise l'interface utilisateur moderne"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Header avec informations de session
        self.create_header(main_layout)
        
        # Conteneur principal avec splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Zone catalogue (gauche - 70%)
        catalog_widget = self.create_catalog_section()
        splitter.addWidget(catalog_widget)
        
        # Zone panier (droite - 30%)
        cart_widget = self.create_cart_section()
        splitter.addWidget(cart_widget)
        
        # Définir les proportions
        splitter.setSizes([700, 300])
    
    def create_header(self, layout):
        """Crée l'en-tête moderne avec informations de session"""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2196F3, stop:1 #1976D2);
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        header_layout = QHBoxLayout(header_frame)
        
        # Titre principal
        title_label = QLabel("🛒 Ayanna Supermarché")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                background: transparent;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Informations utilisateur
        user_info = QLabel(f"👤 {getattr(self.current_user, 'name', 'Utilisateur')} | POS #{self.pos_id}")
        user_info.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                background: transparent;
            }
        """)
        header_layout.addWidget(user_info)
        
        layout.addWidget(header_frame)
    
    def create_catalog_section(self):
        """Crée la section catalogue avec filtres et produits"""
        catalog_widget = QWidget()
        catalog_layout = QVBoxLayout(catalog_widget)
        
        # Barre de recherche et filtres
        filters_frame = QFrame()
        filters_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        filters_layout = QHBoxLayout(filters_frame)
        
        # Recherche
        search_label = QLabel("🔍 Rechercher:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Nom du produit...")
        self.search_edit.textChanged.connect(self.filter_products)
        
        # Filtre par catégorie
        category_label = QLabel("📂 Catégorie:")
        self.category_combo = QComboBox()
        self.category_combo.currentTextChanged.connect(self.filter_products)
        
        filters_layout.addWidget(search_label)
        filters_layout.addWidget(self.search_edit, 2)
        filters_layout.addWidget(category_label)
        filters_layout.addWidget(self.category_combo, 1)
        filters_layout.addStretch()
        
        catalog_layout.addWidget(filters_frame)
        
        # Zone de produits (grille scrollable)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.products_grid_widget = QWidget()
        self.products_grid_layout = QGridLayout(self.products_grid_widget)
        self.products_grid_layout.setSpacing(15)
        
        scroll_area.setWidget(self.products_grid_widget)
        catalog_layout.addWidget(scroll_area)
        
        return catalog_widget
    
    def create_cart_section(self):
        """Crée la section panier avec total et paiement"""
        cart_widget = QWidget()
        cart_layout = QVBoxLayout(cart_widget)
        
        # Titre du panier
        cart_title = QLabel("🛒 Panier")
        cart_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #1976D2;
                padding: 10px;
                border-bottom: 2px solid #E3F2FD;
            }
        """)
        cart_layout.addWidget(cart_title)
        
        # Sélection client
        client_frame = QFrame()
        client_layout = QHBoxLayout(client_frame)
        client_layout.addWidget(QLabel("👤 Client:"))
        
        self.client_combo = QComboBox()
        self.client_combo.setEditable(True)
        client_layout.addWidget(self.client_combo)
        
        cart_layout.addWidget(client_frame)
        
        # Liste des articles du panier
        self.cart_table = QTableWidget(0, 4)
        self.cart_table.setHorizontalHeaderLabels(["Produit", "Qté", "Prix", "Total"])
        self.cart_table.horizontalHeader().setStretchLastSection(True)
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.setAlternatingRowColors(True)
        cart_layout.addWidget(self.cart_table)
        
        # Zone totaux
        totals_frame = self.create_totals_section()
        cart_layout.addWidget(totals_frame)
        
        # Boutons d'action
        actions_frame = self.create_actions_section()
        cart_layout.addWidget(actions_frame)
        
        return cart_widget
    
    def create_totals_section(self):
        """Crée la section des totaux avec remise"""
        totals_frame = QFrame()
        totals_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        totals_layout = QFormLayout(totals_frame)
        
        # Sous-total
        self.subtotal_label = QLabel("0.00 FC")
        totals_layout.addRow("Sous-total:", self.subtotal_label)
        
        # Remise globale
        discount_widget = QWidget()
        discount_layout = QHBoxLayout(discount_widget)
        discount_layout.setContentsMargins(0, 0, 0, 0)
        
        self.discount_spin = QDoubleSpinBox()
        self.discount_spin.setRange(0, 999999)
        self.discount_spin.setSuffix(" FC")
        self.discount_spin.valueChanged.connect(self.update_totals)
        
        apply_discount_btn = QPushButton("Appliquer")
        apply_discount_btn.clicked.connect(self.apply_discount)
        
        discount_layout.addWidget(self.discount_spin)
        discount_layout.addWidget(apply_discount_btn)
        
        totals_layout.addRow("Remise:", discount_widget)
        
        # Montant de la remise
        self.discount_amount_label = QLabel("0.00 FC")
        totals_layout.addRow("Montant remise:", self.discount_amount_label)
        
        # Total final
        self.total_label = QLabel("0.00 FC")
        self.total_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #4CAF50;
            }
        """)
        totals_layout.addRow("TOTAL:", self.total_label)
        
        return totals_frame
    
    def create_actions_section(self):
        """Crée la section des boutons d'action"""
        actions_frame = QFrame()
        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setSpacing(8)
        
        # Bouton valider commande
        validate_btn = QPushButton("💳 Valider & Payer")
        validate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        validate_btn.clicked.connect(self.validate_and_pay)
        actions_layout.addWidget(validate_btn)
        
        # Bouton vider panier
        clear_btn = QPushButton("🗑️ Vider le panier")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 12px;
                padding: 8px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        clear_btn.clicked.connect(self.clear_cart)
        actions_layout.addWidget(clear_btn)
        
        return actions_frame
    
    def create_product_card(self, product):
        """Crée une carte produit moderne"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px;
            }
            QFrame:hover {
                border-color: #2196F3;
                background-color: #F3F9FF;
            }
        """)
        card.setFixedSize(200, 250)
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(8)
        
        # Image produit (placeholder)
        image_label = QLabel()
        image_label.setFixedSize(160, 120)
        image_label.setStyleSheet("""
            QLabel {
                background-color: #F5F5F5;
                border: 1px dashed #BDBDBD;
                border-radius: 4px;
            }
        """)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setText("📦\nImage")
        card_layout.addWidget(image_label, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Nom du produit
        name_label = QLabel(product.name[:25] + "..." if len(product.name) > 25 else product.name)
        name_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #333;
                background: transparent;
            }
        """)
        name_label.setWordWrap(True)
        card_layout.addWidget(name_label)
        
        # Prix
        price_label = QLabel(f"{product.price_unit:.0f} FC")
        price_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #4CAF50;
                background: transparent;
            }
        """)
        card_layout.addWidget(price_label)
        
        # Bouton d'ajout au panier
        add_btn = QPushButton("➕ Ajouter")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        add_btn.clicked.connect(lambda: self.add_to_cart(product))
        card_layout.addWidget(add_btn)
        
        return card
    
    def apply_modern_style(self):
        """Applique le style moderne général"""
        self.setStyleSheet("""
            QWidget {
                background-color: #FAFAFA;
                font-family: 'Segoe UI', sans-serif;
            }
            
            QFrame {
                background-color: white;
            }
            
            QLineEdit {
                padding: 8px;
                border: 2px solid #E0E0E0;
                border-radius: 4px;
                font-size: 13px;
            }
            
            QLineEdit:focus {
                border-color: #2196F3;
            }
            
            QComboBox {
                padding: 8px;
                border: 2px solid #E0E0E0;
                border-radius: 4px;
                font-size: 13px;
            }
            
            QTableWidget {
                background-color: white;
                gridline-color: #E0E0E0;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
            }
            
            QTableWidget::item {
                padding: 8px;
            }
            
            QTableWidget::item:selected {
                background-color: #E3F2FD;
            }
            
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
    
    def load_initial_data(self):
        """Charge les données initiales"""
        self.load_categories()
        self.load_clients()
        self.load_products()
    
    def load_categories(self):
        """Charge les catégories de produits"""
        try:
            with self.db_manager.get_session() as session:
                categories = session.query(CoreProductCategory).filter_by(is_active=True).all()
                
                self.category_combo.clear()
                self.category_combo.addItem("Toutes les catégories", None)
                
                for category in categories:
                    self.category_combo.addItem(category.name, category.id)
                    
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des catégories: {e}")
    
    def load_clients(self):
        """Charge la liste des clients"""
        try:
            with self.db_manager.get_session() as session:
                clients = session.query(ShopClient).filter_by(
                    pos_id=self.pos_id, 
                    is_active=True
                ).all()
                
                self.client_combo.clear()
                self.client_combo.addItem("Client anonyme", None)
                
                for client in clients:
                    display_name = f"{client.nom} {client.prenom or ''}".strip()
                    self.client_combo.addItem(display_name, client.id)
                    
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des clients: {e}")
    
    def load_products(self):
        """Charge et affiche les produits dans la grille"""
        try:
            with self.db_manager.get_session() as session:
                query = session.query(CoreProduct).filter_by(is_active=True)
                
                # Appliquer le filtre de catégorie si sélectionné
                category_id = self.category_combo.currentData()
                if category_id:
                    query = query.filter_by(category_id=category_id)
                
                # Appliquer le filtre de recherche
                search_text = self.search_edit.text().strip()
                if search_text:
                    query = query.filter(CoreProduct.name.ilike(f'%{search_text}%'))
                
                products = query.all()
                self.display_products(products)
                
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des produits: {e}")
    
    def display_products(self, products):
        """Affiche les produits dans la grille"""
        # Vider la grille existante
        for i in reversed(range(self.products_grid_layout.count())):
            child = self.products_grid_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Ajouter les nouveaux produits
        cols = 3  # 3 colonnes de produits
        for i, product in enumerate(products):
            row = i // cols
            col = i % cols
            
            product_card = self.create_product_card(product)
            self.products_grid_layout.addWidget(product_card, row, col)
        
        # Ajouter un stretch pour pousser les cartes vers le haut
        self.products_grid_layout.setRowStretch(len(products) // cols + 1, 1)
    
    def filter_products(self):
        """Filtre les produits selon les critères de recherche"""
        self.load_products()
    
    def add_to_cart(self, product):
        """Ajoute un produit au panier avec dialogue de quantité"""
        try:
            # Vérifier le stock disponible
            available_stock = self.get_available_stock(product.id)
            
            # Ouvrir le dialogue de quantité
            quantity_dialog = QuantityDialog(
                self, 
                product.name, 
                available_stock
            )
            
            if quantity_dialog.exec() == QDialog.DialogCode.Accepted:
                quantity = quantity_dialog.get_quantity()
                
                # Vérifier si le produit est déjà dans le panier
                existing_item = None
                for item in self.current_cart:
                    if item['product_id'] == product.id:
                        existing_item = item
                        break
                
                if existing_item:
                    # Mettre à jour la quantité existante
                    existing_item['quantity'] += quantity
                    print(f"Quantité mise à jour pour {product.name}: {existing_item['quantity']}")
                else:
                    # Nouveau produit dans le panier
                    new_item = {
                        'product_id': product.id,
                        'product_name': product.name,
                        'unit_price': product.price_unit,
                        'quantity': quantity
                    }
                    self.current_cart.append(new_item)
                    print(f"Nouveau produit ajouté: {product.name}, quantité: {quantity}")
                
                # Mettre à jour l'affichage
                self.update_cart_display()
                self.update_totals()
                
                # Émettre les signaux
                self.product_added_to_cart.emit(product.id, quantity)
                self.cart_updated.emit()
                
                # Message de confirmation
                QMessageBox.information(
                    self,
                    "Produit ajouté",
                    f"{product.name}\\nQuantité: {quantity}\\nAjouté au panier avec succès !"
                )
        
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de l'ajout au panier: {e}")
            print(f"Erreur add_to_cart: {e}")
    
    def get_available_stock(self, product_id):
        """Récupère le stock disponible pour un produit dans l'entrepôt POS_2"""
        try:
            with self.db_manager.get_session() as session:
                from sqlalchemy import text
                
                result = session.execute(text("""
                    SELECT spe.quantity 
                    FROM stock_produits_entrepot spe
                    JOIN stock_warehouses sw ON spe.warehouse_id = sw.id
                    WHERE spe.product_id = :product_id 
                    AND sw.code = 'POS_2'
                    AND sw.is_active = 1
                """), {'product_id': product_id})
                
                row = result.fetchone()
                return float(row[0]) if row and row[0] is not None else 0.0
                
        except Exception as e:
            print(f"Erreur récupération stock: {e}")
            return None
    
    def update_cart_display(self):
        """Met à jour l'affichage du panier"""
        # Déconnecter temporairement le signal pour éviter les boucles
        try:
            self.cart_table.itemChanged.disconnect()
        except:
            pass
        
        self.cart_table.setRowCount(len(self.current_cart))
        
        for row, item in enumerate(self.current_cart):
            # Nom du produit
            name_item = QTableWidgetItem(item['product_name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Non-éditable
            self.cart_table.setItem(row, 0, name_item)
            
            # Quantité (editable)
            qty_item = QTableWidgetItem(str(item['quantity']))
            qty_item.setData(Qt.ItemDataRole.UserRole, row)  # Stocker l'index pour modification
            self.cart_table.setItem(row, 1, qty_item)
            
            # Prix unitaire
            price_item = QTableWidgetItem(f"{item['unit_price']:.0f}")
            price_item.setFlags(price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Non-éditable
            self.cart_table.setItem(row, 2, price_item)
            
            # Total ligne
            total_line = item['unit_price'] * item['quantity']
            total_item = QTableWidgetItem(f"{total_line:.0f}")
            total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Non-éditable
            self.cart_table.setItem(row, 3, total_item)
        
        # Reconnecter le signal
        self.cart_table.itemChanged.connect(self.on_cart_item_changed)
        
        # Ajuster la largeur des colonnes
        header = self.cart_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Produit
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)    # Quantité
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)    # Prix
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)    # Total
        
        self.cart_table.setColumnWidth(1, 80)  # Quantité
        self.cart_table.setColumnWidth(2, 80)  # Prix
        self.cart_table.setColumnWidth(3, 90)  # Total
    
    def on_cart_item_changed(self, item):
        """Gère les modifications dans le panier"""
        if item.column() == 1:  # Colonne quantité
            try:
                row = item.data(Qt.ItemDataRole.UserRole)
                if row is None or row >= len(self.current_cart):
                    return
                    
                new_qty_text = item.text().strip()
                if not new_qty_text:
                    return
                    
                new_qty = int(new_qty_text)
                
                if new_qty > 0:
                    # Vérifier le stock disponible
                    product_id = self.current_cart[row]['product_id']
                    available_stock = self.get_available_stock(product_id)
                    
                    if available_stock is not None and new_qty > available_stock:
                        QMessageBox.warning(
                            self, 
                            "Stock insuffisant",
                            f"Stock disponible: {available_stock:.0f}\\nQuantité demandée: {new_qty}"
                        )
                        # Restaurer la quantité précédente
                        self.update_cart_display()
                        return
                    
                    # Mettre à jour la quantité
                    self.current_cart[row]['quantity'] = new_qty
                    self.update_cart_display()
                    self.update_totals()
                    self.cart_updated.emit()
                    
                else:
                    # Demander confirmation pour supprimer l'article
                    product_name = self.current_cart[row]['product_name']
                    reply = QMessageBox.question(
                        self,
                        "Supprimer l'article",
                        f"Supprimer '{product_name}' du panier ?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    
                    if reply == QMessageBox.StandardButton.Yes:
                        del self.current_cart[row]
                        self.update_cart_display()
                        self.update_totals()
                        self.cart_updated.emit()
                    else:
                        # Restaurer la quantité précédente
                        self.update_cart_display()
                    
            except (ValueError, IndexError) as e:
                print(f"Erreur modification panier: {e}")
                # Restaurer l'affichage en cas d'erreur
                self.update_cart_display()
                QMessageBox.warning(
                    self,
                    "Erreur",
                    "Veuillez saisir un nombre entier valide pour la quantité"
                )
    
    def update_totals(self):
        """Met à jour les totaux du panier"""
        subtotal = sum(item['unit_price'] * item['quantity'] for item in self.current_cart)
        
        # Calculer la remise (montant fixe)
        discount_amount = Decimal(str(self.discount_spin.value()))
        
        # S'assurer que la remise ne dépasse pas le sous-total
        if discount_amount > subtotal:
            discount_amount = subtotal
            self.discount_spin.setValue(float(subtotal))
        
        total = subtotal - discount_amount
        
        # Mettre à jour les labels
        self.subtotal_label.setText(f"{subtotal:.0f} FC")
        self.discount_amount_label.setText(f"{discount_amount:.0f} FC")
        self.total_label.setText(f"{total:.0f} FC")
    
    def apply_discount(self):
        """Applique la remise globale"""
        discount_amount = self.discount_spin.value()
        self.global_discount = Decimal(str(discount_amount))
        self.update_totals()
        
        QMessageBox.information(
            self, 
            "Remise appliquée", 
            f"Remise de {discount_amount:.0f} FC appliquée à la commande"
        )
    
    def clear_cart(self):
        """Vide le panier"""
        reply = QMessageBox.question(
            self, 
            "Confirmer", 
            "Êtes-vous sûr de vouloir vider le panier ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.current_cart = []
            self.global_discount = Decimal('0.00')
            self.discount_spin.setValue(0)
            self.update_cart_display()
            self.update_totals()
            self.cart_updated.emit()
    
    def validate_and_pay(self):
        """Valide la commande et procède au paiement"""
        if not self.current_cart:
            QMessageBox.warning(self, "Panier vide", "Veuillez ajouter des produits au panier")
            return
        
        # Vérifier la disponibilité du stock avant de procéder
        stock_validation = self._validate_stock_availability()
        if not stock_validation['valid']:
            QMessageBox.warning(
                self, 
                "Stock insuffisant", 
                f"Stock insuffisant pour :\n{stock_validation['message']}\n\n"
                "Veuillez ajuster les quantités ou retirer les produits concernés."
            )
            return
        
        # Ouvrir le dialogue de paiement
        payment_dialog = PaymentDialog(self, self.current_cart, self.global_discount)
        if payment_dialog.exec() == QDialog.DialogCode.Accepted:
            # Traiter la vente
            self.process_sale(payment_dialog.get_payment_data())
    
    def _validate_stock_availability(self):
        """Valide que tous les produits du panier sont disponibles en stock"""
        try:
            with self.db_manager.get_session() as session:
                from sqlalchemy import text
                
                # Chercher l'entrepôt POS_2
                warehouse_result = session.execute(text("""
                    SELECT id FROM stock_warehouses 
                    WHERE code = 'POS_2' AND is_active = 1
                    LIMIT 1
                """))
                
                warehouse_row = warehouse_result.fetchone()
                if not warehouse_row:
                    return {
                        'valid': False,
                        'message': "Entrepôt POS_2 non trouvé ou inactif"
                    }
                
                warehouse_id = warehouse_row[0]
                unavailable_products = []
                
                for item in self.current_cart:
                    product_id = item['product_id']
                    required_qty = item['quantity']
                    
                    # Vérifier le stock disponible
                    stock_result = session.execute(text("""
                        SELECT COALESCE(quantity, 0) as available_qty
                        FROM stock_produits_entrepot 
                        WHERE product_id = :product_id AND warehouse_id = :warehouse_id
                    """), {
                        'product_id': product_id,
                        'warehouse_id': warehouse_id
                    })
                    
                    stock_row = stock_result.fetchone()
                    available_qty = stock_row[0] if stock_row else 0
                    
                    # Bloquer si stock insuffisant (y compris stocks négatifs)
                    if available_qty <= 0 or available_qty < required_qty:
                        unavailable_products.append(
                            f"• {item['product_name']}: "
                            f"Demandé {required_qty}, Disponible {max(0, available_qty)}"
                        )
                
                if unavailable_products:
                    return {
                        'valid': False,
                        'message': '\n'.join(unavailable_products)
                    }
                
                return {'valid': True, 'message': 'Stock suffisant'}
                
        except Exception as e:
            return {
                'valid': False,
                'message': f"Erreur lors de la vérification du stock: {e}"
            }
    
    def process_sale(self, payment_data):
        """Traite la vente et met à jour le stock"""
        try:
            with self.db_manager.get_session() as session:
                from datetime import datetime
                from sqlalchemy import text
                
                # Calculer les totaux avec remise en montant
                subtotal = sum(item['unit_price'] * item['quantity'] for item in self.current_cart)
                discount_amount = self.global_discount  # Montant fixe
                total_amount = subtotal - discount_amount
                
                # 1. Créer la vente principale (utiliser une table temporaire ou existante)
                sale_data = {
                    'pos_id': self.pos_id,
                    'client_id': self.client_combo.currentData(),
                    'user_id': getattr(self.current_user, 'id', 1),
                    'subtotal': float(subtotal),
                    'discount_amount': float(discount_amount),
                    'total_amount': float(total_amount),
                    'payment_method': payment_data['method'],
                    'amount_received': payment_data['amount_received'],
                    'change_amount': payment_data['change'],
                    'sale_date': datetime.now(),
                    'status': 'completed'
                }
                
                # Créer un panier temporaire pour tracer la vente
                panier_result = session.execute(text("""
                    INSERT INTO shop_panier 
                    (pos_id, client_id, user_id, total_amount, discount_amount, 
                     payment_method, status, created_at, updated_at)
                    VALUES (:pos_id, :client_id, :user_id, :total_amount, :discount_amount,
                            :payment_method, :status, :created_at, :updated_at)
                """), {
                    'pos_id': self.pos_id,
                    'client_id': sale_data['client_id'],
                    'user_id': sale_data['user_id'], 
                    'total_amount': sale_data['total_amount'],
                    'discount_amount': sale_data['discount_amount'],
                    'payment_method': sale_data['payment_method'],
                    'status': 'completed',
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                })
                
                session.flush()
                
                # Récupérer l'ID du panier créé
                panier_id_result = session.execute(text("SELECT last_insert_rowid()"))
                panier_id = panier_id_result.fetchone()[0]
                
                # 2. Créer les lignes de vente et gérer le stock
                for item in self.current_cart:
                    product_id = item['product_id']
                    quantity = item['quantity']
                    unit_price = item['unit_price']
                    line_total = unit_price * quantity
                    
                    # Créer la ligne de panier
                    session.execute(text("""
                        INSERT INTO shop_panier_items 
                        (panier_id, product_id, quantity, unit_price, total_price, created_at)
                        VALUES (:panier_id, :product_id, :quantity, :unit_price, :total_price, :created_at)
                    """), {
                        'panier_id': panier_id,
                        'product_id': product_id,
                        'quantity': quantity,
                        'unit_price': float(unit_price),
                        'total_price': float(line_total),
                        'created_at': datetime.now()
                    })
                    
                    # 3. Gérer le stock POS (sortie de stock)
                    self._update_pos_stock(session, product_id, quantity)
                
                # 4. Créer les écritures comptables si le module comptabilité est configuré
                self._create_sale_accounting_entries(session, sale_data, panier_id)
                
                # Valider la transaction
                session.commit()
                
                # Afficher le reçu
                self._show_sale_receipt(sale_data, payment_data)
                
                # Nettoyer le panier
                self.clear_cart()
                
                QMessageBox.information(
                    self, 
                    "Vente réussie", 
                    f"Vente #{panier_id} enregistrée avec succès\\n"
                    f"Total: {total_amount:.0f} FC\\n"
                    f"Paiement: {payment_data['method']}"
                )
                
                self.sale_completed.emit(panier_id)
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la vente: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_pos_stock(self, session, product_id, quantity_sold):
        """Met à jour le stock POS (soustraction automatique depuis l'entrepôt POS_2)"""
        try:
            from sqlalchemy import text
            
            # Chercher l'entrepôt avec le code POS_2 (entrepôt boutique)
            warehouse_result = session.execute(text("""
                SELECT id FROM stock_warehouses 
                WHERE code = 'POS_2' AND is_active = 1
                LIMIT 1
            """))
            
            warehouse_row = warehouse_result.fetchone()
            if not warehouse_row:
                print(f"⚠️ Entrepôt boutique (POS_2) non trouvé ou inactif")
                return
            
            warehouse_id = warehouse_row[0]
            
            # Vérifier le stock disponible avant la vente
            stock_check = session.execute(text("""
                SELECT quantity FROM stock_produits_entrepot 
                WHERE product_id = :product_id AND warehouse_id = :warehouse_id
            """), {
                'product_id': product_id,
                'warehouse_id': warehouse_id
            })
            
            stock_row = stock_check.fetchone()
            current_stock = stock_row[0] if stock_row else 0
            
            # Cette vérification est faite en amont, on peut procéder directement
            print(f"📦 Stock POS_2 avant vente: Produit {product_id}, Stock: {current_stock}, Vente: {quantity_sold}")
            
            # Mettre à jour le stock produit-entrepôt
            session.execute(text("""
                UPDATE stock_produits_entrepot 
                SET quantity = quantity - :quantity_sold,
                    last_movement_date = CURRENT_TIMESTAMP
                WHERE product_id = :product_id AND warehouse_id = :warehouse_id
            """), {
                'product_id': product_id,
                'warehouse_id': warehouse_id,
                'quantity_sold': quantity_sold
            })
            
            # Créer un mouvement de stock (sortie/vente)
            session.execute(text("""
                INSERT INTO stock_mouvements 
                (product_id, warehouse_id, destination_warehouse_id, movement_type, 
                 quantity, unit_cost, total_cost, reference, description, movement_date, user_id)
                VALUES (:product_id, :warehouse_id, NULL, 'SORTIE', :quantity, 
                        :unit_cost, :total_cost, :reference, :description, CURRENT_TIMESTAMP, :user_id)
            """), {
                'product_id': product_id,
                'warehouse_id': warehouse_id,
                'quantity': -quantity_sold,  # Négatif pour sortie
                'unit_cost': self._get_product_cost(session, product_id),
                'total_cost': -quantity_sold * self._get_product_cost(session, product_id),
                'reference': f"VENTE-BOUTIQUE-{self.pos_id}",
                'description': f"Vente boutique depuis entrepôt POS_2",
                'user_id': getattr(self.current_user, 'id', 1)
            })
            
            print(f"✅ Stock boutique (POS_2) mis à jour: Produit {product_id}, Quantité: -{quantity_sold}")
            
        except Exception as e:
            print(f"❌ Erreur mise à jour stock boutique: {e}")
            import traceback
            traceback.print_exc()
            # Ne pas faire échouer la vente pour un problème de stock
    
    def _get_product_cost(self, session, product_id):
        """Récupère le coût du produit"""
        try:
            from sqlalchemy import text
            result = session.execute(text("""
                SELECT COALESCE(cost, price_unit) FROM core_products WHERE id = :product_id
            """), {'product_id': product_id})
            
            row = result.fetchone()
            return float(row[0]) if row else 0.0
        except:
            return 0.0
    
    def _create_sale_accounting_entries(self, session, sale_data, sale_id):
        """Crée les écritures comptables pour la vente"""
        try:
            from sqlalchemy import text
            from datetime import datetime
            
            # Vérifier si la configuration comptable existe
            config_result = session.execute(text("""
                SELECT compte_vente_id, compte_caisse_id 
                FROM compta_config 
                WHERE enterprise_id = (SELECT enterprise_id FROM core_pos_points WHERE id = :pos_id)
                LIMIT 1
            """), {'pos_id': self.pos_id})
            
            config_row = config_result.fetchone()
            if not config_row or not config_row[0]:
                print("⚠️ Configuration comptable manquante pour les ventes")
                return
            
            compte_vente_id = config_row[0]
            compte_caisse_id = config_row[1] or compte_vente_id  # Fallback
            
            # Créer le journal comptable
            journal_result = session.execute(text("""
                INSERT INTO compta_journaux 
                (date_operation, libelle, montant, type_operation, reference, description, 
                 enterprise_id, user_id, date_creation, date_modification)
                VALUES (:date_operation, :libelle, :montant, :type_operation, :reference, 
                        :description, :enterprise_id, :user_id, :date_creation, :date_modification)
            """), {
                'date_operation': datetime.now(),
                'libelle': f"Vente POS {self.pos_id} - #{sale_id}",
                'montant': sale_data['total_amount'],
                'type_operation': 'entree',
                'reference': f"VENTE-{sale_id}",
                'description': f"Vente boutique - Paiement: {sale_data['payment_method']}",
                'enterprise_id': 1,  # TODO: Récupérer dynamiquement
                'user_id': sale_data['user_id'],
                'date_creation': datetime.now(),
                'date_modification': datetime.now()
            })
            
            session.flush()
            
            # Récupérer l'ID du journal
            journal_id_result = session.execute(text("SELECT last_insert_rowid()"))
            journal_id = journal_id_result.fetchone()[0]
            
            # Écriture débit : Caisse (entrée d'argent)
            session.execute(text("""
                INSERT INTO compta_ecritures 
                (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
            """), {
                'journal_id': journal_id,
                'compte_id': compte_caisse_id,
                'debit': sale_data['total_amount'],
                'credit': 0,
                'ordre': 1,
                'libelle': f"Encaissement vente - {sale_data['payment_method']}",
                'date_creation': datetime.now()
            })
            
            # Écriture crédit : Vente (produit vendu)
            session.execute(text("""
                INSERT INTO compta_ecritures 
                (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
            """), {
                'journal_id': journal_id,
                'compte_id': compte_vente_id,
                'debit': 0,
                'credit': sale_data['total_amount'],
                'ordre': 2,
                'libelle': f"Vente produits POS {self.pos_id}",
                'date_creation': datetime.now()
            })
            
            print(f"✅ Écritures comptables créées - Journal ID: {journal_id}")
            
        except Exception as e:
            print(f"❌ Erreur écritures comptables vente: {e}")
            # Ne pas faire échouer la vente pour un problème comptable
    
    def _show_sale_receipt(self, sale_data, payment_data):
        """Affiche le reçu de vente"""
        receipt_text = f"""
        ===== REÇU DE VENTE =====
        
        Date: {sale_data['sale_date'].strftime('%d/%m/%Y %H:%M')}
        POS: #{self.pos_id}
        Vendeur: {getattr(self.current_user, 'name', 'Utilisateur')}
        
        --- DÉTAIL ---
        """
        
        for item in self.current_cart:
            receipt_text += f"\\n{item['product_name']}"
            receipt_text += f"\\n  {item['quantity']} x {item['unit_price']:.0f} FC = {item['unit_price'] * item['quantity']:.0f} FC"
        
        receipt_text += f"""
        
        --- TOTAUX ---
        Sous-total: {sale_data['subtotal']:.0f} FC
        Remise: -{sale_data['discount_amount']:.0f} FC
        TOTAL: {sale_data['total_amount']:.0f} FC
        
        --- PAIEMENT ---
        Méthode: {payment_data['method']}
        Reçu: {payment_data['amount_received']:.0f} FC
        Monnaie: {payment_data['change']:.0f} FC
        
        Merci pour votre achat !
        =========================
        """
        
        # Afficher dans un dialogue
        receipt_dialog = QDialog(self)
        receipt_dialog.setWindowTitle("Reçu de vente")
        receipt_dialog.setFixedSize(400, 600)
        
        layout = QVBoxLayout(receipt_dialog)
        
        receipt_display = QTextEdit()
        receipt_display.setPlainText(receipt_text)
        receipt_display.setReadOnly(True)
        receipt_display.setStyleSheet("""
            QTextEdit {
                font-family: 'Courier New', monospace;
                font-size: 11px;
                background-color: white;
            }
        """)
        layout.addWidget(receipt_display)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        print_btn = QPushButton("🖨️ Imprimer")
        print_btn.clicked.connect(lambda: self._print_receipt(receipt_text))
        buttons_layout.addWidget(print_btn)
        
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(receipt_dialog.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
        
        receipt_dialog.exec()
    
    def _print_receipt(self, receipt_text):
        """Imprime le reçu (fonction placeholder)"""
        QMessageBox.information(
            self, 
            "Impression", 
            "Fonction d'impression à implémenter\\n"
            "Le reçu peut être copié depuis la fenêtre"
        )


class QuantityDialog(QDialog):
    """Dialogue pour saisir la quantité d'un produit"""
    
    def __init__(self, parent, product_name, available_stock=None):
        super().__init__(parent)
        self.product_name = product_name
        self.available_stock = available_stock
        self.selected_quantity = 1
        
        self.init_ui()
    
    def init_ui(self):
        """Initialise l'interface du dialogue de quantité"""
        self.setWindowTitle("Ajouter au panier")
        self.setModal(True)
        self.setFixedSize(350, 200)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Titre avec nom du produit
        title_label = QLabel(f"📦 {self.product_name}")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2196F3;
                padding: 10px;
                background-color: #E3F2FD;
                border-radius: 6px;
            }
        """)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Formulaire de quantité
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        
        # Saisie de quantité
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(9999)
        self.quantity_spin.setValue(1)
        self.quantity_spin.setSuffix(" unité(s)")
        self.quantity_spin.setStyleSheet("""
            QSpinBox {
                padding: 8px;
                font-size: 14px;
                border: 2px solid #E0E0E0;
                border-radius: 4px;
            }
            QSpinBox:focus {
                border-color: #2196F3;
            }
        """)
        
        # Afficher le stock disponible si connu
        if self.available_stock is not None:
            self.quantity_spin.setMaximum(max(1, int(self.available_stock)))
            stock_label = QLabel(f"Stock disponible: {self.available_stock}")
            stock_label.setStyleSheet("color: #666; font-size: 12px;")
            form_layout.addRow("", stock_label)
        
        form_layout.addRow("Quantité:", self.quantity_spin)
        layout.addWidget(form_widget)
        
        layout.addStretch()
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        add_btn = QPushButton("➕ Ajouter au panier")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        add_btn.clicked.connect(self.accept)
        add_btn.setDefault(True)
        
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(add_btn)
        layout.addLayout(buttons_layout)
        
        # Focus sur la quantité
        self.quantity_spin.setFocus()
        self.quantity_spin.selectAll()
    
    def get_quantity(self):
        """Retourne la quantité sélectionnée"""
        return self.quantity_spin.value()


class PaymentDialog(QDialog):
    """Dialogue de paiement moderne"""
    
    def __init__(self, parent, cart_items, discount, total_amount=None):
        super().__init__(parent)
        self.cart_items = cart_items
        self.discount = discount
        
        if total_amount is None:
            subtotal = sum(item['unit_price'] * item['quantity'] for item in cart_items)
            discount_amount = subtotal * discount / 100
            self.total_amount = subtotal - discount_amount
        else:
            self.total_amount = total_amount
        
        self.init_ui()
    
    def init_ui(self):
        """Initialise l'interface du dialogue de paiement"""
        self.setWindowTitle("💳 Paiement")
        self.setModal(True)
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Récapitulatif
        summary_group = QGroupBox("Récapitulatif de la commande")
        summary_layout = QFormLayout(summary_group)
        
        summary_layout.addRow("Nombre d'articles:", QLabel(str(len(self.cart_items))))
        summary_layout.addRow("Remise appliquée:", QLabel(f"{self.discount}%"))
        
        total_label = QLabel(f"{self.total_amount:.0f} FC")
        total_label.setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 16px;")
        summary_layout.addRow("TOTAL À PAYER:", total_label)
        
        layout.addWidget(summary_group)
        
        # Mode de paiement
        payment_group = QGroupBox("Mode de paiement")
        payment_layout = QFormLayout(payment_group)
        
        self.payment_method = QComboBox()
        self.payment_method.addItems(["Espèces", "Carte bancaire", "Mobile Money", "Crédit"])
        payment_layout.addRow("Méthode:", self.payment_method)
        
        self.amount_received = QDoubleSpinBox()
        self.amount_received.setRange(0, 999999)
        self.amount_received.setValue(float(self.total_amount))
        self.amount_received.setSuffix(" FC")
        payment_layout.addRow("Montant reçu:", self.amount_received)
        
        layout.addWidget(payment_group)
        
        # Boutons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_payment_data(self):
        """Retourne les données de paiement"""
        return {
            'method': self.payment_method.currentText(),
            'amount_received': self.amount_received.value(),
            'total_amount': float(self.total_amount),
            'change': self.amount_received.value() - float(self.total_amount)
        }