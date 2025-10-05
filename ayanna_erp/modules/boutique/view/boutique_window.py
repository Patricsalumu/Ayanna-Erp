"""
Fenêtre principale du module Boutique pour Ayanna ERP
Gestionnaire des onglets - chaque onglet est dans son propre fichier
Architecture MVC avec contrôleurs pour la gestion de la base de données
"""

import sys
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTabWidget, QMessageBox, QProgressDialog)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon

# Import du contrôleur principal
from ..controller.boutique_controller import BoutiqueController

# Import des différents onglets
from .panier_index import PanierIndex
from .produit_index import ProduitIndex
from .categorie_index import CategorieIndex
from .client_index import ClientIndex
from .stock_index import StockIndex
from .rapport_index import RapportIndexWidget


class BoutiqueWindow(QMainWindow):
    """Fenêtre principale du module Boutique"""
    
    # Signaux pour la communication entre composants
    panier_updated = pyqtSignal()
    product_added = pyqtSignal(int)  # ID du produit ajouté
    
    def __init__(self, current_user, pos_id=1):
        super().__init__()
        self.current_user = current_user
        self.pos_id = pos_id

        # Initialiser le contrôleur principal
        self.boutique_controller = BoutiqueController(self.pos_id)

        # Connecter les signaux du contrôleur
        self.boutique_controller.panier_updated.connect(self.on_panier_updated)
        self.boutique_controller.payment_completed.connect(self.on_payment_completed)
        self.boutique_controller.stock_updated.connect(self.on_stock_updated)
        
        self.setWindowTitle("Ayanna ERP - Boutique")
        self.setMinimumSize(1400, 800)
        
        # Indicateur d'initialisation
        self.is_initialized = False
        self.tabs_created = False

        self.setup_ui()
        
        # Lancer l'initialisation
        QTimer.singleShot(500, self.initialize_module)
    
    def initialize_module(self):
        """Initialiser le module Boutique"""
        if not self.is_initialized:
            print("🏪 Lancement de l'initialisation du module Boutique...")
            self.setup_tabs()
            self.is_initialized = True
            self.tabs_created = True
            print("✅ Module Boutique initialisé avec succès")
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal avec onglets
        main_layout = QVBoxLayout(central_widget)
        
        # Widget à onglets
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #BDC3C7;
                background-color: white;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #ECF0F1;
                padding: 12px 24px;
                margin-right: 2px;
                font-weight: bold;
                color: #2C3E50;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background-color: #27AE60;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #D5DBDB;
            }
            QTabWidget::tab-bar {
                alignment: left;
            }
        """)
        
        main_layout.addWidget(self.tab_widget)
    
    def setup_tabs(self):
        """Configuration de tous les onglets avec les contrôleurs"""
        
        try:
            # Onglet Panier - Vue principale de vente
            self.panier_widget = PanierIndex(self.boutique_controller, self.current_user)
            self.tab_widget.addTab(self.panier_widget, "🛒 Panier")
            
            # Connecter le signal d'ajout de produit
            self.panier_widget.product_selected.connect(self.on_product_selected_from_catalog)
            
            # Onglet Produits - Gestion des produits
            pos_id = getattr(self.boutique_controller, 'pos_id', 1)
            self.produits_widget = ProduitIndex(pos_id, self.current_user)
            self.tab_widget.addTab(self.produits_widget, "📦 Produits")
            
            # Onglet Catégories - Gestion des catégories
            self.categories_widget = CategorieIndex(self.boutique_controller.pos_id, self.current_user)
            self.tab_widget.addTab(self.categories_widget, "📂 Catégories")
            
            # Onglet Clients - Gestion des clients
            self.clients_widget = ClientIndex(self.boutique_controller, self.current_user)
            self.tab_widget.addTab(self.clients_widget, "👥 Clients")
            
            # Onglet Stock - Entrées/Sorties et gestion du stock
            self.stock_widget = StockIndex(self.boutique_controller, self.current_user)
            self.tab_widget.addTab(self.stock_widget, "📊 Stock")
            
            # Onglet Rapports - Analyses et rapports
            self.rapports_widget = RapportIndexWidget(self)
            self.tab_widget.addTab(self.rapports_widget, "📈 Rapports")
            
            # Définir l'onglet par défaut (Panier)
            self.tab_widget.setCurrentIndex(0)
            
            print("✅ Tous les onglets de la boutique créés avec leurs contrôleurs")
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'initialisation", 
                               f"Erreur lors de la création des onglets: {str(e)}")
            print(f"❌ Erreur lors de la création des onglets: {e}")
    
    def on_panier_updated(self):
        """Callback quand le panier est mis à jour"""
        # Actualiser l'affichage du panier
        if hasattr(self, 'panier_widget'):
            self.panier_widget.refresh_panier()
        
        # Émettre le signal pour d'autres composants
        self.panier_updated.emit()
    
    def on_payment_completed(self, payment_id: int):
        """Callback quand un paiement est terminé"""
        QMessageBox.information(self, "Paiement réussi", 
                              f"Paiement #{payment_id} effectué avec succès!")
        
        # Actualiser les rapports si l'onglet est ouvert
        if hasattr(self, 'rapports_widget'):
            self.rapports_widget.refresh_data()
    
    def on_stock_updated(self, product_id: int):
        """Callback quand le stock est mis à jour"""
        # Actualiser l'affichage du stock
        if hasattr(self, 'stock_widget'):
            self.stock_widget.refresh_product_stock(product_id)
        
        # Actualiser les produits si nécessaire
        if hasattr(self, 'produits_widget'):
            self.produits_widget.refresh_product(product_id)
    
    def on_product_selected_from_catalog(self, product_id: int, quantity: int = 1):
        """Callback quand un produit est sélectionné depuis le catalogue"""
        # Ajouter le produit au panier
        if hasattr(self, 'panier_widget'):
            self.panier_widget.add_product_to_panier(product_id, quantity)
    
    def switch_to_panier_tab(self):
        """Basculer vers l'onglet panier"""
        self.tab_widget.setCurrentIndex(0)
    
    def switch_to_products_tab(self):
        """Basculer vers l'onglet produits"""
        if hasattr(self, 'produits_widget'):
            index = self.tab_widget.indexOf(self.produits_widget)
            if index >= 0:
                self.tab_widget.setCurrentIndex(index)
    
    def get_current_user(self):
        """Retourner l'utilisateur actuel"""
        return self.current_user
    
    def get_pos_id(self):
        """Retourner l'ID du point de vente"""
        return self.pos_id
    
    def closeEvent(self, event):
        """Gérer la fermeture de la fenêtre"""
        try:
            # Vérifier s'il y a un panier ouvert
            from ayanna_erp.database.database_manager import DatabaseManager
            db_manager = DatabaseManager()
            
            with db_manager.get_session() as session:
                panier_content = self.boutique_controller.get_panier_content(session)
                
                if (panier_content.get("panier") and 
                    (panier_content.get("products") or panier_content.get("services"))):
                    
                    reply = QMessageBox.question(
                        self, "Panier ouvert", 
                        "Vous avez un panier ouvert avec des articles. Voulez-vous vraiment fermer ?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    
                    if reply == QMessageBox.StandardButton.No:
                        event.ignore()
                        return
            
            # Nettoyer les ressources
            if hasattr(self, 'boutique_controller'):
                # Déconnecter les signaux
                self.boutique_controller.panier_updated.disconnect()
                self.boutique_controller.payment_completed.disconnect()
                self.boutique_controller.stock_updated.disconnect()
            
            print("🧹 Ressources de la boutique nettoyées")
            
        except Exception as e:
            print(f"⚠️ Erreur lors du nettoyage de la boutique: {e}")
        finally:
            event.accept()