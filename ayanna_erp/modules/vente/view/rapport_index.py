"""
Widget pour les rapports du module Boutique
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                            QTableWidget, QTableWidgetItem, QPushButton, QLabel,
                            QDateEdit, QComboBox, QGroupBox, QGridLayout,
                            QMessageBox, QHeaderView, QFrame, QSplitter)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
from datetime import datetime, timedelta
import locale

class RapportIndexWidget(QWidget):
    """Widget principal pour les rapports et analyses"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.init_ui()
        
    def init_ui(self):
        """Initialisation de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # En-tête
        header_layout = QHBoxLayout()
        
        title_label = QLabel("📈 RAPPORTS ET ANALYSES")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2E7D32; margin-bottom: 10px;")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Bouton d'actualisation
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        refresh_btn.clicked.connect(self.actualiser_rapports)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Onglets pour différents types de rapports
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 5px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                padding: 10px 15px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #2E7D32;
                color: white;
            }
        """)
        
        # Onglet 1: Ventes par période
        self.init_ventes_periode_tab()
        
        # Onglet 2: Produits les plus vendus
        self.init_produits_populaires_tab()
        
        # Onglet 3: Analyse des clients
        self.init_clients_analyse_tab()
        
        # Onglet 4: Rapports financiers
        self.init_rapports_financiers_tab()
        
        # Onglet 5: Stock et inventaire
        self.init_stock_inventaire_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Charger les données initiales
        self.actualiser_rapports()
        
    def init_ventes_periode_tab(self):
        """Onglet des ventes par période"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Contrôles de période
        controls_group = QGroupBox("🗓️ Période d'analyse")
        controls_layout = QGridLayout(controls_group)
        
        # Sélection de période
        controls_layout.addWidget(QLabel("Du :"), 0, 0)
        self.date_debut = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_debut.setCalendarPopup(True)
        controls_layout.addWidget(self.date_debut, 0, 1)
        
        controls_layout.addWidget(QLabel("Au :"), 0, 2)
        self.date_fin = QDateEdit(QDate.currentDate())
        self.date_fin.setCalendarPopup(True)
        controls_layout.addWidget(self.date_fin, 0, 3)
        
        # Bouton de génération
        generate_btn = QPushButton("📊 Générer le rapport")
        generate_btn.clicked.connect(self.generer_rapport_ventes)
        controls_layout.addWidget(generate_btn, 0, 4)
        
        controls_layout.setColumnStretch(5, 1)
        layout.addWidget(controls_group)
        
        # Indicateurs de performance
        kpi_frame = QFrame()
        kpi_layout = QHBoxLayout(kpi_frame)
        
        self.kpi_chiffre_affaires = self.create_kpi_widget("💰 Chiffre d'Affaires", "0 €", "#4CAF50")
        self.kpi_nb_ventes = self.create_kpi_widget("🛒 Nombre de Ventes", "0", "#2196F3")
        self.kpi_panier_moyen = self.create_kpi_widget("📊 Panier Moyen", "0 €", "#FF9800")
        
        kpi_layout.addWidget(self.kpi_chiffre_affaires)
        kpi_layout.addWidget(self.kpi_nb_ventes)
        kpi_layout.addWidget(self.kpi_panier_moyen)
        
        layout.addWidget(kpi_frame)
        
        # Tableau des ventes détaillées
        self.table_ventes = QTableWidget()
        self.table_ventes.setColumnCount(6)
        self.table_ventes.setHorizontalHeaderLabels([
            "Date", "N° Panier", "Client", "Articles", "Total HT", "Total TTC"
        ])
        
        # Style du tableau
        self.table_ventes.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 10px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
        """)
        
        header = self.table_ventes.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.table_ventes)
        
        self.tab_widget.addTab(tab, "📈 Ventes par Période")
        
    def init_produits_populaires_tab(self):
        """Onglet des produits les plus vendus"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Titre
        title_label = QLabel("🏆 TOP PRODUITS LES PLUS VENDUS")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2E7D32; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Tableau des produits
        self.table_produits_top = QTableWidget()
        self.table_produits_top.setColumnCount(5)
        self.table_produits_top.setHorizontalHeaderLabels([
            "Rang", "Produit", "Quantité Vendue", "Chiffre d'Affaires", "Marge"
        ])
        
        self.table_produits_top.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 10px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
        """)
        
        header = self.table_produits_top.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.table_produits_top)
        
        self.tab_widget.addTab(tab, "🏆 Top Produits")
        
    def init_clients_analyse_tab(self):
        """Onglet d'analyse des clients"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Titre
        title_label = QLabel("👥 ANALYSE DE LA CLIENTÈLE")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2E7D32; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # KPIs clients
        client_kpi_frame = QFrame()
        client_kpi_layout = QHBoxLayout(client_kpi_frame)
        
        self.kpi_nb_clients = self.create_kpi_widget("👥 Clients Actifs", "0", "#9C27B0")
        self.kpi_nouveaux_clients = self.create_kpi_widget("🆕 Nouveaux Clients", "0", "#00BCD4")
        self.kpi_client_fidele = self.create_kpi_widget("⭐ Client le Plus Fidèle", "N/A", "#FF5722")
        
        client_kpi_layout.addWidget(self.kpi_nb_clients)
        client_kpi_layout.addWidget(self.kpi_nouveaux_clients)
        client_kpi_layout.addWidget(self.kpi_client_fidele)
        
        layout.addWidget(client_kpi_frame)
        
        # Tableau des meilleurs clients
        self.table_meilleurs_clients = QTableWidget()
        self.table_meilleurs_clients.setColumnCount(4)
        self.table_meilleurs_clients.setHorizontalHeaderLabels([
            "Client", "Nb Achats", "Total Dépensé", "Dernier Achat"
        ])
        
        self.table_meilleurs_clients.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 10px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
        """)
        
        header = self.table_meilleurs_clients.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.table_meilleurs_clients)
        
        self.tab_widget.addTab(tab, "👥 Clients")
        
    def init_rapports_financiers_tab(self):
        """Onglet des rapports financiers"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Titre
        title_label = QLabel("💼 RAPPORTS FINANCIERS")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2E7D32; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # KPIs financiers
        finance_kpi_frame = QFrame()
        finance_kpi_layout = QHBoxLayout(finance_kpi_frame)
        
        self.kpi_benefices = self.create_kpi_widget("💰 Bénéfices", "0 €", "#4CAF50")
        self.kpi_depenses = self.create_kpi_widget("💸 Dépenses", "0 €", "#F44336")
        self.kpi_marge_moyenne = self.create_kpi_widget("📊 Marge Moyenne", "0%", "#FF9800")
        
        finance_kpi_layout.addWidget(self.kpi_benefices)
        finance_kpi_layout.addWidget(self.kpi_depenses)
        finance_kpi_layout.addWidget(self.kpi_marge_moyenne)
        
        layout.addWidget(finance_kpi_frame)
        
        # Tableau des moyens de paiement
        self.table_moyens_paiement = QTableWidget()
        self.table_moyens_paiement.setColumnCount(3)
        self.table_moyens_paiement.setHorizontalHeaderLabels([
            "Moyen de Paiement", "Nombre de Transactions", "Montant Total"
        ])
        
        self.table_moyens_paiement.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 10px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
        """)
        
        header = self.table_moyens_paiement.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.table_moyens_paiement)
        
        self.tab_widget.addTab(tab, "💼 Finances")
        
    def init_stock_inventaire_tab(self):
        """Onglet de stock et inventaire"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Titre
        title_label = QLabel("📦 GESTION DU STOCK")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2E7D32; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # KPIs stock
        stock_kpi_frame = QFrame()
        stock_kpi_layout = QHBoxLayout(stock_kpi_frame)
        
        self.kpi_valeur_stock = self.create_kpi_widget("💎 Valeur du Stock", "0 €", "#673AB7")
        self.kpi_produits_stock = self.create_kpi_widget("📦 Produits en Stock", "0", "#3F51B5")
        self.kpi_ruptures = self.create_kpi_widget("⚠️ Ruptures de Stock", "0", "#F44336")
        
        stock_kpi_layout.addWidget(self.kpi_valeur_stock)
        stock_kpi_layout.addWidget(self.kpi_produits_stock)
        stock_kpi_layout.addWidget(self.kpi_ruptures)
        
        layout.addWidget(stock_kpi_frame)
        
        # Tableau des alertes stock
        self.table_alertes_stock = QTableWidget()
        self.table_alertes_stock.setColumnCount(4)
        self.table_alertes_stock.setHorizontalHeaderLabels([
            "Produit", "Stock Actuel", "Stock Minimum", "Statut"
        ])
        
        self.table_alertes_stock.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 10px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
        """)
        
        header = self.table_alertes_stock.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.table_alertes_stock)
        
        self.tab_widget.addTab(tab, "📦 Stock")
        
    def create_kpi_widget(self, title, value, color):
        """Crée un widget KPI"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.StyledPanel)
        widget.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 8px;
                margin: 5px;
            }}
        """)
        
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Titre
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #666;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Valeur
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        
        # Stocker la référence pour pouvoir mettre à jour
        setattr(widget, 'value_label', value_label)
        
        return widget
        
    def generer_rapport_ventes(self):
        """Génère le rapport des ventes pour la période sélectionnée"""
        try:
            if not self.parent_window or not hasattr(self.parent_window, 'boutique_controller'):
                QMessageBox.warning(self, "Erreur", "Contrôleur non disponible")
                return
                
            # Récupérer les dates
            date_debut = self.date_debut.date().toPyDate()
            date_fin = self.date_fin.date().toPyDate()
            
            # Récupérer les données via le contrôleur
            controller = self.parent_window.boutique_controller
            
            # Simuler des données pour le moment
            self.charger_donnees_ventes(date_debut, date_fin)
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération du rapport: {str(e)}")
            
    def charger_donnees_ventes(self, date_debut, date_fin):
        """Charge les données de ventes"""
        # Pour le moment, on simule des données
        # À remplacer par de vraies requêtes à la base de données
        
        # Mettre à jour les KPIs
        self.kpi_chiffre_affaires.value_label.setText("1,234 €")
        self.kpi_nb_ventes.value_label.setText("45")
        self.kpi_panier_moyen.value_label.setText("27.42 €")
        
        # Remplir le tableau des ventes
        self.table_ventes.setRowCount(5)
        sample_data = [
            ["2025-09-26", "PAN001", "Client Test", "3", "25.00", "30.00"],
            ["2025-09-25", "PAN002", "Marie Dupont", "2", "15.50", "18.60"],
            ["2025-09-24", "PAN003", "Jean Martin", "5", "45.00", "54.00"],
            ["2025-09-23", "PAN004", "Sophie Claire", "1", "8.00", "9.60"],
            ["2025-09-22", "PAN005", "Pierre Dubois", "4", "32.20", "38.64"]
        ]
        
        for row, data in enumerate(sample_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                self.table_ventes.setItem(row, col, item)
                
    def actualiser_rapports(self):
        """Actualise tous les rapports"""
        try:
            # Actualiser les données de tous les onglets
            self.generer_rapport_ventes()
            self.charger_top_produits()
            self.charger_analyse_clients()
            self.charger_rapports_financiers()
            self.charger_alertes_stock()
            
        except Exception as e:
            print(f"Erreur lors de l'actualisation des rapports: {e}")
    
    def refresh_data(self):
        """Alias pour actualiser_rapports (compatibilité)"""
        self.actualiser_rapports()
            
    def charger_top_produits(self):
        """Charge le top des produits"""
        # Données simulées
        self.table_produits_top.setRowCount(5)
        sample_data = [
            ["🥇", "Coca-Cola 33cl", "25", "75.00 €", "20.00 €"],
            ["🥈", "Sandwich Jambon", "18", "90.00 €", "35.00 €"],
            ["🥉", "Eau Minérale 1.5L", "15", "22.50 €", "8.00 €"],
            ["4", "Café Express", "12", "18.00 €", "10.00 €"],
            ["5", "Croissant", "10", "15.00 €", "8.50 €"]
        ]
        
        for row, data in enumerate(sample_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                if col == 0:  # Rang avec emoji
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_produits_top.setItem(row, col, item)
                
    def charger_analyse_clients(self):
        """Charge l'analyse des clients"""
        # Mettre à jour les KPIs clients
        self.kpi_nb_clients.value_label.setText("23")
        self.kpi_nouveaux_clients.value_label.setText("5")
        self.kpi_client_fidele.value_label.setText("Marie Dupont")
        
        # Remplir le tableau des meilleurs clients
        self.table_meilleurs_clients.setRowCount(5)
        sample_data = [
            ["Marie Dupont", "8", "245.50 €", "2025-09-25"],
            ["Jean Martin", "6", "189.20 €", "2025-09-24"],
            ["Sophie Claire", "5", "156.80 €", "2025-09-23"],
            ["Pierre Dubois", "4", "98.40 €", "2025-09-22"],
            ["Client Test", "3", "75.00 €", "2025-09-26"]
        ]
        
        for row, data in enumerate(sample_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                self.table_meilleurs_clients.setItem(row, col, item)
                
    def charger_rapports_financiers(self):
        """Charge les rapports financiers"""
        # Mettre à jour les KPIs financiers
        self.kpi_benefices.value_label.setText("456.78 €")
        self.kpi_depenses.value_label.setText("123.45 €")
        self.kpi_marge_moyenne.value_label.setText("35.5%")
        
        # Remplir le tableau des moyens de paiement
        self.table_moyens_paiement.setRowCount(4)
        sample_data = [
            ["Espèces", "25", "567.80 €"],
            ["Mobile Money", "15", "234.50 €"],
            ["Carte Bancaire", "8", "156.20 €"],
            ["Virement", "2", "45.00 €"]
        ]
        
        for row, data in enumerate(sample_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                self.table_moyens_paiement.setItem(row, col, item)
                
    def charger_alertes_stock(self):
        """Charge les alertes de stock"""
        # Mettre à jour les KPIs stock
        self.kpi_valeur_stock.value_label.setText("2,345.67 €")
        self.kpi_produits_stock.value_label.setText("45")
        self.kpi_ruptures.value_label.setText("3")
        
        # Remplir le tableau des alertes
        self.table_alertes_stock.setRowCount(5)
        sample_data = [
            ["Coca-Cola 33cl", "2", "5", "⚠️ Stock Faible"],
            ["Eau Minérale 1.5L", "0", "10", "🚨 Rupture"],
            ["Café Express", "1", "3", "⚠️ Stock Faible"],
            ["Sandwich Jambon", "15", "10", "✅ OK"],
            ["Croissant", "0", "5", "🚨 Rupture"]
        ]
        
        for row, data in enumerate(sample_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                if col == 3:  # Colonne statut
                    if "Rupture" in value:
                        item.setBackground(QColor(255, 235, 235))  # Rouge clair
                    elif "Faible" in value:
                        item.setBackground(QColor(255, 248, 220))  # Orange clair
                    else:
                        item.setBackground(QColor(235, 255, 235))  # Vert clair
                self.table_alertes_stock.setItem(row, col, item)