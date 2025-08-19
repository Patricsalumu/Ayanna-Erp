#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test rapide de l'application - démarre et arrête automatiquement
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Ajouter le répertoire racine au PYTHONPATH
sys.path.insert(0, os.path.abspath('.'))

def test_application():
    """Test de démarrage de l'application"""
    try:
        # Import de l'application
        from main import main
        
        # Créer l'application Qt
        app = QApplication(sys.argv)
        
        # Timer pour fermer l'application après 3 secondes
        timer = QTimer()
        timer.timeout.connect(app.quit)
        timer.start(3000)  # 3 secondes
        
        print("🚀 Application en cours de démarrage...")
        print("   (fermeture automatique dans 3 secondes)")
        
        # Démarrer l'application
        main()
        
        print("✅ Application démarrée avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur de démarrage: {e}")
        return False

if __name__ == "__main__":
    success = test_application()
    if not success:
        sys.exit(1)
