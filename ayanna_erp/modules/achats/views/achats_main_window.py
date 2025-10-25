"""
Fenêtre principale du module Achats
Interface complète pour la gestion des achats, fournisseurs et commandes
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QFrame, QPushButton, QSplitter, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.achats.controllers import AchatController

from .fournisseurs_widget import FournisseursWidget
from .commandes_widget import CommandesWidget
from .nouvelle_commande_widget import NouvelleCommandeWidget
from .dashboard_achats_widget import DashboardAchatsWidget


class AchatsMainWindow(QMainWindow):
    """Fenêtre principale du module Achats"""
    
    # Signaux pour la communication entre onglets
    commande_created = pyqtSignal(int)  # ID de la commande créée
    commande_updated = pyqtSignal(int)  # ID de la commande mise à jour
    fournisseur_created = pyqtSignal(int)  # ID du fournisseur créé
    
    def __init__(self, current_user, pos_id=1):
        super().__init__()
        self.current_user = current_user
        self.pos_id = pos_id
        
        self.db_manager = DatabaseManager()
        self.achat_controller = AchatController(pos_id=pos_id)
        
        self.setWindowTitle("Ayanna ERP - Module Achats")
        self.setMinimumSize(1200, 700)
        
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Header
        header_frame = self.create_header()
        main_layout.addWidget(header_frame)
        
        # Onglets principaux
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setDocumentMode(True)
        
        # Créer les onglets
        self.create_tabs()
        
        main_layout.addWidget(self.tab_widget)
    
    def create_header(self) -> QFrame:
        """Crée l'en-tête de la fenêtre"""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #2C3E50;
                border-radius: 5px;
                color: white;
            }
            QLabel {
                color: white;
                font-weight: bold;
            }
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        # Titre
        title_label = QLabel("📦 Module Achats")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        # Description
        desc_label = QLabel("Gestion des fournisseurs, commandes et approvisionnements")
        desc_label.setStyleSheet("color: #BDC3C7; font-size: 12px;")
        
        # Boutons d'action rapide
        quick_actions_layout = QHBoxLayout()
        
        new_order_btn = QPushButton("➕ Nouvelle Commande")
        new_order_btn.clicked.connect(self.on_nouvelle_commande_clicked)
        
        new_supplier_btn = QPushButton("👥 Nouveau Fournisseur")
        new_supplier_btn.clicked.connect(self.on_nouveau_fournisseur_clicked)
        
        quick_actions_layout.addWidget(new_order_btn)
        quick_actions_layout.addWidget(new_supplier_btn)
        
        # Layout de l'en-tête
        left_layout = QVBoxLayout()
        left_layout.addWidget(title_label)
        left_layout.addWidget(desc_label)
        
        header_layout.addLayout(left_layout)
        header_layout.addStretch()
        header_layout.addLayout(quick_actions_layout)
        
        return header_frame
    
    def create_tabs(self):
        """Crée tous les onglets du module"""
        # Onglet Dashboard
        self.dashboard_widget = DashboardAchatsWidget(self.achat_controller)
        self.tab_widget.addTab(self.dashboard_widget, "📊 Dashboard")
        
        # Onglet Commandes
        self.commandes_widget = CommandesWidget(self.achat_controller)
        self.tab_widget.addTab(self.commandes_widget, "📋 Commandes")
        
        # Onglet Nouvelle Commande
        self.nouvelle_commande_widget = NouvelleCommandeWidget(self.achat_controller)
        self.tab_widget.addTab(self.nouvelle_commande_widget, "➕ Nouvelle Commande")
        
        # Onglet Fournisseurs
        self.fournisseurs_widget = FournisseursWidget(self.achat_controller)
        self.tab_widget.addTab(self.fournisseurs_widget, "👥 Fournisseurs")
        
        # Définir l'onglet par défaut
        self.tab_widget.setCurrentIndex(0)
    
    def connect_signals(self):
        """Connecte les signaux entre les widgets"""
        # Signaux commandes
        self.nouvelle_commande_widget.commande_created.connect(self.on_commande_created)
        self.commandes_widget.commande_updated.connect(self.on_commande_updated)
        
        # Signaux fournisseurs
        self.fournisseurs_widget.fournisseur_created.connect(self.on_fournisseur_created)
        
        # Signaux de navigation
        self.commande_created.connect(self.dashboard_widget.refresh_data)
        self.commande_created.connect(self.commandes_widget.refresh_data)
        
        self.fournisseur_created.connect(self.nouvelle_commande_widget.refresh_fournisseurs)
    
    def on_nouvelle_commande_clicked(self):
        """Naviguer vers l'onglet nouvelle commande"""
        self.tab_widget.setCurrentWidget(self.nouvelle_commande_widget)
        self.nouvelle_commande_widget.focus_form()
    
    def on_nouveau_fournisseur_clicked(self):
        """Naviguer vers l'onglet fournisseurs"""
        self.tab_widget.setCurrentWidget(self.fournisseurs_widget)
        self.fournisseurs_widget.show_new_form()
    
    def on_commande_created(self, commande_id: int):
        """Callback quand une commande est créée"""
        self.commande_created.emit(commande_id)
        
        # Afficher un message de succès
        QMessageBox.information(
            self,
            "Commande créée",
            f"La commande a été créée avec succès.\nID: {commande_id}"
        )
        
        # Naviguer vers l'onglet commandes
        self.tab_widget.setCurrentWidget(self.commandes_widget)
    
    def on_commande_updated(self, commande_id: int):
        """Callback quand une commande est mise à jour"""
        self.commande_updated.emit(commande_id)
        self.dashboard_widget.refresh_data()
    
    def on_fournisseur_created(self, fournisseur_id: int):
        """Callback quand un fournisseur est créé"""
        self.fournisseur_created.emit(fournisseur_id)
        
        # Afficher un message de succès
        QMessageBox.information(
            self,
            "Fournisseur créé",
            f"Le fournisseur a été créé avec succès.\nID: {fournisseur_id}"
        )
    
    def closeEvent(self, event):
        """Fermeture de la fenêtre"""
        try:
            self.db_manager.close_session()
        except:
            pass
        event.accept()


# Alias pour compatibilité avec le système existant
AchatsWindow = AchatsMainWindow