"""
Widget principal de gestion du stock - Architecture modulaire
Ce widget remplace l'ancien stock_management_widget.py monolithique
"""

from typing import List, Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QPushButton, 
    QFrame, QMessageBox, QSplitter, QGroupBox, QGridLayout, QProgressBar,
    QApplication, QSystemTrayIcon, QMenu, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QIcon

from ayanna_erp.database.database_manager import DatabaseManager

# Import des widgets modulaires
from ayanna_erp.modules.stock.views.entrepot_widget import EntrepotWidget
from ayanna_erp.modules.stock.views.stock_widget import StockWidget
from ayanna_erp.modules.stock.views.transfert_widget import TransfertWidget
from ayanna_erp.modules.stock.views.alerte_widget import AlerteWidget
from ayanna_erp.modules.stock.views.inventaire_widget import InventaireWidget
from ayanna_erp.modules.stock.views.rapport_widget import RapportWidget

# Import des contrôleurs pour les statistiques globales
from ayanna_erp.modules.stock.controllers.stock_controller import StockController
from ayanna_erp.modules.stock.controllers.alerte_controller import AlerteController


class ModularStockManagementWidget(QWidget):
    """
    Widget principal de gestion du stock avec architecture modulaire
    Remplace l'ancien stock_management_widget.py monolithique
    """
    
    # Signaux pour la communication avec l'application principale
    stock_updated = pyqtSignal()
    alert_generated = pyqtSignal(str, str)  # Type, message
    navigation_requested = pyqtSignal(str)  # Module de destination
    
    def __init__(self, pos_id: int, current_user: dict = None):
        super().__init__()
        self.pos_id = pos_id
        self.current_user = current_user or {"id": 1, "name": "Utilisateur"}
        self.db_manager = DatabaseManager()
        
        # Widgets modulaires
        self.entrepot_widget = None
        self.stock_widget = None
        self.transfert_widget = None
        self.alerte_widget = None
        self.inventaire_widget = None
        self.rapport_widget = None
        # Dashboard supprimé selon la demande utilisateur
        
        self.setup_ui()
        self.load_modules()
        self.connect_signals()
        
        # Notification système (optionnel)
        self.setup_system_notifications()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur avec système de scroll"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Widget de contenu scrollable
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)
        
        # Zone de scroll
        scroll_area = QScrollArea()
        scroll_area.setWidget(content_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #E9ECEF;
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #6C757D;
                border-radius: 6px;
                min-height: 30px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #495057;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar:horizontal {
                background-color: #E9ECEF;
                height: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background-color: #6C757D;
                border-radius: 6px;
                min-width: 30px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #495057;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
                width: 0px;
            }
        """)
        
        # Ajouter le scroll au layout principal
        main_layout.addWidget(scroll_area)
        
        # Onglets des modules uniquement (sans dashboard ni en-tête)
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setMovable(True)  # Onglets réorganisables
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #C0C0C0;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #E0E0E0;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #3498DB;
                color: white;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #BDC3C7;
            }
        """)
        
        content_layout.addWidget(self.tab_widget)
    
    def load_modules(self):
        """Charger tous les widgets modulaires"""
        try:
            # Onglet 1: Entrepôts
            self.entrepot_widget = EntrepotWidget(self.pos_id, self.current_user)
            self.tab_widget.addTab(self.entrepot_widget, "🏪 Entrepôts")
            
            # Onglet 2: Stocks
            self.stock_widget = StockWidget(self.pos_id, self.current_user)
            self.tab_widget.addTab(self.stock_widget, "📦 Stocks")
            
            # Onglet 3: Transferts
            self.transfert_widget = TransfertWidget(self.pos_id, self.current_user)
            self.tab_widget.addTab(self.transfert_widget, "🔄 Transferts")
            
            # Onglet 4: Alertes
            self.alerte_widget = AlerteWidget(self.pos_id, self.current_user)
            self.tab_widget.addTab(self.alerte_widget, "🚨 Alertes")
            
            # Onglet 5: Inventaires
            self.inventaire_widget = InventaireWidget(self.pos_id, self.current_user)
            self.tab_widget.addTab(self.inventaire_widget, "📋 Inventaires")
            
            # Onglet 6: Rapports
            self.rapport_widget = RapportWidget(self.pos_id, self.current_user)
            self.tab_widget.addTab(self.rapport_widget, "📊 Rapports")
            
            self.update_status("✅ Tous les modules chargés avec succès")
            
        except Exception as e:
            self.update_status(f"❌ Erreur lors du chargement des modules: {str(e)}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des modules:\n{str(e)}")
    
    def connect_signals(self):
        """Connecter les signaux entre les widgets"""
        try:
            # Signaux des entrepôts
            if self.entrepot_widget:
                self.entrepot_widget.warehouse_created.connect(self.on_warehouse_updated)
                self.entrepot_widget.warehouse_updated.connect(self.on_warehouse_updated)
            
            # Signaux des stocks
            if self.stock_widget:
                self.stock_widget.stock_updated.connect(self.on_stock_updated)
            
            # Signaux des transferts
            if self.transfert_widget:
                self.transfert_widget.transfer_created.connect(self.on_transfer_created)
                self.transfert_widget.transfer_updated.connect(self.on_transfer_updated)
            
            # Signaux des alertes
            if self.alerte_widget:
                self.alerte_widget.alert_configured.connect(self.on_alert_configured)
                self.alerte_widget.stock_action_needed.connect(self.on_stock_action_needed)
            
            # Signaux des inventaires
            if self.inventaire_widget:
                self.inventaire_widget.inventory_created.connect(self.on_inventory_created)
                self.inventaire_widget.inventory_completed.connect(self.on_inventory_completed)
            
            # Signaux des rapports
            if self.rapport_widget:
                self.rapport_widget.report_generated.connect(self.on_report_generated)
            
        except Exception as e:
            print(f"Erreur lors de la connexion des signaux: {e}")
    
    def setup_system_notifications(self):
        """Configurer les notifications système"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setToolTip("Ayanna ERP - Gestion Stock")
            
            # Menu du tray
            tray_menu = QMenu()
            show_action = tray_menu.addAction("Afficher")
            show_action.triggered.connect(self.show)
            
            tray_menu.addSeparator()
            quit_action = tray_menu.addAction("Quitter")
            quit_action.triggered.connect(QApplication.quit)
            
            self.tray_icon.setContextMenu(tray_menu)
    
    # Méthodes de navigation rapide
    def switch_to_warehouses(self):
        """Basculer vers l'onglet entrepôts"""
        self.tab_widget.setCurrentIndex(0)
    
    def switch_to_stocks(self):
        """Basculer vers l'onglet stocks"""
        self.tab_widget.setCurrentIndex(1)
    
    def switch_to_transfers(self):
        """Basculer vers l'onglet transferts"""
        self.tab_widget.setCurrentIndex(2)
    
    def switch_to_alerts(self):
        """Basculer vers l'onglet alertes"""
        self.tab_widget.setCurrentIndex(3)
    
    def switch_to_inventory(self):
        """Basculer vers l'onglet inventaires"""
        self.tab_widget.setCurrentIndex(4)
    
    def switch_to_reports(self):
        """Basculer vers l'onglet rapports"""
        self.tab_widget.setCurrentIndex(5)
    
    # Gestionnaires de signaux (dashboard supprimé)
    def on_warehouse_updated(self):
        """Quand un entrepôt est créé ou mis à jour"""
        self.stock_updated.emit()
        self.update_status("🏪 Entrepôt mis à jour")
    
    def on_stock_updated(self):
        """Quand le stock est mis à jour"""
        self.stock_updated.emit()
        self.update_status("📦 Stock mis à jour")
    
    def on_transfer_created(self):
        """Quand un transfert est créé"""
        self.update_status("🔄 Nouveau transfert créé")
        self.alert_generated.emit("INFO", "Nouveau transfert créé")
    
    def on_transfer_updated(self):
        """Quand un transfert est mis à jour"""
        self.update_status("🔄 Transfert mis à jour")
    
    def on_alert_configured(self):
        """Quand une alerte est configurée"""
        self.update_status("🚨 Configuration d'alerte mise à jour")
    
    def on_stock_action_needed(self, product_id: int, action: str):
        """Quand une action de stock est nécessaire"""
        self.alert_generated.emit("WARNING", f"Action nécessaire pour le produit {product_id}: {action}")
        
        # Optionally, switch to the appropriate tab
        if action == "restock_needed":
            self.switch_to_transfers()
    
    def on_inventory_created(self):
        """Quand un inventaire est créé"""
        self.update_status("📋 Nouvel inventaire créé")
    
    def on_inventory_completed(self):
        """Quand un inventaire est terminé"""
        self.stock_updated.emit()
        self.update_status("📋 Inventaire terminé - Stock mis à jour")
        self.alert_generated.emit("SUCCESS", "Inventaire terminé avec succès")
    
    def on_report_generated(self, report_data: dict):
        """Quand un rapport est généré"""
        report_type = report_data.get('type', 'Rapport')
        self.update_status(f"📊 Rapport {report_type} généré")
        self.alert_generated.emit("INFO", f"Rapport {report_type} généré avec succès")
    
    # Actions globales (dashboard supprimé)
    def sync_all_data(self):
        """Synchroniser toutes les données"""
        try:
            self.update_status("🔄 Synchronisation en cours...")
            
            # Actualiser tous les widgets
            widgets = [
                self.entrepot_widget,
                self.stock_widget,
                self.transfert_widget,
                self.alerte_widget,
                self.inventaire_widget,
                self.rapport_widget
            ]
            
            for widget in widgets:
                if widget and hasattr(widget, 'load_data'):
                    widget.load_data()
            
            self.stock_updated.emit()
            self.update_status("✅ Synchronisation terminée")
            self.alert_generated.emit("SUCCESS", "Synchronisation de toutes les données terminée")
            
        except Exception as e:
            self.update_status(f"❌ Erreur de synchronisation: {str(e)}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la synchronisation:\n{str(e)}")
    
    def export_global_data(self):
        """Exporter toutes les données de stock"""
        try:
            # Basculer vers l'onglet rapports pour l'export
            self.switch_to_reports()
            self.update_status("📤 Redirection vers les rapports pour export global")
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export global:\n{str(e)}")
    
    def open_global_settings(self):
        """Ouvrir les paramètres globaux du module stock"""
        QMessageBox.information(
            self, "Paramètres",
            "Interface de paramètres globaux à implémenter.\n\n"
            "Fonctionnalités prévues:\n"
            "• Configuration des seuils par défaut\n"
            "• Paramètres de notification\n"
            "• Règles de valorisation\n"
            "• Préférences d'affichage\n"
            "• Sauvegarde/Restauration"
        )
    
    def update_status(self, message: str):
        """Mettre à jour le message de statut (mode console)"""
        print(f"📢 Stock Module: {message}")
        # Note: La barre de statut a été supprimée selon la demande utilisateur
    
    def check_database_connection(self):
        """Vérifier la connexion à la base de données"""
        try:
            with self.db_manager.get_session() as session:
                # Test simple de connexion
                session.execute("SELECT 1")
                print("🔗 Base de données connectée")
                return True
                
        except Exception as e:
            print("❌ Erreur de connexion DB")
            return False
    
    def get_module_status(self):
        """Obtenir le statut de tous les modules"""
        status = {
            'entrepots': self.entrepot_widget is not None,
            'stocks': self.stock_widget is not None,
            'transferts': self.transfert_widget is not None,
            'alertes': self.alerte_widget is not None,
            'inventaires': self.inventaire_widget is not None,
            'rapports': self.rapport_widget is not None,
            # Dashboard supprimé selon la demande utilisateur
            'database': self.check_database_connection()
        }
        
        return status
    
    def refresh_all(self):
        """Actualiser tous les modules"""
        self.sync_all_data()
    
    def showEvent(self, event):
        """Quand le widget devient visible"""
        super().showEvent(event)
        
        # Vérifier la connexion DB
        self.check_database_connection()
        
        # Dashboard supprimé - plus d'actualisation nécessaire


# Alias pour maintenir la compatibilité avec l'ancien nom
StockManagementWidget = ModularStockManagementWidget