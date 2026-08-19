import os
import platform
import subprocess
import tempfile
from datetime import datetime

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QDateEdit, QComboBox, QMessageBox, QDialog, QSpinBox, QFormLayout
)

from ayanna_erp.modules.restaurant.controllers.bon_commande_controller import BonCommandeController
from ayanna_erp.modules.restaurant.utils.bon_commande_printer import BonCommandePrinter
from ayanna_erp.utils.formatting import get_currency
from ayanna_erp.core.session_manager import SessionManager


class BonCommandeWidget(QWidget):
    def __init__(self, entreprise_id=1, current_user=None, parent=None):
        super().__init__(parent)
        self.entreprise_id = entreprise_id
        self.current_user = current_user
        self.controller = BonCommandeController(entreprise_id=entreprise_id)
        self.bon_commande_printer = BonCommandePrinter(enterprise_id=entreprise_id)
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

    def _get_current_user_context(self):
        user = SessionManager.get_current_user() or getattr(self, 'current_user', None)
        self.current_user = user
        if user is None:
            return {'id': None, 'role': '', 'name': ''}
        if isinstance(user, dict):
            return {
                'id': user.get('id'),
                'role': str(user.get('role') or '').strip().lower(),
                'name': str(user.get('name') or user.get('email') or '').strip(),
            }
        return {
            'id': getattr(user, 'id', None),
            'role': str(getattr(user, 'role', '') or '').strip().lower(),
            'name': str(getattr(user, 'name', None) or getattr(user, 'email', None) or '').strip(),
        }

    def _is_serveuse_view(self):
        return self._get_current_user_context().get('role') in {'serveuse', 'waitress'}

    def _filter_rows_for_current_user(self, rows):
        ctx = self._get_current_user_context()
        if not self._is_serveuse_view():
            return rows

        user_id = ctx.get('id')
        user_name = (ctx.get('name') or '').strip().lower()
        if user_id is not None:
            try:
                user_id = int(user_id)
            except (TypeError, ValueError):
                user_id = None

        if user_id is None and not user_name:
            return []

        filtered = []
        for rec in rows:
            try:
                serveuse_id = getattr(rec, 'serveuse_id', None)
                if serveuse_id is None:
                    serveuse_id = getattr(rec, 'serveuse', None)
                if serveuse_id is not None:
                    try:
                        serveuse_id_int = int(serveuse_id)
                    except (TypeError, ValueError):
                        serveuse_id_int = None
                else:
                    serveuse_id_int = None

                if user_id is not None and serveuse_id_int == user_id:
                    filtered.append(rec)
                    continue

                name = str(getattr(rec, 'serveuse_name', '') or '').strip().lower()
                if user_name and name and user_name == name:
                    filtered.append(rec)
            except Exception:
                pass
        return filtered

    def _format_display_amount(self, amount):
        """Format amounts with two decimals for the bon commande view."""
        try:
            value = float(amount)
        except (TypeError, ValueError):
            return str(amount)
        return f"{value:,.2f}".replace(",", " ").replace(".", ",")

    def _make_item(self, text, align=None):
        item = QTableWidgetItem(str(text))
        if align is not None:
            item.setTextAlignment(align)
        return item

    def load_data(self):
        try:
            current_user = SessionManager.get_current_user()
            if current_user is None:
                self.current_user = None
                self.table.setRowCount(0)
                self.totals_label.setText('')
                return
            self.current_user = current_user
            selected = self.day_edit.date().toPyDate()
            rows = self.controller.list_bons_for_date(
                target_date=selected,
                status_filter=self.status_filter.currentData(),
                panier_search=self.panier_search.text().strip() or None,
                serveuse_id=(self._get_current_user_context().get('id') if self._is_serveuse_view() else None),
            )
            rows = self._filter_rows_for_current_user(rows)
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
                self.table.setItem(row, 6, self._make_item(f"{self._format_display_amount(float(rec.montant_total or 0.0))} {get_currency(self.entreprise_id)}", Qt.AlignmentFlag.AlignRight))
                self.table.setItem(row, 7, self._make_item(str(rec.statut or '-'), Qt.AlignmentFlag.AlignCenter))
                self.table.setItem(row, 8, self._make_item(str(rec.products_text or '-')))

                action_container = QWidget()
                action_layout = QHBoxLayout(action_container)
                action_layout.setContentsMargins(0, 0, 0, 0)
                action_layout.setSpacing(4)

                reprint_btn = QPushButton('Réimpr. (copie)')
                reprint_btn.clicked.connect(lambda checked, bon=rec: self._on_reprint_bon(bon))
                action_layout.addWidget(reprint_btn)

                cancel_btn = QPushButton('Annuler')
                cancel_btn.setEnabled(str(rec.statut or '').lower() == 'valide')
                cancel_btn.clicked.connect(lambda checked, bon_id=rec.id: self._on_cancel_bon(bon_id))
                action_layout.addWidget(cancel_btn)

                self.table.setCellWidget(row, 9, action_container)

                total_amount += float(rec.montant_total or 0.0)

            self.info_label.setText(f'{len(rows)} bon(s) de commande trouvés')
            self.totals_label.setText(f'Total bons: {len(rows)} • Montant total: {self._format_display_amount(total_amount)} {get_currency(self.entreprise_id)}')
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f'Impossible de charger les bons de commande: {e}')

    def _on_reprint_bon(self, rec):
        try:
            if not getattr(rec, 'id', None):
                QMessageBox.information(self, 'Info', 'Aucun bon sélectionné')
                return

            ticket_data = {
                'numero_bon': getattr(rec, 'numero_bon', 'N/A'),
                'serveuse': getattr(rec, 'serveuse_name', ''),
                'table': str(getattr(rec, 'table_id', '') or '-'),
                'panier_id': getattr(rec, 'restau_panier_id', ''),
                'created_at': getattr(rec, 'created_at', None),
                'client_name': getattr(rec, 'client_name', ''),
                'items': getattr(rec, 'products', []) or [],
                'copy': True,
            }

            tmpf = None
            try:
                tmpf = tempfile.NamedTemporaryFile(prefix='bon_commande_copy_', suffix='.pdf', delete=False)
                tmpf.close()
                filename = self.bon_commande_printer.print_ticket(ticket_data, tmpf.name)

                if platform.system() == 'Windows':
                    os.startfile(filename)
                elif platform.system() == 'Darwin':
                    subprocess.run(['open', filename], check=True)
                else:
                    subprocess.run(['xdg-open', filename], check=True)

                QMessageBox.information(self, 'Réimpression', 'Copie du bon de commande générée')
            finally:
                if tmpf is not None:
                    try:
                        os.unlink(tmpf.name)
                    except Exception:
                        pass
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Impossible de réimprimer le bon: {e}")

    def _open_partial_cancel_dialog(self, bon_id):
        bon = self.controller.get_bon_by_id(bon_id)
        if bon is None:
            QMessageBox.warning(self, 'Bon introuvable', 'Le bon de commande demandé est introuvable.')
            return

        items = self.controller._safe_load_snapshot(getattr(bon, 'produits_json', None))
        if not items:
            success, msg = self.controller.cancel_bon(bon_id)
            if success:
                QMessageBox.information(self, 'Succès', 'Bon de commande annulé')
                self.load_data()
            else:
                QMessageBox.critical(self, 'Erreur', f'Impossible d\'annuler le bon: {msg}')
            return

        dialog = QDialog(self)
        dialog.setWindowTitle('Annulation partielle du bon')
        dialog.resize(700, 420)

        layout = QVBoxLayout(dialog)
        title = QLabel(f'Bon n° {bon.numero_bon} — choisissez les quantités à annuler')
        title.setWordWrap(True)
        title.setStyleSheet('font-weight: 600;')
        layout.addWidget(title)

        table = QTableWidget(len(items), 4)
        table.setHorizontalHeaderLabels(['Produit', 'Qté du bon', 'Annuler', 'Reste'])
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        spin_map = {}
        for row, item in enumerate(items):
            product_name = item.get('nom') or item.get('name') or f"Produit {item.get('produit_id') or item.get('product_id') or row}"
            qty = int(item.get('quantite', item.get('quantity', 0)) or 0)

            table.setItem(row, 0, QTableWidgetItem(str(product_name)))
            table.setItem(row, 1, QTableWidgetItem(str(qty)))

            spin = QSpinBox()
            spin.setRange(0, qty)
            spin.setValue(0)
            table.setCellWidget(row, 2, spin)
            spin_map[(item.get('produit_id') or item.get('product_id') or row)] = spin

            remain_label = QLabel(str(qty))
            table.setCellWidget(row, 3, remain_label)

            def _update_remaining(index_row, max_qty, label_widget, box):
                label_widget.setText(str(max_qty - box.value()))

            spin.valueChanged.connect(lambda _, row_idx=row, max_qty=qty, label=remain_label, box=spin: _update_remaining(row_idx, max_qty, label, box))

        layout.addWidget(table)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel_btn = QPushButton('Fermer')
        confirm_btn = QPushButton('Valider l\'annulation')
        confirm_btn.setDefault(True)
        cancel_btn.clicked.connect(dialog.reject)

        def _confirm_partial_cancel():
            cancelled_map = {}
            for item in items:
                pid = item.get('produit_id') or item.get('product_id')
                if pid is None:
                    continue
                qty_to_cancel = spin_map.get(pid)
                if qty_to_cancel is not None and qty_to_cancel.value() > 0:
                    cancelled_map[str(pid)] = qty_to_cancel.value()
            if not cancelled_map:
                QMessageBox.information(self, 'Aucune quantité', 'Aucune quantité n\'a été sélectionnée pour l\'annulation.')
                return

            ok, msg = self.controller.cancel_bon_partial(bon_id, cancelled_map)
            if ok:
                QMessageBox.information(self, 'Succès', 'Les quantités sélectionnées ont été annulées.')
                dialog.accept()
                self.load_data()
            else:
                QMessageBox.critical(self, 'Erreur', f'Impossible d\'annuler ces quantités: {msg}')

        confirm_btn.clicked.connect(_confirm_partial_cancel)
        buttons.addWidget(cancel_btn)
        buttons.addWidget(confirm_btn)
        layout.addLayout(buttons)

        dialog.exec()

    def _on_cancel_bon(self, bon_id):
        self._open_partial_cancel_dialog(bon_id)
