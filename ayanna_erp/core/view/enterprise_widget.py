"""
Widget pour la gestion des entreprises
Interface de création et modification d'entreprise avec validation des rôles
"""

import sys
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox, 
    QMessageBox, QGroupBox, QScrollArea, QFrame, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon

# Import des contrôleurs
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
from ayanna_erp.core.controllers.user_controller import UserController


class EnterpriseWidget(QDialog):
    """Widget pour la gestion des entreprises"""
    
    enterprise_saved = pyqtSignal(dict)
    
    def __init__(self, parent=None, enterprise_data=None, current_user=None):
        super().__init__(parent)
        self.enterprise_data = enterprise_data
        self.current_user = current_user
        self.is_editing = enterprise_data is not None
        
        # Contrôleurs
        self.entreprise_controller = EntrepriseController()
        self.user_controller = UserController()
        
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
        
        # Seuls les super admins peuvent créer/modifier des entreprises
        if self.current_user.get('role') != 'super_admin':
            QMessageBox.warning(
                self, 
                "Permissions insuffisantes", 
                "Seul un super administrateur peut créer ou modifier une entreprise."
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
        content_layout.addWidget(title_label)
        
        # Informations générales
        general_group = self.create_general_info_group()
        content_layout.addWidget(general_group)
        
        # Informations de contact
        contact_group = self.create_contact_info_group()
        content_layout.addWidget(contact_group)
        
        # Paramètres
        settings_group = self.create_settings_group()
        content_layout.addWidget(settings_group)
        
        # Configuration du scroll
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        # Boutons d'action (en dehors du scroll)
        button_layout = self.create_button_layout()
        layout.addLayout(button_layout)
    
    def create_general_info_group(self):
        """Créer le groupe d'informations générales"""
        group = QGroupBox("Informations générales")
        layout = QFormLayout(group)
        layout.setSpacing(15)
        
        # Nom de l'entreprise
        self.nom_edit = QLineEdit()
        self.nom_edit.setPlaceholderText("Nom de l'entreprise")
        layout.addRow("Nom de l'entreprise *:", self.nom_edit)
        
        # Type d'entreprise
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "", "SARL", "SA", "SAS", "EURL", "Auto-entrepreneur", 
            "Association", "Coopérative", "Autre"
        ])
        layout.addRow("Type d'entreprise:", self.type_combo)
        
        # Secteur d'activité
        self.secteur_edit = QLineEdit()
        self.secteur_edit.setPlaceholderText("Secteur d'activité")
        layout.addRow("Secteur d'activité:", self.secteur_edit)
        
        # SIRET/SIREN
        self.siret_edit = QLineEdit()
        self.siret_edit.setPlaceholderText("Numéro SIRET ou SIREN")
        layout.addRow("SIRET/SIREN:", self.siret_edit)
        
        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Description de l'entreprise...")
        self.description_edit.setMaximumHeight(80)
        layout.addRow("Description:", self.description_edit)
        
        return group
    
    def create_contact_info_group(self):
        """Créer le groupe d'informations de contact"""
        group = QGroupBox("Informations de contact")
        layout = QFormLayout(group)
        layout.setSpacing(15)
        
        # Adresse
        self.adresse_edit = QLineEdit()
        self.adresse_edit.setPlaceholderText("Adresse complète")
        layout.addRow("Adresse:", self.adresse_edit)
        
        # Ville et Code postal (sur la même ligne)
        ville_layout = QHBoxLayout()
        self.ville_edit = QLineEdit()
        self.ville_edit.setPlaceholderText("Ville")
        self.code_postal_edit = QLineEdit()
        self.code_postal_edit.setPlaceholderText("Code postal")
        self.code_postal_edit.setMaximumWidth(120)
        ville_layout.addWidget(self.ville_edit)
        ville_layout.addWidget(self.code_postal_edit)
        layout.addRow("Ville / Code postal:", ville_layout)
        
        # Pays
        self.pays_edit = QLineEdit()
        self.pays_edit.setPlaceholderText("Pays")
        self.pays_edit.setText("France")  # Valeur par défaut
        layout.addRow("Pays:", self.pays_edit)
        
        # Téléphone
        self.telephone_edit = QLineEdit()
        self.telephone_edit.setPlaceholderText("Numéro de téléphone")
        layout.addRow("Téléphone:", self.telephone_edit)
        
        # Email
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("email@entreprise.com")
        layout.addRow("Email:", self.email_edit)
        
        # Site web
        self.site_web_edit = QLineEdit()
        self.site_web_edit.setPlaceholderText("https://www.entreprise.com")
        layout.addRow("Site web:", self.site_web_edit)
        
        return group
    
    def create_settings_group(self):
        """Créer le groupe de paramètres"""
        group = QGroupBox("Paramètres")
        layout = QFormLayout(group)
        layout.setSpacing(15)
        
        # Devise
        self.devise_combo = QComboBox()
        self.devise_combo.addItems([
            "EUR", "USD", "GBP", "CHF", "CAD", "JPY", "CNY", "AUD", "XOF", "XAF"
        ])
        self.devise_combo.setCurrentText("EUR")
        layout.addRow("Devise:", self.devise_combo)
        
        # Langue
        self.langue_combo = QComboBox()
        self.langue_combo.addItems([
            "Français", "English", "Español", "Deutsch", "Italiano"
        ])
        layout.addRow("Langue:", self.langue_combo)
        
        # Fuseau horaire
        self.fuseau_combo = QComboBox()
        self.fuseau_combo.addItems([
            "Europe/Paris", "Europe/London", "Europe/Berlin", "Europe/Madrid",
            "America/New_York", "America/Los_Angeles", "Asia/Tokyo", "Asia/Shanghai"
        ])
        layout.addRow("Fuseau horaire:", self.fuseau_combo)
        
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
        self.entreprise_controller.entreprise_created.connect(self.on_enterprise_saved)
        self.entreprise_controller.entreprise_updated.connect(self.on_enterprise_saved)
        self.entreprise_controller.error_occurred.connect(self.on_error_occurred)
    
    def load_enterprise_data(self):
        """Charger les données de l'entreprise en mode édition"""
        if not self.enterprise_data:
            return
        
        # Informations générales
        self.nom_edit.setText(self.enterprise_data.get('nom', ''))
        self.type_combo.setCurrentText(self.enterprise_data.get('type_entreprise', ''))
        self.secteur_edit.setText(self.enterprise_data.get('secteur_activite', ''))
        self.siret_edit.setText(self.enterprise_data.get('siret', ''))
        self.description_edit.setPlainText(self.enterprise_data.get('description', ''))
        
        # Informations de contact
        self.adresse_edit.setText(self.enterprise_data.get('adresse', ''))
        self.ville_edit.setText(self.enterprise_data.get('ville', ''))
        self.code_postal_edit.setText(self.enterprise_data.get('code_postal', ''))
        self.pays_edit.setText(self.enterprise_data.get('pays', ''))
        self.telephone_edit.setText(self.enterprise_data.get('telephone', ''))
        self.email_edit.setText(self.enterprise_data.get('email', ''))
        self.site_web_edit.setText(self.enterprise_data.get('site_web', ''))
        
        # Paramètres
        self.devise_combo.setCurrentText(self.enterprise_data.get('devise', 'EUR'))
        self.langue_combo.setCurrentText(self.enterprise_data.get('langue', 'Français'))
        self.fuseau_combo.setCurrentText(self.enterprise_data.get('fuseau_horaire', 'Europe/Paris'))
    
    def validate_form(self):
        """Valider les données du formulaire"""
        errors = []
        
        # Nom obligatoire
        if not self.nom_edit.text().strip():
            errors.append("Le nom de l'entreprise est obligatoire")
        
        # Validation email si fourni
        email = self.email_edit.text().strip()
        if email and '@' not in email:
            errors.append("L'adresse email n'est pas valide")
        
        # Validation site web si fourni
        site_web = self.site_web_edit.text().strip()
        if site_web and not (site_web.startswith('http://') or site_web.startswith('https://')):
            errors.append("L'URL du site web doit commencer par http:// ou https://")
        
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
        return {
            'nom': self.nom_edit.text().strip(),
            'type_entreprise': self.type_combo.currentText(),
            'secteur_activite': self.secteur_edit.text().strip(),
            'siret': self.siret_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'adresse': self.adresse_edit.text().strip(),
            'ville': self.ville_edit.text().strip(),
            'code_postal': self.code_postal_edit.text().strip(),
            'pays': self.pays_edit.text().strip(),
            'telephone': self.telephone_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'site_web': self.site_web_edit.text().strip(),
            'devise': self.devise_combo.currentText(),
            'langue': self.langue_combo.currentText(),
            'fuseau_horaire': self.fuseau_combo.currentText()
        }
    
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
                # Mise à jour
                success = self.entreprise_controller.update_entreprise(
                    self.enterprise_data['id'], 
                    data
                )
            else:
                # Création
                result = self.entreprise_controller.create_entreprise(data)
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


