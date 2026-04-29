"""
PaymentModeWidget – gestion des modes de paiement de l'entreprise.

Accessible depuis : Menu Configuration ▸ Modes de paiement.

Règles métier :
  • 4 modes protégés (is_default=1) : Espèces, Banque, Mobile Money, Crédit.
    Ils NE peuvent PAS être supprimés.
  • L'utilisateur peut :
      – Modifier le libellé et la description d'un mode.
      – Associer un compte comptable (compte trésorerie / caisse) à chaque mode.
      – Créer des modes supplémentaires personnalisés (supprimables).
      – Activer / désactiver un mode.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QCheckBox,
    QDialog, QFormLayout, QHeaderView, QAbstractItemView,
    QMessageBox, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QBrush


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _get_enterprise_id() -> int:
    try:
        from ayanna_erp.core.session_manager import SessionManager
        eid = SessionManager.get_current_enterprise_id()
        return eid if eid else 1
    except Exception:
        return 1


def _get_comptes() -> list:
    """Retourne [(id, 'numero – nom'), …] depuis compta_comptes."""
    try:
        from ayanna_erp.database.database_manager import get_database_manager
        from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaComptes
        db = get_database_manager()
        with db.session_scope() as session:
            rows = (session.query(ComptaComptes)
                    .filter(ComptaComptes.actif == True)
                    .order_by(ComptaComptes.numero)
                    .all())
            return [(r.id, f"{r.numero} – {r.nom}") for r in rows]
    except Exception:
        return []


def _load_modes(enterprise_id: int) -> list:
    """Retourne la liste des PaymentMode pour l'entreprise."""
    try:
        from ayanna_erp.database.database_manager import get_database_manager, PaymentMode
        db = get_database_manager()
        with db.session_scope() as session:
            modes = (session.query(PaymentMode)
                     .filter_by(enterprise_id=enterprise_id)
                     .order_by(PaymentMode.sort_order, PaymentMode.id)
                     .all())
            result = []
            for m in modes:
                result.append({
                    'id': m.id,
                    'code': m.code,
                    'label': m.label,
                    'description': m.description or '',
                    'compte_id': m.compte_id,
                    'compte_label': m.compte_label or '',
                    'is_default': bool(m.is_default),
                    'is_active': bool(m.is_active),
                    'sort_order': m.sort_order,
                })
            return result
    except Exception as e:
        print(f"_load_modes error: {e}")
        return []


# ──────────────────────────────────────────────────────────────────────────────
# Edit dialog
# ──────────────────────────────────────────────────────────────────────────────

