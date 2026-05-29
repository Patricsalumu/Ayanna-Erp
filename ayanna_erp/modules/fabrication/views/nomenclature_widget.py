from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QLabel, QMessageBox
from PyQt6.QtCore import Qt
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.fabrication.models import FabricationRule, FabricationRuleItem
from PyQt6.QtWidgets import QFileDialog
from ayanna_erp.modules.fabrication.print_export import export_rule_pdf

class NomenclatureWidget(QWidget):
    def __init__(self, pos_id=None, current_user=None, parent=None):
        super().__init__(parent)
        self.pos_id = pos_id
        self.current_user = current_user
        self.db = DatabaseManager()
        self.setup_ui()
        self.refresh_rules()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        header.addWidget(QLabel("Nomenclatures (Règles de fabrication)"))
        add_btn = QPushButton("Nouvelle nomenclature")
        add_btn.clicked.connect(self.create_rule)
        header.addWidget(add_btn)
        print_btn = QPushButton("Imprimer règle")
        print_btn.clicked.connect(self.on_print_rule)
        header.addWidget(print_btn)
        layout.addLayout(header)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Produit", "Quantité sortie", "Actif"])
        layout.addWidget(self.table)

    def refresh_rules(self):
        try:
            session = self.db.get_session()
            rules = session.query(FabricationRule).order_by(FabricationRule.id.desc()).all()
            self.table.setRowCount(len(rules))
            for row, r in enumerate(rules):
                self.table.setItem(row, 0, QTableWidgetItem(str(r.id)))
                prod = session.query(FabricationRule.product.property.mapper.class_).get(r.product_id) if r.product_id else None
                prod_name = prod.name if prod else str(r.product_id)
                self.table.setItem(row, 1, QTableWidgetItem(prod_name))
                self.table.setItem(row, 2, QTableWidgetItem(str(r.output_quantity)))
                self.table.setItem(row, 3, QTableWidgetItem("Oui" if r.is_active else "Non"))
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des nomenclatures: {e}")

    def create_rule(self):
        QMessageBox.information(self, "TODO", "Création de nomenclature — implémentation future")

    def on_print_rule(self):
        sel = self.table.currentRow()
        if sel < 0:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner une règle à imprimer.")
            return
        rule_id_item = self.table.item(sel, 0)
        if not rule_id_item:
            QMessageBox.warning(self, "Erreur", "Impossible de lire l'ID de la règle.")
            return
        rule_id = int(rule_id_item.text())
        path, _ = QFileDialog.getSaveFileName(self, "Enregistrer PDF règle A4", f"nomenclature_{rule_id}.pdf", "PDF Files (*.pdf)")
        if not path:
            return
        ok = export_rule_pdf(rule_id, path, paper='A4')
        if ok:
            QMessageBox.information(self, "Impression", f"Règle exportée: {path}")
        else:
            QMessageBox.critical(self, "Erreur", "Échec export PDF règle")
