#!/usr/bin/env python3
"""
Ayanna ERP - Système de Gestion Intégré
Point d'entrée principal de l'application
"""

import sys
import os
import time
from pathlib import Path
from urllib.parse import quote_plus

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


def _database_config_path() -> Path:
    return project_root / 'database_config.txt'


def _save_database_config(server: str, database: str, username: str, password: str) -> None:
    """Enregistre la configuration MySQL dans un fichier texte de projet."""
    config_path = _database_config_path()
    content = (
        f"server={server}\n"
        f"database={database}\n"
        f"username={username}\n"
        f"password={password}\n"
    )
    config_path.write_text(content, encoding='utf-8')

    url = (
        f"mysql+pymysql://{quote_plus(username)}:{quote_plus(password)}@{server}:3306/{database}"
        if password
        else f"mysql+pymysql://{quote_plus(username)}@{server}:3306/{database}"
    )
    os.environ["DATABASE_URL"] = url
    os.environ["DB_USER"] = username
    os.environ["DB_PASSWORD"] = password


def _save_database_url_to_env(url: str) -> None:
    """Met aussi à jour .env pour compatibilité locale, sans dépendre de lui pour le bootstrap."""
    env_path = project_root / '.env'
    try:
        lines = env_path.read_text(encoding='utf-8').splitlines() if env_path.exists() else []
        updated = []
        has_db_line = False
        for line in lines:
            if line.strip().startswith('DATABASE_URL='):
                updated.append(f'DATABASE_URL={url}')
                has_db_line = True
            else:
                updated.append(line)
        if not has_db_line:
            updated.append(f'DATABASE_URL={url}')
        env_path.write_text('\n'.join(updated) + '\n', encoding='utf-8')
    except Exception:
        pass
    os.environ['DATABASE_URL'] = url


def _load_database_config_from_file() -> dict | None:
    """Lit le fichier database_config.txt et retourne les valeurs si elles sont complètes."""
    config_path = _database_config_path()
    if not config_path.exists():
        return None

    try:
        text = config_path.read_text(encoding='utf-8').strip()
    except Exception:
        return None

    if not text:
        return None

    values = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        values[key.strip().lower()] = value.strip()

    server = values.get('server', '').strip()
    database = values.get('database', '').strip()
    username = values.get('username', '').strip()
    password = values.get('password', '')

    if not server or not database or not username:
        return None

    url = (
        f"mysql+pymysql://{quote_plus(username)}:{quote_plus(password)}@{server}:3306/{database}"
        if password
        else f"mysql+pymysql://{quote_plus(username)}@{server}:3306/{database}"
    )
    return {
        'server': server,
        'database': database,
        'username': username,
        'password': password,
        'url': url,
    }


def _get_database_configuration_from_env() -> tuple[str, str, str] | None:
    """Retourne la config de l'environnement si elle est explicitement définie, sinon le fichier local."""
    env_url = os.getenv("DATABASE_URL", "").strip()
    if env_url:
        try:
            rest = env_url.split("://", 1)[1]
            if "@" in rest:
                rest = rest.split("@", 1)[1]
            host_part = rest.split("/", 1)[0]
            host = host_part.rsplit(":", 1)[0] if ":" in host_part else host_part
            db_name = env_url.rsplit("/", 1)[-1].strip() or "insomnia"
            user_part = env_url.split("://", 1)[1].split("@", 1)[0]
            user = user_part.split(":", 1)[0] if ":" in user_part else user_part
            os.environ["DATABASE_URL"] = env_url
            os.environ["DB_USER"] = user
            os.environ["DB_PASSWORD"] = ""
            return env_url, host, db_name
        except Exception:
            return None

    saved = _load_database_config_from_file()
    if saved:
        os.environ["DATABASE_URL"] = saved['url']
        os.environ["DB_USER"] = saved['username']
        os.environ["DB_PASSWORD"] = saved['password']
        return saved['url'], saved['server'], saved['database']

    return None


