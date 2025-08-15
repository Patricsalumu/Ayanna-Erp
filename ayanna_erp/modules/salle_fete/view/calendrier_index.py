"""
Onglet Calendrier pour le module Salle de Fête
Vue d'ensemble et calendrier des événements
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QTableWidget, QTableWidgetItem, 
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
        
        self.event_details = QLabel("Sélectionnez une date pour voir les événements")
        self.event_details.setWordWrap(True)
        
        details_layout.addWidget(self.event_details)
        
        layout.addWidget(self.calendar)
        layout.addWidget(details_group)
        
        self.setLayout(layout)


class CalendrierIndex(QWidget):
    """Onglet principal pour la vue calendrier"""
    
    def __init__(self, db_manager, current_user):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.setup_ui()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        calendar_layout = QHBoxLayout(self)
        
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
        
        self.upcoming_list = QListWidget()
        self.upcoming_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ECF0F1;
            }
            QListWidget::item:selected {
                background-color: #E74C3C;
                color: white;
            }
        """)
        
        upcoming_layout.addWidget(self.upcoming_list)
        
        # Actions rapides
        quick_actions_group = QGroupBox("Actions rapides")
        quick_actions_layout = QVBoxLayout(quick_actions_group)
        
        new_event_button = QPushButton("➕ Nouvel événement")
        new_event_button.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #219A52;
            }
        """)
        
        view_all_button = QPushButton("👁 Voir tous les événements")
        view_all_button.setStyleSheet("""
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
        
        quick_actions_layout.addWidget(new_event_button)
        quick_actions_layout.addWidget(view_all_button)
        quick_actions_layout.addStretch()
        
        # Assemblage du layout des statistiques
        stats_layout.addWidget(today_stats_group)
        stats_layout.addWidget(upcoming_group)
        stats_layout.addWidget(quick_actions_group)
        
        # Ajout au splitter
        splitter.addWidget(self.event_calendar)
        splitter.addWidget(stats_widget)
        splitter.setSizes([600, 400])
        
        calendar_layout.addWidget(splitter)
        
        # Chargement des données
        self.load_upcoming_events()
    
    def create_stat_card(self, title, value, color, layout, row, col):
        """Créer une carte de statistique"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border: none;
                border-radius: 10px;
                padding: 10px;
            }}
            QLabel {{
                color: white;
                font-weight: bold;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        card_layout.addWidget(value_label)
        card_layout.addWidget(title_label)
        
        layout.addWidget(card, row, col)
    
    def load_upcoming_events(self):
        """Charger les événements à venir"""
        # TODO: Implémenter le chargement des événements depuis la base de données
        sample_events = [
            "15/08/2025 - Mariage Johnson",
            "16/08/2025 - Anniversaire Martin", 
            "18/08/2025 - Réunion d'entreprise ABC",
            "20/08/2025 - Baptême Dubois"
        ]
        
        for event in sample_events:
            self.upcoming_list.addItem(event)
