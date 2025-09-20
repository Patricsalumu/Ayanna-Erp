"""
Widget pour la gestion des entreprises utilisant uniquement les champs du modèle DB
"""

import sys
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, 
    QMessageBox, QGroupBox, QFrame, QFileDialog, QScrollArea, QWidget, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

# Import des contrôleurs
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
from ayanna_erp.core.utils.image_utils import ImageUtils


class EnterpriseFormWidget(QDialog):
    """Widget pour la gestion des entreprises avec champs du modèle DB"""
    
    enterprise_saved = pyqtSignal(dict)
    
    def __init__(self, parent=None, enterprise_data=None, mode="create"):
        super().__init__(parent)
        self.enterprise_data = enterprise_data
        self.mode = mode  # "create" ou "edit"
        self.logo_blob = None  # Stockage temporaire du logo
        
        # Contrôleur
        self.enterprise_controller = EntrepriseController()
        
        # Configuration de la fenêtre
        self.setWindowTitle("Modifier l'entreprise" if mode == "edit" else "Créer une entreprise")
        self.setMinimumSize(650, 600)  # Augmenté pour le scroll
        self.resize(700, 650)  # Taille par défaut
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
                min-width: 120px;
            }
            QLineEdit, QTextEdit {
                border: 2px solid #e9ecef;
                border-radius: 6px;
                padding: 8px;
                font-size: 11px;
                background-color: white;
                color: #2c3e50;
                min-height: 20px;
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
            QPushButton#logoButton {
                background-color: #9b59b6;
            }
            QPushButton#logoButton:hover {
                background-color: #8e44ad;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background-color: #f8f9fa;
            }
        """)
        
        self.init_ui()
        self.populate_fields()
    
    def init_ui(self):
        """Initialiser l'interface utilisateur"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Titre principal
        title = QLabel(f"{'Modification' if self.mode == 'edit' else 'Création'} d'une Entreprise")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 15px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        # Zone de scroll pour le contenu
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Widget de contenu
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(15, 15, 15, 15)
        
        # Groupes de champs basés sur le modèle DB
        content_layout.addWidget(self.create_general_info_group())
        content_layout.addWidget(self.create_contact_info_group())
        content_layout.addWidget(self.create_legal_info_group())
        content_layout.addWidget(self.create_branding_group())
        
        # Spacer pour pousser le contenu vers le haut
        content_layout.addStretch()
        
        # Ajouter le widget de contenu à la zone de scroll
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # Boutons d'action en bas (fixes, pas dans le scroll)
        main_layout.addWidget(self.create_button_layout())
    
    def create_general_info_group(self):
        """Créer le groupe des informations générales"""
        group = QGroupBox("Informations Générales")
        layout = QFormLayout()
        
        # Nom (obligatoire selon le modèle)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nom de l'entreprise (obligatoire)")
        layout.addRow("Nom *:", self.name_edit)
        
        # Adresse
        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("Adresse complète de l'entreprise")
        layout.addRow("Adresse:", self.address_edit)
        
        # Devise
        self.currency_edit = QComboBox()
        self.currency_edit.addItems(["USD", "FC"])
        self.currency_edit.setCurrentText("USD")  # Valeur par défaut
        layout.addRow("Devise:", self.currency_edit)
        
        group.setLayout(layout)
        return group
    
    def create_contact_info_group(self):
        """Créer le groupe des informations de contact"""
        group = QGroupBox("Informations de Contact")
        layout = QFormLayout()
        
        # Téléphone
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("Numéro de téléphone principal")
        layout.addRow("Téléphone:", self.phone_edit)
        
        # Email
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Adresse email principale")
        layout.addRow("Email:", self.email_edit)
        
        group.setLayout(layout)
        return group
    
    def create_legal_info_group(self):
        """Créer le groupe des informations légales"""
        group = QGroupBox("Informations Légales")
        layout = QFormLayout()
        
        # RCCM
        self.rccm_edit = QLineEdit()
        self.rccm_edit.setPlaceholderText("Numéro RCCM")
        layout.addRow("RCCM:", self.rccm_edit)
        
        # ID National
        self.id_nat_edit = QLineEdit()
        self.id_nat_edit.setPlaceholderText("Identifiant national")
        layout.addRow("ID National:", self.id_nat_edit)
        
        group.setLayout(layout)
        return group
    
    def create_branding_group(self):
        """Créer le groupe des informations de marque"""
        group = QGroupBox("Image de Marque")
        layout = QFormLayout()
        
        # Slogan
        self.slogan_edit = QTextEdit()
        self.slogan_edit.setPlaceholderText("Slogan ou phrase d'accroche de l'entreprise")
        self.slogan_edit.setMaximumHeight(80)
        layout.addRow("Slogan:", self.slogan_edit)
        
        # Logo - Affichage + bouton de sélection
        logo_layout = QVBoxLayout()
        
        # Zone d'affichage du logo
        self.logo_display = QLabel()
        self.logo_display.setStyleSheet("""
            QLabel {
                border: 2px dashed #bdc3c7;
                border-radius: 8px;
                background-color: #f8f9fa;
                min-height: 120px;
                max-height: 120px;
                margin: 5px;
            }
        """)
        self.logo_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_display.setText("Aucun logo")
        logo_layout.addWidget(self.logo_display)
        
        # Boutons de gestion du logo
        logo_buttons_layout = QHBoxLayout()
        
        self.logo_select_button = QPushButton("Sélectionner...")
        self.logo_select_button.setObjectName("logoButton")
        self.logo_select_button.clicked.connect(self.select_logo)
        logo_buttons_layout.addWidget(self.logo_select_button)
        
        self.logo_remove_button = QPushButton("Supprimer")
        self.logo_remove_button.setObjectName("cancelButton")
        self.logo_remove_button.clicked.connect(self.remove_logo)
        self.logo_remove_button.setEnabled(False)
        logo_buttons_layout.addWidget(self.logo_remove_button)
        
        logo_buttons_layout.addStretch()
        logo_layout.addLayout(logo_buttons_layout)
        
        logo_widget = QFrame()
        logo_widget.setLayout(logo_layout)
        layout.addRow("Logo:", logo_widget)
        
        group.setLayout(layout)
        return group
    
    def create_button_layout(self):
        """Créer la zone des boutons d'action"""
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 20, 0, 0)
        
        layout.addStretch()
        
        # Bouton Annuler
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)
        
        # Bouton Sauvegarder
        self.save_button = QPushButton("Enregistrer" if self.mode == "edit" else "Créer")
        self.save_button.clicked.connect(self.save_enterprise)
        layout.addWidget(self.save_button)
        
        return frame
    
    def select_logo(self):
        """Ouvrir le dialogue de sélection de fichier pour le logo"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner le logo de l'entreprise",
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp *.webp);;Tous les fichiers (*)"
        )
        
        if file_path:
            # Valider le fichier
            if not ImageUtils.validate_image_file(file_path):
                QMessageBox.warning(
                    self,
                    "Fichier invalide",
                    "Le fichier sélectionné n'est pas une image valide."
                )
                return
            
            # Convertir en BLOB avec redimensionnement
            try:
                logo_blob = ImageUtils.file_to_blob(file_path)
                if logo_blob:
                    # Redimensionner pour l'affichage et le stockage
                    self.logo_blob = ImageUtils.resize_image_blob(
                        logo_blob, 
                        max_width=300, 
                        max_height=300
                    )
                    
                    # Afficher l'aperçu
                    self.display_logo_preview()
                    self.logo_remove_button.setEnabled(True)
                else:
                    QMessageBox.warning(
                        self,
                        "Erreur",
                        "Impossible de lire le fichier image."
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erreur",
                    f"Erreur lors du traitement de l'image : {str(e)}"
                )
    
    def remove_logo(self):
        """Supprimer le logo sélectionné"""
        self.logo_blob = None
        self.logo_display.clear()
        self.logo_display.setText("Aucun logo")
        self.logo_remove_button.setEnabled(False)
    
    def display_logo_preview(self):
        """Afficher l'aperçu du logo"""
        if self.logo_blob:
            pixmap = ImageUtils.blob_to_pixmap(self.logo_blob)
            if pixmap:
                # Redimensionner pour l'affichage
                scaled_pixmap = pixmap.scaled(
                    100, 100, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                self.logo_display.setPixmap(scaled_pixmap)
                self.logo_display.setText("")
            else:
                self.logo_display.setText("Erreur d'affichage")
        else:
            self.logo_display.clear()
            self.logo_display.setText("Aucun logo")
    
    def populate_fields(self):
        """Remplir les champs si en mode édition"""
        if self.mode == "edit" and self.enterprise_data:
            # Utiliser directement les clés du modèle DB
            self.name_edit.setText(str(self.enterprise_data.get('name', '')))
            self.address_edit.setText(str(self.enterprise_data.get('address', '')))
            self.phone_edit.setText(str(self.enterprise_data.get('phone', '')))
            self.email_edit.setText(str(self.enterprise_data.get('email', '')))
            self.rccm_edit.setText(str(self.enterprise_data.get('rccm', '')))
            self.id_nat_edit.setText(str(self.enterprise_data.get('id_nat', '')))
            self.slogan_edit.setText(str(self.enterprise_data.get('slogan', '')))
            
            # Devise - utiliser setCurrentText pour QComboBox
            currency = str(self.enterprise_data.get('currency', 'USD'))
            if currency in ['USD', 'FC']:
                self.currency_edit.setCurrentText(currency)
            else:
                self.currency_edit.setCurrentText('USD')  # Valeur par défaut si devise non reconnue
            
            # Logo - récupérer le BLOB
            logo_blob = self.enterprise_data.get('logo')
            if logo_blob:
                self.logo_blob = logo_blob
                self.display_logo_preview()
                self.logo_remove_button.setEnabled(True)
            else:
                self.logo_blob = None
                self.logo_remove_button.setEnabled(False)
    
    def collect_data(self):
        """Collecter les données du formulaire selon le modèle DB"""
        data = {
            'name': self.name_edit.text().strip(),
            'address': self.address_edit.text().strip(),
            'phone': self.phone_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'rccm': self.rccm_edit.text().strip(),
            'id_nat': self.id_nat_edit.text().strip(),
            'slogan': self.slogan_edit.toPlainText().strip(),
            'currency': self.currency_edit.currentText(),  # Utiliser currentText() pour QComboBox
            'logo': self.logo_blob  # BLOB data ou None
        }
        
        # Nettoyer les champs texte vides
        for key, value in data.items():
            if key != 'logo' and (not value or value == 'None'):
                data[key] = ''
        
        return data
    
    def validate_data(self, data):
        """Valider les données avant sauvegarde"""
        errors = []
        
        # Nom obligatoire
        if not data.get('name'):
            errors.append("Le nom de l'entreprise est obligatoire.")
        
        # Validation email si fourni
        if data.get('email'):
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, data['email']):
                errors.append("L'adresse email n'est pas valide.")
        
        return errors
    
    def save_enterprise(self):
        """Sauvegarder l'entreprise"""
        try:
            # Collecter les données
            data = self.collect_data()
            
            # Valider
            errors = self.validate_data(data)
            if errors:
                QMessageBox.warning(
                    self,
                    "Erreurs de validation",
                    "Veuillez corriger les erreurs suivantes :\n\n" + "\n".join(errors)
                )
                return
            
            # Sauvegarder selon le mode
            if self.mode == "edit":
                # Récupérer l'ID pour la mise à jour
                if self.enterprise_data and 'id' in self.enterprise_data:
                    enterprise_id = self.enterprise_data['id']
                    success = self.enterprise_controller.update_enterprise(enterprise_id, data)
                    message = "Entreprise mise à jour avec succès!"
                else:
                    raise ValueError("ID d'entreprise manquant pour la mise à jour")
            else:
                success = self.enterprise_controller.create_enterprise(data)
                message = "Entreprise créée avec succès!"
            
            if success:
                QMessageBox.information(self, "Succès", message)
                self.enterprise_saved.emit(data)
                self.accept()
            else:
                QMessageBox.critical(self, "Erreur", "Erreur lors de la sauvegarde.")
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Une erreur s'est produite lors de la sauvegarde :\n{str(e)}"
            )