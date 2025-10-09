"""
Widget de l'onglet Stock - Gestion des entrées/sorties de stock
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QComboBox,
    QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from ayanna_erp.database.database_manager import DatabaseManager


class StockIndex(QWidget):
    """Widget de gestion du stock"""
    
    def __init__(self, boutique_controller, current_user):
        super().__init__()
        self.boutique_controller = boutique_controller
        self.current_user = current_user
        self.db_manager = DatabaseManager()
        
        self.setup_ui()
        self.load_stock_data()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # === HEADER ===
        header_group = QGroupBox("📊 Gestion du Stock")
        header_layout = QVBoxLayout(header_group)
        
        # Actions
        actions_layout = QHBoxLayout()
        
        self.add_stock_btn = QPushButton("➕ Entrée de Stock")
        self.add_stock_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        actions_layout.addWidget(self.add_stock_btn)
        
        actions_layout.addStretch()
        
        # Filtres
        actions_layout.addWidget(QLabel("Filtrer:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("Tous les produits")
        self.filter_combo.addItem("Stock faible (< 10)")
        self.filter_combo.addItem("Rupture de stock")
        actions_layout.addWidget(self.filter_combo)
        
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.clicked.connect(self.load_stock_data)
        actions_layout.addWidget(refresh_btn)
        
        header_layout.addLayout(actions_layout)
        
        # Statistiques
        stats_layout = QHBoxLayout()
        
        self.total_products_label = QLabel("Produits: 0")
        self.total_products_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        stats_layout.addWidget(self.total_products_label)
        
        self.low_stock_label = QLabel("Stock faible: 0")
        self.low_stock_label.setStyleSheet("color: #F39C12; font-weight: bold;")
        stats_layout.addWidget(self.low_stock_label)
        
        self.out_of_stock_label = QLabel("Ruptures: 0")
        self.out_of_stock_label.setStyleSheet("color: #E74C3C; font-weight: bold;")
        stats_layout.addWidget(self.out_of_stock_label)
        
        stats_layout.addStretch()
        header_layout.addLayout(stats_layout)
        
        main_layout.addWidget(header_group)
        
        # === TABLEAU DU STOCK ===
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(7)
        self.stock_table.setHorizontalHeaderLabels([
            "ID", "Produit", "Catégorie", "Prix", "Stock Actuel", "Statut", "Actions"
        ])
        
        # Configuration des colonnes
        header = self.stock_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Produit
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Catégorie
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Prix
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Stock
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Statut
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Actions
        
        self.stock_table.setAlternatingRowColors(True)
        self.stock_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        main_layout.addWidget(self.stock_table)
    
    def load_stock_data(self):
        """Charger les données de stock"""
        try:
            with self.db_manager.get_session() as session:
                products = self.boutique_controller.get_products(session)
                self.populate_stock_table(products)
                self.update_statistics(products)
                
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement du stock: {str(e)}")
    
    def populate_stock_table(self, products):
        """Peupler le tableau de stock"""
        self.stock_table.setRowCount(len(products))
        
        for row, product in enumerate(products):
            # ID
            id_item = QTableWidgetItem(str(product.id))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.stock_table.setItem(row, 0, id_item)
            
            # Nom du produit
            self.stock_table.setItem(row, 1, QTableWidgetItem(product.name))
            
            # Catégorie (recharger l'objet dans la session)
            category_name = "Non assignée"
            if product.category_id:
                from ayanna_erp.modules.core.models.core_products import CoreProductCategory
                with self.db_manager.get_session() as session:
                    cat = session.query(CoreProductCategory).get(product.category_id)
                    if cat:
                        category_name = cat.name
            self.stock_table.setItem(row, 2, QTableWidgetItem(category_name))
            
            # Prix
            price_item = QTableWidgetItem(f"{product.price_unit:.2f} €")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.stock_table.setItem(row, 3, price_item)
            
            # Stock actuel (simulé pour l'instant)
            stock_quantity = 25  # Valeur par défaut simulée
            stock_item = QTableWidgetItem(str(stock_quantity))
            stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Colorer selon le stock
            if stock_quantity == 0:
                stock_item.setBackground(QColor("#E74C3C"))  # Rouge
                stock_item.setForeground(QColor("white"))
                status = "Rupture"
                status_color = "#E74C3C"
            elif stock_quantity < 10:
                stock_item.setBackground(QColor("#F39C12"))  # Orange
                stock_item.setForeground(QColor("white"))
                status = "Stock faible"
                status_color = "#F39C12"
            else:
                stock_item.setBackground(QColor("#27AE60"))  # Vert
                stock_item.setForeground(QColor("white"))
                status = "Normal"
                status_color = "#27AE60"
            
            self.stock_table.setItem(row, 4, stock_item)
            
            # Statut
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item.setBackground(QColor(status_color))
            status_item.setForeground(QColor("white"))
            self.stock_table.setItem(row, 5, status_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            # Bouton entrée de stock
            add_stock_btn = QPushButton("📈")
            add_stock_btn.setToolTip("Entrée de stock")
            add_stock_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27AE60;
                    color: white;
                    font-weight: bold;
                    padding: 5px;
                    border: none;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #229954;
                }
            """)
            actions_layout.addWidget(add_stock_btn)
            
            # Bouton historique
            history_btn = QPushButton("📊")
            history_btn.setToolTip("Historique du stock")
            history_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498DB;
                    color: white;
                    font-weight: bold;
                    padding: 5px;
                    border: none;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #2980B9;
                }
            """)
            actions_layout.addWidget(history_btn)
            
            self.stock_table.setCellWidget(row, 6, actions_widget)
    
    def update_statistics(self, products):
        """Mettre à jour les statistiques"""
        total = len(products)
        low_stock = 3  # Simulé
        out_of_stock = 1  # Simulé
        
        self.total_products_label.setText(f"Produits: {total}")
        self.low_stock_label.setText(f"Stock faible: {low_stock}")
        self.out_of_stock_label.setText(f"Ruptures: {out_of_stock}")
    
    def refresh_product_stock(self, product_id: int):
        """Actualiser le stock d'un produit spécifique"""
        self.load_stock_data()
    
    def refresh_data(self):
        """Actualiser les données de stock"""
        self.load_stock_data()
    
    def refresh_stock_data(self):
        """Alias pour actualiser les données de stock (compatibilité)"""
        self.load_stock_data()


