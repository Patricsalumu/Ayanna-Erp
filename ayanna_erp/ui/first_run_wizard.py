"""
FirstRunWizard — Assistant de configuration au premier démarrage.

Affiche automatiquement quand la base de données locale est vide (aucun user).

Flux :
  Page 0 — Connexion serveur
    Saisie : URL + email + mot de passe
    [Se connecter et récupérer les données]
      → login() + pull() → récupère TOUT depuis le serveur → page Succès
    [Continuer sans serveur]
      → initialise la BDD avec les données par défaut → page Succès

  Page 1 — Succès
    Message de résultat + bouton "Démarrer Ayanna ERP"
"""

from PyQt6.QtWidgets import (
    QDialog, QStackedWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QProgressBar,
    QMessageBox, QSizePolicy, QWidget,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont


# ──────────────────────────────────────────────────────────────────────────────
# Worker threads
# ──────────────────────────────────────────────────────────────────────────────

class _ServerSetupWorker(QThread):
    """
    Connexion (login) + pull de toutes les données depuis le serveur.
    """

    finished = pyqtSignal(dict)   # {'ok': bool, 'message': str}

    def __init__(self, sm, url, email, password, parent=None):
        super().__init__(parent)
        self._sm       = sm
        self._url      = url
        self._email    = email
        self._password = password

    def run(self):
        try:
            # 1. Sauvegarder URL + identifiants chiffrés dans core_configsync
            self._sm.save_config(
                server_url=self._url,
                server_email=self._email,
                server_password=self._password,
            )
            # 2. Authentification
            self._sm.login(email=self._email, password=self._password)
            # 3. Pull : rapatrier TOUTES les données du serveur
            pull = self._sm.pull(triggered_by=self._email)
            tables = pull.get('tables', [])
            total  = pull.get('total_records', 0)
            self.finished.emit({
                'ok': True,
                'message': (
                    f"Connexion réussie pour {self._email}.\n"
                    f"{total} enregistrement(s) récupéré(s) depuis le serveur "
                    f"({len(tables)} table(s)).\n\n"
                    "La licence et toutes les données ont été restaurées."
                ),
            })
        except Exception as e:
            self.finished.emit({'ok': False, 'message': str(e)})


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _get_sync_manager():
    from ayanna_erp.database.database_manager import get_database_manager
    return get_database_manager().sync_manager


# ──────────────────────────────────────────────────────────────────────────────
# Wizard
# ──────────────────────────────────────────────────────────────────────────────

class FirstRunWizard(QDialog):
    """
    Assistant de premier démarrage.

    Affiche un formulaire de connexion au serveur (URL + email + mot de passe).
    Si la connexion réussit, toutes les données sont rapatriées depuis le serveur.
    Si l'utilisateur n'a pas de serveur, il peut cliquer sur
    "Continuer sans serveur" pour initialiser la BDD avec les données par défaut.

    Retourne QDialog.Accepted une fois la configuration terminée.
    """

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self._db     = db_manager
        self._worker = None
        # True si l'utilisateur s'est connecté au serveur avec succès.
        # main.py utilise ce flag pour sauter la vérification de licence locale.
        self.server_mode_used = False
        self.setWindowTitle("Bienvenue dans Ayanna ERP — Configuration initiale")
        self.setMinimumWidth(620)
        self.setMinimumHeight(500)
        self.setModal(True)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        self._build_ui()

    # -----------------------------------------------------------------------
    # Construction UI
    # -----------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # Bannière
        banner = QFrame()
        banner.setFixedHeight(64)
        banner.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #1565C0, stop:1 #1976D2);"
        )
        bl = QHBoxLayout(banner)
        bl.setContentsMargins(24, 0, 24, 0)
        self._title_lbl = QLabel("  Bienvenue dans Ayanna ERP")
        self._title_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self._title_lbl.setStyleSheet("color:white;")
        bl.addWidget(self._title_lbl)
        root.addWidget(banner)

        # Barre de progression (indéterminée, visible uniquement pendant les op. réseau)
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setFixedHeight(5)
        self._progress.setVisible(False)
        self._progress.setStyleSheet(
            "QProgressBar{background:#E0E0E0;border:none;}"
            "QProgressBar::chunk{background:#1976D2;}"
        )
        root.addWidget(self._progress)

        # Pages
        self._stack = QStackedWidget()
        self._stack.addWidget(self._page_server())   # 0
        self._stack.addWidget(self._page_success())  # 1
        root.addWidget(self._stack)

    # ── Page 0 : Formulaire connexion serveur ────────────────────────────────

    def _page_server(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 28, 40, 24)
        layout.setSpacing(16)

        # Titre + description
        title = QLabel("Connexion au serveur Ayanna ERP")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet("color:#1565C0;")
        layout.addWidget(title)

        desc = QLabel(
            "Entrez l'adresse de votre serveur et vos identifiants.\n"
            "L'application se connectera et rapatriera automatiquement toutes les "
            "données existantes (produits, points de vente, utilisateurs, licence…)."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color:#555; font-size:12px;")
        layout.addWidget(desc)

        # Formulaire
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._srv_url = QLineEdit()
        self._srv_url.setPlaceholderText("http://192.168.1.10:8000")
        self._srv_url.setMinimumHeight(36)
        form.addRow("Adresse serveur * :", self._srv_url)

        self._srv_email = QLineEdit()
        self._srv_email.setPlaceholderText("votre.email@serveur.com")
        self._srv_email.setMinimumHeight(36)
        form.addRow("Email * :", self._srv_email)

        # Mot de passe + bouton afficher/masquer
        pwd_row = QHBoxLayout()
        self._srv_pwd = QLineEdit()
        self._srv_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self._srv_pwd.setPlaceholderText("Votre mot de passe serveur")
        self._srv_pwd.setMinimumHeight(36)
        self._srv_pwd.returnPressed.connect(self._on_server_go)
        show_btn = QPushButton("Afficher")
        show_btn.setFixedWidth(72)
        show_btn.setFixedHeight(36)
        show_btn.setStyleSheet(
            "QPushButton{background:#ECF0F1;border:1px solid #BDC3C7;"
            "border-radius:4px;font-size:11px;}"
            "QPushButton:hover{background:#D5D8DC;}"
        )
        show_btn.clicked.connect(self._toggle_pwd)
        self._show_pwd_btn = show_btn
        pwd_row.addWidget(self._srv_pwd)
        pwd_row.addWidget(show_btn)
        form.addRow("Mot de passe * :", pwd_row)

        layout.addLayout(form)

        # Message de statut (erreur/info)
        self._srv_status = QLabel("")
        self._srv_status.setWordWrap(True)
        self._srv_status.setStyleSheet("font-size:12px; min-height:18px;")
        layout.addWidget(self._srv_status)

        layout.addStretch()

        # --- Boutons ---
        # Bouton principal : se connecter
        self._srv_go_btn = QPushButton("Se connecter et récupérer les données  →")
        self._srv_go_btn.setMinimumHeight(44)
        self._srv_go_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self._srv_go_btn.setStyleSheet(
            "QPushButton{background:#1565C0;color:white;border:none;"
            "border-radius:6px;padding:0 20px;}"
            "QPushButton:hover{background:#0D47A1;}"
            "QPushButton:disabled{background:#90A4AE;}"
        )
        self._srv_go_btn.clicked.connect(self._on_server_go)
        layout.addWidget(self._srv_go_btn)

        # Séparateur
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#E0E0E0; margin:4px 0;")
        layout.addWidget(sep)

        # Bouton secondaire : mode local
        skip_btn = QPushButton("Continuer sans serveur (données par défaut)")
        skip_btn.setMinimumHeight(38)
        skip_btn.setFont(QFont("Segoe UI", 11))
        skip_btn.setStyleSheet(
            "QPushButton{background:#546E7A;color:white;border:none;"
            "border-radius:6px;padding:0 16px;}"
            "QPushButton:hover{background:#37474F;}"
            "QPushButton:disabled{background:#90A4AE;}"
        )
        skip_btn.clicked.connect(self._on_skip_to_local)
        self._skip_btn = skip_btn
        layout.addWidget(skip_btn)

        return page

    # ── Page 1 : Succès ──────────────────────────────────────────────────────

    def _page_success(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        layout.addStretch()

        icon = QLabel("✅")
        icon.setFont(QFont("Segoe UI", 40))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        self._success_lbl = QLabel("")
        self._success_lbl.setWordWrap(True)
        self._success_lbl.setFont(QFont("Segoe UI", 12))
        self._success_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._success_lbl.setStyleSheet("color:#2E7D32;")
        layout.addWidget(self._success_lbl)

        layout.addStretch()

        done_btn = QPushButton("Démarrer Ayanna ERP")
        done_btn.setMinimumHeight(44)
        done_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        done_btn.setStyleSheet(
            "QPushButton{background:#1565C0;color:white;border:none;"
            "border-radius:6px;padding:0 24px;}"
            "QPushButton:hover{background:#0D47A1;}"
        )
        done_btn.clicked.connect(self.accept)
        layout.addWidget(done_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        return page

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _toggle_pwd(self):
        if self._srv_pwd.echoMode() == QLineEdit.EchoMode.Password:
            self._srv_pwd.setEchoMode(QLineEdit.EchoMode.Normal)
            self._show_pwd_btn.setText("Masquer")
        else:
            self._srv_pwd.setEchoMode(QLineEdit.EchoMode.Password)
            self._show_pwd_btn.setText("Afficher")

    def _set_busy(self, busy: bool):
        self._progress.setVisible(busy)
        self._srv_go_btn.setEnabled(not busy)
        self._skip_btn.setEnabled(not busy)

    # -----------------------------------------------------------------------
    # Actions
    # -----------------------------------------------------------------------

    def _on_server_go(self):
        url   = self._srv_url.text().strip()
        email = self._srv_email.text().strip()
        pwd   = self._srv_pwd.text()

        if not url:
            self._srv_status.setText("⚠ L'adresse serveur est obligatoire.")
            self._srv_status.setStyleSheet("font-size:12px; color:#C62828;")
            self._srv_url.setFocus()
            return
        if not email:
            self._srv_status.setText("⚠ L'email est obligatoire.")
            self._srv_status.setStyleSheet("font-size:12px; color:#C62828;")
            self._srv_email.setFocus()
            return
        if not pwd:
            self._srv_status.setText("⚠ Le mot de passe est obligatoire.")
            self._srv_status.setStyleSheet("font-size:12px; color:#C62828;")
            self._srv_pwd.setFocus()
            return

        self._srv_status.setText("Connexion au serveur en cours…")
        self._srv_status.setStyleSheet("font-size:12px; color:#555;")
        self._set_busy(True)

        sm = _get_sync_manager()
        self._worker = _ServerSetupWorker(
            sm, url=url, email=email, password=pwd, parent=self
        )
        self._worker.finished.connect(self._on_server_done)
        self._worker.start()

    def _on_server_done(self, result: dict):
        self._set_busy(False)
        if result['ok']:
            self.server_mode_used = True
            self._success_lbl.setText(
                result['message'] + "\n\nVous pouvez maintenant vous connecter."
            )
            self._stack.setCurrentIndex(1)
        else:
            # Afficher l'erreur et laisser l'utilisateur réessayer ou passer en local
            self._srv_status.setText(
                f"✗ Échec de connexion : {result['message']}\n\n"
                "Vérifiez l'adresse et vos identifiants, ou cliquez sur "
                "\"Continuer sans serveur\" pour démarrer avec les données par défaut."
            )
            self._srv_status.setStyleSheet("font-size:12px; color:#C62828;")

    def _on_skip_to_local(self):
        """Initialise la BDD avec les données par défaut (sans serveur)."""
        self._set_busy(True)
        self._srv_status.setText("Initialisation avec les données par défaut…")
        self._srv_status.setStyleSheet("font-size:12px; color:#555;")
        try:
            self._db.initialize_database()
            self._success_lbl.setText(
                "Application initialisée avec les données par défaut.\n\n"
                "Compte administrateur par défaut :\n"
                "   Email    : admin@ayanna.com\n"
                "   Mot de passe : admin123\n\n"
                "Pensez à modifier ces informations après la connexion."
            )
            self._success_lbl.setStyleSheet(
                "color:#1565C0; font-size:12px; white-space:pre;"
            )
            self._stack.setCurrentIndex(1)
        except Exception as e:
            self._srv_status.setText(f"✗ Erreur lors de l'initialisation : {e}")
            self._srv_status.setStyleSheet("font-size:12px; color:#C62828;")
        finally:
            self._set_busy(False)

    # Garder la compatibilité si du code externe instancie l'ancienne page locale
    def _apply_local_setup(self, company: str, admin_name: str,
                            admin_email: str, admin_pwd: str):
        """Compatibilité — redirige vers initialize_database()."""
        self._db.initialize_database()
