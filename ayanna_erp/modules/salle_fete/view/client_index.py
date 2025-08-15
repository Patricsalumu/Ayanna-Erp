"""
Onglet Clients pour le module Salle de Fête
Gestion et affichage des clients via contrôleur MVC
"""

import sys
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QTableWidget, QTableWidgetItem, 
                            QPushButton, QLineEdit, QLabel, QComboBox, 
                            QSpinBox, QDoubleSpinBox, QTextEdit, QMessageBox,
                            QGroupBox, QGridLayout, QListWidget, QSplitter,
                            QFrame, QScrollArea, QFormLayout, QCheckBox,
                            QDateTimeEdit, QHeaderView)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDateTime
from PyQt6.QtGui import QFont, QPixmap, QIcon
from decimal import Decimal
from datetime import datetime, timedelta

# Import du contrôleur client et du formulaire modal
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from controller.client_controller import ClientController
from .client_form import ClientForm


class ClientIndex(QWidget):
    """Onglet pour la gestion des clients"""
    
    def __init__(self, main_controller, current_user):
        super().__init__()
        self.main_controller = main_controller
        self.current_user = current_user
        
        # Initialiser le contrôleur client
        self.client_controller = ClientController(pos_id=getattr(main_controller, 'pos_id', 1))
        
        # Connecter les signaux du contrôleur
        self.client_controller.clients_loaded.connect(self.on_clients_loaded)
        self.client_controller.client_added.connect(self.on_client_added)
        self.client_controller.client_updated.connect(self.on_client_updated)
        self.client_controller.client_deleted.connect(self.on_client_deleted)
        self.client_controller.error_occurred.connect(self.on_error_occurred)
        
        self.selected_client = None
        self.clients_data = []
        
        self.setup_ui()
        self.connect_signals()
        
        # Charger les clients après initialisation
        if hasattr(main_controller, 'database_ready'):
            main_controller.database_ready.connect(self.load_clients)
        else:
            QTimer.singleShot(1000, self.load_clients)  # Fallback si pas de signal
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # Barre d'outils
        toolbar_layout = QHBoxLayout()
        
        # Boutons d'action
        self.add_client_button = QPushButton("➕ Nouveau client")
        self.add_client_button.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #219A52;
            }
        """)
        
        self.edit_client_button = QPushButton("✏️ Modifier")
        self.edit_client_button.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        
        self.delete_client_button = QPushButton("🗑️ Supprimer")
        self.delete_client_button.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        
        # Barre de recherche
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Rechercher un client...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498DB;
            }
        """)
        
        toolbar_layout.addWidget(self.add_client_button)
        toolbar_layout.addWidget(self.edit_client_button)
        toolbar_layout.addWidget(self.delete_client_button)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.search_input)
        
        # Splitter pour diviser en deux parties
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Table des clients (côté gauche)
        self.clients_table = QTableWidget()
        self.clients_table.setColumnCount(6)
        self.clients_table.setHorizontalHeaderLabels([
            "ID", "Nom", "Prénom", "Téléphone", "Email", "Nb. réservations"
        ])
        
        # Configuration du tableau
        self.clients_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.clients_table.setAlternatingRowColors(True)
        self.clients_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: white;
                gridline-color: #ECF0F1;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #E74C3C;
                color: white;
            }
            QHeaderView::section {
                background-color: #34495E;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        
        # Redimensionnement automatique des colonnes
        header = self.clients_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Nom
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Prénom
        
        # Zone de détails du client (côté droit)
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        # Informations personnelles
        personal_info_group = QGroupBox("Informations personnelles")
        personal_info_layout = QFormLayout(personal_info_group)
        
        self.client_name_label = QLabel("-")
        self.client_phone_label = QLabel("-")
        self.client_email_label = QLabel("-")
        self.client_address_label = QLabel("-")
        self.client_notes_label = QLabel("-")
        
        personal_info_layout.addRow("Nom complet:", self.client_name_label)
        personal_info_layout.addRow("Téléphone:", self.client_phone_label)
        personal_info_layout.addRow("Email:", self.client_email_label)
        personal_info_layout.addRow("Adresse:", self.client_address_label)
        personal_info_layout.addRow("Notes:", self.client_notes_label)
        
        # Historique des réservations
        history_group = QGroupBox("Historique des réservations")
        history_layout = QVBoxLayout(history_group)
        
        self.reservations_list = QListWidget()
        self.reservations_list.setStyleSheet("""
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
                background-color: #3498DB;
                color: white;
            }
        """)
        
        history_layout.addWidget(self.reservations_list)
        
        # Statistiques du client
        stats_group = QGroupBox("Statistiques")
        stats_layout = QFormLayout(stats_group)
        
        self.total_reservations_label = QLabel("0")
        self.total_spent_label = QLabel("0.00 €")
        self.last_reservation_label = QLabel("-")
        self.client_since_label = QLabel("-")
        
        stats_layout.addRow("Total réservations:", self.total_reservations_label)
        stats_layout.addRow("Total dépensé:", self.total_spent_label)
        stats_layout.addRow("Dernière réservation:", self.last_reservation_label)
        stats_layout.addRow("Client depuis:", self.client_since_label)
        
        # Ajouter tous les groupes à la zone de détails
        details_layout.addWidget(personal_info_group)
        details_layout.addWidget(history_group)
        details_layout.addWidget(stats_group)
        details_layout.addStretch()
        
        splitter.addWidget(self.clients_table)
        splitter.addWidget(details_widget)
        splitter.setSizes([600, 400])  # Répartition 60/40
        
        layout.addLayout(toolbar_layout)
        layout.addWidget(splitter)
    
    def connect_signals(self):
        """Connecter les signaux des boutons"""
        self.add_client_button.clicked.connect(self.add_new_client)
        self.edit_client_button.clicked.connect(self.edit_selected_client)
        self.delete_client_button.clicked.connect(self.delete_selected_client)
        self.search_input.textChanged.connect(self.filter_clients)
        self.clients_table.itemSelectionChanged.connect(self.on_client_selected)
    
    def load_clients(self):
        """Charger tous les clients depuis la base de données"""
        print("📋 Chargement des clients...")
        self.client_controller.get_all_clients()
    
    def on_clients_loaded(self, clients):
        """Callback quand les clients sont chargés"""
        self.clients_data = clients
        self.update_clients_table()
        print(f"✅ {len(clients)} clients chargés")
    
    def update_clients_table(self):
        """Mettre à jour la table des clients"""
        self.clients_table.setRowCount(len(self.clients_data))
        
        for row, client in enumerate(self.clients_data):
            # Compter les réservations du client (TODO: implémenter)
            nb_reservations = len(getattr(client, 'reservations', []))
            
            self.clients_table.setItem(row, 0, QTableWidgetItem(str(client.id)))
            self.clients_table.setItem(row, 1, QTableWidgetItem(client.nom))
            self.clients_table.setItem(row, 2, QTableWidgetItem(client.prenom))
            self.clients_table.setItem(row, 3, QTableWidgetItem(client.telephone))
            self.clients_table.setItem(row, 4, QTableWidgetItem(client.email or "-"))
            self.clients_table.setItem(row, 5, QTableWidgetItem(str(nb_reservations)))
            
        # Masquer la colonne ID
        self.clients_table.setColumnHidden(0, True)
    
    def on_client_selected(self):
        """Gérer la sélection d'un client"""
        current_row = self.clients_table.currentRow()
        if current_row >= 0 and current_row < len(self.clients_data):
            self.selected_client = self.clients_data[current_row]
            self.update_client_details()
        else:
            self.selected_client = None
            self.clear_client_details()
    
    def update_client_details(self):
        """Mettre à jour les détails du client sélectionné"""
        if not self.selected_client:
            return
            
        client = self.selected_client
        
        # Informations personnelles
        self.client_name_label.setText(f"{client.prenom} {client.nom}")
        self.client_phone_label.setText(client.telephone)
        self.client_email_label.setText(client.email or "-")
        
        address_parts = []
        if client.adresse:
            address_parts.append(client.adresse)
        if client.ville:
            address_parts.append(client.ville)
        if client.code_postal:
            address_parts.append(client.code_postal)
        self.client_address_label.setText(", ".join(address_parts) or "-")
        
        self.client_notes_label.setText(client.notes or "-")
        
        # Historique et statistiques (TODO: implémenter avec le contrôleur de réservations)
        self.load_client_reservations(client.id)
        
        # Statistiques
        self.total_reservations_label.setText(str(len(getattr(client, 'reservations', []))))
        self.total_spent_label.setText("0.00 €")  # TODO: calculer depuis les réservations
        self.last_reservation_label.setText("-")  # TODO: dernière réservation
        
        if client.created_at:
            self.client_since_label.setText(client.created_at.strftime("%d/%m/%Y"))
        else:
            self.client_since_label.setText("-")
    
    def clear_client_details(self):
        """Effacer les détails du client"""
        self.client_name_label.setText("-")
        self.client_phone_label.setText("-")
        self.client_email_label.setText("-")
        self.client_address_label.setText("-")
        self.client_notes_label.setText("-")
        
        self.reservations_list.clear()
        
        self.total_reservations_label.setText("0")
        self.total_spent_label.setText("0.00 €")
        self.last_reservation_label.setText("-")
        self.client_since_label.setText("-")
    
    def load_client_reservations(self, client_id):
        """Charger l'historique des réservations d'un client"""
        # TODO: Implémenter avec le contrôleur de réservations
        self.reservations_list.clear()
        
        # Pour l'instant, affichage vide
        self.reservations_list.addItem("Aucune réservation trouvée")
    
    def filter_clients(self):
        """Filtrer les clients selon le texte de recherche"""
        search_text = self.search_input.text().strip()
        
        if search_text:
            # Utiliser la recherche du contrôleur
            self.client_controller.search_clients(search_text)
        else:
            # Recharger tous les clients
            self.client_controller.get_all_clients()
    
    def add_new_client(self):
        """Ouvrir le formulaire pour un nouveau client"""
        try:
            dialog = ClientForm(self)
            dialog.client_saved.connect(self.on_client_form_saved)
            dialog.exec()
        except Exception as e:
            print(f"❌ Erreur lors de l'ouverture du formulaire: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir le formulaire client:\n{str(e)}")
    
    def edit_selected_client(self):
        """Modifier le client sélectionné"""
        if not self.selected_client:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un client à modifier.")
            return
        
        try:
            dialog = ClientForm(self, client_data=self.selected_client)
            dialog.client_saved.connect(self.on_client_form_saved)
            dialog.exec()
        except Exception as e:
            print(f"❌ Erreur lors de l'ouverture du formulaire: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir le formulaire client:\n{str(e)}")
    
    def delete_selected_client(self):
        """Supprimer le client sélectionné"""
        if not self.selected_client:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un client à supprimer.")
            return
        
        reply = QMessageBox.question(
            self, "Confirmation", 
            f"Êtes-vous sûr de vouloir supprimer le client {self.selected_client.prenom} {self.selected_client.nom} ?\n\n"
            "Cette action désactivera le client mais conservera l'historique.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.client_controller.delete_client(self.selected_client.id)
    
    def on_client_form_saved(self, client_data):
        """Callback quand un client est sauvegardé depuis le formulaire"""
        if 'id' in client_data and client_data['id']:
            # Modification
            self.client_controller.update_client(client_data['id'], client_data)
        else:
            # Création
            self.client_controller.create_client(client_data)
    
    def on_client_added(self, client):
        """Callback quand un client est ajouté"""
        QMessageBox.information(self, "Succès", f"Client {client.prenom} {client.nom} créé avec succès !")
        self.load_clients()  # Recharger la liste
    
    def on_client_updated(self, client):
        """Callback quand un client est modifié"""
        QMessageBox.information(self, "Succès", f"Client {client.prenom} {client.nom} modifié avec succès !")
        self.load_clients()  # Recharger la liste
        
    def on_client_deleted(self, client_id):
        """Callback quand un client est supprimé"""
        QMessageBox.information(self, "Succès", "Client supprimé avec succès !")
        self.load_clients()  # Recharger la liste
        self.clear_client_details()  # Effacer les détails
        
    def on_error_occurred(self, error_message):
        """Callback quand une erreur survient"""
        QMessageBox.critical(self, "Erreur", error_message)
        print(f"❌ Erreur client: {error_message}")