class _EditModeDialog(QDialog):
    """Dialogue de création / modification d'un mode de paiement."""

    def __init__(self, mode: dict | None = None, comptes: list | None = None,
                 parent=None):
        super().__init__(parent)
        self._mode = mode or {}
        self._comptes = comptes or []
        is_new = not bool(mode)
        self.setWindowTitle("Nouveau mode de paiement" if is_new
                            else f"Modifier – {mode.get('label', '')}")
        self.setMinimumWidth(460)
        self.setModal(True)
        self._build_ui(is_new)

    def _build_ui(self, is_new: bool):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)

        # Code (modifiable uniquement à la création)
        self.code_edit = QLineEdit(self._mode.get('code', ''))
        self.code_edit.setPlaceholderText("Ex : cheque, virement…")
        self.code_edit.setMaxLength(50)
        if not is_new:
            self.code_edit.setReadOnly(True)
            self.code_edit.setStyleSheet("background:#ECF0F1;color:#888;")
        form.addRow("Code * :", self.code_edit)

        # Libellé
        self.label_edit = QLineEdit(self._mode.get('label', ''))
        self.label_edit.setPlaceholderText("Ex : Chèque bancaire")
        self.label_edit.setMaxLength(150)
        form.addRow("Libellé * :", self.label_edit)

        # Description
        self.desc_edit = QTextEdit(self._mode.get('description', ''))
        self.desc_edit.setFixedHeight(64)
        self.desc_edit.setPlaceholderText(
            "Ex : liste des opérateurs acceptés, instructions…")
        form.addRow("Description :", self.desc_edit)

        # Compte comptable associé
        self.compte_combo = QComboBox()
        self.compte_combo.addItem("— aucun compte associé —", None)
        for cid, clabel in self._comptes:
            self.compte_combo.addItem(clabel, cid)
        # Présélectionner le compte actuel
        current_cid = self._mode.get('compte_id')
        if current_cid:
            for i in range(self.compte_combo.count()):
                if self.compte_combo.itemData(i) == current_cid:
                    self.compte_combo.setCurrentIndex(i)
                    break
        form.addRow("Compte caisse/trésorerie :", self.compte_combo)

        # Actif
        self.chk_active = QCheckBox("Mode actif (visible dans les formulaires de paiement)")
        self.chk_active.setChecked(self._mode.get('is_active', True))
        form.addRow("", self.chk_active)

        layout.addLayout(form)

        # Info si mode protégé
        if self._mode.get('is_default'):
            note = QLabel(
                "ℹ️  Ce mode est protégé : le code ne peut pas être modifié "
                "et il ne peut pas être supprimé.")
            note.setWordWrap(True)
            note.setStyleSheet(
                "color:#1565C0;background:#E3F2FD;border-radius:4px;"
                "padding:6px;font-size:11px;")
            layout.addWidget(note)

        # Boutons
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        self.btn_ok = QPushButton("Enregistrer")
        self.btn_ok.setDefault(True)
        self.btn_ok.setStyleSheet(
            "QPushButton{background:#1976D2;color:white;padding:7px 20px;"
            "border-radius:4px;}QPushButton:hover{background:#1565C0;}")
        self.btn_ok.clicked.connect(self._validate)
        btn_row.addWidget(btn_cancel)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_ok)
        layout.addLayout(btn_row)

    def _validate(self):
        if not self.code_edit.text().strip():
            QMessageBox.warning(self, "Code manquant",
                                "Le code du mode de paiement est obligatoire.")
            return
        if not self.label_edit.text().strip():
            QMessageBox.warning(self, "Libellé manquant",
                                "Le libellé du mode de paiement est obligatoire.")
            return
        self.accept()

    def get_data(self) -> dict:
        idx = self.compte_combo.currentIndex()
        cid = self.compte_combo.itemData(idx)
        clabel = ''
        if cid:
            clabel = self.compte_combo.currentText()
        return {
            'code':        self.code_edit.text().strip(),
            'label':       self.label_edit.text().strip(),
            'description': self.desc_edit.toPlainText().strip(),
            'compte_id':   cid,
            'compte_label': clabel,
            'is_active':   int(self.chk_active.isChecked()),
        }


# ──────────────────────────────────────────────────────────────────────────────
# Main widget
# ──────────────────────────────────────────────────────────────────────────────

