"""
SyncConfigDialog — Configuration de la synchronisation avec le serveur API.

Accessible depuis : Menu Configuration ▸ Synchronisation serveur

Fonctionnalites :
  - Formulaire de saisie : URL, email, mot de passe (masque)
  - Bouton "Tester la connexion" (authentification et validation du token)
  - Bouton "Enregistrer" (sauvegarde chiffree dans core_configsync)
  - Section "Derniere synchronisation" : date, utilisateur, statut
  - Bouton "Synchroniser maintenant" (push + pull en arriere-plan)
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QMessageBox,
    QProgressBar, QSizePolicy, QTabWidget, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QComboBox, QWidget,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QColor


# ──────────────────────────────────────────────────────────────────────────────
# Worker thread pour les operations reseau (evite de bloquer l'UI)
# ──────────────────────────────────────────────────────────────────────────────

class _SyncWorker(QThread):
    """Effectue login + synchronize() dans un thread separe."""

    finished = pyqtSignal(dict)   # {'ok': bool, 'message': str, 'result': dict}

    def __init__(self, sm, mode: str, email=None, password=None,
                 name=None, parent=None):
        super().__init__(parent)
        self._sm       = sm
        self._mode     = mode      # 'test' | 'sync' | 'register' | 'init'
        self._email    = email
        self._password = password
        self._name     = name

    def run(self):
        try:
            if self._mode == 'test':
                token = self._sm.login(self._email, self._password)
                self.finished.emit({
                    'ok': True,
                    'message': 'Connexion reussie. Token obtenu.',
                    'result': {'token': token},
                })
            elif self._mode == 'register':
                token = self._sm.register_server_user(
                    name=self._name,
                    email=self._email,
                    password=self._password,
                )
                self.finished.emit({
                    'ok': True,
                    'message': (
                        f"Compte cree avec succes pour {self._email}.\n"
                        "Le token a ete sauvegarde automatiquement."
                    ),
                    'result': {'token': token},
                })
            elif self._mode == 'init':
                try:
                    from ayanna_erp.core.session_manager import SessionManager
                    user = SessionManager.get_current_user()
                    by = (getattr(user, 'name', '') or getattr(user, 'email', '')) if user else ''
                except Exception:
                    by = ''
                result = self._sm.initialize_sync(created_by=by)
                self.finished.emit({
                    'ok': True,
                    'message': (
                        f"{result['total']} enregistrement(s) pre-charges dans le journal \n"
                        f"depuis {len(result['tables'])} table(s).\n"
                        "Vous pouvez maintenant lancer la synchronisation."
                    ),
                    'result': result,
                })
            else:  # 'sync'
                # S'assurer que le token est valide avant de synchroniser
                self._sm.login()
                result = self._sm.synchronize()
                p = result['push']
                r = result['pull']
                self.finished.emit({
                    'ok': True,
                    'message': (
                        f"Synchronisation terminee.\n"
                        f"Push : {p.get('success', 0)}/{p.get('sent', 0)} enregistrement(s) envoyes.\n"
                        f"Pull : {r.get('total_records', 0)} enregistrement(s) recus depuis le serveur."
                    ),
                    'result': result,
                })
        except Exception as e:
            self.finished.emit({'ok': False, 'message': str(e), 'result': {}})


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _get_sync_manager():
    from ayanna_erp.database.database_manager import get_database_manager
    db = get_database_manager()
    return db.sync_manager


def _get_current_user_name() -> str:
    try:
        from ayanna_erp.core.session_manager import SessionManager
        user = SessionManager.get_current_user()
        if user:
            return getattr(user, 'name', '') or getattr(user, 'email', '') or ''
    except Exception:
        pass
    return ''


# ──────────────────────────────────────────────────────────────────────────────
# Dialogue principal
# ──────────────────────────────────────────────────────────────────────────────

class SyncConfigDialog(QDialog):
    """
    Dialogue de configuration et de synchronisation avec le serveur Ayanna API.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Synchronisation avec le serveur")
        self.setMinimumWidth(780)
        self.setMinimumHeight(620)
        self.setModal(True)
        self._worker = None
        self._sm = None
        self._build_ui()
        self._load_saved_config()

    # -----------------------------------------------------------------------
    # Construction de l'interface
    # -----------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ── Banniere titre ──
        banner = QFrame()
        banner.setFixedHeight(56)
        banner.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #1565C0, stop:1 #1976D2);"
        )
        bl = QHBoxLayout(banner)
        bl.setContentsMargins(20, 0, 20, 0)
        title_lbl = QLabel("  Synchronisation serveur")
        title_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color:white;")
        bl.addWidget(title_lbl)
        root.addWidget(banner)

        # ── Onglets ──
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(
            "QTabBar::tab{padding:8px 22px;font-size:12px;}"
            "QTabBar::tab:selected{font-weight:bold;color:#1565C0;"
            "border-bottom:2px solid #1976D2;}"
        )
        self._tabs.addTab(self._build_config_tab(), "  Configuration  ")
        self._tabs.addTab(self._build_journal_tab(), "  Journal local  ")
        self._tabs.addTab(self._build_history_tab(), "  Historique push / pull  ")
        self._tabs.currentChanged.connect(self._on_tab_changed)
        root.addWidget(self._tabs)

        # ── Barre de progression (partagee entre les deux onglets) ──
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedHeight(6)
        self.progress.setVisible(False)
        self.progress.setStyleSheet(
            "QProgressBar{background:#E0E0E0;border-radius:3px;border:none;}"
            "QProgressBar::chunk{background:#1976D2;border-radius:3px;}"
        )
        root.addWidget(self.progress)

        # ── Boutons bas ──
        bottom = QHBoxLayout()
        bottom.setContentsMargins(24, 8, 24, 16)

        self.sync_btn = QPushButton("Synchroniser maintenant")
        self.sync_btn.setMinimumHeight(40)
        self.sync_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.sync_btn.setStyleSheet(
            "QPushButton{background:#1565C0;color:white;border:none;"
            "border-radius:6px;padding:0 20px;}"
            "QPushButton:hover{background:#0D47A1;}"
            "QPushButton:disabled{background:#90A4AE;}"
        )
        self.sync_btn.clicked.connect(self._on_sync)

        self.init_btn = QPushButton("▶  Initialiser (pré-charger les données)")
        self.init_btn.setMinimumHeight(40)
        self.init_btn.setFont(QFont("Segoe UI", 11))
        self.init_btn.setToolTip(
            "Enfile TOUTES les données locales existantes dans le journal\n"
            "comme opérations INSERT en attente.\n"
            "A utiliser UNE SEULE FOIS au premier démarrage avant le premier push."
        )
        self.init_btn.setStyleSheet(
            "QPushButton{background:#E65100;color:white;border:none;"
            "border-radius:6px;padding:0 16px;}"
            "QPushButton:hover{background:#BF360C;}"
            "QPushButton:disabled{background:#90A4AE;}"
        )
        self.init_btn.clicked.connect(self._on_initialize)

        close_btn = QPushButton("Fermer")
        close_btn.setMinimumHeight(40)
        close_btn.setStyleSheet(
            "QPushButton{background:#607D8B;color:white;border:none;"
            "border-radius:6px;padding:0 20px;}"
            "QPushButton:hover{background:#455A64;}"
        )
        close_btn.clicked.connect(self.accept)

        bottom.addWidget(self.sync_btn)
        bottom.addWidget(self.init_btn)
        bottom.addStretch()
        bottom.addWidget(close_btn)
        root.addLayout(bottom)

    def _build_config_tab(self) -> QScrollArea:
        """Onglet 1 — formulaire de configuration + statut de la derniere sync."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        body = QVBoxLayout(container)
        body.setContentsMargins(24, 18, 24, 18)
        body.setSpacing(16)

        # ── Section connexion ──
        body.addWidget(self._section_label("Connexion au serveur"))

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("http://192.168.1.10:8000")
        self.url_input.setMinimumHeight(34)
        form.addRow("URL du serveur * :", self.url_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("admin@votre-serveur.com")
        self.email_input.setMinimumHeight(34)
        form.addRow("Adresse e-mail * :", self.email_input)

        pwd_row = QHBoxLayout()
        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd_input.setMinimumHeight(34)
        self.pwd_input.setPlaceholderText("Mot de passe")
        self._show_pwd_btn = QPushButton("Afficher")
        self._show_pwd_btn.setFixedWidth(72)
        self._show_pwd_btn.setFixedHeight(34)
        self._show_pwd_btn.setStyleSheet(
            "QPushButton{background:#ECF0F1;border:1px solid #BDC3C7;"
            "border-radius:4px;font-size:11px;}"
            "QPushButton:hover{background:#D5D8DC;}"
        )
        self._show_pwd_btn.clicked.connect(self._toggle_password)
        pwd_row.addWidget(self.pwd_input)
        pwd_row.addWidget(self._show_pwd_btn)
        form.addRow("Mot de passe * :", pwd_row)
        body.addLayout(form)

        # Boutons connexion / enregistrer
        btn_row1 = QHBoxLayout()
        self.test_btn = QPushButton("Tester la connexion")
        self.test_btn.setMinimumHeight(36)
        self.test_btn.setStyleSheet(
            "QPushButton{background:#0288D1;color:white;border:none;"
            "border-radius:5px;padding:0 16px;font-size:13px;}"
            "QPushButton:hover{background:#0277BD;}"
            "QPushButton:disabled{background:#B0BEC5;}"
        )
        self.test_btn.clicked.connect(self._on_test)

        self.save_btn = QPushButton("Enregistrer la configuration")
        self.save_btn.setMinimumHeight(36)
        self.save_btn.setStyleSheet(
            "QPushButton{background:#2E7D32;color:white;border:none;"
            "border-radius:5px;padding:0 16px;font-size:13px;}"
            "QPushButton:hover{background:#1B5E20;}"
            "QPushButton:disabled{background:#B0BEC5;}"
        )
        self.save_btn.clicked.connect(self._on_save)
        btn_row1.addWidget(self.test_btn)
        btn_row1.addWidget(self.save_btn)
        btn_row1.addStretch()
        body.addLayout(btn_row1)

        self.test_status = QLabel("")
        self.test_status.setWordWrap(True)
        self.test_status.setStyleSheet("font-size:12px; min-height:18px;")
        body.addWidget(self.test_status)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#E0E0E0;")
        body.addWidget(sep)

        # ── Section : Creer un premier compte serveur ──
        body.addWidget(self._section_label("Premier démarrage — Créer un compte sur le serveur"))
        hint = QLabel(
            "Si votre serveur est vide (aucun utilisateur), créez ici le compte administrateur."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("font-size:11px; color:#666; margin-bottom:4px;")
        body.addWidget(hint)

        reg_form = QFormLayout()
        reg_form.setSpacing(8)
        reg_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.reg_name_input = QLineEdit()
        self.reg_name_input.setPlaceholderText("ex : Admin Ayanna")
        self.reg_name_input.setMinimumHeight(32)
        reg_form.addRow("Nom complet :", self.reg_name_input)

        self.reg_email_input = QLineEdit()
        self.reg_email_input.setPlaceholderText("admin@monserveur.com")
        self.reg_email_input.setMinimumHeight(32)
        reg_form.addRow("Email :", self.reg_email_input)

        self.reg_pwd_input = QLineEdit()
        self.reg_pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_pwd_input.setPlaceholderText("Minimum 8 caractères")
        self.reg_pwd_input.setMinimumHeight(32)
        reg_form.addRow("Mot de passe :", self.reg_pwd_input)

        body.addLayout(reg_form)

        btn_row2 = QHBoxLayout()
        self.reg_btn = QPushButton("➕  Créer le compte sur le serveur")
        self.reg_btn.setMinimumHeight(36)
        self.reg_btn.setStyleSheet(
            "QPushButton{background:#6A1B9A;color:white;border:none;"
            "border-radius:5px;padding:0 16px;font-size:12px;}"
            "QPushButton:hover{background:#4A148C;}"
            "QPushButton:disabled{background:#B0BEC5;}"
        )
        self.reg_btn.clicked.connect(self._on_register)
        btn_row2.addWidget(self.reg_btn)
        btn_row2.addStretch()
        body.addLayout(btn_row2)

        self.reg_status = QLabel("")
        self.reg_status.setWordWrap(True)
        self.reg_status.setStyleSheet("font-size:12px; min-height:18px;")
        body.addWidget(self.reg_status)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("color:#E0E0E0;")
        body.addWidget(sep2)

        # ── Section derniere synchronisation ──
        body.addWidget(self._section_label("Derniere synchronisation"))

        info_frame = QFrame()
        info_frame.setStyleSheet(
            "QFrame{background:#F5F5F5;border:1px solid #E0E0E0;"
            "border-radius:6px;padding:2px;}"
        )
        info_layout = QFormLayout(info_frame)
        info_layout.setSpacing(6)
        info_layout.setContentsMargins(14, 10, 14, 10)

        self.lbl_last_date   = QLabel("—")
        self.lbl_last_by     = QLabel("—")
        self.lbl_last_status = QLabel("—")
        self.lbl_pending     = QLabel("—")

        for lbl in (self.lbl_last_date, self.lbl_last_by,
                    self.lbl_last_status, self.lbl_pending):
            lbl.setFont(QFont("Segoe UI", 11))

        info_layout.addRow("Date / heure :",  self.lbl_last_date)
        info_layout.addRow("Effectuee par :", self.lbl_last_by)
        info_layout.addRow("Statut :",        self.lbl_last_status)
        info_layout.addRow("En attente :",    self.lbl_pending)
        body.addWidget(info_frame)

        body.addStretch()
        scroll.setWidget(container)
        return scroll

    @staticmethod
    def _section_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl.setStyleSheet("color:#1565C0; margin-top:4px;")
        return lbl

    def _build_journal_tab(self) -> QWidget:
        """Onglet 2 — tableau de toutes les entrees de la table core_sync."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 8)
        layout.setSpacing(8)

        # ── Barre d'outils ──
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        lbl_filter = QLabel("Filtrer par statut :")
        lbl_filter.setFont(QFont("Segoe UI", 11))
        toolbar.addWidget(lbl_filter)

        self.journal_filter = QComboBox()
        self.journal_filter.addItems(["Tous", "En attente", "Synchronise", "Erreur"])
        self.journal_filter.setMinimumHeight(32)
        self.journal_filter.setFixedWidth(160)
        self.journal_filter.currentIndexChanged.connect(self._load_journal)
        toolbar.addWidget(self.journal_filter)

        toolbar.addStretch()

        refresh_btn = QPushButton("Actualiser")
        refresh_btn.setMinimumHeight(32)
        refresh_btn.setStyleSheet(
            "QPushButton{background:#1976D2;color:white;border:none;"
            "border-radius:4px;padding:0 14px;font-size:12px;}"
            "QPushButton:hover{background:#1565C0;}"
        )
        refresh_btn.clicked.connect(self._load_journal)
        toolbar.addWidget(refresh_btn)
        layout.addLayout(toolbar)

        # ── Tableau ──
        self.journal_table = QTableWidget()
        self.journal_table.setColumnCount(8)
        self.journal_table.setHorizontalHeaderLabels([
            "Table", "Operation", "ID Enregistrement",
            "Statut", "Cree le", "Cree par", "Synchronise le", "Erreur",
        ])
        self.journal_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.journal_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.journal_table.setAlternatingRowColors(True)
        self.journal_table.verticalHeader().setVisible(False)
        self.journal_table.setSortingEnabled(True)
        hdr = self.journal_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        self.journal_table.setStyleSheet(
            "QTableWidget{border:1px solid #E0E0E0;gridline-color:#F0F0F0;}"
            "QHeaderView::section{background:#1976D2;color:white;padding:6px;"
            "font-weight:bold;border:none;border-right:1px solid #1565C0;}"
            "QTableWidget::item{padding:4px;}"
            "QTableWidget::item:alternate{background:#F5F7FA;}"
            "QTableWidget::item:selected{background:#BBDEFB;color:#000;}"
        )
        layout.addWidget(self.journal_table)

        self.journal_count_lbl = QLabel("")
        self.journal_count_lbl.setStyleSheet(
            "font-size:11px;color:#666;padding:2px 0;"
        )
        layout.addWidget(self.journal_count_lbl)
        return tab

    def _build_history_tab(self) -> QWidget:
        """Onglet 3 — historique des operations push / pull depuis core_sync_history."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 8)
        layout.setSpacing(8)

        # ── Barre d'outils ──
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        lbl_dir = QLabel("Direction :")
        lbl_dir.setFont(QFont("Segoe UI", 11))
        toolbar.addWidget(lbl_dir)

        self.history_filter = QComboBox()
        self.history_filter.addItems(["Tous", "Push", "Pull"])
        self.history_filter.setMinimumHeight(32)
        self.history_filter.setFixedWidth(120)
        self.history_filter.currentIndexChanged.connect(self._load_history)
        toolbar.addWidget(self.history_filter)

        toolbar.addStretch()

        hist_refresh_btn = QPushButton("Actualiser")
        hist_refresh_btn.setMinimumHeight(32)
        hist_refresh_btn.setStyleSheet(
            "QPushButton{background:#1976D2;color:white;border:none;"
            "border-radius:4px;padding:0 14px;font-size:12px;}"
            "QPushButton:hover{background:#1565C0;}"
        )
        hist_refresh_btn.clicked.connect(self._load_history)
        toolbar.addWidget(hist_refresh_btn)
        layout.addLayout(toolbar)

        # ── Tableau ──
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(9)
        self.history_table.setHorizontalHeaderLabels([
            "Direction", "Tables touchées", "Nb enregistrements",
            "Push envoyés", "Push réussis", "Push erreurs",
            "Statut", "Déclenché par", "Date",
        ])
        self.history_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.history_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.history_table.setAlternatingRowColors(True)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setSortingEnabled(True)
        hdr = self.history_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.setStyleSheet(
            "QTableWidget{border:1px solid #E0E0E0;gridline-color:#F0F0F0;}"
            "QHeaderView::section{background:#1976D2;color:white;padding:6px;"
            "font-weight:bold;border:none;border-right:1px solid #1565C0;}"
            "QTableWidget::item{padding:4px;}"
            "QTableWidget::item:alternate{background:#F5F7FA;}"
            "QTableWidget::item:selected{background:#BBDEFB;color:#000;}"
        )
        layout.addWidget(self.history_table)

        self.history_count_lbl = QLabel("")
        self.history_count_lbl.setStyleSheet(
            "font-size:11px;color:#666;padding:2px 0;"
        )
        layout.addWidget(self.history_count_lbl)
        return tab

    def _load_history(self):
        """Charge core_sync_history et remplit le tableau."""
        try:
            sm = _get_sync_manager()
            all_entries = sm.get_history(limit=200)

            filter_idx = self.history_filter.currentIndex()
            if filter_idx == 1:
                all_entries = [e for e in all_entries if e['direction'] == 'push']
            elif filter_idx == 2:
                all_entries = [e for e in all_entries if e['direction'] == 'pull']

            _DIR_STYLE = {
                'push': ('#E3F2FD', '#1565C0', 'PUSH ↑'),
                'pull': ('#E8F5E9', '#2E7D32', 'PULL ↓'),
            }
            _STATUS_STYLE = {
                'success': ('#E8F5E9', '#2E7D32', 'Succès'),
                'partial': ('#FFF8E1', '#E65100', 'Partiel'),
                'error':   ('#FFEBEE', '#C62828', 'Erreur'),
            }

            self.history_table.setSortingEnabled(False)
            self.history_table.setRowCount(len(all_entries))

            for row, entry in enumerate(all_entries):
                direction = entry.get('direction', '')
                d_bg, d_fg, d_lbl = _DIR_STYLE.get(
                    direction, ('#F5F5F5', '#555', direction.upper())
                )
                status = entry.get('status', '')
                s_bg, s_fg, s_lbl = _STATUS_STYLE.get(
                    status, ('#F5F5F5', '#555', status)
                )

                # Formater les tables touchées
                tables_dict = entry.get('tables_affected') or {}
                tables_str = ', '.join(
                    f"{t}({n})" for t, n in tables_dict.items()
                ) if tables_dict else '—'

                push_sent    = entry.get('push_sent')
                push_success = entry.get('push_success')
                push_errors  = entry.get('push_errors')

                values = [
                    d_lbl,
                    tables_str,
                    str(entry.get('records_count', 0)),
                    str(push_sent)    if push_sent    is not None else '—',
                    str(push_success) if push_success is not None else '—',
                    str(push_errors)  if push_errors  is not None else '—',
                    s_lbl,
                    entry.get('triggered_by') or '—',
                    entry.get('created_at')   or '',
                ]
                for col, val in enumerate(values):
                    item = QTableWidgetItem(str(val))
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
                    )
                    if col == 0:  # Direction
                        item.setBackground(QColor(d_bg))
                        item.setForeground(QColor(d_fg))
                        item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                    elif col == 6:  # Statut
                        item.setBackground(QColor(s_bg))
                        item.setForeground(QColor(s_fg))
                        item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                    self.history_table.setItem(row, col, item)

            self.history_table.setSortingEnabled(True)
            self.history_count_lbl.setText(
                f"{len(all_entries)} operation(s) affichee(s)"
            )
        except Exception as e:
            print(f"[SyncConfigDialog] _load_history: {e}")

    def _on_tab_changed(self, index: int):
        """Charge le journal / l'historique au premier affichage de l'onglet."""
        if index == 1:
            self._load_journal()
        elif index == 2:
            self._load_history()

    def _load_journal(self):
        """Interroge core_sync et remplit le tableau."""
        try:
            from ayanna_erp.utils.sync_manager import CoreSync
            sm = _get_sync_manager()
            filter_idx = self.journal_filter.currentIndex()
            # 0=Tous  1=En attente  2=Synchronise  3=Erreur

            # Convertir en dicts DANS la session pour eviter le detachement
            records = []
            with sm._session_scope() as session:
                query = session.query(CoreSync).order_by(
                    CoreSync.created_at.desc()
                )
                if filter_idx == 1:
                    query = query.filter(
                        CoreSync.synced == 0,
                        CoreSync.sync_error.is_(None),
                    )
                elif filter_idx == 2:
                    query = query.filter(CoreSync.synced == 1)
                elif filter_idx == 3:
                    query = query.filter(CoreSync.sync_error.isnot(None))
                for r in query.all():
                    records.append({
                        'table_name': r.table_name or '',
                        'operation':  r.operation  or '',
                        'record_id':  r.record_id  or '',
                        'synced':     r.synced,
                        'sync_error': r.sync_error or '',
                        'created_at': r.created_at or '',
                        'created_by': r.created_by or '',
                        'synced_at':  r.synced_at  or '',
                    })

            _STATUS = {
                'synced':  ('#E8F5E9', '#2E7D32', 'Synchronise'),
                'pending': ('#FFF8E1', '#E65100', 'En attente'),
                'error':   ('#FFEBEE', '#C62828', 'Erreur'),
            }

            self.journal_table.setSortingEnabled(False)
            self.journal_table.setRowCount(len(records))

            for row, rec in enumerate(records):
                if rec['synced'] == 1:
                    s_key = 'synced'
                elif rec['sync_error']:
                    s_key = 'error'
                else:
                    s_key = 'pending'
                bg, fg, label = _STATUS[s_key]

                values = [
                    rec['table_name'],
                    rec['operation'],
                    rec['record_id'],
                    label,
                    rec['created_at'],
                    rec['created_by'],
                    rec['synced_at'],
                    rec['sync_error'],
                ]
                for col, val in enumerate(values):
                    item = QTableWidgetItem(str(val))
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignVCenter
                        | Qt.AlignmentFlag.AlignLeft
                    )
                    if col == 3:  # colonne Statut
                        item.setBackground(QColor(bg))
                        item.setForeground(QColor(fg))
                        item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                    self.journal_table.setItem(row, col, item)

            self.journal_table.setSortingEnabled(True)
            self.journal_count_lbl.setText(
                f"{len(records)} enregistrement(s) affiche(s)"
            )
        except Exception as e:
            print(f"[SyncConfigDialog] _load_journal: {e}")

    # -----------------------------------------------------------------------
    # Chargement de la config sauvegardee
    # -----------------------------------------------------------------------

    def _load_saved_config(self):
        try:
            sm  = _get_sync_manager()
            cfg = sm.get_config()
            if cfg:
                self.url_input.setText(cfg.get('server_url', '') or '')
                self.email_input.setText(cfg.get('server_email', '') or '')
                # Ne pas afficher le mot de passe — juste indiquer qu'il est sauvegarde
                stored_pwd = cfg.get('server_password', '')
                if stored_pwd:
                    self.pwd_input.setText(stored_pwd)
                    self.pwd_input.setPlaceholderText("(mot de passe sauvegarde)")
            self._refresh_stats()
        except Exception as e:
            print(f"[SyncConfigDialog] _load_saved_config: {e}")

    def _refresh_stats(self):
        try:
            sm    = _get_sync_manager()
            stats = sm.get_stats()

            # Derniere sync
            last = stats.get('last_sync_at') or stats.get('last_sync') or '—'
            self.lbl_last_date.setText(str(last))

            by = stats.get('last_sync_by') or '—'
            self.lbl_last_by.setText(str(by))

            status = stats.get('last_sync_status') or '—'
            color  = {
                'success': '#2E7D32',
                'partial': '#E65100',
                'error':   '#C62828',
                'token_ok':'#1565C0',
            }.get(status, '#555')
            self.lbl_last_status.setText(
                f"<span style='color:{color};font-weight:bold;'>{status}</span>"
            )

            pending = stats.get('pending', 0)
            total   = stats.get('total', 0)
            self.lbl_pending.setText(
                f"{pending} operation(s) en attente  "
                f"(total journal : {total})"
            )
        except Exception as e:
            print(f"[SyncConfigDialog] _refresh_stats: {e}")

    # -----------------------------------------------------------------------
    # Actions utilisateur
    # -----------------------------------------------------------------------

    def _toggle_password(self):
        if self.pwd_input.echoMode() == QLineEdit.EchoMode.Password:
            self.pwd_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self._show_pwd_btn.setText("Masquer")
        else:
            self.pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
            self._show_pwd_btn.setText("Afficher")

    def _validate_form(self) -> bool:
        if not self.url_input.text().strip():
            QMessageBox.warning(self, "Champ manquant", "L'URL du serveur est obligatoire.")
            self.url_input.setFocus()
            return False
        if not self.email_input.text().strip():
            QMessageBox.warning(self, "Champ manquant", "L'adresse e-mail est obligatoire.")
            self.email_input.setFocus()
            return False
        if not self.pwd_input.text():
            QMessageBox.warning(self, "Champ manquant", "Le mot de passe est obligatoire.")
            self.pwd_input.setFocus()
            return False
        return True

    def _set_busy(self, busy: bool):
        self.test_btn.setEnabled(not busy)
        self.save_btn.setEnabled(not busy)
        self.sync_btn.setEnabled(not busy)
        self.init_btn.setEnabled(not busy)
        self.reg_btn.setEnabled(not busy)
        self.progress.setVisible(busy)

    def _on_test(self):
        if not self._validate_form():
            return
        self.test_status.setText("Connexion en cours...")
        self.test_status.setStyleSheet("font-size:12px; color:#555;")
        self._set_busy(True)

        sm = _get_sync_manager()
        # Sauvegarder l'URL temporairement pour que login() l'utilise
        sm.save_settings(self.url_input.text().strip())

        self._worker = _SyncWorker(
            sm,
            mode='test',
            email=self.email_input.text().strip(),
            password=self.pwd_input.text(),
            parent=self,
        )
        self._worker.finished.connect(self._on_test_done)
        self._worker.start()

    def _on_test_done(self, result: dict):
        self._set_busy(False)
        if result['ok']:
            self.test_status.setText("Connexion reussie — token obtenu.")
            self.test_status.setStyleSheet("font-size:12px; color:#2E7D32; font-weight:bold;")
        else:
            self.test_status.setText(f"Echec : {result['message']}")
            self.test_status.setStyleSheet("font-size:12px; color:#C62828;")

    def _on_save(self):
        if not self._validate_form():
            return
        try:
            sm = _get_sync_manager()
            sm.save_config(
                server_url=self.url_input.text().strip(),
                server_email=self.email_input.text().strip(),
                server_password=self.pwd_input.text(),
                last_sync_by=_get_current_user_name(),
            )
            self.test_status.setText(
                "Configuration enregistree et chiffree avec succes."
            )
            self.test_status.setStyleSheet(
                "font-size:12px; color:#2E7D32; font-weight:bold;"
            )
            QMessageBox.information(
                self,
                "Enregistre",
                "La configuration de synchronisation a ete enregistree.\n"
                "Les donnees sont chiffrees localement.",
            )
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'enregistrer :\n{e}")

    def _on_sync(self):
        self.test_status.setText("Synchronisation en cours...")
        self.test_status.setStyleSheet("font-size:12px; color:#555;")
        self._set_busy(True)

        sm = _get_sync_manager()
        self._worker = _SyncWorker(sm, mode='sync', parent=self)
        self._worker.finished.connect(self._on_sync_done)
        self._worker.start()

    def _on_sync_done(self, result: dict):
        self._set_busy(False)
        if result['ok']:
            self.test_status.setText(result['message'])
            self.test_status.setStyleSheet("font-size:12px; color:#2E7D32;")
            self._refresh_stats()
            self._load_journal()
            self._load_history()
            QMessageBox.information(self, "Synchronisation", result['message'])
        else:
            self.test_status.setText(f"Erreur : {result['message']}")
            self.test_status.setStyleSheet("font-size:12px; color:#C62828;")
            QMessageBox.critical(
                self, "Erreur de synchronisation",
                f"La synchronisation a echoue :\n\n{result['message']}",
            )

    def _on_register(self):
        """Creer un premier compte utilisateur sur le serveur."""
        name  = self.reg_name_input.text().strip()
        email = self.reg_email_input.text().strip()
        pwd   = self.reg_pwd_input.text()

        if not name:
            QMessageBox.warning(self, "Champ manquant", "Le nom complet est obligatoire.")
            self.reg_name_input.setFocus()
            return
        if not email:
            QMessageBox.warning(self, "Champ manquant", "L'email est obligatoire.")
            self.reg_email_input.setFocus()
            return
        if len(pwd) < 8:
            QMessageBox.warning(
                self, "Mot de passe trop court",
                "Le mot de passe doit faire au moins 8 caracteres."
            )
            self.reg_pwd_input.setFocus()
            return
        if not self.url_input.text().strip():
            QMessageBox.warning(
                self, "URL manquante",
                "Entrez d'abord l'URL du serveur dans la section Connexion."
            )
            return

        # S'assurer que l'URL est sauvegardee
        sm = _get_sync_manager()
        sm.save_settings(self.url_input.text().strip())

        self.reg_status.setText("Creation du compte en cours...")
        self.reg_status.setStyleSheet("font-size:12px; color:#555;")
        self._set_busy(True)

        self._worker = _SyncWorker(
            sm, mode='register',
            email=email, password=pwd, name=name,
            parent=self,
        )
        self._worker.finished.connect(self._on_register_done)
        self._worker.start()

    def _on_register_done(self, result: dict):
        self._set_busy(False)
        if result['ok']:
            self.reg_status.setText(result['message'])
            self.reg_status.setStyleSheet(
                "font-size:12px; color:#2E7D32; font-weight:bold;"
            )
            QMessageBox.information(self, "Compte cree", result['message'])
        else:
            self.reg_status.setText(f"Echec : {result['message']}")
            self.reg_status.setStyleSheet("font-size:12px; color:#C62828;")
            QMessageBox.critical(
                self, "Erreur creation compte",
                f"Impossible de creer le compte :\n\n{result['message']}",
            )

    def _on_initialize(self):
        """Pre-charge toutes les donnees locales dans core_sync (premier demarrage)."""
        reply = QMessageBox.question(
            self,
            "Initialiser la synchronisation",
            "Cette action va enregistrer TOUTES les donnees locales existantes\n"
            "dans le journal de synchronisation comme operations en attente.\n\n"
            "A utiliser UNE SEULE FOIS au premier demarrage.\n\n"
            "Continuer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._set_busy(True)
        sm = _get_sync_manager()
        self._worker = _SyncWorker(sm, mode='init', parent=self)
        self._worker.finished.connect(self._on_initialize_done)
        self._worker.start()

    def _on_initialize_done(self, result: dict):
        self._set_busy(False)
        if result['ok']:
            self._refresh_stats()
            self._load_journal()
            QMessageBox.information(
                self, "Initialisation terminee", result['message']
            )
        else:
            QMessageBox.critical(
                self, "Erreur d'initialisation",
                f"L'initialisation a echoue :\n\n{result['message']}",
            )
