"""
Widget simplifié pour la gestion des utilisateurs avec la structure existante
"""

import sys
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, 
    QMessageBox, QGroupBox, QScrollArea, QFrame, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

# Import des contrôleurs
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from ayanna_erp.core.controllers.simple_user_controller import SimpleUserController


class SimpleUserWidget(QDialog):
    """Widget simplifié pour la gestion des utilisateurs"""
    
    user_saved = pyqtSignal(dict)
    
    def __init__(self, parent=None, user_data=None, current_user=None):
        super().__init__(parent)
        self.user_data = user_data
        self.current_user = current_user
        self.is_editing = user_data is not None
        
        # Contrôleur
        self.user_controller = SimpleUserController()
        
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
            QPushButton#cancelButton {
                background-color: #95a5a6;
            }
            QPushButton#cancelButton:hover {
                background-color: #7f8c8d;
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
        layout.addWidget(title_label)
        
        # Formulaire principal
        form_group = self.create_form_group()
        layout.addWidget(form_group)
        
        # Boutons d'action
        button_layout = self.create_button_layout()
        layout.addLayout(button_layout)
    
    def create_form_group(self):
        """Créer le formulaire principal"""
        group = QGroupBox("Informations utilisateur")
        layout = QFormLayout(group)
        layout.setSpacing(15)
        
        # Nom d'utilisateur / Nom complet
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nom complet de l'utilisateur")
        layout.addRow("Nom complet *:", self.name_edit)
        
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
        layout.addRow("Confirmer:", self.password_confirm_edit)
        
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
            available_roles = ['admin', 'manager', 'user']
        else:
            # Manager peut seulement créer des utilisateurs standards
            available_roles = ['user']
        
        for role in available_roles:
            role_display = self.user_controller.ROLES[role]
            self.role_combo.addItem(role_display, role)
        
        layout.addRow("Rôle:", self.role_combo)
        
        if self.is_editing:
            note_label = QLabel("Laissez le mot de passe vide pour le conserver")
            note_label.setStyleSheet("color: #7f8c8d; font-style: italic; font-size: 10px;")
            layout.addRow("", note_label)
        
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
        self.user_controller.error_occurred.connect(self.on_error_occurred)
    
    def load_user_data(self):
        """Charger les données de l'utilisateur en mode édition"""
        if not self.user_data:
            return
        
        # Nom
        self.name_edit.setText(self.user_data.get('name', ''))
        
        # Email
        self.email_edit.setText(self.user_data.get('email', ''))
        
        # Rôle
        user_role = self.user_data.get('role', 'user')
        for i in range(self.role_combo.count()):
            if self.role_combo.itemData(i) == user_role:
                self.role_combo.setCurrentIndex(i)
                break
    
    def validate_form(self):
        """Valider les données du formulaire"""
        errors = []
        
        # Nom obligatoire
        if not self.name_edit.text().strip():
            errors.append("Le nom est obligatoire")
        
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
            'name': self.name_edit.text().strip(),
            'username': self.name_edit.text().strip(),  # Utiliser le nom comme username
            'email': self.email_edit.text().strip(),
            'role': self.role_combo.currentData()
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
                # Pour le moment, ne pas implémenter la modification
                QMessageBox.information(
                    self,
                    "Information",
                    "La modification des utilisateurs sera implémentée prochainement."
                )
                self.save_button.setEnabled(True)
                self.save_button.setText("Modifier")
                return
            else:
                # Création
                result = self.user_controller.create_user(data, current_role)
                success = result is not None
                
                if success:
                    self.on_user_saved(result)
            
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
            f"L'utilisateur '{user_data.get('name', '')}' a été " +
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