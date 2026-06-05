from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QTextEdit, QDoubleSpinBox, QPushButton, QHBoxLayout, QMessageBox, QTableWidget, QTableWidgetItem, QFileDialog, QDateTimeEdit
from PyQt6.QtCore import Qt
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.fabrication.models import Production, FabricationRuleItem, ProductionItem
from ayanna_erp.modules.fabrication.controllers.fabrication_controller import FabricationController
from decimal import Decimal
from datetime import datetime
from ayanna_erp.modules.fabrication.print_export import export_production_pdf
from sqlalchemy.orm import joinedload
from ayanna_erp.modules.fabrication.models import FabricationRule


class ProductionDetailDialog(QDialog):
    def __init__(self, production_id: int, pos_id=None, current_user=None, parent=None):
        super().__init__(parent)
        self.production_id = production_id
        self.pos_id = pos_id
        self.current_user = current_user or {}
        self.db = DatabaseManager()
        self.controller = FabricationController()
        self.setWindowTitle(f"Fiche production #{production_id}")
        self.setMinimumWidth(600)
        self.load_production()
        self.setup_ui()

    def load_production(self):
        session = self.db.get_session()
        try:
            # eager load related product, rule and items to avoid detached-instance lazy loads
            self.prod = session.query(Production).options(
                joinedload(Production.product),
                joinedload(Production.rule).joinedload(FabricationRule.items).joinedload(FabricationRuleItem.raw_material),
                joinedload(Production.items)
            ).filter_by(id=self.production_id).first()
            if not self.prod:
                raise Exception("Production introuvable")
            # load rule items
            self.rule = self.prod.rule
            self.items = self.rule.items if self.rule else []
            # load existing production items map
            self.prod_items_map = {pi.raw_material_id: pi for pi in (self.prod.items or [])}
        finally:
            session.close()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.code_label = QLabel(self.prod.production_code or "")
        form.addRow(QLabel("Code"), self.code_label)

        product_name = self.prod.product.name if getattr(self.prod, 'product', None) else str(self.prod.product_id)
        form.addRow(QLabel("Produit"), QLabel(product_name))

        self.status_label = QLabel(self.prod.status or "")
        form.addRow(QLabel("Statut"), self.status_label)

        self.planned_spin = QDoubleSpinBox()
        self.planned_spin.setDecimals(3)
        self.planned_spin.setMinimum(0.0)
        self.planned_spin.setMaximum(99999999)
        self.planned_spin.setValue(float(self.prod.planned_quantity or 0))
        form.addRow(QLabel("Quantité prévue"), self.planned_spin)

        self.produced_spin = QDoubleSpinBox()
        self.produced_spin.setDecimals(3)
        self.produced_spin.setMinimum(0.0)
        self.produced_spin.setMaximum(99999999)
        self.produced_spin.setValue(float(self.prod.produced_quantity or 0))
        form.addRow(QLabel("Quantité produite"), self.produced_spin)

        self.operator_input = QLineEdit(self.prod.operator_name or "")
        form.addRow(QLabel("Opérateur"), self.operator_input)

        # End time (allow user to indicate actual end of production)
        self.end_dt = QDateTimeEdit()
        self.end_dt.setCalendarPopup(True)
        try:
            if getattr(self.prod, 'end_time', None):
                self.end_dt.setDateTime(self.prod.end_time)
        except Exception:
            pass
        form.addRow(QLabel("Fin (heure de fin production)"), self.end_dt)

        self.notes_input = QTextEdit(self.prod.notes or "")
        form.addRow(QLabel("Notes"), self.notes_input)

        layout.addLayout(form)

        # Raw materials table
        self.rm_table = QTableWidget()
        self.rm_table.setColumnCount(4)
        self.rm_table.setHorizontalHeaderLabels(["MP ID", "Matière première", "Qté prévue", "Qté consommée"])
        self.rm_table.setRowCount(len(self.items))
        self.consumed_inputs = {}
        for row, item in enumerate(self.items):
            rm = item.raw_material
            name = rm.name if rm else str(item.raw_material_id)
            planned = (Decimal(str(item.quantity_required)) * Decimal(str(self.prod.planned_quantity))) / Decimal(str(self.rule.output_quantity or 1))
            # existing consumed
            existing = self.prod_items_map.get(item.raw_material_id)
            consumed_val = float(existing.consumed_quantity) if existing else float(planned)

            self.rm_table.setItem(row, 0, QTableWidgetItem(str(item.raw_material_id)))
            self.rm_table.setItem(row, 1, QTableWidgetItem(name))
            self.rm_table.setItem(row, 2, QTableWidgetItem(str(planned)))
            spin = QDoubleSpinBox()
            spin.setDecimals(3)
            spin.setMinimum(0.0)
            spin.setMaximum(99999999)
            spin.setValue(consumed_val)
            self.rm_table.setCellWidget(row, 3, spin)
            self.consumed_inputs[item.raw_material_id] = spin

        layout.addWidget(QLabel("Consommation matières premières"))
        layout.addWidget(self.rm_table)

        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Enregistrer")
        self.save_btn.clicked.connect(self.on_save)
        self.validate_btn = QPushButton("Valider la production")
        self.validate_btn.clicked.connect(self.on_validate)
        self.print_a4_btn = QPushButton("Imprimer A4")
        self.print_a4_btn.clicked.connect(self.on_print_a4)
        self.print_80_btn = QPushButton("Imprimer 80mm")
        self.print_80_btn.clicked.connect(self.on_print_80)
        self.close_btn = QPushButton("Fermer")
        self.close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.validate_btn)
        btn_layout.addWidget(self.print_a4_btn)
        btn_layout.addWidget(self.print_80_btn)
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)

    def on_save(self):
        session = self.db.get_session()
        try:
            prod = session.query(Production).filter_by(id=self.production_id).first()
            if not prod:
                raise Exception("Production introuvable")
            prod.planned_quantity = Decimal(str(self.planned_spin.value()))
            prod.operator_name = self.operator_input.text().strip() or None
            prod.notes = self.notes_input.toPlainText().strip() or None
            session.commit()
            QMessageBox.information(self, "Succès", "Production mise à jour")
            self.status_label.setText(prod.status or "")
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", f"Impossible d'enregistrer: {e}")
        finally:
            session.close()

    def on_validate(self):
        # gather consumed quantities
        consumed = {}
        for raw_id, spin in self.consumed_inputs.items():
            consumed[raw_id] = float(spin.value())

        produced_q = float(self.produced_spin.value())

        # Ensure user indicates an end time before validation when not already set
        chosen_end = None
        if not getattr(self.prod, 'end_time', None):
            chosen_end = self._ask_for_end_time()
            if chosen_end is None:
                QMessageBox.warning(self, "Annulé", "Veuillez indiquer l'heure de fin de production pour valider.")
                return
        else:
            chosen_end = self.end_dt.dateTime().toPyDateTime()

        session = self.db.get_session()
        try:
            validated_by = None
            if isinstance(self.current_user, dict):
                validated_by = self.current_user.get('id')

            # call controller validate_production with the user-provided end_time
            prod = self.controller.validate_production(session, self.production_id, produced_q, consumed, validated_by=validated_by, end_time=chosen_end)
            QMessageBox.information(self, "Succès", f"Production validée (ID {prod.id})")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Échec validation: {e}")
        finally:
            try:
                session.close()
            except Exception:
                pass

    def _ask_for_end_time(self):
        # Dialog to request the end time from user
        dlg = QDialog(self)
        dlg.setWindowTitle("Indiquer heure de fin")
        v = QVBoxLayout(dlg)
        info = QLabel("Aucune heure de fin renseignée. Veuillez indiquer l'heure de fin réelle de la production:")
        v.addWidget(info)
        dt = QDateTimeEdit()
        dt.setCalendarPopup(True)
        dt.setDateTime(datetime.utcnow())
        v.addWidget(dt)
        btns = QHBoxLayout()
        ok = QPushButton("OK")
        cancel = QPushButton("Annuler")
        btns.addWidget(ok)
        btns.addWidget(cancel)
        v.addLayout(btns)

        result = {'ok': False}

        def on_ok():
            result['ok'] = True
            dlg.accept()

        def on_cancel():
            dlg.reject()

        ok.clicked.connect(on_ok)
        cancel.clicked.connect(on_cancel)

        if dlg.exec() and result['ok']:
            return dt.dateTime().toPyDateTime()
        return None

    def on_print_a4(self):
        path, _ = QFileDialog.getSaveFileName(self, "Enregistrer PDF A4", f"production_{self.production_id}.pdf", "PDF Files (*.pdf)")
        if not path:
            return
        ok = export_production_pdf(self.production_id, path, paper='A4')
        if ok:
            QMessageBox.information(self, "Impression", f"PDF A4 enregistré: {path}")
        else:
            QMessageBox.critical(self, "Erreur", "Échec export PDF A4")

    def on_print_80(self):
        path, _ = QFileDialog.getSaveFileName(self, "Enregistrer PDF 80mm", f"production_{self.production_id}_80mm.pdf", "PDF Files (*.pdf)")
        if not path:
            return
        ok = export_production_pdf(self.production_id, path, paper='80mm')
        if ok:
            QMessageBox.information(self, "Impression", f"PDF 80mm enregistré: {path}")
        else:
            QMessageBox.critical(self, "Erreur", "Échec export PDF 80mm")
