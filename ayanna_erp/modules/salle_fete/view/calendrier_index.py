"""
Onglet Calendrier pour le module Salle de Fête
Vue d'ensemble et calendrier des événements
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QTableWidget, QTableWidgetItem, QTableView,
                            QPushButton, QLineEdit, QLabel, QComboBox, 
                            QSpinBox, QDoubleSpinBox, QTextEdit, QMessageBox,
                            QGroupBox, QGridLayout, QListWidget, QSplitter,
                            QFrame, QScrollArea, QFormLayout, QCheckBox,
                            QDateTimeEdit, QCalendarWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDateTime, QDate
from PyQt6.QtGui import QFont, QPixmap, QIcon, QTextCharFormat, QColor
from decimal import Decimal
from datetime import datetime, timedelta
from ayanna_erp.database.database_manager import DatabaseManager, get_database_manager
from ayanna_erp.modules.salle_fete.controller.calendrier_controller import CalendrierController


class EventCalendarWidget(QWidget):
    """Widget calendrier pour visualiser les événements"""
    
    event_selected = pyqtSignal(int)  # Signal émis quand un événement est sélectionné
    reservation_requested = pyqtSignal(object)  # Signal pour demander création réservation
    
    def __init__(self, pos_id=1):
        super().__init__()
        self.calendrier_controller = CalendrierController(pos_id=pos_id)
        self.events_by_date = {}  # Cache des événements par date
        self.setup_ui()
        self.connect_signals()
        self.load_current_month()
    
    def setup_ui(self):
        """Configuration de l'interface"""
        layout = QVBoxLayout()
        
        # Calendrier
        self.calendar = QCalendarWidget()
        
        self.calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: white;
                alternate-background-color: #F8F9FA;
                selection-background-color: rgba(52, 152, 219, 0.3);
            }
            QCalendarWidget QToolButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 5px;
                border-radius: 3px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #2980B9;
            }
            QCalendarWidget QMenu {
                background-color: white;
                border: 1px solid #BDC3C7;
            }
            QCalendarWidget QTableView {
                selection-background-color: rgba(52, 152, 219, 0.2);
                color: black;
            }
            QCalendarWidget QTableView::item:selected {
                background-color: rgba(52, 152, 219, 0.3);
                color: black;
            }
        """)
        
        layout.addWidget(self.calendar)
        self.setLayout(layout)
    
    def connect_signals(self):
        """Connecter les signaux"""
        self.calendar.currentPageChanged.connect(self.on_month_changed)
        self.calendar.clicked.connect(self.on_date_clicked)
        self.calendar.activated.connect(self.on_date_double_clicked)  # Double-clic
        self.calendar.selectionChanged.connect(self.on_date_selection_changed)  # Changement de sélection
    
    def load_current_month(self):
        """Charger les événements du mois actuel"""
        current_date = self.calendar.selectedDate()
        year = current_date.year()
        month = current_date.month()
        self.load_events_for_month(year, month)
    
    def on_month_changed(self, year, month):
        """Callback quand le mois change"""
        print(f"📅 Changement de mois: {month}/{year}")
        self.load_events_for_month(year, month)
    
    def load_events_for_month(self, year, month):
        """Charger les événements d'un mois"""
        self.events_by_date = self.calendrier_controller.get_events_for_month(year, month)
        self.update_calendar_display()
    
    def update_calendar_display(self):
        """Mettre à jour l'affichage du calendrier avec les événements"""
        # Réinitialiser le format
        format_default = QTextCharFormat()
        self.calendar.setDateTextFormat(QDate(), format_default)
        
        # Appliquer les couleurs selon les événements
        # Créer un tooltip global avec tous les événements du mois
        global_tooltip = "📅 Événements du mois:\n\n"
        total_events = 0
        
        for date, events in self.events_by_date.items():
            qdate = QDate(date.year, date.month, date.day)
            
            # Déterminer la couleur selon le statut des événements
            color = self.get_date_color(events)
            
            # Créer le format pour cette date avec le nom du client
            format_date = QTextCharFormat()
            format_date.setBackground(QColor(color))
            format_date.setForeground(QColor("white"))
            format_date.setFontWeight(QFont.Weight.Bold)
            format_date.setFontPointSize(9)  # Taille de police lisible
            
            # Créer un texte personnalisé pour la cellule
            if events:
                total_events += len(events)
                
                # Ajouter au tooltip global
                global_tooltip += f"📅 {date.strftime('%d/%m')} - {len(events)} événement(s)\n"
                for event in events:
                    global_tooltip += f"   🎉 {event['client_name']} - {event['event_type']}\n"
                global_tooltip += "\n"
                
                # Prendre le premier client pour l'affichage
                main_client = events[0]['client_name']
                if len(main_client) > 10:
                    display_text = main_client[:8] + ".."
                else:
                    display_text = main_client
                
                # Ajouter un indicateur s'il y a plusieurs événements
                if len(events) > 1:
                    display_text += f" (+{len(events)-1})"
            
            self.calendar.setDateTextFormat(qdate, format_date)
        
        # Définir le tooltip global
        if total_events > 0:
            global_tooltip += f"\n📊 Total: {total_events} événements\n\n"
            global_tooltip += "💡 Cliquez sur une date pour voir les détails\n"
            global_tooltip += "💡 Double-cliquez pour créer une nouvelle réservation"
        else:
            global_tooltip = "📅 Aucun événement ce mois-ci\n\n"
            global_tooltip += "💡 Double-cliquez sur une date pour créer une réservation"
        
        self.calendar.setToolTip(global_tooltip)
        
        # Mettre à jour le tooltip pour la date actuellement sélectionnée
        self.update_current_tooltip()
    
    def get_date_color(self, events):
        """Déterminer la couleur d'une date selon ses événements"""
        if not events:
            return "#FFFFFF"  # Blanc par défaut
        
        # Priorité: Annulé > En attente > Confirmé > Passé
        has_cancelled = any(event['status'] in ['cancelled', 'Annulée'] for event in events)
        has_pending = any(event['status'] in ['draft', 'En attente'] for event in events)
        has_confirmed = any(event['status'] in ['confirmed', 'Confirmée'] for event in events)
        
        # Vérifier si l'événement est passé
        now = datetime.now()
        has_past = any(event['datetime'] < now for event in events)
        
        if has_cancelled:
            return "#E74C3C"  # Rouge pour annulé
        elif has_pending:
            return "#F39C12"  # Orange pour en attente
        elif has_past:
            return "#3498DB"  # Bleu pour passé
        elif has_confirmed:
            return "#27AE60"  # Vert pour confirmé
        else:
            return "#95A5A6"  # Gris par défaut
    
    def on_date_clicked(self, date):
        """Callback quand une date est cliquée"""
        date_py = date.toPyDate()
        if date_py in self.events_by_date:
            events = self.events_by_date[date_py]
            if events:
                # Émettre le signal avec l'ID du premier événement
                self.event_selected.emit(events[0]['id'])
    
    def on_date_selection_changed(self):
        """Callback quand la sélection de date change - met à jour le tooltip"""
        self.update_current_tooltip()
    
    def update_current_tooltip(self):
        """Mettre à jour le tooltip pour la date actuellement sélectionnée"""
        print('--------------DEBUG TOOLIP---------------')
        date = self.calendar.selectedDate()
        print(date)
        if date.isValid():
            date_key = date.toString("yyyy_MM_dd")
            tooltip_attr = f'tooltip_{date_key}'
            
            # Vérifier si on a un tooltip pour cette date
            if hasattr(self, tooltip_attr):
                tooltip_text = getattr(self, tooltip_attr)
                self.calendar.setToolTip(tooltip_text)
            else:
                # Pas d'événement pour cette date
                date_str = date.toString("dd/MM/yyyy")
                self.calendar.setToolTip(f"📅 {date_str}\nAucun événement\n\nDouble-cliquez pour créer une réservation")
    
    def on_date_double_clicked(self, date):
        """Callback quand une date est double-cliquée - ouvrir fenêtre de création"""
        self.open_reservation_form(date)
    
    def open_reservation_form(self, date):
        """Ouvrir la fenêtre de création de réservation pour une date"""
        # Émettre le signal vers la classe parent
        self.reservation_requested.emit(date.toPyDate())


