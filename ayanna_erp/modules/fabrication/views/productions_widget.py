from PyQt6.QtWidgets import QDialog, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QLabel, QMessageBox
from PyQt6.QtCore import Qt
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.fabrication.models import Production
from ayanna_erp.modules.fabrication.controllers.fabrication_controller import FabricationController
from ayanna_erp.modules.fabrication.views.production_dialog import ProductionDialog

class ProductionsWidget(QWidget):
    def __init__(self, pos_id=None, current_user=None, parent=None):
        super().__init__(parent)
        self.pos_id = pos_id
        self.current_user = current_user
        self.db = DatabaseManager()
        self.controller = FabricationController()
        self.setup_ui()
        self.refresh_productions()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        header.addWidget(QLabel("Ordres de Production"))
        add_btn = QPushButton("Nouvelle production")
        add_btn.clicked.connect(self.create_production)
        header.addWidget(add_btn)
        layout.addLayout(header)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Code", "Produit", "Quantité prévue", "Etat", "Actions"])
        layout.addWidget(self.table)

    def refresh_productions(self):
        try:
            session = self.db.get_session()
            prods = session.query(Production).order_by(Production.created_at.desc()).all()
            self.table.setRowCount(len(prods))
            for row, p in enumerate(prods):
                self.table.setItem(row, 0, QTableWidgetItem(str(p.id)))
                self.table.setItem(row, 1, QTableWidgetItem(p.production_code or ""))
                prod_name = session.query(p.product.property.mapper.class_).get(p.product_id).name if p.product_id else str(p.product_id)
                self.table.setItem(row, 2, QTableWidgetItem(prod_name))
                self.table.setItem(row, 3, QTableWidgetItem(str(p.planned_quantity)))
                self.table.setItem(row, 4, QTableWidgetItem(p.status or ""))
                # Actions placeholder
                btn = QPushButton("Ouvrir")
                btn.clicked.connect(lambda checked, pid=p.id: self.open_production(pid))
                self.table.setCellWidget(row, 5, btn)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des productions: {e}")

    def create_production(self):
        dialog = ProductionDialog(pos_id=self.pos_id, current_user=self.current_user, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # refresh list after creation
            self.refresh_productions()

    def open_production(self, production_id: int):
        from ayanna_erp.modules.fabrication.views.production_detail import ProductionDetailDialog
        dialog = ProductionDetailDialog(production_id=production_id, pos_id=self.pos_id, current_user=self.current_user, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_productions()
