from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QFrame, QLabel, QPushButton, QLineEdit, QSpinBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QComboBox, QDialog,
    QSplitter, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ayanna_erp.modules.restaurant.controllers.catalogue_controller import CatalogueController
from ayanna_erp.modules.restaurant.controllers.vente_controller import VenteController
from ayanna_erp.database.database_manager import get_database_manager, User
from ayanna_erp.database.database_manager import Entreprise


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

        self.serveuse_combo = QComboBox()
        # populate options
        try:
            self._populate_serveuse_combo()
        except Exception:
            pass
        header_h.addWidget(QLabel("Serveuse:"))
        header_h.addWidget(self.serveuse_combo)
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
        self.cart_table = QTableWidget(0, 4)
        self.cart_table.setHorizontalHeaderLabels(['Ligne ID', 'Produit', 'Qté', 'Total'])
        self.cart_table.horizontalHeader().setSectionHidden(0, True)
        self.cart_table.horizontalHeader().setStretchLastSection(True)
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.cellClicked.connect(self.on_cart_row_clicked)
        right_l.addWidget(self.cart_table)

        # Numeric pad and actions
        pad = QHBoxLayout()
        self.qty_spin = QSpinBox(); self.qty_spin.setMinimum(1); self.qty_spin.setMaximum(9999)
        pad.addWidget(self.qty_spin)
        inc_btn = QPushButton('+'); dec_btn = QPushButton('-'); del_btn = QPushButton('Suppr')
        inc_btn.clicked.connect(self.increment_selected_qty)
        dec_btn.clicked.connect(self.decrement_selected_qty)
        del_btn.clicked.connect(self.delete_selected_line)
        pad.addWidget(inc_btn); pad.addWidget(dec_btn); pad.addWidget(del_btn)
        right_l.addLayout(pad)

        # (numeric keypad removed - we keep qty_spin + +/-/Suppr controls)

        # Note du panier
        right_l.addWidget(QLabel('Note (commande)'))
        self.note_edit = QTextEdit()
        self.note_edit.setFixedHeight(80)
        right_l.addWidget(self.note_edit)
        save_note_btn = QPushButton('Enregistrer la note')
        save_note_btn.clicked.connect(self.save_note)
        right_l.addWidget(save_note_btn)

        # Finalize
        splitter.addWidget(right)
        # enlarge product area and reduce cart area
        splitter.setSizes([1000, 200])

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
        self.refresh_cart()
        # charger la note si présente
        try:
            if self.panier:
                session = self.controller.db.get_session()
                from ayanna_erp.modules.restaurant.models.restaurant import RestauPanier
                obj = session.query(RestauPanier).filter_by(id=self.panier.id).first()
                if obj and getattr(obj, 'note', None):
                    try:
                        self.note_edit.setPlainText(str(obj.note))
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

        cols = 5
        for idx, prod in enumerate(products):
            card = self.create_product_card(prod)
            r = idx // cols; c = idx % cols
            self.products_layout.addWidget(card, r, c)

        # ensure some stretch so cards align top
        self.products_layout.setRowStretch((len(products) // cols) + 1, 1)

    def create_product_card(self, product):
        """Créer une carte produit similaire à ModernSupermarketWidget.create_product_card
        adaptée au catalogue de la table (simplifiée).
        """
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 8px;
            }
            QFrame:hover {
                border-color: #1976D2;
                background-color: #F3F9FF;
            }
        """)
        card.setFixedSize(160, 120)

        layout = QVBoxLayout(card)
        layout.setSpacing(6)

        # top row: badge on the right
        top_row = QHBoxLayout()
        top_row.addStretch()
        badge = QLabel('0')
        badge.setObjectName('cart_badge')
        badge.setFixedSize(28, 18)
        badge.setStyleSheet('background-color:#E53935; color:white; border-radius:9px; padding:2px; font-size:11px;')
        top_row.addWidget(badge)
        layout.addLayout(top_row)

        # Image placeholder
        img = QLabel()
        img.setFixedSize(120, 54)
        img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img.setText("🧾")
        layout.addWidget(img, 0, Qt.AlignmentFlag.AlignHCenter)

        # Name
        name = getattr(product, 'name', 'Produit')
        name_label = QLabel(name[:30] + '...' if len(name) > 30 else name)
        name_label.setWordWrap(True)
        name_label.setStyleSheet("font-weight: bold; color: #212529;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

        # Entire card is clickable to add product; price/button removed per request
        price = float(getattr(product, 'price_unit', getattr(product, 'price', 0) or 0))
        card.setToolTip(f"{getattr(product,'name','')} - {int(price)} {self._get_currency()}")

        # clickable behaviour
        def _on_click(prod_id=getattr(product, 'id', None)):
            try:
                self.add_product(prod_id)
                # update badges by reloading products
                self._update_badges()
            except Exception as e:
                QMessageBox.critical(self, 'Erreur', str(e))

        # attach click handler
        def _mouse_press(event):
            _on_click()

        card.mousePressEvent = _mouse_press

        # set initial badge value if panier exists
        try:
            qty_in_cart = self._get_cart_quantity_for_product(getattr(product, 'id', None))
            badge.setText(str(int(qty_in_cart)))
            if int(qty_in_cart) <= 0:
                badge.setVisible(False)
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
        # iterate product cards and update badge labels
        for i in range(self.products_layout.count()):
            it = self.products_layout.itemAt(i)
            w = it.widget()
            if not w:
                continue
            # try to find badge child
            badge = w.findChild(QLabel, 'cart_badge')
            # infer product id from tooltip via 'id' not stored; safer to reload all products
        # simplest: reload products to refresh badges
        self.load_products()

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
            total_item = QTableWidgetItem(str(getattr(it, 'total')))
            self.cart_table.setItem(i, 3, total_item)

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
            self.controller.set_panier_note(self.panier.id, note)
            QMessageBox.information(self, 'Succès', 'Note enregistrée')
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Impossible d'enregistrer la note: {e}")

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
