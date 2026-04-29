"""
BalanceWidget - Onglet Balance de Vérification (SYSCOHADA)

Affiche la balance de vérification :
- Tous les comptes ayant des mouvements (solde non nul)
- Colonnes : Numéro | Libellé | Mouvements Débit | Mouvements Crédit | Solde Débiteur | Solde Créditeur
- Total Mouvements Débit = Total Mouvements Crédit (double-entrée garantie)
- Total Solde Débiteur = Total Solde Créditeur
- Filtrage par période (date début / date fin)
- Export PDF
"""

import unicodedata

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton,
    QLabel, QFrame, QLineEdit, QDateEdit, QMessageBox, QHeaderView
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor, QFont
from PyQt6.QtCore import Qt, QDate


class BalanceWidget(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.session = getattr(controller, 'session', None)
        self.entreprise_id = getattr(parent, 'entreprise_id', None) if parent is not None else None

        # Devise
        self.devise = ""
        if parent and hasattr(parent, 'get_currency_symbol'):
            try:
                self.devise = parent.get_currency_symbol()
            except Exception:
                self.devise = ""

        self._build_ui()
        self.load_data()

    # ------------------------------------------------------------------
    # Construction de l'interface
    # ------------------------------------------------------------------

    def _build_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 12, 12, 12)

        # ---- En-tête ----
        header = QFrame()
        header.setStyleSheet(
            "QFrame { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, "
            "stop:0 #2C3E50, stop:1 #34495E); border-radius:8px; padding:6px }"
            "QLabel { color: white; font-weight: bold }"
        )
        h_layout = QHBoxLayout(header)
        title = QLabel("⚖️ Balance de Vérification")
        title.setStyleSheet("font-size:16px")
        h_layout.addWidget(title)
        h_layout.addStretch()
        self.layout.addWidget(header)

        # ---- Filtres ----
        filter_frame = QFrame()
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(0, 6, 0, 6)

        filter_layout.addWidget(QLabel("Du :"))
        self.date_debut = QDateEdit()
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDisplayFormat("dd/MM/yyyy")
        self.date_debut.setDate(QDate(QDate.currentDate().year(), 1, 1))
        filter_layout.addWidget(self.date_debut)

        filter_layout.addWidget(QLabel("Au :"))
        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDisplayFormat("dd/MM/yyyy")
        self.date_fin.setDate(QDate.currentDate())
        filter_layout.addWidget(self.date_fin)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher numéro, libellé…")
        self.search_input.textChanged.connect(self.load_data)
        filter_layout.addWidget(self.search_input, 1)

        refresh_btn = QPushButton("🔄 Rafraîchir")
        refresh_btn.setStyleSheet(
            "background-color:#2C3E50; color:white; padding:6px 12px; border-radius:6px;"
        )
        refresh_btn.clicked.connect(self.load_data)

        export_btn = QPushButton("📤 Exporter PDF")
        export_btn.setStyleSheet(
            "background-color:#4CAF50; color:white; padding:6px 12px; border-radius:6px;"
        )
        export_btn.clicked.connect(self.export_pdf)

        filter_layout.addWidget(refresh_btn)
        filter_layout.addWidget(export_btn)
        self.layout.addWidget(filter_frame)

        # ---- Tableau ----
        table_frame = QFrame()
        table_frame.setStyleSheet("QFrame { background: white; border-radius:6px; padding:4px }")
        table_layout = QVBoxLayout(table_frame)

        self.table = QTableView()
        self.model = QStandardItemModel()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QHeaderView::section {
                background-color: #2C3E50;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                padding: 8px 4px;
            }
            QTableView::item:alternate {
                background-color: #f5f5f5;
            }
            QTableView::item:selected {
                background-color: #d0e8f5;
                color: #2C3E50;
            }
        """)
        table_layout.addWidget(self.table)
        self.layout.addWidget(table_frame)

        # ---- Totaux ----
        totals_frame = QFrame()
        totals_frame.setStyleSheet(
            "QFrame { background: #ECF0F1; border-radius:6px; padding:6px }"
            "QLabel { font-weight: bold; font-size: 13px; color: #2C3E50 }"
        )
        totals_layout = QHBoxLayout(totals_frame)
        totals_layout.setContentsMargins(12, 6, 12, 6)
        totals_layout.addStretch()

        self.lbl_total_mvt_debit = QLabel("Mvt Débit : 0,00")
        self.lbl_total_mvt_credit = QLabel("Mvt Crédit : 0,00")
        self.lbl_total_solde_debiteur = QLabel("Solde Débiteur : 0,00")
        self.lbl_total_solde_crediteur = QLabel("Solde Créditeur : 0,00")

        sep = lambda: self._make_separator()
        totals_layout.addWidget(self.lbl_total_mvt_debit)
        totals_layout.addWidget(sep())
        totals_layout.addWidget(self.lbl_total_mvt_credit)
        totals_layout.addWidget(sep())
        totals_layout.addWidget(self.lbl_total_solde_debiteur)
        totals_layout.addWidget(sep())
        totals_layout.addWidget(self.lbl_total_solde_crediteur)
        totals_layout.addStretch()
        self.layout.addWidget(totals_frame)

        # Date filters trigger reload on change
        self.date_debut.dateChanged.connect(self.load_data)
        self.date_fin.dateChanged.connect(self.load_data)

    def _make_separator(self):
        sep = QLabel("|")
        sep.setStyleSheet("color: #BDC3C7; font-size:16px")
        return sep

    # ------------------------------------------------------------------
    # Chargement des données
    # ------------------------------------------------------------------

    def load_data(self):
        if not self.entreprise_id:
            return

        date_debut = self.date_debut.date().toPyDate()
        date_fin = self.date_fin.date().toPyDate()
        data = self.controller.get_balance(self.entreprise_id, date_debut, date_fin)

        search_text = self._normalize(self.search_input.text())

        headers = [
            "Numéro", "Libellé",
            "Mvt Débit", "Mvt Crédit",
            "Solde Débiteur", "Solde Créditeur"
        ]
        self.model.clear()
        self.model.setHorizontalHeaderLabels(headers)

        total_mvt_debit = 0.0
        total_mvt_credit = 0.0
        total_solde_debiteur = 0.0
        total_solde_crediteur = 0.0

        for row in data:
            if search_text:
                pool = self._normalize(f"{row.get('numero','')} {row.get('nom','')}")
                if search_text not in pool:
                    continue

            td = float(row.get("total_debit", 0) or 0)
            tc = float(row.get("total_credit", 0) or 0)
            sd = float(row.get("solde_debiteur", 0) or 0)
            sc = float(row.get("solde_crediteur", 0) or 0)

            total_mvt_debit += td
            total_mvt_credit += tc
            total_solde_debiteur += sd
            total_solde_crediteur += sc

            items = [
                self._item(str(row.get("numero", ""))),
                self._item(str(row.get("nom", ""))),
                self._amount_item(td),
                self._amount_item(tc),
                self._amount_item(sd, color="#1565C0" if sd > 0 else None),
                self._amount_item(sc, color="#B71C1C" if sc > 0 else None),
            ]
            self.model.appendRow(items)

        # Ligne de total
        self._append_total_row(total_mvt_debit, total_mvt_credit, total_solde_debiteur, total_solde_crediteur)
        self._apply_column_layout()
        self._update_totals_bar(total_mvt_debit, total_mvt_credit, total_solde_debiteur, total_solde_crediteur)

    def _append_total_row(self, td, tc, sd, sc):
        bold_font = QFont()
        bold_font.setBold(True)
        bg = QColor("#D5D8DC")

        items = [
            self._item("TOTAL"),
            self._item(""),
            self._amount_item(td),
            self._amount_item(tc),
            self._amount_item(sd),
            self._amount_item(sc),
        ]
        for item in items:
            item.setFont(bold_font)
            item.setBackground(bg)
        self.model.appendRow(items)

    def _update_totals_bar(self, td, tc, sd, sc):
        self.lbl_total_mvt_debit.setText(f"Mvt Débit : {self._fmt(td)}")
        self.lbl_total_mvt_credit.setText(f"Mvt Crédit : {self._fmt(tc)}")
        self.lbl_total_solde_debiteur.setText(f"Solde Débiteur : {self._fmt(sd)}")
        self.lbl_total_solde_crediteur.setText(f"Solde Créditeur : {self._fmt(sc)}")

    def _apply_column_layout(self):
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col in range(2, 6):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            self.table.setColumnWidth(col, 150)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _item(self, value):
        item = QStandardItem(value)
        item.setEditable(False)
        return item

    def _amount_item(self, value, color=None):
        item = QStandardItem(self._fmt(value) if value != 0 else "")
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        item.setEditable(False)
        if color:
            item.setForeground(QColor(color))
        return item

    def _fmt(self, value):
        try:
            if hasattr(self, 'controller') and self.controller:
                return self.controller.format_amount(float(value))
        except Exception:
            pass
        devise = self.devise or ""
        return f"{float(value):,.2f} {devise}".strip()

    def _normalize(self, text):
        nfkd = unicodedata.normalize("NFKD", str(text or ""))
        return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()

    # ------------------------------------------------------------------
    # Export PDF
    # ------------------------------------------------------------------

    def export_pdf(self):
        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.units import cm
            from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from PyQt6.QtWidgets import QFileDialog
            import datetime
        except ImportError:
            QMessageBox.warning(
                self, "ReportLab manquant",
                "Veuillez installer reportlab : pip install reportlab"
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter la Balance en PDF", "balance_verification.pdf",
            "Fichiers PDF (*.pdf)"
        )
        if not path:
            return

        date_debut = self.date_debut.date().toPyDate()
        date_fin = self.date_fin.date().toPyDate()
        data = self.controller.get_balance(self.entreprise_id, date_debut, date_fin)

        doc = SimpleDocTemplate(
            path, pagesize=landscape(A4),
            rightMargin=1.5 * cm, leftMargin=1.5 * cm,
            topMargin=2 * cm, bottomMargin=2 * cm
        )
        elements = []
        styles = getSampleStyleSheet()

        # En-tête entreprise
        try:
            from ayanna_erp.modules.comptabilite.utils.pdf_export import prepare_header_elements, format_amount
            header_elems = prepare_header_elements(
                self.controller, self.entreprise_id,
                title="BALANCE DE VÉRIFICATION"
            )
            elements.extend(header_elems)
        except Exception:
            titre_style = ParagraphStyle(
                'Titre', parent=styles['Heading2'],
                alignment=1, fontSize=15, spaceAfter=10
            )
            elements.append(Paragraph("BALANCE DE VÉRIFICATION", titre_style))

        # Sous-titre période
        periode_style = ParagraphStyle(
            'Periode', parent=styles['Normal'],
            alignment=1, fontSize=10, spaceAfter=6,
            textColor=colors.HexColor('#555555')
        )
        elements.append(Paragraph(
            f"Période du {date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')}",
            periode_style
        ))
        elements.append(Spacer(1, 0.3 * cm))

        # Données tableau
        col_headers = [
            "Numéro", "Libellé",
            "Mvt Débit", "Mvt Crédit",
            "Solde Débiteur", "Solde Créditeur"
        ]
        table_data = [col_headers]

        total_mvt_debit = 0.0
        total_mvt_credit = 0.0
        total_solde_debiteur = 0.0
        total_solde_crediteur = 0.0

        try:
            _fmt = lambda v: format_amount(v, self.controller)
        except Exception:
            _fmt = lambda v: f"{float(v):,.2f}"

        for row in data:
            td = float(row.get("total_debit", 0) or 0)
            tc = float(row.get("total_credit", 0) or 0)
            sd = float(row.get("solde_debiteur", 0) or 0)
            sc = float(row.get("solde_crediteur", 0) or 0)
            total_mvt_debit += td
            total_mvt_credit += tc
            total_solde_debiteur += sd
            total_solde_crediteur += sc
            table_data.append([
                str(row.get("numero", "")),
                str(row.get("nom", "")),
                _fmt(td) if td != 0 else "",
                _fmt(tc) if tc != 0 else "",
                _fmt(sd) if sd != 0 else "",
                _fmt(sc) if sc != 0 else "",
            ])

        # Ligne totaux
        table_data.append([
            "TOTAL", "",
            _fmt(total_mvt_debit),
            _fmt(total_mvt_credit),
            _fmt(total_solde_debiteur),
            _fmt(total_solde_crediteur),
        ])

        col_widths = [2.5 * cm, 8.5 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm]
        pdf_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        n = len(table_data)
        pdf_table.setStyle(TableStyle([
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            # Corps
            ('FONTSIZE', (0, 1), (-1, -2), 9),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#AAAAAA')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F2F3F4')]),
            # Ligne totaux
            ('BACKGROUND', (0, n - 1), (-1, n - 1), colors.HexColor('#D5D8DC')),
            ('FONTNAME', (0, n - 1), (-1, n - 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, n - 1), (-1, n - 1), 9),
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(pdf_table)

        try:
            doc.build(elements)
            QMessageBox.information(
                self, "Export PDF réussi",
                f"La Balance de Vérification a été exportée :\n{path}"
            )
        except Exception as e:
            QMessageBox.warning(
                self, "Erreur export PDF",
                f"Une erreur est survenue lors de l'export :\n{e}"
            )
