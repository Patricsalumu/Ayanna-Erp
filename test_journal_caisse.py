#!/usr/bin/env python3
"""
Script de test pour le nouveau Journal de Caisse
"""

import sys
import os
from datetime import datetime, date

# Ajouter les chemins nécessaires
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication, QMainWindow
from ayanna_erp.modules.salle_fete.view.entreSortie_index import EntreeSortieIndex

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test - Journal de Caisse")
        self.setGeometry(100, 100, 1200, 800)
        
        # Utilisateur de test
        current_user = {
            'id': 1,
            'name': 'Admin Test',
            'username': 'admin'
        }
        
        # Main controller simulé
        main_controller = None
        
        # Créer l'interface du journal
        self.journal_widget = EntreeSortieIndex(main_controller, current_user)
        self.setCentralWidget(self.journal_widget)

def main():
    app = QApplication(sys.argv)
    
    # Style de l'application
    app.setStyleSheet("""
        QMainWindow {
            background-color: #F8F9FA;
        }
        QWidget {
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11pt;
        }
    """)
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
