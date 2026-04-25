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
from ayanna_erp.modules.salle_fete.view.entreSortie_index import EntreeSortieIndex

log = logging.getLogger(__name__)


def _get_hotel_pos_id() -> int:
    """Retourne l'ID du POS Hôtel (ou 1 en fallback)."""
    try:
        from ayanna_erp.database.database_manager import POSPoint, Module
        from ayanna_erp.core.session_manager import SessionManager
        db = get_database_manager()
        eid = SessionManager.get_current_enterprise_id() or 1
        with db.session_scope() as session:
            row = (
                session.query(POSPoint)
                .join(Module, POSPoint.module_id == Module.id)
                .filter(
                    POSPoint.enterprise_id == eid,
                    Module.name.ilike('%hotel%'),
                )
                .first()
            )
            return row.id if row else 1
    except Exception:
        return 1


class _HotelPosWrapper:
    """Wrapper minimal pour passer le pos_id hôtel à EntreeSortieIndex."""
    def __init__(self, pos_id: int):
        self.pos_id = pos_id


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

    # Migration : ajout des colonnes pays et carte_identite sur shop_clients si absentes
    try:
        db2 = get_database_manager()
        engine2 = db2.engine
        with engine2.connect() as conn:
            for col_def in [
                "ALTER TABLE shop_clients ADD COLUMN pays TEXT",
                "ALTER TABLE shop_clients ADD COLUMN carte_identite TEXT",
            ]:
                try:
                    conn.execute(text(col_def))
                    conn.commit()
                except Exception:
                    pass   # Colonne déjà existante
    except Exception as e:
        log.warning(f"Migration pays/carte_identite ignorée : {e}")

    # Migration : ajout de la colonne reference sur hotel_payments si absente
    try:
        db3 = get_database_manager()
        with db3.engine.connect() as conn:
            try:
                conn.execute(text(
                    "ALTER TABLE hotel_payments ADD COLUMN reference TEXT"
                ))
                conn.commit()
                log.info("Colonne 'reference' ajoutée à hotel_payments.")
            except Exception:
                pass  # Colonne déjà existante
    except Exception as e:
        log.warning(f"Migration reference hotel_payments ignorée : {e}")

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
        self.caisse_tab        = EntreeSortieIndex(
            _HotelPosWrapper(_get_hotel_pos_id()), self.current_user)
        self.paiements_tab     = CaisseView()

        self.tabs.addTab(self.dashboard_tab,    "🏨  Tableau de bord")
        self.tabs.addTab(self.reservations_tab, "📋  Réservations")
        self.tabs.addTab(self.paiements_tab,    "💰  Paiements")
        self.tabs.addTab(self.categories_tab,   "🏷️  Catégories")
        self.tabs.addTab(self.rooms_tab,        "🛏️  Chambres")
        self.tabs.addTab(self.caisse_tab,       "📥📤 Caisse")

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