def _build_database_url(server: str, database: str, username: str, password: str) -> str:
    port = '3306'
    if password:
        return f"mysql+pymysql://{quote_plus(username)}:{quote_plus(password)}@{server}:{port}/{database}"
    return f"mysql+pymysql://{quote_plus(username)}@{server}:{port}/{database}"


def _test_mysql_connection(server: str, database: str, username: str, password: str) -> tuple[bool, str]:
    """Teste simplement la connectivité MySQL avec SQLAlchemy et retourne le résultat."""
    try:
        from sqlalchemy import create_engine, text
        url = _build_database_url(server, database, username, password)
        engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        return True, 'Connexion MySQL OK.'
    except Exception as exc:
        return False, str(exc)


def _prompt_database_configuration(existing: dict | None = None) -> tuple[str, str, str]:
    """Ouvre une boîte de configuration MySQL ergonomique avec les actions demandées."""
    from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QVBoxLayout, QLabel, QMessageBox, QHBoxLayout
    from PyQt6.QtGui import QFont
    from PyQt6.QtCore import Qt

    current_host = (existing or {}).get('server', '127.0.0.1')
    current_db = (existing or {}).get('database', 'insomnia')
    current_user = (existing or {}).get('username', 'ayanna_user')
    current_password = (existing or {}).get('password', '')

    dialog = QDialog()
    dialog.setWindowTitle("Configuration MySQL - Ayanna ERP")
    dialog.resize(540, 340)
    dialog.setModal(True)

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(18, 18, 18, 18)
    layout.setSpacing(12)

    title = QLabel("Connexion à la base de données")
    title_font = QFont()
    title_font.setPointSize(12)
    title_font.setBold(True)
    title.setFont(title_font)
    layout.addWidget(title)

    info = QLabel("Configurez l’accès à votre serveur MySQL. La configuration est sauvegardée localement pour éviter de la re-saisir à chaque lancement.")
    info.setWordWrap(True)
    info.setStyleSheet("color: #4a4a4a;")
    layout.addWidget(info)

    form = QFormLayout()
    form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
    host_edit = QLineEdit(current_host)
    db_edit = QLineEdit(current_db)
    user_edit = QLineEdit(current_user)
    password_edit = QLineEdit(current_password)
    password_edit.setEchoMode(QLineEdit.EchoMode.Password)

    host_edit.setPlaceholderText("127.0.0.1")
    db_edit.setPlaceholderText("insomnia")
    user_edit.setPlaceholderText("root ou ayanna_user")

    form.addRow("Adresse du serveur :", host_edit)
    form.addRow("Base de données :", db_edit)
    form.addRow("Nom utilisateur :", user_edit)
    form.addRow("Mot de passe :", password_edit)
    layout.addLayout(form)

    status_label = QLabel("Prêt.")
    status_label.setStyleSheet("color: #2b6cb0; font-weight: 600;")
    layout.addWidget(status_label)

    buttons_layout = QHBoxLayout()
    modify_button = QPushButton("Modifier la config")
    test_button = QPushButton("Tester la connexion")
    continue_button = QPushButton("Continuer")
    continue_button.setDefault(True)
    continue_button.setEnabled(False)

    buttons_layout.addWidget(modify_button)
    buttons_layout.addWidget(test_button)
    buttons_layout.addStretch()
    buttons_layout.addWidget(continue_button)
    layout.addLayout(buttons_layout)

    connection_validated = False

    def validate_fields() -> tuple[bool, str]:
        host = host_edit.text().strip()
        db_name = db_edit.text().strip()
        user = user_edit.text().strip()
        password = password_edit.text()

        if not host:
            return False, "L'adresse du serveur est obligatoire."
        if not db_name:
            return False, "Le nom de la base est obligatoire."
        if not user:
            return False, "Le nom utilisateur est obligatoire."
        return True, ""

    def on_modify_config():
        nonlocal connection_validated
        connection_validated = False
        continue_button.setEnabled(False)
        host_edit.setEnabled(True)
        db_edit.setEnabled(True)
        user_edit.setEnabled(True)
        password_edit.setEnabled(True)
        status_label.setText("Vous pouvez modifier les informations de connexion.")
        status_label.setStyleSheet("color: #805ad5; font-weight: 600;")
        host_edit.setFocus()

    def on_test_connection():
        nonlocal connection_validated
        ok, message = validate_fields()
        if not ok:
            QMessageBox.critical(dialog, "Erreur de configuration", message)
            return
        success, detail = _test_mysql_connection(host_edit.text().strip(), db_edit.text().strip(), user_edit.text().strip(), password_edit.text())
        if success:
            connection_validated = True
            continue_button.setEnabled(True)
            status_label.setText("Connexion MySQL OK. Vous pouvez continuer.")
            status_label.setStyleSheet("color: #2f855a; font-weight: 600;")
            QMessageBox.information(dialog, "Connexion OK", "La connexion MySQL est fonctionnelle.")
        else:
            connection_validated = False
            continue_button.setEnabled(False)
            status_label.setText("Échec de connexion.")
            status_label.setStyleSheet("color: #c53030; font-weight: 600;")
            QMessageBox.critical(dialog, "Connexion impossible", f"Vérifiez les accès MySQL.\n\nDétail : {detail}")

    def on_continue():
        nonlocal connection_validated
        ok, message = validate_fields()
        if not ok:
            QMessageBox.critical(dialog, "Erreur de configuration", message)
            return
        if not connection_validated:
            QMessageBox.warning(dialog, "Connexion non validée", "Veuillez tester la connexion MySQL avant de continuer.")
            return
        dialog.accept()

    modify_button.clicked.connect(on_modify_config)
    test_button.clicked.connect(on_test_connection)
    continue_button.clicked.connect(on_continue)

    if dialog.exec() != QDialog.DialogCode.Accepted:
        raise ValueError("Connexion MySQL annulée par l'utilisateur.")

    host = host_edit.text().strip()
    db_name = db_edit.text().strip()
    user = user_edit.text().strip()
    password = password_edit.text()
    url = _build_database_url(host, db_name, user, password)

    os.environ["DATABASE_URL"] = url
    os.environ["DB_USER"] = user
    os.environ["DB_PASSWORD"] = password
    _save_database_config(host, db_name, user, password)
    _save_database_url_to_env(url)
    return url, host, db_name


