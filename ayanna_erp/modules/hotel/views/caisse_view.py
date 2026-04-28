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
from ayanna_erp.modules.hotel.utils.helpers import (
    fmt_datetime, get_hotel_company_info, fmt_amount, build_pdf_company_header,
)

_svc = PaymentService()

COLUMNS = ['#', 'Réservation', 'Client', 'Chambre', 'Montant encaissé',
           'Montant facture', 'Méthode', 'Référence',
           'Reçu par', 'Dt. Réservation', 'Check-in', 'Check-out',
           'Date / Heure paiement']

METHOD_LABELS = {
    'cash':           'Espèces',
    'airtelmoney':    'Airtel Money',
    'orangemoney':    'Orange Money',
    'mpesa':          'M-Pesa',
    'equitybcdc':     'Equity BCDC',
    'tmb':            'TMB',
    'rawbank':        'Rawbank',
    'smico':          'Smico',
    'credit':         'Crédit (dette)',
    'remboursement':  'Remboursement',
}

# Couleurs distinctes par méthode pour le tableau
METHOD_COLORS = {
    'cash':           '#27AE60',
    'airtelmoney':    '#E74C3C',
    'orangemoney':    '#E67E22',
    'mpesa':          '#C0392B',
    'equitybcdc':     '#1976D2',
    'tmb':            '#1565C0',
    'rawbank':        '#0288D1',
    'smico':          '#00796B',
    'credit':         '#8E44AD',
    'remboursement':  '#E53935',
}

# Groupes pour le résumé
MOBILE_METHODS = {'airtelmoney', 'orangemoney', 'mpesa'}
BANQUE_METHODS = {'equitybcdc', 'tmb', 'rawbank', 'smico'}

def _method_group(method: str) -> str:
    """Retourne le groupe du mode de paiement : cash / mobile / banque / credit / remboursement."""
    if method == 'cash':
        return 'cash'
    if method in MOBILE_METHODS:
        return 'mobile'
    if method in BANQUE_METHODS:
        return 'banque'
    if method == 'credit':
        return 'credit'
    if method == 'remboursement':
        return 'remboursement'
    return 'autre'


