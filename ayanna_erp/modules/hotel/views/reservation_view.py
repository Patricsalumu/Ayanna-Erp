"""
ReservationView – onglet de gestion des réservations hôtelières.
"""
from datetime import datetime, date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QDateEdit, QComboBox,
    QHeaderView, QMessageBox, QAbstractItemView, QFrame
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont, QBrush

from ayanna_erp.modules.hotel.services.reservation_service import ReservationService
from ayanna_erp.modules.hotel.services.payment_service import PaymentService
from ayanna_erp.modules.hotel.services.room_service import RoomService
from ayanna_erp.modules.hotel.views.reservation_dialog import (
    ReservationDialog, ExtendDialog
)
from ayanna_erp.modules.hotel.views.payment_dialog import PaymentDialog
from ayanna_erp.modules.hotel.utils.helpers import (
    fmt_date, reservation_status_label, payment_status_label,
    RESERVATION_STATUS_COLORS, PAYMENT_STATUS_COLORS
)

_res_svc  = ReservationService()
_pay_svc  = PaymentService()
_room_svc = RoomService()

COLUMNS = [
    'Code', 'Client', 'Catégorie', 'Chambre',
    'Entrée prévue', 'Sortie prévue',
    'Entrée réelle', 'Sortie réelle',
    'Statut', 'Paiement', 'Total', 'Payé', 'Reste'
]


