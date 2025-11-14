"""
Fenêtre principale du module Boutique pour Ayanna ERP
Gestionnaire des onglets - chaque onglet est dans son propre fichier
Architecture MVC avec contrôleurs pour la gestion de la base de données
"""


from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTabWidget, QMessageBox, QProgressDialog)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

# Import du contrôleur principal
from ..controller.boutique_controller import BoutiqueController

# Import des différents onglets
from .modern_supermarket_widget import ModernSupermarketWidget
from .produit_index import ProduitIndex
from modules.salle_fete.view.service_index import ServiceIndex
from modules.salle_fete.view.entreSortie_index import EntreeSortieIndex
from .categorie_index import CategorieIndex
from .client_index import ClientIndex
from .commandes_index import CommandesIndexWidget


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
        
        self.setWindowTitle("Ayanna ERP - Vente")
        self.setMinimumSize(1200, 700)
        
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
                padding: 10px 6px;
                margin-right: 2px;
                font-weight: bold;
                color: #2C3E50;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background-color: #2196F3;
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
            # Onglet Vente - Interface moderne type supermarché
            self.modern_shop_widget = ModernSupermarketWidget(
                self.boutique_controller, 
                self.current_user, 
                self.pos_id
            )
            self.tab_widget.addTab(self.modern_shop_widget, "🛒 Vente")
            
            # Connecter les signaux de la nouvelle interface
            self.modern_shop_widget.product_added_to_cart.connect(self.on_product_added_to_cart)
            self.modern_shop_widget.cart_updated.connect(self.on_cart_updated)
            self.modern_shop_widget.sale_completed.connect(self.on_sale_completed)
            
            # Onglet Commandes - Suivi et gestion des commandes
            self.commandes_widget = CommandesIndexWidget(self.boutique_controller, self.current_user, module='boutique')
            self.tab_widget.addTab(self.commandes_widget, "📋 Commandes")
            
            # Onglet Catégories - Gestion des catégories
            self.categories_widget = CategorieIndex(self.boutique_controller.pos_id, self.current_user)
            self.tab_widget.addTab(self.categories_widget, "📂 Catégories")

            # Onglet Produits - Gestion des produits
            pos_id = getattr(self.boutique_controller, 'pos_id', 1)
            self.produits_widget = ProduitIndex(pos_id, self.current_user)
            self.tab_widget.addTab(self.produits_widget, "📦 Produits")
            
            # Onglet Produits - Gestion des produits
            pos_id = getattr(self.boutique_controller, 'pos_id', 1)
            self.services_widget = ServiceIndex(pos_id, self.current_user)
            self.tab_widget.addTab(self.services_widget, "🔧 Services")

            # Onglet Clients - Gestion des clients
            self.clients_widget = ClientIndex(self.boutique_controller, self.current_user)
            self.tab_widget.addTab(self.clients_widget, "👥 Clients")
            
            # Onglet Clients - Gestion des clients
            self.caisse_widget = EntreeSortieIndex(self.boutique_controller, self.current_user)
            self.tab_widget.addTab(self.caisse_widget, "📥📤 Caisse")

            # # Onglet Rapports - Analyses et rapports
            # self.rapports_widget = RapportIndexWidget(self)
            # self.tab_widget.addTab(self.rapports_widget, "📈 Rapports")

            # Définir l'onglet par défaut (Vente)
            self.tab_widget.setCurrentIndex(0)
            
            print("✅ Interface moderne de boutique créée avec succès")
            print("🗑️ Onglet Stock supprimé - onglet Produits conservé avec onglet Commandes ajouté")
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'initialisation", 
                               f"Erreur lors de la création de l'interface: {str(e)}")
            print(f"❌ Erreur lors de la création de l'interface: {e}")
    
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
        # Actualiser l'affichage des produits
        if hasattr(self, 'produits_widget'):
            self.produits_widget.refresh_product(product_id)
        
        # Actualiser l'onglet Commandes pour refléter les changements de stock
        if hasattr(self, 'commandes_widget'):
            self.commandes_widget.refresh_data()
            print(f"📋 Onglet Commandes actualisé après mise à jour stock produit {product_id}")
    
    def on_product_selected_from_catalog(self, product_id: int, quantity: int = 1):
        """Callback quand un produit est sélectionné depuis le catalogue (ancien système)"""
        # Rediriger vers la nouvelle interface si elle existe
        if hasattr(self, 'modern_shop_widget'):
            # La nouvelle interface gère directement l'ajout au panier
            pass
        elif hasattr(self, 'panier_widget'):
            self.panier_widget.add_product_to_panier(product_id, quantity)
    
    def on_product_added_to_cart(self, product_id: int, quantity: int):
        """Callback pour le nouveau système moderne"""
        print(f"Produit {product_id} ajouté au panier (quantité: {quantity})")
        # Émettre signal vers l'application principale si nécessaire
        self.product_added.emit(product_id)
    
    def on_cart_updated(self):
        """Callback quand le panier est mis à jour (nouveau système)"""
        print("Panier mis à jour")
        self.panier_updated.emit()
    
    def on_sale_completed(self, sale_id: int):
        """Callback quand une vente est complétée"""
        print(f"Vente {sale_id} complétée avec succès")
        
        # Actualiser les rapports
        if hasattr(self, 'rapports_widget'):
            self.rapports_widget.refresh_data()
            
        # Actualiser l'onglet Commandes
        if hasattr(self, 'commandes_widget'):
            self.commandes_widget.refresh_data()
            print("📋 Onglet Commandes actualisé après vente")
    
    def switch_to_panier_tab(self):
        """Basculer vers l'onglet vente (moderne)"""
        self.tab_widget.setCurrentIndex(0)
    
    def switch_to_commandes_tab(self):
        """Basculer vers l'onglet commandes"""
        if hasattr(self, 'commandes_widget'):
            index = self.tab_widget.indexOf(self.commandes_widget)
            if index >= 0:
                self.tab_widget.setCurrentIndex(index)
    
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