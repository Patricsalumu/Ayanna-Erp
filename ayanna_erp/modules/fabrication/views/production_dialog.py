from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLabel, QComboBox, QDoubleSpinBox, QLineEdit, QTextEdit, QPushButton, QMessageBox
from PyQt6.QtCore import Qt
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.fabrication.models import FabricationRule
from ayanna_erp.modules.stock.models import StockWarehouse
from ayanna_erp.modules.fabrication.controllers.fabrication_controller import FabricationController


class ProductionDialog(QDialog):
    def __init__(self, pos_id=None, current_user=None, parent=None):
        super().__init__(parent)
        self.pos_id = pos_id
        self.current_user = current_user or {}
        self.db = DatabaseManager()
        self.controller = FabricationController()
        self.setWindowTitle("Nouvelle production")
        self.setMinimumWidth(480)
        self.setup_ui()
        self.load_defaults()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.rule_combo = QComboBox()
        form.addRow(QLabel("Règle de fabrication"), self.rule_combo)

        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setDecimals(3)
        self.qty_spin.setMinimum(0.001)
        self.qty_spin.setMaximum(9999999)
        form.addRow(QLabel("Quantité prévue"), self.qty_spin)

        self.warehouse_combo = QComboBox()
        form.addRow(QLabel("Entrepôt"), self.warehouse_combo)

        self.operator_input = QLineEdit()
        form.addRow(QLabel("Opérateur"), self.operator_input)

        self.notes_input = QTextEdit()
        form.addRow(QLabel("Notes"), self.notes_input)

        layout.addLayout(form)

        btn_layout = QVBoxLayout()
        self.create_btn = QPushButton("Créer la production")
        self.create_btn.clicked.connect(self.on_create)
        self.cancel_btn = QPushButton("Annuler")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.create_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def load_defaults(self):
        session = self.db.get_session()
        try:
            rules = session.query(FabricationRule).order_by(FabricationRule.id.desc()).all()
            self.rule_combo.clear()
            for r in rules:
                display = f"{r.id} — Produit:{r.product_id} — Qté sortie:{r.output_quantity}"
                self.rule_combo.addItem(display, r.id)

            whs = session.query(StockWarehouse).order_by(StockWarehouse.name).all()
            self.warehouse_combo.clear()
            for w in whs:
                self.warehouse_combo.addItem(w.name or str(w.id), w.id)

            # defaults
            if self.pos_id:
                # try to select warehouse matching pos_id
                idx = self.warehouse_combo.findData(self.pos_id)
                if idx >= 0:
                    self.warehouse_combo.setCurrentIndex(idx)

            # operator default from current_user
            self.operator_input.setText(self.current_user.get('username','') if isinstance(self.current_user, dict) else '')

        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de charger données: {e}")
        finally:
            session.close()

    def on_create(self):
        rule_id = self.rule_combo.currentData()
        qty = float(self.qty_spin.value())
        warehouse_id = self.warehouse_combo.currentData()
        operator = self.operator_input.text().strip() or None
        notes = self.notes_input.toPlainText().strip() or None

        if not rule_id:
            QMessageBox.warning(self, "Validation", "Veuillez sélectionner une règle de fabrication.")
            return
        if qty <= 0:
            QMessageBox.warning(self, "Validation", "Veuillez saisir une quantité valide.")
            return

        session = self.db.get_session()
        try:
            created_by = None
            if isinstance(self.current_user, dict):
                created_by = self.current_user.get('id')

            prod = self.controller.create_production(session, fabrication_rule_id=int(rule_id), planned_quantity=qty, warehouse_id=int(warehouse_id), operator_name=operator, created_by=created_by, notes=notes)
            QMessageBox.information(self, "Succès", f"Production créée (ID {prod.id})")
            self.accept()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", f"Erreur création production: {e}")
        finally:
            session.close()