class CaisseView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list = []
        _ci = get_hotel_company_info()
        self._sym = _ci.get('currency_symbol', '$')
        self._company_info = _ci
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
        self.lbl_banque = _slbl()
        self.lbl_credit = _slbl()
        self.lbl_remb   = _slbl()
        self.lbl_total  = _slbl()
        for lb in (self.lbl_count, self.lbl_cash, self.lbl_mobile,
                   self.lbl_banque, self.lbl_credit, self.lbl_remb, self.lbl_total):
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
            or s in (p.get('room_number') or '').lower()
            or s in METHOD_LABELS.get(p.get('method', ''), p.get('method', '')).lower()
            or s in (p.get('user_name') or '').lower()
        ]
        self._fill_table(filtered)

    def _fill_table(self, rows: list):
        self.table.setRowCount(0)
        total = 0.0
        credit_du = 0.0   # somme des montants facturés non encaissés (crédit)
        grp = {'cash': 0.0, 'mobile': 0.0, 'banque': 0.0, 'credit': 0.0, 'remboursement': 0.0, 'autre': 0.0}

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
            total_invoice = pay.get('total_amount', 0.0)
            is_credit = (method == 'credit')

            # Montant encaissé : 0 pour crédit
            encaisse_str = fmt_amount(amt, self._sym) if isinstance(amt, (int, float)) else '-'
            # Montant facture : toujours affiché, souligné pour crédit
            facture_str = fmt_amount(total_invoice, self._sym) if isinstance(total_invoice, (int, float)) else '-'

            vals = [
                str(idx),
                pay.get('reservation_code', '-'),
                pay.get('client', '-'),
                pay.get('room_number', '-'),
                encaisse_str,
                facture_str,
                method_label,
                pay.get('reference') or '-',
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

            # Coloration ligne crédit (fond violet très clair)
            if is_credit:
                for col in range(len(vals)):
                    it = self.table.item(r, col)
                    if it:
                        it.setBackground(QBrush(QColor('#F3E5F5')))
                # Montant facture (col 5) en rouge gras pour bien signaler la dette
                it_facture = self.table.item(r, 5)
                if it_facture:
                    it_facture.setForeground(QBrush(QColor('#8E44AD')))
                    it_facture.setFont(QFont('', -1, QFont.Weight.Bold))
                credit_du += float(total_invoice or 0)

            # Coloration méthode (col 6)
            color = METHOD_COLORS.get(method)
            m_item = self.table.item(r, 6)
            if m_item and color:
                m_item.setForeground(QBrush(QColor(color)))
                m_item.setFont(QFont('', -1, QFont.Weight.Bold))

            total += float(amt or 0)
            g = _method_group(method)
            grp[g] += float(amt or 0)

        self.lbl_count.setText(f"📋 {len(rows)} paiements")
        self.lbl_cash.setText(f"💵 Espèces : {fmt_amount(grp['cash'], self._sym)}")
        self.lbl_mobile.setText(f"📱 Mobile : {fmt_amount(grp['mobile'], self._sym)}")
        self.lbl_banque.setText(f"🏦 Banque : {fmt_amount(grp['banque'], self._sym)}")
        self.lbl_credit.setText(
            f"📋 Crédit – dû : {fmt_amount(credit_du, self._sym)}")
        self.lbl_remb.setText(f"↩️ Remb. : {fmt_amount(grp['remboursement'], self._sym)}")
        self.lbl_total.setText(f"✅ TOTAL encaissé : {fmt_amount(total, self._sym)}")

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
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.colors import HexColor, white

            now      = datetime.now()
            d_from_s = self.date_from.date().toPyDate().strftime('%d/%m/%Y')
            d_to_s   = self.date_to.date().toPyDate().strftime('%d/%m/%Y')

            export_dir = os.path.join(os.getcwd(), 'exports_commandes')
            os.makedirs(export_dir, exist_ok=True)
            fname = os.path.join(
                export_dir,
                f"hotel_caisse_{now.strftime('%Y%m%d%H%M%S')}.pdf")

            # A4 paysage : marges 1.5 cm → largeur utile ≈ 26.7 cm
            PAGE = landscape(A4)
            LM = RM = 1.5 * cm
            TM = BM = 1.5 * cm
            avail_w_cm = (PAGE[0] - LM - RM) / cm

            doc = SimpleDocTemplate(fname, pagesize=PAGE,
                                    leftMargin=LM, rightMargin=RM,
                                    topMargin=TM, bottomMargin=BM)
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle('CTitle', parent=styles['Title'],
                                      fontSize=13, alignment=1, spaceAfter=4))
            styles.add(ParagraphStyle('CSub', parent=styles['Normal'],
                                      fontSize=8, alignment=1, spaceAfter=6))
            styles.add(ParagraphStyle('SmallInfo', parent=styles['Normal'],
                                      fontSize=7,
                                      textColor=HexColor('#555555')))
            els = []

            # ── En-tête entreprise ──────────────────────────────────────
            ci  = self._company_info
            sym = self._sym
            logo_path = build_pdf_company_header(els, styles, ci, avail_w_cm)

            els.append(Paragraph("<b>CAISSE HÔTEL – RAPPORT PAIEMENTS</b>",
                                  styles['CTitle']))
            els.append(Paragraph(
                f"Période : {d_from_s} – {d_to_s}  |  "
                f"Généré le : {now.strftime('%d/%m/%Y %H:%M')}",
                styles['CSub']))
            els.append(Spacer(1, 0.3 * cm))

            # ── Tableau ─────────────────────────────────────────────────
            headers = ['#', 'Réservation', 'Client', 'Chambre',
                       'Encaissé', 'Facture', 'Méthode',
                       'Référence', 'Reçu par',
                       'Dt. Réservation', 'Check-in', 'Check-out',
                       'Date paiement']
            tbl_data = [headers]
            total = 0.0
            credit_du = 0.0
            grp = {'cash': 0.0, 'mobile': 0.0, 'banque': 0.0, 'credit': 0.0, 'remboursement': 0.0, 'autre': 0.0}
            per_method: dict = {}  # method → montant pour le détail PDF
            credit_row_indices = []  # indices (1-based dans tbl_data) des lignes crédit

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
                total_invoice = pay.get('total_amount', 0.0)
                is_credit = (method == 'credit')
                encaisse_str = fmt_amount(amt, sym) if isinstance(amt, (int, float)) else '-'
                facture_str  = fmt_amount(total_invoice, sym) if isinstance(total_invoice, (int, float)) else '-'
                tbl_data.append([
                    str(idx),
                    pay.get('reservation_code', '-'),
                    (pay.get('client') or '')[:26],
                    (pay.get('room_number') or '-')[:10],
                    encaisse_str,
                    facture_str,
                    METHOD_LABELS.get(method, method),
                    (pay.get('reference') or '-')[:24],
                    (pay.get('user_name') or str(pay.get('user_id', '-')))[:20],
                    _fmtd(pay.get('date_reservation')),
                    _fmtd(pay.get('date_checkin')),
                    _fmtd(pay.get('date_checkout')),
                    dt_str,
                ])
                if is_credit:
                    credit_row_indices.append(len(tbl_data) - 1)  # 1-based dans tbl_data
                    credit_du += float(total_invoice or 0)
                total += float(amt or 0)
                g = _method_group(method)
                grp[g] += float(amt or 0)
                per_method[method] = per_method.get(method, 0.0) + float(amt or 0)

            tbl_data.append([
                f"TOTAL ({len(rows)})", '', '', '',
                fmt_amount(total, sym), '', '', '', '', '', '', '', '',
            ])

            cws = [0.7*cm, 2.2*cm, 3.0*cm, 1.8*cm, 2.2*cm, 2.2*cm,
                   2.2*cm, 2.4*cm, 2.2*cm,
                   2.4*cm, 2.4*cm, 2.4*cm, 2.8*cm]
            tbl = Table(tbl_data, colWidths=cws, repeatRows=1,
                        hAlign='CENTER')
            style_cmds = [
                ('BACKGROUND',     (0, 0),  (-1, 0),  HexColor('#2C3E50')),
                ('TEXTCOLOR',      (0, 0),  (-1, 0),  white),
                ('FONTNAME',       (0, 0),  (-1, 0),  'Helvetica-Bold'),
                ('FONTSIZE',       (0, 0),  (-1, -1), 7),
                ('GRID',           (0, 0),  (-1, -1), 0.3, HexColor('#CCCCCC')),
                ('ROWBACKGROUNDS', (1, 1),  (-2, -1),
                 [HexColor('#FFFFFF'), HexColor('#F5F6FA')]),
                ('BACKGROUND',     (0, -1), (-1, -1), HexColor('#1976D2')),
                ('TEXTCOLOR',      (0, -1), (-1, -1), white),
                ('FONTNAME',       (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('ALIGN',          (0, 0),  (-1, -1), 'CENTER'),
                ('VALIGN',         (0, 0),  (-1, -1), 'MIDDLE'),
                ('ROWHEIGHT',      (0, 0),  (-1, -1), 0.55 * cm),
                ('PADDING',        (0, 0),  (-1, -1), 3),
            ]
            # Lignes crédit : fond violet clair + colonne Facture en violet gras
            for ri in credit_row_indices:
                style_cmds.append(
                    ('BACKGROUND', (0, ri), (-1, ri), HexColor('#F3E5F5')))
                style_cmds.append(
                    ('TEXTCOLOR',  (5, ri), (5, ri),  HexColor('#6A1B9A')))
                style_cmds.append(
                    ('FONTNAME',   (5, ri), (5, ri),  'Helvetica-Bold'))
            tbl.setStyle(TableStyle(style_cmds))
            els.append(tbl)
            els.append(Spacer(1, 0.4 * cm))

            # ── Résumé par méthode ───────────────────────────────────────
            els.append(Paragraph("<b>Résumé par mode de paiement</b>", styles['Heading3']))

            # Groupes
            sum_data = [["Mode de paiement", "Montant"]]
            # Espèces
            if grp['cash']:
                sum_data.append(["💵 Espèces", fmt_amount(grp['cash'], sym)])
            # Mobile Money – détail par opérateur
            if grp['mobile']:
                sum_data.append(["📱 Mobile Money (total)", fmt_amount(grp['mobile'], sym)])
                for m in ('airtelmoney', 'orangemoney', 'mpesa'):
                    if per_method.get(m):
                        sum_data.append([f"   └ {METHOD_LABELS[m]}", fmt_amount(per_method[m], sym)])
            # Banque – détail
            if grp['banque']:
                sum_data.append(["🏦 Banque (total)", fmt_amount(grp['banque'], sym)])
                for m in ('equitybcdc', 'tmb', 'rawbank', 'smico'):
                    if per_method.get(m):
                        sum_data.append([f"   └ {METHOD_LABELS[m]}", fmt_amount(per_method[m], sym)])
            # Crédit
            if grp['credit'] or credit_du:
                sum_data.append(["📋 Crédit – montant dû (factures)",
                                  fmt_amount(credit_du, sym)])
            # Remboursements (négatifs – annulations)
            if grp['remboursement']:
                sum_data.append(["\u21a9\ufe0f Remboursements", fmt_amount(grp['remboursement'], sym)])
            # Autres éventuels
            if grp['autre']:
                sum_data.append(["Autre", fmt_amount(grp['autre'], sym)])
            # Total
            sum_data.append([f"TOTAL ({len(rows)} paiements)", fmt_amount(total, sym)])

            sum_tbl = Table(sum_data, colWidths=[7 * cm, 5 * cm])
            # Indices des lignes de sous-total (total groupe)
            grp_rows = [i for i, row in enumerate(sum_data)
                        if row[0] in ("💵 Espèces", "📱 Mobile Money (total)",
                                      "🏦 Banque (total)", "📋 Crédit (dette)",
                                      "\u21a9\ufe0f Remboursements", "Autre")]
            # Indices des lignes de remboursement (affichées en rouge)
            remb_rows = [i for i, row in enumerate(sum_data)
                         if row[0] == "\u21a9\ufe0f Remboursements"]
            last = len(sum_data) - 1
            style_cmds = [
                ('GRID',       (0, 0),  (-1, -1), 0.4, HexColor('#CCCCCC')),
                ('BACKGROUND', (0, 0),  (-1, 0),  HexColor('#34495E')),
                ('TEXTCOLOR',  (0, 0),  (-1, 0),  white),
                ('FONTNAME',   (0, 0),  (-1, 0),  'Helvetica-Bold'),
                ('BACKGROUND', (0, last), (-1, last), HexColor('#27AE60')),
                ('TEXTCOLOR',  (0, last), (-1, last), white),
                ('FONTNAME',   (0, last), (-1, last), 'Helvetica-Bold'),
                ('FONTSIZE',   (0, 0),  (-1, -1), 9),
                ('PADDING',    (0, 0),  (-1, -1), 5),
                ('ALIGN',      (1, 0),  (1, -1),  'RIGHT'),
            ]
            for gi in grp_rows:
                style_cmds.append(('BACKGROUND', (0, gi), (-1, gi), HexColor('#ECF0F1')))
                style_cmds.append(('FONTNAME', (0, gi), (-1, gi), 'Helvetica-Bold'))
            for ri in remb_rows:
                style_cmds.append(('TEXTCOLOR', (0, ri), (-1, ri), HexColor('#E53935')))
                style_cmds.append(('FONTNAME', (0, ri), (-1, ri), 'Helvetica-Bold'))
            sum_tbl.setStyle(TableStyle(style_cmds))
            els.append(sum_tbl)
            els.append(Spacer(1, 0.3 * cm))
            els.append(Paragraph(
                f"Informatisé par Ayanna ERP – {now.strftime('%d/%m/%Y %H:%M')}",
                styles['SmallInfo']))

            doc.build(els)

            # Nettoyage logo
            if logo_path and os.path.exists(logo_path):
                try:
                    os.unlink(logo_path)
                except Exception:
                    pass

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
