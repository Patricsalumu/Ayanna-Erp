"""
Configuration des paramètres d'impression pour le module Salle de Fête
"""

import json
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QRadioButton, QButtonGroup, QGroupBox,
                            QComboBox, QSpinBox, QCheckBox, QFormLayout,
                            QMessageBox)
from PyQt6.QtCore import Qt

class PrintSettings:
    """Gestionnaire des paramètres d'impression"""
    
    def __init__(self):
        self.config_file = "data/print_settings.json"
        self.default_settings = {
            "receipt_behavior": "direct_print",  # "direct_print" ou "save_and_open"
            "reservation_behavior": "save_pdf",  # "save_pdf" ou "direct_print"
            "default_printer": "",
            "auto_close_after_print": True,
            "receipt_format": "53mm",  # "53mm" ou "80mm"
            "print_copies": 1
        }
        self.settings = self.load_settings()
    
    def load_settings(self):
        """Charger les paramètres depuis le fichier JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                # Fusionner avec les paramètres par défaut pour les nouvelles clés
                for key, value in self.default_settings.items():
                    if key not in settings:
                        settings[key] = value
                return settings
            else:
                return self.default_settings.copy()
        except Exception as e:
            print(f"Erreur lors du chargement des paramètres d'impression: {e}")
            return self.default_settings.copy()
    
    def save_settings(self):
        """Sauvegarder les paramètres dans le fichier JSON"""
        try:
            # Créer le dossier si nécessaire
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des paramètres d'impression: {e}")
            return False
    
    def get_setting(self, key):
        """Obtenir une valeur de paramètre"""
        return self.settings.get(key, self.default_settings.get(key))
    
    def set_setting(self, key, value):
        """Définir une valeur de paramètre"""
        self.settings[key] = value
        self.save_settings()


class PrintSettingsDialog(QDialog):
    """Dialogue de configuration des paramètres d'impression"""
    
    def __init__(self, print_settings, parent=None):
        super().__init__(parent)
        self.print_settings = print_settings
        self.setWindowTitle("Paramètres d'impression")
        self.setModal(True)
        self.resize(400, 300)
        
        self.setup_ui()
        self.load_current_settings()
    
    def setup_ui(self):
        """Configurer l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # Groupe pour les reçus de paiement
        receipt_group = QGroupBox("Reçus de paiement (53mm)")
        receipt_layout = QFormLayout(receipt_group)
        
        # Comportement des reçus
        self.receipt_behavior_group = QButtonGroup()
        self.receipt_direct = QRadioButton("Impression directe")
        self.receipt_save = QRadioButton("Sauvegarder et ouvrir")
        
        self.receipt_behavior_group.addButton(self.receipt_direct, 0)
        self.receipt_behavior_group.addButton(self.receipt_save, 1)
        
        receipt_behavior_layout = QVBoxLayout()
        receipt_behavior_layout.addWidget(self.receipt_direct)
        receipt_behavior_layout.addWidget(self.receipt_save)
        
        receipt_layout.addRow("Comportement:", receipt_behavior_layout)
        
        # Format des reçus
        self.receipt_format = QComboBox()
        self.receipt_format.addItems(["53mm", "80mm"])
        receipt_layout.addRow("Format:", self.receipt_format)
        
        layout.addWidget(receipt_group)
        
        # Groupe pour les réservations
        reservation_group = QGroupBox("Réservations (A4)")
        reservation_layout = QFormLayout(reservation_group)
        
        # Comportement des réservations
        self.reservation_behavior_group = QButtonGroup()
        self.reservation_save = QRadioButton("Sauvegarder en PDF")
        self.reservation_direct = QRadioButton("Impression directe")
        
        self.reservation_behavior_group.addButton(self.reservation_save, 0)
        self.reservation_behavior_group.addButton(self.reservation_direct, 1)
        
        reservation_behavior_layout = QVBoxLayout()
        reservation_behavior_layout.addWidget(self.reservation_save)
        reservation_behavior_layout.addWidget(self.reservation_direct)
        
        reservation_layout.addRow("Comportement:", reservation_behavior_layout)
        
        layout.addWidget(reservation_group)
        
        # Paramètres généraux
        general_group = QGroupBox("Paramètres généraux")
        general_layout = QFormLayout(general_group)
        
        # Nombre de copies
        self.print_copies = QSpinBox()
        self.print_copies.setMinimum(1)
        self.print_copies.setMaximum(5)
        general_layout.addRow("Nombre de copies:", self.print_copies)
        
        # Fermeture automatique
        self.auto_close = QCheckBox("Fermer automatiquement après impression")
        general_layout.addRow(self.auto_close)
        
        layout.addWidget(general_group)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Sauvegarder")
        self.save_button.clicked.connect(self.save_settings)
        
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.clicked.connect(self.reject)
        
        self.reset_button = QPushButton("Réinitialiser")
        self.reset_button.clicked.connect(self.reset_settings)
        
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.reset_button)
        
        layout.addLayout(buttons_layout)
    
    def load_current_settings(self):
        """Charger les paramètres actuels dans l'interface"""
        # Comportement des reçus
        receipt_behavior = self.print_settings.get_setting("receipt_behavior")
        if receipt_behavior == "direct_print":
            self.receipt_direct.setChecked(True)
        else:
            self.receipt_save.setChecked(True)
        
        # Format des reçus
        receipt_format = self.print_settings.get_setting("receipt_format")
        index = self.receipt_format.findText(receipt_format)
        if index >= 0:
            self.receipt_format.setCurrentIndex(index)
        
        # Comportement des réservations
        reservation_behavior = self.print_settings.get_setting("reservation_behavior")
        if reservation_behavior == "save_pdf":
            self.reservation_save.setChecked(True)
        else:
            self.reservation_direct.setChecked(True)
        
        # Paramètres généraux
        self.print_copies.setValue(self.print_settings.get_setting("print_copies"))
        self.auto_close.setChecked(self.print_settings.get_setting("auto_close_after_print"))
    
    def save_settings(self):
        """Sauvegarder les nouveaux paramètres"""
        try:
            # Comportement des reçus
            if self.receipt_direct.isChecked():
                self.print_settings.set_setting("receipt_behavior", "direct_print")
            else:
                self.print_settings.set_setting("receipt_behavior", "save_and_open")
            
            # Format des reçus
            self.print_settings.set_setting("receipt_format", self.receipt_format.currentText())
            
            # Comportement des réservations
            if self.reservation_save.isChecked():
                self.print_settings.set_setting("reservation_behavior", "save_pdf")
            else:
                self.print_settings.set_setting("reservation_behavior", "direct_print")
            
            # Paramètres généraux
            self.print_settings.set_setting("print_copies", self.print_copies.value())
            self.print_settings.set_setting("auto_close_after_print", self.auto_close.isChecked())
            
            QMessageBox.information(self, "Succès", "Paramètres sauvegardés avec succès!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde:\n{str(e)}")
    
    def reset_settings(self):
        """Réinitialiser aux paramètres par défaut"""
        reply = QMessageBox.question(self, "Confirmation", 
                                    "Voulez-vous vraiment réinitialiser tous les paramètres?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.print_settings.settings = self.print_settings.default_settings.copy()
            self.print_settings.save_settings()
            self.load_current_settings()
            QMessageBox.information(self, "Succès", "Paramètres réinitialisés!")