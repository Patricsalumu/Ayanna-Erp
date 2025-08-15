"""
Onglet Entrées/Sorties pour le module Salle de Fête
Gestion des mouvements de stock et de matériel
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QTableWidget, QTableWidgetItem, 
                            QPushButton, QLineEdit, QLabel, QComboBox, 
                            QSpinBox, QDoubleSpinBox, QTextEdit, QMessageBox,
                            QGroupBox, QGridLayout, QListWidget, QSplitter,
                            QFrame, QScrollArea, QFormLayout, QCheckBox,
                            QDateTimeEdit, QHeaderView, QDateEdit, QTabWidget)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDateTime, QDate
from PyQt6.QtGui import QFont, QPixmap, QIcon
from decimal import Decimal
from datetime import datetime, timedelta
from ayanna_erp.database.database_manager import DatabaseManager


class EntreeSortieIndex(QWidget):
    """Onglet pour la gestion des entrées et sorties"""
    
    def __init__(self, db_manager, current_user):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.setup_ui()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # Onglets pour entrées et sorties
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #BDC3C7;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ECF0F1;
                padding: 10px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #3498DB;
                color: white;
            }
        """)
        
        # Onglet Entrées
        self.setup_entrees_tab()
        
        # Onglet Sorties
        self.setup_sorties_tab()
        
        # Onglet Inventaire
        self.setup_inventaire_tab()
        
        layout.addWidget(self.tab_widget)
    
    def setup_entrees_tab(self):
        """Configuration de l'onglet Entrées"""
        entrees_widget = QWidget()
        layout = QVBoxLayout(entrees_widget)
        
        # Barre d'outils
        toolbar_layout = QHBoxLayout()
        
        # Boutons d'action
        self.add_entree_button = QPushButton("📥 Nouvelle entrée")
        self.add_entree_button.setStyleSheet("""
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
        
        self.edit_entree_button = QPushButton("✏️ Modifier")
        self.edit_entree_button.setStyleSheet("""
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
        
        # Filtres
        self.entree_date_filter = QDateEdit()
        self.entree_date_filter.setDate(QDate.currentDate())
        self.entree_date_filter.setStyleSheet("""
            QDateEdit {
                padding: 8px 12px;
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: white;
            }
        """)
        
        self.entree_type_filter = QComboBox()
        self.entree_type_filter.addItems(["Tous types", "Réapprovisionnement", "Retour client", "Achat", "Don", "Autre"])
        self.entree_type_filter.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: white;
            }
        """)
        
        toolbar_layout.addWidget(self.add_entree_button)
        toolbar_layout.addWidget(self.edit_entree_button)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(QLabel("Date:"))
        toolbar_layout.addWidget(self.entree_date_filter)
        toolbar_layout.addWidget(QLabel("Type:"))
        toolbar_layout.addWidget(self.entree_type_filter)
        
        # Table des entrées
        self.entrees_table = QTableWidget()
        self.entrees_table.setColumnCount(7)
        self.entrees_table.setHorizontalHeaderLabels([
            "ID", "Date", "Produit/Service", "Quantité", "Prix unitaire", "Type", "Fournisseur"
        ])
        
        # Configuration du tableau
        self.entrees_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.entrees_table.setAlternatingRowColors(True)
        self.entrees_table.setStyleSheet("""
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
                background-color: #27AE60;
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
        header = self.entrees_table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Produit/Service
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)  # Fournisseur
        
        # Résumé des entrées
        entrees_summary_group = QGroupBox("Résumé des entrées du jour")
        entrees_summary_layout = QHBoxLayout(entrees_summary_group)
        
        self.create_summary_card("Entrées aujourd'hui", "12", "#27AE60", entrees_summary_layout)
        self.create_summary_card("Valeur totale", "2,450.00 €", "#3498DB", entrees_summary_layout)
        self.create_summary_card("Nouveaux produits", "3", "#9B59B6", entrees_summary_layout)
        
        # Assemblage du layout
        layout.addLayout(toolbar_layout)
        layout.addWidget(entrees_summary_group)
        layout.addWidget(self.entrees_table)
        
        # Chargement des données
        self.load_entrees()
        
        # Ajout de l'onglet
        self.tab_widget.addTab(entrees_widget, "📥 Entrées")
    
    def setup_sorties_tab(self):
        """Configuration de l'onglet Sorties"""
        sorties_widget = QWidget()
        layout = QVBoxLayout(sorties_widget)
        
        # Barre d'outils
        toolbar_layout = QHBoxLayout()
        
        # Boutons d'action
        self.add_sortie_button = QPushButton("📤 Nouvelle sortie")
        self.add_sortie_button.setStyleSheet("""
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
        
        self.edit_sortie_button = QPushButton("✏️ Modifier")
        self.edit_sortie_button.setStyleSheet("""
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
        
        # Filtres
        self.sortie_date_filter = QDateEdit()
        self.sortie_date_filter.setDate(QDate.currentDate())
        self.sortie_date_filter.setStyleSheet("""
            QDateEdit {
                padding: 8px 12px;
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: white;
            }
        """)
        
        self.sortie_type_filter = QComboBox()
        self.sortie_type_filter.addItems(["Tous types", "Vente", "Événement", "Perte", "Casse", "Autre"])
        self.sortie_type_filter.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: white;
            }
        """)
        
        toolbar_layout.addWidget(self.add_sortie_button)
        toolbar_layout.addWidget(self.edit_sortie_button)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(QLabel("Date:"))
        toolbar_layout.addWidget(self.sortie_date_filter)
        toolbar_layout.addWidget(QLabel("Type:"))
        toolbar_layout.addWidget(self.sortie_type_filter)
        
        # Table des sorties
        self.sorties_table = QTableWidget()
        self.sorties_table.setColumnCount(7)
        self.sorties_table.setHorizontalHeaderLabels([
            "ID", "Date", "Produit/Service", "Quantité", "Prix unitaire", "Type", "Destination"
        ])
        
        # Configuration du tableau
        self.sorties_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sorties_table.setAlternatingRowColors(True)
        self.sorties_table.setStyleSheet("""
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
        header = self.sorties_table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Produit/Service
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)  # Destination
        
        # Résumé des sorties
        sorties_summary_group = QGroupBox("Résumé des sorties du jour")
        sorties_summary_layout = QHBoxLayout(sorties_summary_group)
        
        self.create_summary_card("Sorties aujourd'hui", "18", "#E74C3C", sorties_summary_layout)
        self.create_summary_card("Valeur totale", "1,890.00 €", "#F39C12", sorties_summary_layout)
        self.create_summary_card("Événements", "3", "#9B59B6", sorties_summary_layout)
        
        # Assemblage du layout
        layout.addLayout(toolbar_layout)
        layout.addWidget(sorties_summary_group)
        layout.addWidget(self.sorties_table)
        
        # Chargement des données
        self.load_sorties()
        
        # Ajout de l'onglet
        self.tab_widget.addTab(sorties_widget, "📤 Sorties")
    
    def setup_inventaire_tab(self):
        """Configuration de l'onglet Inventaire"""
        inventaire_widget = QWidget()
        layout = QVBoxLayout(inventaire_widget)
        
        # Barre d'outils
        toolbar_layout = QHBoxLayout()
        
        # Boutons d'action
        self.start_inventory_button = QPushButton("📋 Nouvel inventaire")
        self.start_inventory_button.setStyleSheet("""
            QPushButton {
                background-color: #9B59B6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8E44AD;
            }
        """)
        
        self.export_inventory_button = QPushButton("📊 Exporter inventaire")
        self.export_inventory_button.setStyleSheet("""
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
        
        # Filtres
        self.inventory_category_filter = QComboBox()
        self.inventory_category_filter.addItems(["Toutes catégories", "Boissons", "Alimentaire", "Matériel", "Décoration", "Autre"])
        self.inventory_category_filter.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: white;
            }
        """)
        
        toolbar_layout.addWidget(self.start_inventory_button)
        toolbar_layout.addWidget(self.export_inventory_button)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(QLabel("Catégorie:"))
        toolbar_layout.addWidget(self.inventory_category_filter)
        
        # Splitter pour diviser en deux parties
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Table de l'inventaire (côté gauche)
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(6)
        self.inventory_table.setHorizontalHeaderLabels([
            "Produit", "Stock théorique", "Stock réel", "Écart", "Valeur", "Statut"
        ])
        
        # Configuration du tableau
        self.inventory_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.inventory_table.setAlternatingRowColors(True)
        self.inventory_table.setStyleSheet("""
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
                background-color: #9B59B6;
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
        header = self.inventory_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Produit
        
        # Zone de résumé (côté droit)
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)
        
        # Statistiques générales
        stats_group = QGroupBox("Statistiques de l'inventaire")
        stats_layout = QFormLayout(stats_group)
        
        self.total_products_label = QLabel("156")
        self.total_value_label = QLabel("15,680.00 €")
        self.products_ok_label = QLabel("142")
        self.products_alert_label = QLabel("14")
        self.last_inventory_label = QLabel("01/08/2025")
        
        stats_layout.addRow("Total produits:", self.total_products_label)
        stats_layout.addRow("Valeur totale:", self.total_value_label)
        stats_layout.addRow("Produits OK:", self.products_ok_label)
        stats_layout.addRow("Alertes:", self.products_alert_label)
        stats_layout.addRow("Dernier inventaire:", self.last_inventory_label)
        
        # Écarts détectés
        ecarts_group = QGroupBox("Écarts détectés")
        ecarts_layout = QVBoxLayout(ecarts_group)
        
        self.ecarts_list = QListWidget()
        self.ecarts_list.setStyleSheet("""
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
                background-color: #E74C3C;
                color: white;
            }
        """)
        
        ecarts_layout.addWidget(self.ecarts_list)
        
        # Actions correctives
        actions_group = QGroupBox("Actions correctives")
        actions_layout = QVBoxLayout(actions_group)
        
        self.adjust_stock_button = QPushButton("🔄 Ajuster les stocks")
        self.adjust_stock_button.setStyleSheet("""
            QPushButton {
                background-color: #F39C12;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E67E22;
            }
        """)
        
        self.generate_report_button = QPushButton("📋 Générer rapport")
        self.generate_report_button.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #219A52;
            }
        """)
        
        actions_layout.addWidget(self.adjust_stock_button)
        actions_layout.addWidget(self.generate_report_button)
        actions_layout.addStretch()
        
        # Assemblage du layout du résumé
        summary_layout.addWidget(stats_group)
        summary_layout.addWidget(ecarts_group)
        summary_layout.addWidget(actions_group)
        
        # Ajout au splitter
        splitter.addWidget(self.inventory_table)
        splitter.addWidget(summary_widget)
        splitter.setSizes([600, 300])
        
        # Assemblage du layout principal
        layout.addLayout(toolbar_layout)
        layout.addWidget(splitter)
        
        # Chargement des données
        self.load_inventory()
        
        # Ajout de l'onglet
        self.tab_widget.addTab(inventaire_widget, "📋 Inventaire")
    
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
        value_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        card_layout.addWidget(value_label)
        card_layout.addWidget(title_label)
        
        layout.addWidget(card)
    
    def load_entrees(self):
        """Charger les entrées depuis la base de données"""
        # TODO: Implémenter le chargement depuis la base de données
        sample_data = [
            ["E001", "2025-08-15", "Champagne Moët & Chandon", "10", "45.00 €", "Réapprovisionnement", "Fournisseur A"],
            ["E002", "2025-08-15", "Petits fours assortis", "20", "12.00 €", "Réapprovisionnement", "Traiteur B"],
            ["E003", "2025-08-14", "Nappes blanches", "15", "15.00 €", "Achat", "Magasin C"],
            ["E004", "2025-08-14", "Bouquets de roses", "8", "35.00 €", "Achat", "Fleuriste D"],
        ]
        
        self.entrees_table.setRowCount(len(sample_data))
        
        for row, data in enumerate(sample_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                self.entrees_table.setItem(row, col, item)
    
    def load_sorties(self):
        """Charger les sorties depuis la base de données"""
        # TODO: Implémenter le chargement depuis la base de données
        sample_data = [
            ["S001", "2025-08-15", "Champagne Moët & Chandon", "3", "45.00 €", "Événement", "Mariage Dupont"],
            ["S002", "2025-08-15", "Petits fours assortis", "5", "12.00 €", "Événement", "Mariage Dupont"],
            ["S003", "2025-08-15", "Nappes blanches", "2", "15.00 €", "Événement", "Anniversaire Bernard"],
            ["S004", "2025-08-14", "Verres cassés", "8", "5.00 €", "Casse", "Incident"],
        ]
        
        self.sorties_table.setRowCount(len(sample_data))
        
        for row, data in enumerate(sample_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                # Couleur selon le type
                if col == 5:  # Colonne type
                    if value == "Casse" or value == "Perte":
                        item.setBackground(Qt.GlobalColor.red)
                        item.setForeground(Qt.GlobalColor.white)
                    elif value == "Événement":
                        item.setBackground(Qt.GlobalColor.green)
                        item.setForeground(Qt.GlobalColor.white)
                
                self.sorties_table.setItem(row, col, item)
    
    def load_inventory(self):
        """Charger l'inventaire depuis la base de données"""
        # TODO: Implémenter le chargement depuis la base de données
        sample_data = [
            ["Champagne Moët & Chandon", "25", "23", "-2", "1,035.00 €", "⚠️ Écart"],
            ["Petits fours assortis", "20", "20", "0", "240.00 €", "✅ OK"],
            ["Nappes blanches", "30", "32", "+2", "480.00 €", "ℹ️ Surplus"],
            ["Bouquets de roses", "5", "0", "-5", "0.00 €", "❌ Rupture"],
            ["Assiettes jetables", "100", "98", "-2", "784.00 €", "⚠️ Écart"],
        ]
        
        self.inventory_table.setRowCount(len(sample_data))
        
        for row, data in enumerate(sample_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                
                # Couleur selon le statut
                if col == 5:  # Colonne statut
                    if "OK" in value:
                        item.setBackground(Qt.GlobalColor.green)
                        item.setForeground(Qt.GlobalColor.white)
                    elif "Écart" in value:
                        item.setBackground(Qt.GlobalColor.yellow)
                    elif "Rupture" in value:
                        item.setBackground(Qt.GlobalColor.red)
                        item.setForeground(Qt.GlobalColor.white)
                    elif "Surplus" in value:
                        item.setBackground(Qt.GlobalColor.blue)
                        item.setForeground(Qt.GlobalColor.white)
                
                self.inventory_table.setItem(row, col, item)
        
        # Charger les écarts
        ecarts = [
            "Champagne Moët & Chandon: -2 unités",
            "Bouquets de roses: -5 unités (rupture)",
            "Assiettes jetables: -2 unités",
            "Nappes blanches: +2 unités (surplus)"
        ]
        
        for ecart in ecarts:
            self.ecarts_list.addItem(ecart)
