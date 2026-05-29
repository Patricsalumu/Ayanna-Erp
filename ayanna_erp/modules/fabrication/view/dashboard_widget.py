from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from ayanna_erp.database.database_manager import DatabaseManager
from sqlalchemy import text

class DashboardWidget(QWidget):
    def __init__(self, pos_id=None, current_user=None):
        super().__init__()
        self.pos_id = pos_id
        self.current_user = current_user
        self.db = DatabaseManager()
        self.setup_ui()
        self.refresh()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.total_label = QLabel("Productions aujourd'hui: -")
        self.yield_label = QLabel("Rendement moyen: -")
        layout.addWidget(self.total_label)
        layout.addWidget(self.yield_label)

    def refresh(self):
        session = self.db.get_session()
        try:
            res = session.execute(text("SELECT COUNT(*) FROM productions WHERE DATE(created_at)=DATE('now')")).fetchone()
            total = res[0] if res else 0
            self.total_label.setText(f"Productions aujourd'hui: {total}")
        except Exception:
            self.total_label.setText("Productions aujourd'hui: -")
        finally:
            session.close()
