"""
GrandLivreWidget - Onglet Grand Livre Comptable
Affiche tous les comptes ave        # Largeurs par défaut
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 120)
        
        # Configuration finale des colonnes maintenant qu'elles existent
        header = self.table.horizontalHeader()
        from PyQt6.QtWidgets import QHeaderView
        col_count = self.model.columnCount()
        if col_count > 0:
            # Appliquer Stretch sur la dernière colonne
            header.setSectionResizeMode(col_count-1, QHeaderView.ResizeMode.Stretch)aux débit, crédit, solde. Double-clic = détail écritures.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableView, QPushButton, QHBoxLayout, QDialog, QLabel, QFrame, QLineEdit
from PyQt6.QtGui import QStandardItemModel
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
            self.search_input.setPlaceholderText("Rechercher compte, libellé...")
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
            header_view.setStretchLastSection(True)
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
        headers = ["Numéro", "Libellé", "Total Débit", "Total Crédit", "Solde"]
        self.model.clear()
        self.model.setHorizontalHeaderLabels(headers)
        self._id_map = []  # Pour retrouver l'id du compte au double-clic
        for row in data:
            items = [
                self._item(str(row.get("numero", ""))),
                self._item(str(row.get("nom", ""))),
                self._item(self._format_currency(row.get("total_debit", 0))),
                self._item(self._format_currency(row.get("total_credit", 0))),
                self._item(self._format_currency(row.get("solde", 0))),
            ]
            for item in items:
                item.setEditable(False)
            self.model.appendRow(items)
            self._id_map.append(row.get("id"))
        # Largeurs par défaut
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(1, 300)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 120)

    def _item(self, value):
        from PyQt6.QtGui import QStandardItem
        return QStandardItem(value)

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

    def export_pdf(self):
        try:
            from reportlab.lib.pagesizes import A4
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
        doc = SimpleDocTemplate(path, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
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
                str(row.get('nom','')),
                td,
                tc,
                sd,
            ])

        table = Table(table_data, colWidths=[3*cm, 7*cm, 2.5*cm, 2.5*cm, 2.5*cm])
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
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTableView, QDialogButtonBox, QPushButton, QFileDialog, QMessageBox, QHBoxLayout
        from PyQt6.QtGui import QStandardItemModel, QStandardItem
        row = index.row()
        compte_id = self._id_map[row]
        ecritures = self.controller.get_ecritures_compte(compte_id, self.entreprise_id)
        dialog = QDialog(self)
        dialog.setWindowTitle("Détail des écritures")
        dialog.resize(900, 600)  # Agrandissement de la fenêtre modale
        layout = QVBoxLayout(dialog)
        table = QTableView()
        model = QStandardItemModel()
        headers = ["Date", "Libellé", "Débit", "Crédit"]
        model.setHorizontalHeaderLabels(headers)
        export_data = []
        # Import du modèle JournalComptable
        from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaJournaux as JournalComptable
        total_debit = 0
        total_credit = 0
        for e in ecritures:
            journal_libelle = ""
            journal = self.session.query(JournalComptable).filter_by(id=e['journal_id']).first()
            debit = float(e.get("debit", 0))
            credit = float(e.get("credit", 0))
            total_debit += debit
            total_credit += credit
            # privilégier le libellé de l'écriture s'il existe, sinon le libellé du journal
            item_libelle = str(e.get('libelle', '')) if isinstance(e, dict) else ''
            if not item_libelle:
                item_libelle = str(journal.libelle if journal else '')
            items = [
                QStandardItem(str(e.get("date", ""))),
                QStandardItem(item_libelle),
                QStandardItem(self._format_currency(debit)),
                QStandardItem(self._format_currency(credit)),
            ]
            for item in items:
                item.setEditable(False)
            model.appendRow(items)
            export_data.append({
                "date": str(e.get("date", "")),
                "libelle": journal_libelle or str(e.get("libelle", "")),
                "debit": self._format_currency(debit),
                "credit": self._format_currency(credit),
            })
        table.setModel(model)
        table.resizeColumnsToContents()
        # Style détail
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
        layout.addWidget(table)

        # Ajout des totaux en bas
        from PyQt6.QtWidgets import QLabel
        solde = total_debit - total_credit
        total_layout = QHBoxLayout()
        total_debit_label = QLabel(f"Total Débit : <b>{self._format_currency(total_debit)}</b>")
        total_credit_label = QLabel(f"Total Crédit : <b>{self._format_currency(total_credit)}</b>")
        solde_label = QLabel(f"Solde : <b>{self._format_currency(solde)}</b>")
        total_layout.addWidget(total_debit_label)
        total_layout.addWidget(total_credit_label)
        total_layout.addWidget(solde_label)
        layout.addLayout(total_layout)

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

