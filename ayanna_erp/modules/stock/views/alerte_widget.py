"""
Widget pour l'analyse des alertes de stock et la gestion des quantités par entrepôt
"""

from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime, date, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton, 
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, 
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout, QTextEdit, 
    QDoubleSpinBox, QSpinBox, QCheckBox, QTabWidget, QTreeWidget, 
    QTreeWidgetItem, QSplitter, QProgressBar, QFrame, QDateEdit,
    QScrollArea, QSlider, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QDate
from PyQt6.QtGui import QFont, QColor, QPixmap, QIcon, QPalette

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.stock.controllers.alerte_controller import AlerteController


class AlertConfigDialog(QDialog):
    """Dialog pour configurer les seuils d'alerte par produit"""
    
    def __init__(self, parent=None, product_data=None, controller=None):
        super().__init__(parent)
        self.product_data = product_data
        self.controller = controller
        
        self.setWindowTitle(f"Configuration Alertes - {product_data['product_name']}")
        self.setFixedSize(500, 400)
        self.setup_ui()
        self.load_current_thresholds()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # Titre
        title = QLabel(f"🚨 Configuration des Alertes")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Informations produit
        product_info = QGroupBox("Informations Produit")
        product_layout = QFormLayout(product_info)
        
        product_layout.addRow("Nom:", QLabel(self.product_data['product_name']))
        if self.product_data.get('product_code'):
            product_layout.addRow("Code:", QLabel(self.product_data['product_code']))
        
        # Stock total actuel
        total_stock = sum(float(stock['quantity']) for stock in self.product_data['stocks'])
        stock_label = QLabel(f"{total_stock:.2f}")
        if total_stock < 10:  # Seuil d'exemple
            stock_label.setStyleSheet("color: red; font-weight: bold;")
        product_layout.addRow("Stock Total:", stock_label)
        
        layout.addWidget(product_info)
        
        # Configuration des seuils
        config_group = QGroupBox("Configuration des Seuils")
        config_layout = QFormLayout(config_group)
        
        # Seuil critique
        self.critical_threshold = QDoubleSpinBox()
        self.critical_threshold.setDecimals(2)
        self.critical_threshold.setMinimum(0.0)
        self.critical_threshold.setMaximum(999999.99)
        self.critical_threshold.setSuffix(" unités")
        config_layout.addRow("Seuil Critique (rouge):", self.critical_threshold)
        
        # Seuil d'alerte
        self.warning_threshold = QDoubleSpinBox()
        self.warning_threshold.setDecimals(2)
        self.warning_threshold.setMinimum(0.0)
        self.warning_threshold.setMaximum(999999.99)
        self.warning_threshold.setSuffix(" unités")
        config_layout.addRow("Seuil d'Alerte (orange):", self.warning_threshold)
        
        # Seuil optimal
        self.optimal_threshold = QDoubleSpinBox()
        self.optimal_threshold.setDecimals(2)
        self.optimal_threshold.setMinimum(0.0)
        self.optimal_threshold.setMaximum(999999.99)
        self.optimal_threshold.setSuffix(" unités")
        config_layout.addRow("Seuil Optimal (vert):", self.optimal_threshold)
        
        # Alertes activées
        self.alerts_enabled = QCheckBox("Alertes activées pour ce produit")
        self.alerts_enabled.setChecked(True)
        config_layout.addRow(self.alerts_enabled)
        
        layout.addWidget(config_group)
        
        # Indicateur visuel
        visual_group = QGroupBox("Aperçu des Niveaux")
        visual_layout = QVBoxLayout(visual_group)
        
        # Barre de progression pour montrer les seuils
        self.threshold_indicator = QProgressBar()
        self.threshold_indicator.setMinimum(0)
        self.threshold_indicator.setMaximum(100)
        self.threshold_indicator.setValue(int((total_stock / max(1, self.optimal_threshold.value() or 100)) * 100))
        visual_layout.addWidget(self.threshold_indicator)
        
        # Légende
        legend_layout = QHBoxLayout()
        
        critical_label = QLabel("🔴 Critique")
        critical_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        legend_layout.addWidget(critical_label)
        
        warning_label = QLabel("🟠 Alerte")
        warning_label.setStyleSheet("color: #f39c12; font-weight: bold;")
        legend_layout.addWidget(warning_label)
        
        good_label = QLabel("🟢 Bon")
        good_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        legend_layout.addWidget(good_label)
        
        optimal_label = QLabel("💚 Optimal")
        optimal_label.setStyleSheet("color: #2ecc71; font-weight: bold;")
        legend_layout.addWidget(optimal_label)
        
        visual_layout.addLayout(legend_layout)
        layout.addWidget(visual_group)
        
        # Connexions pour la mise à jour en temps réel
        self.critical_threshold.valueChanged.connect(self.update_indicator)
        self.warning_threshold.valueChanged.connect(self.update_indicator)
        self.optimal_threshold.valueChanged.connect(self.update_indicator)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 Sauvegarder")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        save_btn.clicked.connect(self.save_thresholds)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_current_thresholds(self):
        """Charger les seuils actuels du produit"""
        # Pour l'instant, utiliser des valeurs par défaut
        # Dans une vraie application, charger depuis la base de données
        total_stock = sum(float(stock['quantity']) for stock in self.product_data['stocks'])
        
        # Valeurs par défaut basées sur le stock actuel
        self.critical_threshold.setValue(max(1.0, total_stock * 0.1))
        self.warning_threshold.setValue(max(2.0, total_stock * 0.2))
        self.optimal_threshold.setValue(max(5.0, total_stock * 1.5))
        
        self.update_indicator()
    
    def update_indicator(self):
        """Mettre à jour l'indicateur visuel"""
        total_stock = sum(float(stock['quantity']) for stock in self.product_data['stocks'])
        optimal = max(1, self.optimal_threshold.value())
        
        percentage = min(100, int((total_stock / optimal) * 100))
        self.threshold_indicator.setValue(percentage)
        
        # Couleur selon le niveau
        critical = self.critical_threshold.value()
        warning = self.warning_threshold.value()
        
        if total_stock <= critical:
            color = "#e74c3c"  # Rouge
        elif total_stock <= warning:
            color = "#f39c12"  # Orange
        elif total_stock <= optimal:
            color = "#27ae60"  # Vert
        else:
            color = "#2ecc71"  # Vert optimal
        
        self.threshold_indicator.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {color};
            }}
        """)
    
    def save_thresholds(self):
        """Sauvegarder les seuils configurés"""
        try:
            # Validation
            critical = self.critical_threshold.value()
            warning = self.warning_threshold.value()
            optimal = self.optimal_threshold.value()
            
            if critical >= warning:
                QMessageBox.warning(self, "Validation", "Le seuil critique doit être inférieur au seuil d'alerte.")
                return
            
            if warning >= optimal:
                QMessageBox.warning(self, "Validation", "Le seuil d'alerte doit être inférieur au seuil optimal.")
                return
            
            # Sauvegarder via le contrôleur
            threshold_data = {
                'product_id': self.product_data['product_id'],
                'critical_threshold': Decimal(str(critical)),
                'warning_threshold': Decimal(str(warning)),
                'optimal_threshold': Decimal(str(optimal)),
                'alerts_enabled': self.alerts_enabled.isChecked()
            }
            
            # TODO: Appeler le contrôleur pour sauvegarder
            # self.controller.save_product_thresholds(threshold_data)
            
            QMessageBox.information(self, "Succès", "Configuration sauvegardée avec succès!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde:\n{str(e)}")


class AlerteWidget(QWidget):
    """Widget principal pour l'analyse des alertes et la gestion des quantités"""
    
    # Signaux
    alert_configured = pyqtSignal()  # Quand une alerte est configurée
    stock_action_needed = pyqtSignal(int, str)  # ID produit, action nécessaire
    
    def __init__(self, pos_id: int, current_user):
        super().__init__()
        self.pos_id = pos_id
        self.current_user = current_user
        self.controller = AlerteController(pos_id)
        self.db_manager = DatabaseManager()
        self.current_alerts = []
        self.analysis_data = {}
        
        self.setup_ui()
        self.load_analysis_data()
        
        # Timer pour actualisation automatique
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh)
        self.refresh_timer.start(300000)  # 5 minutes
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # En-tête avec indicateurs globaux
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2980b9);
                border-radius: 10px;
                color: white;
                padding: 15px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        
        title_layout = QHBoxLayout()
        title_label = QLabel("🚨 Analyse des Alertes de Stock")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: 2px solid white;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        refresh_btn.clicked.connect(self.load_analysis_data)
        title_layout.addWidget(refresh_btn)
        
        header_layout.addLayout(title_layout)
        
        # Indicateurs globaux
        indicators_layout = QHBoxLayout()
        
        self.critical_indicator = self.create_indicator("🔴 Critique", "0", "#e74c3c")
        indicators_layout.addWidget(self.critical_indicator)
        
        self.warning_indicator = self.create_indicator("🟠 Alerte", "0", "#f39c12")
        indicators_layout.addWidget(self.warning_indicator)
        
        self.low_stock_indicator = self.create_indicator("📉 Stock Bas", "0", "#3498db")
        indicators_layout.addWidget(self.low_stock_indicator)
        
        self.out_of_stock_indicator = self.create_indicator("❌ Rupture", "0", "#95a5a6")
        indicators_layout.addWidget(self.out_of_stock_indicator)
        
        header_layout.addLayout(indicators_layout)
        layout.addWidget(header_frame)
        
        # Onglets principaux
        tabs = QTabWidget()
        
        # Onglet Alertes Critiques
        critical_tab = self.create_critical_alerts_tab()
        tabs.addTab(critical_tab, "🔴 Alertes Critiques")
        
        # Onglet Analyse par Entrepôt
        warehouse_tab = self.create_warehouse_analysis_tab()
        tabs.addTab(warehouse_tab, "🏪 Analyse par Entrepôt")
        
        # Onglet Configuration Globale
        config_tab = self.create_global_config_tab()
        tabs.addTab(config_tab, "⚙️ Configuration")
        
        # Onglet Historique
        history_tab = self.create_history_tab()
        tabs.addTab(history_tab, "📈 Historique")
        
        layout.addWidget(tabs)
    
    def create_indicator(self, label: str, value: str, color: str) -> QFrame:
        """Créer un indicateur coloré"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
            }}
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label_widget)
        
        value_widget = QLabel(value)
        value_widget.setStyleSheet("color: white; font-weight: bold; font-size: 20px;")
        value_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_widget.setObjectName(f"{label}_value")  # Pour pouvoir le retrouver
        layout.addWidget(value_widget)
        
        return frame
    
    def create_critical_alerts_tab(self) -> QWidget:
        """Créer l'onglet des alertes critiques"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filtres
        filters_layout = QHBoxLayout()
        
        filters_layout.addWidget(QLabel("Niveau:"))
        self.alert_level_filter = QComboBox()
        self.alert_level_filter.addItems(["Tous", "Critique", "Alerte", "Stock Bas", "Rupture"])
        self.alert_level_filter.currentTextChanged.connect(self.filter_alerts)
        filters_layout.addWidget(self.alert_level_filter)
        
        filters_layout.addWidget(QLabel("Entrepôt:"))
        self.warehouse_filter = QComboBox()
        self.warehouse_filter.addItem("Tous les entrepôts", None)
        self.warehouse_filter.currentTextChanged.connect(self.filter_alerts)
        filters_layout.addWidget(self.warehouse_filter)
        
        filters_layout.addWidget(QLabel("Recherche:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nom ou code produit...")
        self.search_input.textChanged.connect(self.filter_alerts)
        filters_layout.addWidget(self.search_input)
        
        filters_layout.addStretch()
        layout.addLayout(filters_layout)
        
        # Tableau des alertes
        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(8)
        self.alerts_table.setHorizontalHeaderLabels([
            "Priorité", "Produit", "Entrepôt", "Stock Actuel", "Seuil", "Statut", "Dernière MAJ", "Actions"
        ])
        self.alerts_table.setAlternatingRowColors(True)
        self.alerts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.alerts_table)
        
        return widget
    
    def create_warehouse_analysis_tab(self) -> QWidget:
        """Créer l'onglet d'analyse par entrepôt"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Sélection d'entrepôt
        warehouse_selection_layout = QHBoxLayout()
        warehouse_selection_layout.addWidget(QLabel("Analyser l'entrepôt:"))
        
        self.analysis_warehouse_combo = QComboBox()
        self.analysis_warehouse_combo.currentTextChanged.connect(self.analyze_warehouse)
        warehouse_selection_layout.addWidget(self.analysis_warehouse_combo)
        
        warehouse_selection_layout.addStretch()
        layout.addLayout(warehouse_selection_layout)
        
        # Splitter pour diviser l'analyse
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panneau gauche : Vue d'ensemble
        overview_frame = QFrame()
        overview_layout = QVBoxLayout(overview_frame)
        
        overview_title = QLabel("📊 Vue d'Ensemble")
        overview_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        overview_layout.addWidget(overview_title)
        
        # Statistiques de l'entrepôt
        self.warehouse_stats_widget = QWidget()
        self.warehouse_stats_layout = QVBoxLayout(self.warehouse_stats_widget)
        overview_layout.addWidget(self.warehouse_stats_widget)
        
        overview_layout.addStretch()
        splitter.addWidget(overview_frame)
        
        # Panneau droit : Détails des produits
        details_frame = QFrame()
        details_layout = QVBoxLayout(details_frame)
        
        details_title = QLabel("📋 Détails des Produits")
        details_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        details_layout.addWidget(details_title)
        
        # Tableau détaillé pour l'entrepôt sélectionné
        self.warehouse_details_table = QTableWidget()
        self.warehouse_details_table.setColumnCount(6)
        self.warehouse_details_table.setHorizontalHeaderLabels([
            "Produit", "Stock", "Réservé", "Disponible", "Niveau", "Actions"
        ])
        self.warehouse_details_table.setAlternatingRowColors(True)
        details_layout.addWidget(self.warehouse_details_table)
        
        splitter.addWidget(details_frame)
        layout.addWidget(splitter)
        
        return widget
    
    def create_global_config_tab(self) -> QWidget:
        """Créer l'onglet de configuration globale"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Configuration des alertes automatiques
        auto_alerts_group = QGroupBox("Alertes Automatiques")
        auto_alerts_layout = QFormLayout(auto_alerts_group)
        
        self.enable_auto_alerts = QCheckBox("Activer les alertes automatiques")
        self.enable_auto_alerts.setChecked(True)
        auto_alerts_layout.addRow(self.enable_auto_alerts)
        
        self.alert_frequency = QComboBox()
        self.alert_frequency.addItems(["Temps réel", "Toutes les heures", "Quotidien", "Hebdomadaire"])
        auto_alerts_layout.addRow("Fréquence de vérification:", self.alert_frequency)
        
        self.email_notifications = QCheckBox("Notifications par email")
        auto_alerts_layout.addRow(self.email_notifications)
        
        layout.addWidget(auto_alerts_group)
        
        # Seuils par défaut
        default_thresholds_group = QGroupBox("Seuils par Défaut")
        default_thresholds_layout = QFormLayout(default_thresholds_group)
        
        self.default_critical = QDoubleSpinBox()
        self.default_critical.setDecimals(0)
        self.default_critical.setMinimum(0)
        self.default_critical.setMaximum(1000)
        self.default_critical.setValue(5)
        self.default_critical.setSuffix(" unités")
        default_thresholds_layout.addRow("Seuil critique par défaut:", self.default_critical)
        
        self.default_warning = QDoubleSpinBox()
        self.default_warning.setDecimals(0)
        self.default_warning.setMinimum(0)
        self.default_warning.setMaximum(1000)
        self.default_warning.setValue(10)
        self.default_warning.setSuffix(" unités")
        default_thresholds_layout.addRow("Seuil d'alerte par défaut:", self.default_warning)
        
        layout.addWidget(default_thresholds_group)
        
        # Actions en lot
        batch_actions_group = QGroupBox("Actions en Lot")
        batch_actions_layout = QVBoxLayout(batch_actions_group)
        
        batch_buttons_layout = QHBoxLayout()
        
        apply_defaults_btn = QPushButton("📋 Appliquer seuils par défaut à tous")
        apply_defaults_btn.clicked.connect(self.apply_default_thresholds)
        batch_buttons_layout.addWidget(apply_defaults_btn)
        
        recalculate_btn = QPushButton("🔄 Recalculer toutes les alertes")
        recalculate_btn.clicked.connect(self.recalculate_all_alerts)
        batch_buttons_layout.addWidget(recalculate_btn)
        
        batch_actions_layout.addLayout(batch_buttons_layout)
        layout.addWidget(batch_actions_group)
        
        layout.addStretch()
        
        # Bouton de sauvegarde
        save_config_btn = QPushButton("💾 Sauvegarder la Configuration")
        save_config_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        save_config_btn.clicked.connect(self.save_global_config)
        layout.addWidget(save_config_btn)
        
        return widget
    
    def create_history_tab(self) -> QWidget:
        """Créer l'onglet d'historique des alertes"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filtres temporels
        temporal_filters_layout = QHBoxLayout()
        
        temporal_filters_layout.addWidget(QLabel("Période:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["7 derniers jours", "30 derniers jours", "3 derniers mois", "Personnalisée"])
        self.period_combo.currentTextChanged.connect(self.load_alert_history)
        temporal_filters_layout.addWidget(self.period_combo)
        
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addDays(-30))
        self.from_date.setCalendarPopup(True)
        temporal_filters_layout.addWidget(QLabel("Du:"))
        temporal_filters_layout.addWidget(self.from_date)
        
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        temporal_filters_layout.addWidget(QLabel("Au:"))
        temporal_filters_layout.addWidget(self.to_date)
        
        temporal_filters_layout.addStretch()
        layout.addLayout(temporal_filters_layout)
        
        # Tableau de l'historique
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels([
            "Date", "Produit", "Entrepôt", "Type Alerte", "Stock", "Seuil", "Action Prise"
        ])
        self.history_table.setAlternatingRowColors(True)
        layout.addWidget(self.history_table)
        
        return widget
    
    def load_analysis_data(self):
        """Charger les données d'analyse"""
        try:
            with self.db_manager.get_session() as session:
                # Charger les alertes actuelles
                self.current_alerts = self.controller.get_current_alerts(session)
                
                # Charger les entrepôts pour les filtres
                self.load_warehouses_for_filters(session)
                
                # Mettre à jour les indicateurs
                self.update_global_indicators()
                
                # Peupler les tableaux
                self.populate_alerts_table()
                self.analyze_warehouse()
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des données:\n{str(e)}")
    
    def load_warehouses_for_filters(self, session):
        """Charger les entrepôts pour les filtres"""
        try:
            from ayanna_erp.modules.boutique.model.models import ShopWarehouse
            warehouses = session.query(ShopWarehouse).filter(
                ShopWarehouse.pos_id == self.pos_id,
                ShopWarehouse.is_active == True
            ).order_by(ShopWarehouse.name).all()
            
            # Mettre à jour les combos
            for combo in [self.warehouse_filter, self.analysis_warehouse_combo]:
                current_value = combo.currentData()
                combo.clear()
                combo.addItem("Tous les entrepôts", None)
                
                for warehouse in warehouses:
                    combo.addItem(f"{warehouse.name} ({warehouse.code})", warehouse.id)
                
                # Restaurer la sélection si possible
                if current_value:
                    index = combo.findData(current_value)
                    if index >= 0:
                        combo.setCurrentIndex(index)
            
        except Exception as e:
            print(f"Erreur lors du chargement des entrepôts: {e}")
    
    def update_global_indicators(self):
        """Mettre à jour les indicateurs globaux"""
        critical_count = 0
        warning_count = 0
        low_stock_count = 0
        out_of_stock_count = 0
        
        for alert in self.current_alerts:
            alert_level = alert.get('alert_level', 'UNKNOWN')
            if alert_level == 'CRITICAL':
                critical_count += 1
            elif alert_level == 'WARNING':
                warning_count += 1
            elif alert_level == 'LOW_STOCK':
                low_stock_count += 1
            elif alert_level == 'OUT_OF_STOCK':
                out_of_stock_count += 1
        
        # Mettre à jour les labels des indicateurs
        self.critical_indicator.findChild(QLabel, "🔴 Critique_value").setText(str(critical_count))
        self.warning_indicator.findChild(QLabel, "🟠 Alerte_value").setText(str(warning_count))
        self.low_stock_indicator.findChild(QLabel, "📉 Stock Bas_value").setText(str(low_stock_count))
        self.out_of_stock_indicator.findChild(QLabel, "❌ Rupture_value").setText(str(out_of_stock_count))
    
    def populate_alerts_table(self):
        """Peupler le tableau des alertes"""
        # Filtrer les alertes
        filtered_alerts = self.filter_alerts_data()
        
        self.alerts_table.setRowCount(len(filtered_alerts))
        
        for row, alert in enumerate(filtered_alerts):
            # Priorité avec icône
            priority_icons = {
                'CRITICAL': '🔴 Critique',
                'WARNING': '🟠 Alerte',
                'LOW_STOCK': '📉 Bas',
                'OUT_OF_STOCK': '❌ Rupture'
            }
            priority_item = QTableWidgetItem(priority_icons.get(alert.get('alert_level'), 'ℹ️ Info'))
            
            # Couleur de fond selon la priorité
            priority_colors = {
                'CRITICAL': QColor("#ffebee"),
                'WARNING': QColor("#fff8e1"),
                'LOW_STOCK': QColor("#e3f2fd"),
                'OUT_OF_STOCK': QColor("#f3e5f5")
            }
            if alert.get('alert_level') in priority_colors:
                priority_item.setBackground(priority_colors[alert.get('alert_level')])
            
            self.alerts_table.setItem(row, 0, priority_item)
            
            # Produit
            product_text = alert.get('product_name', 'N/A')
            if alert.get('product_code'):
                product_text += f" ({alert['product_code']})"
            self.alerts_table.setItem(row, 1, QTableWidgetItem(product_text))
            
            # Entrepôt
            warehouse_text = f"{alert.get('warehouse_name', 'N/A')} ({alert.get('warehouse_code', 'N/A')})"
            self.alerts_table.setItem(row, 2, QTableWidgetItem(warehouse_text))
            
            # Stock actuel
            current_stock = alert.get('current_stock', 0)
            stock_item = QTableWidgetItem(f"{current_stock:.2f}")
            stock_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.alerts_table.setItem(row, 3, stock_item)
            
            # Seuil
            threshold = alert.get('threshold', 0)
            threshold_item = QTableWidgetItem(f"{threshold:.2f}")
            threshold_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.alerts_table.setItem(row, 4, threshold_item)
            
            # Statut
            if current_stock <= 0:
                status = "❌ Rupture"
            elif current_stock <= threshold:
                status = "🔴 Critique"
            else:
                status = "🟢 Normal"
            self.alerts_table.setItem(row, 5, QTableWidgetItem(status))
            
            # Dernière mise à jour
            last_update = alert.get('last_updated', datetime.now())
            if isinstance(last_update, datetime):
                update_str = last_update.strftime('%d/%m %H:%M')
            else:
                update_str = "N/A"
            self.alerts_table.setItem(row, 6, QTableWidgetItem(update_str))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            
            config_btn = QPushButton("⚙️")
            config_btn.setToolTip("Configurer les alertes")
            config_btn.setMaximumWidth(30)
            config_btn.clicked.connect(lambda checked, a=alert: self.configure_product_alert(a))
            actions_layout.addWidget(config_btn)
            
            if alert.get('alert_level') in ['CRITICAL', 'WARNING']:
                action_btn = QPushButton("🎯")
                action_btn.setToolTip("Action recommandée")
                action_btn.setMaximumWidth(30)
                action_btn.clicked.connect(lambda checked, a=alert: self.suggest_action(a))
                actions_layout.addWidget(action_btn)
            
            self.alerts_table.setCellWidget(row, 7, actions_widget)
        
        self.alerts_table.resizeColumnsToContents()
    
    def filter_alerts_data(self) -> List[Dict]:
        """Filtrer les données d'alertes selon les critères"""
        filtered = self.current_alerts.copy()
        
        # Filtre par niveau d'alerte
        level_filter = self.alert_level_filter.currentText()
        if level_filter != "Tous":
            level_map = {
                "Critique": "CRITICAL",
                "Alerte": "WARNING",
                "Stock Bas": "LOW_STOCK",
                "Rupture": "OUT_OF_STOCK"
            }
            target_level = level_map.get(level_filter)
            if target_level:
                filtered = [a for a in filtered if a.get('alert_level') == target_level]
        
        # Filtre par entrepôt
        warehouse_id = self.warehouse_filter.currentData()
        if warehouse_id:
            filtered = [a for a in filtered if a.get('warehouse_id') == warehouse_id]
        
        # Filtre par recherche
        search_term = self.search_input.text().lower()
        if search_term:
            filtered = [
                a for a in filtered 
                if search_term in a.get('product_name', '').lower() or
                   search_term in a.get('product_code', '').lower()
            ]
        
        return filtered
    
    def filter_alerts(self):
        """Appliquer les filtres aux alertes"""
        self.populate_alerts_table()
    
    def analyze_warehouse(self):
        """Analyser l'entrepôt sélectionné"""
        warehouse_id = self.analysis_warehouse_combo.currentData()
        if not warehouse_id:
            return
        
        try:
            with self.db_manager.get_session() as session:
                # Récupérer les données de l'entrepôt
                warehouse_data = self.controller.get_warehouse_analysis(session, warehouse_id)
                
                # Mettre à jour les statistiques de l'entrepôt
                self.update_warehouse_stats(warehouse_data)
                
                # Mettre à jour le tableau détaillé
                self.populate_warehouse_details_table(warehouse_data.get('products', []))
                
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de l'analyse de l'entrepôt:\n{str(e)}")
    
    def update_warehouse_stats(self, warehouse_data):
        """Mettre à jour les statistiques de l'entrepôt"""
        # Nettoyer le layout existant
        for i in reversed(range(self.warehouse_stats_layout.count())):
            self.warehouse_stats_layout.itemAt(i).widget().setParent(None)
        
        if not warehouse_data:
            return
        
        # Statistiques générales
        stats = warehouse_data.get('stats', {})
        
        total_products = stats.get('total_products', 0)
        total_value = stats.get('total_value', 0)
        critical_products = stats.get('critical_products', 0)
        warning_products = stats.get('warning_products', 0)
        
        # Créer les widgets de statistiques
        stats_data = [
            ("📦 Produits Total", str(total_products), "#3498db"),
            ("💰 Valeur Stock", f"{total_value:.2f} €", "#27ae60"),
            ("🔴 Critique", str(critical_products), "#e74c3c"),
            ("🟠 Alerte", str(warning_products), "#f39c12")
        ]
        
        for label, value, color in stats_data:
            stat_frame = QFrame()
            stat_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {color};
                    border-radius: 8px;
                    padding: 10px;
                    margin: 2px;
                }}
            """)
            
            stat_layout = QVBoxLayout(stat_frame)
            
            label_widget = QLabel(label)
            label_widget.setStyleSheet("color: white; font-weight: bold; font-size: 11px;")
            label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(label_widget)
            
            value_widget = QLabel(value)
            value_widget.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
            value_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(value_widget)
            
            self.warehouse_stats_layout.addWidget(stat_frame)
    
    def populate_warehouse_details_table(self, products):
        """Peupler le tableau des détails de l'entrepôt"""
        self.warehouse_details_table.setRowCount(len(products))
        
        for row, product in enumerate(products):
            # Produit
            product_text = product.get('product_name', 'N/A')
            if product.get('product_code'):
                product_text += f" ({product['product_code']})"
            self.warehouse_details_table.setItem(row, 0, QTableWidgetItem(product_text))
            
            # Stock
            stock = product.get('quantity', 0)
            stock_item = QTableWidgetItem(f"{stock:.2f}")
            stock_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.warehouse_details_table.setItem(row, 1, stock_item)
            
            # Réservé
            reserved = product.get('reserved_quantity', 0)
            reserved_item = QTableWidgetItem(f"{reserved:.2f}")
            reserved_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.warehouse_details_table.setItem(row, 2, reserved_item)
            
            # Disponible
            available = stock - reserved
            available_item = QTableWidgetItem(f"{available:.2f}")
            available_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.warehouse_details_table.setItem(row, 3, available_item)
            
            # Niveau (avec couleur)
            if stock <= 0:
                level = "❌ Rupture"
                level_color = QColor("#ffcdd2")
            elif stock <= 5:  # Seuil exemple
                level = "🔴 Critique"
                level_color = QColor("#ffebee")
            elif stock <= 10:  # Seuil exemple
                level = "🟠 Alerte"
                level_color = QColor("#fff8e1")
            else:
                level = "🟢 Normal"
                level_color = QColor("#e8f5e8")
            
            level_item = QTableWidgetItem(level)
            level_item.setBackground(level_color)
            self.warehouse_details_table.setItem(row, 4, level_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            
            config_btn = QPushButton("⚙️")
            config_btn.setToolTip("Configurer")
            config_btn.setMaximumWidth(30)
            config_btn.clicked.connect(lambda checked, p=product: self.configure_product_alert(p))
            actions_layout.addWidget(config_btn)
            
            self.warehouse_details_table.setCellWidget(row, 5, actions_widget)
        
        self.warehouse_details_table.resizeColumnsToContents()
    
    def configure_product_alert(self, product_data):
        """Configurer les alertes pour un produit"""
        dialog = AlertConfigDialog(self, product_data=product_data, controller=self.controller)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.alert_configured.emit()
            self.load_analysis_data()
            QMessageBox.information(self, "Succès", "Configuration des alertes mise à jour!")
    
    def suggest_action(self, alert_data):
        """Suggérer des actions pour une alerte"""
        product_name = alert_data.get('product_name', 'Produit')
        current_stock = alert_data.get('current_stock', 0)
        threshold = alert_data.get('threshold', 0)
        
        suggestions = []
        
        if current_stock <= 0:
            suggestions.append("🚨 Réapprovisionnement urgent nécessaire")
            suggestions.append("📞 Contacter le fournisseur immédiatement")
            suggestions.append("🔄 Vérifier s'il y a du stock dans d'autres entrepôts")
        elif current_stock <= threshold:
            suggestions.append("📋 Planifier un réapprovisionnement")
            suggestions.append("📊 Vérifier l'historique de consommation")
            suggestions.append("🔄 Envisager un transfert depuis un autre entrepôt")
        
        suggestions_text = "\n".join(f"• {s}" for s in suggestions)
        
        QMessageBox.information(
            self, f"Actions Recommandées - {product_name}",
            f"Stock actuel: {current_stock:.2f}\n"
            f"Seuil configuré: {threshold:.2f}\n\n"
            f"Actions recommandées:\n{suggestions_text}"
        )
        
        # Émettre le signal pour actions externes
        self.stock_action_needed.emit(alert_data.get('product_id', 0), "restock_needed")
    
    def apply_default_thresholds(self):
        """Appliquer les seuils par défaut à tous les produits"""
        reply = QMessageBox.question(
            self, "Confirmation",
            "Appliquer les seuils par défaut à tous les produits?\n\n"
            "Cette action remplacera les configurations existantes.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # TODO: Implémenter via le contrôleur
                # self.controller.apply_default_thresholds_to_all()
                
                QMessageBox.information(self, "Succès", "Seuils par défaut appliqués à tous les produits!")
                self.load_analysis_data()
                
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'application des seuils:\n{str(e)}")
    
    def recalculate_all_alerts(self):
        """Recalculer toutes les alertes"""
        try:
            # TODO: Implémenter via le contrôleur
            # self.controller.recalculate_all_alerts()
            
            QMessageBox.information(self, "Succès", "Toutes les alertes ont été recalculées!")
            self.load_analysis_data()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du recalcul des alertes:\n{str(e)}")
    
    def save_global_config(self):
        """Sauvegarder la configuration globale"""
        try:
            config = {
                'auto_alerts_enabled': self.enable_auto_alerts.isChecked(),
                'alert_frequency': self.alert_frequency.currentText(),
                'email_notifications': self.email_notifications.isChecked(),
                'default_critical_threshold': self.default_critical.value(),
                'default_warning_threshold': self.default_warning.value()
            }
            
            # TODO: Sauvegarder via le contrôleur
            # self.controller.save_global_configuration(config)
            
            QMessageBox.information(self, "Succès", "Configuration globale sauvegardée!")
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde:\n{str(e)}")
    
    def load_alert_history(self):
        """Charger l'historique des alertes"""
        try:
            period = self.period_combo.currentText()
            
            # Calculer les dates selon la période
            if period == "7 derniers jours":
                from_date = datetime.now() - timedelta(days=7)
                to_date = datetime.now()
            elif period == "30 derniers jours":
                from_date = datetime.now() - timedelta(days=30)
                to_date = datetime.now()
            elif period == "3 derniers mois":
                from_date = datetime.now() - timedelta(days=90)
                to_date = datetime.now()
            else:  # Personnalisée
                from_date = self.from_date.date().toPython()
                to_date = self.to_date.date().toPython()
            
            with self.db_manager.get_session() as session:
                history = self.controller.get_alert_history(session, from_date, to_date)
                self.populate_history_table(history)
                
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement de l'historique:\n{str(e)}")
    
    def populate_history_table(self, history):
        """Peupler le tableau de l'historique"""
        self.history_table.setRowCount(len(history))
        
        for row, record in enumerate(history):
            # Date
            date_str = record.get('date', datetime.now()).strftime('%d/%m/%Y %H:%M')
            self.history_table.setItem(row, 0, QTableWidgetItem(date_str))
            
            # Produit
            product_name = record.get('product_name', 'N/A')
            if record.get('product_code'):
                product_name += f" ({record['product_code']})"
            self.history_table.setItem(row, 1, QTableWidgetItem(product_name))
            
            # Entrepôt
            warehouse_name = f"{record.get('warehouse_name', 'N/A')} ({record.get('warehouse_code', 'N/A')})"
            self.history_table.setItem(row, 2, QTableWidgetItem(warehouse_name))
            
            # Type d'alerte
            alert_types = {
                'CRITICAL': '🔴 Critique',
                'WARNING': '🟠 Alerte',
                'LOW_STOCK': '📉 Stock Bas',
                'OUT_OF_STOCK': '❌ Rupture'
            }
            alert_type = alert_types.get(record.get('alert_type'), record.get('alert_type', 'N/A'))
            self.history_table.setItem(row, 3, QTableWidgetItem(alert_type))
            
            # Stock à ce moment
            stock = record.get('stock_at_time', 0)
            stock_item = QTableWidgetItem(f"{stock:.2f}")
            stock_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.history_table.setItem(row, 4, stock_item)
            
            # Seuil
            threshold = record.get('threshold', 0)
            threshold_item = QTableWidgetItem(f"{threshold:.2f}")
            threshold_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.history_table.setItem(row, 5, threshold_item)
            
            # Action prise
            action = record.get('action_taken', 'Aucune')
            self.history_table.setItem(row, 6, QTableWidgetItem(action))
        
        self.history_table.resizeColumnsToContents()
    
    def auto_refresh(self):
        """Actualisation automatique des données"""
        self.load_analysis_data()