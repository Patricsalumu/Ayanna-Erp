"""
BilanWidget - Onglet Bilan
Affiche Actif et Passif classés, export PDF.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableView, QPushButton, QHBoxLayout, QMessageBox, QLabel, QFrame, QDateEdit
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor
from PyQt6.QtCore import Qt

class BilanWidget(QWidget):
    ACTIF_SECTIONS = {
        "2": "ACTIF IMMOBILISÉ",
        "3": "ACTIF CIRCULANT - STOCKS",
        "4": "ACTIF CIRCULANT - TIERS",
        "5": "TRÉSORERIE ACTIF",
    }

    PASSIF_SECTIONS = {
        "1": "RESSOURCES DURABLES ET CAPITAUX PROPRES",
        "4": "PASSIF CIRCULANT - TIERS",
        "5": "TRÉSORERIE PASSIF",
        "R": "RÉSULTAT DE L'EXERCICE",
    }

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
                print(f"[DEBUG] BilanWidget: Erreur lors de l'obtention de la devise: {e}")
                self.devise = "€"  # Fallback
        else:
            print(f"[DEBUG] BilanWidget: parent sans get_currency_symbol(), devise par défaut")
            self.devise = "€"  # Fallback
        self.layout = QVBoxLayout(self)

        # Header
        header = QFrame()
        header.setStyleSheet('''
            QFrame { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #8E44AD, stop:1 #8E44AD); border-radius:8px; padding:6px }
            QLabel { color: white; font-weight: bold }
        ''')
        h_layout = QHBoxLayout(header)
        title = QLabel("⚖️ Bilan")
        title.setStyleSheet('font-size:16px')
        h_layout.addWidget(title)
        h_layout.addStretch()
        self.layout.addWidget(header)

        # Date filters (user requested ability to filter between two dates)
        filter_frame = QFrame()
        fl = QHBoxLayout(filter_frame)
        fl.setContentsMargins(0,6,0,6)
        fl.addWidget(QLabel("Du"))
        self.date_debut = QDateEdit()
        self.date_debut.setCalendarPopup(True)
        from PyQt6.QtCore import QDate
        self.date_debut.setDate(QDate.currentDate().addMonths(-1).addDays(1-QDate.currentDate().day()))
        fl.addWidget(self.date_debut)
        fl.addWidget(QLabel("Au"))
        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDate(QDate.currentDate())
        fl.addWidget(self.date_fin)
        filter_btn = QPushButton("Filtrer")
        filter_btn.setStyleSheet("background:#8E44AD;color:white;padding:6px 12px;border-radius:6px;")
        filter_btn.clicked.connect(self.load_data)
        fl.addWidget(filter_btn)
        refresh_btn = QPushButton("🔄")
        refresh_btn.clicked.connect(self.load_data)
        fl.addWidget(refresh_btn)
        self.layout.addWidget(filter_frame)

        self.table_actif = QTableView()
        self.model_actif = QStandardItemModel()
        self.table_actif.setModel(self.model_actif)
        self.table_passif = QTableView()
        self.model_passif = QStandardItemModel()
        self.table_passif.setModel(self.model_passif)
        # Style uniforme
        for table in (self.table_actif, self.table_passif):
            table.setSelectionBehavior(table.SelectionBehavior.SelectRows)
            table.setEditTriggers(table.EditTrigger.NoEditTriggers)
            header = table.horizontalHeader()
            header.setSectionResizeMode(header.ResizeMode.Interactive)
            header.setStretchLastSection(True)
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
        actif_frame = QFrame()
        actif_frame.setStyleSheet('QFrame{background:white;border-radius:6px;padding:4px}')
        actif_layout = QVBoxLayout(actif_frame)
        actif_layout.addWidget(QLabel("ACTIF"))
        actif_layout.addWidget(self.table_actif)
        self.layout.addWidget(actif_frame)

        passif_frame = QFrame()
        passif_frame.setStyleSheet('QFrame{background:white;border-radius:6px;padding:4px}')
        passif_layout = QVBoxLayout(passif_frame)
        passif_layout.addWidget(QLabel("PASSIF"))
        passif_layout.addWidget(self.table_passif)
        self.layout.addWidget(passif_frame)

        # Totaux Actif / Passif
        totals_layout = QHBoxLayout()
        self.total_actif_label = QLabel("Total Actif : 0")
        self.total_passif_label = QLabel("Total Passif : 0")
        # Style léger pour mettre en évidence
        for lbl in (self.total_actif_label, self.total_passif_label):
            lbl.setStyleSheet('font-weight:bold; padding:6px')
        totals_layout.addWidget(self.total_actif_label)
        totals_layout.addStretch()
        totals_layout.addWidget(self.total_passif_label)
        self.layout.addLayout(totals_layout)

        btn_layout = QHBoxLayout()
        self.export_btn = QPushButton("Exporter PDF")
        btn_layout.addWidget(self.export_btn)
        self.layout.addLayout(btn_layout)
        self.export_btn.clicked.connect(self.export_pdf)
        self.load_data()

    def load_data(self):
        """Charge les données du bilan via le controller (nouvelle logique SYSCOHADA)"""
        if not self.entreprise_id:
            return
        # Utiliser les dates choisies par l'utilisateur
        try:
            d1 = self.date_debut.date().toPyDate()
            d2 = self.date_fin.date().toPyDate()
        except Exception:
            from datetime import date
            d1 = date.today().replace(day=1)
            d2 = date.today()
        data = self.controller.get_bilan_comptable(self.entreprise_id, d1, d2)
        headers = ["Compte", "Rubrique SYSCOHADA", "Montant"]
        # Actifs
        self.model_actif.clear()
        self.model_actif.setHorizontalHeaderLabels(headers)
        self._populate_bilan_model(self.model_actif, data["actifs"], side="actif")
        self.table_actif.setColumnWidth(0, 120)
        self.table_actif.setColumnWidth(1, 360)
        self.table_actif.setColumnWidth(2, 120)
        # Passifs
        self.model_passif.clear()
        self.model_passif.setHorizontalHeaderLabels(headers)
        self._populate_bilan_model(self.model_passif, data["passifs"], side="passif")
        self.table_passif.setColumnWidth(0, 120)
        self.table_passif.setColumnWidth(1, 360)
        self.table_passif.setColumnWidth(2, 120)

        # Calculer et afficher les totaux Actif / Passif
        try:
            total_actif = sum(float(row.get("solde", 0) or 0) for row in data.get("actifs", []))
        except Exception:
            total_actif = 0
        try:
            total_passif = sum(float(row.get("solde", 0) or 0) for row in data.get("passifs", []))
        except Exception:
            total_passif = 0
        try:
            self.total_actif_label.setText(f"Total Actif : {self._format_currency(total_actif)}")
            self.total_passif_label.setText(f"Total Passif : {self._format_currency(total_passif)}")
        except Exception:
            # Si labels non initialisés pour une raison quelconque, on ignore
            pass

    def _section_key(self, compte):
        code = str(compte or "")
        if code.startswith("Résultat"):
            return "R"
        return code[:1] if code else ""

    def _append_section_row(self, model, label):
        items = [QStandardItem(label), QStandardItem(""), QStandardItem("")]
        for item in items:
            item.setEditable(False)
            item.setBackground(QColor("#E8D5F5"))
            font = item.font()
            font.setBold(True)
            item.setFont(font)
        model.appendRow(items)

    def _append_value_row(self, model, compte, nom, montant):
        items = [
            self._item(str(compte or "")),
            self._item(str(nom or "")),
            self._item(self._format_currency(montant or 0)),
        ]
        items[2].setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        for item in items:
            item.setEditable(False)
        model.appendRow(items)

    def _populate_bilan_model(self, model, rows, side="actif"):
        sections = self.ACTIF_SECTIONS if side == "actif" else self.PASSIF_SECTIONS
        grouped = {}
        for row in rows:
            grouped.setdefault(self._section_key(row.get("compte")), []).append(row)
        for section in sections:
            entries = grouped.get(section, [])
            if not entries:
                continue
            self._append_section_row(model, sections[section])
            for row in sorted(entries, key=lambda item: str(item.get("compte", ""))):
                self._append_value_row(model, row.get("compte"), row.get("nom"), row.get("solde", 0))

    def _group_bilan_rows(self, rows, side="actif"):
        sections = self.ACTIF_SECTIONS if side == "actif" else self.PASSIF_SECTIONS
        grouped = {}
        for row in rows:
            grouped.setdefault(self._section_key(row.get("compte")), []).append(row)
        result = []
        for section in sections:
            entries = grouped.get(section, [])
            if not entries:
                continue
            result.append((sections[section], sorted(entries, key=lambda item: str(item.get("compte", "")))))
        return result

    def _item(self, value):
        from PyQt6.QtGui import QStandardItem
        return QStandardItem(value)

    def _format_currency(self, value):
        # Utiliser le formatage central si possible
        try:
            if hasattr(self, 'controller') and self.controller:
                return self.controller.format_amount(value)
        except Exception:
            pass
        if self.devise:
            return f"{value:,.2f} {self.devise}"
        return f"{value:,.2f}"

    def export_pdf(self):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import cm
            from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer, Image
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from PyQt6.QtWidgets import QFileDialog
            import os
            from datetime import datetime
        except ImportError:
            QMessageBox.warning(self, "ReportLab manquant", "Veuillez installer reportlab : pip install reportlab")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Exporter le bilan en PDF", "bilan.pdf", "Fichiers PDF (*.pdf)")
        if not path:
            return

        # Récupérer les données
        try:
            d1 = self.date_debut.date().toPyDate()
            d2 = self.date_fin.date().toPyDate()
        except Exception:
            from datetime import date
            d1 = date.today().replace(day=1)
            d2 = date.today()
        data = self.controller.get_bilan_comptable(self.entreprise_id, d1, d2)

        # Préparer le document
        doc = SimpleDocTemplate(path, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        elements = []
        styles = getSampleStyleSheet()
        styleTitre = ParagraphStyle('Titre', parent=styles['Heading2'], alignment=1, fontSize=15, spaceAfter=10)
        styleMention = ParagraphStyle('Mention', parent=styles['Normal'], alignment=1, textColor=colors.HexColor('#888888'), fontSize=9, spaceAfter=0, spaceBefore=0)

        # Entête entreprise
        # Header (logo + titre + mention)
        try:
            from ayanna_erp.modules.comptabilite.utils.pdf_export import prepare_header_elements, format_amount
            header_elems = prepare_header_elements(self.controller, self.entreprise_id, title="BILAN COMPTABLE")
            elements.extend(header_elems)
        except Exception:
            # fallback minimal header
            elements.append(Paragraph("BILAN COMPTABLE", styleTitre))
            elements.append(Spacer(1, 0.2*cm))

        elements.append(Paragraph(f"Période : du {d1.strftime('%d/%m/%Y')} au {d2.strftime('%d/%m/%Y')}", styles['Normal']))
        elements.append(Spacer(1, 0.2*cm))

        # Actifs
        elements.append(Paragraph("ACTIF", styles['Heading4']))
        actif_data = [["Compte", "Rubrique SYSCOHADA", "Montant"]]
        for label, entries in self._group_bilan_rows(data.get('actifs', []), side='actif'):
            actif_data.append([label, "", ""])
            for r in entries:
                sol = r.get('solde', 0)
                try:
                    display = format_amount(sol, self.controller)
                except Exception:
                    display = f"{sol:,.2f}"
                actif_data.append([r.get('compte', ''), r.get('nom', ''), display])
        table_actif = Table(actif_data, colWidths=[3*cm, 8.5*cm, 3.5*cm])
        actif_style = [
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#8E44AD')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN', (2,1), (2,-1), 'RIGHT'),
            ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
        ]
        for row_index, row in enumerate(actif_data[1:], start=1):
            if row[1] == '' and row[2] == '':
                actif_style.append(('BACKGROUND', (0, row_index), (-1, row_index), colors.HexColor('#E8D5F5')))
                actif_style.append(('FONTNAME', (0, row_index), (-1, row_index), 'Helvetica-Bold'))
        table_actif.setStyle(TableStyle(actif_style))
        elements.append(table_actif)
        elements.append(Spacer(1, 0.3*cm))

        # Passifs
        elements.append(Paragraph("PASSIF", styles['Heading4']))
        passif_data = [["Compte", "Rubrique SYSCOHADA", "Montant"]]
        for label, entries in self._group_bilan_rows(data.get('passifs', []), side='passif'):
            passif_data.append([label, "", ""])
            for r in entries:
                sol = r.get('solde', 0)
                try:
                    display = format_amount(sol, self.controller)
                except Exception:
                    display = f"{sol:,.2f}"
                passif_data.append([r.get('compte', ''), r.get('nom', ''), display])
        table_passif = Table(passif_data, colWidths=[3*cm, 8.5*cm, 3.5*cm])
        passif_style = [
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#8E44AD')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN', (2,1), (2,-1), 'RIGHT'),
            ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
        ]
        for row_index, row in enumerate(passif_data[1:], start=1):
            if row[1] == '' and row[2] == '':
                passif_style.append(('BACKGROUND', (0, row_index), (-1, row_index), colors.HexColor('#E8D5F5')))
                passif_style.append(('FONTNAME', (0, row_index), (-1, row_index), 'Helvetica-Bold'))
        table_passif.setStyle(TableStyle(passif_style))
        elements.append(table_passif)
        elements.append(Spacer(1, 0.3*cm))

        # Totaux
        total_actifs = data.get('total_actifs', 0)
        total_passifs = data.get('total_passifs', 0)
        try:
            ta = format_amount(total_actifs, self.controller)
            tp = format_amount(total_passifs, self.controller)
        except Exception:
            ta = f"{total_actifs:,.2f}"
            tp = f"{total_passifs:,.2f}"
        synthese = Table([
            ["Total Actif", ta],
            ["Total Passif", tp],
        ], colWidths=[8.5*cm, 3.5*cm])
        synthese.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7F1FB')),
            ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ]))
        elements.append(synthese)

        try:
            doc.build(elements)
            QMessageBox.information(self, "Export PDF réussi", f"Le bilan a été exporté en PDF dans :\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "Erreur export PDF", f"Une erreur est survenue lors de l'export :\n{e}")