# Widget de liste des entreprises
class EnterpriseListWidget(QWidget):
    """Widget pour afficher la liste des entreprises"""
    
    def __init__(self, parent=None, current_user=None):
        super().__init__(parent)
        self.current_user = current_user
        self.entreprise_controller = EntrepriseController()
        
        self.init_ui()
        self.connect_signals()
        self.load_enterprises()
    
    def init_ui(self):
        """Initialiser l'interface"""
        layout = QVBoxLayout(self)
        
        # Titre et bouton d'ajout
        header_layout = QHBoxLayout()
        
        title = QLabel("Gestion des entreprises")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Bouton d'ajout (seulement pour super admin)
        if self.current_user and self.current_user.get('role') == 'super_admin':
            self.add_button = QPushButton("Nouvelle entreprise")
            self.add_button.clicked.connect(self.create_enterprise)
            header_layout.addWidget(self.add_button)
        
        layout.addLayout(header_layout)
        
        # Liste des entreprises (à implémenter avec QTableWidget)
        # Pour l'instant, juste un placeholder
        placeholder = QLabel("Liste des entreprises à implémenter...")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(placeholder)
    
    def connect_signals(self):
        """Connecter les signaux"""
        self.entreprise_controller.enterprises_loaded.connect(self.on_enterprises_loaded)
        self.entreprise_controller.error_occurred.connect(self.on_error_occurred)
    
    def load_enterprises(self):
        """Charger la liste des entreprises"""
        self.entreprise_controller.get_all_enterprises()
    
    def create_enterprise(self):
        """Ouvrir le dialogue de création d'entreprise"""
        dialog = EnterpriseWidget(self, current_user=self.current_user)
        dialog.enterprise_saved.connect(self.load_enterprises)
        dialog.exec()
    
    def on_enterprises_loaded(self, enterprises):
        """Gestionnaire pour entreprises chargées"""
        # À implémenter : afficher les entreprises dans un tableau
        pass
    
    def on_error_occurred(self, error_message):
        """Gestionnaire d'erreur"""
        QMessageBox.critical(self, "Erreur", error_message)