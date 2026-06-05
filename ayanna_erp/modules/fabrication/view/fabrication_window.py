from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget
from ..views.nomenclature_widget import NomenclatureWidget
from ..views.productions_widget import ProductionsWidget
from ..views.dashboard_widget import DashboardWidget
from ..views.articles_widget import ArticlesWidget


class FabricationWindow(QMainWindow):
    def __init__(self, current_user, pos_id=None):
        super().__init__()
        self.current_user = current_user
        self.pos_id = pos_id
        self.setWindowTitle("Module Fabrication - Production")
        self.setMinimumSize(1000, 700)
        self.setup_ui()

    def setup_ui(self):
        central = QWidget()
        layout = QVBoxLayout(central)
        tabs = QTabWidget()
        # Dashboard en premier onglet
        tabs.addTab(DashboardWidget(self.pos_id, self.current_user), "Tableau de bord")
        tabs.addTab(ArticlesWidget(self.pos_id, self.current_user), "Articles")
        tabs.addTab(NomenclatureWidget(self.pos_id, self.current_user), "Nomenclatures")
        tabs.addTab(ProductionsWidget(self.pos_id, self.current_user), "Productions")
        # Appliquer un thème de couleur pour le module
        tabs.setStyleSheet("QTabBar::tab { height: 28px; padding: 6px 12px; } QTabWidget::pane { border-top: 2px solid #2C3E50; }")
        central.setStyleSheet("background-color: #F7FBFF;")
        layout.addWidget(tabs)
        self.setCentralWidget(central)
