"""
ClassesWidget - Onglet Classes Comptables
Lecture seule des classes, export PDF.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableView, QPushButton, QHBoxLayout
from PyQt6.QtGui import QStandardItemModel

class ClassesWidget(QWidget):
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
        btn_layout = QHBoxLayout()
        self.export_btn = QPushButton("Exporter PDF")
        btn_layout.addWidget(self.export_btn)
        self.layout.addLayout(btn_layout)
        self.export_btn.clicked.connect(self.export_pdf)
        self.load_data()

    def load_data(self):
        """Charge les classes via le controller"""
        if not self.entreprise_id:
            return
        self._id_map = []
        data = self.controller.get_classes(self.entreprise_id)
        headers = ["Numéro", "Nom", "Libellé"]
        self.model.clear()
        self.model.setHorizontalHeaderLabels(headers)
        for row in data:
            items = [
                self._item(str(row.get("numero", ""))),
                self._item(str(row.get("nom", ""))),
                self._item(str(row.get("libelle", ""))),
            ]
            for item in items:
                item.setEditable(False)
            self.model.appendRow(items)
            self._id_map.append(row.get("id"))
        # Largeurs par défaut
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 300)

    def _item(self, value):
        from PyQt6.QtGui import QStandardItem
        return QStandardItem(value)

    def export_pdf(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        QMessageBox.information(self, "Export PDF", "Export PDF, non encore implémenté dans cette version.")