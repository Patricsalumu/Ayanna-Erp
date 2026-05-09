#!/usr/bin/env python3
"""
Ayanna ERP - Système de Gestion Intégré
Point d'entrée principal de l'application
"""

import sys
import os
import time
from pathlib import Path

# Ajouter le répertoire du projet au PYTHONPATH
project_root = Path(__file__).parent.absolute()
# --- Startup timing helper (writes to startup_times.txt in project root) ---
START_TIME = time.time()
def _log(stage: str):
    try:
        p = project_root / 'startup_times.txt'
        with open(p, 'a', encoding='utf-8') as f:
            f.write(f"{stage}: {time.time() - START_TIME:.3f}s\n")
    except Exception:
        pass

_log('script_start')
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
    # service de licence (import tardif possible)
    from ayanna_erp.core.services.licence_service import verifier_licence
    from ayanna_erp.core.view.licence_dialog import LicenceActivationDialog
    _log('after_imports')
except ImportError as e:
    print(f"❌ Erreur d'importation: {e}")
    print("\n🔧 Solutions possibles:")
    print("1. Exécutez d'abord: ./run.sh install")
    print("2. Ou installez manuellement: python -m pip install PyQt6 SQLAlchemy")
    print("3. Si vous utilisez un système avec environnements gérés:")
    print("   - Créez un environnement virtuel: python -m venv venv")
    print("   - Activez-le: source venv/bin/activate")
    print("   - Installez les dépendances: pip install -r requirements.txt")
    _log('import_error')
    sys.exit(1)


def main():
    """Point d'entrée principal de l'application Ayanna ERP"""
    
    # Si l'application est gelée avec PyInstaller, indiquer à Qt où sont les plugins
    if getattr(sys, 'frozen', False):
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        # Cherche d'abord un dossier 'platforms' à la racine extrait,
        # sinon tente 'plugins/platforms' si vous avez inclus tout 'plugins'.
        plugin_candidates = [
            os.path.join(base_path, 'platforms'),
            os.path.join(base_path, 'plugins', 'platforms'),
        ]
        for candidate in plugin_candidates:
            if os.path.exists(candidate):
                os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = candidate
                break

    # Créer l'application Qt
    _log('before_qapplication')
    app = QApplication(sys.argv)
    _log('after_qapplication')
    app.setApplicationName("Ayanna ERP")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Ayanna Tech")
    
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
    _log('before_db_init')
    db_manager = DatabaseManager()
    from ayanna_erp.database.database_manager import set_database_manager
    set_database_manager(db_manager)   # partager l'instance dès maintenant

    # Créer toutes les tables SANS insérer les données par défaut,
    # afin de pouvoir tester is_first_run() avant l'initialisation.
    try:
        db_manager.create_all_tables()
    except Exception as _e:
        print(f"Avertissement lors de la création des tables : {_e}")
    _log('after_db_table_create')

    # ── Premier démarrage ─────────────────────────────────────────────────────
    # Si la BDD est vide (aucun utilisateur), afficher le wizard de configuration.
    # Le wizard demande les identifiants du serveur :
    #   • Succès  → login() + pull() : toutes les données sont rapatriées.
    #               La vérification de licence locale est sautée (server_mode_used).
    #   • Échec / pas de serveur → clic sur "Continuer sans serveur" →
    #               initialize_database() avec les données par défaut.
    skip_licence = False
    if db_manager.is_first_run():
        _log('first_run_wizard')
        from PyQt6.QtWidgets import QDialog
        from ayanna_erp.ui.first_run_wizard import FirstRunWizard
        wizard = FirstRunWizard(db_manager)
        result = wizard.exec()
        if result != QDialog.DialogCode.Accepted:
            # L'utilisateur a fermé le wizard sans terminer la configuration
            sys.exit(0)
        skip_licence = getattr(wizard, 'server_mode_used', False)
        _log('first_run_wizard_done')
    else:
        # Démarrage normal : s'assurer que toutes les données par défaut existent
        if not db_manager.initialize_database():
            print("Erreur lors de l'initialisation de la base de données")
            _log('db_init_failed')
            sys.exit(1)
    _log('after_db_init')

    # ── Vérification de la licence ───────────────────────────────────────────
    # Sautée si les données (dont la licence) ont déjà été récupérées du serveur.
    if not skip_licence:
        try:
            _log('before_licence_check')
            valid, msg = verifier_licence()
            if not valid:
                # afficher la fenêtre d'activation en mode modal
                dlg = LicenceActivationDialog()
                result = dlg.exec()
                # Si l'utilisateur a accepté, re-vérifier
                if result == 1:
                    _log('before_licence_check_2')
                    valid2, msg2 = verifier_licence()
                    _log('after_licence_check_2')
                    if not valid2:
                        print("Licence introuvable ou invalide après activation :", msg2)
                        sys.exit(1)
                else:
                    print("Activation de licence annulée par l'utilisateur.")
                    sys.exit(1)
        except Exception as e:
            print("Erreur lors de la vérification de la licence:", e)
            sys.exit(1)
    
    # Créer et afficher la fenêtre de connexion
    login_window = LoginWindow()
    _log('after_login_window_created')
    # Appliquer l'icône à la fenêtre de connexion si disponible
    try:
        if 'icon_path' in locals() and os.path.exists(icon_path):
            login_window.setWindowIcon(QIcon(icon_path))
    except Exception:
        pass
    login_window.show()
    
    # Démarrer la boucle d'événements
    _log('before_app_exec')
    ret = app.exec()
    _log('after_app_exec')
    # write final timestamp
    _log('exit')
    sys.exit(ret)


if __name__ == "__main__":
    main()
