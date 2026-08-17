from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QFrame, QLabel, QPushButton, QLineEdit, QSpinBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QComboBox, QDialog,
    QSplitter, QTextEdit, QDoubleSpinBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap


from ayanna_erp.modules.restaurant.controllers.catalogue_controller import CatalogueController
from ayanna_erp.modules.restaurant.controllers.vente_controller import VenteController
from ayanna_erp.modules.restaurant.controllers.printed_invoices_controller import PrintedInvoicesController
from ayanna_erp.modules.restaurant.controllers.bon_commande_controller import BonCommandeController
from ayanna_erp.modules.restaurant.utils.bon_commande_printer import BonCommandePrinter
from ayanna_erp.database.database_manager import get_database_manager, User
from sqlalchemy import text
from ayanna_erp.utils.formatting import get_currency
from ayanna_erp.utils.sumatra_printer import SumatraPrinter
import os
import platform
import subprocess


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
        self.printed_invoices_ctrl = PrintedInvoicesController(entreprise_id=entreprise_id)
        self.bon_commande_ctrl = BonCommandeController(entreprise_id=entreprise_id)
        self.bon_commande_printer = BonCommandePrinter(enterprise_id=entreprise_id)

        # mapping category_id -> assigned color for visible categories (ensures consistency with filter buttons)
        self._category_color_map = {}

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

    def _format_display_amount(self, amount):
        """Format amounts for the restaurant catalogue with two decimals."""
        try:
            value = float(amount)
        except (TypeError, ValueError):
            return str(amount)
        return f"{value:,.2f}".replace(",", " ").replace(".", ",")

    def _print_pdf_with_default_printer(self, file_path: str) -> tuple[bool, str | None]:
        """Send a PDF file directly to the system default printer."""
        printer = SumatraPrinter()
        success, message = printer.print_pdf(file_path)
        return success, message

    def _return_to_vente_view(self):
        """Retourne automatiquement à la vue vente lorsque le widget est contenu dans le QStackedWidget du plan."""
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, 'show_plan_view') and callable(parent.show_plan_view):
                try:
                    parent.show_plan_view()
                    return True
                except Exception:
                    return False
            parent = parent.parent()
        return False

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
        self.serveuse_combo.setEnabled(False)
        self.serveuse_combo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
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

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main.addWidget(self.splitter)

        # Left: products
        left = QWidget()
        left_l = QVBoxLayout(left)
        search_h = QHBoxLayout()
        self.search_edit = QLineEdit(); self.search_edit.setPlaceholderText('Rechercher...')
        self.search_edit.textChanged.connect(self.load_products)
        search_h.addWidget(self.search_edit)
        # Refresh button to reload products / cart quickly
        try:
            refresh_btn = QPushButton('🔄 Rafraîchir')
            refresh_btn.clicked.connect(lambda: (self.load_products(), self.refresh_cart()))
            search_h.addWidget(refresh_btn)
        except Exception:
            pass
        left_l.addLayout(search_h)

        self.products_area = QScrollArea(); self.products_area.setWidgetResizable(True)
        self.products_area.setMinimumHeight(520)
        self.products_area.setMaximumHeight(520)
        self.products_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.products_area.setViewportMargins(0, 0, 0, 0)
        self.products_container = QWidget()
        self.products_layout = QGridLayout(self.products_container)
        self.products_layout.setContentsMargins(0, 0, 0, 0)
        self.products_layout.setSpacing(6)
        self.products_area.setWidget(self.products_container)
        left_l.addWidget(self.products_area)
        # Left: cart
        left_cart = QWidget()
        left_cart.setMinimumWidth(230)
        left_cart.setMaximumWidth(310)
        left_cart_l = QVBoxLayout(left_cart)
        self.cart_title_label = QLabel('Panier')
        left_cart_l.addWidget(self.cart_title_label)
        # Columns: hidden Ligne ID, Produit, Qté, Prix, Total
        self.cart_table = QTableWidget(0, 5)
        self.cart_table.setHorizontalHeaderLabels(['Ligne ID', 'Produit', 'Qté', 'Prix', 'Total'])
        self.cart_table.horizontalHeader().setSectionHidden(0, True)
        self.cart_table.horizontalHeader().setStretchLastSection(True)
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.cellClicked.connect(self.on_cart_row_clicked)
        left_cart_l.addWidget(self.cart_table)

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
        self.qty_spin = QSpinBox(); self.qty_spin.setMinimum(1); self.qty_spin.setMaximum(9999); self.qty_spin.setVisible(False)
        pad.addWidget(self.qty_spin)
        try:
            self.qty_spin.editingFinished.connect(self._apply_qty_from_spin)
        except Exception:
            pass

        self.inc_btn = QPushButton('+'); self.dec_btn = QPushButton('-'); self.del_btn = QPushButton('Suppr')
        self.inc_btn.setMinimumHeight(46); self.inc_btn.setMinimumWidth(72); self.inc_btn.setStyleSheet('font-size:16px; font-weight:700;')
        self.dec_btn.setMinimumHeight(46); self.dec_btn.setMinimumWidth(72); self.dec_btn.setStyleSheet('font-size:16px; font-weight:700;')
        self.del_btn.setMinimumHeight(46); self.del_btn.setMinimumWidth(92); self.del_btn.setStyleSheet('font-size:15px; font-weight:700; background:#d32f2f; color:white;')
        self.inc_btn.clicked.connect(self.increment_selected_qty)
        self.dec_btn.clicked.connect(self.decrement_selected_qty)
        self.del_btn.clicked.connect(self.delete_selected_line)
        pad.addWidget(self.inc_btn); pad.addWidget(self.dec_btn); pad.addWidget(self.del_btn)
        left_cart_l.addLayout(pad)

        # Remise (montant) et label Total
        totals_h = QHBoxLayout()
        self.remise_edit = QLineEdit()
        self.remise_edit.setPlaceholderText('Remise (montant)')
        self.remise_edit.setMinimumHeight(38)
        self.remise_edit.setMinimumWidth(140)
        try:
            self.remise_edit.editingFinished.connect(self._on_remise_changed)
        except Exception:
            pass
        totals_h.addWidget(QLabel('Remise:'))
        totals_h.addWidget(self.remise_edit)
        totals_h.addStretch()
        self.total_label = QLabel('Total: 0 F')
        self.total_label.setMinimumHeight(38)
        self.total_label.setStyleSheet('font-size:15px; font-weight:700;')
        totals_h.addWidget(self.total_label)
        left_cart_l.addLayout(totals_h)

        # Action buttons: Annuler, Payer, Addition
        actions_h = QHBoxLayout()
        self.annuler_btn = QPushButton('Annuler')
        self.payer_btn = QPushButton('Payer')
        self.imprimer_btn = QPushButton('Facturer')
        self.bon_btn = QPushButton('Commander')
        self.liberer_table_btn = QPushButton('Libérer la table')
        for btn in (self.annuler_btn, self.payer_btn, self.imprimer_btn, self.bon_btn, self.liberer_table_btn):
            btn.setMinimumHeight(46)
            btn.setMinimumWidth(110)
            btn.setStyleSheet('font-size:14px; font-weight:700;')
        self.annuler_btn.setStyleSheet('background-color:#e53935; color:white; font-size:14px; font-weight:700;')
        self.payer_btn.setStyleSheet('background-color:#28a745; color:white; font-size:14px; font-weight:700;')
        self.imprimer_btn.setStyleSheet('background-color:#1976D2; color:white; font-size:14px; font-weight:700;')
        self.bon_btn.setStyleSheet('background-color:#1976D2; color:white; font-size:14px; font-weight:700;')
        self.liberer_table_btn.setStyleSheet('background-color:#d32f2f; color:white; font-size:14px; font-weight:700;')
        actions_h.addWidget(self.annuler_btn)
        actions_h.addWidget(self.payer_btn)
        actions_h.addWidget(self.imprimer_btn)
        actions_h.addWidget(self.bon_btn)
        actions_h.addWidget(self.liberer_table_btn)
        left_cart_l.addLayout(actions_h)

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
            self.imprimer_btn.clicked.connect(self._on_imprimer_clicked)
        except Exception:
            pass
        try:
            self.bon_btn.clicked.connect(self._on_bon_commande_clicked)
        except Exception:
            pass
        try:
            self.liberer_table_btn.clicked.connect(self._on_liberer_table_clicked)
        except Exception:
            pass

        # Finalize
        self.splitter.addWidget(left_cart)
        self.splitter.addWidget(left)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 2)
        # cart left 35%, catalog right 65%
        self.splitter.setSizes([400, 600])
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

        cols = 7
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
        # Use the central category color helper so buttons and cards match.
        # If product doesn't expose category name, resolve it via category_id
        category = None
        cat_id = getattr(product, 'category_id', None) if hasattr(product, 'category_id') else None
        try:
            if getattr(product, 'category_name', None):
                category = getattr(product, 'category_name')
            elif cat_id:
                # lookup in core_product_categories using the core model
                db = get_database_manager()
                session = db.get_session()
                try:
                    from ayanna_erp.modules.core.models.core_products import CoreProductCategory
                    # Ensure we only pick categories for the current enterprise
                    cat_obj = session.query(CoreProductCategory).filter_by(id=cat_id, entreprise_id=self.entreprise_id).first()
                    if cat_obj:
                        category = getattr(cat_obj, 'name', None)
                finally:
                    try:
                        session.close()
                    except Exception:
                        pass
        except Exception:
            category = None

        if not category:
            category = 'Autres'

        border_color = self._category_color(category, cat_id)

        # ---- Créer le cadre principal ----
        card = QFrame()
        card.setFixedSize(110, 125)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 10px;
                /* no outer border as requested */
            }}
            QFrame:hover {{
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
            border: none;
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
            font-weight: 400;
            font-size: 12px;
        """)
        layout.addWidget(name_label)

        # ---- Info bulle ----
        price = float(getattr(product, 'price_unit', getattr(product, 'price', 0)))
        # Attempt to resolve available stock in POS_4 for restaurant (best-effort)
        avail_text = ''
        try:
            pid = getattr(product, 'id', None)
            if pid is not None:
                db = get_database_manager()
                session = db.get_session()
                try:
                    row = session.execute(text("""
                        SELECT spe.quantity FROM stock_produits_entrepot spe
                        JOIN stock_warehouses w ON w.id = spe.warehouse_id
                        WHERE spe.product_id = :pid AND w.code = 'POS_4' AND w.is_active = 1
                        LIMIT 1
                    """), {'pid': pid}).fetchone()
                    available = int(row[0]) if row and row[0] is not None else 0
                    avail_text = f"\nDisponible (POS): {available}"
                except Exception:
                    avail_text = ''
                finally:
                    try:
                        session.close()
                    except Exception:
                        pass
        except Exception:
            avail_text = ''

        card.setToolTip(f"{name}\nPrix: {self._format_display_amount(price)} {get_currency(self.entreprise_id)}{avail_text}")

        # ---- bande de couleur de la catégorie (en bas de la carte) ----
        try:
            cat_name = getattr(product, 'category_name', None) or category
            cat_id = getattr(product, 'category_id', None) if hasattr(product, 'category_id') else None
            # prefer the color assigned in the category bar mapping so button and card match
            band_color = None
            try:
                if cat_id is not None and cat_id in self._category_color_map:
                    band_color = self._category_color_map.get(cat_id)
                elif cat_name in self._category_color_map:
                    band_color = self._category_color_map.get(cat_name)
            except Exception:
                band_color = None
            if not band_color:
                band_color = self._category_color(cat_name, cat_id)
            band = QWidget()
            band.setFixedHeight(8)
            band.setStyleSheet(f'background-color: {band_color}; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;')
            layout.addWidget(band)
        except Exception:
            pass

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
        # style 'Tous' with neutral color
        all_btn.setStyleSheet('background-color:#ECEFF1; color:#212121; border-radius:6px; padding:6px 10px;')
        all_btn.clicked.connect(lambda _: self._on_category_selected(None, all_btn))
        self.category_bar.addWidget(all_btn)

        cats = []
        try:
            cats = self.controller.list_categories() or []
        except Exception:
            cats = []

    # Ensure each visible category gets a unique color from the palette.
        palette = [
            '#F44336', '#9C27B0', '#4CAF50', '#3F51B5', '#FF9800',
            '#009688', '#FF4081', '#00BCD4', '#8BC34A', '#795548',
            '#607D8B', '#CDDC39', '#E91E63', '#9E9E9E'
        ]
        used = set()
        # reset mapping for this visible set
        try:
            self._category_color_map = {}
        except Exception:
            self._category_color_map = {}

        for c in cats:
            cname = getattr(c, 'name', 'Cat')
            cid = getattr(c, 'id', None)
            btn = QPushButton(cname)
            btn.setCheckable(True)
            # preferred color from deterministic helper
            preferred = self._category_color(cname, cid)
            col = preferred
            # avoid collisions for the visible set: if preferred already used, pick first free from palette
            if col in used:
                found = None
                for p in palette:
                    if p not in used:
                        found = p
                        break
                if found:
                    col = found
                else:
                    # fallback: keep preferred
                    col = preferred
            used.add(col)
            # store mapping by id (preferred) or by name if id missing
            try:
                if cid is not None:
                    self._category_color_map[int(cid)] = col
                else:
                    # fallback mapping by name
                    self._category_color_map[cname] = col
            except Exception:
                try:
                    self._category_color_map[cname] = col
                except Exception:
                    pass
            # set background color and ensure text contrast
            btn.setStyleSheet(f'background-color: {col}; color: white; font-weight:600; border-radius:6px; padding:6px 10px;')
            btn.clicked.connect(lambda _checked, cid=cid, b=btn: self._on_category_selected(cid, b))
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

    def _update_empty_cart_actions(self):
        if not hasattr(self, 'liberer_table_btn'):
            return
        try:
            if not self.panier:
                self.liberer_table_btn.hide()
                return
            items = self.controller.list_cart_items(self.panier.id) or []
            is_empty = len(items) == 0

            self.cart_title_label.setVisible(not is_empty)
            self.liberer_table_btn.setVisible(is_empty)
            self.annuler_btn.setVisible(not is_empty)
            self.payer_btn.setVisible(not is_empty)
            self.imprimer_btn.setVisible(not is_empty)
            self.bon_btn.setVisible(not is_empty)
            self.cart_table.setVisible(not is_empty)
            self.qty_spin.setVisible(not is_empty)
            self.inc_btn.setVisible(not is_empty)
            self.dec_btn.setVisible(not is_empty)
            self.del_btn.setVisible(not is_empty)
            self.remise_edit.setVisible(not is_empty)
            self.total_label.setVisible(not is_empty)

            if hasattr(self, 'splitter'):
                self.splitter.setSizes([350, 650])
            if hasattr(self, 'splitter'):
                self.splitter.setCollapsible(1, False)
        except Exception:
            self.liberer_table_btn.hide()

    def _on_liberer_table_clicked(self):
        if not self.panier:
            QMessageBox.information(self, 'Info', 'Aucune table active à libérer')
            return

        ok = QMessageBox.question(
            self,
            'Libérer la table',
            'Le panier est vide. Voulez-vous libérer cette table ?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ok != QMessageBox.StandardButton.Yes:
            return

        try:
            session = self.vente_ctrl.db.get_session()
            from ayanna_erp.modules.restaurant.models.restaurant import RestauPanier, RestauPrintedInvoice
            p = session.query(RestauPanier).filter_by(id=self.panier.id).first()
            if not p:
                session.close()
                QMessageBox.information(self, 'Succès', 'Table déjà libérée')
                return

            has_printed_invoice = (
                session.query(RestauPrintedInvoice.id)
                .filter_by(panier_id=self.panier.id)
                .first() is not None
            )
            if has_printed_invoice:
                p.status = 'annule'
                session.commit()
                session.close()
                QMessageBox.information(self, 'Succès', 'Table libérée (facture imprimée conservée)')
            else:
                try:
                    session.delete(p)
                    session.commit()
                except Exception:
                    session.rollback()
                    raise
                finally:
                    session.close()
                QMessageBox.information(self, 'Succès', 'Table libérée')

            parent = self.parent()
            while parent is not None and not hasattr(parent, 'show_plan_view'):
                parent = parent.parent()
            try:
                if parent and hasattr(parent, 'show_plan_view'):
                    parent.show_plan_view()
            except Exception:
                pass
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Impossible de libérer la table: {e}")

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
            price_item = QTableWidgetItem(self._format_display_amount(getattr(it, 'price', 0.0)))
            self.cart_table.setItem(i, 3, price_item)
            total_item = QTableWidgetItem(self._format_display_amount(getattr(it, 'total', 0.0)))
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

        try:
            self._update_empty_cart_actions()
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

    def _get_current_line_quantity(self, lp_id):
        """Retourne la quantité réelle enregistrée dans le panier, sans dépendre du dernier état affiché dans la table."""
        try:
            items = self.controller.list_cart_items(self.panier.id)
            for it in items:
                if int(getattr(it, 'id', 0)) == int(lp_id):
                    return int(float(getattr(it, 'quantity', 0) or 0))
        except Exception:
            pass
        try:
            row = self.selected_cart_row
            if row is not None and row < self.cart_table.rowCount():
                return int(float(self.cart_table.item(row, 2).text() or 0))
        except Exception:
            pass
        return 1

    def increment_selected_qty(self):
        if self.selected_cart_row is None:
            return
        row = self.selected_cart_row
        lp_id = int(self.cart_table.item(row, 0).text())
        current = self._get_current_line_quantity(lp_id)
        newq = current + 1
        try:
            self.controller.update_product_quantity(self.panier.id, lp_id, newq)
            self.selected_line_id = lp_id
            self.refresh_cart()
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', str(e))

    def decrement_selected_qty(self):
        if self.selected_cart_row is None:
            return
        if not self._current_user_is_super_admin():
            if not self._require_super_admin_password():
                return
        row = self.selected_cart_row
        lp_id = int(self.cart_table.item(row, 0).text())
        current = self._get_current_line_quantity(lp_id)
        newq = max(1, current - 1)
        try:
            self.controller.update_product_quantity(self.panier.id, lp_id, newq)
            self.selected_line_id = lp_id
            self.refresh_cart()
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', str(e))

    def delete_selected_line(self):
        if self.selected_cart_row is None:
            return
        # If current user is not super_admin, require super_admin authorization
        if not self._current_user_is_super_admin():
            if not self._require_super_admin_password():
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
        # If reducing quantity (edit results in smaller qty) require super_admin for simple users
        try:
            lp_id = int(self.cart_table.item(self.selected_cart_row, 0).text())
            oldq = int(self.cart_table.item(self.selected_cart_row, 2).text())
            newq = int(self.qty_spin.value())
            if newq < oldq and not self._current_user_is_super_admin():
                if not self._require_super_admin_password():
                    # restore spin to old value
                    try:
                        self.qty_spin.setValue(oldq)
                    except Exception:
                        pass
                    return
            # remember selected_line_id so refresh preserves focus
            self.selected_line_id = lp_id
            self.controller.update_product_quantity(self.panier.id, lp_id, newq)
            self.refresh_cart()
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Impossible d'appliquer la quantité: {e}")

    def _current_user_is_super_admin(self):
        """Return True if current_user has role super_admin."""
        try:
            if not getattr(self, 'current_user', None):
                return False
            role = getattr(self.current_user, 'role', None) or getattr(self.current_user, 'role', None)
            return str(role) == 'super_admin'
        except Exception:
            return False

    def _verify_super_admin_password(self, pwd: str) -> bool:
        """Verify the entered super-admin password against known super-admin users."""
        if not pwd:
            return False
        try:
            db = get_database_manager()
            session = db.get_session()
            users = session.query(User).filter_by(role='super_admin').all()
            session.close()
            for u in users:
                try:
                    if hasattr(u, 'check_password') and u.check_password(pwd):
                        return True
                except Exception:
                    pass
        except Exception:
            pass
        return False

    def _require_super_admin_password(self) -> bool:
        """Open a custom keypad dialog for super-admin password entry and verify it."""
        dialog = QDialog(self)
        dialog.setWindowTitle('Autorisation requise')
        dialog.setModal(True)
        dialog.resize(320, 380)

        main_layout = QVBoxLayout(dialog)
        main_layout.setSpacing(12)

        title = QLabel('Entrez le mot de passe d\'un super administrateur:')
        title.setWordWrap(True)
        title.setStyleSheet('font-weight: 600;')
        main_layout.addWidget(title)

        pwd_edit = QLineEdit()
        pwd_edit.setEchoMode(QLineEdit.EchoMode.Password)
        pwd_edit.setPlaceholderText('Mot de passe')
        pwd_edit.setMinimumHeight(42)
        pwd_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pwd_edit.returnPressed.connect(dialog.accept)
        main_layout.addWidget(pwd_edit)

        keypad = QGridLayout()
        keypad.setHorizontalSpacing(10)
        keypad.setVerticalSpacing(10)

        for row, col, text in [
            (0, 0, '1'), (0, 1, '2'), (0, 2, '3'),
            (1, 0, '4'), (1, 1, '5'), (1, 2, '6'),
            (2, 0, '7'), (2, 1, '8'), (2, 2, '9'),
            (3, 0, 'C'), (3, 1, '0'), (3, 2, '⌫'),
        ]:
            btn = QPushButton(text)
            btn.setMinimumHeight(48)
            btn.setStyleSheet('font-size: 16px; font-weight: 600;')

            if text == 'C':
                btn.clicked.connect(lambda: pwd_edit.clear())
            elif text == '⌫':
                btn.clicked.connect(lambda: pwd_edit.backspace())
            else:
                btn.clicked.connect(lambda checked=False, value=text: pwd_edit.insert(value))

            keypad.addWidget(btn, row, col)

        main_layout.addLayout(keypad)

        actions = QHBoxLayout()
        ok_btn = QPushButton('OK')
        ok_btn.setDefault(True)
        cancel_btn = QPushButton('Annuler')
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        actions.addStretch()
        actions.addWidget(cancel_btn)
        actions.addWidget(ok_btn)
        main_layout.addLayout(actions)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return False

        pwd = pwd_edit.text().strip()
        if not pwd:
            return False

        if not self._verify_super_admin_password(pwd):
            QMessageBox.warning(self, 'Autorisation refusée', 'Mot de passe super_admin invalide')
            return False

        return True

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
        # If current user is not super_admin, require super_admin authorization
        if not self._current_user_is_super_admin():
            if not self._require_super_admin_password():
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
            from ayanna_erp.modules.restaurant.models.restaurant import RestauPanier, RestauPrintedInvoice
            p = session.query(RestauPanier).filter_by(id=self.panier.id).first()
            if p:
                has_printed_invoice = (
                    session.query(RestauPrintedInvoice.id)
                    .filter_by(panier_id=self.panier.id)
                    .first()
                    is not None
                )
                if not items:
                    if has_printed_invoice:
                        # Garder la trace: si une facture a ete imprimee, ne jamais supprimer le panier.
                        p.status = 'annule'
                        session.commit()
                        session.close()
                        QMessageBox.information(self, 'Succès', 'Panier passé à annule (facture imprimée conservée)')
                    else:
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
                # resolve table number and salle name from DB
                db = get_database_manager()
                session = db.get_session()
                from ayanna_erp.modules.restaurant.models.restaurant import RestauTable
                tbl_obj = session.query(RestauTable).filter_by(id=self.table_id).first()
                if tbl_obj:
                    tbl_display = str(getattr(tbl_obj, 'number', self.table_id))
                    try:
                        salle_obj = getattr(tbl_obj, 'salle', None)
                        salle_name = getattr(salle_obj, 'name', None) if salle_obj is not None else None
                    except Exception:
                        salle_name = None
                else:
                    tbl_display = str(self.table_id)
                    salle_name = None
                try:
                    session.close()
                except Exception:
                    pass
            except Exception:
                tbl_display = str(self.table_id)
                salle_name = None
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
            form.addRow(QLabel('Salle:'), QLabel(salle_name or '---'))
            form.addRow(QLabel('Client:'), QLabel(client_name))
            form.addRow(QLabel('Serveuse:'), QLabel(serveuse_name))
            form.addRow(QLabel('Sous-total:'), QLabel(f"{self._format_display_amount(subtotal)} {get_currency(self.entreprise_id)}"))
            form.addRow(QLabel('Remise:'), QLabel(f"{self._format_display_amount(remise)} {get_currency(self.entreprise_id)}"))
            form.addRow(QLabel('<b>Total à payer:</b>'), QLabel(f"<b>{self._format_display_amount(total_final)} {get_currency(self.entreprise_id)}</b>"))
            dlg_l.addWidget(summary_frame)

            # Amount received input (créé en premier pour être accessible par les boutons de paiement)
            amt_input = QDoubleSpinBox()
            amt_input.setPrefix('')
            amt_input.setSuffix(f' {get_currency(self.entreprise_id)}')
            amt_input.setDecimals(2)
            amt_input.setMinimum(0.0)
            try:
                amt_input.setMaximum(max(total_final * 10, total_final + 10000))
            except Exception:
                amt_input.setMaximum(1e9)
            amt_input.setValue(total_final)
            amt_input.setFixedWidth(160)

            change_lbl = QLabel('')
            change_lbl.setStyleSheet('font-weight:600; color:#333;')

            # --- Mode de paiement (boutons sélectionnables) ---
            pay_method_frame = QFrame()
            pay_method_frame.setStyleSheet('QFrame { border: 1px solid #e0e0e0; border-radius:6px; padding:8px; background:#fff }')
            pay_method_layout = QVBoxLayout(pay_method_frame)
            pay_method_label = QLabel('<b>Mode de paiement:</b>')
            pay_method_layout.addWidget(pay_method_label)

            # Charger les modes dynamiques
            _icon_map = {
                'cash':         ('💵', '#28a745'),
                'banque':       ('🏦', '#1976D2'),
                'mobile_money': ('📱', '#FF9800'),
                'credit':       ('📝', '#e53935'),
            }
            try:
                from ayanna_erp.core.view.payment_mode_widget import get_active_payment_modes
                _dyn_modes = get_active_payment_modes()
                pay_methods = [
                    (m['label'], m['code'],
                     _icon_map.get(m['code'], ('💳', '#607D8B'))[0],
                     _icon_map.get(m['code'], ('💳', '#607D8B'))[1])
                    for m in _dyn_modes
                ]
            except Exception:
                pay_methods = [
                    ('Espèces',      'cash',         '💵', '#28a745'),
                    ('Banque',       'banque',       '🏦', '#1976D2'),
                    ('Mobile Money', 'mobile_money', '📱', '#FF9800'),
                    ('Crédit',       'credit',       '📝', '#e53935'),
                ]

            selected_method = {'value': pay_methods[0][0] if pay_methods else 'Espèces',
                               'code':  pay_methods[0][1] if pay_methods else 'cash'}
            method_buttons = []

            def select_payment_method(method_name, method_code, buttons_list):
                selected_method['value'] = method_name
                selected_method['code']  = method_code
                for b in buttons_list:
                    if b.property('method') == method_name:
                        b.setStyleSheet(f"background-color: {b.property('color')}; color: white; font-weight:bold; border-radius:6px; padding:6px 10px; border: 2px solid #333;")
                    else:
                        b.setStyleSheet(f"background-color: #f0f0f0; color: #333; border-radius:6px; padding:6px 10px; border: 1px solid #ccc;")
                # Si Crédit: montant reçu = 0, non modifiable
                if method_code == 'credit':
                    amt_input.setValue(0.0)
                    amt_input.setEnabled(False)
                else:
                    amt_input.setEnabled(True)
                    amt_input.setValue(total_final)
                try:
                    update_change_label()
                except Exception:
                    pass

            # Grille 5 boutons par ligne
            _COLS = 5
            pay_grid = QGridLayout()
            pay_grid.setSpacing(6)
            for _i, (m_name, m_code, m_icon, m_color) in enumerate(pay_methods):
                btn = QPushButton(f'{m_icon} {m_name}')
                btn.setProperty('method', m_name)
                btn.setProperty('color', m_color)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setFixedHeight(32)
                method_buttons.append(btn)
                btn.clicked.connect(lambda _checked, mn=m_name, mc=m_code, bl=method_buttons: select_payment_method(mn, mc, bl))
                pay_grid.addWidget(btn, _i // _COLS, _i % _COLS)

            pay_method_layout.addLayout(pay_grid)
            dlg_l.addWidget(pay_method_frame)

            # Sélectionner le premier mode par défaut
            if pay_methods:
                select_payment_method(pay_methods[0][0], pay_methods[0][1], method_buttons)

            # Montant reçu layout
            amt_h = QHBoxLayout()
            amt_h.setSpacing(8)
            amt_h.addWidget(QLabel('Montant reçu:'))
            amt_h.addWidget(amt_input)
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
                        change_lbl.setText(f"Monnaie: {self._format_display_amount(monnaie)} {get_currency(self.entreprise_id)}")
                    else:
                        reste = total_final - v
                        change_lbl.setText(f"Reste: {self._format_display_amount(reste)} {get_currency(self.entreprise_id)}")
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
                method = selected_method['value']
                is_credit = selected_method.get('code') == 'credit'
                try:
                    if is_credit:
                        # Crédit: montant reçu = 0, enregistrer le total comme crédit
                        pay_amount = 0.0
                        self.vente_ctrl.add_payment(self.panier.id, pay_amount, method, user_id=getattr(self.current_user, 'id', None))
                        QMessageBox.information(dlg, 'Succès', f'Paiement à crédit enregistré. Reste dû: {self._format_display_amount(total_final)} {get_currency(self.entreprise_id)}')
                    elif amt >= total_final:
                        # record payment for the total due and compute monnaie to give back
                        pay_amount = float(total_final)
                        self.vente_ctrl.add_payment(self.panier.id, pay_amount, method, user_id=getattr(self.current_user, 'id', None))
                        monnaie = amt - total_final
                        QMessageBox.information(dlg, 'Succès', f'Paiement de {self._format_display_amount(pay_amount)} {get_currency(self.entreprise_id)} enregistré ({method}). Monnaie: {self._format_display_amount(monnaie)} {get_currency(self.entreprise_id)}')
                    else:
                        # partial payment
                        pay_amount = float(amt)
                        self.vente_ctrl.add_payment(self.panier.id, pay_amount, method, user_id=getattr(self.current_user, 'id', None))
                        reste = total_final - pay_amount
                        QMessageBox.information(dlg, 'Succès', f'Paiement partiel de {self._format_display_amount(pay_amount)} {get_currency(self.entreprise_id)} enregistré ({method}). Reste: {self._format_display_amount(reste)} {get_currency(self.entreprise_id)}')
                    # --- Nouvel ajout: fermer le panier même en cas de paiement partiel ---
                    # payment status is handled by VenteController.add_payment (payment_method)
                    # after payment, if panier has no products -> delete it and return to plan view
                    try:
                        items_after = self.controller.list_cart_items(self.panier.id) or []
                        if not items_after:
                            # delete empty panier -> free table
                            session = self.vente_ctrl.db.get_session()
                            from ayanna_erp.modules.restaurant.models.restaurant import RestauPanier, RestauPrintedInvoice
                            has_printed_invoice = False
                            pdel = session.query(RestauPanier).filter_by(id=self.panier.id).first()
                            if pdel:
                                has_printed_invoice = (
                                    session.query(RestauPrintedInvoice.id)
                                    .filter_by(panier_id=self.panier.id)
                                    .first()
                                    is not None
                                )
                                try:
                                    if has_printed_invoice:
                                        pdel.status = 'annule'
                                    else:
                                        session.delete(pdel)
                                    session.commit()
                                except Exception:
                                    session.rollback()
                                finally:
                                    session.close()
                            else:
                                session.close()
                            if has_printed_invoice:
                                QMessageBox.information(dlg, 'Info', 'Panier vide passé à annule (facture imprimée conservée)')
                            else:
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

    def _on_imprimer_clicked(self):
        """Génère et ouvre directement le ticket PDF dans le lecteur PDF par défaut"""
        if not self.panier:
            QMessageBox.information(self, 'Info', 'Aucun panier actif')
            return
        try:
            # Build invoice_data expected by InvoicePrintManager.print_receipt_53mm
            items = self.controller.list_cart_items(self.panier.id) or []
            invoice_items = []
            subtotal = 0.0
            for it in items:
                try:
                    prod = self.controller.get_product(getattr(it, 'product_id', None))
                    name = getattr(prod, 'name', str(getattr(it, 'product_id', '')))
                except Exception:
                    name = str(getattr(it, 'product_id', ''))
                qty = int(getattr(it, 'quantity', 0) or 0)
                unit_price = float(getattr(it, 'price', 0.0) or 0.0)
                line_total = float(getattr(it, 'total', qty * unit_price) or (qty * unit_price))
                subtotal += line_total
                invoice_items.append({
                    'name': name,
                    'quantity': qty,
                    'unit_price': unit_price,
                    'total': line_total
                })

            # payments list from DB
            payments_list = []
            try:
                db = get_database_manager()
                session = db.get_session()
                from ayanna_erp.modules.restaurant.models.restaurant import RestauPayment
                from ayanna_erp.database.database_manager import User as DBUser
                pays = session.query(RestauPayment).filter_by(panier_id=self.panier.id).all()
                for p in pays:
                    user_name = None
                    try:
                        if getattr(p, 'user_id', None):
                            u = session.query(DBUser).filter_by(id=p.user_id).first()
                            if u:
                                user_name = getattr(u, 'name', None) or getattr(u, 'email', None)
                    except Exception:
                        user_name = None
                    payments_list.append({
                        'amount': float(getattr(p, 'amount', 0.0) or 0.0),
                        'payment_method': getattr(p, 'payment_method', None),
                        'payment_date': getattr(p, 'created_at', None),
                        'user_name': user_name or ''
                    })
                try:
                    session.close()
                except Exception:
                    pass
            except Exception:
                payments_list = []

            # Résoudre table / salle et serveuse
            try:
                db = get_database_manager()
                session = db.get_session()
                from ayanna_erp.modules.restaurant.models.restaurant import RestauTable
                tbl_obj = session.query(RestauTable).filter_by(id=self.table_id).first()
                if tbl_obj:
                    tbl_display = str(getattr(tbl_obj, 'number', self.table_id))
                    try:
                        salle_obj = getattr(tbl_obj, 'salle', None)
                        salle_name = getattr(salle_obj, 'name', None) if salle_obj is not None else None
                    except Exception:
                        salle_name = None
                else:
                    tbl_display = str(self.table_id)
                    salle_name = None
                try:
                    session.close()
                except Exception:
                    pass
            except Exception:
                tbl_display = str(self.table_id)
                salle_name = None

            # Résoudre serveuse
            serveuse_name = ''
            try:
                if getattr(self.panier, 'serveuse_id', None):
                    db = get_database_manager()
                    session = db.get_session()
                    from ayanna_erp.database.database_manager import User as DBUser
                    u = session.query(DBUser).filter_by(id=self.panier.serveuse_id).first()
                    if u:
                        serveuse_name = getattr(u, 'name', None) or getattr(u, 'email', None) or ''
                    try:
                        session.close()
                    except Exception:
                        pass
            except Exception:
                serveuse_name = ''

            # Calculer le net
            try:
                remise_val = float(getattr(self.panier, 'remise_amount', 0.0) or 0.0)
            except Exception:
                remise_val = 0.0
            total_net_computed = subtotal - remise_val

            invoice_data = {
                'module': 'restaurant',
                'reference': f"FAC-{self.panier.id}",
                'client_nom': '',
                'order_date': getattr(self.panier, 'created_at', None),
                'items': invoice_items,
                'subtotal_ht': subtotal,
                'discount_amount': float(remise_val),
                'total_net': float(total_net_computed),
                'notes': getattr(self.panier, 'notes', '') or '',
                'table': tbl_display,
                'salle': salle_name,
                'serveuse': serveuse_name,
                'comptoiriste': getattr(self.current_user, 'name', '')
            }

            # Résoudre le nom du client
            try:
                if getattr(self.panier, 'client_id', None):
                    db = get_database_manager()
                    session = db.get_session()
                    from ayanna_erp.modules.boutique.model.models import ShopClient
                    c = session.query(ShopClient).filter_by(id=self.panier.client_id).first()
                    if c:
                        invoice_data['client_nom'] = (getattr(c, 'nom', '') or '') + ' ' + (getattr(c, 'prenom', '') or '')
                    try:
                        session.close()
                    except Exception:
                        pass
            except Exception:
                pass

            # Récupérer les infos de paiement
            try:
                payment_info = self.vente_ctrl.get_payment_info(self.panier.id)
                invoice_data.update({
                    'payment_status': payment_info.get('payment_status', 'NON PAYÉE'),
                    'change': payment_info.get('change', 0.0),
                    'reste_a_payer': payment_info.get('reste_a_payer', 0.0)
                })
            except Exception as e:
                print(f"Erreur récupération infos paiement: {e}")
                invoice_data.update({
                    'payment_status': 'NON PAYÉE',
                    'change': 0.0,
                    'reste_a_payer': 0.0
                })

            # Générer le PDF et l'ouvrir directement
            try:
                from ayanna_erp.modules.boutique.utils.invoice_printer import InvoicePrintManager
                import tempfile
                import os
                import subprocess
                import platform
                
                mgr = InvoicePrintManager(enterprise_id=self.entreprise_id)
                tmpf = tempfile.NamedTemporaryFile(prefix='ticket_', suffix='.pdf', delete=False)
                tmpf.close()
                filename = mgr.print_receipt_53mm(invoice_data, payments_list, getattr(self.current_user, 'name', ''), tmpf.name)

                # Capturer chaque impression de facture (1 impression = 1 enregistrement)
                try:
                    self.printed_invoices_ctrl.record_printed_invoice(
                        panier_id=self.panier.id,
                        printed_by_user_id=getattr(self.current_user, 'id', None),
                    )
                except Exception:
                    # La generation du ticket ne doit pas etre bloquee par ce tracking
                    pass
                
                # Ouvrir directement le PDF avec le lecteur par défaut
                try:
                    system = platform.system()
                    if system == "Windows":
                        os.startfile(filename)
                    elif system == "Darwin":  # macOS
                        subprocess.run(["open", filename], check=True)
                    elif system == "Linux":
                        subprocess.run(["xdg-open", filename], check=True)
                except Exception as e:
                    QMessageBox.information(self, 'Ticket généré', f'Ticket enregistré: {filename}')
            except Exception as e:
                QMessageBox.critical(self, 'Erreur', f"Impossible de générer le ticket: {e}")
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Erreur lors de l'impression du ticket: {e}")

    def _on_bon_commande_clicked(self):
        if not self.panier:
            QMessageBox.information(self, 'Info', 'Aucun panier actif')
            return

        serveuse_id = getattr(self.panier, 'serveuse_id', None)
        if not serveuse_id:
            QMessageBox.information(self, 'Info', 'Veuillez sélectionner une serveuse avant d\'imprimer le bon de commande.')
            return

        client_id = getattr(self.panier, 'client_id', None)
        success, result, pending_items = self.bon_commande_ctrl.create_bon_commande(
            panier_id=self.panier.id,
            user_id=getattr(self.current_user, 'id', None),
            client_id=client_id,
            serveuse_id=serveuse_id,
        )

        if not success:
            if result == 'SERVEUSE_REQUIRED':
                QMessageBox.information(self, 'Info', 'Veuillez sélectionner une serveuse avant d\'imprimer le bon de commande.')
                return
            if result == 'NO_NEW_ITEMS':
                QMessageBox.information(self, 'Info', 'Aucun nouveau produit à envoyer en cuisine.')
                return
            QMessageBox.critical(self, 'Erreur', f"Impossible de créer le bon de commande: {result}")
            return

        bon = result
        try:
            # Résoudre table / serveuse pour le ticket
            table_display = str(self.table_id)
            try:
                db = get_database_manager()
                session = db.get_session()
                from ayanna_erp.modules.restaurant.models.restaurant import RestauTable
                tbl_obj = session.query(RestauTable).filter_by(id=self.table_id).first()
                if tbl_obj:
                    table_display = str(getattr(tbl_obj, 'number', self.table_id))
                session.close()
            except Exception:
                pass

            serveuse_name = ''
            try:
                if getattr(self.panier, 'serveuse_id', None):
                    db = get_database_manager()
                    session = db.get_session()
                    from ayanna_erp.database.database_manager import User as DBUser
                    u = session.query(DBUser).filter_by(id=self.panier.serveuse_id).first()
                    if u:
                        serveuse_name = getattr(u, 'name', None) or getattr(u, 'email', None) or ''
                    session.close()
            except Exception:
                pass

            # Résoudre le nom du client
            client_name = ''
            try:
                if getattr(self.panier, 'client_id', None):
                    db = get_database_manager()
                    session = db.get_session()
                    from ayanna_erp.modules.boutique.model.models import ShopClient
                    c = session.query(ShopClient).filter_by(id=self.panier.client_id).first()
                    if c:
                        nom = getattr(c, 'nom', '') or ''
                        prenom = getattr(c, 'prenom', '') or ''
                        client_name = f"{nom} {prenom}".strip()
                    session.close()
            except Exception:
                pass

            ticket_data = {
                'numero_bon': getattr(bon, 'numero_bon', 'N/A'),
                'serveuse': serveuse_name,
                'serveuse_name': serveuse_name,
                'table': table_display,
                'panier_id': getattr(bon, 'restau_panier_id', ''),
                'created_at': getattr(bon, 'created_at', None),
                'client_name': client_name,
                'items': pending_items or [],
            }

            tmpf = None
            try:
                import tempfile
                tmpf = tempfile.NamedTemporaryFile(prefix='bon_commande_', suffix='.pdf', delete=False)
                tmpf.close()
                filename = self.bon_commande_printer.print_ticket(ticket_data, tmpf.name)

                printed, error_message = self._print_pdf_with_default_printer(filename)
                if printed:
                    parent = self.parent()
                    while parent is not None:
                        if hasattr(parent, '_confirm_after_print_action') and callable(parent._confirm_after_print_action):
                            parent._confirm_after_print_action()
                            break
                        parent = parent.parent()
                    else:
                        QMessageBox.information(self, 'Bon de commande', 'Bon de commande envoyé à l\'imprimante par défaut.')
                        self._return_to_vente_view()
                else:
                    if error_message:
                        QMessageBox.critical(self, 'Erreur d\'impression', f"Impossible d\'imprimer automatiquement le bon de commande:\n{error_message}")
                    else:
                        QMessageBox.critical(self, 'Erreur d\'impression', 'Impossible d\'imprimer automatiquement le bon de commande.')
            except Exception as e:
                QMessageBox.critical(self, 'Erreur', f"Impossible d\'imprimer le bon de commande: {e}")
            finally:
                if tmpf is not None:
                    try:
                        os.unlink(tmpf.name)
                    except Exception:
                        pass
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Erreur impression bon de commande: {e}")


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
                self.total_label.setText(f"Total: 0 {get_currency(self.entreprise_id)}")
                return
            p = None
            try:
                p = self.vente_ctrl.get_panier(self.panier.id)
            except Exception:
                p = self.panier
            subtotal = float(getattr(p, 'subtotal', 0.0) or 0.0)
            remise = float(getattr(p, 'remise_amount', 0.0) or 0.0)
            total_final = float(getattr(p, 'total_final', subtotal - remise))
            self.total_label.setText(f"Total: {self._format_display_amount(total_final)} {get_currency(self.entreprise_id)}")
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

    # currency/format helpers moved to ayanna_erp.utils.formatting (format_amount, get_currency)

    def _category_color(self, category_name: str = None, category_id: int = None):
        """Return a deterministic color for a category.

        Preference order: known name mapping -> color palette by id or name hash.
        This avoids many categories having the same fallback color.
        """
        try:
            # explicit mapping for well-known categories
            known = {
                'Bière': '#F44336',
                'Vin': '#9C27B0',
                'Sucré': '#4CAF50',
                'Whisky': '#3F51B5',
                'Autres': '#FFEB3B',
                'Champagne': '#FF4081',
                'Cuisine': '#00BCD4'
            }
            if category_name:
                # normalize for lookup (case-insensitive)
                name = str(category_name).strip()
                lname = name.lower()
                # check known mapping case-insensitively
                for k, v in known.items():
                    if k.lower() == lname:
                        return v

            # palette of distinct colors for fallback
            palette = [
                '#F44336', '#9C27B0', '#4CAF50', '#3F51B5', '#FF9800',
                '#009688', '#FF4081', '#00BCD4', '#8BC34A', '#795548',
                '#607D8B', '#CDDC39', '#E91E63', '#9E9E9E'
            ]
            key = None
            if category_id is not None:
                key = int(category_id)
            elif category_name:
                key = abs(hash(category_name))
            if key is None:
                return palette[0]
            return palette[int(key) % len(palette)]
        except Exception:
            return '#B0BEC5'

    def _apply_cart_column_proportions(self):
        """Apply proportional widths to cart columns: Produit 45%, Qté 10%, Prix 15%, Total 30%."""
        try:
            # viewport width is the available width for columns
            total_w = self.cart_table.viewport().width()
            if total_w <= 0:
                return
            # compute pixel widths
            w_prod = int(total_w * 0.43)
            w_qte = int(total_w * 0.14)
            w_prix = int(total_w * 0.18)
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
