from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QDialog, QFormLayout, QLineEdit, QSpinBox,
    QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ayanna_erp.modules.restaurant.controllers.salle_controller import SalleController
from ayanna_erp.modules.restaurant.controllers.vente_controller import VenteController


# ----------------------------------------------------------------------
# BOUTON TABLE - STYLE TYPE "AYANNA CLOUD"
# ----------------------------------------------------------------------
class TableButton(QPushButton):
    def __init__(self, table_obj, parent_view):
        super().__init__(str(table_obj.number), parent_view.plan_frame)
        self.table_obj = table_obj
        self.table_id = table_obj.id
        self.parent_view = parent_view

        w = int(getattr(table_obj, "width", 80) or 80)
        h = int(getattr(table_obj, "height", 80) or 80)
        self.setFixedSize(w, h)

        self.move(
            int(getattr(table_obj, "pos_x", 0) or 0),
            int(getattr(table_obj, "pos_y", 0) or 0)
        )

        self.apply_style()

    def apply_style(self, occupied=False, selected=False):
        border_free = "#28a745"
        bg_free = "#ffffff"
        bg_occ = "#28a74522"
        border_occ = "#28a745"
        border_select = "#1e7e34"

        shape = (getattr(self.table_obj, "shape", "square") or "").lower()
        w = self.width()
        h = self.height()

        radius = min(w, h) // 2 if shape in ("round", "circle") else 6

        bg = bg_occ if occupied else bg_free
        border = border_select if selected else (border_occ if occupied else border_free)

        self.setStyleSheet(f"""
            background-color: {bg};
            border: 3px solid {border};
            border-radius: {radius}px;
            font-size: 18px;
            font-weight: bold;
        """)

        # Badge montant (si occupée)
        if occupied:
            montant = occupied if isinstance(occupied, str) else ""
            self.setText(f"{self.table_obj.number}\n<font color='#e53935'><b>{montant}</b></font>")
        else:
            self.setText(str(self.table_obj.number))

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.parent_view.select_table_button(self)
        self.parent_view.open_table_panel(self.table_id)


