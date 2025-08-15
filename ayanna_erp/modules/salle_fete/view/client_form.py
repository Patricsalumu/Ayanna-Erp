"""
Formulaire modal pour ajouter/modifier un client
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                            QFormLayout, QPushButton, QLineEdit, QLabel, 
                            QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, 
                            QMessageBox, QGroupBox, QGridLayout, QDateEdit)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime
from ayanna_erp.database.database_manager import DatabaseManager


class ClientForm(QDialog):
    """Formulaire modal pour créer/modifier un client"""
    
    # Signal émis quand le client est sauvegardé
    client_saved = pyqtSignal(dict)
    
    def __init__(self, parent=None, client_data=None, db_manager=None):
        super().__init__(parent)
        self.client_data = client_data
        self.db_manager = db_manager or DatabaseManager()
        self.is_edit_mode = client_data is not None
        
        self.setWindowTitle("Modifier le client" if self.is_edit_mode else "Nouveau client")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        
        self.setup_ui()
        if self.is_edit_mode:
            self.load_client_data()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # Informations personnelles
        personal_group = QGroupBox("Informations personnelles")
        personal_layout = QFormLayout(personal_group)
        
        # Nom et prénom
        self.nom_edit = QLineEdit()
        self.nom_edit.setPlaceholderText("Nom de famille")
        
        self.prenom_edit = QLineEdit()
        self.prenom_edit.setPlaceholderText("Prénom")
        
        # Contact
        self.telephone_edit = QLineEdit()
        self.telephone_edit.setPlaceholderText("06.12.34.56.78")
        
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("client@email.com")
        
        # Adresse
        self.adresse_edit = QLineEdit()
        self.adresse_edit.setPlaceholderText("Numéro et nom de rue")
        
        self.ville_edit = QLineEdit()
        self.ville_edit.setPlaceholderText("Ville")
        
        self.code_postal_edit = QLineEdit()
        self.code_postal_edit.setPlaceholderText("Code postal")
        
        personal_layout.addRow("Nom*:", self.nom_edit)
        personal_layout.addRow("Prénom*:", self.prenom_edit)
        personal_layout.addRow("Téléphone*:", self.telephone_edit)
        personal_layout.addRow("Email:", self.email_edit)
        personal_layout.addRow("Adresse:", self.adresse_edit)
        personal_layout.addRow("Ville:", self.ville_edit)
        personal_layout.addRow("Code postal:", self.code_postal_edit)
        
        # Informations complémentaires
        additional_group = QGroupBox("Informations complémentaires")
        additional_layout = QFormLayout(additional_group)
        
        # Date de naissance
        self.date_naissance = QDateEdit()
        self.date_naissance.setDate(QDate(1990, 1, 1))
        self.date_naissance.setDisplayFormat("dd/MM/yyyy")
        self.date_naissance.setCalendarPopup(True)
        
        # Type de client
        self.type_client_combo = QComboBox()
        self.type_client_combo.addItems([
            "Particulier", "Entreprise", "Association", "Autre"
        ])
        
        # Source
        self.source_combo = QComboBox()
        self.source_combo.addItems([
            "Bouche à oreille", "Site internet", "Réseaux sociaux", 
            "Publicité locale", "Ancien client", "Autre"
        ])
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Notes sur le client, préférences, etc.")
        
        additional_layout.addRow("Date de naissance:", self.date_naissance)
        additional_layout.addRow("Type de client:", self.type_client_combo)
        additional_layout.addRow("Comment nous a connu:", self.source_combo)
        additional_layout.addRow("Notes:", self.notes_edit)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("❌ Annuler")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #95A5A6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7F8C8D;
            }
        """)
        
        self.save_button = QPushButton("💾 Enregistrer")
        self.save_button.setStyleSheet("""
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
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.save_button)
        
        # Assemblage du layout principal
        layout.addWidget(personal_group)
        layout.addWidget(additional_group)
        layout.addLayout(buttons_layout)
        
        # Note sur les champs obligatoires
        note_label = QLabel("* Champs obligatoires")
        note_label.setStyleSheet("color: #E74C3C; font-style: italic;")
        layout.addWidget(note_label)
        
        # Connexion des signaux
        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self.save_client)
    
    def load_client_data(self):
        """Charger les données du client pour modification"""
        if not self.client_data:
            return
        
        # TODO: Implémenter le chargement des données depuis la base
        self.nom_edit.setText(self.client_data.get('nom', ''))
        self.prenom_edit.setText(self.client_data.get('prenom', ''))
        self.telephone_edit.setText(self.client_data.get('telephone', ''))
        self.email_edit.setText(self.client_data.get('email', ''))
        self.adresse_edit.setText(self.client_data.get('adresse', ''))
        self.ville_edit.setText(self.client_data.get('ville', ''))
        self.code_postal_edit.setText(self.client_data.get('code_postal', ''))
        
        if 'type_client' in self.client_data:
            self.type_client_combo.setCurrentText(self.client_data['type_client'])
        
        if 'source' in self.client_data:
            self.source_combo.setCurrentText(self.client_data['source'])
        
        self.notes_edit.setPlainText(self.client_data.get('notes', ''))
    
    def validate_data(self):
        """Valider les données saisies"""
        errors = []
        
        if not self.nom_edit.text().strip():
            errors.append("Le nom est obligatoire")
        
        if not self.prenom_edit.text().strip():
            errors.append("Le prénom est obligatoire")
        
        if not self.telephone_edit.text().strip():
            errors.append("Le téléphone est obligatoire")
        
        # Validation du format email si saisi
        email = self.email_edit.text().strip()
        if email and '@' not in email:
            errors.append("Le format de l'email n'est pas valide")
        
        return errors
    
    def save_client(self):
        """Sauvegarder le client"""
        # Validation des données
        errors = self.validate_data()
        if errors:
            QMessageBox.warning(self, "Erreurs de validation", "\n".join(errors))
            return
        
        # Récupération des données
        client_data = {
            'nom': self.nom_edit.text().strip(),
            'prenom': self.prenom_edit.text().strip(),
            'telephone': self.telephone_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'adresse': self.adresse_edit.text().strip(),
            'ville': self.ville_edit.text().strip(),
            'code_postal': self.code_postal_edit.text().strip(),
            'date_naissance': self.date_naissance.date().toPyDate(),
            'type_client': self.type_client_combo.currentText(),
            'source': self.source_combo.currentText(),
            'notes': self.notes_edit.toPlainText().strip(),
            'date_creation': datetime.now(),
            'nb_reservations': 0 if not self.is_edit_mode else self.client_data.get('nb_reservations', 0)
        }
        
        # TODO: Sauvegarder dans la base de données
        try:
            # Simulation de sauvegarde
            if not self.is_edit_mode:
                client_data['id'] = f"CLI{datetime.now().strftime('%Y%m%d%H%M%S')}"
            else:
                client_data['id'] = self.client_data['id']
            
            # Émettre le signal avec les données
            self.client_saved.emit(client_data)
            
            QMessageBox.information(
                self, 
                "Succès", 
                f"Client {'modifié' if self.is_edit_mode else 'créé'} avec succès !"
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Erreur", 
                f"Erreur lors de la sauvegarde: {str(e)}"
            )