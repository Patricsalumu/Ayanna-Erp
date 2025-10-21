"""
Interface moderne de type supermarché pour le module Boutique
Design épuré avec catalogue de produits et panier de vente
"""

import os
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
from ..model.models import ShopClient, ShopPanier, ShopService
from ayanna_erp.modules.salle_fete.model.salle_fete import EventService
from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
from .client_index import ClientFormDialog


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
        self.enterprise_controller = EntrepriseController()
        
        # Variables d'état
        self.current_cart = []  # Liste des articles du panier
        self.selected_client = None
        self.global_discount = Decimal('0.00')
        self.categories = []
        self.products = []
        # catalogue mode: 'products' or 'services'
        self.catalog_mode = 'products'

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
        title_label = QLabel("🛒 Ayanna Point de vente")
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

        # Toggle produits / services
        self.products_radio = QPushButton("Produits")
        self.products_radio.setCheckable(True)
        self.products_radio.setChecked(True)
        self.products_radio.clicked.connect(self.on_catalog_mode_changed)
        filters_layout.addWidget(self.products_radio)

        self.services_radio = QPushButton("Services")
        self.services_radio.setCheckable(True)
        self.services_radio.setChecked(False)
        self.services_radio.clicked.connect(self.on_catalog_mode_changed)
        filters_layout.addWidget(self.services_radio)

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

    def on_catalog_mode_changed(self):
        """Basculer entre affichage produits et services."""
        # Gérer l'état des boutons comme un toggle simple
        sender = self.sender()
        if sender == self.products_radio:
            self.catalog_mode = 'products'
            self.products_radio.setChecked(True)
            self.services_radio.setChecked(False)
        else:
            self.catalog_mode = 'services'
            self.products_radio.setChecked(False)
            self.services_radio.setChecked(True)

        # Recharger le catalogue
        self.load_products()

    def load_services(self):
        """Charge et affiche les services (shop_services + event_services)."""
        try:
            with self.db_manager.get_session() as session:
                # Services depuis shop_services via ShopService
                shop_query = session.query(ShopService).filter(ShopService.is_active == True)
                search_text = self.search_edit.text().strip()
                if search_text:
                    shop_query = shop_query.filter(ShopService.name.ilike(f'%{search_text}%'))
                shop_services = shop_query.order_by(ShopService.name).all()

                # Services depuis event_services
                try:
                    event_query = session.query(EventService).filter(EventService.is_active == True)
                    if search_text:
                        event_query = event_query.filter(EventService.name.ilike(f'%{search_text}%'))
                    event_services = event_query.order_by(EventService.name).all()
                except Exception:
                    event_services = []

                # Combiner (marquer la source)
                combined = []
                for s in shop_services:
                    combined.append(('shop', s))
                for s in event_services:
                    combined.append(('event', s))

                self.display_services(combined)

        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des services: {e}")

    def display_services(self, services):
        """Affiche les services dans la grille (cards)."""
        # Vider la grille existante
        for i in reversed(range(self.products_grid_layout.count())):
            child = self.products_grid_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        # Si on est en mode 'services', afficher en LISTE (une ligne par service)
        if getattr(self, 'catalog_mode', 'products') == 'services':
            for i, (source, service) in enumerate(services):
                row = i
                list_item = self.create_service_list_item(service, source)
                # ajouter sur une seule colonne
                self.products_grid_layout.addWidget(list_item, row, 0)

            # pousser le reste vers le bas
            self.products_grid_layout.setRowStretch(len(services) + 1, 1)
            return

        # Mode par défaut : grille de cards
        cols = 3
        for i, (source, service) in enumerate(services):
            row = i // cols
            col = i % cols
            service_card = self.create_service_card(service, source)
            self.products_grid_layout.addWidget(service_card, row, col)

        self.products_grid_layout.setRowStretch(len(services) // cols + 1, 1)

    def create_service_card(self, service, source='shop'):
        """Crée une carte visuelle pour un service (source='shop'|'event')."""
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
                border-color: #1976D2;
                background-color: #F3F9FF;
            }
        """)
        card.setFixedSize(200, 220)

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(6)

        # Icone/service image
        img = QLabel()
        img.setFixedSize(140, 80)
        img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img.setText("🎯")
        card_layout.addWidget(img, 0, Qt.AlignmentFlag.AlignCenter)

        # Nom
        name = getattr(service, 'name', 'Service')
        name_label = QLabel(name[:25] + '...' if len(name) > 25 else name)
        name_label.setStyleSheet("font-weight: bold; color: #333;")
        name_label.setWordWrap(True)
        card_layout.addWidget(name_label)

        # Prix
        price_val = getattr(service, 'price', None) or getattr(service, 'prix', 0.0)
        price_label = QLabel(f"{float(price_val):.0f} FC")
        price_label.setStyleSheet("font-size:14px; font-weight:bold; color:#4CAF50;")
        card_layout.addWidget(price_label)

        # Source badge
        source_label = QLabel("(événement)" if source == 'event' else "(boutique)")
        source_label.setStyleSheet("color:#777; font-size:11px;")
        card_layout.addWidget(source_label)
        # Bouton ajouter
        add_btn = QPushButton("➕ Ajouter")
        add_btn.setStyleSheet("background-color:#2196F3; color:white; border:none; border-radius:4px; padding:6px; font-weight:bold;")
        # Capturer l'id et la source; récupérer l'objet en session au moment de l'ajout
        # Passer explicitement l'id du service (plus robuste que l'objet lui-même)
        add_btn.clicked.connect(lambda svc_id=getattr(service, 'id', None), svc_name=getattr(service, 'name', None) or getattr(service, 'nom', None), src=source: self.add_service_to_cart_by_id(svc_id, src, svc_name))
        card_layout.addWidget(add_btn)

        return card

    def create_service_list_item(self, service, source='shop'):
        """Crée un widget ligne pour afficher un service en mode liste."""
        row = QFrame()
        row.setFrameStyle(QFrame.Shape.StyledPanel)
        row.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E8E8E8;
                border-radius: 6px;
                padding: 8px;
            }
            QFrame:hover {
                background-color: #F3F9FF;
            }
        """)

        layout = QHBoxLayout(row)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(12)

        # Nom et description (colonne principale)
        name = getattr(service, 'name', getattr(service, 'nom', 'Service'))
        name_label = QLabel(name)
        name_label.setStyleSheet("font-weight: bold; color: #333;")
        name_label.setWordWrap(True)
        layout.addWidget(name_label, 3)

        # Prix
        price_val = getattr(service, 'price', None) or getattr(service, 'prix', 0.0)
        price_label = QLabel(f"{float(price_val):.0f} FC")
        price_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        layout.addWidget(price_label, 1, Qt.AlignmentFlag.AlignRight)

        # Source
        source_label = QLabel("(événement)" if source == 'event' else "(boutique)")
        source_label.setStyleSheet("color:#777; font-size:11px;")
        layout.addWidget(source_label, 1, Qt.AlignmentFlag.AlignRight)

        # Bouton ajouter
        add_btn = QPushButton("➕")
        add_btn.setToolTip("Ajouter au panier")
        add_btn.setFixedSize(34, 28)
        add_btn.setStyleSheet("background-color:#2196F3; color:white; border:none; border-radius:4px;")
        # Transmettre l'id pour garantir la recherche en session
        add_btn.clicked.connect(lambda svc_id=getattr(service, 'id', None), svc_name=getattr(service, 'name', None) or getattr(service, 'nom', None), src=source: self.add_service_to_cart_by_id(svc_id, src, svc_name))
        layout.addWidget(add_btn, 0, Qt.AlignmentFlag.AlignRight)

        return row

    def add_service_to_cart_by_id(self, service_or_id, source='shop', service_name=None):
        """Récupère le service en session (shop ou event), résout/crée si nécessaire et ajoute au panier.

        Accepts either an integer id, a string id, or an object with attributes (id/name/nom/price).
        When source == 'event' we search in EventService and map/create a ShopService.
        When source == 'shop' we search directly in ShopService.
        """
        try:
            # Debug: enregistrer la valeur reçue dans un fichier pour diagnostics
            # debug logs removed
            with self.db_manager.get_session() as session:
                svc = None

                # Normaliser l'entrée: extraire id et nom si disponibles
                incoming_id = None
                incoming_name = service_name
                try:
                    # traiter bool séparément (False n'est pas un id valide)
                    if isinstance(service_or_id, bool):
                        incoming_id = None
                    elif isinstance(service_or_id, int):
                        incoming_id = int(service_or_id)
                    elif isinstance(service_or_id, str) and service_or_id.isdigit():
                        incoming_id = int(service_or_id)
                    else:
                        incoming_id = getattr(service_or_id, 'id', None) or getattr(service_or_id, 'pk', None)
                        if incoming_name is None:
                            incoming_name = getattr(service_or_id, 'name', None) or getattr(service_or_id, 'nom', None)
                except Exception:
                    incoming_id = None

                # Si c'est un service venant d'un événement, chercher dans EventService
                if source == 'event':
                    ev = None
                    if incoming_id is not None:
                        ev = session.query(EventService).filter_by(id=incoming_id).first()

                    if ev is None and incoming_name:
                        try:
                            ev = session.query(EventService).filter(EventService.name.ilike(f'%{incoming_name}%')).first()
                        except Exception:
                            ev = None

                    if ev:
                        svc = self._resolve_event_service_to_shop_service(session, ev)

                # Sinon, chercher directement dans les services de la boutique
                else:
                    if incoming_id is not None:
                        svc = session.query(ShopService).filter_by(id=incoming_id).first()

                    if svc is None and incoming_name:
                        try:
                            svc = session.query(ShopService).filter(ShopService.name.ilike(f'%{incoming_name}%')).first()
                        except Exception:
                            svc = None

                if svc is None:
                    # Debug temporaire: afficher l'id et la source reçus
                    # debug logs removed
                    QMessageBox.warning(self, "Service introuvable", "Le service sélectionné est introuvable en base.")
                    return

                # svc est un ShopService ORM (id/name/price disponibles)
                # Appeler add_to_cart avec l'objet ShopService
                self.add_to_cart(svc, item_type='service', source='shop')

        except Exception as e:
            print(f"Erreur add_service_to_cart_by_id: {e}")
    
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
        
        # Sélection client avec recherche avancée
        client_frame = QFrame()
        client_layout = QHBoxLayout(client_frame)
        client_layout.setContentsMargins(5, 5, 5, 5)
        client_layout.addWidget(QLabel("👤 Client:"))

        # LineEdit pour la recherche
        self.client_search = QLineEdit()
        self.client_search.setMinimumWidth(150)
        self.client_search.setPlaceholderText("Tapez numéro téléphone ou nom...")
        self.client_search.textChanged.connect(self.on_client_search_changed)
        client_layout.addWidget(self.client_search)

        # ComboBox pour afficher les résultats (non éditable)
        self.client_combo = QComboBox()
        self.client_combo.setMinimumWidth(150)
        self.client_combo.currentIndexChanged.connect(self.on_client_selected)
        client_layout.addWidget(self.client_combo)

        # Bouton pour ajouter un nouveau client
        self.add_client_btn = QPushButton("➕")
        self.add_client_btn.setToolTip("Ajouter un nouveau client")
        self.add_client_btn.setFixedSize(30, 25)
        self.add_client_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.add_client_btn.clicked.connect(self.create_new_client)
        client_layout.addWidget(self.add_client_btn)

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
        # Application automatique de la remise lors du changement de valeur
        self.discount_spin.valueChanged.connect(self.apply_discount_auto)
        
        # Suppression du bouton "Appliquer" - remise automatique
        discount_layout.addWidget(self.discount_spin)
        
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
        """Charge la liste des clients dans le combo"""
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
    
    def on_client_search_changed(self, text):
        """Gestionnaire de changement de texte dans la recherche client"""
        text = text.strip()

        try:
            with self.db_manager.get_session() as session:
                # Vider le combo
                self.client_combo.clear()

                if not text:
                    # Si le texte est vide, commencer par l'option anonyme puis tous les clients
                    self.client_combo.addItem("Client anonyme", None)
                    clients = session.query(ShopClient).filter_by(
                        pos_id=self.pos_id,
                        is_active=True
                    ).all()

                    for client in clients:
                        display_name = f"{client.nom} {client.prenom or ''}".strip()
                        self.client_combo.addItem(display_name, client.id)
                    return

                # Recherche par téléphone (priorité)
                client_by_phone = session.query(ShopClient).filter(
                    ShopClient.pos_id == self.pos_id,
                    ShopClient.is_active == True,
                    ShopClient.telephone.like(f"%{text}%")
                ).first()

                if client_by_phone:
                    # Si trouvé par téléphone, afficher ce client en premier (sans client anonyme)
                    display_name = f"{client_by_phone.nom} {client_by_phone.prenom or ''}".strip()
                    full_display = f"{display_name} ({client_by_phone.telephone})"
                    self.client_combo.addItem(full_display, client_by_phone.id)
                    self.selected_client = client_by_phone
                    return

                # Recherche par nom/prénom
                clients_by_name = session.query(ShopClient).filter(
                    ShopClient.pos_id == self.pos_id,
                    ShopClient.is_active == True,
                    (ShopClient.nom.like(f"%{text}%") | ShopClient.prenom.like(f"%{text}%"))
                ).limit(10).all()

                if clients_by_name:
                    # Afficher les clients trouvés en premier (sans client anonyme)
                    for client in clients_by_name:
                        display_name = f"{client.nom} {client.prenom or ''}".strip()
                        if client.telephone:
                            display_name += f" ({client.telephone})"
                        self.client_combo.addItem(display_name, client.id)

                    self.selected_client = clients_by_name[0]
                else:
                    # Aucun client trouvé - commencer par anonyme puis proposer de créer
                    self.client_combo.addItem("Client anonyme", None)
                    self.client_combo.addItem(f"➕ Créer client '{text}'", -1)  # -1 pour indiquer création
                    self.selected_client = None

        except Exception as e:
            print(f"Erreur lors de la recherche client: {e}")
            import traceback
            traceback.print_exc()
            # En cas d'erreur, s'assurer qu'on a au moins l'option anonyme
            try:
                if self.client_combo.count() == 0:
                    self.client_combo.addItem("Client anonyme", None)
            except:
                pass
    
    def on_client_selected(self, index):
        """Gestionnaire de sélection de client"""
        if index >= 0:
            client_id = self.client_combo.itemData(index)
            if client_id == -1:
                # L'utilisateur a sélectionné "Créer client"
                current_text = self.client_combo.currentText().replace("➕ Créer client '", "").replace("'", "")
                self.create_new_client_with_text(current_text)
                return
            elif client_id is not None:
                try:
                    with self.db_manager.get_session() as session:
                        self.selected_client = session.query(ShopClient).filter_by(id=client_id).first()
                except Exception as e:
                    print(f"Erreur lors de la sélection du client: {e}")
                    self.selected_client = None
            else:
                self.selected_client = None
    
    def create_new_client_with_text(self, text):
        """Créer un nouveau client depuis la recherche avec pré-remplissage"""
        try:
            dialog = ClientFormDialog(self)

            # Pré-remplir selon le type de texte saisi
            if text and (text.isdigit() or text.startswith('+')):
                # Si c'est un numéro de téléphone
                dialog.telephone_input.setText(text)
            else:
                # Essayer de séparer nom et prénom
                parts = text.split()
                if len(parts) >= 2:
                    dialog.nom_input.setText(parts[0])
                    dialog.prenom_input.setText(' '.join(parts[1:]))
                elif len(parts) == 1:
                    dialog.nom_input.setText(parts[0])

            if dialog.exec() == QDialog.DialogCode.Accepted:
                client_data = dialog.get_client_data()

                try:
                    with self.db_manager.get_session() as session:
                        new_client = self.boutique_controller.create_client(
                            session,
                            nom=client_data["nom"],
                            prenom=client_data.get("prenom"),
                            email=client_data.get("email"),
                            telephone=client_data.get("telephone"),
                            adresse=client_data.get("adresse")
                        )

                        # Recharger les clients de manière sécurisée
                        self._safe_reload_clients()

                        # Vider le champ de recherche après création
                        self.client_search.clear()

                        QMessageBox.information(self, "Succès", f"Client '{new_client.nom}' créé avec succès!")

                except Exception as e:
                    QMessageBox.critical(self, "Erreur", f"Erreur lors de la création du client: {str(e)}")
                    import traceback
                    traceback.print_exc()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ouverture du dialogue: {str(e)}")
            import traceback
            traceback.print_exc()

    def _safe_reload_clients(self):
        """Recharge les clients de manière sécurisée sans déclencher de signaux récursifs"""
        try:
            # Déconnecter temporairement les signaux
            self.client_combo.currentIndexChanged.disconnect(self.on_client_selected)
        except:
            pass

        try:
            # Recharger les clients
            self.load_clients()
        finally:
            # Reconnecter les signaux
            try:
                self.client_combo.currentIndexChanged.connect(self.on_client_selected)
            except:
                pass
    
    def create_new_client(self):
        """Créer un nouveau client depuis le bouton ➕"""
        # Récupérer le texte actuel du champ de recherche
        current_text = self.client_search.text().strip()

        dialog = ClientFormDialog(self)

        # Pré-remplir le téléphone si ça ressemble à un numéro
        if current_text and (current_text.isdigit() or current_text.startswith('+')):
            dialog.telephone_input.setText(current_text)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            client_data = dialog.get_client_data()

            try:
                with self.db_manager.get_session() as session:
                    new_client = self.boutique_controller.create_client(
                        session,
                        nom=client_data["nom"],
                        prenom=client_data.get("prenom"),
                        email=client_data.get("email"),
                        telephone=client_data.get("telephone"),
                        adresse=client_data.get("adresse")
                    )

                    # Recharger les clients et vider le champ de recherche
                    self.load_clients()
                    self.client_search.clear()

                    QMessageBox.information(self, "Succès", f"Client '{new_client.nom}' créé avec succès!")

            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la création du client: {str(e)}")
    
    def load_products(self):
        """Charge et affiche les produits dans la grille"""
        # Si le catalogue est en mode 'services', déléguer au loader de services
        if getattr(self, 'catalog_mode', 'products') == 'services':
            self.load_services()
            return

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

    def _get_display_name(self, obj):
        """Retourne un nom lisible pour un produit ou service en testant plusieurs attributs possibles."""
        for attr in ('name', 'nom', 'title', 'titre', 'label', 'libelle'):
            val = getattr(obj, attr, None)
            # ignorer les booléens (True/False) et valeurs vides
            if val is None or isinstance(val, bool):
                continue
            sval = str(val).strip()
            if sval:
                return sval
        # fallback to str(obj) or generic
        try:
            s = str(obj)
            if s is None:
                return 'Article'
            ls = s.strip().lower()
            if ls in ('false', 'none', ''):
                return 'Article'
            return s
        except Exception:
            return 'Article'

    def _get_id(self, obj):
        """Retourne un identifiant numérique/texte pour un objet (id, service_id, etc.)."""
        for attr in ('id', 'service_id', 'event_service_id', 'pk'):
            try:
                val = getattr(obj, attr, None)
            except Exception:
                val = None
            if val is not None:
                return val
        # last resort: try to inspect __dict__ for a primary key-like field
        try:
            if hasattr(obj, '__dict__'):
                for k, v in obj.__dict__.items():
                    if k.endswith('id') and v is not None:
                        return v
        except Exception:
            pass
        return None

    def _resolve_event_service_to_shop_service(self, session, event_service):
        """Trouve ou crée un ShopService correspondant à un EventService.

        Retourne une instance de ShopService (ORM) avec id, name, price.
        """
        try:
            # essayer par nom
            name = self._get_display_name(event_service)
            price = self._get_price(event_service)

            shop = session.query(ShopService).filter(ShopService.name == name).first()
            if shop:
                return shop

            # Aucun trouvé -> créer un enregistrement minimal en ne passant que les champs mappés
            now = __import__('datetime').datetime.now()
            candidate = {
                'pos_id': getattr(event_service, 'pos_id', getattr(event_service, 'pos', getattr(self, 'pos_id', None))),
                'name': name,
                'price': float(price) if price is not None else 0.0,
                'description': getattr(event_service, 'description', None),
                'is_active': True,
                # created_at will be set by default if declared in model
            }

            # Garder uniquement les clés présentes dans le modèle ShopService
            allowed = {}
            for k, v in candidate.items():
                if hasattr(ShopService, k):
                    allowed[k] = v

            try:
                new_shop = ShopService(**allowed)
                session.add(new_shop)
                session.flush()
                return new_shop
            except Exception as e:
                # log pour faciliter le debug sans casser l'UI
                print(f"Erreur création ShopService depuis EventService: {e}")
                return None
        except Exception:
            return None

    def _get_price(self, obj):
        """Retourne le prix (float) en testant plusieurs attributs possibles."""
        for attr in ('price_unit', 'price', 'prix', 'tarif', 'amount', 'montant', 'cost'):
            val = getattr(obj, attr, None)
            if val is not None:
                try:
                    return float(val)
                except Exception:
                    # essayer de nettoyer si c'est une string
                    try:
                        return float(str(val).replace(',', '.'))
                    except Exception:
                        continue
        return 0.0
    
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
    
    def add_to_cart(self, product, item_type='product', source=None):
        """Ajoute un produit ou service au panier avec dialogue de quantité.

        item_type: 'product' or 'service'
        source: for services only, 'shop' or 'event'
        """
        try:
            # Debug: inspect the incoming object for services to diagnose missing fields
            try:
                if item_type == 'service':
                    print('[DBG] add_to_cart received object type:', type(product))
                    try:
                        print('[DBG] repr:', repr(product))
                    except Exception:
                        pass
                    try:
                        print('[DBG] getattr name:', getattr(product, 'name', None))
                        print('[DBG] getattr nom:', getattr(product, 'nom', None))
                        print('[DBG] getattr id:', getattr(product, 'id', None))
                        print('[DBG] getattr price:', getattr(product, 'price', getattr(product, 'prix', None)))
                    except Exception:
                        pass
            except Exception:
                pass
            # Pour les produits, vérifier le stock
            available_stock = None
            if item_type == 'product':
                available_stock = self.get_available_stock(product.id)

            # Ouvrir le dialogue de quantité (utiliser le nom résolu)
            quantity_dialog = QuantityDialog(self, self._get_display_name(product), available_stock)

            if quantity_dialog.exec() == QDialog.DialogCode.Accepted:
                quantity = quantity_dialog.get_quantity()

                # Construire l'item générique en utilisant helpers pour nom/prix
                # Déterminer un id fiable : privilégier l'attribut id des instances ORM
                resolved_id = None
                try:
                    resolved_id = getattr(product, 'id', None)
                except Exception:
                    resolved_id = None

                if resolved_id in (None, False):
                    # fallback to legacy helper (may return pos_id in some cases)
                    resolved_id = self._get_id(product)

                new_item = {
                    'type': item_type,
                    'id': resolved_id,
                    'name': self._get_display_name(product),
                    'unit_price': float(self._get_price(product)),
                    'quantity': quantity,
                    'source': source
                }

                # Si c'est un service provenant d'un EventService, tenter d'abord de retrouver l'objet en base
                if new_item['type'] == 'service' and new_item.get('source') == 'event':
                    try:
                        with self.db_manager.get_session() as session:
                            event_obj = None
                            # Si l'objet en entrée avait un id, l'utiliser
                            try:
                                incoming_id = self._get_id(product)
                            except Exception:
                                incoming_id = None

                            if incoming_id is not None:
                                # Chercher par id
                                try:
                                    event_obj = session.query(EventService).filter_by(id=incoming_id).first()
                                except Exception:
                                    event_obj = None

                            # Sinon, chercher par nom (display name)
                            if event_obj is None:
                                try:
                                    candidate_name = self._get_display_name(product)
                                    if candidate_name and candidate_name != 'Article':
                                        event_obj = session.query(EventService).filter(EventService.name.ilike(f'%{candidate_name}%')).first()
                                except Exception:
                                    event_obj = None

                            # Si trouvé, résoudre/créer le ShopService correspondant et remplir les infos
                            if event_obj is not None:
                                resolved = self._resolve_event_service_to_shop_service(session, event_obj)
                                if resolved is not None:
                                    new_item['id'] = getattr(resolved, 'id', None)
                                    new_item['name'] = self._get_display_name(resolved)
                                    new_item['unit_price'] = float(self._get_price(resolved))
                            else:
                                # fallback : essayer de résoudre directement à partir de l'objet reçu
                                try:
                                    resolved = self._resolve_event_service_to_shop_service(session, product)
                                    if resolved is not None:
                                        new_item['id'] = getattr(resolved, 'id', None)
                                        new_item['name'] = self._get_display_name(resolved)
                                        new_item['unit_price'] = float(self._get_price(resolved))
                                except Exception:
                                    pass
                    except Exception:
                        pass

                # debug logs removed

                # Vérifier si l'item existe déjà
                existing_item = None
                for item in self.current_cart:
                    if item.get('type') != new_item.get('type'):
                        continue

                    if new_item.get('type') == 'product':
                        # Pour les produits, comparer par id + source
                        if item.get('id') == new_item.get('id') and item.get('source') == new_item.get('source'):
                            existing_item = item
                            break
                    else:
                        # Pour les services, utiliser name+unit_price+source comme clé (id peut être incorrect)
                        try:
                            same_name = (str(item.get('name')) == str(new_item.get('name')))
                            same_price = float(item.get('unit_price', 0)) == float(new_item.get('unit_price', 0))
                        except Exception:
                            same_name = (item.get('name') == new_item.get('name'))
                            same_price = item.get('unit_price') == new_item.get('unit_price')

                        if same_name and same_price and item.get('source') == new_item.get('source'):
                            existing_item = item
                            break

                if existing_item:
                    existing_item['quantity'] += quantity
                else:
                    self.current_cart.append(new_item)

                # Mettre à jour l'affichage
                self.update_cart_display()
                self.update_totals()

                # Émettre les signaux
                if new_item['type'] == 'product':
                    self.product_added_to_cart.emit(new_item['id'], quantity)
                self.cart_updated.emit()

                print(f"✅ {new_item['name']} ajouté au panier (quantité: {quantity})")

        except Exception as e:
            print(f"❌ Erreur add_to_cart: {e}")
    
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
            # Nom
            name_item = QTableWidgetItem(item.get('name') or '')
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.cart_table.setItem(row, 0, name_item)

            # Quantité (editable)
            qty_item = QTableWidgetItem(str(item.get('quantity', 0)))
            qty_item.setData(Qt.ItemDataRole.UserRole, row)
            self.cart_table.setItem(row, 1, qty_item)

            # Prix unitaire
            price_item = QTableWidgetItem(f"{float(item.get('unit_price', 0)):.0f}")
            price_item.setFlags(price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.cart_table.setItem(row, 2, price_item)

            # Total ligne
            total_line = float(item.get('unit_price', 0)) * float(item.get('quantity', 0))
            total_item = QTableWidgetItem(f"{total_line:.0f}")
            total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
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
                    # Si c'est un produit, vérifier le stock disponible
                    item_obj = self.current_cart[row]
                    if item_obj.get('type') == 'product':
                        product_id = item_obj.get('id')
                        available_stock = self.get_available_stock(product_id)
                        if available_stock is not None and new_qty > available_stock:
                            QMessageBox.warning(
                                self,
                                "Stock insuffisant",
                                f"Stock disponible: {available_stock:.0f}\\nQuantité demandée: {new_qty}"
                            )
                            self.update_cart_display()
                            return

                    # Mettre à jour la quantité
                    self.current_cart[row]['quantity'] = new_qty
                    self.update_cart_display()
                    self.update_totals()
                    self.cart_updated.emit()
                    
                else:
                    # Demander confirmation pour supprimer l'article
                    product_name = self.current_cart[row].get('name', '')
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
        subtotal = float(sum(item['unit_price'] * item['quantity'] for item in self.current_cart))

        # Calculer la remise (montant fixe)
        discount_amount = float(self.discount_spin.value())

        # S'assurer que la remise ne dépasse pas le sous-total
        if discount_amount > subtotal:
            discount_amount = subtotal
            self.discount_spin.setValue(float(subtotal))

        total = subtotal - discount_amount

        # Mettre à jour les labels
        self.subtotal_label.setText(f"{subtotal:.0f} FC")
        self.discount_amount_label.setText(f"{discount_amount:.0f} FC")
        self.total_label.setText(f"{total:.0f} FC")
    
    def apply_discount_auto(self):
        """Applique automatiquement la remise lors du changement de valeur"""
        discount_amount = self.discount_spin.value()
        self.global_discount = Decimal(str(discount_amount))
        self.update_totals()
        # Pas de feedback - application silencieuse et fluide
    
    def apply_discount(self):
        """Applique la remise globale (méthode de compatibilité)"""
        self.apply_discount_auto()
    
    def clear_cart(self):
        """Vide le panier sans confirmation"""
        # Suppression de la confirmation - vider directement
        self.current_cart = []
        self.global_discount = Decimal('0.00')
        self.discount_spin.setValue(0)
        self.update_cart_display()
        self.update_totals()
        self.cart_updated.emit()
        print("🗑️ Panier vidé")
    
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
                    # Ne vérifier que les produits physiques
                    if item.get('type') != 'product':
                        continue

                    product_id = item.get('id')
                    required_qty = item.get('quantity')

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
                            f"• {item.get('name', '')}: "
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
                
                # Calculer les totaux avec remise en montant (forcer float)
                subtotal = float(sum(item['unit_price'] * item['quantity'] for item in self.current_cart))
                discount_amount = float(self.global_discount) if isinstance(self.global_discount, Decimal) else float(self.global_discount)
                total_amount = float(subtotal - discount_amount)
                
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
                    INSERT INTO shop_paniers 
                    (pos_id, client_id, numero_commande, status, payment_method, 
                     subtotal, remise_amount, total_final, user_id, created_at, updated_at)
                    VALUES (:pos_id, :client_id, :numero_commande, :status, :payment_method,
                            :subtotal, :remise_amount, :total_final, :user_id, :created_at, :updated_at)
                """), {
                    'pos_id': self.pos_id,
                    'client_id': sale_data['client_id'],
                    'numero_commande': f"CMD-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                    'status': 'completed',
                    'payment_method': sale_data['payment_method'],
                    'subtotal': sale_data['subtotal'],
                    'remise_amount': sale_data['discount_amount'],
                    'total_final': sale_data['total_amount'],
                    'user_id': sale_data['user_id'],
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                })
                
                session.flush()
                
                # Récupérer l'ID du panier créé
                panier_id_result = session.execute(text("SELECT last_insert_rowid()"))
                panier_id = panier_id_result.fetchone()[0]
                
                # 2. Créer les lignes de vente et gérer le stock
                for item in self.current_cart:
                    if item.get('type') == 'product':
                        product_id = item.get('id')
                        quantity = item.get('quantity')
                        unit_price = item.get('unit_price')
                        line_total = unit_price * quantity

                        # Créer la ligne de panier produits
                        session.execute(text("""
                            INSERT INTO shop_paniers_products 
                            (panier_id, product_id, quantity, price_unit, total_price)
                            VALUES (:panier_id, :product_id, :quantity, :price_unit, :total_price)
                        """), {
                            'panier_id': panier_id,
                            'product_id': product_id,
                            'quantity': quantity,
                            'price_unit': float(unit_price),
                            'total_price': float(line_total)
                        })

                        # 3. Gérer le stock POS (sortie de stock)
                        self._update_pos_stock(session, product_id, quantity)

                    elif item.get('type') == 'service':
                        quantity = item.get('quantity')
                        unit_price = item.get('unit_price')
                        line_total = unit_price * quantity

                        # Déterminer l'ID du ShopService : si source == 'event' -> mapper par nom
                        service_id = None
                        if item.get('source') == 'shop':
                            service_id = item.get('id')
                        elif item.get('source') == 'event':
                            # Chercher ShopService existant par nom
                            svc = session.query(ShopService).filter(ShopService.name == item.get('name')).first()
                            if not svc:
                                svc = ShopService(
                                    pos_id=self.pos_id,
                                    name=item.get('name'),
                                    description='',
                                    cost=0.0,
                                    price=unit_price,
                                    is_active=True
                                )
                                session.add(svc)
                                session.flush()
                                session.refresh(svc)
                            service_id = svc.id

                        # Insérer la ligne de service
                        session.execute(text("""
                            INSERT INTO shop_paniers_services
                            (panier_id, service_id, quantity, price_unit, total_price)
                            VALUES (:panier_id, :service_id, :quantity, :price_unit, :total_price)
                        """), {
                            'panier_id': panier_id,
                            'service_id': service_id,
                            'quantity': quantity,
                            'price_unit': float(unit_price),
                            'total_price': float(line_total)
                        })
                
                # 4. Enregistrer le paiement
                session.execute(text("""
                    INSERT INTO shop_payments 
                    (panier_id, amount, payment_method, payment_date, reference)
                    VALUES (:panier_id, :amount, :payment_method, :payment_date, :reference)
                """), {
                    'panier_id': panier_id,
                    'amount': sale_data['total_amount'],
                    'payment_method': sale_data['payment_method'],
                    'payment_date': datetime.now(),
                    'reference': f"VENTE-{panier_id}"
                })
                
                # 5. Créer les écritures comptables si le module comptabilité est configuré
                self._create_sale_accounting_entries(session, sale_data, panier_id)
                
                # Valider la transaction
                session.commit()
                
                # Afficher le reçu
                self._show_sale_receipt(sale_data, payment_data)
                
                # Nettoyer le panier automatiquement après le reçu
                self.clear_cart()
                
                # Feedback discret - juste l'émission du signal
                print(f"✅ Vente #{panier_id} complétée - {total_amount:.0f} FC")
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
        """Affiche le reçu de vente avec en-tête d'entreprise"""
        
        # Récupérer les informations de l'entreprise
        enterprise_info = self.enterprise_controller.get_current_enterprise()
        
        # Générer un numéro de commande unique (basé sur timestamp + POS)
        from datetime import datetime
        order_number = f"CMD-{self.pos_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Construire l'en-tête d'entreprise avec logo
        receipt_text = f"""===============================
{enterprise_info['name']}
===============================

Adresse: {enterprise_info['address']}
Téléphone: {enterprise_info['phone']}
Email: {enterprise_info['email']}
RCCM: {enterprise_info['rccm']}

===== REÇU DE VENTE =====

N° Commande: {order_number}
Date: {sale_data['sale_date'].strftime('%d/%m/%Y %H:%M')}
POS: #{self.pos_id}
Vendeur: {getattr(self.current_user, 'name', 'Utilisateur')}

--- DÉTAIL DES ARTICLES ---
"""
        
        # Formater les produits avec alignement correct
        for item in self.current_cart:
            product_name = item.get('name', '')[:25] + '...' if len(item.get('name', '')) > 25 else item.get('name', '')
            quantity = item.get('quantity', 0)
            unit_price = item.get('unit_price', 0.0)
            total_price = unit_price * quantity
            
            # Formatage aligné avec espaces
            line = f"{product_name:<28} {quantity:>3} x {unit_price:>6.0f} = {total_price:>8.0f} FC\n"
            receipt_text += line
        
        receipt_text += f"""
--- TOTAUX ---
Sous-total:              {sale_data['subtotal']:>8.0f} FC
Remise appliquée:        -{sale_data['discount_amount']:>8.0f} FC
TOTAL À PAYER:           {sale_data['total_amount']:>8.0f} FC

--- PAIEMENT ---
Méthode:                 {payment_data['method']}
Montant reçu:            {payment_data['amount_received']:>8.0f} FC
Monnaie rendue:          {payment_data['change']:>8.0f} FC

Merci pour votre achat !
Bonne journée.

===============================
Généré par Ayanna ERP©
Tous droits réservés
===============================
"""
        
        # Afficher dans un dialogue
        receipt_dialog = QDialog(self)
        receipt_dialog.setWindowTitle("🧾 Reçu de vente")
        receipt_dialog.setFixedSize(500, 700)
        
        layout = QVBoxLayout(receipt_dialog)
        
        # Tentative d'affichage du logo (optionnel)
        try:
            logo_path = enterprise_info.get('logo_path', '')
            if logo_path and os.path.exists(logo_path):
                logo_label = QLabel()
                pixmap = QPixmap(logo_path)
                if not pixmap.isNull():
                    # Redimensionner le logo
                    scaled_pixmap = pixmap.scaled(100, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    logo_label.setPixmap(scaled_pixmap)
                    logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    layout.addWidget(logo_label)
        except Exception as e:
            print(f"⚠️ Logo non affiché: {e}")
        
        receipt_display = QTextEdit()
        receipt_display.setPlainText(receipt_text)
        receipt_display.setReadOnly(True)
        receipt_display.setStyleSheet("""
            QTextEdit {
                font-family: 'Courier New', 'Consolas', monospace;
                font-size: 12px;
                background-color: white;
                line-height: 1.3;
                padding: 10px;
                border: 1px solid #ddd;
            }
        """)
        layout.addWidget(receipt_display)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        print_btn = QPushButton("🖨️ Imprimer")
        print_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        print_btn.clicked.connect(lambda: self._print_receipt(receipt_text))
        buttons_layout.addWidget(print_btn)
        
        close_btn = QPushButton("✅ Fermer")
        close_btn.setStyleSheet("""
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
        close_btn.clicked.connect(receipt_dialog.accept)
        close_btn.setDefault(True)
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
        self.client = None
        try:
            # try to get currently selected client name if available from parent
            if hasattr(parent, 'client_combo'):
                data = parent.client_combo.currentData()
                # try to fetch display text safely
                try:
                    idx = parent.client_combo.currentIndex()
                    self.client = parent.client_combo.itemText(idx)
                except Exception:
                    self.client = None
        except Exception:
            self.client = None
        
        if total_amount is None:
            subtotal = sum(item['unit_price'] * item['quantity'] for item in cart_items)
            # s'assurer que discount est un float (éviter Decimal * float)
            try:
                discount_val = float(discount)
            except Exception:
                discount_val = 0.0

            # discount est maintenant un montant fixe en FC, pas un pourcentage
            self.discount_amount = discount_val
            # s'assurer que la remise ne dépasse pas le sous-total
            if self.discount_amount > subtotal:
                self.discount_amount = subtotal
            self.total_amount = subtotal - self.discount_amount
        else:
            self.total_amount = total_amount
        
        self.init_ui()
    
    def init_ui(self):
        """Initialise l'interface du dialogue de paiement"""
        self.setWindowTitle("💳 Paiement")
        self.setModal(True)
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Récapitulatif enrichi
        summary_group = QGroupBox()
        summary_group.setTitle("Récapitulatif de la commande")
        summary_layout = QFormLayout(summary_group)

        # Sous-total
        subtotal = sum(item['unit_price'] * item['quantity'] for item in self.cart_items)
        subtotal_label = QLabel(f"{subtotal:.0f} FC")
        subtotal_label.setStyleSheet("color: #333; font-weight: bold;")
        summary_layout.addRow("Sous-total:", subtotal_label)

        # Client (si connu)
        client_display = QLabel(self.client or "Client anonyme")
        client_display.setStyleSheet("color: #555;")
        summary_layout.addRow("Client:", client_display)

        # Nombre d'articles
        items_label = QLabel(str(len(self.cart_items)))
        items_label.setStyleSheet("color: #555;")
        summary_layout.addRow("Articles:", items_label)

        # Remise (montant fixe)
        disc_val = getattr(self, 'discount_amount', float(self.discount) if self.discount else 0.0)
        disc_label = QLabel(f"-{disc_val:.0f} FC")
        disc_label.setStyleSheet("color: #e53935; font-weight: bold;")
        summary_layout.addRow("Remise:", disc_label)

        # Total final mis en valeur
        total_label = QLabel(f"{self.total_amount:.0f} FC")
        total_label.setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 18px;")
        summary_layout.addRow("TOTAL À PAYER:", total_label)

        # Améliorer l'aspect visuel du groupe
        summary_group.setStyleSheet('''
            QGroupBox { border: 1px solid #E0E0E0; border-radius: 6px; padding: 10px; background: #FFF; }
            QLabel { font-size: 13px; }
        ''')

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