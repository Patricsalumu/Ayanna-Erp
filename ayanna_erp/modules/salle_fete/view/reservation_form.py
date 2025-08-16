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
        self.product_quantity_spinboxes = []  # Pour les quantités des produits
        
        self.setWindowTitle("Modifier la réservation" if self.is_edit_mode else "Nouvelle réservation")
        self.setModal(True)
        self.setMinimumSize(900, 700)  # Augmenté pour une meilleure visibilité
        self.resize(1000, 800)  # Taille par défaut plus grande
        
        self.setup_ui()
        
        # Désactiver l'acompte en mode édition
        if self.is_edit_mode:
            self.deposit_spinbox.setEnabled(False)
            self.deposit_spinbox.setToolTip("L'acompte ne peut pas être modifié. Utilisez l'onglet Paiements pour ajouter des paiements.")
            
        # Retarder le chargement des données jusqu'à ce que l'UI soit complètement créée
        if self.is_edit_mode:
            # Utiliser un timer pour retarder le chargement
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, self.load_reservation_data)
    
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
        
        # Statut (ligne 5, visible seulement en mode édition)
        self.status_combo = QComboBox()
        self.status_combo.addItems(["En attente", "A venir", "Annuller", "Passé"])
        
        general_layout.addWidget(QLabel("Statut:"), 4, 0)
        general_layout.addWidget(self.status_combo, 4, 1)
        
        # Masquer le statut en mode création
        if not self.is_edit_mode:
            general_layout.itemAtPosition(4, 0).widget().setVisible(False)  # Label
            self.status_combo.setVisible(False)
        
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
        
        # Résumé des sélections en deux colonnes
        selection_summary = QGroupBox("Résumé des sélections")
        self.selection_layout = QHBoxLayout(selection_summary)
        
        # Colonne services (gauche)
        services_group = QGroupBox("Services sélectionnés")
        services_layout = QVBoxLayout(services_group)
        self.services_summary_label = QLabel("Aucun service sélectionné")
        self.services_summary_label.setStyleSheet("color: #7F8C8D; font-style: italic;")
        self.services_summary_label.setWordWrap(True)
        services_layout.addWidget(self.services_summary_label)
        
        # Colonne produits (droite)
        products_group = QGroupBox("Produits sélectionnés")
        products_layout = QVBoxLayout(products_group)
        self.products_summary_label = QLabel("Aucun produit sélectionné")
        self.products_summary_label.setStyleSheet("color: #7F8C8D; font-style: italic;")
        self.products_summary_label.setWordWrap(True)
        products_layout.addWidget(self.products_summary_label)
        
        # Ajouter les deux colonnes
        self.selection_layout.addWidget(services_group)
        self.selection_layout.addWidget(products_group)
        
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
        self.product_quantity_spinboxes = []  # Pour stocker les spinboxes de quantité
        
        if not products:
            self.create_default_products()
            return
        
        # Créer une case à cocher avec quantité pour chaque produit
        for product in products:
            # Widget conteneur pour checkbox + quantité
            product_widget = QWidget()
            product_layout = QHBoxLayout(product_widget)
            product_layout.setContentsMargins(0, 0, 0, 0)
            
            # Checkbox du produit
            checkbox = QCheckBox(f"{product.name} - {product.price_unit:.2f} €")
            checkbox.setObjectName(f"product_{product.id}")
            checkbox.product_data = product
            checkbox.toggled.connect(self.update_selection_summary)
            
            # Spinbox pour la quantité
            quantity_spinbox = QSpinBox()
            quantity_spinbox.setRange(1, 999)
            quantity_spinbox.setValue(1)
            quantity_spinbox.setEnabled(False)  # Désactivé par défaut
            quantity_spinbox.setMaximumWidth(60)
            quantity_spinbox.setToolTip("Quantité")
            quantity_spinbox.valueChanged.connect(self.update_selection_summary)
            
            # Connecter checkbox et spinbox
            checkbox.toggled.connect(lambda checked, spinbox=quantity_spinbox: spinbox.setEnabled(checked))
            
            # Ajouter au layout
            product_layout.addWidget(checkbox)
            product_layout.addWidget(QLabel("Qté:"))
            product_layout.addWidget(quantity_spinbox)
            product_layout.addStretch()  # Pousser vers la gauche
            
            # Stocker les références
            self.product_checkboxes.append(checkbox)
            self.product_quantity_spinboxes.append(quantity_spinbox)
            
            # Ajouter au layout principal
            self.products_layout.addWidget(product_widget)
        
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
        """Mettre à jour le résumé des sélections en deux colonnes"""
        selected_services = []
        selected_products = []
        total_services = 0.0
        total_products = 0.0
        
        # Vérifier les services sélectionnés
        for checkbox in self.service_checkboxes:
            if checkbox.isChecked():
                service_data = checkbox.service_data
                if hasattr(service_data, 'name'):
                    name = service_data.name
                    price = float(service_data.price)
                else:
                    name = service_data['name']
                    price = float(service_data['price'])
                
                selected_services.append(f"🔧 {name} - {price:.2f} €")
                total_services += price
        
        # Vérifier les produits sélectionnés avec quantités
        for i, checkbox in enumerate(self.product_checkboxes):
            if checkbox.isChecked():
                product_data = checkbox.product_data
                
                # Récupérer la quantité du spinbox correspondant
                quantity = 1
                if i < len(self.product_quantity_spinboxes):
                    quantity = self.product_quantity_spinboxes[i].value()
                
                if hasattr(product_data, 'name'):
                    name = product_data.name
                    unit_price = float(product_data.price_unit)
                else:
                    name = product_data['name']
                    unit_price = float(product_data['price'])
                
                line_total = unit_price * quantity
                selected_products.append(f"📦 {name} (x{quantity}) - {line_total:.2f} €")
                total_products += line_total
        
        # Mettre à jour l'affichage des services
        if selected_services:
            services_text = "\n".join(selected_services)
            services_text += f"\n\nSous-total services: {total_services:.2f} €"
            self.services_summary_label.setText(services_text)
            self.services_summary_label.setStyleSheet("color: #27AE60; font-weight: bold;")
        else:
            self.services_summary_label.setText("Aucun service sélectionné")
            self.services_summary_label.setStyleSheet("color: #7F8C8D; font-style: italic;")
        
        # Mettre à jour l'affichage des produits
        if selected_products:
            products_text = "\n".join(selected_products)
            products_text += f"\n\nSous-total produits: {total_products:.2f} €"
            self.products_summary_label.setText(products_text)
            self.products_summary_label.setStyleSheet("color: #3498DB; font-weight: bold;")
        else:
            self.products_summary_label.setText("Aucun produit sélectionné")
            self.products_summary_label.setStyleSheet("color: #7F8C8D; font-style: italic;")
        
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
        
        for i, checkbox in enumerate(self.product_checkboxes):
            if checkbox.isChecked():
                product_data = checkbox.product_data
                
                # Récupérer la quantité du spinbox correspondant
                quantity = 1
                if i < len(self.product_quantity_spinboxes):
                    quantity = self.product_quantity_spinboxes[i].value()
                
                if hasattr(product_data, 'price_unit'):
                    line_total = float(product_data.price_unit) * quantity
                    subtotal += line_total
                else:
                    line_total = float(product_data['price']) * quantity
                    subtotal += line_total
        
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
            print("❌ Aucune donnée de réservation fournie")
            return
        
        print(f"🔍 Données de réservation reçues: {self.reservation_data}")
        
        # Pré-remplir les informations client
        client_name = self.reservation_data.get('client_nom', '')
        print(f"📝 Nom client: '{client_name}'")
        self.client_combo.setCurrentText(client_name)
        self.client_phone_edit.setText(self.reservation_data.get('client_telephone', ''))
        
        # Pré-remplir les informations de l'événement
        self.event_type_combo.setCurrentText(self.reservation_data.get('event_type', ''))
        self.guests_spinbox.setValue(self.reservation_data.get('guests_count', 50))
        self.theme_edit.setText(self.reservation_data.get('theme', ''))
        
        # Pré-remplir date et heure
        event_date = self.reservation_data.get('event_date')
        if event_date:
            from datetime import datetime
            if isinstance(event_date, str):
                try:
                    event_date = datetime.fromisoformat(event_date.replace('Z', '+00:00'))
                except:
                    event_date = datetime.now()
            
            # Utiliser le widget QDateTimeEdit combiné
            self.event_datetime.setDateTime(event_date)
        
        # Pré-remplir les notes
        self.notes_edit.setPlainText(self.reservation_data.get('notes', ''))
        
        # Pré-remplir le statut (seulement en mode édition)
        if self.is_edit_mode:
            status = self.reservation_data.get('status', 'En attente')
            index = self.status_combo.findText(status)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
        
        # Pré-remplir les montants et taux
        self.tax_rate_spinbox.setValue(self.reservation_data.get('tax_rate', 0))
        self.discount_spinbox.setValue(self.reservation_data.get('discount_percent', 0))
        
        # Pré-remplir l'acompte (même si désactivé)
        total_paid = self.reservation_data.get('total_paid', 0)
        self.deposit_spinbox.setValue(total_paid)
        
        # Pré-cocher les services sélectionnés
        self._load_selected_services()
        
        # Pré-cocher les produits sélectionnés  
        self._load_selected_products()
        
        # Mettre à jour l'affichage des totaux
        self.calculate_totals()
    
    def _load_selected_services(self):
        """Charger et cocher les services sélectionnés"""
        if not self.reservation_data:
            return
            
        selected_services = self.reservation_data.get('services', [])
        service_names = [service['name'] for service in selected_services]
        
        # Parcourir les checkboxes de services et cocher ceux qui sont sélectionnés
        for checkbox in self.service_checkboxes:
            if hasattr(checkbox, 'service_data'):
                service_name = checkbox.service_data.name
                
                # Vérifier si ce service est dans les services sélectionnés
                if service_name in service_names:
                    checkbox.setChecked(True)
    
    def _load_selected_products(self):
        """Charger et cocher les produits sélectionnés"""
        if not self.reservation_data:
            return
            
        selected_products = self.reservation_data.get('products', [])
        
        # Parcourir les checkboxes de produits et cocher ceux qui sont sélectionnés
        for i, checkbox in enumerate(self.product_checkboxes):
            if hasattr(checkbox, 'product_data'):
                product_name = checkbox.product_data.name
                
                # Trouver le produit correspondant dans les données
                matching_product = next((p for p in selected_products if p['name'] == product_name), None)
                
                if matching_product:
                    checkbox.setChecked(True)
                    
                    # Restaurer la quantité si on a un spinbox correspondant
                    if i < len(self.product_quantity_spinboxes):
                        quantity = matching_product.get('quantity', 1)
                        self.product_quantity_spinboxes[i].setValue(int(quantity))
    
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
            'status': self.status_combo.currentText() if self.is_edit_mode else 'En attente',
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
                'event_date': reservation_data['event_datetime'],  # Date et heure de l'événement
                'type': reservation_data['event_type'],  # Type d'événement (attention au nom !)
                'guests': reservation_data['guests'],  # Nombre d'invités
                'status': reservation_data['status'],  # Statut
                'notes': reservation_data['notes'],  # Notes
                'discount': reservation_data['discount'],  # Remise
                'tax_rate': reservation_data['tax_rate'],  # Taux de TVA
                'tax_amount': reservation_data['tax_amount'],  # Montant de TVA
                'total': reservation_data['total'],  # Total
                'total_services': 0,  # Sera calculé dans le contrôleur
                'total_products': 0   # Sera calculé dans le contrôleur
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
            for i, checkbox in enumerate(self.product_checkboxes):
                if checkbox.isChecked():
                    product_data = checkbox.product_data
                    if hasattr(product_data, 'id'):  # Objet réel de la DB
                        # Récupérer la quantité du spinbox correspondant
                        quantity = self.product_quantity_spinboxes[i].value() if i < len(self.product_quantity_spinboxes) else 1
                        products_data.append({
                            'product_id': product_data.id,
                            'quantity': quantity,
                            'unit_price': float(product_data.price_unit)
                        })
            
            if self.is_edit_mode:
                # Modification d'une réservation existante
                controller_data['id'] = self.reservation_data.get('id')
                # Ajouter les services et produits aux données du contrôleur
                controller_data['services'] = services_data
                controller_data['products'] = products_data
                
                updated_reservation = self.reservation_controller.update_reservation(
                    controller_data['id'], 
                    controller_data
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
