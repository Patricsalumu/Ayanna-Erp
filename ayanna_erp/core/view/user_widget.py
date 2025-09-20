"""
Widget pour la gestion des utilisateurs
Interface de création et modification d'utilisateurs avec gestion des rôles
"""

import sys
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox, 
    QMessageBox, QGroupBox, QScrollArea, QFrame, QWidget,
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QDateTime
from PyQt6.QtGui import QFont, QPixmap, QIcon, QAction
from datetime import datetime

# Import des contrôleurs
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from ayanna_erp.core.controllers.user_controller import UserController


class UserWidget(QDialog):
    """Widget pour la gestion des utilisateurs"""
    
    user_saved = pyqtSignal(dict)
    
    def __init__(self, parent=None, user_data=None, current_user=None):
        super().__init__(parent)
        self.user_data = user_data
        self.current_user = current_user
        self.is_editing = user_data is not None
        
        # Contrôleur
        self.user_controller = UserController()
        
        # Configuration de la fenêtre
        self.setWindowTitle("Modifier l'utilisateur" if self.is_editing else "Créer un utilisateur")
        self.setMinimumSize(500, 400)
        self.setModal(True)
        
        # Application du style
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin: 10px 0;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                background-color: #f8f9fa;
            }
            QLabel {
                color: #2c3e50;
                font-weight: 500;
                font-size: 11px;
            }
            QLineEdit, QTextEdit, QComboBox {
                border: 2px solid #e9ecef;
                border-radius: 6px;
                padding: 8px;
                font-size: 11px;
                background-color: white;
                color: #2c3e50;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
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
            QPushButton#cancelButton {
                background-color: #95a5a6;
            }
            QPushButton#cancelButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton#cancelButton:pressed {
                background-color: #566573;
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
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEzLjUgNEw2IDExLjVMMi41IDgiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }
        """)
        
        self.init_ui()
        self.connect_signals()
        
        # Vérifier les permissions
        if not self.check_permissions():
            return
        
        # Charger les données si en mode édition
        if self.is_editing:
            self.load_user_data()
    
    def check_permissions(self):
        """Vérifier si l'utilisateur a les permissions pour créer/modifier un utilisateur"""
        if not self.current_user:
            QMessageBox.warning(self, "Erreur", "Utilisateur non connecté")
            self.reject()
            return False
        
        # Seuls les admins et super admins peuvent gérer les utilisateurs
        current_role = self.current_user.get('role', '')
        if not self.user_controller.has_permission(current_role, 'admin'):
            QMessageBox.warning(
                self, 
                "Permissions insuffisantes", 
                "Vous n'avez pas les permissions pour gérer les utilisateurs."
            )
            self.reject()
            return False
        
        return True
    
    def init_ui(self):
        """Initialiser l'interface utilisateur"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Zone de défilement
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Widget principal du contenu
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        
        # Titre
        title_label = QLabel("Modifier l'utilisateur" if self.is_editing else "Créer un nouvel utilisateur")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 20px;
                padding: 10px;
                background-color: white;
                border-radius: 8px;
                border: 1px solid #bdc3c7;
            }
        """)
        content_layout.addWidget(title_label)
        
        # Informations de connexion
        auth_group = self.create_auth_info_group()
        content_layout.addWidget(auth_group)
        
        # Informations personnelles
        personal_group = self.create_personal_info_group()
        content_layout.addWidget(personal_group)
        
        # Paramètres
        settings_group = self.create_settings_group()
        content_layout.addWidget(settings_group)
        
        # Configuration du scroll
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        # Boutons d'action (en dehors du scroll)
        button_layout = self.create_button_layout()
        layout.addLayout(button_layout)
    
    def create_auth_info_group(self):
        """Créer le groupe d'informations de connexion"""
        group = QGroupBox("Informations de connexion")
        layout = QFormLayout(group)
        layout.setSpacing(15)
        
        # Nom d'utilisateur
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Nom d'utilisateur unique")
        layout.addRow("Nom d'utilisateur *:", self.username_edit)
        
        # Email
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("email@exemple.com")
        layout.addRow("Email *:", self.email_edit)
        
        # Mot de passe
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Mot de passe" + ("" if self.is_editing else " (requis)"))
        password_label = "Nouveau mot de passe:" if self.is_editing else "Mot de passe *:"
        layout.addRow(password_label, self.password_edit)
        
        # Confirmation mot de passe
        self.password_confirm_edit = QLineEdit()
        self.password_confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_confirm_edit.setPlaceholderText("Confirmer le mot de passe")
        layout.addRow("Confirmer le mot de passe:", self.password_confirm_edit)
        
        if self.is_editing:
            note_label = QLabel("Laissez vide pour conserver le mot de passe actuel")
            note_label.setStyleSheet("color: #7f8c8d; font-style: italic; font-size: 10px;")
            layout.addRow("", note_label)
        
        return group
    
    def create_personal_info_group(self):
        """Créer le groupe d'informations personnelles"""
        group = QGroupBox("Informations personnelles")
        layout = QFormLayout(group)
        layout.setSpacing(15)
        
        # Prénom
        self.first_name_edit = QLineEdit()
        self.first_name_edit.setPlaceholderText("Prénom")
        layout.addRow("Prénom:", self.first_name_edit)
        
        # Nom
        self.last_name_edit = QLineEdit()
        self.last_name_edit.setPlaceholderText("Nom de famille")
        layout.addRow("Nom:", self.last_name_edit)
        
        return group
    
    def create_settings_group(self):
        """Créer le groupe de paramètres"""
        group = QGroupBox("Paramètres et permissions")
        layout = QFormLayout(group)
        layout.setSpacing(15)
        
        # Rôle
        self.role_combo = QComboBox()
        
        # Définir les rôles disponibles selon l'utilisateur connecté
        current_role = self.current_user.get('role', '')
        available_roles = []
        
        if current_role == 'super_admin':
            # Super admin peut attribuer tous les rôles
            available_roles = list(self.user_controller.ROLES.keys())
        elif current_role == 'admin':
            # Admin peut attribuer des rôles inférieurs
            available_roles = ['admin', 'manager', 'user', 'guest']
        else:
            # Manager peut seulement créer des utilisateurs standards
            available_roles = ['user', 'guest']
        
        for role in available_roles:
            role_display = self.user_controller.ROLES[role]
            self.role_combo.addItem(role_display, role)
        
        layout.addRow("Rôle:", self.role_combo)
        
        # Compte actif
        self.is_active_checkbox = QCheckBox("Compte actif")
        self.is_active_checkbox.setChecked(True)
        layout.addRow("", self.is_active_checkbox)
        
        return group
    
    def create_button_layout(self):
        """Créer la zone des boutons"""
        layout = QHBoxLayout()
        layout.setSpacing(15)
        layout.addStretch()
        
        # Bouton Annuler
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.setObjectName("cancelButton")
        layout.addWidget(self.cancel_button)
        
        # Bouton Enregistrer
        self.save_button = QPushButton("Modifier" if self.is_editing else "Créer")
        layout.addWidget(self.save_button)
        
        return layout
    
    def connect_signals(self):
        """Connecter les signaux"""
        self.save_button.clicked.connect(self.save_user)
        self.cancel_button.clicked.connect(self.reject)
        
        # Signaux du contrôleur
        self.user_controller.user_created.connect(self.on_user_saved)
        self.user_controller.user_updated.connect(self.on_user_saved)
        self.user_controller.error_occurred.connect(self.on_error_occurred)
    
    def load_user_data(self):
        """Charger les données de l'utilisateur en mode édition"""
        if not self.user_data:
            return
        
        # Informations de connexion
        self.username_edit.setText(self.user_data.get('username', ''))
        self.email_edit.setText(self.user_data.get('email', ''))
        
        # Informations personnelles
        self.first_name_edit.setText(self.user_data.get('first_name', ''))
        self.last_name_edit.setText(self.user_data.get('last_name', ''))
        
        # Paramètres
        user_role = self.user_data.get('role', 'user')
        for i in range(self.role_combo.count()):
            if self.role_combo.itemData(i) == user_role:
                self.role_combo.setCurrentIndex(i)
                break
        
        self.is_active_checkbox.setChecked(self.user_data.get('is_active', True))
    
    def validate_form(self):
        """Valider les données du formulaire"""
        errors = []
        
        # Nom d'utilisateur obligatoire
        if not self.username_edit.text().strip():
            errors.append("Le nom d'utilisateur est obligatoire")
        
        # Email obligatoire et valide
        email = self.email_edit.text().strip()
        if not email:
            errors.append("L'adresse email est obligatoire")
        elif '@' not in email or '.' not in email:
            errors.append("L'adresse email n'est pas valide")
        
        # Mot de passe (obligatoire seulement pour création)
        password = self.password_edit.text()
        password_confirm = self.password_confirm_edit.text()
        
        if not self.is_editing and not password:
            errors.append("Le mot de passe est obligatoire")
        elif password and len(password) < 6:
            errors.append("Le mot de passe doit contenir au moins 6 caractères")
        elif password != password_confirm:
            errors.append("Les mots de passe ne correspondent pas")
        
        if errors:
            QMessageBox.warning(
                self,
                "Erreurs de validation",
                "\n".join([f"• {error}" for error in errors])
            )
            return False
        
        return True
    
    def collect_form_data(self):
        """Collecter les données du formulaire"""
        data = {
            'username': self.username_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'first_name': self.first_name_edit.text().strip(),
            'last_name': self.last_name_edit.text().strip(),
            'role': self.role_combo.currentData(),
            'is_active': self.is_active_checkbox.isChecked()
        }
        
        # Ajouter le mot de passe seulement s'il est fourni
        password = self.password_edit.text()
        if password:
            data['password'] = password
        
        return data
    
    def save_user(self):
        """Enregistrer l'utilisateur"""
        if not self.validate_form():
            return
        
        data = self.collect_form_data()
        
        # Désactiver le bouton pendant le traitement
        self.save_button.setEnabled(False)
        self.save_button.setText("Enregistrement...")
        
        try:
            current_role = self.current_user.get('role', '')
            
            if self.is_editing:
                # Mise à jour
                success = self.user_controller.update_user(
                    self.user_data['id'], 
                    data,
                    current_role
                )
            else:
                # Création
                result = self.user_controller.create_user(data, current_role)
                success = result is not None
            
            if not success:
                # Réactiver le bouton en cas d'erreur
                self.save_button.setEnabled(True)
                self.save_button.setText("Modifier" if self.is_editing else "Créer")
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors de l'enregistrement: {str(e)}"
            )
            # Réactiver le bouton
            self.save_button.setEnabled(True)
            self.save_button.setText("Modifier" if self.is_editing else "Créer")
    
    def on_user_saved(self, user_data):
        """Gestionnaire pour utilisateur sauvegardé"""
        QMessageBox.information(
            self,
            "Succès",
            f"L'utilisateur '{user_data.get('username', '')}' a été " +
            ("modifié" if self.is_editing else "créé") + " avec succès!"
        )
        
        self.user_saved.emit(user_data)
        self.accept()
    
    def on_error_occurred(self, error_message):
        """Gestionnaire d'erreur"""
        QMessageBox.critical(self, "Erreur", error_message)
        
        # Réactiver le bouton
        self.save_button.setEnabled(True)
        self.save_button.setText("Modifier" if self.is_editing else "Créer")


