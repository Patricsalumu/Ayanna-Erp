from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from ayanna_erp.modules.fabrication.views.nomenclature_widget import NomenclatureWidget
from ayanna_erp.modules.fabrication.views.production_widget import ProductionWidget
from ayanna_erp.modules.fabrication.views.dashboard_widget import DashboardWidget

class FabricationWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fabrication")
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        tabs.addTab(DashboardWidget(), "Tableau de bord")
        tabs.addTab(NomenclatureWidget(), "Nomenclatures")
        tabs.addTab(ProductionWidget(), "Productions")
        layout.addWidget(tabs)
