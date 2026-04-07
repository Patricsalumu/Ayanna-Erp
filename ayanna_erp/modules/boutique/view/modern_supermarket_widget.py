"""
Interface moderne de type supermarché pour le module Boutique
Design épuré avec catalogue de produits et panier de vente
"""

import os
from decimal import Decimal
from typing import List, Dict, Optional
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QFrame, QLabel, QPushButton, QLineEdit, QComboBox, QSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QSplitter, QGroupBox, QFormLayout, QDoubleSpinBox, QTextEdit,
    QDialog, QDialogButtonBox, QStyle
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.core.models import CoreProduct, CoreProductCategory
from ..model.models import ShopClient, ShopPanier, ShopService
from ayanna_erp.modules.salle_fete.model.salle_fete import EventService
from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
from ..utils.invoice_printer import InvoicePrintManager
from .client_index import ClientFormDialog
from ..controller.vente_controller import VenteController
from sqlalchemy import or_


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
        # Déterminer enterprise_id en privilégiant le contrôleur d'entreprise
        try:
            eid = None
            # Si le contrôleur propose l'objet entreprise courant
            if hasattr(self.enterprise_controller, 'get_current_enterprise'):
                try:
                    ent = self.enterprise_controller.get_current_enterprise()
                    if ent and isinstance(ent, dict) and ent.get('id'):
                        eid = ent.get('id')
                except Exception:
                    eid = None

            # Si pas d'id trouvé, tenter get_current_enterprise_id()
            if not eid and hasattr(self.enterprise_controller, 'get_current_enterprise_id'):
                try:
                    eid = self.enterprise_controller.get_current_enterprise_id()
                except Exception:
                    eid = None

            # Fallback: pos_id ou 1
            if not eid:
                eid = self.pos_id or 1
        except Exception:
            eid = self.pos_id or 1

        self.invoice_printer = InvoicePrintManager(enterprise_id=eid)
        self.vente_controller = VenteController(self.pos_id, self.current_user)
        
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
    
    def get_currency_symbol(self):
        """Récupère le symbole de devise depuis l'entreprise"""
        return self.enterprise_controller.get_currency_symbol()

    def format_money(self, amount):
        # Format en "1 000 000"
        formatted = f"{amount:,.0f}".replace(",", " ")
        return f"{formatted} {self.get_currency_symbol()}"
    
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
        splitter.setSizes([600, 400])

        # --- Ajout gestion scanner code-barres ---
        # Focus automatique sur la barre de recherche à l'ouverture
        QTimer.singleShot(200, self.set_search_focus)

        # Gestion de l'événement "entrée" sur la barre de recherche (pour scanner)
        self.search_edit.returnPressed.connect(self.handle_barcode_scanned)

    def set_search_focus(self):
        """Place le focus sur la barre de recherche produit (pour scanner)"""
        try:
            self.search_edit.setFocus()
            self.search_edit.selectAll()
        except Exception:
            pass

    def handle_barcode_scanned(self):
        """Détecte si un code-barres a été scanné, recherche le produit et l'ajoute au panier automatiquement."""
        code = self.search_edit.text().strip()
        if not code:
            return
        try:
            session = self.db_manager.get_session()
            # Recherche d'abord par barcode, puis par code si non trouvé
            product = session.query(CoreProduct).filter(CoreProduct.barcode == code).first()
            if product:
                self.products = [product]
                # Ajout direct sans fenêtre de quantité
                self.add_to_cart(product, item_type='product', skip_quantity_dialog=True)
                self.search_edit.clear()
                self.display_products(self.products)
                QTimer.singleShot(100, self.set_search_focus)
            else:
                QMessageBox.warning(self, "Produit introuvable", f"Aucun produit trouvé pour le code-barres : {code}")
                self.search_edit.selectAll()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de la recherche du produit : {e}")
            self.search_edit.selectAll()
    
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
        price_label = QLabel(self.format_money(float(price_val)))
        price_label.setStyleSheet("font-size:14px; font-weight:bold; color:#4CAF50;")
        card_layout.addWidget(price_label)

        # Source badge
        source_label = QLabel("(service)" if source == 'event' else "(service)")
        source_label.setStyleSheet("color:#777; font-size:11px;")
        card_layout.addWidget(source_label)
        # Bouton ajouter
        add_btn = QPushButton("➕ Ajouter")
        add_btn.setStyleSheet("background-color:#2196F3; color:white; border:none; border-radius:4px; padding:6px; font-weight:bold;")
        add_btn.clicked.connect(lambda _checked, svc_id=getattr(service, 'id', None), svc_name=getattr(service, 'name', None) or getattr(service, 'nom', None), src=source: self.add_service_to_cart_by_id(svc_id, src, svc_name))
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
        price_label = QLabel(self.format_money(float(price_val)))
        price_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        layout.addWidget(price_label, 1, Qt.AlignmentFlag.AlignRight)

        # Source
        source_label = QLabel("(service)" if source == 'event' else "(service)")
        source_label.setStyleSheet("color:#777; font-size:11px;")
        layout.addWidget(source_label, 1, Qt.AlignmentFlag.AlignRight)

        # Bouton ajouter
        add_btn = QPushButton("➕")
        add_btn.setToolTip("Ajouter au panier")
        add_btn.setFixedSize(34, 28)
        add_btn.setStyleSheet("background-color:#2196F3; color:white; border:none; border-radius:4px;")
        # Transmettre l'id pour garantir la recherche en session
        # Même raison: le signal clicked passe un bool; absorber avec `_checked`.
        add_btn.clicked.connect(lambda _checked, svc_id=getattr(service, 'id', None), svc_name=getattr(service, 'name', None) or getattr(service, 'nom', None), src=source: self.add_service_to_cart_by_id(svc_id, src, svc_name))
        layout.addWidget(add_btn, 0, Qt.AlignmentFlag.AlignRight)

        return row

    def add_service_to_cart_by_id(self, service_or_id, source='shop', service_name=None):
        print(f"DEBUGG : ADD SERVICE TO CART ID : {service_or_id} - SERVICE NAME {service_name}")
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
                incoming_id = service_or_id
                incoming_name = service_name


                # chercher directement  dans EventService
                
                ev = session.query(EventService).filter_by(id=incoming_id).first()

                print(f"DEBUGG ADD SERVICE TO CART BY ID APRES REQUETE {ev}")
                if ev is None:
                    # Debug temporaire: afficher l'id et la source reçus
                    # debug logs removed
                    QMessageBox.warning(self, "Service introuvable", "Le service sélectionné est introuvable en base.")
                    return
                # Appeler add_to_cart avec l'objet ShopService
                self.add_to_cart(ev, item_type='service', source='event')

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
        
        # Zone scrollable pour client, produits et notes
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setMaximumHeight(400)  # Hauteur maximale pour le scroll
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                background-color: white;
            }
            QScrollBar:vertical {
                width: 12px;
                background-color: #F0F0F0;
            }
            QScrollBar::handle:vertical {
                background-color: #C0C0C0;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #A0A0A0;
            }
        """)

        # Contenu scrollable
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(8)

        # Sélection client
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

        scroll_layout.addWidget(client_frame)

        # Liste des articles du panier
        # Add a fifth column for the delete action (Suppr)
        self.cart_table = QTableWidget(0, 5)
        self.cart_table.setHorizontalHeaderLabels(["Produit", "Qté", "Prix", "Total", "Suppr"])
        self.cart_table.horizontalHeader().setStretchLastSection(True)
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.setAlternatingRowColors(True)
        self.cart_table.setMinimumHeight(150)  # Hauteur minimale
        scroll_layout.addWidget(self.cart_table)

        # Section notes sur la commande
        notes_frame = QFrame()
        notes_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        notes_layout = QVBoxLayout(notes_frame)
        notes_layout.setContentsMargins(5, 5, 5, 5)

        # Titre de la section notes
        notes_title = QLabel("📝 Notes sur la commande")
        notes_title.setStyleSheet("font-weight: bold; color: #333; margin-bottom: 5px;")
        notes_layout.addWidget(notes_title)

        # Zone de texte pour les notes avec scroll
        self.notes_text = QTextEdit()
        self.notes_text.setPlaceholderText("Ajoutez ici des notes détaillées sur la commande...\n\nPar exemple :\n- Type d'habit pour pressing\n- Instructions spéciales\n- Préférences client\n- Commentaires...")
        self.notes_text.setMaximumHeight(120)  # Hauteur maximale avec scroll
        self.notes_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 5px;
                background-color: #FAFAFA;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
            }
            QTextEdit:focus {
                border-color: #2196F3;
                background-color: white;
            }
        """)
        notes_layout.addWidget(self.notes_text)

        scroll_layout.addWidget(notes_frame)

        # Définir le contenu scrollable
        scroll_area.setWidget(scroll_content)
        cart_layout.addWidget(scroll_area)

        # Zone totaux (statique - pas dans le scroll)
        totals_frame = self.create_totals_section()
        cart_layout.addWidget(totals_frame)

        # Boutons d'action (statiques - pas dans le scroll)
        actions_frame = self.create_actions_section()
        cart_layout.addWidget(actions_frame)

        return cart_widget
    
    def create_totals_section(self):
        """Crée la section des totaux avec remise en ligne horizontale"""
        totals_frame = QFrame()
        totals_layout = QVBoxLayout(totals_frame)

        # ===== Première ligne =====
        top_line_frame = QFrame()
        top_line_layout = QHBoxLayout(top_line_frame)
        top_line_layout.setContentsMargins(0, 0, 0, 0)
        top_line_layout.setSpacing(15)

        # ---- Sous-total ----
        subtotal_frame = QFrame()
        subtotal_layout = QVBoxLayout(subtotal_frame)
        subtotal_layout.setContentsMargins(0, 0, 0, 0)

        subtotal_label_title = QLabel("Sous-total:")
        subtotal_label_title.setStyleSheet("font-weight: bold; color: #666;")

        self.subtotal_label = QLabel(f"0.00 {self.get_currency_symbol()}")
        self.subtotal_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")

        subtotal_layout.addWidget(subtotal_label_title)
        subtotal_layout.addWidget(self.subtotal_label)

        top_line_layout.addWidget(subtotal_frame)

        # ---- Remise ----
        discount_frame = QFrame()
        discount_layout = QVBoxLayout(discount_frame)
        discount_layout.setContentsMargins(0, 0, 0, 0)

        discount_label_title = QLabel("Remise:")
        discount_label_title.setStyleSheet("font-weight: bold; color: #666;")

        self.discount_spin = QDoubleSpinBox()
        self.discount_spin.setRange(0, 999999)
        self.discount_spin.setSuffix(f" {self.get_currency_symbol()}")
        self.discount_spin.setFixedWidth(120)
        self.discount_spin.valueChanged.connect(self.apply_discount_auto)

        discount_layout.addWidget(discount_label_title)
        discount_layout.addWidget(self.discount_spin)

        top_line_layout.addWidget(discount_frame)

        # ---- Net à payer ----
        net_frame = QFrame()
        net_layout = QVBoxLayout(net_frame)
        net_layout.setContentsMargins(0, 0, 0, 0)

        net_label_title = QLabel("Net à payer:")
        net_label_title.setStyleSheet("font-weight: bold; color: #666;")

        self.net_total_label = QLabel(f"0.00 {self.get_currency_symbol()}")
        self.net_total_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #2196F3;"
        )

        net_layout.addWidget(net_label_title)
        net_layout.addWidget(self.net_total_label)

        top_line_layout.addWidget(net_frame)

        # 🔴 IMPORTANT : ajouter la première ligne au layout principal
        totals_layout.addWidget(top_line_frame)

        # ===== Séparateur =====
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #E0E0E0;")
        totals_layout.addWidget(separator)

        # ===== Total final =====
        total_frame = QFrame()
        total_layout = QHBoxLayout(total_frame)
        total_layout.setContentsMargins(0, 0, 0, 0)

        total_label_title = QLabel("TOTAL À PAYER:")
        total_label_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")

        self.total_label = QLabel(f"0.00 {self.get_currency_symbol()}")
        self.total_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #4CAF50;
            }
        """)

        total_layout.addStretch()
        total_layout.addWidget(total_label_title)
        total_layout.addWidget(self.total_label)
        total_layout.addStretch()

        totals_layout.addWidget(total_frame)

        return totals_frame

    
    def create_actions_section(self):
        """Crée la section des boutons d'action côte à côte"""
        actions_frame = QFrame()
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setSpacing(10)

        # Bouton vider panier (à gauche)
        clear_btn = QPushButton("�️ Vider le panier")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 12px;
                padding: 10px 15px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        clear_btn.clicked.connect(self.clear_cart)
        actions_layout.addWidget(clear_btn)

        # Espace extensible
        actions_layout.addStretch()

        # Bouton valider commande (à droite)
        validate_btn = QPushButton("� Valider & Payer")
        validate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px 20px;
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

        return actions_frame
    
    def create_product_card(self, product):
        """Crée une carte produit moderne avec image haute résolution"""
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
        card.setFixedSize(220, 280)  # Augmenté pour meilleure visibilité
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(8)
        
        # Image produit avec haute résolution
        image_label = QLabel()
        image_label.setFixedSize(180, 140)  # Résolution améliorée
        image_label.setStyleSheet("""
            QLabel {
                background-color: #F8F9FA;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
            }
        """)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Charger l'image du produit selon la logique spécifiée
        image_loaded = False
        if hasattr(product, 'image') and product.image and product.image.strip():
            try:
                # Le champ image contient le chemin relatif ou nom du fichier
                image_filename = product.image.strip()
                
                # Construire le chemin complet de l'image (même logique que produit_index.py)
                if os.path.isabs(image_filename):
                    # Chemin absolu
                    full_path = image_filename
                else:
                    # Chemin relatif depuis la racine du projet
                    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                    full_path = os.path.join(project_root, image_filename.replace("/", os.sep))
                
                if os.path.exists(full_path):
                    # Charger l'image avec PyQt5
                    pixmap = QPixmap(full_path)
                    if not pixmap.isNull():
                        # Redimensionner l'image pour s'adapter au label tout en gardant les proportions
                        scaled_pixmap = pixmap.scaled(
                            image_label.size(),  # Utiliser la taille du label comme dans produit_index.py
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation  # Haute qualité
                        )
                        image_label.setPixmap(scaled_pixmap)
                        image_loaded = True
                    else:
                        print(f"❌ Image corrompue: {full_path}")
                else:
                    print(f"❌ Image introuvable: {full_path}")
                        
            except Exception as e:
                print(f"❌ Erreur chargement image '{product.image}': {e}")
        
        # Si pas d'image chargée, afficher une image par défaut moderne
        if not image_loaded:
            image_label.setText("📦\nProduit")
            image_label.setStyleSheet("""
                QLabel {
                    background-color: #F8F9FA;
                    border: 2px dashed #DEE2E6;
                    border-radius: 6px;
                    color: #6C757D;
                    font-size: 12px;
                    font-weight: bold;
                }
            """)
        
        card_layout.addWidget(image_label, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Nom du produit
        name_label = QLabel(product.name[:30] + "..." if len(product.name) > 30 else product.name)
        name_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #212529;
                background: transparent;
                font-size: 11px;
            }
        """)
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(name_label)
        
        # Prix avec meilleure mise en forme
        price = getattr(product, 'price_unit', getattr(product, 'sale_price', 0))
        price_label = QLabel(self.format_money(price))

        price_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: bold;
                color: #28A745;
                background: transparent;
            }
        """)
        price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(price_label)
        
        # Informations supplémentaires (code produit si disponible)
        if hasattr(product, 'code') and product.code:
            code_label = QLabel(f"Code: {product.code}")
            code_label.setStyleSheet("""
                QLabel {
                    font-size: 9px;
                    color: #6C757D;
                    background: transparent;
                }
            """)
            code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(code_label)
        
        # Bouton d'ajout au panier
        add_btn = QPushButton("➕ Ajouter")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
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
                # Charger tous les clients actifs, peu importe leur pos_id
                # pour permettre le partage des clients entre modules
                clients = session.query(ShopClient).filter_by(
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
                        is_active=True
                    ).all()

                    for client in clients:
                        display_name = f"{client.nom} {client.prenom or ''}".strip()
                        self.client_combo.addItem(display_name, client.id)
                    return

                # Recherche par téléphone (priorité)
                client_by_phone = session.query(ShopClient).filter(
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
                        query = query.filter(
                            or_(
                                CoreProduct.name.ilike(f'%{search_text}%'),
                                CoreProduct.barcode.ilike(f'%{search_text}%')
                            )
                        )

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
    
    def add_to_cart(self, product, item_type='product', source=None, skip_quantity_dialog=False):
        """Ajoute un produit ou service au panier. Si skip_quantity_dialog=True, ajoute directement avec quantité 1."""
        try:
            # Pour les produits, vérifier le stock
            available_stock = None
            if item_type == 'product':
                available_stock = self.get_available_stock(product.id)

            if skip_quantity_dialog:
                quantity = 1
            else:
                # Ouvrir le dialogue de quantité (utiliser le nom résolu)
                quantity_dialog = QuantityDialog(self, self._get_display_name(product), available_stock)
                if quantity_dialog.exec() == QDialog.DialogCode.Accepted:
                    quantity = quantity_dialog.get_quantity()
                else:
                    return  # Annulé

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
        # Défensif : si des widgets Qt sous-jacents ont été détruits, attraper RuntimeError
        try:
            # Déconnecter temporairement le signal pour éviter les boucles
            try:
                self.cart_table.itemChanged.disconnect()
            except Exception:
                pass
            
            self.cart_table.setRowCount(len(self.current_cart))

            for row, item in enumerate(self.current_cart):
                # Nom
                name_item = QTableWidgetItem(item.get('name') or '')
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.cart_table.setItem(row, 0, name_item)

                # Quantité (editable)
                qty_item = QTableWidgetItem(str(item.get('quantity', 0)))
                # Stocker l'index logique dans UserRole pour on_cart_item_changed
                qty_item.setData(Qt.ItemDataRole.UserRole, row)
                qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.cart_table.setItem(row, 1, qty_item)

                # Prix unitaire (non éditable)
                price_item = QTableWidgetItem(self.format_money(float(item.get('unit_price', 0))))
                price_item.setFlags(price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.cart_table.setItem(row, 2, price_item)

                # Total ligne (non éditable)
                total_line = float(item.get('unit_price', 0)) * float(item.get('quantity', 0))
                total_item = QTableWidgetItem(self.format_money(total_line))
                total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.cart_table.setItem(row, 3, total_item)

                # Bouton Suppr: icône corbeille système si disponible, sinon emoji
                del_btn = QPushButton()
                del_btn.setToolTip("Supprimer cet article du panier")
                del_btn.setFixedSize(34, 28)
                try:
                    trash_icon = self.style().standardIcon(QStyle.SP_TrashIcon)
                    if not trash_icon.isNull():
                        del_btn.setIcon(trash_icon)
                    else:
                        del_btn.setText("🗑️")
                except Exception:
                    del_btn.setText("🗑️")
                del_btn.setStyleSheet("background-color:transparent;color:#f44336;border:none;")
                captured_item = item
                del_btn.clicked.connect(lambda _checked, it=captured_item: self._confirm_and_remove_item(it))
                self.cart_table.setCellWidget(row, 4, del_btn)
            
            # Reconnecter le signal
            try:
                self.cart_table.itemChanged.connect(self.on_cart_item_changed)
            except Exception:
                pass
            
            # Ajuster la largeur des colonnes
            header = self.cart_table.horizontalHeader()
            header.setStretchLastSection(False)
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Produit
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)    # Quantité
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)    # Prix
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)    # Total
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)    # Suppr
            
            try:
                self.cart_table.setColumnWidth(1, 80)  # Quantité
                self.cart_table.setColumnWidth(2, 80)  # Prix
                self.cart_table.setColumnWidth(3, 90)  # Total
                self.cart_table.setColumnWidth(4, 70)  # Suppr (bouton)
            except RuntimeError:
                print("DEBUG: cart_table déjà détruit lors de update_cart_display")
        except RuntimeError as re:
            print(f"DEBUG: RuntimeError dans update_cart_display: {re}")
        except Exception as e:
            print(f"DEBUG: Erreur inattendue dans update_cart_display: {e}")

    def _remove_cart_row(self, row):
        """Supprime un article du panier par index et met à jour l'affichage/totaux."""
        try:
            if 0 <= row < len(self.current_cart):
                removed = self.current_cart.pop(row)
                self.update_cart_display()
                self.update_totals()
                try:
                    self.cart_updated.emit()
                except Exception:
                    pass
                print(f"🗑️ Article supprimé du panier: {removed.get('name', '')}")
        except Exception as e:
            print(f"Erreur suppression ligne panier: {e}")

    def _confirm_and_remove_item(self, item):
        """Demande confirmation puis supprime l'article donné s'il est toujours présent."""
        try:
            product_name = item.get('name', '') if isinstance(item, dict) else str(item)
        except Exception:
            product_name = 'cet article'

        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            f"Supprimer '{product_name}' du panier ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Trouver l'index de l'objet (par identité si possible)
            try:
                for idx, it in enumerate(self.current_cart):
                    if it is item or it == item:
                        self._remove_cart_row(idx)
                        return
                # fallback: tenter de comparer par 'id' si présent
                item_id = item.get('id') if isinstance(item, dict) else None
                if item_id is not None:
                    for idx, it in enumerate(self.current_cart):
                        if isinstance(it, dict) and it.get('id') == item_id:
                            self._remove_cart_row(idx)
                            return
            except Exception as e:
                print(f"Erreur lors de la suppression confirmée: {e}")
    
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
        # Défensif : utiliser self.global_discount si le widget Qt a été détruit.
        try:
            try:
                discount_amount = float(self.discount_spin.value())
            except RuntimeError:
                # widget C++ supprimé
                print("DEBUG: discount_spin supprimé - fallback sur self.global_discount")
                discount_amount = float(self.global_discount)
        except Exception:
            # Toute autre erreur -> fallback sur self.global_discount
            discount_amount = float(self.global_discount)

        # S'assurer que la remise ne dépasse pas le sous-total
        if discount_amount > subtotal:
            discount_amount = subtotal
            try:
                if getattr(self, 'discount_spin', None) is not None:
                    try:
                        self.discount_spin.setValue(float(subtotal))
                    except RuntimeError:
                        print("DEBUG: impossible de setValue sur discount_spin (supprimé)")
            except Exception:
                pass

        total = subtotal - discount_amount

        # Mettre à jour les labels (défensif)
        try:
            if getattr(self, 'subtotal_label', None) is not None:
                try:
                    self.subtotal_label.setText(self.format_money(subtotal))
                except RuntimeError:
                    print("DEBUG: subtotal_label détruit lors de update_totals")
        except Exception:
            pass

        try:
            if getattr(self, 'net_total_label', None) is not None:
                try:
                    self.net_total_label.setText(self.format_money(total))
                except RuntimeError:
                    print("DEBUG: net_total_label détruit lors de update_totals")
        except Exception:
            pass

        try:
            if getattr(self, 'total_label', None) is not None:
                try:
                    self.total_label.setText(self.format_money(total))
                except RuntimeError:
                    print("DEBUG: total_label détruit lors de update_totals")
        except Exception:
            pass
    
    def apply_discount_auto(self):
        """Applique automatiquement la remise lors du changement de valeur"""
        try:
            try:
                discount_amount = self.discount_spin.value()
            except RuntimeError:
                print("DEBUG: discount_spin supprimé dans apply_discount_auto - fallback sur global_discount")
                discount_amount = float(self.global_discount)
        except Exception:
            discount_amount = float(self.global_discount)

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
        # Défensif : certains widgets Qt peuvent avoir été détruits côté C++.
        try:
            if getattr(self, 'discount_spin', None) is not None:
                try:
                    self.discount_spin.setValue(0)
                except RuntimeError:
                    # widget C++ supprimé
                    print("DEBUG: discount_spin déjà détruit lors de clear_cart()")
        except Exception:
            pass

        try:
            if getattr(self, 'notes_text', None) is not None:
                try:
                    self.notes_text.clear()
                except RuntimeError:
                    print("DEBUG: notes_text déjà détruit lors de clear_cart()")
        except Exception:
            pass
        # Vider la sélection client : QComboBox n'a pas clearSelection()
        try:
            # Essayer de désélectionner en positionnant l'index à -1
            self.client_combo.setCurrentIndex(-1)
        except Exception:
            # Si la combo est éditable, tenter de vider le texte
            try:
                self.client_combo.setCurrentText("")
            except Exception:
                pass
        self.selected_client = None
        # Vider le champ de recherche client
        try:
            if getattr(self, 'client_search', None) is not None:
                try:
                    self.client_search.clear()
                except RuntimeError:
                    print("DEBUG: client_search déjà détruit lors de clear_cart()")
        except Exception:
            pass
        self.update_cart_display()
        self.update_totals()
        self.cart_updated.emit()
        print("🗑️ Panier vidé")
    
    def validate_and_pay(self):
        """Valide la commande et procède au paiement"""
        if not self.current_cart:
            QMessageBox.warning(self, "Panier vide", "Veuillez ajouter des produits au panier")
            return

        # Refuser la vente si aucun client sélectionné (client anonyme)
        # try:
        #     # Si selected_client n'est pas défini ou si le combo contient un identifiant sentinel (-1)
        #     if not getattr(self, 'selected_client', None) or self.client_combo.currentData() in (None, -1):
        #         QMessageBox.warning(self, "Client requis", "Veuillez sélectionner un client valide avant de valider la vente (client anonyme non autorisé).")
        #         return
        # except Exception:
        #     QMessageBox.warning(self, "Client requis", "Impossible de vérifier le client — la vente est refusée.")
        #     return

        # Validation du stock via le contrôleur
        stock_valid, stock_message = self.vente_controller.validate_stock_availability(self.current_cart)
        if not stock_valid:
            QMessageBox.warning(
                self,
                "Stock insuffisant",
                f"Stock insuffisant pour :\n{stock_message}\n\n"
                "Veuillez ajuster les quantités ou retirer les produits concernés."
            )
            return

        # Ouvrir le dialogue de paiement
        payment_dialog = PaymentDialog(self, self.current_cart, self.global_discount)
        if payment_dialog.exec() == QDialog.DialogCode.Accepted:
            payment_data = payment_dialog.get_payment_data()

            # Préparer les données de vente pour le contrôleur
            subtotal = float(sum(item['unit_price'] * item['quantity'] for item in self.current_cart))
            total_amount = subtotal - float(self.global_discount)
            
            sale_data = {
                'cart_items': self.current_cart,
                'payment_data': payment_data,
                'client_id': self.client_combo.currentData(),
                'subtotal': subtotal,
                'total_amount': total_amount,
                'discount_amount': float(self.global_discount),
                'notes': self.notes_text.toPlainText().strip(),
                'sale_date': datetime.now()
            }

            # Traiter la vente via le contrôleur
            success, message, panier_id = self.vente_controller.process_sale(sale_data)

            if success:
                # Afficher le reçu (impression disponible) même si le montant reçu est 0
                # L'utilisateur doit toujours pouvoir imprimer la facture/reçu.
                try:
                    self._show_sale_receipt(sale_data, payment_data)
                except Exception as e:
                    # Ne pas bloquer le flux de vente si l'affichage du reçu échoue
                    print(f"Erreur affichage reçu: {e}")

                # Nettoyer le panier automatiquement après le traitement
                # Log d'état pour diagnostiquer widget détruit (RuntimeError)
                try:
                    print("DEBUG before clear_cart:",
                          "discount_spin=", getattr(self, 'discount_spin', None),
                          "notes_text=", getattr(self, 'notes_text', None),
                          "client_combo=", getattr(self, 'client_combo', None))
                except Exception:
                    pass

                self.clear_cart()

                # Feedback
                print(message)
                self.sale_completed.emit(panier_id)
            else:
                QMessageBox.critical(self, "Erreur de vente", message)

    def _show_sale_receipt(self, sale_data, payment_data):
        """Affiche le reçu de vente avec en-tête d'entreprise en utilisant InvoicePrintManager"""

        # Générer un numéro de commande unique (basé sur timestamp + POS)
        from datetime import datetime
        order_number = f"CMD-{self.pos_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Récupérer la note depuis la base de données (panier le plus récent)
        panier_notes = ""
        # Préinitialiser notes_row pour éviter des variables non définies en cas d'erreur
        notes_row = (order_number, '')
        try:
            with self.db_manager.get_session() as session:
                from sqlalchemy import text
                notes_result = session.execute(text("""
                    SELECT numero_commande, notes FROM shop_paniers 
                    WHERE pos_id = :pos_id 
                    ORDER BY created_at DESC LIMIT 1
                """), {'pos_id': self.pos_id})
                notes_row = notes_result.fetchone()
                if notes_row and notes_row[1]:
                    panier_notes = notes_row[1]
        except Exception as e:
            print(f"Erreur récupération notes panier: {e}")

        # Préparer les données de la facture
        total_amount = sale_data['total_amount']
        amount_received = payment_data['amount_received']
        
        # Calculer le change ou le reste
        change = 0.0
        reste_a_payer = 0.0
        if amount_received > total_amount:
            change = amount_received - total_amount
        elif amount_received < total_amount:
            reste_a_payer = total_amount - amount_received
        
        invoice_data = {
            'reference': notes_row[0],
            'order_date': sale_data['sale_date'],
            'created_at': sale_data['sale_date'],
            'status': 'Payée',
            'client_nom': getattr(self.selected_client, 'nom', 'Client anonyme') if self.selected_client else 'Client anonyme',
            'client_telephone': getattr(self.selected_client, 'telephone', '') if self.selected_client else '',
            'client_email': getattr(self.selected_client, 'email', '') if self.selected_client else '',
            'client_adresse': getattr(self.selected_client, 'adresse', '') if self.selected_client else '',
            'items': self.current_cart,
            'subtotal_ht': sale_data['subtotal'],
            'tax_amount': 0.0,  # Pas de TVA pour l'instant
            'total_ttc': total_amount,
            'discount_amount': sale_data['discount_amount'],
            'total_net': total_amount,  # Net à payer après remise
            'net_a_payer': total_amount,  # Alias pour compatibilité
            'change': change,  # Monnaie rendue
            'reste_a_payer': reste_a_payer,  # Montant restant dû
            'notes': panier_notes if panier_notes else f"Vente effectuée par {getattr(self.current_user, 'name', 'Utilisateur')} - POS #{self.pos_id}",
            'payments': [{
                'payment_date': sale_data['sale_date'],
                'amount': amount_received,
                'payment_method': payment_data['method'],
                'user_name': getattr(self.current_user, 'name', 'Utilisateur')
            }]
        }

        # Créer le dialogue d'impression
        receipt_dialog = QDialog(self)
        receipt_dialog.setWindowTitle("🧾 Reçu de vente")
        receipt_dialog.setFixedSize(500, 400)

        layout = QVBoxLayout(receipt_dialog)

        # Titre
        title_label = QLabel("Impression du reçu")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # Options d'impression
        options_group = QGroupBox("Options d'impression")
        options_layout = QVBoxLayout(options_group)

        # Format d'impression
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))

        self.print_format_combo = QComboBox()
        self.print_format_combo.addItems(["Reçu 53mm (ticket)", "Facture A4 (complet)"])
        format_layout.addWidget(self.print_format_combo)
        options_layout.addLayout(format_layout)

        # Aperçu du contenu
        preview_label = QLabel("Contenu du reçu généré:")
        preview_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        options_layout.addWidget(preview_label)

        # Aperçu simplifié
        preview_text = f"""
N° Commande: {notes_row[0]}
Client: {invoice_data['client_nom']}
Total: {self.format_money(sale_data['total_amount'])}
Paiement: {payment_data['method']}
        """.strip()

        preview_display = QTextEdit()
        preview_display.setPlainText(preview_text)
        preview_display.setReadOnly(True)
        preview_display.setMaximumHeight(100)
        preview_display.setStyleSheet("""
            QTextEdit {
                font-family: 'Courier New', monospace;
                font-size: 10px;
                background-color: #f5f5f5;
                border: 1px solid #ddd;
            }
        """)
        options_layout.addWidget(preview_display)

        layout.addWidget(options_group)

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
        print_btn.clicked.connect(lambda: self._print_invoice_receipt(invoice_data, receipt_dialog))
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

    def _print_invoice_receipt(self, invoice_data, dialog):
        """Imprime la facture/reçu en utilisant InvoicePrintManager"""
        try:
            # Déterminer le format d'impression
            format_choice = self.print_format_combo.currentText()

            # Générer un nom de fichier
            from datetime import datetime
            import tempfile
            import os

            # Déterminer le répertoire de destination
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            if "53mm" in format_choice:
                # Pour les tickets 53mm : dossier temporaire (pour impression directe)
                temp_dir = tempfile.gettempdir()
                filename = os.path.join(temp_dir, f"receipt_{timestamp}.pdf")
                printed_file = self.invoice_printer.print_receipt_53mm(
                    invoice_data,
                    invoice_data['payments'],
                    getattr(self.current_user, 'name', 'Utilisateur'),
                    filename
                )
                print_type = "ticket 53mm"
            else:
                # Pour les factures A4 : dossier racine du projet
                invoices_dir = os.path.join(os.getcwd(), "factures_export")
                os.makedirs(invoices_dir, exist_ok=True)  # Créer le dossier s'il n'existe pas
                filename = os.path.join(invoices_dir, f"facture_{invoice_data.get('reference', 'UNKNOWN')}_{timestamp}.pdf")
                printed_file = self.invoice_printer.print_invoice_a4(
                    invoice_data,
                    filename
                )
                print_type = "facture A4"

            if os.path.exists(printed_file):
                if "53mm" in format_choice:
                    # Pour les tickets 53mm : imprimer directement
                    try:
                        import subprocess
                        # Ouvrir le PDF avec l'application par défaut (qui permet l'impression)
                        subprocess.run(['start', '', printed_file], shell=True, check=True)
                        QMessageBox.information(
                            self,
                            "Impression lancée",
                            f"Le ticket 53mm a été généré et l'impression a été lancée automatiquement !\\n\\n"
                            f"Fichier: {printed_file}"
                        )
                    except Exception as print_error:
                        QMessageBox.warning(
                            self,
                            "Impression manuelle requise",
                            f"Le ticket 53mm a été généré avec succès !\\n\\n"
                            f"Fichier: {printed_file}\\n\\n"
                            f"Erreur d'impression automatique: {print_error}\\n"
                            "Veuillez imprimer manuellement depuis votre lecteur PDF."
                        )
                else:
                    # Pour les factures A4 : juste exporter
                    QMessageBox.information(
                        self,
                        "Export réussi",
                        f"La facture A4 a été exportée avec succès !\\n\\n"
                        f"Fichier: {printed_file}\\n\\n"
                        "Vous pouvez l'ouvrir et l'imprimer selon vos besoins."
                    )
            else:
                QMessageBox.warning(
                    self,
                    "Erreur d'export",
                    f"Impossible de générer le document."
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur d'impression",
                f"Une erreur s'est produite lors de l'impression:\\n{str(e)}"
            )
            import traceback
            traceback.print_exc()

    def _print_invoice_receipt(self, invoice_data, dialog):
        """Imprime la facture/reçu en utilisant InvoicePrintManager (même système que commandes_index.py)"""
        try:
            # Déterminer le format d'impression
            format_choice = self.print_format_combo.currentText()

            # Générer un nom de fichier
            from datetime import datetime
            import tempfile
            import os

            # Déterminer le répertoire de destination
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            if "53mm" in format_choice:
                # Pour les tickets 53mm : dossier temporaire (pour impression directe)
                temp_dir = tempfile.gettempdir()
                filename = os.path.join(temp_dir, f"receipt_sale_{timestamp}.pdf")
                print_type = "ticket 53mm"
            else:
                # Pour les factures A4 : dossier factures_export
                invoices_dir = os.path.join(os.getcwd(), "factures_export")
                os.makedirs(invoices_dir, exist_ok=True)  # Créer le dossier s'il n'existe pas
                filename = os.path.join(invoices_dir, f"facture_vente_{invoice_data.get('reference', 'UNKNOWN')}_{timestamp}.pdf")
                print_type = "facture A4"

            # Générer le document
            if "53mm" in format_choice:
                # Impression ticket 53mm
                payments_list = invoice_data.get('payments', [])
                user_name = invoice_data.get('payments', [{}])[0].get('user_name', 'Utilisateur') if invoice_data.get('payments') else 'Utilisateur'

                result = self.invoice_printer.print_receipt_53mm(invoice_data, payments_list, user_name, filename)
            else:
                # Impression A4
                result = self.invoice_printer.print_invoice_a4(invoice_data, filename)

            if result and os.path.exists(result):
                if "53mm" in format_choice:
                    # Pour les tickets 53mm : ouvrir directement dans le lecteur par défaut
                    try:
                        import subprocess
                        subprocess.run(['start', '', result], shell=True, check=True)
                        QMessageBox.information(dialog, "Impression lancée",
                                              f"Le ticket 53mm a été généré et l'impression a été lancée automatiquement !\n\n"
                                              f"Fichier: {result}")
                    except Exception as print_error:
                        QMessageBox.warning(dialog, "Impression manuelle requise",
                                          f"Le ticket 53mm a été généré avec succès !\n\n"
                                          f"Fichier: {result}\n\n"
                                          f"Erreur d'impression automatique: {print_error}\n"
                                          "Veuillez imprimer manuellement depuis votre lecteur PDF.")
                else:
                    # Pour les factures A4 : ouvrir le dossier factures_export
                    try:
                        import os, sys, subprocess
                        opened = False
                        if os.name == 'nt':
                            try:
                                os.startfile(result)
                                opened = True
                            except Exception:
                                opened = False
                        else:
                            try:
                                if sys.platform == 'darwin':
                                    subprocess.run(['open', result], check=True)
                                else:
                                    subprocess.run(['xdg-open', result], check=True)
                                opened = True
                            except Exception:
                                opened = False

                        if opened:
                            QMessageBox.information(dialog, "Export réussi",
                                                  f"La facture A4 a été exportée avec succès !\n\n"
                                                  f"Fichier: {result}\n\n"
                                                  "Le fichier a été ouvert dans l'application par défaut.")
                        else:
                            QMessageBox.information(dialog, "Export réussi",
                                                  f"La facture A4 a été exportée avec succès !\n\n"
                                                  f"Fichier: {result}\n\n"
                                                  "Impossible d'ouvrir automatiquement le fichier. Vous pouvez l'ouvrir manuellement.")
                    except Exception as open_error:
                        QMessageBox.information(dialog, "Export réussi",
                                              f"La facture A4 a été exportée avec succès !\n\n"
                                              f"Fichier: {result}\n\n"
                                              f"Erreur lors de l'ouverture du fichier: {open_error}")

                dialog.accept()
            else:
                QMessageBox.warning(dialog, "Erreur", f"Impossible de générer le document {print_type}.")

        except Exception as e:
            QMessageBox.critical(dialog, "Erreur", f"Erreur lors de l'impression: {e}")
            print(f"❌ Erreur _print_invoice_receipt: {e}")

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
    
    def get_currency_symbol(self):
        """Récupère le symbole de devise depuis l'entreprise"""
        try:
            return self.parent().get_currency_symbol()
        except Exception:
            return "FC"  # Fallback
    def format_money(self, amount):
        # Format en "1 000 000"
        formatted = f"{amount:,.0f}".replace(",", " ")
        return f"{formatted} {self.get_currency_symbol()}"
    
    def init_ui(self):
        """Initialise l'interface du dialogue de paiement"""
        self.setWindowTitle("💳 Paiement")
        self.setModal(True)
        self.setFixedSize(450, 420)
        
        layout = QVBoxLayout(self)
        
        # Récapitulatif enrichi
        summary_group = QGroupBox()
        summary_group.setTitle("Récapitulatif de la commande")
        summary_layout = QFormLayout(summary_group)

        # Sous-total
        subtotal = sum(item['unit_price'] * item['quantity'] for item in self.cart_items)
        subtotal_label = QLabel(self.format_money(subtotal))
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
        disc_label = QLabel(self.format_money(disc_val))
        disc_label.setStyleSheet("color: #e53935; font-weight: bold;")
        summary_layout.addRow("Remise:", disc_label)

        # Total final mis en valeur
        total_label = QLabel(self.format_money(self.total_amount))
        total_label.setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 18px;")
        summary_layout.addRow("TOTAL À PAYER:", total_label)

        # Améliorer l'aspect visuel du groupe
        summary_group.setStyleSheet('''
            QGroupBox { border: 1px solid #E0E0E0; border-radius: 6px; padding: 10px; background: #FFF; }
            QLabel { font-size: 13px; }
        ''')

        layout.addWidget(summary_group)
        
        # --- Mode de paiement (boutons sélectionnables) ---
        payment_group = QGroupBox("Mode de paiement")
        payment_group_layout = QVBoxLayout(payment_group)

        pay_btns_layout = QHBoxLayout()
        pay_methods = [
            ('Espèces', '💵', '#28a745'),
            ('Carte bancaire', '💳', '#1976D2'),
            ('Mobile Money', '📱', '#FF9800'),
            ('Crédit', '📝', '#e53935'),
        ]
        self._selected_method = 'Espèces'
        self._method_buttons = []

        def select_payment_method(method_name):
            self._selected_method = method_name
            for b in self._method_buttons:
                if b.property('method') == method_name:
                    b.setStyleSheet(f"background-color: {b.property('color')}; color: white; font-weight:bold; border-radius:6px; padding:8px 12px; border: 2px solid #333;")
                else:
                    b.setStyleSheet(f"background-color: #f0f0f0; color: #333; border-radius:6px; padding:8px 12px; border: 1px solid #ccc;")
            # Si Crédit: montant reçu = 0, non modifiable
            if method_name == 'Crédit':
                self.amount_received.setValue(0.0)
                self.amount_received.setEnabled(False)
            else:
                self.amount_received.setEnabled(True)
                self.amount_received.setValue(float(self.total_amount))

        for m_name, m_icon, m_color in pay_methods:
            btn = QPushButton(f'{m_icon} {m_name}')
            btn.setProperty('method', m_name)
            btn.setProperty('color', m_color)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._method_buttons.append(btn)
            btn.clicked.connect(lambda _checked, mn=m_name: select_payment_method(mn))
            pay_btns_layout.addWidget(btn)

        payment_group_layout.addLayout(pay_btns_layout)

        # Montant reçu
        amt_layout = QFormLayout()
        self.amount_received = QDoubleSpinBox()
        self.amount_received.setRange(0, 999999)
        self.amount_received.setValue(float(self.total_amount))
        self.amount_received.setSuffix(f" {self.get_currency_symbol()}")
        
        # Label pour afficher la monnaie ou le reste
        self.change_label = QLabel("")
        self.change_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #FF9800;")
        
        # Mettre à jour le label en temps réel
        def update_change_display():
            amount = self.amount_received.value()
            total = float(self.total_amount)
            if amount > total:
                monnaie = amount - total
                self.change_label.setText(f"Monnaie: {self.format_money(monnaie)}")
                self.change_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #4CAF50;")
            elif amount < total:
                reste = total - amount
                self.change_label.setText(f"Reste: {self.format_money(reste)}")
                self.change_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #E53935;")
            else:
                self.change_label.setText("")
        
        self.amount_received.valueChanged.connect(update_change_display)
        
        amt_layout.addRow("Montant reçu:", self.amount_received)
        amt_layout.addRow("", self.change_label)
        payment_group_layout.addLayout(amt_layout)
        
        # Appeler une fois pour initialiser l'affichage
        update_change_display()
        
        layout.addWidget(payment_group)

        # Sélectionner Espèces par défaut
        select_payment_method('Espèces')
        
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
            'method': self._selected_method,
            'amount_received': self.amount_received.value(),
            'total_amount': float(self.total_amount),
            'change': self.amount_received.value() - float(self.total_amount)
        }