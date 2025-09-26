"""
Widget de l'onglet Clients - Gestion des clients de la boutique
"""

from typing import List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton, 
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, 
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ayanna_erp.database.database_manager import DatabaseManager
from ..model.models import ShopClient


class ClientIndex(QWidget):
    """Widget de gestion des clients"""
    
    # Signaux
    client_updated = pyqtSignal()
    
    def __init__(self, boutique_controller, current_user):
        super().__init__()
        self.boutique_controller = boutique_controller
        self.current_user = current_user
        self.db_manager = DatabaseManager()
        
        self.setup_ui()
        self.load_clients()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # === HEADER ET ACTIONS ===
        header_group = QGroupBox("👥 Gestion des Clients")
        header_layout = QVBoxLayout(header_group)
        
        # Actions principales
        actions_layout = QHBoxLayout()
        
        self.new_client_btn = QPushButton("➕ Nouveau Client")
        self.new_client_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.new_client_btn.clicked.connect(self.create_new_client)
        actions_layout.addWidget(self.new_client_btn)
        
        actions_layout.addStretch()
        
        # Recherche
        actions_layout.addWidget(QLabel("Recherche:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nom, téléphone, email...")
        self.search_input.textChanged.connect(self.search_clients)
        actions_layout.addWidget(self.search_input)
        
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.clicked.connect(self.load_clients)
        actions_layout.addWidget(refresh_btn)
        
        header_layout.addLayout(actions_layout)
        
        # Statistiques
        stats_layout = QHBoxLayout()
        self.total_clients_label = QLabel("Total: 0 clients")
        self.total_clients_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        stats_layout.addWidget(self.total_clients_label)
        stats_layout.addStretch()
        header_layout.addLayout(stats_layout)
        
        main_layout.addWidget(header_group)
        
        # === TABLEAU DES CLIENTS ===
        self.clients_table = QTableWidget()
        self.clients_table.setColumnCount(6)
        self.clients_table.setHorizontalHeaderLabels([
            "ID", "Nom", "Prénom", "Téléphone", "Email", "Actions"
        ])
        
        # Configuration des colonnes
        header = self.clients_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Nom
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Prénom
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Téléphone
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Email
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Actions
        
        self.clients_table.setAlternatingRowColors(True)
        self.clients_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        main_layout.addWidget(self.clients_table)
    
    def load_clients(self):
        """Charger et afficher les clients"""
        try:
            with self.db_manager.get_session() as session:
                clients = self.boutique_controller.get_clients(session)
                self.populate_clients_table(clients)
                self.update_statistics(clients)
                
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des clients: {str(e)}")
    
    def search_clients(self):
        """Rechercher des clients"""
        search_term = self.search_input.text().strip()
        
        try:
            with self.db_manager.get_session() as session:
                clients = self.boutique_controller.get_clients(session, search_term=search_term)
                self.populate_clients_table(clients)
                
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de la recherche: {str(e)}")
    
    def populate_clients_table(self, clients: List[ShopClient]):
        """Peupler le tableau des clients"""
        self.clients_table.setRowCount(len(clients))
        
        for row, client in enumerate(clients):
            # ID
            id_item = QTableWidgetItem(str(client.id))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.clients_table.setItem(row, 0, id_item)
            
            # Nom
            self.clients_table.setItem(row, 1, QTableWidgetItem(client.nom))
            
            # Prénom
            prenom = client.prenom if client.prenom else "-"
            self.clients_table.setItem(row, 2, QTableWidgetItem(prenom))
            
            # Téléphone
            telephone = client.telephone if client.telephone else "-"
            self.clients_table.setItem(row, 3, QTableWidgetItem(telephone))
            
            # Email
            email = client.email if client.email else "-"
            self.clients_table.setItem(row, 4, QTableWidgetItem(email))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            # Bouton modifier
            edit_btn = QPushButton("✏️")
            edit_btn.setToolTip("Modifier le client")
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498DB;
                    color: white;
                    font-weight: bold;
                    padding: 5px;
                    border: none;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #2980B9;
                }
            """)
            edit_btn.clicked.connect(lambda checked, c=client: self.edit_client(c))
            actions_layout.addWidget(edit_btn)
            
            # Bouton historique
            history_btn = QPushButton("📊")
            history_btn.setToolTip("Historique des achats")
            history_btn.setStyleSheet("""
                QPushButton {
                    background-color: #9B59B6;
                    color: white;
                    font-weight: bold;
                    padding: 5px;
                    border: none;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #8E44AD;
                }
            """)
            history_btn.clicked.connect(lambda checked, c=client: self.view_client_history(c))
            actions_layout.addWidget(history_btn)
            
            self.clients_table.setCellWidget(row, 5, actions_widget)
    
    def update_statistics(self, clients: List[ShopClient]):
        """Mettre à jour les statistiques"""
        total = len(clients)
        self.total_clients_label.setText(f"Total: {total} clients")
    
    def create_new_client(self):
        """Créer un nouveau client"""
        dialog = ClientFormDialog(self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            client_data = dialog.get_client_data()
            
            try:
                with self.db_manager.get_session() as session:
                    new_client = self.boutique_controller.create_client(
                        session,
                        nom=client_data["nom"],
                        prenom=client_data.get("prenom"),
                        email=client_data.get("email"),
                        telephone=client_data.get("telephone"),
                        adresse=client_data.get("adresse")
                    )
                    
                    QMessageBox.information(self, "Succès", f"Client '{new_client.nom}' créé avec succès!")
                    self.load_clients()
                    self.client_updated.emit()
                    
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la création du client: {str(e)}")
    
    def edit_client(self, client: ShopClient):
        """Modifier un client existant"""
        dialog = ClientFormDialog(self, client)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            client_data = dialog.get_client_data()
            
            try:
                with self.db_manager.get_session() as session:
                    # Mise à jour du client
                    updated_client = session.query(ShopClient).filter(ShopClient.id == client.id).first()
                    if updated_client:
                        updated_client.nom = client_data["nom"]
                        updated_client.prenom = client_data.get("prenom")
                        updated_client.email = client_data.get("email")
                        updated_client.telephone = client_data.get("telephone")
                        updated_client.adresse = client_data.get("adresse")
                        
                        session.commit()
                        
                        QMessageBox.information(self, "Succès", f"Client '{updated_client.nom}' mis à jour avec succès!")
                        self.load_clients()
                        self.client_updated.emit()
                    else:
                        QMessageBox.warning(self, "Erreur", "Client introuvable.")
                        
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la mise à jour du client: {str(e)}")
    
    def view_client_history(self, client: ShopClient):
        """Afficher l'historique d'un client"""
        QMessageBox.information(
            self, "Historique Client", 
            f"Historique des achats pour: {client.nom} {client.prenom or ''}\n\n"
            "Cette fonctionnalité sera implémentée dans une version future."
        )


class ClientFormDialog(QDialog):
    """Dialog pour créer/modifier un client"""
    
    def __init__(self, parent=None, client: ShopClient = None):
        super().__init__(parent)
        self.client = client
        
        # Mode édition ou création
        self.is_editing = client is not None
        
        title = "Modifier le Client" if self.is_editing else "Nouveau Client"
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(400, 350)
        
        self.setup_ui()
        
        if self.is_editing:
            self.load_client_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Formulaire
        form_layout = QFormLayout()
        
        # Nom
        self.nom_input = QLineEdit()
        self.nom_input.setPlaceholderText("Nom du client (obligatoire)")
        form_layout.addRow("Nom *:", self.nom_input)
        
        # Prénom
        self.prenom_input = QLineEdit()
        self.prenom_input.setPlaceholderText("Prénom du client")
        form_layout.addRow("Prénom:", self.prenom_input)
        
        # Téléphone
        self.telephone_input = QLineEdit()
        self.telephone_input.setPlaceholderText("+243 XXX XXX XXX")
        form_layout.addRow("Téléphone:", self.telephone_input)
        
        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email@example.com")
        form_layout.addRow("Email:", self.email_input)
        
        # Adresse
        self.adresse_input = QTextEdit()
        self.adresse_input.setMaximumHeight(80)
        self.adresse_input.setPlaceholderText("Adresse complète")
        form_layout.addRow("Adresse:", self.adresse_input)
        
        layout.addLayout(form_layout)
        
        # Boutons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Validation
        buttons.button(QDialogButtonBox.StandardButton.Ok).clicked.connect(self.validate_form)
    
    def load_client_data(self):
        """Charger les données du client pour l'édition"""
        if self.client:
            self.nom_input.setText(self.client.nom)
            
            if self.client.prenom:
                self.prenom_input.setText(self.client.prenom)
            
            if self.client.telephone:
                self.telephone_input.setText(self.client.telephone)
            
            if self.client.email:
                self.email_input.setText(self.client.email)
            
            if self.client.adresse:
                self.adresse_input.setPlainText(self.client.adresse)
    
    def validate_form(self):
        """Valider le formulaire avant acceptation"""
        if not self.nom_input.text().strip():
            QMessageBox.warning(self, "Erreur", "Le nom du client est obligatoire.")
            return False
        
        return True
    
    def get_client_data(self):
        """Récupérer les données du client"""
        return {
            "nom": self.nom_input.text().strip(),
            "prenom": self.prenom_input.text().strip() or None,
            "telephone": self.telephone_input.text().strip() or None,
            "email": self.email_input.text().strip() or None,
            "adresse": self.adresse_input.toPlainText().strip() or None
        }
    
    def accept(self):
        """Accepter le dialog après validation"""
        if self.validate_form():
            super().accept()