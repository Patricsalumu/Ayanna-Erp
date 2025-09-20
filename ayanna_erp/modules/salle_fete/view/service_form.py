"""
Formulaire modal pour l'ajout/modification des services
Module Salle de Fête - Ayanna ERP
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
            return "€"  # Fallback
    
    def format_amount(self, amount):
        """Formate un montant avec la devise de l'entreprise"""
        try:
            return self.entreprise_controller.format_amount(amount)
        except:
            return f"{amount:.2f} €"  # Fallback
    
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
        self.name_edit.setPlaceholderText("Ex: Décoration florale premium")
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
        
        # Coût
        self.cost_spinbox = QDoubleSpinBox()
        self.cost_spinbox.setRange(0.0, 999999.99)
        self.cost_spinbox.setDecimals(2)
        self.cost_spinbox.setSuffix(f" {self.get_currency_symbol()}")
        self.cost_spinbox.setSpecialValueText("Gratuit")
        pricing_layout.addRow("Coût du service:", self.cost_spinbox)
        
        # Prix de vente
        self.price_spinbox = QDoubleSpinBox()
        self.price_spinbox.setRange(0.0, 999999.99)
        self.price_spinbox.setDecimals(2)
        self.price_spinbox.setSuffix(f" {self.get_currency_symbol()}")
        self.price_spinbox.setSpecialValueText("Gratuit")
        pricing_layout.addRow("Prix de vente *:", self.price_spinbox)
        
        # Marge automatique
        self.margin_label = QLabel(f"Marge: 0.00 {self.get_currency_symbol()}")
        pricing_layout.addRow("", self.margin_label)
        
        layout.addWidget(pricing_group)
        
        # === COMPTABILITÉ ===
        accounting_group = QGroupBox("Comptabilité")
        accounting_layout = QFormLayout(accounting_group)
        
        # Compte comptable de vente
        self.account_combo = QComboBox()
        self.account_combo.setMinimumWidth(250)
        self.account_combo.setToolTip("Sélectionnez le compte comptable de vente pour ce service")
        self.load_sales_accounts()
        accounting_layout.addRow("Compte de vente:", self.account_combo)
        
        layout.addWidget(accounting_group)
        
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
        self.cost_spinbox.valueChanged.connect(self.update_margin)
        self.price_spinbox.valueChanged.connect(self.update_margin)
        
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
    
    def update_margin(self):
        """Mettre à jour l'affichage de la marge"""
        cost = self.cost_spinbox.value()
        price = self.price_spinbox.value()
        margin = price - cost
        
        self.margin_label.setText(f"Marge: {self.format_amount(margin)}")
        
        if margin < 0:
            self.margin_label.setStyleSheet("color: #dc3545; font-weight: bold;")
        elif margin == 0:
            self.margin_label.setStyleSheet("color: #6c757d;")
        else:
            self.margin_label.setStyleSheet("color: #28a745; font-weight: bold;")
    
    def load_sales_accounts(self):
        """Charger les comptes de vente dans le combo box"""
        try:
            # Importer ici pour éviter les imports circulaires
            from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ComptabiliteController
            
            comptabilite_controller = ComptabiliteController()
            comptes = comptabilite_controller.get_comptes_vente()
            
            self.account_combo.clear()
            self.account_combo.addItem("-- Sélectionner un compte --", None)
            
            for compte in comptes:
                self.account_combo.addItem(f"{compte.numero} - {compte.nom}", compte.id)
                
        except Exception as e:
            print(f"Erreur lors du chargement des comptes: {e}")
            self.account_combo.addItem("Erreur - Comptes indisponibles", None)
    
    def load_service_data(self):
        """Charger les données du service en mode édition"""
        if not self.service_data:
            return
        
        # Gestion des objets SQLAlchemy et dictionnaires
        if hasattr(self.service_data, 'name'):
            # Objet SQLAlchemy
            self.name_edit.setText(self.service_data.name or '')
            self.description_edit.setPlainText(self.service_data.description or '')
            self.cost_spinbox.setValue(float(self.service_data.cost or 0))
            self.price_spinbox.setValue(float(self.service_data.price or 0))
            self.active_checkbox.setChecked(bool(self.service_data.is_active))
            
            # Sélectionner le compte comptable
            if hasattr(self.service_data, 'account_id') and self.service_data.account_id:
                for i in range(self.account_combo.count()):
                    if self.account_combo.itemData(i) == self.service_data.account_id:
                        self.account_combo.setCurrentIndex(i)
                        break
        else:
            # Dictionnaire (rétrocompatibilité)
            self.name_edit.setText(self.service_data.get('name', ''))
            self.description_edit.setPlainText(self.service_data.get('description', ''))
            self.cost_spinbox.setValue(float(self.service_data.get('cost', 0)))
            self.price_spinbox.setValue(float(self.service_data.get('price', 0)))
            self.active_checkbox.setChecked(bool(self.service_data.get('is_active', True)))
            
            # Sélectionner le compte comptable
            account_id = self.service_data.get('account_id')
            if account_id:
                for i in range(self.account_combo.count()):
                    if self.account_combo.itemData(i) == account_id:
                        self.account_combo.setCurrentIndex(i)
                        break
        
        # Mettre à jour la marge
        self.update_margin()
    
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
    
    def get_form_data(self):
        """Récupérer les données du formulaire"""
        return {
            'name': self.name_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'cost': round(self.cost_spinbox.value(), 2),
            'price': round(self.price_spinbox.value(), 2),
            'is_active': self.active_checkbox.isChecked(),
            'account_id': self.account_combo.currentData()  # ID du compte comptable sélectionné
        }
    
    def save_service(self):
        """Sauvegarder le service"""
        if not self.validate_form():
            return
        
        try:
            form_data = self.get_form_data()
            
            if self.controller:
                if self.is_edit_mode:
                    # Modification
                    if hasattr(self.service_data, 'id'):
                        service_id = self.service_data.id  # Objet SQLAlchemy
                    else:
                        service_id = self.service_data.get('id')  # Dictionnaire
                    success = self.controller.update_service(service_id, form_data)
                    if success:
                        QMessageBox.information(self, "Succès", "Service modifié avec succès !")
                    else:
                        QMessageBox.critical(self, "Erreur", "Erreur lors de la modification du service.")
                        return
                else:
                    # Création
                    success = self.controller.add_service(form_data)
                    if success:
                        QMessageBox.information(self, "Succès", "Service créé avec succès !")
                    else:
                        QMessageBox.critical(self, "Erreur", "Erreur lors de la création du service.")
                        return
            
            # Émettre le signal avec les données
            self.service_saved.emit(form_data)
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
