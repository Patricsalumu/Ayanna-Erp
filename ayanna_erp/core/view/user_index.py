"""
Vue d'index pour la gestion des utilisateurs
Affiche la liste des utilisateurs avec les fonctionnalités CRUD selon les permissions
"""

import sys
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QMessageBox, QHeaderView, QAbstractItemView,
    QMenu, QFrame, QLineEdit, QComboBox, QCheckBox, QGroupBox,
    QFormLayout, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QAction, QIcon
from datetime import datetime

# Import des contrôleurs et widgets
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from ayanna_erp.core.controllers.simple_user_controller import SimpleUserController
from ayanna_erp.core.view.simple_user_widget import SimpleUserWidget


class UserIndexView(QWidget):
    """Vue principale pour la gestion des utilisateurs"""
    
    def __init__(self, parent=None, current_user=None):
        super().__init__(parent)
        self.current_user = current_user
        self.user_controller = SimpleUserController()
        self.users_data = []
        self.filtered_users = []
        
        # Configuration du style
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin: 10px 0;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                background-color: #f8f9fa;
            }
            QLabel {
                color: #2c3e50;
                font-size: 12px;
            }
            QLineEdit, QComboBox {
                border: 2px solid #e9ecef;
                border-radius: 6px;
                padding: 8px;
                font-size: 11px;
                background-color: white;
                color: #2c3e50;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #3498db;
                outline: none;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 11px;
                font-weight: 600;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton#addButton {
                background-color: #27ae60;
            }
            QPushButton#addButton:hover {
                background-color: #229954;
            }
            QPushButton#refreshButton {
                background-color: #f39c12;
            }
            QPushButton#refreshButton:hover {
                background-color: #e67e22;
            }
            QPushButton#deleteButton {
                background-color: #e74c3c;
            }
            QPushButton#deleteButton:hover {
                background-color: #c0392b;
            }
            QTableWidget {
                gridline-color: #e9ecef;
                background-color: white;
                selection-background-color: #3498db;
                selection-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e9ecef;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 12px;
                border: none;
                font-weight: bold;
                font-size: 11px;
            }
            QCheckBox {
                color: #2c3e50;
                font-size: 11px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #3498db;
                border-radius: 3px;
                background-color: #3498db;
            }
        """)
        
        self.init_ui()
        self.connect_signals()
        self.load_users()
    
    def init_ui(self):
        """Initialiser l'interface utilisateur"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # En-tête avec titre et boutons d'action
        header_layout = self.create_header_layout()
        layout.addLayout(header_layout)
        
        # Zone de filtres
        filter_widget = self.create_filter_layout()
        layout.addWidget(filter_widget)
        
        # Tableau des utilisateurs
        self.create_users_table(layout)
        
        # Zone d'informations/statistiques
        stats_widget = self.create_stats_layout()
        layout.addWidget(stats_widget)
    
    def create_header_layout(self):
        """Créer l'en-tête avec titre et boutons"""
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)
        
        # Titre principal
        title_label = QLabel("Gestion des Utilisateurs")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px 0;
            }
        """)
        header_layout.addWidget(title_label)
        
        # Espace flexible
        header_layout.addStretch()
        
        # Boutons d'action
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Bouton Actualiser
        self.refresh_button = QPushButton("Actualiser")
        self.refresh_button.setObjectName("refreshButton")
        self.refresh_button.clicked.connect(self.load_users)
        button_layout.addWidget(self.refresh_button)
        
        # Boutons selon les permissions
        current_role = self.current_user.get('role', '') if self.current_user else ''
        
        # Bouton Ajouter (pour admin et super admin)
        if self.user_controller.has_permission(current_role, 'admin'):
            self.add_button = QPushButton("Nouvel Utilisateur")
            self.add_button.setObjectName("addButton")
            self.add_button.clicked.connect(self.create_user)
            button_layout.addWidget(self.add_button)
        
        header_layout.addLayout(button_layout)
        return header_layout
    
    def create_filter_layout(self):
        """Créer la zone de filtres"""
        filter_group = QGroupBox("Filtres et Recherche")
        filter_layout = QHBoxLayout(filter_group)
        filter_layout.setSpacing(15)
        
        # Recherche par nom/email
        search_label = QLabel("Rechercher:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Nom d'utilisateur, email, nom ou prénom...")
        self.search_edit.textChanged.connect(self.filter_users)
        
        # Filtre par rôle
        role_label = QLabel("Rôle:")
        self.role_filter = QComboBox()
        self.role_filter.addItem("Tous les rôles", "")
        for role, display in self.user_controller.ROLES.items():
            self.role_filter.addItem(display, role)
        self.role_filter.currentTextChanged.connect(self.filter_users)
        
        # Filtre par statut
        status_label = QLabel("Statut:")
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Tous", "Actifs", "Inactifs"])
        self.status_filter.currentTextChanged.connect(self.filter_users)
        
        # Bouton de réinitialisation des filtres
        reset_button = QPushButton("Réinitialiser")
        reset_button.clicked.connect(self.reset_filters)
        
        # Assemblage
        filter_layout.addWidget(search_label)
        filter_layout.addWidget(self.search_edit, 2)
        filter_layout.addWidget(role_label)
        filter_layout.addWidget(self.role_filter, 1)
        filter_layout.addWidget(status_label)
        filter_layout.addWidget(self.status_filter, 1)
        filter_layout.addWidget(reset_button)
        
        return filter_group
    
    def create_users_table(self, layout):
        """Créer le tableau des utilisateurs"""
        # Tableau
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Configuration des colonnes
        columns = [
            'ID', 'Nom d\'utilisateur', 'Email', 'Prénom', 'Nom', 
            'Rôle', 'Actif', 'Créé le', 'Dernière connexion'
        ]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        
        # Ajustement des colonnes
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Username
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Email
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Prénom
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Nom
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Rôle
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Actif
        
        # Double-clic pour éditer
        self.table.itemDoubleClicked.connect(self.edit_selected_user)
        
        layout.addWidget(self.table)
    
    def create_stats_layout(self):
        """Créer la zone de statistiques"""
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding: 15px;
            }
        """)
        
        stats_layout = QHBoxLayout(stats_frame)
        
        # Statistiques des utilisateurs
        self.total_users_label = QLabel("Total: 0")
        self.active_users_label = QLabel("Actifs: 0")
        self.inactive_users_label = QLabel("Inactifs: 0")
        self.admins_label = QLabel("Admins: 0")
        
        # Style des labels de statistiques
        for label in [self.total_users_label, self.active_users_label, 
                     self.inactive_users_label, self.admins_label]:
            label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    color: #2c3e50;
                    padding: 5px 10px;
                    background-color: #ecf0f1;
                    border-radius: 4px;
                    margin: 0 5px;
                }
            """)
        
        stats_layout.addWidget(QLabel("Statistiques:"))
        stats_layout.addWidget(self.total_users_label)
        stats_layout.addWidget(self.active_users_label)
        stats_layout.addWidget(self.inactive_users_label)
        stats_layout.addWidget(self.admins_label)
        stats_layout.addStretch()
        
        return stats_frame
    
    def connect_signals(self):
        """Connecter les signaux"""
        self.user_controller.users_loaded.connect(self.on_users_loaded)
        self.user_controller.user_deleted.connect(self.on_user_deleted)
        self.user_controller.error_occurred.connect(self.on_error_occurred)
    
    def load_users(self):
        """Charger la liste des utilisateurs de l'entreprise courante"""
        # Récupérer l'ID de l'entreprise de l'utilisateur courant
        enterprise_id = None
        if self.current_user:
            enterprise_id = self.current_user.get('enterprise_id')
        
        if enterprise_id:
            self.user_controller.get_all_users(enterprise_id)
        else:
            # Si pas d'entreprise définie, charger tous les utilisateurs (pour super admin)
            self.user_controller.get_all_users()
    
    def create_user(self):
        """Ouvrir le dialogue de création d'utilisateur"""
        dialog = SimpleUserWidget(self, current_user=self.current_user)
        dialog.user_saved.connect(self.on_user_saved)
        dialog.exec()
    
    def edit_selected_user(self):
        """Éditer l'utilisateur sélectionné"""
        row = self.table.currentRow()
        if row >= 0 and row < len(self.filtered_users):
            user_data = self.filtered_users[row]
            
            # Vérifier les permissions pour éditer
            current_role = self.current_user.get('role', '') if self.current_user else ''
            if not self.user_controller.has_permission(current_role, 'admin'):
                QMessageBox.warning(
                    self, 
                    "Permissions insuffisantes", 
                    "Vous n'avez pas les permissions pour modifier les utilisateurs."
                )
                return
            
            dialog = SimpleUserWidget(self, user_data=user_data, current_user=self.current_user)
            dialog.user_saved.connect(self.on_user_saved)
            dialog.exec()
    
    def show_context_menu(self, position):
        """Afficher le menu contextuel"""
        if self.table.itemAt(position) is None:
            return
        
        current_role = self.current_user.get('role', '') if self.current_user else ''
        if not self.user_controller.has_permission(current_role, 'admin'):
            return
        
        menu = QMenu(self)
        
        # Action Modifier
        edit_action = QAction("Modifier", self)
        edit_action.triggered.connect(self.edit_selected_user)
        menu.addAction(edit_action)
        
        menu.addSeparator()
        
        # Action Supprimer
        delete_action = QAction("Supprimer", self)
        delete_action.triggered.connect(self.delete_selected_user)
        menu.addAction(delete_action)
        
        menu.exec(self.table.mapToGlobal(position))
    
    def delete_selected_user(self):
        """Supprimer l'utilisateur sélectionné"""
        row = self.table.currentRow()
        if row >= 0 and row < len(self.filtered_users):
            user_data = self.filtered_users[row]
            
            # Vérifier les permissions
            current_role = self.current_user.get('role', '') if self.current_user else ''
            if not self.user_controller.has_permission(current_role, 'admin'):
                QMessageBox.warning(
                    self, 
                    "Permissions insuffisantes", 
                    "Vous n'avez pas les permissions pour supprimer les utilisateurs."
                )
                return
            
            # Empêcher la suppression de son propre compte
            if self.current_user and user_data['id'] == self.current_user.get('id'):
                QMessageBox.warning(
                    self, 
                    "Action interdite", 
                    "Vous ne pouvez pas supprimer votre propre compte."
                )
                return
            
            reply = QMessageBox.question(
                self,
                "Confirmer la suppression",
                f"Voulez-vous vraiment supprimer l'utilisateur '{user_data['username']}' ?\n\n"
                f"Nom: {user_data.get('first_name', '')} {user_data.get('last_name', '')}\n"
                f"Email: {user_data.get('email', '')}\n"
                f"Rôle: {user_data.get('role_display', user_data.get('role', ''))}\n\n"
                "Cette action est irréversible.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.user_controller.delete_user(user_data['id'], current_role)
    
    def filter_users(self):
        """Filtrer les utilisateurs selon les critères"""
        if not self.users_data:
            return
        
        search_text = self.search_edit.text().lower()
        selected_role = self.role_filter.currentData()
        selected_status = self.status_filter.currentText()
        
        self.filtered_users = []
        
        for user in self.users_data:
            # Filtre par recherche textuelle
            if search_text:
                searchable_text = (
                    user.get('username', '') + ' ' +
                    user.get('email', '') + ' ' +
                    user.get('first_name', '') + ' ' +
                    user.get('last_name', '')
                ).lower()
                
                if search_text not in searchable_text:
                    continue
            
            # Filtre par rôle
            if selected_role and user.get('role') != selected_role:
                continue
            
            # Filtre par statut
            if selected_status == "Actifs" and not user.get('is_active', False):
                continue
            elif selected_status == "Inactifs" and user.get('is_active', True):
                continue
            
            self.filtered_users.append(user)
        
        self.populate_table()
        self.update_stats()
    
    def reset_filters(self):
        """Réinitialiser tous les filtres"""
        self.search_edit.clear()
        self.role_filter.setCurrentIndex(0)
        self.status_filter.setCurrentIndex(0)
        self.filter_users()
    
    def populate_table(self):
        """Remplir le tableau avec les utilisateurs filtrés"""
        self.table.setRowCount(0)
        
        for row, user in enumerate(self.filtered_users):
            self.table.insertRow(row)
            
            # ID
            self.table.setItem(row, 0, QTableWidgetItem(str(user['id'])))
            
            # Nom d'utilisateur
            self.table.setItem(row, 1, QTableWidgetItem(user['username']))
            
            # Email
            self.table.setItem(row, 2, QTableWidgetItem(user['email']))
            
            # Prénom
            self.table.setItem(row, 3, QTableWidgetItem(user.get('first_name', '')))
            
            # Nom
            self.table.setItem(row, 4, QTableWidgetItem(user.get('last_name', '')))
            
            # Rôle
            role_display = user.get('role_display', user.get('role', ''))
            role_item = QTableWidgetItem(role_display)
            
            # Couleur selon le rôle
            if user.get('role') == 'super_admin':
                role_item.setBackground(Qt.GlobalColor.red)
                role_item.setForeground(Qt.GlobalColor.white)
            elif user.get('role') == 'admin':
                role_item.setBackground(Qt.GlobalColor.darkBlue)
                role_item.setForeground(Qt.GlobalColor.white)
            
            self.table.setItem(row, 5, role_item)
            
            # Actif
            is_active = "✓ Oui" if user.get('is_active', False) else "✗ Non"
            active_item = QTableWidgetItem(is_active)
            if user.get('is_active', False):
                active_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                active_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(row, 6, active_item)
            
            # Date de création
            created_at = user.get('created_at')
            if created_at:
                if isinstance(created_at, datetime):
                    created_str = created_at.strftime("%d/%m/%Y")
                else:
                    created_str = str(created_at)
            else:
                created_str = "-"
            self.table.setItem(row, 7, QTableWidgetItem(created_str))
            
            # Dernière connexion
            last_login = user.get('last_login')
            if last_login:
                if isinstance(last_login, datetime):
                    login_str = last_login.strftime("%d/%m/%Y %H:%M")
                else:
                    login_str = str(last_login)
            else:
                login_str = "Jamais"
            self.table.setItem(row, 8, QTableWidgetItem(login_str))
    
    def update_stats(self):
        """Mettre à jour les statistiques affichées"""
        total = len(self.users_data)
        active = len([u for u in self.users_data if u.get('is_active', False)])
        inactive = total - active
        admins = len([u for u in self.users_data if u.get('role') in ['admin', 'super_admin']])
        
        self.total_users_label.setText(f"Total: {total}")
        self.active_users_label.setText(f"Actifs: {active}")
        self.inactive_users_label.setText(f"Inactifs: {inactive}")
        self.admins_label.setText(f"Admins: {admins}")
    
    def on_users_loaded(self, users):
        """Gestionnaire pour utilisateurs chargés"""
        self.users_data = users
        self.filtered_users = users.copy()
        self.populate_table()
        self.update_stats()
    
    def on_user_saved(self, user_data):
        """Gestionnaire pour utilisateur sauvegardé"""
        self.load_users()
    
    def on_user_deleted(self, user_id):
        """Gestionnaire pour utilisateur supprimé"""
        QMessageBox.information(self, "Succès", "Utilisateur supprimé avec succès!")
        self.load_users()
    
    def on_error_occurred(self, error_message):
        """Gestionnaire d'erreur"""
        QMessageBox.critical(self, "Erreur", error_message)