class RapportIndex(QWidget):
    """Widget des rapports de la boutique"""
    
    def __init__(self, boutique_controller, current_user):
        super().__init__()
        self.boutique_controller = boutique_controller
        self.current_user = current_user
        self.db_manager = DatabaseManager()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # === HEADER ===
        header_group = QGroupBox("📈 Rapports et Analyses")
        header_layout = QVBoxLayout(header_group)
        
        # Actions
        actions_layout = QHBoxLayout()
        
        self.daily_report_btn = QPushButton("📅 Rapport Journalier")
        self.daily_report_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        actions_layout.addWidget(self.daily_report_btn)
        
        self.monthly_report_btn = QPushButton("📊 Rapport Mensuel")
        self.monthly_report_btn.setStyleSheet("""
            QPushButton {
                background-color: #9B59B6;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #8E44AD;
            }
        """)
        actions_layout.addWidget(self.monthly_report_btn)
        
        actions_layout.addStretch()
        
        header_layout.addLayout(actions_layout)
        main_layout.addWidget(header_group)
        
        # === RÉSUMÉ DES VENTES ===
        summary_group = QGroupBox("💰 Résumé des Ventes")
        summary_layout = QVBoxLayout(summary_group)
        
        # Métriques principales
        metrics_layout = QHBoxLayout()
        
        # Ventes du jour
        daily_sales_group = QGroupBox("Aujourd'hui")
        daily_sales_layout = QVBoxLayout(daily_sales_group)
        
        self.daily_sales_amount = QLabel("0,00 €")
        self.daily_sales_amount.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.daily_sales_amount.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.daily_sales_amount.setStyleSheet("color: #27AE60;")
        daily_sales_layout.addWidget(self.daily_sales_amount)
        
        self.daily_sales_count = QLabel("0 ventes")
        self.daily_sales_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        daily_sales_layout.addWidget(self.daily_sales_count)
        
        metrics_layout.addWidget(daily_sales_group)
        
        # Ventes du mois
        monthly_sales_group = QGroupBox("Ce mois")
        monthly_sales_layout = QVBoxLayout(monthly_sales_group)
        
        self.monthly_sales_amount = QLabel("0,00 €")
        self.monthly_sales_amount.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.monthly_sales_amount.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.monthly_sales_amount.setStyleSheet("color: #3498DB;")
        monthly_sales_layout.addWidget(self.monthly_sales_amount)
        
        self.monthly_sales_count = QLabel("0 ventes")
        self.monthly_sales_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        monthly_sales_layout.addWidget(self.monthly_sales_count)
        
        metrics_layout.addWidget(monthly_sales_group)
        
        # Produits les plus vendus
        top_products_group = QGroupBox("Top Produit")
        top_products_layout = QVBoxLayout(top_products_group)
        
        self.top_product_name = QLabel("Aucun")
        self.top_product_name.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.top_product_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_products_layout.addWidget(self.top_product_name)
        
        self.top_product_sales = QLabel("0 vendus")
        self.top_product_sales.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_products_layout.addWidget(self.top_product_sales)
        
        metrics_layout.addWidget(top_products_group)
        
        summary_layout.addLayout(metrics_layout)
        main_layout.addWidget(summary_group)
        
        # === TABLEAU DES VENTES RÉCENTES ===
        recent_sales_group = QGroupBox("🕐 Ventes Récentes")
        recent_sales_layout = QVBoxLayout(recent_sales_group)
        
        self.recent_sales_table = QTableWidget()
        self.recent_sales_table.setColumnCount(5)
        self.recent_sales_table.setHorizontalHeaderLabels([
            "Date", "Client", "Articles", "Montant", "Statut"
        ])
        
        # Configuration des colonnes
        header = self.recent_sales_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Date
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Client
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Articles
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Montant
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Statut
        
        self.recent_sales_table.setMaximumHeight(200)
        self.recent_sales_table.setAlternatingRowColors(True)
        
        recent_sales_layout.addWidget(self.recent_sales_table)
        main_layout.addWidget(recent_sales_group)
        
        # Stretch pour pousser tout vers le haut
        main_layout.addStretch()
        
        # Charger les données initiales
        self.load_reports_data()
    
    def load_reports_data(self):
        """Charger les données des rapports"""
        # Données simulées pour l'instant
        self.daily_sales_amount.setText("250,75 €")
        self.daily_sales_count.setText("8 ventes")
        
        self.monthly_sales_amount.setText("5.420,30 €")
        self.monthly_sales_count.setText("156 ventes")
        
        self.top_product_name.setText("Coca-Cola")
        self.top_product_sales.setText("45 vendus")
        
        # Ventes récentes simulées
        self.populate_recent_sales()
    
    def populate_recent_sales(self):
        """Peupler le tableau des ventes récentes"""
        # Données simulées
        sales_data = [
            ("26/09/2025 14:30", "Jean Dupont", "3", "45,50 €", "Payé"),
            ("26/09/2025 13:15", "Marie Martin", "1", "15,00 €", "Payé"),
            ("26/09/2025 12:00", "Client Anonyme", "2", "28,75 €", "Payé"),
            ("26/09/2025 10:45", "Pierre Durand", "5", "67,25 €", "Payé"),
        ]
        
        self.recent_sales_table.setRowCount(len(sales_data))
        
        for row, (date, client, articles, montant, statut) in enumerate(sales_data):
            self.recent_sales_table.setItem(row, 0, QTableWidgetItem(date))
            self.recent_sales_table.setItem(row, 1, QTableWidgetItem(client))
            
            articles_item = QTableWidgetItem(articles)
            articles_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.recent_sales_table.setItem(row, 2, articles_item)
            
            montant_item = QTableWidgetItem(montant)
            montant_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.recent_sales_table.setItem(row, 3, montant_item)
            
            statut_item = QTableWidgetItem(statut)
            statut_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            statut_item.setBackground(QColor("#27AE60"))  # Vert pour payé
            statut_item.setForeground(QColor("white"))
            self.recent_sales_table.setItem(row, 4, statut_item)
    
    def refresh_data(self):
        """Actualiser les données des rapports"""
        self.load_reports_data()
    
    def refresh_stock_data(self):
        """Alias pour actualiser les données de stock (compatibilité)"""
        self.load_stock_data()
        self.load_reports_data()