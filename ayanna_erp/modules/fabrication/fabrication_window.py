from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget
from ayanna_erp.modules.fabrication.views.nomenclature_widget import NomenclatureWidget
from ayanna_erp.modules.fabrication.views.production_widget import ProductionWidget
from ayanna_erp.modules.fabrication.views.dashboard_widget import DashboardWidget
from ayanna_erp.modules.fabrication.views.articles_widget import ArticlesWidget


class FabricationWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fabrication")
        self.resize(1100, 700)

        central = QWidget()
        layout = QVBoxLayout(central)
        tabs = QTabWidget()
        tabs.addTab(DashboardWidget(), "Tableau de bord")
        tabs.addTab(NomenclatureWidget(), "Nomenclatures")
        tabs.addTab(ProductionWidget(), "Productions")
        tabs.addTab(ArticlesWidget(), "Articles")
        layout.addWidget(tabs)

        self.setCentralWidget(central)
