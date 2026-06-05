from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTableWidget,
    QTableWidgetItem, QPushButton, QFileDialog, QMessageBox, QHeaderView, QCheckBox
)
from PyQt6.QtCore import Qt
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.core.models.core_products import CoreProduct, CoreProductCategory
from ayanna_erp.modules.stock.models import StockWarehouse, StockProduitEntrepot
from ayanna_erp.modules.fabrication.print_export import export_product_pdf, export_products_catalog_pdf
from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ComptabiliteController
from ayanna_erp.core.entreprise_controller import EntrepriseController


def _format_qty(val, unit: str = '', decimals: int = 3) -> str:
    try:
        v = float(val or 0)
        if decimals == 0:
            s = f"{int(v):,}".replace(',', ' ')
        else:
            s = f"{v:,.{decimals}f}".replace(',', ' ')
        if unit:
            return f"{s} {unit}"
        return s
    except Exception:
        return str(val or '')

# Mapping des types de produit vers des libellés humains
PRODUCT_TYPE_LABELS = {
    'resale_product': 'Achat / Revente',
    'raw_material': 'Matière première',
    'semi_finished': 'Semi fini',
    'finished_good': 'Produit fini',
    'consumable': 'Consommable interne',
}
from decimal import Decimal
from sqlalchemy import or_, func


