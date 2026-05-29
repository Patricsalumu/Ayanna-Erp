from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QListWidget, QMessageBox, QDialog, QFormLayout, QLineEdit, QSpinBox, QTextEdit
from ayanna_erp.modules.fabrication.controllers.fabrication_controller import FabricationController
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.fabrication.models import FabricationRule
from decimal import Decimal
from sqlalchemy import text

class NomenclatureWidget(QWidget):
    def __init__(self, pos_id=None, current_user=None):
        super().__init__()
        self.pos_id = pos_id
        self.current_user = current_user
        self.db = DatabaseManager()
        self.fc = FabricationController()
        self.setup_ui()
        self.load_rules()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        btn_layout = QHBoxLayout()
        self.new_btn = QPushButton("Nouvelle règle")
        self.new_btn.clicked.connect(self.open_new_rule)
        btn_layout.addWidget(self.new_btn)
        layout.addLayout(btn_layout)

        self.rules_list = QListWidget()
        layout.addWidget(self.rules_list)

    def load_rules(self):
        self.rules_list.clear()
        session = self.db.get_session()
        try:
            rules = session.query(FabricationRule).order_by(FabricationRule.id.desc()).all()
            for r in rules:
                self.rules_list.addItem(f"Règle #{r.id} - Produit {r.product_id} - Qte sortie {r.output_quantity}")
        except Exception as e:
            print(f"Erreur chargement règles: {e}")
        finally:
            session.close()

    def open_new_rule(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Nouvelle règle de fabrication")
        form = QFormLayout(dialog)
        product_input = QLineEdit()
        qty_input = QSpinBox()
        qty_input.setRange(1, 100000)
        duration_input = QSpinBox()
        duration_input.setRange(0, 100000)
        notes_input = QTextEdit()
        form.addRow("Product ID:", product_input)
        form.addRow("Output quantity:", qty_input)
        form.addRow("Estimated duration (min):", duration_input)
        form.addRow("Notes:", notes_input)
        btn_save = QPushButton("Enregistrer")
        btn_save.clicked.connect(lambda: self.save_rule(dialog, product_input, qty_input, duration_input, notes_input))
        form.addRow(btn_save)
        dialog.exec()

    def save_rule(self, dialog, product_input, qty_input, duration_input, notes_input):
        try:
            product_id = int(product_input.text())
            out_q = Decimal(str(qty_input.value()))
            duration = int(duration_input.value())
            notes = notes_input.toPlainText().strip()
            session = self.db.get_session()
            rule = self.fc.create_rule(session, product_id=product_id, output_quantity=out_q, estimated_duration_minutes=duration, notes=notes, created_by=(self.current_user.get('id') if isinstance(self.current_user, dict) else None))
            QMessageBox.information(self, "Succès", f"Règle créée (ID {rule.id})")
            dialog.accept()
            self.load_rules()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
