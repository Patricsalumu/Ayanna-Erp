"""
Widget de l'onglet Produits - Gestion des produits de la boutique
"""

from typing import List, Optional
from decimal import Decimal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton, 
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, 
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout, QTextEdit, 
    QDoubleSpinBox, QSpinBox, QCheckBox, QTabWidget, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPixmap

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.core.models import CoreProduct, CoreProductCategory
from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ComptabiliteController
import os
import shutil
from datetime import datetime


class ProduitIndex(QWidget):
    """Widget de gestion des produits"""
    
    # Signaux
    product_updated = pyqtSignal(int)  # product_id
    
    def __init__(self, pos_id, current_user):
        super().__init__()
        from ayanna_erp.modules.boutique.controller.produit_controller import ProduitController
        self.produit_controller = ProduitController(pos_id)
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
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)  # Marges minimales
        main_layout.setSpacing(5)  # Espacement minimal entre les zones

        # === PARTIE GAUCHE : TABLEAU PRODUITS ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)  # Pas de marges internes

        header_group = QGroupBox("📦 Gestion des Produits")
        header_layout = QVBoxLayout(header_group)
        header_layout.setContentsMargins(5, 5, 5, 5)  # Marges minimales

        # Actions principales
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(5)
        self.new_product_btn = QPushButton("➕ Nouveau Produit")
        self.new_product_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                font-weight: bold;
                padding: 2px 2px;
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

        # Filtres de recherche
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(5)
        filter_layout.addWidget(QLabel("Recherche:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nom ou description du produit...")
        self.search_input.textChanged.connect(self.on_search_changed)
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(QLabel("Catégorie:"))
        self.category_combo = QComboBox()
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        filter_layout.addWidget(self.category_combo)
        filter_layout.addWidget(QLabel("Statut:"))
        self.status_combo = QComboBox()
        self.status_combo.addItem("Tous", None)
        self.status_combo.addItem("Actifs seulement", True)
        self.status_combo.addItem("Inactifs seulement", False)
        self.status_combo.currentTextChanged.connect(self.refresh_products)
        filter_layout.addWidget(self.status_combo)
        header_layout.addLayout(filter_layout)
        left_layout.addWidget(header_group)

        # Tableau des produits
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(8)
        self.products_table.setHorizontalHeaderLabels([
            "ID", "Nom", "Catégorie", "Prix", "Stock", "Unité", "Statut", "Actions"
        ])
        header = self.products_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.products_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Désactiver l'édition directe
        left_layout.addWidget(self.products_table)

        # === PARTIE DROITE : DÉTAILS PRODUIT ===
        self.detail_widget = QGroupBox("Détails du produit")
        self.detail_layout = QVBoxLayout(self.detail_widget)
        self.detail_layout.setContentsMargins(5, 5, 5, 5)
        
        # Conteneur pour l'image et les détails textuels
        details_container = QHBoxLayout()
        
        # Zone d'image (partie gauche) avec titre
        image_container = QVBoxLayout()
        image_title = QLabel("Image")
        image_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_title.setStyleSheet("font-weight: bold; color: #2C3E50; margin-bottom: 5px;")
        image_container.addWidget(image_title)
        
        self.image_label = QLabel()
        self.image_label.setFixedSize(120, 120)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 2px solid #BDC3C7;
                border-radius: 8px;
                background-color: #F8F9FA;
            }
        """)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setText("Aucune\nimage")
        self.image_label.setScaledContents(True)
        image_container.addWidget(self.image_label)
        image_container.addStretch()  # Pour pousser l'image vers le haut
        
        details_container.addLayout(image_container)
        
        # Zone de texte (partie droite)
        self.detail_label = QLabel("Sélectionnez un produit pour voir les détails.")
        self.detail_label.setWordWrap(True)
        self.detail_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        details_container.addWidget(self.detail_label, stretch=1)
        
        self.detail_layout.addLayout(details_container)

        # Ajout au layout principal avec proportions 70/30
        main_layout.addWidget(left_widget, stretch=7)
        main_layout.addWidget(self.detail_widget, stretch=3)

        # Connexion du clic sur le tableau
        self.products_table.cellClicked.connect(self.on_product_selected)
        # Connexion du double-clic pour édition
        self.products_table.cellDoubleClicked.connect(self.on_product_double_clicked)

    def on_product_selected(self, row, column):
        product_id_item = self.products_table.item(row, 0)
        if not product_id_item:
            self.detail_label.setText("Aucun produit sélectionné.")
            self.image_label.clear()
            self.image_label.setText("Aucune\nimage")
            return
        product_id = int(product_id_item.text())
        with self.db_manager.get_session() as session:
            product = self.produit_controller.get_product_by_id(session, product_id)
            if not product:
                self.detail_label.setText("Produit introuvable.")
                self.image_label.clear()
                self.image_label.setText("Aucune\nimage")
                return
            
            # Affichage des détails textuels
            details = f"<b>Nom :</b> {product.name}<br>"
            details += f"<b>Catégorie :</b> {product.category_id}<br>"
            details += f"<b>Prix :</b> {product.price_unit} €<br>"
            details += f"<b>Coût :</b> {product.cost} €<br>"
            # Récupérer le stock depuis le module stock
            stock_info = self._get_product_stock_info(product.id)
            details += f"<b>Stock :</b> {stock_info['total_stock']}<br>"
            details += f"<b>Unité :</b> {product.unit}<br>"
            details += f"<b>Code-barres :</b> {product.barcode}<br>"
            details += f"<b>Compte comptable :</b> {product.account_id}<br>"
            details += f"<b>Statut :</b> {'Actif' if product.is_active else 'Inactif'}<br>"
            details += f"<b>Description :</b> {product.description or ''}<br>"
            
            # Ajouter les statistiques de vente
            sales_stats = self.produit_controller.get_product_sales_statistics(session, product_id)
            details += f"<br><b>📊 STATISTIQUES DE VENTE</b><br>"
            details += f"<b>Ventes :</b> {sales_stats['sales_count']} fois<br>"
            details += f"<b>Quantité vendue :</b> {sales_stats['total_quantity_sold']:.2f} {product.unit}<br>"
            if sales_stats['last_sale_date']:
                # Gérer le cas où last_sale_date peut être une string ou un datetime
                last_sale = sales_stats['last_sale_date']
                if isinstance(last_sale, str):
                    details += f"<b>Dernière vente :</b> {last_sale}<br>"
                else:
                    details += f"<b>Dernière vente :</b> {last_sale.strftime('%d/%m/%Y %H:%M')}<br>"
            else:
                details += f"<b>Dernière vente :</b> Jamais vendu<br>"
            details += f"<b>Chiffre d'affaires :</b> {sales_stats['total_revenue']:.2f} €<br>"
            details += f"<b>Bénéfice :</b> {sales_stats['total_profit']:.2f} €<br>"
            
            # Ajouter les détails de stock
            stock_details = self.produit_controller.get_product_stock_details(session, product_id)
            details += f"<br><b>📦 DÉTAILS DE STOCK</b><br>"
            details += f"<b>Stock actuel :</b> {stock_details['current_stock']:.2f} {product.unit}<br>"
            details += f"<b>Stock minimum :</b> {stock_details['min_stock_level']:.2f} {product.unit}<br>"
            details += f"<b>Entrepôt :</b> {stock_details['warehouse_name']}<br>"
            
            if stock_details['recent_movements']:
                details += f"<b>Derniers mouvements ({len(stock_details['recent_movements'])} - du plus récent au plus ancien):</b><br>"
                for i, movement in enumerate(stock_details['recent_movements'][:10]):  # Afficher les 10 plus récents (déjà triés)
                    date_str = movement['date'].strftime('%d/%m/%Y %H:%M') if movement['date'] else 'N/A'
                    details += f"  • {date_str}: {movement['quantity']} ({movement['movement_type']}) - {movement['source']}<br>"
            else:
                details += f"<b>Mouvements :</b> Aucun mouvement récent<br>"
            
            self.detail_label.setText(details)
            
            # Affichage de l'image
            self.load_product_image(product.image)

    def _get_product_stock_info(self, product_id):
        """Récupérer les informations de stock d'un produit depuis l'entrepôt POS Boutique"""
        try:
            from ayanna_erp.modules.stock.models import StockProduitEntrepot, StockWarehouse
            session = self.db_manager.get_session()
            
            # Récupérer l'entrepôt POS Boutique
            pos_warehouse = session.query(StockWarehouse).filter_by(code='POS_2').first()
            
            if not pos_warehouse:
                session.close()
                return {
                    'total_stock': 0,
                    'min_stock': 0,
                    'warehouse_name': 'Entrepôt introuvable'
                }
            
            # Récupérer le stock pour ce produit dans l'entrepôt POS Boutique
            stock_entry = session.query(StockProduitEntrepot).filter_by(
                product_id=product_id, 
                warehouse_id=pos_warehouse.id
            ).first()
            
            if stock_entry:
                total_stock = float(stock_entry.quantity)
                min_stock = float(stock_entry.min_stock_level)
            else:
                total_stock = 0
                min_stock = 0
            
            session.close()
            
            return {
                'total_stock': total_stock,
                'min_stock': min_stock,
                'warehouse_name': pos_warehouse.name
            }
        except Exception as e:
            print(f"Erreur lors de la récupération du stock: {e}")
            return {
                'total_stock': 0,
                'min_stock': 0,
                'warehouse_name': 'Erreur'
            }

    def load_product_image(self, image_path):
        """Charger et afficher l'image du produit"""
        self.image_label.clear()
        
        if not image_path:
            self.image_label.setText("Aucune\nimage")
            self.image_label.setStyleSheet("""
                QLabel {
                    border: 2px solid #BDC3C7;
                    border-radius: 8px;
                    background-color: #F8F9FA;
                    color: #7F8C8D;
                    font-size: 12px;
                }
            """)
            return
        
        try:
            # Construire le chemin complet de l'image
            if os.path.isabs(image_path):
                # Chemin absolu
                full_path = image_path
            else:
                # Chemin relatif depuis la racine du projet
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                full_path = os.path.join(project_root, image_path.replace("/", os.sep))
            
            if os.path.exists(full_path):
                # Charger l'image avec QPixmap
                pixmap = QPixmap(full_path)
                if not pixmap.isNull():
                    # Redimensionner l'image pour s'adapter au label tout en gardant les proportions
                    scaled_pixmap = pixmap.scaled(
                        self.image_label.size(), 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)
                    self.image_label.setStyleSheet("""
                        QLabel {
                            border: 2px solid #3498DB;
                            border-radius: 8px;
                            background-color: white;
                        }
                    """)
                else:
                    self.image_label.setText("Image\ncorrompue")
                    self.image_label.setStyleSheet("""
                        QLabel {
                            border: 2px solid #E74C3C;
                            border-radius: 8px;
                            background-color: #FADBD8;
                            color: #E74C3C;
                            font-size: 11px;
                        }
                    """)
            else:
                self.image_label.setText("Image\nintrouvable")
                self.image_label.setStyleSheet("""
                    QLabel {
                        border: 2px solid #F39C12;
                        border-radius: 8px;
                        background-color: #FEF5E7;
                        color: #F39C12;
                        font-size: 11px;
                    }
                """)
                
        except Exception as e:
            print(f"❌ Erreur lors du chargement de l'image: {e}")
            self.image_label.setText("Erreur\nimage")
            self.image_label.setStyleSheet("""
                QLabel {
                    border: 2px solid #E74C3C;
                    border-radius: 8px;
                    background-color: #FADBD8;
                    color: #E74C3C;
                    font-size: 11px;
                }
            """)

    def on_product_double_clicked(self, row, column):
        """Gestionnaire du double-clic pour ouvrir la fenêtre d'édition"""
        product_id_item = self.products_table.item(row, 0)
        if not product_id_item:
            return
        product_id = int(product_id_item.text())
        with self.db_manager.get_session() as session:
            product = self.produit_controller.get_product_by_id(session, product_id)
            if product:
                self.edit_product(product)
    
    def load_initial_data(self):
        """Charger les données initiales"""
        self.load_categories()
        self.refresh_products()
    
    def load_categories(self):
        """Charger les catégories dans le combo box"""
        try:
            with self.db_manager.get_session() as session:
                categories = self.produit_controller.get_categories(session)
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
                products = self.produit_controller.get_products(
                    session,
                    category_id=category_id,
                    search_term=search_term,
                    active_only=active_only if active_only is not None else True
                )
                self.populate_products_table(products)
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des produits: {str(e)}")
    
    def populate_products_table(self, products: List):
        self.products_table.setRowCount(len(products))
        for row, product in enumerate(products):
            # ID
            id_item = QTableWidgetItem(str(product.id))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.products_table.setItem(row, 0, id_item)

            # Nom
            self.products_table.setItem(row, 1, QTableWidgetItem(product.name))

            # Catégorie
            category_name = "Non assignée"
            if product.category_id:
                with self.db_manager.get_session() as session:
                    cat = session.query(CoreProductCategory).get(product.category_id)
                    if cat:
                        category_name = cat.name
            self.products_table.setItem(row, 2, QTableWidgetItem(category_name))

            # Prix
            price_item = QTableWidgetItem(f"{product.price_unit:.2f} €")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.products_table.setItem(row, 3, price_item)

            # Stock
            try:
                with self.db_manager.get_session() as session:
                    stock_total = self.produit_controller.get_product_stock_total(session, product.id)
                stock_item = QTableWidgetItem(str(stock_total))
                stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if stock_total == 0:
                    stock_item.setBackground(QColor("#E74C3C"))
                    stock_item.setForeground(QColor("white"))
                elif stock_total < 10:
                    stock_item.setBackground(QColor("#F39C12"))
                    stock_item.setForeground(QColor("white"))
                else:
                    stock_item.setBackground(QColor("#27AE60"))
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
                status_item.setBackground(QColor("#27AE60"))
                status_item.setForeground(QColor("white"))
            else:
                status_item.setBackground(QColor("#E74C3C"))
                status_item.setForeground(QColor("white"))
            self.products_table.setItem(row, 6, status_item)

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)

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

            toggle_btn = QPushButton("🔴" if product.is_active else "🟢")
            toggle_btn.setToolTip("Désactiver" if product.is_active else "Activer")
            toggle_btn.clicked.connect(lambda checked, p=product: self.toggle_product_status(p))
            actions_layout.addWidget(toggle_btn)

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
        dialog = ProductFormDialog(self, self.produit_controller)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            product_data = dialog.get_product_data()
            try:
                with self.db_manager.get_session() as session:
                    new_product = self.produit_controller.create_product(
                        session,
                        nom=product_data["nom"],
                        prix=product_data["prix"],
                        category_id=product_data["category_id"],
                        description=product_data.get("description"),
                        unit=product_data.get("unit", "unité"),
                        stock_initial=product_data.get("stock_initial", 0),
                        cost=product_data.get("cost", 0.0),
                        barcode=product_data.get("barcode"),
                        image=product_data.get("image"),
                        stock_min=product_data.get("stock_min", 0),
                        account_id=product_data.get("account_id"),
                        is_active=product_data.get("is_active", True)
                    )
                    QMessageBox.information(self, "Succès", f"Produit '{new_product.name}' créé avec succès!")
                    self.refresh_products()
                    self.product_updated.emit(new_product.id)
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la création du produit: {str(e)}")
    
    def edit_product(self, product):
        dialog = ProductFormDialog(self, self.produit_controller, product)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            product_data = dialog.get_product_data()
            try:
                with self.db_manager.get_session() as session:
                    updated_product = self.produit_controller.update_product(
                        session,
                        product.id,
                        name=product_data["nom"],
                        description=product_data.get("description"),
                        price_unit=product_data["prix"],
                        category_id=product_data["category_id"],
                        unit=product_data.get("unit", "unité"),
                        cost=product_data.get("cost", 0.0),
                        barcode=product_data.get("barcode"),
                        image=product_data.get("image"),
                        stock_min=product_data.get("stock_min", 0),
                        account_id=product_data.get("account_id"),
                        is_active=product_data.get("is_active", True)
                    )
                    if updated_product:
                        QMessageBox.information(self, "Succès", f"Produit '{updated_product.name}' mis à jour avec succès!")
                        self.refresh_products()
                        self.product_updated.emit(updated_product.id)
                    else:
                        QMessageBox.warning(self, "Erreur", "Produit introuvable.")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la mise à jour du produit: {str(e)}")
    
    def toggle_product_status(self, product):
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
                    updated_product = self.produit_controller.update_product(
                        session, product.id, is_active=new_status
                    )
                    QMessageBox.information(self, "Succès", f"Produit {action}é avec succès!")
                    self.refresh_products()
                    self.product_updated.emit(product.id)
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la modification du statut: {str(e)}")
    
    def manage_product_stock(self, product: CoreProduct):
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
    
    def __init__(self, parent=None, produit_controller=None, product=None):
        super().__init__(parent)
        self.produit_controller = produit_controller
        self.product = product
        self.db_manager = DatabaseManager()

        self.is_editing = product is not None
        title = "Modifier le Produit" if self.is_editing else "Nouveau Produit"
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(600, 650)  # Taille plus grande pour les onglets
        self.resize(650, 700)  # Taille par défaut
        self.setup_ui()
        if self.is_editing:
            self.load_product_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # En-tête avec titre et description
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("Modifier le Produit" if self.is_editing else "Nouveau Produit")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #2C3E50;
                margin-bottom: 5px;
            }
        """)
        
        subtitle_label = QLabel("Saisissez les informations du produit ci-dessous")
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #7F8C8D;
                margin-bottom: 15px;
            }
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        layout.addWidget(header_widget)

        # Conteneur principal avec onglets
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #BDC3C7;
                background-color: white;
                border-radius: 8px;
                padding: 10px;
            }
            QTabBar::tab {
                background-color: #ECF0F1;
                padding: 10px 20px;
                margin-right: 2px;
                font-weight: bold;
                color: #2C3E50;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background-color: #3498DB;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #D5DBDB;
            }
        """)

        # Onglet Informations générales
        general_tab = QWidget()
        general_layout = QFormLayout(general_tab)
        general_layout.setSpacing(15)
        general_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Style pour les labels
        label_style = "QLabel { font-weight: bold; color: #2C3E50; }"
        
        # Style pour les champs de saisie
        input_style = """
            QLineEdit, QTextEdit, QDoubleSpinBox, QSpinBox, QComboBox {
                border: 2px solid #BDC3C7;
                border-radius: 5px;
                padding: 8px;
                font-size: 12px;
                background-color: white;
            }
            QLineEdit:focus, QTextEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus {
                border-color: #3498DB;
            }
        """

        # Nom du produit
        nom_label = QLabel("Nom du produit *:")
        nom_label.setStyleSheet(label_style)
        self.nom_input = QLineEdit()
        self.nom_input.setPlaceholderText("Saisissez le nom du produit")
        self.nom_input.setStyleSheet(input_style)
        general_layout.addRow(nom_label, self.nom_input)

        # Description
        desc_label = QLabel("Description:")
        desc_label.setStyleSheet(label_style)
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setPlaceholderText("Description détaillée du produit")
        self.description_input.setStyleSheet(input_style)
        general_layout.addRow(desc_label, self.description_input)

        # Catégorie
        cat_label = QLabel("Catégorie *:")
        cat_label.setStyleSheet(label_style)
        self.category_combo = QComboBox()
        self.category_combo.setStyleSheet(input_style)
        self.load_categories()
        general_layout.addRow(cat_label, self.category_combo)

        # Code-barres avec bouton scanner
        barcode_label = QLabel("Code-barres:")
        barcode_label.setStyleSheet(label_style)
        barcode_widget = QWidget()
        barcode_layout = QHBoxLayout(barcode_widget)
        barcode_layout.setContentsMargins(0, 0, 0, 0)
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Code-barres du produit")
        self.barcode_input.setStyleSheet(input_style)
        scanner_btn = QPushButton("📷 Scanner")
        scanner_btn.setStyleSheet("""
            QPushButton {
                background-color: #9B59B6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8E44AD;
            }
        """)
        barcode_layout.addWidget(self.barcode_input, stretch=3)
        barcode_layout.addWidget(scanner_btn, stretch=1)
        general_layout.addRow(barcode_label, barcode_widget)

        self.tab_widget.addTab(general_tab, "📝 Informations")

        # Onglet Prix et Stock
        price_tab = QWidget()
        price_layout = QFormLayout(price_tab)
        price_layout.setSpacing(15)
        price_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Prix de vente
        prix_label = QLabel("Prix de vente *:")
        prix_label.setStyleSheet(label_style)
        self.prix_input = QDoubleSpinBox()
        self.prix_input.setRange(0.01, 999999.99)
        self.prix_input.setDecimals(2)
        self.prix_input.setSuffix(" €")
        self.prix_input.setValue(1.00)
        self.prix_input.setStyleSheet(input_style)
        price_layout.addRow(prix_label, self.prix_input)

        # Coût d'achat
        cost_label = QLabel("Coût d'achat:")
        cost_label.setStyleSheet(label_style)
        self.cost_input = QDoubleSpinBox()
        self.cost_input.setRange(0.00, 999999.99)
        self.cost_input.setDecimals(2)
        self.cost_input.setSuffix(" €")
        self.cost_input.setValue(0.00)
        self.cost_input.setStyleSheet(input_style)
        price_layout.addRow(cost_label, self.cost_input)

        # Unité
        unit_label = QLabel("Unité:")
        unit_label.setStyleSheet(label_style)
        self.unite_input = QLineEdit()
        self.unite_input.setPlaceholderText("Ex: pièce, kg, litre...")
        self.unite_input.setText("pièce")
        self.unite_input.setStyleSheet(input_style)
        price_layout.addRow(unit_label, self.unite_input)

        # Stock initial (seulement en mode création)
        if not self.is_editing:
            stock_label = QLabel("Stock initial:")
            stock_label.setStyleSheet(label_style)
            self.stock_initial_input = QSpinBox()
            self.stock_initial_input.setRange(0, 999999)
            self.stock_initial_input.setValue(0)
            self.stock_initial_input.setStyleSheet(input_style)
            price_layout.addRow(stock_label, self.stock_initial_input)

        # Stock minimum
        stock_min_label = QLabel("Stock minimum:")
        stock_min_label.setStyleSheet(label_style)
        self.stock_min_input = QSpinBox()
        self.stock_min_input.setRange(0, 999999)
        self.stock_min_input.setValue(0)
        self.stock_min_input.setStyleSheet(input_style)
        price_layout.addRow(stock_min_label, self.stock_min_input)

        self.tab_widget.addTab(price_tab, "💰 Prix & Stock")

        # Onglet Autres informations
        other_tab = QWidget()
        other_layout = QFormLayout(other_tab)
        other_layout.setSpacing(15)
        other_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Image avec prévisualisation
        image_label = QLabel("Image:")
        image_label.setStyleSheet(label_style)
        image_widget = QWidget()
        image_layout = QVBoxLayout(image_widget)
        image_layout.setContentsMargins(0, 0, 0, 0)
        
        image_input_layout = QHBoxLayout()
        self.image_input = QLineEdit()
        self.image_input.setPlaceholderText("Chemin de l'image ou URL")
        self.image_input.setStyleSheet(input_style)
        self.image_btn = QPushButton("📁 Parcourir")
        self.image_btn.setStyleSheet("""
            QPushButton {
                background-color: #E67E22;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D35400;
            }
        """)
        def choose_image():
            file, _ = QFileDialog.getOpenFileName(self, "Choisir une image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
            if file:
                self.image_input.setText(file)
        self.image_btn.clicked.connect(choose_image)
        
        image_input_layout.addWidget(self.image_input, stretch=3)
        image_input_layout.addWidget(self.image_btn, stretch=1)
        image_layout.addLayout(image_input_layout)
        other_layout.addRow(image_label, image_widget)

        # Compte comptable
        account_label = QLabel("Compte comptable:")
        account_label.setStyleSheet(label_style)
        self.account_combo = QComboBox()
        self.account_combo.setStyleSheet(input_style)
        self.load_accounting_accounts()
        other_layout.addRow(account_label, self.account_combo)

        # Statut actif/inactif
        status_label = QLabel("Statut:")
        status_label.setStyleSheet(label_style)
        self.active_checkbox = QCheckBox("Produit actif")
        self.active_checkbox.setChecked(True)
        self.active_checkbox.setStyleSheet("""
            QCheckBox {
                font-weight: bold;
                color: #27AE60;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #BDC3C7;
                background-color: white;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #27AE60;
                background-color: #27AE60;
                border-radius: 3px;
            }
        """)
        other_layout.addRow(status_label, self.active_checkbox)

        self.tab_widget.addTab(other_tab, "⚙️ Autres")

        layout.addWidget(self.tab_widget)

        # Boutons d'action
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 10, 0, 0)
        
        cancel_btn = QPushButton("❌ Annuler")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 25px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("✅ Enregistrer")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 25px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        save_btn.clicked.connect(self.validate_and_accept)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(save_btn)
        
        layout.addWidget(buttons_widget)
    
    def get_enterprise_id(self):
        """Récupérer l'ID de l'entreprise depuis le contrôleur produit"""
        try:
            if self.produit_controller and hasattr(self.produit_controller, 'pos_id'):
                # Récupérer l'entreprise depuis le pos_id
                from ayanna_erp.database.database_manager import POSPoint
                from ayanna_erp.modules.core.models import CoreProduct, CoreProductCategory
                
                with self.db_manager.get_session() as session:
                    # Récupérer le POS et son entreprise
                    pos = session.query(POSPoint).filter_by(id=self.produit_controller.pos_id).first()
                    
                    if pos:
                        return pos.enterprise_id
                    else:
                        print(f"⚠️  POS avec ID {self.produit_controller.pos_id} non trouvé")
                        return None
            else:
                print("⚠️  Contrôleur ou pos_id non disponible")
                return None
        except Exception as e:
            print(f"❌ Erreur lors de la récupération de l'entreprise: {e}")
            return None

    def load_accounting_accounts(self):
        """Charger les comptes comptables de classe 7 (ventes) dans le combo box"""
        try:
            enterprise_id = self.get_enterprise_id()
            if not enterprise_id:
                self.account_combo.addItem("Aucune entreprise trouvée", None)
                return

            # Utiliser le contrôleur comptabilité pour récupérer les comptes de vente
            comptabilite_controller = ComptabiliteController()
            with self.db_manager.get_session() as session:
                comptabilite_controller.session = session
                comptes_vente = comptabilite_controller.get_comptes_vente(enterprise_id)
                
                self.account_combo.clear()
                self.account_combo.addItem("Sélectionnez un compte", None)
                
                if not comptes_vente:
                    self.account_combo.addItem("Aucun compte de vente disponible", None)
                else:
                    for compte in comptes_vente:
                        # Format: "701 - Ventes marchandises"
                        display_text = f"{compte.numero} - {compte.nom}"
                        self.account_combo.addItem(display_text, compte.id)
                        
        except Exception as e:
            print(f"❌ Erreur lors du chargement des comptes comptables: {e}")
            self.account_combo.clear()
            self.account_combo.addItem("Erreur de chargement", None)

    def copy_image_to_project(self, image_path: str) -> str:
        """Copier l'image sélectionnée dans le dossier du projet et retourner le chemin relatif"""
        if not image_path or not os.path.exists(image_path):
            return None
        
        try:
            # Créer le dossier des images s'il n'existe pas
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            images_dir = os.path.join(project_root, "data", "images", "produits")
            os.makedirs(images_dir, exist_ok=True)
            
            # Générer un nom unique pour l'image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = os.path.splitext(image_path)[1]
            unique_filename = f"produit_{timestamp}{file_extension}"
            
            # Copier l'image
            destination_path = os.path.join(images_dir, unique_filename)
            shutil.copy2(image_path, destination_path)
            
            # Retourner le chemin relatif
            relative_path = os.path.join("data", "images", "produits", unique_filename)
            return relative_path.replace("\\", "/")  # Utiliser des slashes Unix pour la compatibilité
            
        except Exception as e:
            print(f"❌ Erreur lors de la copie de l'image: {e}")
            return None
    
    def load_categories(self):
        try:
            with self.db_manager.get_session() as session:
                categories = self.produit_controller.get_categories(session)
                self.category_combo.clear()
                if not categories:
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
            # Onglet informations générales
            self.nom_input.setText(self.product.name)
            
            if self.product.description:
                self.description_input.setPlainText(self.product.description)
            
            if getattr(self.product, "barcode", None):
                self.barcode_input.setText(self.product.barcode)
            
            # Sélectionner la catégorie
            if self.product.category_id:
                for i in range(self.category_combo.count()):
                    if self.category_combo.itemData(i) == self.product.category_id:
                        self.category_combo.setCurrentIndex(i)
                        break
            
            # Onglet prix et stock
            self.prix_input.setValue(float(self.product.price_unit))
            
            if getattr(self.product, "cost", None):
                self.cost_input.setValue(float(self.product.cost))
            
            if getattr(self.product, "unit", None):
                self.unite_input.setText(self.product.unit)
            
            if getattr(self.product, "stock_min", None):
                self.stock_min_input.setValue(int(self.product.stock_min))
            
            # Onglet autres informations
            if getattr(self.product, "image", None):
                self.image_input.setText(self.product.image)
            
            # Sélectionner le compte comptable
            if getattr(self.product, "account_id", None):
                for i in range(self.account_combo.count()):
                    if self.account_combo.itemData(i) == self.product.account_id:
                        self.account_combo.setCurrentIndex(i)
                        break
            
            self.active_checkbox.setChecked(getattr(self.product, "is_active", True))
    
    def validate_and_accept(self):
        """Valider et accepter le formulaire"""
        if self.validate_form():
            self.accept()

    def validate_form(self):
        """Valider le formulaire avant acceptation"""
        # Validation du nom
        if not self.nom_input.text().strip():
            QMessageBox.warning(self, "❌ Erreur de validation", 
                              "Le nom du produit est obligatoire.\nVeuillez saisir un nom.")
            self.tab_widget.setCurrentIndex(0)  # Aller au premier onglet
            self.nom_input.setFocus()
            return False
        
        # Validation du prix
        if self.prix_input.value() <= 0:
            QMessageBox.warning(self, "❌ Erreur de validation", 
                              "Le prix doit être supérieur à zéro.\nVeuillez saisir un prix valide.")
            self.tab_widget.setCurrentIndex(1)  # Aller à l'onglet prix
            self.prix_input.setFocus()
            return False
        
        # Validation de la catégorie
        if self.category_combo.currentData() is None:
            QMessageBox.warning(self, "❌ Erreur de validation", 
                              "Veuillez sélectionner une catégorie valide.\nLa catégorie est obligatoire.")
            self.tab_widget.setCurrentIndex(0)  # Aller au premier onglet
            self.category_combo.setFocus()
            return False
        
        return True
    
    def get_product_data(self):
        """Récupérer les données du produit"""
        # Traiter l'image si une nouvelle a été sélectionnée
        image_path = self.image_input.text().strip()
        final_image_path = None
        
        if image_path:
            # Si c'est un chemin absolu (nouvelle image), la copier dans le projet
            if os.path.isabs(image_path) and os.path.exists(image_path):
                final_image_path = self.copy_image_to_project(image_path)
            else:
                # Si c'est déjà un chemin relatif (image existante), le garder tel quel
                final_image_path = image_path
        
        data = {
            "nom": self.nom_input.text().strip(),
            "description": self.description_input.toPlainText().strip() or None,
            "prix": Decimal(str(self.prix_input.value())),
            "cost": Decimal(str(self.cost_input.value())),
            "barcode": self.barcode_input.text().strip() or None,
            "image": final_image_path,
            "category_id": self.category_combo.currentData(),
            "unit": self.unite_input.text().strip() or "unité",
            "stock_min": self.stock_min_input.value(),
            "account_id": self.account_combo.currentData(),
            "is_active": self.active_checkbox.isChecked()
        }
        # Stock initial seulement en mode création
        if not self.is_editing and hasattr(self, 'stock_initial_input'):
            data["stock_initial"] = self.stock_initial_input.value()
        return data