"""
Widget dashboard pour le module Achats
Affiche les statistiques et indicateurs clés
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QFrame, QScrollArea, QSizePolicy
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
        # Style plus compact pour permettre d'afficher 6 cartes sur une ligne
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid {color};
                border-radius: 6px;
                padding: 6px;
            }}
            QLabel {{
                border: none;
            }}
        """)

        layout = QVBoxLayout(self)
        # Marges plus petites
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Icône et valeur
        header_layout = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 20px; color: {color};")

        value_label = QLabel(str(value))
        # Taille de police réduite pour compacité
        value_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        header_layout.addWidget(icon_label)
        header_layout.addStretch()
        header_layout.addWidget(value_label)

        # Titre
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 11px; color: #7F8C8D; font-weight: bold;")
        title_label.setWordWrap(True)
        
        layout.addLayout(header_layout)
        layout.addWidget(title_label)
        
        self.value_label = value_label
        # Taille compacte: permettre au layout de compresser si nécessaire
        try:
            # hauteur maximale compacte
            self.setMaximumHeight(80)
            # laisser la largeur flexible pour tenir 6 cartes sur une ligne
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        except Exception:
            pass
    
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
        # Autoriser le défilement horizontal si le contenu dépasse la largeur
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        content_widget = QWidget()
        scroll.setWidget(content_widget)
        
        layout = QVBoxLayout(self)
        layout.addWidget(scroll)
        
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # Titre
        title_row = QHBoxLayout()
        title_label = QLabel("📊 Dashboard Achats")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #2C3E50; margin-bottom: 20px;")
        title_row.addWidget(title_label)
        title_row.addStretch()
        # Bouton rafraîchir
        refresh_btn = QPushButton("🔄 Rafraîchir")
        refresh_btn.setToolTip("Rafraîchir les indicateurs")
        refresh_btn.clicked.connect(self.refresh_data)
        title_row.addWidget(refresh_btn)
        content_layout.addLayout(title_row)

        # Cartes de statistiques
        # Utiliser une QHBoxLayout pour forcer une seule ligne et permettre
        # aux cartes d'adapter leur largeur (shrinking) si nécessaire.
        stats_layout = QHBoxLayout()
        # Espacements réduits pour compacité et pour tenir 6 cartes sur une ligne
        stats_layout.setSpacing(6)
        stats_layout.setContentsMargins(0, 0, 0, 0)

        self.total_commandes_card = StatCard("Total Commandes", "0", "📋", "#3498DB")
        self.commandes_encours_card = StatCard("En Cours", "0", "⏳", "#F39C12")
        self.commandes_validees_card = StatCard("Validées", "0", "✅", "#27AE60")
        # Remplacer 'Montant Total' par 'Total Payés' (somme des AchatDepense)
        self.total_payes_card = StatCard("Total Payés", "0 €", "💰", "#9B59B6")
        # Nouvelle carte: Montant non payé (somme des commandes non annulées - total payé)
        self.total_non_payes_card = StatCard("Montant non payé", "0 €", "❗", "#E74C3C")
        # Nouvelle carte: nombre de commandes non payées (count)
        self.commandes_non_payees_card = StatCard("Commandes non payées", "0", "🧾", "#8E44AD")

        # Placer les 6 cartes sur la même ligne (QHBoxLayout gère l'alignement)
        stats_layout.addWidget(self.total_commandes_card)
        stats_layout.addWidget(self.commandes_encours_card)
        stats_layout.addWidget(self.commandes_validees_card)
        stats_layout.addWidget(self.total_payes_card)
        stats_layout.addWidget(self.total_non_payes_card)
        stats_layout.addWidget(self.commandes_non_payees_card)

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
        # Calculer le total payé (somme de toutes les dépenses liées aux commandes)
        try:
            total_payes = sum((sum(d.montant for d in cmd.depenses) if cmd.depenses else 0) for cmd in commandes)
        except Exception:
            total_payes = Decimal('0')

        # Somme des montants des commandes non annulées
        total_non_annule = sum(cmd.montant_total for cmd in commandes if cmd.etat != EtatCommande.ANNULE and cmd.montant_total)

        # Montant non payé = total des commandes non annulées - total payé
        try:
            total_non_payes = Decimal(total_non_annule) - Decimal(total_payes)
        except Exception:
            total_non_payes = Decimal('0')

        # Nombre de commandes non payées (commande où total payé < montant_total et non annulée)
        commandes_non_payees_count = 0
        for cmd in commandes:
            if cmd.etat == EtatCommande.ANNULE:
                continue
            try:
                paid = sum(d.montant for d in cmd.depenses) if cmd.depenses else Decimal('0')
            except Exception:
                paid = Decimal('0')
            if paid < (cmd.montant_total or Decimal('0')):
                commandes_non_payees_count += 1

        # Mettre à jour les cartes
        self.total_commandes_card.update_value(total_commandes)
        self.commandes_encours_card.update_value(commandes_encours)
        self.commandes_validees_card.update_value(commandes_validees)
        self.total_payes_card.update_value(f"{Decimal(total_payes):.2f} €")
        self.total_non_payes_card.update_value(f"{Decimal(total_non_payes):.2f} €")
        self.commandes_non_payees_card.update_value(str(commandes_non_payees_count))
    
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