"""
Widget pour la gestion des commandes d'achat
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QComboBox, QHeaderView, QMessageBox,
    QTabWidget, QGroupBox, QFormLayout, QDateEdit, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont
from decimal import Decimal
from datetime import datetime

from ayanna_erp.modules.achats.controllers import AchatController
from ayanna_erp.modules.achats.models import AchatCommande, EtatCommande


class CommandesWidget(QWidget):
    """Widget principal pour la gestion des commandes d'achat"""
    
    commande_updated = pyqtSignal(int)
    commande_selected = pyqtSignal(int)
    
    def __init__(self, achat_controller: AchatController):
        super().__init__()
        self.achat_controller = achat_controller
        self.current_commandes = []
        
        self.setup_ui()
        self.refresh_data()
    
    def setup_ui(self):
        """Configuration de l'interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # En-tête avec filtres
        header_layout = QHBoxLayout()
        
        title_label = QLabel("📋 Gestion des Commandes")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2C3E50;")
        
        # Filtres
        filter_group = QGroupBox("Filtres")
        filter_layout = QHBoxLayout(filter_group)
        
        # Filtre par état
        filter_layout.addWidget(QLabel("État:"))
        self.etat_combo = QComboBox()
        self.etat_combo.addItem("Tous", None)
        self.etat_combo.addItem("En cours", EtatCommande.ENCOURS)
        self.etat_combo.addItem("Validé", EtatCommande.VALIDE)
        self.etat_combo.addItem("Annulé", EtatCommande.ANNULE)
        self.etat_combo.currentTextChanged.connect(self.refresh_data)
        filter_layout.addWidget(self.etat_combo)
        
        # Recherche
        filter_layout.addWidget(QLabel("Recherche:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Numéro de commande, fournisseur...")
        self.search_edit.textChanged.connect(self.refresh_data)
        filter_layout.addWidget(self.search_edit)
        
        filter_layout.addStretch()
        
        # Bouton actualiser
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.clicked.connect(self.refresh_data)
        filter_layout.addWidget(refresh_btn)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(filter_group)
        
        layout.addLayout(header_layout)
        
        # Table des commandes
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Numéro", "Fournisseur", "Date", "Montant", "État", "Entrepôt", "Actions"
        ])
        
        # Configuration de la table
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        
        layout.addWidget(self.table)
        
        # Détails de la commande sélectionnée
        self.details_widget = self.create_details_widget()
        layout.addWidget(self.details_widget)
    
    def create_details_widget(self):
        """Crée le widget des détails de commande"""
        details_group = QGroupBox("Détails de la commande")
        details_group.setMaximumHeight(200)
        
        # Utiliser un TabWidget pour organiser les détails
        tab_widget = QTabWidget()
        
        # Onglet informations générales
        info_widget = QWidget()
        info_layout = QFormLayout(info_widget)
        
        self.detail_numero = QLabel("-")
        self.detail_fournisseur = QLabel("-")
        self.detail_date = QLabel("-")
        self.detail_montant = QLabel("-")
        self.detail_etat = QLabel("-")
        
        info_layout.addRow("Numéro:", self.detail_numero)
        info_layout.addRow("Fournisseur:", self.detail_fournisseur)
        info_layout.addRow("Date:", self.detail_date)
        info_layout.addRow("Montant total:", self.detail_montant)
        info_layout.addRow("État:", self.detail_etat)
        
        tab_widget.addTab(info_widget, "Informations")
        
        # Onglet lignes de commande
        lignes_widget = QWidget()
        lignes_layout = QVBoxLayout(lignes_widget)
        
        self.lignes_table = QTableWidget()
        self.lignes_table.setColumnCount(5)
        self.lignes_table.setHorizontalHeaderLabels([
            "Produit", "Quantité", "Prix unitaire", "Remise", "Total"
        ])
        self.lignes_table.setMaximumHeight(120)
        
        lignes_layout.addWidget(self.lignes_table)
        tab_widget.addTab(lignes_widget, "Lignes")
        
        # Onglet paiements
        paiements_widget = QWidget()
        paiements_layout = QVBoxLayout(paiements_widget)
        
        self.paiements_table = QTableWidget()
        self.paiements_table.setColumnCount(4)
        self.paiements_table.setHorizontalHeaderLabels([
            "Date", "Montant", "Compte", "Référence"
        ])
        self.paiements_table.setMaximumHeight(120)
        
        paiements_layout.addWidget(self.paiements_table)
        tab_widget.addTab(paiements_widget, "Paiements")
        
        # Layout principal du groupe
        main_layout = QVBoxLayout(details_group)
        
        # Boutons d'action pour la commande sélectionnée
        actions_layout = QHBoxLayout()
        
        self.pay_btn = QPushButton("💰 Payer")
        self.pay_btn.clicked.connect(self.pay_selected_commande)
        self.pay_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("❌ Annuler")
        self.cancel_btn.clicked.connect(self.cancel_selected_commande)
        self.cancel_btn.setEnabled(False)
        
        self.print_btn = QPushButton("🖨️ Imprimer")
        self.print_btn.clicked.connect(self.print_selected_commande)
        self.print_btn.setEnabled(False)
        
        actions_layout.addWidget(self.pay_btn)
        actions_layout.addWidget(self.cancel_btn)
        actions_layout.addWidget(self.print_btn)
        actions_layout.addStretch()
        
        main_layout.addLayout(actions_layout)
        main_layout.addWidget(tab_widget)
        
        return details_group
    
    def refresh_data(self):
        """Actualise la liste des commandes"""
        try:
            session = self.achat_controller.db_manager.get_session()
            
            # Récupérer l'état sélectionné
            etat_filter = self.etat_combo.currentData() if hasattr(self, 'etat_combo') else None
            
            self.current_commandes = self.achat_controller.get_commandes(
                session, 
                etat=etat_filter,
                limit=200
            )
            
            # Filtrer par recherche si nécessaire
            search_text = self.search_edit.text().lower() if hasattr(self, 'search_edit') else ""
            if search_text:
                self.current_commandes = [
                    cmd for cmd in self.current_commandes 
                    if search_text in cmd.numero.lower() or 
                       (cmd.fournisseur and search_text in cmd.fournisseur.nom.lower())
                ]
            
            self.populate_table()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement: {str(e)}")
        finally:
            session.close()
    
    def populate_table(self):
        """Remplit la table avec les données des commandes"""
        self.table.setRowCount(len(self.current_commandes))
        
        for row, commande in enumerate(self.current_commandes):
            # ID
            self.table.setItem(row, 0, QTableWidgetItem(str(commande.id)))
            
            # Numéro
            self.table.setItem(row, 1, QTableWidgetItem(commande.numero))
            
            # Fournisseur
            fournisseur_nom = commande.fournisseur.nom if commande.fournisseur else "Aucun"
            self.table.setItem(row, 2, QTableWidgetItem(fournisseur_nom))
            
            # Date
            date_str = commande.date_commande.strftime("%d/%m/%Y %H:%M") if commande.date_commande else ""
            self.table.setItem(row, 3, QTableWidgetItem(date_str))
            
            # Montant
            montant_str = f"{commande.montant_total:.2f} €"
            item = QTableWidgetItem(montant_str)
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 4, item)
            
            # État
            etat_item = QTableWidgetItem(commande.etat.value.title())
            if commande.etat == EtatCommande.ENCOURS:
                etat_item.setBackground(Qt.GlobalColor.yellow)
            elif commande.etat == EtatCommande.VALIDE:
                etat_item.setBackground(Qt.GlobalColor.green)
            elif commande.etat == EtatCommande.ANNULE:
                etat_item.setBackground(Qt.GlobalColor.red)
            self.table.setItem(row, 5, etat_item)
            
            # Entrepôt (à implémenter si nécessaire)
            self.table.setItem(row, 6, QTableWidgetItem("Entrepôt"))
            
            # Actions
            actions_widget = self.create_actions_widget(commande)
            self.table.setCellWidget(row, 7, actions_widget)
    
    def create_actions_widget(self, commande):
        """Crée le widget des actions pour une commande"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        
        if commande.etat == EtatCommande.ENCOURS:
            pay_btn = QPushButton("💰")
            pay_btn.setToolTip("Payer la commande")
            pay_btn.clicked.connect(lambda: self.pay_commande(commande.id))
            layout.addWidget(pay_btn)
            
            cancel_btn = QPushButton("❌")
            cancel_btn.setToolTip("Annuler la commande")
            cancel_btn.clicked.connect(lambda: self.cancel_commande(commande.id))
            layout.addWidget(cancel_btn)
        
        view_btn = QPushButton("👁️")
        view_btn.setToolTip("Voir les détails")
        view_btn.clicked.connect(lambda: self.select_commande(commande.id))
        layout.addWidget(view_btn)
        
        return widget
    
    def on_selection_changed(self):
        """Gestion de la sélection dans la table"""
        selected_rows = self.table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        
        self.pay_btn.setEnabled(has_selection)
        self.cancel_btn.setEnabled(has_selection)
        self.print_btn.setEnabled(has_selection)
        
        if has_selection:
            row = selected_rows[0].row()
            commande = self.current_commandes[row]
            self.show_commande_details(commande)
            self.commande_selected.emit(commande.id)
        else:
            self.clear_details()
    
    def show_commande_details(self, commande: AchatCommande):
        """Affiche les détails d'une commande"""
        # Informations générales
        self.detail_numero.setText(commande.numero)
        self.detail_fournisseur.setText(commande.fournisseur.nom if commande.fournisseur else "Aucun")
        self.detail_date.setText(commande.date_commande.strftime("%d/%m/%Y %H:%M"))
        self.detail_montant.setText(f"{commande.montant_total:.2f} €")
        self.detail_etat.setText(commande.etat.value.title())
        
        # Lignes de commande
        self.lignes_table.setRowCount(len(commande.lignes))
        for row, ligne in enumerate(commande.lignes):
            self.lignes_table.setItem(row, 0, QTableWidgetItem(f"Produit {ligne.produit_id}"))
            self.lignes_table.setItem(row, 1, QTableWidgetItem(str(ligne.quantite)))
            self.lignes_table.setItem(row, 2, QTableWidgetItem(f"{ligne.prix_unitaire:.2f} €"))
            self.lignes_table.setItem(row, 3, QTableWidgetItem(f"{ligne.remise_ligne:.2f} €"))
            self.lignes_table.setItem(row, 4, QTableWidgetItem(f"{ligne.total_ligne:.2f} €"))
        
        # Paiements
        self.paiements_table.setRowCount(len(commande.depenses))
        for row, depense in enumerate(commande.depenses):
            self.paiements_table.setItem(row, 0, QTableWidgetItem(depense.date_paiement.strftime("%d/%m/%Y")))
            self.paiements_table.setItem(row, 1, QTableWidgetItem(f"{depense.montant:.2f} €"))
            self.paiements_table.setItem(row, 2, QTableWidgetItem(f"Compte {depense.compte_id}"))
            self.paiements_table.setItem(row, 3, QTableWidgetItem(depense.reference or ""))
    
    def clear_details(self):
        """Efface les détails affichés"""
        self.detail_numero.setText("-")
        self.detail_fournisseur.setText("-")
        self.detail_date.setText("-")
        self.detail_montant.setText("-")
        self.detail_etat.setText("-")
        
        self.lignes_table.setRowCount(0)
        self.paiements_table.setRowCount(0)
    
    def select_commande(self, commande_id):
        """Sélectionne une commande dans la table"""
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == str(commande_id):
                self.table.selectRow(row)
                break
    
    def pay_selected_commande(self):
        """Paye la commande sélectionnée"""
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            commande = self.current_commandes[row]
            self.pay_commande(commande.id)
    
    def pay_commande(self, commande_id):
        """Paye une commande"""
        # TODO: Implémenter le dialog de paiement
        QMessageBox.information(self, "Paiement", f"Paiement de la commande {commande_id} à implémenter")
    
    def cancel_selected_commande(self):
        """Annule la commande sélectionnée"""
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            commande = self.current_commandes[row]
            self.cancel_commande(commande.id)
    
    def cancel_commande(self, commande_id):
        """Annule une commande"""
        reply = QMessageBox.question(
            self,
            "Confirmer l'annulation",
            "Êtes-vous sûr de vouloir annuler cette commande ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                session = self.achat_controller.db_manager.get_session()
                self.achat_controller.annuler_commande(session, commande_id)
                self.refresh_data()
                self.commande_updated.emit(commande_id)
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'annulation: {str(e)}")
            finally:
                session.close()
    
    def print_selected_commande(self):
        """Imprime la commande sélectionnée"""
        # TODO: Implémenter l'impression
        QMessageBox.information(self, "Impression", "Impression à implémenter")