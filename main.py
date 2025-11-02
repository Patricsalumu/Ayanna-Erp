#!/usr/bin/env python3
"""
Ayanna ERP - Système de Gestion Intégré
Point d'entrée principal de l'application
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire du projet au PYTHONPATH
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Si un environnement virtuel existe, l'utiliser
venv_site_packages = project_root / "venv" / "lib"
if venv_site_packages.exists():
    for site_pkg in venv_site_packages.glob("python*/site-packages"):
        sys.path.insert(0, str(site_pkg))

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QIcon
    from ayanna_erp.database.database_manager import DatabaseManager
    from ayanna_erp.ui.login_window import LoginWindow
    from ayanna_erp.core.config import Config
except ImportError as e:
    print(f"❌ Erreur d'importation: {e}")
    print("\n🔧 Solutions possibles:")
    print("1. Exécutez d'abord: ./run.sh install")
    print("2. Ou installez manuellement: python -m pip install PyQt6 SQLAlchemy")
    print("3. Si vous utilisez un système avec environnements gérés:")
    print("   - Créez un environnement virtuel: python -m venv venv")
    print("   - Activez-le: source venv/bin/activate")
    print("   - Installez les dépendances: pip install -r requirements.txt")
    sys.exit(1)


def main():
    """Point d'entrée principal de l'application Ayanna ERP"""
    
    # Créer l'application Qt
    app = QApplication(sys.argv)
    app.setApplicationName("Ayanna ERP")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Ayanna Solutions")
    
    # Configurer le style de l'application
    app.setStyle('Fusion')
    # Définir l'icône de l'application et de la fenêtre (préfère .ico, fallback png)
    icon_path = os.path.join(str(project_root), 'data', 'images', 'icone_ayanna_erp.ico')
    if not os.path.exists(icon_path):
        icon_path = os.path.join(str(project_root), 'data', 'images', 'icone_ayanna_erp.png')
    if os.path.exists(icon_path):
        try:
            app.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"Avertissement: impossible de définir l'icône de l'application: {e}")
    
    # Initialiser la base de données
    db_manager = DatabaseManager()
    if not db_manager.initialize_database():
        print("Erreur lors de l'initialisation de la base de données")
        sys.exit(1)
    
    # Créer et afficher la fenêtre de connexion
    login_window = LoginWindow()
    # Appliquer l'icône à la fenêtre de connexion si disponible
    try:
        if 'icon_path' in locals() and os.path.exists(icon_path):
            login_window.setWindowIcon(QIcon(icon_path))
    except Exception:
        pass
    login_window.show()
    
    # Démarrer la boucle d'événements
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
