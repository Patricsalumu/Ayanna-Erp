from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QFrame, QLabel, QPushButton, QLineEdit, QSpinBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QComboBox, QDialog,
    QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ayanna_erp.modules.restaurant.controllers.catalogue_controller import CatalogueController
from ayanna_erp.modules.restaurant.controllers.vente_controller import VenteController


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
        self.selected_cart_row = None

        self.init_ui()
        self.load_products()
        self.ensure_panier()

    def init_ui(self):
        main = QVBoxLayout(self)
        header = QLabel(f"Catalogue - Table {self.table_id}")
        header.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        main.addWidget(header)

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

        # Finalize
        splitter.addWidget(right)
        splitter.setSizes([700, 300])

    def ensure_panier(self):
        p = self.vente_ctrl.get_open_panier_for_table(self.table_id)
        if not p:
            p = self.controller.get_or_create_panier_for_table(self.table_id, user_id=getattr(self.current_user, 'id', None))
        self.panier = p
        self.refresh_cart()

    def load_products(self):
        search = self.search_edit.text() if hasattr(self, 'search_edit') else None
        products = self.controller.list_products(search=search)
        # clear
        for i in reversed(range(self.products_layout.count())):
            w = self.products_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        cols = 3
        for idx, prod in enumerate(products):
            card = QFrame(); card.setFrameStyle(QFrame.Shape.StyledPanel)
            card_l = QVBoxLayout(card)
            name = QLabel(getattr(prod, 'name', 'Produit'))
            price = QLabel(f"{getattr(prod, 'price_unit', getattr(prod, 'price', 0))} F")
            add_btn = QPushButton('➕')
            add_btn.clicked.connect(lambda _checked, pid=prod.id: self.add_product(pid))
            card_l.addWidget(name); card_l.addWidget(price); card_l.addWidget(add_btn)
            r = idx // cols; c = idx % cols
            self.products_layout.addWidget(card, r, c)

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
        self.cart_table.setRowCount(0)
        for i, it in enumerate(items):
            self.cart_table.insertRow(i)
            id_item = QTableWidgetItem(str(getattr(it, 'id')))
            id_item.setData(Qt.ItemDataRole.UserRole, getattr(it, 'id'))
            self.cart_table.setItem(i, 0, id_item)
            name_item = QTableWidgetItem(str(getattr(it, 'product_id')))
            self.cart_table.setItem(i, 1, name_item)
            qty_item = QTableWidgetItem(str(getattr(it, 'quantity')))
            self.cart_table.setItem(i, 2, qty_item)
            total_item = QTableWidgetItem(str(getattr(it, 'total')))
            self.cart_table.setItem(i, 3, total_item)

    def on_cart_row_clicked(self, row, col):
        self.selected_cart_row = row
        pid_item = self.cart_table.item(row, 0)
        if pid_item:
            lp_id = int(pid_item.text())
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
