from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter, QWidget, QGroupBox, QLabel, QPushButton,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox,
    QFrame, QButtonGroup, QRadioButton, QMessageBox, QGridLayout, QInputDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QPixmap
from ayanna_erp.modules.boutique.controller.panier_coontroller import PanierController


class NouveauPanierDialog(QDialog):
    def get_filtered_products(self):
        from ayanna_erp.modules.boutique.model.models import ShopService
        from ayanna_erp.modules.core.models.core_products import CoreProduct, CoreProductCategory
        session = self.panier_controller.db_manager.get_session()
        pos_id = getattr(self.current_user, 'pos_id', 1)
        search_text = self.search_input.text().strip().lower()
        selected_cat = self.category_combo.currentText()
        # Si Produits sélectionné
        if hasattr(self, 'products_radio') and self.products_radio.isChecked():
            query = session.query(CoreProduct).filter(CoreProduct.entreprise_id == pos_id)
            if search_text:
                query = query.filter(CoreProduct.name.ilike(f'%{search_text}%'))
            if selected_cat and selected_cat != "Toutes":
                cat_obj = session.query(CoreProductCategory).filter(CoreProductCategory.name == selected_cat).first()
                if cat_obj:
                    query = query.filter(CoreProduct.category_id == cat_obj.id)
            return query.all()
        # Si Services sélectionné
        elif hasattr(self, 'services_radio') and self.services_radio.isChecked():
            query = session.query(ShopService).filter(ShopService.pos_id == pos_id)
            if search_text:
                query = query.filter(ShopService.name.ilike(f'%{search_text}%'))
            # Pas de filtre catégorie pour les services
            return query.all()
        return []
        
    def __init__(self, parent=None, boutique_controller=None, current_user=None):
        super().__init__(parent)
        self.setWindowTitle("Nouveau panier de vente")
        self.setModal(True)
        self.resize(1100, 700)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)

        self.boutique_controller = boutique_controller
        self.current_user = current_user
        self.panier_controller = PanierController()
        self.panier = self.panier_controller.create_empty_panier(pos_id=1, client_id=None)

        layout = QVBoxLayout(self)
        main_layout = QHBoxLayout()
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.catalog_mode = 'card'
        self.catalog_section = self.create_catalog_section()
        splitter.addWidget(self.catalog_section)
        splitter.addWidget(self.create_panier_section())
        splitter.setSizes([800, 600])
        main_layout.addWidget(splitter)
        layout.addLayout(main_layout)

        # Boutons bas
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.cancel_btn = QPushButton("Annuler panier")
        self.cancel_btn.setStyleSheet("background-color: #E74C3C; color: white; font-weight: bold;")
        self.cancel_btn.clicked.connect(self.annuler_panier)
        btn_layout.addWidget(self.cancel_btn)

        self.validate_btn = QPushButton("Valider panier")
        self.validate_btn.setStyleSheet("background-color: #27AE60; color: white; font-weight: bold;")
        self.validate_btn.clicked.connect(self.valider_panier)
        btn_layout.addWidget(self.validate_btn)
        layout.addLayout(btn_layout)
        
        
        self.print_btn = QPushButton("Imprimer facture")
        self.print_btn.setStyleSheet("background-color: #F1C40F; color: black; font-weight: bold;")
        btn_layout.addWidget(self.print_btn)

    def annuler_panier(self):
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Êtes-vous sûr de vouloir annuler ce panier ? Cette action est irréversible.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.panier_controller.update_panier_status(self.panier.id, "annule")
            self.reject()

    def valider_panier(self):
        self.panier_controller.update_panier_status(self.panier.id, "valide")
        self.accept()

    def create_catalog_section(self):
        catalog_widget = QWidget()
        catalog_layout = QVBoxLayout(catalog_widget)

        header_group = QGroupBox("🛍️ Catalogue - Produits & Services")
        header_layout = QVBoxLayout(header_group)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Recherche:"))
        self.search_input = QLineEdit()
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(QLabel("Catégorie:"))
        self.category_combo = QComboBox()
        filter_layout.addWidget(self.category_combo)
        # Initialisation des catégories APRÈS la création du QComboBox
        from ayanna_erp.modules.core.models.core_products import CoreProductCategory
        session = self.panier_controller.db_manager.get_session()
        pos_id = getattr(self.current_user, 'pos_id', 1)
        categories = session.query(CoreProductCategory).filter(CoreProductCategory.entreprise_id == 1).all()
        self.category_combo.addItem("Toutes")
        for cat in categories:
            if cat.name:
                self.category_combo.addItem(cat.name)
        self.category_combo.currentIndexChanged.connect(self.populate_catalog_with_products)
        self.search_input.textChanged.connect(self.populate_catalog_with_products)

        refresh_btn = QPushButton("🔄 Actualiser")
        filter_layout.addWidget(refresh_btn)

        self.switch_mode_btn = QPushButton("🗂️ Mode liste")
        self.switch_mode_btn.setCheckable(True)
        self.switch_mode_btn.setChecked(False)
        self.switch_mode_btn.clicked.connect(self.toggle_catalog_mode)
        filter_layout.addWidget(self.switch_mode_btn)

        header_layout.addLayout(filter_layout)

        type_layout = QHBoxLayout()
        self.type_button_group = QButtonGroup()
        self.products_radio = QRadioButton("Produits")
        self.products_radio.setChecked(True)
        self.type_button_group.addButton(self.products_radio)
        type_layout.addWidget(self.products_radio)
        self.services_radio = QRadioButton("Services")
        self.type_button_group.addButton(self.services_radio)
        type_layout.addWidget(self.services_radio)
        type_layout.addStretch()
        # Connecter le changement de type au rafraîchissement du catalogue
        self.products_radio.toggled.connect(self.populate_catalog_with_products)
        self.services_radio.toggled.connect(self.populate_catalog_with_products)
        header_layout.addLayout(type_layout)

        catalog_layout.addWidget(header_group)

        # Zone affichage statique avec scroll
        from PyQt6.QtWidgets import QScrollArea
        self.catalog_display = QWidget()
        self.catalog_display_layout = QVBoxLayout(self.catalog_display)
        self.catalog_display_layout.setContentsMargins(0, 0, 0, 0)
        self.catalog_display_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.catalog_display)
        scroll_area.setFixedHeight(420)  # Hauteur fixe pour la zone catalogue
        catalog_layout.addWidget(scroll_area)

        self.populate_catalog_with_products()
        return catalog_widget

    def populate_catalog_with_products(self):
        items = self.get_filtered_products()

        # Nettoyer complètement l'affichage (cartes ou tableau)
        while self.catalog_display_layout.count():
            item = self.catalog_display_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                sublayout = item.layout()
                while sublayout.count():
                    subitem = sublayout.takeAt(0)
                    subwidget = subitem.widget()
                    if subwidget:
                        subwidget.deleteLater()
                sublayout.deleteLater()

        # Toujours garder la zone de filtre/recherche statique
        # Si aucun produit/service, afficher un message dans la zone d’affichage
        if not items:
            empty_lbl = QLabel("Aucun produit ou service trouvé.")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet("color: #7F8C8D; font-size: 16px; margin: 40px;")
            self.catalog_display_layout.addWidget(empty_lbl)

        if self.catalog_mode == 'card':
            grid = QGridLayout()
            grid.setSpacing(15)
            max_cards = 6
            for idx, item in enumerate(items[:max_cards]):
                card = QFrame()
                card.setFrameShape(QFrame.Shape.StyledPanel)
                card.setStyleSheet("""
                    QFrame {
                        background: #FFFFFF;
                        border: 1px solid #D5D8DC;
                        border-radius: 12px;
                        padding: 10px;
                    }
                    QFrame:hover {
                        border: 2px solid #3498DB;
                        background: #F4F9FF;
                    }
                """)
                vbox = QVBoxLayout(card)
                img = QLabel()
                img.setFixedSize(120, 100)
                img.setAlignment(Qt.AlignmentFlag.AlignCenter)
                image_path = getattr(item, "image", None)
                if image_path:
                    pixmap = QPixmap(image_path)
                    if not pixmap.isNull():
                        img.setPixmap(pixmap.scaled(120, 100, Qt.AspectRatioMode.KeepAspectRatio,
                                                    Qt.TransformationMode.SmoothTransformation))
                    else:
                        img.setText("🖼️")
                        img.setStyleSheet("background: #ECF0F1; border-radius: 8px;")
                else:
                    img.setText("🖼️")
                    img.setStyleSheet("background: #ECF0F1; border-radius: 8px;")
                vbox.addWidget(img, alignment=Qt.AlignmentFlag.AlignCenter)
                name_lbl = QLabel(item.name)
                name_lbl.setFont(QFont("Arial", 11, QFont.Weight.Bold))
                name_lbl.setWordWrap(True)
                name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                vbox.addWidget(name_lbl)
                # Prix : CoreProduct.price_unit ou ShopService.price
                price = getattr(item, "price_unit", None)
                if price is None:
                    price = getattr(item, "price", 0)
                price_lbl = QLabel(f"{price:.2f} €")
                price_lbl.setFont(QFont("Arial", 11))
                price_lbl.setStyleSheet("color: #27AE60; font-weight: bold;")
                price_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                vbox.addWidget(price_lbl)
                card.mousePressEvent = lambda event, pid=item.id: self.handle_card_click(pid)
                grid.addWidget(card, idx // 3, idx % 3)
            self.catalog_display_layout.addLayout(grid)
        else:
            table = QTableWidget()
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(["Nom", "Description", "Prix", "Action"])
            header = table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            table.setAlternatingRowColors(True)
            table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            table.setRowCount(len(items))
            for row, item in enumerate(items):
                table.setItem(row, 0, QTableWidgetItem(item.name))
                description = getattr(item, "description", "-") or "-"
                table.setItem(row, 1, QTableWidgetItem(description))
                price = getattr(item, "price_unit", None)
                if price is None:
                    price = getattr(item, "price", 0)
                price_item = QTableWidgetItem(f"{price:.2f} €")
                price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                table.setItem(row, 2, price_item)
                add_btn = QPushButton("➕ Ajouter")
                add_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3498DB;
                        color: white;
                        font-weight: bold;
                        padding: 5px 10px;
                        border: none;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #2980B9;
                    }
                    QPushButton:disabled {
                        background-color: #BDC3C7;
                    }
                """)
                add_btn.clicked.connect(
                    lambda checked, pid=item.id: self.handle_card_click(pid)
                )
                table.setCellWidget(row, 3, add_btn)
            self.catalog_display_layout.addWidget(table)
            self.catalog_table = table

    def handle_card_click(self, product_id):
        """Quand on clique sur une card, proposer la quantité ou incrémenter"""
        from ayanna_erp.modules.core.models import CoreProduct
        session = self.panier_controller.db_manager.get_session()
        product = session.query(CoreProduct).get(product_id)

        if not product:
            return
        # Vérifier si le produit existe déjà dans le panier
        panier_product = session.query(type(product).panier_products.property.mapper.class_).filter_by(panier_id=self.panier.id, product_id=product_id).first()
        if panier_product:
            # Demander la quantité à ajouter
            qty, ok = QInputDialog.getInt(self, "Quantité supplémentaire", f"Ajouter combien à {product.name} ?", 1, 1, 1000, 1)
            if ok:
                new_qty = float(panier_product.quantity) + qty
                self.panier_controller.update_product_quantity(self.panier.id, product_id, new_qty)
                self.refresh_panier()
        else:
            qty, ok = QInputDialog.getInt(self, "Quantité", f"Quantité pour {product.name} :", 1, 1, 1000, 1)
            if ok:
                self.panier_controller.add_product_to_panier(self.panier.id, product_id, qty, product.price_unit)
                self.refresh_panier()

    def toggle_catalog_mode(self):
        if self.catalog_mode == 'card':
            self.catalog_mode = 'list'
            self.switch_mode_btn.setText('🃏 Mode card')
        else:
            self.catalog_mode = 'card'
            self.switch_mode_btn.setText('🗂️ Mode liste')
        self.populate_catalog_with_products()

    def create_panier_section(self):
        panier_widget = QWidget()
        panier_layout = QVBoxLayout(panier_widget)

        panier_group = QGroupBox("🛒 Panier")
        panier_group_layout = QVBoxLayout(panier_group)

        # --- Sélection client en haut ---
        client_layout = QHBoxLayout()
        client_layout.addWidget(QLabel("Client :"))
        self.client_combo = QComboBox()
        self.client_combo.setMinimumWidth(180)
        self.client_combo.setEditable(True)
        self.client_combo.setPlaceholderText("Sélectionner ou rechercher client")
        self.client_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.client_combo.setMaxVisibleItems(10)
        self.client_combo.setStyleSheet("QComboBox { font-size: 12px; }")
        client_layout.addWidget(self.client_combo)
        self.add_client_btn = QPushButton("Ajouter client")
        client_layout.addWidget(self.add_client_btn)
        self.add_client_btn.clicked.connect(self.open_add_client_dialog)
        client_layout.addStretch()
        panier_layout.addLayout(client_layout)

        # Initialisation du combo client et recherche
        self.load_clients_for_combo()
        self.client_combo.lineEdit().textChanged.connect(self.on_client_search)

        self.panier_table = QTableWidget()
        self.panier_table.setColumnCount(5)
        self.panier_table.setHorizontalHeaderLabels(["Article", "Prix unit.", "Qté", "Sous-total", "Action"])
        panier_header = self.panier_table.horizontalHeader()
        panier_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        panier_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        panier_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        panier_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        panier_header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self.panier_table.setMaximumHeight(300)
        panier_group_layout.addWidget(self.panier_table)

        # --- Champ remise ---
        remise_layout = QHBoxLayout()
        remise_layout.addWidget(QLabel("Remise (€) :"))
        self.remise_input = QLineEdit()
        self.remise_input.setPlaceholderText("0.00")
        self.remise_input.setFixedWidth(80)
        self.remise_input.setText("0.00")
        self.remise_input.textChanged.connect(self.refresh_panier)
        remise_layout.addWidget(self.remise_input)
        remise_layout.addStretch()
        panier_group_layout.addLayout(remise_layout)

        # --- Total panier ---
        total_layout = QHBoxLayout()
        total_layout.addStretch()
        self.total_label = QLabel("Total : 0.00 €")
        self.total_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #27AE60;")
        total_layout.addWidget(self.total_label)
        panier_group_layout.addLayout(total_layout)

        panier_layout.addWidget(panier_group)

        # --- Options de paiement en bas ---
        paiement_group = QGroupBox("Options de paiement")
        paiement_layout = QHBoxLayout(paiement_group)
        self.paiement_espece_radio = QRadioButton("Espèce")
        self.paiement_banque_radio = QRadioButton("Banque")
        self.paiement_compte_radio = QRadioButton("Compte client")
        self.paiement_espece_radio.setChecked(True)
        paiement_layout.addWidget(self.paiement_espece_radio)
        paiement_layout.addWidget(self.paiement_banque_radio)
        paiement_layout.addWidget(self.paiement_compte_radio)
        paiement_layout.addStretch()
        panier_layout.addWidget(paiement_group)

        self.refresh_panier()
        return panier_widget

    def load_clients_for_combo(self, search_term=None):
        from ayanna_erp.modules.boutique.model.models import ShopClient
        session = self.panier_controller.db_manager.get_session()
        query = session.query(ShopClient)
        if search_term is not None and str(search_term).strip() != "":
            safe_text = str(search_term)
            query = query.filter(ShopClient.nom.ilike(':search_term')).params(search_term=f'%{safe_text}%')
        clients = query.order_by(ShopClient.nom.asc()).all()
        current_text = self.client_combo.currentText() if self.client_combo.isEditable() else None
        self.client_combo.clear()
        for client in clients:
            display = f"{client.nom} {client.prenom or ''} - {client.telephone or ''}"
            self.client_combo.addItem(display, client.id)
        if current_text:
            self.client_combo.setEditText(current_text)
        else:
            self.client_combo.setCurrentIndex(-1)

    def on_client_search(self, text):
        self.load_clients_for_combo(text)

    def open_add_client_dialog(self):
        from ayanna_erp.modules.boutique.view.client_index import ClientFormDialog
        dialog = ClientFormDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_clients_for_combo()


        self.panier_table = QTableWidget()
        self.panier_table.setColumnCount(5)
        self.panier_table.setHorizontalHeaderLabels(["Article", "Prix unit.", "Qté", "Sous-total", "Action"])
        panier_header = self.panier_table.horizontalHeader()
        panier_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        panier_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        panier_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        panier_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        panier_header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self.panier_table.setMaximumHeight(300)
        # Define panier_layout before using it
        panier_widget = QWidget()
        panier_layout = QVBoxLayout(panier_widget)

        panier_group = QGroupBox("🛒 Panier")
        panier_group_layout = QVBoxLayout()
        panier_group.setLayout(panier_group_layout)
        panier_group_layout.addWidget(self.panier_table)

        # --- Champ remise ---
        remise_layout = QHBoxLayout()
        remise_layout.addWidget(QLabel("Remise (€) :"))
        self.remise_input = QLineEdit()
        self.remise_input.setPlaceholderText("0.00")
        self.remise_input.setFixedWidth(80)
        self.remise_input.setText("0.00")
        self.remise_input.textChanged.connect(self.refresh_panier)
        remise_layout.addWidget(self.remise_input)
        remise_layout.addStretch()
        panier_group_layout.addLayout(remise_layout)

        # --- Total panier ---
        total_layout = QHBoxLayout()
        total_layout.addStretch()
        self.total_label = QLabel("Total : 0.00 €")
        self.total_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #27AE60;")
        total_layout.addWidget(self.total_label)
        panier_group_layout.addLayout(total_layout)

        panier_layout.addWidget(panier_group)

        # --- Options de paiement en bas ---
        paiement_group = QGroupBox("Options de paiement")
        paiement_layout = QHBoxLayout(paiement_group)
        self.paiement_espece_radio = QRadioButton("Espèce")
        self.paiement_banque_radio = QRadioButton("Banque")
        self.paiement_compte_radio = QRadioButton("Compte client")
        self.paiement_espece_radio.setChecked(True)
        paiement_layout.addWidget(self.paiement_espece_radio)
        paiement_layout.addWidget(self.paiement_banque_radio)
        paiement_layout.addWidget(self.paiement_compte_radio)
        paiement_layout.addStretch()
        panier_layout.addWidget(paiement_group)

        self.refresh_panier()
        return panier_widget

    def refresh_panier(self):
        if not hasattr(self, "panier_table") or self.panier_table is None:
            return
        try:
            session = self.panier_controller.db_manager.get_session()
            panier_obj = session.get(type(self.panier), self.panier.id)
            products = panier_obj.products if panier_obj else []

            self.panier_table.setRowCount(len(products))
            total = 0.0
            for row, panier_product in enumerate(products):
                # Récupérer le nom du produit
                product_name = ""
                if hasattr(panier_product, "product_id"):
                    from ayanna_erp.modules.core.models import CoreProduct
                    prod = session.get(CoreProduct, panier_product.product_id)
                    product_name = prod.name if prod and hasattr(prod, "name") else str(panier_product.product_id)
                else:
                    product_name = str(panier_product.product_id)

                self.panier_table.setItem(row, 0, QTableWidgetItem(product_name))
                self.panier_table.setItem(row, 1, QTableWidgetItem(str(panier_product.price_unit)))
                self.panier_table.setItem(row, 2, QTableWidgetItem(str(panier_product.quantity)))
                self.panier_table.setItem(row, 3, QTableWidgetItem(str(panier_product.total_price)))

                total += float(panier_product.total_price)

                remove_btn = QPushButton("🗑️")
                remove_btn.clicked.connect(lambda checked, pid=panier_product.product_id: self.remove_product_from_panier(pid))
                self.panier_table.setCellWidget(row, 4, remove_btn)

            # Calculer le total avec remise
            try:
                remise = float(self.remise_input.text()) if hasattr(self, "remise_input") else 0.0
            except Exception:
                remise = 0.0
            total_final = max(total - remise, 0.0)
            if hasattr(self, "total_label"):
                self.total_label.setText(f"Total : {total_final:.2f} €")
        except RuntimeError:
            # Le widget a été supprimé, on ignore l’appel
            pass

    def remove_product_from_panier(self, product_id):
        self.panier_controller.remove_product_from_panier(self.panier.id, product_id)
        self.refresh_panier()

