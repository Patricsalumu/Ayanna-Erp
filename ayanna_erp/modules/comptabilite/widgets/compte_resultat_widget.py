"""
CompteResultatWidget - Onglet Compte de Résultat
Affiche charges, produits, résultat net. Export PDF.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableView, QPushButton, QHBoxLayout
from PyQt6.QtGui import QStandardItemModel

class CompteResultatWidget(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        from PyQt6.QtWidgets import QDateEdit, QLabel
        from PyQt6.QtCore import QDate
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
        # Filtres date
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Date début :"))
        self.date_debut_edit = QDateEdit()
        self.date_debut_edit.setCalendarPopup(True)
        self.date_debut_edit.setDate(QDate.currentDate().addMonths(-1).addDays(1-QDate.currentDate().day()))
        filter_layout.addWidget(self.date_debut_edit)
        filter_layout.addWidget(QLabel("Date fin :"))
        self.date_fin_edit = QDateEdit()
        self.date_fin_edit.setCalendarPopup(True)
        self.date_fin_edit.setDate(QDate.currentDate())
        filter_layout.addWidget(self.date_fin_edit)
        self.filtrer_btn = QPushButton("Filtrer")
        filter_layout.addWidget(self.filtrer_btn)
        self.layout.addLayout(filter_layout)

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
        self.layout.addWidget(self.table_charges)
        self.total_charges_label = QPushButton("Total Charges : 0")
        self.total_charges_label.setEnabled(False)
        self.layout.addWidget(self.total_charges_label)
        self.layout.addWidget(self.table_produits)
        self.total_produits_label = QPushButton("Total Produits : 0")
        self.total_produits_label.setEnabled(False)
        self.layout.addWidget(self.total_produits_label)
        self.resultat_label = QPushButton("Résultat Net : 0")
        self.resultat_label.setEnabled(False)
        self.layout.addWidget(self.resultat_label)
        btn_layout = QHBoxLayout()
        self.export_btn = QPushButton("Exporter PDF")
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
        if self.devise:
            return f"{value:,.0f} {self.devise}"
        return f"{value:,.0f}"

    def export_pdf(self):
        from PyQt6.QtWidgets import  QMessageBox
        QMessageBox.information(self, "Export PDF", "Export PDF,non encore implémenté dans cette version.")

