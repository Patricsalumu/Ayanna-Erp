from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QListWidget, QMessageBox, QDialog, QFormLayout, QLineEdit, QSpinBox
from ayanna_erp.modules.fabrication.controllers.fabrication_controller import FabricationController
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.fabrication.models import Production
from decimal import Decimal
from sqlalchemy import text

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
            res = session.execute(text("SELECT id, production_code, status, product_id, planned_quantity FROM productions ORDER BY id DESC")).fetchall()
            for r in res:
                self.prod_list.addItem(f"#{r[0]} {r[1]} - Produit {r[3]} - Qte {r[4]} - {r[2]}")
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
        # extract id from item text
        try:
            tid = int(sel.text().split()[0].lstrip('#'))
        except Exception:
            QMessageBox.critical(self, "Erreur", "Impossible de lire l'ID")
            return
        session = self.db.get_session()
        try:
            ok = self.fc.validate_production(session, production_id=tid, validated_by=(self.current_user.get('id') if isinstance(self.current_user, dict) else None))
            if ok:
                QMessageBox.information(self, "Succès", "Production validée")
                self.load_productions()
            else:
                QMessageBox.critical(self, "Erreur", "Validation a retourné False")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
        finally:
            session.close()
