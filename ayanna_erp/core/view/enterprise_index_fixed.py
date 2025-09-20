"""
Vue d'index pour afficher les détails de l'entreprise
Utilise directement les champs du modèle de base de données
"""

import sys
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QMessageBox,
    QGroupBox, QTextBrowser, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from datetime import datetime

# Import des contrôleurs et widgets
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
from ayanna_erp.core.view.simple_enterprise_widget import SimpleEnterpriseWidget


class EnterpriseIndexView(QWidget):
    """Vue principale pour afficher les détails de l'entreprise"""
    
    def __init__(self, parent=None, current_user=None):
        super().__init__(parent)
        self.current_user = current_user
        self.entreprise_controller = EntrepriseController()
        self.enterprise_data = None
        
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
            QLabel.field-label {
                font-weight: bold;
                color: #34495e;
                min-width: 150px;
            }
            QLabel.field-value {
                color: #2c3e50;
                padding: 5px;
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                min-height: 20px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 20px;
                font-size: 12px;
                font-weight: 600;
                min-width: 120px;
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
            QPushButton#editButton {
                background-color: #f39c12;
            }
            QPushButton#editButton:hover {
                background-color: #e67e22;
            }
        """)
        
        self.init_ui()
        self.connect_signals()
        self.load_enterprise_data()
    
    def init_ui(self):
        """Initialiser l'interface utilisateur"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # En-tête avec titre et boutons d'action
        header_layout = self.create_header_layout()
        layout.addLayout(header_layout)
        
        # Zone de contenu principal avec scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # Widget de contenu
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(20)
        
        scroll_area.setWidget(self.content_widget)
        layout.addWidget(scroll_area)
    
    def create_header_layout(self):
        """Créer l'en-tête avec titre et boutons"""
        layout = QHBoxLayout()
        
        # Titre principal
        title_label = QLabel("Configuration de l'Entreprise")
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        """)
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Boutons d'action selon les permissions
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Bouton Rafraîchir (toujours visible)
        self.refresh_button = QPushButton("Rafraîchir")
        self.refresh_button.clicked.connect(self.load_enterprise_data)
        button_layout.addWidget(self.refresh_button)
        
        # Bouton Ajouter (seulement pour super admin)
        if self.current_user and self.current_user.get('role') == 'super_admin':
            self.add_button = QPushButton("Créer Entreprise")
            self.add_button.setObjectName("addButton")
            self.add_button.clicked.connect(self.create_enterprise)
            button_layout.addWidget(self.add_button)
        
        # Bouton Modifier (admin et super admin)
        if self.current_user and self.current_user.get('role') in ['admin', 'super_admin']:
            self.edit_button = QPushButton("Modifier")
            self.edit_button.setObjectName("editButton")
            self.edit_button.clicked.connect(self.edit_enterprise)
            button_layout.addWidget(self.edit_button)
        
        layout.addLayout(button_layout)
        return layout
    
    def create_enterprise_view(self, data):
        """Créer la vue d'affichage de l'entreprise"""
        # Nettoyer le layout existant
        self.clear_layout(self.content_layout)
        
        if not data:
            self.show_no_enterprise_message()
            return
        
        # Stocker les données pour les boutons d'action
        self.enterprise_data = data
        
        # Logo de l'entreprise
        self.create_logo_section(data)
        
        # Groupes d'informations basés sur le modèle DB
        self.content_layout.addWidget(self.create_general_info_group(data))
        self.content_layout.addWidget(self.create_contact_info_group(data))
        self.content_layout.addWidget(self.create_technical_info_group(data))
        self.content_layout.addWidget(self.create_timestamps_group(data))
        
        # Spacer pour pousser le contenu vers le haut
        self.content_layout.addStretch()
    
    def create_logo_section(self, data):
        """Créer la section logo"""
        logo_group = QGroupBox("Logo de l'Entreprise")
        layout = QVBoxLayout(logo_group)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        logo_path = data.get('logo_path', '')
        
        # Créer le label pour le logo
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #bdc3c7;
                border-radius: 8px;
                padding: 20px;
                background-color: white;
                min-height: 150px;
                max-height: 200px;
            }
        """)
        
        if logo_path and logo_path != 'assets/logo.png':
            # Essayer de charger le logo
            try:
                pixmap = QPixmap(logo_path)
                if not pixmap.isNull():
                    # Redimensionner le logo
                    scaled_pixmap = pixmap.scaled(200, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    logo_label.setPixmap(scaled_pixmap)
                else:
                    logo_label.setText("❌ Logo introuvable\\n" + logo_path)
            except Exception:
                logo_label.setText("❌ Erreur de chargement du logo\\n" + logo_path)
        else:
            logo_label.setText("📷 Aucun logo configuré\\n\\nChemin: " + (logo_path or "Non défini"))
        
        layout.addWidget(logo_label)
        
        # Information sur le chemin du logo
        path_label = QLabel(f"Chemin: {logo_path or 'Non défini'}")
        path_label.setStyleSheet("color: #7f8c8d; font-style: italic; font-size: 10px;")
        path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(path_label)
        
        self.content_layout.addWidget(logo_group)
    
    def create_general_info_group(self, data):
        """Créer le groupe d'informations générales - champs du modèle DB"""
        group = QGroupBox("Informations Générales")
        layout = QFormLayout(group)
        layout.setSpacing(15)
        
        # Champs correspondant exactement au modèle DB
        self.add_field_row(layout, "Nom de l'entreprise:", data.get('name', 'Non défini'))
        self.add_field_row(layout, "RCCM:", data.get('rccm', 'Non défini'))
        self.add_field_row(layout, "ID National:", data.get('id_nat', 'Non défini'))
        self.add_field_row(layout, "Slogan:", data.get('slogan', 'Non défini'))
        self.add_field_row(layout, "Devise:", data.get('currency', 'USD'))
        
        return group
    
    def create_contact_info_group(self, data):
        """Créer le groupe d'informations de contact - champs du modèle DB"""
        group = QGroupBox("Informations de Contact")
        layout = QFormLayout(group)
        layout.setSpacing(15)
        
        # Champs correspondant exactement au modèle DB
        self.add_field_row(layout, "Adresse:", data.get('address', 'Non définie'))
        self.add_field_row(layout, "Téléphone:", data.get('phone', 'Non défini'))
        self.add_field_row(layout, "Email:", data.get('email', 'Non défini'))
        
        return group
    
    def create_technical_info_group(self, data):
        """Créer le groupe d'informations techniques"""
        group = QGroupBox("Informations Techniques")
        layout = QFormLayout(group)
        layout.setSpacing(15)
        
        # Informations système
        self.add_field_row(layout, "ID Système:", str(data.get('id', 'N/A')))
        self.add_field_row(layout, "Chemin Logo:", data.get('logo_path', 'Non défini'))
        
        return group
    
    def create_timestamps_group(self, data):
        """Créer le groupe d'informations de dates"""
        group = QGroupBox("Informations de Création")
        layout = QFormLayout(group)
        layout.setSpacing(15)
        
        # Date de création
        created_at = data.get('created_at')
        if created_at:
            if isinstance(created_at, datetime):
                created_str = created_at.strftime("%d/%m/%Y à %H:%M")
            else:
                created_str = str(created_at)
        else:
            created_str = "Non disponible"
        
        self.add_field_row(layout, "Créée le:", created_str)
        
        return group
    
    def add_field_row(self, layout, label_text, value):
        """Ajouter une ligne de champ avec label et valeur"""
        label = QLabel(label_text)
        label.setObjectName("field-label")
        
        value_label = QLabel(str(value))
        value_label.setObjectName("field-value")
        value_label.setWordWrap(True)
        
        layout.addRow(label, value_label)
    
    def show_no_enterprise_message(self):
        """Afficher un message quand aucune entreprise n'est trouvée"""
        message_frame = QFrame()
        message_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px dashed #e74c3c;
                border-radius: 10px;
                padding: 40px;
            }
        """)
        
        layout = QVBoxLayout(message_frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Icône et message
        icon_label = QLabel("🏢")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px; margin-bottom: 20px;")
        layout.addWidget(icon_label)
        
        message_label = QLabel("Aucune entreprise configurée")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #e74c3c;
            margin-bottom: 10px;
        """)
        layout.addWidget(message_label)
        
        sub_message = QLabel("Veuillez créer une entreprise pour commencer.")
        sub_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_message.setStyleSheet("color: #7f8c8d; font-size: 14px;")
        layout.addWidget(sub_message)
        
        # Bouton pour créer si super admin
        if self.current_user and self.current_user.get('role') == 'super_admin':
            create_button = QPushButton("Créer une Entreprise")
            create_button.setObjectName("addButton")
            create_button.clicked.connect(self.create_enterprise)
            layout.addWidget(create_button)
        
        self.content_layout.addWidget(message_frame)
    
    def clear_layout(self, layout):
        """Vider un layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def connect_signals(self):
        """Connecter les signaux"""
        # Connecter les signaux du contrôleur s'ils existent
        if hasattr(self.entreprise_controller, 'entreprises_loaded'):
            self.entreprise_controller.entreprises_loaded.connect(self.on_enterprises_loaded)
        if hasattr(self.entreprise_controller, 'entreprise_created'):
            self.entreprise_controller.entreprise_created.connect(self.on_enterprise_saved)
        if hasattr(self.entreprise_controller, 'entreprise_updated'):
            self.entreprise_controller.entreprise_updated.connect(self.on_enterprise_saved)
        if hasattr(self.entreprise_controller, 'error_occurred'):
            self.entreprise_controller.error_occurred.connect(self.on_error_occurred)
    
    def load_enterprise_data(self):
        """Charger les données de l'entreprise de l'utilisateur connecté"""
        try:
            # Récupérer l'ID de l'entreprise de l'utilisateur connecté
            if self.current_user and 'enterprise_id' in self.current_user:
                enterprise_id = self.current_user['enterprise_id']
            else:
                # Fallback vers ID 1 si pas trouvé
                enterprise_id = 1
            
            # Charger l'entreprise spécifique
            enterprise = self.entreprise_controller.get_current_enterprise(enterprise_id)
            
            if enterprise:
                self.on_enterprises_loaded([enterprise])
            else:
                QMessageBox.warning(
                    self, 
                    "Aucune entreprise", 
                    "Aucune entreprise trouvée pour cet utilisateur."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur", 
                f"Erreur lors du chargement de l'entreprise: {str(e)}"
            )
    
    def create_enterprise(self):
        """Ouvrir le dialogue de création d'entreprise"""
        dialog = SimpleEnterpriseWidget(self, current_user=self.current_user)
        dialog.enterprise_saved.connect(self.on_enterprise_created)
        dialog.exec()
    
    def edit_enterprise(self):
        """Ouvrir le dialogue de modification d'entreprise"""
        if self.enterprise_data:
            dialog = SimpleEnterpriseWidget(
                self, 
                enterprise_data=self.enterprise_data, 
                current_user=self.current_user
            )
            dialog.enterprise_saved.connect(self.on_enterprise_updated)
            dialog.exec()
    
    def on_enterprises_loaded(self, enterprises):
        """Gestionnaire pour entreprises chargées"""
        if enterprises and len(enterprises) > 0:
            # Prendre la première entreprise (normalement il n'y en a qu'une par utilisateur)
            enterprise_data = enterprises[0]
            self.create_enterprise_view(enterprise_data)
        else:
            self.create_enterprise_view(None)
    
    def on_enterprise_created(self, enterprise_data):
        """Gestionnaire pour entreprise créée"""
        QMessageBox.information(
            self,
            "Succès",
            f"L'entreprise '{enterprise_data.get('name', '')}' a été créée avec succès!"
        )
        self.load_enterprise_data()
    
    def on_enterprise_updated(self, enterprise_data):
        """Gestionnaire pour entreprise mise à jour"""
        QMessageBox.information(
            self,
            "Succès",
            f"L'entreprise '{enterprise_data.get('name', '')}' a été mise à jour avec succès!"
        )
        self.load_enterprise_data()
    
    def on_enterprise_saved(self, enterprise_data):
        """Gestionnaire générique pour entreprise sauvegardée"""
        self.load_enterprise_data()
    
    def on_error_occurred(self, error_message):
        """Gestionnaire d'erreur"""
        QMessageBox.critical(self, "Erreur", error_message)