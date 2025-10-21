"""
Widget pour l'affichage et la gestion des commandes du module Boutique
Vue uniquement - la logique métier est gérée par CommandeController
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                            QTableWidgetItem, QPushButton, QLabel, QDateEdit, 
                            QLineEdit, QComboBox, QGroupBox, QGridLayout,
                            QHeaderView, QFrame, QSplitter, QMessageBox)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
from datetime import datetime, timedelta
from decimal import Decimal
from ayanna_erp.modules.boutique.controller.commande_controller import CommandeController

class CommandesIndexWidget(QWidget):
    """Widget principal pour l'affichage et gestion des commandes"""
    
    # Signaux
    commande_selected = pyqtSignal(int)  # ID de la commande sélectionnée
    
    def __init__(self, boutique_controller, current_user, parent=None):
        super().__init__(parent)
        self.boutique_controller = boutique_controller
        self.current_user = current_user
        self.parent_window = parent
        
        # Initialiser le contrôleur des commandes
        self.commande_controller = CommandeController()
        
        self.init_ui()
        self.load_commandes()
        
    def init_ui(self):
        """Initialisation de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)
        
        # Zone de filtres et recherche
        self.create_filters_section(layout)
        
        # Tableau des commandes
        self.create_commandes_table(layout)
        
        # Zone de statistiques (texte formaté)
        period_stats = QHBoxLayout()
        period_label = QLabel("📊 Statistiques de la période")
        period_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        period_stats.addWidget(period_label)

        self.stats_text = QLabel()
        self.stats_text.setStyleSheet("font-family: monospace; font-size: 11px;")
        # initialisation du texte de stats
        try:
            self.update_period_stats()
        except Exception:
            pass
        period_stats.addWidget(self.stats_text)
        period_stats.addStretch()
        layout.addLayout(period_stats)

        
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
            "N° Commande", "Date", "Client", "Produits / Services", "Quantité Tot.", 
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
        
    def load_commandes(self):
        """Charger les commandes depuis le contrôleur"""
        try:
            # Récupérer les filtres actuels
            date_debut = self.date_debut.date().toPyDate() if hasattr(self, 'date_debut') else None
            date_fin = self.date_fin.date().toPyDate() if hasattr(self, 'date_fin') else None
            search_term = self.search_input.text().strip() if hasattr(self, 'search_input') and self.search_input.text().strip() else None
            payment_filter = self.payment_filter.currentText() if hasattr(self, 'payment_filter') else None
            
            # Utiliser le contrôleur pour récupérer les commandes
            commandes = self.commande_controller.get_commandes(
                date_debut=date_debut,
                date_fin=date_fin,
                search_term=search_term,
                payment_filter=payment_filter
            )
            
            self.populate_table(commandes)
            self.update_statistics(commandes)
            
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des commandes: {e}")
            print(f"❌ Erreur load_commandes: {e}")
                
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des commandes: {e}")
            print(f"❌ Erreur load_commandes: {e}")
            
    def populate_table(self, commandes):
        """Remplir le tableau avec les commandes"""
        self.commandes_table.setRowCount(len(commandes))
        
        for row, commande in enumerate(commandes):
            # N° Commande
            self.commandes_table.setItem(row, 0, QTableWidgetItem(str(commande.get('numero_commande') or f"CMD-{commande.get('id')}")))

            # Date
            date_str = ""
            created_at = commande.get('created_at')
            if created_at:
                if isinstance(created_at, str):
                    try:
                        from datetime import datetime
                        date_obj = datetime.strptime(created_at[:19], "%Y-%m-%d %H:%M:%S")
                        date_str = date_obj.strftime("%d/%m/%Y %H:%M")
                    except:
                        date_str = created_at[:16]
                else:
                    date_str = created_at.strftime("%d/%m/%Y %H:%M")
            self.commandes_table.setItem(row, 1, QTableWidgetItem(date_str))

            # Client
            self.commandes_table.setItem(row, 2, QTableWidgetItem(str(commande.get('client_name', ''))))

            # Produits et services (déjà concaténés dans commande['produits'])
            items_text = commande.get('produits', 'Aucun produit/service')
            if len(items_text) > 100:
                items_text = items_text[:97] + '...'
            self.commandes_table.setItem(row, 3, QTableWidgetItem(items_text))

            # Quantité totale
            self.commandes_table.setItem(row, 4, QTableWidgetItem(str(commande.get('total_quantity') or 0)))

            # Sous-total
            self.commandes_table.setItem(row, 5, QTableWidgetItem(f"{commande.get('subtotal', 0):.0f} FC"))

            # Remise
            self.commandes_table.setItem(row, 6, QTableWidgetItem(f"{commande.get('remise_amount', 0):.0f} FC"))

            # Total
            total_item = QTableWidgetItem(f"{commande.get('total_final', 0):.0f} FC")
            if commande.get('payment_method') == 'Crédit':
                total_item.setBackground(QColor("#ffecb3"))
            self.commandes_table.setItem(row, 7, total_item)

            # Paiement
            payment_item = QTableWidgetItem(str(commande.get('payment_method', '')))
            if commande.get('payment_method') == 'Crédit':
                payment_item.setBackground(QColor("#ffcdd2"))
            self.commandes_table.setItem(row, 8, payment_item)
            
    def update_statistics(self, commandes):
        """Mettre à jour les statistiques"""
        if not commandes:
            return
            
        # Utiliser le contrôleur pour calculer les statistiques
        stats = self.commande_controller.get_commandes_statistics(commandes)
        
        # Mise à jour des widgets de stats
        if hasattr(self, 'stat_widgets'):
            self.stat_widgets.get('commandes_aujourd\'hui', QLabel()).setText(str(stats['commandes_aujourd_hui']))
            self.stat_widgets.get('total_ca', QLabel()).setText(f"{stats['total_ca']:.0f} FC")
            self.stat_widgets.get('créances', QLabel()).setText(f"{stats['total_creances']:.0f} FC")
            
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
            # Utiliser le contrôleur pour formater les statistiques
            stats = self.commande_controller.get_commandes_statistics(commandes)
            stats_text = self.commande_controller.format_period_stats(
                stats, self.date_debut.date(), self.date_fin.date()
            )
            
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
        try:
            # Récupérer les commandes actuelles (avec filtres appliqués)
            date_debut = self.date_debut.date().toPyDate() if hasattr(self, 'date_debut') else None
            date_fin = self.date_fin.date().toPyDate() if hasattr(self, 'date_fin') else None
            search_term = self.search_input.text().strip() if hasattr(self, 'search_input') and self.search_input.text().strip() else None
            payment_filter = self.payment_filter.currentText() if hasattr(self, 'payment_filter') else None
            
            commandes = self.commande_controller.get_commandes(
                date_debut=date_debut,
                date_fin=date_fin,
                search_term=search_term,
                payment_filter=payment_filter,
                limit=1000  # Plus de données pour l'export
            )
            
            # Utiliser le contrôleur pour l'export
            result = self.commande_controller.export_commandes(commandes, 'csv')
            QMessageBox.information(self, "Export", result)
            
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de l'export: {e}")
            print(f"❌ Erreur export_commandes: {e}")
        
    def refresh_data(self):
        """Actualiser les données (interface publique)"""
        self.load_commandes()