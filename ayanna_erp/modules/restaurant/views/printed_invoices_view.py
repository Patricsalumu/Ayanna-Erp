from datetime import datetime
import os
import subprocess
import tempfile

from PyQt6.QtCore import Qt, QDate, QSizeF, QMarginsF
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDateEdit,
    QComboBox,
    QMessageBox,
)
from PyQt6.QtGui import QTextDocument, QPdfWriter, QPageSize, QPageLayout

from ayanna_erp.modules.restaurant.controllers.printed_invoices_controller import PrintedInvoicesController
from ayanna_erp.utils.formatting import format_amount, get_currency


class PrintedInvoicesView(QWidget):
    """Vue de suivi des factures imprimees du module restaurant."""

    def __init__(self, entreprise_id=1, current_user=None, parent=None):
        super().__init__(parent)
        self.entreprise_id = entreprise_id
        self.current_user = current_user
        self.controller = PrintedInvoicesController(entreprise_id=entreprise_id)
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        main = QVBoxLayout(self)

        title = QLabel('Factures imprimees - Restaurant')
        title.setStyleSheet('font-size: 16px; font-weight: 700;')
        main.addWidget(title)

        filters = QHBoxLayout()

        self.day_edit = QDateEdit(QDate.currentDate())
        self.day_edit.setCalendarPopup(True)
        self.day_edit.dateChanged.connect(self.load_data)

        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText('Recherche produit...')
        self.product_search.textChanged.connect(self.load_data)

        self.panier_search = QLineEdit()
        self.panier_search.setPlaceholderText('Recherche panier (id)...')
        self.panier_search.textChanged.connect(self.load_data)

        self.status_filter = QComboBox()
        self.status_filter.addItem('Tous statuts', 'all')
        self.status_filter.addItem('En cours', 'en_cours')
        self.status_filter.addItem('Valide', 'valide')
        self.status_filter.addItem('Annule', 'annule')
        self.status_filter.currentIndexChanged.connect(self.load_data)

        self.amount_filter = QComboBox()
        self.amount_filter.addItem('Tous montants', 'all')
        self.amount_filter.addItem('Montant change', 'changed')
        self.amount_filter.addItem('Montant non change', 'unchanged')
        self.amount_filter.currentIndexChanged.connect(self.load_data)

        refresh_btn = QPushButton('Rafraichir')
        refresh_btn.clicked.connect(self.load_data)

        print_btn = QPushButton('🖨️ Imprimer rapport')
        print_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        print_btn.clicked.connect(self.print_report)

        filters.addWidget(QLabel('Jour:'))
        filters.addWidget(self.day_edit)
        filters.addWidget(QLabel('Produit:'))
        filters.addWidget(self.product_search)
        filters.addWidget(QLabel('Panier:'))
        filters.addWidget(self.panier_search)
        filters.addWidget(QLabel('Statut:'))
        filters.addWidget(self.status_filter)
        filters.addWidget(QLabel('Montant:'))
        filters.addWidget(self.amount_filter)
        filters.addWidget(refresh_btn)
        filters.addWidget(print_btn)

        main.addLayout(filters)

        self.info_label = QLabel('')
        self.info_label.setStyleSheet('color: #555;')
        main.addWidget(self.info_label)

        self.table = QTableWidget(0, 11)
        self.table.setHorizontalHeaderLabels([
            'Impression #',
            'Date impression',
            'Panier',
            'Statut panier',
            'Client',
            'Utilisateur',
            'Total imprime',
            'Total courant',
            'Montant change',
            'Nb lignes',
            'Produits (snapshot)',
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.Stretch)

        main.addWidget(self.table)

    def _make_item(self, text, align=None):
        item = QTableWidgetItem(text)
        if align is not None:
            item.setTextAlignment(align)
        return item

    def load_data(self):
        try:
            selected = self.day_edit.date().toPyDate()
            rows, err = self.controller.list_printed_invoices_for_date(
                target_date=selected,
                product_search=self.product_search.text().strip(),
                panier_search=self.panier_search.text().strip(),
                panier_status_filter=self.status_filter.currentData(),
                amount_change_filter=self.amount_filter.currentData(),
            )

            self.table.setRowCount(0)

            if err == 'TABLE_RESTAU_PRINTED_INVOICES_MISSING':
                self.info_label.setText(
                    'La table restau_printed_invoices n\'existe pas encore dans la base. '
                    'La vue est prete, en attente de migration physique.'
                )
                return

            self.info_label.setText(f'{len(rows)} facture(s) imprimee(s)')
            currency = get_currency(self.entreprise_id)

            for r in rows:
                row = self.table.rowCount()
                self.table.insertRow(row)

                printed_at = ''
                if isinstance(r.printed_at, datetime):
                    printed_at = r.printed_at.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    printed_at = str(r.printed_at or '')

                total_printed = f"{format_amount(float(r.total_amount or 0.0))} {currency}"
                if r.current_total is None:
                    total_current = '-'
                else:
                    total_current = f"{format_amount(float(r.current_total or 0.0))} {currency}"

                exists_text = 'Oui' if r.panier_exists else 'Non'
                changed_text = 'Oui' if r.amount_changed else 'Non'
                status_text = str(r.current_status or '-')

                self.table.setItem(row, 0, self._make_item(str(r.id), Qt.AlignmentFlag.AlignCenter))
                self.table.setItem(row, 1, self._make_item(printed_at, Qt.AlignmentFlag.AlignCenter))
                self.table.setItem(row, 2, self._make_item(str(r.panier_id), Qt.AlignmentFlag.AlignCenter))
                self.table.setItem(row, 3, self._make_item(status_text, Qt.AlignmentFlag.AlignCenter))
                
                # Client et Utilisateur
                customer_display = str(
                    getattr(r, 'customer_name', None)
                    or getattr(r, 'customer_id', '-')
                    or '-'
                )
                user_display = str(
                    getattr(r, 'printed_by_user_name', None)
                    or getattr(r, 'printed_by_user_id', '-')
                    or '-'
                )
                self.table.setItem(row, 4, self._make_item(customer_display, Qt.AlignmentFlag.AlignCenter))
                self.table.setItem(row, 5, self._make_item(user_display, Qt.AlignmentFlag.AlignCenter))
                
                # Totaux et détails
                self.table.setItem(row, 6, self._make_item(total_printed, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter))
                self.table.setItem(row, 7, self._make_item(total_current, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter))
                self.table.setItem(row, 8, self._make_item(changed_text, Qt.AlignmentFlag.AlignCenter))
                self.table.setItem(row, 9, self._make_item(str(r.product_lines_count), Qt.AlignmentFlag.AlignCenter))
                self.table.setItem(row, 10, self._make_item(r.products_text or '-'))

                if not r.panier_exists:
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        if item is not None:
                            item.setBackground(Qt.GlobalColor.lightGray)
                elif r.amount_changed:
                    self.table.item(row, 8).setBackground(Qt.GlobalColor.yellow)

        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f'Impossible de charger les factures imprimees: {e}')

    def print_report(self):
        """Générer et ouvrir le rapport des factures imprimees en PDF format paysage A4"""
        try:
            # Générer le contenu HTML du rapport
            html_content = self._generate_html_report()
            
            # Créer un fichier PDF temporaire
            temp_dir = tempfile.gettempdir()
            selected_date = self.day_edit.date().toPyDate()
            filename = f"rapport_factures_imprimees_{selected_date.strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = os.path.join(temp_dir, filename)
            
            # Créer un document et le convertir en PDF
            doc = QTextDocument()
            doc.setHtml(html_content)
            
            # Créer un writer PDF avec configuration paysage A4
            pdf_writer = QPdfWriter(pdf_path)
            
            # Configurer la page en A4 paysage
            # A4 en portrait = 210mm x 297mm
            # A4 en paysage = 297mm x 210mm (dimensions inversées)
            page_size = QSizeF(297, 210)  # Largeur x Hauteur en mm pour A4 paysage
            pdf_writer.setPageSize(QPageSize(page_size, QPageSize.Unit.Millimeter))
            pdf_writer.setPageMargins(QMarginsF(10, 10, 10, 10), QPageLayout.Unit.Millimeter)  # Marges: 10mm partout
            pdf_writer.setResolution(300)  # Haute résolution
            
            # Imprimer le document dans le PDF
            doc.print(pdf_writer)
            
            # Ouvrir le PDF avec l'application par défaut
            self._open_pdf(pdf_path)
            
            QMessageBox.information(self, 'Succès', f'Rapport généré: {filename}')

        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de la génération du PDF: {e}')

    def _open_pdf(self, pdf_path):
        """Ouvrir le fichier PDF avec l'application par défaut du système"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(pdf_path)
            elif os.name == 'posix':  # macOS ou Linux
                # macOS
                if os.sys.platform == 'darwin':
                    subprocess.run(['open', pdf_path])
                # Linux
                else:
                    subprocess.run(['xdg-open', pdf_path])
        except Exception as e:
            print(f"Impossible d'ouvrir le PDF: {e}")
            # Au minimum, on a créé le file
            QMessageBox.information(self, 'Fichier créé', f'Fichier PDF créé à: {pdf_path}')

    def _generate_html_report(self):
        """Générer le contenu HTML du rapport des factures imprimees"""
        selected_date = self.day_edit.date().toPyDate()
        product_search = self.product_search.text().strip()
        panier_search = self.panier_search.text().strip()
        
        rows, err = self.controller.list_printed_invoices_for_date(
            target_date=selected_date,
            product_search=product_search,
            panier_search=panier_search,
            panier_status_filter=self.status_filter.currentData(),
            amount_change_filter=self.amount_filter.currentData(),
        )

        if err == 'TABLE_RESTAU_PRINTED_INVOICES_MISSING':
            return "<p>La table restau_printed_invoices n'existe pas encore dans la base.</p>"

        currency = get_currency(self.entreprise_id)
        
        # En-tête du rapport
        html = """
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    font-size: 10pt;
                    margin: 5mm;
                }
                h1 {
                    text-align: center;
                    font-size: 14pt;
                    margin-bottom: 10px;
                    color: #2C3E50;
                }
                .info-line {
                    margin-bottom: 5px;
                    font-size: 9pt;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 10px;
                }
                th {
                    background-color: #34495E;
                    color: white;
                    padding: 6px;
                    text-align: left;
                    font-size: 9pt;
                    font-weight: bold;
                    border: 1px solid #2C3E50;
                }
                td {
                    padding: 4px 6px;
                    border: 1px solid #BDC3C7;
                    font-size: 9pt;
                }
                tr:nth-child(even) {
                    background-color: #F8F9FA;
                }
                .text-center {
                    text-align: center;
                }
                .text-right {
                    text-align: right;
                }
                .total-row {
                    background-color: #ECF0F1;
                    font-weight: bold;
                }
                .missing-panier {
                    background-color: #D5DBDB;
                }
                .amount-changed {
                    background-color: #FFFACD;
                }
            </style>
        </head>
        <body>
        """
        
        # Titre et informations du rapport
        html += f"<h1>RAPPORT DES FACTURES IMPRIMEES - RESTAURANT</h1>"
        html += f'<div class="info-line"><strong>Date:</strong> {selected_date.strftime("%Y-%m-%d")}</div>'
        if product_search:
            html += f'<div class="info-line"><strong>Filtre produit:</strong> {product_search}</div>'
        if panier_search:
            html += f'<div class="info-line"><strong>Filtre panier:</strong> {panier_search}</div>'
        html += f'<div class="info-line"><strong>Total factures:</strong> {len(rows)}</div>'
        
        # Tableau des données
        html += """
        <table>
            <thead>
                <tr>
                    <th class="text-center">Impression #</th>
                    <th class="text-center">Date impression</th>
                    <th class="text-center">Panier</th>
                    <th class="text-center">Statut</th>
                    <th class="text-center">Client</th>
                    <th class="text-center">Utilisateur</th>
                    <th class="text-right">Total imprimé</th>
                    <th class="text-right">Total courant</th>
                    <th class="text-center">Changé</th>
                    <th class="text-center">Lignes</th>
                    <th>Produits</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for r in rows:
            printed_at = ''
            if isinstance(r.printed_at, datetime):
                printed_at = r.printed_at.strftime('%Y-%m-%d %H:%M:%S')
            else:
                printed_at = str(r.printed_at or '')

            total_printed = f"{format_amount(float(r.total_amount or 0.0))} {currency}"
            if r.current_total is None:
                total_current = '-'
            else:
                total_current = f"{format_amount(float(r.current_total or 0.0))} {currency}"

            exists_text = 'Oui' if r.panier_exists else 'Non'
            exists_text = 'Oui' if r.panier_exists else 'Non'
            changed_text = 'Oui' if r.amount_changed else 'Non'
            status_text = str(r.current_status or '-')
            
            # Client et Utilisateur
            customer_display = (
                getattr(r, 'customer_name', None)
                or getattr(r, 'customer_id', None)
                or '-'
            )
            user_display = (
                getattr(r, 'printed_by_user_name', None)
                or getattr(r, 'printed_by_user_id', None)
                or '-'
            )

            # Déterminer la classe CSS pour la ligne
            row_class = ''
            if not r.panier_exists:
                row_class = 'missing-panier'
            elif r.amount_changed:
                row_class = 'amount-changed'

            html += f'<tr class="{row_class}">'
            html += f'<td class="text-center">{r.id}</td>'
            html += f'<td class="text-center">{printed_at}</td>'
            html += f'<td class="text-center">{r.panier_id}</td>'
            html += f'<td class="text-center">{status_text}</td>'
            html += f'<td class="text-center">{customer_display}</td>'
            html += f'<td class="text-center">{user_display}</td>'
            html += f'<td class="text-right">{total_printed}</td>'
            html += f'<td class="text-right">{total_current}</td>'
            html += f'<td class="text-center">{changed_text}</td>'
            html += f'<td class="text-center">{r.product_lines_count}</td>'
            html += f'<td>{r.products_text or "-"}</td>'
            html += '</tr>'

        html += """
            </tbody>
        </table>
        </body>
        </html>
        """
        
        return html