class CalendrierIndex(QWidget):
    """Onglet principal pour la vue calendrier"""
    
    def __init__(self, main_controller, current_user):
        super().__init__()
        self.main_controller = main_controller
        self.current_user = current_user
        # Utiliser le pos_id du contrôleur principal
        pos_id = getattr(main_controller, 'pos_id', 1)
        self.calendrier_controller = CalendrierController(pos_id=pos_id)
        self.setup_ui()
        self.connect_signals()
        self.load_upcoming_events()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        calendar_layout = QHBoxLayout(self)
        
        # Splitter pour diviser l'écran
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Calendrier à gauche
        pos_id = getattr(self.main_controller, 'pos_id', 1)
        self.event_calendar = EventCalendarWidget(pos_id=pos_id)
        
        # Informations à droite
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Barre d'outils avec bouton de rafraîchissement
        toolbar_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("🔄 Rafraîchir")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
            QPushButton:pressed {
                background-color: #1F618D;
            }
        """)
        self.refresh_button.setToolTip("Actualiser les données du calendrier et de la liste des événements")
        
        toolbar_layout.addWidget(self.refresh_button)
        toolbar_layout.addStretch()  # Espacer vers la droite
        
        right_layout.addLayout(toolbar_layout)
        
        # Événements à venir (tous les événements du mois)
        upcoming_group = QGroupBox("📅 Événements à venir")
        upcoming_layout = QVBoxLayout(upcoming_group)
        
        self.upcoming_list = QListWidget()
        self.upcoming_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: white;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #ECF0F1;
                min-height: 40px;
            }
            QListWidget::item:selected {
                background-color: #3498DB;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #EBF3FD;
            }
        """)
        
        upcoming_layout.addWidget(self.upcoming_list)
        
        # Détails de l'événement sélectionné
        details_group = QGroupBox("📋 Détails de l'événement")
        details_layout = QVBoxLayout(details_group)
        
        self.event_details = QLabel("Cliquez sur une date du calendrier pour voir les détails")
        self.event_details.setWordWrap(True)
        self.event_details.setStyleSheet("""
            QLabel {
                padding: 15px;
                background-color: #F8F9FA;
                border: 1px solid #E9ECEF;
                border-radius: 5px;
                color: #6C757D;
                font-size: 13px;
                line-height: 1.4;
            }
        """)
        
        details_layout.addWidget(self.event_details)
        
        # Assemblage du layout de droite
        right_layout.addWidget(upcoming_group)
        right_layout.addWidget(details_group)
        
        # Ajout au splitter
        splitter.addWidget(self.event_calendar)
        splitter.addWidget(right_widget)
        splitter.setSizes([600, 400])
        
        calendar_layout.addWidget(splitter)
    
    def connect_signals(self):
        """Connecter les signaux"""
        self.event_calendar.event_selected.connect(self.on_event_selected)
        self.event_calendar.reservation_requested.connect(self.on_reservation_requested)
        self.calendrier_controller.events_loaded.connect(self.on_events_loaded)
        self.calendrier_controller.event_details_loaded.connect(self.on_event_details_loaded)
        self.calendrier_controller.error_occurred.connect(self.on_error_occurred)
        
        # Connecter le bouton de rafraîchissement
        self.refresh_button.clicked.connect(self.refresh_data)
    
    def load_upcoming_events(self):
        """Charger tous les prochains événements du mois"""
        self.calendrier_controller.get_upcoming_events(50)  # Augmenter la limite pour afficher plus d'événements
    
    def refresh_data(self):
        """Rafraîchir toutes les données du calendrier et des événements"""
        print("🔄 Rafraîchissement des données...")
        
        # Changer temporairement le texte du bouton pour indiquer le chargement
        original_text = self.refresh_button.text()
        self.refresh_button.setText("⏳ Actualisation...")
        self.refresh_button.setEnabled(False)
        
        try:
            # Rafraîchir le calendrier (événements du mois)
            self.event_calendar.load_current_month()
            
            # Rafraîchir la liste des événements à venir
            self.load_upcoming_events()
            
            # Effacer les détails de l'événement sélectionné
            self.event_details.setText("Cliquez sur une date du calendrier pour voir les détails")
            
            print("✅ Données rafraîchies avec succès")
            
        except Exception as e:
            print(f"❌ Erreur lors du rafraîchissement: {e}")
            QMessageBox.warning(self, "Erreur", f"Impossible de rafraîchir les données: {e}")
        
        finally:
            # Restaurer le bouton
            self.refresh_button.setText(original_text)
            self.refresh_button.setEnabled(True)
    
    def on_events_loaded(self, events):
        """Callback quand les événements à venir sont chargés"""
        self.upcoming_list.clear()
        
        for event in events:
            # Formatage de l'affichage
            date_str = event['datetime'].strftime("%d/%m/%Y %H:%M")
            status_emoji = self.get_status_emoji(event['status'])
            
            text = f"{status_emoji} {date_str} - {event['event_type']}\n"
            text += f"   Client: {event['client_name']}"
            if event['theme']:
                text += f"\n   Thème: {event['theme']}"
            
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, event)  # Stocker les données de l'événement
            
            self.upcoming_list.addItem(item)
    
    def on_event_selected(self, event_id):
        """Callback quand un événement est sélectionné dans le calendrier"""
        print(f"📋 Événement sélectionné: {event_id}")
        self.calendrier_controller.get_event_details(event_id)
    
    def on_reservation_requested(self, date):
        """Callback quand une réservation est demandée pour une date"""
        self.open_reservation_form(date)
    
    def open_reservation_form(self, date):
        """Ouvrir la fenêtre de création de réservation pour une date"""
        try:
            from ayanna_erp.modules.salle_fete.view.reservation_form import ReservationForm
            from PyQt6.QtCore import QDateTime, QDate, QTime
            
            # Obtenir le gestionnaire de base de données
            db_manager = get_database_manager()
            
            # Obtenir le pos_id du contrôleur principal
            pos_id = getattr(self.main_controller, 'pos_id', 1)
            
            # Créer la fenêtre de réservation avec les paramètres corrects
            reservation_form = ReservationForm(
                parent=self,
                reservation_data=None,  # Nouvelle réservation
                db_manager=db_manager,
                pos_id=pos_id
            )
            
            # Pré-remplir la date/heure avec la date sélectionnée à 18h00
            # Convertir la date en QDate puis créer QDateTime avec QTime
            qdate = QDate(date.year, date.month, date.day)
            qtime = QTime(18, 0)  # 18h00
            selected_datetime = QDateTime(qdate, qtime)
            reservation_form.event_datetime.setDateTime(selected_datetime)
            
            if reservation_form.exec():
                # Recharger les données après création
                self.refresh_data()
                
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de l'ouverture du formulaire: {str(e)}")
            print(f"❌ Erreur lors de l'ouverture du formulaire: {str(e)}")
    
    def on_event_details_loaded(self, details):
        """Callback quand les détails d'un événement sont chargés"""
        # Formatage des détails selon les spécifications
        details_text = f"""<h3 style="color: #2C3E50; margin-bottom: 15px;">🎉 {details['event_type']}</h3>
        
<div style="background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
    <p style="margin: 5px 0;"><strong>👤 Client:</strong> {details['client_name']}</p>
    <p style="margin: 5px 0;"><strong>📞 Téléphone:</strong> {details['phone']}</p>
    <p style="margin: 5px 0;"><strong>🎭 Type d'événement:</strong> {details['event_type']}</p>
    <p style="margin: 5px 0;"><strong>🎨 Thème:</strong> {details['theme'] or 'Non spécifié'}</p>
</div>

<div style="background-color: #E8F4FD; padding: 10px; border-radius: 5px; margin-top: 10px;">
    <p style="margin: 3px 0; font-size: 12px;"><strong>📅 Date:</strong> {details['datetime'].strftime('%d/%m/%Y à %H:%M')}</p>
    <p style="margin: 3px 0; font-size: 12px;"><strong>👥 Invités:</strong> {details['guests_count']}</p>
    <p style="margin: 3px 0; font-size: 12px;"><strong>📊 Statut:</strong> <span style="color: {self.get_status_color(details['status'])};">{details['status']}</span></p>
</div>"""
        
        self.event_details.setText(details_text)
    
    def on_error_occurred(self, error_message):
        """Callback en cas d'erreur"""
        QMessageBox.warning(self, "Erreur", error_message)
        print(f"❌ Erreur calendrier: {error_message}")
    
    def get_status_emoji(self, status):
        """Retourner l'emoji approprié pour un statut"""
        status_emojis = {
            'draft': '⏳',
            'En attente': '⏳',
            'confirmed': '✅',
            'Confirmée': '✅',
            'cancelled': '❌',
            'Annulée': '❌',
            'completed': '🏁',
            'Terminée': '🏁'
        }
        return status_emojis.get(status, '📝')
    
    def get_status_color(self, status):
        """Retourner la couleur appropriée pour un statut"""
        status_colors = {
            'draft': '#F39C12',
            'En attente': '#F39C12',
            'confirmed': '#27AE60',
            'Confirmée': '#27AE60',
            'cancelled': '#E74C3C',
            'Annulée': '#E74C3C',
            'completed': '#3498DB',
            'Terminée': '#3498DB'
        }
        return status_colors.get(status, '#95A5A6')
