"""
CaisseView – onglet 5 : paiements hôtel avec filtres par plage de dates.
"""
import os
import subprocess
import sys
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QDateEdit, QLineEdit, QHeaderView,
    QAbstractItemView, QFrame, QMessageBox,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor, QBrush

from ayanna_erp.modules.hotel.services.payment_service import PaymentService
from ayanna_erp.modules.hotel.utils.helpers import fmt_datetime

_svc = PaymentService()

COLUMNS = ['#', 'Réservation', 'Client', 'Montant', 'Méthode', 'Reçu par',
           'Dt. Réservation', 'Check-in', 'Check-out', 'Date / Heure paiement']
METHOD_LABELS = {
    'cash':         'Espèces',
    'mobile_money': 'Mobile Money',
    'carte':        'Carte',
}


class CaisseView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list = []
        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # Titre
        title = QLabel("Caisse – Paiements hôtel")
        title.setStyleSheet("font-size:16px;font-weight:bold;color:#2C3E50;")
        root.addWidget(title)

        # ── Barre de filtres ──────────────────────────────────────────────
        bar = QHBoxLayout()
        bar.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Recherche (réservation, client, méthode, utilisateur)…")
        self.search_input.setFixedHeight(32)
        self.search_input.textChanged.connect(self._apply_filters)
        bar.addWidget(self.search_input, 2)

        today = QDate.currentDate()
        bar.addWidget(QLabel("Du :"))
        self.date_from = QDateEdit(today)
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("dd/MM/yyyy")
        self.date_from.setFixedHeight(32)
        self.date_from.dateChanged.connect(self.refresh)
        bar.addWidget(self.date_from)

        bar.addWidget(QLabel("Au :"))
        self.date_to = QDateEdit(today)
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("dd/MM/yyyy")
        self.date_to.setFixedHeight(32)
        self.date_to.dateChanged.connect(self.refresh)
        bar.addWidget(self.date_to)

        btn_refresh = QPushButton("↻")
        btn_refresh.setFixedSize(32, 32)
        btn_refresh.setToolTip("Actualiser")
        btn_refresh.clicked.connect(self.refresh)
        bar.addWidget(btn_refresh)

        btn_export = QPushButton("📄 Export PDF")
        btn_export.setFixedHeight(32)
        btn_export.setStyleSheet(
            "QPushButton{background:#16A085;color:white;border-radius:4px;"
            "padding:0 12px;font-size:11px;font-weight:bold;}"
            "QPushButton:hover{background:#138D75;}")
        btn_export.clicked.connect(self._on_export_pdf)
        bar.addWidget(btn_export)

        root.addLayout(bar)

        # ── Tableau ───────────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setStyleSheet(
            "QTableWidget{border:1px solid #ddd;}"
            "QHeaderView::section{background:#34495E;color:white;"
            "padding:6px;font-weight:bold;}")
        root.addWidget(self.table)

        # ── Barre de résumé ───────────────────────────────────────────────
        self.summary_frame = QFrame()
        self.summary_frame.setFixedHeight(40)
        self.summary_frame.setStyleSheet(
            "QFrame{background:#2C3E50;border-radius:4px;}")
        _sl = QHBoxLayout(self.summary_frame)
        _sl.setContentsMargins(10, 4, 10, 4)
        _sl.setSpacing(22)

        def _slbl():
            lb = QLabel()
            lb.setStyleSheet("color:white;font-size:11px;font-weight:bold;")
            return lb

        self.lbl_count  = _slbl()
        self.lbl_cash   = _slbl()
        self.lbl_mobile = _slbl()
        self.lbl_carte  = _slbl()
        self.lbl_total  = _slbl()
        for lb in (self.lbl_count, self.lbl_cash, self.lbl_mobile,
                   self.lbl_carte, self.lbl_total):
            _sl.addWidget(lb)
        _sl.addStretch()
        root.addWidget(self.summary_frame)

    # ------------------------------------------------------------------
    def refresh(self):
        d_from = self.date_from.date().toPyDate()
        d_to   = self.date_to.date().toPyDate()
        self._data = _svc.get_daily_payments(
            target_date=datetime(d_from.year, d_from.month, d_from.day),
            date_to=datetime(d_to.year, d_to.month, d_to.day),
        )
        self._apply_filters()

    def _apply_filters(self):
        s = self.search_input.text().strip().lower()
        if not s:
            self._fill_table(self._data)
            return
        filtered = [
            p for p in self._data
            if s in (p.get('reservation_code') or '').lower()
            or s in (p.get('client') or '').lower()
            or s in METHOD_LABELS.get(p.get('method', ''), p.get('method', '')).lower()
            or s in (p.get('user_name') or '').lower()
        ]
        self._fill_table(filtered)

    def _fill_table(self, rows: list):
        self.table.setRowCount(0)
        total = 0.0
        totals = {'cash': 0.0, 'mobile_money': 0.0, 'carte': 0.0}

        for idx, pay in enumerate(rows, start=1):
            r = self.table.rowCount()
            self.table.insertRow(r)
            method = pay.get('method', '')
            method_label = METHOD_LABELS.get(method, method or '-')
            dt_str = (pay['created_at'].strftime('%d/%m/%Y %H:%M')
                      if hasattr(pay.get('created_at'), 'strftime')
                      else str(pay.get('created_at', '-')))

            def _fmtd(v):
                if v is None:
                    return '-'
                try:
                    return v.strftime('%d/%m/%Y %H:%M')
                except Exception:
                    return str(v)

            amt = pay.get('amount', 0)
            vals = [
                str(idx),
                pay.get('reservation_code', '-'),
                pay.get('client', '-'),
                f"{amt:,.0f}" if isinstance(amt, (int, float)) else '-',
                method_label,
                pay.get('user_name', str(pay.get('user_id', '-'))),
                _fmtd(pay.get('date_reservation')),
                _fmtd(pay.get('date_checkin')),
                _fmtd(pay.get('date_checkout')),
                dt_str,
            ]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, col, item)

            # Coloration par méthode (col 4)
            m_colors = {'cash': '#27AE60', 'mobile_money': '#8E44AD', 'carte': '#1976D2'}
            m_item = self.table.item(r, 4)
            if m_item and method in m_colors:
                m_item.setForeground(QBrush(QColor(m_colors[method])))
                m_item.setFont(QFont('', -1, QFont.Weight.Bold))

            total += float(amt or 0)
            if method in totals:
                totals[method] += float(amt or 0)

        self.lbl_count.setText(f"📋 {len(rows)} paiements")
        self.lbl_cash.setText(f"💵 Espèces : {totals['cash']:,.0f}")
        self.lbl_mobile.setText(f"📱 Mobile : {totals['mobile_money']:,.0f}")
        self.lbl_carte.setText(f"💳 Carte : {totals['carte']:,.0f}")
        self.lbl_total.setText(f"✅ TOTAL : {total:,.0f}")

    # ------------------------------------------------------------------
    def _on_export_pdf(self):
        s = self.search_input.text().strip().lower()
        if s:
            rows = [
                p for p in self._data
                if s in (p.get('reservation_code') or '').lower()
                or s in (p.get('client') or '').lower()
                or s in METHOD_LABELS.get(p.get('method', ''), p.get('method', '')).lower()
                or s in (p.get('user_name') or '').lower()
            ]
        else:
            rows = self._data

        if not rows:
            QMessageBox.information(self, "Export PDF", "Aucun paiement à exporter.")
            return

        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.units import cm
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle)
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.colors import HexColor

            now      = datetime.now()
            d_from_s = self.date_from.date().toPyDate().strftime('%d/%m/%Y')
            d_to_s   = self.date_to.date().toPyDate().strftime('%d/%m/%Y')

            export_dir = os.path.join(os.getcwd(), 'exports_commandes')
            os.makedirs(export_dir, exist_ok=True)
            fname = os.path.join(
                export_dir,
                f"hotel_caisse_{now.strftime('%Y%m%d%H%M%S')}.pdf")

            doc = SimpleDocTemplate(fname, pagesize=landscape(A4),
                                    leftMargin=1.5*cm, rightMargin=1.5*cm,
                                    topMargin=1.5*cm, bottomMargin=1.5*cm)
            styles = getSampleStyleSheet()
            els = []

            els.append(Paragraph("<b>CAISSE HÔTEL – RAPPORT PAIEMENTS</b>",
                                  styles['Title']))
            els.append(Paragraph(
                f"Période : {d_from_s} – {d_to_s}  |  "
                f"Généré le : {now.strftime('%d/%m/%Y %H:%M')}",
                styles['Normal']))
            els.append(Spacer(1, 0.4*cm))

            headers = ['#', 'Réservation', 'Client', 'Montant',
                       'Méthode', 'Reçu par',
                       'Dt. Réservation', 'Check-in', 'Check-out',
                       'Date / Heure paiement']
            tbl_data = [headers]
            total = 0.0
            totals = {'cash': 0.0, 'mobile_money': 0.0, 'carte': 0.0}

            def _fmtd(v):
                if v is None:
                    return '-'
                try:
                    return v.strftime('%d/%m/%Y %H:%M')
                except Exception:
                    return str(v)

            for idx, pay in enumerate(rows, start=1):
                dt_str = (pay['created_at'].strftime('%d/%m/%Y %H:%M')
                          if hasattr(pay.get('created_at'), 'strftime')
                          else str(pay.get('created_at', '-')))
                amt    = pay.get('amount', 0)
                method = pay.get('method', '')
                tbl_data.append([
                    str(idx),
                    pay.get('reservation_code', '-'),
                    (pay.get('client') or '')[:28],
                    f"{amt:,.0f}" if isinstance(amt, (int, float)) else '-',
                    METHOD_LABELS.get(method, method),
                    (pay.get('user_name') or str(pay.get('user_id', '-')))[:22],
                    _fmtd(pay.get('date_reservation')),
                    _fmtd(pay.get('date_checkin')),
                    _fmtd(pay.get('date_checkout')),
                    dt_str,
                ])
                total += float(amt or 0)
                if method in totals:
                    totals[method] += float(amt or 0)

            tbl_data.append([
                f"TOTAL ({len(rows)})", '', '', f"{total:,.0f}", '', '', '', '', '', '',
            ])

            cws = [1.2*cm, 3*cm, 5*cm, 2.8*cm, 2.8*cm, 4*cm,
                   2.8*cm, 2.8*cm, 2.8*cm, 3.8*cm]
            tbl = Table(tbl_data, colWidths=cws, repeatRows=1)
            tbl.setStyle(TableStyle([
                ('BACKGROUND',     (0, 0), (-1, 0),  HexColor('#34495E')),
                ('TEXTCOLOR',      (0, 0), (-1, 0),  HexColor('#FFFFFF')),
                ('FONTNAME',       (0, 0), (-1, 0),  'Helvetica-Bold'),
                ('FONTSIZE',       (0, 0), (-1, -1), 8),
                ('GRID',           (0, 0), (-1, -1), 0.3, HexColor('#CCCCCC')),
                ('ROWBACKGROUNDS', (1, 1), (-2, -1),
                 [HexColor('#FFFFFF'), HexColor('#F5F6FA')]),
                ('BACKGROUND',     (0, -1), (-1, -1), HexColor('#2C3E50')),
                ('TEXTCOLOR',      (0, -1), (-1, -1), HexColor('#FFFFFF')),
                ('FONTNAME',       (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('ALIGN',          (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN',         (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWHEIGHT',      (0, 0), (-1, -1), 0.55*cm),
                ('PADDING',        (0, 0), (-1, -1), 3),
            ]))
            els.append(tbl)
            els.append(Spacer(1, 0.5*cm))

            # Résumé par méthode
            els.append(Paragraph("<b>Résumé par méthode</b>", styles['Heading3']))
            sum_data = [
                ["Total transactions",  str(len(rows))],
                ["Espèces",             f"{totals['cash']:,.0f}"],
                ["Mobile Money",        f"{totals['mobile_money']:,.0f}"],
                ["Carte",               f"{totals['carte']:,.0f}"],
                ["TOTAL",               f"{total:,.0f}"],
            ]
            sum_tbl = Table(sum_data, colWidths=[5*cm, 4*cm])
            sum_tbl.setStyle(TableStyle([
                ('GRID',       (0, 0), (-1, -1), 0.4, HexColor('#CCCCCC')),
                ('BACKGROUND', (0, 0), (0, -2),  HexColor('#ECF0F1')),
                ('BACKGROUND', (0, -1), (-1, -1), HexColor('#1976D2')),
                ('TEXTCOLOR',  (0, -1), (-1, -1), HexColor('#FFFFFF')),
                ('FONTNAME',   (0, 0), (0, -1),  'Helvetica-Bold'),
                ('FONTNAME',   (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE',   (0, 0), (-1, -1), 9),
                ('PADDING',    (0, 0), (-1, -1), 5),
                ('ALIGN',      (1, 0), (1, -1),  'RIGHT'),
            ]))
            els.append(sum_tbl)

            doc.build(els)

            if os.name == 'nt':
                os.startfile(fname)
            elif sys.platform == 'darwin':
                subprocess.run(['open', fname])
            else:
                subprocess.run(['xdg-open', fname])

            QMessageBox.information(self, "Export PDF",
                                    f"Fichier exporté :\n{fname}")

        except Exception as e:
            QMessageBox.warning(self, "Export PDF", f"Erreur export : {e}")
