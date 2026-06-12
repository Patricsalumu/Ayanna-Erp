from datetime import datetime

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QDateEdit, QComboBox, QMessageBox
)

from ayanna_erp.modules.restaurant.controllers.bon_commande_controller import BonCommandeController
from ayanna_erp.utils.formatting import format_amount, get_currency


class BonCommandeWidget(QWidget):
    def __init__(self, entreprise_id=1, current_user=None, parent=None):
        super().__init__(parent)
        self.entreprise_id = entreprise_id
        self.current_user = current_user
        self.controller = BonCommandeController(entreprise_id=entreprise_id)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        main = QVBoxLayout(self)

        title = QLabel('Bons de commande')
        title.setStyleSheet('font-size: 16px; font-weight: 700;')
        main.addWidget(title)

        filters = QHBoxLayout()
        self.day_edit = QDateEdit(QDate.currentDate())
        self.day_edit.setCalendarPopup(True)
        self.day_edit.dateChanged.connect(self.load_data)

        self.status_filter = QComboBox()
        self.status_filter.addItem('Tous statuts', 'all')
        self.status_filter.addItem('Valide', 'valide')
        self.status_filter.addItem('Annulé', 'annule')
        self.status_filter.currentIndexChanged.connect(self.load_data)

        self.panier_search = QLineEdit()
        self.panier_search.setPlaceholderText('Rechercher (Bon #, Panier, Client, Serveuse, Produit, Montant)...')
        self.panier_search.textChanged.connect(self.load_data)

        refresh_btn = QPushButton('Rafraîchir')
        refresh_btn.clicked.connect(self.load_data)

        filters.addWidget(QLabel('Jour:'))
        filters.addWidget(self.day_edit)
        filters.addWidget(QLabel('Statut:'))
        filters.addWidget(self.status_filter)
        filters.addWidget(QLabel('Rechercher:'))
        filters.addWidget(self.panier_search)
        filters.addWidget(refresh_btn)
        main.addLayout(filters)

        self.info_label = QLabel('')
        self.info_label.setStyleSheet('color: #555;')
        main.addWidget(self.info_label)

        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels([
            'Bon #', 'Date', 'Panier', 'Table', 'Client', 'Serveuse', 'Montant', 'Statut', 'Produits', 'Action'
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)
        main.addWidget(self.table)

        self.totals_label = QLabel('')
        self.totals_label.setStyleSheet('font-weight: 600;')
        main.addWidget(self.totals_label)

    def _make_item(self, text, align=None):
        item = QTableWidgetItem(str(text))
        if align is not None:
            item.setTextAlignment(align)
        return item

    def load_data(self):
        try:
            selected = self.day_edit.date().toPyDate()
            rows = self.controller.list_bons_for_date(
                target_date=selected,
                status_filter=self.status_filter.currentData(),
                panier_search=self.panier_search.text().strip() or None,
            )
            self.table.setRowCount(0)
            total_amount = 0.0
            for rec in rows:
                row = self.table.rowCount()
                self.table.insertRow(row)

                printed_at = ''
                if isinstance(rec.created_at, datetime):
                    printed_at = rec.created_at.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    printed_at = str(rec.created_at or '')

                self.table.setItem(row, 0, self._make_item(str(rec.numero_bon), Qt.AlignmentFlag.AlignCenter))
                self.table.setItem(row, 1, self._make_item(printed_at, Qt.AlignmentFlag.AlignCenter))
                self.table.setItem(row, 2, self._make_item(str(rec.restau_panier_id), Qt.AlignmentFlag.AlignCenter))
                self.table.setItem(row, 3, self._make_item(str(rec.table_id or '-'), Qt.AlignmentFlag.AlignCenter))
                self.table.setItem(row, 4, self._make_item(str(rec.client_name or '-'), Qt.AlignmentFlag.AlignCenter))
                self.table.setItem(row, 5, self._make_item(str(rec.serveuse_name or '-'), Qt.AlignmentFlag.AlignCenter))
                self.table.setItem(row, 6, self._make_item(f"{format_amount(float(rec.montant_total or 0.0))} {get_currency(self.entreprise_id)}", Qt.AlignmentFlag.AlignRight))
                self.table.setItem(row, 7, self._make_item(str(rec.statut or '-'), Qt.AlignmentFlag.AlignCenter))
                self.table.setItem(row, 8, self._make_item(str(rec.products_text or '-')))

                action_btn = QPushButton('Annuler')
                action_btn.setEnabled(str(rec.statut or '').lower() == 'valide')
                action_btn.clicked.connect(lambda checked, bon_id=rec.id: self._on_cancel_bon(bon_id))
                self.table.setCellWidget(row, 9, action_btn)

                total_amount += float(rec.montant_total or 0.0)

            self.info_label.setText(f'{len(rows)} bon(s) de commande trouvés')
            self.totals_label.setText(f'Total bons: {len(rows)} • Montant total: {format_amount(total_amount)} {get_currency(self.entreprise_id)}')
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f'Impossible de charger les bons de commande: {e}')

    def _on_cancel_bon(self, bon_id):
        ok = QMessageBox.question(
            self,
            'Annuler le bon',
            'Confirmez-vous l\'annulation de ce bon de commande ?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ok != QMessageBox.StandardButton.Yes:
            return

        success, msg = self.controller.cancel_bon(bon_id)
        if success:
            QMessageBox.information(self, 'Succès', 'Bon de commande annulé')
            self.load_data()
        else:
            QMessageBox.critical(self, 'Erreur', f'Impossible d\'annuler le bon: {msg}')
