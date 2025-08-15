"""
Fenêtre principale du module Salle de Fête pour Ayanna ERP
Gestionnaire des onglets - chaque onglet est maintenant dans son propre fichier
Architecture MVC avec contrôleurs pour la gestion de la base de données
"""

import sys
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTabWidget, QMessageBox, QProgressDialog)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap, QIcon

# Import du contrôleur principal
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from controller.mainWindow_controller import MainWindowController

# Import des différents onglets
from .calendrier_index import CalendrierIndex
from .reservation_index import ReservationIndex
from .client_index import ClientIndex
from .service_index import ServiceIndex
from .produit_index import ProduitIndex
from .paiement_index import PaiementIndex
from .rapport_index import RapportIndex
from .entreSortie_index import EntreeSortieIndex


class SalleFeteWindow(QMainWindow):
    """Fenêtre principale du module Salle de Fête"""
    
    def __init__(self, current_user, pos_id=1):
        super().__init__()
        self.current_user = current_user
        self.pos_id = pos_id
        
        # Initialiser le contrôleur principal
        self.main_controller = MainWindowController(self)
        self.main_controller.set_pos_id(pos_id)
        
        # Connecter les signaux du contrôleur
        self.main_controller.initialization_completed.connect(self.on_initialization_completed)
        self.main_controller.database_ready.connect(self.on_database_ready)
        
        self.setWindowTitle("Ayanna ERP - Salle de Fête")
        self.setMinimumSize(1200, 750)
        
        # Indicateur d'initialisation
        self.is_initialized = False
        self.tabs_created = False

        self.setup_ui()
        
        # Lancer l'initialisation de la base de données
        QTimer.singleShot(500, self.initialize_module)
    
    def initialize_module(self):
        """Initialiser le module Salle de Fête"""
        if not self.is_initialized:
            print("🎪 Lancement de l'initialisation du module...")
            self.main_controller.initialize_module()
    
    def on_initialization_completed(self, success):
        """Callback quand l'initialisation est terminée"""
        self.is_initialized = success
        if success:
            print("✅ Initialisation terminée avec succès")
        else:
            print("❌ Échec de l'initialisation")
            
    def on_database_ready(self):
        """Callback quand la base de données est prête"""
        if not self.tabs_created:
            print("🎯 Base de données prête, création des onglets...")
            self.setup_tabs()
            self.tabs_created = True
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal avec onglets
        main_layout = QVBoxLayout(central_widget)
        
        # Widget à onglets
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
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #E74C3C;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #D5DBDB;
            }
        """)
        
        # Ne pas créer les onglets ici - ils seront créés quand la BDD sera prête
        
        main_layout.addWidget(self.tab_widget)
    
    def setup_tabs(self):
        """Configuration de tous les onglets avec les contrôleurs"""
        
        # Onglet Calendrier / Vue d'ensemble
        self.calendrier_widget = CalendrierIndex(self.main_controller, self.current_user)
        self.tab_widget.addTab(self.calendrier_widget, "📅 Calendrier")
        
        # Onglet Réservations
        self.reservations_widget = ReservationIndex(self.main_controller, self.current_user)
        self.tab_widget.addTab(self.reservations_widget, "📋 Réservations")
        
        # Onglet Clients
        self.clients_widget = ClientIndex(self.main_controller, self.current_user)
        self.tab_widget.addTab(self.clients_widget, "👥 Clients")
        
        # Onglet Services
        self.services_widget = ServiceIndex(self.main_controller, self.current_user)
        self.tab_widget.addTab(self.services_widget, "🔧 Services")
        
        # Onglet Produits
        self.produits_widget = ProduitIndex(self.main_controller, self.current_user)
        self.tab_widget.addTab(self.produits_widget, "📦 Produits")
        
        # Onglet Entrées/Sorties
        self.entree_sortie_widget = EntreeSortieIndex(self.main_controller, self.current_user)
        self.tab_widget.addTab(self.entree_sortie_widget, "📥📤 Entrées/Sorties")
        
        # Onglet Paiements
        self.paiements_widget = PaiementIndex(self.main_controller, self.current_user)
        self.tab_widget.addTab(self.paiements_widget, "💳 Paiements")
        
        # Onglet Rapports
        self.rapports_widget = RapportIndex(self.main_controller, self.current_user)
        self.tab_widget.addTab(self.rapports_widget, "📊 Rapports")
        
        print("✅ Tous les onglets créés avec leurs contrôleurs")
    
    def closeEvent(self, event):
        """Gérer la fermeture de la fenêtre"""
        try:
            # Nettoyer les ressources du contrôleur
            if hasattr(self, 'main_controller'):
                self.main_controller.cleanup()
            print("🧹 Ressources nettoyées")
        except Exception as e:
            print(f"⚠️ Erreur lors du nettoyage: {e}")
        finally:
            event.accept()
