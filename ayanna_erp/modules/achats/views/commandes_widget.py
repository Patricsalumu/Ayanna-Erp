"""
Widget pour la gestion des commandes d'achat
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QComboBox, QHeaderView, QMessageBox,
    QTabWidget, QGroupBox, QFormLayout, QDateEdit, QTextEdit, QDialog, 
    QDialogButtonBox, QDoubleSpinBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont
from decimal import Decimal
from datetime import datetime

from ayanna_erp.modules.achats.controllers import AchatController
from ayanna_erp.modules.achats.models import AchatCommande, EtatCommande


class PaiementDialog(QDialog):
    """Dialog pour saisir un paiement"""
    
    def __init__(self, parent=None, commande=None, montant_restant=0):
        super().__init__(parent)
        self.commande = commande
        self.montant_restant = montant_restant
        self.setWindowTitle(f"Paiement - Commande {commande.numero}")
        self.setFixedSize(400, 300)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Informations commande
        info_group = QGroupBox("Informations de la commande")
        info_layout = QFormLayout(info_group)
        
        info_layout.addRow("N° Commande:", QLabel(self.commande.numero))
        info_layout.addRow("Fournisseur:", QLabel(self.commande.fournisseur.nom if self.commande.fournisseur else "N/A"))
        info_layout.addRow("Montant total:", QLabel(f"{self.commande.montant_total:.2f} €"))
        info_layout.addRow("Montant restant:", QLabel(f"{self.montant_restant:.2f} €"))
        
        layout.addWidget(info_group)
        
        # Saisie paiement
        paiement_group = QGroupBox("Nouveau paiement")
        paiement_layout = QFormLayout(paiement_group)
        
        # Montant
        self.montant_spinbox = QDoubleSpinBox()
        self.montant_spinbox.setRange(0.01, float(self.montant_restant))
        self.montant_spinbox.setDecimals(2)
        self.montant_spinbox.setValue(float(self.montant_restant))
        self.montant_spinbox.setSuffix(" €")
        paiement_layout.addRow("Montant*:", self.montant_spinbox)
        
        # Mode de paiement
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Espèces", "Chèque", "Virement", "Carte bancaire", "Mobile Money", "Autre"
        ])
        paiement_layout.addRow("Mode de paiement*:", self.mode_combo)
        
        # Référence
        self.reference_edit = QLineEdit()
        self.reference_edit.setPlaceholderText("Numéro de chèque, référence virement, etc.")
        paiement_layout.addRow("Référence:", self.reference_edit)
        
        # Commentaire
        self.commentaire_edit = QTextEdit()
        self.commentaire_edit.setMaximumHeight(60)
        self.commentaire_edit.setPlaceholderText("Commentaire optionnel")
        paiement_layout.addRow("Commentaire:", self.commentaire_edit)
        
        layout.addWidget(paiement_group)
        
        # Boutons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_montant(self):
        return Decimal(str(self.montant_spinbox.value()))
    
    def get_mode_paiement(self):
        return self.mode_combo.currentText()
    
    def get_reference(self):
        return self.reference_edit.text().strip()
    
    def get_commentaire(self):
        return self.commentaire_edit.toPlainText().strip()


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
        self.detail_entrepot = QLabel("-")
        self.detail_date = QLabel("-")
        self.detail_montant = QLabel("-")
        self.detail_etat = QLabel("-")
        
        info_layout.addRow("Numéro:", self.detail_numero)
        info_layout.addRow("Fournisseur:", self.detail_fournisseur)
        info_layout.addRow("Entrepôt destination:", self.detail_entrepot)
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
        
        self.print_btn = QPushButton("� Export PDF")
        self.print_btn.clicked.connect(self.export_pdf_selected_commande)
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
        try:
            # Recharger la commande avec ses relations dans une nouvelle session
            session = self.achat_controller.db_manager.get_session()
            commande_complete = session.query(AchatCommande).filter_by(id=commande.id).first()
            
            if not commande_complete:
                self.clear_details()
                session.close()
                return
            
            # Informations générales
            self.detail_numero.setText(commande_complete.numero)
            self.detail_fournisseur.setText(commande_complete.fournisseur.nom if commande_complete.fournisseur else "Aucun")
            
            # Affichage de l'entrepôt
            if commande_complete.entrepot_id:
                from ayanna_erp.modules.stock.models import StockWarehouse
                entrepot = session.query(StockWarehouse).filter_by(id=commande_complete.entrepot_id).first()
                entrepot_text = f"{entrepot.name} ({entrepot.code})" if entrepot else f"Entrepôt ID {commande_complete.entrepot_id}"
                self.detail_entrepot.setText(entrepot_text)
            else:
                self.detail_entrepot.setText("Non spécifié")
                
            self.detail_date.setText(commande_complete.date_commande.strftime("%d/%m/%Y %H:%M"))
            self.detail_montant.setText(f"{commande_complete.montant_total:.2f} €")
            self.detail_etat.setText(commande_complete.etat.value.title())
            
            # Lignes de commande
            self.lignes_table.setRowCount(len(commande_complete.lignes))
            for row, ligne in enumerate(commande_complete.lignes):
                # Récupérer le nom du produit
                try:
                    product_name = ligne.product.name if ligne.product else f"Produit {ligne.produit_id}"
                except:
                    # Si la relation product n'est pas disponible, charger le produit manuellement
                    from ayanna_erp.modules.core.models import CoreProduct
                    product = session.query(CoreProduct).filter_by(id=ligne.produit_id).first()
                    product_name = product.name if product else f"Produit {ligne.produit_id}"
                
                self.lignes_table.setItem(row, 0, QTableWidgetItem(product_name))
                self.lignes_table.setItem(row, 1, QTableWidgetItem(str(ligne.quantite)))
                self.lignes_table.setItem(row, 2, QTableWidgetItem(f"{ligne.prix_unitaire:.2f} €"))
                self.lignes_table.setItem(row, 3, QTableWidgetItem(f"{ligne.remise_ligne:.2f} €"))
                self.lignes_table.setItem(row, 4, QTableWidgetItem(f"{ligne.total_ligne:.2f} €"))
            
            # Paiements - Gestion d'erreur pour la migration
            try:
                self.paiements_table.setRowCount(len(commande_complete.depenses))
                for row, depense in enumerate(commande_complete.depenses):
                    self.paiements_table.setItem(row, 0, QTableWidgetItem(depense.date_paiement.strftime("%d/%m/%Y")))
                    self.paiements_table.setItem(row, 1, QTableWidgetItem(f"{depense.montant:.2f} €"))
                    self.paiements_table.setItem(row, 2, QTableWidgetItem(getattr(depense, 'mode_paiement', 'N/A') or "N/A"))
                    self.paiements_table.setItem(row, 3, QTableWidgetItem(depense.reference or "N/A"))
            except Exception as e:
                print(f"Erreur chargement paiements: {e}")
                self.paiements_table.setRowCount(0)
            
            session.close()
            
        except Exception as e:
            print(f"Erreur lors de l'affichage des détails de commande: {e}")
            self.clear_details()
    
    def clear_details(self):
        """Efface les détails affichés"""
        self.detail_numero.setText("-")
        self.detail_fournisseur.setText("-")
        self.detail_entrepot.setText("-")
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
        try:
            # Récupérer la commande
            session = self.achat_controller.db_manager.get_session()
            commande = session.query(AchatCommande).filter_by(id=commande_id).first()
            
            if not commande:
                QMessageBox.warning(self, "Erreur", "Commande introuvable")
                session.close()
                return
            
            if commande.etat == EtatCommande.VALIDE:
                QMessageBox.warning(self, "Erreur", "Cette commande est déjà payée et validée")
                session.close()
                return
            
            if commande.etat == EtatCommande.ANNULE:
                QMessageBox.warning(self, "Erreur", "Impossible de payer une commande annulée")
                session.close()
                return
            
            # Calculer le montant restant à payer
            try:
                montant_paye = sum(d.montant for d in commande.depenses)
            except Exception as e:
                print(f"Erreur calcul paiements existants: {e}")
                montant_paye = Decimal('0')
                
            montant_restant = commande.montant_total - montant_paye
            
            if montant_restant <= 0:
                QMessageBox.information(self, "Information", "Cette commande est déjà entièrement payée")
                session.close()
                return
            
            # Dialog de paiement
            dialog = PaiementDialog(self, commande, montant_restant)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Traiter le paiement
                montant_paiement = dialog.get_montant()
                mode_paiement = dialog.get_mode_paiement()
                reference = dialog.get_reference()
                
                # Appeler le contrôleur pour traiter le paiement
                try:
                    success = self.achat_controller.process_paiement_commande(
                        session, commande_id, montant_paiement, mode_paiement, reference
                    )
                    
                    if success:
                        QMessageBox.information(self, "Succès", f"Paiement de {montant_paiement:.2f} € enregistré avec succès")
                        # Actualiser l'affichage
                        self.refresh_data()
                        # Si il y a encore une sélection, actualiser les détails
                        selected_rows = self.table.selectionModel().selectedRows()
                        if selected_rows:
                            row = selected_rows[0].row()
                            commande_updated = self.current_commandes[row]
                            self.show_commande_details(commande_updated)
                    else:
                        QMessageBox.critical(self, "Erreur", "Erreur lors de l'enregistrement du paiement")
                        
                except Exception as e:
                    QMessageBox.critical(self, "Erreur", f"Erreur lors du paiement: {str(e)}")
                    print(f"Erreur paiement détaillée: {e}")
            
            session.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du paiement: {e}")
            print(f"Erreur paiement: {e}")
    
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
    
    def export_pdf_selected_commande(self):
        """Exporte la commande sélectionnée en PDF"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une commande à exporter")
            return
        
        row = selected_rows[0].row()
        commande = self.current_commandes[row]
        self.export_commande_to_pdf(commande.id)
    
    def export_commande_to_pdf(self, commande_id):
        """Exporte une commande en PDF"""
        try:
            # Récupérer la commande complète
            session = self.achat_controller.db_manager.get_session()
            commande = session.query(AchatCommande).filter_by(id=commande_id).first()
            
            if not commande:
                QMessageBox.warning(self, "Erreur", "Commande introuvable")
                session.close()
                return
            
            # Dialog pour choisir l'emplacement du fichier
            file_name = f"Commande_{commande.numero}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Enregistrer la commande en PDF",
                file_name,
                "Fichiers PDF (*.pdf)"
            )
            
            if not file_path:
                session.close()
                return
            
            # Générer le PDF
            self.generate_commande_pdf(commande, file_path, session)
            QMessageBox.information(self, "Succès", f"Commande exportée avec succès vers:\n{file_path}")
            
            session.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export PDF: {e}")
            print(f"Erreur export PDF: {e}")
    
    def generate_commande_pdf(self, commande, file_path, session):
        """Génère le fichier PDF pour la commande"""
        from PyQt6.QtGui import QTextDocument
        from PyQt6.QtPrintSupport import QPrinter
        
        # Récupérer l'entrepôt
        from ayanna_erp.modules.stock.models import StockWarehouse
        entrepot = session.query(StockWarehouse).filter_by(id=commande.entrepot_id).first()
        entrepot_nom = entrepot.name if entrepot else "Entrepôt inconnu"
        
        # Créer le document HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 30px; 
                    line-height: 1.4;
                    color: #333;
                }}
                .header {{ 
                    text-align: center; 
                    margin-bottom: 40px; 
                    border-bottom: 3px solid #2c3e50;
                    padding-bottom: 20px;
                }}
                .title {{ 
                    font-size: 28px; 
                    font-weight: bold; 
                    color: #2c3e50; 
                    margin-bottom: 10px;
                }}
                .subtitle {{ 
                    font-size: 18px; 
                    color: #7f8c8d; 
                    margin-top: 10px; 
                }}
                .info-section {{ 
                    margin-bottom: 30px; 
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 5px;
                }}
                .info-table {{ 
                    width: 100%; 
                    border-collapse: collapse;
                }}
                .info-table td {{ 
                    padding: 10px; 
                    border-bottom: 1px solid #dee2e6; 
                }}
                .info-label {{ 
                    font-weight: bold; 
                    width: 180px; 
                    color: #495057;
                }}
                .lines-section {{ 
                    margin-bottom: 30px; 
                }}
                .lines-table {{ 
                    width: 100%; 
                    border-collapse: collapse; 
                    margin-top: 15px;
                }}
                .lines-table th, .lines-table td {{ 
                    border: 1px solid #dee2e6; 
                    padding: 12px; 
                    text-align: left; 
                }}
                .lines-table th {{ 
                    background-color: #e9ecef; 
                    font-weight: bold; 
                    color: #495057;
                }}
                .lines-table tr:nth-child(even) {{
                    background-color: #f8f9fa;
                }}
                .total-section {{ 
                    margin-top: 30px; 
                    text-align: right; 
                    background-color: #e8f5e8;
                    padding: 20px;
                    border-radius: 5px;
                }}
                .total-amount {{ 
                    font-size: 22px; 
                    font-weight: bold; 
                    color: #27ae60; 
                }}
                .footer {{ 
                    margin-top: 50px; 
                    text-align: center; 
                    font-size: 12px; 
                    color: #6c757d; 
                    border-top: 1px solid #dee2e6;
                    padding-top: 20px;
                }}
                .section-title {{
                    font-size: 18px;
                    font-weight: bold;
                    color: #2c3e50;
                    margin-bottom: 15px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="title">BON DE COMMANDE</div>
                <div class="subtitle">N° {commande.numero}</div>
            </div>
            
            <div class="info-section">
                <div class="section-title">Informations de la commande</div>
                <table class="info-table">
                    <tr>
                        <td class="info-label">Fournisseur:</td>
                        <td>{commande.fournisseur.nom if commande.fournisseur else 'Non spécifié'}</td>
                    </tr>
                    <tr>
                        <td class="info-label">Date de commande:</td>
                        <td>{commande.date_commande.strftime('%d/%m/%Y à %H:%M')}</td>
                    </tr>
                    <tr>
                        <td class="info-label">Entrepôt de destination:</td>
                        <td>{entrepot_nom}</td>
                    </tr>
                    <tr>
                        <td class="info-label">État:</td>
                        <td>{commande.etat.value.title()}</td>
                    </tr>
                </table>
            </div>
            
            <div class="lines-section">
                <div class="section-title">Détail des produits commandés</div>
                <table class="lines-table">
                    <thead>
                        <tr>
                            <th>Produit</th>
                            <th>Quantité</th>
                            <th>Prix unitaire</th>
                            <th>Remise</th>
                            <th>Total ligne</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # Ajouter les lignes de commande
        for ligne in commande.lignes:
            # Récupérer le nom du produit
            try:
                product_name = ligne.product.name if ligne.product else f"Produit {ligne.produit_id}"
            except:
                from ayanna_erp.modules.core.models import CoreProduct
                product = session.query(CoreProduct).filter_by(id=ligne.produit_id).first()
                product_name = product.name if product else f"Produit {ligne.produit_id}"
            
            html_content += f"""
                        <tr>
                            <td>{product_name}</td>
                            <td>{ligne.quantite}</td>
                            <td>{ligne.prix_unitaire:.2f} €</td>
                            <td>{ligne.remise_ligne:.2f} €</td>
                            <td>{ligne.total_ligne:.2f} €</td>
                        </tr>
            """
        
        html_content += f"""
                    </tbody>
                </table>
            </div>
            
            <div class="total-section">
                <div class="total-amount">MONTANT TOTAL: {commande.montant_total:.2f} €</div>
            </div>
            
            <div class="footer">
                Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} par Ayanna ERP
            </div>
        </body>
        </html>
        """
        
        # Créer le document et l'exporter en PDF
        document = QTextDocument()
        document.setHtml(html_content)
        
        # Configuration de l'imprimante pour PDF
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(file_path)
        
        # Imprimer vers le PDF
        document.print(printer)