# ----------------------------------------------------------------------
# VUE PRINCIPALE RESTAURANT
# ----------------------------------------------------------------------
class VenteView(QWidget):
    def __init__(self, entreprise_id=1, parent=None):
        super().__init__(parent)
        self.entreprise_id = entreprise_id

        self.salle_ctrl = SalleController(entreprise_id=entreprise_id)
        self.vente_ctrl = VenteController(entreprise_id=entreprise_id)

        self.table_buttons = {}
        self.current_salle_id = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # ----------------------------
        # ✅ BARRE D’ONGLETS DES SALLES
        # ----------------------------
        self.tabs_layout = QHBoxLayout()
        self.tabs_layout.setSpacing(10)
        layout.addLayout(self.tabs_layout)

        # ----------------------------
        # ✅ ZONE DU PLAN DE SALLE
        # ----------------------------
        self.plan_frame = QFrame()
        self.plan_frame.setMinimumHeight(500)
        self.plan_frame.setStyleSheet("""
            background-color: #f7f7f7;
            border-radius: 8px;
        """)
        layout.addWidget(self.plan_frame)

        self.load_salles()

    # ------------------------------------------------------------------
    def load_salles(self):
        # vider onglets
        while self.tabs_layout.count():
            w = self.tabs_layout.takeAt(0).widget()
            if w:
                w.deleteLater()

        salles = self.salle_ctrl.list_salles()

        self.salle_buttons = {}

        for s in salles:
            btn = QPushButton(s.name)
            btn.setCheckable(True)
            btn.setProperty("salle_id", s.id)

            btn.setStyleSheet("""
                QPushButton {
                    background-color: #e3e4e6;
                    padding: 8px 20px;
                    border-radius: 6px;
                    font-weight: 600;
                }
                QPushButton:checked {
                    background-color: #28a745;
                    color: white;
                }
            """)

            btn.clicked.connect(lambda checked, sid=s.id, b=btn: self.select_salle(sid, b))

            self.tabs_layout.addWidget(btn)
            self.salle_buttons[s.id] = btn

    # ------------------------------------------------------------------
    def select_salle(self, salle_id, btn):
        if hasattr(self, "active_salle") and self.active_salle:
            self.active_salle.setChecked(False)

        btn.setChecked(True)
        self.active_salle = btn

        self.current_salle_id = salle_id
        self.load_tables_for_salle(salle_id)

    # ------------------------------------------------------------------
    def load_tables_for_salle(self, salle_id):
        # Clear plan
        for b in list(self.table_buttons.values()):
            b.setParent(None)
        self.table_buttons.clear()

        tables = self.salle_ctrl.list_tables_for_salle(salle_id)

        for t in tables:
            btn = TableButton(t, self)

            panier = self.vente_ctrl.get_open_panier_for_table(t.id)

            if panier:
                total, _ = self.vente_ctrl.get_panier_total(panier.id)
                btn.apply_style(occupied=f"{int(total)} F")
            else:
                btn.apply_style(occupied=False)

            btn.show()
            self.table_buttons[t.id] = btn

    # ------------------------------------------------------------------
    def select_table_button(self, table_button):
        if hasattr(self, "active_table_btn") and self.active_table_btn:
            panier = self.vente_ctrl.get_open_panier_for_table(self.active_table_btn.table_id)
            total = None
            if panier:
                total, _ = self.vente_ctrl.get_panier_total(panier.id)

            self.active_table_btn.apply_style(
                occupied=(f"{int(total)} F" if total else False),
                selected=False
            )

        panier = self.vente_ctrl.get_open_panier_for_table(table_button.table_id)
        total = None
        if panier:
            total, _ = self.vente_ctrl.get_panier_total(panier.id)

        table_button.apply_style(
            occupied=(f"{int(total)} F" if total else False),
            selected=True
        )
        self.active_table_btn = table_button

    def open_table_panel(self, table_id):
        """Ouvre un petit dialogue permettant de créer le panier, ajouter un produit simulé, ou payer."""
        try:
            panier = self.vente_ctrl.get_open_panier_for_table(table_id)
            dlg = QDialog(self)
            dlg.setWindowTitle(f"Table {table_id} - Panier")
            form = QFormLayout(dlg)
            if not panier:
                create_btn = QPushButton('Créer panier')
                create_btn.clicked.connect(lambda: self._create_panier_and_close(table_id, dlg))
                form.addRow(create_btn)
            else:
                # afficher totaux et options
                total_lines, total_paid = self.vente_ctrl.get_panier_total(panier.id)
                form.addRow(QLabel(f"Total lignes: {total_lines:.2f}"))
                form.addRow(QLabel(f"Total payé: {total_paid:.2f}"))
                # ajouter produit simulé
                prod_id_input = QLineEdit()
                prod_id_input.setPlaceholderText('product_id (int)')
                qty_input = QSpinBox(); qty_input.setValue(1)
                price_input = QLineEdit(); price_input.setPlaceholderText('price')
                add_prod_btn = QPushButton('Ajouter produit (simulé)')
                add_prod_btn.clicked.connect(lambda: self._add_product_to_panier(panier.id, prod_id_input.text(), qty_input.value(), price_input.text(), dlg))
                form.addRow('Product ID:', prod_id_input)
                form.addRow('Qty:', qty_input)
                form.addRow('Price:', price_input)
                form.addRow(add_prod_btn)
                # paiement
                pay_amount = QLineEdit(); pay_amount.setPlaceholderText('amount')
                pay_method = QLineEdit(); pay_method.setPlaceholderText('Espèces/Carte')
                pay_btn = QPushButton('Enregistrer paiement')
                pay_btn.clicked.connect(lambda: self._add_payment_to_panier(panier.id, pay_amount.text(), pay_method.text(), dlg))
                form.addRow('Montant:', pay_amount)
                form.addRow('Méthode:', pay_method)
                form.addRow(pay_btn)

            dlg.setLayout(form)
            dlg.exec()
            # Après interaction, recharger l'affichage pour rafraîchir couleur/montant
            if self.current_salle_id:
                self.load_tables_for_salle(self.current_salle_id)
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Erreur table panel: {e}")

    def _create_panier_and_close(self, table_id, dlg):
        try:
            p = self.vente_ctrl.create_panier(table_id=table_id)
            dlg.accept()
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Impossible de créer panier: {e}")

    def _add_product_to_panier(self, panier_id, prod_id_text, qty, price_text, dlg):
        try:
            prod_id = int(prod_id_text)
            price = float(price_text)
            self.vente_ctrl.add_product(panier_id, prod_id, qty, price)
            QMessageBox.information(self, 'Succès', 'Produit ajouté')
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Impossible d'ajouter le produit: {e}")

    def _add_payment_to_panier(self, panier_id, amount_text, method_text, dlg):
        try:
            amount = float(amount_text)
            method = method_text or 'Espèces'
            self.vente_ctrl.add_payment(panier_id, amount, method)
            QMessageBox.information(self, 'Succès', 'Paiement enregistré')
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Impossible d'ajouter le paiement: {e}")
