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
from PyQt6.QtGui import QFont, QPixmap, QIcon, QBrush, QColor, QAction
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
        
        font = self.font()
        font.setPointSize(11)  # 11 ou 12 selon ton écran
        self.setFont(font)

        self.setWindowTitle("Enregistrer une sortie d'argent")
        self.setModal(True)
        self.resize(550, 450)
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
            return "FC"  # Fallback
    
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
        form_group = QGroupBox("Informations de la sortie d'argent")
        form_layout = QFormLayout(form_group)
        
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form_layout.setVerticalSpacing(12)
        form_layout.setHorizontalSpacing(20)
        
        label_font = QFont()
        label_font.setPointSize(14)
        label_font.setBold(True)

        for i in range(form_layout.rowCount()):
            label_item = form_layout.itemAt(i, QFormLayout.LabelRole)
            if label_item and label_item.widget():
                label_item.widget().setFont(label_font)
        
        # Libellé
        self.libelle_edit = QLineEdit()
        self.libelle_edit.setMinimumHeight(36)
        self.libelle_edit.setPlaceholderText("Ex: Achat décoration, Transport...")
        form_layout.addRow("Libellé *:", self.libelle_edit)
        
        # Montant
        self.montant_spinbox = QDoubleSpinBox()
        self.montant_spinbox.setMinimumHeight(36)
        self.montant_spinbox.setRange(0.01, 99999999.99)
        self.montant_spinbox.setDecimals(2)
        self.montant_spinbox.setSuffix(f" {self.get_currency_symbol()}")
        form_layout.addRow("Montant *:", self.montant_spinbox)
        
        # Compte comptable (nouveau)
        self.compte_combo = QComboBox()
        self.compte_combo.setMinimumHeight(36)
        self.compte_combo.setPlaceholderText("Sélectionner un compte de charges...")
        form_layout.addRow("Compte de charges (Entrée) *:", self.compte_combo)

        # Compte financier (pour transférer / choisir caisse/banque)
        self.compte_financier_combo = QComboBox()
        self.compte_financier_combo.setMinimumHeight(36)
        self.compte_financier_combo.setPlaceholderText("Sélectionner un compte financier (caisse/banque)...")
        form_layout.addRow("Compte financier(Sortie) *:", self.compte_financier_combo)
                
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
                padding: 12px 28px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)

        self.cancel_btn.setMinimumHeight(40)
        self.save_btn.setMinimumHeight(40)
        
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
            from ayanna_erp.database.database_manager import get_database_manager
            from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaComptes, ComptaClasses
            
            db_manager = get_database_manager()
            session = db_manager.SessionLocal()
            
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
        # Connecter le signal d'erreur du contrôleur à un affichage utilisateur convivial
        try:
            self.expense_controller.error_occurred.connect(lambda msg: QMessageBox.critical(self, 'Erreur', str(msg)))
        except Exception:
            pass
        
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
        
        # Bouton Enregistrer Sortie
        self.add_depense_btn = QPushButton("💸 Enregistrer Sortie")
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
        
        # Bouton Export Rapport Quotidien
        self.export_report_btn = QPushButton("📑 Export Rapport")
        self.export_report_btn.setStyleSheet("""
            QPushButton {
                background-color: #9B59B6;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #8E44AD;
            }
        """)
        toolbar_layout.addWidget(self.export_report_btn)
        
        # Bouton Rafraîchir
        self.refresh_btn = QPushButton("🔄 Actualiser")
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
        # Solde global du compte financier (si un compte est sélectionné)
        self.global_balance_label = QLabel("")
        self.global_balance_label.setStyleSheet("""
            QLabel {
                background-color: #34495E;
                color: white;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
        """)
        stats_layout.addWidget(self.global_balance_label)
        
        layout.addWidget(stats_group)
        
        # === CONNEXIONS SIGNAUX ===
        self.add_depense_btn.clicked.connect(self.show_depense_dialog)
        self.export_pdf_btn.clicked.connect(self.export_to_pdf)
        self.export_report_btn.clicked.connect(self.export_daily_report)
        self.refresh_btn.clicked.connect(self.load_journal_data)
        # Double-clic -> annulation si c'est une dépense interne (EXP_...)
        self.journal_table.cellDoubleClicked.connect(self.on_journal_row_double_clicked)
        self.date_debut_filter.dateChanged.connect(self.filter_journal)
        self.date_fin_filter.dateChanged.connect(self.filter_journal)
        self.type_filter.currentTextChanged.connect(self.filter_journal)
        self.search_edit.textChanged.connect(self.filter_journal)
        # Signaux pour le filtre compte financier
        if hasattr(self, 'financial_account_combo'):
            self.financial_account_combo.currentIndexChanged.connect(self.on_financial_account_changed)

    def on_financial_account_changed(self, *args):
        # Protection pour éviter les appels multiples
        if hasattr(self, '_block_financial_account_signal') and self._block_financial_account_signal:
            return
        self._block_financial_account_signal = True
        try:
            self.load_journal_data()
        finally:
            self._block_financial_account_signal = False

        # Remplacer les connexions de date par une version protégée
        self.date_debut_filter.dateChanged.disconnect()
        self.date_debut_filter.dateChanged.connect(self.on_date_filter_changed)
        self.date_fin_filter.dateChanged.disconnect()
        self.date_fin_filter.dateChanged.connect(self.on_date_filter_changed)

    def on_date_filter_changed(self, *args):
        # Protection pour éviter les appels multiples
        if hasattr(self, '_block_date_filter_signal') and self._block_date_filter_signal:
            return
        self._block_date_filter_signal = True
        try:
            self.filter_journal()
        finally:
            self._block_date_filter_signal = False
    
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

            print(f"✅ {len(comptes)} comptes financiers chargés pour l'entreprise {enterprise_id}")

        except Exception as e:
            print(f"Erreur chargement comptes financiers: {e}")
        finally:
            try:
                session.close()
            except Exception:
                pass

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

            # Désactiver le double-clic pour les lignes de type 'Entrée' (UI-side)
            try:
                entry_type = (entry.get('type') or '').strip().lower()
                if entry_type in ('entrée', 'entree'):
                    QMessageBox.information(self, "Action désactivée", "La suppression via double‑clic est désactivée pour les opérations de type 'Entrée'.")
                    return
            except Exception:
                pass

            # Traiter les différents types d'entrées :
            # - Dépenses internes : id 'EXP_<id>' -> annulation via cancel_expense
            # - Écritures comptables : id 'EC_<id>' -> annulation via cancel_accounting_entry
            if not entry_id:
                return

            # Dépenses internes
            if str(entry_id).startswith('EXP_'):
                try:
                    expense_id = int(str(entry_id).split('_', 1)[1])
                except Exception:
                    return

                # Demander une raison optionnelle (champ libre)
                reason, _ = QInputDialog.getText(self, 'Raison de suppression (optionnel)', 'Veuillez indiquer une raison pour la suppression (optionnel):')

                # Confirmation explicite avant suppression définitive
                confirm_msg = (
                    f"Vous êtes sur le point de SUPPRIMER DÉFINITIVEMENT la dépense #{expense_id}.\n\n"
                    "Cette opération supprimera la dépense métier ainsi que le journal comptable associé et toutes ses écritures."
                    "\n\nCette action est IRRÉVERSIBLE. Voulez-vous continuer ?"
                )

                reply = QMessageBox.question(self, 'Confirmer la suppression définitive', confirm_msg,
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                             QMessageBox.StandardButton.No)
                if reply != QMessageBox.StandardButton.Yes:
                    return

                # Déterminer user_id
                user_id = None
                try:
                    user_id = getattr(self.current_user, 'id', None) or int(self.current_user)
                except Exception:
                    user_id = 1

                # Appeler la suppression (méthode supprimant dépense + journal + écritures)
                reason_text = reason.strip() if isinstance(reason, str) and reason.strip() else f"Supprimé depuis l'interface par utilisateur {user_id}"
                result = self.expense_controller.cancel_expense(expense_id, user_id=user_id, reason=reason_text)
                if result:
                    QMessageBox.information(self, 'Suppression effectuée', f"La dépense #{expense_id} et les écritures/journal associés ont été supprimés.")
                    self.load_journal_data()
                else:
                    QMessageBox.critical(self, 'Erreur', f"Impossible de supprimer la dépense #{expense_id}. Voir logs.")
                return

            # Écritures comptables
            if str(entry_id).startswith('EC_'):
                try:
                    ecr_id = int(str(entry_id).split('_', 1)[1])
                except Exception:
                    return

                # Demander une raison optionnelle pour la suppression
                reason, _ = QInputDialog.getText(self, 'Raison suppression (optionnel)', 'Veuillez indiquer une raison pour la suppression (optionnel):')

                # Confirmation explicite avant suppression définitive
                confirm_msg = (
                    f"Vous êtes sur le point de SUPPRIMER DÉFINITIVEMENT l\'écriture comptable #{ecr_id}.\n\n"
                    "Cette opération supprimera le journal comptable associé et toutes ses écritures."
                    "\n\nCette action est IRRÉVERSIBLE. Voulez-vous continuer ?"
                )

                reply = QMessageBox.question(self, 'Confirmer la suppression définitive', confirm_msg,
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                             QMessageBox.StandardButton.No)
                if reply != QMessageBox.StandardButton.Yes:
                    return

                user_id = None
                try:
                    user_id = getattr(self.current_user, 'id', None) or int(self.current_user)
                except Exception:
                    user_id = 1

                # Appeler suppression définitive du journal et écritures
                reason_text = reason.strip() if isinstance(reason, str) and reason.strip() else f"Supprimé depuis l'interface par utilisateur {user_id}"
                # Utilise la nouvelle méthode delete_accounting_entry si disponible
                try:
                    result = self.expense_controller.delete_accounting_entry(ecr_id, user_id=user_id, reason=reason_text)
                except Exception:
                    # Fallback vers l'annulation par création de journal inverse si la suppression n'existe pas
                    result = self.expense_controller.cancel_accounting_entry(ecr_id, user_id=user_id, reason=reason_text)

                if result:
                    QMessageBox.information(self, 'Suppression effectuée', f"L\'écriture comptable #{ecr_id} et le journal associé ont été supprimés.")
                    self.load_journal_data()
                else:
                    QMessageBox.critical(self, 'Erreur', f"Impossible de supprimer l\'écriture #{ecr_id}. Voir logs.")
                return

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

            # Vérification de la cohérence de la plage de dates
            if start_date > end_date:
                QMessageBox.warning(self, "Erreur de plage de dates", "La date de début ne peut pas être postérieure à la date de fin.")
                return

            # Définir les bornes de la période pour les requêtes SQL
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            # Initialiser la liste des données
            self.journal_data = []
            # Réinitialiser l'affichage du solde global par défaut
            try:
                self.global_balance_label.setText("")
            except Exception:
                pass

            # Mettre à jour le solde global du compte sélectionné (si applicable)
            try:
                if hasattr(self, 'financial_account_combo') and self.financial_account_combo.currentIndex() > 0:
                    selected_account_id = self.financial_account_combo.currentData()
                    if selected_account_id:
                        global_balance = self.get_account_global_balance(selected_account_id) or 0
                        currency_symbol = self.get_currency_symbol() if hasattr(self, 'get_currency_symbol') else "FC"
                        if global_balance >= 0:
                            self.global_balance_label.setText(f"Solde global du compte: +{self.format_amount(global_balance)} {currency_symbol}")
                            self.global_balance_label.setStyleSheet("""
                                QLabel {
                                    background-color: #27AE60;
                                    color: white;
                                    padding: 10px;
                                    border-radius: 6px;
                                    font-weight: bold;
                                    font-size: 13px;
                                }
                            """)
                        else:
                            self.global_balance_label.setText(f"Solde global du compte: {self.format_amount(global_balance)} {currency_symbol}")
                            self.global_balance_label.setStyleSheet("""
                                QLabel {
                                    background-color: #E67E22;
                                    color: white;
                                    padding: 10px;
                                    border-radius: 6px;
                                    font-weight: bold;
                                    font-size: 13px;
                                }
                            """)
                else:
                    self.global_balance_label.setText("")
            except Exception as e:
                print(f"[DEBUG] Erreur lors de la mise à jour du solde global: {e}")

            # Si un compte financier est sélectionné (différent de -- Tous --), charger ses écritures comptables
            try:
                if hasattr(self, 'financial_account_combo') and self.financial_account_combo.currentIndex() > 0:
                    selected_account_id = self.financial_account_combo.currentData()
                    if selected_account_id:
                        pos_id = getattr(self.main_controller, 'pos_id', 1)
                        entre_sortie_controller = EntreSortieController(pos_id=pos_id)
                        entries = entre_sortie_controller.load_account_journal(selected_account_id, start_date, end_date)
                        # Ajout du champ account_id pour chaque écriture
                        for entry in entries:
                            entry['account_id'] = selected_account_id
                        self.journal_data = entries or []
                        self.journal_data.sort(key=lambda x: x['datetime'], reverse=True)
                        def update_journal_display(self):
                            """Met à jour l'affichage du tableau et des statistiques (limite à 500 lignes, optimisé PyQt5)."""
                            import logging
                            MAX_ROWS = 500
                            filtered_data = self.get_filtered_data()
                            total_rows = len(filtered_data)
                            if total_rows > MAX_ROWS:
                                filtered_data = filtered_data[:MAX_ROWS]
                                QMessageBox.information(self, "Limite d'affichage", f"Seuls les {MAX_ROWS} premiers enregistrements sont affichés pour des raisons de performance.")
                            self.journal_table.setSortingEnabled(False)
                            self.journal_table.setUpdatesEnabled(False)
                            self.journal_table.blockSignals(True)
                            self.journal_table.clearContents()
                            self.journal_table.setRowCount(0)
                            self.journal_table.setRowCount(len(filtered_data))
                            for row, entry in enumerate(filtered_data):
                                # Remplissage optimisé, inspiré de commandes_index.py
                                try:
                                    # Date/Heure
                                    date_str = entry.get('date_heure', '')
                                    item_date = QTableWidgetItem(str(date_str))
                                    self.journal_table.setItem(row, 0, item_date)
                                    # Type
                                    type_str = entry.get('type', '')
                                    item_type = QTableWidgetItem(str(type_str))
                                    self.journal_table.setItem(row, 1, item_type)
                                    # Libellé
                                    libelle = entry.get('libelle', '')
                                    item_libelle = QTableWidgetItem(str(libelle))
                                    self.journal_table.setItem(row, 2, item_libelle)
                                    # Entrée
                                    entree = entry.get('montant_entree', 0)
                                    item_entree = QTableWidgetItem(self.format_amount(entree))
                                    self.journal_table.setItem(row, 3, item_entree)
                                    # Sortie
                                    sortie = entry.get('montant_sortie', 0)
                                    item_sortie = QTableWidgetItem(self.format_amount(sortie))
                                    self.journal_table.setItem(row, 4, item_sortie)
                                    # Style grisé si annulé
                                    if entry.get('status', '') in ('annule', 'cancelled'):
                                        for col in range(5):
                                            item = self.journal_table.item(row, col)
                                            if item:
                                                item.setForeground(QBrush(QColor('#888888')))
                                                font = item.font()
                                                font.setStrikeOut(True)
                                                item.setFont(font)
                                except Exception as e:
                                    print(f"[DEBUG] Erreur remplissage ligne {row}: {e}")
                            self.journal_table.blockSignals(False)
                            self.journal_table.setUpdatesEnabled(True)
                            self.journal_table.setSortingEnabled(True)
                            # Mettre à jour les statistiques
                            self.update_statistics(filtered_data)
                        
                        # Fin du bloc d'affichage des écritures du compte
                        # (le try ci‑dessus doit être suivi d'un except pour capturer les erreurs)
            except Exception as e:
                print(f"Erreur lors du chargement des écritures du compte: {e}")
                # Charger les sorties (dépenses) depuis event_expenses
                try:
                    from ayanna_erp.database.database_manager import DatabaseManager
                    db_manager = DatabaseManager()
                    session = db_manager.get_session()

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
                            'description': '',
                            'account_id': getattr(expense, 'account_id', None)  # Ajout du compte financier utilisé
                        }
                        self.journal_data.append(entry)

                except Exception as e:
                    print(f"Erreur lors du chargement des dépenses: {e}")
                finally:
                    try:
                        session.close()
                    except Exception:
                        pass
            
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
                        'description': f'Réservation #{payment.reservation_id}' if payment.reservation_id else '',
                        'account_id': getattr(payment, 'account_id', None)  # Ajout du compte financier utilisé si présent
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
        """Mettre à jour l'affichage du tableau et des statistiques (limite à 500 lignes)"""
        import logging
        logging.debug("Début update_journal_display")
        filtered_data = self.get_filtered_data()
        self.journal_table.setUpdatesEnabled(False)
        self.journal_table.blockSignals(True)
        self.journal_table.clearContents()
        self.journal_table.setRowCount(len(filtered_data))
        import time
        for row, entry in enumerate(filtered_data):
            t0 = time.time()
            try:
                # Date/Heure
                datetime_str = entry['datetime'].strftime("%d/%m/%Y %H:%M")
                self.journal_table.setItem(row, 0, QTableWidgetItem(datetime_str))
                # Type
                type_item = QTableWidgetItem(entry['type'])
                type_item.setForeground(Qt.GlobalColor.black)
                self.journal_table.setItem(row, 1, type_item)
                # Libellé
                self.journal_table.setItem(row, 2, QTableWidgetItem(entry['libelle']))
                # Montant Entrée (colonne 3)
                if entry['montant_entree'] > 0:
                    entree_item = QTableWidgetItem(self.format_amount(entry['montant_entree']))
                    entree_item.setForeground(Qt.GlobalColor.darkGreen)
                    entree_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    entree_item = QTableWidgetItem("-")
                    entree_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.journal_table.setItem(row, 3, entree_item)
                # Montant Sortie (colonne 4)
                if entry['montant_sortie'] > 0:
                    sortie_item = QTableWidgetItem(self.format_amount(entry['montant_sortie']))
                    sortie_item.setForeground(Qt.GlobalColor.darkRed)
                    sortie_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    sortie_item = QTableWidgetItem("-")
                    sortie_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.journal_table.setItem(row, 4, sortie_item)
            except Exception as e:
                print(f"[ERROR] Row {row} - Exception: {e}")
            t1 = time.time()
        self.journal_table.blockSignals(False)
        self.journal_table.setUpdatesEnabled(True)
        # Mettre à jour les statistiques
        self.update_statistics(filtered_data)
    
    def get_filtered_data(self):
        """Obtenir les données filtrées selon les critères, robustes aux erreurs de données."""
        filtered_data = self.journal_data.copy()

        # Filtre par compte caisse sélectionné
        if hasattr(self, 'financial_account_combo') and self.financial_account_combo.currentIndex() > 0:
            selected_account_id = self.financial_account_combo.currentData()
            if selected_account_id:
                # On suppose que chaque entrée a un champ 'account_id' ou similaire
                filtered_data = [entry for entry in filtered_data if entry.get('account_id') == selected_account_id]

        # Filtre par plage de dates (robuste)
        if hasattr(self, 'date_debut_filter') and hasattr(self, 'date_fin_filter'):
            qdate_debut = self.date_debut_filter.date()
            qdate_fin = self.date_fin_filter.date()
            start_date = date(qdate_debut.year(), qdate_debut.month(), qdate_debut.day())
            end_date = date(qdate_fin.year(), qdate_fin.month(), qdate_fin.day())
            print(f"[DEBUG] Filtrage date: start_date={start_date}, end_date={end_date}")
            safe_filtered = []
            for idx, entry in enumerate(filtered_data):
                dt = entry.get('datetime')
                libelle = entry.get('libelle')
                montant_entree = entry.get('montant_entree')
                montant_sortie = entry.get('montant_sortie')
                # Vérification des champs critiques
                if dt is None or not hasattr(dt, 'date'):
                    print(f"[WARNING] Entry {idx} ignorée: datetime manquant ou invalide: {dt}")
                    continue
                if libelle is None or not isinstance(libelle, str):
                    print(f"[WARNING] Entry {idx} ignorée: libellé manquant ou invalide: {libelle}")
                    continue
                try:
                    # Vérifier que les montants sont des nombres (float ou int)
                    float(montant_entree)
                    float(montant_sortie)
                except Exception:
                    print(f"[WARNING] Entry {idx} ignorée: montant_entree ou montant_sortie invalide: {montant_entree}, {montant_sortie}")
                    continue
                try:
                    d = dt.date()
                    if start_date <= d <= end_date:
                        safe_filtered.append(entry)
                except Exception as e:
                    print(f"[ERROR] Exception lors du filtrage de l'entrée {idx}: {e}")
                    continue  # Ignore les entrées corrompues
            filtered_data = safe_filtered

        # Filtre par type
        if hasattr(self, 'type_filter'):
            type_filter = self.type_filter.currentText()
            if type_filter == "Entrées":
                filtered_data = [entry for entry in filtered_data if entry.get('type') == 'Entrée']
            elif type_filter == "Sorties":
                filtered_data = [entry for entry in filtered_data if entry.get('type') == 'Sortie']
            # Si "Tous" est sélectionné, on ne filtre pas (on garde toutes les données)

        # Filtre par recherche
        if hasattr(self, 'search_edit'):
            search_text = self.search_edit.text().lower()
            if search_text:
                filtered_data = [entry for entry in filtered_data 
                               if search_text in str(entry.get('libelle', '')).lower()]

        return filtered_data
    
    def update_statistics(self, data):
        """Mettre à jour les statistiques affichées"""
        def safe_float(val):
            try:
                return float(val)
            except Exception:
                return 0.0

        # Filtrer par compte caisse sélectionné pour les stats aussi
        filtered_data = data
        if hasattr(self, 'financial_account_combo') and self.financial_account_combo.currentIndex() > 0:
            selected_account_id = self.financial_account_combo.currentData()
            if selected_account_id:
                filtered_data = [entry for entry in filtered_data if entry.get('account_id') == selected_account_id]

        total_entrees = sum(safe_float(entry.get('montant_entree', 0)) for entry in filtered_data)
        total_sorties = sum(safe_float(entry.get('montant_sortie', 0)) for entry in filtered_data)
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

    def get_account_global_balance(self, account_id):
        """Retourne le solde global (débit - crédit) pour un compte comptable donné."""
        try:
            from ayanna_erp.database.database_manager import get_database_manager
            from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaEcritures
            from sqlalchemy import func

            db_manager = get_database_manager()
            session = db_manager.SessionLocal()

            balance_expr = (func.coalesce(func.sum(ComptaEcritures.debit), 0) - func.coalesce(func.sum(ComptaEcritures.credit), 0))
            bal = session.query(balance_expr).filter(ComptaEcritures.compte_comptable_id == account_id).scalar()
            try:
                return float(bal or 0)
            except Exception:
                return None
        except Exception:
            return None
        finally:
            try:
                session.close()
            except Exception:
                pass
    
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

                # Nom du compte caisse sélectionné
                compte_caisse_name = "Tous les comptes"
                if hasattr(self, 'financial_account_combo') and self.financial_account_combo.currentIndex() > 0:
                    compte_caisse_name = self.financial_account_combo.currentText()
                elements.append(Paragraph(f"<b>Compte :</b> {compte_caisse_name}", styles['NormalText']))
                elements.append(Spacer(1, 0.3*cm))

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

                    # Préparer les lignes de statistiques pour le PDF
                    stats_data = [
                        ['Résumé de la période', ''],
                        ['Total Entrées:', format_amount_for_pdf(total_entrees, currency=currency_symbol)],
                        ['Total Sorties:', format_amount_for_pdf(total_sorties, currency=currency_symbol)],
                    ]

                    # Solde de la période
                    stats_data.append(['Solde:', format_amount_for_pdf(solde, currency=currency_symbol)])

                    # Si un compte financier est sélectionné, ajouter le solde global de ce compte
                    selected_account_id = None
                    try:
                        if hasattr(self, 'financial_account_combo') and self.financial_account_combo.currentIndex() > 0:
                            selected_account_id = self.financial_account_combo.currentData()
                    except Exception:
                        selected_account_id = None

                    if selected_account_id:
                        try:
                            global_balance = self.get_account_global_balance(selected_account_id) or 0
                            # Placer 'Solde global du compte' APRÈS la ligne 'Solde'
                            stats_data.append(['Solde global du compte:', format_amount_for_pdf(global_balance, currency=currency_symbol)])
                        except Exception:
                            # Ne pas bloquer l'export si le calcul échoue
                            pass

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

    def export_daily_report(self):
        """Exporter un rapport quotidien avec tableau Entrée/Sortie/Solde et graphique d'évolution"""
        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib.colors import HexColor, black, white
            from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, 
                                           Table, TableStyle, PageBreak, NextPageTemplate, 
                                           PageTemplate, BaseDocTemplate)
            from reportlab.platypus.frames import Frame
            from reportlab.graphics.shapes import Drawing, String
            from reportlab.graphics.charts.linecharts import HorizontalLineChart
            from reportlab.graphics.charts.legends import Legend
            from reportlab.graphics.widgets.markers import makeMarker
            from reportlab.lib.enums import TA_CENTER
            from reportlab.lib import colors
            from sqlalchemy import text
            import tempfile
            import os
            import subprocess
            import sys

            # Récupérer les dates sélectionnées
            date_debut = self.date_debut_filter.date().toPyDate()
            date_fin = self.date_fin_filter.date().toPyDate()
            
            if date_debut > date_fin:
                QMessageBox.warning(self, "Erreur", "La date de début doit être antérieure à la date de fin.")
                return

            # Récupérer le compte caisse sélectionné
            compte_id = None
            compte_caisse_name = "Tous les comptes"
            if hasattr(self, 'financial_account_combo') and self.financial_account_combo.currentIndex() > 0:
                compte_id = self.financial_account_combo.currentData()
                compte_caisse_name = self.financial_account_combo.currentText()
            
            if not compte_id:
                QMessageBox.warning(self, "Attention", "Veuillez sélectionner un compte caisse spécifique pour générer le rapport quotidien.")
                return

            # Préparer les données quotidiennes depuis les écritures comptables
            days_fr = {0: "Lun", 1: "Mar", 2: "Mer", 3: "Jeu", 4: "Ven", 5: "Sam", 6: "Dim"}
            rows = []
            current = date_debut
            
            from ayanna_erp.database.database_manager import DatabaseManager
            db_manager = DatabaseManager()
            
            while current <= date_fin:
                label = f"{days_fr.get(current.weekday(), '')} {current.strftime('%d/%m')}"
                
                day_start = datetime.combine(current, datetime.min.time())
                day_end = datetime.combine(current, datetime.max.time())
                
                entrees = 0.0
                sorties = 0.0
                
                try:
                    with db_manager.get_session() as session:
                        # Requête pour obtenir les totaux débit (entrées) et crédit (sorties) du compte pour ce jour
                        # Les écritures comptables : débit = entrée, crédit = sortie
                        query = text("""
                            SELECT 
                                COALESCE(SUM(ce.debit), 0) as total_debit,
                                COALESCE(SUM(ce.credit), 0) as total_credit
                            FROM compta_ecritures ce
                            JOIN compta_journaux cj ON ce.journal_id = cj.id
                            WHERE ce.compte_comptable_id = :compte_id
                            AND cj.date_operation >= :day_start
                            AND cj.date_operation <= :day_end
                        """)
                        result = session.execute(query, {
                            'compte_id': compte_id,
                            'day_start': day_start,
                            'day_end': day_end
                        }).fetchone()
                        
                        if result:
                            entrees = float(result.total_debit or 0)
                            sorties = float(result.total_credit or 0)
                except Exception as e:
                    print(f"Erreur requête écritures jour {current}: {e}")
                
                solde = entrees - sorties
                rows.append({
                    'label': label,
                    'entrees': entrees,
                    'sorties': sorties,
                    'solde': solde
                })
                
                current = current + timedelta(days=1)

            # Générer le PDF
            currency_symbol = self.get_currency_symbol()
            filename = self._generate_caisse_daily_report_pdf(rows, date_debut, date_fin, currency_symbol, compte_caisse_name)
            
            if filename and os.path.exists(filename):
                # Ouvrir le fichier
                try:
                    if sys.platform == 'win32':
                        os.startfile(filename)
                    elif sys.platform == 'darwin':
                        subprocess.run(['open', filename], check=False)
                    else:
                        subprocess.run(['xdg-open', filename], check=False)
                except Exception:
                    pass
                
                QMessageBox.information(self, "Export réussi",
                                       f"Le rapport quotidien a été exporté avec succès !\n\n"
                                       f"Fichier: {os.path.basename(filename)}")
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de générer le rapport PDF.")

        except Exception as e:
            print(f"❌ Erreur export rapport quotidien caisse: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible d'exporter le rapport: {str(e)}")

    def _generate_caisse_daily_report_pdf(self, rows, date_debut, date_fin, currency_symbol, compte_caisse_name="Tous les comptes"):
        """Générer le PDF du rapport quotidien caisse avec tableau et graphique"""
        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib.colors import HexColor, black, white
            from reportlab.platypus import (Paragraph, Spacer, Image, Table, TableStyle, 
                                           PageBreak, NextPageTemplate, PageTemplate, BaseDocTemplate)
            from reportlab.platypus.frames import Frame
            from reportlab.graphics.shapes import Drawing, String
            from reportlab.graphics.charts.linecharts import HorizontalLineChart
            from reportlab.graphics.charts.legends import Legend
            from reportlab.graphics.widgets.markers import makeMarker
            from reportlab.lib.enums import TA_CENTER
            from reportlab.lib import colors
            import tempfile
            import os

            # Créer le dossier d'export
            export_dir = os.path.join(os.getcwd(), "exports_caisse")
            os.makedirs(export_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(export_dir, f"rapport_caisse_{timestamp}.pdf")

            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='ReportTitle', fontSize=15, fontName='Helvetica-Bold', 
                                      alignment=TA_CENTER, spaceAfter=10))
            styles.add(ParagraphStyle(name='SmallInfo', fontSize=9, fontName='Helvetica', textColor="grey"))

            story = []

            # En-tête entreprise
            header_table, logo_path = self._build_company_header_for_report(styles)
            story.append(header_table)
            story.append(Spacer(1, 0.6*cm))

            # Titre
            story.append(Paragraph("RAPPORT QUOTIDIEN DE CAISSE", styles['ReportTitle']))
            story.append(Paragraph(f"<b>Compte :</b> {compte_caisse_name}", styles['Normal']))
            story.append(Paragraph(f"Période : <b>{date_debut.strftime('%d/%m/%Y')}</b> - <b>{date_fin.strftime('%d/%m/%Y')}</b>", 
                                  styles['Normal']))
            story.append(Spacer(1, 0.4*cm))

            # Fonction de formatage
            def fmt(amount):
                try:
                    formatted = f"{float(amount):,.0f}".replace(",", " ")
                    return f"{formatted} {currency_symbol or ''}"
                except:
                    return f"{amount} {currency_symbol or ''}"

            # Tableau des données
            headers = ["Date", "Entrées", "Sorties", "Solde"]
            data = [headers]
            totals = {'entrees': 0.0, 'sorties': 0.0, 'solde': 0.0}
            
            for r in rows:
                data.append([
                    r.get('label', ''),
                    fmt(r.get('entrees', 0)),
                    fmt(r.get('sorties', 0)),
                    fmt(r.get('solde', 0))
                ])
                totals['entrees'] += float(r.get('entrees', 0) or 0)
                totals['sorties'] += float(r.get('sorties', 0) or 0)
                totals['solde'] += float(r.get('solde', 0) or 0)

            data.append(["Total", fmt(totals['entrees']), fmt(totals['sorties']), fmt(totals['solde'])])

            table = Table(data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2C3E50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), HexColor('#eaeaea')),
                ('GRID', (0, 0), (-1, -1), 0.4, black),
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))

            story.append(table)
            story.append(Spacer(1, 0.6*cm))
            story.append(Paragraph(f"Informatisé par Ayanna Erp © - {datetime.now().strftime('%d/%m/%Y %H:%M')}", 
                                  styles['SmallInfo']))

            # Page graphique en paysage
            try:
                story.append(PageBreak())
                
                landscape_width, landscape_height = landscape(A4)
                landscape_content_width = landscape_width - 4*cm

                titre_graphique = f"Courbe d'évolution des Entrées et Sorties de Caisse du {date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')}"
                story.append(Paragraph(titre_graphique, styles['ReportTitle']))

                labels = [r.get('label', '') for r in rows]
                series_entrees = [float(r.get('entrees', 0) or 0) for r in rows]
                series_sorties = [float(r.get('sorties', 0) or 0) for r in rows]
                series_solde = [float(r.get('solde', 0) or 0) for r in rows]

                chart_margin_left = 70
                chart_margin_right = 30
                chart_margin_bottom = 50
                chart_height = 280
                chart_width = max(400, landscape_content_width - (chart_margin_left + chart_margin_right))

                d = Drawing(landscape_content_width, chart_height + chart_margin_bottom + 40)
                lc = HorizontalLineChart()
                lc.x = chart_margin_left
                lc.y = chart_margin_bottom
                lc.height = chart_height
                lc.width = chart_width
                lc.data = [series_entrees, series_sorties, series_solde]
                lc.categoryAxis.categoryNames = labels
                lc.categoryAxis.labels.angle = 25
                lc.categoryAxis.labels.boxAnchor = 'ne'
                lc.valueAxis.valueMin = min(0, min(series_solde) if series_solde else 0)

                # Formater les labels Y avec devise
                class CurrencyAxisLabelFormatter:
                    def __init__(self, currency):
                        self.currency = currency or ''
                    def __call__(self, value):
                        try:
                            formatted = f"{value:,.0f}".replace(",", " ")
                            return f"{formatted} {self.currency}".strip()
                        except:
                            return str(value)

                lc.valueAxis.labelTextFormat = CurrencyAxisLabelFormatter(currency_symbol)

                # Couleurs
                lc.lines[0].strokeColor = colors.HexColor('#27AE60')  # Entrées - Vert
                lc.lines[1].strokeColor = colors.HexColor('#E74C3C')  # Sorties - Rouge
                lc.lines[2].strokeColor = colors.HexColor('#3498DB')  # Solde - Bleu
                for i in range(len(lc.data)):
                    lc.lines[i].symbol = makeMarker('Circle')

                d.add(lc)

                # Légende
                legend = Legend()
                legend.alignment = 'right'
                legend.x = chart_margin_left + chart_width - 10
                legend.y = chart_margin_bottom + chart_height
                legend.boxAnchor = 'ne'
                legend.columnMaximum = 1
                legend.colorNamePairs = [
                    (lc.lines[0].strokeColor, "Entrées"),
                    (lc.lines[1].strokeColor, "Sorties"),
                    (lc.lines[2].strokeColor, "Solde"),
                ]
                d.add(legend)

                # Footer dans le graphique
                footer_text = f"Informatisé par Ayanna Erp © - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
                footer_string = String(landscape_content_width / 2, 10, footer_text,
                                       textAnchor='middle', fontSize=9, fillColor=colors.grey)
                d.add(footer_string)

                story.append(d)
            except Exception as e:
                print(f"Erreur graphique: {e}")
                story.append(Paragraph(f"(Graphique non disponible) - Informatisé par Ayanna Erp © - {datetime.now().strftime('%d/%m/%Y %H:%M')}", 
                                      styles['SmallInfo']))

            # Construire le PDF avec templates portrait + paysage
            doc = BaseDocTemplate(filename, pagesize=A4)

            frame_portrait = Frame(2*cm, 2*cm, A4[0] - 4*cm, A4[1] - 4*cm, id='portrait')
            landscape_page = landscape(A4)
            frame_landscape = Frame(2*cm, 2*cm, landscape_page[0] - 4*cm, landscape_page[1] - 4*cm, id='landscape')

            template_portrait = PageTemplate(id='Portrait', frames=[frame_portrait], pagesize=A4)
            template_landscape = PageTemplate(id='Landscape', frames=[frame_landscape], pagesize=landscape_page)

            doc.addPageTemplates([template_portrait, template_landscape])

            # Insérer NextPageTemplate avant le PageBreak
            story_final = []
            found_chart_break = False
            for elem in story:
                if isinstance(elem, PageBreak) and not found_chart_break:
                    story_final.append(NextPageTemplate('Landscape'))
                    story_final.append(elem)
                    found_chart_break = True
                else:
                    story_final.append(elem)

            doc.build(story_final)

            # Nettoyer le logo temporaire
            if logo_path and os.path.exists(logo_path):
                try:
                    os.unlink(logo_path)
                except:
                    pass

            return filename

        except Exception as e:
            print(f"❌ Erreur génération PDF rapport caisse: {e}")
            return None

    def _build_company_header_for_report(self, styles):
        """Construire l'en-tête entreprise pour le rapport"""
        try:
            from reportlab.platypus import Table, TableStyle, Image, Paragraph
            from reportlab.lib.units import cm
            import tempfile
            
            company_info = self.entreprise_controller.get_company_info_for_pdf()
            
            temp_logo = None
            logo_path = None
            header_data = []

            company_text = (
                f"<b>{company_info.get('name', 'AYANNA ERP')}</b><br/>"
                f"{company_info.get('address', '')}<br/>"
                f"{company_info.get('city', '')}<br/>"
                f"Tel: {company_info.get('phone', '')}"
            )

            if company_info.get('logo'):
                try:
                    temp_logo = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                    temp_logo.write(company_info['logo'])
                    logo_path = temp_logo.name
                    temp_logo.close()
                    logo = Image(logo_path, width=2.3*cm, height=2.3*cm)
                    header_data.append([logo, Paragraph(company_text, styles['Normal'])])
                except Exception:
                    header_data.append([Paragraph(company_text, styles['Normal']), ''])
            else:
                header_data.append([Paragraph(company_text, styles['Normal']), ''])

            header_table = Table(header_data, colWidths=[3*cm, 12*cm])
            header_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))

            return header_table, logo_path

        except Exception as e:
            print(f"Erreur construction en-tête: {e}")
            from reportlab.platypus import Paragraph
            return Paragraph("AYANNA ERP", styles['Normal']), None
