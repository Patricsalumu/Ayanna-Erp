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
from ayanna_erp.core.entreprise_controller import EntrepriseController


class ServiceIndex(QWidget):
    """Onglet pour la gestion des services"""
    
    def __init__(self, main_controller, current_user):
        super().__init__()
        self.main_controller = main_controller
        self.current_user = current_user
        
        # Initialiser le contrôleur service
        self.service_controller = ServiceController(pos_id=getattr(main_controller, 'pos_id', 1))
        
        # Initialiser le contrôleur entreprise pour les devises
        self.entreprise_controller = EntrepriseController()
        
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
    
    def get_currency_symbol(self):
        """Récupère le symbole de devise depuis l'entreprise"""
        try:
            return self.entreprise_controller.get_currency_symbol()
        except:
            return "$"  # Fallback
    
    def format_amount(self, amount):
        """Formate un montant avec la devise de l'entreprise"""
        try:
            return self.entreprise_controller.format_amount(amount)
        except:
            return f"{amount:.2f} $"  # Fallback
    
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
        self.services_table.setColumnCount(7)
        self.services_table.setHorizontalHeaderLabels([
            "ID", "Nom du service", "Cout", "Prix ", "Marge", "Compte", "Statut"
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
        self.total_revenue_label = QLabel(f"0.00 {self.get_currency_symbol()}")
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
    
    def on_service_selected(self):
        """Gérer la sélection d'un service"""
        current_row = self.services_table.currentRow()
        if current_row >= 0 and current_row < len(self.services_data):
            # Récupérer le service depuis les données chargées
            service = self.services_data[current_row]
            self.selected_service = service
            
            # Mettre à jour les détails du service
            self.service_name_label.setText(service.name)
            self.service_category_label.setText(getattr(service, 'category', 'Non spécifiée'))
            self.service_price_label.setText(self.format_amount(service.price))
            self.service_unit_label.setText(getattr(service, 'unit', 'Service'))
            self.service_status_label.setText("Actif" if service.is_active else "Inactif")
            self.service_description_label.setText(service.description or "Aucune description")
            
            # Charger les statistiques d'utilisation réelles
            self.load_service_statistics(service.id)
            
            # Charger les dernières utilisations réelles
            self.load_recent_usage(service.id)
    
    def load_service_statistics(self, service_id):
        """Charger les statistiques d'utilisation d'un service"""
        try:
            # Récupérer les statistiques depuis le contrôleur
            stats = self.service_controller.get_service_usage_statistics(service_id)
            
            if stats:
                # Mettre à jour les labels avec les vraies données
                self.times_used_label.setText(str(stats['total_uses']))
                self.total_revenue_label.setText(self.format_amount(stats['total_revenue']))
                
                # Formatage de la dernière utilisation
                if stats['last_used']:
                    last_used = stats['last_used']
                    if hasattr(last_used, 'strftime'):
                        self.last_used_label.setText(last_used.strftime("%d/%m/%Y"))
                    else:
                        self.last_used_label.setText(str(last_used))
                else:
                    self.last_used_label.setText("Jamais utilisé")
                
                # Quantité moyenne
                if stats['average_quantity'] > 0:
                    self.avg_quantity_label.setText(f"{stats['average_quantity']:.1f}")
                else:
                    self.avg_quantity_label.setText("0")
            else:
                # Aucune statistique disponible
                self.times_used_label.setText("0")
                self.total_revenue_label.setText(f"0.00 {self.get_currency_symbol()}")
                self.last_used_label.setText("Jamais utilisé")
                self.avg_quantity_label.setText("0")
                
        except Exception as e:
            print(f"❌ Erreur lors du chargement des statistiques: {str(e)}")
            # Valeurs par défaut en cas d'erreur
            self.times_used_label.setText("Erreur")
            self.total_revenue_label.setText("Erreur")
            self.last_used_label.setText("Erreur")
            self.avg_quantity_label.setText("Erreur")
    
    def load_recent_usage(self, service_id):
        """Charger les dernières utilisations d'un service"""
        try:
            # Vider la liste actuelle
            self.recent_usage_list.clear()
            
            # Récupérer les dernières utilisations depuis le contrôleur
            recent_usage = self.service_controller.get_service_recent_usage(service_id, limit=10)
            
            if recent_usage and len(recent_usage) > 0:
                for usage in recent_usage:
                    # Formatage de la date
                    event_date = usage['event_date']
                    if hasattr(event_date, 'strftime'):
                        date_str = event_date.strftime("%d/%m/%Y")
                    else:
                        date_str = str(event_date)
                    
                    # Formatage de l'élément de liste
                    client_name = usage['client_name'] or "Client non spécifié"
                    quantity = usage['quantity']
                    total_line = usage['total_line']
                    
                    usage_text = f"{date_str} - {client_name} - Qté: {quantity} - {self.format_amount(total_line)}"
                    self.recent_usage_list.addItem(usage_text)
            else:
                # Aucune utilisation trouvée
                self.recent_usage_list.addItem("Aucune utilisation enregistrée")
                
        except Exception as e:
            print(f"❌ Erreur lors du chargement des dernières utilisations: {str(e)}")
            self.recent_usage_list.clear()
            self.recent_usage_list.addItem("Erreur lors du chargement")
    
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
            self.services_table.setItem(row, 0, QTableWidgetItem(str(service.id)))
            
            # Nom
            self.services_table.setItem(row, 1, QTableWidgetItem(service.name or ''))
            
            # Coût
            cost = float(service.cost or 0)
            self.services_table.setItem(row, 2, QTableWidgetItem(self.format_amount(cost)))
            
            # Prix
            price = float(service.price or 0)
            self.services_table.setItem(row, 3, QTableWidgetItem(self.format_amount(price)))
            
            # Marge
            margin = price - cost
            margin_item = QTableWidgetItem(self.format_amount(margin))
            if margin < 0:
                margin_item.setBackground(Qt.GlobalColor.red)
            elif margin > 0:
                margin_item.setBackground(Qt.GlobalColor.green)
            self.services_table.setItem(row, 4, margin_item)
            
            # Compte comptable
            account_text = "Non défini"
            if hasattr(service, 'account_id') and service.account_id:
                try:
                    # Importer ici pour éviter les imports circulaires
                    from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ComptabiliteController
                    comptabilite_controller = ComptabiliteController()
                    compte = comptabilite_controller.get_compte_by_id(service.account_id)
                    if compte:
                        account_text = f"{compte.numero} - {compte.nom}"
                except Exception as e:
                    print(f"Erreur lors de la récupération du compte: {e}")
                    account_text = "Erreur"
            self.services_table.setItem(row, 5, QTableWidgetItem(account_text))
            
            # Statut
            status = "Actif" if service.is_active else "Inactif"
            status_item = QTableWidgetItem(status)
            if not service.is_active:
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
                if service.id == service_id:
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
        active_services = sum(1 for s in self.services_data if s.is_active)
        
        # Calcul des totaux financiers
        total_cost = sum(float(s.cost or 0) for s in self.services_data)
        total_price = sum(float(s.price or 0) for s in self.services_data)
        total_margin = total_price - total_cost
        
        # Mise à jour des labels (si ils existent)
        if hasattr(self, 'stats_label'):
            self.stats_label.setText(
                f"Services: {active_services}/{total_services} actifs | "
                f"Marge totale: {self.format_amount(total_margin)}"
            )
