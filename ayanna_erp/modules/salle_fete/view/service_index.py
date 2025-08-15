"""
Onglet Services pour le module Salle de Fête
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
from controller.service_controller import ServiceController
from .service_form import ServiceForm


class ServiceIndex(QWidget):
    """Onglet pour la gestion des services"""
    
    def __init__(self, main_controller, current_user):
        super().__init__()
        self.main_controller = main_controller
        self.current_user = current_user
        
        # Initialiser le contrôleur service
        self.service_controller = ServiceController(pos_id=getattr(main_controller, 'pos_id', 1))
        
        # Connecter les signaux du contrôleur
        self.service_controller.services_loaded.connect(self.on_services_loaded)
        self.service_controller.service_added.connect(self.on_service_added)
        self.service_controller.service_updated.connect(self.on_service_updated)
        self.service_controller.service_deleted.connect(self.on_service_deleted)
        self.service_controller.error_occurred.connect(self.on_error_occurred)
        
        self.selected_service = None
        self.services_data = []
        
        self.setup_ui()
        self.connect_signals()
        
        # Charger les services après initialisation
        QTimer.singleShot(100, self.load_services)
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # Barre d'outils
        toolbar_layout = QHBoxLayout()
        
        # Boutons d'action
        self.add_service_button = QPushButton("➕ Nouveau service")
        self.add_service_button.setStyleSheet("""
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
        
        self.edit_service_button = QPushButton("✏️ Modifier")
        self.edit_service_button.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        
        self.delete_service_button = QPushButton("🗑️ Supprimer")
        self.delete_service_button.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        
        # Barre de recherche et filtres
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Rechercher un service...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498DB;
            }
        """)
        
        # Filtre par catégorie
        self.category_filter = QComboBox()
        self.category_filter.addItems(["Toutes catégories", "Décoration", "Musique", "Restauration", "Animation", "Autre"])
        self.category_filter.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: white;
            }
        """)
        
        toolbar_layout.addWidget(self.add_service_button)
        toolbar_layout.addWidget(self.edit_service_button)
        toolbar_layout.addWidget(self.delete_service_button)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(QLabel("Catégorie:"))
        toolbar_layout.addWidget(self.category_filter)
        toolbar_layout.addWidget(self.search_input)
        
        # Splitter pour diviser en deux parties
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Table des services (côté gauche)
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(6)
        self.services_table.setHorizontalHeaderLabels([
            "ID", "Nom du service", "Catégorie", "Prix unitaire", "Unité", "Statut"
        ])
        
        # Configuration du tableau
        self.services_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.services_table.setAlternatingRowColors(True)
        self.services_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: white;
                gridline-color: #ECF0F1;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #E74C3C;
                color: white;
            }
            QHeaderView::section {
                background-color: #34495E;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        
        # Redimensionnement automatique des colonnes
        header = self.services_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Nom du service
        
        # Zone de détails du service (côté droit)
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        # Informations du service
        service_info_group = QGroupBox("Détails du service")
        service_info_layout = QFormLayout(service_info_group)
        
        self.service_name_label = QLabel("-")
        self.service_category_label = QLabel("-")
        self.service_price_label = QLabel("-")
        self.service_unit_label = QLabel("-")
        self.service_status_label = QLabel("-")
        self.service_description_label = QLabel("-")
        self.service_description_label.setWordWrap(True)
        
        service_info_layout.addRow("Nom:", self.service_name_label)
        service_info_layout.addRow("Catégorie:", self.service_category_label)
        service_info_layout.addRow("Prix unitaire:", self.service_price_label)
        service_info_layout.addRow("Unité:", self.service_unit_label)
        service_info_layout.addRow("Statut:", self.service_status_label)
        service_info_layout.addRow("Description:", self.service_description_label)
        
        # Statistiques d'utilisation
        usage_stats_group = QGroupBox("Statistiques d'utilisation")
        usage_stats_layout = QFormLayout(usage_stats_group)
        
        self.times_used_label = QLabel("0")
        self.total_revenue_label = QLabel("0.00 €")
        self.last_used_label = QLabel("-")
        self.avg_quantity_label = QLabel("-")
        
        usage_stats_layout.addRow("Fois utilisé:", self.times_used_label)
        usage_stats_layout.addRow("Revenus générés:", self.total_revenue_label)
        usage_stats_layout.addRow("Dernière utilisation:", self.last_used_label)
        usage_stats_layout.addRow("Quantité moyenne:", self.avg_quantity_label)
        
        # Dernières utilisations
        recent_usage_group = QGroupBox("Dernières utilisations")
        recent_usage_layout = QVBoxLayout(recent_usage_group)
        
        self.recent_usage_list = QListWidget()
        self.recent_usage_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ECF0F1;
            }
            QListWidget::item:selected {
                background-color: #3498DB;
                color: white;
            }
        """)
        
        recent_usage_layout.addWidget(self.recent_usage_list)
        
        # Assemblage du layout des détails
        details_layout.addWidget(service_info_group)
        details_layout.addWidget(usage_stats_group)
        details_layout.addWidget(recent_usage_group)
        details_layout.addStretch()
        
        # Ajout au splitter
        splitter.addWidget(self.services_table)
        splitter.addWidget(details_widget)
        splitter.setSizes([600, 400])
        
        # Assemblage du layout principal
        layout.addLayout(toolbar_layout)
        layout.addWidget(splitter)
        
        # Chargement des données
        self.load_services()
        
        # Connexion des signaux
        self.services_table.itemSelectionChanged.connect(self.on_service_selected)
        self.search_input.textChanged.connect(self.filter_services)
        self.category_filter.currentTextChanged.connect(self.filter_services)
    
    def load_services(self):
        """Charger les services depuis la base de données"""
        # TODO: Implémenter le chargement depuis la base de données
        # Pour l'instant, on utilise des données de test
        sample_data = [
            ["001", "Décoration florale premium", "Décoration", "250.00 €", "forfait", "Actif"],
            ["002", "DJ avec équipement son", "Musique", "400.00 €", "soirée", "Actif"],
            ["003", "Buffet traditionnel", "Restauration", "25.00 €", "personne", "Actif"],
            ["004", "Animation enfants", "Animation", "150.00 €", "heure", "Actif"],
            ["005", "Photobooth", "Animation", "200.00 €", "soirée", "Inactif"],
            ["006", "Service de nettoyage", "Autre", "100.00 €", "forfait", "Actif"],
        ]
        
        self.services_table.setRowCount(len(sample_data))
        
        for row, data in enumerate(sample_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                
                # Couleur selon le statut
                if col == 5:  # Colonne statut
                    if value == "Actif":
                        item.setBackground(Qt.GlobalColor.green)
                        item.setForeground(Qt.GlobalColor.white)
                    else:
                        item.setBackground(Qt.GlobalColor.red)
                        item.setForeground(Qt.GlobalColor.white)
                
                self.services_table.setItem(row, col, item)
    
    def on_service_selected(self):
        """Gérer la sélection d'un service"""
        current_row = self.services_table.currentRow()
        if current_row >= 0:
            # Récupérer les informations du service sélectionné
            service_id = self.services_table.item(current_row, 0).text()
            nom = self.services_table.item(current_row, 1).text()
            categorie = self.services_table.item(current_row, 2).text()
            prix = self.services_table.item(current_row, 3).text()
            unite = self.services_table.item(current_row, 4).text()
            statut = self.services_table.item(current_row, 5).text()
            
            # Mettre à jour les détails
            self.service_name_label.setText(nom)
            self.service_category_label.setText(categorie)
            self.service_price_label.setText(prix)
            self.service_unit_label.setText(unite)
            self.service_status_label.setText(statut)
            
            # Description d'exemple selon le service
            descriptions = {
                "Décoration florale premium": "Décoration complète avec fleurs fraîches, compositions centrales et décoration de la salle",
                "DJ avec équipement son": "DJ professionnel avec système son complet, éclairage et musique adaptée",
                "Buffet traditionnel": "Buffet avec entrées, plats principaux, desserts et boissons",
                "Animation enfants": "Animateur professionnel avec jeux et activités adaptés aux enfants",
                "Photobooth": "Borne photo avec accessoires et impression instantanée",
                "Service de nettoyage": "Nettoyage complet de la salle après l'événement"
            }
            
            self.service_description_label.setText(descriptions.get(nom, "Description non disponible"))
            
            # Mettre à jour les statistiques (données d'exemple)
            self.times_used_label.setText("15")
            self.total_revenue_label.setText("3,750.00 €")
            self.last_used_label.setText("2025-08-12")
            self.avg_quantity_label.setText("1.2")
            
            # Charger les dernières utilisations
            self.load_recent_usage(service_id)
    
    def load_recent_usage(self, service_id):
        """Charger les dernières utilisations d'un service"""
        # TODO: Implémenter le chargement depuis la base de données
        # Pour l'instant, on utilise des données de test
        self.recent_usage_list.clear()
        
        sample_usage = [
            "2025-08-12 - Mariage Dupont - Qté: 1 - 250.00 €",
            "2025-08-08 - Anniversaire Martin - Qté: 1 - 250.00 €",
            "2025-08-05 - Baptême Moreau - Qté: 1 - 250.00 €",
            "2025-08-01 - Réunion ABC Corp - Qté: 2 - 500.00 €",
        ]
        
        for usage in sample_usage:
            self.recent_usage_list.addItem(usage)
    
    def filter_services(self):
        """Filtrer les services selon les critères"""
        search_text = self.search_input.text().lower()
        category_filter = self.category_filter.currentText()
        
        for row in range(self.services_table.rowCount()):
            show_row = True
            
            # Filtre par texte de recherche
            if search_text:
                nom = self.services_table.item(row, 1).text().lower()
                categorie = self.services_table.item(row, 2).text().lower()
                if search_text not in nom and search_text not in categorie:
                    show_row = False
            
            # Filtre par catégorie
            if category_filter != "Toutes catégories":
                categorie = self.services_table.item(row, 2).text()
                if categorie != category_filter:
                    show_row = False
            
            self.services_table.setRowHidden(row, not show_row)
    
    # === MÉTHODES DE CONNEXION AUX CONTRÔLEURS ===
    
    def connect_signals(self):
        """Connecter les signaux des widgets aux méthodes"""
        # Boutons d'action
        self.add_service_button.clicked.connect(self.show_add_service_form)
        self.edit_service_button.clicked.connect(self.show_edit_service_form)
        self.delete_service_button.clicked.connect(self.delete_selected_service)
        
        # Table des services
        self.services_table.itemSelectionChanged.connect(self.on_service_selection_changed)
        self.services_table.itemDoubleClicked.connect(self.show_edit_service_form)
        
        # Filtres
        self.search_input.textChanged.connect(self.filter_services)
        self.category_filter.currentTextChanged.connect(self.filter_services)
    
    def load_services(self):
        """Charger la liste des services depuis le contrôleur"""
        try:
            self.service_controller.load_services()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des services: {str(e)}")
    
    def on_services_loaded(self, services):
        """Callback quand les services sont chargés"""
        self.services_data = services
        self.populate_services_table()
        self.update_statistics()
    
    def on_service_added(self, service):
        """Callback quand un service est ajouté"""
        self.load_services()  # Recharger la liste
        QMessageBox.information(self, "Succès", "Service ajouté avec succès !")
    
    def on_service_updated(self, service):
        """Callback quand un service est modifié"""
        self.load_services()  # Recharger la liste
        QMessageBox.information(self, "Succès", "Service modifié avec succès !")
    
    def on_service_deleted(self, service_id):
        """Callback quand un service est supprimé"""
        self.load_services()  # Recharger la liste
        QMessageBox.information(self, "Succès", "Service supprimé avec succès !")
    
    def on_error_occurred(self, error_message):
        """Callback quand une erreur survient"""
        QMessageBox.critical(self, "Erreur", error_message)
    
    def populate_services_table(self):
        """Remplir le tableau des services avec les données"""
        self.services_table.setRowCount(len(self.services_data))
        
        for row, service in enumerate(self.services_data):
            # ID (caché)
            self.services_table.setItem(row, 0, QTableWidgetItem(str(service.get('id', ''))))
            
            # Nom
            self.services_table.setItem(row, 1, QTableWidgetItem(service.get('name', '')))
            
            # Catégorie
            category = service.get('category', '')
            self.services_table.setItem(row, 2, QTableWidgetItem(category))
            
            # Coût
            cost = float(service.get('cost', 0))
            self.services_table.setItem(row, 3, QTableWidgetItem(f"{cost:.2f} €"))
            
            # Prix
            price = float(service.get('price', 0))
            self.services_table.setItem(row, 4, QTableWidgetItem(f"{price:.2f} €"))
            
            # Marge
            margin = price - cost
            margin_item = QTableWidgetItem(f"{margin:.2f} €")
            if margin < 0:
                margin_item.setBackground(Qt.GlobalColor.red)
            elif margin > 0:
                margin_item.setBackground(Qt.GlobalColor.green)
            self.services_table.setItem(row, 5, margin_item)
            
            # Statut
            status = "Actif" if service.get('is_active', True) else "Inactif"
            status_item = QTableWidgetItem(status)
            if not service.get('is_active', True):
                status_item.setBackground(Qt.GlobalColor.lightGray)
            self.services_table.setItem(row, 6, status_item)
        
        # Cacher la colonne ID
        self.services_table.hideColumn(0)
    
    def on_service_selection_changed(self):
        """Gestion de la sélection d'un service"""
        selected_rows = self.services_table.selectionModel().selectedRows()
        
        if selected_rows:
            row = selected_rows[0].row()
            service_id = int(self.services_table.item(row, 0).text())
            
            # Trouver le service sélectionné dans les données
            self.selected_service = None
            for service in self.services_data:
                if service.get('id') == service_id:
                    self.selected_service = service
                    break
            
            # Activer les boutons
            self.edit_service_button.setEnabled(True)
            self.delete_service_button.setEnabled(True)
        else:
            self.selected_service = None
            self.edit_service_button.setEnabled(False)
            self.delete_service_button.setEnabled(False)
    
    def show_add_service_form(self):
        """Afficher le formulaire d'ajout de service"""
        form = ServiceForm(self, controller=self.service_controller)
        form.service_saved.connect(self.on_service_form_saved)
        form.exec()
    
    def show_edit_service_form(self):
        """Afficher le formulaire de modification de service"""
        if not self.selected_service:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un service à modifier.")
            return
        
        form = ServiceForm(self, service_data=self.selected_service, controller=self.service_controller)
        form.service_saved.connect(self.on_service_form_saved)
        form.exec()
    
    def delete_selected_service(self):
        """Supprimer le service sélectionné"""
        if not self.selected_service:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un service à supprimer.")
            return
        
        # Confirmation
        reply = QMessageBox.question(
            self, 
            "Confirmation", 
            f"Êtes-vous sûr de vouloir supprimer le service '{self.selected_service.get('name', '')}'?\n\n"
            "Cette action est irréversible.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.service_controller.delete_service(self.selected_service.get('id'))
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression: {str(e)}")
    
    def on_service_form_saved(self, service_data):
        """Callback quand un service est sauvegardé depuis le formulaire"""
        # Le contrôleur gère déjà les callbacks, pas besoin d'action ici
        pass
    
    def update_statistics(self):
        """Mettre à jour les statistiques des services"""
        if not hasattr(self, 'services_data'):
            return
        
        total_services = len(self.services_data)
        active_services = sum(1 for s in self.services_data if s.get('is_active', True))
        
        # Calcul des totaux financiers
        total_cost = sum(float(s.get('cost', 0)) for s in self.services_data)
        total_price = sum(float(s.get('price', 0)) for s in self.services_data)
        total_margin = total_price - total_cost
        
        # Mise à jour des labels (si ils existent)
        if hasattr(self, 'stats_label'):
            self.stats_label.setText(
                f"Services: {active_services}/{total_services} actifs | "
                f"Marge totale: {total_margin:.2f} €"
            )
