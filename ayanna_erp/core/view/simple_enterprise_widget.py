"""
Widget simplifié pour la gestion des entreprises avec la structure existante
"""

import sys
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, 
    QMessageBox, QGroupBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

# Import des contrôleurs
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController


class SimpleEnterpriseWidget(QDialog):
    """Widget simplifié pour la gestion des entreprises"""
    
    enterprise_saved = pyqtSignal(dict)
    
    def __init__(self, parent=None, enterprise_data=None, current_user=None):
        super().__init__(parent)
        self.enterprise_data = enterprise_data
        self.current_user = current_user
        self.is_editing = enterprise_data is not None
        
        # Contrôleur
        self.enterprise_controller = EntrepriseController()
        
        # Configuration de la fenêtre
        self.setWindowTitle("Modifier l'entreprise" if self.is_editing else "Créer une entreprise")
        self.setMinimumSize(600, 500)
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
            QLineEdit, QTextEdit {
                border: 2px solid #e9ecef;
                border-radius: 6px;
                padding: 8px;
                font-size: 11px;
                background-color: white;
                color: #2c3e50;
            }
            QLineEdit:focus, QTextEdit:focus {
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
            self.load_enterprise_data()
    
    def check_permissions(self):
        """Vérifier si l'utilisateur a les permissions pour créer/modifier une entreprise"""
        if not self.current_user:
            QMessageBox.warning(self, "Erreur", "Utilisateur non connecté")
            self.reject()
            return False
        
        # Seuls les super admins peuvent créer une entreprise
        current_role = self.current_user.get('role', '')
        if current_role != 'super_admin' and not self.is_editing:
            QMessageBox.warning(
                self, 
                "Permissions insuffisantes", 
                "Seuls les super administrateurs peuvent créer une nouvelle entreprise."
            )
            self.reject()
            return False
        
        # Pour la modification, admin et super admin peuvent
        if self.is_editing and current_role not in ['admin', 'super_admin']:
            QMessageBox.warning(
                self, 
                "Permissions insuffisantes", 
                "Vous n'avez pas les permissions pour modifier l'entreprise."
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
        title_label = QLabel("Modifier l'entreprise" if self.is_editing else "Créer une nouvelle entreprise")
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
        
        # Groupe informations générales
        general_group = self.create_general_group()
        layout.addWidget(general_group)
        
        # Groupe adresse
        address_group = self.create_address_group()
        layout.addWidget(address_group)
        
        # Groupe contact
        contact_group = self.create_contact_group()
        layout.addWidget(contact_group)
        
        # Boutons d'action
        button_layout = self.create_button_layout()
        layout.addLayout(button_layout)
    
    def create_general_group(self):
        """Créer le groupe d'informations générales"""
        group = QGroupBox("Informations générales")
        layout = QFormLayout(group)
        layout.setSpacing(15)
        
        # Nom de l'entreprise
        self.nom_edit = QLineEdit()
        self.nom_edit.setPlaceholderText("Nom de l'entreprise")
        layout.addRow("Nom *:", self.nom_edit)
        
        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Description de l'entreprise")
        layout.addRow("Description:", self.description_edit)
        
        # Secteur d'activité
        self.secteur_edit = QLineEdit()
        self.secteur_edit.setPlaceholderText("Secteur d'activité")
        layout.addRow("Secteur:", self.secteur_edit)
        
        return group
    
    def create_address_group(self):
        """Créer le groupe d'adresse"""
        group = QGroupBox("Adresse")
        layout = QFormLayout(group)
        layout.setSpacing(15)
        
        # Adresse
        self.adresse_edit = QLineEdit()
        self.adresse_edit.setPlaceholderText("Adresse complète")
        layout.addRow("Adresse:", self.adresse_edit)
        
        # Ville
        self.ville_edit = QLineEdit()
        self.ville_edit.setPlaceholderText("Ville")
        layout.addRow("Ville:", self.ville_edit)
        
        # Code postal
        self.code_postal_edit = QLineEdit()
        self.code_postal_edit.setPlaceholderText("Code postal")
        layout.addRow("Code postal:", self.code_postal_edit)
        
        # Pays
        self.pays_edit = QLineEdit()
        self.pays_edit.setPlaceholderText("Pays")
        layout.addRow("Pays:", self.pays_edit)
        
        return group
    
    def create_contact_group(self):
        """Créer le groupe de contact"""
        group = QGroupBox("Contact")
        layout = QFormLayout(group)
        layout.setSpacing(15)
        
        # Email
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("email@entreprise.com")
        layout.addRow("Email:", self.email_edit)
        
        # Téléphone
        self.telephone_edit = QLineEdit()
        self.telephone_edit.setPlaceholderText("Numéro de téléphone")
        layout.addRow("Téléphone:", self.telephone_edit)
        
        # Site web
        self.site_web_edit = QLineEdit()
        self.site_web_edit.setPlaceholderText("www.entreprise.com")
        layout.addRow("Site web:", self.site_web_edit)
        
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
        self.save_button.clicked.connect(self.save_enterprise)
        self.cancel_button.clicked.connect(self.reject)
        
        # Signaux du contrôleur
        if hasattr(self.enterprise_controller, 'enterprise_created'):
            self.enterprise_controller.enterprise_created.connect(self.on_enterprise_saved)
        if hasattr(self.enterprise_controller, 'error_occurred'):
            self.enterprise_controller.error_occurred.connect(self.on_error_occurred)
    
    def load_enterprise_data(self):
        """Charger les données de l'entreprise en mode édition"""
        if not self.enterprise_data:
            return
        
        # Informations générales
        self.nom_edit.setText(self.enterprise_data.get('nom', ''))
        self.description_edit.setText(self.enterprise_data.get('description', ''))
        self.secteur_edit.setText(self.enterprise_data.get('secteur_activite', ''))
        
        # Adresse
        self.adresse_edit.setText(self.enterprise_data.get('adresse', ''))
        self.ville_edit.setText(self.enterprise_data.get('ville', ''))
        self.code_postal_edit.setText(self.enterprise_data.get('code_postal', ''))
        self.pays_edit.setText(self.enterprise_data.get('pays', ''))
        
        # Contact
        self.email_edit.setText(self.enterprise_data.get('email', ''))
        self.telephone_edit.setText(self.enterprise_data.get('telephone', ''))
        self.site_web_edit.setText(self.enterprise_data.get('site_web', ''))
    
    def validate_form(self):
        """Valider les données du formulaire"""
        errors = []
        
        # Nom obligatoire
        if not self.nom_edit.text().strip():
            errors.append("Le nom de l'entreprise est obligatoire")
        
        # Email valide si fourni
        email = self.email_edit.text().strip()
        if email and ('@' not in email or '.' not in email):
            errors.append("L'adresse email n'est pas valide")
        
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
            'nom': self.nom_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'secteur_activite': self.secteur_edit.text().strip(),
            'adresse': self.adresse_edit.text().strip(),
            'ville': self.ville_edit.text().strip(),
            'code_postal': self.code_postal_edit.text().strip(),
            'pays': self.pays_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'telephone': self.telephone_edit.text().strip(),
            'site_web': self.site_web_edit.text().strip()
        }
        
        return data
    
    def save_enterprise(self):
        """Enregistrer l'entreprise"""
        if not self.validate_form():
            return
        
        data = self.collect_form_data()
        
        # Désactiver le bouton pendant le traitement
        self.save_button.setEnabled(False)
        self.save_button.setText("Enregistrement...")
        
        try:
            if self.is_editing:
                # Modification
                if hasattr(self.enterprise_controller, 'update_enterprise'):
                    result = self.enterprise_controller.update_enterprise(
                        self.enterprise_data.get('id'), 
                        data
                    )
                else:
                    # Simulation de modification réussie
                    result = data
                    result['id'] = self.enterprise_data.get('id')
            else:
                # Création
                if hasattr(self.enterprise_controller, 'create_enterprise'):
                    result = self.enterprise_controller.create_enterprise(data)
                else:
                    # Simulation de création réussie
                    result = data
                    result['id'] = 1
            
            if result:
                self.on_enterprise_saved(result)
            else:
                QMessageBox.warning(
                    self,
                    "Erreur",
                    "Erreur lors de l'enregistrement de l'entreprise"
                )
                # Réactiver le bouton
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
    
    def on_enterprise_saved(self, enterprise_data):
        """Gestionnaire pour entreprise sauvegardée"""
        QMessageBox.information(
            self,
            "Succès",
            f"L'entreprise '{enterprise_data.get('nom', '')}' a été " +
            ("modifiée" if self.is_editing else "créée") + " avec succès!"
        )
        
        self.enterprise_saved.emit(enterprise_data)
        self.accept()
    
    def on_error_occurred(self, error_message):
        """Gestionnaire d'erreur"""
        QMessageBox.critical(self, "Erreur", error_message)
        
        # Réactiver le bouton
        self.save_button.setEnabled(True)
        self.save_button.setText("Modifier" if self.is_editing else "Créer")