"""
Dialogue "À propos" pour afficher les informations de version et les notes de version
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QScrollArea, QWidget, QTabWidget)
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt, QSize
from ayanna_erp.core.config import Config


class AboutDialog(QDialog):
    """Dialogue "À propos" avec informations de version et notes"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"À propos de {Config.APP_NAME}")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialiser l'interface utilisateur"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # En-tête avec titre et version
        header_layout = QHBoxLayout()
        
        # Titre
        title_label = QLabel(f"{Config.APP_NAME}")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        # Version
        version_label = QLabel(f"v{Config.APP_VERSION}")
        version_font = QFont()
        version_font.setPointSize(14)
        version_font.setItalic(True)
        version_label.setFont(version_font)
        version_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header_layout.addWidget(version_label)
        
        layout.addLayout(header_layout)
        
        # Séparateur
        separator = QLabel("-" * 50)
        layout.addWidget(separator)
        
        # Onglets
        tabs = QTabWidget()
        
        # Onglet: Version actuelle
        current_version_widget = self.create_current_version_tab()
        tabs.addTab(current_version_widget, "Version Actuelle")
        
        # Onglet: Historique
        history_widget = self.create_history_tab()
        tabs.addTab(history_widget, "Historique des versions")
        
        layout.addWidget(tabs)
        
        # Bouton Fermer
        close_button = QPushButton("Fermer")
        close_button.setMinimumWidth(100)
        close_button.clicked.connect(self.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
    
    def create_current_version_tab(self):
        """Créer l'onglet de la version actuelle"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Informations de la version actuelle
        current_version = Config.APP_VERSION
        version_info = Config.VERSION_NOTES.get(current_version, {})
        
        # Titre de la version
        title_label = QLabel(f"{Config.APP_NAME} {current_version}")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Date
        if version_info.get('date'):
            date_label = QLabel(f"📅 {version_info.get('date')}")
            layout.addWidget(date_label)
        
        # Titre des changements
        if version_info.get('titre'):
            titre_label = QLabel(f"<b>🎯 {version_info.get('titre')}</b>")
            layout.addWidget(titre_label)
        
        # Changements
        if version_info.get('changements'):
            layout.addWidget(QLabel("<b>Changements:</b>"))
            
            for change in version_info.get('changements', []):
                change_label = QLabel(f"  {change}")
                change_label.setWordWrap(True)
                layout.addWidget(change_label)
        
        layout.addStretch()
        return widget
    
    def create_history_tab(self):
        """Créer l'onglet historique des versions"""
        # Créer un scroll area pour l'historique
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Afficher toutes les versions
        for version in sorted(Config.VERSION_NOTES.keys(), reverse=True):
            version_info = Config.VERSION_NOTES.get(version, {})
            
            # Titre de la version
            version_title = QLabel(f"{Config.APP_NAME} {version}")
            version_title_font = QFont()
            version_title_font.setPointSize(11)
            version_title_font.setBold(True)
            version_title.setFont(version_title_font)
            layout.addWidget(version_title)
            
            # Date
            if version_info.get('date'):
                date_label = QLabel(f"  📅 {version_info.get('date')}")
                layout.addWidget(date_label)
            
            # Titre des changements
            if version_info.get('titre'):
                titre_label = QLabel(f"  {version_info.get('titre')}")
                titre_label.setStyleSheet("color: #1976D2; font-weight: bold;")
                layout.addWidget(titre_label)
            
            # Changements
            if version_info.get('changements'):
                for change in version_info.get('changements', []):
                    change_label = QLabel(f"    • {change}")
                    change_label.setWordWrap(True)
                    change_label.setStyleSheet("margin-left: 10px;")
                    layout.addWidget(change_label)
            
            layout.addSpacing(10)
        
        layout.addStretch()
        scroll_area.setWidget(container)
        return scroll_area
