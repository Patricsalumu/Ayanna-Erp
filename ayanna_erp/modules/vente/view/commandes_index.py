"""
Widget pour l'affichage et la gestion des commandes du module Boutique
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                            QTableWidgetItem, QPushButton, QLabel, QDateEdit, 
                            QLineEdit, QComboBox, QGroupBox, QGridLayout,
                            QHeaderView, QFrame, QSplitter, QMessageBox)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
from datetime import datetime, timedelta
from decimal import Decimal

class CommandesIndexWidget(QWidget):
    """Widget principal pour l'affichage et gestion des commandes"""
    
    # Signaux
    commande_selected = pyqtSignal(int)  # ID de la commande sélectionnée
    
    def __init__(self, boutique_controller, current_user, parent=None):
        super().__init__(parent)
        self.boutique_controller = boutique_controller
        self.current_user = current_user
        self.parent_window = parent
        
        self.init_ui()
        self.load_commandes()
        
    def init_ui(self):
        """Initialisation de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)
        
        # En-tête avec titre et statistiques
        self.create_header(layout)
        
        # Zone de filtres et recherche
        self.create_filters_section(layout)
        
        # Tableau des commandes
        self.create_commandes_table(layout)
        
        # Zone de statistiques en bas
        self.create_statistics_section(layout)
        
    def create_header(self, layout):
        """Créer l'en-tête avec titre et stats rapides"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        header_layout = QHBoxLayout(header_frame)
        
        # Titre
        title_label = QLabel("📋 GESTION DES COMMANDES")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2E7D32; margin-bottom: 5px;")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Stats rapides
        self.stats_layout = QHBoxLayout()
        self.create_stat_widget("Commandes aujourd'hui", "0", "#4CAF50")
        self.create_stat_widget("Total CA", "0 FC", "#2196F3")
        self.create_stat_widget("Créances", "0 FC", "#FF9800")
        
        header_layout.addLayout(self.stats_layout)
        
        layout.addWidget(header_frame)
        
    def create_stat_widget(self, label_text, value_text, color):
        """Créer un widget de statistique"""
        stat_frame = QFrame()
        stat_frame.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 6px;
                padding: 10px;
                margin: 5px;
            }}
        """)
        
        stat_layout = QVBoxLayout(stat_frame)
        stat_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Valeur
        value_label = QLabel(value_text)
        value_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Label
        label = QLabel(label_text)
        label.setStyleSheet("font-size: 11px; color: #666;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        stat_layout.addWidget(value_label)
        stat_layout.addWidget(label)
        
        # Stocker les références pour mise à jour
        if not hasattr(self, 'stat_widgets'):
            self.stat_widgets = {}
        
        key = label_text.lower().replace(' ', '_')
        self.stat_widgets[key] = value_label
        
        self.stats_layout.addWidget(stat_frame)
        
    def create_filters_section(self, layout):
        """Créer la section des filtres et recherche"""
        filters_group = QGroupBox("🔍 Filtres et Recherche")
        filters_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        filters_layout = QGridLayout(filters_group)
        
        # Filtre par dates
        filters_layout.addWidget(QLabel("Du :"), 0, 0)
        self.date_debut = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_debut.setCalendarPopup(True)
        self.date_debut.dateChanged.connect(self.filter_commandes)
        filters_layout.addWidget(self.date_debut, 0, 1)
        
        filters_layout.addWidget(QLabel("Au :"), 0, 2)
        self.date_fin = QDateEdit(QDate.currentDate())
        self.date_fin.setCalendarPopup(True)
        self.date_fin.dateChanged.connect(self.filter_commandes)
        filters_layout.addWidget(self.date_fin, 0, 3)
        
        # Recherche
        filters_layout.addWidget(QLabel("Recherche :"), 1, 0)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Chercher par client, produit, numéro commande...")
        self.search_input.textChanged.connect(self.filter_commandes)
        filters_layout.addWidget(self.search_input, 1, 1, 1, 2)
        
        # Filtre par statut paiement
        filters_layout.addWidget(QLabel("Paiement :"), 1, 3)
        self.payment_filter = QComboBox()
        self.payment_filter.addItems(["Tous", "Espèces", "Crédit", "Carte", "Mobile Money"])
        self.payment_filter.currentTextChanged.connect(self.filter_commandes)
        filters_layout.addWidget(self.payment_filter, 1, 4)
        
        # Boutons d'action
        actions_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.clicked.connect(self.load_commandes)
        refresh_btn.setStyleSheet("QPushButton { padding: 8px 15px; }")
        
        export_btn = QPushButton("📊 Exporter")
        export_btn.clicked.connect(self.export_commandes)
        export_btn.setStyleSheet("QPushButton { padding: 8px 15px; }")
        
        actions_layout.addWidget(refresh_btn)
        actions_layout.addWidget(export_btn)
        actions_layout.addStretch()
        
        filters_layout.addLayout(actions_layout, 2, 0, 1, 5)
        
        layout.addWidget(filters_group)
        
    def create_commandes_table(self, layout):
        """Créer le tableau des commandes"""
        self.commandes_table = QTableWidget()
        self.commandes_table.setColumnCount(9)
        self.commandes_table.setHorizontalHeaderLabels([
            "N° Commande", "Date", "Client", "Produits", "Quantité Tot.", 
            "Sous-total", "Remise", "Total", "Paiement"
        ])
        
        # Configuration du tableau
        header = self.commandes_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # N° Commande
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Date
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)           # Client
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)           # Produits
        
        self.commandes_table.setAlternatingRowColors(True)
        self.commandes_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.commandes_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                background-color: white;
                selection-background-color: #e3f2fd;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                font-weight: bold;
                border: 1px solid #ddd;
            }
        """)
        
        # Connecter les signaux
        self.commandes_table.doubleClicked.connect(self.on_commande_double_click)
        
        layout.addWidget(self.commandes_table)
        
    def create_statistics_section(self, layout):
        """Créer la section des statistiques détaillées"""
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        stats_layout = QHBoxLayout(stats_frame)
        
        # Statistiques de la période
        period_stats = QVBoxLayout()
        period_label = QLabel("📊 Statistiques de la période")
        period_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        period_stats.addWidget(period_label)
        
        self.stats_text = QLabel()
        self.stats_text.setStyleSheet("font-family: monospace; font-size: 11px;")
        self.update_period_stats()
        period_stats.addWidget(self.stats_text)
        
        stats_layout.addLayout(period_stats)
        stats_layout.addStretch()
        
        layout.addWidget(stats_frame)
        
    def load_commandes(self):
        """Charger les commandes depuis la base de données"""
        try:
            from ayanna_erp.database.database_manager import DatabaseManager
            from sqlalchemy import text
            
            db_manager = DatabaseManager()
            
            with db_manager.get_session() as session:
                # Requête pour récupérer les commandes avec détails
                query = text("""
                    SELECT 
                        sp.id,
                        sp.numero_commande,
                        sp.created_at,
                        COALESCE(sc.nom || ' ' || COALESCE(sc.prenom, ''), 'Client anonyme') as client_name,
                        sp.subtotal,
                        sp.remise_amount,
                        sp.total_final,
                        sp.payment_method,
                        sp.status,
                        GROUP_CONCAT(cp.name || ' (x' || spp.quantity || ')') as produits,
                        SUM(spp.quantity) as total_quantity
                    FROM shop_paniers sp
                    LEFT JOIN shop_clients sc ON sp.client_id = sc.id
                    LEFT JOIN shop_paniers_products spp ON sp.id = spp.panier_id
                    LEFT JOIN core_products cp ON spp.product_id = cp.id
                    WHERE sp.status = 'completed'
                    GROUP BY sp.id, sp.numero_commande, sp.created_at, sc.nom, sc.prenom, 
                             sp.subtotal, sp.remise_amount, sp.total_final, 
                             sp.payment_method, sp.status
                    ORDER BY sp.created_at DESC
                    LIMIT 100
                """)
                
                result = session.execute(query)
                commandes = result.fetchall()
                
                self.populate_table(commandes)
                self.update_statistics(commandes)
                
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des commandes: {e}")
            print(f"❌ Erreur load_commandes: {e}")
            
    def populate_table(self, commandes):
        """Remplir le tableau avec les commandes"""
        self.commandes_table.setRowCount(len(commandes))
        
        for row, commande in enumerate(commandes):
            # N° Commande
            self.commandes_table.setItem(row, 0, QTableWidgetItem(str(commande.numero_commande or f"CMD-{commande.id}")))
            
            # Date
            date_str = ""
            if commande.created_at:
                if isinstance(commande.created_at, str):
                    # Si c'est une chaîne, la parser
                    try:
                        from datetime import datetime
                        date_obj = datetime.strptime(commande.created_at[:19], "%Y-%m-%d %H:%M:%S")
                        date_str = date_obj.strftime("%d/%m/%Y %H:%M")
                    except:
                        date_str = commande.created_at[:16]  # Fallback
                else:
                    # Si c'est déjà un objet datetime
                    date_str = commande.created_at.strftime("%d/%m/%Y %H:%M")
            self.commandes_table.setItem(row, 1, QTableWidgetItem(date_str))
            
            # Client
            self.commandes_table.setItem(row, 2, QTableWidgetItem(str(commande.client_name)))
            
            # Produits
            produits_text = commande.produits or "Aucun produit"
            if len(produits_text) > 50:
                produits_text = produits_text[:47] + "..."
            self.commandes_table.setItem(row, 3, QTableWidgetItem(produits_text))
            
            # Quantité totale
            self.commandes_table.setItem(row, 4, QTableWidgetItem(str(commande.total_quantity or 0)))
            
            # Sous-total
            self.commandes_table.setItem(row, 5, QTableWidgetItem(f"{commande.subtotal:.0f} FC"))
            
            # Remise
            self.commandes_table.setItem(row, 6, QTableWidgetItem(f"{commande.remise_amount:.0f} FC"))
            
            # Total
            total_item = QTableWidgetItem(f"{commande.total_final:.0f} FC")
            if commande.payment_method == 'Crédit':
                total_item.setBackground(QColor("#ffecb3"))  # Jaune pour crédit
            self.commandes_table.setItem(row, 7, total_item)
            
            # Paiement
            payment_item = QTableWidgetItem(str(commande.payment_method))
            if commande.payment_method == 'Crédit':
                payment_item.setBackground(QColor("#ffcdd2"))  # Rouge pour crédit
            self.commandes_table.setItem(row, 8, payment_item)
            
    def update_statistics(self, commandes):
        """Mettre à jour les statistiques"""
        if not commandes:
            return
            
        total_ca = sum(c.total_final for c in commandes)
        total_creances = sum(c.total_final for c in commandes if c.payment_method == 'Crédit')
        
        # Calculer les commandes d'aujourd'hui
        commandes_aujourd_hui = 0
        today = datetime.now().date()
        
        for c in commandes:
            if c.created_at:
                try:
                    if isinstance(c.created_at, str):
                        # Parser la chaîne de date
                        date_obj = datetime.strptime(c.created_at[:19], "%Y-%m-%d %H:%M:%S")
                        if date_obj.date() == today:
                            commandes_aujourd_hui += 1
                    else:
                        # Objet datetime
                        if c.created_at.date() == today:
                            commandes_aujourd_hui += 1
                except:
                    pass  # Ignorer les dates mal formatées
        
        # Mise à jour des widgets de stats
        if hasattr(self, 'stat_widgets'):
            self.stat_widgets.get('commandes_aujourd\'hui', QLabel()).setText(str(commandes_aujourd_hui))
            self.stat_widgets.get('total_ca', QLabel()).setText(f"{total_ca:.0f} FC")
            self.stat_widgets.get('créances', QLabel()).setText(f"{total_creances:.0f} FC")
            
        self.update_period_stats(commandes)
        
    def update_period_stats(self, commandes=None):
        """Mettre à jour les statistiques de période"""
        if not commandes:
            stats_text = """
Période: Derniers 30 jours
Commandes: 0
Chiffre d'affaires: 0 FC
Créances: 0 FC
Panier moyen: 0 FC
            """
        else:
            nb_commandes = len(commandes)
            total_ca = sum(c.total_final for c in commandes)
            creances = sum(c.total_final for c in commandes if c.payment_method == 'Crédit')
            panier_moyen = total_ca / nb_commandes if nb_commandes > 0 else 0
            
            stats_text = f"""
Période: {self.date_debut.date().toString('dd/MM/yyyy')} - {self.date_fin.date().toString('dd/MM/yyyy')}
Commandes: {nb_commandes}
Chiffre d'affaires: {total_ca:.0f} FC
Créances: {creances:.0f} FC
Panier moyen: {panier_moyen:.0f} FC
            """
            
        self.stats_text.setText(stats_text.strip())
        
    def filter_commandes(self):
        """Filtrer les commandes selon les critères"""
        # TODO: Implémenter le filtrage en temps réel
        # Pour l'instant, on recharge tout
        self.load_commandes()
        
    def on_commande_double_click(self, index):
        """Gérer le double-clic sur une commande"""
        row = index.row()
        if row >= 0:
            commande_id = self.commandes_table.item(row, 0).text()
            # TODO: Ouvrir détail de la commande
            QMessageBox.information(self, "Détail commande", 
                                  f"Affichage du détail de la commande {commande_id}")
            
    def export_commandes(self):
        """Exporter les commandes"""
        # TODO: Implémenter l'export CSV/Excel
        QMessageBox.information(self, "Export", "Fonctionnalité d'export à implémenter")
        
    def refresh_data(self):
        """Actualiser les données (interface publique)"""
        self.load_commandes()