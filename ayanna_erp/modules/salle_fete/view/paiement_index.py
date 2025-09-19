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
                            QDialogButtonBox, QAbstractItemView, QFileDialog)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDateTime, QDate, QAbstractTableModel
from PyQt6.QtGui import QFont, QPixmap, QIcon, QStandardItemModel, QStandardItem
from decimal import Decimal
from datetime import datetime, timedelta
import sys
import os

# Import du gestionnaire d'impression
try:
    from ayanna_erp.modules.salle_fete.utils.payment_printer import PaymentPrintManager
    from ayanna_erp.modules.salle_fete.utils.print_settings import PrintSettings, PrintSettingsDialog
    from ayanna_erp.core.entreprise_controller import EntrepriseController
except ImportError:
    from ..utils.payment_printer import PaymentPrintManager
    from ..utils.print_settings import PrintSettings, PrintSettingsDialog
    try:
        from ayanna_erp.core.entreprise_controller import EntrepriseController
    except ImportError:
        EntrepriseController = None


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
            # Récupérer le symbole de devise depuis l'entreprise
            currency_symbol = "$"  # Fallback par défaut
            try:
                from ayanna_erp.core.entreprise_controller import EntrepriseController
                controller = EntrepriseController()
                currency_symbol = controller.get_currency_symbol()
            except:
                pass
            info_layout.addRow("Total à payer:", QLabel(f"{self.reservation_data.get('total_amount', 0):.2f} {currency_symbol}"))
            info_layout.addRow("Solde restant:", QLabel(f"{self.balance:.2f} {currency_symbol}"))
        
        layout.addWidget(info_group)
        
        # Formulaire de paiement
        payment_group = QGroupBox("Détails du paiement")
        payment_layout = QFormLayout(payment_group)
        
        # Montant
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMaximum(99999.99)
        self.amount_input.setValue(self.balance)
        self.amount_input.setSuffix(f" {currency_symbol}")
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
            'user_id': 1,  # TODO: Récupérer l'ID de l'utilisateur connecté
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
        
        # Initialiser le contrôleur d'entreprise pour les devises
        self.entreprise_controller = EntrepriseController() if EntrepriseController else None
        
        # Initialiser les paramètres d'impression
        self.print_settings = PrintSettings()
        
        # Initialiser le gestionnaire d'impression
        self.payment_printer = PaymentPrintManager()
        
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
    
    def format_amount(self, amount):
        """Formater un montant avec la devise de l'entreprise"""
        if self.entreprise_controller:
            return self.entreprise_controller.format_amount(amount)
        else:
            return f"{amount:.2f} €"  # Fallback
    
    def get_currency_symbol(self):
        """Récupérer le symbole de devise"""
        if self.entreprise_controller:
            return self.entreprise_controller.get_currency_symbol()
        else:
            return "€"  # Fallback
    
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
        self.guest_count_label = QLabel("-")
        
        client_info_layout.addRow("Client:", self.client_name_label)
        client_info_layout.addRow("Téléphone:", self.client_phone_label)
        client_info_layout.addRow("Date événement:", self.event_date_label)
        client_info_layout.addRow("Type:", self.event_type_label)
        client_info_layout.addRow("Nombre d'invités:", self.guest_count_label)
        
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
        
        self.subtotal_label = QLabel(f"0.00 {self.get_currency_symbol()}")
        self.tax_label = QLabel(f"0.00 {self.get_currency_symbol()}")
        self.total_ttc_label = QLabel(f"0.00 {self.get_currency_symbol()}")  # Nouveau
        self.discount_label = QLabel(f"0.00 {self.get_currency_symbol()}")
        self.total_net_label = QLabel(f"0.00 {self.get_currency_symbol()}")  # Renommé
        self.paid_label = QLabel(f"0.00 {self.get_currency_symbol()}")
        self.balance_label = QLabel(f"0.00 {self.get_currency_symbol()}")
        
        # Style pour les labels financiers
        financial_style = "font-weight: bold; font-size: 12px;"
        self.total_ttc_label.setStyleSheet(financial_style + "color: #2980B9;")  # Bleu pour TTC
        self.total_net_label.setStyleSheet(financial_style + "color: #E74C3C;")  # Rouge pour net final
        self.paid_label.setStyleSheet(financial_style + "color: #27AE60;")
        self.balance_label.setStyleSheet(financial_style + "color: #E74C3C;")
        self.discount_label.setStyleSheet("color: #E74C3C;")  # Rouge pour remise
        
        financial_layout.addRow("Sous-total HT:", self.subtotal_label)
        financial_layout.addRow("TVA:", self.tax_label)
        financial_layout.addRow("Total TTC:", self.total_ttc_label)
        financial_layout.addRow("Remise:", self.discount_label)
        financial_layout.addRow("Total NET:", self.total_net_label)
        financial_layout.addRow("Payé:", self.paid_label)
        financial_layout.addRow("Solde:", self.balance_label)
        
        details_layout.addWidget(financial_group)
        right_layout.addWidget(details_group)
        
        # Historique des paiements
        payments_group = QGroupBox("💳 Historique des paiements")
        payments_layout = QVBoxLayout(payments_group)
        
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(4)
        self.payments_table.setHorizontalHeaderLabels(["Date", "Montant", "Méthode", "Utilisateur"])
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
        
        self.print_reservation_button = QPushButton("📄 Imprimer réservation")
        self.print_reservation_button.setStyleSheet("""
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
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #BDC3C7;
            }
        """)
        self.print_reservation_button.setEnabled(False)
        
        # Bouton de configuration d'impression
        self.print_settings_button = QPushButton("⚙️ Paramètres impression")
        self.print_settings_button.setStyleSheet("""
            QPushButton {
                background-color: #7F8C8D;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #566367;
            }
        """)
        
        buttons_layout.addWidget(self.pay_button)
        buttons_layout.addWidget(self.print_receipt_button)
        buttons_layout.addWidget(self.print_reservation_button)
        buttons_layout.addWidget(self.print_settings_button)
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
        
        # Sélection de réservation - plusieurs signaux pour garantir la sélection
        self.reservations_table.itemSelectionChanged.connect(self.on_reservation_selected)
        self.reservations_table.cellClicked.connect(self.on_cell_clicked)
        self.reservations_table.currentItemChanged.connect(self.on_current_item_changed)
        
        # Boutons d'action
        self.pay_button.clicked.connect(self.open_payment_dialog)
        self.print_receipt_button.clicked.connect(self.print_receipt)
        self.print_reservation_button.clicked.connect(self.print_reservation)
        self.print_settings_button.clicked.connect(self.open_print_settings)
        
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
            self.reservations_table.setItem(row, 3, QTableWidgetItem(self.format_amount(total)))
            
            # Colorer le solde selon le statut
            balance_item = QTableWidgetItem(self.format_amount(balance))
            if balance > 0:
                balance_item.setBackground(Qt.GlobalColor.red)
                balance_item.setForeground(Qt.GlobalColor.white)
            elif balance == 0:
                balance_item.setBackground(Qt.GlobalColor.green)
                balance_item.setForeground(Qt.GlobalColor.white)
            
            self.reservations_table.setItem(row, 4, balance_item)
            
            # Stocker les données de la réservation
            self.reservations_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, reservation)
        
        # Sélectionner automatiquement la première ligne s'il y en a une
        if len(reservations) > 0:
            self.reservations_table.selectRow(0)
            self.select_reservation_at_row(0)
    
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
        self.select_reservation_at_row(current_row)
    
    def on_cell_clicked(self, row, column):
        """Callback quand une cellule est cliquée"""
        self.select_reservation_at_row(row)
    
    def on_current_item_changed(self, current, previous):
        """Callback quand l'élément courant change"""
        if current:
            row = current.row()
            self.select_reservation_at_row(row)
    
    def select_reservation_at_row(self, row):
        """Sélectionner la réservation à la ligne donnée"""
        if row >= 0 and row < self.reservations_table.rowCount():
            item = self.reservations_table.item(row, 0)
            if item:
                self.selected_reservation = item.data(Qt.ItemDataRole.UserRole)
                self.load_reservation_details()
                self.pay_button.setEnabled(True)
                self.print_receipt_button.setEnabled(True)
                self.print_reservation_button.setEnabled(True)
                
                # S'assurer que la ligne est sélectionnée visuellement
                self.reservations_table.selectRow(row)
            else:
                self.selected_reservation = None
                self.clear_reservation_details()
                self.pay_button.setEnabled(False)
                self.print_receipt_button.setEnabled(False)
                self.print_reservation_button.setEnabled(False)
    
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
                    
                    # Nombre d'invités
                    guest_count = reservation_details.get('guests_count', 0)  # Utiliser 'guests_count' avec un 's'
                    self.guest_count_label.setText(str(guest_count) if guest_count else "Non spécifié")
                    
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
                self.services_table.setItem(row, 3, QTableWidgetItem(self.format_amount(service.get('line_total', 0))))
                row += 1
            
            # Ajouter les produits
            for product in products:
                self.services_table.setItem(row, 0, QTableWidgetItem("Produit"))
                self.services_table.setItem(row, 1, QTableWidgetItem(product.get('name', 'N/A')))
                self.services_table.setItem(row, 2, QTableWidgetItem(str(product.get('quantity', 1))))
                self.services_table.setItem(row, 3, QTableWidgetItem(self.format_amount(product.get('line_total', 0))))
                row += 1
                
        except Exception as e:
            print(f"Erreur lors du chargement des services/produits: {e}")
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des détails: {str(e)}")
    
    def load_financial_summary(self):
        """Charger le résumé financier depuis les détails BDD - Nouvelle logique"""
        if not self.selected_reservation:
            return
        
        try:
            # Nouvelle logique : Sous-total HT + TVA = Total TTC, puis remise sur TTC
            subtotal_ht = self.selected_reservation.get('total_services', 0) + self.selected_reservation.get('total_products', 0)
            tax_amount = self.selected_reservation.get('tax_amount', 0) or 0
            total_ttc = self.selected_reservation.get('total_amount', 0) or 0  # TTC sans remise (stocké en BDD)
            discount_percent = self.selected_reservation.get('discount_percent', 0) or 0
            
            # Calcul de la remise sur le TTC 
            discount_amount = total_ttc * (discount_percent / 100) if total_ttc > 0 else 0
            
            # Total net = TTC - remise
            total_net = total_ttc - discount_amount
            
            # Montants payés et solde
            paid = self.selected_reservation.get('total_paid', 0) or 0
            balance = total_net - paid  # Solde calculé sur le total net
            
            # Mettre à jour les labels avec la nouvelle structure
            self.subtotal_label.setText(self.format_amount(subtotal_ht))
            self.tax_label.setText(self.format_amount(tax_amount))
            self.total_ttc_label.setText(self.format_amount(total_ttc))
            
            # Affichage de la remise avec pourcentage et montant
            if discount_percent > 0:
                self.discount_label.setText(f"{discount_percent:.1f}% (-{self.format_amount(discount_amount)})")
            else:
                self.discount_label.setText("0%")
            
            self.total_net_label.setText(self.format_amount(total_net))
            self.paid_label.setText(self.format_amount(paid))
            self.balance_label.setText(self.format_amount(balance))
            
            # Mettre à jour le solde dans selected_reservation pour cohérence
            self.selected_reservation['balance'] = balance
            
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
                self.payments_table.setItem(row, 1, QTableWidgetItem(self.format_amount(amount)))
                
                # Méthode
                method = payment.get('payment_method', 'N/A')
                self.payments_table.setItem(row, 2, QTableWidgetItem(method))
                
                # Utilisateur (nettoyer le nom pour enlever les notes automatiques)
                user_name = payment.get('user_name', f"Utilisateur {payment.get('user_id', 'N/A')}")
                if user_name and user_name != 'N/A':
                    # Supprimer les mots-clés indiquant des notes automatiques
                    keywords_to_remove = [
                        'acompte automatique pour réservation',
                        'automatique pour réservation', 
                        'pour réservation',
                        'acompte automatique',
                        'paiement automatique'
                    ]
                    
                    user_name_clean = user_name
                    for keyword in keywords_to_remove:
                        # Recherche insensible à la casse
                        if keyword.lower() in user_name_clean.lower():
                            # Supprimer le keyword et ce qui suit
                            index = user_name_clean.lower().find(keyword.lower())
                            user_name_clean = user_name_clean[:index].strip()
                            break
                    
                    # Si le nom devient vide ou trop court, utiliser une valeur par défaut
                    if not user_name_clean or len(user_name_clean) < 3:
                        user_name_clean = "Système"
                    
                    # Limiter la longueur pour éviter le débordement
                    user_name = user_name_clean[:20] if len(user_name_clean) > 20 else user_name_clean
                
                self.payments_table.setItem(row, 3, QTableWidgetItem(user_name))
                
        except Exception as e:
            print(f"Erreur lors du chargement de l'historique des paiements: {e}")
    
    def clear_reservation_details(self):
        """Effacer les détails de la réservation"""
        self.client_name_label.setText("Aucune réservation sélectionnée")
        self.client_phone_label.setText("-")
        self.event_date_label.setText("-")
        self.event_type_label.setText("-")
        self.guest_count_label.setText("-")
        
        self.services_table.setRowCount(0)
        self.payments_table.setRowCount(0)
        
        self.subtotal_label.setText(f"0.00 {self.get_currency_symbol()}")
        self.tax_label.setText(f"0.00 {self.get_currency_symbol()}")
        self.total_ttc_label.setText(f"0.00 {self.get_currency_symbol()}")
        self.discount_label.setText("0%")
        self.total_net_label.setText(f"0.00 {self.get_currency_symbol()}")
        self.paid_label.setText(f"0.00 {self.get_currency_symbol()}")
        self.balance_label.setText(f"0.00 {self.get_currency_symbol()}")
    
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
                    <tr><td>Sous-total HT</td><td>{self.format_amount(self.selected_reservation.get('total_services', 0) + self.selected_reservation.get('total_products', 0))}</td></tr>
                    <tr><td>TVA ({self.selected_reservation.get('tax_rate', 0):.1f}%)</td><td>{self.format_amount(self.selected_reservation.get('tax_amount', 0))}</td></tr>
                    <tr style="background-color: #f0f7ff;"><td><strong>Total TTC</strong></td><td><strong>{self.format_amount(self.selected_reservation.get('total_amount', 0))}</strong></td></tr>
                    <tr><td>Remise ({self.selected_reservation.get('discount_percent', 0):.1f}%)</td><td style="color: red;">-{self.format_amount(self.selected_reservation.get('total_amount', 0) * self.selected_reservation.get('discount_percent', 0) / 100)}</td></tr>
                    <tr class="total"><td><strong>Total NET</strong></td><td><strong>{self.format_amount(self.selected_reservation.get('total_amount', 0) * (1 - self.selected_reservation.get('discount_percent', 0) / 100))}</strong></td></tr>
                    <tr><td>Total payé</td><td style="color: green;">{self.format_amount(balance_info.get('total_paid', 0))}</td></tr>
                    <tr class="total"><td><strong>Solde restant</strong></td><td style="color: red;"><strong>{self.format_amount(balance_info.get('balance', 0))}</strong></td></tr>
                </table>
            </div>
            
            <div class="section">
                <h3>Historique des paiements</h3>
                <table>
                    <tr><th>Date</th><th>Montant</th><th>Méthode</th><th>Utilisateur</th><th>Notes</th></tr>
        """
        
        for payment in payments:
            date_str = payment.payment_date.strftime('%d/%m/%Y %H:%M') if payment.payment_date else 'N/A'
            user_name = getattr(payment, 'user_name', f"Utilisateur {payment.user_id}") if hasattr(payment, 'user_id') else 'N/A'
            html += f"""
                    <tr>
                        <td>{date_str}</td>
                        <td>{self.format_amount(payment.amount)}</td>
                        <td>{payment.payment_method or 'N/A'}</td>
                        <td>{user_name}</td>
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
    
    def print_reservation(self):
        """Exporter la réservation complète en PDF (A4)"""
        if not self.selected_reservation:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une réservation")
            return
        
        try:
            # Préparer les données de la réservation
            reservation_data = self.prepare_reservation_data()
            
            # Récupérer l'historique des paiements
            payment_history = self.get_payment_history()
            
            # Vérifier le comportement d'impression configuré
            behavior = self.print_settings.get_setting("reservation_behavior")
            
            if behavior == "save_pdf":
                # Comportement : Demander où sauvegarder le fichier
                reference = self.selected_reservation.get('reference', 'UNKNOWN')
                default_filename = f"reservation_{reference}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                
                filename, _ = QFileDialog.getSaveFileName(
                    self,
                    "Exporter la réservation",
                    default_filename,
                    "Fichiers PDF (*.pdf)"
                )
                
                if filename:
                    # Générer le PDF
                    result = self.payment_printer.print_reservation_a4(
                        reservation_data, payment_history, filename
                    )
                    
                    QMessageBox.information(self, "Export réussi", 
                                          f"Réservation exportée avec succès:\n{filename}")
            else:
                # Comportement : Impression directe
                import tempfile
                reference = self.selected_reservation.get('reference', 'UNKNOWN')
                
                with tempfile.NamedTemporaryFile(
                    suffix=f'_reservation_{reference}.pdf', 
                    delete=False
                ) as temp_file:
                    temp_filename = temp_file.name
                
                # Générer le PDF
                result = self.payment_printer.print_reservation_a4(
                    reservation_data, payment_history, temp_filename
                )
                
                # Utiliser les paramètres d'impression
                self.print_with_settings(temp_filename, "reservation")
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'export", 
                               f"Erreur lors de l'export:\n{str(e)}")
    
    def print_receipt(self):
        """Imprimer directement le reçu de paiement (53mm)"""
        if not self.selected_reservation:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une réservation")
            return
        
        # Vérifier qu'il y a au moins un paiement
        if not self.payments_table.rowCount():
            QMessageBox.warning(self, "Attention", "Aucun paiement à imprimer")
            return
        
        try:
            # Préparer les données de la réservation
            reservation_data = self.prepare_reservation_data()
            
            # Récupérer tous les paiements pour le reçu
            all_payments = self.get_payment_history()
            
            # Créer un fichier temporaire pour l'impression
            import tempfile
            reference = self.selected_reservation.get('reference', 'UNKNOWN')
            
            with tempfile.NamedTemporaryFile(
                suffix=f'_recu_{reference}.pdf', 
                delete=False
            ) as temp_file:
                temp_filename = temp_file.name
            
            # Générer le reçu avec tous les paiements
            result = self.payment_printer.print_receipt_53mm(
                reservation_data, all_payments, 
                self.current_user.name if hasattr(self.current_user, 'name') else 'Utilisateur', 
                temp_filename
            )
            
            # Utiliser les paramètres d'impression
            self.print_with_settings(temp_filename, "receipt")
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'impression", 
                               f"Erreur lors de l'impression du reçu:\n{str(e)}")
    
    def open_print_settings(self):
        """Ouvrir la fenêtre de configuration des paramètres d'impression"""
        dialog = PrintSettingsDialog(self.print_settings, self)
        dialog.exec()
    
    def print_with_settings(self, file_path, print_type="receipt"):
        """Imprimer selon les paramètres configurés"""
        import subprocess
        import os
        
        # Vérifier le comportement selon le type et les paramètres
        if print_type == "receipt":
            behavior = self.print_settings.get_setting("receipt_behavior")
        else:  # reservation
            behavior = self.print_settings.get_setting("reservation_behavior")
        
        if behavior == "direct_print":
            try:
                if os.name == 'nt':  # Windows
                    # Essayer plusieurs méthodes d'impression directe
                    try:
                        subprocess.run(['SumatraPDF.exe', '-print-to-default', file_path], 
                                     check=True, timeout=10)
                    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                        try:
                            subprocess.run(['AcroRd32.exe', '/t', file_path], 
                                         check=True, timeout=10)
                        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                            try:
                                subprocess.run(['powershell', '-Command', 
                                              f'Start-Process -FilePath "{file_path}" -Verb Print'], 
                                             check=True, timeout=10)
                            except:
                                os.startfile(file_path)
                                QMessageBox.information(self, "Impression", 
                                                       "Le fichier PDF a été ouvert. Veuillez utiliser Ctrl+P pour imprimer.")
                                return
                else:  # Linux/Mac
                    subprocess.call(['lpr', file_path])
                
                QMessageBox.information(self, "Impression envoyée", 
                                      "Document envoyé à l'imprimante par défaut")
            except Exception as print_error:
                QMessageBox.warning(self, "Erreur d'impression", 
                                   f"Impossible d'imprimer automatiquement.\nErreur: {print_error}\n\nLe fichier sera ouvert pour impression manuelle.")
                os.startfile(file_path)
        else:
            # Comportement "save_and_open" - juste ouvrir le fichier
            os.startfile(file_path)
            QMessageBox.information(self, "Fichier ouvert", 
                                  f"Le fichier a été ouvert :\n{file_path}")
    
    def prepare_reservation_data(self):
        """Préparer les données de la réservation pour l'impression"""
        if not self.selected_reservation:
            return {}
        
        # Récupérer les services et produits depuis les données de la réservation
        services = []
        for service_data in self.selected_reservation.get('services', []):
            try:
                service = {
                    'name': service_data.get('name', ''),
                    'quantity': float(service_data.get('quantity', 0)),
                    'unit_price': float(service_data.get('unit_price', 0))
                }
                services.append(service)
            except Exception as e:
                print(f"Erreur service: {e}")
                continue
        
        products = []
        for product_data in self.selected_reservation.get('products', []):
            try:
                product = {
                    'name': product_data.get('name', ''),
                    'quantity': float(product_data.get('quantity', 0)),
                    'unit_price': float(product_data.get('unit_price', 0))
                }
                products.append(product)
            except Exception as e:
                print(f"Erreur produit: {e}")
                continue
        
        # Calculer les totaux selon la nouvelle logique
        total_services = sum(s['quantity'] * s['unit_price'] for s in services)
        total_products = sum(p['quantity'] * p['unit_price'] for p in products)
        subtotal_ht = total_services + total_products
        
        # Récupérer les valeurs depuis la BDD
        tax_amount = self.selected_reservation.get('tax_amount', 0)
        total_ttc = self.selected_reservation.get('total_amount', 0)  # TTC sans remise (stocké en BDD)
        discount_percent = self.selected_reservation.get('discount_percent', 0)
        
        # Calculer remise et total net
        discount_amount = total_ttc * (discount_percent / 100) if total_ttc > 0 else 0
        total_net = total_ttc - discount_amount
        
        return {
            'reference': self.selected_reservation.get('reference', 'N/A'),
            'client_nom': self.selected_reservation.get('client_nom', 'N/A'),
            'client_telephone': self.selected_reservation.get('client_telephone', 'N/A'),
            'client_email': self.selected_reservation.get('client_email', 'N/A'),
            'client_adresse': self.selected_reservation.get('client_adresse', 'N/A'),
            'event_type': self.selected_reservation.get('event_type', 'N/A'),
            'event_date': str(self.selected_reservation.get('event_date', 'N/A')),
            'created_at': str(self.selected_reservation.get('created_at', 'N/A')),
            'guest_count': self.selected_reservation.get('guests_count', 0),  # Utiliser 'guests_count' avec un 's'
            'theme': self.selected_reservation.get('theme', 'N/A'),
            'notes': self.selected_reservation.get('notes', 'Aucune'),
            'services': services,
            'products': products,
            'total_services': total_services,
            'total_products': total_products,
            'subtotal_ht': subtotal_ht,
            'tax_amount': tax_amount,
            'tax_rate': self.selected_reservation.get('tax_rate', 0),
            'total_ttc': total_ttc,
            'discount_percent': discount_percent,
            'discount_amount': discount_amount,
            'total_net': total_net,
            'total_amount': total_ttc  # Pour compatibilité
        }
    
    def prepare_payment_data(self, row_index):
        """Préparer les données d'un paiement pour l'impression"""
        if row_index < 0 or row_index >= self.payments_table.rowCount():
            return {}
        
        # Calculer le total payé jusqu'à ce paiement
        total_paid = 0
        for i in range(row_index + 1):
            amount_text = self.payments_table.item(i, 1).text().replace(f' {self.get_currency_symbol()}', '') if self.payments_table.item(i, 1) else '0'
            total_paid += float(amount_text)
        
        return {
            'payment_date': self.payments_table.item(row_index, 0).text() if self.payments_table.item(row_index, 0) else 'N/A',
            'amount': float(self.payments_table.item(row_index, 1).text().replace(f' {self.get_currency_symbol()}', '')) if self.payments_table.item(row_index, 1) else 0,
            'payment_method': self.payments_table.item(row_index, 2).text() if self.payments_table.item(row_index, 2) else 'N/A',
            'total_paid': total_paid
        }
    
    def get_payment_history(self):
        """Récupérer l'historique complet des paiements"""
        payments = []
        for i in range(self.payments_table.rowCount()):
            payment = {
                'payment_date': self.payments_table.item(i, 0).text() if self.payments_table.item(i, 0) else 'N/A',
                'amount': float(self.payments_table.item(i, 1).text().replace(f' {self.get_currency_symbol()}', '')) if self.payments_table.item(i, 1) else 0,
                'payment_method': self.payments_table.item(i, 2).text() if self.payments_table.item(i, 2) else 'N/A',
                'user_name': self.payments_table.item(i, 3).text() if self.payments_table.item(i, 3) else 'N/A'
            }
            payments.append(payment)
        return payments
