from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QListWidget, QMessageBox, QDialog, QFormLayout, QLineEdit, QSpinBox, QListWidgetItem
from ayanna_erp.modules.fabrication.controllers.fabrication_controller import FabricationController
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.fabrication.models import Production, ProductionItem, FabricationRuleItem
from ayanna_erp.modules.core.models import CoreProduct
from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.orm import joinedload
from PyQt6.QtCore import Qt
from ayanna_erp.modules.fabrication.views.production_detail import ProductionDetailDialog

class ProductionsWidget(QWidget):
    def __init__(self, pos_id=None, current_user=None):
        super().__init__()
        self.pos_id = pos_id
        self.current_user = current_user
        self.db = DatabaseManager()
        self.fc = FabricationController()
        self.setup_ui()
        self.load_productions()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        btn_layout = QHBoxLayout()
        self.new_btn = QPushButton("Nouvelle production")
        self.new_btn.clicked.connect(self.open_new_production)
        btn_layout.addWidget(self.new_btn)
        self.validate_btn = QPushButton("Valider production sélectionnée")
        self.validate_btn.clicked.connect(self.validate_selected)
        btn_layout.addWidget(self.validate_btn)
        layout.addLayout(btn_layout)

        self.prod_list = QListWidget()
        layout.addWidget(self.prod_list)

    def load_productions(self):
        self.prod_list.clear()
        session = self.db.get_session()
        try:
            # load productions with related product and rule
            prods = session.query(Production).options(joinedload(Production.product), joinedload(Production.rule)).order_by(Production.id.desc()).all()
            for p in prods:
                # compute estimated quantity from consumed MP if items present
                estimated = Decimal('0')
                try:
                    estimates = []
                    for pi in (p.items or []):
                        # find matching rule item
                        rule_items = [ri for ri in (p.rule.items or []) if int(ri.raw_material_id) == int(pi.raw_material_id)] if p.rule else []
                        if not rule_items:
                            continue
                        ri = rule_items[0]
                        req = Decimal(str(ri.quantity_required or 0))
                        out_q = Decimal(str(p.rule.output_quantity or 1)) if p.rule else Decimal('1')
                        if req and pi.consumed_quantity:
                            est = (Decimal(str(pi.consumed_quantity)) * out_q) / req
                            estimates.append(est)
                    estimated = min(estimates) if estimates else Decimal('0')
                except Exception:
                    estimated = Decimal('0')

                prod_name = p.product.name if p.product else str(p.product_id)
                unit = p.product.unit if p.product and getattr(p.product, 'unit', None) else ''
                planned = f"{float(p.planned_quantity)} {unit}" if p.planned_quantity else f"0 {unit}"
                estimated_display = f"{float(estimated)} {unit}" if estimated else f"0 {unit}"
                # display status mapping: show 'encours' instead of 'draft'
                status = p.status
                if status == 'draft':
                    status = 'encours'
                item_text = f"{p.production_code or ''} - Produit {prod_name} - Qte prev: {planned} - Qte estime: {estimated_display} - {status}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, int(p.id))
                self.prod_list.addItem(item)
        finally:
            session.close()

    def open_new_production(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Créer production")
        form = QFormLayout(dialog)
        product_input = QLineEdit()
        qty_input = QSpinBox()
        qty_input.setRange(1, 100000)
        form.addRow("Fabrication Rule ID:", product_input)
        form.addRow("Quantity:", qty_input)
        btn_save = QPushButton("Créer")
        btn_save.clicked.connect(lambda: self.save_production(dialog, product_input, qty_input))
        form.addRow(btn_save)
        dialog.exec()

    def save_production(self, dialog, product_input, qty_input):
        try:
            fabrication_rule_id = int(product_input.text())
            qty = Decimal(str(qty_input.value()))
            session = self.db.get_session()
            prod = self.fc.create_production(session, fabrication_rule_id=fabrication_rule_id, planned_quantity=qty, warehouse_id=self.pos_id, created_by=(self.current_user.get('id') if isinstance(self.current_user, dict) else None))
            QMessageBox.information(self, "Succès", f"Production créée (ID {prod.id})")
            dialog.accept()
            self.load_productions()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def validate_selected(self):
        sel = self.prod_list.currentItem()
        if not sel:
            QMessageBox.warning(self, "Sélection", "Sélectionnez une production")
            return
        # extract id from item data
        try:
            tid = sel.data(Qt.ItemDataRole.UserRole)
        except Exception:
            QMessageBox.critical(self, "Erreur", "Impossible de lire l'ID")
            return
        # Open production detail dialog to allow user to set produced/consumptions and end time
        dlg = ProductionDetailDialog(production_id=tid, pos_id=self.pos_id, current_user=self.current_user, parent=self)
        if dlg.exec():
            # after possible validation, refresh list
            self.load_productions()
