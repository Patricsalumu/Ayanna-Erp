"""
CompteResultatWidget - Onglet Compte de Résultat
Affiche charges, produits, résultat net. Export PDF.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableView, QPushButton, QHBoxLayout, QLabel, QFrame, QDateEdit, QLineEdit
from PyQt6.QtGui import QStandardItemModel

class CompteResultatWidget(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        from PyQt6.QtWidgets import QDateEdit, QLabel
        from PyQt6.QtCore import QDate
        self.controller = controller
        self.session = getattr(controller, 'session', None)
        self.entreprise_id = getattr(parent, 'entreprise_id', None) if parent is not None else None
        # Pré-charger la devise de l'entreprise via le parent
        self.devise = ""
        if parent and hasattr(parent, 'get_currency_symbol'):
            try:
                self.devise = parent.get_currency_symbol()
            except Exception as e:
                print(f"[DEBUG] CompteResultatWidget: Erreur lors de l'obtention de la devise: {e}")
                self.devise = ""  # Fallback
        else:
            print(f"[DEBUG] CompteResultatWidget: parent sans get_currency_symbol(), devise par défaut")
            self.devise = ""  # Fallback
        self.layout = QVBoxLayout(self)

        # Header
        header = QFrame()
        header.setStyleSheet('''
            QFrame { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #8E44AD, stop:1 #8E44AD); border-radius:8px; padding:6px }
            QLabel { color: white; font-weight: bold }
        ''')
        h_layout = QHBoxLayout(header)
        title = QLabel("📊 Compte de résultat")
        title.setStyleSheet('font-size:16px')
        h_layout.addWidget(title)
        h_layout.addStretch()
        self.layout.addWidget(header)

        # Filters: date range + search
        filter_frame = QFrame()
        fl = QHBoxLayout(filter_frame)
        fl.setContentsMargins(0,6,0,6)
        fl.addWidget(QLabel("Du"))
        self.date_debut_edit = QDateEdit()
        self.date_debut_edit.setCalendarPopup(True)
        self.date_debut_edit.setDate(QDate.currentDate().addMonths(-1).addDays(1-QDate.currentDate().day()))
        fl.addWidget(self.date_debut_edit)
        fl.addWidget(QLabel("Au"))
        self.date_fin_edit = QDateEdit()
        self.date_fin_edit.setCalendarPopup(True)
        self.date_fin_edit.setDate(QDate.currentDate())
        fl.addWidget(self.date_fin_edit)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filtrer par compte ou libellé...")
        self.search_input.textChanged.connect(self.load_data)
        fl.addWidget(self.search_input)
        self.filtrer_btn = QPushButton("Filtrer")
        self.filtrer_btn.setStyleSheet("background:#8E44AD;color:white;padding:6px 12px;border-radius:6px;")
        fl.addWidget(self.filtrer_btn)
        refresh_btn = QPushButton("🔄")
        refresh_btn.clicked.connect(self.load_data)
        fl.addWidget(refresh_btn)
        self.layout.addWidget(filter_frame)

        # Tables
        self.table_charges = QTableView()
        self.model_charges = QStandardItemModel()
        self.table_charges.setModel(self.model_charges)
        self.table_produits = QTableView()
        self.model_produits = QStandardItemModel()
        self.table_produits.setModel(self.model_produits)
        # Style uniforme
        for table in (self.table_charges, self.table_produits):
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
        # Put tables inside frames with titles
        charges_frame = QFrame(); charges_frame.setStyleSheet('QFrame{background:white;border-radius:6px;padding:4px}')
        cf_layout = QVBoxLayout(charges_frame)
        cf_layout.addWidget(QLabel("Charges"))
        cf_layout.addWidget(self.table_charges)
        self.layout.addWidget(charges_frame)

        produits_frame = QFrame(); produits_frame.setStyleSheet('QFrame{background:white;border-radius:6px;padding:4px}')
        pf_layout = QVBoxLayout(produits_frame)
        pf_layout.addWidget(QLabel("Produits"))
        pf_layout.addWidget(self.table_produits)
        self.layout.addWidget(produits_frame)

        # Totals / résultat
        totals_frame = QFrame()
        totals_layout = QHBoxLayout(totals_frame)
        self.total_charges_label = QLabel("Total Charges : 0")
        self.total_produits_label = QLabel("Total Produits : 0")
        self.resultat_label = QLabel("Résultat Net : 0")
        for lbl in (self.total_charges_label, self.total_produits_label, self.resultat_label):
            lbl.setStyleSheet('font-weight:bold; padding:6px')
            totals_layout.addWidget(lbl)
        totals_layout.addStretch()
        self.layout.addWidget(totals_frame)

        btn_layout = QHBoxLayout()
        self.export_btn = QPushButton("📤 Exporter PDF")
        self.export_btn.setStyleSheet("background:#4CAF50;color:white;padding:8px 14px;border-radius:6px;")
        btn_layout.addStretch()
        btn_layout.addWidget(self.export_btn)
        self.layout.addLayout(btn_layout)
        self.export_btn.clicked.connect(self.export_pdf)
        self.filtrer_btn.clicked.connect(self.load_data)
        self.load_data()

    def load_data(self):
        """Charge les données du compte de résultat via le controller avec filtre date"""
        if not self.entreprise_id:
            return
        d1 = self.date_debut_edit.date().toPyDate()
        d2 = self.date_fin_edit.date().toPyDate()
        data = self.controller.get_compte_resultat(self.entreprise_id, d1, d2)
        # Charges
        headers = ["Compte", "Libellé", "Total"]
        self.model_charges.clear()
        self.model_charges.setHorizontalHeaderLabels(headers)
        for row in data["charges"]:
            if row.get("total", 0) != 0:
                items = [
                    self._item(str(row.get("compte", ""))),
                    self._item(str(row.get("nom", ""))),
                    self._item(self._format_currency(row.get("total", 0))),
                ]
                for item in items:
                    item.setEditable(False)
                self.model_charges.appendRow(items)
        self.table_charges.setColumnWidth(0, 120)
        self.table_charges.setColumnWidth(1, 300)
        self.table_charges.setColumnWidth(2, 120)
        # Produits
        self.model_produits.clear()
        self.model_produits.setHorizontalHeaderLabels(headers)
        for row in data["produits"]:
            if row.get("total", 0) != 0:
                items = [
                    self._item(str(row.get("compte", ""))),
                    self._item(str(row.get("nom", ""))),
                    self._item(self._format_currency(row.get("total", 0))),
                ]
                for item in items:
                    item.setEditable(False)
                self.model_produits.appendRow(items)
        self.table_produits.setColumnWidth(0, 120)
        self.table_produits.setColumnWidth(1, 300)
        self.table_produits.setColumnWidth(2, 120)
        # Totaux charges/produits
        total_charges = sum(row.get("total", 0) for row in data["charges"])
        total_produits = sum(row.get("total", 0) for row in data["produits"])
        self.total_charges_label.setText(f"Total Charges : {self._format_currency(total_charges)}")
        self.total_produits_label.setText(f"Total Produits : {self._format_currency(total_produits)}")
        # Résultat net
        self.resultat_label.setText(f"Résultat Net : {self._format_currency(data['resultat_net'])}")

    def _item(self, value):
        from PyQt6.QtGui import QStandardItem
        return QStandardItem(value)

    def _format_currency(self, value):
        # Utiliser le formatage central si possible (respecter la configuration entreprise)
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
            from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from PyQt6.QtWidgets import QFileDialog
            import os
            from datetime import datetime
        except ImportError:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "ReportLab manquant", "Veuillez installer reportlab : pip install reportlab")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Exporter le compte de résultat en PDF", "compte_resultat.pdf", "Fichiers PDF (*.pdf)")
        if not path:
            return

        # Récupérer les données
        d1 = self.date_debut_edit.date().toPyDate()
        d2 = self.date_fin_edit.date().toPyDate()
        data = self.controller.get_compte_resultat(self.entreprise_id, d1, d2)

        doc = SimpleDocTemplate(path, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        elements = []
        styles = getSampleStyleSheet()
        styleTitre = ParagraphStyle('Titre', parent=styles['Heading2'], alignment=1, fontSize=15, spaceAfter=10)

        # Header with logo and generated mention
        try:
            from ayanna_erp.modules.comptabilite.utils.pdf_export import prepare_header_elements, format_amount
            header_elems = prepare_header_elements(self.controller, self.entreprise_id, title="COMPTE DE RÉSULTAT")
            elements.extend(header_elems)
        except Exception:
            elements.append(Paragraph("COMPTE DE RÉSULTAT", styleTitre))
        elements.append(Spacer(1, 0.2*cm))

        # Charges
        elements.append(Paragraph("Charges", styles['Heading4']))
        charges = data.get('charges', [])
        ch_data = [["Compte", "Libellé", "Total"]]
        for r in charges:
            try:
                display = format_amount(r.get('total', 0), self.controller)
            except Exception:
                display = f"{r.get('total', 0):,.2f}"
            ch_data.append([r.get('compte', ''), r.get('nom', ''), display])
        table_ch = Table(ch_data, colWidths=[3*cm, 9*cm, 3*cm])
        table_ch.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#8E44AD')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (2,1), (2,-1), 'RIGHT'),
            ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
        ]))
        elements.append(table_ch)
        elements.append(Spacer(1, 0.3*cm))

        # Produits
        elements.append(Paragraph("Produits", styles['Heading4']))
        produits = data.get('produits', [])
        pr_data = [["Compte", "Libellé", "Total"]]
        for r in produits:
            try:
                display = format_amount(r.get('total', 0), self.controller)
            except Exception:
                display = f"{r.get('total', 0):,.2f}"
            pr_data.append([r.get('compte', ''), r.get('nom', ''), display])
        table_pr = Table(pr_data, colWidths=[3*cm, 9*cm, 3*cm])
        table_pr.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#8E44AD')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (2,1), (2,-1), 'RIGHT'),
            ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
        ]))
        elements.append(table_pr)
        elements.append(Spacer(1, 0.3*cm))

        # Totaux et résultat
        total_charges = sum(r.get('total', 0) for r in charges)
        total_produits = sum(r.get('total', 0) for r in produits)
        resultat = data.get('resultat_net', 0)
        try:
            tc = format_amount(total_charges, self.controller)
            tp = format_amount(total_produits, self.controller)
            rt = format_amount(resultat, self.controller)
        except Exception:
            tc = f"{total_charges:,.2f}"
            tp = f"{total_produits:,.2f}"
            rt = f"{resultat:,.2f}"
        elements.append(Paragraph(f"Total Charges : {tc}", styles['Normal']))
        elements.append(Paragraph(f"Total Produits : {tp}", styles['Normal']))
        elements.append(Paragraph(f"Résultat Net : {rt}", styles['Normal']))

        try:
            doc.build(elements)
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Export PDF réussi", f"Le compte de résultat a été exporté en PDF dans :\n{path}")
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur export PDF", f"Une erreur est survenue lors de l'export :\n{e}")

