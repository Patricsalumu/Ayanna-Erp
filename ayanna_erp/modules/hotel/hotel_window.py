"""
Fenêtre du module Hôtel pour Ayanna ERP
Gestion des chambres, réservations et services hôteliers
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTabWidget, QTableWidget, QTableWidgetItem, 
                            QPushButton, QLineEdit, QLabel, QComboBox, 
                            QSpinBox, QDoubleSpinBox, QTextEdit, QMessageBox,
                            QGroupBox, QGridLayout, QListWidget, QSplitter,
                            QFrame, QScrollArea, QFormLayout, QCheckBox,
                            QDateEdit, QCalendarWidget)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QPixmap, QIcon, QColor
from decimal import Decimal
from datetime import datetime, timedelta
from ayanna_erp.database.database_manager import DatabaseManager


class HotelWindow(QMainWindow):
    """Fenêtre principale du module Hôtel"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.db_manager = DatabaseManager()
        
        self.setWindowTitle("Ayanna ERP - Hôtel")
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
                background-color: #9B59B6;
                color: white;
            }
        """)
        
        # Ajouter les onglets
        self.setup_dashboard_tab()
        self.setup_reservations_tab()
        self.setup_rooms_tab()
        self.setup_checkin_tab()
        self.setup_checkout_tab()
        self.setup_services_tab()
        self.setup_clients_tab()
        self.setup_payments_tab()
        self.setup_reports_tab()
        
        main_layout.addWidget(self.tab_widget)
    
    def setup_dashboard_tab(self):
        """Tableau de bord de l'hôtel"""
        dashboard_widget = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_widget)
        
        # Statistiques en haut
        stats_layout = QGridLayout()
        
        # Cartes de statistiques
        self.create_stat_card("Chambres occupées", "12/20", "#E74C3C", stats_layout, 0, 0)
        self.create_stat_card("Revenus du jour", "2,340 €", "#27AE60", stats_layout, 0, 1)
        self.create_stat_card("Taux d'occupation", "60%", "#3498DB", stats_layout, 0, 2)
        self.create_stat_card("Check-in aujourd'hui", "5", "#F39C12", stats_layout, 0, 3)
        
        # Calendrier d'occupation
        calendar_group = QGroupBox("Calendrier d'occupation")
        calendar_layout = QVBoxLayout(calendar_group)
        
        self.occupation_calendar = QCalendarWidget()
        calendar_layout.addWidget(self.occupation_calendar)
        
        # Réservations du jour
        today_reservations_group = QGroupBox("Réservations d'aujourd'hui")
        today_layout = QVBoxLayout(today_reservations_group)
        
        self.today_reservations_table = QTableWidget()
        self.today_reservations_table.setColumnCount(5)
        self.today_reservations_table.setHorizontalHeaderLabels([
            "Client", "Chambre", "Check-in", "Check-out", "Statut"
        ])
        
        today_layout.addWidget(self.today_reservations_table)
        
        dashboard_layout.addLayout(stats_layout)
        dashboard_layout.addWidget(calendar_group)
        dashboard_layout.addWidget(today_reservations_group)
        
        self.tab_widget.addTab(dashboard_widget, "📊 Tableau de bord")
    
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
    
    def setup_reservations_tab(self):
        """Gestion des réservations"""
        reservations_widget = QWidget()
        reservations_layout = QVBoxLayout(reservations_widget)
        
        # Barre d'outils
        toolbar_layout = QHBoxLayout()
        
        new_reservation_button = QPushButton("➕ Nouvelle Réservation")
        new_reservation_button.setStyleSheet("""
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
        
        edit_button = QPushButton("✏️ Modifier")
        cancel_button = QPushButton("❌ Annuler")
        
        toolbar_layout.addWidget(new_reservation_button)
        toolbar_layout.addWidget(edit_button)
        toolbar_layout.addWidget(cancel_button)
        toolbar_layout.addStretch()
        
        # Filtres
        filters_layout = QHBoxLayout()
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Toutes", "Confirmée", "Check-in", "Check-out", "Annulée"])
        
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate())
        
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate().addDays(30))
        
        filters_layout.addWidget(QLabel("Statut:"))
        filters_layout.addWidget(self.status_filter)
        filters_layout.addWidget(QLabel("Du:"))
        filters_layout.addWidget(self.date_from)
        filters_layout.addWidget(QLabel("Au:"))
        filters_layout.addWidget(self.date_to)
        filters_layout.addStretch()
        
        # Table des réservations
        self.reservations_table = QTableWidget()
        self.reservations_table.setColumnCount(8)
        self.reservations_table.setHorizontalHeaderLabels([
            "ID", "Client", "Chambre", "Check-in", "Check-out", "Nuits", "Total", "Statut"
        ])
        self.reservations_table.horizontalHeader().setStretchLastSection(True)
        
        reservations_layout.addLayout(toolbar_layout)
        reservations_layout.addLayout(filters_layout)
        reservations_layout.addWidget(self.reservations_table)
        
        self.tab_widget.addTab(reservations_widget, "📅 Réservations")
    
    def setup_rooms_tab(self):
        """Gestion des chambres"""
        rooms_widget = QWidget()
        rooms_layout = QVBoxLayout(rooms_widget)
        
        # Barre d'outils
        toolbar_layout = QHBoxLayout()
        
        add_room_button = QPushButton("➕ Nouvelle Chambre")
        add_room_button.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        
        edit_room_button = QPushButton("✏️ Modifier")
        delete_room_button = QPushButton("🗑️ Supprimer")
        
        toolbar_layout.addWidget(add_room_button)
        toolbar_layout.addWidget(edit_room_button)
        toolbar_layout.addWidget(delete_room_button)
        toolbar_layout.addStretch()
        
        # Vue grille des chambres
        rooms_scroll = QScrollArea()
        rooms_container = QWidget()
        self.rooms_grid_layout = QGridLayout(rooms_container)
        
        # Exemple de chambres
        self.create_room_cards()
        
        rooms_scroll.setWidget(rooms_container)
        rooms_scroll.setWidgetResizable(True)
        
        # Table détaillée des chambres
        self.rooms_table = QTableWidget()
        self.rooms_table.setColumnCount(7)
        self.rooms_table.setHorizontalHeaderLabels([
            "Numéro", "Type", "Capacité", "Prix/nuit", "Statut", "Nettoyage", "Actions"
        ])
        self.rooms_table.horizontalHeader().setStretchLastSection(True)
        
        # Splitter pour diviser la vue
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(rooms_scroll)
        splitter.addWidget(self.rooms_table)
        splitter.setSizes([300, 200])
        
        rooms_layout.addLayout(toolbar_layout)
        rooms_layout.addWidget(splitter)
        
        self.tab_widget.addTab(rooms_widget, "🏨 Chambres")
    
    def create_room_cards(self):
        """Créer les cartes des chambres"""
        room_statuses = [
            ("101", "Simple", "Libre", "#27AE60"),
            ("102", "Double", "Occupée", "#E74C3C"),
            ("103", "Suite", "Nettoyage", "#F39C12"),
            ("104", "Double", "Libre", "#27AE60"),
            ("105", "Simple", "Réservée", "#3498DB"),
            ("106", "Suite", "Occupée", "#E74C3C"),
        ]
        
        row, col = 0, 0
        for room_number, room_type, status, color in room_statuses:
            room_card = self.create_room_card(room_number, room_type, status, color)
            self.rooms_grid_layout.addWidget(room_card, row, col)
            
            col += 1
            if col >= 4:
                col = 0
                row += 1
    
    def create_room_card(self, number, room_type, status, color):
        """Créer une carte de chambre"""
        card = QFrame()
        card.setFixedSize(150, 120)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 10px;
                border: 2px solid #BDC3C7;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        number_label = QLabel(f"Ch. {number}")
        number_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        type_label = QLabel(room_type)
        type_label.setStyleSheet("color: white; font-size: 12px;")
        type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        status_label = QLabel(status)
        status_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(number_label)
        layout.addWidget(type_label)
        layout.addWidget(status_label)
        
        return card
    
    def setup_checkin_tab(self):
        """Gestion des check-in"""
        checkin_widget = QWidget()
        checkin_layout = QVBoxLayout(checkin_widget)
        
        # Titre
        title_label = QLabel("Check-in des clients")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #2C3E50;")
        
        # Formulaire de check-in
        form_group = QGroupBox("Informations de check-in")
        form_layout = QFormLayout(form_group)
        
        self.reservation_search = QLineEdit()
        self.reservation_search.setPlaceholderText("Rechercher par nom ou numéro de réservation...")
        
        self.client_name = QLineEdit()
        self.room_number = QComboBox()
        self.checkin_date = QDateEdit()
        self.checkin_date.setDate(QDate.currentDate())
        
        form_layout.addRow("Recherche réservation:", self.reservation_search)
        form_layout.addRow("Nom du client:", self.client_name)
        form_layout.addRow("Numéro de chambre:", self.room_number)
        form_layout.addRow("Date de check-in:", self.checkin_date)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        checkin_button = QPushButton("✅ Effectuer le check-in")
        checkin_button.setStyleSheet("""
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
        
        cancel_button = QPushButton("❌ Annuler")
        
        buttons_layout.addWidget(checkin_button)
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addStretch()
        
        checkin_layout.addWidget(title_label)
        checkin_layout.addWidget(form_group)
        checkin_layout.addLayout(buttons_layout)
        checkin_layout.addStretch()
        
        self.tab_widget.addTab(checkin_widget, "🔑 Check-in")
    
    def setup_checkout_tab(self):
        """Gestion des check-out"""
        checkout_widget = QWidget()
        checkout_layout = QVBoxLayout(checkout_widget)
        
        # Titre
        title_label = QLabel("Check-out des clients")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #2C3E50;")
        
        # Liste des chambres occupées
        occupied_group = QGroupBox("Chambres occupées")
        occupied_layout = QVBoxLayout(occupied_group)
        
        self.occupied_rooms_table = QTableWidget()
        self.occupied_rooms_table.setColumnCount(6)
        self.occupied_rooms_table.setHorizontalHeaderLabels([
            "Chambre", "Client", "Check-in", "Check-out prévu", "Services", "Total"
        ])
        
        occupied_layout.addWidget(self.occupied_rooms_table)
        
        # Boutons d'action
        checkout_buttons_layout = QHBoxLayout()
        
        checkout_button = QPushButton("🏃 Effectuer le check-out")
        checkout_button.setStyleSheet("""
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
        
        extend_stay_button = QPushButton("⏰ Prolonger le séjour")
        
        checkout_buttons_layout.addWidget(checkout_button)
        checkout_buttons_layout.addWidget(extend_stay_button)
        checkout_buttons_layout.addStretch()
        
        checkout_layout.addWidget(title_label)
        checkout_layout.addWidget(occupied_group)
        checkout_layout.addLayout(checkout_buttons_layout)
        
        self.tab_widget.addTab(checkout_widget, "🚪 Check-out")
    
    def setup_services_tab(self):
        """Gestion des services hôteliers"""
        services_widget = QWidget()
        services_layout = QVBoxLayout(services_widget)
        
        # Barre d'outils
        toolbar_layout = QHBoxLayout()
        
        add_service_button = QPushButton("➕ Nouveau Service")
        add_service_button.setStyleSheet("""
            QPushButton {
                background-color: #1ABC9C;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #16A085;
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
        
        self.tab_widget.addTab(services_widget, "🛎️ Services")
    
    def setup_clients_tab(self):
        """Gestion des clients"""
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
        self.clients_table.setColumnCount(6)
        self.clients_table.setHorizontalHeaderLabels([
            "ID", "Nom", "Email", "Téléphone", "Adresse", "Dernière visite"
        ])
        self.clients_table.horizontalHeader().setStretchLastSection(True)
        
        clients_layout.addLayout(toolbar_layout)
        clients_layout.addWidget(self.clients_table)
        
        self.tab_widget.addTab(clients_widget, "👥 Clients")
    
    def setup_payments_tab(self):
        """Gestion des paiements"""
        payments_widget = QWidget()
        payments_layout = QVBoxLayout(payments_widget)
        
        # Configuration des moyens de paiement
        config_group = QGroupBox("Configuration des moyens de paiement")
        config_layout = QVBoxLayout(config_group)
        
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
        self.payments_history_table.setColumnCount(6)
        self.payments_history_table.setHorizontalHeaderLabels([
            "Date", "Réservation", "Client", "Moyen", "Montant", "Statut"
        ])
        
        history_layout.addWidget(self.payments_history_table)
        
        payments_layout.addWidget(config_group)
        payments_layout.addWidget(history_group)
        
        self.tab_widget.addTab(payments_widget, "💳 Paiements")
    
    def setup_reports_tab(self):
        """Gestion des rapports"""
        reports_widget = QWidget()
        reports_layout = QVBoxLayout(reports_widget)
        
        # Zone de sélection des rapports
        reports_selection = QGroupBox("Sélection du rapport")
        selection_layout = QGridLayout(reports_selection)
        
        # Différents types de rapports
        occupancy_button = QPushButton("📊 Taux d'occupation")
        revenue_button = QPushButton("💰 Revenus")
        client_stats_button = QPushButton("👥 Statistiques clients")
        room_stats_button = QPushButton("🏨 Statistiques chambres")
        
        selection_layout.addWidget(occupancy_button, 0, 0)
        selection_layout.addWidget(revenue_button, 0, 1)
        selection_layout.addWidget(client_stats_button, 1, 0)
        selection_layout.addWidget(room_stats_button, 1, 1)
        
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