# Widget de liste des utilisateurs
class UserListWidget(QWidget):
    """Widget pour afficher la liste des utilisateurs"""
    
    def __init__(self, parent=None, current_user=None):
        super().__init__(parent)
        self.current_user = current_user
        self.user_controller = UserController()
        self.users_data = []
        
        self.init_ui()
        self.connect_signals()
        self.load_users()
    
    def init_ui(self):
        """Initialiser l'interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Titre et bouton d'ajout
        header_layout = QHBoxLayout()
        
        title = QLabel("Gestion des utilisateurs")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Bouton d'ajout (seulement pour admin et super admin)
        current_role = self.current_user.get('role', '') if self.current_user else ''
        if self.user_controller.has_permission(current_role, 'admin'):
            self.add_button = QPushButton("Nouvel utilisateur")
            self.add_button.clicked.connect(self.create_user)
            header_layout.addWidget(self.add_button)
        
        layout.addLayout(header_layout)
        
        # Tableau des utilisateurs
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Configuration des colonnes
        columns = ['ID', 'Nom d\'utilisateur', 'Email', 'Nom complet', 'Rôle', 'Actif', 'Créé le', 'Dernière connexion']
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        
        # Ajustement des colonnes
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Username
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Email
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Nom complet
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Rôle
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Actif
        
        layout.addWidget(self.table)
        
        # Style du tableau
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e9ecef;
                background-color: white;
                selection-background-color: #3498db;
                selection-color: white;
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
                background-color: #f8f9fa;
                color: #2c3e50;
                padding: 10px;
                border: 1px solid #e9ecef;
                font-weight: bold;
            }
        """)
    
    def connect_signals(self):
        """Connecter les signaux"""
        self.user_controller.users_loaded.connect(self.on_users_loaded)
        self.user_controller.user_deleted.connect(self.on_user_deleted)
        self.user_controller.error_occurred.connect(self.on_error_occurred)
        
        # Double-clic pour éditer
        self.table.itemDoubleClicked.connect(self.edit_selected_user)
    
    def load_users(self):
        """Charger la liste des utilisateurs"""
        self.user_controller.get_all_users()
    
    def create_user(self):
        """Ouvrir le dialogue de création d'utilisateur"""
        dialog = UserWidget(self, current_user=self.current_user)
        dialog.user_saved.connect(self.load_users)
        dialog.exec()
    
    def edit_selected_user(self):
        """Éditer l'utilisateur sélectionné"""
        row = self.table.currentRow()
        if row >= 0 and row < len(self.users_data):
            user_data = self.users_data[row]
            dialog = UserWidget(self, user_data=user_data, current_user=self.current_user)
            dialog.user_saved.connect(self.load_users)
            dialog.exec()
    
    def show_context_menu(self, position):
        """Afficher le menu contextuel"""
        if self.table.itemAt(position) is None:
            return
        
        current_role = self.current_user.get('role', '') if self.current_user else ''
        if not self.user_controller.has_permission(current_role, 'admin'):
            return
        
        menu = QMenu(self)
        
        edit_action = QAction("Modifier", self)
        edit_action.triggered.connect(self.edit_selected_user)
        menu.addAction(edit_action)
        
        delete_action = QAction("Supprimer", self)
        delete_action.triggered.connect(self.delete_selected_user)
        menu.addAction(delete_action)
        
        menu.exec(self.table.mapToGlobal(position))
    
    def delete_selected_user(self):
        """Supprimer l'utilisateur sélectionné"""
        row = self.table.currentRow()
        if row >= 0 and row < len(self.users_data):
            user_data = self.users_data[row]
            
            reply = QMessageBox.question(
                self,
                "Confirmer la suppression",
                f"Voulez-vous vraiment supprimer l'utilisateur '{user_data['username']}' ?\n\n"
                "Cette action est irréversible.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                current_role = self.current_user.get('role', '') if self.current_user else ''
                self.user_controller.delete_user(user_data['id'], current_role)
    
    def on_users_loaded(self, users):
        """Gestionnaire pour utilisateurs chargés"""
        self.users_data = users
        
        # Vider le tableau
        self.table.setRowCount(0)
        
        # Remplir le tableau
        for row, user in enumerate(users):
            self.table.insertRow(row)
            
            # ID
            self.table.setItem(row, 0, QTableWidgetItem(str(user['id'])))
            
            # Nom d'utilisateur
            self.table.setItem(row, 1, QTableWidgetItem(user['username']))
            
            # Email
            self.table.setItem(row, 2, QTableWidgetItem(user['email']))
            
            # Nom complet
            full_name = user.get('full_name', f"{user.get('first_name', '')} {user.get('last_name', '')}").strip()
            if not full_name:
                full_name = "-"
            self.table.setItem(row, 3, QTableWidgetItem(full_name))
            
            # Rôle
            role_display = user.get('role_display', user.get('role', ''))
            self.table.setItem(row, 4, QTableWidgetItem(role_display))
            
            # Actif
            is_active = "Oui" if user.get('is_active', False) else "Non"
            self.table.setItem(row, 5, QTableWidgetItem(is_active))
            
            # Date de création
            created_at = user.get('created_at')
            if created_at:
                if isinstance(created_at, datetime):
                    created_str = created_at.strftime("%d/%m/%Y %H:%M")
                else:
                    created_str = str(created_at)
            else:
                created_str = "-"
            self.table.setItem(row, 6, QTableWidgetItem(created_str))
            
            # Dernière connexion
            last_login = user.get('last_login')
            if last_login:
                if isinstance(last_login, datetime):
                    login_str = last_login.strftime("%d/%m/%Y %H:%M")
                else:
                    login_str = str(last_login)
            else:
                login_str = "Jamais"
            self.table.setItem(row, 7, QTableWidgetItem(login_str))
    
    def on_user_deleted(self, user_id):
        """Gestionnaire pour utilisateur supprimé"""
        QMessageBox.information(self, "Succès", "Utilisateur supprimé avec succès!")
        self.load_users()
    
    def on_error_occurred(self, error_message):
        """Gestionnaire d'erreur"""
        QMessageBox.critical(self, "Erreur", error_message)