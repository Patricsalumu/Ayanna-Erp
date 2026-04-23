"""
CaisseView – onglet 5 : paiements du jour et total journalier.
"""
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QDateEdit, QHeaderView, QAbstractItemView, QFrame
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor, QBrush

from ayanna_erp.modules.hotel.services.payment_service import PaymentService
from ayanna_erp.modules.hotel.utils.helpers import fmt_datetime

_svc = PaymentService()

COLUMNS = ['ID', 'Réservation', 'Client', 'Montant', 'Méthode', 'Heure']
METHOD_LABELS = {
    'cash':         'Espèces',
    'mobile_money': 'Mobile Money',
    'carte':        'Carte',
}


class CaisseView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        title = QLabel("Caisse – Paiements hôtel")
        title.setStyleSheet("font-size:16px;font-weight:bold;color:#2C3E50;")
        root.addWidget(title)

        # Filtre date
        bar = QHBoxLayout()
        bar.addWidget(QLabel("Date :"))
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.dateChanged.connect(self.refresh)
        bar.addWidget(self.date_edit)
        btn_today = QPushButton("Aujourd'hui")
        btn_today.setFixedHeight(30)
        btn_today.clicked.connect(self._go_today)
        bar.addWidget(btn_today)
        btn_refresh = QPushButton("↻")
        btn_refresh.setFixedSize(30, 30)
        btn_refresh.clicked.connect(self.refresh)
        bar.addWidget(btn_refresh)
        bar.addStretch()
        root.addLayout(bar)

        # Tableau
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

        # Barre récapitulatif
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(sep)

        recap_row = QHBoxLayout()
        self.lbl_count  = QLabel()
        self.lbl_total  = QLabel()
        self.lbl_cash   = QLabel()
        self.lbl_mobile = QLabel()
        self.lbl_carte  = QLabel()
        for lbl in (self.lbl_count, self.lbl_cash, self.lbl_mobile,
                    self.lbl_carte, self.lbl_total):
            lbl.setStyleSheet("font-size:13px;font-weight:bold;padding:4px 10px;")
            recap_row.addWidget(lbl)
        recap_row.addStretch()
        root.addLayout(recap_row)

    # ------------------------------------------------------------------
    def _go_today(self):
        self.date_edit.setDate(QDate.currentDate())
        self.refresh()

    def refresh(self):
        d = self.date_edit.date().toPyDate()
        target = datetime(d.year, d.month, d.day)
        self._data = _svc.get_daily_payments(target)
        self._fill_table()

    def _fill_table(self):
        self.table.setRowCount(0)
        total = 0.0
        totals = {'cash': 0.0, 'mobile_money': 0.0, 'carte': 0.0}
        for pay in self._data:
            r = self.table.rowCount()
            self.table.insertRow(r)
            vals = [
                str(pay['id']),
                pay['reservation_code'],
                pay['client'],
                f"{pay['amount']:,.0f}",
                METHOD_LABELS.get(pay['method'], pay['method']),
                fmt_datetime(pay['created_at']),
            ]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, col, item)

            total += float(pay['amount'] or 0)
            if pay['method'] in totals:
                totals[pay['method']] += float(pay['amount'] or 0)

        self.lbl_count.setText(f"Transactions : {len(self._data)}")
        self.lbl_cash.setText(f"Espèces : {totals['cash']:,.0f}")
        self.lbl_mobile.setText(f"Mobile : {totals['mobile_money']:,.0f}")
        self.lbl_carte.setText(f"Carte : {totals['carte']:,.0f}")
        self.lbl_total.setText(f"TOTAL : {total:,.0f}")
        self.lbl_total.setStyleSheet(
            "font-size:15px;font-weight:bold;color:#1976D2;"
            "padding:4px 10px;")
