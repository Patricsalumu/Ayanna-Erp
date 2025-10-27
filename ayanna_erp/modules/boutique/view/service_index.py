"""
Onglet Services pour le module Boutique
Gestion et affichage des services via contrôleur MVC
"""

import sys
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QTableWidget, QTableWidgetItem, 
                            QPushButton, QLineEdit, QLabel, QComboBox, 
                            QSpinBox, QDoubleSpinBox, QTextEdit, QMessageBox,
                            QGroupBox, QGridLayout, QListWidget, QSplitter,
                            QFrame, QScrollArea, QFormLayout, QCheckBox,
                            QDateTimeEdit, QHeaderView)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDateTime
from PyQt6.QtGui import QFont, QPixmap, QIcon
from decimal import Decimal
from datetime import datetime, timedelta

# Import du contrôleur service et du formulaire modal
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ..controller.service_controller import ServiceController
from .service_form import ServiceForm
from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController


class ServiceIndex(QWidget):
    """Onglet pour la gestion des services"""
    
    def __init__(self, main_controller, current_user, user_controller=None):
        super().__init__()
        self.main_controller = main_controller
        self.current_user = current_user
        self.user_controller = user_controller
        
        # Initialiser le contrôleur service
        self.service_controller = ServiceController(pos_id=getattr(main_controller, 'pos_id', 1))
        
        # Initialiser le contrôleur entreprise pour les devises
        self.entreprise_controller = EntrepriseController()
        
        # Méthode pour obtenir le symbole de devise
        def get_currency_symbol(self):
            try:
                return self.entreprise_controller.get_currency_symbol()
            except Exception:
                return "FC"  # Fallback
        
        # Connecter les signaux du contrôleur
        self.service_controller.services_loaded.connect(self.on_services_loaded)
        self.service_controller.service_added.connect(self.on_service_added)
        self.service_controller.service_updated.connect(self.on_service_updated)
        self.service_controller.service_deleted.connect(self.on_service_deleted)
        self.service_controller.error_occurred.connect(self.on_error_occurred)
        
        self.selected_service = None
        self.services_data = []
        
        self.setup_ui()
        
        # Charger les services après l'initialisation
        QTimer.singleShot(100, self.load_services)
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        # Layout principal horizontal avec splitter
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Splitter pour diviser l'interface
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # === PARTIE GAUCHE : LISTE SERVICES ===
        left_frame = QFrame()
        left_frame.setMaximumWidth(350)
        left_frame.setMinimumWidth(300)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # En-tête services
        services_header = QGroupBox("🔧 Gestion des Services")
        services_header_layout = QVBoxLayout(services_header)

        # Barre d'outils services
        services_toolbar = QHBoxLayout()
        self.new_service_btn = QPushButton("➕ Nouveau")
        self.new_service_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #219A52;
            }
        """)
        self.new_service_btn.clicked.connect(self.create_new_service)
        services_toolbar.addWidget(self.new_service_btn)

        self.edit_service_btn = QPushButton("✏️ Modifier")
        self.edit_service_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        self.edit_service_btn.clicked.connect(self.edit_selected_service)
        self.edit_service_btn.setEnabled(False)
        services_toolbar.addWidget(self.edit_service_btn)

        self.delete_service_btn = QPushButton("🗑️ Supprimer")
        self.delete_service_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        self.delete_service_btn.clicked.connect(self.delete_selected_service)
        self.delete_service_btn.setEnabled(False)
        services_toolbar.addWidget(self.delete_service_btn)

        services_toolbar.addStretch()
        services_header_layout.addLayout(services_toolbar)

        # Recherche services
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Recherche:"))
        self.search_service_input = QLineEdit()
        self.search_service_input.setPlaceholderText("Nom du service...")
        self.search_service_input.textChanged.connect(self.filter_services)
        search_layout.addWidget(self.search_service_input)
        services_header_layout.addLayout(search_layout)

        left_layout.addWidget(services_header)

        # Liste des services
        self.services_list = QListWidget()
        self.services_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                background-color: white;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ECF0F1;
            }
            QListWidget::item:selected {
                background-color: #3498DB;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #EBF5FF;
            }
        """)
        self.services_list.itemClicked.connect(self.on_service_selected)
        left_layout.addWidget(self.services_list)

        splitter.addWidget(left_frame)

        # === PARTIE DROITE : DÉTAILS ET STATISTIQUES ===
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Statistiques
        stats_group = QGroupBox("📊 Statistiques Services")
        stats_layout = QGridLayout(stats_group)

        self.total_services_label = QLabel("Total: 0 services")
        self.total_services_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.total_services_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.total_services_label.setStyleSheet("""
            QLabel {
                border: 2px solid #3498DB;
                border-radius: 8px;
                background-color: #EBF5FF;
                padding: 10px;
                color: #2C3E50;
            }
        """)
        stats_layout.addWidget(self.total_services_label, 0, 0)

        self.active_services_label = QLabel("Actifs: 0")
        self.active_services_label.setFont(QFont("Arial", 9))
        self.active_services_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.active_services_label.setStyleSheet("""
            QLabel {
                border: 1px solid #27AE60;
                border-radius: 5px;
                background-color: #E8F5E8;
                padding: 8px;
                color: #27AE60;
            }
        """)
        stats_layout.addWidget(self.active_services_label, 0, 1)

        self.avg_price_label = QLabel(f"Prix moyen: 0 {self.get_currency_symbol()}")
        self.avg_price_label.setFont(QFont("Arial", 9))
        self.avg_price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avg_price_label.setStyleSheet("""
            QLabel {
                border: 1px solid #F39C12;
                border-radius: 5px;
                background-color: #FEF9E7;
                padding: 8px;
                color: #F39C12;
            }
        """)
        stats_layout.addWidget(self.avg_price_label, 1, 0, 1, 2)

        right_layout.addWidget(stats_group)

        # Détails du service sélectionné
        details_group = QGroupBox("🔍 Détails du Service")
        self.details_layout = QVBoxLayout(details_group)

        self.service_details_label = QLabel("Sélectionnez un service pour voir les détails.")
        self.service_details_label.setWordWrap(True)
        self.service_details_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.service_details_label.setStyleSheet("""
            QLabel {
                color: #7F8C8D;
                font-style: italic;
                padding: 20px;
            }
        """)
        self.details_layout.addWidget(self.service_details_label)

        right_layout.addWidget(details_group)
        right_layout.addStretch()

        splitter.addWidget(right_frame)

        # Proportions du splitter
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

    def load_services(self):
        """Charger les services"""
        try:
            self.service_controller.load_services()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des services: {str(e)}")

    def on_services_loaded(self, services):
        """Callback quand les services sont chargés"""
        self.services_data = services
        self.populate_services_list()
        self.update_statistics()

    def populate_services_list(self):
        """Peupler la liste des services"""
        self.services_list.clear()
        
        search_text = self.search_service_input.text().lower()
        
        for service in self.services_data:
            # Compatibilité dict et objet
            if isinstance(service, dict):
                name = service.get('nom', service.get('name', 'N/A'))
                price = service.get('prix', service.get('price', 0))
                active = service.get('actif', service.get('is_active', True))
            else:
                name = getattr(service, 'nom', getattr(service, 'name', 'N/A'))
                price = getattr(service, 'prix', getattr(service, 'price', 0))
                active = getattr(service, 'actif', getattr(service, 'is_active', True))
            
            # Filtrage
            if search_text and search_text not in name.lower():
                continue
            
            # Format d'affichage
            status_icon = "✅" if active else "❌"
            item_text = f"{status_icon} {name} - {price} {self.get_currency_symbol()}"
            
            item = QTableWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, service)
            self.services_list.addItem(item)

    def filter_services(self):
        """Filtrer les services selon la recherche"""
        self.populate_services_list()

    def update_statistics(self):
        """Mettre à jour les statistiques"""
        total_services = len(self.services_data)
        active_count = 0
        total_price = 0
        
        for service in self.services_data:
            # Compatibilité dict et objet
            if isinstance(service, dict):
                active = service.get('actif', service.get('is_active', True))
                price = service.get('prix', service.get('price', 0))
            else:
                active = getattr(service, 'actif', getattr(service, 'is_active', True))
                price = getattr(service, 'prix', getattr(service, 'price', 0))
            
            if active:
                active_count += 1
            total_price += float(price or 0)
        
        avg_price = total_price / total_services if total_services > 0 else 0
        
        self.total_services_label.setText(f"Total: {total_services} services")
        self.active_services_label.setText(f"Actifs: {active_count}")
        self.avg_price_label.setText(f"Prix moyen: {avg_price:.0f} {self.get_currency_symbol()}")

    def on_service_selected(self, item):
        """Gestionnaire de sélection de service"""
        service = item.data(Qt.ItemDataRole.UserRole)
        if service:
            self.selected_service = service
            self.show_service_details()
            self.edit_service_btn.setEnabled(True)
            self.delete_service_btn.setEnabled(True)

    def show_service_details(self):
        """Afficher les détails du service sélectionné"""
        if not self.selected_service:
            return
        
        service = self.selected_service
        
        # Compatibilité dict et objet
        if isinstance(service, dict):
            name = service.get('nom', service.get('name', 'N/A'))
            description = service.get('description', 'Aucune description')
            price = service.get('prix', service.get('price', 0))
            active = service.get('actif', service.get('is_active', True))
            category = service.get('categorie', service.get('category', 'Aucune'))
        else:
            name = getattr(service, 'nom', getattr(service, 'name', 'N/A'))
            description = getattr(service, 'description', 'Aucune description')
            price = getattr(service, 'prix', getattr(service, 'price', 0))
            active = getattr(service, 'actif', getattr(service, 'is_active', True))
            category = getattr(service, 'categorie', getattr(service, 'category', 'Aucune'))
        
        details = f"""
        <h3 style='color: #2C3E50;'>{name}</h3>
        <p><b>Prix:</b> {price} {self.get_currency_symbol()}</p>
        <p><b>Catégorie:</b> {category}</p>
        <p><b>Statut:</b> {'Actif' if active else 'Inactif'}</p>
        <p><b>Description:</b></p>
        <p style='font-style: italic; margin-left: 10px;'>{description}</p>
        """
        
        self.service_details_label.setText(details)

    def create_new_service(self):
        """Créer un nouveau service"""
        try:
            form = ServiceForm(self)
            if form.exec():
                service_data = form.get_service_data()
                self.service_controller.create_service(service_data)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la création du service: {str(e)}")

    def edit_selected_service(self):
        """Modifier le service sélectionné"""
        if not self.selected_service:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un service à modifier.")
            return
        
        try:
            form = ServiceForm(self, self.selected_service)
            if form.exec():
                service_data = form.get_service_data()
                service_id = self.selected_service.get('id') if isinstance(self.selected_service, dict) else getattr(self.selected_service, 'id')
                self.service_controller.update_service(service_id, service_data)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la modification du service: {str(e)}")

    def delete_selected_service(self):
        """Supprimer le service sélectionné"""
        if not self.selected_service:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un service à supprimer.")
            return
        
        service_name = self.selected_service.get('nom') if isinstance(self.selected_service, dict) else getattr(self.selected_service, 'nom', 'ce service')
        
        reply = QMessageBox.question(
            self, "Confirmation", 
            f"Êtes-vous sûr de vouloir supprimer le service '{service_name}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                service_id = self.selected_service.get('id') if isinstance(self.selected_service, dict) else getattr(self.selected_service, 'id')
                self.service_controller.delete_service(service_id)
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression du service: {str(e)}")

    # Callbacks du contrôleur
    def on_service_added(self, service):
        """Callback service ajouté"""
        QMessageBox.information(self, "Succès", "Service créé avec succès!")
        self.load_services()

    def on_service_updated(self, service):
        """Callback service modifié"""
        QMessageBox.information(self, "Succès", "Service modifié avec succès!")
        self.load_services()

    def on_service_deleted(self, service_id):
        """Callback service supprimé"""
        QMessageBox.information(self, "Succès", "Service supprimé avec succès!")
        self.selected_service = None
        self.edit_service_btn.setEnabled(False)
        self.delete_service_btn.setEnabled(False)
        self.service_details_label.setText("Sélectionnez un service pour voir les détails.")
        self.load_services()

    def on_error_occurred(self, error_message):
        """Callback erreur"""
        QMessageBox.critical(self, "Erreur", error_message)