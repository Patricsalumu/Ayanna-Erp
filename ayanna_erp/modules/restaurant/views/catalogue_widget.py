from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QFrame, QLabel, QPushButton, QLineEdit, QSpinBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QComboBox, QDialog,
    QSplitter, QTextEdit, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap


from ayanna_erp.modules.restaurant.controllers.catalogue_controller import CatalogueController
from ayanna_erp.modules.restaurant.controllers.vente_controller import VenteController
from ayanna_erp.database.database_manager import get_database_manager, User
from ayanna_erp.database.database_manager import Entreprise
import os


class CatalogueWidget(QWidget):
    """Widget catalogue + panier minimal pour ouverture depuis une table.

    Comportement:
    - Affiche les produits (via CoreProductController)
    - Permet d'ajouter au panier du restaurant (via CatalogueController / VenteController)
    - Affiche le panier à droite avec possibilité de sélectionner une ligne
      puis d'ouvrir un pavé numérique pour incrémenter/décrémenter/supprimer
    """

    cart_updated = pyqtSignal()

    def __init__(self, table_id: int, entreprise_id: int = 1, pos_id: int = 1, current_user=None, parent=None):
        super().__init__(parent)
        self.table_id = table_id
        self.entreprise_id = entreprise_id
        self.pos_id = pos_id
        self.current_user = current_user

        self.controller = CatalogueController(entreprise_id=entreprise_id, pos_id=pos_id)
        self.vente_ctrl = VenteController(entreprise_id=entreprise_id)

        # state
        self.panier = None
        self.selected_line_id = None
        self.selected_cart_row = None
        # keypad buffer (string)
        self._keypad_buffer = ""
        # finish initialization
        self.__post_init_load()

    # initialize UI and ensure panier before loading products so badges are correct
    def __post_init_load(self):
        # helper called after __init__ to finish setup
        self.init_ui()
        self.ensure_panier()
        self.load_products()

    def init_ui(self):
        main = QVBoxLayout(self)
        header_h = QHBoxLayout()
        uid = getattr(self.current_user, 'id', None) if getattr(self, 'current_user', None) else None
        # essayer d'obtenir le numéro de la table (champ `number`) plutôt que l'id
        table_display = str(self.table_id)
        try:
            db = get_database_manager()
            session = db.get_session()
            from ayanna_erp.modules.restaurant.models.restaurant import RestauTable
            tbl = session.query(RestauTable).filter_by(id=self.table_id).first()
            if tbl and getattr(tbl, 'number', None):
                table_display = str(getattr(tbl, 'number'))
            session.close()
        except Exception:
            # fallback: conserver l'id si récupération impossible
            pass

        header_label = QLabel(f"Catalogue - Table {table_display}" + (f" — User {uid}" if uid else ""))
        header_label.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        header_h.addWidget(header_label)
        header_h.addStretch()

        # Serveuse selection
        # Client selection
        self.client_combo = QComboBox()
        try:
            self._populate_client_combo()
        except Exception:
            pass
        header_h.addWidget(QLabel('Client:'))
        header_h.addWidget(self.client_combo)
        try:
            self.client_combo.currentIndexChanged.connect(self._on_client_selected)
        except Exception:
            pass

        self.serveuse_combo = QComboBox()
        # populate options
        try:
            self._populate_serveuse_combo()
        except Exception:
            pass
        header_h.addWidget(QLabel("Serveuse:"))
        header_h.addWidget(self.serveuse_combo)
        try:
            self.serveuse_combo.currentIndexChanged.connect(self._on_serveuse_selected)
        except Exception:
            pass
        main.addLayout(header_h)

        # Category filter buttons
        self.category_bar = QHBoxLayout()
        main.addLayout(self.category_bar)
        self.selected_category = None
        try:
            self._populate_category_buttons()
        except Exception:
            pass

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main.addWidget(splitter)

        # Left: products
        left = QWidget()
        left_l = QVBoxLayout(left)
        search_h = QHBoxLayout()
        self.search_edit = QLineEdit(); self.search_edit.setPlaceholderText('Rechercher...')
        self.search_edit.textChanged.connect(self.load_products)
        search_h.addWidget(self.search_edit)
        left_l.addLayout(search_h)

        self.products_area = QScrollArea(); self.products_area.setWidgetResizable(True)
        self.products_container = QWidget()
        self.products_layout = QGridLayout(self.products_container)
        self.products_layout.setSpacing(8)
        self.products_area.setWidget(self.products_container)
        left_l.addWidget(self.products_area)
        splitter.addWidget(left)

        # Right: cart
        right = QWidget()
        right_l = QVBoxLayout(right)
        right_l.addWidget(QLabel('Panier'))
        # Columns: hidden Ligne ID, Produit, Qté, Prix, Total
        self.cart_table = QTableWidget(0, 5)
        self.cart_table.setHorizontalHeaderLabels(['Ligne ID', 'Produit', 'Qté', 'Prix', 'Total'])
        self.cart_table.horizontalHeader().setSectionHidden(0, True)
        self.cart_table.horizontalHeader().setStretchLastSection(True)
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.cellClicked.connect(self.on_cart_row_clicked)
        right_l.addWidget(self.cart_table)

        # Configure header resize modes so we can drive widths proportionally
        try:
            header = self.cart_table.horizontalHeader()
            # set fixed resize mode; we'll set widths based on proportions in resizeEvent
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        except Exception:
            pass

        # Numeric pad and actions
        pad = QHBoxLayout()
        self.qty_spin = QSpinBox(); self.qty_spin.setMinimum(1); self.qty_spin.setMaximum(9999)
        pad.addWidget(self.qty_spin)
        # apply qty when editing finished (focus lost)
        try:
            self.qty_spin.editingFinished.connect(self._apply_qty_from_spin)
        except Exception:
            pass
        inc_btn = QPushButton('+'); dec_btn = QPushButton('-'); del_btn = QPushButton('Suppr')
        inc_btn.clicked.connect(self.increment_selected_qty)
        dec_btn.clicked.connect(self.decrement_selected_qty)
        del_btn.clicked.connect(self.delete_selected_line)
        pad.addWidget(inc_btn); pad.addWidget(dec_btn); pad.addWidget(del_btn)
        right_l.addLayout(pad)

        # (numeric keypad removed - we keep qty_spin + +/-/Suppr controls)

        # Note du panier (hauteur réduite) + bouton sur la même ligne
        note_h = QHBoxLayout()
        note_h.setSpacing(8)
        note_h.addWidget(QLabel('Note'))
        self.note_edit = QTextEdit()
        self.note_edit.setFixedHeight(48)
        # make the note edit expand and occupy available horizontal space
        self.note_edit.setSizePolicy(self.note_edit.sizePolicy().horizontalPolicy(), self.note_edit.sizePolicy().verticalPolicy())
        note_h.addWidget(self.note_edit, stretch=1)
        save_note_btn = QPushButton('Enregistrer')
        save_note_btn.setFixedHeight(36)
        save_note_btn.setFixedWidth(120)
        save_note_btn.clicked.connect(self.save_note)
        # style the button to match primary action
        save_note_btn.setStyleSheet('background-color:#1976D2; color:white; font-weight:600;')
        note_h.addWidget(save_note_btn)
        right_l.addLayout(note_h)

        # Remise (montant) et label Total
        totals_h = QHBoxLayout()
        self.remise_edit = QLineEdit()
        self.remise_edit.setPlaceholderText('Remise (montant)')
        self.remise_edit.setFixedWidth(120)
        try:
            self.remise_edit.editingFinished.connect(self._on_remise_changed)
        except Exception:
            pass
        totals_h.addWidget(QLabel('Remise:'))
        totals_h.addWidget(self.remise_edit)
        totals_h.addStretch()
        self.total_label = QLabel('Total: 0 F')
        totals_h.addWidget(self.total_label)
        right_l.addLayout(totals_h)

        # Action buttons: Annuler, Payer, Addition
        actions_h = QHBoxLayout()
        self.annuler_btn = QPushButton('Annuler')
        self.payer_btn = QPushButton('Payer')
        self.addition_btn = QPushButton('Addition')
        self.annuler_btn.setStyleSheet('background-color:#e53935; color:white;')
        self.payer_btn.setStyleSheet('background-color:#28a745; color:white;')
        self.addition_btn.setStyleSheet('background-color:#1976D2; color:white;')
        actions_h.addWidget(self.annuler_btn)
        actions_h.addWidget(self.payer_btn)
        actions_h.addWidget(self.addition_btn)
        right_l.addLayout(actions_h)

        # Connect actions
        try:
            self.annuler_btn.clicked.connect(self._on_annuler_clicked)
        except Exception:
            pass
        try:
            # open payment dialog
            self.payer_btn.clicked.connect(self._on_payer_dialog)
        except Exception:
            pass
        try:
            self.addition_btn.clicked.connect(self._on_addition_clicked)
        except Exception:
            pass

        # Finalize
        splitter.addWidget(right)
        # enlarge product area and reduce cart area
        splitter.setSizes([1000, 200])
        # apply initial proportional widths for cart columns
        try:
            self._apply_cart_column_proportions()
        except Exception:
            pass

    def ensure_panier(self):
        p = self.vente_ctrl.get_open_panier_for_table(self.table_id)
        if not p:
            # récupérer la serveuse sélectionnée si présente
            serveuse_id = None
            try:
                serveuse_id = int(self.serveuse_combo.currentData() or 0) if hasattr(self, 'serveuse_combo') else None
            except Exception:
                serveuse_id = None
            p = self.controller.get_or_create_panier_for_table(self.table_id, user_id=getattr(self.current_user, 'id', None), serveuse_id=serveuse_id)
        self.panier = p
        # positionner les combos client/serveuse selon le panier chargé
        try:
            # block signals to avoid re-persisting the same values
            try:
                self.client_combo.blockSignals(True)
            except Exception:
                pass
            try:
                self.serveuse_combo.blockSignals(True)
            except Exception:
                pass

            # select client if present
            try:
                cid = getattr(self.panier, 'client_id', None)
                if cid:
                    idx = self.client_combo.findData(int(cid))
                    if idx >= 0:
                        self.client_combo.setCurrentIndex(idx)
                    else:
                        # fallback: ensure first placeholder selected
                        self.client_combo.setCurrentIndex(0)
                else:
                    self.client_combo.setCurrentIndex(0)
            except Exception:
                pass

            # select serveuse if present
            try:
                sid = getattr(self.panier, 'serveuse_id', None)
                if sid:
                    idx = self.serveuse_combo.findData(int(sid))
                    if idx >= 0:
                        self.serveuse_combo.setCurrentIndex(idx)
                    else:
                        self.serveuse_combo.setCurrentIndex(0)
                else:
                    self.serveuse_combo.setCurrentIndex(0)
            except Exception:
                pass

        finally:
            try:
                self.client_combo.blockSignals(False)
            except Exception:
                pass
            try:
                self.serveuse_combo.blockSignals(False)
            except Exception:
                pass

        self.refresh_cart()
        # charger la note si présente
        try:
            if self.panier:
                session = self.controller.db.get_session()
                from ayanna_erp.modules.restaurant.models.restaurant import RestauPanier
                obj = session.query(RestauPanier).filter_by(id=self.panier.id).first()
                if obj and getattr(obj, 'notes', None):
                    try:
                        self.note_edit.setPlainText(str(obj.notes))
                    except Exception:
                        pass
                # populate remise field and update total label
                try:
                    r = getattr(obj, 'remise_amount', 0.0) or 0.0
                    try:
                        self.remise_edit.setText(str(int(r)) if r else '')
                    except Exception:
                        self.remise_edit.setText(str(r))
                except Exception:
                    pass
                session.close()
        except Exception:
            pass

    def load_products(self):
        search = self.search_edit.text() if hasattr(self, 'search_edit') else None
        cat_id = self.selected_category
        products = self.controller.list_products(search=search, category_id=cat_id)
        # clear
        for i in reversed(range(self.products_layout.count())):
            it = self.products_layout.itemAt(i)
            if it:
                w = it.widget()
                if w:
                    w.setParent(None)

        cols = 6
        for idx, prod in enumerate(products):
            card = self.create_product_card(prod)
            r = idx // cols; c = idx % cols
            self.products_layout.addWidget(card, r, c)

        # ensure some stretch so cards align top
        self.products_layout.setRowStretch((len(products) // cols) + 1, 1)

    def create_product_card(self, product):
        """
        Crée une carte produit visuellement proche du style Ayanna Cloud :
        - Fond blanc, coins arrondis, bordure colorée selon la catégorie
        - Image centrée avec fond clair
        - Nom du produit centré
        - Badge quantité/commande en haut à droite
        """
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QWidget, QMessageBox
        from PyQt6.QtGui import QPixmap
        import os

        # ---- Déterminer la couleur de bordure selon la catégorie ----
        cat_color_map = {
            'Bière': '#F44336',
            'Vin': '#9C27B0',
            'Sucré': '#4CAF50',
            'Whisky': '#3F51B5',
            'Autres': '#FFEB3B',
            'Champagne': '#FF4081',
            'Cuisine': '#00BCD4'
        }
        category = getattr(product, 'category_name', 'Autres')
        border_color = cat_color_map.get(category, '#E0E0E0')

        # ---- Créer le cadre principal ----
        card = QFrame()
        card.setFixedSize(110, 135)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 10px;
            }}
            QFrame:hover {{
                border-color: #1976D2;
                box-shadow: 0 0 8px rgba(0,0,0,0.1);
                background-color: #F8FAFF;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # ---- Ligne du haut (badge) ----
        top_row = QWidget()
        top_layout = QHBoxLayout(top_row)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addStretch()

        badge = QLabel('')
        badge.setObjectName('cart_badge')
        badge.setFixedSize(24, 18)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet("""
            background-color: #1976D2;
            color: white;
            border-radius: 9px;
            font-size: 10px;
            font-weight: bold;
            padding: 0px 4px;
        """)
        # show/hide badge according to current cart quantity for this product
        try:
            pid = getattr(product, 'id', None)
            qty = int(self._get_cart_quantity_for_product(pid) or 0)
            if qty and qty > 0:
                badge.setText(str(int(qty)))
                badge.show()
            else:
                badge.hide()
        except Exception:
            # safe fallback: hide badge
            badge.hide()
        top_layout.addWidget(badge)
        layout.addWidget(top_row)

        # ---- Image produit ----
        image_label = QLabel()
        image_label.setFixedSize(80, 70)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setStyleSheet("""
            background-color: #F9FAFB;
            border: 1px solid #E0E0E0;
            border-radius: 6px;
        """)

        image_loaded = False
        if hasattr(product, 'image') and product.image:
            try:
                image_filename = product.image.strip()
                if os.path.isabs(image_filename):
                    full_path = image_filename
                else:
                    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                    full_path = os.path.join(base_path, image_filename.replace("/", os.sep))
                if os.path.exists(full_path):
                    pixmap = QPixmap(full_path)
                    if not pixmap.isNull():
                        scaled = pixmap.scaled(image_label.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation)
                        image_label.setPixmap(scaled)
                        image_loaded = True
            except Exception as e:
                print("Erreur image:", e)

        if not image_loaded:
            image_label.setText("🧾")
            image_label.setStyleSheet("""
                background-color: #F8F9FA;
                border: 2px dashed #DEE2E6;
                color: #9E9E9E;
                border-radius: 6px;
                font-size: 18px;
            """)

        layout.addWidget(image_label, 0, Qt.AlignmentFlag.AlignHCenter)

        # ---- Nom du produit ----
        name = getattr(product, 'name', 'Produit')
        # keep the raw product name only (no counters appended)
        name_label = QLabel(name if len(name) < 20 else name[:18] + '…')
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet("""
            color: #212529;
            font-weight: 600;
            font-size: 12px;
        """)
        layout.addWidget(name_label)

        # ---- Info bulle ----
        price = float(getattr(product, 'price_unit', getattr(product, 'price', 0)))
        card.setToolTip(f"{name}\nPrix: {int(price)} {self._get_currency()}")

        # ---- Clic sur la carte ----
        def _on_click(prod_id=getattr(product, 'id', None)):
            try:
                self.add_product(prod_id)
                self._update_badges()
            except Exception as e:
                QMessageBox.critical(self, 'Erreur', str(e))

        card.mousePressEvent = lambda event: _on_click()
        # store product id on card so badges can be updated in-place
        try:
            card.setProperty('product_id', getattr(product, 'id', None))
        except Exception:
            pass

        return card

    def _get_cart_quantity_for_product(self, product_id):
        if not self.panier:
            return 0
        try:
            items = self.controller.list_cart_items(self.panier.id)
            total = 0
            for it in items:
                if getattr(it, 'product_id', None) == product_id:
                    total += float(getattr(it, 'quantity', 0))
            return total
        except Exception:
            return 0

    def _update_badges(self):
        # iterate product cards and update badge labels in-place (avoid full reload)
        try:
            for i in range(self.products_layout.count()):
                it = self.products_layout.itemAt(i)
                if not it:
                    continue
                w = it.widget()
                if not w:
                    continue
                badge = w.findChild(QLabel, 'cart_badge')
                if not badge:
                    continue
                try:
                    pid = w.property('product_id') if hasattr(w, 'property') else None
                    qty = int(self._get_cart_quantity_for_product(pid) or 0)
                    if qty and qty > 0:
                        badge.setText(str(int(qty)))
                        badge.show()
                    else:
                        badge.hide()
                except Exception:
                    try:
                        badge.hide()
                    except Exception:
                        pass
        except Exception:
            # fallback: if anything goes wrong, do a full reload
            try:
                self.load_products()
            except Exception:
                pass

    def _populate_category_buttons(self):
        # Clear existing buttons
        while self.category_bar.count():
            it = self.category_bar.takeAt(0)
            if it and it.widget():
                it.widget().deleteLater()

        # 'Tous' button
        all_btn = QPushButton('Tous')
        all_btn.setCheckable(True)
        all_btn.setChecked(True if self.selected_category is None else False)
        all_btn.clicked.connect(lambda _: self._on_category_selected(None, all_btn))
        self.category_bar.addWidget(all_btn)

        cats = []
        try:
            cats = self.controller.list_categories() or []
        except Exception:
            cats = []

        for c in cats:
            btn = QPushButton(getattr(c, 'name', 'Cat'))
            btn.setCheckable(True)
            btn.clicked.connect(lambda _checked, cid=getattr(c, 'id', None), b=btn: self._on_category_selected(cid, b))
            self.category_bar.addWidget(btn)

        self.category_bar.addStretch()

    def _on_category_selected(self, category_id, button):
        # Uncheck other buttons in the category bar
        for i in range(self.category_bar.count()):
            it = self.category_bar.itemAt(i)
            if it and it.widget() and isinstance(it.widget(), QPushButton):
                w = it.widget()
                if w is not button:
                    w.setChecked(False)

        # Toggle selection
        if self.selected_category == category_id:
            # deselect
            self.selected_category = None
            button.setChecked(False)
        else:
            self.selected_category = category_id
            button.setChecked(True)

        # reload products with new filter
        self.load_products()

    def add_product(self, product_id: int):
        try:
            prod = self.controller.get_product(product_id)
            if not prod:
                QMessageBox.warning(self, 'Produit introuvable', 'Le produit est introuvable en base')
                return
            # ensure panier
            self.ensure_panier()
            # add with default qty 1 and product price
            price = float(getattr(prod, 'price_unit', getattr(prod, 'price', 0)))
            self.controller.add_product_to_panier(self.panier.id, product_id, 1, price)
            self.refresh_cart()
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Impossible d'ajouter le produit: {e}")

    def refresh_cart(self):
        if not self.panier:
            return
        items = self.controller.list_cart_items(self.panier.id)
        # remember selected line id
        sel_id = getattr(self, 'selected_line_id', None)
        self.cart_table.setRowCount(0)
        for i, it in enumerate(items):
            self.cart_table.insertRow(i)
            id_item = QTableWidgetItem(str(getattr(it, 'id')))
            id_item.setData(Qt.ItemDataRole.UserRole, getattr(it, 'id'))
            self.cart_table.setItem(i, 0, id_item)
            # show product name instead of product_id
            try:
                pid = getattr(it, 'product_id')
                prod = None
                try:
                    prod = self.controller.get_product(pid)
                except Exception:
                    prod = None
                pname = str(getattr(prod, 'name', pid)) if prod else str(pid)
            except Exception:
                pname = str(getattr(it, 'product_id', ''))
            name_item = QTableWidgetItem(pname)
            self.cart_table.setItem(i, 1, name_item)
            qty_item = QTableWidgetItem(str(getattr(it, 'quantity')))
            self.cart_table.setItem(i, 2, qty_item)
            # price per unit
            price_item = QTableWidgetItem(str(getattr(it, 'price', 0.0)))
            self.cart_table.setItem(i, 3, price_item)
            total_item = QTableWidgetItem(str(getattr(it, 'total')))
            self.cart_table.setItem(i, 4, total_item)

        # restore selection if possible
        if sel_id:
            found = False
            for row in range(self.cart_table.rowCount()):
                item = self.cart_table.item(row, 0)
                if item and int(item.text()) == int(sel_id):
                    self.selected_cart_row = row
                    self.selected_line_id = sel_id
                    self.cart_table.selectRow(row)
                    # set qty spin to the row's qty
                    try:
                        qv = int(self.cart_table.item(row, 2).text())
                        self.qty_spin.setValue(qv)
                    except Exception:
                        pass
                    self.cart_table.setFocus()
                    found = True
                    break
            if not found:
                self.selected_cart_row = None
                self.selected_line_id = None

        # update total label after refreshing rows
        try:
            self._update_total_label()
        except Exception:
            pass

    def on_cart_row_clicked(self, row, col):
        self.selected_cart_row = row
        pid_item = self.cart_table.item(row, 0)
        if pid_item:
            lp_id = int(pid_item.text())
            # remember selected line id so refresh keeps selection/focus
            self.selected_line_id = lp_id
            qty_item = self.cart_table.item(row, 2)
            try:
                q = int(qty_item.text())
            except Exception:
                q = 1
            self.qty_spin.setValue(q)

    def increment_selected_qty(self):
        if self.selected_cart_row is None:
            return
        row = self.selected_cart_row
        lp_id = int(self.cart_table.item(row, 0).text())
        current = int(self.qty_spin.value())
        newq = current + 1
        try:
            self.controller.update_product_quantity(self.panier.id, lp_id, newq)
            self.refresh_cart()
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', str(e))

    def decrement_selected_qty(self):
        if self.selected_cart_row is None:
            return
        row = self.selected_cart_row
        lp_id = int(self.cart_table.item(row, 0).text())
        current = int(self.qty_spin.value())
        newq = max(1, current - 1)
        try:
            self.controller.update_product_quantity(self.panier.id, lp_id, newq)
            self.refresh_cart()
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', str(e))

    def delete_selected_line(self):
        if self.selected_cart_row is None:
            return
        row = self.selected_cart_row
        lp_id = int(self.cart_table.item(row, 0).text())
        try:
            self.controller.remove_product_from_panier(self.panier.id, lp_id)
            self.selected_cart_row = None
            self.refresh_cart()
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', str(e))

    def _apply_qty_from_spin(self):
        """Apply the qty value from the spinbox to the selected cart line when editing is finished."""
        if self.selected_cart_row is None:
            return
        try:
            lp_id = int(self.cart_table.item(self.selected_cart_row, 0).text())
            newq = int(self.qty_spin.value())
            # remember selected_line_id so refresh preserves focus
            self.selected_line_id = lp_id
            self.controller.update_product_quantity(self.panier.id, lp_id, newq)
            self.refresh_cart()
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Impossible d'appliquer la quantité: {e}")

    def _on_client_selected(self, index):
        """Persist selected client into the panier as soon as selection changes."""
        if not self.panier:
            return
        try:
            client_id = int(self.client_combo.currentData() or 0)
            # treat 0 as no client
            client_val = client_id if client_id else None
            try:
                self.controller.set_panier_client(self.panier.id, client_val)
            except Exception:
                # fallback: try via vente_ctrl directly
                session = self.vente_ctrl.db.get_session()
                from ayanna_erp.modules.restaurant.models.restaurant import RestauPanier
                p = session.query(RestauPanier).filter_by(id=self.panier.id).first()
                if p:
                    p.client_id = client_val
                    session.commit()
                session.close()
            # update local cached panier if possible
            try:
                self.panier.client_id = client_val
            except Exception:
                pass
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Impossible d'enregistrer le client: {e}")

    def _on_serveuse_selected(self, index):
        """Persist selected serveuse into the panier as soon as selection changes."""
        if not self.panier:
            return
        try:
            serveuse_id = int(self.serveuse_combo.currentData() or 0)
            serveuse_val = serveuse_id if serveuse_id else None
            try:
                self.controller.set_panier_serveuse(self.panier.id, serveuse_val)
            except Exception:
                session = self.vente_ctrl.db.get_session()
                from ayanna_erp.modules.restaurant.models.restaurant import RestauPanier
                p = session.query(RestauPanier).filter_by(id=self.panier.id).first()
                if p:
                    p.serveuse_id = serveuse_val
                    session.commit()
                session.close()
            try:
                self.panier.serveuse_id = serveuse_val
            except Exception:
                pass
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Impossible d'enregistrer la serveuse: {e}")

    # -----------------------
    # Keypad helpers
    # -----------------------
    def keypad_digit(self, digit: str):
        try:
            if digit.isdigit():
                if self._keypad_buffer == '0':
                    self._keypad_buffer = digit
                else:
                    self._keypad_buffer += digit
                try:
                    val = int(self._keypad_buffer)
                    self.qty_spin.setValue(max(1, val))
                except Exception:
                    pass
        except Exception:
            pass

    def keypad_clear(self):
        self._keypad_buffer = ""
        self.qty_spin.setValue(1)

    def keypad_apply(self):
        if self.selected_cart_row is None:
            QMessageBox.information(self, 'Info', "Sélectionnez une ligne du panier d'abord")
            return
        try:
            newq = int(self.qty_spin.value())
            lp_id = int(self.cart_table.item(self.selected_cart_row, 0).text())
            self.controller.update_product_quantity(self.panier.id, lp_id, newq)
            self.refresh_cart()
            # reset buffer
            self._keypad_buffer = ""
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', str(e))

    def save_note(self):
        if not self.panier:
            QMessageBox.information(self, 'Info', 'Aucun panier actif')
            return
        note = self.note_edit.toPlainText()
        try:
            # use new API name set_panier_notes
            self.controller.set_panier_notes(self.panier.id, note)
            QMessageBox.information(self, 'Succès', 'Note enregistrée')
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Impossible d'enregistrer la note: {e}")

    # -----------------------
    # Action button handlers
    # -----------------------
    def _on_annuler_clicked(self):
        if not self.panier:
            QMessageBox.information(self, 'Info', 'Aucun panier actif')
            return
        ok = QMessageBox.question(self, 'Annuler la commande', 'Confirmez-vous l\'annulation de cette commande ?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ok != QMessageBox.StandardButton.Yes:
            return
        try:
            # If panier is empty -> delete it (free the table) and return to plan view
            items = []
            try:
                items = self.controller.list_cart_items(self.panier.id) or []
            except Exception:
                items = []

            session = self.vente_ctrl.db.get_session()
            from ayanna_erp.modules.restaurant.models.restaurant import RestauPanier
            p = session.query(RestauPanier).filter_by(id=self.panier.id).first()
            if p:
                if not items:
                    # delete empty panier -> free table
                    try:
                        session.delete(p)
                        session.commit()
                    except Exception:
                        session.rollback()
                        raise
                    finally:
                        session.close()
                    QMessageBox.information(self, 'Succès', 'Panier vide supprimé, table libérée')
                    # return to plan view if possible
                    parent = self.parent()
                    while parent is not None and not hasattr(parent, 'show_plan_view'):
                        parent = parent.parent()
                    try:
                        if parent and hasattr(parent, 'show_plan_view'):
                            parent.show_plan_view()
                    except Exception:
                        pass
                    return
                else:
                    # mark panier as cancelled
                    p.status = 'annule'
                    session.commit()
            session.close()
            QMessageBox.information(self, 'Succès', 'Commande annulée')
            # After cancelling, go back to plan view
            parent = self.parent()
            while parent is not None and not hasattr(parent, 'show_plan_view'):
                parent = parent.parent()
            try:
                if parent and hasattr(parent, 'show_plan_view'):
                    parent.show_plan_view()
            except Exception:
                pass
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Impossible d'annuler la commande: {e}")

    def _on_payer_clicked(self):
        # kept for backward compatibility but payment now handled in dialog
        return self._on_payer_dialog()

    def _on_payer_dialog(self):
        """Open a payment dialog where user saisit le montant reçu.
        - default montant = total du panier
        - if montant < total => enregistrer paiement avec méthode 'Crédit'
        - n'accepte pas montant > total
        """
        if not self.panier:
            QMessageBox.information(self, 'Info', 'Aucun panier actif')
            return
        try:
            # refresh panier from DB to get latest subtotal/remise/total_final
            p = self.vente_ctrl.get_panier(self.panier.id)
            subtotal = float(getattr(p, 'subtotal', 0.0) or 0.0)
            remise = float(getattr(p, 'remise_amount', 0.0) or 0.0)
            total_final = float(getattr(p, 'total_final', subtotal - remise))

            dlg = QDialog(self)
            dlg.setWindowTitle('Paiement')
            dlg.setMinimumWidth(380)
            dlg_l = QVBoxLayout(dlg)
            # dialog styling
            dlg.setStyleSheet('''
                QLabel { font-size:13px; }
                QPushButton { padding:6px 10px; border-radius:6px; }
                QPushButton#confirm_btn { background-color: #28a745; color: white; font-weight:600; }
                QPushButton#cancel_btn { background-color: #9e9e9e; color: white; }
            ''')

            # Summary
            try:
                tbl_display = str(getattr(self.table_id, 'number', self.table_id))
            except Exception:
                tbl_display = str(self.table_id)
            client_name = '---'
            try:
                if getattr(p, 'client_id', None):
                    # try to lookup client name
                    db = get_database_manager()
                    session = db.get_session()
                    from ayanna_erp.modules.boutique.model.models import ShopClient
                    c = session.query(ShopClient).filter_by(id=p.client_id).first()
                    if c:
                        client_name = (getattr(c, 'nom', '') or '') + ' ' + (getattr(c, 'prenom', '') or '')
                    session.close()
            except Exception:
                pass
            serveuse_name = '---'
            try:
                if getattr(p, 'serveuse_id', None):
                    db = get_database_manager()
                    session = db.get_session()
                    from ayanna_erp.database.database_manager import User as DBUser
                    u = session.query(DBUser).filter_by(id=p.serveuse_id).first()
                    if u:
                        serveuse_name = getattr(u, 'name', str(getattr(u, 'email', '')))
                    session.close()
            except Exception:
                pass

            # Nicely formatted summary using a frame and form layout
            summary_frame = QFrame()
            summary_frame.setStyleSheet('QFrame { border: 1px solid #e0e0e0; border-radius:6px; padding:8px; background:#fafafa }')
            from PyQt6.QtWidgets import QFormLayout
            form = QFormLayout(summary_frame)
            form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
            form.addRow(QLabel('Table:'), QLabel(str(tbl_display)))
            form.addRow(QLabel('Client:'), QLabel(client_name))
            form.addRow(QLabel('Serveuse:'), QLabel(serveuse_name))
            form.addRow(QLabel('Sous-total:'), QLabel(f"{int(subtotal)} {self._get_currency()}"))
            form.addRow(QLabel('Remise:'), QLabel(f"{int(remise)} {self._get_currency()}"))
            form.addRow(QLabel('<b>Total à payer:</b>'), QLabel(f"<b>{int(total_final)} {self._get_currency()}</b>"))
            dlg_l.addWidget(summary_frame)

            # Amount received input (with change/remainder label)
            amt_h = QHBoxLayout()
            amt_h.setSpacing(8)
            amt_h.addWidget(QLabel('Montant reçu:'))
            amt_input = QDoubleSpinBox()
            amt_input.setPrefix('')
            amt_input.setSuffix(f' {self._get_currency()}')
            amt_input.setDecimals(2)
            amt_input.setMinimum(0.0)
            # allow entering an amount greater than total so we can compute monnaie
            try:
                amt_input.setMaximum(max(total_final * 10, total_final + 10000))
            except Exception:
                amt_input.setMaximum(1e9)
            amt_input.setValue(total_final)
            amt_input.setFixedWidth(160)
            amt_h.addWidget(amt_input)
            change_lbl = QLabel('')
            change_lbl.setStyleSheet('font-weight:600; color:#333;')
            amt_h.addWidget(change_lbl)
            amt_h.addStretch()
            dlg_l.addLayout(amt_h)

            # Buttons
            btns_h = QHBoxLayout()
            confirm_btn = QPushButton('Enregistrer le paiement')
            confirm_btn.setObjectName('confirm_btn')
            cancel_btn = QPushButton('Annuler')
            cancel_btn.setObjectName('cancel_btn')
            btns_h.addStretch()
            btns_h.addWidget(cancel_btn)
            btns_h.addWidget(confirm_btn)
            dlg_l.addLayout(btns_h)

            def do_cancel():
                dlg.reject()

            def update_change_label(val=None):
                try:
                    v = float(amt_input.value()) if val is None else float(val)
                    if v >= total_final:
                        monnaie = v - total_final
                        change_lbl.setText(f"Monnaie: {int(monnaie)} {self._get_currency()}")
                    else:
                        reste = total_final - v
                        change_lbl.setText(f"Reste: {int(reste)} {self._get_currency()}")
                except Exception:
                    change_lbl.setText('')

            # update label initially
            try:
                update_change_label()
            except Exception:
                pass

            amt_input.valueChanged.connect(update_change_label)

            def do_confirm():
                amt = float(amt_input.value())
                try:
                    if amt >= total_final:
                        # record payment for the total due and compute monnaie to give back
                        pay_amount = float(total_final)
                        method = 'Espèces'
                        self.vente_ctrl.add_payment(self.panier.id, pay_amount, method, user_id=getattr(self.current_user, 'id', None))
                        monnaie = amt - total_final
                        QMessageBox.information(dlg, 'Succès', f'Paiement de {int(pay_amount)} {self._get_currency()} enregistré ({method}). Monnaie: {int(monnaie)} {self._get_currency()}')
                    else:
                        # partial payment -> credit
                        pay_amount = float(amt)
                        method = 'Crédit'
                        self.vente_ctrl.add_payment(self.panier.id, pay_amount, method, user_id=getattr(self.current_user, 'id', None))
                        reste = total_final - pay_amount
                        QMessageBox.information(dlg, 'Succès', f'Paiement partiel de {int(pay_amount)} {self._get_currency()} enregistré ({method}). Reste: {int(reste)} {self._get_currency()}')
                    # --- Nouvel ajout: fermer le panier même en cas de paiement partiel ---
                    # payment status is handled by VenteController.add_payment (payment_method)
                    # after payment, if panier has no products -> delete it and return to plan view
                    try:
                        items_after = self.controller.list_cart_items(self.panier.id) or []
                        if not items_after:
                            # delete empty panier -> free table
                            session = self.vente_ctrl.db.get_session()
                            from ayanna_erp.modules.restaurant.models.restaurant import RestauPanier
                            pdel = session.query(RestauPanier).filter_by(id=self.panier.id).first()
                            if pdel:
                                try:
                                    session.delete(pdel)
                                    session.commit()
                                except Exception:
                                    session.rollback()
                                finally:
                                    session.close()
                            else:
                                session.close()
                            QMessageBox.information(dlg, 'Info', 'Panier vidé après paiement, table libérée')
                            # navigate back to plan view
                            parent = self.parent()
                            while parent is not None and not hasattr(parent, 'show_plan_view'):
                                parent = parent.parent()
                            try:
                                if parent and hasattr(parent, 'show_plan_view'):
                                    parent.show_plan_view()
                            except Exception:
                                pass
                            return
                    except Exception:
                        pass

                    dlg.accept()
                except Exception as e:
                    QMessageBox.critical(dlg, 'Erreur', f"Impossible d'enregistrer le paiement: {e}")

            cancel_btn.clicked.connect(do_cancel)
            confirm_btn.clicked.connect(do_confirm)

            if dlg.exec() == QDialog.DialogCode.Accepted:
                # refresh local panier and cart
                try:
                    self.panier = self.vente_ctrl.get_panier(self.panier.id)
                except Exception:
                    pass
                # if panier is now validated (paid) -> go back to plan view
                try:
                    if getattr(self.panier, 'status', None) and str(getattr(self.panier, 'status')) != 'en_cours':
                        parent = self.parent()
                        while parent is not None and not hasattr(parent, 'show_plan_view'):
                            parent = parent.parent()
                        try:
                            if parent and hasattr(parent, 'show_plan_view'):
                                parent.show_plan_view()
                                return
                        except Exception:
                            pass
                except Exception:
                    pass

                self.refresh_cart()

        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Erreur paiement: {e}")

    def _on_addition_clicked(self):
        # show a simple bill dialog with items and totals
        if not self.panier:
            QMessageBox.information(self, 'Info', 'Aucun panier actif')
            return
        try:
            items = self.controller.list_cart_items(self.panier.id)
            lines = []
            total = 0.0
            for it in items:
                try:
                    prod = self.controller.get_product(getattr(it, 'product_id', None))
                    name = getattr(prod, 'name', str(getattr(it, 'product_id', '')))
                except Exception:
                    name = str(getattr(it, 'product_id', ''))
                qty = getattr(it, 'quantity', 0)
                price = getattr(it, 'price', 0.0)
                line_total = getattr(it, 'total', float(qty) * float(price))
                total += float(line_total)
                lines.append(f"{name}  x{int(qty)}  {int(price)} {self._get_currency()}  = {int(line_total)} {self._get_currency()}")

            txt = "\n".join(lines)
            txt += f"\n\nTotal: {int(total)} {self._get_currency()}"

            # show in a dialog
            dlg = QDialog(self)
            dlg.setWindowTitle('Addition')
            dlg_l = QVBoxLayout(dlg)
            te = QTextEdit()
            te.setReadOnly(True)
            te.setPlainText(txt)
            dlg_l.addWidget(te)
            btn = QPushButton('Fermer')
            btn.clicked.connect(dlg.accept)
            dlg_l.addWidget(btn)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Impossible d'afficher l'addition: {e}")

    def _on_remise_changed(self):
        """Apply remise amount entered by user to the panier (montant)."""
        if not self.panier:
            return
        try:
            txt = self.remise_edit.text().strip()
            if not txt:
                val = 0.0
            else:
                try:
                    val = float(txt)
                except Exception:
                    QMessageBox.warning(self, 'Erreur', 'Remise invalide')
                    return
            # persist remise on panier
            session = self.vente_ctrl.db.get_session()
            from ayanna_erp.modules.restaurant.models.restaurant import RestauPanier
            p = session.query(RestauPanier).filter_by(id=self.panier.id).first()
            if not p:
                session.close()
                return
            p.remise_amount = float(val)
            # recompute total_final
            subtotal = sum([pr.total for pr in p.produits]) if p.produits else 0.0
            p.subtotal = subtotal
            p.total_final = subtotal - (p.remise_amount or 0.0)
            p.updated_at = p.updated_at
            session.commit()
            session.close()
            # refresh local panier and UI
            try:
                self.panier = self.vente_ctrl.get_panier(self.panier.id)
            except Exception:
                pass
            self._update_total_label()
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Impossible d'appliquer la remise: {e}")

    def _update_total_label(self):
        try:
            if not self.panier:
                self.total_label.setText(f"Total: 0 {self._get_currency()}")
                return
            p = None
            try:
                p = self.vente_ctrl.get_panier(self.panier.id)
            except Exception:
                p = self.panier
            subtotal = float(getattr(p, 'subtotal', 0.0) or 0.0)
            remise = float(getattr(p, 'remise_amount', 0.0) or 0.0)
            total_final = float(getattr(p, 'total_final', subtotal - remise))
            self.total_label.setText(f"Total: {int(total_final)} {self._get_currency()}")
        except Exception:
            pass

    def _populate_serveuse_combo(self):
        try:
            # tenter de lister les utilisateurs de l'entreprise
            db = get_database_manager()
            session = db.get_session()
            users = session.query(User).filter_by(enterprise_id=self.entreprise_id).all()
            session.close()
            self.serveuse_combo.clear()
            # ajouter une option vide
            self.serveuse_combo.addItem('---', 0)
            for u in users:
                self.serveuse_combo.addItem(getattr(u, 'name', str(getattr(u, 'email', 'user'))), getattr(u, 'id', 0))
            # si current_user présent, sélectionner
            if getattr(self, 'current_user', None):
                try:
                    uid = getattr(self.current_user, 'id', None)
                    if uid:
                        index = self.serveuse_combo.findData(uid)
                        if index >= 0:
                            self.serveuse_combo.setCurrentIndex(index)
                except Exception:
                    pass
        except Exception:
            # fallback: si current_user disponible
            try:
                self.serveuse_combo.clear()
                self.serveuse_combo.addItem(getattr(self.current_user, 'name', 'Serveuse'), getattr(self.current_user, 'id', 0))
            except Exception:
                pass

    def _populate_client_combo(self):
        try:
            db = get_database_manager()
            session = db.get_session()
            from ayanna_erp.modules.boutique.model.models import ShopClient
            clients = session.query(ShopClient).filter_by(is_active=True).order_by(ShopClient.nom.asc()).all()
            session.close()
            self.client_combo.clear()
            self.client_combo.addItem('---', 0)
            for c in clients:
                name = f"{getattr(c,'nom','') or ''} {getattr(c,'prenom','') or ''}".strip()
                if not name:
                    name = getattr(c, 'telephone', 'Client')
                self.client_combo.addItem(name, getattr(c, 'id', 0))
        except Exception:
            try:
                self.client_combo.clear()
                self.client_combo.addItem('---', 0)
            except Exception:
                pass

    def _get_currency(self):
        try:
            db = get_database_manager()
            session = db.get_session()
            ent = session.query(Entreprise).filter_by(id=self.entreprise_id).first()
            session.close()
            if ent and getattr(ent, 'currency', None):
                return getattr(ent, 'currency')
        except Exception:
            pass
        return 'F'

    def _apply_cart_column_proportions(self):
        """Apply proportional widths to cart columns: Produit 45%, Qté 10%, Prix 15%, Total 30%."""
        try:
            # viewport width is the available width for columns
            total_w = self.cart_table.viewport().width()
            if total_w <= 0:
                return
            # compute pixel widths
            w_prod = int(total_w * 0.45)
            w_qte = int(total_w * 0.10)
            w_prix = int(total_w * 0.20)
            w_total = max(0, total_w - (w_prod + w_qte + w_prix))
            # set widths (column 0 is hidden)
            self.cart_table.setColumnWidth(1, w_prod)
            self.cart_table.setColumnWidth(2, w_qte)
            self.cart_table.setColumnWidth(3, w_prix)
            self.cart_table.setColumnWidth(4, w_total)
        except Exception:
            pass

    def resizeEvent(self, event):
        # update column proportions when widget is resized
        try:
            self._apply_cart_column_proportions()
        except Exception:
            pass
        return super().resizeEvent(event)
