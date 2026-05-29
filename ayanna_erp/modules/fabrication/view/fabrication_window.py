from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTabWidget
from .nomenclature_widget import NomenclatureWidget
from .productions_widget import ProductionsWidget
from .dashboard_widget import DashboardWidget

class FabricationWindow(QDialog):
    def __init__(self, current_user, pos_id=None):
        super().__init__()
        self.current_user = current_user
        self.pos_id = pos_id
        self.setWindowTitle("Module Fabrication - Production")
        self.setMinimumSize(1000, 700)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        tabs.addTab(NomenclatureWidget(self.pos_id, self.current_user), "Nomenclatures")
        tabs.addTab(ProductionsWidget(self.pos_id, self.current_user), "Productions")
        tabs.addTab(DashboardWidget(self.pos_id, self.current_user), "Tableau de bord")
        layout.addWidget(tabs)
