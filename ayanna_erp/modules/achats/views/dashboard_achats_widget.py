"""
Widget dashboard pour le module Achats
Affiche les statistiques et indicateurs clés
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPainter, QPen
from decimal import Decimal
from datetime import datetime, timedelta

from ayanna_erp.modules.achats.controllers import AchatController
from ayanna_erp.modules.achats.models import EtatCommande


class StatCard(QFrame):
    """Widget pour afficher une statistique"""
    
    def __init__(self, title, value, icon="📊", color="#3498DB"):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 8px;
                padding: 10px;
            }}
            QLabel {{
                border: none;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Icône et valeur
        header_layout = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 24px; color: {color};")
        
        value_label = QLabel(str(value))
        value_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        header_layout.addWidget(icon_label)
        header_layout.addStretch()
        header_layout.addWidget(value_label)
        
        # Titre
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: #7F8C8D; font-weight: bold;")
        title_label.setWordWrap(True)
        
        layout.addLayout(header_layout)
        layout.addWidget(title_label)
        
        self.value_label = value_label
    
    def update_value(self, value):
        """Met à jour la valeur affichée"""
        self.value_label.setText(str(value))


class DashboardAchatsWidget(QWidget):
    """Widget dashboard principal pour les achats"""
    
    def __init__(self, achat_controller: AchatController):
        super().__init__()
        self.achat_controller = achat_controller
        
        self.setup_ui()
        self.refresh_data()
    
    def setup_ui(self):
        """Configuration de l'interface"""
        # Scroll area pour le contenu
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content_widget = QWidget()
        scroll.setWidget(content_widget)
        
        layout = QVBoxLayout(self)
        layout.addWidget(scroll)
        
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # Titre
        title_label = QLabel("📊 Dashboard Achats")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #2C3E50; margin-bottom: 20px;")
        content_layout.addWidget(title_label)
        
        # Cartes de statistiques
        stats_layout = QGridLayout()
        
        self.total_commandes_card = StatCard("Total Commandes", "0", "📋", "#3498DB")
        self.commandes_encours_card = StatCard("En Cours", "0", "⏳", "#F39C12")
        self.commandes_validees_card = StatCard("Validées", "0", "✅", "#27AE60")
        self.total_montant_card = StatCard("Montant Total", "0 €", "💰", "#9B59B6")
        
        stats_layout.addWidget(self.total_commandes_card, 0, 0)
        stats_layout.addWidget(self.commandes_encours_card, 0, 1)
        stats_layout.addWidget(self.commandes_validees_card, 0, 2)
        stats_layout.addWidget(self.total_montant_card, 0, 3)
        
        content_layout.addLayout(stats_layout)
        
        # Section des tables
        tables_layout = QHBoxLayout()
        
        # Commandes récentes
        recent_group = QGroupBox("Commandes Récentes")
        recent_layout = QVBoxLayout(recent_group)
        
        self.recent_table = QTableWidget()
        self.recent_table.setColumnCount(5)
        self.recent_table.setHorizontalHeaderLabels([
            "Numéro", "Fournisseur", "Date", "Montant", "État"
        ])
        
        # Configuration de la table
        header = self.recent_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        self.recent_table.setAlternatingRowColors(True)
        self.recent_table.setMaximumHeight(300)
        
        recent_layout.addWidget(self.recent_table)
        tables_layout.addWidget(recent_group, 2)
        
        # Top fournisseurs
        suppliers_group = QGroupBox("Top Fournisseurs")
        suppliers_layout = QVBoxLayout(suppliers_group)
        
        self.suppliers_table = QTableWidget()
        self.suppliers_table.setColumnCount(3)
        self.suppliers_table.setHorizontalHeaderLabels([
            "Fournisseur", "Commandes", "Montant Total"
        ])
        
        # Configuration de la table
        supplier_header = self.suppliers_table.horizontalHeader()
        supplier_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        supplier_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        supplier_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        self.suppliers_table.setAlternatingRowColors(True)
        self.suppliers_table.setMaximumHeight(300)
        
        suppliers_layout.addWidget(self.suppliers_table)
        tables_layout.addWidget(suppliers_group, 1)
        
        content_layout.addLayout(tables_layout)
        
        # Boutons d'action rapide
        actions_group = QGroupBox("Actions Rapides")
        actions_layout = QHBoxLayout(actions_group)
        
        new_order_btn = QPushButton("➕ Nouvelle Commande")
        new_order_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #219A52;
            }
        """)
        
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.clicked.connect(self.refresh_data)
        
        export_btn = QPushButton("📊 Exporter Rapport")
        
        actions_layout.addWidget(new_order_btn)
        actions_layout.addWidget(refresh_btn)
        actions_layout.addWidget(export_btn)
        actions_layout.addStretch()
        
        content_layout.addWidget(actions_group)
        
        # Espacement final
        content_layout.addStretch()
    
    def refresh_data(self):
        """Actualise toutes les données du dashboard"""
        try:
            session = self.achat_controller.db_manager.get_session()
            
            # Récupérer les commandes
            all_commandes = self.achat_controller.get_commandes(session, limit=1000)
            
            # Calculer les statistiques
            self.update_statistics(all_commandes)
            
            # Actualiser les tables
            self.update_recent_orders(all_commandes[:10])  # 10 plus récentes
            self.update_top_suppliers(session)
            
        except Exception as e:
            print(f"Erreur lors de l'actualisation du dashboard: {e}")
        finally:
            session.close()
    
    def update_statistics(self, commandes):
        """Met à jour les cartes de statistiques"""
        total_commandes = len(commandes)
        commandes_encours = sum(1 for cmd in commandes if cmd.etat == EtatCommande.ENCOURS)
        commandes_validees = sum(1 for cmd in commandes if cmd.etat == EtatCommande.VALIDE)
        
        # Calculer le montant total
        montant_total = sum(cmd.montant_total for cmd in commandes if cmd.montant_total)
        
        # Mettre à jour les cartes
        self.total_commandes_card.update_value(total_commandes)
        self.commandes_encours_card.update_value(commandes_encours)
        self.commandes_validees_card.update_value(commandes_validees)
        self.total_montant_card.update_value(f"{montant_total:.2f} €")
    
    def update_recent_orders(self, commandes):
        """Met à jour la table des commandes récentes"""
        self.recent_table.setRowCount(len(commandes))
        
        for row, commande in enumerate(commandes):
            # Numéro
            self.recent_table.setItem(row, 0, QTableWidgetItem(commande.numero))
            
            # Fournisseur
            fournisseur_nom = commande.fournisseur.nom if commande.fournisseur else "Aucun"
            self.recent_table.setItem(row, 1, QTableWidgetItem(fournisseur_nom))
            
            # Date
            date_str = commande.date_commande.strftime("%d/%m/%Y") if commande.date_commande else ""
            self.recent_table.setItem(row, 2, QTableWidgetItem(date_str))
            
            # Montant
            montant_str = f"{commande.montant_total:.2f} €"
            montant_item = QTableWidgetItem(montant_str)
            montant_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.recent_table.setItem(row, 3, montant_item)
            
            # État
            etat_item = QTableWidgetItem(commande.etat.value.title())
            if commande.etat == EtatCommande.ENCOURS:
                etat_item.setBackground(Qt.GlobalColor.yellow)
            elif commande.etat == EtatCommande.VALIDE:
                etat_item.setBackground(Qt.GlobalColor.green)
            elif commande.etat == EtatCommande.ANNULE:
                etat_item.setBackground(Qt.GlobalColor.red)
            self.recent_table.setItem(row, 4, etat_item)
    
    def update_top_suppliers(self, session):
        """Met à jour la table des top fournisseurs"""
        try:
            # Récupérer les fournisseurs avec leurs statistiques
            fournisseurs = self.achat_controller.get_fournisseurs(session)
            
            # Calculer les statistiques pour chaque fournisseur
            supplier_stats = []
            for fournisseur in fournisseurs:
                commandes_fournisseur = [cmd for cmd in fournisseur.commandes if cmd.etat == EtatCommande.VALIDE]
                nb_commandes = len(commandes_fournisseur)
                montant_total = sum(cmd.montant_total for cmd in commandes_fournisseur if cmd.montant_total)
                
                if nb_commandes > 0:  # Seulement les fournisseurs avec des commandes
                    supplier_stats.append({
                        'nom': fournisseur.nom,
                        'commandes': nb_commandes,
                        'montant': montant_total
                    })
            
            # Trier par montant total décroissant
            supplier_stats.sort(key=lambda x: x['montant'], reverse=True)
            
            # Limiter aux 10 premiers
            top_suppliers = supplier_stats[:10]
            
            # Remplir la table
            self.suppliers_table.setRowCount(len(top_suppliers))
            
            for row, stats in enumerate(top_suppliers):
                # Nom du fournisseur
                self.suppliers_table.setItem(row, 0, QTableWidgetItem(stats['nom']))
                
                # Nombre de commandes
                nb_item = QTableWidgetItem(str(stats['commandes']))
                nb_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.suppliers_table.setItem(row, 1, nb_item)
                
                # Montant total
                montant_item = QTableWidgetItem(f"{stats['montant']:.2f} €")
                montant_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.suppliers_table.setItem(row, 2, montant_item)
        
        except Exception as e:
            print(f"Erreur lors de la mise à jour des top fournisseurs: {e}")