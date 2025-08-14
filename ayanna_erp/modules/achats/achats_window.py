"""
Fenêtre du module Achats pour Ayanna ERP
"""

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel
from ayanna_erp.database.database_manager import DatabaseManager


class AchatsWindow(QMainWindow):
    """Fenêtre principale du module Achats"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.db_manager = DatabaseManager()
        
        self.setWindowTitle("Ayanna ERP - Achats")
        self.setMinimumSize(800, 600)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        title_label = QLabel("Module Achats")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2C3E50;")
        
        info_label = QLabel("Module en cours de développement...")
        info_label.setStyleSheet("font-size: 16px; color: #7F8C8D;")
        
        layout.addWidget(title_label)
        layout.addWidget(info_label)
    
    def closeEvent(self, event):
        self.db_manager.close_session()
        event.accept()
