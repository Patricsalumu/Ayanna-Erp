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
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableView, QPushButton, QHBoxLayout, QDialog
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
            self.layout = QVBoxLayout(self)
            self.table = QTableView()
            self.model = QStandardItemModel()
            self.table.setModel(self.model)
            # Style uniforme
            self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
            self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)
            header = self.table.horizontalHeader()
            from PyQt6.QtWidgets import QHeaderView
            # Configuration des colonnes sera faite après le chargement des données
            header.setSectionResizeMode(header.ResizeMode.Interactive)
            header.setStretchLastSection(True)
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
            self.layout.addWidget(self.table)
            btn_layout = QHBoxLayout()
            self.export_btn = QPushButton("Exporter PDF")
            btn_layout.addWidget(self.export_btn)
            self.layout.addLayout(btn_layout)
            self.export_btn.clicked.connect(self.export_pdf)
            self.table.doubleClicked.connect(self.show_ecritures)
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
        if self.devise:
            return f"{value:,.0f} {self.devise}"
        return f"{value:,.0f}"

    def export_pdf(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        QMessageBox.information(self, "Export PDF", "Export PDF, non encore implémenté dans cette version.")

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
            items = [
                QStandardItem(str(e.get("date", ""))),
                QStandardItem(str(journal.libelle if journal else "")),
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

