"""
Onglet Paiements pour le module Salle de Fête
Gestion et affichage des paiements liés aux réservations
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QTableWidget, QTableWidgetItem, QTableView,
                            QPushButton, QLineEdit, QLabel, QComboBox, 
                            QSpinBox, QDoubleSpinBox, QTextEdit, QMessageBox,
                            QGroupBox, QGridLayout, QListWidget, QSplitter,
                            QFrame, QScrollArea, QFormLayout, QCheckBox,
                            QDateTimeEdit, QHeaderView, QDateEdit, QDialog,
                            QDialogButtonBox, QAbstractItemView)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDateTime, QDate, QAbstractTableModel
from PyQt6.QtGui import QFont, QPixmap, QIcon, QStandardItemModel, QStandardItem
from decimal import Decimal
from datetime import datetime, timedelta
import sys
import os


class PaymentDialog(QDialog):
    """Fenêtre modale pour effectuer un paiement"""
    
    def __init__(self, parent=None, reservation_data=None, balance=0):
        super().__init__(parent)
        self.reservation_data = reservation_data
        self.balance = balance
        self.setWindowTitle("Effectuer un paiement")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        self.setup_ui()
        
    def setup_ui(self):
        """Configuration de l'interface de paiement"""
        layout = QVBoxLayout(self)
        
        # Informations de la réservation
        info_group = QGroupBox("Informations de la réservation")
        info_layout = QFormLayout(info_group)
        
        if self.reservation_data:
            info_layout.addRow("Référence:", QLabel(self.reservation_data.get('reference', 'N/A')))
            info_layout.addRow("Client:", QLabel(self.reservation_data.get('client_nom', 'N/A')))
            info_layout.addRow("Total à payer:", QLabel(f"{self.reservation_data.get('total_amount', 0):.2f} €"))
            info_layout.addRow("Solde restant:", QLabel(f"{self.balance:.2f} €"))
        
        layout.addWidget(info_group)
        
        # Formulaire de paiement
        payment_group = QGroupBox("Détails du paiement")
        payment_layout = QFormLayout(payment_group)
        
        # Montant
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMaximum(99999.99)
        self.amount_input.setValue(self.balance)
        self.amount_input.setSuffix(" €")
        payment_layout.addRow("Montant:", self.amount_input)
        
        # Méthode de paiement
        self.payment_method = QComboBox()
        self.payment_method.addItems(["Espèces", "Carte bancaire", "Chèque", "Virement", "Mobile Money"])
        payment_layout.addRow("Méthode:", self.payment_method)
        
        # Date de paiement
        self.payment_date = QDateTimeEdit()
        self.payment_date.setDateTime(QDateTime.currentDateTime())
        payment_layout.addRow("Date:", self.payment_date)
        
        # Notes
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        payment_layout.addRow("Notes:", self.notes)
        
        layout.addWidget(payment_group)
        
        # Boutons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_payment_data(self):
        """Récupérer les données du paiement"""
        # Gestion de la compatibilité PyQt6 pour la conversion de date
        payment_datetime = self.payment_date.dateTime()
        if hasattr(payment_datetime, 'toPython'):
            payment_date = payment_datetime.toPython()
        else:
            payment_date = payment_datetime.toPyDateTime()
            
        return {
            'reservation_id': self.reservation_data.get('id') if self.reservation_data else None,
            'amount': self.amount_input.value(),
            'payment_method': self.payment_method.currentText(),
            'payment_date': payment_date,
            'notes': self.notes.toPlainText(),
            'status': 'validated'
        }


