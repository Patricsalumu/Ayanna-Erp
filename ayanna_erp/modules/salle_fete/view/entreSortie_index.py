"""
Journal de Caisse - Module Salle de Fête
Gestion des entrées et sorties d'argent avec journal journalier
"""

import sys
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QTableWidget, QTableWidgetItem, 
                            QPushButton, QLineEdit, QLabel, QComboBox, 
                            QSpinBox, QDoubleSpinBox, QTextEdit, QMessageBox,
                            QGroupBox, QGridLayout, QListWidget, QSplitter,
                            QFrame, QScrollArea, QFormLayout, QCheckBox,
                            QDateTimeEdit, QHeaderView, QDateEdit, QDialog, QInputDialog)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDateTime, QDate
from PyQt6.QtGui import QFont, QPixmap, QIcon, QAction
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from decimal import Decimal
from datetime import datetime, timedelta, date
import json

# Import des contrôleurs
from ..controller.entre_sortie_controller import EntreSortieController
from ..controller.paiement_controller import PaiementController
from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
from ayanna_erp.utils.formatting import format_amount_for_pdf
from ayanna_erp.modules.boutique.model.models import ShopPayment, ShopPanier, ShopClient
from ayanna_erp.modules.restaurant.models.restaurant import RestauPanier, RestauPayment, RestauProduitPanier
from ayanna_erp.modules.achats.models.achats_models import AchatDepense


class DepenseDialog(QDialog):
    """Dialog pour enregistrer une dépense"""
    
    def __init__(self, parent=None, current_user=None):
        super().__init__(parent)
        self.setWindowTitle("Enregistrer une dépense")
        self.setModal(True)
        self.resize(450, 400)
        self.current_user = current_user
        self.comptes_charges = []
        
        # Initialiser le contrôleur entreprise pour les devises
        self.entreprise_controller = EntrepriseController()
        
        self.setup_ui()
        self.load_comptes_charges()
    
    def get_currency_symbol(self):
        """Récupère le symbole de devise depuis l'entreprise"""
        try:
            return self.entreprise_controller.get_currency_symbol()
        except:
            return "€"  # Fallback
    
    def format_amount(self, amount):
        """Formate un montant avec la devise de l'entreprise"""
        try:
            return self.entreprise_controller.format_amount(amount)
        except:
            try:
                cur = self.get_currency_symbol()
                v = float(amount)
                if abs(v - int(v)) < 1e-9:
                    s = f"{int(v):,}".replace(',', ' ')
                else:
                    s = f"{v:,.2f}".replace(',', ' ').rstrip('0').rstrip('.')
                if any(ch.isalpha() for ch in str(cur)):
                    cur = str(cur).lower()
                return f"{s} {cur}".strip()
            except Exception:
                return str(amount)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Formulaire
        form_group = QGroupBox("Informations de la dépense")
        form_layout = QFormLayout(form_group)
        
        # Libellé
        self.libelle_edit = QLineEdit()
        self.libelle_edit.setPlaceholderText("Ex: Achat décoration, Transport...")
        form_layout.addRow("Libellé *:", self.libelle_edit)
        
        # Montant
        self.montant_spinbox = QDoubleSpinBox()
        self.montant_spinbox.setRange(0.01, 99999999.99)
        self.montant_spinbox.setDecimals(2)
        self.montant_spinbox.setSuffix(f" {self.get_currency_symbol()}")
        form_layout.addRow("Montant *:", self.montant_spinbox)
        
        # Compte comptable (nouveau)
        self.compte_combo = QComboBox()
        self.compte_combo.setPlaceholderText("Sélectionner un compte de charges...")
        form_layout.addRow("Compte de charges *:", self.compte_combo)

        # Compte financier (pour transférer / choisir caisse/banque)
        self.compte_financier_combo = QComboBox()
        self.compte_financier_combo.setPlaceholderText("Sélectionner un compte financier (caisse/banque)...")
        form_layout.addRow("Compte financier:", self.compte_financier_combo)
        
        # (Catégorie removed to simplify the expense flow)
        
        # Compte financier (pour transférer / choisir caisse/banque)
        # (déjà ajouté plus bas)
        
        layout.addWidget(form_group)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Annuler")
        self.save_btn = QPushButton("Enregistrer")
        
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.save_btn)
        layout.addLayout(buttons_layout)
        
        # Connexions
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self.validate_and_accept)
        self.libelle_edit.setFocus()
    
    def load_comptes_charges(self):
        """Charger les comptes de charges (classe 6) depuis la base de données filtrés par entreprise"""
        try:
            from ayanna_erp.database.database_manager import DatabaseManager
            from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaComptes, ComptaClasses
            
            db_manager = DatabaseManager()
            session = db_manager.get_session()
            
            # Importer et utiliser le SessionManager
            from ayanna_erp.core.session_manager import SessionManager
            
            # Obtenir l'enterprise_id depuis la session utilisateur
            enterprise_id = SessionManager.get_current_enterprise_id() or 1
            
            # Récupérer les comptes de classe 6 (charges) filtrés par entreprise
            from sqlalchemy import or_
            comptes = session.query(ComptaComptes).join(ComptaClasses).filter(
                or_(ComptaClasses.code.like('6%'), ComptaClasses.code.like('5%')),
                ComptaClasses.enterprise_id == enterprise_id,
                ComptaComptes.actif == True
            ).order_by(ComptaComptes.numero).all()

            self.comptes_charges = comptes
            self.compte_combo.clear()
            for compte in comptes:
                display_text = f"{compte.numero} - {compte.nom}"
                self.compte_combo.addItem(display_text, compte.id)

            # Récupérer aussi les comptes financiers (classe 5) pour permettre transferts entre comptes
            comptes_financiers = session.query(ComptaComptes).join(ComptaClasses).filter(
                ComptaClasses.code.like('5%'),
                ComptaClasses.enterprise_id == enterprise_id,
                ComptaComptes.actif == True
            ).order_by(ComptaComptes.numero).all()

            self.compte_financier_combo.clear()
            # Ajouter une option vide par défaut (aucun)
            self.compte_financier_combo.addItem('-- Aucun --', None)
            for c in comptes_financiers:
                self.compte_financier_combo.addItem(f"{c.numero} - {c.nom}", c.id)
            
            session.close()
            print(f"✅ {len(comptes)} comptes de charges chargés pour l'entreprise {enterprise_id}")
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement des comptes: {e}")
            QMessageBox.warning(self, "Erreur", f"Impossible de charger les comptes de charges: {e}")
    
    def validate_and_accept(self):
        if not self.libelle_edit.text().strip():
            QMessageBox.warning(self, "Erreur", "Le libellé est obligatoire.")
            return
        if self.montant_spinbox.value() <= 0:
            QMessageBox.warning(self, "Erreur", "Le montant doit être supérieur à 0.")
            return
        if self.compte_combo.currentIndex() == -1:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un compte de charges.")
            return
        # Bloquer si aucun compte financier (contrepartie) sélectionné
        if hasattr(self, 'compte_financier_combo'):
            # index 0 est '-- Aucun --' ajouté par défaut
            if self.compte_financier_combo.currentIndex() <= 0 or self.compte_financier_combo.currentData() is None:
                QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un compte financier (caisse/banque) pour la contrepartie.")
                return
        self.accept()
    
    def get_data(self):
        selected_compte_id = self.compte_combo.currentData() if self.compte_combo.currentIndex() != -1 else None
        selected_financier_id = None
        if hasattr(self, 'compte_financier_combo') and self.compte_financier_combo.currentIndex() != -1:
            selected_financier_id = self.compte_financier_combo.currentData()

        return {
            'libelle': self.libelle_edit.text().strip(),
            'montant': self.montant_spinbox.value(),
            'compte_id': selected_compte_id,
            'compte_financier_id': selected_financier_id
        }