class ReservationView(QWidget):

    def __init__(self, current_user=None, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self._data: list = []
        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(10, 10, 10, 10)

        # ---- Barre d'outils ----
        toolbar = QHBoxLayout()

        # Recherche
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Recherche (code, client, chambre)…")
        self.search_input.setFixedHeight(34)
        self.search_input.textChanged.connect(self._apply_filters)
        toolbar.addWidget(self.search_input, 2)

        # Filtre statut
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tous les statuts", None)
        for code, label in [
            ('en_attente', 'En attente'),
            ('confirmee',  'Confirmée'),
            ('en_cours',   'En cours'),
            ('terminee',   'Terminée'),
            ('annulee',    'Annulée'),
        ]:
            self.status_filter.addItem(label, code)
        self.status_filter.currentIndexChanged.connect(self.refresh)
        toolbar.addWidget(self.status_filter)

        # Dates
        today = QDate.currentDate()
        self.date_from = QDateEdit(today.addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("dd/MM/yyyy")
        self.date_from.dateChanged.connect(self.refresh)
        toolbar.addWidget(QLabel("Du :"))
        toolbar.addWidget(self.date_from)

        self.date_to = QDateEdit(today.addDays(30))
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("dd/MM/yyyy")
        self.date_to.dateChanged.connect(self.refresh)
        toolbar.addWidget(QLabel("Au :"))
        toolbar.addWidget(self.date_to)

        btn_refresh = QPushButton("↻")
        btn_refresh.setFixedSize(34, 34)
        btn_refresh.setToolTip("Actualiser")
        btn_refresh.clicked.connect(self.refresh)
        toolbar.addWidget(btn_refresh)

        root.addLayout(toolbar)

        # ---- Actions ----
        actions = QHBoxLayout()
        self.btn_new     = self._btn("➕ Nouvelle réservation", "#27AE60")
        self.btn_checkin = self._btn("✅ Check-in",  "#1976D2")
        self.btn_pay     = self._btn("💰 Paiement",  "#8E44AD")
        self.btn_extend  = self._btn("📅 Prolonger", "#E67E22")
        self.btn_checkout= self._btn("🚪 Check-out", "#E74C3C")
        self.btn_cancel  = self._btn("✖ Annuler",   "#7F8C8D")
        self.btn_print   = self._btn("🖨️ Imprimer",  "#34495E")

        for btn in [self.btn_new, self.btn_checkin, self.btn_pay,
                    self.btn_extend, self.btn_checkout,
                    self.btn_cancel, self.btn_print]:
            actions.addWidget(btn)
        actions.addStretch()
        root.addLayout(actions)

        self.btn_new.clicked.connect(self._on_new)
        self.btn_checkin.clicked.connect(self._on_checkin)
        self.btn_pay.clicked.connect(self._on_pay)
        self.btn_extend.clicked.connect(self._on_extend)
        self.btn_checkout.clicked.connect(self._on_checkout)
        self.btn_cancel.clicked.connect(self._on_cancel)
        self.btn_print.clicked.connect(self._on_print)

        # ---- Tableau ----
        self.table = QTableWidget()
        self.table.setColumnCount(len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setStyleSheet(
            "QTableWidget{border:1px solid #ddd;}"
            "QHeaderView::section{background:#34495E;color:white;"
            "padding:6px;font-weight:bold;}")
        root.addWidget(self.table)

        # Stat bar
        self.stat_bar = QLabel()
        self.stat_bar.setStyleSheet("color:#555;font-size:11px;")
        root.addWidget(self.stat_bar)

    @staticmethod
    def _btn(text: str, color: str) -> QPushButton:
        b = QPushButton(text)
        b.setFixedHeight(32)
        b.setStyleSheet(
            f"QPushButton{{background:{color};color:white;border-radius:4px;"
            f"padding:0 10px;font-size:11px;}}"
            f"QPushButton:hover{{opacity:0.85;}}")
        return b

    # ------------------------------------------------------------------
    def refresh(self):
        d_from = self.date_from.date().toPyDate()
        d_to   = self.date_to.date().toPyDate()
        status = self.status_filter.currentData()
        self._data = _res_svc.get_all_reservations(
            date_from=d_from, date_to=d_to, status=status)
        self._fill_table(self._data)

    def _apply_filters(self):
        s = self.search_input.text().strip().lower()
        if not s:
            self._fill_table(self._data)
            return
        filtered = [r for r in self._data
                    if s in r['code'].lower()
                    or s in r['client_name'].lower()
                    or s in r['room'].lower()]
        self._fill_table(filtered)

    def _fill_table(self, rows: list):
        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            cells = [
                row['code'],
                row['client_name'],
                row['category'],
                row['room'],
                fmt_date(row['date_entree_prevue']),
                fmt_date(row['date_sortie_prevue']),
                fmt_date(row['date_entree_reelle']),
                fmt_date(row['date_sortie_reelle']),
                reservation_status_label(row['status']),
                payment_status_label(row['statut_paiement']),
                f"{row['total']:,.0f}",
                f"{row['paid']:,.0f}",
                f"{row['reste']:,.0f}",
            ]
            for col, val in enumerate(cells):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 0:  # store id in first column
                    item.setData(Qt.ItemDataRole.UserRole, row['id'])
                self.table.setItem(r, col, item)

            # Coloration statut
            s_color = RESERVATION_STATUS_COLORS.get(row['status'], '#333')
            p_color = PAYMENT_STATUS_COLORS.get(row['statut_paiement'], '#333')
            self.table.item(r, 8).setForeground(QBrush(QColor(s_color)))
            self.table.item(r, 9).setForeground(QBrush(QColor(p_color)))
            if row['status'] == 'annulee':
                for c in range(len(COLUMNS)):
                    it = self.table.item(r, c)
                    if it:
                        it.setForeground(QBrush(QColor('#95A5A6')))

        self.stat_bar.setText(
            f"{len(rows)} réservation(s) affichée(s)")

    def _selected_row(self) -> dict | None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Sélection", "Veuillez sélectionner une réservation.")
            return None
        item = self.table.item(row, 0)
        if not item:
            return None
        res_id = item.data(Qt.ItemDataRole.UserRole)
        for r in self._data:
            if r['id'] == res_id:
                return r
        return None

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _on_new(self):
        try:
            from ayanna_erp.modules.boutique.model.models import ShopClient
            from ayanna_erp.database.database_manager import get_database_manager
            db = get_database_manager()
            with db.session_scope() as session:
                clients = (session.query(ShopClient)
                           .filter(ShopClient.is_active == True)
                           .order_by(ShopClient.nom)
                           .all())
                session.expunge_all()

            categories = _room_svc.get_all_categories()
            if not categories:
                QMessageBox.warning(self, "Aucune catégorie",
                                    "Créez d'abord au moins une catégorie de chambre.")
                return

            dlg = ReservationDialog(clients, categories, self)
            if dlg.exec() != ReservationDialog.DialogCode.Accepted:
                return

            data = dlg.get_data()
            uid = self._uid()
            ok, msg, _ = ReservationService().create_reservation(
                client_id=data['client_id'],
                category_id=data['category_id'],
                date_entree=data['date_entree'],
                date_sortie=data['date_sortie'],
                reduction=data['reduction'],
                notes=data['notes'],
                user_id=uid,
                acompte=data['acompte'],
                method=data['method'],
            )
            if ok:
                QMessageBox.information(self, "Succès", msg)
                self.refresh()
            else:
                QMessageBox.warning(self, "Erreur", msg)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def _on_checkin(self):
        row = self._selected_row()
        if not row:
            return
        ok, msg = _res_svc.checkin(row['id'], self._uid())
        if ok:
            QMessageBox.information(self, "Check-in", msg)
            self.refresh()
        else:
            QMessageBox.warning(self, "Check-in impossible", msg)

    def _on_pay(self):
        row = self._selected_row()
        if not row:
            return
        dlg = PaymentDialog(row, self)
        if dlg.exec() != PaymentDialog.DialogCode.Accepted:
            return
        ok, msg = _pay_svc.add_payment(
            row['id'], dlg.get_amount(), dlg.get_method(), self._uid())
        if ok:
            QMessageBox.information(self, "Paiement", msg)
            self.refresh()
        else:
            QMessageBox.warning(self, "Erreur paiement", msg)

    def _on_extend(self):
        row = self._selected_row()
        if not row:
            return
        dlg = ExtendDialog(row, self)
        if dlg.exec() != ExtendDialog.DialogCode.Accepted:
            return
        ok, msg = _res_svc.extend_stay(row['id'], dlg.get_new_date(), self._uid())
        if ok:
            QMessageBox.information(self, "Prolongation", msg)
            self.refresh()
        else:
            QMessageBox.warning(self, "Erreur prolongation", msg)

    def _on_checkout(self):
        row = self._selected_row()
        if not row:
            return
        reply = QMessageBox.question(
            self, "Check-out",
            f"Confirmer le check-out de la réservation {row['code']} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        ok, msg = _res_svc.checkout(row['id'], self._uid())
        if ok:
            QMessageBox.information(self, "Check-out", msg)
            self.refresh()
        else:
            QMessageBox.warning(self, "Check-out impossible", msg)

    def _on_cancel(self):
        row = self._selected_row()
        if not row:
            return
        reply = QMessageBox.question(
            self, "Annulation",
            f"Annuler la réservation {row['code']} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        ok, msg = _res_svc.cancel_reservation(row['id'])
        if ok:
            QMessageBox.information(self, "Annulée", msg)
            self.refresh()
        else:
            QMessageBox.warning(self, "Erreur", msg)

    def _on_print(self):
        row = self._selected_row()
        if not row:
            return
        self._print_reservation(row)

    def _print_reservation(self, row: dict):
        """Génère et ouvre un PDF A4 simple pour la réservation."""
        try:
            import os, subprocess, sys
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import cm
            from reportlab.lib.colors import HexColor, black

            export_dir = os.path.join(os.getcwd(), "exports_commandes")
            os.makedirs(export_dir, exist_ok=True)
            fname = os.path.join(export_dir,
                f"hotel_res_{row['code']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf")
            doc = SimpleDocTemplate(fname, pagesize=A4)
            styles = getSampleStyleSheet()
            els = []
            els.append(Paragraph("<b>FACTURE / RÉSERVATION HÔTEL</b>", styles['Title']))
            els.append(Spacer(1, 0.5*cm))
            data = [
                ["Code",      row['code']],
                ["Client",    row['client_name']],
                ["Catégorie", row['category']],
                ["Chambre",   row['room']],
                ["Entrée",    fmt_date(row['date_entree_prevue'])],
                ["Sortie",    fmt_date(row['date_sortie_prevue'])],
                ["Statut",    reservation_status_label(row['status'])],
                ["Paiement",  payment_status_label(row['statut_paiement'])],
                ["Total",     f"{row['total']:,.0f}"],
                ["Payé",      f"{row['paid']:,.0f}"],
                ["Reste",     f"{row['reste']:,.0f}"],
            ]
            t = Table(data, colWidths=[5*cm, 11*cm])
            t.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, black),
                ('BACKGROUND', (0,0), (0,-1), HexColor('#ECF0F1')),
                ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ]))
            els.append(t)
            doc.build(els)
            if os.name == 'nt':
                os.startfile(fname)
            elif sys.platform == 'darwin':
                subprocess.run(['open', fname])
            else:
                subprocess.run(['xdg-open', fname])
        except Exception as e:
            QMessageBox.warning(self, "Impression", f"Erreur impression : {e}")

    def _uid(self):
        if self.current_user is None:
            return 1
        if isinstance(self.current_user, dict):
            return self.current_user.get('id', 1)
        return getattr(self.current_user, 'id', 1)
