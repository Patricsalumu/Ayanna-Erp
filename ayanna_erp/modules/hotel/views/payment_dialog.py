"""
PaymentDialog – dialogue d'ajout de paiement / mise en crédit.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QDoubleSpinBox, QComboBox, QPushButton, QMessageBox, QLineEdit
)
from PyQt6.QtCore import Qt


def _load_payment_modes():
    """Retourne les modes actifs depuis la DB ou les 4 modes par défaut."""
    try:
        from ayanna_erp.core.view.payment_mode_widget import get_active_payment_modes
        modes = get_active_payment_modes()
        return [(m['code'], m['label']) for m in modes]
    except Exception:
        return [
            ('cash',         'Espèces'),
            ('banque',       'Banque'),
            ('mobile_money', 'Mobile Money'),
            ('credit',       'Crédit'),
        ]


class PaymentDialog(QDialog):
    """Dialogue pour enregistrer un paiement ou mettre en crédit."""

    def __init__(self, reservation: dict, parent=None):
        super().__init__(parent)
        self.reservation = reservation
        self.setWindowTitle("Enregistrer un paiement")
        self.setMinimumWidth(380)
        self.setModal(True)
        # Charger les modes dynamiques avant de construire l'UI
        self._methods = _load_payment_modes()
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # Informations
        info = QLabel(
            f"<b>Réservation :</b> {self.reservation.get('code', '-')}<br>"
            f"<b>Client :</b> {self.reservation.get('client_name', '-')}<br>"
            f"<b>Total :</b> {self.reservation.get('total', 0):,.0f}<br>"
            f"<b>Déjà payé :</b> {self.reservation.get('paid', 0):,.0f}<br>"
            f"<b>Reste :</b> <span style='color:#E74C3C;font-weight:bold;'>"
            f"{self.reservation.get('reste', 0):,.0f}</span>"
        )
        info.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(10)

        # Montant
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 99_999_999)
        self.amount_spin.setDecimals(0)
        self.amount_spin.setSingleStep(1000)
        reste = float(self.reservation.get('reste', 0) or 0)
        self.amount_spin.setValue(reste)
        form.addRow("Montant :", self.amount_spin)

        # Méthode
        self.method_combo = QComboBox()
        for code, label in self._methods:
            self.method_combo.addItem(label, code)
        form.addRow("Méthode :", self.method_combo)

        # Référence transaction (mobile money / banque)
        self.ref_label = QLabel("Référence :")
        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("Ex : TXN-123456789")
        self.ref_input.setMaxLength(200)
        form.addRow(self.ref_label, self.ref_input)

        layout.addLayout(form)

        # Gestion crédit : griser le montant ; référence : visible si mobile/banque
        self.method_combo.currentIndexChanged.connect(self._on_method_change)
        self._on_method_change()  # état initial

        # Boutons
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("Enregistrer")
        btn_ok.setDefault(True)
        btn_ok.setStyleSheet(
            "QPushButton{background:#1976D2;color:white;padding:8px 20px;"
            "border-radius:5px;}QPushButton:hover{background:#1565C0;}")
        btn_ok.clicked.connect(self._validate)
        btn_row.addWidget(btn_cancel)
        btn_row.addStretch()
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def _on_method_change(self):
        method = self.method_combo.currentData()
        is_credit = (method == 'credit')
        # Référence requise pour tout mode autre que espèces et crédit
        needs_ref = method is not None and method not in ('cash', 'credit')
        self.amount_spin.setEnabled(not is_credit)
        self.ref_label.setVisible(needs_ref)
        self.ref_input.setVisible(needs_ref)
        if not needs_ref:
            self.ref_input.clear()

    def _validate(self):
        method = self.method_combo.currentData()
        if method != 'credit' and self.amount_spin.value() <= 0:
            QMessageBox.warning(self, "Montant invalide",
                                "Le montant doit être supérieur à 0.")
            return
        needs_ref = method is not None and method not in ('cash', 'credit')
        if needs_ref and not self.ref_input.text().strip():
            QMessageBox.warning(self, "Référence manquante",
                                f"Veuillez saisir la référence de la transaction "
                                f"{self.method_combo.currentText()}.")
            return
        self.accept()

    # ------------------------------------------------------------------
    # Accesseurs
    # ------------------------------------------------------------------

    def get_amount(self) -> float:
        return 0.0 if self.method_combo.currentData() == 'credit' \
            else self.amount_spin.value()

    def get_method(self) -> str:
        return self.method_combo.currentData()

    def get_reference(self) -> str:
        """Retourne la référence de transaction (vide si méthode sans référence)."""
        return self.ref_input.text().strip()
