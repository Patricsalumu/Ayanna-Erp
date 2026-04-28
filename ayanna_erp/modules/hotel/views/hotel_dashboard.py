"""
HotelDashboard – onglet 1 : vue d'ensemble des chambres par catégorie.
"""
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QPushButton, QLabel, QFrame, QGridLayout,
    QSizePolicy, QMessageBox, QDialog, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QDateTimeEdit, QFormLayout,
    QCheckBox, QComboBox
)
from PyQt6.QtCore import Qt, QTimer, QDateTime
from PyQt6.QtGui import QFont, QColor, QBrush

from ayanna_erp.modules.hotel.services.room_service import RoomService
from ayanna_erp.modules.hotel.services.reservation_service import ReservationService
from ayanna_erp.modules.hotel.utils.helpers import (
    room_status_label, ROOM_STATUS_COLORS, fmt_date, fmt_datetime
)

_room_svc = RoomService()
_res_svc  = ReservationService()


class CheckinDialog(QDialog):
    """Dialogue de recherche et sélection de réservation pour le check-in."""

    def __init__(self, room, current_user=None, parent=None):
        super().__init__(parent)
        self.room = room
        self.current_user = current_user
        if isinstance(current_user, dict):
            _role = current_user.get('role', '')
        else:
            _role = getattr(current_user, 'role', '')
        self._is_super_admin = (_role == 'super_admin')
        self.setWindowTitle(f"Check-in – Chambre {room.number}")
        self.setMinimumSize(640, 420)
        self.setModal(True)
        self._reservations = []
        self._build_ui()
        self._load_reservations()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # En-tête
        room_cat_name = self.room.category.name if self.room.category else '-'
        self._room_cat_price = (
            self.room.category.price_per_night if self.room.category else 0.0)
        lbl = QLabel(
            f"Sélectionnez une réservation à affecter à la chambre "
            f"<b>{self.room.number}</b> "
            f"(catégorie : {room_cat_name} – {self._room_cat_price:,.0f}/nuit)"
        )
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        # Option upgrade
        upgrade_row = QHBoxLayout()
        self.chk_upgrade = QCheckBox(
            "⬆️  Afficher les réservations de catégories inférieures (Upgrade)")
        self.chk_upgrade.setStyleSheet(
            "QCheckBox{font-weight:bold;color:#6A1B9A;font-size:11px;}")
        self.chk_upgrade.toggled.connect(lambda: self._load_reservations(
            self.search.text().strip().lower()))
        upgrade_row.addWidget(self.chk_upgrade)
        upgrade_row.addStretch()
        layout.addLayout(upgrade_row)

        # Barre de recherche
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Rechercher (code, client)…")
        self.search.setFixedHeight(32)
        self.search.textChanged.connect(self._filter)
        layout.addWidget(self.search)

        # Tableau réservations
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ['Code', 'Client', 'Catégorie', 'Prix/nuit', 'Entrée prévue', 'Sortie prévue'])
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setStyleSheet(
            "QHeaderView::section{background:#34495E;color:white;"
            "padding:5px;font-weight:bold;}")
        self.table.doubleClicked.connect(self._accept_selection)
        layout.addWidget(self.table)

        # Date check-in
        form = QFormLayout()
        self.dt_checkin = QDateTimeEdit(QDateTime.currentDateTime())
        self.dt_checkin.setCalendarPopup(True)
        self.dt_checkin.setDisplayFormat("dd/MM/yyyy HH:mm")
        if not self._is_super_admin:
            self.dt_checkin.setReadOnly(True)
            self.dt_checkin.setStyleSheet("background:#ECF0F1;color:#888;")
            note = QLabel("(Date fixée à maintenant — réservé au super administrateur)")
            note.setStyleSheet("color:#888;font-size:10px;")
            form.addRow("Date check-in :", self.dt_checkin)
            form.addRow("", note)
        else:
            # Super admin : peut antidater librement — pas de borne minimale
            from PyQt6.QtCore import QDateTime as _QDT
            self.dt_checkin.setMinimumDateTime(_QDT(
                _QDT.fromString("2000-01-01 00:00", "yyyy-MM-dd HH:mm")))
            # Pas de borne maximale stricte : le super admin peut aussi saisir
            # la date réelle passée (antidatage) ou l'heure actuelle
            self.dt_checkin.clearMaximumDateTime()
            self.dt_checkin.setToolTip(
                "Super admin : vous pouvez antidater le check-in.\n"
                "Utilisez le calendrier ou saisissez directement la date.")
            self.dt_checkin.setStyleSheet(
                "QDateTimeEdit{background:#FFF9C4;border:1px solid #F9A825;"
                "border-radius:4px;padding:2px 6px;}")
            note_admin = QLabel("⚠️ Antidatage autorisé — super administrateur uniquement")
            note_admin.setStyleSheet("color:#E65100;font-size:10px;font-weight:bold;")
            form.addRow("Date check-in :", self.dt_checkin)
            form.addRow("", note_admin)
        layout.addLayout(form)

        # Boutons
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        self.btn_ok = QPushButton("✅ Check-in")
        self.btn_ok.setEnabled(False)
        self.btn_ok.setStyleSheet(
            "QPushButton{background:#1976D2;color:white;padding:6px 18px;"
            "border-radius:4px;}QPushButton:hover{background:#1565C0;}"
            "QPushButton:disabled{background:#BDC3C7;}")
        self.btn_ok.clicked.connect(self._accept_selection)
        self.table.selectionModel().selectionChanged.connect(
            lambda: self.btn_ok.setEnabled(
                self.table.currentRow() >= 0))
        btn_row.addWidget(btn_cancel)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_ok)
        layout.addLayout(btn_row)

    def _load_reservations(self, search: str = ''):
        cat_name = self.room.category.name if self.room.category else ''
        room_price = self._room_cat_price
        all_res = (_res_svc.get_all_reservations(status='en_attente') +
                   _res_svc.get_all_reservations(status='confirmee'))

        if self.chk_upgrade.isChecked():
            # Upgrade : afficher toutes les réservations de catégories
            # dont le prix/nuit est STRICTEMENT inférieur à celui de cette chambre
            # (+ les réservations de même catégorie normales)
            all_cats = {c.name: c.price_per_night
                        for c in _room_svc.get_all_categories()}
            self._reservations = [
                r for r in all_res
                if all_cats.get(r['category'], 0) <= room_price
            ]
        else:
            # Mode normal : uniquement la même catégorie
            self._reservations = [
                r for r in all_res if r['category'] == cat_name]

        self._fill_table(search)

    def _filter(self, text: str):
        self._fill_table(text.strip().lower())

    def _fill_table(self, search: str = ''):
        cat_name = self.room.category.name if self.room.category else ''
        all_cats = {c.name: c.price_per_night
                    for c in _room_svc.get_all_categories()}
        room_price = self._room_cat_price

        self.table.setRowCount(0)
        for res in self._reservations:
            if search and (
                search not in res['code'].lower()
                and search not in res['client_name'].lower()
            ):
                continue
            r = self.table.rowCount()
            self.table.insertRow(r)
            cat_price = all_cats.get(res['category'], 0)
            is_upgrade = (res['category'] != cat_name and cat_price < room_price)
            price_str = f"{cat_price:,.0f}" if cat_price else '-'
            vals = [
                res['code'], res['client_name'], res['category'],
                price_str,
                fmt_date(res['date_entree_prevue']),
                fmt_date(res['date_sortie_prevue']),
            ]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setData(Qt.ItemDataRole.UserRole, res['id'])
                if is_upgrade:
                    # Colorer les lignes upgrade en violet clair
                    item.setBackground(QBrush(QColor('#EDE7F6')))
                    item.setForeground(QBrush(QColor('#4A148C')))
                self.table.setItem(r, col, item)

    def _accept_selection(self):
        if self.table.currentRow() < 0:
            QMessageBox.information(self, "Sélection",
                                    "Veuillez sélectionner une réservation.")
            return
        self.accept()

    def get_reservation_id(self) -> int:
        item = self.table.item(self.table.currentRow(), 0)
        return item.data(Qt.ItemDataRole.UserRole)

    def get_checkin_datetime(self) -> datetime:
        qdt = self.dt_checkin.dateTime().toPyDateTime()
        return qdt


