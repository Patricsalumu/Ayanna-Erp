from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QListWidget, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QSpinBox, QTextEdit, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox
)
from PyQt6.QtGui import QColor, QBrush
from ayanna_erp.modules.fabrication.controllers.fabrication_controller import FabricationController
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.fabrication.models import FabricationRule, FabricationRuleItem
from ayanna_erp.modules.core.models import CoreProduct
from decimal import Decimal


class NomenclatureWidget(QWidget):
    """UI pour gérer les nomenclatures (règles de fabrication).

    - Les règles ne peuvent être créées que pour des produits de type 'finished_good'
    - On peut ajouter des items (matières premières) avec quantités et perte
    """

    def __init__(self, pos_id=None, current_user=None):
        super().__init__()
        self.pos_id = pos_id
        self.current_user = current_user or {}
        self.db = DatabaseManager()
        self.fc = FabricationController()
        self.setup_ui()
        self.load_rules()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        btn_layout = QHBoxLayout()
        self.new_btn = QPushButton("Nouvelle nomenclature")
        self.new_btn.clicked.connect(self.safe_open_new_rule)
        btn_layout.addWidget(self.new_btn)
        self.refresh_btn = QPushButton("Rafraîchir")
        self.refresh_btn.clicked.connect(self.load_rules)
        btn_layout.addWidget(self.refresh_btn)
        layout.addLayout(btn_layout)

        self.rules_list = QListWidget()
        self.rules_list.itemDoubleClicked.connect(self.open_edit_rule)
        layout.addWidget(self.rules_list)

    def load_rules(self):
        self.rules_list.clear()
        session = self.db.get_session()
        try:
            rules = session.query(FabricationRule).order_by(FabricationRule.id.desc()).all()
            for r in rules:
                prod_name = r.product.name if r.product else str(r.product_id)
                items_count = len(r.items or [])
                self.rules_list.addItem(f"Règle #{r.id} - {prod_name} - Qte sortie {r.output_quantity} - Items: {items_count}")
        except Exception as e:
            print(f"Erreur chargement règles: {e}")
        finally:
            session.close()

    def open_new_rule(self):
        self._open_rule_dialog()

    def safe_open_new_rule(self):
        try:
            self.open_new_rule()
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ouverture de la fenêtre de nomenclature:\n{str(e)}\n\n{tb}")

    def open_edit_rule(self, item):
        # extract id from item text (Règle #ID - ...)
        try:
            text = item.text()
            rid = int(text.split('#')[1].split()[0])
        except Exception:
            QMessageBox.warning(self, "Erreur", "Impossible d'ouvrir la règle sélectionnée")
            return
        self._open_rule_dialog(rule_id=rid)

    def _open_rule_dialog(self, rule_id: int = None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Nomenclature" if not rule_id else f"Éditer nomenclature #{rule_id}")
        form = QFormLayout(dialog)

        session = self.db.get_session()
        try:
            # product selection: finished or semi-finished products
            prod_select = QComboBox()
            prods = session.query(CoreProduct).filter(CoreProduct.product_type.in_(['finished_good', 'semi_finished'])).order_by(CoreProduct.name).all()
            prod_map = {}
            prod_select.addItem("-- Sélectionner --", -1)
            for p in prods:
                prod_select.addItem(f"{p.name} (ID:{p.id})", p.id)
                prod_map[p.id] = p

            qty_input = QSpinBox()
            qty_input.setRange(1, 1000000)
            duration_input = QSpinBox()
            duration_input.setRange(0, 1000000)
            notes_input = QTextEdit()

            form.addRow("Produit (fini ou semi-fini):", prod_select)
            form.addRow("Quantité sortie:", qty_input)
            form.addRow("Durée estimée (min):", duration_input)
            form.addRow("Notes:", notes_input)

            # Items table for raw materials
            form.addRow(QLabel("Composants (matières premières):"))
            items_table = QTableWidget(0, 4)
            items_table.setHorizontalHeaderLabels(["MP ID", "MP Nom", "Quantité requise", "Perte %"])
            items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            form.addRow(items_table)

            # Controls to add MP
            mp_add_layout = QHBoxLayout()
            mp_input = QComboBox()
            mp_input.addItem("-- Sélectionner MP --", -1)
            # load raw materials: raw materials and semi-finished products can be used as components
            mps = session.query(CoreProduct).filter(CoreProduct.product_type.in_(['raw_material', 'semi_finished'])).order_by(CoreProduct.name).all()
            mp_map = {}
            for m in mps:
                label = f"{m.name} (ID:{m.id})"
                if getattr(m, 'product_type', None) == 'semi_finished':
                    label += ' [Semi-fini]'
                mp_input.addItem(label, m.id)
                mp_map[m.id] = m
            mp_qty = QSpinBox()
            mp_qty.setRange(0, 1000000)
            mp_wast = QSpinBox()
            mp_wast.setRange(0, 100)
            add_mp_btn = QPushButton("Ajouter MP")
            def on_add_mp():
                mp_id = mp_input.currentData()
                if not mp_id or mp_id == -1:
                    QMessageBox.warning(dialog, "Erreur", "Sélectionnez une matière première")
                    return
                # ensure a product is selected as parent
                parent_prod_id = prod_select.currentData()
                if not parent_prod_id or parent_prod_id == -1:
                    QMessageBox.warning(dialog, "Erreur", "Sélectionnez d'abord le produit cible de la nomenclature")
                    return
                # prevent adding the product itself as component
                if int(mp_id) == int(parent_prod_id):
                    QMessageBox.warning(dialog, "Erreur", "Un produit ne peut pas contenir lui-même comme composant")
                    return
                # circular dependency check (parent -> ... -> candidate)
                def product_contains_target(sess, current_prod_id, target_prod_id, visited=None):
                    if visited is None:
                        visited = set()
                    if current_prod_id in visited:
                        return False
                    visited.add(current_prod_id)
                    # find rule for current_prod_id
                    rule = sess.query(FabricationRule).filter_by(product_id=current_prod_id).first()
                    if not rule:
                        return False
                    for it in (rule.items or []):
                        try:
                            child_id = int(it.raw_material_id)
                        except Exception:
                            continue
                        if child_id == target_prod_id:
                            return True
                        # if child has its own rule, recurse
                        if product_contains_target(sess, child_id, target_prod_id, visited):
                            return True
                    return False
                # check if candidate already contains parent (directly or indirectly)
                if product_contains_target(session, int(mp_id), int(parent_prod_id)):
                    QMessageBox.warning(dialog, "Erreur", "Ajout interdit: cela créerait une dépendance circulaire avec le produit sélectionné")
                    return
                row = items_table.rowCount()
                items_table.insertRow(row)
                items_table.setItem(row, 0, QTableWidgetItem(str(mp_id)))
                name = mp_map[mp_id].name
                is_semi = getattr(mp_map[mp_id], 'product_type', None) == 'semi_finished'
                if is_semi:
                    name = f"{name} [Semi-fini]"
                items_table.setItem(row, 1, QTableWidgetItem(name))
                items_table.setItem(row, 2, QTableWidgetItem(str(mp_qty.value())))
                items_table.setItem(row, 3, QTableWidgetItem(str(mp_wast.value())))
                # color the row if semi-finished
                if is_semi:
                    brush = QBrush(QColor('#fff4e6'))
                    for c in range(items_table.columnCount()):
                        itm = items_table.item(row, c)
                        if itm:
                            itm.setBackground(brush)
            add_mp_btn.clicked.connect(on_add_mp)
            mp_add_layout.addWidget(mp_input)
            mp_add_layout.addWidget(QLabel("Qté:"))
            mp_add_layout.addWidget(mp_qty)
            mp_add_layout.addWidget(QLabel("Perte %:"))
            mp_add_layout.addWidget(mp_wast)
            mp_add_layout.addWidget(add_mp_btn)
            form.addRow(mp_add_layout)

            # load existing rule if editing
            if rule_id:
                rule = session.query(FabricationRule).filter_by(id=rule_id).first()
                if rule:
                    # set selected product
                    idx = prod_select.findData(rule.product_id)
                    if idx >= 0:
                        prod_select.setCurrentIndex(idx)
                    qty_input.setValue(int(rule.output_quantity or 1))
                    duration_input.setValue(int(rule.estimated_duration_minutes or 0))
                    notes_input.setPlainText(rule.notes or '')
                    # load items
                    for it in (rule.items or []):
                        r = items_table.rowCount()
                        items_table.insertRow(r)
                        items_table.setItem(r, 0, QTableWidgetItem(str(it.raw_material_id)))
                        name = it.raw_material.name if it.raw_material else str(it.raw_material_id)
                        is_semi = getattr(it.raw_material, 'product_type', None) == 'semi_finished'
                        if is_semi:
                            name = f"{name} [Semi-fini]"
                        items_table.setItem(r, 1, QTableWidgetItem(name))
                        items_table.setItem(r, 2, QTableWidgetItem(str(it.quantity_required)))
                        items_table.setItem(r, 3, QTableWidgetItem(str(it.wastage_percent)))
                        if is_semi:
                            brush = QBrush(QColor('#fff4e6'))
                            for c in range(items_table.columnCount()):
                                itm = items_table.item(r, c)
                                if itm:
                                    itm.setBackground(brush)

            # Save/Cancel
            btn_layout = QHBoxLayout()
            save_btn = QPushButton("Enregistrer")
            cancel_btn = QPushButton("Annuler")
            btn_layout.addWidget(save_btn)
            btn_layout.addWidget(cancel_btn)
            form.addRow(btn_layout)

            def on_save():
                try:
                    prod_id = prod_select.currentData()
                    if not prod_id or prod_id == -1:
                        QMessageBox.warning(dialog, "Erreur", "Sélectionnez un produit (fini ou semi-fini)")
                        return
                    # ensure selected product is finished or semi-finished
                    selected = session.query(CoreProduct).filter_by(id=prod_id).first()
                    if not selected or selected.product_type not in ('finished_good', 'semi_finished'):
                        QMessageBox.warning(dialog, "Erreur", "Le produit sélectionné doit être fini ou semi-fini")
                        return
                    out_q = Decimal(str(qty_input.value()))
                    duration = int(duration_input.value())
                    notes = notes_input.toPlainText().strip()
                    # create or update rule
                    if rule_id:
                        # update existing
                        rule = session.query(FabricationRule).filter_by(id=rule_id).first()
                        if not rule:
                            QMessageBox.critical(dialog, "Erreur", "Règle introuvable")
                            return
                        rule.product_id = prod_id
                        rule.output_quantity = out_q
                        rule.estimated_duration_minutes = duration
                        rule.notes = notes
                        # remove existing items then add from table
                        session.query(FabricationRuleItem).filter_by(fabrication_rule_id=rule.id).delete()
                    else:
                        rule = FabricationRule(product_id=prod_id, output_quantity=out_q, estimated_duration_minutes=duration, notes=notes, created_by=(self.current_user.get('id') if isinstance(self.current_user, dict) else None))
                        session.add(rule)
                        session.flush()

                    # add items
                    for r in range(items_table.rowCount()):
                        raw_id = int(items_table.item(r, 0).text())
                        qreq = Decimal(str(items_table.item(r, 2).text() or '0'))
                        wast = Decimal(str(items_table.item(r, 3).text() or '0'))
                        fri = FabricationRuleItem(fabrication_rule_id=rule.id, raw_material_id=raw_id, quantity_required=qreq, wastage_percent=wast)
                        session.add(fri)

                    session.commit()
                    QMessageBox.information(dialog, "Succès", "Règle enregistrée")
                    dialog.accept()
                    self.load_rules()
                except Exception as e:
                    session.rollback()
                    QMessageBox.critical(dialog, "Erreur", str(e))

            save_btn.clicked.connect(on_save)
            cancel_btn.clicked.connect(dialog.reject)

            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur interne: {e}")
        finally:
            session.close()
