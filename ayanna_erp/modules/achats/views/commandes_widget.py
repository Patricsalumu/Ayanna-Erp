"""
Widget pour la gestion des commandes d'achat
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QComboBox, QHeaderView, QMessageBox,
    QTabWidget, QGroupBox, QFormLayout, QTextEdit, QDialog,
    QDialogButtonBox, QDoubleSpinBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from decimal import Decimal
from datetime import datetime

from ayanna_erp.modules.achats.controllers import AchatController
from ayanna_erp.modules.achats.models.achats_models import AchatCommande, EtatCommande
from ayanna_erp.core.config import Config
from ayanna_erp.core.entreprise_controller import EntrepriseController


class PaiementDialog(QDialog):
    """Dialog pour saisir un paiement"""

    def __init__(self, parent=None, commande=None, montant_restant=0):
        super().__init__(parent)
        self.commande = commande
        self.montant_restant = montant_restant
        # Récupérer le symbole de la devise dynamique
        try:
            self.entreprise_ctrl = EntrepriseController()
            self.currency = self.entreprise_ctrl.get_currency_symbol()
        except Exception:
            self.currency = "FC"
        self.setWindowTitle(f"Paiement - Commande {commande.numero}")
        self.setFixedSize(420, 320)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        info = QGroupBox("Informations")
        form = QFormLayout(info)
        form.addRow("N°:", QLabel(self.commande.numero))
        form.addRow("Fournisseur:", QLabel(self.commande.fournisseur.nom if self.commande.fournisseur else "N/A"))
        form.addRow("Montant total:", QLabel(self.entreprise_ctrl.format_amount(self.commande.montant_total)))
        form.addRow("Montant restant:", QLabel(self.entreprise_ctrl.format_amount(self.montant_restant)))
        layout.addWidget(info)

        pay_group = QGroupBox("Nouveau paiement")
        pay_form = QFormLayout(pay_group)
        self.montant_spinbox = QDoubleSpinBox()
        self.montant_spinbox.setRange(0.01, float(self.montant_restant))
        self.montant_spinbox.setDecimals(2)
        self.montant_spinbox.setValue(float(self.montant_restant))
        # Spinbox suffix: afficher le symbole (sans le montant formaté)
        self.montant_spinbox.setSuffix(f" {self.entreprise_ctrl.get_currency_symbol()}")
        pay_form.addRow("Montant*:", self.montant_spinbox)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Espèces", "Chèque", "Virement", "Carte bancaire", "Mobile Money", "Autre"])
        pay_form.addRow("Mode*:", self.mode_combo)

        self.reference_edit = QLineEdit()
        self.reference_edit.setPlaceholderText("Référence (chèque, virement...)")
        pay_form.addRow("Référence:", self.reference_edit)

        self.commentaire = QTextEdit()
        self.commentaire.setMaximumHeight(60)
        pay_form.addRow("Commentaire:", self.commentaire)

        layout.addWidget(pay_group)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_montant(self):
        return Decimal(str(self.montant_spinbox.value()))

    def get_mode_paiement(self):
        return self.mode_combo.currentText()

    def get_reference(self):
        return self.reference_edit.text().strip()


class EditCommandeDialog(QDialog):
    """Dialog pour modifier une commande d'achat"""

    def __init__(self, parent=None, achat_controller=None, commande=None):
        super().__init__(parent)
        self.achat_controller = achat_controller
        self.commande = commande
        self.produits = []
        try:
            self.entreprise_ctrl = EntrepriseController()
            self.currency = self.entreprise_ctrl.get_currency_symbol()
        except Exception:
            self.currency = "FC"
        self.setWindowTitle(f"Modifier Commande {commande.numero}")
        self.setFixedSize(800, 600)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Infos commande
        info_group = QGroupBox("Informations commande")
        info_layout = QFormLayout(info_group)
        info_layout.addRow("Numéro:", QLabel(self.commande.numero))
        info_layout.addRow("Fournisseur:", QLabel(self.commande.fournisseur.nom if self.commande.fournisseur else "Aucun"))
        info_layout.addRow("Entrepôt:", QLabel(str(self.commande.entrepot_id)))
        layout.addWidget(info_group)

        # Lignes de commande
        lines_group = QGroupBox("Lignes de commande")
        lines_layout = QVBoxLayout(lines_group)

        # Boutons pour gérer les lignes
        lines_buttons_layout = QHBoxLayout()

        self.add_product_btn = QPushButton("➕ Ajouter des produits")
        self.add_product_btn.clicked.connect(self.add_products)
        self.add_product_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #219A52;
            }
        """)

        self.remove_line_btn = QPushButton("🗑️ Supprimer ligne")
        self.remove_line_btn.clicked.connect(self.remove_selected_line)
        self.remove_line_btn.setEnabled(False)

        lines_buttons_layout.addWidget(self.add_product_btn)
        lines_buttons_layout.addWidget(self.remove_line_btn)
        lines_buttons_layout.addStretch()

        lines_layout.addLayout(lines_buttons_layout)

        # Table des lignes
        self.lines_table = QTableWidget()
        self.lines_table.setColumnCount(6)
        self.lines_table.setHorizontalHeaderLabels([
            "Produit", "Quantité", "Prix unitaire", "Remise ligne", "Total ligne", "Actions"
        ])

        # Configuration de la table
        header = self.lines_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self.lines_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.lines_table.selectionModel().selectionChanged.connect(self.on_line_selection_changed)

        lines_layout.addWidget(self.lines_table)
        layout.addWidget(lines_group)

        # Boutons OK/Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_data(self):
        # Charger produits
        session = self.achat_controller.db_manager.get_session()
        try:
            self.produits = self.achat_controller.get_produits_disponibles(session)
            # Charger lignes existantes
            self.lignes_table.setRowCount(len(self.commande.lignes))
            for row, ligne in enumerate(self.commande.lignes):
                self.populate_ligne_row(row, ligne)
        finally:
            session.close()

    def populate_ligne_row(self, row, ligne=None):
        # Produit combo
        produit_combo = QComboBox()
        for prod in self.produits:
            produit_combo.addItem(f"{prod.name} ({prod.code})", prod.id)
        if ligne:
            index = produit_combo.findData(ligne.produit_id)
            if index >= 0:
                produit_combo.setCurrentIndex(index)
        self.lignes_table.setCellWidget(row, 0, produit_combo)

        # Quantité
        quantite_spin = QDoubleSpinBox()
        quantite_spin.setRange(0.01, 999999)
        quantite_spin.setDecimals(2)
        quantite_spin.setValue(float(ligne.quantite) if ligne else 1.0)
        self.lignes_table.setCellWidget(row, 1, quantite_spin)

        # Prix unitaire
        prix_spin = QDoubleSpinBox()
        prix_spin.setRange(0, 999999999)
        prix_spin.setDecimals(2)
        prix_spin.setSuffix(f" {self.currency}")
        prix_spin.setValue(float(ligne.prix_unitaire) if ligne else 0.0)
        self.lignes_table.setCellWidget(row, 2, prix_spin)

        # Remise
        remise_spin = QDoubleSpinBox()
        remise_spin.setRange(0, 999999999)
        remise_spin.setDecimals(2)
        remise_spin.setSuffix(f" {self.currency}")
        remise_spin.setValue(float(ligne.remise_ligne) if ligne else 0.0)
        self.lignes_table.setCellWidget(row, 3, remise_spin)

        # Total (calculé)
        total_label = QLabel()
        self.update_total_label(row, quantite_spin, prix_spin, remise_spin, total_label)
        quantite_spin.valueChanged.connect(lambda: self.update_total_label(row, quantite_spin, prix_spin, remise_spin, total_label))
        prix_spin.valueChanged.connect(lambda: self.update_total_label(row, quantite_spin, prix_spin, remise_spin, total_label))
        remise_spin.valueChanged.connect(lambda: self.update_total_label(row, quantite_spin, prix_spin, remise_spin, total_label))
        self.lignes_table.setCellWidget(row, 4, total_label)

        # Actions
        delete_btn = QPushButton("🗑️")
        delete_btn.clicked.connect(lambda: self.delete_ligne(row))
        self.lignes_table.setCellWidget(row, 5, delete_btn)

    def update_total_label(self, row, quantite_spin, prix_spin, remise_spin, total_label):
        quantite = Decimal(str(quantite_spin.value()))
        prix = Decimal(str(prix_spin.value()))
        remise = Decimal(str(remise_spin.value()))
        total = (quantite * prix) - remise
        total_label.setText(self.entreprise_ctrl.format_amount(total))

    def add_ligne(self):
        row = self.lignes_table.rowCount()
        self.lignes_table.insertRow(row)
        self.populate_ligne_row(row)

    def delete_ligne(self, row):
        self.lignes_table.removeRow(row)

    def get_lignes_data(self):
        lignes = []
        for row in range(self.lignes_table.rowCount()):
            produit_combo = self.lignes_table.cellWidget(row, 0)
            quantite_spin = self.lignes_table.cellWidget(row, 1)
            prix_spin = self.lignes_table.cellWidget(row, 2)
            remise_spin = self.lignes_table.cellWidget(row, 3)

            if produit_combo and quantite_spin and prix_spin and remise_spin:
                lignes.append({
                    'produit_id': produit_combo.currentData(),
                    'quantite': Decimal(str(quantite_spin.value())),
                    'prix_unitaire': Decimal(str(prix_spin.value())),
                    'remise_ligne': Decimal(str(remise_spin.value()))
                })
        return lignes

    def add_products(self):
        # Pour simplifier, on ajoute juste une ligne vide
        self.add_ligne()

    def remove_selected_line(self):
        selected_rows = self.lines_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            self.delete_ligne(row)

    def on_line_selection_changed(self):
        has_selection = len(self.lines_table.selectionModel().selectedRows()) > 0
        self.remove_line_btn.setEnabled(has_selection)


class CommandesWidget(QWidget):
    """Widget principal pour la gestion des commandes d'achat"""

    commande_updated = pyqtSignal(int)
    commande_selected = pyqtSignal(int)

    def __init__(self, achat_controller: AchatController):
        super().__init__()
        self.achat_controller = achat_controller
        # Récupérer le symbole de la devise dynamique pour affichage
        try:
            self.entreprise_ctrl = EntrepriseController()
            self.currency = self.entreprise_ctrl.get_currency_symbol()
        except Exception:
            self.currency = "FC"
        self.current_commandes = []
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Left: header + table
        left_v = QVBoxLayout()
        header_h = QHBoxLayout()
        title = QLabel("📋 Gestion des Commandes")
        title.setStyleSheet("font-weight:600; font-size:15px;")

        filters = QGroupBox("Filtres")
        f_layout = QHBoxLayout(filters)
        f_layout.addWidget(QLabel("État:"))
        self.etat_combo = QComboBox()
        self.etat_combo.addItem("Tous", None)
        self.etat_combo.addItem("En cours", EtatCommande.ENCOURS)
        self.etat_combo.addItem("Réceptionné", EtatCommande.RECEPTIONNE)
        self.etat_combo.addItem("Validé", EtatCommande.VALIDE)
        self.etat_combo.addItem("Annulé", EtatCommande.ANNULE)
        self.etat_combo.currentIndexChanged.connect(self.refresh_data)
        f_layout.addWidget(self.etat_combo)

        f_layout.addWidget(QLabel("Recherche:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Numéro, fournisseur...")
        self.search_edit.textChanged.connect(self.refresh_data)
        f_layout.addWidget(self.search_edit)

        refresh_btn = QPushButton("🔄")
        refresh_btn.clicked.connect(self.refresh_data)
        f_layout.addWidget(refresh_btn)

        header_h.addWidget(title)
        header_h.addStretch()
        header_h.addWidget(filters)

        left_v.addLayout(header_h)

        self.table = QTableWidget()
        # Colonnes: ID, Numéro, Fournisseur, Date, Montant, Payé, Statut Paiement, État, Entrepôt, Actions
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(["ID", "Numéro", "Fournisseur", "Date", "Montant", "Payé", "Statut paiement", "État", "Entrepôt", "Actions"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        left_v.addWidget(self.table)

        left_widget = QWidget()
        left_widget.setLayout(left_v)

        # Right: details
        right_widget = self.create_details_widget()

        main_layout.addWidget(left_widget, 2)
        main_layout.addWidget(right_widget, 1)

    def create_details_widget(self):
        details = QGroupBox("Détails de la commande")
        v = QVBoxLayout(details)

        tabs = QTabWidget()
        info_w = QWidget()
        info_form = QFormLayout(info_w)
        self.detail_numero = QLabel("-")
        self.detail_fournisseur = QLabel("-")
        self.detail_entrepot = QLabel("-")
        self.detail_date = QLabel("-")
        self.detail_montant = QLabel("-")
        self.detail_statut_paiement = QLabel("-")
        self.detail_total_paye = QLabel("-")
        self.detail_etat = QLabel("-")
        info_form.addRow("Numéro:", self.detail_numero)
        info_form.addRow("Fournisseur:", self.detail_fournisseur)
        info_form.addRow("Entrepôt:", self.detail_entrepot)
        info_form.addRow("Date:", self.detail_date)
        info_form.addRow("Montant:", self.detail_montant)
        info_form.addRow("Montant payé:", self.detail_total_paye)
        info_form.addRow("Statut paiement:", self.detail_statut_paiement)
        info_form.addRow("État:", self.detail_etat)
        tabs.addTab(info_w, "Infos")

        lignes_w = QWidget()
        lignes_v = QVBoxLayout(lignes_w)
        self.lignes_table = QTableWidget()
        self.lignes_table.setColumnCount(5)
        self.lignes_table.setHorizontalHeaderLabels(["Produit", "Quantité", "Prix", "Remise", "Total"])
        lignes_v.addWidget(self.lignes_table)
        tabs.addTab(lignes_w, "Lignes")

        paiements_w = QWidget()
        paiements_v = QVBoxLayout(paiements_w)
        self.paiements_table = QTableWidget()
        self.paiements_table.setColumnCount(4)
        self.paiements_table.setHorizontalHeaderLabels(["Date", "Montant", "Mode", "Réf."])
        paiements_v.addWidget(self.paiements_table)
        tabs.addTab(paiements_w, "Paiements")

        v.addWidget(tabs)

        # Actions
        actions = QHBoxLayout()
        self.edit_btn = QPushButton("✏️ Modifier")
        self.edit_btn.clicked.connect(self.edit_selected_commande)
        self.edit_btn.setEnabled(False)
        self.reception_btn = QPushButton("📦 Réceptionner")
        self.reception_btn.clicked.connect(self.reception_selected_commande)
        self.reception_btn.setEnabled(False)
        self.pay_btn = QPushButton("💰 Payer")
        self.pay_btn.clicked.connect(self.pay_selected_commande)
        self.pay_btn.setEnabled(False)
        self.cancel_btn = QPushButton("❌ Annuler")
        self.cancel_btn.clicked.connect(self.cancel_selected_commande)
        self.cancel_btn.setEnabled(False)
        self.print_btn = QPushButton("📄 Export")
        self.print_btn.clicked.connect(self.export_pdf_selected_commande)
        self.print_btn.setEnabled(False)

        actions.addWidget(self.edit_btn)
        actions.addWidget(self.reception_btn)
        actions.addWidget(self.pay_btn)
        actions.addWidget(self.cancel_btn)
        actions.addWidget(self.print_btn)
        actions.addStretch()

        v.addLayout(actions)
        return details

    def refresh_data(self):
        try:
            session = self.achat_controller.db_manager.get_session()
            etat_filter = self.etat_combo.currentData() if hasattr(self, 'etat_combo') else None
            self.current_commandes = self.achat_controller.get_commandes(session, etat=etat_filter, limit=200)
            search_text = self.search_edit.text().strip().lower() if hasattr(self, 'search_edit') else ""
            if search_text:
                self.current_commandes = [c for c in self.current_commandes if search_text in c.numero.lower() or (c.fournisseur and search_text in c.fournisseur.nom.lower())]
            self.populate_table()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement: {e}")
        finally:
            try:
                session.close()
            except:
                pass

    def populate_table(self):
        self.table.setRowCount(len(self.current_commandes))
        for row, commande in enumerate(self.current_commandes):
            self.table.setItem(row, 0, QTableWidgetItem(str(commande.id)))
            self.table.setItem(row, 1, QTableWidgetItem(commande.numero))
            self.table.setItem(row, 2, QTableWidgetItem(commande.fournisseur.nom if commande.fournisseur else "Aucun"))
            date_str = commande.date_commande.strftime("%d/%m/%Y %H:%M") if commande.date_commande else ""
            self.table.setItem(row, 3, QTableWidgetItem(date_str))
            montant = QTableWidgetItem(self.entreprise_ctrl.format_amount(getattr(commande, 'montant_total', 0)))
            montant.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 4, montant)

            # Colonne 'Payé' - somme des paiements
            try:
                total_paye = commande.total_paye if hasattr(commande, 'total_paye') else sum(d.montant for d in commande.depenses) if commande.depenses else 0
            except Exception:
                try:
                    total_paye = sum(d.montant for d in commande.depenses) if commande.depenses else 0
                except Exception:
                    total_paye = 0
            paye_item = QTableWidgetItem(self.entreprise_ctrl.format_amount(total_paye))
            paye_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 5, paye_item)

            # Colonne 'Statut paiement'
            statut_paiement = getattr(commande, 'statut_paiement', None)
            if not statut_paiement:
                # Déterminer dynamiquement si la colonne n'existe pas en base
                if total_paye <= 0:
                    statut_paiement = "non_paye"
                elif total_paye >= commande.montant_total:
                    statut_paiement = "paye"
                else:
                    statut_paiement = "partiel"
            statut_item = QTableWidgetItem(str(statut_paiement).replace('_', ' ').title())
            self.table.setItem(row, 6, statut_item)

            # État commande (séparée du statut paiement)
            etat_item = QTableWidgetItem(commande.etat.value.title())
            if commande.etat == EtatCommande.ENCOURS:
                etat_item.setBackground(Qt.GlobalColor.yellow)
            elif commande.etat == EtatCommande.VALIDE:
                etat_item.setBackground(Qt.GlobalColor.green)
            elif commande.etat == EtatCommande.ANNULE:
                etat_item.setBackground(Qt.GlobalColor.red)
            elif commande.etat == EtatCommande.RECEPTIONNE:
                etat_item.setBackground(Qt.GlobalColor.cyan)
            self.table.setItem(row, 7, etat_item)

            self.table.setItem(row, 8, QTableWidgetItem(str(commande.entrepot_id or "-")))
            self.table.setCellWidget(row, 9, self.create_actions_widget(commande))

    def create_actions_widget(self, commande):
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(2, 2, 2, 2)
        if commande.etat == EtatCommande.ENCOURS:
            edit_btn = QPushButton("✏️")
            edit_btn.setToolTip("Modifier")
            edit_btn.clicked.connect(lambda: self.edit_commande(commande.id))
            l.addWidget(edit_btn)
            pay_btn = QPushButton("💰")
            pay_btn.setToolTip("Payer")
            pay_btn.clicked.connect(lambda: self.pay_commande(commande.id))
            l.addWidget(pay_btn)
            recv_btn = QPushButton("📦")
            recv_btn.setToolTip("Réceptionner")
            recv_btn.clicked.connect(lambda: self.reception_commande_inline(commande.id))
            l.addWidget(recv_btn)
        view_btn = QPushButton("👁️")
        view_btn.clicked.connect(lambda: self.select_commande(commande.id))
        l.addWidget(view_btn)
        return w

    def on_selection_changed(self):
        selected = self.table.selectionModel().selectedRows()
        has = len(selected) > 0
        self.edit_btn.setEnabled(has and self.current_commandes[selected[0].row()].etat == EtatCommande.ENCOURS if has else False)
        self.reception_btn.setEnabled(has)
        self.pay_btn.setEnabled(has)
        self.cancel_btn.setEnabled(has)
        self.print_btn.setEnabled(has)
        if has:
            row = selected[0].row()
            cmd = self.current_commandes[row]
            self.show_commande_details(cmd)
            self.commande_selected.emit(cmd.id)
        else:
            self.clear_details()

    def show_commande_details(self, commande: AchatCommande):
        try:
            session = self.achat_controller.db_manager.get_session()
            cmd = session.query(AchatCommande).filter_by(id=commande.id).first()
            if not cmd:
                self.clear_details()
                session.close()
                return
            self.detail_numero.setText(cmd.numero)
            self.detail_fournisseur.setText(cmd.fournisseur.nom if cmd.fournisseur else "Aucun")
            self.detail_entrepot.setText(str(cmd.entrepot_id or "Non spécifié"))
            self.detail_date.setText(cmd.date_commande.strftime("%d/%m/%Y %H:%M"))
            self.detail_montant.setText(self.entreprise_ctrl.format_amount(getattr(cmd, 'montant_total', 0)))
            # calculs paiements
            try:
                total_paye = cmd.total_paye if hasattr(cmd, 'total_paye') else (sum(d.montant for d in cmd.depenses) if cmd.depenses else Decimal('0'))
            except Exception:
                try:
                    total_paye = sum(d.montant for d in cmd.depenses) if cmd.depenses else Decimal('0')
                except Exception:
                    total_paye = Decimal('0')

            # statut paiement
            statut = getattr(cmd, 'statut_paiement', None)
            if not statut:
                if total_paye <= 0:
                    statut = "non_paye"
                elif total_paye >= cmd.montant_total:
                    statut = "paye"
                else:
                    statut = "partiel"

            self.detail_total_paye.setText(self.entreprise_ctrl.format_amount(total_paye))
            self.detail_statut_paiement.setText(str(statut).replace('_', ' ').title())
            self.detail_etat.setText(cmd.etat.value.title())

            # lignes
            self.lignes_table.setRowCount(len(cmd.lignes))
            for r, ligne in enumerate(cmd.lignes):
                try:
                    prod_name = ligne.product.name if ligne.product else f"Produit {ligne.produit_id}"
                except:
                    prod_name = f"Produit {ligne.produit_id}"
                self.lignes_table.setItem(r, 0, QTableWidgetItem(prod_name))
                self.lignes_table.setItem(r, 1, QTableWidgetItem(str(ligne.quantite)))
                self.lignes_table.setItem(r, 2, QTableWidgetItem(self.entreprise_ctrl.format_amount(getattr(ligne, 'prix_unitaire', 0))))
                self.lignes_table.setItem(r, 3, QTableWidgetItem(self.entreprise_ctrl.format_amount(getattr(ligne, 'remise_ligne', 0))))
                self.lignes_table.setItem(r, 4, QTableWidgetItem(self.entreprise_ctrl.format_amount(getattr(ligne, 'total_ligne', 0))))

            # paiements
            try:
                self.paiements_table.setRowCount(len(cmd.depenses))
                for r, d in enumerate(cmd.depenses):
                    self.paiements_table.setItem(r, 0, QTableWidgetItem(d.date_paiement.strftime("%d/%m/%Y")))
                    self.paiements_table.setItem(r, 1, QTableWidgetItem(self.entreprise_ctrl.format_amount(getattr(d, 'montant', 0))))
                    self.paiements_table.setItem(r, 2, QTableWidgetItem(d.mode_paiement or "N/A"))
                    self.paiements_table.setItem(r, 3, QTableWidgetItem(d.reference or "N/A"))
            except Exception:
                self.paiements_table.setRowCount(0)
            session.close()
        except Exception as e:
            print(f"Erreur affichage détails: {e}")
            self.clear_details()

    def clear_details(self):
        self.detail_numero.setText("-")
        self.detail_fournisseur.setText("-")
        self.detail_entrepot.setText("-")
        self.detail_date.setText("-")
        self.detail_montant.setText("-")
        self.detail_etat.setText("-")
        self.lignes_table.setRowCount(0)
        self.paiements_table.setRowCount(0)

    def select_commande(self, commande_id):
        for r in range(self.table.rowCount()):
            if self.table.item(r, 0) and self.table.item(r, 0).text() == str(commande_id):
                self.table.selectRow(r)
                break

    def pay_selected_commande(self):
        sel = self.table.selectionModel().selectedRows()
        if sel:
            cmd = self.current_commandes[sel[0].row()]
            self.pay_commande(cmd.id)

    def pay_commande(self, commande_id):
        try:
            session = self.achat_controller.db_manager.get_session()
            cmd = session.query(AchatCommande).filter_by(id=commande_id).first()
            if not cmd:
                QMessageBox.warning(self, "Erreur", "Commande introuvable")
                session.close()
                return
            montant_deja = sum(d.montant for d in cmd.depenses) if cmd.depenses else Decimal('0')
            montant_restant = cmd.montant_total - montant_deja
            if montant_restant <= 0:
                QMessageBox.information(self, "Info", "Commande déjà payée")
                session.close()
                return
            dialog = PaiementDialog(self, cmd, montant_restant)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                montant = dialog.get_montant()
                mode = dialog.get_mode_paiement()
                ref = dialog.get_reference()
                try:
                    success = self.achat_controller.process_paiement_commande(session, commande_id, montant, mode, ref)
                    if success:
                        QMessageBox.information(self, "Succès", f"Paiement de {self.entreprise_ctrl.format_amount(montant)} enregistré")
                        self.refresh_data()
                except Exception as e:
                    QMessageBox.critical(self, "Erreur", f"Erreur paiement: {e}")
            session.close()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur: {e}")

    def cancel_selected_commande(self):
        sel = self.table.selectionModel().selectedRows()
        if sel:
            cmd = self.current_commandes[sel[0].row()]
            self.cancel_commande(cmd.id)

    def cancel_commande(self, commande_id):
        reply = QMessageBox.question(self, "Confirmer", "Annuler cette commande ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                session = self.achat_controller.db_manager.get_session()
                self.achat_controller.annuler_commande(session, commande_id)
                self.refresh_data()
                session.close()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur annulation: {e}")

    def export_pdf_selected_commande(self):
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            QMessageBox.warning(self, "Attention", "Sélectionnez une commande")
            return
        cmd = self.current_commandes[sel[0].row()]
        self.export_commande_to_pdf(cmd.id)

    def export_commande_to_pdf(self, commande_id):
        try:
            session = self.achat_controller.db_manager.get_session()
            cmd = session.query(AchatCommande).filter_by(id=commande_id).first()
            if not cmd:
                QMessageBox.warning(self, "Erreur", "Commande introuvable")
                session.close()
                return
            file_name = f"Commande_{cmd.numero}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path, _ = QFileDialog.getSaveFileName(self, "Enregistrer PDF", file_name, "Fichiers PDF (*.pdf)")
            if not file_path:
                session.close()
                return
            self.generate_commande_pdf(cmd, file_path, session)
            QMessageBox.information(self, "Succès", f"Exporté vers {file_path}")
            session.close()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur export: {e}")

    def generate_commande_pdf(self, commande, file_path, session):
        # Utiliser reportlab pour un rendu professionnel similaire à celui d'EntreeSortie
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
            from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
            import tempfile
            import os

            # Récupérer infos entreprise (logo BLOB possible)
            ent_ctrl = EntrepriseController()
            comp = ent_ctrl.get_company_info_for_pdf()

            # Préparer logo si BLOB
            temp_logo = None
            logo_path = None
            if comp and comp.get('logo'):
                try:
                    blob = comp.get('logo')
                    # écrire dans un fichier temporaire
                    fd, temp_logo = tempfile.mkstemp(suffix='.png')
                    with os.fdopen(fd, 'wb') as f:
                        f.write(blob)
                    logo_path = temp_logo
                except Exception:
                    logo_path = None

            # Informations entrepôt
            from ayanna_erp.modules.stock.models import StockWarehouse
            entrepot = session.query(StockWarehouse).filter_by(id=commande.entrepot_id).first()
            entrepot_nom = entrepot.name if entrepot else 'Entrepôt inconnu'

            # Paiements
            try:
                total_paye = commande.total_paye if hasattr(commande, 'total_paye') else (sum(d.montant for d in commande.depenses) if commande.depenses else Decimal('0'))
            except Exception:
                total_paye = Decimal('0')

            statut = getattr(commande, 'statut_paiement', None)
            if not statut:
                if total_paye <= 0:
                    statut = 'non_paye'
                elif total_paye >= commande.montant_total:
                    statut = 'paye'
                else:
                    statut = 'partiel'

            # Création du document
            doc = SimpleDocTemplate(file_path, pagesize=A4,
                                    rightMargin=15*mm, leftMargin=15*mm,
                                    topMargin=15*mm, bottomMargin=20*mm)
            styles = getSampleStyleSheet()
            normal = styles['Normal']
            normal.fontName = 'Helvetica'
            normal.fontSize = 11
            heading = ParagraphStyle('Heading', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, leading=22)
            small = ParagraphStyle('Small', parent=styles['Normal'], fontSize=9)

            flow = []

            # Header: logo + company info
            header_cells = []
            if logo_path:
                try:
                    img = Image(logo_path, width=45*mm, height=45*mm)
                    header_cells.append(img)
                except Exception:
                    header_cells.append(Paragraph(f"<b>{comp.get('name','')}</b>", heading))
            else:
                header_cells.append(Paragraph(f"<b>{comp.get('name','')}</b>", heading))

            company_info = f"<b>{comp.get('name','')}</b><br/>{comp.get('address','')}<br/>Tel: {comp.get('phone','')}<br/>{comp.get('email','')}"
            header_cells.append(Paragraph(company_info, normal))

            header_table = Table([[header_cells[0], header_cells[1]]], colWidths=[50*mm, None])
            header_table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'), ('LEFTPADDING',(0,0),(-1,-1),0)]))
            flow.append(header_table)
            flow.append(Spacer(1, 6))

            # Title
            flow.append(Paragraph(f"Bon de commande - <b>{commande.numero}</b>", heading))
            flow.append(Spacer(1, 8))

            # Meta table
            meta_data = [
                ['Fournisseur', commande.fournisseur.nom if commande.fournisseur else ''],
                ['Entrepôt', entrepot_nom],
                ['Date', commande.date_commande.strftime('%d/%m/%Y %H:%M')],
                ['État', commande.etat.value.title()],
                ['Statut paiement', str(statut).replace('_',' ').title()],
                ['Montant payé', ent_ctrl.format_amount(total_paye)]
            ]
            meta_table = Table(meta_data, colWidths=[80*mm, None])
            meta_table.setStyle(TableStyle([
                ('VALIGN',(0,0),(-1,-1),'TOP'),
                ('FONTNAME',(0,0),(-1,-1),'Helvetica'),
                ('FONTSIZE',(0,0),(-1,-1),11),
                ('BOTTOMPADDING',(0,0),(-1,-1),6),
            ]))
            flow.append(meta_table)
            flow.append(Spacer(1, 8))

            # Lines table header
            items = [['Produit','Qté','PU','Remise','Total']]
            for l in commande.lignes:
                try:
                    pname = l.product.name if l.product else f"Produit {l.produit_id}"l.produit_id}"
                except Exception:
                    pname = f"Produit {l.produit_id}"
                items.append([pname, str(l.quantite), ent_ctrl.format_amount(getattr(l, 'prix_unitaire', 0)), ent_ctrl.format_amount(getattr(l, 'remise_ligne', 0)), ent_ctrl.format_amount(getattr(l, 'total_ligne', 0))])

            tbl = Table(items, colWidths=[None, 25*mm, 30*mm, 30*mm, 35*mm])
            tbl.setStyle(TableStyle([
                ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#f4f6f8')),
                ('TEXTCOLOR',(0,0),(-1,0),colors.black),
                ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#dddddd')),
                ('FONTNAME',(0,0),(-1,-1),'Helvetica'),
                ('FONTSIZE',(0,0),(-1,-1),10),
                ('ALIGN',(1,1),(-1,-1),'RIGHT'),
            ]))
            flow.append(tbl)
            flow.append(Spacer(1, 8))

            # Totals
            remainder = Decimal(commande.montant_total) - Decimal(total_paye)
            totals_paras = []
            totals_paras.append(Paragraph(f"<b>Total commande: {ent_ctrl.format_amount(commande.montant_total)}</b>", normal))
            totals_paras.append(Paragraph(f"Montant payé: {ent_ctrl.format_amount(total_paye)}", normal))
            totals_paras.append(Paragraph(f"<b>Reste à payer: {ent_ctrl.format_amount(remainder)}</b>", normal))
            for p in totals_paras:
                flow.append(p)
                flow.append(Spacer(1,4))

            # Watermark/footer on each page
            def _footer(canvas, doc):
                canvas.saveState()
                canvas.setFont('Helvetica', 8)
                canvas.setFillColor(colors.HexColor('#9aa0a6'))
                footer_text = f"Généré par {Config.APP_NAME} — Tous droits réservés"
                canvas.drawCentredString(doc.leftMargin + doc.width/2, 12*mm, footer_text)
                canvas.restoreState()

            doc.build(flow, onFirstPage=_footer, onLaterPages=_footer)

            # Nettoyer fichier logo temporaire
            if temp_logo:
                try:
                    os.remove(temp_logo)
                except Exception:
                    pass

        except ImportError:
            # reportlab non installé: retomber sur le rendu HTML/QPrinter existant
            try:
                from PyQt6.QtGui import QTextDocument
                from PyQt6.QtPrintSupport import QPrinter
                # Simple fallback: utiliser le HTML minimal
                html = f"<html><body><h2>Bon de commande - {commande.numero}</h2><p>Installez reportlab pour un rendu PDF professionnel (pip install reportlab).</p></body></html>"
                doc = QTextDocument()
                doc.setHtml(html)
                printer = QPrinter()
                printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                printer.setOutputFileName(file_path)
                doc.print(printer)
            except Exception:
                # Renvoyer l'exception si tout échoue
                raise

    def reception_selected_commande(self):
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            QMessageBox.warning(self, "Attention", "Sélectionnez une commande à réceptionner")
            return
        cmd = self.current_commandes[sel[0].row()]
        reply = QMessageBox.question(self, "Confirmer", f"Réceptionner la commande {cmd.numero} ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            session = self.achat_controller.db_manager.get_session()
            ok = self.achat_controller.reception_commande(session, cmd.id)
            if ok:
                QMessageBox.information(self, "Succès", "Commande réceptionnée")
            else:
                QMessageBox.information(self, "Info", "Commande déjà réceptionnée")
            self.refresh_data()
            self.select_commande(cmd.id)
            session.close()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur réception: {e}")

    def reception_commande_inline(self, commande_id):
        try:
            session = self.achat_controller.db_manager.get_session()
            ok = self.achat_controller.reception_commande(session, commande_id)
            if ok:
                QMessageBox.information(self, "Succès", "Commande réceptionnée")
            else:
                QMessageBox.information(self, "Info", "Commande déjà réceptionnée")
            self.refresh_data()
            session.close()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur réception: {e}")

    class EditCommandeDialog(QDialog):
        """Dialog pour modifier une commande d'achat"""

        def __init__(self, parent=None, achat_controller=None, commande=None):
            super().__init__(parent)
            self.achat_controller = achat_controller
            self.commande = commande
            self.produits = []
            try:
                self.entreprise_ctrl = EntrepriseController()
                self.currency = self.entreprise_ctrl.get_currency_symbol()
            except Exception:
                self.currency = "FC"
            self.setWindowTitle(f"Modifier Commande {commande.numero}")
            self.setFixedSize(800, 600)
            self.setup_ui()
            self.load_data()

        def setup_ui(self):
            layout = QVBoxLayout(self)

            # Infos commande
            info_group = QGroupBox("Informations commande")
            info_layout = QFormLayout(info_group)
            info_layout.addRow("Numéro:", QLabel(self.commande.numero))
            info_layout.addRow("Fournisseur:", QLabel(self.commande.fournisseur.nom if self.commande.fournisseur else "Aucun"))
            info_layout.addRow("Entrepôt:", QLabel(str(self.commande.entrepot_id)))
            layout.addWidget(info_group)

            # Lignes de commande
            lines_group = QGroupBox("Lignes de commande")
            lines_layout = QVBoxLayout(lines_group)

            # Boutons pour gérer les lignes
            lines_buttons_layout = QHBoxLayout()

            self.add_product_btn = QPushButton("➕ Ajouter des produits")
            self.add_product_btn.clicked.connect(self.add_products)
            self.add_product_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27AE60;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #219A52;
                }
            """)

            self.remove_line_btn = QPushButton("🗑️ Supprimer ligne")
            self.remove_line_btn.clicked.connect(self.remove_selected_line)
            self.remove_line_btn.setEnabled(False)

            lines_buttons_layout.addWidget(self.add_product_btn)
            lines_buttons_layout.addWidget(self.remove_line_btn)
            lines_buttons_layout.addStretch()

            lines_layout.addLayout(lines_buttons_layout)

            # Table des lignes
            self.lines_table = QTableWidget()
            self.lines_table.setColumnCount(6)
            self.lines_table.setHorizontalHeaderLabels([
                "Produit", "Quantité", "Prix unitaire", "Remise ligne", "Total ligne", "Actions"
            ])

            # Configuration de la table
            header = self.lines_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

            self.lines_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.lines_table.selectionModel().selectionChanged.connect(self.on_line_selection_changed)

            lines_layout.addWidget(self.lines_table)
            layout.addWidget(lines_group)

            # Boutons OK/Cancel
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)
            layout.addWidget(buttons)

        def load_data(self):
            # Charger produits
            session = self.achat_controller.db_manager.get_session()
            try:
                self.produits = self.achat_controller.get_produits_disponibles(session)
                # Charger lignes existantes
                self.lignes_table.setRowCount(len(self.commande.lignes))
                for row, ligne in enumerate(self.commande.lignes):
                    self.populate_ligne_row(row, ligne)
            finally:
                session.close()

        def populate_ligne_row(self, row, ligne=None):
            # Produit combo
            produit_combo = QComboBox()
            for prod in self.produits:
                produit_combo.addItem(f"{prod.name} ({prod.code})", prod.id)
            if ligne:
                index = produit_combo.findData(ligne.produit_id)
                if index >= 0:
                    produit_combo.setCurrentIndex(index)
            self.lignes_table.setCellWidget(row, 0, produit_combo)

            # Quantité
            quantite_spin = QDoubleSpinBox()
            quantite_spin.setRange(0.01, 999999)
            quantite_spin.setDecimals(2)
            quantite_spin.setValue(float(ligne.quantite) if ligne else 1.0)
            self.lignes_table.setCellWidget(row, 1, quantite_spin)

            # Prix unitaire
            prix_spin = QDoubleSpinBox()
            prix_spin.setRange(0, 999999999)
            prix_spin.setDecimals(2)
            prix_spin.setSuffix(f" {self.currency}")
            prix_spin.setValue(float(ligne.prix_unitaire) if ligne else 0.0)
            self.lignes_table.setCellWidget(row, 2, prix_spin)

            # Remise
            remise_spin = QDoubleSpinBox()
            remise_spin.setRange(0, 999999999)
            remise_spin.setDecimals(2)
            remise_spin.setSuffix(f" {self.currency}")
            remise_spin.setValue(float(ligne.remise_ligne) if ligne else 0.0)
            self.lignes_table.setCellWidget(row, 3, remise_spin)

            # Total (calculé)
            total_label = QLabel()
            self.update_total_label(row, quantite_spin, prix_spin, remise_spin, total_label)
            quantite_spin.valueChanged.connect(lambda: self.update_total_label(row, quantite_spin, prix_spin, remise_spin, total_label))
            prix_spin.valueChanged.connect(lambda: self.update_total_label(row, quantite_spin, prix_spin, remise_spin, total_label))
            remise_spin.valueChanged.connect(lambda: self.update_total_label(row, quantite_spin, prix_spin, remise_spin, total_label))
            self.lignes_table.setCellWidget(row, 4, total_label)

            # Actions
            delete_btn = QPushButton("🗑️")
            delete_btn.clicked.connect(lambda: self.delete_ligne(row))
            self.lignes_table.setCellWidget(row, 5, delete_btn)

        def update_total_label(self, row, quantite_spin, prix_spin, remise_spin, total_label):
            quantite = Decimal(str(quantite_spin.value()))
            prix = Decimal(str(prix_spin.value()))
            remise = Decimal(str(remise_spin.value()))
            total = (quantite * prix) - remise
            total_label.setText(self.entreprise_ctrl.format_amount(total))

        def add_ligne(self):
            row = self.lignes_table.rowCount()
            self.lignes_table.insertRow(row)
            self.populate_ligne_row(row)

        def delete_ligne(self, row):
            self.lignes_table.removeRow(row)

        def get_lignes_data(self):
            lignes = []
            for row in range(self.lignes_table.rowCount()):
                produit_combo = self.lignes_table.cellWidget(row, 0)
                quantite_spin = self.lignes_table.cellWidget(row, 1)
                prix_spin = self.lignes_table.cellWidget(row, 2)
                remise_spin = self.lignes_table.cellWidget(row, 3)

                if produit_combo and quantite_spin and prix_spin and remise_spin:
                    lignes.append({
                        'produit_id': produit_combo.currentData(),
                        'quantite': Decimal(str(quantite_spin.value())),
                        'prix_unitaire': Decimal(str(prix_spin.value())),
                        'remise_ligne': Decimal(str(remise_spin.value()))
                    })
            return lignes

        def add_products(self):
            # Pour simplifier, on ajoute juste une ligne vide
            self.add_ligne()

        def remove_selected_line(self):
            selected_rows = self.lines_table.selectionModel().selectedRows()
            if selected_rows:
                row = selected_rows[0].row()
                self.delete_ligne(row)

        def on_line_selection_changed(self):
            has_selection = len(self.lines_table.selectionModel().selectedRows()) > 0
            self.remove_line_btn.setEnabled(has_selection)


class CommandesWidget(QWidget):
    """Widget principal pour la gestion des commandes d'achat"""

    commande_updated = pyqtSignal(int)
    commande_selected = pyqtSignal(int)

    def __init__(self, achat_controller: AchatController):
        super().__init__()
        self.achat_controller = achat_controller
        # Récupérer le symbole de la devise dynamique pour affichage
        try:
            self.entreprise_ctrl = EntrepriseController()
            self.currency = self.entreprise_ctrl.get_currency_symbol()
        except Exception:
            self.currency = "FC"
        self.current_commandes = []
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Left: header + table
        left_v = QVBoxLayout()
        header_h = QHBoxLayout()
        title = QLabel("📋 Gestion des Commandes")
        title.setStyleSheet("font-weight:600; font-size:15px;")

        filters = QGroupBox("Filtres")
        f_layout = QHBoxLayout(filters)
        f_layout.addWidget(QLabel("État:"))
        self.etat_combo = QComboBox()
        self.etat_combo.addItem("Tous", None)
        self.etat_combo.addItem("En cours", EtatCommande.ENCOURS)
        self.etat_combo.addItem("Réceptionné", EtatCommande.RECEPTIONNE)
        self.etat_combo.addItem("Validé", EtatCommande.VALIDE)
        self.etat_combo.addItem("Annulé", EtatCommande.ANNULE)
        self.etat_combo.currentIndexChanged.connect(self.refresh_data)
        f_layout.addWidget(self.etat_combo)

        f_layout.addWidget(QLabel("Recherche:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Numéro, fournisseur...")
        self.search_edit.textChanged.connect(self.refresh_data)
        f_layout.addWidget(self.search_edit)

        refresh_btn = QPushButton("🔄")
        refresh_btn.clicked.connect(self.refresh_data)
        f_layout.addWidget(refresh_btn)

        header_h.addWidget(title)
        header_h.addStretch()
        header_h.addWidget(filters)

        left_v.addLayout(header_h)

        self.table = QTableWidget()
        # Colonnes: ID, Numéro, Fournisseur, Date, Montant, Payé, Statut Paiement, État, Entrepôt, Actions
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(["ID", "Numéro", "Fournisseur", "Date", "Montant", "Payé", "Statut paiement", "État", "Entrepôt", "Actions"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        left_v.addWidget(self.table)

        left_widget = QWidget()
        left_widget.setLayout(left_v)

        # Right: details
        right_widget = self.create_details_widget()

        main_layout.addWidget(left_widget, 2)
        main_layout.addWidget(right_widget, 1)

    def create_details_widget(self):
        details = QGroupBox("Détails de la commande")
        v = QVBoxLayout(details)

        tabs = QTabWidget()
        info_w = QWidget()
        info_form = QFormLayout(info_w)
        self.detail_numero = QLabel("-")
        self.detail_fournisseur = QLabel("-")
        self.detail_entrepot = QLabel("-")
        self.detail_date = QLabel("-")
        self.detail_montant = QLabel("-")
        self.detail_statut_paiement = QLabel("-")
        self.detail_total_paye = QLabel("-")
        self.detail_etat = QLabel("-")
        info_form.addRow("Numéro:", self.detail_numero)
        info_form.addRow("Fournisseur:", self.detail_fournisseur)
        info_form.addRow("Entrepôt:", self.detail_entrepot)
        info_form.addRow("Date:", self.detail_date)
        info_form.addRow("Montant:", self.detail_montant)
        info_form.addRow("Montant payé:", self.detail_total_paye)
        info_form.addRow("Statut paiement:", self.detail_statut_paiement)
        info_form.addRow("État:", self.detail_etat)
        tabs.addTab(info_w, "Infos")

        lignes_w = QWidget()
        lignes_v = QVBoxLayout(lignes_w)
        self.lignes_table = QTableWidget()
        self.lignes_table.setColumnCount(5)
        self.lignes_table.setHorizontalHeaderLabels(["Produit", "Quantité", "Prix", "Remise", "Total"])
        lignes_v.addWidget(self.lignes_table)
        tabs.addTab(lignes_w, "Lignes")

        paiements_w = QWidget()
        paiements_v = QVBoxLayout(paiements_w)
        self.paiements_table = QTableWidget()
        self.paiements_table.setColumnCount(4)
        self.paiements_table.setHorizontalHeaderLabels(["Date", "Montant", "Mode", "Réf."])
        paiements_v.addWidget(self.paiements_table)
        tabs.addTab(paiements_w, "Paiements")

        v.addWidget(tabs)

        # Actions
        actions = QHBoxLayout()
        self.edit_btn = QPushButton("✏️ Modifier")
        self.edit_btn.clicked.connect(self.edit_selected_commande)
        self.edit_btn.setEnabled(False)
        self.reception_btn = QPushButton("📦 Réceptionner")
        self.reception_btn.clicked.connect(self.reception_selected_commande)
        self.reception_btn.setEnabled(False)
        self.pay_btn = QPushButton("💰 Payer")
        self.pay_btn.clicked.connect(self.pay_selected_commande)
        self.pay_btn.setEnabled(False)
        self.cancel_btn = QPushButton("❌ Annuler")
        self.cancel_btn.clicked.connect(self.cancel_selected_commande)
        self.cancel_btn.setEnabled(False)
        self.print_btn = QPushButton("📄 Export")
        self.print_btn.clicked.connect(self.export_pdf_selected_commande)
        self.print_btn.setEnabled(False)

        actions.addWidget(self.edit_btn)
        actions.addWidget(self.reception_btn)
        actions.addWidget(self.pay_btn)
        actions.addWidget(self.cancel_btn)
        actions.addWidget(self.print_btn)
        actions.addStretch()

        v.addLayout(actions)
        return details

    def refresh_data(self):
        try:
            session = self.achat_controller.db_manager.get_session()
            etat_filter = self.etat_combo.currentData() if hasattr(self, 'etat_combo') else None
            self.current_commandes = self.achat_controller.get_commandes(session, etat=etat_filter, limit=200)
            search_text = self.search_edit.text().strip().lower() if hasattr(self, 'search_edit') else ""
            if search_text:
                self.current_commandes = [c for c in self.current_commandes if search_text in c.numero.lower() or (c.fournisseur and search_text in c.fournisseur.nom.lower())]
            self.populate_table()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement: {e}")
        finally:
            try:
                session.close()
            except:
                pass

    def populate_table(self):
        self.table.setRowCount(len(self.current_commandes))
        for row, commande in enumerate(self.current_commandes):
            self.table.setItem(row, 0, QTableWidgetItem(str(commande.id)))
            self.table.setItem(row, 1, QTableWidgetItem(commande.numero))
            self.table.setItem(row, 2, QTableWidgetItem(commande.fournisseur.nom if commande.fournisseur else "Aucun"))
            date_str = commande.date_commande.strftime("%d/%m/%Y %H:%M") if commande.date_commande else ""
            self.table.setItem(row, 3, QTableWidgetItem(date_str))
            montant = QTableWidgetItem(self.entreprise_ctrl.format_amount(getattr(commande, 'montant_total', 0)))
            montant.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 4, montant)

            # Colonne 'Payé' - somme des paiements
            try:
                total_paye = commande.total_paye if hasattr(commande, 'total_paye') else sum(d.montant for d in commande.depenses) if commande.depenses else 0
            except Exception:
                try:
                    total_paye = sum(d.montant for d in commande.depenses) if commande.depenses else 0
                except Exception:
                    total_paye = 0
            paye_item = QTableWidgetItem(self.entreprise_ctrl.format_amount(total_paye))
            paye_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 5, paye_item)

            # Colonne 'Statut paiement'
            statut_paiement = getattr(commande, 'statut_paiement', None)
            if not statut_paiement:
                # Déterminer dynamiquement si la colonne n'existe pas en base
                if total_paye <= 0:
                    statut_paiement = "non_paye"
                elif total_paye >= commande.montant_total:
                    statut_paiement = "paye"
                else:
                    statut_paiement = "partiel"
            statut_item = QTableWidgetItem(str(statut_paiement).replace('_', ' ').title())
            self.table.setItem(row, 6, statut_item)

            # État commande (séparée du statut paiement)
            etat_item = QTableWidgetItem(commande.etat.value.title())
            if commande.etat == EtatCommande.ENCOURS:
                etat_item.setBackground(Qt.GlobalColor.yellow)
            elif commande.etat == EtatCommande.VALIDE:
                etat_item.setBackground(Qt.GlobalColor.green)
            elif commande.etat == EtatCommande.ANNULE:
                etat_item.setBackground(Qt.GlobalColor.red)
            elif commande.etat == EtatCommande.RECEPTIONNE:
                etat_item.setBackground(Qt.GlobalColor.cyan)
            self.table.setItem(row, 7, etat_item)

            self.table.setItem(row, 8, QTableWidgetItem(str(commande.entrepot_id or "-")))
            self.table.setCellWidget(row, 9, self.create_actions_widget(commande))

    def create_actions_widget(self, commande):
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(2, 2, 2, 2)
        if commande.etat == EtatCommande.ENCOURS:
            edit_btn = QPushButton("✏️")
            edit_btn.setToolTip("Modifier")
            edit_btn.clicked.connect(lambda: self.edit_commande(commande.id))
            l.addWidget(edit_btn)
            pay_btn = QPushButton("💰")
            pay_btn.setToolTip("Payer")
            pay_btn.clicked.connect(lambda: self.pay_commande(commande.id))
            l.addWidget(pay_btn)
            recv_btn = QPushButton("📦")
            recv_btn.setToolTip("Réceptionner")
            recv_btn.clicked.connect(lambda: self.reception_commande_inline(commande.id))
            l.addWidget(recv_btn)
        view_btn = QPushButton("👁️")
        view_btn.clicked.connect(lambda: self.select_commande(commande.id))
        l.addWidget(view_btn)
        return w

    def on_selection_changed(self):
        selected = self.table.selectionModel().selectedRows()
        has = len(selected) > 0
        self.edit_btn.setEnabled(has and self.current_commandes[selected[0].row()].etat == EtatCommande.ENCOURS if has else False)
        self.reception_btn.setEnabled(has)
        self.pay_btn.setEnabled(has)
        self.cancel_btn.setEnabled(has)
        self.print_btn.setEnabled(has)
        if has:
            row = selected[0].row()
            cmd = self.current_commandes[row]
            self.show_commande_details(cmd)
            self.commande_selected.emit(cmd.id)
        else:
            self.clear_details()

    def show_commande_details(self, commande: AchatCommande):
        try:
            session = self.achat_controller.db_manager.get_session()
            cmd = session.query(AchatCommande).filter_by(id=commande.id).first()
            if not cmd:
                self.clear_details()
                session.close()
                return
            self.detail_numero.setText(cmd.numero)
            self.detail_fournisseur.setText(cmd.fournisseur.nom if cmd.fournisseur else "Aucun")
            self.detail_entrepot.setText(str(cmd.entrepot_id or "Non spécifié"))
            self.detail_date.setText(cmd.date_commande.strftime("%d/%m/%Y %H:%M"))
            self.detail_montant.setText(self.entreprise_ctrl.format_amount(getattr(cmd, 'montant_total', 0)))
            # calculs paiements
            try:
                total_paye = cmd.total_paye if hasattr(cmd, 'total_paye') else (sum(d.montant for d in cmd.depenses) if cmd.depenses else Decimal('0'))
            except Exception:
                try:
                    total_paye = sum(d.montant for d in cmd.depenses) if cmd.depenses else Decimal('0')
                except Exception:
                    total_paye = Decimal('0')

            # statut paiement
            statut = getattr(cmd, 'statut_paiement', None)
            if not statut:
                if total_paye <= 0:
                    statut = "non_paye"
                elif total_paye >= cmd.montant_total:
                    statut = "paye"
                else:
                    statut = "partiel"

            self.detail_total_paye.setText(self.entreprise_ctrl.format_amount(total_paye))
            self.detail_statut_paiement.setText(str(statut).replace('_', ' ').title())
            self.detail_etat.setText(cmd.etat.value.title())

            # lignes
            self.lignes_table.setRowCount(len(cmd.lignes))
            for r, ligne in enumerate(cmd.lignes):
                try:
                    prod_name = ligne.product.name if ligne.product else f"Produit {ligne.produit_id}"
                except:
                    prod_name = f"Produit {ligne.produit_id}"
                self.lignes_table.setItem(r, 0, QTableWidgetItem(prod_name))
                self.lignes_table.setItem(r, 1, QTableWidgetItem(str(ligne.quantite)))
                self.lignes_table.setItem(r, 2, QTableWidgetItem(self.entreprise_ctrl.format_amount(getattr(ligne, 'prix_unitaire', 0))))
                self.lignes_table.setItem(r, 3, QTableWidgetItem(self.entreprise_ctrl.format_amount(getattr(ligne, 'remise_ligne', 0))))
                self.lignes_table.setItem(r, 4, QTableWidgetItem(self.entreprise_ctrl.format_amount(getattr(ligne, 'total_ligne', 0))))

            # paiements
            try:
                self.paiements_table.setRowCount(len(cmd.depenses))
                for r, d in enumerate(cmd.depenses):
                    self.paiements_table.setItem(r, 0, QTableWidgetItem(d.date_paiement.strftime("%d/%m/%Y")))
                    self.paiements_table.setItem(r, 1, QTableWidgetItem(self.entreprise_ctrl.format_amount(getattr(d, 'montant', 0))))
                    self.paiements_table.setItem(r, 2, QTableWidgetItem(d.mode_paiement or "N/A"))
                    self.paiements_table.setItem(r, 3, QTableWidgetItem(d.reference or "N/A"))
            except Exception:
                self.paiements_table.setRowCount(0)
            session.close()
        except Exception as e:
            print(f"Erreur affichage détails: {e}")
            self.clear_details()

    def clear_details(self):
        self.detail_numero.setText("-")
        self.detail_fournisseur.setText("-")
        self.detail_entrepot.setText("-")
        self.detail_date.setText("-")
        self.detail_montant.setText("-")
        self.detail_etat.setText("-")
        self.lignes_table.setRowCount(0)
        self.paiements_table.setRowCount(0)

    def select_commande(self, commande_id):
        for r in range(self.table.rowCount()):
            if self.table.item(r, 0) and self.table.item(r, 0).text() == str(commande_id):
                self.table.selectRow(r)
                break

    def pay_selected_commande(self):
        sel = self.table.selectionModel().selectedRows()
        if sel:
            cmd = self.current_commandes[sel[0].row()]
            self.pay_commande(cmd.id)

    def pay_commande(self, commande_id):
        try:
            session = self.achat_controller.db_manager.get_session()
            cmd = session.query(AchatCommande).filter_by(id=commande_id).first()
            if not cmd:
                QMessageBox.warning(self, "Erreur", "Commande introuvable")
                session.close()
                return
            montant_deja = sum(d.montant for d in cmd.depenses) if cmd.depenses else Decimal('0')
            montant_restant = cmd.montant_total - montant_deja
            if montant_restant <= 0:
                QMessageBox.information(self, "Info", "Commande déjà payée")
                session.close()
                return
            dialog = PaiementDialog(self, cmd, montant_restant)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                montant = dialog.get_montant()
                mode = dialog.get_mode_paiement()
                ref = dialog.get_reference()
                try:
                    success = self.achat_controller.process_paiement_commande(session, commande_id, montant, mode, ref)
                    if success:
                        QMessageBox.information(self, "Succès", f"Paiement de {self.entreprise_ctrl.format_amount(montant)} enregistré")
                        self.refresh_data()
                except Exception as e:
                    QMessageBox.critical(self, "Erreur", f"Erreur paiement: {e}")
            session.close()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur: {e}")

    def cancel_selected_commande(self):
        sel = self.table.selectionModel().selectedRows()
        if sel:
            cmd = self.current_commandes[sel[0].row()]
            self.cancel_commande(cmd.id)

    def cancel_commande(self, commande_id):
        reply = QMessageBox.question(self, "Confirmer", "Annuler cette commande ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                session = self.achat_controller.db_manager.get_session()
                self.achat_controller.annuler_commande(session, commande_id)
                self.refresh_data()
                session.close()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur annulation: {e}")

    def export_pdf_selected_commande(self):
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            QMessageBox.warning(self, "Attention", "Sélectionnez une commande")
            return
        cmd = self.current_commandes[sel[0].row()]
        self.export_commande_to_pdf(cmd.id)

    def export_commande_to_pdf(self, commande_id):
        try:
            session = self.achat_controller.db_manager.get_session()
            cmd = session.query(AchatCommande).filter_by(id=commande_id).first()
            if not cmd:
                QMessageBox.warning(self, "Erreur", "Commande introuvable")
                session.close()
                return
            file_name = f"Commande_{cmd.numero}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path, _ = QFileDialog.getSaveFileName(self, "Enregistrer PDF", file_name, "Fichiers PDF (*.pdf)")
            if not file_path:
                session.close()
                return
            self.generate_commande_pdf(cmd, file_path, session)
            QMessageBox.information(self, "Succès", f"Exporté vers {file_path}")
            session.close()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur export: {e}")

    def generate_commande_pdf(self, commande, file_path, session):
        # Utiliser reportlab pour un rendu professionnel similaire à celui d'EntreeSortie
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
            from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
            import tempfile
            import os

            # Récupérer infos entreprise (logo BLOB possible)
            ent_ctrl = EntrepriseController()
            comp = ent_ctrl.get_company_info_for_pdf()

            # Préparer logo si BLOB
            temp_logo = None
            logo_path = None
            if comp and comp.get('logo'):
                try:
                    blob = comp.get('logo')
                    # écrire dans un fichier temporaire
                    fd, temp_logo = tempfile.mkstemp(suffix='.png')
                    with os.fdopen(fd, 'wb') as f:
                        f.write(blob)
                    logo_path = temp_logo
                except Exception:
                    logo_path = None

            # Informations entrepôt
            from ayanna_erp.modules.stock.models import StockWarehouse
            entrepot = session.query(StockWarehouse).filter_by(id=commande.entrepot_id).first()
            entrepot_nom = entrepot.name if entrepot else 'Entrepôt inconnu'

            # Paiements
            try:
                total_paye = commande.total_paye if hasattr(commande, 'total_paye') else (sum(d.montant for d in commande.depenses) if commande.depenses else Decimal('0'))
            except Exception:
                total_paye = Decimal('0')

            statut = getattr(commande, 'statut_paiement', None)
            if not statut:
                if total_paye <= 0:
                    statut = 'non_paye'
                elif total_paye >= commande.montant_total:
                    statut = 'paye'
                else:
                    statut = 'partiel'

            # Création du document
            doc = SimpleDocTemplate(file_path, pagesize=A4,
                                    rightMargin=15*mm, leftMargin=15*mm,
                                    topMargin=15*mm, bottomMargin=20*mm)
            styles = getSampleStyleSheet()
            normal = styles['Normal']
            normal.fontName = 'Helvetica'
            normal.fontSize = 11
            heading = ParagraphStyle('Heading', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, leading=22)
            small = ParagraphStyle('Small', parent=styles['Normal'], fontSize=9)

            flow = []

            # Header: logo + company info
            header_cells = []
            if logo_path:
                try:
                    img = Image(logo_path, width=45*mm, height=45*mm)
                    header_cells.append(img)
                except Exception:
                    header_cells.append(Paragraph(f"<b>{comp.get('name','')}</b>", heading))
            else:
                header_cells.append(Paragraph(f"<b>{comp.get('name','')}</b>", heading))

            company_info = f"<b>{comp.get('name','')}</b><br/>{comp.get('address','')}<br/>Tel: {comp.get('phone','')}<br/>{comp.get('email','')}"
            header_cells.append(Paragraph(company_info, normal))

            header_table = Table([[header_cells[0], header_cells[1]]], colWidths=[50*mm, None])
            header_table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'), ('LEFTPADDING',(0,0),(-1,-1),0)]))
            flow.append(header_table)
            flow.append(Spacer(1, 6))

            # Title
            flow.append(Paragraph(f"Bon de commande - <b>{commande.numero}</b>", heading))
            flow.append(Spacer(1, 8))

            # Meta table
            meta_data = [
                ['Fournisseur', commande.fournisseur.nom if commande.fournisseur else ''],
                ['Entrepôt', entrepot_nom],
                ['Date', commande.date_commande.strftime('%d/%m/%Y %H:%M')],
                ['État', commande.etat.value.title()],
                ['Statut paiement', str(statut).replace('_',' ').title()],
                ['Montant payé', ent_ctrl.format_amount(total_paye)]
            ]
            meta_table = Table(meta_data, colWidths=[80*mm, None])
            meta_table.setStyle(TableStyle([
                ('VALIGN',(0,0),(-1,-1),'TOP'),
                ('FONTNAME',(0,0),(-1,-1),'Helvetica'),
                ('FONTSIZE',(0,0),(-1,-1),11),
                ('BOTTOMPADDING',(0,0),(-1,-1),6),
            ]))
            flow.append(meta_table)
            flow.append(Spacer(1, 8))

            # Lines table header
            items = [['Produit','Qté','PU','Remise','Total']]
            for l in commande.lignes:
                try:
                    pname = l.product.name if l.product else f"Produit {l.produit_id}"
