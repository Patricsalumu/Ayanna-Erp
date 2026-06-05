"""GrandLivreWidget - Onglet Grand Livre Comptable

Affiche la liste des comptes avec les totaux débit, crédit et le solde.
Double-clic sur une ligne : ouvre le détail des écritures du compte.
"""
import unicodedata

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableView, QPushButton, QHBoxLayout, QDialog, QLabel, QFrame, QLineEdit, QDateEdit
from PyQt6.QtGui import QStandardItemModel, QColor
from PyQt6.QtCore import Qt, QDate
class GrandLivreWidget(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.session = getattr(controller, 'session', None)
        self.entreprise_id = getattr(parent, 'entreprise_id', None) if parent is not None else None
        # Pré-charger la devise de l'entreprise via le parent
        self.devise = ""
        if parent and hasattr(parent, 'get_currency_symbol'):
            try:
                self.devise = parent.get_currency_symbol()
            except Exception as e:
                print(f"[DEBUG] GrandLivreWidget: Erreur lors de l'obtention de la devise: {e}")
                self.devise = "€"  # Fallback
        else:
            print(f"[DEBUG] GrandLivreWidget: parent sans get_currency_symbol(), devise par défaut")
            self.devise = "€"  # Fallback
        try:
            # Main layout
            self.layout = QVBoxLayout(self)
            self.layout.setContentsMargins(12, 12, 12, 12)

            # Header card
            header = QFrame()
            header.setStyleSheet('''
                QFrame { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #8E44AD, stop:1 #8E44AD); border-radius:8px; padding:6px }
                QLabel { color: white; font-weight: bold }
            ''')
            h_layout = QHBoxLayout(header)
            title = QLabel("📘 Grand Livre")
            title.setStyleSheet('font-size:16px')
            h_layout.addWidget(title)
            h_layout.addStretch()
            self.layout.addWidget(header)

            # Filters: search + refresh + export
            filter_frame = QFrame()
            filter_layout = QHBoxLayout(filter_frame)
            filter_layout.setContentsMargins(0, 6, 0, 6)
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Rechercher numéro, libellé, sens, montant...")
            self.search_input.textChanged.connect(self.load_data)
            filter_layout.addWidget(self.search_input)
            refresh_btn = QPushButton("🔄 Rafraîchir")
            refresh_btn.setStyleSheet("background-color:#8E44AD; color:white; padding:6px 12px; border-radius:6px;")
            refresh_btn.clicked.connect(self.load_data)
            export_btn = QPushButton("📤 Exporter")
            export_btn.setStyleSheet("background-color:#4CAF50; color:white; padding:6px 12px; border-radius:6px;")
            export_btn.clicked.connect(self.export_pdf)
            filter_layout.addWidget(refresh_btn)
            filter_layout.addWidget(export_btn)
            self.layout.addWidget(filter_frame)

            # Table container
            table_frame = QFrame()
            table_frame.setStyleSheet('QFrame { background: white; border-radius:6px; padding:4px }')
            table_layout = QVBoxLayout(table_frame)

            self.table = QTableView()
            self.model = QStandardItemModel()
            self.table.setModel(self.model)
            # Style uniforme
            self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
            self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)
            from PyQt6.QtWidgets import QHeaderView
            header_view = self.table.horizontalHeader()
            header_view.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            header_view.setStretchLastSection(False)
            self.table.setStyleSheet('''
                QHeaderView::section {
                    background-color: #8E44AD;
                    color: white;
                    font-weight: bold;
                    font-size: 13px;
                    border: none;
                    padding: 8px 4px;
                }
                QTableView::item:selected {
                    background-color: #e3f2fd;
                    color: #8E44AD;
                }
            ''')
            table_layout.addWidget(self.table)
            self.layout.addWidget(table_frame)

            # Connections
            self.table.doubleClicked.connect(self.show_ecritures)
            # initial load
            self.load_data()
        except Exception as e:
            print(f"[ERROR] GrandLivreWidget: erreur lors de la création des widgets/layout: {e}")

    def load_data(self):
        """Charge les données du grand livre via le controller"""
        if not self.entreprise_id:
            return
        data = self.controller.get_grand_livre(self.entreprise_id)
        search_text = self.search_input.text().strip().lower() if hasattr(self, "search_input") else ""
        headers = ["Numéro", "Libellé", "Total Débit", "Total Crédit", "Solde"]
        self.model.clear()
        self.model.setHorizontalHeaderLabels(headers)
        self._id_map = []  # Pour retrouver l'id du compte au double-clic
        for row in data:
            if search_text and not self._matches_search(row, search_text):
                continue

            items = self._build_row_items(row)
            for item in items:
                item.setEditable(False)
            self.model.appendRow(items)
            self._id_map.append(row.get("id"))
        self._apply_column_layout()

    def _apply_column_layout(self):
        from PyQt6.QtWidgets import QHeaderView

        numeric_width = 145
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(2, numeric_width)
        self.table.setColumnWidth(3, numeric_width)
        self.table.setColumnWidth(4, numeric_width)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)

    def _item(self, value):
        from PyQt6.QtGui import QStandardItem
        return QStandardItem(value)

    def _normalize_search_text(self, value):
        text = unicodedata.normalize("NFKD", str(value or ""))
        return "".join(char for char in text if not unicodedata.combining(char)).lower().strip()

    def _matches_search(self, row, search_text):
        normalized_search = self._normalize_search_text(search_text)
        terms = [term for term in normalized_search.split() if term]
        if not terms:
            return True

        search_pool = [
            row.get("numero", ""),
            row.get("nom", ""),
            row.get("libelle_sens", ""),
            row.get("sens_solde", ""),
            self._format_currency(row.get("total_debit", 0)),
            self._format_currency(row.get("total_credit", 0)),
            self._format_currency(row.get("solde", 0)),
            f"{float(row.get('total_debit', 0) or 0):.2f}",
            f"{float(row.get('total_credit', 0) or 0):.2f}",
            f"{float(row.get('solde', 0) or 0):.2f}",
        ]
        normalized_pool = " ".join(self._normalize_search_text(value) for value in search_pool)
        return all(term in normalized_pool for term in terms)

    def _build_row_items(self, row):
        items = [
            self._item(str(row.get("numero", ""))),
            self._item(str(row.get("nom", ""))),
            self._item(self._format_currency(row.get("total_debit", 0))),
            self._item(self._format_currency(row.get("total_credit", 0))),
            self._item(self._format_currency(row.get("solde", 0))),
        ]

        for item in items[2:]:
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        if float(row.get("solde", 0) or 0) < 0:
            items[4].setForeground(QColor("#C62828"))

        return items

    def _format_currency(self, value):
        # Utiliser le formateur central si disponible pour respecter la configuration de l'entreprise
        try:
            if hasattr(self, 'controller') and self.controller:
                return self.controller.format_amount(value)
        except Exception:
            pass
        if self.devise:
            return f"{value:,.2f} {self.devise}"
        return f"{value:,.2f}"

    def truncate(self, text, max_len):
        text = str(text or "")
        return text if len(text) <= max_len else text[:max_len-3] + "..."

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
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "ReportLab manquant", "Veuillez installer reportlab : pip install reportlab")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Exporter le Grand Livre en PDF", "grand_livre.pdf", "Fichiers PDF (*.pdf)")
        if not path:
            return

        data = self.controller.get_grand_livre(self.entreprise_id)
        doc = SimpleDocTemplate(path, pagesize=landscape(A4), rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        elements = []
        styles = getSampleStyleSheet()
        styleTitre = ParagraphStyle('Titre', parent=styles['Heading2'], alignment=1, fontSize=15, spaceAfter=10)

        # Header (logo + title)
        try:
            from ayanna_erp.modules.comptabilite.utils.pdf_export import prepare_header_elements, format_amount
            header_elems = prepare_header_elements(self.controller, self.entreprise_id, title="GRAND LIVRE")
            elements.extend(header_elems)
        except Exception:
            elements.append(Paragraph("GRAND LIVRE", styleTitre))
            elements.append(Spacer(1, 0.2*cm))

        table_data = [["Numéro", "Libellé", "Total Débit", "Total Crédit", "Solde"]]
        for row in data:
            try:
                td = format_amount(row.get('total_debit', 0), self.controller)
                tc = format_amount(row.get('total_credit', 0), self.controller)
                sd = format_amount(row.get('solde', 0), self.controller)
            except Exception:
                td = f"{row.get('total_debit',0):,.2f}"
                tc = f"{row.get('total_credit',0):,.2f}"
                sd = f"{row.get('solde',0):,.2f}"
            table_data.append([
                str(row.get('numero','')),
                self.truncate(row.get('nom',''), 60),
                td,
                tc,
                sd,
            ])

        table = Table(table_data, colWidths=[3*cm, 10*cm, 3.0*cm, 3.0*cm, 3.0*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#8E44AD')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (2,1), (-1,-1), 'RIGHT'),
            ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
        ]))
        elements.append(table)

        try:
            doc.build(elements)
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Export PDF réussi", f"Le Grand Livre a été exporté en PDF dans :\n{path}")
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur export PDF", f"Une erreur est survenue lors de l'export :\n{e}")

    def show_ecritures(self, index):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTableView, QDialogButtonBox, QPushButton, QFileDialog, QMessageBox, QHBoxLayout, QHeaderView
        from PyQt6.QtGui import QStandardItemModel, QStandardItem
        row = index.row()
        compte_id = self._id_map[row]
        compte = self.controller.get_compte_by_id(compte_id)
        dialog = QDialog(self)
        compte_label = f"{getattr(compte, 'numero', '')} - {getattr(compte, 'nom', '')}".strip(" -")
        dialog.setWindowTitle(f"Détail des écritures - {compte_label}")
        dialog.resize(1100, 700)
        layout = QVBoxLayout(dialog)

        filter_frame = QFrame()
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(0, 0, 0, 0)

        detail_search_input = QLineEdit()
        detail_search_input.setPlaceholderText("Rechercher date, journal, libellé, montant...")
        filter_layout.addWidget(detail_search_input, 2)

        date_debut_input = QDateEdit()
        date_debut_input.setCalendarPopup(True)
        date_debut_input.setDisplayFormat("dd/MM/yyyy")
        filter_layout.addWidget(QLabel("Du :"))
        filter_layout.addWidget(date_debut_input)

        date_fin_input = QDateEdit()
        date_fin_input.setCalendarPopup(True)
        date_fin_input.setDisplayFormat("dd/MM/yyyy")
        filter_layout.addWidget(QLabel("Au :"))
        filter_layout.addWidget(date_fin_input)

        apply_filter_btn = QPushButton("Filtrer")
        apply_filter_btn.setStyleSheet("background-color:#8E44AD; color:white; padding:6px 12px; border-radius:6px;")
        reset_filter_btn = QPushButton("Réinitialiser")
        reset_filter_btn.setStyleSheet("background-color:#607D8B; color:white; padding:6px 12px; border-radius:6px;")
        filter_layout.addWidget(apply_filter_btn)
        filter_layout.addWidget(reset_filter_btn)
        layout.addWidget(filter_frame)

        table = QTableView()
        model = QStandardItemModel()
        headers = ["Date", "Journal", "Libellé", "Débit", "Crédit"]
        model.setHorizontalHeaderLabels(headers)
        table.setModel(model)
        table.setSelectionBehavior(table.SelectionBehavior.SelectRows)
        table.setEditTriggers(table.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setWordWrap(False)
        table.verticalHeader().setVisible(False)
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        table.setStyleSheet('''
            QHeaderView::section {
                background-color: #8E44AD;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                padding: 8px 4px;
            }
            QTableView::item:selected {
                background-color: #e3f2fd;
                color: #8E44AD;
            }
        ''')
        layout.addWidget(table)

        # Ajout des totaux en bas
        total_layout = QHBoxLayout()
        total_debit_label = QLabel()
        total_credit_label = QLabel()
        solde_label = QLabel()
        total_layout.addWidget(total_debit_label)
        total_layout.addWidget(total_credit_label)
        total_layout.addWidget(solde_label)
        total_layout.addStretch()
        layout.addLayout(total_layout)

        export_data = []
        all_ecritures = self.controller.get_ecritures_compte(compte_id, self.entreprise_id)
        if all_ecritures:
            min_date = min(e.get("date_operation") for e in all_ecritures if e.get("date_operation"))
            max_date = max(e.get("date_operation") for e in all_ecritures if e.get("date_operation"))
            if min_date and max_date:
                q_min = QDate(min_date.year, min_date.month, min_date.day)
                q_max = QDate(max_date.year, max_date.month, max_date.day)
                date_debut_input.setDate(q_min)
                date_fin_input.setDate(q_max)
                date_debut_input.setMinimumDate(q_min)
                date_debut_input.setMaximumDate(q_max)
                date_fin_input.setMinimumDate(q_min)
                date_fin_input.setMaximumDate(q_max)
        else:
            today = QDate.currentDate()
            date_debut_input.setDate(today)
            date_fin_input.setDate(today)

        def build_detail_label(ecriture):
            ecriture_libelle = str(ecriture.get("libelle", "") or "").strip()
            journal_libelle = str(ecriture.get("journal", "") or "").strip()
            reference = str(ecriture.get("reference", "") or "").strip()

            parts = []
            if ecriture_libelle:
                parts.append(ecriture_libelle)
            if journal_libelle and journal_libelle.lower() != ecriture_libelle.lower():
                parts.append(journal_libelle)
            if reference:
                parts.append(f"Réf. {reference}")

            return " | ".join(parts) if parts else journal_libelle or "Sans libellé"

        def apply_detail_table_layout():
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
            table.setColumnWidth(0, 110)
            table.setColumnWidth(1, 220)
            table.setColumnWidth(3, 150)
            table.setColumnWidth(4, 150)

        def refresh_detail_data():
            nonlocal export_data

            date_debut = date_debut_input.date().toPyDate()
            date_fin = date_fin_input.date().toPyDate()
            raw_ecritures = self.controller.get_ecritures_compte(
                compte_id,
                self.entreprise_id,
                date_debut=date_debut,
                date_fin=date_fin,
            )

            search_text = detail_search_input.text().strip()
            if search_text:
                normalized_search = self._normalize_search_text(search_text)
                terms = [term for term in normalized_search.split() if term]
                filtered_ecritures = []
                for ecriture in raw_ecritures:
                    detail_label = build_detail_label(ecriture)
                    search_pool = " ".join([
                        str(ecriture.get("date", "")),
                        str(ecriture.get("journal", "")),
                        detail_label,
                        self._format_currency(ecriture.get("debit", 0)),
                        self._format_currency(ecriture.get("credit", 0)),
                        f"{float(ecriture.get('debit', 0) or 0):.2f}",
                        f"{float(ecriture.get('credit', 0) or 0):.2f}",
                    ])
                    normalized_pool = self._normalize_search_text(search_pool)
                    if all(term in normalized_pool for term in terms):
                        filtered_ecritures.append(ecriture)
            else:
                filtered_ecritures = raw_ecritures

            model.removeRows(0, model.rowCount())
            export_data = []
            total_debit = 0.0
            total_credit = 0.0

            for ecriture in filtered_ecritures:
                debit = float(ecriture.get("debit", 0) or 0)
                credit = float(ecriture.get("credit", 0) or 0)
                detail_label = build_detail_label(ecriture)
                total_debit += debit
                total_credit += credit

                items = [
                    QStandardItem(str(ecriture.get("date", ""))),
                    QStandardItem(str(ecriture.get("journal", "") or "-")),
                    QStandardItem(detail_label),
                    QStandardItem(self._format_currency(debit)),
                    QStandardItem(self._format_currency(credit)),
                ]
                for column, item in enumerate(items):
                    item.setEditable(False)
                    if column >= 3:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                model.appendRow(items)

                export_data.append({
                    "date": str(ecriture.get("date", "")),
                    "libelle": detail_label,
                    "debit": self._format_currency(debit),
                    "credit": self._format_currency(credit),
                })

            solde, metadata = self.controller.compute_account_display_balance(compte, total_debit, total_credit)
            total_debit_label.setText(f"Total Débit : <b>{self._format_currency(total_debit)}</b>")
            total_credit_label.setText(f"Total Crédit : <b>{self._format_currency(total_credit)}</b>")
            solde_prefix = f"Solde {metadata.get('libelle_sens', '')}".strip()
            solde_label.setText(f"{solde_prefix} : <b>{self._format_currency(solde)}</b>")
            solde_label.setStyleSheet("color: #C62828; font-weight: bold;" if solde < 0 else "")
            apply_detail_table_layout()

        detail_search_input.textChanged.connect(refresh_detail_data)
        apply_filter_btn.clicked.connect(refresh_detail_data)

        def reset_filters():
            detail_search_input.clear()
            if all_ecritures:
                min_date = min(e.get("date_operation") for e in all_ecritures if e.get("date_operation"))
                max_date = max(e.get("date_operation") for e in all_ecritures if e.get("date_operation"))
                if min_date and max_date:
                    date_debut_input.setDate(QDate(min_date.year, min_date.month, min_date.day))
                    date_fin_input.setDate(QDate(max_date.year, max_date.month, max_date.day))
            refresh_detail_data()

        reset_filter_btn.clicked.connect(reset_filters)
        refresh_detail_data()

        # Boutons
        btn_layout = QHBoxLayout()
        export_btn = QPushButton("Exporter PDF")
        btn_layout.addWidget(export_btn)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(dialog.reject)
        btn_layout.addWidget(btns)
        layout.addLayout(btn_layout)
        def export_detail_pdf():
            path, _ = QFileDialog.getSaveFileName(dialog, "Exporter le détail du compte en PDF", "detail_compte.pdf", "PDF Files (*.pdf)")
            if path:
                try:
                    # On passe l'entreprise_id pour un export PDF uniforme
                    self.controller.export_detail_compte_pdf(export_data, path, self.entreprise_id)
                    QMessageBox.information(dialog, "Export PDF", "Export PDF réussi !")
                except Exception as e:
                    QMessageBox.critical(dialog, "Erreur export PDF", str(e))
        export_btn.clicked.connect(export_detail_pdf)
        dialog.exec()

