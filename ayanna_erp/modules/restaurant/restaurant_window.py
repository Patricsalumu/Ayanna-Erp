"""
Fenêtre du module Restaurant/Bar pour Ayanna ERP
Gestion des salles, tables, commandes et POS
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTabWidget, QTableWidget, QTableWidgetItem, 
                            QPushButton, QLineEdit, QLabel, QComboBox, 
                            QSpinBox, QDoubleSpinBox, QTextEdit, QMessageBox,
                            QGroupBox, QGridLayout, QListWidget, QSplitter,
                            QFrame, QScrollArea, QFormLayout, QCheckBox,
                            QGraphicsView, QGraphicsScene, QGraphicsRectItem,
                            QApplication)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF
from PyQt6.QtGui import QFont, QPixmap, QIcon, QBrush, QPen, QColor
from decimal import Decimal
from datetime import datetime
from ayanna_erp.database.database_manager import get_database_manager
from ayanna_erp.modules.restaurant.views.salle_view import SalleView
from ayanna_erp.modules.restaurant.views.vente_view import VenteView
from ayanna_erp.modules.restaurant.views.commandes_view import CommandesView
from ayanna_erp.modules.restaurant.views.printed_invoices_view import PrintedInvoicesView
from ayanna_erp.modules.restaurant.views.boncommande_widget import BonCommandeWidget
from ayanna_erp.modules.salle_fete.view.entreSortie_index import EntreeSortieIndex
from ayanna_erp.modules.boutique.view.client_index import ClientIndex
from ayanna_erp.modules.boutique.view.commandes_index import CommandesIndexWidget
from ayanna_erp.modules.boutique.view.categorie_index import CategorieIndex
from ayanna_erp.modules.boutique.view.produit_index import ProduitIndex

#import du controlleur principale de la boutique
from ayanna_erp.modules.boutique.controller.boutique_controller import BoutiqueController


class RestaurantWindow(QMainWindow):
    """Fenêtre principale du module Restaurant/Bar"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        # Utiliser l'instance globale de DatabaseManager partagée par l'application
        # POS id pour le module restaurant — utilise l'ID 4 qui mappe normalement à POS_4 (restaurant)
        # Si votre base utilise un autre pos_id pour le restaurant, ajustez cette valeur ou
        # modifiez l'appelant pour transmettre le pos_id correct.
        self.pos_id = 4
        self.db_manager = get_database_manager()
        self.boutique_controller = BoutiqueController(self.pos_id)
        
        self.setWindowTitle("Ayanna ERP - Restaurant/Bar")
        self.setMinimumSize(1200, 650)
        
        self.setup_ui()
    
    def _clear_tabs(self):
        """Supprime proprement les onglets existants pour reconstruire l'interface sans état stale."""
        if not hasattr(self, 'tab_widget') or self.tab_widget is None:
            return
        while self.tab_widget.count() > 0:
            widget = self.tab_widget.widget(0)
            self.tab_widget.removeTab(0)
            if widget is not None:
                widget.deleteLater()

    def setup_ui(self):
        """Configuration de l'interface utilisateur sur une base complètement neuve."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #BDC3C7;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ECF0F1;
                padding: 10px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #28a745;
                color: white;
            }
        """)
        main_layout.addWidget(self.tab_widget)

        if self._get_current_user_role() == 'serveuse':
            self._update_serveuse_label()
            self.setup_pos_tab()
            self.setup_bon_commande_tab()
            self.setup_orders_tab()
            return

        # Onglet POS Restaurant
        self.setup_pos_tab()

        # Onglet Commandes
        self.setup_orders_tab()

        # Onglet Categories
        self.setup_categories_tab()

        # Onglet Produits
        self.setup_produits_tab()

        # Onglet Gestion des salles
        self.setup_halls_tab()

        # Onglet Gestion des tables
        # self.setup_tables_tab()

        # Onglet Bons de Commande
        self.setup_bon_commande_tab()

        # Onglet Clients
        self.setup_clients_tab()

        # Onglet factures imprimees (super admin uniquement)
        if self._get_current_user_role() == 'super_admin':
            self.setup_printed_invoices_tab()

        # Onglet Rapports
        self.setup_caisse_tab()
    
    def _on_serveuse_authenticated(self, user):
        """Reconstruit l'interface après une authentification serveuse sur une fenêtre stable."""
        if user is None:
            return
        self.current_user = user
        try:
            from ayanna_erp.core.session_manager import SessionManager
            SessionManager.set_current_user(user)
        except Exception:
            pass

        try:
            self._clear_tabs()
            self.setup_ui()
            self._update_serveuse_label()
            self.tab_widget.setCurrentIndex(0)
            self.show()
            self.raise_()
            self.activateWindow()
            QTimer.singleShot(0, self._refresh_after_serveuse_login)
            QTimer.singleShot(50, self._refresh_after_serveuse_login)
            QTimer.singleShot(150, self._refresh_after_serveuse_login)
            QApplication.instance().processEvents()
        except Exception:
            pass

    def _refresh_after_serveuse_login(self):
        """Force l'affichage immédiat du plan de vente sur le premier rendu après login."""
        try:
            if self.tab_widget.count() == 0:
                return

            pos_index = None
            pos_widget = None
            for idx in range(self.tab_widget.count()):
                widget = self.tab_widget.widget(idx)
                if isinstance(widget, VenteView):
                    pos_index = idx
                    pos_widget = widget
                    break

            if pos_widget is None:
                return

            self.tab_widget.setCurrentWidget(pos_widget)
            self.tab_widget.setCurrentIndex(pos_index)
            QApplication.instance().processEvents()

            pos_widget.current_user = self.current_user
            try:
                from ayanna_erp.core.session_manager import SessionManager
                SessionManager.set_current_user(self.current_user)
            except Exception:
                pass

            try:
                pos_widget._reload_vente_for_current_user()
                QTimer.singleShot(0, pos_widget._reload_vente_for_current_user)
                QTimer.singleShot(50, pos_widget._reload_vente_for_current_user)
            except Exception:
                pass

            QApplication.instance().processEvents()
            pos_widget.show()
            pos_widget.raise_()
            pos_widget.activateWindow()
        except Exception:
            pass

    def _update_serveuse_label(self):
        user = self.current_user
        if user is None:
            label = "Serveuse: --"
        elif isinstance(user, dict):
            label = f"Serveuse: {user.get('name') or user.get('email') or 'Serveuse'}"
        else:
            label = f"Serveuse: {getattr(user, 'name', None) or getattr(user, 'email', None) or 'Serveuse'}"

        if hasattr(self, 'serveuse_label'):
            self.serveuse_label.setText(label)

    def _logout_from_parent_vente(self):
        """Déconnecte la serveuse depuis le widget parent, puis ouvre le login serveuse."""
        try:
            from ayanna_erp.core.session_manager import SessionManager
            SessionManager.clear_session()
        except Exception:
            pass

        self.current_user = None
        self._update_serveuse_label()
        self.open_serveuse_login()

    def _restore_restaurant_access(self):
        """Réactive la fenêtre restaurant après la fermeture du dialog de login serveuse."""
        try:
            self.setEnabled(True)
            self.show()
            self.raise_()
            self.activateWindow()
        except Exception:
            pass

    def open_serveuse_login(self):
        """Ouvre un login serveuse séparé de la vue de vente actuelle, centré et modal."""
        try:
            from ayanna_erp.modules.restaurant.views.serveuse_login_view import ServeuseLoginView
            self.current_user = None
            self.setEnabled(False)
            login_view = ServeuseLoginView(entreprise_id=1, parent=self)
            login_view.setWindowModality(Qt.WindowModality.ApplicationModal)
            login_view.user_authenticated.connect(self._on_serveuse_authenticated)
            login_view.finished.connect(self._restore_restaurant_access)
            login_view.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
            login_view.show()
            login_view.raise_()
            login_view.activateWindow()
            screen = self.screen().availableGeometry()
            login_rect = login_view.frameGeometry()
            login_rect.moveCenter(screen.center())
            login_view.move(login_rect.topLeft())
        except Exception:
            self.setEnabled(True)
            pass

    def setup_pos_tab(self):
        """Configuration de l'onglet POS en réutilisant la vue du module (VenteView)"""
        pos_view = VenteView(entreprise_id=1, current_user=self.current_user, parent=self)
        self.tab_widget.addTab(pos_view, "🍽️ Point de Vente")
        self.tab_widget.setCurrentWidget(pos_view)

        try:
            pos_view.current_user = self.current_user
            try:
                from ayanna_erp.core.session_manager import SessionManager
                SessionManager.set_current_user(self.current_user)
            except Exception:
                pass
            pos_view._initial_load_for_current_user()
            pos_view.show_plan_view()
        except Exception:
            pass

        try:
            def on_tab_changed(index):
                widget = self.tab_widget.widget(index)
                if isinstance(widget, VenteView):
                    try:
                        widget.current_user = self.current_user
                        widget._reload_vente_for_current_user()
                    except Exception:
                        pass
            self.tab_widget.currentChanged.connect(on_tab_changed)
        except Exception:
            pass
    
    def setup_halls_tab(self):
        """Onglet Salles — utiliser la vue de gestion des salles (SalleView)"""
        salle_view = SalleView(entreprise_id=1, parent=self)
        self.tab_widget.addTab(salle_view, "🏢 Salles")
    
    def setup_tables_tab(self):
        """Onglet Tables — réutilise `SalleView` (plan et édition des tables)"""
        tables_view = SalleView(entreprise_id=1, parent=self)
        self.tab_widget.addTab(tables_view, "🪑 Tables")
    
    def setup_categories_tab(self):
        """Configuration de l'onglet Menu"""
        categorie_widget = CategorieIndex(self.pos_id, self.current_user)
        self.tab_widget.addTab(categorie_widget, "📂 Categories")
        
    def setup_produits_tab(self):
        """Configuration de l'onglet Paiements"""
        # Instancier le widget produits en mode 'restaurant' pour afficher le stock et
        # les statistiques liées au POS restaurant (entrepôt POS_4)
        produit_widget = ProduitIndex(self.pos_id, self.current_user, module='restaurant')
        self.tab_widget.addTab(produit_widget, "📦 Produits")
    
    def setup_orders_tab(self):
        """Onglet Commandes — utiliser la vue de commandes du module"""
        commandes_view = CommandesIndexWidget(self.boutique_controller, self.current_user, module='restaurant')
        self.tab_widget.addTab(commandes_view, "📝 Commandes")
    
    def setup_clients_tab(self):
        """Configuration de l'onglet Clients"""
        clients_widget = ClientIndex(self.boutique_controller, self.current_user)
        self.tab_widget.addTab(clients_widget, "👥 Clients")    

    def setup_printed_invoices_tab(self):
        """Configuration de l'onglet Factures imprimees (super admin)."""
        printed_view = PrintedInvoicesView(entreprise_id=1, current_user=self.current_user, parent=self)
        self.tab_widget.addTab(printed_view, "🧾 Factures imprimees")

    def setup_bon_commande_tab(self):
        """Configuration de l'onglet Bons de Commande."""
        bon_commande_view = BonCommandeWidget(entreprise_id=1, current_user=self.current_user, parent=self)
        self.tab_widget.addTab(bon_commande_view, "🍳 Bons de Commande")

    def _get_current_user_role(self):
        user = self.current_user
        if user is None:
            return ''
        if isinstance(user, dict):
            return str(user.get('role', '') or '').lower()
        return str(getattr(user, 'role', '') or '').lower()
    
    def setup_caisse_tab(self):
        """Configuration de l'onglet caisse"""

        caisses_view = EntreeSortieIndex(self.boutique_controller, 1) #TODO A implementer
        self.tab_widget.addTab(caisses_view, "📊 Caisse")
    
    def closeEvent(self, event):
        """Gérer la fermeture de la fenêtre pour la serveuse avec confirmation explicite."""
        if self._get_current_user_role() == 'serveuse':
            reply = QMessageBox.question(
                self,
                "Quitter le module restaurant",
                "Voulez-vous vraiment quitter le module restaurant ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return

            try:
                from ayanna_erp.core.session_manager import SessionManager
                SessionManager.clear_session()
            except Exception:
                pass

            self.current_user = None
            self._update_serveuse_label()
            self.db_manager.close_session()
            event.accept()
            return

        self.db_manager.close_session()
        event.accept()
