"""
JournalWidget - Onglet Journal Comptable

Affiche la liste des journaux comptables enregistrés dans la base.

Tables SQLAlchemy utilisées :
- JournalComptable (__tablename__='journaux_comptables')
- EcritureComptable (__tablename__='ecritures_comptables')

Fonctionnalités :
- Filtrer les journaux par intervalle de dates (date_operation)
- Afficher les colonnes : Date, Libellé, Montant, Type d’opération
- Bouton "Transfert de fonds" (vérification des soldes, création journal + écritures)
- Bouton "Exporter PDF" (PDF uniforme)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QPushButton, QHBoxLayout, QLineEdit, QDateEdit, QHeaderView, QAbstractItemView, QMessageBox
)
from PyQt6.QtWidgets import QLabel, QComboBox, QFrame
from PyQt6.QtGui import QStandardItem, QColor
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, QDate
import datetime

from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ComptabiliteController
class JournalWidget(QWidget):
    JOURNAL_TYPE_OPTIONS = [
        ("Vente", "vente"),
        ("Achat", "achat"),
        ("Caisse", "caisse"),
        ("Banque", "banque"),
        ("OD", "od"),
    ]

    JOURNAL_TYPE_LABELS = {
        "vente": "Vente",
        "achat": "Achat",
        "caisse": "Caisse",
        "banque": "Banque",
        "od": "OD",
    }

    JOURNAL_TYPE_ALIASES = {
        "entree": "caisse",
        "entrée": "caisse",
        "sortie": "caisse",
        "transfert": "od",
        "paie": "caisse",
        "paies": "caisse",
        "operations diverses": "od",
        "operation diverse": "od",
    }

    @classmethod
    def normalize_journal_type(cls, raw_type):
        t = (raw_type or "").strip().lower()
        if t in cls.JOURNAL_TYPE_LABELS:
            return t
        return cls.JOURNAL_TYPE_ALIASES.get(t, "od")

    @classmethod
    def journal_type_label(cls, raw_type):
        code = cls.normalize_journal_type(raw_type)
        return cls.JOURNAL_TYPE_LABELS.get(code, "OD")

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        # Harmonisation : on attend toujours le controller en premier argument
        self.controller = controller
        self.session = getattr(controller, 'session', None)
        # On tente de récupérer entreprise_id depuis le parent si possible
        self.entreprise_id = getattr(parent, 'entreprise_id', None) if parent is not None else None
        # Pré-charger la devise de l'entreprise via le parent
        if parent and hasattr(parent, 'get_currency_symbol'):
            try:
                self.devise = parent.get_currency_symbol()
            except Exception as e:
                self.devise = ""  # Fallback
        else:
            self.devise = ""  # Fallback

        # Layout principal
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 12, 12, 12)

        # Header visuel (card) pour le module Comptabilité
        header_frame = QFrame()
        header_frame.setObjectName('journalHeader')
        header_frame.setStyleSheet('''
            QFrame#journalHeader {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8E44AD, stop:1 #8E44AD);
                border-radius: 8px;
                padding: 12px;
            }
            QLabel#titleLabel { color: white; font-size:16px; font-weight:bold }
            QLabel#subLabel { color: rgba(255,255,255,0.85); font-size:12px }
        ''')
        header_layout = QHBoxLayout(header_frame)
        title = QLabel("Journal Comptable")
        title.setObjectName('titleLabel')
        subtitle = QLabel("Consultation des journaux et écritures")
        subtitle.setObjectName('subLabel')
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(subtitle)
        self.layout.addWidget(header_frame)

        # Filtres (recherche, date, type, rafraîchir)
        filtres_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher par libellé...")
        self.debut_date = QDateEdit()
        self.debut_date.setCalendarPopup(True)
        self.debut_date.setDate(QDate.currentDate().addMonths(-1))
        self.fin_date = QDateEdit()
        self.fin_date.setCalendarPopup(True)
        self.fin_date.setDate(QDate.currentDate())

        # Filtre par type d'opération
        self.type_filter = QComboBox()
        self.type_filter.addItem("Tous", "")
        for label, code in self.JOURNAL_TYPE_OPTIONS:
            self.type_filter.addItem(label, code)

        # Boutons
        filtre_btn = QPushButton("Filtrer")
        filtre_btn.setStyleSheet("background-color:#8E44AD; color:white; padding:6px 12px; border-radius:6px;")
        filtre_btn.clicked.connect(self.load_data)
        refresh_btn = QPushButton("Rafraîchir")
        refresh_btn.setStyleSheet("background-color:#8E44AD; color:white; padding:6px 12px; border-radius:6px;")
        refresh_btn.clicked.connect(self.load_data)

        # Connexions des filtres pour rafraîchissement automatique
        try:
            self.search_input.textChanged.connect(self.load_data)
            self.debut_date.dateChanged.connect(self.load_data)
            self.fin_date.dateChanged.connect(self.load_data)
            self.type_filter.currentIndexChanged.connect(self.load_data)
        except Exception:
            # sécurité : si un widget n'existe pas encore, ignorer
            pass

        filtres_layout.addWidget(self.search_input)
        filtres_layout.addWidget(QLabel("Du"))
        filtres_layout.addWidget(self.debut_date)
        filtres_layout.addWidget(QLabel("Au"))
        filtres_layout.addWidget(self.fin_date)
        filtres_layout.addWidget(QLabel("Type"))
        filtres_layout.addWidget(self.type_filter)
        filtres_layout.addWidget(filtre_btn)
        filtres_layout.addWidget(refresh_btn)
        self.layout.addLayout(filtres_layout)

        # Table (encadrée dans une card blanche)
        table_frame = QFrame()
        table_frame.setStyleSheet('''
            QFrame { background-color: white; border-radius:8px; padding:8px }
        ''')
        table_layout = QVBoxLayout(table_frame)

        self.table = QTableView()
        self.model = QStandardItemModel()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Définir les labels des colonnes
        self.model.setHorizontalHeaderLabels(["Date opération", "Référence", "Libellé", "Type", "Débit", "Crédit"])

        # Colonnes redimensionnables
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)


        # Style du header et des lignes sélectionnées, thème comptabilité
        self.table.setStyleSheet('''
            QHeaderView::section { background-color: #8E44AD; color: white; font-weight: bold; padding:1px }
            QTableView::item:selected { background-color: #e3f2fd; color: #8E44AD }
            QTableView { alternate-background-color: #FBF5FF }
        ''')

        # Largeurs par défaut
        self.table.setColumnWidth(0, 140)
        self.table.setColumnWidth(1, 130)
        self.table.setColumnWidth(2, 420)
        self.table.setColumnWidth(3, 70)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 100)

        # Forcer hauteur d'en-tête et hauteur de ligne pour éviter agrandissement
        try:
            self.table.horizontalHeader().setFixedHeight(40)
            # Hauteur par défaut des lignes
            self.table.verticalHeader().setDefaultSectionSize(25)
        except Exception:
            pass

        table_layout.addWidget(self.table)
        self.layout.addWidget(table_frame, 2)


        # Actions
        actions_layout = QHBoxLayout()
        self.export_btn = QPushButton("Exporter PDF")
        self.export_btn.clicked.connect(self.export_pdf)
        actions_layout.addWidget(self.export_btn)
        self.transfer_btn = QPushButton("Passer une ecriture")
        self.transfer_btn.clicked.connect(self.show_transfer_dialog)
        actions_layout.addWidget(self.transfer_btn)
        self.layout.addLayout(actions_layout)

        self.table.doubleClicked.connect(self.toggle_ecritures_row)

        self.journaux = []
        self.ecritures_rows = {}  # journal_id: row index of ecritures
        # remplir les données
        self.load_data()

    def load_data(self):
        """Charge les journaux comptables filtrés"""
        if not self.controller or not self.entreprise_id:
            return
        debut = self.debut_date.date().toPyDate()
        fin = self.fin_date.date().toPyDate()
        search = self.search_input.text().strip().lower()
        # Récupérer tous les journaux disponibles
        journaux_all = self.controller.get_journaux_comptables(self.entreprise_id)
        # Filtrer uniquement par date d'opération
        journaux = [j for j in journaux_all if getattr(j, 'date_operation', None) and debut <= j.date_operation.date() <= fin]
        # Filtrer par recherche texte
        if search:
            journaux = [j for j in journaux if search in (j.libelle or '').lower()]

        # Filtrer par type si demandé
        sel_type = self.type_filter.currentData() if self.type_filter.count() > 0 else ''
        if sel_type:
            journaux = [j for j in journaux if self.normalize_journal_type(getattr(j, 'type_operation', '')) == sel_type]

        self.journaux = journaux
        self.refresh_table()

    def refresh_table(self):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(["Date opération", "Référence", "Libellé", "Type", "Débit", "Crédit"])
        self.ecritures_rows = {}

        total_debit = 0.0
        total_credit = 0.0

        for j in self.journaux:
            date_str = j.date_operation.strftime('%d/%m/%Y %H:%M')
            reference_str = getattr(j, 'reference', '') or ''
            montant = float(getattr(j, 'montant', 0) or 0)
            total_debit += montant
            total_credit += montant
            try:
                montant_str = self.controller.format_amount(montant)
            except Exception:
                montant_str = f"{montant:,.2f} {self.devise}" if self.devise else f"{montant:,.2f}"
            row = [
                QStandardItem(date_str),
                QStandardItem(reference_str),
                QStandardItem(j.libelle or ''),
                QStandardItem(self.journal_type_label(getattr(j, 'type_operation', ''))),
                QStandardItem(montant_str),
                QStandardItem(montant_str),
            ]

            # Alignements : Débit et Crédit à droite
            for idx, item in enumerate(row):
                if idx in (4, 5):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            # Taguer la ligne avec l'ID du journal
            try:
                row[0].setData(getattr(j, 'id', None), Qt.ItemDataRole.UserRole)
            except Exception:
                pass

            self.model.appendRow(row)

        # Ligne de totaux SYSCOHADA : Σ Débit = Σ Crédit
        try:
            total_d_str = self.controller.format_amount(total_debit)
            total_c_str = self.controller.format_amount(total_credit)
        except Exception:
            total_d_str = f"{total_debit:,.2f} {self.devise}" if self.devise else f"{total_debit:,.2f}"
            total_c_str = f"{total_credit:,.2f} {self.devise}" if self.devise else f"{total_credit:,.2f}"
        total_row = [
            QStandardItem("TOTAUX"),
            QStandardItem(""),
            QStandardItem(f"{len(self.journaux)} opération(s)"),
            QStandardItem(""),
            QStandardItem(total_d_str),
            QStandardItem(total_c_str),
        ]
        for idx, item in enumerate(total_row):
            fnt = item.font()
            fnt.setBold(True)
            item.setFont(fnt)
            item.setBackground(QColor("#E8D5F5"))
            if idx in (4, 5):
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            else:
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.model.appendRow(total_row)

        # Largeurs des colonnes
        self.table.setColumnWidth(0, 140)  # Date opération
        self.table.setColumnWidth(1, 150)  # Référence
        self.table.setColumnWidth(2, 500)  # Libellé
        self.table.setColumnWidth(3, 70)   # Type
        self.table.setColumnWidth(4, 100)  # Débit
        self.table.setColumnWidth(5, 100)  # Crédit
            
            
    def toggle_ecritures_row(self, index):
        clicked_row = index.row()

        # Trouver la ligne parente (celle qui a le UserRole) en remontant si nécessaire
        parent_row = None
        r = clicked_row
        while r >= 0:
            item = self.model.item(r, 0)
            if item:
                try:
                    val = item.data(Qt.ItemDataRole.UserRole)
                except Exception:
                    val = None
                if val is not None:
                    parent_row = r
                    break
            r -= 1

        if parent_row is None:
            # Rien à faire si on ne retrouve pas la ligne parente
            return

        row = parent_row

        # Vérifier si la ligne suivante est déjà un détail (évite doublons)
        if row + 1 < self.model.rowCount() and self.model.item(row + 1, 0) \
                and self.model.item(row + 1, 0).data(Qt.ItemDataRole.UserRole + 1) == "detail":
            # Supprimer toutes les lignes de détail existantes
            while row + 1 < self.model.rowCount() and \
                    self.model.item(row + 1, 0) and \
                    self.model.item(row + 1, 0).data(Qt.ItemDataRole.UserRole + 1) == "detail":
                self.model.removeRow(row + 1)
            return

        # Récupérer l'ID du journal stocké sur la ligne
        journal_id = None
        try:
            journal_id = self.model.item(row, 0).data(Qt.ItemDataRole.UserRole)
        except Exception:
            journal_id = None

        # Trouver l'objet journal correspondant dans self.journaux
        journal = None
        if journal_id is not None:
            for j in self.journaux:
                if getattr(j, 'id', None) == journal_id:
                    journal = j
                    break

        if journal is None:
            # Si non trouvé, essayer de récupérer par position (dégradé)
            try:
                journal = self.journaux[row]
            except Exception:
                return
        ecritures = self.controller.get_ecritures_du_journal(journal.id)

        for idx, e in enumerate(ecritures):
            # e peut être un objet ORM ou un dict léger retourné par le controller
            if isinstance(e, dict):
                debit_val = float(e.get('debit', 0) or 0)
                credit_val = float(e.get('credit', 0) or 0)
                # sens
                if float(debit_val) == 0 and float(credit_val) != 0:
                    sens = "Crédit"
                else:
                    sens = "Débit"

                # Montant à afficher
                montant = credit_val if sens == 'Crédit' else debit_val
                montant = montant or 0
                try:
                    montant_str = self.controller.format_amount(montant)
                except Exception:
                    montant_str = f"{montant:,.2f} {self.devise}" if self.devise else f"{montant:,.2f}"

                # Libellé : privilégier le champ 'libelle' renvoyé par le controller
                libelle = e.get('libelle') or ''
                # Compte : on peut tenter de récupérer le numéro du compte via l'id si la session est disponible
                compte = ''
                cid = e.get('compte_id')
                if cid and self.session:
                    try:
                        from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaComptes as CompteComptable
                        comp = self.session.query(CompteComptable).filter_by(id=cid).first()
                        compte = getattr(comp, 'numero', '') if comp is not None else str(cid)
                    except Exception:
                        compte = str(cid)

                detail_text = f"{sens} : {compte} - {libelle}  Montant : {montant_str}"
            else:
                # Objet ORM ancien format — conserver compatibilité
                debit_val = getattr(e, 'debit', 0) or 0
                credit_val = getattr(e, 'credit', 0) or 0
                if float(debit_val) == 0 and float(credit_val) != 0:
                    sens = "Crédit"
                else:
                    sens = "Débit"

                compte = getattr(e.compte_comptable, 'numero', '')
                # privilégier un libellé explicite si l'écriture expose 'libelle'
                libelle = getattr(e, 'libelle', None) or getattr(e.compte_comptable, 'libelle', '')

                montant = credit_val if sens == 'Crédit' else debit_val
                montant = montant or 0
                try:
                    montant_str = self.controller.format_amount(montant)
                except Exception:
                    montant_str = f"{montant:,.2f} {self.devise}" if self.devise else f"{montant:,.2f}"

                detail_text = f"{sens} : {compte} - {libelle}  Montant : {montant_str}"
            # Ligne de détail SYSCOHADA : date vide | compte | libellé | type vide | Débit | Crédit
            item_date_operation = QStandardItem("")
            item_compte = QStandardItem(f"  → {compte}")
            item_libelle = QStandardItem(libelle)
            item_type = QStandardItem("")
            item_debit = QStandardItem(montant_str if sens == "Débit" else "")
            item_credit = QStandardItem(montant_str if sens == "Crédit" else "")
            for it in [item_date_operation, item_compte, item_libelle, item_type, item_debit, item_credit]:
                it.setBackground(QColor("#f5f5f5"))
                fnt = it.font()
                fnt.setPointSize(10)
                it.setFont(fnt)
            item_debit.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item_credit.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            # Marqueur pour le toggle (collapse)
            item_date_operation.setData("detail", Qt.ItemDataRole.UserRole + 1)
            items = [item_date_operation, item_compte, item_libelle, item_type, item_debit, item_credit]
            self.model.insertRow(row + 1 + idx, items)


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
            QMessageBox.warning(self, "ReportLab manquant", "Veuillez installer reportlab : pip install reportlab")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Exporter le journal en PDF", "journal_comptable.pdf", "Fichiers PDF (*.pdf)")
        if not path:
            return

        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(path, pagesize=A4,
                                rightMargin=1.5*cm, leftMargin=1.5*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        elements = []

        styleTitre = ParagraphStyle('Titre', parent=styles['Heading2'], alignment=1, fontSize=15, spaceAfter=10)
        try:
            from ayanna_erp.modules.comptabilite.utils.pdf_export import prepare_header_elements
            header_elems = prepare_header_elements(self.controller,
                                                   getattr(self.controller, 'entreprise_id', None),
                                                   title="JOURNAL COMPTABLE")
            elements.extend(header_elems)
        except Exception:
            elements.append(Paragraph("JOURNAL COMPTABLE", styleTitre))
            elements.append(Spacer(1, 0.2*cm))

        # Période
        debut_str = self.debut_date.date().toString("dd/MM/yyyy")
        fin_str   = self.fin_date.date().toString("dd/MM/yyyy")
        elements.append(Paragraph(f"Période : du {debut_str} au {fin_str}", styles['Normal']))
        elements.append(Spacer(1, 0.3*cm))

        # En-têtes des colonnes SYSCOHADA
        col_widths = [2.8*cm, 2.0*cm, 6.0*cm, 1.5*cm, 2.2*cm, 2.2*cm]
        data = [["Date opération", "Référence", "Libellé", "Type", "Débit", "Crédit"]]
        # Indice des lignes "en-tête journal" pour le fond coloré
        header_rows = []

        total_debit  = 0.0
        total_credit = 0.0

        for j in self.journaux:
            date_str      = j.date_operation.strftime('%d/%m/%Y %H:%M')
            reference_str = getattr(j, 'reference', '') or ''
            montant       = float(getattr(j, 'montant', 0) or 0)
            total_debit  += montant
            total_credit += montant
            try:
                montant_str = self.controller.format_amount(montant)
            except Exception:
                montant_str = f"{montant:,.2f}"

            # Ligne résumé de l'opération
            header_rows.append(len(data))
            data.append([
                self.truncate(date_str, 16),
                self.truncate(reference_str, 12),
                self.truncate(j.libelle or '', 36),
                self.truncate(self.journal_type_label(getattr(j, 'type_operation', '')), 10),
                montant_str,
                montant_str,
            ])

            # Lignes d'écritures détaillées sous chaque opération
            try:
                ecritures = self.controller.get_ecritures_du_journal(j.id)
                for e in ecritures:
                    if isinstance(e, dict):
                        debit_val  = float(e.get('debit', 0) or 0)
                        credit_val = float(e.get('credit', 0) or 0)
                        e_libelle  = e.get('libelle') or ''
                        cid = e.get('compte_id')
                        e_compte = ''
                        if cid and self.session:
                            try:
                                from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaComptes as _CC
                                comp = self.session.query(_CC).filter_by(id=cid).first()
                                e_compte = getattr(comp, 'numero', '') if comp else str(cid)
                            except Exception:
                                e_compte = str(cid)
                    else:
                        debit_val  = float(getattr(e, 'debit', 0) or 0)
                        credit_val = float(getattr(e, 'credit', 0) or 0)
                        e_libelle  = getattr(e, 'libelle', None) or ''
                        e_compte   = getattr(e.compte_comptable, 'numero', '') if hasattr(e, 'compte_comptable') else ''
                    try:
                        d_str = self.controller.format_amount(debit_val)  if debit_val  else ''
                        c_str = self.controller.format_amount(credit_val) if credit_val else ''
                    except Exception:
                        d_str = f"{debit_val:,.2f}"  if debit_val  else ''
                        c_str = f"{credit_val:,.2f}" if credit_val else ''
                    data.append([
                        '',
                        f"  {e_compte}",
                        f"  {self.truncate(e_libelle, 34)}",
                        '',
                        d_str,
                        c_str,
                    ])
            except Exception:
                pass

        # Ligne de totaux
        try:
            total_d_str = self.controller.format_amount(total_debit)
            total_c_str = self.controller.format_amount(total_credit)
        except Exception:
            total_d_str = f"{total_debit:,.2f}"
            total_c_str = f"{total_credit:,.2f}"
        data.append(["TOTAUX", "", f"{len(self.journaux)} opération(s)", "", total_d_str, total_c_str])

        n = len(data)
        table = Table(data, repeatRows=1, colWidths=col_widths)
        style_cmds = [
            # En-tête colonnes
            ('BACKGROUND',    (0, 0),    (-1, 0),    colors.HexColor('#8E44AD')),
            ('TEXTCOLOR',     (0, 0),    (-1, 0),    colors.white),
            ('FONTNAME',      (0, 0),    (-1, 0),    'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0),    (-1, 0),    10),
            # Corps
            ('FONTSIZE',      (0, 1),    (-1, -1),   9),
            ('GRID',          (0, 0),    (-1, -1),   0.3, colors.grey),
            ('ALIGN',         (4, 0),    (-1, -1),   'RIGHT'),
            ('ALIGN',         (0, 0),    (3, -1),    'LEFT'),
            # Alternance de fond pour les lignes de détail
            ('ROWBACKGROUNDS',(0, 1),    (-1, n-2),  [colors.whitesmoke, colors.HexColor('#F9F3FF')]),
            # Ligne de totaux
            ('BACKGROUND',    (0, n-1),  (-1, n-1),  colors.HexColor('#E8D5F5')),
            ('FONTNAME',      (0, n-1),  (-1, n-1),  'Helvetica-Bold'),
        ]
        # Fond légèrement violet pour les lignes résumé (en-têtes journal)
        for hr in header_rows:
            style_cmds.append(('BACKGROUND', (0, hr), (-1, hr), colors.HexColor('#EFE0FB')))
            style_cmds.append(('FONTNAME',   (0, hr), (-1, hr), 'Helvetica-Bold'))
        table.setStyle(TableStyle(style_cmds))
        elements.append(table)

        try:
            doc.build(elements)
            QMessageBox.information(self, "Export PDF réussi",
                                    f"Journal SYSCOHADA exporté avec succès :\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "Erreur export PDF", f"Erreur lors de l'export :\n{e}")
    
    @staticmethod
    def truncate(text, max_len):
        text = str(text)
        return text if len(text) <= max_len else text[:max_len-3] + "..."

    def show_transfer_dialog(self):

        # ...existing code...
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QMessageBox, QFrame
        from PyQt6.QtGui import QFont
        dialog = QDialog(self)
        dialog.setWindowTitle("Passer une ecriture comptable")
        dialog.setMinimumWidth(480)
        layout = QVBoxLayout(dialog)

        title = QLabel("<b>Passer une ecriture comptable</b>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(13)
        title.setFont(font)
        layout.addWidget(title)

        # Ligne séparatrice
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # Sélection compte débit (caisse uniquement)
        h_debit = QHBoxLayout()
        lbl_debit = QLabel("<b>Compte caisse à débiter :</b>")
        h_debit.addWidget(lbl_debit)
        cb_debit = QComboBox()
        comptes_caisse = self.controller.get_comptes_caisse_banque(self.entreprise_id)
        for c in comptes_caisse:
            solde = self.controller.get_solde_compte(c.id)
            try:
                solde_str = self.controller.format_amount(solde)
            except Exception:
                solde_str = f"{solde:,.2f} {self.devise}" if self.devise else f"{solde:,.2f}"
            cb_debit.addItem(f"{c.numero} - {c.libelle} (Solde: {solde_str})", c.id)
        h_debit.addWidget(cb_debit)
        layout.addLayout(h_debit)

        # Sélection compte crédit (actif, passif, charge, produit)
        h_credit = QHBoxLayout()
        lbl_credit = QLabel("<b>Compte à créditer :</b>")
        h_credit.addWidget(lbl_credit)
        cb_credit = QComboBox()
        # Import des modèles depuis le bon chemin
        from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import CompteComptable, ClasseComptable
        classes = self.controller.session.query(ClasseComptable).filter(
            ClasseComptable.enterprise_id == self.entreprise_id,
            ClasseComptable.actif == True,
            ClasseComptable.type.in_(["actif", "passif", "charge", "produit"])
        ).all()
        comptes_credit = []
        for cl in classes:
            comptes_credit += [c for c in cl.comptes if c.actif]
        for c in comptes_credit:
            solde = self.controller.get_solde_compte(c.id)
            try:
                solde_str = self.controller.format_amount(solde)
            except Exception:
                solde_str = f"{solde:,.2f} {self.devise}" if self.devise else f"{solde:,.2f}"
            cb_credit.addItem(f"{c.numero} - {c.libelle} (Solde: {solde_str})", c.id)
        h_credit.addWidget(cb_credit)
        layout.addLayout(h_credit)

        # Montant
        h_montant = QHBoxLayout()
        lbl_montant = QLabel("<b>Montant :</b>")
        h_montant.addWidget(lbl_montant)
        le_montant = QLineEdit()
        le_montant.setPlaceholderText("0")
        h_montant.addWidget(le_montant)
        layout.addLayout(h_montant)

        # Libellé
        h_libelle = QHBoxLayout()
        lbl_libelle = QLabel("<b>Libellé :</b>")
        h_libelle.addWidget(lbl_libelle)
        le_libelle = QLineEdit()
        h_libelle.addWidget(le_libelle)
        layout.addLayout(h_libelle)

        # N° pièce / Référence
        h_reference = QHBoxLayout()
        lbl_reference = QLabel("<b>N° pièce / Référence :</b>")
        h_reference.addWidget(lbl_reference)
        le_reference = QLineEdit()
        le_reference.setPlaceholderText("Ex : OD-001, VRS-001, EXP-005...")
        h_reference.addWidget(le_reference)
        layout.addLayout(h_reference)

        # Date de l'opération
        h_date = QHBoxLayout()
        lbl_date = QLabel("<b>Date de l’opération :</b>")
        h_date.addWidget(lbl_date)
        le_date = QDateEdit()
        le_date.setCalendarPopup(True)
        le_date.setDate(QDate.currentDate())
        le_date.setDisplayFormat("dd/MM/yyyy")
        h_date.addWidget(le_date)
        layout.addLayout(h_date)

        # Type de journal
        h_type = QHBoxLayout()
        lbl_type = QLabel("<b>Type de journal :</b>")
        h_type.addWidget(lbl_type)
        cb_type = QComboBox()
        cb_type.addItem("Vente", "vente")
        cb_type.addItem("Achat", "achat")
        cb_type.addItem("Caisse", "caisse")
        cb_type.addItem("Banque", "banque")
        cb_type.addItem("OD", "od")
        h_type.addWidget(cb_type)
        layout.addLayout(h_type)

        note_type = QLabel("Note: les paies sont a enregistrer dans le type Caisse.")
        note_type.setStyleSheet("color:#555; font-size:11px;")
        layout.addWidget(note_type)

        # Boutons
        btns = QHBoxLayout()
        btn_ok = QPushButton("Valider")
        btn_cancel = QPushButton("Annuler")
        btn_ok.setStyleSheet("background-color: #8E44AD; color: white; font-weight: bold; padding: 6px 18px; border-radius: 6px;")
        btn_cancel.setStyleSheet("background-color: #e0e0e0; color: #333; font-weight: bold; padding: 6px 18px; border-radius: 6px;")
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

        # Style général
        dialog.setStyleSheet('''
            QDialog { background: #fafbfc; }
            QLabel { font-size: 12px; }
            QComboBox, QLineEdit { font-size: 12px; min-height: 28px; }
        ''')

        def on_valider():
            compte_debit_id = cb_debit.currentData()
            compte_credit_id = cb_credit.currentData()
            montant = le_montant.text().replace(",", ".")
            libelle = le_libelle.text().strip()
            reference = le_reference.text().strip()
            date_py = le_date.date().toPyDate()
            from datetime import datetime as _DT
            date_op = _DT(date_py.year, date_py.month, date_py.day)
            try:
                montant = float(montant)
            except Exception:
                QMessageBox.warning(dialog, "Erreur", "Montant invalide.")
                return
            if not compte_debit_id or not compte_credit_id or compte_debit_id == compte_credit_id:
                QMessageBox.warning(dialog, "Erreur", "Sélectionnez deux comptes différents.")
                return
            if montant <= 0:
                QMessageBox.warning(dialog, "Erreur", "Le montant doit être positif.")
                return

            # Récupérer les libellés pour affichage
            debit_label = cb_debit.currentText()
            credit_label = cb_credit.currentText()
            details = f"<b>Compte à débiter :</b> {debit_label}<br>"
            details += f"<b>Compte à créditer :</b> {credit_label}<br>"
            try:
                montant_display = self.controller.format_amount(montant)
            except Exception:
                montant_display = f"{montant:,.2f} {self.devise}" if self.devise else f"{montant:,.2f}"
            details += f"<b>Montant :</b> {montant_display}<br>"
            details += f"<b>Libellé :</b> {libelle}<br>"
            details += f"<b>N° pièce :</b> {reference or '—'}<br>"
            details += f"<b>Date :</b> {le_date.date().toString('dd/MM/yyyy')}<br>"
            details += f"<b>Type de journal :</b> {cb_type.currentText()}"

            confirm = QMessageBox(self)
            confirm.setWindowTitle("Confirmer l'ecriture")
            confirm.setText("Veuillez confirmer les informations de l'ecriture :")
            confirm.setInformativeText(details)
            confirm.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
            confirm.setDefaultButton(QMessageBox.StandardButton.Ok)
            confirm.setIcon(QMessageBox.Icon.Question)
            ret = confirm.exec()
            if ret != QMessageBox.StandardButton.Ok:
                return

            # Appel du contrôleur pour effectuer le transfert
            ok, msg = self.controller.transfert_journal(
                entreprise_id=self.entreprise_id,
                compte_debit_id=compte_debit_id,
                compte_credit_id=compte_credit_id,
                montant=montant,
                libelle=libelle,
                type_operation=cb_type.currentData(),
                date_operation=date_op,
                reference=reference or None
            )
            if ok:
                QMessageBox.information(dialog, "Succès", msg)
                dialog.accept()
                self.load_data()
            else:
                QMessageBox.warning(dialog, "Erreur", msg)

        btn_ok.clicked.connect(on_valider)
        btn_cancel.clicked.connect(dialog.reject)
        dialog.exec()