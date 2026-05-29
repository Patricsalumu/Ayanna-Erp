from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.fabrication.models import Production

class DashboardWidget(QWidget):
    def __init__(self, pos_id=None, current_user=None, parent=None):
        super().__init__(parent)
        self.pos_id = pos_id
        self.current_user = current_user
        self.db = DatabaseManager()
        self.setup_ui()
        self.refresh()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.title = QLabel("Tableau de bord Fabrication")
        layout.addWidget(self.title)
        self.kpi_label = QLabel("")
        layout.addWidget(self.kpi_label)

    def refresh(self):
        try:
            session = self.db.get_session()
            today = session.query(Production).filter(Production.status == 'completed').count()
            ongoing = session.query(Production).filter(Production.status == 'in_progress').count()
            self.kpi_label.setText(f"Productions aujourd'hui: {today} — En cours: {ongoing}")
        except Exception as e:
            self.kpi_label.setText(f"Erreur chargement KPIs: {e}")
