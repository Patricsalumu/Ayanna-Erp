"""
Widget de l'onglet Clients - Gestion des clients de la boutique
"""

from typing import List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton, 
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, 
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout, QTextEdit,
    QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ayanna_erp.database.database_manager import DatabaseManager
from sqlalchemy import func
from ..model.models import ShopClient, ShopPanier, ShopPayment

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
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)  # Marges minimales
        main_layout.setSpacing(5)  # Espacement minimal entre les zones

        # === PARTIE GAUCHE : TABLEAU CLIENTS ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)  # Pas de marges internes

        header_group = QGroupBox("👥 Gestion des Clients")
        header_layout = QVBoxLayout(header_group)
        header_layout.setContentsMargins(5, 5, 5, 5)  # Marges minimales

        # Actions principales
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(5)
        self.new_client_btn = QPushButton("➕ Nouveau Client")
        self.new_client_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                font-weight: bold;
                padding: 2px 2px;
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
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.clicked.connect(self.load_clients)
        actions_layout.addWidget(refresh_btn)
        header_layout.addLayout(actions_layout)

        # Filtres de recherche
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(5)
        filter_layout.addWidget(QLabel("Recherche:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nom, téléphone, email...")
        self.search_input.textChanged.connect(self.search_clients)
        filter_layout.addWidget(self.search_input)
        header_layout.addLayout(filter_layout)
        left_layout.addWidget(header_group)

        # Tableau des clients
        self.clients_table = QTableWidget()
        self.clients_table.setColumnCount(6)
        self.clients_table.setHorizontalHeaderLabels([
            "ID", "Nom", "Prénom", "Téléphone", "Email", "Actions"
        ])
        header = self.clients_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.clients_table.setAlternatingRowColors(True)
        self.clients_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.clients_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Désactiver l'édition directe
        left_layout.addWidget(self.clients_table)

        # === PARTIE DROITE : DÉTAILS CLIENT ===
        self.detail_widget = QGroupBox("Détails du client")
        self.detail_layout = QVBoxLayout(self.detail_widget)
        self.detail_layout.setContentsMargins(5, 5, 5, 5)
        
        # Statistiques
        stats_container = QVBoxLayout()
        stats_title = QLabel("📊 Statistiques Globales")
        stats_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_title.setStyleSheet("font-weight: bold; color: #2C3E50; margin-bottom: 10px; font-size: 14px;")
        stats_container.addWidget(stats_title)
        
        # Grille des statistiques
        stats_grid = QGridLayout()
        stats_grid.setSpacing(8)
        
        # Ligne 1
        self.total_clients_label = QLabel("0")
        self.total_clients_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.total_clients_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.total_clients_label.setStyleSheet("""
            QLabel {
                border: 2px solid #3498DB;
                border-radius: 8px;
                background-color: #EBF5FF;
                padding: 12px;
                color: #2C3E50;
                min-width: 80px;
            }
        """)
        stats_grid.addWidget(QLabel("👥 Total Clients"), 0, 0, Qt.AlignmentFlag.AlignCenter)
        stats_grid.addWidget(self.total_clients_label, 1, 0)
        
        self.total_commandes_label = QLabel("0")
        self.total_commandes_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.total_commandes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.total_commandes_label.setStyleSheet("""
            QLabel {
                border: 2px solid #E74C3C;
                border-radius: 8px;
                background-color: #FDEDEC;
                padding: 12px;
                color: #2C3E50;
                min-width: 80px;
            }
        """)
        stats_grid.addWidget(QLabel("🛒 Total Commandes"), 0, 1, Qt.AlignmentFlag.AlignCenter)
        stats_grid.addWidget(self.total_commandes_label, 1, 1)
        
        # Ligne 2
        self.total_depense_label = QLabel("0.00 €")
        self.total_depense_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.total_depense_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.total_depense_label.setStyleSheet("""
            QLabel {
                border: 2px solid #27AE60;
                border-radius: 8px;
                background-color: #D5F4E6;
                padding: 12px;
                color: #2C3E50;
                min-width: 80px;
            }
        """)
        stats_grid.addWidget(QLabel("💰 Total Dépensé"), 2, 0, Qt.AlignmentFlag.AlignCenter)
        stats_grid.addWidget(self.total_depense_label, 3, 0)
        
        self.paniers_non_regles_label = QLabel("0")
        self.paniers_non_regles_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.paniers_non_regles_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.paniers_non_regles_label.setStyleSheet("""
            QLabel {
                border: 2px solid #F39C12;
                border-radius: 8px;
                background-color: #FEF5E7;
                padding: 12px;
                color: #2C3E50;
                min-width: 80px;
            }
        """)
        stats_grid.addWidget(QLabel("⚠️ Paniers Non Réglés"), 2, 1, Qt.AlignmentFlag.AlignCenter)
        stats_grid.addWidget(self.paniers_non_regles_label, 3, 1)
        
        # Ligne 3 - Montant non payé
        self.montant_non_paye_label = QLabel("0.00 €")
        self.montant_non_paye_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.montant_non_paye_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.montant_non_paye_label.setStyleSheet("""
            QLabel {
                border: 2px solid #9B59B6;
                border-radius: 8px;
                background-color: #F5EEF8;
                padding: 12px;
                color: #2C3E50;
                min-width: 80px;
            }
        """)
        stats_grid.addWidget(QLabel("💸 Montant Non Payé"), 4, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)
        stats_grid.addWidget(self.montant_non_paye_label, 5, 0, 1, 2)
        
        stats_container.addLayout(stats_grid)
        stats_container.addStretch()
        
        self.detail_layout.addLayout(stats_container)
        
        # Zone de détails du client sélectionné
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setPlainText("Sélectionnez un client pour voir les détails.")
        self.detail_text.setMinimumHeight(200)  # Hauteur minimale
        self.detail_layout.addWidget(self.detail_text, stretch=1)

        # Ajout au layout principal avec proportions 70/30
        main_layout.addWidget(left_widget, stretch=7)
        main_layout.addWidget(self.detail_widget, stretch=3)

        # Connexion du clic sur le tableau
        self.clients_table.cellClicked.connect(self.on_client_selected)
        # Connexion du double-clic pour édition
        self.clients_table.cellDoubleClicked.connect(self.on_client_double_clicked)

    def on_client_selected(self, row, column):
        """Gestionnaire de sélection d'un client"""
        client_id_item = self.clients_table.item(row, 0)
        if not client_id_item:
            self.detail_text.setPlainText("Aucun client sélectionné.")
            return
        
        client_id = int(client_id_item.text())
        try:
            with self.db_manager.get_session() as session:
                client = session.query(ShopClient).filter(ShopClient.id == client_id).first()
                if not client:
                    self.detail_text.setPlainText("Client introuvable.")
                    return
                
                # Calculer les statistiques spécifiques au client
                # Total commandes payées
                total_commandes = session.query(ShopPanier).filter(
                    ShopPanier.client_id == client.id,
                    ShopPanier.status.in_(['validé', 'payé', 'completed'])
                ).count()
                
                # Total dépensé (somme des montants des paniers payés)
                total_depense = session.query(func.sum(ShopPanier.total_final)).filter(
                    ShopPanier.client_id == client.id,
                    ShopPanier.status.in_(['validé', 'payé', 'completed'])
                ).scalar() or 0.0
                
                # Commandes non réglées
                paniers_non_regles = session.query(ShopPanier).filter(
                    ShopPanier.client_id == client.id,
                    ShopPanier.status.not_in(['validé', 'payé', 'completed'])
                ).all()
                
                commandes_non_reglees = len(paniers_non_regles)
                
                # Montant non réglé (total dû)
                montant_non_regle = 0.0
                for panier in paniers_non_regles:
                    montant_paye = session.query(func.sum(ShopPayment.amount)).filter(
                        ShopPayment.panier_id == panier.id
                    ).scalar() or 0.0
                    montant_du = float(panier.total_final or 0) - float(montant_paye)
                    if montant_du > 0:
                        montant_non_regle += montant_du
                
                # Dernière commande
                derniere_commande = session.query(ShopPanier).filter(
                    ShopPanier.client_id == client.id
                ).order_by(ShopPanier.created_at.desc()).first()
                
                # 5 dernières commandes
                dernieres_commandes = session.query(ShopPanier).filter(
                    ShopPanier.client_id == client.id
                ).order_by(ShopPanier.created_at.desc()).limit(5).all()
                
                # Affichage des détails du client
                details = f"<h3>📋 Informations du client</h3>"
                details += f"<b>Nom complet :</b> {client.nom} {client.prenom or ''}<br>"
                details += f"<b>ID :</b> {client.id}<br>"
                details += f"<b>Téléphone :</b> {client.telephone or 'Non renseigné'}<br>"
                details += f"<b>Email :</b> {client.email or 'Non renseigné'}<br>"
                details += f"<b>Adresse :</b> {client.adresse or 'Non renseignée'}<br>"
                details += f"<b>Ville :</b> {client.ville or 'Non renseignée'}<br>"
                details += f"<b>Type :</b> {client.type_client or 'Particulier'}<br>"
                details += f"<b>Limite crédit :</b> {client.credit_limit or 0} €<br>"
                details += f"<b>Solde compte :</b> {client.balance or 0} €<br>"
                details += f"<b>Statut :</b> {'Actif' if client.is_active else 'Inactif'}<br>"
                if client.created_at:
                    details += f"<b>Créé le :</b> {client.created_at.strftime('%d/%m/%Y')}<br>"
                if client.notes:
                    details += f"<b>Notes :</b> {client.notes}<br>"
                
                # Statistiques financières
                details += f"<h3>💰 Statistiques financières</h3>"
                details += f"<b>🛒 Total commandes :</b> {total_commandes}<br>"
                details += f"<b>💵 Total dépensé :</b> {total_depense:.2f} €<br>"
                details += f"<b>⚠️ Commandes non réglées :</b> {commandes_non_reglees}<br>"
                details += f"<b>💳 Montant dû :</b> {montant_non_regle:.2f} €<br>"
                
                # Dernière commande
                if derniere_commande:
                    details += f"<h3>🕒 Dernière commande</h3>"
                    details += f"<b>Référence :</b> {derniere_commande.numero_commande or 'N/A'}<br>"
                    details += f"<b>Date :</b> {derniere_commande.created_at.strftime('%d/%m/%Y %H:%M')}<br>"
                    details += f"<b>Montant :</b> {derniere_commande.total_final:.2f} €<br>"
                    details += f"<b>Statut :</b> {derniere_commande.status}<br>"
                
                # 5 dernières commandes
                if dernieres_commandes:
                    details += f"<h3>📜 5 dernières commandes</h3>"
                    for i, cmd in enumerate(dernieres_commandes, 1):
                        details += f"<b>{i}. {cmd.numero_commande or 'N/A'}</b> - "
                        details += f"{cmd.created_at.strftime('%d/%m/%Y')} - "
                        details += f"{cmd.total_final:.2f} € - {cmd.status}<br>"
                
                self.detail_text.setHtml(details)
                
        except Exception as e:
            self.detail_text.setPlainText(f"Erreur lors du chargement des détails: {str(e)}")

    def on_client_double_clicked(self, row, column):
        """Gestionnaire du double-clic pour ouvrir la fenêtre d'édition"""
        client_id_item = self.clients_table.item(row, 0)
        if not client_id_item:
            return
        
        client_id = int(client_id_item.text())
        try:
            with self.db_manager.get_session() as session:
                client = session.query(ShopClient).filter(ShopClient.id == client_id).first()
                if client:
                    self.edit_client(client)
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement du client: {str(e)}")
    
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
                self.update_statistics(clients)  # Mettre à jour les statistiques après recherche
                
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
        """Mettre à jour les statistiques globales"""
        try:
            with self.db_manager.get_session() as session:
                # Nombre total de clients
                total_clients = len(clients)
                self.total_clients_label.setText(str(total_clients))
                
                # Statistiques des paniers/commandes
                paniers = session.query(ShopPanier).filter(ShopPanier.pos_id == getattr(self.boutique_controller, 'pos_id', 1)).all()
                total_commandes = len([p for p in paniers if p.status in ['validé', 'payé', 'completed']])
                self.total_commandes_label.setText(str(total_commandes))
                
                # Calculer les montants
                total_depense = 0.0
                paniers_non_regles = 0
                montant_non_paye = 0.0
                
                for panier in paniers:
                    if panier.status in ['validé', 'payé', 'completed']:
                        # Paniers payés - ajouter au total dépensé
                        total_depense += float(panier.total_final or 0)
                    else:
                        # Paniers non réglés
                        paniers_non_regles += 1
                        
                        # Calculer le montant non payé pour ce panier
                        montant_paye = session.query(ShopPayment)\
                            .filter(ShopPayment.panier_id == panier.id)\
                            .with_entities(func.sum(ShopPayment.amount))\
                            .scalar() or 0
                        
                        montant_du = float(panier.total_final or 0) - float(montant_paye)
                        if montant_du > 0:
                            montant_non_paye += montant_du
                
                # Mettre à jour les labels
                self.total_depense_label.setText(f"{total_depense:.2f} €")
                self.paniers_non_regles_label.setText(str(paniers_non_regles))
                self.montant_non_paye_label.setText(f"{montant_non_paye:.2f} €")
                
        except Exception as e:
            print(f"Erreur lors du calcul des statistiques: {e}")
            # Valeurs par défaut en cas d'erreur
            self.total_clients_label.setText("0")
            self.total_commandes_label.setText("0")
            self.total_depense_label.setText("0.00 €")
            self.paniers_non_regles_label.setText("0")
            self.montant_non_paye_label.setText("0.00 €")
        
        # Gestion du message de détails
        if len(clients) == 0:
            self.detail_text.setPlainText("Aucun client disponible.")
        elif self.clients_table.currentRow() == -1:  # Aucune sélection
            self.detail_text.setPlainText("Sélectionnez un client pour voir les détails.")
    
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