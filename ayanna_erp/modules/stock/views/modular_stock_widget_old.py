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


class StockDashboard(QFrame):
    """Dashboard avec indicateurs de performance du stock"""
    
    def __init__(self, pos_id: int, current_user):
        super().__init__()
        self.pos_id = pos_id
        self.current_user = current_user
        self.stock_controller = StockController(pos_id)
        self.alerte_controller = AlerteController(pos_id)
        self.db_manager = DatabaseManager()
        
        self.setup_ui()
        self.load_dashboard_data()
        
        # Timer pour actualisation automatique
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_dashboard_data)
        self.refresh_timer.start(60000)  # 1 minute
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 15px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Titre du dashboard
        title_layout = QHBoxLayout()
        
        title_label = QLabel("📊 Tableau de Bord Stock")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white; margin-bottom: 10px;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # Dernière mise à jour
        self.last_update_label = QLabel("Dernière MAJ: --:--")
        self.last_update_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 12px;")
        title_layout.addWidget(self.last_update_label)
        
        layout.addLayout(title_layout)
        
        # Indicateurs principaux
        indicators_layout = QGridLayout()
        
        # Indicateur 1: Valeur totale du stock
        self.total_value_indicator = self.create_indicator(
            "💰", "Valeur Totale", "0,00 €", "#27ae60"
        )
        indicators_layout.addWidget(self.total_value_indicator, 0, 0)
        
        # Indicateur 2: Alertes critiques
        self.critical_alerts_indicator = self.create_indicator(
            "🚨", "Alertes Critiques", "0", "#e74c3c"
        )
        indicators_layout.addWidget(self.critical_alerts_indicator, 0, 1)
        
        # Indicateur 3: Produits en stock
        self.products_count_indicator = self.create_indicator(
            "📦", "Produits en Stock", "0", "#3498db"
        )
        indicators_layout.addWidget(self.products_count_indicator, 0, 2)
        
        # Indicateur 4: Transferts en cours
        self.transfers_indicator = self.create_indicator(
            "🔄", "Transferts Actifs", "0", "#f39c12"
        )
        indicators_layout.addWidget(self.transfers_indicator, 1, 0)
        
        # Indicateur 5: Entrepôts actifs
        self.warehouses_indicator = self.create_indicator(
            "🏪", "Entrepôts Actifs", "0", "#9b59b6"
        )
        indicators_layout.addWidget(self.warehouses_indicator, 1, 1)
        
        # Indicateur 6: Mouvements aujourd'hui
        self.movements_today_indicator = self.create_indicator(
            "📈", "Mouvements/Jour", "0", "#1abc9c"
        )
        indicators_layout.addWidget(self.movements_today_indicator, 1, 2)
        
        layout.addLayout(indicators_layout)
        
        # Actions rapides
        quick_actions_layout = QHBoxLayout()
        
        quick_transfer_btn = QPushButton("⚡ Transfert Rapide")
        quick_transfer_btn.setStyleSheet(self.get_button_style("#3498db"))
        quick_transfer_btn.clicked.connect(self.quick_transfer)
        quick_actions_layout.addWidget(quick_transfer_btn)
        
        quick_inventory_btn = QPushButton("📋 Correction Stock")
        quick_inventory_btn.setStyleSheet(self.get_button_style("#27ae60"))
        quick_inventory_btn.clicked.connect(self.quick_inventory_correction)
        quick_actions_layout.addWidget(quick_inventory_btn)
        
        view_alerts_btn = QPushButton("🚨 Voir Alertes")
        view_alerts_btn.setStyleSheet(self.get_button_style("#e74c3c"))
        view_alerts_btn.clicked.connect(self.view_critical_alerts)
        quick_actions_layout.addWidget(view_alerts_btn)
        
        quick_actions_layout.addStretch()
        layout.addLayout(quick_actions_layout)
    
    def create_indicator(self, icon: str, label: str, value: str, color: str) -> QFrame:
        """Créer un indicateur du dashboard"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.15);
                border-radius: 10px;
                padding: 15px;
                margin: 5px;
            }}
        """)
        
        layout = QVBoxLayout(frame)
        
        # Ligne du haut: icône et valeur
        top_layout = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 24))
        icon_label.setStyleSheet("color: white;")
        top_layout.addWidget(icon_label)
        
        top_layout.addStretch()
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        value_label.setObjectName(f"{label.replace(' ', '_').lower()}_value")
        top_layout.addWidget(value_label)
        
        layout.addLayout(top_layout)
        
        # Label descriptif
        desc_label = QLabel(label)
        desc_label.setFont(QFont("Arial", 12))
        desc_label.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        layout.addWidget(desc_label)
        
        return frame
    
    def get_button_style(self, color: str) -> str:
        """Style pour les boutons d'action rapide"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                margin: 2px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
        """
    
    def load_dashboard_data(self):
        """Charger les données du dashboard"""
        try:
            from datetime import datetime
            
            with self.db_manager.get_session() as session:
                # Statistiques générales
                stats = self.stock_controller.get_global_statistics(session)
                
                # Alertes critiques
                alerts = self.alerte_controller.get_current_alerts(session)
                critical_alerts = len([a for a in alerts if a.get('alert_level') == 'CRITICAL'])
                
                # Mettre à jour les indicateurs
                self.update_indicator("valeur_totale_value", f"{stats.get('total_stock_value', 0):,.2f} €")
                self.update_indicator("alertes_critiques_value", str(critical_alerts))
                self.update_indicator("produits_en_stock_value", str(stats.get('total_products_with_stock', 0)))
                self.update_indicator("transferts_actifs_value", str(stats.get('active_transfers', 0)))
                self.update_indicator("entrepôts_actifs_value", str(stats.get('active_warehouses', 0)))
                self.update_indicator("mouvements/jour_value", str(stats.get('movements_today', 0)))
                
                # Mettre à jour le timestamp
                self.last_update_label.setText(f"Dernière MAJ: {datetime.now().strftime('%H:%M')}")
                
        except Exception as e:
            print(f"Erreur lors du chargement des données du dashboard: {e}")
    
    def update_indicator(self, object_name: str, new_value: str):
        """Mettre à jour la valeur d'un indicateur"""
        indicator = self.findChild(QLabel, object_name)
        if indicator:
            indicator.setText(new_value)
    
    def quick_transfer(self):
        """Action rapide: nouveau transfert"""
        # Signal pour ouvrir l'onglet transferts
        parent = self.parent()
        while parent and not hasattr(parent, 'switch_to_transfers'):
            parent = parent.parent()
        
        if parent and hasattr(parent, 'switch_to_transfers'):
            parent.switch_to_transfers()
    
    def quick_inventory_correction(self):
        """Action rapide: correction d'inventaire"""
        parent = self.parent()
        while parent and not hasattr(parent, 'switch_to_inventory'):
            parent = parent.parent()
        
        if parent and hasattr(parent, 'switch_to_inventory'):
            parent.switch_to_inventory()
    
    def view_critical_alerts(self):
        """Action rapide: voir les alertes critiques"""
        parent = self.parent()
        while parent and not hasattr(parent, 'switch_to_alerts'):
            parent = parent.parent()
        
        if parent and hasattr(parent, 'switch_to_alerts'):
            parent.switch_to_alerts()


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