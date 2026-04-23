"""
CategoryView – onglet CRUD des catégories de chambres.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QDialog, QFormLayout, QLineEdit,
    QDoubleSpinBox, QDialogButtonBox, QMessageBox, QHeaderView,
    QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ayanna_erp.modules.hotel.services.room_service import RoomService

_svc = RoomService()

COLUMNS = ['ID', 'Nom', 'Prix / nuit']


class _CatDialog(QDialog):
    def __init__(self, name='', price=0.0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Catégorie")
        self.setMinimumWidth(320)
        self.setModal(True)
        form = QFormLayout(self)
        self.name_edit = QLineEdit(name)
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 9_999_999)
        self.price_spin.setDecimals(0)
        self.price_spin.setSingleStep(1000)
        self.price_spin.setValue(float(price))
        form.addRow("Nom * :", self.name_edit)
        form.addRow("Prix par nuit * :", self.price_spin)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def _validate(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Nom requis", "Veuillez saisir un nom.")
            return
        if self.price_spin.value() <= 0:
            QMessageBox.warning(self, "Prix requis",
                                "Le prix par nuit doit être supérieur à 0.")
            return
        self.accept()

    def get_data(self):
        return self.name_edit.text().strip(), self.price_spin.value()


class CategoryView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        title = QLabel("Catégories de chambres")
        title.setStyleSheet("font-size:16px;font-weight:bold;color:#2C3E50;")
        root.addWidget(title)

        # Actions
        bar = QHBoxLayout()
        self.btn_add  = QPushButton("➕ Ajouter")
        self.btn_edit = QPushButton("✏️ Modifier")
        self.btn_del  = QPushButton("🗑️ Supprimer")
        for b in (self.btn_add, self.btn_edit, self.btn_del):
            b.setFixedHeight(30)
            bar.addWidget(b)
        bar.addStretch()
        root.addLayout(bar)

        self.btn_add.clicked.connect(self._on_add)
        self.btn_edit.clicked.connect(self._on_edit)
        self.btn_del.clicked.connect(self._on_delete)

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
        self._data = _svc.get_all_categories()
        self.table.setRowCount(0)
        for cat in self._data:
            r = self.table.rowCount()
            self.table.insertRow(r)
            for col, val in enumerate([cat.id, cat.name,
                                        f"{cat.price_per_night:,.0f}"]):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, cat.id)
                self.table.setItem(r, col, item)

    def _selected_cat(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Sélection",
                                    "Veuillez sélectionner une catégorie.")
            return None
        cat_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        for c in self._data:
            if c.id == cat_id:
                return c
        return None

    def _on_add(self):
        dlg = _CatDialog(parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        name, price = dlg.get_data()
        _svc.create_category(name, price)
        self.refresh()

    def _on_edit(self):
        cat = self._selected_cat()
        if not cat:
            return
        dlg = _CatDialog(cat.name, cat.price_per_night, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        name, price = dlg.get_data()
        _svc.update_category(cat.id, name, price)
        self.refresh()

    def _on_delete(self):
        cat = self._selected_cat()
        if not cat:
            return
        reply = QMessageBox.question(
            self, "Supprimer",
            f"Supprimer la catégorie « {cat.name} » ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        _svc.delete_category(cat.id)
        self.refresh()
