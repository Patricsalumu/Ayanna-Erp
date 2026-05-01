"""
ReservationView – onglet de gestion des réservations hôtelières.
"""
from datetime import datetime, date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QDateEdit, QComboBox,
    QHeaderView, QMessageBox, QAbstractItemView, QFrame,
    QDialog, QScrollArea, QSizePolicy, QSpacerItem
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
    fmt_date, fmt_datetime, reservation_status_label, payment_status_label,
    RESERVATION_STATUS_COLORS, PAYMENT_STATUS_COLORS,
    get_hotel_company_info, fmt_amount, build_pdf_company_header,
)

_res_svc  = ReservationService()
_pay_svc  = PaymentService()
_room_svc = RoomService()


# ============================================================================
# Fiche détaillée de réservation (Check-out, Prolonger, Annuler, Imprimer)
# ============================================================================

class ReservationDetailDialog(QDialog):
    """
    Fiche complète d'une réservation.
    Actions disponibles selon le statut :
      - Check-out (en_cours  → done(ACTION_CHECKOUT))
      - Prolonger (en_cours  → done(ACTION_EXTEND))
      - Annuler   (en_attente → done(ACTION_CANCEL))
    """
    ACTION_CHECKOUT = QDialog.DialogCode.Accepted   # = 1
    ACTION_EXTEND   = 2
    ACTION_CANCEL   = 3

    def __init__(self, row: dict, parent=None):
        super().__init__(parent)
        self._row = row
        status = row.get('status', '')
        titles = {
            'en_attente': '⏳ Fiche réservation (En attente)',
            'confirmee':  '✅ Fiche réservation (Confirmée)',
            'en_cours':   '🔑 Fiche réservation (En cours)',
            'terminee':   '🏁 Fiche réservation (Terminée)',
            'annulee':    '❌ Fiche réservation (Annulée)',
        }
        self.setWindowTitle(titles.get(status, 'Fiche réservation') +
                            f' – {row["code"]}')
        self.setMinimumWidth(600)
        self.setMinimumHeight(640)
        self.setModal(True)
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        r       = self._row
        status  = r.get('status', '')
        now     = datetime.now()

        # --- Header colour by status ---
        hdr_colors = {
            'en_attente': '#F39C12',
            'confirmee':  '#2980B9',
            'en_cours':   '#27AE60',
            'terminee':   '#7F8C8D',
            'annulee':    '#95A5A6',
        }
        hdr_color = hdr_colors.get(status, '#34495E')
        status_title = {
            'en_attente': '⏳ EN ATTENTE',
            'confirmee':  '✅ CONFIRMÉE',
            'en_cours':   '🔑 EN COURS',
            'terminee':   '🏁 TERMINÉE',
            'annulee':    '❌ ANNULÉE',
        }.get(status, status.upper())
        header = QLabel(f"{status_title}  –  {r['code']}")
        header.setFixedHeight(48)
        header.setStyleSheet(
            f"background:{hdr_color};color:white;font-size:16px;"
            "font-weight:bold;padding-left:16px;")
        root.addWidget(header)

        # --- Scrollable body ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;}")
        body   = QWidget()
        vbox   = QVBoxLayout(body)
        vbox.setSpacing(10)
        vbox.setContentsMargins(16, 12, 16, 12)

        def section(title):
            lbl = QLabel(title)
            lbl.setStyleSheet(
                "font-size:12px;font-weight:bold;color:white;"
                "background:#34495E;padding:4px 8px;border-radius:3px;")
            vbox.addWidget(lbl)

        def row_info(label, value, value_color='#2C3E50', bold=False):
            hl  = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet("color:#666;font-size:12px;min-width:200px;")
            lbl.setFixedWidth(200)
            val = QLabel(str(value))
            w   = 'bold' if bold else 'normal'
            val.setStyleSheet(
                f"color:{value_color};font-size:13px;font-weight:{w};")
            hl.addWidget(lbl)
            hl.addWidget(val)
            hl.addStretch()
            vbox.addLayout(hl)

        jr          = r.get('jours_reels', '-')
        montant_reel = r.get('montant_reel', r.get('total', 0))
        paid        = r.get('paid', 0)
        solde       = r.get('solde', montant_reel - paid)
        price       = r.get('price_per_night', 0)
        reduction   = r.get('reduction', 0)
        nuitees     = r.get('nuitees', '-')
        _ci  = get_hotel_company_info()
        _sym = _ci.get('currency_symbol', '$')

        # ── Section réservation ──────────────────────────────────────────────
        section("  Informations de réservation")
        row_info("Code réservation :",   r['code'])
        row_info("Client :",              r['client_name'], bold=True)
        row_info("Catégorie :",           r['category'])
        row_info("Chambre :",             r['room'])
        row_info("Créé par :",
                 r.get('created_by_name') or '-', '#8E44AD')
        row_info("Date de réservation :", _fmt_dt(r.get('created_at')))
        # Pays et pièce d'identité
        pays_val = r.get('pays', '').strip()
        ci_val   = r.get('carte_identite', '').strip()
        if pays_val:
            row_info("Pays :", pays_val)
        if ci_val:
            row_info("Pièce d'identité :", ci_val)
        vbox.addSpacing(4)

        # ── Section dates ────────────────────────────────────────────────────
        section("  Dates")
        row_info("Entrée prévue :",    fmt_date(r['date_entree_prevue']))
        row_info("Sortie prévue :",    fmt_date(r['date_sortie_prevue']))
        row_info("Nuitées prévues :",  str(nuitees))
        row_info("Entrée réelle :",
                 fmt_datetime(r.get('date_entree_reelle')), '#27AE60')
        if status == 'en_cours':
            row_info("Check-out (maintenant) :",
                     now.strftime('%d/%m/%Y %H:%M'), '#E74C3C', bold=True)
        elif r.get('date_sortie_reelle'):
            row_info("Sortie réelle :",
                     fmt_datetime(r['date_sortie_reelle']), '#E74C3C')
        vbox.addSpacing(4)

        # ── Section financière ───────────────────────────────────────────────
        section("  Récapitulatif financier")
        if status == 'en_cours':
            row_info("Jours réels passés :",
                     str(jr) if jr != '-' else 'N/A', '#1976D2', bold=True)
        row_info("Prix / nuit :",         fmt_amount(price, _sym))
        row_info("Réduction :",           fmt_amount(reduction, _sym))
        row_info("Montant réel à payer :",
                 fmt_amount(montant_reel, _sym), '#1976D2', bold=True)
        row_info("Déjà payé :",           fmt_amount(paid, _sym), '#27AE60')

        if isinstance(solde, (int, float)):
            if solde > 0:
                row_info("Reste à payer :", fmt_amount(solde, _sym), '#E74C3C', bold=True)
            elif solde < 0:
                row_info("Crédit (trop payé) :", fmt_amount(abs(solde), _sym), '#27AE60', bold=True)
            else:
                row_info("Solde :", "Soldé ✓", '#27AE60', bold=True)
        vbox.addSpacing(4)

        # ── Section paiements ────────────────────────────────────────────────
        section("  Détail des paiements")
        pays = []
        try:
            pays = _pay_svc.get_payments_for_reservation(r['id'])
        except Exception:
            pass

        if pays:
            pay_tbl = QTableWidget(len(pays), 5)
            pay_tbl.setHorizontalHeaderLabels(
                ['#', 'Date / Heure', 'Montant', 'Méthode', 'Reçu par'])
            pay_tbl.setEditTriggers(
                QAbstractItemView.EditTrigger.NoEditTriggers)
            pay_tbl.setSelectionMode(
                QAbstractItemView.SelectionMode.NoSelection)
            pay_tbl.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.Stretch)
            pay_tbl.verticalHeader().setVisible(False)
            pay_tbl.setAlternatingRowColors(True)
            pay_tbl.setFixedHeight(min(200, 32 + 28 * len(pays)))
            pay_tbl.setStyleSheet(
                "QTableWidget{border:1px solid #ddd;}"
                "QHeaderView::section{background:#8E44AD;color:white;"
                "padding:4px;font-weight:bold;font-size:11px;}")
            for i, p in enumerate(pays):
                dt_str = (p['created_at'].strftime('%d/%m/%Y %H:%M')
                          if hasattr(p.get('created_at'), 'strftime')
                          else str(p.get('created_at', '-')))
                amt_str = fmt_amount(p['amount'], _sym) if isinstance(
                    p.get('amount'), (int, float)) else '-'
                for col, val in enumerate([
                    str(i + 1), dt_str, amt_str,
                    p.get('method', '-'),
                    p.get('user_name', str(p.get('user_id', '-'))),
                ]):
                    it = QTableWidgetItem(val)
                    it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    pay_tbl.setItem(i, col, it)
            vbox.addWidget(pay_tbl)
        else:
            lbl_no_pay = QLabel("  Aucun paiement enregistré.")
            lbl_no_pay.setStyleSheet("color:#95A5A6;font-style:italic;")
            vbox.addWidget(lbl_no_pay)

        vbox.addSpacing(4)

        # ── Notes ────────────────────────────────────────────────────────────
        notes = r.get('notes', '').strip()
        if notes:
            section("  Notes")
            lbl_notes = QLabel(notes)
            lbl_notes.setWordWrap(True)
            lbl_notes.setStyleSheet("color:#555;font-size:12px;padding:4px 8px;")
            vbox.addWidget(lbl_notes)

        vbox.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll)

        # --- Footer (buttons) ---
        foot = QWidget()
        foot.setFixedHeight(56)
        foot.setStyleSheet("background:#F5F6FA;border-top:1px solid #ddd;")
        btn_row = QHBoxLayout(foot)
        btn_row.setContentsMargins(16, 10, 16, 10)
        btn_row.setSpacing(10)

        self.btn_pay_modal = QPushButton("💰 Payer")
        self.btn_pay_modal.setFixedHeight(34)
        self.btn_pay_modal.setStyleSheet(
            "QPushButton{background:#8E44AD;color:white;border-radius:4px;"
            "padding:0 12px;font-weight:bold;}"
            "QPushButton:hover{background:#6C3483;}"
            "QPushButton:disabled{background:#DFE6E9;color:#B2BEC3;}")
        _payable = status in ('en_attente', 'confirmee', 'en_cours')
        self.btn_pay_modal.setEnabled(_payable)
        self.btn_pay_modal.clicked.connect(self._do_pay)

        btn_close = QPushButton("❌ Fermer")
        btn_close.setFixedHeight(34)
        btn_close.setStyleSheet(
            "QPushButton{background:#95A5A6;color:white;border-radius:4px;"
            "padding:0 14px;}QPushButton:hover{background:#7F8C8D;}")
        btn_close.clicked.connect(self.reject)

        self.btn_print = QPushButton("🖨️ Imprimer")
        self.btn_print.setFixedHeight(34)
        self.btn_print.setStyleSheet(
            "QPushButton{background:#34495E;color:white;border-radius:4px;"
            "padding:0 14px;}QPushButton:hover{background:#2C3E50;}")
        self.btn_print.clicked.connect(self._do_print)

        self.btn_annuler = QPushButton("✖ Annuler résv.")
        self.btn_annuler.setFixedHeight(34)
        self.btn_annuler.setStyleSheet(
            "QPushButton{background:#7F8C8D;color:white;border-radius:4px;"
            "padding:0 12px;font-weight:bold;}"
            "QPushButton:hover{background:#636E72;}"
            "QPushButton:disabled{background:#DFE6E9;color:#B2BEC3;}")
        self.btn_annuler.setEnabled(status == 'en_attente')
        self.btn_annuler.clicked.connect(self._do_annuler)

        self.btn_extend = QPushButton("📅 Prolonger")
        self.btn_extend.setFixedHeight(34)
        self.btn_extend.setStyleSheet(
            "QPushButton{background:#E67E22;color:white;border-radius:4px;"
            "padding:0 12px;font-weight:bold;}"
            "QPushButton:hover{background:#D35400;}"
            "QPushButton:disabled{background:#DFE6E9;color:#B2BEC3;}")
        self.btn_extend.setEnabled(status == 'en_cours')
        self.btn_extend.clicked.connect(lambda: self.done(self.ACTION_EXTEND))

        self.btn_checkout = QPushButton("🚪 Check-out")
        self.btn_checkout.setFixedHeight(34)
        self.btn_checkout.setStyleSheet(
            "QPushButton{background:#E74C3C;color:white;border-radius:4px;"
            "padding:0 12px;font-weight:bold;}"
            "QPushButton:hover{background:#C0392B;}"
            "QPushButton:disabled{background:#DFE6E9;color:#B2BEC3;}")
        self.btn_checkout.setEnabled(status == 'en_cours')
        self.btn_checkout.clicked.connect(self._do_checkout)

        btn_row.addWidget(btn_close)
        btn_row.addWidget(self.btn_print)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_pay_modal)
        btn_row.addWidget(self.btn_annuler)
        btn_row.addWidget(self.btn_extend)
        btn_row.addWidget(self.btn_checkout)
        root.addWidget(foot)

    # ------------------------------------------------------------------
    def _do_pay(self):
        from ayanna_erp.modules.hotel.views.payment_dialog import PaymentDialog
        dlg = PaymentDialog(self._row, self)
        if dlg.exec() != PaymentDialog.DialogCode.Accepted:
            return
        ok, msg = _pay_svc.add_payment(
            self._row['id'], dlg.get_amount(), dlg.get_method(),
            self._get_uid(), reference=dlg.get_reference(),
            compte_id=dlg.get_compte_id())
        if ok:
            QMessageBox.information(self, "Paiement", msg)
            # Recharger les données du paiement et rafraîchir la vue parente
            if hasattr(self.parent(), 'refresh'):
                self.parent().refresh()
            self.reject()  # ferme la modale — la vue parente est à jour
        else:
            QMessageBox.warning(self, "Erreur paiement", msg)

    def _get_uid(self):
        p = self.parent()
        if p is not None and hasattr(p, '_uid'):
            return p._uid()
        return 1

    def _do_checkout(self):
        reply = QMessageBox.question(
            self, "Confirmer check-out",
            f"Confirmer le check-out de la réservation {self._row['code']} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.done(int(self.ACTION_CHECKOUT))

    def _do_annuler(self):
        reply = QMessageBox.question(
            self, "Confirmer annulation",
            f"Annuler la réservation {self._row['code']} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.done(self.ACTION_CANCEL)

    def _do_print(self):
        fmt_dlg = _PrintFormatDialog(self)
        if fmt_dlg.exec() != QDialog.DialogCode.Accepted:
            return
        _print_checkout_pdf(self._row, fmt_dlg.get_format(), self)


def _fmt_dt(dt) -> str:
    """Formate un datetime ou date en 'dd/mm/yyyy HH:MM', ou '-' si None."""
    if dt is None:
        return '-'
    try:
        return dt.strftime('%d/%m/%Y %H:%M')
    except Exception:
        return str(dt)


def _pdf_table(data):
    """Construit un reportlab.Table simple à deux colonnes."""
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib.units import cm
    from reportlab.lib.colors import HexColor, black
    t = Table(data, colWidths=[6*cm, 10*cm])
    t.setStyle(TableStyle([
        ('GRID',       (0, 0), (-1, -1), 0.4, HexColor('#CCCCCC')),
        ('BACKGROUND', (0, 0), (0, -1),  HexColor('#ECF0F1')),
        ('FONTNAME',   (0, 0), (0, -1),  'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1),
         [HexColor('#FFFFFF'), HexColor('#F9F9F9')]),
        ('PADDING',    (0, 0), (-1, -1), 5),
    ]))
    return t


# ============================================================================
# Dialogue de choix de format d'impression
# ============================================================================

class _PrintFormatDialog(QDialog):
    """Petit dialogue pour choisir le format : A4 ou 80 mm (ticket thermique)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Format d'impression")
        self.setFixedSize(320, 130)
        self.setModal(True)
        self._format = 'a4'
        vbox = QVBoxLayout(self)
        vbox.setSpacing(10)
        vbox.setContentsMargins(16, 14, 16, 14)
        vbox.addWidget(QLabel("Choisissez le format d'impression :"))
        btns = QHBoxLayout()
        btn_a4 = QPushButton("🖨️  A4")
        btn_a4.setFixedHeight(38)
        btn_a4.setStyleSheet(
            "QPushButton{background:#1976D2;color:white;border-radius:5px;"
            "font-size:13px;font-weight:bold;}"
            "QPushButton:hover{background:#1565C0;}")
        btn_a4.clicked.connect(lambda: self._pick('a4'))
        btn_80 = QPushButton("🧾  80 mm (Ticket)")
        btn_80.setFixedHeight(38)
        btn_80.setStyleSheet(
            "QPushButton{background:#27AE60;color:white;border-radius:5px;"
            "font-size:13px;font-weight:bold;}"
            "QPushButton:hover{background:#219A52;}")
        btn_80.clicked.connect(lambda: self._pick('80mm'))
        btns.addWidget(btn_a4)
        btns.addWidget(btn_80)
        vbox.addLayout(btns)

    def _pick(self, fmt: str):
        self._format = fmt
        self.accept()

    def get_format(self) -> str:
        return self._format


# ============================================================================
# Générateur PDF checkout (A4 et 80 mm)
# ============================================================================

def _print_checkout_pdf(row: dict, fmt: str = 'a4', parent=None):
    """Génère et ouvre la fiche de check-out (A4 ou ticket 80 mm)."""
    try:
        import os, subprocess, sys, tempfile
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm, cm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle)
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.colors import HexColor, black, white
        from reportlab.lib.enums import TA_CENTER
        from reportlab.pdfgen import canvas as pdfcanvas

        now = datetime.now()
        r   = row
        ci  = get_hotel_company_info()
        sym = ci.get('currency_symbol', '$')

        jr           = r.get('jours_reels', '-')
        montant_reel = r.get('montant_reel', r.get('total', 0))
        paid         = r.get('paid', 0)
        solde        = r.get('solde', montant_reel - paid)
        if isinstance(solde, (int, float)) and solde > 0:
            solde_str = f"Reste à payer : {fmt_amount(solde, sym)}"
        elif isinstance(solde, (int, float)) and solde < 0:
            solde_str = f"Crédit : {fmt_amount(abs(solde), sym)}"
        else:
            solde_str = "Soldé"

        export_dir = os.path.join(os.getcwd(), 'exports_commandes')
        os.makedirs(export_dir, exist_ok=True)
        suffix = 'a4' if fmt == 'a4' else '80mm'
        fname = os.path.join(
            export_dir,
            f"checkout_{r['code']}_{now.strftime('%Y%m%d%H%M%S')}_{suffix}.pdf")

        styles = getSampleStyleSheet()

        # ==============================================================
        # FORMAT A4
        # ==============================================================
        if fmt == 'a4':
            LM = RM = TM = BM = 2 * cm
            avail_w_cm = (A4[0] - LM - RM) / cm

            doc = SimpleDocTemplate(fname, pagesize=A4,
                                    leftMargin=LM, rightMargin=RM,
                                    topMargin=TM, bottomMargin=BM)
            els = []

            # En-tête entreprise
            logo_path = build_pdf_company_header(els, styles, ci, avail_w_cm)

            styles.add(ParagraphStyle('CkTitle', parent=styles['Title'],
                                      fontSize=14, alignment=1, spaceAfter=6))
            styles.add(ParagraphStyle('SmInfo', parent=styles['Normal'],
                                      fontSize=7, textColor=HexColor('#666666')))
            els.append(Paragraph("<b>FICHE DE CHECK-OUT – HÔTEL</b>",
                                 styles['CkTitle']))
            els.append(Spacer(1, 0.3 * cm))

            def _h3(t):
                return Paragraph(f"<b>{t}</b>", styles['Heading3'])

            els.append(_h3("Informations de réservation"))
            els.append(_pdf_table([
                ["Code réservation", r['code']],
                ["Client",           r['client_name']],
                ["Catégorie",        r['category']],
                ["Chambre",          r['room']],
            ]))
            els.append(Spacer(1, 0.3 * cm))

            els.append(_h3("Dates"))
            els.append(_pdf_table([
                ["Entrée prévue",   fmt_date(r['date_entree_prevue'])],
                ["Sortie prévue",   fmt_date(r['date_sortie_prevue'])],
                ["Nuitées prévues", str(r.get('nuitees', '-'))],
                ["Entrée réelle",   fmt_datetime(r.get('date_entree_reelle'))],
                ["Check-out",       now.strftime('%d/%m/%Y %H:%M')],
            ]))
            els.append(Spacer(1, 0.3 * cm))

            els.append(_h3("Récapitulatif financier"))
            els.append(_pdf_table([
                ["Jours réels passés",  str(jr)],
                ["Prix / nuit",         fmt_amount(r.get('price_per_night', 0), sym)],
                ["Réduction",           fmt_amount(r.get('reduction', 0), sym)],
                ["Montant réel à payer",fmt_amount(montant_reel, sym)],
                ["Déjà payé",           fmt_amount(paid, sym)],
                ["Solde",               solde_str],
            ]))
            els.append(Spacer(1, 0.8 * cm))
            els.append(Paragraph("<i>Merci pour votre séjour.</i>",
                                 styles['Italic']))
            els.append(Spacer(1, 0.3 * cm))
            els.append(Paragraph(
                f"Informatisé par Ayanna ERP – {now.strftime('%d/%m/%Y %H:%M')}",
                styles['SmInfo']))

            doc.build(els)

            # Nettoyage logo
            if logo_path and os.path.exists(logo_path):
                try:
                    os.unlink(logo_path)
                except Exception:
                    pass

        # ==============================================================
        # FORMAT 80 mm (ticket thermique)
        # ==============================================================
        else:
            TICKET_W = 80 * mm
            LEFT_M   = 3 * mm
            cw       = TICKET_W - 2 * LEFT_M

            # --- Créer logo temporaire ---
            logo_path = None
            if ci.get('logo'):
                try:
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                        f.write(ci['logo'])
                        logo_path = f.name
                except Exception:
                    logo_path = None

            # --- Estimation hauteur ---
            y_sim = 120 * mm
            if logo_path:
                y_sim += 18 * mm
            for k in ['address', 'phone', 'id_nat', 'rccm']:
                if ci.get(k):
                    y_sim += 3 * mm
            slogan = ci.get('slogan', '').strip()
            if slogan:
                words = slogan.split()
                lines = 1
                cur_w = 0
                max_c = int(cw / (2.5 * mm))
                for w in words:
                    if cur_w + len(w) + 1 > max_c:
                        lines += 1
                        cur_w = len(w)
                    else:
                        cur_w += len(w) + 1
                y_sim += max(5 * mm, lines * 3.5 * mm)
            TICKET_HEIGHT = max(y_sim, 80 * mm)

            c = pdfcanvas.Canvas(fname, pagesize=(TICKET_W, TICKET_HEIGHT))
            y = TICKET_HEIGHT - 5 * mm

            def _cstr(text, font, size, y_pos, center=False):
                c.setFont(font, size)
                if center:
                    c.drawCentredString(TICKET_W / 2, y_pos, str(text)[:40])
                else:
                    c.drawString(LEFT_M, y_pos, str(text)[:40])
                return y_pos - (size * 0.4 * mm + 1.5 * mm)

            def _draw_wrapped(text, font, size, y_pos, center=False, leading=3.5*mm):
                words = (text or '').split()
                cur = ''
                lines = []
                max_c = int(cw / (size * 0.5 * mm))
                for w in words:
                    test = (cur + ' ' + w).strip()
                    if len(test) <= max_c:
                        cur = test
                    else:
                        if cur:
                            lines.append(cur)
                        cur = w
                if cur:
                    lines.append(cur)
                c.setFont(font, size)
                for line in lines:
                    if center:
                        c.drawCentredString(TICKET_W / 2, y_pos, line)
                    else:
                        c.drawString(LEFT_M, y_pos, line)
                    y_pos -= leading
                return y_pos

            # Logo
            if logo_path and os.path.exists(logo_path):
                c.drawImage(logo_path, (TICKET_W - 15*mm) / 2, y - 15*mm,
                            width=15*mm, height=15*mm, preserveAspectRatio=True)
                y -= 18 * mm

            # Nom entreprise
            c.setFont('Helvetica-Bold', 9)
            c.drawCentredString(TICKET_W / 2, y, ci.get('name', 'HÔTEL')[:30])
            y -= 4 * mm
            c.setFont('Helvetica', 7)
            for k, prefix in [('address', ''), ('phone', 'Tél : '),
                               ('rccm', 'RCCM : '), ('id_nat', 'ID : ')]:
                v = ci.get(k, '').strip()
                if v:
                    c.drawCentredString(TICKET_W / 2, y, f"{prefix}{v}"[:42])
                    y -= 3 * mm

            if slogan:
                y = _draw_wrapped(slogan, 'Helvetica', 7, y, center=True)

            c.setFont('Helvetica', 7)
            c.drawCentredString(TICKET_W / 2, y,
                                f"Devise : {ci.get('currency', 'USD')} ({sym})")
            y -= 4 * mm

            # Séparateur
            c.line(LEFT_M, y, TICKET_W - LEFT_M, y)
            y -= 4 * mm

            # Titre
            c.setFont('Helvetica-Bold', 10)
            c.drawCentredString(TICKET_W / 2, y, "FICHE DE CHECK-OUT")
            y -= 5 * mm

            def _row80(lbl, val, y_pos):
                c.setFont('Helvetica-Bold', 8)
                c.drawString(LEFT_M, y_pos, lbl)
                c.setFont('Helvetica', 8)
                c.drawRightString(TICKET_W - LEFT_M, y_pos, str(val))
                return y_pos - 4 * mm

            c.line(LEFT_M, y, TICKET_W - LEFT_M, y)
            y -= 3 * mm
            for lbl, val in [
                ("Code :",      r['code']),
                ("Client :",    r['client_name']),
                ("Chambre :",   r['room']),
                ("Catégorie :", r['category']),
            ]:
                y = _row80(lbl, val, y)

            c.line(LEFT_M, y, TICKET_W - LEFT_M, y)
            y -= 3 * mm
            for lbl, val in [
                ("Entrée prévue :", fmt_date(r['date_entree_prevue'])),
                ("Sortie prévue :", fmt_date(r['date_sortie_prevue'])),
                ("Nuitées :",       str(r.get('nuitees', '-'))),
                ("Entrée réelle :", fmt_datetime(r.get('date_entree_reelle'))),
                ("Check-out :",     now.strftime('%d/%m/%Y %H:%M')),
            ]:
                y = _row80(lbl, val, y)

            c.line(LEFT_M, y, TICKET_W - LEFT_M, y)
            y -= 3 * mm
            for lbl, val in [
                ("Jours réels :",  str(jr)),
                ("Prix/nuit :",    fmt_amount(r.get('price_per_night', 0), sym)),
                ("Réduction :",    fmt_amount(r.get('reduction', 0), sym)),
                ("Montant réel :", fmt_amount(montant_reel, sym)),
                ("Déjà payé :",   fmt_amount(paid, sym)),
                ("Solde :",        solde_str),
            ]:
                y = _row80(lbl, val, y)

            c.line(LEFT_M, y, TICKET_W - LEFT_M, y)
            y -= 4 * mm
            c.setFont('Helvetica', 8)
            c.drawCentredString(TICKET_W / 2, y, "Merci pour votre séjour !")
            y -= 5 * mm
            c.setFont('Helvetica', 6)
            c.drawCentredString(TICKET_W / 2, y,
                                f"Informatisé par Ayanna ERP {now.strftime('%d/%m/%Y %H:%M')}")
            c.save()

            # Nettoyage logo
            if logo_path and os.path.exists(logo_path):
                try:
                    os.unlink(logo_path)
                except Exception:
                    pass

        # Ouvrir le fichier
        if os.name == 'nt':
            os.startfile(fname)
        elif sys.platform == 'darwin':
            subprocess.run(['open', fname])
        else:
            subprocess.run(['xdg-open', fname])

    except Exception as e:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(parent, "Impression", f"Erreur impression : {e}")


# ============================================================================
# Export PDF liste des réservations filtrées
# ============================================================================

def _export_reservations_pdf(rows: list, date_from, date_to,
                             status_lbl: str, parent=None):
    """Génère un PDF A4 paysage récapitulatif des réservations filtrées."""
    try:
        import os, subprocess, sys
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle)
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.colors import HexColor, white
        from reportlab.lib.enums import TA_CENTER

        now = datetime.now()
        export_dir = os.path.join(os.getcwd(), 'exports_commandes')
        os.makedirs(export_dir, exist_ok=True)
        fname = os.path.join(
            export_dir,
            f"hotel_reservations_{now.strftime('%Y%m%d%H%M%S')}.pdf")

        # A4 paysage : marges 1.5 cm → largeur utile ≈ 29.7 − 3 = 26.7 cm
        PAGE = landscape(A4)
        LM = RM = 1.5 * cm
        TM = BM = 1.5 * cm
        avail_w = PAGE[0] - LM - RM   # points

        doc = SimpleDocTemplate(fname, pagesize=PAGE,
                                leftMargin=LM, rightMargin=RM,
                                topMargin=TM, bottomMargin=BM)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle('RptTitle', parent=styles['Title'],
                                  fontSize=13, alignment=1, spaceAfter=4))
        styles.add(ParagraphStyle('RptSub', parent=styles['Normal'],
                                  fontSize=8, alignment=1, spaceAfter=6))
        styles.add(ParagraphStyle('SmallInfo', parent=styles['Normal'],
                                  fontSize=7, textColor=HexColor('#555555')))
        els = []

        # ── En-tête entreprise ──────────────────────────────────────────────
        ci = get_hotel_company_info()
        sym = ci.get('currency_symbol', '$')
        avail_w_cm = (PAGE[0] - LM - RM) / cm
        logo_path = build_pdf_company_header(els, styles, ci, avail_w_cm)

        d_from_s = date_from.strftime('%d/%m/%Y') if hasattr(date_from, 'strftime') else str(date_from)
        d_to_s   = date_to.strftime('%d/%m/%Y')   if hasattr(date_to,   'strftime') else str(date_to)

        els.append(Paragraph("<b>RAPPORT RÉSERVATIONS HÔTEL</b>", styles['RptTitle']))
        els.append(Paragraph(
            f"Période : {d_from_s} – {d_to_s}  |  Statut : {status_lbl}  |  "
            f"Généré le : {now.strftime('%d/%m/%Y %H:%M')}",
            styles['RptSub']))
        els.append(Spacer(1, 0.3 * cm))

        # ── Tableau ─────────────────────────────────────────────────────────
        headers = ['Code', 'Client', 'Chambre',
                   'Entrée prévue', 'Sortie prévue', 'Nuitées',
                   'Entrée réelle', 'Sortie réelle', 'Jours réels',
                   'Total prévu', 'Montant réel', 'Payé', 'Solde', 'Statut']
        tbl_data = [headers]

        tot_brut = tot_reduc = tot_net = tot_paid = 0.0
        for r in rows:
            mr    = r.get('montant_reel', r.get('total', 0))
            solde = r.get('solde', mr - r.get('paid', 0))
            solde_s = (fmt_amount(abs(solde), sym)
                       if isinstance(solde, (int, float)) else '-')
            tbl_data.append([
                r['code'],
                (r['client_name'] or '')[:18],
                r['room'],
                fmt_date(r['date_entree_prevue']),
                fmt_date(r['date_sortie_prevue']),
                str(r.get('nuitees', '-')),
                fmt_datetime(r.get('date_entree_reelle')),
                fmt_datetime(r.get('date_sortie_reelle')),
                str(r.get('jours_reels', '-')),
                fmt_amount(r['total'], sym),
                fmt_amount(mr, sym) if isinstance(mr, (int, float)) else '-',
                fmt_amount(r['paid'], sym),
                solde_s,
                reservation_status_label(r['status']),
            ])
            tot_brut  += r.get('total', 0) + r.get('reduction', 0)
            tot_reduc += r.get('reduction', 0)
            tot_net   += r.get('total', 0)
            tot_paid  += r.get('paid', 0)

        tbl_data.append([
            f"TOTAL ({len(rows)})", '', '', '', '', '', '', '', '',
            fmt_amount(tot_net, sym), fmt_amount(tot_net, sym),
            fmt_amount(tot_paid, sym), '', '',
        ])

        # Colonnes réduites – largeur totale ≈ 24 cm, table centrée avec marges
        cws = [1.7*cm, 3.5*cm, 1.5*cm,
               2.0*cm, 2.0*cm, 1.2*cm,
               2.0*cm, 2.0*cm, 1.3*cm,
               2.4*cm, 2.4*cm, 2.4*cm, 2.0*cm, 1.6*cm]
        tbl = Table(tbl_data, colWidths=cws, repeatRows=1,
                    hAlign='CENTER')
        tbl.setStyle(TableStyle([
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
            ('ROWHEIGHT',      (0, 0),  (-1, -1), 0.5 * cm),
            ('PADDING',        (0, 0),  (-1, -1), 3),
        ]))
        els.append(tbl)
        els.append(Spacer(1, 0.4 * cm))

        # ── Résumé financier ─────────────────────────────────────────────────
        els.append(Paragraph("<b>Résumé financier</b>", styles['Heading3']))
        sum_data = [
            ["Total réservations",   str(len(rows))],
            ["Montant prévu (brut)", fmt_amount(tot_brut, sym)],
            ["Total réductions",     fmt_amount(tot_reduc, sym)],
            ["Net montant",          fmt_amount(tot_net, sym)],
            ["Total payé",           fmt_amount(tot_paid, sym)],
            ["Non payé (reste)",     fmt_amount(max(0.0, tot_net - tot_paid), sym)],
        ]
        sum_tbl = Table(sum_data, colWidths=[5.5 * cm, 6 * cm])
        sum_tbl.setStyle(TableStyle([
            ('GRID',       (0, 0), (-1, -1), 0.4, HexColor('#CCCCCC')),
            ('BACKGROUND', (0, 0), (0, -1),  HexColor('#ECF0F1')),
            ('FONTNAME',   (0, 0), (0, -1),  'Helvetica-Bold'),
            ('FONTSIZE',   (0, 0), (-1, -1), 9),
            ('PADDING',    (0, 0), (-1, -1), 5),
        ]))
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
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(parent, "Export PDF",
                                f"Fichier exporté :\n{fname}")
    except Exception as e:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(parent, "Export PDF", f"Erreur export : {e}")


COLUMNS = [
    'Code',           # 0
    'Client',         # 1
    'Chambre',        # 2
    'Entrée prévue',  # 3
    'Sortie prévue',  # 4
    'Nuitée',         # 5
    'Entrée réelle',  # 6
    'Sortie réelle',  # 7
    'Jours réels',    # 8
    'Total prévu',    # 9
    'Montant réel',   # 10
    'Payé',           # 11
    'Solde',          # 12
    'Statut',         # 13
]
_COLUMNS_LABELS = [c.split('#')[0].strip() for c in COLUMNS]


class ReservationView(QWidget):

    def __init__(self, current_user=None, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self._data: list = []
        _ci = get_hotel_company_info()
        self._sym = _ci.get('currency_symbol', '$')
        self._company_info = _ci
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

        # Dates — début et fin du mois en cours par défaut
        today        = QDate.currentDate()
        first_of_month = QDate(today.year(), today.month(), 1)
        last_of_month  = QDate(today.year(), today.month(), today.daysInMonth())

        self.date_from = QDateEdit(first_of_month)
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("dd/MM/yyyy")
        self.date_from.setToolTip("Filtrer par date de réservation (création)")
        self.date_from.dateChanged.connect(self.refresh)
        toolbar.addWidget(QLabel("Réservé du :"))
        toolbar.addWidget(self.date_from)

        self.date_to = QDateEdit(last_of_month)
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("dd/MM/yyyy")
        self.date_to.setToolTip("Filtrer par date de réservation (création)")
        self.date_to.dateChanged.connect(self.refresh)
        toolbar.addWidget(QLabel("au :"))
        toolbar.addWidget(self.date_to)

        btn_refresh = QPushButton("↻")
        btn_refresh.setFixedSize(34, 34)
        btn_refresh.setToolTip("Actualiser")
        btn_refresh.clicked.connect(self.refresh)
        toolbar.addWidget(btn_refresh)

        root.addLayout(toolbar)

        # ---- Actions ----
        actions = QHBoxLayout()
        self.btn_new    = self._btn("➕ Nouvelle réservation", "#27AE60")
        self.btn_export = self._btn("📄 Export PDF",  "#16A085")

        for btn in [self.btn_new, self.btn_export]:
            actions.addWidget(btn)
        actions.addStretch()
        root.addLayout(actions)

        self.btn_new.clicked.connect(self._on_new)
        self.btn_export.clicked.connect(self._on_export_pdf)

        # ---- Tableau ----
        self.table = QTableWidget()
        self.table.setColumnCount(len(COLUMNS))
        self.table.setHorizontalHeaderLabels(_COLUMNS_LABELS)
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
        self.table.cellDoubleClicked.connect(self._on_row_double_click)
        root.addWidget(self.table)

        # Barre de résumé financier
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

        self.lbl_count     = _slbl()
        self.lbl_brut      = _slbl()
        self.lbl_reduc     = _slbl()
        self.lbl_net       = _slbl()
        self.lbl_paid_sum  = _slbl()
        self.lbl_reste_sum = _slbl()
        for lb in [self.lbl_count, self.lbl_brut, self.lbl_reduc,
                   self.lbl_net, self.lbl_paid_sum, self.lbl_reste_sum]:
            _sl.addWidget(lb)
        _sl.addStretch()
        root.addWidget(self.summary_frame)

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
            # Nuitées prévues
            nuitees = row.get('nuitees', '-')
            nuitees_str = str(nuitees) if nuitees != '-' else '-'

            # Montant réel
            montant_reel = row.get('montant_reel', None)
            montant_reel_str = (
                fmt_amount(montant_reel, self._sym) if isinstance(montant_reel, (int, float))
                else '-')

            # Solde
            solde = row.get('solde', None)
            if isinstance(solde, (int, float)):
                solde_str = fmt_amount(abs(solde), self._sym)
            else:
                solde_str = '-'

            cells = [
                row['code'],           # 0
                row['client_name'],    # 1
                row['room'],           # 2
                fmt_date(row['date_entree_prevue']),  # 3
                fmt_date(row['date_sortie_prevue']),  # 4
                nuitees_str,           # 5
                fmt_datetime(row['date_entree_reelle']),  # 6
                fmt_datetime(row['date_sortie_reelle']),  # 7
                str(row.get('jours_reels', '-')),     # 8
                fmt_amount(row['total'], self._sym),   # 9
                montant_reel_str,              # 10
                fmt_amount(row['paid'], self._sym),    # 11
                solde_str,                     # 12
                reservation_status_label(row['status']),  # 13
            ]
            for col, val in enumerate(cells):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 0:  # store id in first column
                    item.setData(Qt.ItemDataRole.UserRole, row['id'])
                self.table.setItem(r, col, item)

            # Coloration statut (col 13)
            s_color = RESERVATION_STATUS_COLORS.get(row['status'], '#333')
            self.table.item(r, 13).setForeground(QBrush(QColor(s_color)))

            # Jours réels en bleu si en cours (col 8)
            if row['status'] == 'en_cours' and row.get('jours_reels', '-') != '-':
                jr_item = self.table.item(r, 8)
                if jr_item:
                    jr_item.setForeground(QBrush(QColor('#1976D2')))
                    jr_item.setFont(QFont('', -1, QFont.Weight.Bold))

            # Montant réel en bleu (col 10)
            mr_item = self.table.item(r, 10)
            if mr_item and montant_reel_str != '-':
                mr_item.setForeground(QBrush(QColor('#1976D2')))

            # Solde : rouge si positif, vert si négatif (col 12)
            solde_item = self.table.item(r, 12)
            if solde_item and isinstance(solde, (int, float)):
                if solde > 0:
                    solde_item.setForeground(QBrush(QColor('#E74C3C')))
                    solde_item.setFont(QFont('', -1, QFont.Weight.Bold))
                elif solde < 0:
                    solde_item.setForeground(QBrush(QColor('#27AE60')))
                else:
                    solde_item.setForeground(QBrush(QColor('#555')))

            if row['status'] == 'annulee':
                for c in range(len(COLUMNS)):
                    it = self.table.item(r, c)
                    if it:
                        it.setForeground(QBrush(QColor('#95A5A6')))

        # Totaux barre de résumé
        tot_brut  = sum(r.get('total', 0) + r.get('reduction', 0) for r in rows)
        tot_reduc = sum(r.get('reduction', 0) for r in rows)
        tot_net   = sum(r.get('total', 0) for r in rows)
        tot_paid  = sum(r.get('paid', 0) for r in rows)
        tot_reste = sum(r.get('reste', 0) for r in rows)
        self.lbl_count.setText(f"📋 {len(rows)} rés.")
        self.lbl_brut.setText(f"Brut : {fmt_amount(tot_brut, self._sym)}")
        self.lbl_reduc.setText(f"Réd. : {fmt_amount(tot_reduc, self._sym)}")
        self.lbl_net.setText(f"Net : {fmt_amount(tot_net, self._sym)}")
        self.lbl_paid_sum.setText(f"✅ Payé : {fmt_amount(tot_paid, self._sym)}")
        self.lbl_reste_sum.setText(f"❗ Reste : {fmt_amount(tot_reste, self._sym)}")

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
                reference=data.get('reference'),
                compte_id=data.get('compte_id'),
            )
            if ok:
                QMessageBox.information(self, "Succès", msg)
                self.refresh()
            else:
                QMessageBox.warning(self, "Erreur", msg)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def _on_pay(self):
        row = self._selected_row()
        if not row:
            return
        dlg = PaymentDialog(row, self)
        if dlg.exec() != PaymentDialog.DialogCode.Accepted:
            return
        ok, msg = _pay_svc.add_payment(
            row['id'], dlg.get_amount(), dlg.get_method(), self._uid(),
            reference=dlg.get_reference(), compte_id=dlg.get_compte_id())
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

    def _open_detail_dialog(self, row: dict):
        """Ouvre la fiche détaillée et exécute l'action choisie."""
        dlg = ReservationDetailDialog(row, self)
        result = dlg.exec()
        if result == ReservationDetailDialog.ACTION_CHECKOUT:
            ok, msg = _res_svc.checkout(row['id'], self._uid())
            if ok:
                QMessageBox.information(self, "Check-out", msg)
                self.refresh()
            else:
                mb = QMessageBox(self)
                mb.setIcon(QMessageBox.Icon.Critical)
                mb.setWindowTitle("Check-out impossible")
                mb.setText(msg)
                mb.setStandardButtons(QMessageBox.StandardButton.Ok)
                mb.exec()
        elif result == ReservationDetailDialog.ACTION_EXTEND:
            ext_dlg = ExtendDialog(row, self)
            if ext_dlg.exec() == ExtendDialog.DialogCode.Accepted:
                ok, msg = _res_svc.extend_stay(
                    row['id'], ext_dlg.get_new_date(), self._uid())
                if ok:
                    QMessageBox.information(self, "Prolongation", msg)
                    self.refresh()
                else:
                    QMessageBox.warning(self, "Erreur prolongation", msg)
        elif result == ReservationDetailDialog.ACTION_CANCEL:
            ok, msg = _res_svc.cancel_reservation(row['id'], self._uid())
            if ok:
                QMessageBox.information(self, "Annulée", msg)
                self.refresh()
            else:
                QMessageBox.warning(self, "Erreur", msg)

    def _on_row_double_click(self, row_idx, _col):
        item = self.table.item(row_idx, 0)
        if not item:
            return
        res_id = item.data(Qt.ItemDataRole.UserRole)
        for r in self._data:
            if r['id'] == res_id:
                self._open_detail_dialog(r)
                return

    def _on_checkout(self):
        row = self._selected_row()
        if not row:
            return
        if row['status'] != 'en_cours':
            QMessageBox.warning(self, "Check-out impossible",
                                "Seule une réservation 'En cours' peut être check-outée.")
            return
        self._open_detail_dialog(row)

    def _on_cancel(self):
        row = self._selected_row()
        if not row:
            return
        if row['status'] != 'en_attente':
            QMessageBox.warning(
                self, "Annulation impossible",
                f"Seule une réservation 'En attente' peut être annulée.\n"
                f"Statut actuel : {reservation_status_label(row['status'])}.")
            return
        reply = QMessageBox.question(
            self, "Annulation",
            f"Annuler la réservation {row['code']} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        ok, msg = _res_svc.cancel_reservation(row['id'], self._uid())
        if ok:
            QMessageBox.information(self, "Annulée", msg)
            self.refresh()
        else:
            QMessageBox.warning(self, "Erreur", msg)

    def _on_export_pdf(self):
        """Exporte les réservations affichées (après tous les filtres) en PDF A4."""
        # Appliquer recherche texte + filtre statut sur self._data
        s      = self.search_input.text().strip().lower()
        status = self.status_filter.currentData()
        rows   = self._data
        if status:
            rows = [r for r in rows if r['status'] == status]
        if s:
            rows = [r for r in rows
                    if s in r['code'].lower()
                    or s in r['client_name'].lower()
                    or s in r['room'].lower()]
        if not rows:
            QMessageBox.information(self, "Export PDF",
                                    "Aucune réservation à exporter.")
            return
        _export_reservations_pdf(
            rows,
            self.date_from.date().toPyDate(),
            self.date_to.date().toPyDate(),
            self.status_filter.currentText(),
            self,
        )

    def _on_print(self):
        row = self._selected_row()
        if not row:
            return
        self._print_reservation(row)

    def _print_reservation(self, row: dict):
        """Génère et ouvre un PDF pour la réservation dans le format choisi."""
        fmt_dlg = _PrintFormatDialog(self)
        if fmt_dlg.exec() != QDialog.DialogCode.Accepted:
            return
        _print_checkout_pdf(row, fmt_dlg.get_format(), self)

    def _uid(self):
        if self.current_user is None:
            return 1
        if isinstance(self.current_user, dict):
            return self.current_user.get('id', 1)
        return getattr(self.current_user, 'id', 1)