class ArticlesWidget(QWidget):
    """Onglet Articles pour le module Fabrication
    Affiche tous les produits CoreProduct, avec filtres par catégorie, type, entrepôt et état de stock.
    Permet d'exporter les produits sélectionnés en PDF A4 ou 80mm.
    """

    def __init__(self, pos_id=None, current_user=None, parent=None):
        super().__init__(parent)
        self.pos_id = pos_id
        self.current_user = current_user
        self.db = DatabaseManager()
        self.setup_ui()
        self.load_initial_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Filtres
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel('Catégorie'))
        self.cat_combo = QComboBox()
        self.cat_combo.addItem('Tous', None)
        filter_layout.addWidget(self.cat_combo)

        filter_layout.addWidget(QLabel('Type'))
        self.type_combo = QComboBox()
        self.type_combo.addItem('Tous', None)
        self.type_combo.addItem('Produit acheté / revente', 'resale_product')
        self.type_combo.addItem('Matière première', 'raw_material')
        self.type_combo.addItem('Semi-fini', 'semi_finished')
        self.type_combo.addItem('Produit fini', 'finished_good')
        self.type_combo.addItem('Consommable interne', 'consumable')
        filter_layout.addWidget(self.type_combo)

        filter_layout.addWidget(QLabel('Entrepôt'))
        self.wh_combo = QComboBox()
        self.wh_combo.addItem('Tous', None)
        filter_layout.addWidget(self.wh_combo)

        filter_layout.addWidget(QLabel('Etat stock'))
        self.stock_combo = QComboBox()
        self.stock_combo.addItem('Tous', None)
        self.stock_combo.addItem('Rupture', 'rupture')
        self.stock_combo.addItem('Faible', 'faible')
        self.stock_combo.addItem('Normal', 'normal')
        filter_layout.addWidget(self.stock_combo)

        self.filter_btn = QPushButton('Filtrer')
        self.filter_btn.clicked.connect(self.load_products)
        filter_layout.addWidget(self.filter_btn)

        layout.addLayout(filter_layout)

        # Table
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(['ID', 'Code', 'Nom', 'Type', 'Prix', 'Stock', 'Stock min', 'Compte stock'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet('QTableWidget { background: white; alternate-background-color: #f9fbff; } QHeaderView::section { font-weight: bold; background: #ecf3ff; }')
        layout.addWidget(self.table)

        # Actions
        actions = QHBoxLayout()
        # Export options
        opts_layout = QHBoxLayout()
        self.chk_code = QCheckBox('Inclure code')
        self.chk_code.setChecked(True)
        opts_layout.addWidget(self.chk_code)
        self.chk_price = QCheckBox('Inclure prix')
        self.chk_price.setChecked(True)
        opts_layout.addWidget(self.chk_price)
        self.chk_account = QCheckBox('Inclure compte stock')
        self.chk_account.setChecked(True)
        opts_layout.addWidget(self.chk_account)
        self.chk_cover = QCheckBox('Inclure page de couverture')
        self.chk_cover.setChecked(True)
        opts_layout.addWidget(self.chk_cover)
        self.chk_paginate = QCheckBox('Pagination')
        self.chk_paginate.setChecked(True)
        opts_layout.addWidget(self.chk_paginate)
        layout.addLayout(opts_layout)
        self.export_a4_btn = QPushButton('Exporter sélection (A4)')
        self.export_a4_btn.clicked.connect(lambda: self.export_selected('A4'))
        actions.addWidget(self.export_a4_btn)

        self.export_80_btn = QPushButton('Exporter sélection (80mm)')
        self.export_80_btn.clicked.connect(lambda: self.export_selected('80mm'))
        actions.addWidget(self.export_80_btn)

        layout.addLayout(actions)

    def load_initial_data(self):
        # Charger catégories et entrepôts
        try:
            session = self.db.get_session()
            cats = session.query(CoreProductCategory).order_by(CoreProductCategory.name).all()
            for c in cats:
                self.cat_combo.addItem(c.name, c.id)

            whs = session.query(StockWarehouse).filter_by(is_active=True).all()
            for w in whs:
                self.wh_combo.addItem(f"{w.name}", w.id)

            session.close()
        except Exception:
            pass

        self.load_products()

    def _get_stock_for_product(self, session, product_id, warehouse_id=None):
        # Retourne (total_stock, min_stock)
        if warehouse_id:
            row = session.query(StockProduitEntrepot).filter_by(product_id=product_id, warehouse_id=warehouse_id).first()
            if row:
                return float(row.quantity or 0), float(row.min_stock_level or 0)
            return 0, 0

        # sum across warehouses
        total = session.query(func.COALESCE(func.SUM(StockProduitEntrepot.quantity), 0)).filter(StockProduitEntrepot.product_id == product_id).scalar() or 0
        minv = 0
        return float(total), float(minv)

    def load_products(self):
        self.table.setRowCount(0)
        try:
            session = self.db.get_session()
            query = session.query(CoreProduct).order_by(CoreProduct.name)

            cat_id = self.cat_combo.currentData()
            if cat_id:
                query = query.filter(CoreProduct.category_id == cat_id)

            ptype = self.type_combo.currentData()
            if ptype:
                query = query.filter(CoreProduct.product_type == ptype)

            products = query.all()

            wh_id = self.wh_combo.currentData()
            stock_filter = self.stock_combo.currentData()

            for p in products:
                total_stock, min_stock = self._get_stock_for_product(session, p.id, warehouse_id=wh_id)
                # Determine stock status
                status = 'normal'
                if total_stock == 0:
                    status = 'rupture'
                elif total_stock > 0 and min_stock and total_stock < min_stock:
                    status = 'faible'

                if stock_filter and stock_filter != status:
                    continue

                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(p.id)))
                self.table.setItem(row, 1, QTableWidgetItem(str(p.code or '')))
                self.table.setItem(row, 2, QTableWidgetItem(p.name or ''))
                ptype_label = PRODUCT_TYPE_LABELS.get(p.product_type, p.product_type or '')
                self.table.setItem(row, 3, QTableWidgetItem(ptype_label))
                # Price with currency
                try:
                    ent = EntrepriseController()
                    price_text = ent.format_amount(getattr(p, 'price_unit', 0))
                except Exception:
                    price_text = str(getattr(p, 'price_unit', 0))
                self.table.setItem(row, 4, QTableWidgetItem(price_text))

                # Stock quantities with units
                unit = getattr(p, 'unit', '') or ''
                stock_text = _format_qty(total_stock, unit=unit, decimals=3)
                min_text = _format_qty(min_stock, unit=unit, decimals=3)
                self.table.setItem(row, 5, QTableWidgetItem(stock_text))
                self.table.setItem(row, 6, QTableWidgetItem(min_text))
                # Resolve compte stock name/numero for display
                account_text = ''
                try:
                    if getattr(p, 'stock_account_id', None):
                        compta = ComptabiliteController()
                        with self.db.get_session() as s:
                            compta.session = s
                            compte = compta.get_compte_by_id(p.stock_account_id)
                            if compte:
                                account_text = f"{compte.numero} - {compte.nom}"
                            else:
                                account_text = str(p.stock_account_id)
                except Exception:
                    account_text = str(p.stock_account_id or '')
                item_acc = QTableWidgetItem(account_text)
                item_acc.setToolTip(account_text)
                self.table.setItem(row, 7, item_acc)

            session.close()
        except Exception as e:
            QMessageBox.warning(self, 'Erreur', f'Erreur chargement produits: {e}')

    def export_selected(self, paper='A4'):
        try:
            rows = sorted({idx.row() for idx in self.table.selectedIndexes()})
            if not rows:
                QMessageBox.information(self, 'Export', 'Aucun produit sélectionné')
                return

            product_ids = []
            for r in rows:
                item = self.table.item(r, 0)
                if item:
                    try:
                        product_ids.append(int(item.text()))
                    except Exception:
                        pass

            if not product_ids:
                QMessageBox.warning(self, 'Aucun produit', 'Veuillez sélectionner au moins un produit.')
                return

            out, _ = QFileDialog.getSaveFileName(self, 'Enregistrer le catalogue', f'products_catalog_{paper}.pdf', 'PDF Files (*.pdf)')
            if not out:
                return

            from ayanna_erp.modules.fabrication.print_export import export_products_catalog_pdf
            ok = export_products_catalog_pdf(
                product_ids,
                out,
                paper,
                include_code=self.chk_code.isChecked(),
                include_price=self.chk_price.isChecked(),
                include_account=self.chk_account.isChecked(),
                include_cover=self.chk_cover.isChecked(),
                paginate=self.chk_paginate.isChecked()
            )

            if ok:
                QMessageBox.information(self, 'Export terminé', f'Catalogue exporté : {out}')
            else:
                QMessageBox.critical(self, 'Erreur', 'Erreur pendant l\'export du catalogue.')

        except Exception as e:
            QMessageBox.warning(self, 'Export', f'Erreur export catalogue: {e}')