def _resolve_database_url_from_prompt(force_edit: bool = False) -> tuple[str, str, str]:
    """Vérifie la configuration locale. Si force_edit est vrai, on ouvre explicitement la boîte d'édition."""
    saved = _load_database_config_from_file()
    if saved and saved.get('server') and saved.get('database') and saved.get('username') and not force_edit:
        os.environ["DATABASE_URL"] = saved['url']
        os.environ["DB_USER"] = saved['username']
        os.environ["DB_PASSWORD"] = saved['password']
        return saved['url'], saved['server'], saved['database']

    return _prompt_database_configuration(saved)


def _show_database_error_dialog(error_message: str, existing: dict | None = None) -> str:
    """Affiche une alerte explicite si la base serveur est inaccessible et propose les actions utiles."""
    from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
    from PyQt6.QtGui import QDesktopServices
    from PyQt6.QtCore import QUrl

    dialog = QDialog()
    dialog.setWindowTitle("Connexion au serveur impossible")
    dialog.setModal(True)
    dialog.resize(560, 360)

    layout = QVBoxLayout(dialog)
    layout.setSpacing(14)
    layout.setContentsMargins(18, 18, 18, 18)

    title = QLabel("Impossible de se connecter à la base de données du serveur")
    title.setStyleSheet("font-size: 18px; font-weight: 700; color: #111827;")
    layout.addWidget(title)

    message = QLabel(
        "Ayanna ERP n'arrive pas à joindre la base de données configurée sur la machine serveur.\n\n"
        "Veuillez vérifier que :\n"
        "• la machine serveur est allumée;\n"
        "• XAMPP/MySQL est bien démarré;\n"
        "• la machine est connectée au réseau configuré;\n"
        "• les paramètres serveur, base, utilisateur et mot de passe sont corrects.\n\n"
        "Si le problème persiste, contactez l'équipe technique au +243 997 554 905."
    )
    message.setWordWrap(True)
    message.setStyleSheet("font-size: 12px; color: #1f2937; line-height: 1.4;")
    layout.addWidget(message)

    details = QLabel(f"Détail technique : {error_message[:500]}")
    details.setWordWrap(True)
    details.setStyleSheet("font-size: 10px; color: #4b5563; background: #f3f4f6; border-radius: 8px; padding: 8px;")
    layout.addWidget(details)

    buttons = QHBoxLayout()
    buttons.addStretch()

    modify_btn = QPushButton("Modifier la config")
    retry_btn = QPushButton("Réessayer")
    contact_btn = QPushButton("Contacter le support")
    quit_btn = QPushButton("Quitter")

    modify_btn.setStyleSheet("padding: 8px 12px; font-weight: 600;")
    retry_btn.setStyleSheet("padding: 8px 12px; font-weight: 600;")
    contact_btn.setStyleSheet("padding: 8px 12px; font-weight: 600;")
    quit_btn.setStyleSheet("padding: 8px 12px; font-weight: 600;")

    buttons.addWidget(modify_btn)
    buttons.addWidget(retry_btn)
    buttons.addWidget(contact_btn)
    buttons.addWidget(quit_btn)
    layout.addLayout(buttons)

    action = {"value": "quit"}

    def set_action(value: str):
        action["value"] = value
        dialog.accept()

    modify_btn.clicked.connect(lambda: set_action("modify"))
    retry_btn.clicked.connect(lambda: set_action("retry"))
    contact_btn.clicked.connect(lambda: (QDesktopServices.openUrl(QUrl("tel:+243997554905")), set_action("retry")))
    quit_btn.clicked.connect(lambda: set_action("quit"))

    dialog.exec()
    return action["value"]