class MoveRoomDialog(QDialog):
    """Dialogue de déménagement : transférer une réservation en cours vers une
    autre chambre disponible de la même catégorie (Moov Room)."""

    def __init__(self, reservation_id: int, current_room, category_id: int,
                 category_name: str, parent=None):
        super().__init__(parent)
        self.reservation_id = reservation_id
        self.current_room = current_room
        self.category_id = category_id
        self.setWindowTitle(f"Moov Room – Déménagement ({category_name})")
        self.setMinimumSize(500, 340)
        self.setModal(True)
        self._rooms = []
        self._build_ui()
        self._load_rooms()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        lbl = QLabel(
            f"Chambre actuelle : <b>{self.current_room}</b><br>"
            f"Sélectionnez la chambre de destination (même catégorie, disponible) :"
        )
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Chambre', 'Statut', 'Catégorie'])
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setStyleSheet(
            "QHeaderView::section{background:#34495E;color:white;"
            "padding:5px;font-weight:bold;}")
        self.table.doubleClicked.connect(self._accept_selection)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        self.btn_ok = QPushButton("🔀 Déménager")
        self.btn_ok.setEnabled(False)
        self.btn_ok.setStyleSheet(
            "QPushButton{background:#6A1B9A;color:white;padding:6px 18px;"
            "border-radius:4px;}QPushButton:hover{background:#4A148C;}"
            "QPushButton:disabled{background:#BDC3C7;}")
        self.btn_ok.clicked.connect(self._accept_selection)
        self.table.selectionModel().selectionChanged.connect(
            lambda: self.btn_ok.setEnabled(self.table.currentRow() >= 0))
        btn_row.addWidget(btn_cancel)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_ok)
        layout.addLayout(btn_row)

    def _load_rooms(self):
        rooms = _room_svc.get_all_rooms(category_id=self.category_id)
        # Exclure la chambre actuelle et les non-disponibles
        self._rooms = [
            r for r in rooms
            if r.status == 'disponible' and r.number != self.current_room
        ]
        self.table.setRowCount(0)
        for room in self._rooms:
            r = self.table.rowCount()
            self.table.insertRow(r)
            vals = [room.number, room_status_label(room.status),
                    room.category.name if room.category else '-']
            for col, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setData(Qt.ItemDataRole.UserRole, room.id)
                self.table.setItem(r, col, item)
        if not self._rooms:
            QLabel  # will be shown via message
            self.table.setRowCount(1)
            no_item = QTableWidgetItem("Aucune chambre disponible dans cette catégorie")
            no_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            no_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.table.setItem(0, 0, no_item)
            self.table.setSpan(0, 0, 1, 3)

    def _accept_selection(self):
        if self.table.currentRow() < 0 or not self._rooms:
            QMessageBox.information(self, "Sélection",
                                    "Veuillez sélectionner une chambre.")
            return
        self.accept()

    def get_new_room_id(self) -> int:
        item = self.table.item(self.table.currentRow(), 0)
        return item.data(Qt.ItemDataRole.UserRole)