class PaiementIndex(QWidget):
    """Onglet pour la gestion des paiements"""
    
    def __init__(self, db_manager, current_user):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.selected_reservation = None
        
        # Initialiser les contrôleurs - Import dynamique pour éviter les problèmes SQLAlchemy
        try:
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from ayanna_erp.modules.salle_fete.controller.paiement_controller import PaiementController
            from ayanna_erp.modules.salle_fete.controller.reservation_controller import ReservationController
            
            self.paiement_controller = PaiementController(pos_id=1)
            self.reservation_controller = ReservationController(pos_id=1)
        except Exception as e:
            print(f"Erreur lors de l'import des contrôleurs: {e}")
            self.paiement_controller = None
            self.reservation_controller = None
        
        self.setup_ui()
        self.connect_signals()
        self.load_reservations()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        main_layout = QHBoxLayout(self)
        
        # Splitter pour diviser l'écran en deux
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Partie gauche - Liste des réservations
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Barre de recherche
        search_group = QGroupBox("🔍 Rechercher une réservation")
        search_layout = QVBoxLayout(search_group)
        
        search_input_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher par nom de client, référence ou téléphone...")
        self.search_button = QPushButton("🔍")
        self.search_button.setMaximumWidth(40)
        
        search_input_layout.addWidget(self.search_input)
        search_input_layout.addWidget(self.search_button)
        search_layout.addLayout(search_input_layout)
        
        # Filtre par date
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Date:"))
        self.date_filter = QDateEdit()
        self.date_filter.setDate(QDate.currentDate())
        self.date_filter.setSpecialValueText("Toutes les dates")
        self.clear_date_button = QPushButton("❌")
        self.clear_date_button.setMaximumWidth(30)
        
        date_layout.addWidget(self.date_filter)
        date_layout.addWidget(self.clear_date_button)
        search_layout.addLayout(date_layout)
        
        left_layout.addWidget(search_group)
        
        # Liste des réservations
        reservations_group = QGroupBox("📋 Réservations")
        reservations_layout = QVBoxLayout(reservations_group)
        
        self.reservations_table = QTableWidget()
        self.reservations_table.setColumnCount(5)
        self.reservations_table.setHorizontalHeaderLabels([
            "Référence", "Client", "Date", "Total", "Solde"
        ])
        self.reservations_table.horizontalHeader().setStretchLastSection(True)
        self.reservations_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.reservations_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        reservations_layout.addWidget(self.reservations_table)
        left_layout.addWidget(reservations_group)
        
        # Partie droite - Détails et paiement
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Détails de la réservation sélectionnée
        details_group = QGroupBox("📋 Détails de la réservation")
        details_layout = QVBoxLayout(details_group)
        
        # Informations client
        client_info_layout = QFormLayout()
        self.client_name_label = QLabel("Aucune réservation sélectionnée")
        self.client_phone_label = QLabel("-")
        self.event_date_label = QLabel("-")
        self.event_type_label = QLabel("-")
        
        client_info_layout.addRow("Client:", self.client_name_label)
        client_info_layout.addRow("Téléphone:", self.client_phone_label)
        client_info_layout.addRow("Date événement:", self.event_date_label)
        client_info_layout.addRow("Type:", self.event_type_label)
        
        details_layout.addLayout(client_info_layout)
        
        # Services et produits
        services_group = QGroupBox("🛍️ Services et Produits")
        services_layout = QVBoxLayout(services_group)
        
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(4)
        self.services_table.setHorizontalHeaderLabels(["Type", "Nom", "Quantité", "Prix"])
        self.services_table.horizontalHeader().setStretchLastSection(True)
        self.services_table.setMaximumHeight(200)
        
        services_layout.addWidget(self.services_table)
        details_layout.addWidget(services_group)
        
        # Résumé financier
        financial_group = QGroupBox("💰 Résumé financier")
        financial_layout = QFormLayout(financial_group)
        
        self.subtotal_label = QLabel("0.00 €")
        self.discount_label = QLabel("0.00 €")
        self.tax_label = QLabel("0.00 €")
        self.total_label = QLabel("0.00 €")
        self.paid_label = QLabel("0.00 €")
        self.balance_label = QLabel("0.00 €")
        
        # Style pour les labels financiers
        financial_style = "font-weight: bold; font-size: 12px;"
        self.total_label.setStyleSheet(financial_style + "color: #2E86AB;")
        self.paid_label.setStyleSheet(financial_style + "color: #27AE60;")
        self.balance_label.setStyleSheet(financial_style + "color: #E74C3C;")
        
        financial_layout.addRow("Sous-total:", self.subtotal_label)
        financial_layout.addRow("Remise:", self.discount_label)
        financial_layout.addRow("TVA:", self.tax_label)
        financial_layout.addRow("Total:", self.total_label)
        financial_layout.addRow("Payé:", self.paid_label)
        financial_layout.addRow("Solde:", self.balance_label)
        
        details_layout.addWidget(financial_group)
        right_layout.addWidget(details_group)
        
        # Historique des paiements
        payments_group = QGroupBox("💳 Historique des paiements")
        payments_layout = QVBoxLayout(payments_group)
        
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(4)
        self.payments_table.setHorizontalHeaderLabels(["Date", "Montant", "Méthode", "Notes"])
        self.payments_table.horizontalHeader().setStretchLastSection(True)
        self.payments_table.setMaximumHeight(150)
        
        payments_layout.addWidget(self.payments_table)
        right_layout.addWidget(payments_group)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        self.pay_button = QPushButton("💳 Effectuer un paiement")
        self.pay_button.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #219A52;
            }
            QPushButton:disabled {
                background-color: #BDC3C7;
            }
        """)
        self.pay_button.setEnabled(False)
        
        self.print_receipt_button = QPushButton("🖨️ Imprimer reçu")
        self.print_receipt_button.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
            QPushButton:disabled {
                background-color: #BDC3C7;
            }
        """)
        self.print_receipt_button.setEnabled(False)
        
        buttons_layout.addWidget(self.pay_button)
        buttons_layout.addWidget(self.print_receipt_button)
        buttons_layout.addStretch()
        
        right_layout.addLayout(buttons_layout)
        
        # Assemblage final
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([500, 700])  # Proportion 40-60
        
        main_layout.addWidget(splitter)
    
    def connect_signals(self):
        """Connecter les signaux"""
        # Recherche
        self.search_input.textChanged.connect(self.perform_search)
        self.search_button.clicked.connect(self.perform_search)
        self.date_filter.dateChanged.connect(self.filter_by_date)
        self.clear_date_button.clicked.connect(self.clear_date_filter)
        
        # Sélection de réservation
        self.reservations_table.itemSelectionChanged.connect(self.on_reservation_selected)
        
        # Boutons d'action
        self.pay_button.clicked.connect(self.open_payment_dialog)
        self.print_receipt_button.clicked.connect(self.print_receipt)
        
        # Signaux du contrôleur
        if self.paiement_controller:
            self.paiement_controller.payment_added.connect(self.on_payment_added)
            self.paiement_controller.error_occurred.connect(self.on_error_occurred)
    
    def load_reservations(self):
        """Charger les dernières réservations de la base de données"""
        try:
            if self.paiement_controller:
                # Utiliser le nouveau contrôleur pour récupérer les 10 dernières réservations
                reservations = self.paiement_controller.get_latest_reservations(limit=10)
                self.populate_reservations_table(reservations)
            else:
                QMessageBox.warning(self, "Erreur", "Contrôleur de paiements non disponible")
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des réservations: {str(e)}")
    
    def populate_reservations_table(self, reservations):
        """Remplir le tableau des réservations avec les données de la BDD"""
        self.reservations_table.setRowCount(len(reservations))
        
        for row, reservation in enumerate(reservations):
            # Le solde est déjà calculé dans le contrôleur
            balance = reservation.get('balance', 0)
            
            # Remplir les colonnes
            self.reservations_table.setItem(row, 0, QTableWidgetItem(str(reservation.get('reference', ''))))
            self.reservations_table.setItem(row, 1, QTableWidgetItem(str(reservation.get('client_nom', ''))))
            
            # Date formatée
            event_date = reservation.get('event_date')
            if event_date:
                if isinstance(event_date, str):
                    date_str = event_date
                else:
                    date_str = event_date.strftime('%d/%m/%Y %H:%M')
            else:
                date_str = 'N/A'
            self.reservations_table.setItem(row, 2, QTableWidgetItem(date_str))
            
            # Total et solde
            total = reservation.get('total_amount', 0)
            self.reservations_table.setItem(row, 3, QTableWidgetItem(f"{total:.2f} €"))
            
            # Colorer le solde selon le statut
            balance_item = QTableWidgetItem(f"{balance:.2f} €")
            if balance > 0:
                balance_item.setBackground(Qt.GlobalColor.red)
                balance_item.setForeground(Qt.GlobalColor.white)
            elif balance == 0:
                balance_item.setBackground(Qt.GlobalColor.green)
                balance_item.setForeground(Qt.GlobalColor.white)
            
            self.reservations_table.setItem(row, 4, balance_item)
            
            # Stocker les données de la réservation
            self.reservations_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, reservation)
    
    def perform_search(self):
        """Effectuer une recherche dans la base de données"""
        search_text = self.search_input.text().strip()
        
        try:
            if self.paiement_controller:
                if search_text:
                    # Recherche par terme
                    reservations = self.paiement_controller.search_reservations(search_text, 'all')
                else:
                    # Charger les dernières réservations si pas de recherche
                    reservations = self.paiement_controller.get_latest_reservations(limit=10)
                
                self.populate_reservations_table(reservations)
            else:
                QMessageBox.warning(self, "Erreur", "Contrôleur de paiements non disponible")
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de la recherche: {str(e)}")
    
    def filter_by_date(self):
        """Filtrer les réservations par date d'événement"""
        selected_date = self.date_filter.date().toPython() if hasattr(self.date_filter.date(), 'toPython') else self.date_filter.date().toPyDate()
        
        try:
            if self.paiement_controller:
                # Filtrer par date d'événement (jour entier)
                start_date = datetime.combine(selected_date, datetime.min.time())
                end_date = datetime.combine(selected_date, datetime.max.time())
                
                reservations = self.paiement_controller.filter_reservations_by_date(start_date, end_date)
                self.populate_reservations_table(reservations)
            else:
                QMessageBox.warning(self, "Erreur", "Contrôleur de paiements non disponible")
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du filtrage par date: {str(e)}")
    
    def clear_date_filter(self):
        """Effacer le filtre de date et recharger toutes les réservations"""
        self.date_filter.setDate(QDate.currentDate())
        self.load_reservations()
    
    def on_reservation_selected(self):
        """Callback quand une réservation est sélectionnée"""
        current_row = self.reservations_table.currentRow()
        if current_row >= 0:
            item = self.reservations_table.item(current_row, 0)
            if item:
                self.selected_reservation = item.data(Qt.ItemDataRole.UserRole)
                self.load_reservation_details()
                self.pay_button.setEnabled(True)
                self.print_receipt_button.setEnabled(True)
        else:
            self.selected_reservation = None
            self.clear_reservation_details()
            self.pay_button.setEnabled(False)
            self.print_receipt_button.setEnabled(False)
    
    def load_reservation_details(self):
        """Charger les détails complets de la réservation depuis la BDD"""
        if not self.selected_reservation:
            return
        
        try:
            if self.paiement_controller:
                # Récupérer les détails complets depuis la base de données
                reservation_details = self.paiement_controller.get_reservation_details(self.selected_reservation['id'])
                
                if reservation_details:
                    # Mettre à jour les informations client
                    self.client_name_label.setText(reservation_details.get('client_nom', 'N/A'))
                    self.client_phone_label.setText(reservation_details.get('client_telephone', 'N/A'))
                    
                    # Date et type d'événement
                    event_date = reservation_details.get('event_date')
                    if event_date:
                        if isinstance(event_date, str):
                            self.event_date_label.setText(event_date)
                        else:
                            self.event_date_label.setText(event_date.strftime('%d/%m/%Y à %H:%M'))
                    else:
                        self.event_date_label.setText('N/A')
                    
                    self.event_type_label.setText(reservation_details.get('event_type', 'N/A'))
                    
                    # Mettre à jour la réservation sélectionnée avec les détails complets
                    self.selected_reservation = reservation_details
                    
                    # Charger les services et produits
                    self.load_services_and_products()
                    
                    # Charger les informations financières
                    self.load_financial_summary()
                    
                    # Charger l'historique des paiements
                    self.load_payment_history()
                else:
                    QMessageBox.warning(self, "Erreur", "Impossible de charger les détails de la réservation")
            else:
                QMessageBox.warning(self, "Erreur", "Contrôleur non disponible")
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des détails: {str(e)}")
    
    def load_services_and_products(self):
        """Charger les services et produits de la réservation depuis les détails BDD"""
        if not self.selected_reservation:
            return
        
        try:
            # Utiliser les données déjà chargées depuis la BDD
            services = self.selected_reservation.get('services', [])
            products = self.selected_reservation.get('products', [])
            
            total_items = len(services) + len(products)
            self.services_table.setRowCount(total_items)
            
            row = 0
            
            # Ajouter les services
            for service in services:
                self.services_table.setItem(row, 0, QTableWidgetItem("Service"))
                self.services_table.setItem(row, 1, QTableWidgetItem(service.get('name', 'N/A')))
                self.services_table.setItem(row, 2, QTableWidgetItem(str(service.get('quantity', 1))))
                self.services_table.setItem(row, 3, QTableWidgetItem(f"{service.get('line_total', 0):.2f} €"))
                row += 1
            
            # Ajouter les produits
            for product in products:
                self.services_table.setItem(row, 0, QTableWidgetItem("Produit"))
                self.services_table.setItem(row, 1, QTableWidgetItem(product.get('name', 'N/A')))
                self.services_table.setItem(row, 2, QTableWidgetItem(str(product.get('quantity', 1))))
                self.services_table.setItem(row, 3, QTableWidgetItem(f"{product.get('line_total', 0):.2f} €"))
                row += 1
                
        except Exception as e:
            print(f"Erreur lors du chargement des services/produits: {e}")
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des détails: {str(e)}")
    
    def load_financial_summary(self):
        """Charger le résumé financier depuis les détails BDD"""
        if not self.selected_reservation:
            return
        
        try:
            # Utiliser les données déjà chargées depuis la BDD
            subtotal = self.selected_reservation.get('total_services', 0) + self.selected_reservation.get('total_products', 0)
            discount = (self.selected_reservation.get('discount_percent', 0) / 100) * subtotal if subtotal > 0 else 0
            tax = self.selected_reservation.get('tax_amount', 0) or 0
            total = self.selected_reservation.get('total_amount', 0) or 0
            paid = self.selected_reservation.get('total_paid', 0) or 0
            balance = self.selected_reservation.get('balance', 0) or 0
            
            # Mettre à jour les labels
            self.subtotal_label.setText(f"{subtotal:.2f} €")
            self.discount_label.setText(f"{discount:.2f} €")
            self.tax_label.setText(f"{tax:.2f} €")
            self.total_label.setText(f"{total:.2f} €")
            self.paid_label.setText(f"{paid:.2f} €")
            self.balance_label.setText(f"{balance:.2f} €")
            
        except Exception as e:
            print(f"Erreur lors du chargement du résumé financier: {e}")
    
    def load_payment_history(self):
        """Charger l'historique des paiements depuis les détails BDD"""
        if not self.selected_reservation:
            return
        
        try:
            # Utiliser les données déjà chargées depuis la BDD
            payments = self.selected_reservation.get('payments', [])
            
            self.payments_table.setRowCount(len(payments))
            
            for row, payment in enumerate(payments):
                # Date
                payment_date = payment.get('payment_date')
                if payment_date:
                    if isinstance(payment_date, str):
                        date_str = payment_date
                    else:
                        date_str = payment_date.strftime('%d/%m/%Y %H:%M')
                else:
                    date_str = 'N/A'
                self.payments_table.setItem(row, 0, QTableWidgetItem(date_str))
                
                # Montant
                amount = payment.get('amount', 0)
                self.payments_table.setItem(row, 1, QTableWidgetItem(f"{amount:.2f} €"))
                
                # Méthode
                method = payment.get('payment_method', 'N/A')
                self.payments_table.setItem(row, 2, QTableWidgetItem(method))
                
                # Notes
                notes = payment.get('notes', '')
                self.payments_table.setItem(row, 3, QTableWidgetItem(notes))
                
        except Exception as e:
            print(f"Erreur lors du chargement de l'historique des paiements: {e}")
    
    def clear_reservation_details(self):
        """Effacer les détails de la réservation"""
        self.client_name_label.setText("Aucune réservation sélectionnée")
        self.client_phone_label.setText("-")
        self.event_date_label.setText("-")
        self.event_type_label.setText("-")
        
        self.services_table.setRowCount(0)
        self.payments_table.setRowCount(0)
        
        self.subtotal_label.setText("0.00 €")
        self.discount_label.setText("0.00 €")
        self.tax_label.setText("0.00 €")
        self.total_label.setText("0.00 €")
        self.paid_label.setText("0.00 €")
        self.balance_label.setText("0.00 €")
    
    def open_payment_dialog(self):
        """Ouvrir la fenêtre de paiement et créer le paiement en BDD"""
        if not self.selected_reservation:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une réservation.")
            return
        
        if not self.paiement_controller:
            QMessageBox.warning(self, "Erreur", "Contrôleur de paiements non disponible")
            return
        
        # Utiliser le solde déjà calculé dans les détails
        balance = self.selected_reservation.get('balance', 0)
        
        if balance <= 0:
            QMessageBox.information(self, "Information", "Cette réservation est entièrement payée.")
            return
        
        # Ouvrir la fenêtre de paiement
        dialog = PaymentDialog(self, self.selected_reservation, balance)
        if dialog.exec():
            payment_data = dialog.get_payment_data()
            
            # Créer le paiement dans la base de données
            success = self.paiement_controller.create_payment(payment_data)
            if success:
                QMessageBox.information(self, "Succès", "Paiement enregistré avec succès!")
                # Recharger les détails pour voir le nouveau paiement
                self.load_reservation_details()
            else:
                QMessageBox.warning(self, "Erreur", "Erreur lors de l'enregistrement du paiement")
                
    def print_receipt(self):
        """Imprimer le reçu"""
        if not self.selected_reservation:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une réservation.")
            return
        
        try:
            from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
            from PyQt6.QtGui import QPainter, QTextDocument, QPageSize
            
            # Créer le contenu du reçu
            receipt_html = self.generate_receipt_html()
            
            # Configuration d'impression
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            
            # Configuration de la taille de page (compatible PyQt6)
            page_size = QPageSize(QPageSize.PageSizeId.A4)
            printer.setPageSize(page_size)
            
            print_dialog = QPrintDialog(printer, self)
            if print_dialog.exec():
                document = QTextDocument()
                document.setHtml(receipt_html)
                document.print(printer)
                
                QMessageBox.information(self, "Succès", "Reçu imprimé avec succès!")
                
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de l'impression: {str(e)}")
    
    def generate_receipt_html(self):
        """Générer le HTML du reçu"""
        if not self.selected_reservation:
            return ""
        
        # Récupérer les informations
        balance_info = self.paiement_controller.get_payment_balance(self.selected_reservation['id'])
        payments = self.paiement_controller.get_payments_by_reservation(self.selected_reservation['id'])
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; }}
                .section {{ margin: 20px 0; }}
                .total {{ font-weight: bold; font-size: 14px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>REÇU DE PAIEMENT</h1>
                <p>Salle de Fête - Ayanna ERP</p>
                <p>Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
            
            <div class="section">
                <h3>Informations de la réservation</h3>
                <p><strong>Référence:</strong> {self.selected_reservation.get('reference', 'N/A')}</p>
                <p><strong>Client:</strong> {self.selected_reservation.get('client_nom', 'N/A')}</p>
                <p><strong>Téléphone:</strong> {self.selected_reservation.get('client_telephone', 'N/A')}</p>
                <p><strong>Type d'événement:</strong> {self.selected_reservation.get('event_type', 'N/A')}</p>
                <p><strong>Date de l'événement:</strong> {self.selected_reservation.get('event_date', 'N/A')}</p>
            </div>
            
            <div class="section">
                <h3>Résumé financier</h3>
                <table>
                    <tr><td>Sous-total</td><td>{self.selected_reservation.get('subtotal', 0):.2f} €</td></tr>
                    <tr><td>Remise</td><td>{self.selected_reservation.get('discount', 0):.2f} €</td></tr>
                    <tr><td>TVA</td><td>{self.selected_reservation.get('tax_amount', 0):.2f} €</td></tr>
                    <tr class="total"><td>Total</td><td>{self.selected_reservation.get('total_amount', 0):.2f} €</td></tr>
                    <tr><td>Total payé</td><td>{balance_info.get('total_paid', 0):.2f} €</td></tr>
                    <tr class="total"><td>Solde restant</td><td>{balance_info.get('balance', 0):.2f} €</td></tr>
                </table>
            </div>
            
            <div class="section">
                <h3>Historique des paiements</h3>
                <table>
                    <tr><th>Date</th><th>Montant</th><th>Méthode</th><th>Notes</th></tr>
        """
        
        for payment in payments:
            date_str = payment.payment_date.strftime('%d/%m/%Y %H:%M') if payment.payment_date else 'N/A'
            html += f"""
                    <tr>
                        <td>{date_str}</td>
                        <td>{payment.amount:.2f} €</td>
                        <td>{payment.payment_method or 'N/A'}</td>
                        <td>{payment.notes or ''}</td>
                    </tr>
            """
        
        html += """
                </table>
            </div>
            
            <div class="section" style="text-align: center; margin-top: 40px;">
                <p>Merci pour votre confiance!</p>
                <p><em>Ce document constitue un reçu de paiement</em></p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def on_payment_added(self, payment):
        """Callback quand un paiement est ajouté"""
        # Recharger les détails de la réservation
        self.load_reservation_details()
        # Recharger la liste des réservations pour mettre à jour les soldes
        self.load_reservations()
    
    def on_error_occurred(self, error_message):
        """Callback en cas d'erreur"""
        QMessageBox.warning(self, "Erreur", error_message)
