"""
Formulaire modal pour l'ajout/modification des produits
Module Salle de Fête - Ayanna ERP
"""

import sys
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                            QFormLayout, QLineEdit, QPushButton, 
                            QTextEdit, QDoubleSpinBox, QComboBox,
                            QCheckBox, QLabel, QMessageBox, QGroupBox,
                            QSpinBox, QScrollArea, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from decimal import Decimal
from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController


class ProduitForm(QDialog):
    """Formulaire modal pour créer/modifier un produit"""
    
    produit_saved = pyqtSignal(dict)  # Signal émis quand un produit est sauvegardé
    
    def __init__(self, parent=None, produit_data=None, controller=None):
        super().__init__(parent)
        self.produit_data = produit_data
        self.controller = controller
        self.is_edit_mode = produit_data is not None
        
        """Initialiser l'interface utilisateur"""
        self.setWindowTitle("Modifier le produit" if self.is_edit_mode else "Nouveau produit")
        self.setModal(True)
        self.setMinimumSize(700, 500)  # Augmenté pour une meilleure visibilité
        self.resize(800, 600)  # Taille par défaut plus grande
        
        # Initialiser le contrôleur entreprise pour les devises
        self.entreprise_controller = EntrepriseController()
        
        self.setup_ui()
        self.setup_style()
        
        if self.is_edit_mode:
            self.load_produit_data()
    
    def get_currency_symbol(self):
        """Récupère le symbole de devise depuis l'entreprise via la session"""
        try:
            # Utiliser la méthode sans paramètre car elle utilise automatiquement la session maintenant
            return self.entreprise_controller.get_currency_symbol()
        except:
            return "€"  # Fallback
    
    def format_amount(self, amount):
        """Formate un montant avec la devise de l'entreprise via la session"""
        try:
            # Utiliser la méthode sans paramètre car elle utilise automatiquement la session maintenant
            return self.entreprise_controller.format_amount(amount)
        except:
            return f"{amount:.2f} €"  # Fallback
    
    def setup_ui(self):
            
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Créer le scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Widget de contenu pour le scroll
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # === INFORMATIONS GÉNÉRALES ===
        general_group = QGroupBox("Informations générales")
        general_layout = QFormLayout(general_group)
        
        # Nom du produit
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ex: Champagne Moët & Chandon")
        general_layout.addRow("Nom du produit *:", self.name_edit)
        
        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Description détaillée du produit...")
        general_layout.addRow("Description:", self.description_edit)
        
        # Catégorie
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "Boissons",
            "Alimentaire",
            "Décoration",
            "Matériel",
            "Vaisselle",
            "Mobilier",
            "Éclairage",
            "Audio/Vidéo",
            "Autre"
        ])
        self.category_combo.setEditable(True)
        general_layout.addRow("Catégorie:", self.category_combo)
        
        # Unité
        self.unit_combo = QComboBox()
        self.unit_combo.addItems([
            "pièce",
            "bouteille", 
            "plateau",
            "lot",
            "kg",
            "litre",
            "mètre",
            "m²",
            "paquet",
            "boîte"
        ])
        self.unit_combo.setEditable(True)
        general_layout.addRow("Unité:", self.unit_combo)
        
        layout.addWidget(general_group)
        
        # === TARIFICATION ===
        pricing_group = QGroupBox("Tarification")
        pricing_layout = QFormLayout(pricing_group)
        
        # Coût d'achat
        self.cost_spinbox = QDoubleSpinBox()
        self.cost_spinbox.setRange(0.0, 999999.99)
        self.cost_spinbox.setDecimals(2)
        self.cost_spinbox.setSuffix(f" {self.get_currency_symbol()}")
        self.cost_spinbox.setSpecialValueText("Gratuit")
        pricing_layout.addRow("Coût d'achat:", self.cost_spinbox)
        
        # Prix de vente unitaire
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
        
        # === GESTION DE STOCK ===
        stock_group = QGroupBox("Gestion de stock")
        stock_layout = QFormLayout(stock_group)
        
        # Quantité en stock
        self.stock_spinbox = QDoubleSpinBox()
        self.stock_spinbox.setRange(0.0, 999999.99)
        self.stock_spinbox.setDecimals(2)
        self.stock_spinbox.setSpecialValueText("Aucun")
        stock_layout.addRow("Quantité en stock:", self.stock_spinbox)
        
        # Seuil minimum
        self.stock_min_spinbox = QDoubleSpinBox()
        self.stock_min_spinbox.setRange(0.0, 999999.99)
        self.stock_min_spinbox.setDecimals(2)
        self.stock_min_spinbox.setSpecialValueText("Aucun")
        stock_layout.addRow("Seuil minimum:", self.stock_min_spinbox)
        
        # Alerte stock
        self.stock_alert_label = QLabel("")
        stock_layout.addRow("", self.stock_alert_label)
        
        layout.addWidget(stock_group)
        
        # === COMPTABILITÉ ===
        accounting_group = QGroupBox("Comptabilité")
        accounting_layout = QFormLayout(accounting_group)
        
        # Compte comptable de vente
        self.account_combo = QComboBox()
        self.account_combo.setMinimumWidth(250)
        self.account_combo.setToolTip("Sélectionnez le compte comptable de vente pour ce produit")
        self.load_sales_accounts()
        accounting_layout.addRow("Compte de vente:", self.account_combo)
        
        layout.addWidget(accounting_group)
        
        # === OPTIONS ===
        options_group = QGroupBox("Options")
        options_layout = QFormLayout(options_group)
        
        # Produit actif
        self.active_checkbox = QCheckBox("Produit actif")
        self.active_checkbox.setChecked(True)
        options_layout.addRow("", self.active_checkbox)
        
        layout.addWidget(options_group)
        
        # Configurer le scroll area
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # === BOUTONS (en dehors du scroll) ===
        buttons_widget = QWidget()
        buttons_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
            }
        """)
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(15, 10, 15, 10)
        
        self.cancel_btn = QPushButton("Annuler")
        self.save_btn = QPushButton("Modifier" if self.is_edit_mode else "Créer")
        
        # Forcer la couleur du texte des boutons
        self.cancel_btn.setStyleSheet("color: #2c3e50; font-weight: bold;")
        self.save_btn.setStyleSheet("color: #2c3e50; font-weight: bold;")
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addSpacing(8)  # Espacement entre les boutons
        buttons_layout.addWidget(self.save_btn)
        
        main_layout.addWidget(buttons_widget)
        
        # Connecter les signaux
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self.save_produit)
        self.cost_spinbox.valueChanged.connect(self.update_margin)
        self.price_spinbox.valueChanged.connect(self.update_margin)
        self.stock_spinbox.valueChanged.connect(self.check_stock_alert)
        self.stock_min_spinbox.valueChanged.connect(self.check_stock_alert)
        
        # Focus sur le premier champ
        self.name_edit.setFocus()
    
    def setup_style(self):
        """Appliquer les styles"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QScrollArea {
                border: none;
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
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
                min-width: 80px;
                max-height: 35px;
                color: #2c3e50;
                text-align: center;
                background-color: #f8f9fa;
            }
            QPushButton#save_btn {
                background-color: #e3f2fd;
                color: #1976d2;
                border: 1px solid #1976d2;
            }
            QPushButton#save_btn:hover {
                background-color: #bbdefb;
                border-color: #1565c0;
                color: #0d47a1;
            }
            QPushButton#save_btn:pressed {
                background-color: #90caf9;
                color: #0d47a1;
            }
            QPushButton#cancel_btn {
                background-color: #f5f5f5;
                color: #424242;
                border: 1px solid #9e9e9e;
            }
            QPushButton#cancel_btn:hover {
                background-color: #eeeeee;
                border-color: #757575;
                color: #212121;
            }
            QPushButton#cancel_btn:pressed {
                background-color: #e0e0e0;
                color: #212121;
            }
        """)
        
        self.save_btn.setObjectName("save_btn")
        self.cancel_btn.setObjectName("cancel_btn")
        
        # S'assurer que les boutons utilisent une police claire
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.save_btn.setFont(font)
        self.cancel_btn.setFont(font)
    
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
            
            comptabilite_controller = ComptabiliteController(user_controller=self.user_controller)
            
            # Récupérer l'entreprise depuis le contrôleur produit
            entreprise_id = self.get_enterprise_id()
            
            # Filtrer les comptes par entreprise
            comptes = comptabilite_controller.get_comptes_vente(entreprise_id=entreprise_id)
            
            self.account_combo.clear()
            self.account_combo.addItem("-- Sélectionner un compte --", None)
            
            for compte in comptes:
                self.account_combo.addItem(f"{compte.numero} - {compte.nom}", compte.id)
                
        except Exception as e:
            print(f"Erreur lors du chargement des comptes: {e}")
            self.account_combo.addItem("Erreur - Comptes indisponibles", None)
    
    def get_enterprise_id(self):
        """Récupérer l'ID de l'entreprise depuis le contrôleur produit"""
        try:
            if self.controller and hasattr(self.controller, 'pos_id'):
                # Récupérer l'entreprise depuis le pos_id
                from ayanna_erp.database.database_manager import get_database_manager
                
                db_manager = get_database_manager()
                session = db_manager.get_session()
                
                try:
                    # Récupérer le POS et son entreprise
                    from ayanna_erp.database.database_manager import POSPoint
                    pos = session.query(POSPoint).filter_by(id=self.controller.pos_id).first()
                    
                    if pos:
                        return pos.enterprise_id
                    else:
                        print(f"⚠️  POS avec ID {self.controller.pos_id} non trouvé")
                        return None
                finally:
                    session.close()
            else:
                print("⚠️  Contrôleur ou pos_id non disponible")
                return None
        except Exception as e:
            print(f"❌ Erreur lors de la récupération de l'entreprise: {e}")
            return None
    
    def check_stock_alert(self):
        """Vérifier et afficher les alertes de stock"""
        stock = self.stock_spinbox.value()
        stock_min = self.stock_min_spinbox.value()
        
        if stock == 0:
            self.stock_alert_label.setText("⚠️ Stock épuisé")
            self.stock_alert_label.setStyleSheet("color: #dc3545; font-weight: bold;")
        elif stock <= stock_min and stock_min > 0:
            self.stock_alert_label.setText("⚠️ Stock faible")
            self.stock_alert_label.setStyleSheet("color: #fd7e14; font-weight: bold;")
        else:
            self.stock_alert_label.setText("✅ Stock correct")
            self.stock_alert_label.setStyleSheet("color: #28a745; font-weight: bold;")
    
    def load_produit_data(self):
        """Charger les données du produit en mode édition"""
        if not self.produit_data:
            return
        
        # Gestion des objets SQLAlchemy et dictionnaires
        if hasattr(self.produit_data, 'name'):
            # Objet SQLAlchemy
            self.name_edit.setText(self.produit_data.name or '')
            self.description_edit.setPlainText(self.produit_data.description or '')
            
            # Catégorie
            category = self.produit_data.category or ''
            if category:
                index = self.category_combo.findText(category)
                if index >= 0:
                    self.category_combo.setCurrentIndex(index)
                else:
                    self.category_combo.setCurrentText(category)
            
            # Unité
            unit = self.produit_data.unit or 'pièce'
            index = self.unit_combo.findText(unit)
            if index >= 0:
                self.unit_combo.setCurrentIndex(index)
            else:
                self.unit_combo.setCurrentText(unit)
            
            self.cost_spinbox.setValue(float(self.produit_data.cost or 0))
            self.price_spinbox.setValue(float(self.produit_data.price_unit or 0))
            self.stock_spinbox.setValue(float(self.produit_data.stock_quantity or 0))
            self.stock_min_spinbox.setValue(float(self.produit_data.stock_min or 0))
            self.active_checkbox.setChecked(bool(self.produit_data.is_active))
            
            # Sélectionner le compte comptable
            if hasattr(self.produit_data, 'account_id') and self.produit_data.account_id:
                for i in range(self.account_combo.count()):
                    if self.account_combo.itemData(i) == self.produit_data.account_id:
                        self.account_combo.setCurrentIndex(i)
                        break
        else:
            # Dictionnaire (rétrocompatibilité)
            self.name_edit.setText(self.produit_data.get('name', ''))
            self.description_edit.setPlainText(self.produit_data.get('description', ''))
            
            # Catégorie
            category = self.produit_data.get('category', '')
            if category:
                index = self.category_combo.findText(category)
                if index >= 0:
                    self.category_combo.setCurrentIndex(index)
                else:
                    self.category_combo.setCurrentText(category)
            
            # Unité
            unit = self.produit_data.get('unit', 'pièce')
            index = self.unit_combo.findText(unit)
            if index >= 0:
                self.unit_combo.setCurrentIndex(index)
            else:
                self.unit_combo.setCurrentText(unit)
            
            self.cost_spinbox.setValue(float(self.produit_data.get('cost', 0)))
            self.price_spinbox.setValue(float(self.produit_data.get('price_unit', 0)))
            self.stock_spinbox.setValue(float(self.produit_data.get('stock_quantity', 0)))
            self.stock_min_spinbox.setValue(float(self.produit_data.get('stock_min', 0)))
            self.active_checkbox.setChecked(bool(self.produit_data.get('is_active', True)))
            
            # Sélectionner le compte comptable
            account_id = self.produit_data.get('account_id')
            if account_id:
                for i in range(self.account_combo.count()):
                    if self.account_combo.itemData(i) == account_id:
                        self.account_combo.setCurrentIndex(i)
                        break
        
        # Mettre à jour les calculs
        self.update_margin()
        self.check_stock_alert()
    
    def validate_form(self):
        """Valider les données du formulaire"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Erreur", "Le nom du produit est obligatoire.")
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
            'category': self.category_combo.currentText().strip(),
            'unit': self.unit_combo.currentText().strip(),
            'cost': round(self.cost_spinbox.value(), 2),
            'price_unit': round(self.price_spinbox.value(), 2),
            'stock_quantity': round(self.stock_spinbox.value(), 2),
            'stock_min': round(self.stock_min_spinbox.value(), 2),
            'is_active': self.active_checkbox.isChecked(),
            'account_id': self.account_combo.currentData()  # ID du compte comptable sélectionné
        }
    
    def save_produit(self):
        """Sauvegarder le produit"""
        if not self.validate_form():
            return
        
        try:
            form_data = self.get_form_data()
            
            if self.controller:
                if self.is_edit_mode:
                    # Modification
                    if hasattr(self.produit_data, 'id'):
                        produit_id = self.produit_data.id  # Objet SQLAlchemy
                    else:
                        produit_id = self.produit_data.get('id')  # Dictionnaire
                    success = self.controller.update_product(produit_id, form_data)
                    if success:
                        QMessageBox.information(self, "Succès", "Produit modifié avec succès !")
                    else:
                        QMessageBox.critical(self, "Erreur", "Erreur lors de la modification du produit.")
                        return
                else:
                    # Création
                    success = self.controller.add_product(form_data)
                    if success:
                        QMessageBox.information(self, "Succès", "Produit créé avec succès !")
                    else:
                        QMessageBox.critical(self, "Erreur", "Erreur lors de la création du produit.")
                        return
            
            # Émettre le signal avec les données
            self.produit_saved.emit(form_data)
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur inattendue: {str(e)}")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Test du formulaire
    form = ProduitForm()
    form.show()
    
    sys.exit(app.exec())