class RoomCard(QFrame):
    """Carte visuelle pour une chambre."""

    def __init__(self, room, reservation, assign_cb, move_cb=None, parent=None):
        super().__init__(parent)
        self.room = room
        self.reservation = reservation
        self.assign_cb = assign_cb
        self.move_cb = move_cb
        self._build()

    def _build(self):
        color = ROOM_STATUS_COLORS.get(self.room.status, '#333')
        self.setFixedSize(175, 195)
        self.setStyleSheet(
            f"QFrame{{border:2px solid {color};border-radius:10px;"
            f"background:white;}}"
            f"QFrame:hover{{background:#F8F9FA;}}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Numéro + badge statut
        top = QHBoxLayout()
        lbl_num = QLabel(f"🏨 {self.room.number}")
        lbl_num.setStyleSheet("font-size:16px;font-weight:bold;")
        top.addWidget(lbl_num)
        badge = QLabel(room_status_label(self.room.status))
        badge.setStyleSheet(
            f"background:{color};color:white;border-radius:4px;"
            f"padding:2px 6px;font-size:10px;font-weight:bold;")
        top.addWidget(badge, 0, Qt.AlignmentFlag.AlignRight)
        layout.addLayout(top)

        # Catégorie (si libre) ou code réservation (si occupée)
        if self.reservation:
            res_code = getattr(self.reservation, 'reservation_code', '-')
            layout.addWidget(QLabel(
                f"<span style='color:#E74C3C;font-size:11px;font-weight:bold;'"
                f">🔑 {res_code}</span>"))
        else:
            cat_name = self.room.category.name if self.room.category else '-'
            layout.addWidget(QLabel(
                f"<span style='color:#888;font-size:11px;'>{cat_name}</span>"))

        # Info réservation active
        if self.reservation:
            res = self.reservation
            client_name = ''
            if res.client:
                client_name = (res.client.nom or '') + ' ' + (
                    res.client.prenom or '')
            layout.addWidget(QLabel(
                f"<b>{client_name.strip()}</b>"))
            layout.addWidget(QLabel(
                f"📅 {fmt_date(res.date_entree_prevue)} → {fmt_date(res.date_sortie_prevue)}"))
            nuits = max(
                (res.date_sortie_prevue.date() - res.date_entree_prevue.date()).days, 1
            ) if res.date_entree_prevue and res.date_sortie_prevue else '-'
            layout.addWidget(QLabel(f"🌙 {nuits} nuit(s)"))
            # Bouton Moov Room (déménagement)
            layout.addStretch()
            if self.move_cb and self.room.status == 'occupee':
                btn_move = QPushButton("🔀 Moov Room")
                btn_move.setStyleSheet(
                    "QPushButton{background:#6A1B9A;color:white;border-radius:4px;"
                    "padding:3px;font-size:9px;}QPushButton:hover{background:#4A148C;}")
                btn_move.clicked.connect(
                    lambda: self.move_cb(self.room, self.reservation))
                layout.addWidget(btn_move)
        else:
            layout.addWidget(QLabel("<span style='color:#27AE60;'>Libre</span>"))
            layout.addStretch()
            btn = QPushButton("✅ Check-in")
            btn.setStyleSheet(
                "QPushButton{background:#1976D2;color:white;border-radius:4px;"
                "padding:4px;font-size:10px;}QPushButton:hover{background:#1565C0;}")
            btn.clicked.connect(lambda: self.assign_cb(self.room))
            layout.addWidget(btn)


_CARD_W = 175
_CARD_H = 195
_CARD_SPACING = 12


class _CardsContainer(QWidget):
    """Container qui recalcule les colonnes à chaque redimensionnement."""

    def __init__(self, rebuild_cb, parent=None):
        super().__init__(parent)
        self._rebuild_cb = rebuild_cb
        self._last_col_max = -1

    def resizeEvent(self, event):
        super().resizeEvent(event)
        col_max = max(1, self.width() // (_CARD_W + _CARD_SPACING))
        if col_max != self._last_col_max:
            self._last_col_max = col_max
            self._rebuild_cb(col_max)


class HotelDashboard(QWidget):

    def __init__(self, current_user=None, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self._selected_cat_id = None
        self._categories = []
        self._rooms = []
        self._cached_cards = []   # list of RoomCard widgets (current filter)
        self._build_ui()
        self.refresh()

        # Rafraîchissement automatique toutes les 60 s
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(60_000)

    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(10, 10, 10, 10)

        # Titre + bouton refresh
        title_row = QHBoxLayout()
        title = QLabel("Tableau de bord – Chambres")
        title.setStyleSheet("font-size:18px;font-weight:bold;color:#2C3E50;")
        title_row.addWidget(title)
        title_row.addStretch()

        # Légende
        for status, color in ROOM_STATUS_COLORS.items():
            dot = QLabel(f"● {room_status_label(status)}")
            dot.setStyleSheet(f"color:{color};font-size:11px;margin-right:8px;")
            title_row.addWidget(dot)

        btn_refresh = QPushButton("↻ Actualiser")
        btn_refresh.setFixedHeight(30)
        btn_refresh.clicked.connect(self.refresh)
        title_row.addWidget(btn_refresh)
        root.addLayout(title_row)

        # Filtre catégories
        self.cat_bar = QHBoxLayout()
        root.addLayout(self.cat_bar)

        # Zone de cartes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;}")
        self.cards_container = _CardsContainer(self._apply_col_max)
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setSpacing(_CARD_SPACING)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(self.cards_container)
        root.addWidget(scroll)

        # Barre de statistiques
        self.stat_bar = QLabel()
        self.stat_bar.setStyleSheet("color:#555;font-size:11px;padding:4px;")
        root.addWidget(self.stat_bar)

    # ------------------------------------------------------------------
    def refresh(self):
        self._categories = _room_svc.get_all_categories()
        self._rooms = _room_svc.get_all_rooms()
        self._rebuild_cat_bar()
        self._rebuild_cards()

    def _rebuild_cat_bar(self):
        # Vider
        while self.cat_bar.count():
            item = self.cat_bar.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        btn_all = QPushButton("Toutes")
        btn_all.setCheckable(True)
        btn_all.setChecked(self._selected_cat_id is None)
        btn_all.setFixedHeight(30)
        btn_all.clicked.connect(lambda: self._filter_cat(None))
        btn_all.setStyleSheet(self._cat_btn_style(None))
        self.cat_bar.addWidget(btn_all)

        for cat in self._categories:
            b = QPushButton(cat.name)
            b.setCheckable(True)
            b.setChecked(self._selected_cat_id == cat.id)
            b.setFixedHeight(30)
            b.clicked.connect(lambda _=False, c=cat: self._filter_cat(c.id))
            b.setStyleSheet(self._cat_btn_style(cat.id))
            self.cat_bar.addWidget(b)
        self.cat_bar.addStretch()

    def _cat_btn_style(self, cat_id) -> str:
        selected = cat_id == self._selected_cat_id
        bg = "#1976D2" if selected else "#ECF0F1"
        fg = "white" if selected else "#2C3E50"
        return (f"QPushButton{{background:{bg};color:{fg};border-radius:4px;"
                f"padding:0 12px;font-weight:{'bold' if selected else 'normal'};}}"
                f"QPushButton:hover{{background:#1565C0;color:white;}}")

    def _filter_cat(self, cat_id):
        self._selected_cat_id = cat_id
        self._rebuild_cat_bar()
        self._rebuild_cards()

    def _rebuild_cards(self):
        """Reconstruit la liste de cartes (avec appels DB) puis place dans la grille."""
        # Supprimer les cartes existantes
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cached_cards.clear()

        rooms = self._rooms
        if self._selected_cat_id is not None:
            rooms = [r for r in rooms
                     if r.hotel_category_id == self._selected_cat_id]

        total = len(rooms)
        dispo = sum(1 for r in rooms if r.status == 'disponible')
        occupee = sum(1 for r in rooms if r.status == 'occupee')

        for room in rooms:
            res = _room_svc.get_room_with_active_reservation(room.id)
            card = RoomCard(room, res, self._on_assign, self._on_move, self)
            self._cached_cards.append(card)

        # Placement initial selon la largeur courante
        col_max = max(1, self.cards_container.width() // (_CARD_W + _CARD_SPACING))
        if col_max < 1:
            col_max = 4  # valeur par défaut avant premier resize
        self._place_cards(col_max)

        self.stat_bar.setText(
            f"Total : {total}  |  Disponibles : {dispo}  |  "
            f"Occupées : {occupee}  |  Autres : {total - dispo - occupee}")

    def _place_cards(self, col_max):
        """Place les cartes en cache dans la grille avec col_max colonnes."""
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            # Ne pas deleteLater – les widgets sont en cache
        for idx, card in enumerate(self._cached_cards):
            self.cards_layout.addWidget(card, idx // col_max, idx % col_max)

    def _apply_col_max(self, col_max):
        """Appelé par _CardsContainer.resizeEvent – replace sans requête DB."""
        if self._cached_cards:
            self._place_cards(col_max)

    def _on_assign(self, room):
        """Ouvre le dialogue de check-in pour sélectionner une réservation.
        La chambre cliquée est affectée directement (force_room_id)."""
        dlg = CheckinDialog(room, self.current_user, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        res_id = dlg.get_reservation_id()
        checkin_dt = dlg.get_checkin_datetime()
        uid = (self.current_user.get('id')
               if isinstance(self.current_user, dict) else None)
        ok, msg = ReservationService().checkin(
            res_id, checkin_date=checkin_dt, user_id=uid,
            force_room_id=room.id)  # affecter CETTE chambre précisément
        if ok:
            QMessageBox.information(self, "Check-in", msg)
            self.refresh()
        else:
            QMessageBox.warning(self, "Impossible", msg)

    def _on_move(self, room, reservation):
        """Ouvre le dialogue Moov Room pour déménager une réservation en cours."""
        if reservation is None:
            return
        cat_name = room.category.name if room.category else '-'
        dlg = MoveRoomDialog(
            reservation_id=reservation.id,
            current_room=room.number,
            category_id=room.hotel_category_id,
            category_name=cat_name,
            parent=self,
        )
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        new_room_id = dlg.get_new_room_id()
        if not new_room_id:
            return
        uid = (self.current_user.get('id')
               if isinstance(self.current_user, dict) else None)
        ok, msg = ReservationService().move_room(
            reservation.id, new_room_id, user_id=uid)
        if ok:
            QMessageBox.information(self, "Moov Room", msg)
            self.refresh()
        else:
            QMessageBox.warning(self, "Impossible", msg)
