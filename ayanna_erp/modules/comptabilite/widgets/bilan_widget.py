"""
BilanWidget - Onglet Bilan
Affiche Actif et Passif classés, export PDF.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableView, QPushButton, QHBoxLayout, QMessageBox
from PyQt6.QtGui import QStandardItemModel

class BilanWidget(QWidget):
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
        self.layout.addWidget(self.table_actif)
        self.layout.addWidget(self.table_passif)
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
        from datetime import date
        d1 = date.today().replace(day=1)
        d2 = date.today()
        data = self.controller.get_bilan_comptable(self.entreprise_id, d1, d2)
        headers = ["Compte", "Libellé", "Solde"]
        # Actifs
        self.model_actif.clear()
        self.model_actif.setHorizontalHeaderLabels(headers)
        for row in data["actifs"]:
            items = [
                self._item(str(row.get("compte", ""))),
                self._item(str(row.get("nom", ""))),
                self._item(self._format_currency(row.get("solde", 0))),
            ]
            for item in items:
                item.setEditable(False)
            self.model_actif.appendRow(items)
        self.table_actif.setColumnWidth(0, 120)
        self.table_actif.setColumnWidth(1, 300)
        self.table_actif.setColumnWidth(2, 120)
        # Passifs
        self.model_passif.clear()
        self.model_passif.setHorizontalHeaderLabels(headers)
        for row in data["passifs"]:
            items = [
                self._item(str(row.get("compte", ""))),
                self._item(str(row.get("nom", ""))),
                self._item(self._format_currency(row.get("solde", 0))),
            ]
            for item in items:
                item.setEditable(False)
            self.model_passif.appendRow(items)
        self.table_passif.setColumnWidth(0, 120)
        self.table_passif.setColumnWidth(1, 300)
        self.table_passif.setColumnWidth(2, 120)

    def _item(self, value):
        from PyQt6.QtGui import QStandardItem
        return QStandardItem(value)

    def _format_currency(self, value):
        if self.devise:
            return f"{value:,.0f} {self.devise}"
        return f"{value:,.0f}"

    def export_pdf(self):
        QMessageBox.information(self, "Export PDF", "Fonction d'export PDF non implémentée.")