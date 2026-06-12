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


def _run_migrations_silently():
    """Exécute automatiquement les migrations de schéma sans affichage"""
    try:
        from pathlib import Path
        import sqlite3
        
        project_root = Path(__file__).parent.absolute()
        
        # Créer la table restau_bon_commandes si elle n'existe pas
        CREATE_TABLE_SQL = """
        CREATE TABLE IF NOT EXISTS restau_bon_commandes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entreprise_id INTEGER NOT NULL,
            numero_bon INTEGER NOT NULL,
            restau_panier_id INTEGER NOT NULL,
            serveuse_id INTEGER,
            client_id INTEGER NOT NULL,
            user_id INTEGER,
            produits_json TEXT NOT NULL,
            montant_total FLOAT DEFAULT 0.0,
            statut VARCHAR(50) DEFAULT 'valide',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(restau_panier_id) REFERENCES restau_paniers(id) ON DELETE CASCADE,
            FOREIGN KEY(entreprise_id) REFERENCES entreprises(id) ON DELETE CASCADE,
            FOREIGN KEY(serveuse_id) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY(client_id) REFERENCES shop_clients(id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL,
            UNIQUE(entreprise_id, numero_bon)
        );
        
        CREATE INDEX IF NOT EXISTS idx_restau_bon_commandes_restau_panier_id ON restau_bon_commandes(restau_panier_id);
        CREATE INDEX IF NOT EXISTS idx_restau_bon_commandes_entreprise_id ON restau_bon_commandes(entreprise_id);
        CREATE INDEX IF NOT EXISTS idx_restau_bon_commandes_statut ON restau_bon_commandes(statut);
        CREATE INDEX IF NOT EXISTS idx_restau_bon_commandes_client_id ON restau_bon_commandes(client_id);
        CREATE INDEX IF NOT EXISTS idx_restau_bon_commandes_created_at ON restau_bon_commandes(created_at);
        CREATE INDEX IF NOT EXISTS idx_restau_bon_commandes_entreprise_statut ON restau_bon_commandes(entreprise_id, statut);
        """
        
        # Trouver toutes les bases de données SQLite
        db_files = []
        
        # Chemins connus
        known_paths = [
            project_root / 'ayanna_erp' / 'database' / 'database.db',
            project_root / 'ayanna_erp' / 'ayanna_erp.sqbpro',
            project_root / 'ayanna_erp' / 'ss.sqbpro',
        ]
        
        for db_path in known_paths:
            if db_path.exists():
                db_files.append(db_path)
        
        # Chercher aussi récursivement
        for root, dirs, files in os.walk(project_root):
            if any(ignore in root for ignore in ['node_modules', 'venv', '.git', '__pycache__', 'vendor']):
                continue
            for file in files:
                if file.endswith('.db') or file.endswith('.sqbpro'):
                    full_path = Path(root) / file
                    if full_path not in db_files:
                        db_files.append(full_path)
        
        # Appliquer les migrations à chaque BDD
        for db_path in db_files:
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                for statement in CREATE_TABLE_SQL.split(';'):
                    statement = statement.strip()
                    if statement:
                        cursor.execute(statement)
                conn.commit()
                conn.close()
            except Exception:
                pass  # Silence les erreurs pour ne pas déranger le démarrage
    except Exception:
        pass  # Silence toute erreur pour un démarrage fluide


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
    
    # ✅ Exécuter les migrations de schéma automatiquement
    _log('before_migrations')
    _run_migrations_silently()
    _log('after_migrations')

    # ── Logique de démarrage selon l'état de la BDD ───────────────────────────
    # • BDD vide (premier démarrage) :
    #     1. Afficher la fenêtre d'activation de licence
    #     2. Si licence valide → afficher le wizard de synchronisation/configuration
    # • BDD existante (démarrage normal) :
    #     1. Initialiser les données par défaut si besoin
    #     2. Vérifier la licence → afficher le login

    def _check_and_activate_licence():
        """Vérifie la licence ; affiche LicenceActivationDialog si invalide.
        Retourne True si la licence est valide, False sinon (quitte l'app)."""
        try:
            _log('before_licence_check')
            valid, msg = verifier_licence()
            if not valid:
                dlg = LicenceActivationDialog()
                result = dlg.exec()
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

    if db_manager.is_first_run():
        # ── Premier démarrage : licence D'ABORD, puis wizard de configuration ──
        _log('first_run_licence_check')
        _check_and_activate_licence()

        # Licence valide → afficher le wizard de synchronisation/configuration
        _log('first_run_wizard')
        from PyQt6.QtWidgets import QDialog
        from ayanna_erp.ui.first_run_wizard import FirstRunWizard
        wizard = FirstRunWizard(db_manager)
        result = wizard.exec()
        if result != QDialog.DialogCode.Accepted:
            # L'utilisateur a fermé le wizard sans terminer la configuration
            sys.exit(0)
        _log('first_run_wizard_done')
    else:
        # ── Démarrage normal : initialiser les données par défaut + vérifier licence ──
        if not db_manager.initialize_database():
            print("Erreur lors de l'initialisation de la base de données")
            _log('db_init_failed')
            sys.exit(1)
        _log('after_db_init')
        _check_and_activate_licence()
    
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
