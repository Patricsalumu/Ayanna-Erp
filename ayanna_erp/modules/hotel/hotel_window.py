"""
HotelWindow – fenêtre principale du module Hôtel pour Ayanna ERP.
Point d'entrée unique qui initialise les tables, charge les vues
et gère la navigation par onglets.
"""
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, QLabel, QStatusBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ayanna_erp.database.database_manager import get_database_manager
from ayanna_erp.modules.hotel.views.hotel_dashboard  import HotelDashboard
from ayanna_erp.modules.hotel.views.reservation_view import ReservationView
from ayanna_erp.modules.hotel.views.category_view    import CategoryView
from ayanna_erp.modules.hotel.views.room_view        import RoomView
from ayanna_erp.modules.hotel.views.caisse_view      import CaisseView

log = logging.getLogger(__name__)


def _ensure_tables():
    """Crée les tables du module hôtel si elles n'existent pas encore."""
    import os
    from sqlalchemy import text

    sql_file = os.path.join(
        os.path.dirname(__file__), 'migrations', 'create_tables.sql')

    try:
        db = get_database_manager()
        with open(sql_file, encoding='utf-8') as f:
            sql = f.read()

        engine = db.engine
        # Exécuter chaque instruction séparément
        with engine.connect() as conn:
            for stmt in sql.split(';'):
                stmt = stmt.strip()
                if stmt:
                    conn.execute(text(stmt))
            conn.commit()
        log.info("Tables hôtel vérifiées / créées.")
    except Exception as e:
        log.exception(f"Erreur création tables hôtel : {e}")

    # Enregistrer les modèles ORM dans la métadonnée SQLAlchemy
    try:
        from ayanna_erp.modules.hotel.models.model import (
            HotelCategory, HotelRoom, HotelReservation, HotelPayment
        )
        from ayanna_erp.database.base import Base
        Base.metadata.create_all(get_database_manager().engine, checkfirst=True)
    except Exception as e:
        log.exception(f"Erreur ORM create_all hôtel : {e}")


class HotelWindow(QMainWindow):
    """Fenêtre principale du module Hôtel."""

    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self.setWindowTitle("Ayanna ERP – Module Hôtel")
        self.setMinimumSize(1200, 700)

        _ensure_tables()
        self._setup_ui()

    # ------------------------------------------------------------------
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ---- Barre de titre ----
        header = QLabel("  🏨  Module Hôtel")
        header.setFixedHeight(46)
        header.setStyleSheet(
            "background:#2C3E50;color:white;font-size:16px;font-weight:bold;"
            "padding-left:12px;")
        layout.addWidget(header)

        # ---- Onglets ----
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane   { border:none; background:#F5F6FA; }
            QTabBar::tab       { padding:10px 20px; font-size:13px;
                                 min-width:120px; }
            QTabBar::tab:selected   { background:#1976D2; color:white;
                                      font-weight:bold; border-radius:4px 4px 0 0; }
            QTabBar::tab:!selected  { background:#ECF0F1; color:#555; }
        """)

        self.dashboard_tab     = HotelDashboard(self.current_user)
        self.reservations_tab  = ReservationView(self.current_user)
        self.categories_tab    = CategoryView()
        self.rooms_tab         = RoomView()
        self.caisse_tab        = CaisseView()

        self.tabs.addTab(self.dashboard_tab,    "🏨  Tableau de bord")
        self.tabs.addTab(self.reservations_tab, "📋  Réservations")
        self.tabs.addTab(self.categories_tab,   "🏷️  Catégories")
        self.tabs.addTab(self.rooms_tab,        "🛏️  Chambres")
        self.tabs.addTab(self.caisse_tab,       "💰  Caisse")

        # Rafraîchir les onglets concernés quand on les affiche
        self.tabs.currentChanged.connect(self._on_tab_changed)

        layout.addWidget(self.tabs)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Module Hôtel chargé.")

    def _on_tab_changed(self, index):
        tab = self.tabs.widget(index)
        if hasattr(tab, 'refresh'):
            try:
                tab.refresh()
            except Exception as e:
                log.error(f"Erreur refresh onglet hôtel : {e}")
