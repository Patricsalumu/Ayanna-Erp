"""
Fenêtre du module Salle de Fête pour Ayanna ERP
Gestion des événements, réservations, services et produits
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTabWidget, QTableWidget, QTableWidgetItem, 
                            QPushButton, QLineEdit, QLabel, QComboBox, 
                            QSpinBox, QDoubleSpinBox, QTextEdit, QMessageBox,
                            QGroupBox, QGridLayout, QListWidget, QSplitter,
                            QFrame, QScrollArea, QFormLayout, QCheckBox,
                            QDateTimeEdit, QCalendarWidget)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDateTime
from PyQt6.QtGui import QFont, QPixmap, QIcon
from decimal import Decimal
from datetime import datetime, timedelta
from ayanna_erp.database.database_manager import DatabaseManager


class EventCalendarWidget(QWidget):
    """Widget calendrier pour visualiser les événements"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Configuration de l'interface"""
        layout = QVBoxLayout()
        
        # Calendrier
        self.calendar = QCalendarWidget()
        self.calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: white;
                alternate-background-color: #F8F9FA;
            }
            QCalendarWidget QToolButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 5px;
            }
            QCalendarWidget QMenu {
                background-color: white;
                border: 1px solid #BDC3C7;
            }
        """)
        
        # Zone des détails de l'événement sélectionné
        details_group = QGroupBox("Détails de l'événement")
        details_layout = QVBoxLayout(details_group)
        
        self.event_details_label = QLabel("Aucun événement sélectionné")
        self.event_details_label.setStyleSheet("""
            padding: 10px;
            background-color: #F8F9FA;
            border-radius: 5px;
            border: 1px solid #BDC3C7;
        """)
        
        details_layout.addWidget(self.event_details_label)
        
        layout.addWidget(self.calendar)
        layout.addWidget(details_group)
        self.setLayout(layout)


class ReservationFormWidget(QWidget):
    """Formulaire de création/modification de réservation"""
    
    reservation_saved = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.current_reservation = None
        self.setup_ui()
    
    def setup_ui(self):
        """Configuration du formulaire"""
        layout = QVBoxLayout()
        
        # Informations générales
        general_group = QGroupBox("Informations générales")
        general_layout = QFormLayout(general_group)
        
        self.client_combo = QComboBox()
        self.client_combo.setEditable(True)
        
        self.event_date_edit = QDateTimeEdit()
        self.event_date_edit.setDateTime(QDateTime.currentDateTime())
        self.event_date_edit.setCalendarPopup(True)
        
        self.reference_edit = QLineEdit()
        self.reference_edit.setPlaceholderText("Référence automatique")
        self.reference_edit.setReadOnly(True)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        
        general_layout.addRow("Client:", self.client_combo)
        general_layout.addRow("Date de l'événement:", self.event_date_edit)
        general_layout.addRow("Référence:", self.reference_edit)
        general_layout.addRow("Notes:", self.notes_edit)
        
        # Services et produits
        items_group = QGroupBox("Services et Produits")
        items_layout = QVBoxLayout(items_group)
        
        # Barre d'outils pour ajouter services/produits
        items_toolbar = QHBoxLayout()
        
        self.add_service_button = QPushButton("➕ Ajouter Service")
        self.add_product_button = QPushButton("➕ Ajouter Produit")
        
        items_toolbar.addWidget(self.add_service_button)
        items_toolbar.addWidget(self.add_product_button)
        items_toolbar.addStretch()
        
        # Table des éléments
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels([
            "Type", "Nom", "Prix unitaire", "Quantité", "Total", "Action"
        ])
        self.items_table.horizontalHeader().setStretchLastSection(True)
        
        items_layout.addLayout(items_toolbar)
        items_layout.addWidget(self.items_table)
        
        # Totaux
        totals_group = QGroupBox("Totaux")
        totals_layout = QFormLayout(totals_group)
        
        self.total_services_label = QLabel("0.00 €")
        self.total_products_label = QLabel("0.00 €")
        self.total_amount_label = QLabel("0.00 €")
        self.total_amount_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #E74C3C;")
        
        totals_layout.addRow("Total Services:", self.total_services_label)
        totals_layout.addRow("Total Produits:", self.total_products_label)
        totals_layout.addRow("TOTAL GÉNÉRAL:", self.total_amount_label)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        self.save_button = QPushButton("💾 Enregistrer")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        self.confirm_button = QPushButton("✅ Confirmer")
        self.confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        
        self.cancel_button = QPushButton("❌ Annuler")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.confirm_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_button)
        
        # Layout principal
        layout.addWidget(general_group)
        layout.addWidget(items_group)
        layout.addWidget(totals_group)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)


class SalleFeteWindow(QMainWindow):
    """Fenêtre principale du module Salle de Fête"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.db_manager = DatabaseManager()
        
        self.setWindowTitle("Ayanna ERP - Salle de Fête")
        self.setMinimumSize(1400, 900)
        
        self.setup_ui()
    
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
            }
            QTabBar::tab:selected {
                background-color: #E74C3C;
                color: white;
            }
        """)
        
        # Onglet Calendrier / Vue d'ensemble
        self.setup_calendar_tab()
        
        # Onglet Nouvelle réservation
        self.setup_new_reservation_tab()
        
        # Onglet Réservations
        self.setup_reservations_tab()
        
        # Onglet Services
        self.setup_services_tab()
        
        # Onglet Produits
        self.setup_products_tab()
        
        # Onglet Clients
        self.setup_clients_tab()
        
        # Onglet Paiements
        self.setup_payments_tab()
        
        # Onglet Rapports
        self.setup_reports_tab()
        
        main_layout.addWidget(self.tab_widget)
    
    def setup_calendar_tab(self):
        """Configuration de l'onglet Calendrier"""
        calendar_widget = QWidget()
        calendar_layout = QHBoxLayout(calendar_widget)
        
        # Splitter pour diviser l'écran
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Calendrier à gauche
        self.event_calendar = EventCalendarWidget()
        
        # Statistiques et informations à droite
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        
        # Statistiques du jour
        today_stats_group = QGroupBox("Statistiques du jour")
        today_stats_layout = QGridLayout(today_stats_group)
        
        # Cartes de statistiques
        self.create_stat_card("Événements", "3", "#3498DB", today_stats_layout, 0, 0)
        self.create_stat_card("Revenus", "2,500 €", "#27AE60", today_stats_layout, 0, 1)
        self.create_stat_card("Clients", "8", "#9B59B6", today_stats_layout, 1, 0)
        self.create_stat_card("En attente", "2", "#F39C12", today_stats_layout, 1, 1)
        
        # Événements à venir
        upcoming_group = QGroupBox("Événements à venir")
        upcoming_layout = QVBoxLayout(upcoming_group)
        
        self.upcoming_events_list = QListWidget()
        self.upcoming_events_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #BDC3C7;
                background-color: #FAFAFA;
                alternate-background-color: white;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #ECF0F1;
            }
            QListWidget::item:selected {
                background-color: #3498DB;
                color: white;
            }
        """)
        
        upcoming_layout.addWidget(self.upcoming_events_list)
        
        stats_layout.addWidget(today_stats_group)
        stats_layout.addWidget(upcoming_group)
        
        splitter.addWidget(self.event_calendar)
        splitter.addWidget(stats_widget)
        splitter.setSizes([700, 400])
        
        calendar_layout.addWidget(splitter)
        self.tab_widget.addTab(calendar_widget, "📅 Calendrier")
    
    def create_stat_card(self, title, value, color, layout, row, col):
        """Créer une carte de statistique"""
        card_frame = QFrame()
        card_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 8px;
                padding: 15px;
                max-height: 100px;
            }}
        """)
        
        card_layout = QVBoxLayout(card_frame)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)
        
        layout.addWidget(card_frame, row, col)
    
    def setup_new_reservation_tab(self):
        """Configuration de l'onglet Nouvelle réservation"""
        self.reservation_form = ReservationFormWidget()
        self.tab_widget.addTab(self.reservation_form, "➕ Nouvelle Réservation")
    
    def setup_reservations_tab(self):
        """Configuration de l'onglet Réservations"""
        reservations_widget = QWidget()
        reservations_layout = QVBoxLayout(reservations_widget)
        
        # Barre de filtres
        filters_layout = QHBoxLayout()
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Tous", "Brouillon", "Confirmé", "Payé", "Annulé"])
        
        self.date_from_edit = QDateTimeEdit()
        self.date_from_edit.setDate(QDateTime.currentDateTime().addDays(-30).date())
        
        self.date_to_edit = QDateTimeEdit()
        self.date_to_edit.setDate(QDateTime.currentDateTime().date())
        
        filters_layout.addWidget(QLabel("Statut:"))
        filters_layout.addWidget(self.status_filter)
        filters_layout.addWidget(QLabel("Du:"))
        filters_layout.addWidget(self.date_from_edit)
        filters_layout.addWidget(QLabel("Au:"))
        filters_layout.addWidget(self.date_to_edit)
        filters_layout.addStretch()
        
        # Barre d'outils
        toolbar_layout = QHBoxLayout()
        
        refresh_button = QPushButton("🔄 Actualiser")
        edit_button = QPushButton("✏️ Modifier")
        delete_button = QPushButton("🗑️ Supprimer")
        print_button = QPushButton("🖨️ Imprimer")
        
        toolbar_layout.addWidget(refresh_button)
        toolbar_layout.addWidget(edit_button)
        toolbar_layout.addWidget(delete_button)
        toolbar_layout.addWidget(print_button)
        toolbar_layout.addStretch()
        
        # Table des réservations
        self.reservations_table = QTableWidget()
        self.reservations_table.setColumnCount(8)
        self.reservations_table.setHorizontalHeaderLabels([
            "ID", "Référence", "Client", "Date événement", "Total", "Statut", "Créé le", "Actions"
        ])
        self.reservations_table.horizontalHeader().setStretchLastSection(True)
        
        reservations_layout.addLayout(filters_layout)
        reservations_layout.addLayout(toolbar_layout)
        reservations_layout.addWidget(self.reservations_table)
        
        self.tab_widget.addTab(reservations_widget, "📋 Réservations")
    
    def setup_services_tab(self):
        """Configuration de l'onglet Services"""
        services_widget = QWidget()
        services_layout = QVBoxLayout(services_widget)
        
        # Barre d'outils
        toolbar_layout = QHBoxLayout()
        
        add_service_button = QPushButton("➕ Nouveau Service")
        add_service_button.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        
        edit_service_button = QPushButton("✏️ Modifier")
        delete_service_button = QPushButton("🗑️ Supprimer")
        
        toolbar_layout.addWidget(add_service_button)
        toolbar_layout.addWidget(edit_service_button)
        toolbar_layout.addWidget(delete_service_button)
        toolbar_layout.addStretch()
        
        # Table des services
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(6)
        self.services_table.setHorizontalHeaderLabels([
            "ID", "Nom", "Description", "Coût", "Prix", "Statut"
        ])
        self.services_table.horizontalHeader().setStretchLastSection(True)
        
        services_layout.addLayout(toolbar_layout)
        services_layout.addWidget(self.services_table)
        
        self.tab_widget.addTab(services_widget, "🎪 Services")
    
    def setup_products_tab(self):
        """Configuration de l'onglet Produits"""
        products_widget = QWidget()
        products_layout = QVBoxLayout(products_widget)
        
        # Barre d'outils
        toolbar_layout = QHBoxLayout()
        
        add_product_button = QPushButton("➕ Nouveau Produit")
        add_product_button.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        edit_product_button = QPushButton("✏️ Modifier")
        delete_product_button = QPushButton("🗑️ Supprimer")
        
        toolbar_layout.addWidget(add_product_button)
        toolbar_layout.addWidget(edit_product_button)
        toolbar_layout.addWidget(delete_product_button)
        toolbar_layout.addStretch()
        
        # Table des produits
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(7)
        self.products_table.setHorizontalHeaderLabels([
            "ID", "Nom", "Description", "Coût", "Prix", "Stock", "Statut"
        ])
        self.products_table.horizontalHeader().setStretchLastSection(True)
        
        products_layout.addLayout(toolbar_layout)
        products_layout.addWidget(self.products_table)
        
        self.tab_widget.addTab(products_widget, "📦 Produits")
    
    def setup_clients_tab(self):
        """Configuration de l'onglet Clients"""
        clients_widget = QWidget()
        clients_layout = QVBoxLayout(clients_widget)
        
        # Barre d'outils
        toolbar_layout = QHBoxLayout()
        
        add_client_button = QPushButton("➕ Nouveau Client")
        add_client_button.setStyleSheet("""
            QPushButton {
                background-color: #9B59B6;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8E44AD;
            }
        """)
        
        edit_client_button = QPushButton("✏️ Modifier")
        delete_client_button = QPushButton("🗑️ Supprimer")
        
        toolbar_layout.addWidget(add_client_button)
        toolbar_layout.addWidget(edit_client_button)
        toolbar_layout.addWidget(delete_client_button)
        toolbar_layout.addStretch()
        
        # Table des clients
        self.clients_table = QTableWidget()
        self.clients_table.setColumnCount(5)
        self.clients_table.setHorizontalHeaderLabels([
            "ID", "Nom", "Email", "Téléphone", "Adresse"
        ])
        self.clients_table.horizontalHeader().setStretchLastSection(True)
        
        clients_layout.addLayout(toolbar_layout)
        clients_layout.addWidget(self.clients_table)
        
        self.tab_widget.addTab(clients_widget, "👥 Clients")
    
    def setup_payments_tab(self):
        """Configuration de l'onglet Paiements"""
        payments_widget = QWidget()
        payments_layout = QVBoxLayout(payments_widget)
        
        # Configuration des moyens de paiement
        config_group = QGroupBox("Configuration des moyens de paiement")
        config_layout = QVBoxLayout(config_group)
        
        # Table des moyens de paiement
        self.payment_methods_table = QTableWidget()
        self.payment_methods_table.setColumnCount(4)
        self.payment_methods_table.setHorizontalHeaderLabels([
            "Nom", "Compte comptable", "Par défaut", "Actif"
        ])
        
        config_layout.addWidget(self.payment_methods_table)
        
        # Historique des paiements
        history_group = QGroupBox("Historique des paiements")
        history_layout = QVBoxLayout(history_group)
        
        self.payments_history_table = QTableWidget()
        self.payments_history_table.setColumnCount(5)
        self.payments_history_table.setHorizontalHeaderLabels([
            "Date", "Réservation", "Moyen", "Montant", "Statut"
        ])
        
        history_layout.addWidget(self.payments_history_table)
        
        payments_layout.addWidget(config_group)
        payments_layout.addWidget(history_group)
        
        self.tab_widget.addTab(payments_widget, "💳 Paiements")
    
    def setup_reports_tab(self):
        """Configuration de l'onglet Rapports"""
        reports_widget = QWidget()
        reports_layout = QVBoxLayout(reports_widget)
        
        # Zone de sélection des rapports
        reports_selection = QGroupBox("Sélection du rapport")
        selection_layout = QGridLayout(reports_selection)
        
        # Différents types de rapports
        daily_events_button = QPushButton("📊 Événements du jour")
        weekly_events_button = QPushButton("📈 Événements de la semaine")
        monthly_events_button = QPushButton("📉 Événements du mois")
        revenue_report_button = QPushButton("💰 Rapport de revenus")
        client_report_button = QPushButton("👥 Rapport clients")
        
        selection_layout.addWidget(daily_events_button, 0, 0)
        selection_layout.addWidget(weekly_events_button, 0, 1)
        selection_layout.addWidget(monthly_events_button, 1, 0)
        selection_layout.addWidget(revenue_report_button, 1, 1)
        selection_layout.addWidget(client_report_button, 2, 0)
        
        # Zone d'affichage des rapports
        self.reports_display = QTextEdit()
        self.reports_display.setReadOnly(True)
        
        reports_layout.addWidget(reports_selection)
        reports_layout.addWidget(self.reports_display)
        
        self.tab_widget.addTab(reports_widget, "📊 Rapports")
    
    def closeEvent(self, event):
        """Gérer la fermeture de la fenêtre"""
        self.db_manager.close_session()
        event.accept()
