"""
Fenêtre du module Stock pour Ayanna ERP - Architecture Modulaire
Intégration du nouveau système de stock modulaire avec tous les widgets spécialisés
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QHBoxLayout, 
    QPushButton, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.stock.views.modular_stock_widget import ModularStockManagementWidget


class StockWindow(QMainWindow):
    """Fenêtre principale du module Stock - Architecture Modulaire"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.db_manager = DatabaseManager()
        
        self.setWindowTitle("Ayanna ERP - Gestion de Stock ")
        self.setMinimumSize(1200, 700)  # Taille augmentée pour le dashboard
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur avec système de scroll"""
        # Créer le widget central principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal pour le widget central
        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        
        # Créer le widget de contenu scrollable
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)
        
        # Créer la zone de scroll
        scroll_area = QScrollArea()
        scroll_area.setWidget(content_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #F8F9FA;
            }
            QScrollBar:vertical {
                background-color: #E9ECEF;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #6C757D;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #495057;
            }
            QScrollBar:horizontal {
                background-color: #E9ECEF;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: #6C757D;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #495057;
            }
        """)
        
        # Ajouter la zone de scroll au layout central
        central_layout.addWidget(scroll_area)
        
        # Interface principale de gestion des stocks - Architecture Modulaire (ONGLETS SEULEMENT)
        try:
            # Utiliser POS ID 1 par défaut, vous pouvez l'adapter selon vos besoins
            pos_id = 1
            self.stock_widget = ModularStockManagementWidget(pos_id, self.current_user)
            content_layout.addWidget(self.stock_widget)
            
            # Connecter les signaux pour la communication
            self.stock_widget.stock_updated.connect(self.on_stock_updated)
            
        except Exception as e:
            # En cas d'erreur, afficher un message d'erreur informatif
            error_label = QLabel(f"❌ Erreur lors du chargement de l'interface de stock modulaire:\n{str(e)}")
            error_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #E74C3C;
                    padding: 20px;
                    background-color: #FADBD8;
                    border-radius: 8px;
                    border: 1px solid #E74C3C;
                }
            """)
            error_label.setWordWrap(True)
            content_layout.addWidget(error_label)
            
            # Proposer une solution de base
            fallback_label = QLabel("💡 Vérifiez que les nouveaux contrôleurs modulaires sont correctement configurés.")
            fallback_label.setStyleSheet("font-size: 12px; color: #7F8C8D; padding: 10px;")
            content_layout.addWidget(fallback_label)
    
    # Nouveaux gestionnaires de signaux pour l'architecture modulaire
    def on_stock_updated(self):
        """Quand le stock est mis à jour"""
        print("📦 Stock mis à jour dans l'application principale")
        # Ici vous pouvez ajouter des actions globales quand le stock change

    
    def closeEvent(self, event):
        """Gestionnaire de fermeture de la fenêtre"""
        try:
            self.db_manager.close_session()
        except Exception:
            pass  # Ignorer les erreurs lors de la fermeture
        event.accept()
