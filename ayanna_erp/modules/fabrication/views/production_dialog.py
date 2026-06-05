from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLabel, QComboBox, QDoubleSpinBox, QLineEdit, QTextEdit, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QDateTimeEdit, QHBoxLayout, QHeaderView
from decimal import Decimal
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
        self.setMinimumWidth(800)
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

        # Estimated quantity (read-only display) and timings
        self.produced_spin = QDoubleSpinBox()
        self.produced_spin.setDecimals(3)
        self.produced_spin.setMinimum(0)
        self.produced_spin.setMaximum(9999999)
        self.produced_spin.setEnabled(False)
        form.addRow(QLabel("Quantité estimée (calculée depuis consommations)"), self.produced_spin)

        self.start_dt = QDateTimeEdit()
        self.start_dt.setCalendarPopup(True)
        form.addRow(QLabel("Début"), self.start_dt)
        self.end_dt = QDateTimeEdit()
        self.end_dt.setCalendarPopup(True)
        form.addRow(QLabel("Fin"), self.end_dt)

        self.warehouse_combo = QComboBox()
        form.addRow(QLabel("Entrepôt"), self.warehouse_combo)

        self.operator_input = QLineEdit()
        form.addRow(QLabel("Opérateur"), self.operator_input)

        self.notes_input = QTextEdit()
        self.notes_input.setFixedHeight(60)
        form.addRow(QLabel("Notes"), self.notes_input)
        layout.addLayout(form)

        # Materials table (auto-filled from selected rule)
        # Columns: MP Nom, Qté requise, Qté consommée (required)
        self.items_table = QTableWidget(0, 3)
        self.items_table.setHorizontalHeaderLabels(["MP Nom", "Qté requise", "Qté consommée"])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(QLabel("Matières premières (calculées depuis la règle):"))
        layout.addWidget(self.items_table)

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
                prod_name = r.product.name if r.product else str(r.product_id)
                display = f"{r.id} — {prod_name} — Qté sortie:{r.output_quantity}"
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

            # connect change handlers
            self.rule_combo.currentIndexChanged.connect(self.on_rule_changed)
            self.qty_spin.valueChanged.connect(self.on_qty_changed)
            self.items_table.cellChanged.connect(self.on_items_table_cell_changed)

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

        # Validate consumed quantities are provided (Qté consommée required)
        for row in range(self.items_table.rowCount()):
            itm = self.items_table.item(row, 2)
            if not itm or not itm.text().strip():
                QMessageBox.warning(self, "Validation", "Veuillez saisir la quantité consommée pour toutes les matières premières.")
                return
            try:
                Decimal(str(itm.text()))
            except Exception:
                QMessageBox.warning(self, "Validation", "Format invalide pour une quantité consommée.")
                return

        session = self.db.get_session()
        try:
            created_by = None
            if isinstance(self.current_user, dict):
                created_by = self.current_user.get('id')

            prod = self.controller.create_production(session, fabrication_rule_id=int(rule_id), planned_quantity=qty, warehouse_id=int(warehouse_id), operator_name=operator, created_by=created_by, notes=notes)
            try:
                if self.start_dt.dateTime():
                    prod.start_time = self.start_dt.dateTime().toPyDateTime()
                if self.end_dt.dateTime():
                    prod.end_time = self.end_dt.dateTime().toPyDateTime()
            except Exception:
                pass

            # create ProductionItem records from items_table (planned/consumed)
            from ayanna_erp.modules.fabrication.models import ProductionItem
            # remove any existing items if present
            for row in range(self.items_table.rowCount()):
                try:
                    name_item = self.items_table.item(row, 0)
                    # raw_material_id stored in item data (role = UserRole + 2)
                    raw_id = int(name_item.data(int(Qt.ItemDataRole.UserRole) + 2))
                    planned_q = Decimal(str(self.items_table.item(row, 1).text() or '0'))
                    consumed_q = Decimal(str(self.items_table.item(row, 2).text()))
                    pi = ProductionItem(production_id=prod.id, raw_material_id=raw_id, planned_quantity=planned_q, consumed_quantity=consumed_q)
                    session.add(pi)
                except Exception:
                    continue
            session.commit()
            QMessageBox.information(self, "Succès", f"Production créée (ID {prod.id})")
            self.accept()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", f"Erreur création production: {e}")
        finally:
            session.close()

    def on_rule_changed(self):
        self._populate_items_from_rule()

    def on_qty_changed(self):
        self._populate_items_from_rule()

    def on_items_table_cell_changed(self, row, column):
        # only respond to consumed column edits (index 2)
        try:
            if column != 2:
                return
            self._recompute_estimated_qty(single_row=row)
        except Exception as e:
            QMessageBox.warning(self, "Erreur mise à jour composants", f"{e}")

    def _populate_items_from_rule(self):
        # Fill items_table using selected rule and current planned qty
        rule_id = self.rule_combo.currentData()
        planned_qty = Decimal(str(self.qty_spin.value()))
        session = self.db.get_session()
        try:
            self.items_table.setRowCount(0)
            if not rule_id:
                return
            rule = session.query(FabricationRule).filter_by(id=int(rule_id)).first()
            if not rule:
                return
            out_qty = Decimal(str(rule.output_quantity or 1))
            # populate rows; block signals to avoid triggering cellChanged
            self.items_table.blockSignals(True)
            for it in (rule.items or []):
                required_per_unit = Decimal(str(it.quantity_required or 0))
                required_total = (required_per_unit * planned_qty) / (out_qty or Decimal('1'))
                row = self.items_table.rowCount()
                self.items_table.insertRow(row)
                # Column 0: MP name (store metadata here)
                name = it.raw_material.name if it.raw_material else str(it.raw_material_id)
                itm0 = QTableWidgetItem(name)
                # Column 1: required total
                itm1 = QTableWidgetItem(str(required_total))
                # Column 2: consumed (user must fill)
                itm2 = QTableWidgetItem("")
                self.items_table.setItem(row, 0, itm0)
                self.items_table.setItem(row, 1, itm1)
                self.items_table.setItem(row, 2, itm2)
                # store required_per_unit and rule output qty and raw id in item data of name cell
                try:
                    itm0.setData(Qt.ItemDataRole.UserRole, float(required_per_unit))
                    itm0.setData(int(Qt.ItemDataRole.UserRole) + 1, float(out_qty))
                    itm0.setData(int(Qt.ItemDataRole.UserRole) + 2, int(it.raw_material_id))
                except Exception:
                    pass
            self.items_table.blockSignals(False)
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de remplir composants: {e}")
        finally:
            session.close()

    # legacy loss calculation removed; losses are not displayed in creation dialog

    def _recompute_estimated_qty(self, single_row: int = None):
        # Estimate finished product quantity from consumed MPs.
        rows = range(self.items_table.rowCount()) if single_row is None else [single_row]
        estimates = []
        for r in rows:
            item0 = self.items_table.item(r, 0)
            if not item0:
                continue
            try:
                req_per_unit = Decimal(str(item0.data(Qt.ItemDataRole.UserRole) or 0))
                out_qty = Decimal(str(item0.data(int(Qt.ItemDataRole.UserRole) + 1) or 1))
            except Exception:
                continue
            if req_per_unit == 0:
                continue
            try:
                cons_text = (self.items_table.item(r, 2).text() if self.items_table.item(r, 2) else '0')
                consumed_input = Decimal(str(cons_text or '0'))
            except Exception:
                consumed_input = Decimal('0')
            try:
                est = (consumed_input * out_qty) / req_per_unit
            except Exception:
                est = Decimal('0')
            estimates.append(est)

        estimated = min(estimates) if estimates else Decimal('0')
        try:
            self.produced_spin.setValue(float(estimated))
        except Exception:
            self.produced_spin.setValue(0.0)
