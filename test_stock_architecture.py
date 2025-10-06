"""
Test de l'architecture modulaire du système de stock
Ce fichier permet de tester les widgets individuellement
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget, QMessageBox
from PyQt6.QtCore import Qt

# Ajouter le chemin racine au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ayanna_erp.database.database_manager import DatabaseManager


class StockModuleTestWindow(QMainWindow):
    """Fenêtre de test pour les widgets de stock"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧪 Test Architecture Modulaire - Gestion Stock")
        self.setGeometry(100, 100, 1200, 800)
        
        # Configuration test
        self.pos_id = 1  # ID de test
        self.current_user = {"id": 1, "name": "Test User"}
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configuration de l'interface de test"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Onglets pour chaque widget
        tabs = QTabWidget()
        
        try:
            # Test EntrepotWidget
            from ayanna_erp.modules.stock.views.entrepot_widget import EntrepotWidget
            entrepot_widget = EntrepotWidget(self.pos_id, self.current_user)
            tabs.addTab(entrepot_widget, "🏪 Entrepôts")
            print("✅ EntrepotWidget chargé avec succès")
            
        except Exception as e:
            print(f"❌ Erreur EntrepotWidget: {e}")
            tabs.addTab(QWidget(), "❌ Entrepôts (Erreur)")
        
        try:
            # Test StockWidget
            from ayanna_erp.modules.stock.views.stock_widget import StockWidget
            stock_widget = StockWidget(self.pos_id, self.current_user)
            tabs.addTab(stock_widget, "📦 Stocks")
            print("✅ StockWidget chargé avec succès")
            
        except Exception as e:
            print(f"❌ Erreur StockWidget: {e}")
            tabs.addTab(QWidget(), "❌ Stocks (Erreur)")
        
        try:
            # Test TransfertWidget
            from ayanna_erp.modules.stock.views.transfert_widget import TransfertWidget
            transfert_widget = TransfertWidget(self.pos_id, self.current_user)
            tabs.addTab(transfert_widget, "🔄 Transferts")
            print("✅ TransfertWidget chargé avec succès")
            
        except Exception as e:
            print(f"❌ Erreur TransfertWidget: {e}")
            tabs.addTab(QWidget(), "❌ Transferts (Erreur)")
        
        try:
            # Test AlerteWidget
            from ayanna_erp.modules.stock.views.alerte_widget import AlerteWidget
            alerte_widget = AlerteWidget(self.pos_id, self.current_user)
            tabs.addTab(alerte_widget, "🚨 Alertes")
            print("✅ AlerteWidget chargé avec succès")
            
        except Exception as e:
            print(f"❌ Erreur AlerteWidget: {e}")
            tabs.addTab(QWidget(), "❌ Alertes (Erreur)")
        
        try:
            # Test InventaireWidget
            from ayanna_erp.modules.stock.views.inventaire_widget import InventaireWidget
            inventaire_widget = InventaireWidget(self.pos_id, self.current_user)
            tabs.addTab(inventaire_widget, "📋 Inventaires")
            print("✅ InventaireWidget chargé avec succès")
            
        except Exception as e:
            print(f"❌ Erreur InventaireWidget: {e}")
            tabs.addTab(QWidget(), "❌ Inventaires (Erreur)")
        
        try:
            # Test RapportWidget
            from ayanna_erp.modules.stock.views.rapport_widget import RapportWidget
            rapport_widget = RapportWidget(self.pos_id, self.current_user)
            tabs.addTab(rapport_widget, "📊 Rapports")
            print("✅ RapportWidget chargé avec succès")
            
        except Exception as e:
            print(f"❌ Erreur RapportWidget: {e}")
            tabs.addTab(QWidget(), "❌ Rapports (Erreur)")
        
        try:
            # Test du Widget Principal Orchestrateur
            from ayanna_erp.modules.stock.views.modular_stock_widget import ModularStockManagementWidget
            modular_widget = ModularStockManagementWidget(self.pos_id, self.current_user)
            tabs.addTab(modular_widget, "🏭 WIDGET PRINCIPAL")
            print("✅ ModularStockManagementWidget chargé avec succès")
            
        except Exception as e:
            print(f"❌ Erreur ModularStockManagementWidget: {e}")
            tabs.addTab(QWidget(), "❌ Widget Principal (Erreur)")
        
        layout.addWidget(tabs)
        
        # Test des contrôleurs
        self.test_controllers()
    
    def test_controllers(self):
        """Tester l'importation des contrôleurs"""
        print("\n🔧 Test des Contrôleurs:")
        
        controllers = [
            ("EntrepotController", "ayanna_erp.modules.stock.controllers.entrepot_controller"),
            ("StockController", "ayanna_erp.modules.stock.controllers.stock_controller"),
            ("TransfertController", "ayanna_erp.modules.stock.controllers.transfert_controller"),
            ("AlerteController", "ayanna_erp.modules.stock.controllers.alerte_controller"),
            ("InventaireController", "ayanna_erp.modules.stock.controllers.inventaire_controller"),
            ("RapportController", "ayanna_erp.modules.stock.controllers.rapport_controller")
        ]
        
        for class_name, module_path in controllers:
            try:
                module = __import__(module_path, fromlist=[class_name])
                controller_class = getattr(module, class_name)
                controller = controller_class(self.pos_id)
                print(f"✅ {class_name} initialisé avec succès")
                
            except Exception as e:
                print(f"❌ Erreur {class_name}: {e}")


def main():
    """Fonction principale de test"""
    print("🚀 Démarrage du test de l'architecture modulaire Stock...")
    print("=" * 60)
    
    # Vérifier la base de données
    try:
        db_manager = DatabaseManager()
        with db_manager.get_session() as session:
            print("✅ Connexion à la base de données réussie")
    except Exception as e:
        print(f"❌ Erreur de connexion à la base de données: {e}")
        return
    
    # Créer l'application Qt
    app = QApplication(sys.argv)
    
    # Créer la fenêtre de test
    window = StockModuleTestWindow()
    window.show()
    
    print("\n🎯 Test terminé. Interface lancée!")
    print("=" * 60)
    print("Instructions:")
    print("- Chaque onglet représente un widget modulaire")
    print("- Les onglets avec ❌ indiquent des erreurs d'importation")
    print("- Testez les fonctionnalités de chaque widget")
    print("- Vérifiez que les signaux PyQt6 fonctionnent")
    print("- Fermez la fenêtre pour terminer le test")
    
    # Exécuter l'application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()