"""
Onglet Réservations pour le module Salle de Fête
Gestion et affichage des réservations via contrôleur MVC
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

# Import du contrôleur réservation et du formulaire modal
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from controller.reservation_controller import ReservationController
from .reservation_form import ReservationForm
from ....database.database_manager import get_database_manager
from ayanna_erp.core.entreprise_controller import EntrepriseController


class ReservationIndex(QWidget):
    """Onglet pour la gestion des réservations"""
    
    def __init__(self, main_controller, current_user):
        super().__init__()
        self.main_controller = main_controller
        self.current_user = current_user
        
        # Initialiser le contrôleur réservation
        self.reservation_controller = ReservationController(pos_id=getattr(main_controller, 'pos_id', 1))
        
        # Initialiser le contrôleur entreprise pour les devises
        self.entreprise_controller = EntrepriseController()
        
        # Connecter les signaux du contrôleur
        self.reservation_controller.reservations_loaded.connect(self.on_reservations_loaded)
        self.reservation_controller.reservation_added.connect(self.on_reservation_added)
        self.reservation_controller.reservation_updated.connect(self.on_reservation_updated)
        self.reservation_controller.reservation_deleted.connect(self.on_reservation_deleted)
        self.reservation_controller.error_occurred.connect(self.on_error_occurred)
        
        self.selected_reservation = None
        self.reservations_data = []
        
        self.setup_ui()
        self.connect_signals()
        
        # Charger les réservations après initialisation
        QTimer.singleShot(100, self.load_reservations)
    
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
        self.add_reservation_button = QPushButton("➕ Nouvelle réservation")
        self.add_reservation_button.setStyleSheet("""
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
        
        # Barre de recherche
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Rechercher une réservation...")
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
        
        # Filtre par statut
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Tous", "Confirmé", "En attente", "Annulé", "Terminé"])
        self.status_filter.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: white;
            }
        """)
        
        toolbar_layout.addWidget(self.add_reservation_button)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(QLabel("Statut:"))
        toolbar_layout.addWidget(self.status_filter)
        toolbar_layout.addWidget(self.search_input)
        
        # Table des réservations
        self.reservations_table = QTableWidget()
        self.reservations_table.setColumnCount(8)
        self.reservations_table.setHorizontalHeaderLabels([
            "ID", "Client", "Date événement", "Type", "Statut", 
            "Montant total", "Acompte", "Date création"
        ])
        
        # Configuration du tableau
        self.reservations_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.reservations_table.setAlternatingRowColors(True)
        self.reservations_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Désactiver l'édition directe
        self.reservations_table.setStyleSheet("""
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
                padding: 2px;
                border: none;
                font-weight: bold;
            }
        """)
        
        # Redimensionnement automatique des colonnes
        header = self.reservations_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Client
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Date
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Statut
        
        # Zone d'informations - optimisée pour l'espace
        info_group = QGroupBox("Informations sur la réservation sélectionnée")
        info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                margin-top: 1px;
                padding-top: 2px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        info_layout = QHBoxLayout(info_group)
        info_layout.setContentsMargins(4, 2, 4, 2)  # Réduire les marges
        info_layout.setSpacing(1)  # Réduire l'espacement
        
        self.reservation_details = QTextEdit()
        self.reservation_details.setReadOnly(True)
        self.reservation_details.setMaximumHeight(250)  # Réduire de 120 à 200
        self.reservation_details.setStyleSheet("""
            QTextEdit {
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: #F8F9FA;
                padding: 5px;
                font-size: 13px;
                line-height: 1.2;
            }
        """)
        
        info_layout.addWidget(self.reservation_details)
        
        # Assemblage du layout avec espacements réduits
        layout.setSpacing(8)  # Réduire l'espacement général
        layout.addLayout(toolbar_layout)
        layout.addWidget(self.reservations_table)
        layout.addWidget(info_group)
        
        # Chargement des données
        self.load_reservations()
        
        # Connexion des signaux
        self.reservations_table.itemSelectionChanged.connect(self.on_reservation_selected)
        self.search_input.textChanged.connect(self.filter_reservations)
        self.status_filter.currentTextChanged.connect(self.filter_reservations)
        self.add_reservation_button.clicked.connect(self.add_new_reservation)
    
    def load_reservations(self):
        """Charger les réservations depuis la base de données"""
        # Utiliser le contrôleur pour charger les réservations
        self.reservation_controller.load_reservations()
    
    def on_reservation_selected(self):
        """Gérer la sélection d'une réservation avec tous les détails"""
        current_row = self.reservations_table.currentRow()
        if current_row >= 0:
            # Récupérer l'ID de la réservation
            reservation_id = int(self.reservations_table.item(current_row, 0).text())
            
            # Utiliser le contrôleur pour récupérer toutes les informations
            reservation_details = self.reservation_controller.get_reservation(reservation_id)
            
            if reservation_details:
                # Formater la date d'événement
                event_date_str = ""
                if reservation_details['event_date']:
                    if hasattr(reservation_details['event_date'], 'strftime'):
                        event_date_str = reservation_details['event_date'].strftime('%d/%m/%Y à %H:%M')
                    else:
                        event_date_str = str(reservation_details['event_date'])
                
                # Formater la date de création
                created_date_str = ""
                if reservation_details['created_at']:
                    if hasattr(reservation_details['created_at'], 'strftime'):
                        created_date_str = reservation_details['created_at'].strftime('%d/%m/%Y à %H:%M')
                    else:
                        created_date_str = str(reservation_details['created_at'])
                
                # Formater les services sélectionnés
                services_html = ""
                if reservation_details['services']:
                    services_html = "<br>".join([
                        f"• {service['name']} - Qté: {service['quantity']} - Prix: {self.format_amount(service['unit_price'])} - Total: {self.format_amount(service['line_total'])}"
                        for service in reservation_details['services']
                    ])
                else:
                    services_html = "<i>Aucun service sélectionné</i>"
                
                # Formater les produits sélectionnés
                products_html = ""
                if reservation_details['products']:
                    products_html = "<br>".join([
                        f"• {product['name']} - Qté: {product['quantity']} - Prix: {self.format_amount(product['unit_price'])} - Total: {self.format_amount(product['line_total'])}"
                        for product in reservation_details['products']
                    ])
                else:
                    products_html = "<i>Aucun produit sélectionné</i>"
                
                # Déterminer la couleur du statut
                status = reservation_details['status']
                status_color = {
                    'Confirmé': 'green',
                    'En attente': '#FF8C00',
                    'Annulé': 'red',
                    'Terminé': 'blue'
                }.get(status, 'gray')
                
                # Couleur du solde restant
                remaining = reservation_details['remaining_amount']
                remaining_color = 'green' if remaining <= 0 else '#E74C3C'
                
                # Format HTML complet et détaillé
                details = f"""
                <div style="font-family: Arial; font-size: 12px; line-height: 1.4;">
                    <h3 style="margin: 0 0 10px 0; color: #2C3E50;">📋 Réservation #{reservation_details['id']}</h3>
                    
                    <table width="100%" cellpadding="3" cellspacing="0" style="border-collapse: collapse;">
                        <tr>
                            <td width="50%"><b>👤 Client:</b> {reservation_details['client_nom']}</td>
                            <td><b>📞 Téléphone:</b> {reservation_details['client_telephone']}</td>
                        </tr>
                        <tr>
                            <td><b>🎭 Thème:</b> {reservation_details['theme']}</td>
                            <td><b>📅 Date événement:</b> {event_date_str}</td>
                        </tr>
                        <tr>
                            <td><b>🎉 Type:</b> {reservation_details['event_type']}</td>
                            <td><b>👥 Invités:</b> {reservation_details['guests_count']}</td>
                        </tr>
                        <tr>
                            <td><b>📊 Statut:</b> <span style="color: {status_color}; font-weight: bold;">{status}</span></td>
                            <td><b>📝 Créé le:</b> {created_date_str}</td>
                        </tr>
                    </table>
                    
                    <hr style="margin: 10px 0; border: 1px solid #BDC3C7;">
                    
                    <table width="100%" cellpadding="5" cellspacing="0">
                        <tr>
                            <td width="50%" valign="top">
                                <h4 style="margin: 0 0 5px 0; color: #2980B9;">🛠️ Services sélectionnés:</h4>
                                <div style="font-size: 11px;">
                                    {services_html}
                                </div>
                            </td>
                            <td width="50%" valign="top">
                                <h4 style="margin: 0 0 5px 0; color: #2980B9;">📦 Produits sélectionnés:</h4>
                                <div style="font-size: 11px;">
                                    {products_html}
                                </div>
                            </td>
                        </tr>
                    </table>
                    
                    <hr style="margin: 10px 0; border: 1px solid #BDC3C7;">
                    
                    <h4 style="margin: 5px 0; color: #E74C3C;">💰 Résumé financier:</h4>
                    <table width="100%" cellpadding="2" cellspacing="0">
                        <tr>
                            <td><b>Sous-total HT:</b> {self.format_amount(reservation_details['total_services'] + reservation_details['total_products'])}</td>
                            <td><b>TVA ({reservation_details['tax_rate']:.1f}%):</b> {self.format_amount(reservation_details['tax_amount'])}</td>
                        </tr>
                        <tr style="background-color: #F0F7FF;">
                            <td><b>Total TTC:</b> <span style="color: #2980B9; font-size: 13px;">{self.format_amount(reservation_details['total_amount'])}</span></td>
                            <td><b>Remise ({reservation_details['discount_percent']:.1f}%):</b> <span style="color: #E74C3C;">-{self.format_amount(reservation_details['total_amount'] * reservation_details['discount_percent'] / 100)}</span></td>
                        </tr>
                        <tr style="background-color: #F8F9FA;">
                            <td><b>TOTAL NET:</b> <span style="color: #E74C3C; font-size: 14px; font-weight: bold;">{self.format_amount(reservation_details['total_amount'] * (1 - reservation_details['discount_percent'] / 100))}</span></td>
                            <td><b>Payé:</b> {self.format_amount(reservation_details['total_paid'])}</td>
                        </tr>
                        <tr>
                            <td colspan="2"><b>Solde restant:</b> <span style="color: {remaining_color}; font-weight: bold; font-size: 13px;">{self.format_amount(remaining)}</span></td>
                        </tr>
                    </table>
                    
                    <h4 style="margin: 10px 0 5px 0; color: #8E44AD;">📝 Notes:</h4>
                    <div style="margin-left: 10px; font-style: italic; background-color: #F8F9FA; padding: 5px; border-radius: 3px;">
                        {reservation_details['notes'] or '<i>Aucune note</i>'}
                    </div>
                </div>
                """
                
                self.reservation_details.setHtml(details)
            else:
                self.reservation_details.setHtml("<p>Erreur lors du chargement des détails de la réservation.</p>")
        else:
            self.reservation_details.setHtml("<p>Sélectionnez une réservation pour voir les détails.</p>")
    
    def filter_reservations(self):
        """Filtrer les réservations selon les critères"""
        search_text = self.search_input.text().lower()
        status_filter = self.status_filter.currentText()
        
        for row in range(self.reservations_table.rowCount()):
            show_row = True
            
            # Filtre par texte de recherche
            if search_text:
                client = self.reservations_table.item(row, 1).text().lower()
                type_event = self.reservations_table.item(row, 3).text().lower()
                if search_text not in client and search_text not in type_event:
                    show_row = False
            
            # Filtre par statut
            if status_filter != "Tous":
                status = self.reservations_table.item(row, 4).text()
                if status != status_filter:
                    show_row = False
            
            self.reservations_table.setRowHidden(row, not show_row)
    
    def add_new_reservation(self):
        """Ouvrir le formulaire pour une nouvelle réservation"""
        from .reservation_form import ReservationForm
        from ayanna_erp.modules.salle_fete.model.salle_fete import get_database_manager
        
        # Récupérer le gestionnaire de base de données
        db_manager = get_database_manager()
        
        # Transmettre le pos_id du contrôleur principal
        pos_id = getattr(self.main_controller, 'pos_id', 1)
        
        dialog = ReservationForm(self, db_manager=db_manager, pos_id=pos_id)
        dialog.reservation_saved.connect(self.on_reservation_added)
        dialog.exec()
    
    def edit_selected_reservation(self):
        """Modifier la réservation sélectionnée"""
        current_row = self.reservations_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une réservation à modifier.")
            return
        
        # Récupérer l'ID de la réservation sélectionnée
        reservation_id = self.reservations_table.item(current_row, 0).text()
        
        # Récupérer les données complètes de la réservation depuis la base de données
        reservation_data = self.reservation_controller.get_reservation(int(reservation_id))
        
        if not reservation_data:
            QMessageBox.warning(self, "Erreur", "Impossible de récupérer les données de la réservation.")
            return
        
        from .reservation_form import ReservationForm
        
        # Transmettre le pos_id du contrôleur principal
        pos_id = getattr(self.main_controller, 'pos_id', 1)
        
        dialog = ReservationForm(self, reservation_data=reservation_data, db_manager=get_database_manager(), pos_id=pos_id)
        dialog.reservation_saved.connect(self.on_reservation_updated)
        dialog.exec()
    
    def delete_selected_reservation(self):
        """Supprimer la réservation sélectionnée"""
        current_row = self.reservations_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une réservation à supprimer.")
    
    # === MÉTHODES DE CONNEXION AUX CONTRÔLEURS ===
    
    def connect_signals(self):
        """Connecter les signaux des widgets aux méthodes"""
        # Boutons d'action
        self.add_reservation_button.clicked.connect(self.show_add_reservation_form)
        
        # Table des réservations
        self.reservations_table.itemSelectionChanged.connect(self.on_reservation_selection_changed)
        self.reservations_table.itemDoubleClicked.connect(self.show_edit_reservation_form)
    
    def load_reservations(self):
        try:
            self.reservation_controller.get_all_reservations()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des réservations: {str(e)}")
    
    def on_reservations_loaded(self, reservations):
        """Callback quand les réservations sont chargées"""
        self.reservations_data = reservations
        
        # Vérifier s'il y a des réservations
        if not reservations:
            # Aucune réservation trouvée
            self.reservations_table.setRowCount(1)
            no_data_item = QTableWidgetItem("Aucune réservation trouvée pour cette entreprise.")
            no_data_item.setBackground(Qt.GlobalColor.lightGray)
            no_data_item.setForeground(Qt.GlobalColor.black)
            self.reservations_table.setItem(0, 0, no_data_item)
            self.reservations_table.setSpan(0, 0, 1, 8)  # Fusion sur toutes les colonnes
            return
        
        # Afficher les réservations
        self.reservations_table.setRowCount(len(reservations))
        
        for row, reservation in enumerate(reservations):
            # ID de la réservation
            self.reservations_table.setItem(row, 0, QTableWidgetItem(str(reservation.id)))
            
            # Client (nom + prénom)
            client_name = reservation.get_client_name()
            self.reservations_table.setItem(row, 1, QTableWidgetItem(client_name))
            
            # Date de l'événement
            event_date = ""
            if reservation.event_date:
                event_date = reservation.event_date.strftime('%Y-%m-%d') if hasattr(reservation.event_date, 'strftime') else str(reservation.event_date)
            self.reservations_table.setItem(row, 2, QTableWidgetItem(event_date))
            
            # Type d'événement
            self.reservations_table.setItem(row, 3, QTableWidgetItem(reservation.event_type or ''))
            
            # Statut avec couleur
            status = reservation.status or ''
            status_item = QTableWidgetItem(status)
            if status == "Confirmé":
                status_item.setBackground(Qt.GlobalColor.green)
                status_item.setForeground(Qt.GlobalColor.white)
            elif status == "En attente":
                status_item.setBackground(Qt.GlobalColor.yellow)
            elif status == "Annulé":
                status_item.setBackground(Qt.GlobalColor.red)
                status_item.setForeground(Qt.GlobalColor.white)
            elif status == "Terminé":
                status_item.setBackground(Qt.GlobalColor.blue)
                status_item.setForeground(Qt.GlobalColor.white)
            self.reservations_table.setItem(row, 4, status_item)
            
            # Montant total
            total_amount = reservation.total_amount or 0
            self.reservations_table.setItem(row, 5, QTableWidgetItem(self.format_amount(total_amount)))
            
            # Acompte (calculé à partir des paiements)
            paid_amount = 0
            if hasattr(reservation, 'payments') and reservation.payments:
                paid_amount = sum(payment.amount for payment in reservation.payments)
            self.reservations_table.setItem(row, 6, QTableWidgetItem(self.format_amount(paid_amount)))
            
            # Date de création
            created_at = ""
            if reservation.created_at:
                created_at = reservation.created_at.strftime('%Y-%m-%d') if hasattr(reservation.created_at, 'strftime') else str(reservation.created_at)
            self.reservations_table.setItem(row, 7, QTableWidgetItem(created_at))
    
    def on_reservation_added(self, reservation):
        """Callback quand une réservation est ajoutée"""
        self.load_reservations()
        QMessageBox.information(self, "Succès", "Réservation ajoutée avec succès !")
    
    def on_reservation_updated(self, reservation):
        """Callback quand une réservation est modifiée"""
        self.load_reservations()
        QMessageBox.information(self, "Succès", "Réservation modifiée avec succès !")
    
    def on_reservation_deleted(self, reservation_id):
        """Callback quand une réservation est supprimée"""
        self.load_reservations()
        QMessageBox.information(self, "Succès", "Réservation supprimée avec succès !")
    
    def on_error_occurred(self, error_message):
        """Callback quand une erreur survient"""
        QMessageBox.critical(self, "Erreur", error_message)
    
    def on_reservation_selection_changed(self):
        """Gestion de la sélection d'une réservation"""
        selected_rows = self.reservations_table.selectionModel().selectedRows()
        
        if selected_rows:
            row = selected_rows[0].row()
            # Activer les boutons
            if hasattr(self, 'edit_reservation_button'):
                self.edit_reservation_button.setEnabled(True)
        else:
            if hasattr(self, 'edit_reservation_button'):
                self.edit_reservation_button.setEnabled(False)
    
    def show_add_reservation_form(self):
        """Afficher le formulaire d'ajout de réservation"""
        pass  # À implémenter
    
    def show_edit_reservation_form(self):
        """Afficher le formulaire de modification de réservation"""
        self.edit_selected_reservation()

