"""
Simple PyQt6 view for restaurant vente (plan de salle + panier)
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QListWidgetItem,
    QFrame, QDialog, QFormLayout, QLineEdit, QSpinBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ayanna_erp.modules.restaurant.controllers.salle_controller import SalleController
from ayanna_erp.modules.restaurant.controllers.vente_controller import VenteController


class TableButton(QPushButton):
    def __init__(self, table_obj, parent_view):
        super().__init__(str(table_obj.number), parent_view.plan_frame)
        self.table_obj = table_obj
        self.table_id = table_obj.id
        self.parent_view = parent_view
        self.setFixedSize(table_obj.width or 80, table_obj.height or 80)
        self.move(table_obj.pos_x or 0, table_obj.pos_y or 0)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        # On click, ouvrir le panneau panier
        self.parent_view.open_table_panel(self.table_id)


class VenteView(QWidget):
    def __init__(self, entreprise_id=1, parent=None):
        super().__init__(parent)
        self.entreprise_id = entreprise_id
        self.salle_ctrl = SalleController(entreprise_id=self.entreprise_id)
        self.vente_ctrl = VenteController(entreprise_id=self.entreprise_id)
        self.table_buttons = {}
        self.current_salle_id = None
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        # Left: salles
        left = QVBoxLayout()
        left.addWidget(QLabel("Salles"))
        self.salles_list = QListWidget()
        self.salles_list.itemClicked.connect(self.on_salle_selected)
        left.addWidget(self.salles_list)
        refresh_btn = QPushButton("Charger salles")
        refresh_btn.clicked.connect(self.load_salles)
        left.addWidget(refresh_btn)
        layout.addLayout(left, 1)

        # Right: plan / panier placeholder
        right = QVBoxLayout()
        right.addWidget(QLabel("Plan de salle / Table"))
        self.plan_frame = QFrame()
        self.plan_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.plan_frame.setFixedSize(800, 480)
        right.addWidget(self.plan_frame)
        layout.addLayout(right, 2)

        self.load_salles()

    def load_salles(self):
        self.salles_list.clear()
        try:
            salles = self.salle_ctrl.list_salles()
            for s in salles:
                item = QListWidgetItem(f"{s.name} (ID:{s.id})")
                item.setData(Qt.ItemDataRole.UserRole, s.id)
                self.salles_list.addItem(item)
        except Exception as e:
            print(f"Erreur load_salles: {e}")

    def on_salle_selected(self, item):
        try:
            sid = int(str(item.text()).split(' (ID:')[1].rstrip(')'))
        except Exception:
            return
        self.current_salle_id = sid
        self.load_tables_for_salle(sid)

    def load_tables_for_salle(self, salle_id):
        # clear existing
        for b in list(self.table_buttons.values()):
            b.setParent(None)
        self.table_buttons.clear()
        try:
            tables = self.salle_ctrl.list_tables_for_salle(salle_id)
            for t in tables:
                btn = TableButton(t, self)
                # vérifier si table a un panier en_cours
                panier = self.vente_ctrl.get_open_panier_for_table(t.id)
                if panier:
                    total_lines, total_paid = self.vente_ctrl.get_panier_total(panier.id)
                    btn.setStyleSheet("background-color: #c8e6c9; border:1px solid #2e7d32; border-radius:4px;")
                    btn.setToolTip(f"Montant: {total_lines:.2f} - Payé: {total_paid:.2f}")
                else:
                    btn.setStyleSheet("background-color: #f5f5f5; border:1px solid #ccc; border-radius:4px;")
                btn.show()
                self.table_buttons[t.id] = btn
        except Exception as e:
            print(f"Erreur load_tables_for_salle: {e}")

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
