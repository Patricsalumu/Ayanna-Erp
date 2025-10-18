"""
Formulaire modal pour l'ajout/modification des services
Module Boutique - Ayanna ERP
"""

import sys
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                            QFormLayout, QLineEdit, QPushButton, 
                            QTextEdit, QDoubleSpinBox, QComboBox,
                            QCheckBox, QLabel, QMessageBox, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from decimal import Decimal
from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController


class ServiceForm(QDialog):
    """Formulaire modal pour créer/modifier un service"""
    
    service_saved = pyqtSignal(dict)  # Signal émis quand un service est sauvegardé
    
    def __init__(self, parent=None, service_data=None, controller=None):
        super().__init__(parent)
        self.service_data = service_data
        self.controller = controller
        self.is_edit_mode = service_data is not None
        
        # Initialiser le contrôleur entreprise pour les devises
        self.entreprise_controller = EntrepriseController()
        
        self.setup_ui()
        self.setup_style()
        
        if self.is_edit_mode:
            self.load_service_data()
    
    def get_currency_symbol(self):
        """Récupère le symbole de devise depuis l'entreprise"""
        try:
            return self.entreprise_controller.get_currency_symbol()
        except:
            return "FC"  # Fallback pour Franc Congolais
    
    def format_amount(self, amount):
        """Formate un montant avec la devise de l'entreprise"""
        try:
            return self.entreprise_controller.format_amount(amount)
        except:
            return f"{amount:.2f} FC"  # Fallback
    
    def setup_ui(self):
        """Initialiser l'interface utilisateur"""
        self.setWindowTitle("Modifier le service" if self.is_edit_mode else "Nouveau service")
        self.setModal(True)
        self.resize(500, 400)
        
        # Layout principal
        layout = QVBoxLayout(self)
        
        # === INFORMATIONS GÉNÉRALES ===
        general_group = QGroupBox("Informations générales")
        general_layout = QFormLayout(general_group)
        
        # Nom du service
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ex: Livraison à domicile")
        general_layout.addRow("Nom du service *:", self.name_edit)
        
        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Description détaillée du service...")
        general_layout.addRow("Description:", self.description_edit)
        
        layout.addWidget(general_group)
        
        # === TARIFICATION ===
        pricing_group = QGroupBox("Tarification")
        pricing_layout = QFormLayout(pricing_group)
        
        # Prix de vente
        self.price_spinbox = QDoubleSpinBox()
        self.price_spinbox.setRange(0.0, 999999.99)
        self.price_spinbox.setDecimals(0)
        self.price_spinbox.setSuffix(f" {self.get_currency_symbol()}")
        self.price_spinbox.setSpecialValueText("Gratuit")
        pricing_layout.addRow("Prix de vente *:", self.price_spinbox)
        
        layout.addWidget(pricing_group)
        
        # === OPTIONS ===
        options_group = QGroupBox("Options")
        options_layout = QFormLayout(options_group)
        
        # Service actif
        self.active_checkbox = QCheckBox("Service actif")
        self.active_checkbox.setChecked(True)
        options_layout.addRow("", self.active_checkbox)
        
        layout.addWidget(options_group)
        
        # === BOUTONS ===
        buttons_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Annuler")
        self.save_btn = QPushButton("Modifier" if self.is_edit_mode else "Créer")
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.save_btn)
        
        layout.addLayout(buttons_layout)
        
        # Connecter les signaux
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self.save_service)
        
        # Focus sur le premier champ
        self.name_edit.setFocus()
    
    def setup_style(self):
        """Appliquer les styles"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QGroupBox {
                font-weight: bold;
                padding-top: 15px;
                margin-top: 10px;
                border: 2px solid #dee2e6;
                border-radius: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #495057;
                background-color: #f8f9fa;
            }
            QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox {
                padding: 8px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {
                border-color: #007bff;
                outline: none;
            }
            QPushButton {
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton#save_btn {
                background-color: #007bff;
                color: white;
            }
            QPushButton#save_btn:hover {
                background-color: #0056b3;
            }
            QPushButton#cancel_btn {
                background-color: #6c757d;
                color: white;
            }
            QPushButton#cancel_btn:hover {
                background-color: #545b62;
            }
        """)
        
        self.save_btn.setObjectName("save_btn")
        self.cancel_btn.setObjectName("cancel_btn")
    
    def load_service_data(self):
        """Charger les données du service en mode édition"""
        if not self.service_data:
            return
        
        # Gestion des objets et dictionnaires
        if isinstance(self.service_data, dict):
            name = self.service_data.get('nom', self.service_data.get('name', ''))
            description = self.service_data.get('description', '')
            price = self.service_data.get('prix', self.service_data.get('price', 0))
            is_active = self.service_data.get('actif', self.service_data.get('is_active', True))
        else:
            name = getattr(self.service_data, 'nom', getattr(self.service_data, 'name', ''))
            description = getattr(self.service_data, 'description', '')
            price = getattr(self.service_data, 'prix', getattr(self.service_data, 'price', 0))
            is_active = getattr(self.service_data, 'actif', getattr(self.service_data, 'is_active', True))
        
        self.name_edit.setText(name or '')
        self.description_edit.setPlainText(description or '')
        self.price_spinbox.setValue(float(price or 0))
        self.active_checkbox.setChecked(bool(is_active))
    
    def validate_form(self):
        """Valider les données du formulaire"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Erreur", "Le nom du service est obligatoire.")
            self.name_edit.setFocus()
            return False
        
        if self.price_spinbox.value() <= 0:
            QMessageBox.warning(self, "Erreur", "Le prix de vente doit être supérieur à 0.")
            self.price_spinbox.setFocus()
            return False
        
        return True
    
    def get_service_data(self):
        """Récupérer les données du formulaire"""
        return {
            'nom': self.name_edit.text().strip(),
            'name': self.name_edit.text().strip(),  # Compatibilité
            'description': self.description_edit.toPlainText().strip(),
            'prix': round(self.price_spinbox.value(), 0),
            'price': round(self.price_spinbox.value(), 0),  # Compatibilité
            'actif': self.active_checkbox.isChecked(),
            'is_active': self.active_checkbox.isChecked()  # Compatibilité
        }
    
    def save_service(self):
        """Sauvegarder le service"""
        if not self.validate_form():
            return
        
        try:
            # Émettre le signal avec les données pour que le parent traite
            self.service_saved.emit(self.get_service_data())
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur inattendue: {str(e)}")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Test du formulaire
    form = ServiceForm()
    form.show()
    
    sys.exit(app.exec())