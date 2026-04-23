"""
RoomView – onglet CRUD + gestion de statut des chambres.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QDialog, QFormLayout, QLineEdit,
    QComboBox, QDialogButtonBox, QMessageBox, QHeaderView,
    QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor

from ayanna_erp.modules.hotel.services.room_service import RoomService
from ayanna_erp.modules.hotel.utils.helpers import (
    room_status_label, ROOM_STATUS_COLORS
)

_svc = RoomService()

COLUMNS = ['ID', 'Numéro', 'Catégorie', 'Statut']
STATUSES = ['disponible', 'occupee', 'menage', 'maintenance']


class _RoomDialog(QDialog):
    def __init__(self, categories, number='', cat_id=None, status='disponible',
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chambre")
        self.setMinimumWidth(320)
        self.setModal(True)
        form = QFormLayout(self)
        form.setSpacing(10)

        self.number_edit = QLineEdit(number)
        form.addRow("Numéro * :", self.number_edit)

        self.cat_combo = QComboBox()
        for cat in categories:
            self.cat_combo.addItem(cat.name, cat.id)
            if cat.id == cat_id:
                self.cat_combo.setCurrentIndex(self.cat_combo.count() - 1)
        form.addRow("Catégorie * :", self.cat_combo)

        self.status_combo = QComboBox()
        for s in STATUSES:
            self.status_combo.addItem(room_status_label(s), s)
            if s == status:
                self.status_combo.setCurrentIndex(self.status_combo.count() - 1)
        form.addRow("Statut :", self.status_combo)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def _validate(self):
        if not self.number_edit.text().strip():
            QMessageBox.warning(self, "Numéro requis",
                                "Veuillez saisir le numéro de chambre.")
            return
        self.accept()

    def get_data(self):
        return (self.number_edit.text().strip(),
                self.cat_combo.currentData(),
                self.status_combo.currentData())


class RoomView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []
        self._categories = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        title = QLabel("Gestion des chambres")
        title.setStyleSheet("font-size:16px;font-weight:bold;color:#2C3E50;")
        root.addWidget(title)

        # Actions
        bar = QHBoxLayout()
        self.btn_add    = QPushButton("➕ Ajouter")
        self.btn_edit   = QPushButton("✏️ Modifier")
        self.btn_del    = QPushButton("🗑️ Supprimer")
        self.btn_status = QPushButton("🔄 Changer statut")
        for b in (self.btn_add, self.btn_edit, self.btn_del, self.btn_status):
            b.setFixedHeight(30)
            bar.addWidget(b)
        bar.addStretch()
        root.addLayout(bar)

        self.btn_add.clicked.connect(self._on_add)
        self.btn_edit.clicked.connect(self._on_edit)
        self.btn_del.clicked.connect(self._on_delete)
        self.btn_status.clicked.connect(self._on_status)

        # Tableau
        self.table = QTableWidget()
        self.table.setColumnCount(len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet(
            "QTableWidget{border:1px solid #ddd;}"
            "QHeaderView::section{background:#34495E;color:white;"
            "padding:6px;font-weight:bold;}")
        root.addWidget(self.table)

    def refresh(self):
        self._categories = _svc.get_all_categories()
        self._data = _svc.get_all_rooms()
        self.table.setRowCount(0)
        for room in self._data:
            r = self.table.rowCount()
            self.table.insertRow(r)
            cat_name = room.category.name if room.category else '-'
            vals = [room.id, room.number, cat_name,
                    room_status_label(room.status)]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, room.id)
                self.table.setItem(r, col, item)

            # Colorier la colonne statut
            color = ROOM_STATUS_COLORS.get(room.status, '#333')
            self.table.item(r, 3).setForeground(QBrush(QColor(color)))

    def _selected_room(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Sélection",
                                    "Veuillez sélectionner une chambre.")
            return None
        room_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        for room in self._data:
            if room.id == room_id:
                return room
        return None

    def _on_add(self):
        if not self._categories:
            QMessageBox.warning(self, "Pas de catégorie",
                                "Créez d'abord une catégorie de chambre.")
            return
        dlg = _RoomDialog(self._categories, parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        number, cat_id, _ = dlg.get_data()
        _svc.create_room(number, cat_id)
        self.refresh()

    def _on_edit(self):
        room = self._selected_room()
        if not room:
            return
        dlg = _RoomDialog(self._categories,
                          number=room.number,
                          cat_id=room.hotel_category_id,
                          status=room.status,
                          parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        number, cat_id, status = dlg.get_data()
        _svc.update_room(room.id, number, cat_id, status)
        self.refresh()

    def _on_delete(self):
        room = self._selected_room()
        if not room:
            return
        reply = QMessageBox.question(
            self, "Supprimer",
            f"Supprimer la chambre {room.number} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        _svc.delete_room(room.id)
        self.refresh()

    def _on_status(self):
        room = self._selected_room()
        if not room:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Statut – Chambre {room.number}")
        dlg.setMinimumWidth(260)
        form = QFormLayout(dlg)
        combo = QComboBox()
        for s in STATUSES:
            combo.addItem(room_status_label(s), s)
            if s == room.status:
                combo.setCurrentIndex(combo.count() - 1)
        form.addRow("Nouveau statut :", combo)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        form.addRow(btns)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            _svc.set_room_status(room.id, combo.currentData())
            self.refresh()
