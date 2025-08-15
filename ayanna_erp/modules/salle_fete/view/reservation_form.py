"""
Formulaire modal pour ajouter/modifier une réservation
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                            QFormLayout, QPushButton, QLineEdit, QLabel, 
                            QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, 
                            QMessageBox, QGroupBox, QGridLayout, QDateTimeEdit,
                            QTableWidget, QTableWidgetItem, QHeaderView,
                            QScrollArea, QWidget, QCheckBox)
from PyQt6.QtCore import Qt, QDateTime, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime
from ayanna_erp.database.database_manager import DatabaseManager

# Import des contrôleurs
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from controller.service_controller import ServiceController
from controller.produit_controller import ProduitController
from controller.reservation_controller import ReservationController


class ReservationForm(QDialog):
    """Formulaire modal pour créer/modifier une réservation"""
    
    # Signal émis quand la réservation est sauvegardée
    reservation_saved = pyqtSignal(dict)
    
    def __init__(self, parent=None, reservation_data=None, db_manager=None, pos_id=1):
        super().__init__(parent)
        self.reservation_data = reservation_data
        self.db_manager = db_manager or DatabaseManager()
        self.is_edit_mode = reservation_data is not None
        self.pos_id = pos_id
        
        # Initialiser les contrôleurs avec le bon pos_id
        self.service_controller = ServiceController(pos_id=pos_id)
        self.produit_controller = ProduitController(pos_id=pos_id)
        self.reservation_controller = ReservationController(pos_id=pos_id)
        
        # Lists pour stocker les cases à cocher
        self.service_checkboxes = []
        self.product_checkboxes = []
        
        self.setWindowTitle("Modifier la réservation" if self.is_edit_mode else "Nouvelle réservation")
        self.setModal(True)
        self.setMinimumSize(900, 700)  # Augmenté pour une meilleure visibilité
        self.resize(1000, 800)  # Taille par défaut plus grande
        
        self.setup_ui()
        if self.is_edit_mode:
            self.load_reservation_data()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        # Layout principal du dialog
        main_layout = QVBoxLayout(self)
        
        # Créer un scroll area pour tout le contenu
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Widget principal qui contiendra tout le contenu
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # Informations générales
        general_group = QGroupBox("Informations générales")
        general_layout = QGridLayout(general_group)
        
        # Client et Téléphone (ligne 1)
        self.client_combo = QComboBox()
        self.client_combo.setEditable(True)
        self.client_combo.setPlaceholderText("Sélectionner un client ou taper un nouveau nom...")
        self.load_clients()  # Charger les clients depuis la base de données
        
        self.client_phone_edit = QLineEdit()
        self.client_phone_edit.setPlaceholderText("Téléphone du client")
        
        general_layout.addWidget(QLabel("Client:"), 0, 0)
        general_layout.addWidget(self.client_combo, 0, 1)
        general_layout.addWidget(QLabel("Téléphone:"), 0, 2)
        general_layout.addWidget(self.client_phone_edit, 0, 3)
        
        # Thème et Date (ligne 2)
        self.theme_edit = QLineEdit()
        self.theme_edit.setPlaceholderText("Thème de l'événement (ex: Mariage de Jean et Marie)")
        
        self.event_datetime = QDateTimeEdit()
        self.event_datetime.setDateTime(QDateTime.currentDateTime())
        self.event_datetime.setDisplayFormat("dd/MM/yyyy hh:mm")
        
        general_layout.addWidget(QLabel("Thème:"), 1, 0)
        general_layout.addWidget(self.theme_edit, 1, 1)
        general_layout.addWidget(QLabel("Date et heure:"), 1, 2)
        general_layout.addWidget(self.event_datetime, 1, 3)
        
        # Type d'événement et Nombre d'invités (ligne 3)
        self.event_type_combo = QComboBox()
        self.event_type_combo.addItems([
            "Mariage", "Anniversaire", "Baptême", "Communion", 
            "Réunion d'entreprise", "Cocktail", "Autre"
        ])
        
        self.guests_spinbox = QSpinBox()
        self.guests_spinbox.setRange(1, 500)
        self.guests_spinbox.setValue(50)
        
        general_layout.addWidget(QLabel("Type d'événement:"), 2, 0)
        general_layout.addWidget(self.event_type_combo, 2, 1)
        general_layout.addWidget(QLabel("Nombre d'invités:"), 2, 2)
        general_layout.addWidget(self.guests_spinbox, 2, 3)
        
        # Notes (ligne 4, sur toute la largeur)
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        self.notes_edit.setPlaceholderText("Notes ou demandes spéciales...")
        
        general_layout.addWidget(QLabel("Notes:"), 3, 0)
        general_layout.addWidget(self.notes_edit, 3, 1, 1, 3)  # Span sur 3 colonnes
        
        # Services et produits
        items_group = QGroupBox("Services et Produits")
        items_layout = QVBoxLayout(items_group)
        
        # Créer un layout horizontal pour services et produits côte à côte
        services_products_layout = QHBoxLayout()
        
        # Section Services
        services_section = QGroupBox("Services disponibles")
        services_layout = QVBoxLayout(services_section)
        
        # Scroll area pour les services
        services_scroll = QScrollArea()
        services_scroll.setWidgetResizable(True)
        services_scroll.setMaximumHeight(200)
        
        self.services_widget = QWidget()
        self.services_layout = QVBoxLayout(self.services_widget)
        
        # Charger les services disponibles
        self.load_available_services()
        
        services_scroll.setWidget(self.services_widget)
        services_layout.addWidget(services_scroll)
        
        # Section Produits
        products_section = QGroupBox("Produits disponibles")
        products_layout = QVBoxLayout(products_section)
        
        # Scroll area pour les produits
        products_scroll = QScrollArea()
        products_scroll.setWidgetResizable(True)
        products_scroll.setMaximumHeight(200)
        
        self.products_widget = QWidget()
        self.products_layout = QVBoxLayout(self.products_widget)
        
        # Charger les produits disponibles
        self.load_available_products()
        
        products_scroll.setWidget(self.products_widget)
        products_layout.addWidget(products_scroll)
        
        # Ajouter les deux sections côte à côte
        services_products_layout.addWidget(services_section)
        services_products_layout.addWidget(products_section)
        
        items_layout.addLayout(services_products_layout)
        
        # Résumé des sélections
        selection_summary = QGroupBox("Résumé des sélections")
        self.selection_layout = QVBoxLayout(selection_summary)
        
        self.selection_label = QLabel("Aucun service ou produit sélectionné")
        self.selection_label.setStyleSheet("color: #7F8C8D; font-style: italic;")
        self.selection_layout.addWidget(self.selection_label)
        
        items_layout.addWidget(selection_summary)
        
        # Zone des totaux
        totals_group = QGroupBox("Résumé financier")
        totals_layout = QGridLayout(totals_group)
        
        self.subtotal_label = QLabel("0.00 €")
        self.discount_spinbox = QDoubleSpinBox()
        self.discount_spinbox.setRange(0, 100)
        self.discount_spinbox.setSuffix(" %")
        self.discount_spinbox.valueChanged.connect(self.calculate_totals)
        
        self.tax_rate_spinbox = QDoubleSpinBox()
        self.tax_rate_spinbox.setRange(0, 30)
        self.tax_rate_spinbox.setValue(20)  # TVA à 20% par défaut
        self.tax_rate_spinbox.setSuffix(" %")
        self.tax_rate_spinbox.valueChanged.connect(self.calculate_totals)
        
        self.tax_amount_label = QLabel("0.00 €")
        self.total_label = QLabel("0.00 €")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #E74C3C;")
        
        # Acompte
        self.deposit_spinbox = QDoubleSpinBox()
        self.deposit_spinbox.setRange(0, 999999)
        self.deposit_spinbox.setSuffix(" €")
        self.deposit_spinbox.valueChanged.connect(self.calculate_totals)
        
        self.remaining_label = QLabel("0.00 €")
        self.remaining_label.setStyleSheet("font-weight: bold; color: #F39C12;")
        
        # Ligne 1: Sous-total et Remise
        totals_layout.addWidget(QLabel("Sous-total:"), 0, 0)
        totals_layout.addWidget(self.subtotal_label, 0, 1)
        totals_layout.addWidget(QLabel("Remise:"), 0, 2)
        totals_layout.addWidget(self.discount_spinbox, 0, 3)
        
        # Ligne 2: TVA et Montant TVA
        totals_layout.addWidget(QLabel("Taux de TVA:"), 1, 0)
        totals_layout.addWidget(self.tax_rate_spinbox, 1, 1)
        totals_layout.addWidget(QLabel("Montant TVA:"), 1, 2)
        totals_layout.addWidget(self.tax_amount_label, 1, 3)
        
        # Ligne 3: Total, Acompte et Solde
        totals_layout.addWidget(QLabel("TOTAL TTC:"), 2, 0)
        totals_layout.addWidget(self.total_label, 2, 1)
        totals_layout.addWidget(QLabel("Acompte:"), 2, 2)
        totals_layout.addWidget(self.deposit_spinbox, 2, 3)
        
        # Ligne 4: Solde restant (centré)
        remaining_layout = QHBoxLayout()
        remaining_layout.addWidget(QLabel("Solde restant:"))
        remaining_layout.addWidget(self.remaining_label)
        remaining_layout.addStretch()
        
        remaining_widget = QWidget()
        remaining_widget.setLayout(remaining_layout)
        totals_layout.addWidget(remaining_widget, 3, 0, 1, 4)  # Span sur 4 colonnes
        
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
        layout.addWidget(general_group)
        layout.addWidget(items_group)
        layout.addWidget(totals_group)
        layout.addLayout(buttons_layout)
        
        # Ajouter le widget content au scroll area
        scroll_area.setWidget(content_widget)
        
        # Ajouter le scroll area au layout principal du dialog
        main_layout.addWidget(scroll_area)
        
        # Connexion des signaux
        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self.save_reservation)
    
    
    def load_available_services(self):
        """Charger les services disponibles depuis la base de données"""
        try:
            # Connecter le signal pour recevoir les services
            self.service_controller.services_loaded.connect(self.on_services_loaded)
            
            # Charger les services
            self.service_controller.get_all_services()
            
        except Exception as e:
            print(f"Erreur lors du chargement des services: {e}")
            self.create_default_services()
    
    def load_available_products(self):
        """Charger les produits disponibles depuis la base de données"""
        try:
            # Connecter le signal pour recevoir les produits
            self.produit_controller.products_loaded.connect(self.on_products_loaded)
            
            # Charger les produits
            self.produit_controller.get_all_products()
            
        except Exception as e:
            print(f"Erreur lors du chargement des produits: {e}")
            self.create_default_products()
    
    def load_clients(self):
        """Charger les clients disponibles depuis la base de données"""
        try:
            from controller.client_controller import ClientController
            client_controller = ClientController(pos_id=self.pos_id)
            
            # Récupérer tous les clients
            clients = client_controller.get_all_clients()
            
            # Ajouter les clients au combo
            self.client_combo.clear()
            self.client_combo.addItem("", None)  # Option vide
            
            for client in clients:
                display_text = f"{client.nom} {client.prenom}"
                if client.telephone:
                    display_text += f" - {client.telephone}"
                
                # Stocker l'objet client en tant que données
                self.client_combo.addItem(display_text, client)
            
            # Connecter le signal de changement de sélection
            self.client_combo.currentIndexChanged.connect(self.on_client_selected)
            
        except Exception as e:
            print(f"Erreur lors du chargement des clients: {e}")
            # En cas d'erreur, permettre juste la saisie libre
            self.client_combo.setEditable(True)
    
    def on_client_selected(self, index):
        """Callback quand un client pré-enregistré est sélectionné"""
        if index <= 0:  # Option vide sélectionnée
            self.client_phone_edit.clear()
            self.client_email_edit.clear()
            return
        
        # Récupérer le client sélectionné
        client = self.client_combo.itemData(index)
        if client:
            # Pré-remplir les champs téléphone et email
            self.client_phone_edit.setText(client.telephone or "")
            self.client_email_edit.setText(client.email or "")
    
    def on_services_loaded(self, services):
        """Callback quand les services sont chargés"""
        # Vider le layout existant
        for i in reversed(range(self.services_layout.count())):
            self.services_layout.itemAt(i).widget().setParent(None)
        
        self.service_checkboxes.clear()
        
        if not services:
            self.create_default_services()
            return
        
        # Créer une case à cocher pour chaque service
        for service in services:
            checkbox = QCheckBox(f"{service.name} - {service.price:.2f} €")
            checkbox.setObjectName(f"service_{service.id}")
            checkbox.service_data = service
            checkbox.toggled.connect(self.update_selection_summary)
            
            self.service_checkboxes.append(checkbox)
            self.services_layout.addWidget(checkbox)
        
        # Ajouter un stretch pour pousser les éléments vers le haut
        self.services_layout.addStretch()
    
    def on_products_loaded(self, products):
        """Callback quand les produits sont chargés"""
        # Vider le layout existant
        for i in reversed(range(self.products_layout.count())):
            self.products_layout.itemAt(i).widget().setParent(None)
        
        self.product_checkboxes.clear()
        
        if not products:
            self.create_default_products()
            return
        
        # Créer une case à cocher pour chaque produit
        for product in products:
            checkbox = QCheckBox(f"{product.name} - {product.price_unit:.2f} €")
            checkbox.setObjectName(f"product_{product.id}")
            checkbox.product_data = product
            checkbox.toggled.connect(self.update_selection_summary)
            
            self.product_checkboxes.append(checkbox)
            self.products_layout.addWidget(checkbox)
        
        # Ajouter un stretch pour pousser les éléments vers le haut
        self.products_layout.addStretch()
    
    def create_default_services(self):
        """Créer des services par défaut si aucun n'est trouvé"""
        default_services = [
            {"name": "Service de base", "price": 100.0},
            {"name": "Animation DJ", "price": 200.0},
            {"name": "Décoration florale", "price": 150.0},
            {"name": "Service traiteur", "price": 300.0},
        ]
        
        for service_data in default_services:
            checkbox = QCheckBox(f"{service_data['name']} - {service_data['price']:.2f} €")
            checkbox.service_data = service_data
            checkbox.toggled.connect(self.update_selection_summary)
            
            self.service_checkboxes.append(checkbox)
            self.services_layout.addWidget(checkbox)
        
        self.services_layout.addStretch()
    
    def create_default_products(self):
        """Créer des produits par défaut si aucun n'est trouvé"""
        default_products = [
            {"name": "Chaises", "price": 5.0},
            {"name": "Tables", "price": 10.0},
            {"name": "Vaisselle", "price": 3.0},
            {"name": "Éclairage", "price": 50.0},
        ]
        
        for product_data in default_products:
            checkbox = QCheckBox(f"{product_data['name']} - {product_data['price']:.2f} €")
            checkbox.product_data = product_data
            checkbox.toggled.connect(self.update_selection_summary)
            
            self.product_checkboxes.append(checkbox)
            self.products_layout.addWidget(checkbox)
        
        self.products_layout.addStretch()
    
    def update_selection_summary(self):
        """Mettre à jour le résumé des sélections"""
        selected_items = []
        total = 0.0
        
        # Vérifier les services sélectionnés
        for checkbox in self.service_checkboxes:
            if checkbox.isChecked():
                service_data = checkbox.service_data
                if hasattr(service_data, 'name'):
                    selected_items.append(f"🔧 {service_data.name}")
                    total += float(service_data.price)
                else:
                    selected_items.append(f"🔧 {service_data['name']}")
                    total += float(service_data['price'])
        
        # Vérifier les produits sélectionnés
        for checkbox in self.product_checkboxes:
            if checkbox.isChecked():
                product_data = checkbox.product_data
                if hasattr(product_data, 'name'):
                    selected_items.append(f"📦 {product_data.name}")
                    total += float(product_data.price_unit)
                else:
                    selected_items.append(f"📦 {product_data['name']}")
                    total += float(product_data['price'])
        
        # Mettre à jour l'affichage
        if selected_items:
            summary_text = "\n".join(selected_items)
            summary_text += f"\n\nTotal: {total:.2f} €"
            self.selection_label.setText(summary_text)
            self.selection_label.setStyleSheet("color: #27AE60; font-weight: bold;")
        else:
            self.selection_label.setText("Aucun service ou produit sélectionné")
            self.selection_label.setStyleSheet("color: #7F8C8D; font-style: italic;")
        
        # Calculer les totaux
        self.calculate_totals()
    
    def calculate_totals(self):
        """Calculer les totaux"""
        subtotal = 0.0
        
        # Calculer le sous-total basé sur les sélections
        for checkbox in self.service_checkboxes:
            if checkbox.isChecked():
                service_data = checkbox.service_data
                if hasattr(service_data, 'price'):
                    subtotal += float(service_data.price)
                else:
                    subtotal += float(service_data['price'])
        
        for checkbox in self.product_checkboxes:
            if checkbox.isChecked():
                product_data = checkbox.product_data
                if hasattr(product_data, 'price_unit'):
                    subtotal += float(product_data.price_unit)
                else:
                    subtotal += float(product_data['price'])
        
        # Appliquer la remise
        discount_percent = self.discount_spinbox.value()
        discount_amount = subtotal * (discount_percent / 100)
        subtotal_after_discount = subtotal - discount_amount
        
        # Calculer la TVA
        tax_rate = self.tax_rate_spinbox.value()
        tax_amount = subtotal_after_discount * (tax_rate / 100)
        total_ttc = subtotal_after_discount + tax_amount
        
        # Calculer le solde restant
        deposit = self.deposit_spinbox.value()
        remaining = total_ttc - deposit
        
        # Mettre à jour les labels
        self.subtotal_label.setText(f"{subtotal:.2f} €")
        self.tax_amount_label.setText(f"{tax_amount:.2f} €")
        self.total_label.setText(f"{total_ttc:.2f} €")
        self.remaining_label.setText(f"{remaining:.2f} €")
        
        # Changer la couleur du solde selon le montant
        if remaining <= 0:
            self.remaining_label.setStyleSheet("font-weight: bold; color: #27AE60;")
        elif remaining < total_ttc * 0.5:
            self.remaining_label.setStyleSheet("font-weight: bold; color: #F39C12;")
        else:
            self.remaining_label.setStyleSheet("font-weight: bold; color: #E74C3C;")
    
    def load_reservation_data(self):
        """Charger les données de la réservation pour modification"""
        if not self.reservation_data:
            return
        
        # TODO: Implémenter le chargement des données depuis la base
        # Pour l'instant, on utilise des données d'exemple
        self.client_combo.setCurrentText(self.reservation_data.get('client', ''))
        self.event_type_combo.setCurrentText(self.reservation_data.get('type', ''))
        self.guests_spinbox.setValue(self.reservation_data.get('guests', 50))
        self.reference_edit.setText(self.reservation_data.get('reference', ''))
        self.notes_edit.setPlainText(self.reservation_data.get('notes', ''))
    
    def save_reservation(self):
        """Sauvegarder la réservation"""
        # Validation des données
        if not self.client_combo.currentText().strip():
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner ou saisir un client.")
            return
        
        if not self.event_type_combo.currentText().strip():
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un type d'événement.")
            return
        
        # Récupération des données
        # Gestion du client (pré-enregistré ou nouveau)
        client_id = None
        client_nom = None
        client_prenom = None
        client_telephone = self.client_phone_edit.text().strip()
        
        # Vérifier si un client pré-enregistré est sélectionné
        current_index = self.client_combo.currentIndex()
        if current_index > 0:  # Un client de la liste est sélectionné
            client = self.client_combo.itemData(current_index)
            if client:
                client_id = client.id
                # Utiliser les données du champ si remplies, sinon celles du client
                if not client_telephone:
                    client_telephone = client.telephone or ""
        else:
            # Client saisi manuellement - parser le nom
            client_text = self.client_combo.currentText().strip()
            if client_text:
                # Essayer de séparer nom et prénom
                parts = client_text.split(' ', 1)
                client_nom = parts[0]
                client_prenom = parts[1] if len(parts) > 1 else ""
        
        reservation_data = {
            'partner_id': client_id,  # ID du client pré-enregistré ou None
            'client_nom': client_nom,  # Nom saisi directement ou None
            'client_prenom': client_prenom,  # Prénom saisi directement ou None  
            'client_telephone': client_telephone,  # Téléphone (peut venir des deux sources)
            'theme': self.theme_edit.text().strip(),  # Thème de l'événement
            'event_datetime': self.event_datetime.dateTime().toPyDateTime(),
            'event_type': self.event_type_combo.currentText(),
            'guests': self.guests_spinbox.value(),
            'notes': self.notes_edit.toPlainText().strip(),
            'subtotal': float(self.subtotal_label.text().replace(" €", "").replace(",", ".")),
            'discount': self.discount_spinbox.value(),
            'tax_rate': self.tax_rate_spinbox.value(),
            'tax_amount': float(self.tax_amount_label.text().replace(" €", "").replace(",", ".")),
            'total': float(self.total_label.text().replace(" €", "").replace(",", ".")),
            'deposit': self.deposit_spinbox.value(),
            'remaining': float(self.remaining_label.text().replace(" €", "").replace(",", ".")),
            'status': 'En attente',
            'items': []
        }
        
        # Récupération des services et produits sélectionnés
        for checkbox in self.service_checkboxes:
            if checkbox.isChecked():
                service_data = checkbox.service_data
                item = {
                    'type': 'Service',
                    'name': service_data.name if hasattr(service_data, 'name') else service_data['name'],
                    'unit_price': float(service_data.price) if hasattr(service_data, 'price') else float(service_data['price']),
                    'quantity': 1,
                    'total': float(service_data.price) if hasattr(service_data, 'price') else float(service_data['price'])
                }
                reservation_data['items'].append(item)
        
        for checkbox in self.product_checkboxes:
            if checkbox.isChecked():
                product_data = checkbox.product_data
                item = {
                    'type': 'Produit',
                    'name': product_data.name if hasattr(product_data, 'name') else product_data['name'],
                    'unit_price': float(product_data.price_unit) if hasattr(product_data, 'price_unit') else float(product_data['price']),
                    'quantity': 1,
                    'total': float(product_data.price_unit) if hasattr(product_data, 'price_unit') else float(product_data['price'])
                }
                reservation_data['items'].append(item)
        
        # Sauvegarder dans la base de données
        try:
            # Adapter les données pour le contrôleur
            controller_data = {
                'partner_id': reservation_data['partner_id'],  # Client pré-enregistré
                'client_nom': reservation_data['client_nom'],  # Nom client direct
                'client_prenom': reservation_data['client_prenom'],  # Prénom client direct
                'client_telephone': reservation_data['client_telephone'],  # Téléphone
                'theme': reservation_data['theme'],  # Thème de l'événement
                'event_date': reservation_data['event_datetime'],  # Conversion nom de champ
                'event_type': reservation_data['event_type'],
                'guests_count': reservation_data['guests'],  # Conversion nom de champ
                'status': 'En attente',
                'notes': reservation_data['notes'],
                'discount_percent': reservation_data['discount'],
                'tax_rate': reservation_data['tax_rate'],
                'deposit': reservation_data['deposit'],  # Acompte pour création de paiement
                'payment_method': 'cash',  # Méthode de paiement par défaut
                'created_by': 1  # ID utilisateur par défaut
            }
            
            # Debug : afficher les données client
            print(f"🔍 Debug - Données client envoyées au contrôleur:")
            print(f"   - partner_id: {controller_data['partner_id']}")
            print(f"   - client_nom: {controller_data['client_nom']}")
            print(f"   - client_prenom: {controller_data['client_prenom']}")
            print(f"   - client_telephone: {controller_data['client_telephone']}")
            print(f"   - theme: {controller_data['theme']}")
            
            # Préparer les données des services
            services_data = []
            for checkbox in self.service_checkboxes:
                if checkbox.isChecked():
                    service_data = checkbox.service_data
                    if hasattr(service_data, 'id'):  # Objet réel de la DB
                        services_data.append({
                            'service_id': service_data.id,
                            'quantity': 1,
                            'unit_price': float(service_data.price)
                        })
            
            # Préparer les données des produits
            products_data = []
            for checkbox in self.product_checkboxes:
                if checkbox.isChecked():
                    product_data = checkbox.product_data
                    if hasattr(product_data, 'id'):  # Objet réel de la DB
                        products_data.append({
                            'product_id': product_data.id,
                            'quantity': 1,
                            'unit_price': float(product_data.price_unit)
                        })
            
            if self.is_edit_mode:
                # Modification d'une réservation existante
                controller_data['id'] = self.reservation_data.get('id')
                updated_reservation = self.reservation_controller.update_reservation(
                    controller_data['id'], 
                    controller_data,
                    services_data,
                    products_data
                )
                if updated_reservation:
                    # Émettre le signal avec les données originales
                    self.reservation_saved.emit(reservation_data)
                    
                    QMessageBox.information(
                        self, 
                        "Succès", 
                        "Réservation modifiée avec succès !"
                    )
                    self.accept()
                else:
                    QMessageBox.critical(
                        self, 
                        "Erreur", 
                        "Erreur lors de la modification de la réservation."
                    )
            else:
                # Création d'une nouvelle réservation
                new_reservation = self.reservation_controller.create_reservation(
                    controller_data, 
                    services_data, 
                    products_data
                )
                if new_reservation:
                    reservation_data['id'] = new_reservation.id
                    
                    # Émettre le signal avec les données originales
                    self.reservation_saved.emit(reservation_data)
                    
                    QMessageBox.information(
                        self, 
                        "Succès", 
                        f"Réservation créée avec succès ! (ID: {new_reservation.id})"
                    )
                    self.accept()
                else:
                    QMessageBox.critical(
                        self, 
                        "Erreur", 
                        "Erreur lors de la création de la réservation."
                    )
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Erreur", 
                f"Erreur lors de la sauvegarde: {str(e)}"
            )