class EntreeSortieIndex(QWidget):
    """Journal de Caisse - Gestion des entrées et sorties d'argent"""
    
    def __init__(self, main_controller, current_user):
        super().__init__()
        self.main_controller = main_controller
        self.current_user = current_user
        self.journal_data = []
        
        # Initialiser le contrôleur entreprise pour les devises
        self.entreprise_controller = EntrepriseController()
        
        # Initialiser le contrôleur des dépenses
        from ayanna_erp.modules.salle_fete.controller.entre_sortie_controller import EntreSortieController
        pos_id = getattr(main_controller, 'pos_id', 1)
        self.expense_controller = EntreSortieController(pos_id=pos_id)
        
        self.setup_ui()
        # Charger la liste des comptes financiers pour le filtre
        self.load_financial_accounts()
        self.load_journal_data()
    
    def get_currency_symbol(self):
        """Récupère le symbole de devise depuis l'entreprise"""
        try:
            return self.entreprise_controller.get_currency_symbol()
        except:
            return "€"  # Fallback
    
    def format_amount(self, amount):
        """Formate un montant avec la devise de l'entreprise"""
        try:
            return self.entreprise_controller.format_amount(amount)
        except:
            try:
                cur = self.get_currency_symbol()
                v = float(amount)
                if abs(v - int(v)) < 1e-9:
                    s = f"{int(v):,}".replace(',', ' ')
                else:
                    s = f"{v:,.2f}".replace(',', ' ').rstrip('0').rstrip('.')
                if any(ch.isalpha() for ch in str(cur)):
                    cur = str(cur).lower()
                return f"{s} {cur}".strip()
            except Exception:
                return str(amount)
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # === TITRE ET DATE ===
        header_layout = QHBoxLayout()
        
        title_label = QLabel("📊 Journal de Caisse")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2C3E50;
                padding: 10px;
            }
        """)
        
        # Date courante
        self.date_label = QLabel(f"📅 {datetime.now().strftime('%A %d %B %Y')}")
        self.date_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #7F8C8D;
                padding: 10px;
            }
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.date_label)
        layout.addLayout(header_layout)
        
        # === BARRE D'OUTILS ===
        toolbar_layout = QHBoxLayout()
        
        # Bouton Enregistrer Dépense
        self.add_depense_btn = QPushButton("💸 Enregistrer Dépense")
        self.add_depense_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        
        # Bouton Export PDF
        self.export_pdf_btn = QPushButton("📄 Export PDF")
        self.export_pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        
        toolbar_layout.addWidget(self.add_depense_btn)
        toolbar_layout.addWidget(self.export_pdf_btn)
        # Bouton Rafraîchir
        self.refresh_btn = QPushButton("🔄 Rafraîchir")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ECC71;
                color: white;
                border: none;
                padding: 12px 18px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #27AE60;
            }
        """)
        toolbar_layout.addWidget(self.refresh_btn)
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # === FILTRES ===
        filters_group = QGroupBox("Filtres et Recherche")
        filters_layout = QHBoxLayout(filters_group)
        
        # Filtre par plage de dates
        filters_layout.addWidget(QLabel("Du:"))
        self.date_debut_filter = QDateEdit()
        # Par défaut : afficher uniquement la date du jour (intervalle d'une seule journée)
        self.date_debut_filter.setDate(QDate.currentDate())
        self.date_debut_filter.setCalendarPopup(True)
        self.date_debut_filter.setStyleSheet("""
            QDateEdit {
                padding: 8px;
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                background-color: white;
            }
        """)
        filters_layout.addWidget(self.date_debut_filter)
        
        filters_layout.addWidget(QLabel("Au:"))
        self.date_fin_filter = QDateEdit()
        self.date_fin_filter.setDate(QDate.currentDate())
        self.date_fin_filter.setCalendarPopup(True)
        self.date_fin_filter.setStyleSheet("""
            QDateEdit {
                padding: 8px;
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                background-color: white;
            }
        """)
        filters_layout.addWidget(self.date_fin_filter)
        
    # Filtre type d'opération
        filters_layout.addWidget(QLabel("Type:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems(["Tous", "Entrées", "Sorties"])
        self.type_filter.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                background-color: white;
            }
        """)
        filters_layout.addWidget(self.type_filter)
        
        # Recherche par libellé
        filters_layout.addWidget(QLabel("Recherche:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Rechercher par libellé...")
        self.search_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #3498DB;
            }
        """)
        filters_layout.addWidget(self.search_edit)

        # Filtre par compte financier (classe 5)
        filters_layout.addWidget(QLabel("Compte financier:"))
        self.financial_account_combo = QComboBox()
        self.financial_account_combo.setPlaceholderText("Tous les comptes financiers")
        self.financial_account_combo.setStyleSheet(self.type_filter.styleSheet())
        filters_layout.addWidget(self.financial_account_combo)
        
        layout.addWidget(filters_group)
        
        # === TABLEAU DU JOURNAL ===
        table_group = QGroupBox("Journal des Opérations")
        table_layout = QVBoxLayout(table_group)
        
        self.journal_table = QTableWidget()
        # Colonnes: Date/Heure, Type, Libellé, Entrée, Sortie
        self.journal_table.setColumnCount(5)
        currency_symbol = self.get_currency_symbol()
        self.journal_table.setHorizontalHeaderLabels([
            "Date/Heure", "Type", "Libellé", f"Entrée ({currency_symbol})", f"Sortie ({currency_symbol})"
        ])
        
        # Configuration du tableau
        self.journal_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.journal_table.setAlternatingRowColors(True)
        # Interdire l'édition directe (annulation de l'édition inline)
        self.journal_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.journal_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: white;
                gridline-color: #ECF0F1;
            }
            QTableWidget::item {
                padding: 12px 8px;
                border-bottom: 1px solid #ECF0F1;
            }
            QTableWidget::item:selected {
                background-color: #3498DB;
                color: white;
            }
            QHeaderView::section {
                background-color: #34495E;
                color: white;
                padding: 12px;
                border: none;
                font-weight: bold;
            }
        """)
        
        # Redimensionnement des colonnes
        header = self.journal_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Date
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)           # Libellé
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Entrée
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Sortie
        
        table_layout.addWidget(self.journal_table)
        layout.addWidget(table_group)
        
        # === STATISTIQUES ===
        stats_group = QGroupBox("Résumé de la période")
        stats_layout = QHBoxLayout(stats_group)
        
        # Total Entrées
        currency_symbol = self.get_currency_symbol()
        self.total_entrees_label = QLabel(f"Total Entrées: 0.00 {currency_symbol}")
        self.total_entrees_label.setStyleSheet("""
            QLabel {
                background-color: #27AE60;
                color: white;
                padding: 15px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
            }
        """)
        
        # Total Sorties  
        self.total_sorties_label = QLabel(f"Total Sorties: 0.00 {currency_symbol}")
        self.total_sorties_label.setStyleSheet("""
            QLabel {
                background-color: #E74C3C;
                color: white;
                padding: 15px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
            }
        """)
        
        # Solde
        self.solde_label = QLabel(f"Solde: 0.00 {currency_symbol}")
        self.solde_label.setStyleSheet("""
            QLabel {
                background-color: #3498DB;
                color: white;
                padding: 15px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
            }
        """)
        
        stats_layout.addWidget(self.total_entrees_label)
        stats_layout.addWidget(self.total_sorties_label)
        stats_layout.addWidget(self.solde_label)
        
        layout.addWidget(stats_group)
        
        # === CONNEXIONS SIGNAUX ===
        self.add_depense_btn.clicked.connect(self.show_depense_dialog)
        self.export_pdf_btn.clicked.connect(self.export_to_pdf)
        self.refresh_btn.clicked.connect(self.load_journal_data)
        # Double-clic -> annulation si c'est une dépense interne (EXP_...)
        self.journal_table.cellDoubleClicked.connect(self.on_journal_row_double_clicked)
        self.date_debut_filter.dateChanged.connect(self.filter_journal)
        self.date_fin_filter.dateChanged.connect(self.filter_journal)
        self.type_filter.currentTextChanged.connect(self.filter_journal)
        self.search_edit.textChanged.connect(self.filter_journal)
        # Signaux pour le filtre compte financier
        if hasattr(self, 'financial_account_combo'):
            self.financial_account_combo.currentIndexChanged.connect(self.load_journal_data)

    def load_financial_accounts(self):
        """Charger les comptes financiers (classe 5) pour le filtre"""
        try:
            from ayanna_erp.database.database_manager import DatabaseManager
            from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaComptes, ComptaClasses
            from ayanna_erp.core.session_manager import SessionManager
            from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaConfig

            db_manager = DatabaseManager()
            session = db_manager.get_session()

            enterprise_id = SessionManager.get_current_enterprise_id() or 1

            comptes = session.query(ComptaComptes)
            comptes = comptes.join(ComptaClasses)
            comptes = comptes.filter(ComptaClasses.code.like('5%'))
            comptes = comptes.filter(ComptaClasses.enterprise_id == enterprise_id)
            comptes = comptes.filter(ComptaComptes.actif == True)
            comptes = comptes.order_by(ComptaComptes.numero).all()

            self.financial_account_combo.clear()
            # Ajouter une option 'Tous' (None) en première position
            self.financial_account_combo.addItem("-- Tous --", None)
            for c in comptes:
                self.financial_account_combo.addItem(f"{c.numero} - {c.nom}", c.id)

            # Déterminer le compte caisse configuré pour le POS courant et le sélectionner par défaut
            try:
                pos_id = getattr(self.main_controller, 'pos_id', None) or 1
                config = session.query(ComptaConfig).filter_by(pos_id=pos_id).first()
                default_id = None
                if config and getattr(config, 'compte_caisse_id', None):
                    default_id = config.compte_caisse_id

                # Trouver l'index du compte par id
                if default_id:
                    index_to_select = -1
                    for i in range(self.financial_account_combo.count()):
                        if self.financial_account_combo.itemData(i) == default_id:
                            index_to_select = i
                            break
                    if index_to_select >= 0:
                        self.financial_account_combo.setCurrentIndex(index_to_select)

            except Exception as _:
                pass

            session.close()
            print(f"✅ {len(comptes)} comptes financiers chargés pour l'entreprise {enterprise_id}")

        except Exception as e:
            print(f"Erreur chargement comptes financiers: {e}")

    def on_journal_row_double_clicked(self, row, column):
        """
        Gestion du double-clic sur une ligne du journal :
        - Si l'id commence par 'EXP_<id>' -> proposer annulation via EntreSortieController.cancel_expense
        - Sinon, rien (ou future extension)
        """
        try:
            # Récupérer la ligne affichée (appliquer les filtres actuels)
            filtered = self.get_filtered_data()
            if row < 0 or row >= len(filtered):
                return
            entry = filtered[row]
            entry_id = entry.get('id')

            # Ne traiter que les dépenses internes (EventExpense) identifiées par EXP_<id>
            if not entry_id or not str(entry_id).startswith('EXP_'):
                return

            try:
                expense_id = int(str(entry_id).split('_', 1)[1])
            except Exception:
                return

            # Confirmation
            # Demander la raison d'annulation (optionnelle)
            ok = False
            reason = ''
            reason, ok = QInputDialog.getText(self, 'Raison annulation', 'Veuillez indiquer une raison d\'annulation (optionnel):')
            if not ok:
                # Utilisateur a annulé la saisie -> on demande une confirmation simple
                reply = QMessageBox.question(self, 'Annuler la dépense',
                                             f"Voulez-vous annuler la dépense #{expense_id} ?\nCette opération créera une écriture d'annulation.",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply != QMessageBox.StandardButton.Yes:
                    return

            # Déterminer user_id (si current_user est un objet avec attribut id)
            user_id = None
            try:
                user_id = getattr(self.current_user, 'id', None) or int(self.current_user)
            except Exception:
                user_id = 1

            result = self.expense_controller.cancel_expense(expense_id, user_id=user_id, reason=reason or f"Annulé depuis l'interface par utilisateur {user_id}")
            if result:
                QMessageBox.information(self, 'Annulation effectuée', f"La dépense #{expense_id} a été annulée et les écritures inverses enregistrées.")
                # Recharger le journal
                self.load_journal_data()
            else:
                QMessageBox.critical(self, 'Erreur', f"Impossible d'annuler la dépense #{expense_id}. Voir logs.")

        except Exception as e:
            print(f"Erreur lors du double-clic journal: {e}")
    
    def load_journal_data(self):
        """
        Charger les données du journal depuis les tables métier
        - event_expenses (sorties)
        - event_payments (entrées)
        Filtrées par POS courant et plage de dates sélectionnée
        """
        try:
            # Obtenir les dates de début et fin sélectionnées
            if hasattr(self, 'date_debut_filter') and hasattr(self, 'date_fin_filter'):
                qdate_debut = self.date_debut_filter.date()
                qdate_fin = self.date_fin_filter.date()
                start_date = date(qdate_debut.year(), qdate_debut.month(), qdate_debut.day())
                end_date = date(qdate_fin.year(), qdate_fin.month(), qdate_fin.day())
            else:
                # Valeurs par défaut si les filtres n'existent pas
                end_date = date.today()
                start_date = end_date
            
            # Définir les bornes de la période pour les requêtes SQL
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            # Initialiser la liste des données
            self.journal_data = []

            # Si un compte financier est sélectionné (différent de -- Tous --), charger ses écritures comptables
            try:
                if hasattr(self, 'financial_account_combo') and self.financial_account_combo.currentIndex() > 0:
                    selected_account_id = self.financial_account_combo.currentData()
                    if selected_account_id:
                        pos_id = getattr(self.main_controller, 'pos_id', 1)
                        entre_sortie_controller = EntreSortieController(pos_id=pos_id)
                        entries = entre_sortie_controller.load_account_journal(selected_account_id, start_date, end_date)
                        self.journal_data = entries or []
                        self.journal_data.sort(key=lambda x: x['datetime'], reverse=True)
                        self.update_journal_display()
                        return
            except Exception as e:
                print(f"Erreur filtre compte financier: {e}")
            
            # Charger les sorties (dépenses) depuis event_expenses
            try:
                pos_id = getattr(self.main_controller, 'pos_id', 1)
                entre_sortie_controller = EntreSortieController(pos_id=pos_id)
                # Utiliser une requête directe avec plage de dates
                from ayanna_erp.database.database_manager import DatabaseManager
                db_manager = DatabaseManager()
                session = db_manager.get_session()
                
                # Récupérer les dépenses pour la plage de dates
                from ayanna_erp.modules.salle_fete.model.salle_fete import EventExpense
                expenses = session.query(EventExpense)\
                    .filter(
                        # EventExpense.pos_id == pos_id,
                        EventExpense.expense_date.between(start_datetime, end_datetime)
                    )\
                    .all()
                
                for expense in expenses:
                    entry = {
                        'id': f'EXP_{expense.id}',
                        'datetime': expense.expense_date,
                        'type': 'Sortie',
                        'libelle': expense.description,
                        'categorie': expense.expense_type,
                        'montant_entree': 0.0,
                        'montant_sortie': float(expense.amount),
                        'utilisateur': getattr(expense, 'created_by', 'Utilisateur'),
                        'description': ''
                    }
                    self.journal_data.append(entry)
                
                session.close()
                    
            except Exception as e:
                print(f"Erreur lors du chargement des dépenses: {e}")
            
            # Charger les entrées (paiements) depuis event_payments
            try:
                pos_id = getattr(self.main_controller, 'pos_id', 1)
                paiement_controller = PaiementController(pos_id=pos_id)
                # Utiliser une requête directe avec plage de dates
                from ayanna_erp.database.database_manager import DatabaseManager
                db_manager = DatabaseManager()
                session = db_manager.get_session()
                
                # Récupérer les paiements pour la plage de dates
                from ayanna_erp.modules.salle_fete.model.salle_fete import EventPayment
                payments = session.query(EventPayment)\
                    .join(EventPayment.reservation)\
                    .filter(
                        EventPayment.reservation.has(pos_id=pos_id),
                        EventPayment.payment_date.between(start_datetime, end_datetime)
                    )\
                    .all()
                
                for payment in payments:
                    entry = {
                        'id': f'PAY_{payment.id}',
                        'datetime': payment.payment_date,
                        'type': 'Entrée',
                        'libelle': f'Paiement {payment.payment_method}',
                        'categorie': 'Paiement client',
                        'montant_entree': float(payment.amount),
                        'montant_sortie': 0.0,
                        'utilisateur': getattr(payment, 'user_id', 'Utilisateur'),
                        'description': f'Réservation #{payment.reservation_id}' if payment.reservation_id else ''
                    }
                    self.journal_data.append(entry)
                
                session.close()
                    
            except Exception as e:
                print(f"Erreur lors du chargement des paiements: {e}")
            
            # Charger les sorties (dépenses) depuis achat_expenses (boutique)
            try:
                from ayanna_erp.database.database_manager import DatabaseManager
                db_manager = DatabaseManager()
                session = db_manager.get_session()
                
                # Récupérer les dépenses de boutique pour la date sélectionnée
                achat_expenses = session.query(AchatDepense)\
                    .filter(
                        AchatDepense.date_paiement.between(start_datetime, end_datetime)
                    )\
                    .all()
                
                for expense in achat_expenses:
                    entry = {
                        'id': f'SHOP_EXP_{expense.id}',
                        'datetime': expense.date_paiement,
                        'type': 'Sortie',
                        'libelle': expense.description,
                        'categorie': 'Achat',
                        'montant_entree': 0.0,
                        'montant_sortie': float(expense.montant),
                        'utilisateur': 'Système',  # Pas d'info utilisateur pour les dépenses boutique
                        'description': f'Référence: {expense.reference or ""}'
                    }
                    self.journal_data.append(entry)
                    
                session.close()
                    
            except Exception as e:
                print(f"Erreur lors du chargement des dépenses boutique: {e}")
            
            # Charger les entrées (paiements) depuis shop_payments (boutique)
            try:
                from ayanna_erp.database.database_manager import DatabaseManager
                db_manager = DatabaseManager()
                session = db_manager.get_session()
                
                # Récupérer les paiements de boutique pour la date sélectionnée
                shop_payments = session.query(ShopPayment)\
                    .join(ShopPanier)\
                    .outerjoin(ShopClient)\
                    .filter(
                        # ShopPanier.pos_id == pos_id,
                        ShopPayment.payment_date.between(start_datetime, end_datetime),
                        ShopPanier.status.in_(['validé', 'payé', 'completed', 'pending'])
                    )\
                    .all()
                
                for payment in shop_payments:
                    # Récupérer le nom du client
                    client_name = "Client anonyme"
                    if payment.panier.client:
                        client_name = f"{payment.panier.client.nom or ''} {payment.panier.client.prenom or ''}".strip()
                        if not client_name:
                            client_name = f"Client #{payment.panier.client.id}"
                    
                    entry = {
                        'id': f'SHOP_PAY_{payment.id}',
                        'datetime': payment.payment_date,
                        'type': 'Entrée',
                        'libelle': f'[VENTE] Encaissement Facture - {payment.reference}',
                        'categorie': 'VENTE',
                        'montant_entree': float(payment.amount),
                        'montant_sortie': 0.0,
                        'utilisateur': 'Système',  # Pas d'info utilisateur pour les paiements boutique
                        'description': f'Panier #{payment.panier.numero_commande or payment.panier.id}'
                    }
                    self.journal_data.append(entry)
                    
                session.close()
                    
            except Exception as e:
                print(f"Erreur lors du chargement des paiements boutique: {e}")
                
                
            # Charger les entrées (paiements) depuis restau_payments
            try:
                from ayanna_erp.database.database_manager import DatabaseManager
                db_manager = DatabaseManager()
                session = db_manager.get_session()
                
                # Récupérer les paiements de boutique pour la date sélectionnée
                restau_payments = session.query(RestauPayment)\
                    .join(RestauPanier)\
                    .filter(
                        # ShopPanier.pos_id == pos_id,
                        RestauPayment.created_at.between(start_datetime, end_datetime),
                        RestauPanier.status.in_(['valide', 'en_cours'])
                    )\
                    .all()
                
                for payment in restau_payments:
                    # Récupérer le nom du client
                    client_name = "Client anonyme"
                    if payment.panier.client_id:
                        # client_name = f"{payment.panier.client.nom or ''} {payment.panier.client.prenom or ''}".strip()
                        if not client_name:
                            client_name = f"Client #{payment.panier.client.id}"
                    
                    entry = {
                        'id': f'RESTAU_PAY_{payment.id}',
                        'datetime': payment.created_at,
                        'type': 'Entrée',
                        'libelle': f'[VENTE] Encaissement Panier - {payment.panier_id} - {client_name}',
                        'categorie': 'RESTAU_BAR',
                        'montant_entree': float(payment.amount),
                        'montant_sortie': 0.0,
                        'utilisateur': 'Système',  # Pas d'info utilisateur pour les paiements boutique
                        'description': f'Panier #{payment.panier.id or payment.panier.id}'
                    }
                    self.journal_data.append(entry)
                    
                session.close()
                    
            except Exception as e:
                print(f"Erreur lors du chargement des paiements restaurant: {e}")
            
            # Trier par date/heure décroissante
            self.journal_data.sort(key=lambda x: x['datetime'], reverse=True)
            
            # Mettre à jour l'affichage
            self.update_journal_display()
            
        except Exception as e:
            print(f"Erreur lors du chargement du journal: {e}")
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement du journal: {str(e)}")
    
    
    def update_journal_display(self):
        """Mettre à jour l'affichage du tableau et des statistiques"""
        # Filtrer les données selon les critères
        filtered_data = self.get_filtered_data()
        
        # Mettre à jour le tableau
        self.journal_table.setRowCount(len(filtered_data))
        
        for row, entry in enumerate(filtered_data):
            # Date/Heure
            datetime_str = entry['datetime'].strftime("%d/%m/%Y %H:%M")
            self.journal_table.setItem(row, 0, QTableWidgetItem(datetime_str))
            
            # Type
            type_item = QTableWidgetItem(entry['type'])
            type_item.setForeground(Qt.GlobalColor.black)  # Texte noir pour une meilleure visibilité
            self.journal_table.setItem(row, 1, type_item)
            
            # Libellé
            self.journal_table.setItem(row, 2, QTableWidgetItem(entry['libelle']))
            
            # Montant Entrée (colonne 3 après suppression de la catégorie)
            if entry['montant_entree'] > 0:
                entree_item = QTableWidgetItem(self.format_amount(entry['montant_entree']))
                entree_item.setForeground(Qt.GlobalColor.darkGreen)
                entree_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            else:
                entree_item = QTableWidgetItem("-")
                entree_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.journal_table.setItem(row, 3, entree_item)
            
            # Montant Sortie
            if entry['montant_sortie'] > 0:
                sortie_item = QTableWidgetItem(self.format_amount(entry['montant_sortie']))
                sortie_item.setForeground(Qt.GlobalColor.darkRed)
                sortie_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            else:
                sortie_item = QTableWidgetItem("-")
                sortie_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # Montant Sortie (colonne 4)
            self.journal_table.setItem(row, 4, sortie_item)
            
            # (Utilisateur column removed)
        
        # Mettre à jour les statistiques
        self.update_statistics(filtered_data)
    
    def get_filtered_data(self):
        """Obtenir les données filtrées selon les critères"""
        filtered_data = self.journal_data.copy()
        
        # Filtre par plage de dates
        if hasattr(self, 'date_debut_filter') and hasattr(self, 'date_fin_filter'):
            qdate_debut = self.date_debut_filter.date()
            qdate_fin = self.date_fin_filter.date()
            start_date = date(qdate_debut.year(), qdate_debut.month(), qdate_debut.day())
            end_date = date(qdate_fin.year(), qdate_fin.month(), qdate_fin.day())
            filtered_data = [entry for entry in filtered_data 
                           if start_date <= entry['datetime'].date() <= end_date]
        
        # Filtre par type
        if hasattr(self, 'type_filter'):
            type_filter = self.type_filter.currentText()
            if type_filter == "Entrées":
                filtered_data = [entry for entry in filtered_data if entry['type'] == 'Entrée']
            elif type_filter == "Sorties":
                filtered_data = [entry for entry in filtered_data if entry['type'] == 'Sortie']
            # Si "Tous" est sélectionné, on ne filtre pas (on garde toutes les données)
        
        # Filtre par recherche
        if hasattr(self, 'search_edit'):
            search_text = self.search_edit.text().lower()
            if search_text:
                filtered_data = [entry for entry in filtered_data 
                               if search_text in entry['libelle'].lower()]
        
        return filtered_data
    
    def update_statistics(self, data):
        """Mettre à jour les statistiques affichées"""
        total_entrees = sum(entry['montant_entree'] for entry in data)
        total_sorties = sum(entry['montant_sortie'] for entry in data)
        solde = total_entrees - total_sorties
        
        currency_symbol = self.get_currency_symbol()

        # Mettre à jour les labels (utiliser le formateur central pour l'affichage)
        self.total_entrees_label.setText(f"Total Entrées: {self.format_amount(total_entrees)}")
        self.total_sorties_label.setText(f"Total Sorties: {self.format_amount(total_sorties)}")

        # Couleur du solde selon le signe
        if solde >= 0:
            self.solde_label.setText(f"Solde: +{self.format_amount(solde)}")
            self.solde_label.setStyleSheet("""
                QLabel {
                    background-color: #27AE60;
                    color: white;
                    padding: 15px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 16px;
                }
            """)
        else:
            self.solde_label.setText(f"Solde: {self.format_amount(solde)}")
            self.solde_label.setStyleSheet("""
                QLabel {
                    background-color: #E67E22;
                    color: white;
                    padding: 15px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 16px;
                }
            """)
    
    def filter_journal(self):
        """Appliquer les filtres et mettre à jour l'affichage"""
        # Vérifier si la plage de dates a changé
        if hasattr(self, 'date_debut_filter') and hasattr(self, 'date_fin_filter'):
            qdate_debut = self.date_debut_filter.date()
            qdate_fin = self.date_fin_filter.date()
            new_start_date = date(qdate_debut.year(), qdate_debut.month(), qdate_debut.day())
            new_end_date = date(qdate_fin.year(), qdate_fin.month(), qdate_fin.day())
            
            # Recharger les données seulement si la plage de dates a changé
            if (not hasattr(self, '_current_start_date') or 
                not hasattr(self, '_current_end_date') or
                self._current_start_date != new_start_date or 
                self._current_end_date != new_end_date):
                
                self._current_start_date = new_start_date
                self._current_end_date = new_end_date
                self.load_journal_data()
            else:
                # Juste mettre à jour l'affichage avec les filtres actuels
                self.update_journal_display()
        else:
            # Fallback: recharger les données
            self.load_journal_data()
    
    def show_depense_dialog(self):
        """Afficher le dialog pour enregistrer une dépense"""
        dialog = DepenseDialog(self, current_user=self.current_user)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.save_depense(data)
    
    def save_depense(self, depense_data):
        """Sauvegarder une nouvelle dépense avec intégration comptable"""
        try:
            # Utiliser le contrôleur pour créer la dépense avec intégration comptable
            expense = self.expense_controller.create_expense(depense_data)
            
            if expense:
                # Recharger les données
                self.load_journal_data()
                
                currency_symbol = self.get_currency_symbol()
                QMessageBox.information(self, "Succès", 
                    f"Dépense enregistrée avec succès!\n"
                    f"Montant: {expense.amount}{currency_symbol}\n"
                    f"Écritures comptables créées automatiquement.")
            else:
                QMessageBox.critical(self, "Erreur", "Impossible d'enregistrer la dépense.")
                
        except Exception as e:
            print(f"Erreur lors de la sauvegarde: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible d'enregistrer la dépense: {str(e)}")
    
    def export_to_pdf(self):
        """Exporter le journal de caisse en PDF professionnel"""
        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch, cm
            from reportlab.lib.colors import HexColor, black, white, gray
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
            from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
            from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
            import os
            import tempfile

            # Créer le dossier d'export s'il n'existe pas
            export_dir = os.path.join(os.getcwd(), "exports_caisse")
            os.makedirs(export_dir, exist_ok=True)

            # Générer le nom du fichier
            qdate_debut = self.date_debut_filter.date()
            qdate_fin = self.date_fin_filter.date()
            start_date = date(qdate_debut.year(), qdate_debut.month(), qdate_debut.day())
            end_date = date(qdate_fin.year(), qdate_fin.month(), qdate_fin.day())

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if start_date == end_date:
                filename = os.path.join(export_dir, f"journal_caisse_{start_date.strftime('%Y%m%d')}_{timestamp}.pdf")
                period_title = f"Journal de Caisse - {start_date.strftime('%d/%m/%Y')}"
            else:
                filename = os.path.join(export_dir, f"journal_caisse_{start_date.strftime('%Y%m%d')}_au_{end_date.strftime('%Y%m%d')}_{timestamp}.pdf")
                period_title = f"Journal de Caisse - Du {start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}"

            # Variables pour gérer le fichier temporaire du logo
            temp_logo_file = None
            logo_path = None

            try:
                # Créer le document PDF
                doc = SimpleDocTemplate(filename, pagesize=A4, leftMargin=5*cm, rightMargin=5*cm, topMargin=2*cm, bottomMargin=2*cm)
                elements = []

                # Styles personnalisés
                styles = getSampleStyleSheet()
                styles.add(ParagraphStyle(
                    name='CompanyTitle',
                    fontSize=18,
                    fontName='Helvetica-Bold',
                    textColor=HexColor('#2C3E50'),
                    alignment=TA_CENTER,
                    spaceAfter=10
                ))
                styles.add(ParagraphStyle(
                    name='ReportTitle',
                    fontSize=16,
                    fontName='Helvetica-Bold',
                    textColor=HexColor('#1976D2'),
                    alignment=TA_CENTER,
                    spaceAfter=20
                ))
                styles.add(ParagraphStyle(
                    name='SectionHeader',
                    fontSize=12,
                    fontName='Helvetica-Bold',
                    textColor=HexColor('#34495E'),
                    spaceAfter=10
                ))
                styles.add(ParagraphStyle(
                    name='NormalText',
                    fontSize=9,
                    fontName='Helvetica',
                    spaceAfter=5
                ))
                styles.add(ParagraphStyle(
                    name='FooterText',
                    fontSize=8,
                    fontName='Helvetica-Oblique',
                    textColor=gray,
                    alignment=TA_CENTER,
                    spaceAfter=5
                ))

                # Informations de l'entreprise
                enterprise_controller = EntrepriseController()
                company_info = enterprise_controller.get_company_info_for_pdf(1)  # POS ID par défaut

                # En-tête avec logo et informations entreprise
                header_data = []

                # Logo (si disponible)
                if company_info.get('logo'):
                    try:
                        # Créer un fichier temporaire pour le logo (garder ouvert)
                        temp_logo_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                        temp_logo_file.write(company_info['logo'])
                        logo_path = temp_logo_file.name
                        temp_logo_file.close()  # Fermer mais ne pas supprimer

                        logo = Image(logo_path, width=2*cm, height=2*cm)
                        header_data.append([logo, Paragraph(f"<b>{company_info.get('name', 'AYANNA ERP')}</b><br/>{company_info.get('address', '')}<br/>{company_info.get('city', '')}<br/>Tel: {company_info.get('phone', '')}", styles['NormalText'])])

                    except Exception as e:
                        print(f"Erreur logo: {e}")
                        # Nettoyer en cas d'erreur
                        if temp_logo_file:
                            try:
                                os.unlink(logo_path)
                            except:
                                pass
                        header_data.append([Paragraph(f"<b>{company_info.get('name', 'AYANNA ERP')}</b><br/>{company_info.get('address', '')}<br/>{company_info.get('city', '')}<br/>Tel: {company_info.get('phone', '')}", styles['NormalText']), ''])
                else:
                    header_data.append([Paragraph(f"<b>{company_info.get('name', 'AYANNA ERP')}</b><br/>{company_info.get('address', '')}<br/>{company_info.get('city', '')}<br/>Tel: {company_info.get('phone', '')}", styles['NormalText']), ''])

                header_table = Table(header_data, colWidths=[3*cm, 12*cm])
                header_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                    ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                elements.append(header_table)
                elements.append(Spacer(1, 0.5*cm))

                # Titre du rapport
                elements.append(Paragraph(period_title, styles['ReportTitle']))

                # Informations sur les filtres appliqués
                filter_info = []
                type_filter = self.type_filter.currentText() if hasattr(self, 'type_filter') else None
                search_text = self.search_edit.text().strip() if hasattr(self, 'search_edit') and self.search_edit.text().strip() else None

                if type_filter and type_filter != "Tous":
                    filter_info.append(f"Type: {type_filter}")
                if search_text:
                    filter_info.append(f"Recherche: '{search_text}'")

                if filter_info:
                    elements.append(Paragraph(f"<b>Filtres appliqués:</b> {' | '.join(filter_info)}", styles['SectionHeader']))
                else:
                    elements.append(Paragraph("<b>Toutes les opérations</b>", styles['SectionHeader']))

                elements.append(Paragraph(f"<b>Date d'export:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['NormalText']))
                elements.append(Spacer(1, 0.5*cm))

                # Données filtrées
                filtered_data = self.get_filtered_data()

                if not filtered_data:
                    elements.append(Paragraph("Aucune opération trouvée pour cette période.", styles['NormalText']))
                else:
                    # Statistiques générales
                    total_entrees = sum(entry['montant_entree'] for entry in filtered_data)
                    total_sorties = sum(entry['montant_sortie'] for entry in filtered_data)
                    solde = total_entrees - total_sorties

                    currency_symbol = self.get_currency_symbol()

                    stats_data = [
                        ['Résumé de la période', ''],
                        ['Total Entrées:', format_amount_for_pdf(total_entrees, currency=currency_symbol)],
                        ['Total Sorties:', format_amount_for_pdf(total_sorties, currency=currency_symbol)],
                        ['Solde:', format_amount_for_pdf(solde, currency=currency_symbol)]
                    ]

                    stats_table = Table(stats_data, colWidths=[6*cm, 6*cm])
                    stats_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (1, 0), HexColor('#ECF0F1')),
                        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                        ('GRID', (0, 0), (-1, -1), 0.5, black),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    elements.append(stats_table)
                    elements.append(Spacer(2, 2*cm))

                    # Tableau des opérations
                    table_data = [
                        ['Date/Heure', 'Type', 'Libellé', f'Entrée ({currency_symbol})', f'Sortie ({currency_symbol})']
                    ]

                    for entry in filtered_data:
                        # Formatage des montants avec couleurs conditionnelles
                        if entry['montant_entree'] > 0:
                            entree_str = format_amount_for_pdf(entry['montant_entree'], currency=currency_symbol)
                            sortie_str = "-"
                        elif entry['montant_sortie'] > 0:
                            entree_str = "-"
                            sortie_str = format_amount_for_pdf(entry['montant_sortie'], currency=currency_symbol)
                        else:
                            entree_str = "-"
                            sortie_str = "-"

                        row = [
                            entry['datetime'].strftime("%d/%m/%Y\n%H:%M"),
                            entry['type'],
                            entry['libelle'],
                            entree_str,
                            sortie_str
                        ]
                        table_data.append(row)

                    # Créer le tableau avec des largeurs appropriées
                    col_widths = [2.5*cm, 2*cm, 8*cm, 3*cm, 3*cm]
                    operations_table = Table(table_data, colWidths=col_widths, repeatRows=1)

                    # Style du tableau
                    table_style = TableStyle([
                        # En-tête
                        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#34495E')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), white),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 8),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),

                        # Corps du tableau
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 7),
                        ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Date
                        ('ALIGN', (1, 0), (1, -1), 'CENTER'),  # Type
                        ('ALIGN', (2, 0), (2, -1), 'LEFT'),    # Libellé
                        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),   # Montants (Entrée)
                        ('ALIGN', (4, 0), (4, -1), 'RIGHT'),   # Montants (Sortie)

                        # Bordures
                        ('GRID', (0, 0), (-1, -1), 0.5, black),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

                        # Espacement des cellules
                        ('LEFTPADDING', (0, 0), (-1, -1), 3),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                        ('TOPPADDING', (0, 0), (-1, -1), 2),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                    ])

                    # Ajouter les lignes alternées dynamiquement
                    if len(table_data) > 2:  # En-tête + au moins 1 ligne de données
                        for i in range(2, len(table_data), 2):  # Commencer à 1 (après en-tête) et alterner
                            table_style.add('BACKGROUND', (0, i), (-1, i), HexColor('#F8F9FA'))

                    operations_table.setStyle(table_style)
                    elements.append(operations_table)
                    elements.append(Spacer(1, 1*cm))

                # Pied de page avec informations de génération
                elements.append(Spacer(1, 1*cm))
                elements.append(Paragraph(f"<i>Généré par Ayanna ERP App - {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</i>", styles['FooterText']))

                # Générer le PDF
                doc.build(elements)

                # Nettoyer le fichier temporaire du logo
                if logo_path and os.path.exists(logo_path):
                    try:
                        os.unlink(logo_path)
                    except Exception as cleanup_error:
                        print(f"Avertissement nettoyage logo: {cleanup_error}")

                # Ouvrir le dossier contenant le PDF
                try:
                    import subprocess
                    fullpath = os.path.abspath(filename)
                    # Sous Windows, on demande à explorer de sélectionner le fichier. Certaines environnements
                    # retournent un code non-zéro si la sélection échoue ; dans ce cas on ouvre le dossier.
                    if os.name == 'nt':
                        if os.path.exists(fullpath):
                            # Utiliser une commande shell pour conserver la syntaxe attendue par explorer
                            cmd = f'explorer /select,"{fullpath}"'
                            proc = subprocess.run(cmd, shell=True)
                            if proc.returncode != 0:
                                # Fallback : ouvrir le dossier contenant le fichier
                                folder = os.path.dirname(fullpath)
                                try:
                                    subprocess.run(['explorer', folder], check=False)
                                except Exception:
                                    pass
                        else:
                            # Si le fichier n'existe pas (imprévu), ouvrir le dossier d'exports
                            folder = os.path.dirname(fullpath)
                            try:
                                subprocess.run(['explorer', folder], check=False)
                            except Exception:
                                pass
                    else:
                        # Pour les autres OS, ouvrir le dossier contenant le fichier
                        folder = os.path.dirname(fullpath)
                        if sys.platform == 'darwin':
                            subprocess.run(['open', folder], check=False)
                        else:
                            subprocess.run(['xdg-open', folder], check=False)

                    QMessageBox.information(self, "Export réussi",
                                          f"Le journal de caisse a été exporté avec succès !\n\n"
                                          f"Fichier: {filename}\n\n"
                                          "Le dossier contenant l'export a été ouvert (ou sélectionné).")
                except Exception as open_error:
                    # Ne leverons pas d'exception ici : informer l'utilisateur mais considérer l'export comme réussi
                    QMessageBox.information(self, "Export réussi",
                                          f"Le journal de caisse a été exporté avec succès !\n\n"
                                          f"Fichier: {filename}\n\n"
                                          f"Erreur ouverture dossier: {open_error}")

            except Exception as e:
                # Nettoyer en cas d'erreur
                if logo_path and os.path.exists(logo_path):
                    try:
                        os.unlink(logo_path)
                    except:
                        pass
                raise e

        except ImportError:
            QMessageBox.warning(self, "Erreur", "La bibliothèque reportlab n'est pas installée.\nInstallez-la avec: pip install reportlab")
        except Exception as e:
            print(f"❌ Erreur génération PDF caisse: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible d'exporter le PDF: {str(e)}")