class PaymentModeWidget(QWidget):
    """Fenêtre de gestion des modes de paiement."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._enterprise_id = _get_enterprise_id()
        self._modes: list = []
        self._comptes: list = []
        self._build_ui()
        self._comptes = _get_comptes()
        self.refresh()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        # Titre
        title = QLabel("💳  Modes de paiement")
        title.setStyleSheet(
            "font-size:18px;font-weight:bold;color:#2C3E50;")
        root.addWidget(title)

        subtitle = QLabel(
            "Configurez les modes de paiement acceptés par votre établissement. "
            "Associez un compte comptable (caisse / trésorerie) à chaque mode "
            "pour que les écritures soient passées automatiquement.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color:#555;font-size:11px;")
        root.addWidget(subtitle)

        # Barre d'actions
        bar = QHBoxLayout()
        btn_add = QPushButton("➕  Nouveau mode")
        btn_add.setStyleSheet(
            "QPushButton{background:#27AE60;color:white;padding:6px 16px;"
            "border-radius:4px;font-weight:bold;}"
            "QPushButton:hover{background:#219A52;}")
        btn_add.clicked.connect(self._on_add)
        bar.addWidget(btn_add)
        bar.addStretch()
        btn_refresh = QPushButton("↻  Actualiser")
        btn_refresh.setFixedHeight(30)
        btn_refresh.clicked.connect(self.refresh)
        bar.addWidget(btn_refresh)
        root.addLayout(bar)

        # Tableau
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            'Code', 'Libellé', 'Description',
            'Compte associé', 'Actif', 'Protégé', 'Actions',
        ])
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setStyleSheet(
            "QTableWidget{border:1px solid #ddd;}"
            "QHeaderView::section{background:#2C3E50;color:white;"
            "padding:6px;font-weight:bold;}")
        root.addWidget(self.table)

        # Légende
        legend = QLabel(
            "🔒 Modes protégés (fond bleu clair) : libellé et compte modifiables, "
            "mais code et suppression verrouillés.")
        legend.setStyleSheet("color:#777;font-size:10px;")
        root.addWidget(legend)

    # ── Data ──────────────────────────────────────────────────────────────────

    def refresh(self):
        self._modes = _load_modes(self._enterprise_id)
        self._fill_table()

    def _fill_table(self):
        self.table.setRowCount(0)
        for mode in self._modes:
            r = self.table.rowCount()
            self.table.insertRow(r)

            is_default = mode['is_default']
            is_active  = mode['is_active']
            bg = QColor('#E3F2FD') if is_default else (
                QColor('#FAFAFA') if is_active else QColor('#FDECEA'))

            def _cell(text, align=Qt.AlignmentFlag.AlignCenter):
                item = QTableWidgetItem(str(text))
                item.setTextAlignment(align)
                item.setBackground(QBrush(bg))
                return item

            self.table.setItem(r, 0, _cell(mode['code']))
            self.table.setItem(r, 1, _cell(mode['label']))
            self.table.setItem(r, 2, _cell(
                mode['description'][:60] + ('…' if len(mode['description']) > 60 else ''),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter))
            self.table.setItem(r, 3, _cell(
                mode['compte_label'] or '—',
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter))
            self.table.setItem(r, 4, _cell('✅ Oui' if is_active else '❌ Non'))
            lock_item = _cell('🔒 Protégé' if is_default else '—')
            if is_default:
                lock_item.setForeground(QBrush(QColor('#1565C0')))
                lock_item.setFont(QFont('', -1, QFont.Weight.Bold))
            self.table.setItem(r, 5, lock_item)

            # Boutons Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)

            btn_edit = QPushButton("✏️ Modifier")
            btn_edit.setStyleSheet(
                "QPushButton{background:#1976D2;color:white;border-radius:3px;"
                "padding:3px 10px;font-size:10px;}"
                "QPushButton:hover{background:#1565C0;}")
            btn_edit.clicked.connect(
                lambda _, m=mode: self._on_edit(m))
            actions_layout.addWidget(btn_edit)

            if not is_default:
                btn_del = QPushButton("🗑️ Suppr.")
                btn_del.setStyleSheet(
                    "QPushButton{background:#E53935;color:white;border-radius:3px;"
                    "padding:3px 10px;font-size:10px;}"
                    "QPushButton:hover{background:#B71C1C;}")
                btn_del.clicked.connect(
                    lambda _, m=mode: self._on_delete(m))
                actions_layout.addWidget(btn_del)

            actions_layout.addStretch()
            self.table.setCellWidget(r, 6, actions_widget)

        self.table.resizeRowsToContents()

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _on_add(self):
        dlg = _EditModeDialog(comptes=self._comptes, parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.get_data()
        try:
            from ayanna_erp.database.database_manager import get_database_manager, PaymentMode
            db = get_database_manager()
            with db.session_scope() as session:
                # Vérifier unicité du code pour cette entreprise
                if session.query(PaymentMode).filter_by(
                        enterprise_id=self._enterprise_id,
                        code=data['code']).first():
                    QMessageBox.warning(
                        self, "Code dupliqué",
                        f"Un mode avec le code « {data['code']} » existe déjà.")
                    return
                # Déterminer sort_order suivant
                from sqlalchemy import func
                max_order = session.query(
                    func.max(PaymentMode.sort_order)).filter_by(
                    enterprise_id=self._enterprise_id).scalar() or 0
                session.add(PaymentMode(
                    enterprise_id=self._enterprise_id,
                    code=data['code'],
                    label=data['label'],
                    description=data['description'] or None,
                    compte_id=data['compte_id'],
                    compte_label=data['compte_label'] or None,
                    is_default=0,
                    is_active=data['is_active'],
                    sort_order=max_order + 1,
                ))
            QMessageBox.information(
                self, "Mode créé",
                f"Le mode « {data['label']} » a été créé.")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de créer le mode :\n{e}")

    def _on_edit(self, mode: dict):
        dlg = _EditModeDialog(mode=mode, comptes=self._comptes, parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.get_data()
        try:
            from ayanna_erp.database.database_manager import get_database_manager, PaymentMode
            db = get_database_manager()
            with db.session_scope() as session:
                m = session.query(PaymentMode).filter_by(id=mode['id']).first()
                if not m:
                    return
                # Pour les modes protégés : ne pas changer le code
                if not m.is_default:
                    m.code = data['code']
                m.label       = data['label']
                m.description = data['description'] or None
                m.compte_id   = data['compte_id']
                m.compte_label = data['compte_label'] or None
                m.is_active   = data['is_active']
            QMessageBox.information(
                self, "Mode modifié",
                f"Le mode « {data['label']} » a été mis à jour.")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de modifier le mode :\n{e}")

    def _on_delete(self, mode: dict):
        if mode['is_default']:
            QMessageBox.warning(
                self, "Suppression impossible",
                "Ce mode est protégé et ne peut pas être supprimé.")
            return
        rep = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Supprimer le mode « {mode['label']} » ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if rep != QMessageBox.StandardButton.Yes:
            return
        try:
            from ayanna_erp.database.database_manager import get_database_manager, PaymentMode
            db = get_database_manager()
            with db.session_scope() as session:
                m = session.query(PaymentMode).filter_by(id=mode['id']).first()
                if m and not m.is_default:
                    session.delete(m)
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de supprimer le mode :\n{e}")


# ──────────────────────────────────────────────────────────────────────────────
# Helper public : récupérer les modes actifs d'une entreprise
# ──────────────────────────────────────────────────────────────────────────────

def get_active_payment_modes(enterprise_id: int | None = None) -> list:
    """Retourne la liste des modes actifs pour l'entreprise.

    Utilisable depuis n'importe quel module pour peupler une ComboBox
    de méthode de paiement de façon dynamique.

    Retourne : [{'code': str, 'label': str, 'compte_id': int|None,
                 'compte_label': str, 'is_default': bool}, …]
    """
    eid = enterprise_id or _get_enterprise_id()
    try:
        from ayanna_erp.database.database_manager import get_database_manager, PaymentMode
        db = get_database_manager()
        with db.session_scope() as session:
            modes = (session.query(PaymentMode)
                     .filter_by(enterprise_id=eid, is_active=1)
                     .order_by(PaymentMode.sort_order, PaymentMode.id)
                     .all())
            return [
                {
                    'id': m.id,
                    'code': m.code,
                    'label': m.label,
                    'compte_id': m.compte_id,
                    'compte_label': m.compte_label or '',
                    'is_default': bool(m.is_default),
                }
                for m in modes
            ]
    except Exception:
        # Fallback : 4 modes de base si la table n'est pas encore disponible
        return [
            {'id': None, 'code': 'cash',         'label': 'Espèces',       'compte_id': None, 'compte_label': '', 'is_default': True},
            {'id': None, 'code': 'banque',        'label': 'Banque',         'compte_id': None, 'compte_label': '', 'is_default': True},
            {'id': None, 'code': 'mobile_money',  'label': 'Mobile Money',   'compte_id': None, 'compte_label': '', 'is_default': True},
            {'id': None, 'code': 'credit',        'label': 'Crédit',        'compte_id': None, 'compte_label': '', 'is_default': True},
        ]
