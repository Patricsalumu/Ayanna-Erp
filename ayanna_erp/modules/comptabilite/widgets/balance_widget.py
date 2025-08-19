from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableView, QPushButton, QHBoxLayout, QDateEdit, QLabel
from PyQt6.QtGui import QStandardItemModel
from PyQt6.QtCore import QDate

class BalanceWidget(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.session = getattr(controller, 'session', None)
        self.entreprise_id = getattr(parent, 'entreprise_id', None) if parent is not None else None
        # Pré-charger la devise de l'entreprise
        self.devise = ""
        if self.session and self.entreprise_id:
            try:
                from core.controllers.ecole_controller import EcoleController
                ecole_ctrl = EcoleController(self.session)
                entreprise = ecole_ctrl.get_school_by_id(self.entreprise_id)
                if entreprise:
                    self.devise = getattr(entreprise, 'devise', '') or ''
            except Exception:
                self.devise = ''
        self.layout = QVBoxLayout(self)
        # Filtres période
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Du :"))
        self.date_debut = QDateEdit()
        self.date_debut.setDate(QDate.currentDate().addMonths(-1))
        filter_layout.addWidget(self.date_debut)
        filter_layout.addWidget(QLabel("au :"))
        self.date_fin = QDateEdit()
        self.date_fin.setDate(QDate.currentDate())
        filter_layout.addWidget(self.date_fin)
        self.refresh_btn = QPushButton("Rafraîchir")
        filter_layout.addWidget(self.refresh_btn)
        self.layout.addLayout(filter_layout)
        # Table
        self.table = QTableView()
        self.model = QStandardItemModel()
        self.table.setModel(self.model)
        # Style uniforme
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)
        header = self.table.horizontalHeader()
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
        # Export
        btn_layout = QHBoxLayout()
        self.export_btn = QPushButton("Exporter PDF")
        btn_layout.addWidget(self.export_btn)
        self.layout.addLayout(btn_layout)
        self.refresh_btn.clicked.connect(self.load_data)
        self.export_btn.clicked.connect(self.export_pdf)
        self.load_data()


    def load_data(self):
        """Charge la balance comptable filtrée via le controller"""
        if not self.entreprise_id:
            return
        d1 = self.date_debut.date().toPyDate()
        d2 = self.date_fin.date().toPyDate()
        data = self.controller.get_balance(self.entreprise_id, d1, d2)
        headers = ["Numéro", "Libellé", "Total Débit", "Total Crédit", "Solde"]
        self.model.clear()
        self.model.setHorizontalHeaderLabels(headers)
        for row in data:
            items = [
                self._item(str(row.get("compte", ""))),
                self._item(str(row.get("libelle", ""))),
                self._item(self._format_currency(row.get("debit", 0))),
                self._item(self._format_currency(row.get("credit", 0))),
                self._item(self._format_currency(row.get("solde", 0))),
            ]
            for item in items:
                item.setEditable(False)
            self.model.appendRow(items)
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
        d1 = self.date_debut.date().toPyDate()
        d2 = self.date_fin.date().toPyDate()
        data = []
        for row in range(self.model.rowCount()):
            data.append({
                "compte": self.model.item(row, 0).text(),
                "libelle": self.model.item(row, 1).text(),
                "debit": self.model.item(row, 2).text(),
                "credit": self.model.item(row, 3).text(),
                "solde": self.model.item(row, 4).text(),
            })
        path, _ = QFileDialog.getSaveFileName(self, "Exporter la balance en PDF", "balance.pdf", "PDF Files (*.pdf)")
        if path:
            try:
                self.controller.export_balance_pdf(data, path, d1, d2)
                QMessageBox.information(self, "Export PDF", "Export PDF réussi !")
            except Exception as e:
                QMessageBox.critical(self, "Erreur export PDF", str(e))
