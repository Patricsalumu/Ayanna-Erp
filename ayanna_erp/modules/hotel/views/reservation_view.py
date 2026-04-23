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
    fmt_date, reservation_status_label, payment_status_label,
    RESERVATION_STATUS_COLORS, PAYMENT_STATUS_COLORS
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

        # ── Section réservation ──────────────────────────────────────────────
        section("  Informations de réservation")
        row_info("Code réservation :",   r['code'])
        row_info("Client :",              r['client_name'], bold=True)
        row_info("Catégorie :",           r['category'])
        row_info("Chambre :",             r['room'])
        row_info("Créé par :",
                 r.get('created_by_name') or '-', '#8E44AD')
        row_info("Date de réservation :", _fmt_dt(r.get('created_at')))
        vbox.addSpacing(4)

        # ── Section dates ────────────────────────────────────────────────────
        section("  Dates")
        row_info("Entrée prévue :",    fmt_date(r['date_entree_prevue']))
        row_info("Sortie prévue :",    fmt_date(r['date_sortie_prevue']))
        row_info("Nuitées prévues :",  str(nuitees))
        row_info("Entrée réelle :",
                 fmt_date(r.get('date_entree_reelle')), '#27AE60')
        if status == 'en_cours':
            row_info("Check-out (maintenant) :",
                     now.strftime('%d/%m/%Y %H:%M'), '#E74C3C', bold=True)
        elif r.get('date_sortie_reelle'):
            row_info("Sortie réelle :",
                     fmt_date(r['date_sortie_reelle']), '#E74C3C')
        vbox.addSpacing(4)

        # ── Section financière ───────────────────────────────────────────────
        section("  Récapitulatif financier")
        if status == 'en_cours':
            row_info("Jours réels passés :",
                     str(jr) if jr != '-' else 'N/A', '#1976D2', bold=True)
        row_info("Prix / nuit :",         f"{price:,.0f}")
        row_info("Réduction :",           f"{reduction:,.0f}")
        row_info("Montant réel à payer :",
                 f"{montant_reel:,.0f}", '#1976D2', bold=True)
        row_info("Déjà payé :",           f"{paid:,.0f}", '#27AE60')

        if isinstance(solde, (int, float)):
            if solde > 0:
                row_info("Reste à payer :", f"+{solde:,.0f}", '#E74C3C', bold=True)
            elif solde < 0:
                row_info("Crédit (trop payé) :", f"{abs(solde):,.0f}", '#27AE60', bold=True)
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
                amt_str = f"{p['amount']:,.0f}" if isinstance(
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
            self._get_uid())
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
        import os, subprocess, sys
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm, cm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle)
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.colors import HexColor, black
        from reportlab.lib.enums import TA_CENTER

        now = datetime.now()
        r = row
        jr = r.get('jours_reels', '-')
        montant_reel = r.get('montant_reel', r.get('total', 0))
        paid = r.get('paid', 0)
        solde = r.get('solde', montant_reel - paid)
        if isinstance(solde, (int, float)) and solde > 0:
            solde_str = f"Reste à payer : {solde:,.0f}"
        elif isinstance(solde, (int, float)) and solde < 0:
            solde_str = f"Crédit : {abs(solde):,.0f}"
        else:
            solde_str = "Soldé"

        export_dir = os.path.join(os.getcwd(), 'exports_commandes')
        os.makedirs(export_dir, exist_ok=True)
        suffix = 'a4' if fmt == 'a4' else '80mm'
        fname = os.path.join(
            export_dir,
            f"checkout_{r['code']}_{now.strftime('%Y%m%d%H%M%S')}_{suffix}.pdf")

        styles = getSampleStyleSheet()

        if fmt == 'a4':
            doc = SimpleDocTemplate(fname, pagesize=A4,
                                    leftMargin=2*cm, rightMargin=2*cm,
                                    topMargin=2*cm, bottomMargin=2*cm)
            els = []
            els.append(Paragraph("<b>FICHE DE CHECK-OUT – HÔTEL</b>",
                                  styles['Title']))
            els.append(Spacer(1, 0.4*cm))

            def _h3(t): return Paragraph(f"<b>{t}</b>", styles['Heading3'])

            els.append(_h3("Informations de réservation"))
            els.append(_pdf_table([
                ["Code réservation",  r['code']],
                ["Client",             r['client_name']],
                ["Catégorie",          r['category']],
                ["Chambre",            r['room']],
            ]))
            els.append(Spacer(1, 0.3*cm))

            els.append(_h3("Dates"))
            els.append(_pdf_table([
                ["Entrée prévue",    fmt_date(r['date_entree_prevue'])],
                ["Sortie prévue",    fmt_date(r['date_sortie_prevue'])],
                ["Nuitées prévues", str(r.get('nuitees', '-'))],
                ["Entrée réelle",    fmt_date(r.get('date_entree_reelle'))],
                ["Check-out",          now.strftime('%d/%m/%Y %H:%M')],
            ]))
            els.append(Spacer(1, 0.3*cm))

            els.append(_h3("Récapitulatif financier"))
            els.append(_pdf_table([
                ["Jours réels passés",   str(jr)],
                ["Prix / nuit",            f"{r.get('price_per_night', 0):,.0f}"],
                ["Réduction",             f"{r.get('reduction', 0):,.0f}"],
                ["Montant réel à payer",  f"{montant_reel:,.0f}"],
                ["Déjà payé",            f"{paid:,.0f}"],
                ["Solde",                  solde_str],
            ]))
            els.append(Spacer(1, 1*cm))
            els.append(Paragraph("<i>Merci pour votre séjour.</i>",
                                  styles['Italic']))
            doc.build(els)

        else:  # 80 mm ticket
            W = 80 * mm
            M = 4 * mm
            cw = W - 2 * M
            doc = SimpleDocTemplate(fname, pagesize=(W, 400 * mm),
                                    leftMargin=M, rightMargin=M,
                                    topMargin=M, bottomMargin=M)
            c_style = ParagraphStyle('c', parent=styles['Normal'],
                                     alignment=TA_CENTER, fontSize=9)
            bc_style = ParagraphStyle('bc', parent=styles['Normal'],
                                      alignment=TA_CENTER, fontSize=11,
                                      fontName='Helvetica-Bold')
            n_style = ParagraphStyle('n', parent=styles['Normal'], fontSize=8)

            def _row80(lbl, val):
                t = Table([[lbl, val]], colWidths=[cw * 0.48, cw * 0.52])
                t.setStyle(TableStyle([
                    ('FONTSIZE',  (0, 0), (-1, -1), 8),
                    ('FONTNAME',  (0, 0), (0, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                    ('TOPPADDING',    (0, 0), (-1, -1), 2),
                ]))
                return t

            sep = Paragraph("-" * 44, n_style)
            els = []
            els.append(Paragraph("<b>HÔTEL</b>", bc_style))
            els.append(Paragraph("FICHE DE CHECK-OUT", c_style))
            els.append(Spacer(1, 2 * mm))
            els.append(sep)
            for lbl, val in [
                ("Code :",       r['code']),
                ("Client :",     r['client_name']),
                ("Catégorie :",  r['category']),
                ("Chambre :",    r['room']),
            ]:
                els.append(_row80(lbl, val))
            els.append(Spacer(1, 1 * mm))
            els.append(sep)
            for lbl, val in [
                ("Entrée prévue :",  fmt_date(r['date_entree_prevue'])),
                ("Sortie prévue :",  fmt_date(r['date_sortie_prevue'])),
                ("Nuitées :",         str(r.get('nuitees', '-'))),
                ("Entrée réelle :",  fmt_date(r.get('date_entree_reelle'))),
                ("Check-out :",       now.strftime('%d/%m/%Y %H:%M')),
            ]:
                els.append(_row80(lbl, val))
            els.append(Spacer(1, 1 * mm))
            els.append(sep)
            for lbl, val in [
                ("Jours réels :",    str(jr)),
                ("Prix/nuit :",       f"{r.get('price_per_night', 0):,.0f}"),
                ("Réduction :",       f"{r.get('reduction', 0):,.0f}"),
                ("Montant réel :",    f"{montant_reel:,.0f}"),
                ("Déjà payé :",      f"{paid:,.0f}"),
                ("Solde :",           solde_str),
            ]:
                els.append(_row80(lbl, val))
            els.append(Spacer(1, 3 * mm))
            els.append(sep)
            els.append(Paragraph("Merci pour votre séjour !", c_style))
            els.append(Spacer(1, 6 * mm))
            doc.build(els)

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
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.colors import HexColor

        now = datetime.now()
        export_dir = os.path.join(os.getcwd(), 'exports_commandes')
        os.makedirs(export_dir, exist_ok=True)
        fname = os.path.join(
            export_dir,
            f"hotel_reservations_{now.strftime('%Y%m%d%H%M%S')}.pdf")

        doc = SimpleDocTemplate(fname, pagesize=landscape(A4),
                                leftMargin=1.5*cm, rightMargin=1.5*cm,
                                topMargin=1.5*cm, bottomMargin=1.5*cm)
        styles = getSampleStyleSheet()
        els = []

        d_from_s = date_from.strftime('%d/%m/%Y') if hasattr(date_from, 'strftime') else str(date_from)
        d_to_s   = date_to.strftime('%d/%m/%Y')   if hasattr(date_to,   'strftime') else str(date_to)

        els.append(Paragraph("<b>RAPPORT RÉSERVATIONS HÔTEL</b>",
                              styles['Title']))
        els.append(Paragraph(
            f"Période : {d_from_s} – {d_to_s}  |  Statut : {status_lbl}  |  "
            f"Généré le : {now.strftime('%d/%m/%Y %H:%M')}",
            styles['Normal']))
        els.append(Spacer(1, 0.4*cm))

        # --- Tableau ---
        headers = ['Code', 'Client', 'Catégorie', 'Chambre',
                   'Entrée prévue', 'Sortie prévue', 'Nuitées',
                   'Statut', 'Total prévu', 'Montant réel', 'Payé', 'Reste', 'Solde']
        tbl_data = [headers]

        tot_brut = tot_reduc = tot_net = tot_paid = tot_reste = 0.0
        for r in rows:
            mr = r.get('montant_reel', r.get('total', 0))
            solde = r.get('solde', mr - r.get('paid', 0))
            solde_s = (f"+{solde:,.0f}" if isinstance(solde, (int, float)) and solde > 0
                       else f"{solde:,.0f}" if isinstance(solde, (int, float))
                       else '-')
            tbl_data.append([
                r['code'],
                (r['client_name'] or '')[:22],
                (r['category']    or '')[:16],
                r['room'],
                fmt_date(r['date_entree_prevue']),
                fmt_date(r['date_sortie_prevue']),
                str(r.get('nuitees', '-')),
                reservation_status_label(r['status']),
                f"{r['total']:,.0f}",
                f"{mr:,.0f}" if isinstance(mr, (int, float)) else '-',
                f"{r['paid']:,.0f}",
                f"{r['reste']:,.0f}",
                solde_s,
            ])
            tot_brut  += r.get('total', 0) + r.get('reduction', 0)
            tot_reduc += r.get('reduction', 0)
            tot_net   += r.get('total', 0)
            tot_paid  += r.get('paid', 0)
            tot_reste += r.get('reste', 0)

        # Ligne totaux
        tbl_data.append([
            f"TOTAL ({len(rows)})", '', '', '', '', '', '', '',
            f"{tot_net:,.0f}", f"{tot_net:,.0f}",
            f"{tot_paid:,.0f}", f"{tot_reste:,.0f}", '',
        ])

        cws = [2.2*cm, 4.2*cm, 3*cm, 1.8*cm,
               2.4*cm, 2.4*cm, 1.5*cm,
               2.2*cm, 2.6*cm, 2.6*cm, 2.6*cm, 2.4*cm, 2.4*cm]
        tbl = Table(tbl_data, colWidths=cws, repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0),  HexColor('#34495E')),
            ('TEXTCOLOR',     (0, 0), (-1, 0),  HexColor('#FFFFFF')),
            ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, -1), 7),
            ('GRID',          (0, 0), (-1, -1), 0.3, HexColor('#CCCCCC')),
            ('ROWBACKGROUNDS',(1, 1), (-2, -1),
             [HexColor('#FFFFFF'), HexColor('#F5F6FA')]),
            ('BACKGROUND',    (0, -1), (-1, -1), HexColor('#2C3E50')),
            ('TEXTCOLOR',     (0, -1), (-1, -1), HexColor('#FFFFFF')),
            ('FONTNAME',      (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWHEIGHT',     (0, 0), (-1, -1), 0.5*cm),
            ('PADDING',       (0, 0), (-1, -1), 3),
        ]))
        els.append(tbl)
        els.append(Spacer(1, 0.5*cm))

        # --- Résumé financier ---
        els.append(Paragraph("<b>Résumé financier</b>", styles['Heading3']))
        sum_data = [
            ["Total réservations",    str(len(rows))],
            ["Montant prévu (brut)",  f"{tot_brut:,.0f}"],
            ["Total réductions",      f"{tot_reduc:,.0f}"],
            ["Net montant",            f"{tot_net:,.0f}"],
            ["Total payé",            f"{tot_paid:,.0f}"],
            ["Non payé (reste)",      f"{tot_reste:,.0f}"],
        ]
        sum_tbl = Table(sum_data, colWidths=[5.5*cm, 5*cm])
        sum_tbl.setStyle(TableStyle([
            ('GRID',       (0, 0), (-1, -1), 0.4, HexColor('#CCCCCC')),
            ('BACKGROUND', (0, 0), (0, -1),  HexColor('#ECF0F1')),
            ('FONTNAME',   (0, 0), (0, -1),  'Helvetica-Bold'),
            ('FONTSIZE',   (0, 0), (-1, -1), 9),
            ('PADDING',    (0, 0), (-1, -1), 5),
        ]))
        els.append(sum_tbl)

        doc.build(els)
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
    'Catégorie',      # 2
    'Chambre',        # 3
    'Entrée prévue',  # 4
    'Sortie prévue',  # 5
    'Nuitée',         # 6
    'Entrée réelle',  # 7
    'Sortie réelle',  # 8
    'Jours réels',    # 9
    'Statut',         # 10
    'Paiement',       # 11
    'Total prévu',    # 12
    'Montant réel',   # 13
    'Payé',           # 14
    'Reste',          # 15
    'Solde',          # 16
]
_COLUMNS_LABELS = [c.split('#')[0].strip() for c in COLUMNS]


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

        # Dates — début et fin du mois en cours par défaut
        today        = QDate.currentDate()
        first_of_month = QDate(today.year(), today.month(), 1)
        last_of_month  = QDate(today.year(), today.month(), today.daysInMonth())

        self.date_from = QDateEdit(first_of_month)
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("dd/MM/yyyy")
        self.date_from.dateChanged.connect(self.refresh)
        toolbar.addWidget(QLabel("Du :"))
        toolbar.addWidget(self.date_from)

        self.date_to = QDateEdit(last_of_month)
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
                f"{montant_reel:,.0f}" if isinstance(montant_reel, (int, float))
                else '-')

            # Solde
            solde = row.get('solde', None)
            if isinstance(solde, (int, float)):
                solde_str = (f"+{solde:,.0f}" if solde > 0
                             else f"{solde:,.0f}")
            else:
                solde_str = '-'

            cells = [
                row['code'],           # 0
                row['client_name'],    # 1
                row['category'],       # 2
                row['room'],           # 3
                fmt_date(row['date_entree_prevue']),  # 4
                fmt_date(row['date_sortie_prevue']),  # 5
                nuitees_str,           # 6
                fmt_date(row['date_entree_reelle']),  # 7
                fmt_date(row['date_sortie_reelle']),  # 8
                str(row.get('jours_reels', '-')),     # 9
                reservation_status_label(row['status']),       # 10
                payment_status_label(row['statut_paiement']),  # 11
                f"{row['total']:,.0f}",        # 12
                montant_reel_str,              # 13
                f"{row['paid']:,.0f}",         # 14
                f"{row['reste']:,.0f}",        # 15
                solde_str,                     # 16
            ]
            for col, val in enumerate(cells):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 0:  # store id in first column
                    item.setData(Qt.ItemDataRole.UserRole, row['id'])
                self.table.setItem(r, col, item)

            # Coloration statut (col 10) et paiement (col 11)
            s_color = RESERVATION_STATUS_COLORS.get(row['status'], '#333')
            p_color = PAYMENT_STATUS_COLORS.get(row['statut_paiement'], '#333')
            self.table.item(r, 10).setForeground(QBrush(QColor(s_color)))
            self.table.item(r, 11).setForeground(QBrush(QColor(p_color)))

            # Jours réels en bleu si en cours (col 9)
            if row['status'] == 'en_cours' and row.get('jours_reels', '-') != '-':
                jr_item = self.table.item(r, 9)
                if jr_item:
                    jr_item.setForeground(QBrush(QColor('#1976D2')))
                    jr_item.setFont(QFont('', -1, QFont.Weight.Bold))

            # Montant réel en bleu (col 13)
            mr_item = self.table.item(r, 13)
            if mr_item and montant_reel_str != '-':
                mr_item.setForeground(QBrush(QColor('#1976D2')))

            # Solde : rouge si positif (doit encore payer), vert si négatif (crédit)
            solde_item = self.table.item(r, 16)
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
        self.lbl_brut.setText(f"Brut : {tot_brut:,.0f}")
        self.lbl_reduc.setText(f"Réd. : {tot_reduc:,.0f}")
        self.lbl_net.setText(f"Net : {tot_net:,.0f}")
        self.lbl_paid_sum.setText(f"✅ Payé : {tot_paid:,.0f}")
        self.lbl_reste_sum.setText(f"❗ Reste : {tot_reste:,.0f}")

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
                QMessageBox.warning(self, "Check-out impossible", msg)
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
            ok, msg = _res_svc.cancel_reservation(row['id'])
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
        ok, msg = _res_svc.cancel_reservation(row['id'])
        if ok:
            QMessageBox.information(self, "Annulée", msg)
            self.refresh()
        else:
            QMessageBox.warning(self, "Erreur", msg)

    def _on_export_pdf(self):
        """Exporte les réservations affichées (après filtres) en PDF A4."""
        s = self.search_input.text().strip().lower()
        if s:
            rows = [r for r in self._data
                    if s in r['code'].lower()
                    or s in r['client_name'].lower()
                    or s in r['room'].lower()]
        else:
            rows = self._data
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
