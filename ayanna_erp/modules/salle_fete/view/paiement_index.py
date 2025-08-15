"""
Onglet Paiements pour le module Salle de Fête
Gestion et affichage des paiements
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QTableWidget, QTableWidgetItem, 
                            QPushButton, QLineEdit, QLabel, QComboBox, 
                            QSpinBox, QDoubleSpinBox, QTextEdit, QMessageBox,
                            QGroupBox, QGridLayout, QListWidget, QSplitter,
                            QFrame, QScrollArea, QFormLayout, QCheckBox,
                            QDateTimeEdit, QHeaderView, QDateEdit)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDateTime, QDate
from PyQt6.QtGui import QFont, QPixmap, QIcon
from decimal import Decimal
from datetime import datetime, timedelta
from ayanna_erp.database.database_manager import DatabaseManager


class PaiementIndex(QWidget):
    """Onglet pour la gestion des paiements"""
    
    def __init__(self, db_manager, current_user):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.setup_ui()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # Barre d'outils
        toolbar_layout = QHBoxLayout()
        
        # Boutons d'action
        self.add_payment_button = QPushButton("➕ Nouveau paiement")
        self.add_payment_button.setStyleSheet("""
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
        
        self.edit_payment_button = QPushButton("✏️ Modifier")
        self.edit_payment_button.setStyleSheet("""
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
        
        self.delete_payment_button = QPushButton("🗑️ Supprimer")
        self.delete_payment_button.setStyleSheet("""
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
        
        # Filtre par période
        period_label = QLabel("Période:")
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setStyleSheet("""
            QDateEdit {
                padding: 8px 12px;
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: white;
            }
        """)
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setStyleSheet("""
            QDateEdit {
                padding: 8px 12px;
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: white;
            }
        """)
        
        # Filtre par méthode de paiement
        self.payment_method_filter = QComboBox()
        self.payment_method_filter.addItems(["Toutes méthodes", "Espèces", "Carte bancaire", "Chèque", "Virement", "Autre"])
        self.payment_method_filter.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: white;
            }
        """)
        
        # Barre de recherche
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Rechercher un paiement...")
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
        
        toolbar_layout.addWidget(self.add_payment_button)
        toolbar_layout.addWidget(self.edit_payment_button)
        toolbar_layout.addWidget(self.delete_payment_button)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(period_label)
        toolbar_layout.addWidget(self.start_date)
        toolbar_layout.addWidget(QLabel("au"))
        toolbar_layout.addWidget(self.end_date)
        toolbar_layout.addWidget(QLabel("Méthode:"))
        toolbar_layout.addWidget(self.payment_method_filter)
        toolbar_layout.addWidget(self.search_input)
        
        # Résumé financier
        summary_group = QGroupBox("Résumé de la période")
        summary_layout = QHBoxLayout(summary_group)
        
        # Cartes de résumé
        self.create_summary_card("Total encaissé", "12,750.00 €", "#27AE60", summary_layout)
        self.create_summary_card("Nombre de paiements", "28", "#3498DB", summary_layout)
        self.create_summary_card("Paiement moyen", "455.36 €", "#9B59B6", summary_layout)
        self.create_summary_card("En attente", "2,150.00 €", "#F39C12", summary_layout)
        
        # Table des paiements
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(8)
        self.payments_table.setHorizontalHeaderLabels([
            "ID", "Date", "Client", "Réservation", "Montant", "Méthode", "Statut", "Notes"
        ])
        
        # Configuration du tableau
        self.payments_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.payments_table.setAlternatingRowColors(True)
        self.payments_table.setStyleSheet("""
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
        header = self.payments_table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Client
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)  # Notes
        
        # Zone de détails du paiement sélectionné
        details_group = QGroupBox("Détails du paiement sélectionné")
        details_layout = QVBoxLayout(details_group)
        
        self.payment_details = QTextEdit()
        self.payment_details.setReadOnly(True)
        self.payment_details.setMaximumHeight(120)
        self.payment_details.setStyleSheet("""
            QTextEdit {
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: #F8F9FA;
                padding: 10px;
            }
        """)
        
        details_layout.addWidget(self.payment_details)
        
        # Assemblage du layout principal
        layout.addLayout(toolbar_layout)
        layout.addWidget(summary_group)
        layout.addWidget(self.payments_table)
        layout.addWidget(details_group)
        
        # Chargement des données
        self.load_payments()
        
        # Connexion des signaux
        self.payments_table.itemSelectionChanged.connect(self.on_payment_selected)
        self.search_input.textChanged.connect(self.filter_payments)
        self.payment_method_filter.currentTextChanged.connect(self.filter_payments)
        self.start_date.dateChanged.connect(self.filter_payments)
        self.end_date.dateChanged.connect(self.filter_payments)
    
    def create_summary_card(self, title, value, color, layout):
        """Créer une carte de résumé"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border: none;
                border-radius: 10px;
                padding: 15px;
                margin: 5px;
            }}
            QLabel {{
                color: white;
                font-weight: bold;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        card_layout.addWidget(value_label)
        card_layout.addWidget(title_label)
        
        layout.addWidget(card)
    
    def load_payments(self):
        """Charger les paiements depuis la base de données"""
        # TODO: Implémenter le chargement depuis la base de données
        # Pour l'instant, on utilise des données de test
        sample_data = [
            ["001", "2025-08-15", "Martin Dupont", "RES001", "500.00 €", "Carte bancaire", "Validé", "Acompte mariage"],
            ["002", "2025-08-14", "Sophie Bernard", "RES002", "200.00 €", "Espèces", "Validé", "Acompte anniversaire"],
            ["003", "2025-08-13", "Jean Moreau", "RES003", "1200.00 €", "Virement", "Validé", "Solde baptême"],
            ["004", "2025-08-12", "Claire Dubois", "RES004", "800.00 €", "Chèque", "En attente", "Acompte réunion"],
            ["005", "2025-08-11", "Pierre Martin", "RES005", "300.00 €", "Carte bancaire", "Validé", "Complément service"],
            ["006", "2025-08-10", "Marie Leroy", "RES006", "1500.00 €", "Virement", "Validé", "Paiement complet"],
            ["007", "2025-08-09", "Paul Durand", "RES007", "450.00 €", "Espèces", "Validé", "Acompte cocktail"],
            ["008", "2025-08-08", "Anne Petit", "RES008", "2500.00 €", "Virement", "Validé", "Solde mariage"],
        ]
        
        self.payments_table.setRowCount(len(sample_data))
        
        for row, data in enumerate(sample_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                
                # Couleur selon le statut
                if col == 6:  # Colonne statut
                    if value == "Validé":
                        item.setBackground(Qt.GlobalColor.green)
                        item.setForeground(Qt.GlobalColor.white)
                    elif value == "En attente":
                        item.setBackground(Qt.GlobalColor.yellow)
                    elif value == "Annulé":
                        item.setBackground(Qt.GlobalColor.red)
                        item.setForeground(Qt.GlobalColor.white)
                
                self.payments_table.setItem(row, col, item)
    
    def on_payment_selected(self):
        """Gérer la sélection d'un paiement"""
        current_row = self.payments_table.currentRow()
        if current_row >= 0:
            # Récupérer les informations du paiement sélectionné
            payment_id = self.payments_table.item(current_row, 0).text()
            date = self.payments_table.item(current_row, 1).text()
            client = self.payments_table.item(current_row, 2).text()
            reservation = self.payments_table.item(current_row, 3).text()
            montant = self.payments_table.item(current_row, 4).text()
            methode = self.payments_table.item(current_row, 5).text()
            statut = self.payments_table.item(current_row, 6).text()
            notes = self.payments_table.item(current_row, 7).text()
            
            details = f"""
            <b>Paiement #{payment_id}</b><br>
            <b>Date:</b> {date}<br>
            <b>Client:</b> {client}<br>
            <b>Réservation:</b> {reservation}<br>
            <b>Montant:</b> {montant}<br>
            <b>Méthode de paiement:</b> {methode}<br>
            <b>Statut:</b> {statut}<br>
            <b>Notes:</b> {notes}<br>
            <b>Traité par:</b> {self.current_user.get('nom', 'Utilisateur')}
            """
            
            self.payment_details.setHtml(details)
    
    def filter_payments(self):
        """Filtrer les paiements selon les critères"""
        search_text = self.search_input.text().lower()
        method_filter = self.payment_method_filter.currentText()
        start_date = self.start_date.date()
        end_date = self.end_date.date()
        
        for row in range(self.payments_table.rowCount()):
            show_row = True
            
            # Filtre par texte de recherche
            if search_text:
                client = self.payments_table.item(row, 2).text().lower()
                reservation = self.payments_table.item(row, 3).text().lower()
                notes = self.payments_table.item(row, 7).text().lower()
                if (search_text not in client and search_text not in reservation and 
                    search_text not in notes):
                    show_row = False
            
            # Filtre par méthode de paiement
            if method_filter != "Toutes méthodes":
                methode = self.payments_table.item(row, 5).text()
                if methode != method_filter:
                    show_row = False
            
            # Filtre par date
            payment_date_str = self.payments_table.item(row, 1).text()
            try:
                payment_date = QDate.fromString(payment_date_str, "yyyy-MM-dd")
                if payment_date < start_date or payment_date > end_date:
                    show_row = False
            except:
                pass  # Si la conversion de date échoue, on garde la ligne
            
            self.payments_table.setRowHidden(row, not show_row)
        
        # Mettre à jour le résumé après filtrage
        self.update_summary()
    
    def update_summary(self):
        """Mettre à jour le résumé des paiements visibles"""
        # TODO: Implémenter le calcul des totaux selon les filtres
        # Pour l'instant, on garde les valeurs statiques
        pass
