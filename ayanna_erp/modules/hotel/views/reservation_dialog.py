"""
ReservationDialog – dialogue de création / modification de réservation.
"""
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QDateEdit, QDoubleSpinBox, QComboBox,
    QPushButton, QTextEdit, QMessageBox, QGroupBox, QWidget
)
from PyQt6.QtCore import Qt, QDate

from ayanna_erp.modules.hotel.services.room_service import RoomService
from ayanna_erp.modules.hotel.utils.helpers import fmt_money

_room_svc = RoomService()


class _QuickClientDialog(QDialog):
    """Mini-dialogue de création rapide d'un client."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nouveau client")
        self.setMinimumWidth(340)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        form = QFormLayout(self)
        form.setSpacing(10)

        self.nom_edit = QLineEdit()
        self.nom_edit.setPlaceholderText("Obligatoire")
        form.addRow("Nom * :", self.nom_edit)

        self.prenom_edit = QLineEdit()
        form.addRow("Prénom :", self.prenom_edit)

        self.tel_edit = QLineEdit()
        form.addRow("Téléphone :", self.tel_edit)

        self.pays_edit = QLineEdit()
        self.pays_edit.setPlaceholderText("Ex : France, DRC, USA\u2026")
        form.addRow("Pays :", self.pays_edit)

        self.carte_edit = QLineEdit()
        self.carte_edit.setPlaceholderText("N\u00b0 pi\u00e8ce d'identit\u00e9 / passeport")
        form.addRow("Pi\u00e8ce d'identit\u00e9 :", self.carte_edit)

        btns = QHBoxLayout()
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("Enregistrer")
        btn_ok.setDefault(True)
        btn_ok.setStyleSheet(
            "QPushButton{background:#27AE60;color:white;padding:6px 16px;"
            "border-radius:4px;}QPushButton:hover{background:#219A52;}")
        btn_ok.clicked.connect(self._validate)
        btns.addWidget(btn_cancel)
        btns.addStretch()
        btns.addWidget(btn_ok)
        form.addRow(btns)

    def _validate(self):
        if not self.nom_edit.text().strip():
            QMessageBox.warning(self, "Nom manquant", "Le nom est obligatoire.")
            return
        self.accept()

    def get_data(self):
        return (
            self.nom_edit.text().strip(),
            self.prenom_edit.text().strip(),
            self.tel_edit.text().strip(),
            self.pays_edit.text().strip(),
            self.carte_edit.text().strip(),
        )


class ReservationDialog(QDialog):
    """
    Dialogue pour créer une nouvelle réservation.
    Passe les données saisies via .get_data().
    """

    def __init__(self, clients: list, categories: list, parent=None):
        super().__init__(parent)
        self.clients = clients      # List[SimpleNamespace | ORM obj] avec .id, .nom, .prenom
        self.categories = categories  # List[HotelCategory]
        self.setWindowTitle("Nouvelle réservation")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        grp = QGroupBox("Informations de réservation")
        form = QFormLayout(grp)
        form.setSpacing(10)

        # Client
        self.client_combo = QComboBox()
        self.client_combo.setSizePolicy(
            self.client_combo.sizePolicy().horizontalPolicy(),
            self.client_combo.sizePolicy().verticalPolicy())
        self._fill_client_combo()

        client_row = QWidget()
        client_hl = QHBoxLayout(client_row)
        client_hl.setContentsMargins(0, 0, 0, 0)
        client_hl.setSpacing(4)
        client_hl.addWidget(self.client_combo, 1)
        btn_new_client = QPushButton("+")
        btn_new_client.setFixedSize(28, 28)
        btn_new_client.setToolTip("Ajouter un nouveau client")
        btn_new_client.setStyleSheet(
            "QPushButton{background:#27AE60;color:white;font-weight:bold;"
            "border-radius:4px;font-size:14px;}"
            "QPushButton:hover{background:#219A52;}")
        btn_new_client.clicked.connect(self._add_new_client)
        client_hl.addWidget(btn_new_client)
        form.addRow("Client * :", client_row)

        # Catégorie
        self.cat_combo = QComboBox()
        for cat in self.categories:
            self.cat_combo.addItem(
                f"{cat.name}  ({cat.price_per_night:,.0f}/nuit)", cat.id)
        self.cat_combo.currentIndexChanged.connect(self._refresh_total)
        form.addRow("Catégorie * :", self.cat_combo)

        # Dates
        today = QDate.currentDate()
        self.date_entree = QDateEdit(today)
        self.date_entree.setCalendarPopup(True)
        self.date_entree.setDisplayFormat("dd/MM/yyyy")
        self.date_entree.dateChanged.connect(self._refresh_total)
        form.addRow("Date d'entrée * :", self.date_entree)

        self.date_sortie = QDateEdit(today.addDays(1))
        self.date_sortie.setCalendarPopup(True)
        self.date_sortie.setDisplayFormat("dd/MM/yyyy")
        self.date_sortie.dateChanged.connect(self._refresh_total)
        form.addRow("Date de sortie * :", self.date_sortie)

        # Réduction
        self.reduction_spin = QDoubleSpinBox()
        self.reduction_spin.setRange(0, 9_999_999)
        self.reduction_spin.setDecimals(0)
        self.reduction_spin.setSingleStep(1000)
        self.reduction_spin.valueChanged.connect(self._refresh_total)
        form.addRow("Réduction :", self.reduction_spin)

        # Acompte
        self.acompte_spin = QDoubleSpinBox()
        self.acompte_spin.setRange(0, 9_999_999)
        self.acompte_spin.setDecimals(0)
        self.acompte_spin.setSingleStep(1000)
        form.addRow("Acompte :", self.acompte_spin)

        # Méthode acompte
        self.method_combo = QComboBox()
        try:
            from ayanna_erp.core.view.payment_mode_widget import get_active_payment_modes
            _modes = get_active_payment_modes()
        except Exception:
            _modes = [
                {'code': 'cash',         'label': 'Espèces',       'compte_id': None},
                {'code': 'banque',       'label': 'Banque',         'compte_id': None},
                {'code': 'mobile_money', 'label': 'Mobile Money',   'compte_id': None},
                {'code': 'credit',       'label': 'Crédit',        'compte_id': None},
            ]
        for m in _modes:
            self.method_combo.addItem(m['label'], (m['code'], m.get('compte_id')))
        self.method_combo.currentIndexChanged.connect(self._on_method_change)
        form.addRow("Méthode acompte :", self.method_combo)

        # Référence acompte (optionnelle, visible si mobile/banque)
        self.ref_label_acompte = QLabel("Référence :")
        self.ref_input_acompte = QLineEdit()
        self.ref_input_acompte.setPlaceholderText("Ex : TXN-123456789 (optionnel)")
        self.ref_input_acompte.setMaxLength(200)
        form.addRow(self.ref_label_acompte, self.ref_input_acompte)
        self._on_method_change()  # état initial

        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setFixedHeight(60)
        form.addRow("Notes :", self.notes_edit)

        layout.addWidget(grp)

        # Résumé total
        self.lbl_total = QLabel()
        self.lbl_total.setStyleSheet(
            "font-size:14px;font-weight:bold;color:#1976D2;")
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.lbl_total)
        self._refresh_total()

        # Boutons
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("Créer la réservation")
        btn_ok.setDefault(True)
        btn_ok.setStyleSheet(
            "QPushButton{background:#27AE60;color:white;padding:8px 22px;"
            "border-radius:5px;}QPushButton:hover{background:#219A52;}")
        btn_ok.clicked.connect(self._validate)
        btn_row.addWidget(btn_cancel)
        btn_row.addStretch()
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    def _fill_client_combo(self, select_id=None):
        """(Re)remplit la combo clients depuis la BD."""
        from ayanna_erp.modules.boutique.model.models import ShopClient as _SC
        from ayanna_erp.database.database_manager import get_database_manager
        db = get_database_manager()
        with db.session_scope() as session:
            clients = (session.query(_SC)
                       .filter(_SC.is_active == True)
                       .order_by(_SC.nom)
                       .all())
            session.expunge_all()
        self.clients = clients
        self.client_combo.clear()
        self.client_combo.addItem("-- Sélectionner un client --", None)
        for c in self.clients:
            name = f"{c.nom} {c.prenom or ''}".strip()
            self.client_combo.addItem(name, c.id)
        if select_id is not None:
            for i in range(self.client_combo.count()):
                if self.client_combo.itemData(i) == select_id:
                    self.client_combo.setCurrentIndex(i)
                    break

    def _add_new_client(self):
        """Ouvre le dialogue de création rapide et sélectionne le nouveau client."""
        from ayanna_erp.modules.boutique.model.models import ShopClient as _SC
        from ayanna_erp.database.database_manager import get_database_manager
        dlg = _QuickClientDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        nom, prenom, telephone, pays, carte_identite = dlg.get_data()
        if not nom:
            return
        db = get_database_manager()
        try:
            with db.session_scope() as session:
                first = session.query(_SC.pos_id).order_by(_SC.pos_id).first()
                pos_id = first[0] if first else 1
                client = _SC(
                    pos_id=pos_id,
                    nom=nom,
                    prenom=prenom or None,
                    telephone=telephone or None,
                    pays=pays or None,
                    carte_identite=carte_identite or None,
                    is_active=True,
                )
                session.add(client)
                session.flush()
                new_id = client.id
            self._fill_client_combo(select_id=new_id)
        except Exception as e:
            QMessageBox.critical(self, "Erreur",
                                 f"Impossible de créer le client :\n{e}")

    def _refresh_total(self):
        try:
            cat = self._selected_category()
            if cat is None:
                self.lbl_total.setText("")
                return
            nuits = self._nb_nuits()
            total = max(nuits * cat.price_per_night - self.reduction_spin.value(), 0)
            self.lbl_total.setText(
                f"Total : {total:,.0f}   ({nuits} nuit(s) × "
                f"{cat.price_per_night:,.0f} − {self.reduction_spin.value():,.0f})")
        except Exception:
            pass

    def _on_method_change(self):
        data = self.method_combo.currentData()
        code = data[0] if isinstance(data, tuple) else (data or '')
        needs_ref = code not in ('cash', 'credit')
        self.ref_label_acompte.setVisible(needs_ref)
        self.ref_input_acompte.setVisible(needs_ref)
        if not needs_ref:
            self.ref_input_acompte.clear()

    def _selected_category(self):
        idx = self.cat_combo.currentIndex()
        if idx < 0 or idx >= len(self.categories):
            return None
        return self.categories[idx]

    def _nb_nuits(self) -> int:
        d1 = self.date_entree.date().toPyDate()
        d2 = self.date_sortie.date().toPyDate()
        delta = (d2 - d1).days
        return max(delta, 1)

    def _validate(self):
        if self.client_combo.currentData() is None:
            QMessageBox.warning(self, "Client manquant",
                                "Veuillez sélectionner un client.")
            return
        d1 = self.date_entree.date().toPyDate()
        d2 = self.date_sortie.date().toPyDate()
        if d2 <= d1:
            QMessageBox.warning(self, "Dates invalides",
                                "La date de sortie doit être après la date d'entrée.")
            return
        self.accept()

    # ------------------------------------------------------------------
    def get_data(self) -> dict:
        d1 = self.date_entree.date().toPyDate()
        d2 = self.date_sortie.date().toPyDate()
        method_data = self.method_combo.currentData()
        method_code = method_data[0] if isinstance(method_data, tuple) else (method_data or 'cash')
        method_compte_id = method_data[1] if isinstance(method_data, tuple) else None
        return {
            'client_id':   self.client_combo.currentData(),
            'category_id': self.cat_combo.currentData(),
            'date_entree': datetime(d1.year, d1.month, d1.day),
            'date_sortie': datetime(d2.year, d2.month, d2.day),
            'reduction':   self.reduction_spin.value(),
            'acompte':     self.acompte_spin.value(),
            'method':      method_code,
            'compte_id':   method_compte_id,
            'reference':   self.ref_input_acompte.text().strip(),
            'notes':       self.notes_edit.toPlainText().strip(),
        }


class ExtendDialog(QDialog):
    """Dialogue pour prolonger un séjour."""

    def __init__(self, reservation: dict, parent=None):
        super().__init__(parent)
        self.reservation = reservation
        self.setWindowTitle("Prolonger le séjour")
        self.setMinimumWidth(340)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        current_sortie = self.reservation.get('date_sortie_prevue') or datetime.now()
        if isinstance(current_sortie, datetime):
            qd = QDate(current_sortie.year, current_sortie.month, current_sortie.day)
        else:
            qd = QDate.currentDate()

        form = QFormLayout()
        self.new_sortie = QDateEdit(qd.addDays(1))
        self.new_sortie.setCalendarPopup(True)
        self.new_sortie.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Nouvelle date de sortie :", self.new_sortie)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("Prolonger")
        btn_ok.setDefault(True)
        btn_ok.setStyleSheet(
            "QPushButton{background:#1976D2;color:white;padding:8px 20px;"
            "border-radius:5px;}")
        btn_ok.clicked.connect(self._validate)
        btn_row.addWidget(btn_cancel)
        btn_row.addStretch()
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def _validate(self):
        current_sortie = self.reservation.get('date_sortie_prevue') or datetime.now()
        d = self.new_sortie.date().toPyDate()
        new_dt = datetime(d.year, d.month, d.day)
        if isinstance(current_sortie, datetime):
            if new_dt <= current_sortie:
                QMessageBox.warning(self, "Date invalide",
                                    "La nouvelle date doit être après la date de sortie actuelle.")
                return
        self.accept()

    def get_new_date(self) -> datetime:
        d = self.new_sortie.date().toPyDate()
        return datetime(d.year, d.month, d.day)
