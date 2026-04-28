"""
Widget pour la gestion des commandes d'achat
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QComboBox, QHeaderView, QMessageBox,
    QTabWidget, QGroupBox, QFormLayout, QTextEdit, QDialog,
    QDialogButtonBox, QDoubleSpinBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread, QObject
from decimal import Decimal
from datetime import datetime
import os
import sys
import subprocess
import tempfile

from ayanna_erp.modules.achats.controllers import AchatController
from ayanna_erp.modules.achats.models.achats_models import AchatCommande, EtatCommande
from ayanna_erp.core.config import Config
from ayanna_erp.core.entreprise_controller import EntrepriseController
from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaComptes, ComptaConfig


class LoadDataWorker(QObject):
    """Worker pour charger les données en arrière-plan dans un thread séparé"""
    finished = pyqtSignal(list, str, int)  # commandes, search_text, etat_filter
    error = pyqtSignal(str)
    
    def __init__(self, achat_controller, etat_filter=None, search_text=""):
        super().__init__()
        self.achat_controller = achat_controller
        self.etat_filter = etat_filter
        self.search_text = search_text
        
    def run(self):
        """Charger les données (optimisé et sécurisé)"""
        session = None
        try:
            # 🔹 Ouverture session
            session = self.achat_controller.db_manager.get_session()

            # 🔹 Appel optimisé (filtrage SQL inclus)
            commandes = self.achat_controller.get_commandes(
                session=session,
                etat=self.etat_filter,
                search_text=self.search_text,
                limit=25  # Limite pour éviter surcharge, pagination à implémenter si besoin
            )

            # 🔥 DÉTACHER les objets AVANT fermeture session
            for cmd in commandes:
                session.expunge(cmd)
            # 🔹 Émission résultat
            self.finished.emit(commandes, self.search_text, self.etat_filter)

        except Exception as e:
            # 🔥 Toujours capturer proprement les erreurs
            self.error.emit(str(e))


class PaiementDialog(QDialog):
    """Dialog pour saisir un paiement (avec sélection du compte financier)"""

    def __init__(self, parent=None, commande=None, montant_restant=0, achat_controller: AchatController = None):
        super().__init__(parent)
        self.commande = commande
        self.montant_restant = montant_restant
        self.achat_controller = achat_controller
        # Récupérer le symbole de la devise dynamique
        try:
            self.entreprise_ctrl = EntrepriseController()
            self.currency = self.entreprise_ctrl.get_currency_symbol()
        except Exception:
            self.currency = "FC"
        self.setWindowTitle(f"Paiement - Commande {commande.numero}")
        # Fenêtre agrandie et modal
        self.setMinimumSize(520, 420)
        self.resize(520, 420)
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        # Style général et layout
        self.setStyleSheet("""
            QWidget { font-family: 'Segoe UI', Arial, sans-serif; font-size: 11px; }
            QGroupBox { font-weight: 600; font-size: 13px; margin-top: 6px; }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 3px 0 3px; }
            QDialogButtonBox QPushButton { padding: 8px 14px; border-radius: 6px; }
            QComboBox, QLineEdit, QDoubleSpinBox, QTextEdit { padding: 6px; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

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
        self.montant_spinbox.setFixedWidth(180)
        pay_form.addRow("Montant*:", self.montant_spinbox)

        self.mode_combo = QComboBox()
        try:
            from ayanna_erp.core.view.payment_mode_widget import get_active_payment_modes
            for m in get_active_payment_modes():
                self.mode_combo.addItem(m['label'], m['code'])
        except Exception:
            self.mode_combo.addItems(["Espèces", "Banque", "Mobile Money", "Crédit"])
        pay_form.addRow("Mode*:", self.mode_combo)

        self.reference_edit = QLineEdit()
        self.reference_edit.setPlaceholderText("Référence (chèque, virement...)")
        self.reference_edit.setFixedWidth(320)
        pay_form.addRow("Référence:", self.reference_edit)

        # Compte financier (optionnel) : permettre de choisir le compte à créditer
        self.compte_financier_combo = QComboBox()
        self.compte_financier_combo.addItem("-- Sélectionner compte financier --", None)
        # Charger les comptes financiers (classe 5) depuis la base
        try:
            if self.achat_controller and getattr(self.achat_controller, 'db_manager', None):
                session = self.achat_controller.db_manager.get_session()
                try:
                    comptes = session.query(ComptaComptes).filter(ComptaComptes.numero.like('5%')).order_by(ComptaComptes.numero).all()

                    # Récupérer les soldes pour tous les comptes en une seule requête GROUP BY
                    try:
                        from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaEcritures
                        from sqlalchemy import func
                        compte_ids = [c.id for c in comptes]
                        balances = {}
                        if compte_ids:
                            rows = session.query(
                                ComptaEcritures.compte_comptable_id,
                                func.coalesce(func.sum(ComptaEcritures.debit), 0) - func.coalesce(func.sum(ComptaEcritures.credit), 0)
                            ).filter(ComptaEcritures.compte_comptable_id.in_(compte_ids)).group_by(ComptaEcritures.compte_comptable_id).all()
                            for cid, bal in rows:
                                balances[cid] = bal or 0
                    except Exception:
                        balances = {}

                    for c in comptes:
                        try:
                            bal = balances.get(c.id, 0)
                            try:
                                formatted = self.entreprise_ctrl.format_amount(bal)
                            except Exception:
                                formatted = str(bal)
                            saldo_text = f"Solde: {formatted}"
                        except Exception:
                            saldo_text = None

                        compte_nom = getattr(c, 'nom', None) or getattr(c, 'name', '') or ''
                        base_label = f"{c.numero} - {compte_nom}"
                        label = f"{base_label} - {saldo_text}" if saldo_text else base_label
                        self.compte_financier_combo.addItem(label, c.id)
                    # sélectionner le compte caisse par défaut si présent dans la config
                    config = session.query(ComptaConfig).filter_by(enterprise_id=getattr(self.achat_controller, 'entreprise_id', None)).first()
                    if config and config.compte_caisse_id:
                        idx = self.compte_financier_combo.findData(config.compte_caisse_id)
                        if idx >= 0:
                            self.compte_financier_combo.setCurrentIndex(idx)
                finally:
                    session.close()
        except Exception:
            pass

        # largeur du combo pour meilleure lisibilité
        self.compte_financier_combo.setFixedWidth(360)
        pay_form.addRow("Compte financier:", self.compte_financier_combo)

        self.commentaire = QTextEdit()
        self.commentaire.setMaximumHeight(60)
        pay_form.addRow("Commentaire:", self.commentaire)

        layout.addWidget(pay_group)

        # Boutons OK/Cancel stylés et centrés
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        try:
            btn_ok = buttons.button(QDialogButtonBox.StandardButton.Ok)
            if btn_ok:
                btn_ok.setStyleSheet('background-color: #27AE60; color: white; font-weight:600;')
            btn_cancel = buttons.button(QDialogButtonBox.StandardButton.Cancel)
            if btn_cancel:
                btn_cancel.setStyleSheet('background-color: #E0E0E0;')
        except Exception:
            pass
        btn_holder = QHBoxLayout()
        btn_holder.addStretch()
        btn_holder.addWidget(buttons)
        btn_holder.addStretch()
        layout.addLayout(btn_holder)

    def get_montant(self):
        return Decimal(str(self.montant_spinbox.value()))

    def get_mode_paiement(self):
        return self.mode_combo.currentText()

    def get_reference(self):
        return self.reference_edit.text().strip()

    def get_compte_financier_id(self):
        return self.compte_financier_combo.currentData()

    def accept(self) -> None:
        """Valider le dialogue seulement si un compte financier est sélectionné."""
        compte_id = self.get_compte_financier_id()
        if not compte_id:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un compte financier.")
            return
        super().accept()


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
            self.lines_table.setRowCount(len(self.commande.lignes))
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
        self.lines_table.setCellWidget(row, 0, produit_combo)

        # Quantité
        quantite_spin = QDoubleSpinBox()
        quantite_spin.setRange(0.01, 999999)
        quantite_spin.setDecimals(2)
        quantite_spin.setValue(float(ligne.quantite) if ligne else 1.0)
        self.lines_table.setCellWidget(row, 1, quantite_spin)

        # Prix unitaire
        prix_spin = QDoubleSpinBox()
        prix_spin.setRange(0, 999999999)
        prix_spin.setDecimals(2)
        prix_spin.setSuffix(f" {self.currency}")
        prix_spin.setValue(float(ligne.prix_unitaire) if ligne else 0.0)
        self.lines_table.setCellWidget(row, 2, prix_spin)

        # Remise
        remise_spin = QDoubleSpinBox()
        remise_spin.setRange(0, 999999999)
        remise_spin.setDecimals(2)
        remise_spin.setSuffix(f" {self.currency}")
        remise_spin.setValue(float(ligne.remise_ligne) if ligne else 0.0)
        self.lines_table.setCellWidget(row, 3, remise_spin)

        # Total (calculé)
        total_label = QLabel()
        self.update_total_label(row, quantite_spin, prix_spin, remise_spin, total_label)
        quantite_spin.valueChanged.connect(lambda: self.update_total_label(row, quantite_spin, prix_spin, remise_spin, total_label))
        prix_spin.valueChanged.connect(lambda: self.update_total_label(row, quantite_spin, prix_spin, remise_spin, total_label))
        remise_spin.valueChanged.connect(lambda: self.update_total_label(row, quantite_spin, prix_spin, remise_spin, total_label))
        self.lines_table.setCellWidget(row, 4, total_label)

        # Actions
        delete_btn = QPushButton("🗑️")
        delete_btn.clicked.connect(lambda: self.delete_ligne(row))
        self.lines_table.setCellWidget(row, 5, delete_btn)

    def update_total_label(self, row, quantite_spin, prix_spin, remise_spin, total_label):
        quantite = Decimal(str(quantite_spin.value()))
        prix = Decimal(str(prix_spin.value()))
        remise = Decimal(str(remise_spin.value()))
        total = (quantite * prix) - remise
        total_label.setText(self.entreprise_ctrl.format_amount(total))

    def add_ligne(self):
        row = self.lines_table.rowCount()
        self.lines_table.insertRow(row)
        self.populate_ligne_row(row)

    def delete_ligne(self, row):
        self.lines_table.removeRow(row)

    def get_lignes_data(self):
        lignes = []
        for row in range(self.lines_table.rowCount()):
            produit_combo = self.lines_table.cellWidget(row, 0)
            quantite_spin = self.lines_table.cellWidget(row, 1)
            prix_spin = self.lines_table.cellWidget(row, 2)
            remise_spin = self.lines_table.cellWidget(row, 3)

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

    def __init__(self, achat_controller: AchatController, current_user=None):
        super().__init__()
        self.achat_controller = achat_controller
        self.current_user = current_user
        # Récupérer le symbole de la devise dynamique pour affichage
        try:
            self.entreprise_ctrl = EntrepriseController()
            self.currency = self.entreprise_ctrl.get_currency_symbol()
        except Exception:
            self.currency = "FC"
        self.current_commandes = []
        
        # Thread pour le chargement des données
        self.data_thread = None
        self.data_worker = None
        
        self.setup_ui()
        self._schedule_refresh()
    
    def get_username_by_id(self, session, utilisateur_id):
        """Récupère le nom d'un utilisateur par son ID"""
        if not utilisateur_id:
            return "-"
        try:
            from ayanna_erp.database.database_manager import User
            user = session.query(User).filter_by(id=utilisateur_id).first()
            if user and user.name:
                return user.name
            return f"Utilisateur #{utilisateur_id}"
        except Exception:
            return f"Utilisateur #{utilisateur_id}"

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
        # Colonnes simplifiées: ID, Date, Montant, Payé, Statut Paiement, État, Utilisateur
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["N° Commande", "Date", "Montant", "Payé", "Statut paiement", "État", "Utilisateur"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Date
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Montant
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Payé
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Statut
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # État
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Utilisateur
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
        self.detail_utilisateur = QLabel("-")
        info_form.addRow("Numéro:", self.detail_numero)
        info_form.addRow("Fournisseur:", self.detail_fournisseur)
        info_form.addRow("Entrepôt:", self.detail_entrepot)
        info_form.addRow("Date:", self.detail_date)
        info_form.addRow("Montant:", self.detail_montant)
        info_form.addRow("Montant payé:", self.detail_total_paye)
        info_form.addRow("Statut paiement:", self.detail_statut_paiement)
        info_form.addRow("État:", self.detail_etat)
        info_form.addRow("Utilisateur:", self.detail_utilisateur)
        tabs.addTab(info_w, "Infos")

        lignes_w = QWidget()
        lignes_v = QVBoxLayout(lignes_w)
        self.lignes_table = QTableWidget()
        self.lignes_table.setColumnCount(7)
        self.lignes_table.setHorizontalHeaderLabels(["Produit", "Qté", "PU Achat", "PU Vente", "Remise", "Total Achat", "Total Vente"])
        # Configuration des colonnes
        lignes_header = self.lignes_table.horizontalHeader()
        lignes_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Produit
        for i in range(1, 7):
            lignes_header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        lignes_v.addWidget(self.lignes_table)
        
        # Zone des totaux
        totaux_layout = QHBoxLayout()
        self.total_achat_label = QLabel("Total Achat: -")
        self.total_achat_label.setStyleSheet("font-weight: bold; color: #1976D2;")
        self.total_vente_label = QLabel("Total Vente: -")
        self.total_vente_label.setStyleSheet("font-weight: bold; color: #388E3C;")
        totaux_layout.addWidget(self.total_achat_label)
        totaux_layout.addStretch()
        totaux_layout.addWidget(self.total_vente_label)
        lignes_v.addLayout(totaux_layout)
        
        tabs.addTab(lignes_w, "Lignes")

        paiements_w = QWidget()
        paiements_v = QVBoxLayout(paiements_w)
        self.paiements_table = QTableWidget()
        # Colonnes : Date, Montant, Mode, Réf., Compte (num - nom)
        self.paiements_table.setColumnCount(5)
        self.paiements_table.setHorizontalHeaderLabels(["Date", "Montant", "Mode", "Réf.", "Compte"])
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

    def _schedule_refresh(self):
        """Lancer le chargement des données dans un thread séparé"""
        # Arrêter le thread précédent s'il est encore actif
        if self.data_thread is not None and self.data_thread.isRunning():
            self.data_thread.quit()
            self.data_thread.wait()
        
        # Créer et configurer le worker
        etat_filter = self.etat_combo.currentData() if hasattr(self, 'etat_combo') else None
        search_text = self.search_edit.text().strip().lower() if hasattr(self, 'search_edit') else ""
        
        self.data_worker = LoadDataWorker(self.achat_controller, etat_filter, search_text)
        self.data_thread = QThread()
        self.data_worker.moveToThread(self.data_thread)
        
        # Connecter les signaux
        self.data_thread.started.connect(self.data_worker.run)
        self.data_worker.finished.connect(self._on_data_loaded)
        self.data_worker.error.connect(self._on_data_error)
        self.data_worker.finished.connect(self.data_thread.quit)
        
        # Démarrer le thread
        self.data_thread.start()

    def refresh_data(self):
        """Appel public pour rafraîchir les données (dans un thread)"""
        self._schedule_refresh()
    
    def _on_data_loaded(self, commandes, search_text, etat_filter):
        """Callback appelé quand les données sont chargées"""
        self.current_commandes = commandes
        self.populate_table()
    
    def _on_data_error(self, error_msg):
        """Callback appelé en cas d'erreur de chargement"""
        QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement: {error_msg}")

    def _do_refresh_data(self):
        """Effectuer le refresh réel en arrière-plan"""
        self._schedule_refresh()

    def populate_table(self):
        self.table.setRowCount(len(self.current_commandes))
        # Récupérer la session pour charger les utilisateurs
        session = self.achat_controller.db_manager.get_session()
        try:
            for row, commande in enumerate(self.current_commandes):
                # Colonne N° Commande
                self.table.setItem(row, 0, QTableWidgetItem(commande.numero))
                
                # Colonne Date
                date_str = commande.date_commande.strftime("%d/%m/%Y %H:%M") if commande.date_commande else ""
                self.table.setItem(row, 1, QTableWidgetItem(date_str))
                
                # Colonne Montant
                montant = QTableWidgetItem(self.entreprise_ctrl.format_amount(getattr(commande, 'montant_total', 0)))
                montant.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 2, montant)

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
                self.table.setItem(row, 3, paye_item)

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
                self.table.setItem(row, 4, statut_item)

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
                self.table.setItem(row, 5, etat_item)
                
                # Colonne 'Utilisateur' - charger l'utilisateur qui a créé la commande
                utilisateur_nom = self.get_username_by_id(session, commande.utilisateur_id)
                self.table.setItem(row, 6, QTableWidgetItem(utilisateur_nom))
        finally:
            session.close()

    def on_selection_changed(self):
        selected = self.table.selectionModel().selectedRows()
        has = len(selected) > 0
        self.edit_btn.setEnabled(has and self.current_commandes[selected[0].row()].etat == EtatCommande.ENCOURS if has else False)
        self.reception_btn.setEnabled(has and self.current_commandes[selected[0].row()].etat != EtatCommande.RECEPTIONNE if has else False)
        # Activer le bouton Payer seulement si une ligne est sélectionnée et que le montant restant > 0
        if has:
            try:
                cmd = self.current_commandes[selected[0].row()]
                try:
                    total_paye = cmd.total_paye if hasattr(cmd, 'total_paye') else (sum(d.montant for d in cmd.depenses) if cmd.depenses else Decimal('0'))
                except Exception:
                    total_paye = Decimal('0')
                montant_restant = (cmd.montant_total or Decimal('0')) - Decimal(total_paye)
                self.pay_btn.setEnabled(montant_restant > 0)
            except Exception:
                # En cas d'erreur, laisser le bouton désactivé pour sécurité
                self.pay_btn.setEnabled(False)
        else:
            self.pay_btn.setEnabled(False)
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
            # Afficher le nom de l'entrepôt au lieu de l'ID
            entrepot_nom = "Non spécifié"
            if cmd.entrepot_id:
                try:
                    from ayanna_erp.modules.stock.models import StockWarehouse
                    entrepot = session.query(StockWarehouse).filter_by(id=cmd.entrepot_id).first()
                    if entrepot:
                        entrepot_nom = entrepot.name
                except Exception:
                    entrepot_nom = str(cmd.entrepot_id)
            self.detail_entrepot.setText(entrepot_nom)
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
            
            # Afficher l'utilisateur qui a créé la commande
            utilisateur_nom = self.get_username_by_id(session, cmd.utilisateur_id)
            self.detail_utilisateur.setText(utilisateur_nom)

            # lignes avec prix d'achat et prix de vente
            self.lignes_table.setRowCount(len(cmd.lignes))
            total_achat = Decimal('0')
            total_vente = Decimal('0')
            
            for r, ligne in enumerate(cmd.lignes):
                try:
                    prod_name = ligne.product.name if ligne.product else f"Produit {ligne.produit_id}"
                    # Prix de vente du produit
                    prix_vente = Decimal(str(ligne.product.price_unit)) if ligne.product and ligne.product.price_unit else Decimal('0')
                except:
                    prod_name = f"Produit {ligne.produit_id}"
                    prix_vente = Decimal('0')
                
                # Prix d'achat (de la ligne de commande)
                prix_achat = Decimal(str(getattr(ligne, 'prix_unitaire', 0) or 0))
                quantite = Decimal(str(ligne.quantite))
                remise = Decimal(str(getattr(ligne, 'remise_ligne', 0) or 0))
                
                # Calcul des totaux
                total_ligne_achat = (quantite * prix_achat) - remise
                total_ligne_vente = quantite * prix_vente
                
                total_achat += total_ligne_achat
                total_vente += total_ligne_vente
                
                self.lignes_table.setItem(r, 0, QTableWidgetItem(prod_name))
                self.lignes_table.setItem(r, 1, QTableWidgetItem(str(ligne.quantite)))
                self.lignes_table.setItem(r, 2, QTableWidgetItem(self.entreprise_ctrl.format_amount(prix_achat)))
                self.lignes_table.setItem(r, 3, QTableWidgetItem(self.entreprise_ctrl.format_amount(prix_vente)))
                self.lignes_table.setItem(r, 4, QTableWidgetItem(self.entreprise_ctrl.format_amount(remise)))
                self.lignes_table.setItem(r, 5, QTableWidgetItem(self.entreprise_ctrl.format_amount(total_ligne_achat)))
                self.lignes_table.setItem(r, 6, QTableWidgetItem(self.entreprise_ctrl.format_amount(total_ligne_vente)))
            
            # Mettre à jour les labels de totaux
            self.total_achat_label.setText(f"Total Achat: {self.entreprise_ctrl.format_amount(total_achat)}")
            self.total_vente_label.setText(f"Total Vente: {self.entreprise_ctrl.format_amount(total_vente)}")

            # paiements
            try:
                self.paiements_table.setRowCount(len(cmd.depenses))
                for r, d in enumerate(cmd.depenses):
                    self.paiements_table.setItem(r, 0, QTableWidgetItem(d.date_paiement.strftime("%d/%m/%Y")))
                    self.paiements_table.setItem(r, 1, QTableWidgetItem(self.entreprise_ctrl.format_amount(getattr(d, 'montant', 0))))
                    self.paiements_table.setItem(r, 2, QTableWidgetItem(d.mode_paiement or "N/A"))
                    self.paiements_table.setItem(r, 3, QTableWidgetItem(d.reference or "N/A"))
                    # Afficher le compte utilisé si renseigné
                    compte_label = "-"
                    try:
                        if getattr(d, 'compte_financier_id', None):
                            compte = session.query(ComptaComptes).get(d.compte_financier_id)
                            if compte:
                                compte_label = f"{compte.numero} - {getattr(compte, 'intitule', None) or getattr(compte, 'name', '')}"
                    except Exception:
                        compte_label = "-"
                    self.paiements_table.setItem(r, 4, QTableWidgetItem(compte_label))
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
        self.detail_utilisateur.setText("-")
        self.lignes_table.setRowCount(0)
        self.paiements_table.setRowCount(0)

    def select_commande(self, commande_id):
        for r in range(self.table.rowCount()):
            if self.table.item(r, 0) and self.table.item(r, 0).text() == str(commande_id):
                self.table.selectRow(r)
                break

    def edit_selected_commande(self):
        sel = self.table.selectionModel().selectedRows()
        if sel:
            cmd = self.current_commandes[sel[0].row()]
            self.edit_commande(cmd.id)

    def edit_commande(self, commande_id):
        session = None
        try:
            session = self.achat_controller.db_manager.get_session()
            cmd = session.query(AchatCommande).filter_by(id=commande_id).first()
            if not cmd:
                QMessageBox.warning(self, "Erreur", "Commande introuvable")
                return
            dialog = EditCommandeDialog(self, self.achat_controller, cmd)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                try:
                    # Récupérer les lignes modifiées depuis le dialogue
                    lignes = dialog.get_lignes_data()
                    # Appeler le contrôleur pour mettre à jour la commande
                    updated = self.achat_controller.update_commande(session, commande_id, lignes)
                    QMessageBox.information(self, "Succès", f"Commande {getattr(updated, 'numero', commande_id)} mise à jour")
                except Exception as e:
                    QMessageBox.critical(self, "Erreur", f"Erreur lors de la mise à jour: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur édition: {e}")
        finally:
            # Fermer la session AVANT refresh_data() pour ne pas bloquer
            if session:
                try:
                    session.close()
                except Exception:
                    pass
            # Rafraîchir après fermeture de la session  
            try:
                self.refresh_data()
            except Exception:
                pass

    def reception_selected_commande(self):
        sel = self.table.selectionModel().selectedRows()
        if sel:
            cmd = self.current_commandes[sel[0].row()]
            self.reception_commande(cmd.id)

    def reception_commande(self, commande_id):
        try:
            session = self.achat_controller.db_manager.get_session()
            cmd = session.query(AchatCommande).filter_by(id=commande_id).first()
            if not cmd:
                QMessageBox.warning(self, "Erreur", "Commande introuvable")
                session.close()
                return
            if cmd.etat == EtatCommande.RECEPTIONNE:
                QMessageBox.information(self, "Info", "Cette commande est déjà réceptionnée")
                session.close()
                return
            reply = QMessageBox.question(self, "Confirmation",
                                       f"Confirmer la réception de la commande {cmd.numero} ?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                if self.achat_controller.reception_commande(session, commande_id):
                    session.commit()
                    QMessageBox.information(self, "Succès", "Commande réceptionnée avec succès")
                    self.refresh_data()
                else:
                    QMessageBox.warning(self, "Erreur", "Échec de la réception")
            session.close()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur réception: {e}")

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
            dialog = PaiementDialog(self, cmd, montant_restant, self.achat_controller)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                montant = dialog.get_montant()
                mode = dialog.get_mode_paiement()
                ref = dialog.get_reference()
                compte_financier_id = dialog.get_compte_financier_id()

                # Vérification locale du solde du compte financier (UX) avant confirmation serveur
                try:
                    compte_a_verifier = None
                    try:
                        config = session.query(ComptaConfig).filter_by(enterprise_id=getattr(self.achat_controller, 'entreprise_id', None)).first()
                        compte_a_verifier = compte_financier_id or (config.compte_caisse_id if config and getattr(config, 'compte_caisse_id', None) else None)
                    except Exception:
                        compte_a_verifier = compte_financier_id

                    if compte_a_verifier:
                        from decimal import Decimal as _Decimal
                        ok = self.achat_controller.verify_solde_compte(session, int(compte_a_verifier), _Decimal(str(montant)))
                        if not ok:
                            # Récupérer informations du compte
                            try:
                                compte_obj = session.query(ComptaComptes).filter(ComptaComptes.id == int(compte_a_verifier)).first()
                                compte_num = getattr(compte_obj, 'numero', None) or str(compte_a_verifier)
                                compte_nom = getattr(compte_obj, 'nom', '') or ''
                            except Exception:
                                compte_num = str(compte_a_verifier)
                                compte_nom = ''

                            QMessageBox.critical(self, "Solde insuffisant", \
                                f"Paiement impossible : le compte sélectionné ({compte_num}{(' - ' + compte_nom) if compte_nom else ''}) ne dispose pas de fonds suffisants pour couvrir le montant de {self.entreprise_ctrl.format_amount(montant)}.\n\n" \
                                "Actions : approvisionner le compte, sélectionner un autre compte financier, ou contacter l'administrateur.")
                            session.close()
                            return

                    # Appel serveur pour effectuer le paiement (vérification côté serveur restera active)
                    try:
                        success = self.achat_controller.process_paiement_commande(session, commande_id, montant, mode, ref, compte_financier_id=compte_financier_id)
                        if success:
                            QMessageBox.information(self, "Succès", f"Paiement de {self.entreprise_ctrl.format_amount(montant)} enregistré")
                            self.refresh_data()
                    except Exception as e:
                        QMessageBox.critical(self, "Erreur", f"Erreur paiement: {e}")
                except Exception as e:
                    QMessageBox.critical(self, "Erreur", f"Erreur lors de la vérification du compte: {e}")
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
            session = None
            try:
                session = self.achat_controller.db_manager.get_session()
                self.achat_controller.annuler_commande(session, commande_id)
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur annulation: {e}")
            finally:
                if session:
                    try:
                        session.close()
                    except Exception:
                        pass

    def export_pdf_selected_commande(self):
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            QMessageBox.warning(self, "Attention", "Sélectionnez une commande")
            return
        cmd = self.current_commandes[sel[0].row()]
        self.export_commande_to_pdf(cmd.id)

    def export_commande_to_pdf(self, commande_id):
        session = None
        try:
            session = self.achat_controller.db_manager.get_session()
            cmd = session.query(AchatCommande).filter_by(id=commande_id).first()
            if not cmd:
                QMessageBox.warning(self, "Erreur", "Commande introuvable")
                return

            # Export forcé en ticket 80mm uniquement
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            format_suffix = "80mm"
            file_name = f"Commande_{cmd.numero}_{format_suffix}_{timestamp}.pdf"
            file_path = os.path.join(tempfile.gettempdir(), file_name)

            self.generate_commande_pdf_80mm(cmd, file_path, session)
            
            opened, open_err = self._open_pdf_with_default_app(file_path)
            if opened:
                QMessageBox.information(self, "Succès", f"PDF généré et ouvert: {file_path}")
            else:
                QMessageBox.information(
                    self,
                    "Succès",
                    f"PDF généré: {file_path}\nOuverture automatique impossible: {open_err}",
                )
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur export: {e}")
        finally:
            if session:
                try:
                    session.close()
                except Exception:
                    pass

    def _open_pdf_with_default_app(self, file_path):
        """Ouvrir un PDF avec l'application par défaut du système."""
        try:
            if os.name == 'nt':
                os.startfile(file_path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', file_path], check=True)
            else:
                subprocess.run(['xdg-open', file_path], check=True)
            return True, None
        except Exception as e:
            return False, str(e)

    def generate_commande_pdf(self, commande, file_path, session, page_format="A4"):
        # Rendu A4/A3 harmonisé avec les factures de vente (Helvetica 10/12/16)
        temp_logo = None
        try:
            from reportlab.lib.pagesizes import A4, A3
            from reportlab.lib.units import mm
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
            from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController

            ent_ctrl = EntrepriseController()
            comp = ent_ctrl.get_company_info_for_pdf() or {}

            logo_path = None
            if comp.get('logo'):
                try:
                    fd, temp_logo = tempfile.mkstemp(suffix='.png')
                    with os.fdopen(fd, 'wb') as f:
                        f.write(comp.get('logo'))
                    logo_path = temp_logo
                except Exception:
                    logo_path = None

            from ayanna_erp.modules.stock.models import StockWarehouse
            entrepot = session.query(StockWarehouse).filter_by(id=commande.entrepot_id).first()
            entrepot_nom = entrepot.name if entrepot else 'Entrepôt inconnu'

            try:
                total_paye = commande.total_paye if hasattr(commande, 'total_paye') else (
                    sum(d.montant for d in commande.depenses) if commande.depenses else Decimal('0')
                )
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

            pagesize = A3 if page_format == "A3" else A4
            doc = SimpleDocTemplate(
                file_path,
                pagesize=pagesize,
                rightMargin=15 * mm,
                leftMargin=15 * mm,
                topMargin=15 * mm,
                bottomMargin=20 * mm,
            )

            styles = getSampleStyleSheet()
            normal = styles['Normal']
            normal.fontName = 'Helvetica'
            normal.fontSize = 10
            heading = ParagraphStyle(
                'HeadingCommande',
                parent=styles['Heading1'],
                fontName='Helvetica-Bold',
                fontSize=16,
                leading=20,
            )
            subheading = ParagraphStyle(
                'SubHeadingCommande',
                parent=styles['Heading2'],
                fontName='Helvetica-Bold',
                fontSize=12,
                leading=14,
            )
            small = ParagraphStyle('SmallCommande', parent=styles['Normal'], fontSize=9, fontName='Helvetica')

            flow = []

            header_left = None
            if logo_path:
                try:
                    header_left = Image(logo_path, width=40 * mm, height=40 * mm)
                except Exception:
                    header_left = Paragraph(f"<b>{comp.get('name', '')}</b>", heading)
            else:
                header_left = Paragraph(f"<b>{comp.get('name', '')}</b>", heading)

            company_info = (
                f"<b>{comp.get('name', '')}</b><br/>"
                f"{comp.get('address', '')}<br/>"
                f"Tel: {comp.get('phone', '')}<br/>"
                f"{comp.get('email', '')}"
            )
            header_right = Paragraph(company_info, normal)
            header_table = Table([[header_left, header_right]], colWidths=[50 * mm, None])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ]))
            flow.append(header_table)
            flow.append(Spacer(1, 8))

            flow.append(Paragraph("BON DE COMMANDE D'ACHAT", heading))
            flow.append(Spacer(1, 6))

            meta_data = [
                ['N° commande', commande.numero],
                ['Fournisseur', commande.fournisseur.nom if commande.fournisseur else ''],
                ['Entrepôt', entrepot_nom],
                ['Date', commande.date_commande.strftime('%d/%m/%Y %H:%M')],
                ['Utilisateur', self.get_username_by_id(session, commande.utilisateur_id)],
                ['État', commande.etat.value.title()],
                ['Statut paiement', str(statut).replace('_', ' ').title()],
                ['Montant payé', ent_ctrl.format_amount(total_paye)],
            ]
            meta_table = Table(meta_data, colWidths=[55 * mm, None])
            meta_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            flow.append(meta_table)
            flow.append(Spacer(1, 10))

            flow.append(Paragraph("DÉTAILS DES ARTICLES", subheading))
            flow.append(Spacer(1, 4))

            items = [['Produit', 'Qté', 'Prix Achat', 'Total Achat', 'Prix Vente', 'Total Vente', 'Remise']]
            total_achat_global = Decimal('0')
            total_vente_global = Decimal('0')
            total_remise_lignes = Decimal('0')

            for l in commande.lignes:
                try:
                    pname = l.product.name if l.product else f"Produit {l.produit_id}"
                except Exception:
                    pname = f"Produit {l.produit_id}"

                qty = Decimal(str(getattr(l, 'quantite', 0) or 0))
                prix_achat = Decimal(str(getattr(l, 'prix_unitaire', 0) or 0))
                remise_ligne = Decimal(str(getattr(l, 'remise_ligne', 0) or 0))
                prix_vente = Decimal('0')
                if getattr(l, 'product', None):
                    prix_vente = Decimal(str(
                        getattr(l.product, 'price', None)
                        or getattr(l.product, 'selling_price', None)
                        or getattr(l.product, 'price_unit', None)
                        or 0
                    ))

                total_achat = qty * prix_achat - remise_ligne
                total_vente = qty * prix_vente

                total_achat_global += total_achat
                total_vente_global += total_vente
                total_remise_lignes += remise_ligne

                items.append([
                    pname,
                    str(getattr(l, 'quantite', 0)),
                    ent_ctrl.format_amount(prix_achat),
                    ent_ctrl.format_amount(total_achat),
                    ent_ctrl.format_amount(prix_vente),
                    ent_ctrl.format_amount(total_vente),
                    ent_ctrl.format_amount(remise_ligne),
                ])

            items_table = Table(items, colWidths=[55 * mm, 15 * mm, 28 * mm, 30 * mm, 28 * mm, 30 * mm, 24 * mm])
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E9F1FB')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#C7D3E0')),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            flow.append(items_table)
            flow.append(Spacer(1, 10))

            remise_globale = Decimal(str(getattr(commande, 'remise_global', 0) or 0))
            net_a_payer = total_achat_global - remise_globale

            totals_data = [
                ['Total Achat', ent_ctrl.format_amount(total_achat_global)],
                ['Total Vente', ent_ctrl.format_amount(total_vente_global)],
                ['Remises lignes', ent_ctrl.format_amount(total_remise_lignes)],
                ['Remise globale', ent_ctrl.format_amount(remise_globale)],
                ['NET À PAYER', ent_ctrl.format_amount(net_a_payer)],
            ]
            totals_table = Table(totals_data, colWidths=[60 * mm, 45 * mm])
            totals_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -2), 'Helvetica'),
                ('FONTNAME', (1, -1), (1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -2), 10),
                ('FONTSIZE', (0, -1), (-1, -1), 11),
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#C7D3E0')),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#2ECC71')),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
            ]))
            flow.append(totals_table)

            flow.append(Spacer(1, 16))
            footer_text = f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} - Ayanna ERP"
            flow.append(Paragraph(footer_text, small))

            doc.build(flow)
        except Exception as e:
            print(f"Erreur génération PDF: {e}")
            raise
        finally:
            if temp_logo and os.path.exists(temp_logo):
                try:
                    os.unlink(temp_logo)
                except Exception:
                    pass

    def generate_commande_pdf_80mm(self, commande, file_path, session):
        """Générer un PDF au format ticket 80mm pour impression thermique"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.enums import TA_CENTER, TA_RIGHT
            from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController

            # Format ticket 80mm (largeur ~72mm utile)
            page_width = 80 * mm
            page_height = 297 * mm  # Hauteur variable, on prend une grande valeur

            ent_ctrl = EntrepriseController()
            comp = ent_ctrl.get_company_info_for_pdf()

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
            doc = SimpleDocTemplate(
                file_path, 
                pagesize=(page_width, page_height),
                rightMargin=2*mm, leftMargin=2*mm,
                topMargin=3*mm, bottomMargin=3*mm
            )

            styles = getSampleStyleSheet()
            # Styles personnalisés pour ticket
            style_title = ParagraphStyle('Title80', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, alignment=TA_CENTER, spaceAfter=2)
            style_normal = ParagraphStyle('Normal80', parent=styles['Normal'], fontName='Helvetica', fontSize=10, alignment=TA_CENTER, spaceAfter=1)
            style_small = ParagraphStyle('Small80', parent=styles['Normal'], fontName='Helvetica', fontSize=9, alignment=TA_CENTER)
            style_line = ParagraphStyle('Line80', parent=styles['Normal'], fontName='Helvetica', fontSize=9)

            flow = []

            # En-tête entreprise
            flow.append(Paragraph(f"<b>{comp.get('name', 'ENTREPRISE')}</b>", style_title))
            if comp.get('address'):
                flow.append(Paragraph(comp.get('address', ''), style_small))
            if comp.get('phone'):
                flow.append(Paragraph(f"Tél: {comp.get('phone', '')}", style_small))
            flow.append(Spacer(1, 2*mm))

            # Ligne séparatrice
            flow.append(Paragraph("=" * 40, style_normal))

            # Titre du document
            flow.append(Paragraph(f"<b>BON DE COMMANDE</b>", style_title))
            flow.append(Paragraph(f"N°: {commande.numero}", style_normal))
            flow.append(Paragraph("=" * 40, style_normal))
            flow.append(Spacer(1, 1*mm))

            # Informations commande
            utilisateur_nom = self.get_username_by_id(session, commande.utilisateur_id)
            
            info_data = [
                [Paragraph(f"<b>Fournisseur:</b>", style_line), Paragraph(commande.fournisseur.nom if commande.fournisseur else 'N/A', style_line)],
                [Paragraph(f"<b>Entrepôt:</b>", style_line), Paragraph(entrepot_nom, style_line)],
                [Paragraph(f"<b>Date:</b>", style_line), Paragraph(commande.date_commande.strftime('%d/%m/%Y %H:%M'), style_line)],
                [Paragraph(f"<b>Utilisateur:</b>", style_line), Paragraph(utilisateur_nom, style_line)],
                [Paragraph(f"<b>État:</b>", style_line), Paragraph(commande.etat.value.title(), style_line)],
            ]
            info_table = Table(info_data, colWidths=[25*mm, 47*mm])
            info_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 1),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ]))
            flow.append(info_table)
            flow.append(Spacer(1, 2*mm))

            # Ligne séparatrice
            flow.append(Paragraph("-" * 40, style_normal))

            # Lignes de commande avec tableau prix achat/vente
            flow.append(Paragraph("<b>ARTICLES</b>", style_normal))
            flow.append(Spacer(1, 1*mm))
            
            # En-tête du tableau des articles
            style_header = ParagraphStyle('Header80', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, alignment=TA_CENTER)
            
            # Créer le tableau des articles
            articles_data = [[
                Paragraph("<b>Produit</b>", style_header),
                Paragraph("<b>Qté</b>", style_header),
                Paragraph("<b>T Achat</b>", style_header),
                Paragraph("<b>T Vente</b>", style_header),
            ]]
            
            total_achat = Decimal('0')
            total_vente = Decimal('0')
            
            for ligne in commande.lignes:
                try:
                    pname = ligne.product.name if ligne.product else f"Produit {ligne.produit_id}"
                    prix_vente_unit = Decimal(str(ligne.product.price_unit)) if ligne.product and ligne.product.price_unit else Decimal('0')
                except Exception:
                    pname = f"Produit {ligne.produit_id}"
                    prix_vente_unit = Decimal('0')
                
                # Tronquer le nom si trop long
                if len(pname) > 20:
                    pname = pname[:18] + ".."
                
                qty = Decimal(str(ligne.quantite))
                prix_achat = Decimal(str(getattr(ligne, 'prix_unitaire', 0) or 0))
                remise = Decimal(str(getattr(ligne, 'remise_ligne', 0) or 0))
                
                total_ligne_achat = (qty * prix_achat) - remise
                total_ligne_vente = qty * prix_vente_unit
                
                total_achat += total_ligne_achat
                total_vente += total_ligne_vente
                
                articles_data.append([
                    Paragraph(pname, style_line),
                    Paragraph(str(ligne.quantite), style_line),
                    Paragraph(ent_ctrl.format_amount(total_ligne_achat), style_line),
                    Paragraph(ent_ctrl.format_amount(total_ligne_vente), style_line),
                ])
            
            articles_table = Table(articles_data, colWidths=[30*mm, 10*mm, 16*mm, 16*mm])
            articles_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 2),
                ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            flow.append(articles_table)
            flow.append(Spacer(1, 2*mm))

            # Ligne séparatrice
            flow.append(Paragraph("-" * 40, style_normal))

            # Totaux avec prix d'achat et prix de vente
            totals_data = [
                [Paragraph("Total Achat:", style_line), Paragraph(f"<b>{ent_ctrl.format_amount(total_achat)}</b>", style_line)],
                [Paragraph("Total Vente:", style_line), Paragraph(f"<b>{ent_ctrl.format_amount(total_vente)}</b>", style_line)],
                [Paragraph("Remise globale:", style_line), Paragraph(f"{ent_ctrl.format_amount(commande.remise_global)}", style_line)],
                [Paragraph("<b>NET À PAYER:</b>", style_line), Paragraph(f"<b>{ent_ctrl.format_amount(total_achat - commande.remise_global)}</b>", style_line)],
            ]
            totals_table = Table(totals_data, colWidths=[40*mm, 32*mm])
            totals_table.setStyle(TableStyle([
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]))
            flow.append(totals_table)

            # Statut paiement
            flow.append(Spacer(1, 2*mm))
            flow.append(Paragraph("-" * 40, style_normal))
            flow.append(Paragraph(f"Payé: {ent_ctrl.format_amount(total_paye)}", style_normal))
            flow.append(Paragraph(f"Statut: {str(statut).replace('_', ' ').title()}", style_normal))

            # Footer
            flow.append(Spacer(1, 3*mm))
            flow.append(Paragraph("=" * 40, style_normal))
            flow.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}", style_small))
            flow.append(Paragraph("Ayanna ERP", style_small))

            # Build PDF
            doc.build(flow)
        except Exception as e:
            print(f"Erreur génération PDF 80mm: {e}")
            raise