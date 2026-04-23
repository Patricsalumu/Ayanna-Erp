"""
HotelDashboard – onglet 1 : vue d'ensemble des chambres par catégorie.
"""
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QPushButton, QLabel, QFrame, QGridLayout, QButtonGroup,
    QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

from ayanna_erp.modules.hotel.services.room_service import RoomService
from ayanna_erp.modules.hotel.services.reservation_service import ReservationService
from ayanna_erp.modules.hotel.utils.helpers import (
    room_status_label, ROOM_STATUS_COLORS, fmt_date
)

_room_svc = RoomService()
_res_svc  = ReservationService()


class RoomCard(QFrame):
    """Carte visuelle pour une chambre."""

    def __init__(self, room, reservation, assign_cb, parent=None):
        super().__init__(parent)
        self.room = room
        self.reservation = reservation
        self.assign_cb = assign_cb
        self._build()

    def _build(self):
        color = ROOM_STATUS_COLORS.get(self.room.status, '#333')
        self.setFixedSize(175, 170)
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

        # Catégorie
        cat_name = self.room.category.name if self.room.category else '-'
        layout.addWidget(QLabel(f"<span style='color:#888;font-size:11px;'>{cat_name}</span>"))

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
        else:
            layout.addWidget(QLabel("<span style='color:#27AE60;'>Libre</span>"))
            layout.addStretch()
            btn = QPushButton("Affecter réservation")
            btn.setStyleSheet(
                "QPushButton{background:#1976D2;color:white;border-radius:4px;"
                "padding:4px;font-size:10px;}QPushButton:hover{background:#1565C0;}")
            btn.clicked.connect(lambda: self.assign_cb(self.room))
            layout.addWidget(btn)


class HotelDashboard(QWidget):

    def __init__(self, current_user=None, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self._selected_cat_id = None
        self._categories = []
        self._rooms = []
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
        self.cards_container = QWidget()
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setSpacing(12)
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
        # Nettoyer
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        rooms = self._rooms
        if self._selected_cat_id is not None:
            rooms = [r for r in rooms
                     if r.hotel_category_id == self._selected_cat_id]

        total = len(rooms)
        dispo = sum(1 for r in rooms if r.status == 'disponible')
        occupee = sum(1 for r in rooms if r.status == 'occupee')

        col_max = 5
        for idx, room in enumerate(rooms):
            # Chercher réservation active
            res = _room_svc.get_room_with_active_reservation(room.id)
            card = RoomCard(room, res, self._on_assign, self)
            self.cards_layout.addWidget(card, idx // col_max, idx % col_max)

        self.stat_bar.setText(
            f"Total : {total}  |  Disponibles : {dispo}  |  "
            f"Occupées : {occupee}  |  Autres : {total - dispo - occupee}")

    def _on_assign(self, room):
        """Affecte la première réservation en attente de cette catégorie à la chambre."""
        from ayanna_erp.modules.hotel.services.reservation_service import ReservationService
        reservations = ReservationService().get_all_reservations(status='en_attente')
        cat_reservations = [
            r for r in reservations
            if r['category'] == (room.category.name if room.category else '')]
        if not cat_reservations:
            QMessageBox.information(
                self, "Aucune réservation",
                "Aucune réservation en attente pour cette catégorie.")
            return
        # Prendre la plus ancienne
        target = cat_reservations[0]
        ok, msg = ReservationService().checkin(target['id'])
        if ok:
            QMessageBox.information(self, "Check-in", msg)
            self.refresh()
        else:
            QMessageBox.warning(self, "Impossible", msg)