def main():
    """Point d'entrée principal de l'application Ayanna ERP"""
    if getattr(sys, 'frozen', False):
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        plugin_candidates = [
            os.path.join(base_path, 'platforms'),
            os.path.join(base_path, 'plugins', 'platforms'),
        ]
        for candidate in plugin_candidates:
            if os.path.exists(candidate):
                os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = candidate
                break

    _log('before_qapplication')
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    _log('after_qapplication')
    app.setApplicationName("Ayanna ERP")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Ayanna Tech")
    app.setStyle('Fusion')

    while True:
        try:
            db_url, db_host, db_name = _resolve_database_url_from_prompt()
            break
        except ValueError as exc:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "Configuration MySQL incomplète", str(exc))
            sys.exit(1)

    while True:
        try:
            db_manager = DatabaseManager(db_url)
            break
        except Exception as exc:
            choice = _show_database_error_dialog(str(exc), {
                'server': db_host,
                'database': db_name,
                'username': os.getenv('DB_USER', ''),
                'password': os.getenv('DB_PASSWORD', ''),
            })
            if choice == 'modify':
                try:
                    db_url, db_host, db_name = _resolve_database_url_from_prompt(force_edit=True)
                    continue
                except ValueError as exc:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.critical(None, "Configuration MySQL incomplète", str(exc))
                    sys.exit(1)
            if choice in {'retry', 'contact'}:
                try:
                    db_url, db_host, db_name = _resolve_database_url_from_prompt()
                    continue
                except ValueError as exc:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.critical(None, "Configuration MySQL incomplète", str(exc))
                    sys.exit(1)
            sys.exit(1)

    # Configurer le style de l'application
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
    from ayanna_erp.database.database_manager import set_database_manager
    set_database_manager(db_manager)   # partager l'instance dès maintenant

    # Le schéma et les données de base doivent être importés via la migration PHP / SQL.
    # Ce client Python ne vérifie plus la BDD ni n'injecte les données par défaut.
    _log('database_seed_is_externalized')

    # Vérification de licence de l'application uniquement, sans logique de bootstrap BDD.
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
