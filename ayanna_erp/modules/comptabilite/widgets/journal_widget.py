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
from PyQt6.QtGui import QStandardItem, QColor
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, QDate
import datetime

from comptabilite.controller.comptabilite_controller import ComptabiliteController
class JournalWidget(QWidget):

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        # Harmonisation : on attend toujours le controller en premier argument
        self.controller = controller
        self.session = getattr(controller, 'session', None)
        # On tente de récupérer entreprise_id depuis le parent si possible
        self.entreprise_id = getattr(parent, 'entreprise_id', None) if parent is not None else None
        # Pré-charger la devise de l'entreprise (utilise une valeur par défaut pour l'instant)
        self.devise = "CDF"  # Devise par défaut

        self.layout = QVBoxLayout(self)

        # Filtres
        filtres_layout = QHBoxLayout()
        self.debut_date = QDateEdit()
        self.debut_date.setCalendarPopup(True)
        self.debut_date.setDate(QDate.currentDate().addMonths(-1))
        self.fin_date = QDateEdit()
        self.fin_date.setCalendarPopup(True)
        self.fin_date.setDate(QDate.currentDate())
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher par libellé...")
        filtre_btn = QPushButton("Filtrer")
        filtre_btn.clicked.connect(self.load_data)
        self.debut_date.dateChanged.connect(self.load_data)
        self.fin_date.dateChanged.connect(self.load_data)
        self.search_input.textChanged.connect(self.load_data)
        filtres_layout.addWidget(self.debut_date)
        filtres_layout.addWidget(self.fin_date)
        filtres_layout.addWidget(self.search_input)
        filtres_layout.addWidget(filtre_btn)
        self.layout.addLayout(filtres_layout)

        # Table
        self.table = QTableView()
        self.model = QStandardItemModel()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Définir les labels des colonnes
        self.model.setHorizontalHeaderLabels(["Date/Heure", "Libellé", "Montant", "Type"])

        # Colonnes redimensionnables manuellement
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)  # L'utilisateur peut redimensionner
        header.setStretchLastSection(True)  # La dernière colonne s'étire pour occuper tout l'espace

        # Largeurs par défaut pour chaque colonne
        self.table.setColumnWidth(0, 150)  # Date/Heure
        self.table.setColumnWidth(1, 460)  # Libellé
        self.table.setColumnWidth(2, 120)  # Montant
        self.table.setColumnWidth(3, 40)  # Type

        # Style du header
        self.table.setStyleSheet('''
            QHeaderView::section {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                padding: 8px 4px;
            }
            QTableView::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
        ''')

        self.layout.addWidget(self.table, 2)


        # Actions
        actions_layout = QHBoxLayout()
        self.export_btn = QPushButton("Exporter PDF")
        self.export_btn.clicked.connect(self.export_pdf)
        actions_layout.addWidget(self.export_btn)
        self.transfer_btn = QPushButton("Transfert de fonds")
        self.transfer_btn.clicked.connect(self.show_transfer_dialog)
        actions_layout.addWidget(self.transfer_btn)
        self.layout.addLayout(actions_layout)

        self.table.doubleClicked.connect(self.toggle_ecritures_row)

        self.journaux = []
        self.ecritures_rows = {}  # journal_id: row index of ecritures
        self.load_data()

    def load_data(self):
        """Charge les journaux comptables filtrés"""
        if not self.controller or not self.entreprise_id:
            return
        debut = self.debut_date.date().toPyDate()
        fin = self.fin_date.date().toPyDate()
        search = self.search_input.text().strip().lower()
        journaux = self.controller.get_journaux_comptables(self.entreprise_id)
        journaux = [j for j in journaux if debut <= j.date_operation.date() <= fin]
        if search:
            journaux = [j for j in journaux if search in (j.libelle or '').lower()]
        self.journaux = journaux
        self.refresh_table()

    def refresh_table(self):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(["Date/Heure", "Libellé", "Montant", "Type"])
        self.ecritures_rows = {}

        for j in self.journaux:
            # Date+Heure
            date_str = j.date_operation.strftime('%d/%m/%Y %H:%M')
            # Montant avec devise
            montant_str = f"{j.montant:,.0f} {self.devise}" if self.devise else f"{j.montant:,.0f}"
            row = [
                QStandardItem(date_str),
                QStandardItem(j.libelle),
                QStandardItem(montant_str),
                QStandardItem(j.type_operation)
            ]

            # Alignements
            for idx, item in enumerate(row):
                if idx == 2:  # Montant à droite
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            self.model.appendRow(row)

            # ✅ Définir des largeurs par défaut pour chaque colonne
            self.table.setColumnWidth(0, 150)  # Date/Heure
            self.table.setColumnWidth(1, 460)  # Libellé
            self.table.setColumnWidth(2, 120)  # Montant
            self.table.setColumnWidth(3, 40)  # Type
            
            
    def toggle_ecritures_row(self, index):
        row = index.row()

        # Vérifier si la ligne suivante est déjà un détail (évite doublons)
        if row + 1 < self.model.rowCount() and self.model.item(row + 1, 0) \
                and self.model.item(row + 1, 0).text().startswith("Débit"):
            # Supprimer toutes les lignes de détail existantes
            while row + 1 < self.model.rowCount() and \
                    self.model.item(row + 1, 0) and \
                    (self.model.item(row + 1, 0).text().startswith("Débit") or
                    self.model.item(row + 1, 0).text().startswith("Crédit")):
                self.table.setSpan(row + 1, 0, 1, 1)  # Réinitialiser la fusion
                self.model.removeRow(row + 1)
            return

        journal = self.journaux[row]
        ecritures = self.controller.get_ecritures_du_journal(journal.id)

        for idx, e in enumerate(ecritures):
            sens = "Débit" if e.ordre == 1 else "Crédit"
            compte = getattr(e.compte_comptable, 'numero', '')
            libelle = getattr(e.compte_comptable, 'libelle', '')
            montant = e.debit if e.ordre == 1 else e.credit
            montant_str = f"{montant:,.0f} {self.devise}" if self.devise else f"{montant:,.0f}"

            # Créer un item pour cette écriture
            detail_text = f"{sens} : {compte} - {libelle}  Montant : {montant_str}"
            detail_item = QStandardItem(detail_text)
            detail_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            detail_item.setBackground(QColor("#f5f5f5"))  # Fond gris clair
            font = detail_item.font()
            font.setPointSize(10)  # Police un peu plus petite
            detail_item.setFont(font)

            # Ajouter la ligne avec 4 colonnes (les 3 dernières vides)
            items = [detail_item] + [QStandardItem("") for _ in range(3)]
            self.model.insertRow(row + 1 + idx, items)

            # Fusionner cette ligne pour occuper toute la largeur
            self.table.setSpan(row + 1 + idx, 0, 1, 4)


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
        path, _ = QFileDialog.getSaveFileName(self, "Exporter le journal en PDF", "journal_comptable.pdf", "Fichiers PDF (*.pdf)")
        if not path:
            return
        # Préparer les données
        data = [["Date/Heure", "Libellé", "Montant", "Type"]]
        for j in self.journaux:
            date_str = j.date_operation.strftime('%d/%m/%Y %H:%M')
            montant_str = f"{j.montant:,.0f} {self.devise}" if self.devise else f"{j.montant:,.0f}"
            libelle_pdf = self.truncate(j.libelle, 40)
            date_pdf = self.truncate(date_str, 20)
            montant_pdf = self.truncate(montant_str, 15)
            type_pdf = self.truncate(j.type_operation, 12)
            data.append([
                date_pdf,
                libelle_pdf,
                montant_pdf,
                type_pdf
            ])
        # Largeurs PDF personnalisées
        page_width = A4[0] - 4*cm
        col_widths = [3.2*cm, 7.5*cm, 3.2*cm, 2.1*cm]
        # Récupérer infos école/logo (utilise des valeurs par défaut pour l'instant)
        entite_info = {'nom': 'Ayanna ERP', 'adresse': '', 'telephone': '', 'email': ''}
        logo_path = None
        # Création du PDF
        doc = SimpleDocTemplate(
            path,
            pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm
        )
        elements = []
        styles = getSampleStyleSheet()
        styleN = styles['Normal']
        styleTitre = ParagraphStyle('Titre', parent=styles['Heading2'], alignment=1, fontSize=15, spaceAfter=10)
        styleMention = ParagraphStyle('Mention', parent=styles['Normal'], alignment=1, textColor=colors.HexColor('#888888'), fontSize=9, spaceAfter=0, spaceBefore=0)
        # Mention spéciale en haut
        mention_text = "Généré par Ayanna School - {}".format(datetime.now().strftime('%d/%m/%Y %H:%M'))
        elements.append(Paragraph(mention_text, styleMention))
        elements.append(Spacer(1, 0.2*cm))
        # Bloc logo + infos école
        header_data = []
        if logo_path and os.path.exists(logo_path):
            try:
                img = Image(logo_path, width=2.5*cm, height=2.5*cm)
                header_data.append([
                    img,
                    Paragraph(f"<b>{entite_info.get('nom','')}</b><br/>{entite_info.get('adresse','')}<br/>{entite_info.get('telephone','')}<br/>{entite_info.get('email','')}", styleN)
                ])
            except Exception:
                header_data.append([
                    Paragraph("<b>Logo non lisible</b>", styleN),
                    Paragraph(f"<b>{entite_info.get('nom','')}</b><br/>{entite_info.get('adresse','')}<br/>{entite_info.get('telephone','')}<br/>{entite_info.get('email','')}", styleN)
                ])
        else:
            header_data.append([
                "",
                Paragraph(f"<b>{entite_info.get('nom','')}</b><br/>{entite_info.get('adresse','')}<br/>{entite_info.get('telephone','')}<br/>{entite_info.get('email','')}", styleN)
            ])
        t = Table(header_data, colWidths=[3*cm, 12*cm], hAlign='LEFT')
        t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 0.2*cm))
        # Titre stylisé
        titre = "JOURNAL COMPTABLE"
        elements.append(Paragraph(titre, styleTitre))
        elements.append(Spacer(1, 0.2*cm))
        # Tableau
        table = Table(data, repeatRows=1, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#FF9800')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 11),
            ('FONTSIZE', (0,1), (-1,-1), 10),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.lightgrey]),
        ]))
        elements.append(table)
        try:
            doc.build(elements)
            QMessageBox.information(self, "Export PDF réussi", f"Le journal comptable a été exporté en PDF dans :\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "Erreur export PDF", f"Une erreur est survenue lors de l'export :\n{e}")
    
    @staticmethod
    def truncate(text, max_len):
        text = str(text)
        return text if len(text) <= max_len else text[:max_len-3] + "..."

    def show_transfer_dialog(self):

        # ...existing code...
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QMessageBox, QFrame
        from PyQt6.QtGui import QFont
        dialog = QDialog(self)
        dialog.setWindowTitle("Transfert de fonds entre comptes")
        dialog.setMinimumWidth(480)
        layout = QVBoxLayout(dialog)

        title = QLabel("<b>Transfert de fonds entre comptes</b>")
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
            cb_debit.addItem(f"{c.numero} - {c.libelle} (Solde: {solde:,.0f} {self.devise})", c.id)
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
            cb_credit.addItem(f"{c.numero} - {c.libelle} (Solde: {solde:,.0f} {self.devise})", c.id)
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

        # Boutons
        btns = QHBoxLayout()
        btn_ok = QPushButton("Valider")
        btn_cancel = QPushButton("Annuler")
        btn_ok.setStyleSheet("background-color: #1976d2; color: white; font-weight: bold; padding: 6px 18px; border-radius: 6px;")
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
            details += f"<b>Montant :</b> {montant:,.0f} {self.devise}<br>"
            details += f"<b>Libellé :</b> {libelle}"

            confirm = QMessageBox(self)
            confirm.setWindowTitle("Confirmer le transfert")
            confirm.setText("Veuillez confirmer les informations du transfert :")
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
                libelle=libelle
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