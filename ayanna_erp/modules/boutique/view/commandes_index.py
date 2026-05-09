"""
Widget pour l'affichage et la gestion des commandes du module Boutique
Vue uniquement - la logique métier est gérée par CommandeController
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                            QTableWidgetItem, QPushButton, QLabel, QDateEdit, 
                            QLineEdit, QComboBox, QGroupBox, QGridLayout, QFormLayout,
                            QHeaderView, QFrame, QSplitter, QMessageBox, QScrollArea, QDialog, QTextEdit, QAbstractItemView, QCheckBox, QDialogButtonBox,
                            QListWidget, QListWidgetItem)
from PyQt6.QtWidgets import QInputDialog
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor, QBrush
from datetime import datetime, timedelta
from decimal import Decimal
import os
import re
from ayanna_erp.modules.boutique.controller.commande_controller import CommandeController
from ayanna_erp.modules.boutique.controller.vente_controller import VenteController
from ayanna_erp.modules.boutique.view.modern_supermarket_widget import PaymentDialog
from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
from ayanna_erp.core.controllers.client_controller import ClientController

class CommandesIndexWidget(QWidget):
    """Widget principal pour l'affichage et gestion des commandes"""
    
    # Signaux
    commande_selected = pyqtSignal(int)  # ID de la commande sélectionnée
    
    def __init__(self, boutique_controller, current_user, module=None, parent=None):
        super().__init__(parent)
        self.boutique_controller = boutique_controller
        self.current_user = current_user
        self.parent_window = parent
        
        #Initialisation du controlleur client
        self.session = self.boutique_controller.session
        self.client_controller = ClientController(self.session)
        
        # module can be 'boutique' or 'restaurant' or None
        self.module = module
        
        # Initialiser le contrôleur des commandes
        self.commande_controller = CommandeController()
        
        # Initialiser le contrôleur de vente pour les annulations
        self.vente_controller = VenteController(self.boutique_controller.pos_id, self.current_user)
        
        # Initialiser le contrôleur entreprise pour les devises
        self.entreprise_controller = EntrepriseController()
        
        self.init_ui()
        self.load_commandes()

    def _is_admin(self):
        """Vérifie si l'utilisateur courant est super_admin ou admin"""
        if not self.current_user:
            return False
        if isinstance(self.current_user, dict):
            role = self.current_user.get('role', '')
        else:
            role = getattr(self.current_user, 'role', '')
        return role in ('super_admin', 'admin')

    def format_money(self, amount):
        """Formatage uniforme des montants avec espace milliers et suffixe de devise en minuscules."""
        try:
            from ayanna_erp.utils.formatting import format_amount as _fmt
            symbol = (self.entreprise_controller.get_currency_symbol() or '').lower()
            return f"{_fmt(amount)} {symbol}"
        except Exception:
            try:
                return f"{int(round(float(amount))):,}".replace(',', ' ') + f" {self.get_currency_symbol().lower()}"
            except Exception:
                return str(amount)
        
    def get_currency_symbol(self):
        """Récupère le symbole de devise depuis l'entreprise"""
        return self.entreprise_controller.get_currency_symbol()
        
    def init_ui(self):
        """Initialisation de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)
        
        # Zone de filtres et recherche
        self.create_filters_section(layout)
        
        # Splitter principal : tableau à gauche, détails à droite
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(main_splitter)
        
        # Tableau des commandes (côté gauche)
        table_widget = self.create_commandes_table()
        main_splitter.addWidget(table_widget)
        
        # Zone de détails (côté droit)
        details_widget = self.create_details_section()
        main_splitter.addWidget(details_widget)
        
        # Définir les proportions (70% tableau, 30% détails)
        main_splitter.setSizes([700, 300])
        
        # Zone de statistiques (texte formaté) - en bas
        period_stats = QHBoxLayout()
        period_label = QLabel("📊 Statistiques de la période")
        period_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        period_stats.addWidget(period_label)

        self.stats_text = QLabel()
        self.stats_text.setStyleSheet("font-family: monospace; font-size: 11px;")
        # initialisation du texte de stats
        try:
            self.update_period_stats()
        except Exception:
            pass
        period_stats.addWidget(self.stats_text)
        period_stats.addStretch()
        layout.addLayout(period_stats)

        
    def create_filters_section(self, layout):
        """Créer la section des filtres et recherche"""
        filters_group = QGroupBox("🔍 Filtres et Recherche")
        filters_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        filters_layout = QGridLayout(filters_group)

        # Filtre par dates
        filters_layout.addWidget(QLabel("Du :"), 0, 0)
        # Par défaut, afficher uniquement les commandes du jour : date_debut == date_fin == aujourd'hui
        self.date_debut = QDateEdit(QDate.currentDate())
        self.date_debut.setCalendarPopup(True)
        self.date_debut.dateChanged.connect(self.filter_commandes)
        if not self._is_admin():
            self.date_debut.setEnabled(False)
        filters_layout.addWidget(self.date_debut, 0, 1)

        filters_layout.addWidget(QLabel("Au :"), 0, 2)
        self.date_fin = QDateEdit(QDate.currentDate())
        self.date_fin.setCalendarPopup(True)
        self.date_fin.dateChanged.connect(self.filter_commandes)
        if not self._is_admin():
            self.date_fin.setEnabled(False)
        filters_layout.addWidget(self.date_fin, 0, 3)
        
        # Recherche
        filters_layout.addWidget(QLabel("Recherche :"), 1, 0)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Chercher par client, produit, numéro commande...")
        # Ajouter un délai pour éviter les appels trop fréquents
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.filter_commandes)
        self.search_input.textChanged.connect(lambda: self.search_timer.start(300))  # 300ms de délai
        filters_layout.addWidget(self.search_input, 1, 1, 1, 2)
        
        # Filtre par statut paiement
        filters_layout.addWidget(QLabel("Paiement :"), 1, 3)
        self.payment_filter = QComboBox()
        self.payment_filter.addItem("Tous")
        try:
            from ayanna_erp.core.view.payment_mode_widget import get_active_payment_modes
            for m in get_active_payment_modes():
                self.payment_filter.addItem(m['label'])
        except Exception:
            self.payment_filter.addItems(["Espèces", "Banque", "Mobile Money", "Crédit"])
        self.payment_filter.currentTextChanged.connect(self.filter_commandes)
        filters_layout.addWidget(self.payment_filter, 1, 4)

        # Filtre par statut 'Prêt'
        filters_layout.addWidget(QLabel("Prêt :"), 2, 0)
        self.pret_filter = QComboBox()
        self.pret_filter.addItems(["Tous", "Oui", "Non"])
        self.pret_filter.currentTextChanged.connect(self.filter_commandes)
        filters_layout.addWidget(self.pret_filter, 2, 1)

        # Filtre par statut 'Livré'
        filters_layout.addWidget(QLabel("Livré :"), 2, 2)
        self.livre_filter = QComboBox()
        self.livre_filter.addItems(["Tous", "Oui", "Non"])
        self.livre_filter.currentTextChanged.connect(self.filter_commandes)
        filters_layout.addWidget(self.livre_filter, 2, 3)
        
        # Boutons d'action
        actions_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.clicked.connect(self.load_commandes)
        refresh_btn.setStyleSheet("QPushButton { padding: 8px 15px; }")
        
        export_btn = QPushButton("📊 Export Commandes")
        export_btn.clicked.connect(self.export_commandes)
        export_btn.setStyleSheet("QPushButton { padding: 8px 15px; }")
        export_products_btn = QPushButton("📦 Export produits")
        export_products_btn.clicked.connect(self.export_products_sold)
        export_products_btn.setStyleSheet("QPushButton { padding: 8px 15px; }")
        export_report_btn = QPushButton("📑 Export rapport")
        export_report_btn.clicked.connect(self.export_daily_report)
        export_report_btn.setStyleSheet("QPushButton { padding: 8px 15px; }")
        
        actions_layout.addWidget(refresh_btn)
        actions_layout.addWidget(export_btn)
        if self._is_admin():
            actions_layout.addWidget(export_products_btn)
            actions_layout.addWidget(export_report_btn)
        actions_layout.addStretch()
        
        filters_layout.addLayout(actions_layout, 2, 0, 1, 5)
        
        layout.addWidget(filters_group)
        
    def create_commandes_table(self):
        """Créer le tableau des commandes"""
        self.commandes_table = QTableWidget()
        # Colonnes : N° Commande, Date, Client, Produits/Services, Sous-total, Remise, Total, Payé, Paiement, Prêt, Livré
        self.commandes_table.setColumnCount(11)
        self.commandes_table.setHorizontalHeaderLabels([
            "N° Commande", "Date", "Client", "Produits / Services", 
            "Sous-total", "Remise", "Total", "Payé", "Paiement", "Prêt", "Livré"
        ])

        
        # Configuration du tableau
        header = self.commandes_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # N° Commande
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Date
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)           # Client
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)           # Produits
        
        self.commandes_table.setAlternatingRowColors(True)
        self.commandes_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        # Sélection claire et unique pour que le clic soit visible
        try:
            self.commandes_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        except Exception:
            pass
        self.commandes_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.commandes_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                background-color: white;
            }
            QTableWidget::item:selected {
                background-color: #bbdefb; /* bleu clair */
                color: #0b2545; /* texte sombre pour contraste */
            }
            QTableWidget::item:selected:!active {
                background-color: #bbdefb;
                color: #0b2545;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                font-weight: bold;
                border: 1px solid #ddd;
            }
        """)
        # Désactiver l'édition directe dans le tableau des commandes
        try:
            self.commandes_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        except Exception:
            # Fallback pour différentes versions de PyQt
            from PyQt6.QtWidgets import QAbstractItemView
            self.commandes_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # Connecter les signaux
        self.commandes_table.itemSelectionChanged.connect(self.on_commande_selected)
        # Double-clic pour marquer Prêt / Livré
        try:
            self.commandes_table.cellDoubleClicked.connect(self.on_commande_double_clicked)
        except Exception:
            try:
                self.commandes_table.itemDoubleClicked.connect(self.on_commande_double_clicked)
            except Exception:
                pass
        
        return self.commandes_table
    
    def create_details_section(self):
        """Créer la section de détails des commandes"""
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(10, 10, 10, 10)
        details_layout.setSpacing(15)
        
        # Titre de la section
        title_label = QLabel("📋 Détails de la commande")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #1976D2;
                padding: 10px;
                background-color: #E3F2FD;
                border-radius: 6px;
            }
        """)
        details_layout.addWidget(title_label)
        
        # Scroll area pour les détails
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
            }
        """)
        
        # Contenu scrollable
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(10, 10, 10, 10)
        scroll_layout.setSpacing(15)
        self.details_info = QGroupBox("Informations générales")
        self.details_info.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        info_layout = QFormLayout(self.details_info)
        
        self.detail_numero = QLabel("-")
        self.detail_date = QLabel("-")
        self.detail_client = QLabel("-")
        self.detail_utilisateur = QLabel("-")  # Utilisateur qui a passé la commande
        # Champs spécifiques au module Restaurant
        self.detail_table = QLabel("-")
        self.detail_salle = QLabel("-")
        self.detail_serveuse = QLabel("-")
        self.detail_sous_total = QLabel("-")
        self.detail_remise = QLabel("-")
        self.detail_total = QLabel("-")
        self.detail_paye = QLabel("-")
        self.detail_restant = QLabel("-")
        self.detail_statut = QLabel("-")
        
        info_layout.addRow("N° Commande:", self.detail_numero)
        info_layout.addRow("Date:", self.detail_date)
        info_layout.addRow("Client:", self.detail_client)
        info_layout.addRow("Utilisateur:", self.detail_utilisateur)  # Ajout utilisateur
        # Ajouter les informations restaurant si nécessaire
        info_layout.addRow("Table:", self.detail_table)
        info_layout.addRow("Salle:", self.detail_salle)
        info_layout.addRow("Serveuse:", self.detail_serveuse)
        info_layout.addRow("Sous-total:", self.detail_sous_total)
        info_layout.addRow("Remise:", self.detail_remise)
        info_layout.addRow("Total:", self.detail_total)
        info_layout.addRow("Payé:", self.detail_paye)
        info_layout.addRow("Restant:", self.detail_restant)
        info_layout.addRow("Statut:", self.detail_statut)
        
        scroll_layout.addWidget(self.details_info)
        
        # Liste des produits/services
        products_group = QGroupBox("Produits / Services")
        products_layout = QVBoxLayout(products_group)
        
        self.products_list = QLabel("Sélectionnez une commande pour voir les détails")
        self.products_list.setWordWrap(True)
        self.products_list.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #f9f9f9;
                border-radius: 4px;
                min-height: 60px;
            }
        """)
        products_layout.addWidget(self.products_list)
        
        scroll_layout.addWidget(products_group)
        
        # Section notes sur la commande
        notes_group = QGroupBox("📝 Notes sur la commande")
        notes_layout = QVBoxLayout(notes_group)
        
        self.detail_notes = QLabel("Aucune note")
        self.detail_notes.setWordWrap(True)
        self.detail_notes.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #f9f9f9;
                border-radius: 4px;
                min-height: 60px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
            }
        """)
        notes_layout.addWidget(self.detail_notes)
        
        scroll_layout.addWidget(notes_group)
        
        # Boutons d'action
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)
        actions_layout.setSpacing(10)
        
        self.pay_button = QPushButton("💳 Payer")
        self.pay_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.pay_button.clicked.connect(self.on_pay_commande)
        self.pay_button.setEnabled(False)
        actions_layout.addWidget(self.pay_button)
        
        self.print_button = QPushButton("🖨️ Imprimer")
        self.print_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.print_button.clicked.connect(self.on_print_commande)
        self.print_button.setEnabled(False)
        actions_layout.addWidget(self.print_button)
        
        # Bouton d'annulation
        self.cancel_button = QPushButton("❌ Annuler")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
        """)
        self.cancel_button.clicked.connect(self.on_cancel_commande)
        self.cancel_button.setEnabled(False)
        actions_layout.addWidget(self.cancel_button)
        
        # Bouton WhatsApp
        self.btn_whatsapp = QPushButton("📱 Envoyer via WhatsApp")
        self.btn_whatsapp.setStyleSheet("""
            QPushButton {
                background-color: #25D366;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1DA851;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
        """)
        self.btn_whatsapp.clicked.connect(self.send_whatsapp_message)
        self.btn_whatsapp.setEnabled(False)
        actions_layout.addWidget(self.btn_whatsapp)

        
        scroll_layout.addWidget(actions_group)
        
        # Espacement
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        details_layout.addWidget(scroll_area)
        
        return details_widget
        
    def load_commandes(self):
        """Charger les commandes depuis le contrôleur"""
        try:
            # Récupérer les filtres actuels
            date_debut = self.date_debut.date().toPyDate() if hasattr(self, 'date_debut') else None
            date_fin = self.date_fin.date().toPyDate() if hasattr(self, 'date_fin') else None
            search_term = self.search_input.text().strip() if hasattr(self, 'search_input') and self.search_input.text().strip() else None
            payment_filter = self.payment_filter.currentText() if hasattr(self, 'payment_filter') else None
            
            # Utiliser le contrôleur pour récupérer les commandes
            commandes = self.commande_controller.get_commandes(
                date_debut=date_debut,
                date_fin=date_fin,
                search_term=search_term,
                payment_filter=payment_filter
            )
            
            self.populate_table(commandes)
            self.update_statistics(commandes)
            
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des commandes: {e}")
            print(f"❌ Erreur load_commandes: {e}")
                
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des commandes: {e}")
            print(f"❌ Erreur load_commandes: {e}")
            
    def populate_table(self, commandes):
        """Remplir le tableau avec les commandes"""
        # Appliquer filtres locaux (pret / livre) avant d'afficher
        def flag_val(c, keys):
            for k in keys:
                v = c.get(k)
                if v is not None:
                    return bool(v)
            return False

        pret_sel = getattr(self, 'pret_filter', None).currentText() if hasattr(self, 'pret_filter') else 'Tous'
        livre_sel = getattr(self, 'livre_filter', None).currentText() if hasattr(self, 'livre_filter') else 'Tous'

        filtered = []
        for c in commandes:
            is_pret = flag_val(c, ('is_ready', 'pret', 'ready'))
            is_livre = flag_val(c, ('is_delivered', 'livre', 'delivered'))

            ok_pret = (pret_sel == 'Tous') or (pret_sel == 'Oui' and is_pret) or (pret_sel == 'Non' and not is_pret)
            ok_livre = (livre_sel == 'Tous') or (livre_sel == 'Oui' and is_livre) or (livre_sel == 'Non' and not is_livre)

            if ok_pret and ok_livre:
                # enrich with normalized flags for easier use later
                c['_is_pret'] = is_pret
                c['_is_livre'] = is_livre
                filtered.append(c)

        self.commandes_table.setRowCount(len(filtered))

        for row, commande in enumerate(filtered):
            # N° Commande
            numero_text = str(commande.get('numero_commande') or f"CMD-{commande.get('id')}")
            numero_item = QTableWidgetItem(numero_text)
            # Stocker l'ID réel dans l'item (UserRole) pour récupération sûre
            # IMPORTANT: Inclure aussi le module (boutique/restaurant) pour éviter les conflits d'ID
            panier_id = commande.get('id')
            module = commande.get('module', 'boutique')
            
            # Stocker les données comme tuple (panier_id, module) pour éviter les collisions
            try:
                numero_item.setData(Qt.ItemDataRole.UserRole, (panier_id, module))
            except Exception:
                try:
                    numero_item.setData(Qt.ItemDataRole.UserRole, panier_id)
                except Exception:
                    pass
            self.commandes_table.setItem(row, 0, numero_item)

            # Date
            date_str = ""
            created_at = commande.get('created_at')
            if created_at:
                if isinstance(created_at, str):
                    try:
                        from datetime import datetime
                        date_obj = datetime.strptime(created_at[:19], "%Y-%m-%d %H:%M:%S")
                        date_str = date_obj.strftime("%d/%m/%Y %H:%M")
                    except:
                        date_str = created_at[:16]
                else:
                    date_str = created_at.strftime("%d/%m/%Y %H:%M")
            date_item = QTableWidgetItem(date_str)
            self.commandes_table.setItem(row, 1, date_item)

            # Client
            client_item = QTableWidgetItem(str(commande.get('client_name', '')))
            self.commandes_table.setItem(row, 2, client_item)

            # Produits et services (déjà concaténés dans commande['produits'])
            items_text = commande.get('produits', 'Aucun produit/service')
            if len(items_text) > 100:
                items_text = items_text[:97] + '...'
            items_item = QTableWidgetItem(items_text)
            self.commandes_table.setItem(row, 3, items_item)

            # Sous-total
            subtotal_item = QTableWidgetItem(self.format_money(commande.get('subtotal', 0)))
            self.commandes_table.setItem(row, 4, subtotal_item)

            # Remise
            remise_item = QTableWidgetItem(self.format_money(commande.get('remise_amount', 0)))
            self.commandes_table.setItem(row, 5, remise_item)

            # Total
            total_item = QTableWidgetItem(self.format_money(commande.get('total_final', 0)))
            if commande.get('payment_method') == 'Crédit':
                total_item.setBackground(QColor("#ffecb3"))
            self.commandes_table.setItem(row, 6, total_item)

            # Payé (montant déjà payé)
            montant_paye = commande.get('montant_paye', 0)
            paye_item = QTableWidgetItem(self.format_money(montant_paye))
            if montant_paye >= commande.get('total_final', 0):
                paye_item.setBackground(QColor("#c8e6c9"))  # Vert pour soldé
            elif montant_paye > 0:
                paye_item.setBackground(QColor("#fff3e0"))  # Orange pour partiellement payé
            self.commandes_table.setItem(row, 7, paye_item)

            # Paiement
            payment_item = QTableWidgetItem(str(commande.get('payment_method', '')))
            if commande.get('payment_method') == 'Crédit':
                payment_item.setBackground(QColor("#ffcdd2"))
            self.commandes_table.setItem(row, 8, payment_item)
            # Colonne 'Prêt'
            try:
                pret_val = commande.get('_is_pret', False)
                pret_item = QTableWidgetItem("Oui" if pret_val else "Non")
                if pret_val:
                    pret_item.setBackground(QColor('#e8f5e9'))
                else:
                    pret_item.setBackground(QColor('#ffffff'))
                self.commandes_table.setItem(row, 9, pret_item)
            except Exception:
                pass

            # Colonne 'Livré'
            try:
                livre_val = commande.get('_is_livre', False)
                livre_item = QTableWidgetItem("Oui" if livre_val else "Non")
                if livre_val:
                    livre_item.setBackground(QColor('#e3f2fd'))
                else:
                    livre_item.setBackground(QColor('#ffffff'))
                self.commandes_table.setItem(row, 10, livre_item)
            except Exception:
                pass

            # Si la commande est annulée, appliquer un style grisé / barré
            status = commande.get('status', '')
            try:
                if status in ('cancelled', 'annule', 'annulé', 'annulee'):
                    # Style gris pour tous les items de la ligne
                    gray_brush = QBrush(QColor('#9e9e9e'))
                    strike_font = QFont()
                    strike_font.setStrikeOut(True)

                    for col in range(self.commandes_table.columnCount()):
                        it = self.commandes_table.item(row, col)
                        if it is not None:
                            try:
                                it.setForeground(gray_brush)
                            except Exception:
                                pass
                            try:
                                f = it.font()
                                f.setStrikeOut(True)
                                it.setFont(f)
                            except Exception:
                                pass
                    # Optionnel: modifier le texte du numéro pour indiquer l'état
                    try:
                        numero_item.setText(numero_item.text() + ' (ANNULÉE)')
                    except Exception:
                        pass
            except Exception:
                pass
        
    def update_statistics(self, commandes):
        """Mettre à jour les statistiques"""
        if not commandes:
            return
            
        # Utiliser le contrôleur pour calculer les statistiques
        stats = self.commande_controller.get_commandes_statistics(commandes)
        
        # Sécurité: s'assurer que les créances ne sont jamais négatives
        stats['total_creances'] = max(0.0, float(stats.get('total_creances', 0)))
        
        # Mise à jour des widgets de stats
        if hasattr(self, 'stat_widgets'):
            self.stat_widgets.get('commandes_aujourd\'hui', QLabel()).setText(str(stats['commandes_aujourd_hui']))
            self.stat_widgets.get('total_ca', QLabel()).setText(self.format_money(stats['total_ca']))
            self.stat_widgets.get('créances', QLabel()).setText(self.format_money(stats['total_creances']))
            
        self.update_period_stats(commandes)
        
    def update_period_stats(self, commandes=None):
        """Met à jour les statistiques de période avec synthèse CA/remises/total vente."""
        try:
            from datetime import datetime, time
            if hasattr(self, 'date_debut'):
                d1 = self.date_debut.date().toPyDate()
                d1 = datetime.combine(d1, time.min)
            else:
                d1 = None
            if hasattr(self, 'date_fin'):
                d2 = self.date_fin.date().toPyDate()
                d2 = datetime.combine(d2, time.max)
            else:
                d2 = None
            # Inclure la recherche et le filtre paiement dans les stats de période
            search_term = self.search_input.text().strip() if hasattr(self, 'search_input') and self.search_input.text().strip() else None
            payment_filter = self.payment_filter.currentText() if hasattr(self, 'payment_filter') else None
            stats = self.commande_controller.get_period_commandes_stats(d1, d2, search_term=search_term, payment_filter=payment_filter)
            # Calcul CA et remises à partir de subtotal/remise_amount
            ca = 0
            total_remises = 0
            try:
                from sqlalchemy import text as sq_text
                from ayanna_erp.database.database_manager import DatabaseManager
                db_manager = DatabaseManager()
                with db_manager.get_session() as session:
                    # CA = SUM(subtotal) boutique + restau
                    # Construire conditions dynamiques (shop)
                    cond_shop = ["created_at >= :d1", "created_at <= :d2", "LOWER(COALESCE(status,'')) NOT IN ('cancelled', 'annule', 'canceled')"]
                    params = {'d1': d1, 'd2': d2}
                    if payment_filter and payment_filter != 'Tous':
                        cond_shop.append("payment_method = :payment_method")
                        params['payment_method'] = payment_filter
                    if search_term:
                        cond_shop.append("(numero_commande LIKE :search OR EXISTS (SELECT 1 FROM shop_clients sc WHERE sc.id = shop_paniers.client_id AND (sc.nom LIKE :search OR sc.prenom LIKE :search)) OR EXISTS (SELECT 1 FROM shop_paniers_products spp JOIN core_products cp ON spp.product_id = cp.id WHERE spp.panier_id = shop_paniers.id AND cp.name LIKE :search) OR EXISTS (SELECT 1 FROM shop_paniers_services sps JOIN shop_services ss ON sps.service_id = ss.id WHERE sps.panier_id = shop_paniers.id AND ss.name LIKE :search))")
                        params['search'] = f"%{search_term}%"
                    q_ca1 = sq_text(f"SELECT COALESCE(SUM(subtotal),0) as ca FROM shop_paniers WHERE {' AND '.join(cond_shop)}")
                    ca1 = session.execute(q_ca1, params).fetchone()
                    ca += float(ca1.ca) if ca1.ca is not None else 0
                    # Construire conditions dynamiques (restau)
                    cond_restau = ["created_at >= :d1", "created_at <= :d2", "LOWER(COALESCE(status,'')) NOT IN ('annule', 'annulé', 'cancelled', 'canceled')"]
                    params2 = {'d1': d1, 'd2': d2}
                    if payment_filter and payment_filter != 'Tous':
                        cond_restau.append("payment_method = :payment_method")
                        params2['payment_method'] = payment_filter
                    if search_term:
                        cond_restau.append("(CAST(id AS TEXT) LIKE :search OR EXISTS (SELECT 1 FROM shop_clients sc WHERE sc.id = restau_paniers.client_id AND (sc.nom LIKE :search OR sc.prenom LIKE :search)) OR EXISTS (SELECT 1 FROM restau_produit_panier rpp JOIN core_products cp ON rpp.product_id = cp.id WHERE rpp.panier_id = restau_paniers.id AND cp.name LIKE :search))")
                        params2['search'] = f"%{search_term}%"
                    q_ca2 = sq_text(f"SELECT COALESCE(SUM(subtotal),0) as ca FROM restau_paniers WHERE {' AND '.join(cond_restau)}")
                    ca2 = session.execute(q_ca2, params2).fetchone()
                    ca += float(ca2.ca) if ca2.ca is not None else 0
                    # Remises = SUM(remise_amount) boutique + restau
                    q1 = sq_text(f"SELECT COALESCE(SUM(remise_amount),0) as total_remise FROM shop_paniers WHERE {' AND '.join(cond_shop)}")
                    r1 = session.execute(q1, params).fetchone()
                    total_remises += float(r1.total_remise) if r1.total_remise is not None else 0
                    q2 = sq_text(f"SELECT COALESCE(SUM(remise_amount),0) as total_remise FROM restau_paniers WHERE {' AND '.join(cond_restau)}")
                    r2 = session.execute(q2, params2).fetchone()
                    total_remises += float(r2.total_remise) if r2.total_remise is not None else 0
            except Exception as e:
                print(f"Erreur récupération CA/remises: {e}")
                ca = 0
                total_remises = 0
            total_vente = ca - total_remises
            # Affichage synthèse
            stats_text = f"""
Période: {self.date_debut.date().toString('dd/MM/yyyy')} - {self.date_fin.date().toString('dd/MM/yyyy')}
Commandes: {stats.get('nb_commandes', 0)}
Commandes Non Payées: {stats.get('nb_creances', 0)}
Chiffre d'affaires: {ca:,.0f} {self.get_currency_symbol()}
Remises: {total_remises:,.0f} {self.get_currency_symbol()}
Total vente: {total_vente:,.0f} {self.get_currency_symbol()}
Montant Créances: {stats.get('total_creances', 0):,.0f} {self.get_currency_symbol()}
Montant Espèces: {stats.get('total_paid', 0):,.0f} {self.get_currency_symbol()}
            """
            self.stats_text.setText(stats_text.strip())
        except Exception as e:
            print(f"❌ Erreur update_period_stats: {e}")
        
    def filter_commandes(self):
        """Filtrer les commandes selon les critères actuels"""
        try:
            # Récupérer les filtres actuels
            date_debut = self.date_debut.date().toPyDate() if hasattr(self, 'date_debut') else None
            date_fin = self.date_fin.date().toPyDate() if hasattr(self, 'date_fin') else None
            search_term = self.search_input.text().strip() if hasattr(self, 'search_input') and self.search_input.text().strip() else None
            payment_filter = self.payment_filter.currentText() if hasattr(self, 'payment_filter') else None

            # Utiliser le contrôleur pour récupérer les commandes filtrées
            commandes = self.commande_controller.get_commandes(
                date_debut=date_debut,
                date_fin=date_fin,
                search_term=search_term,
                payment_filter=payment_filter
            )

            # Mettre à jour le tableau sans déclencher de signaux problématiques
            self.commandes_table.setRowCount(0)  # Vider le tableau proprement
            self.populate_table(commandes)
            self.update_statistics(commandes)

        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du filtrage des commandes: {e}")
            print(f"❌ Erreur filter_commandes: {e}")
        
    def on_commande_selected(self):
        """Gérer la sélection d'une commande dans le tableau"""
        selected_rows = self.commandes_table.selectionModel().selectedRows()
        if not selected_rows:
            self.clear_details()
            return
            
        row = selected_rows[0].row()
        
        # Récupérer d'abord l'ID et le MODULE stockés dans l'item (UserRole) si présent
        commande_id = None
        commande_module = 'boutique'  # Default
        try:
            item0 = self.commandes_table.item(row, 0)
            if item0 is not None:
                # essayer UserRole (peut être un tuple (panier_id, module) ou juste panier_id)
                try:
                    data = item0.data(Qt.ItemDataRole.UserRole)
                    
                    if isinstance(data, tuple) and len(data) == 2:
                        # C'est un tuple (panier_id, module)
                        commande_id, commande_module = data
                    else:
                        # C'est juste l'ID
                        commande_id = data
                except Exception:
                    commande_id = None
                
                # Si pas trouvé dans data(), essayer le texte et extraire l'entier
                if commande_id in (None, ''):
                    txt = item0.text() if item0.text() is not None else ''
                    # extraire le premier groupe de chiffres
                    m = re.search(r"(\d+)", txt)
                    if m:
                        try:
                            commande_id = int(m.group(1))
                        except Exception:
                            commande_id = txt
                    else:
                        commande_id = txt
            else:
                # fallback via model index
                try:
                    idx = self.commandes_table.model().index(row, 0)
                    commande_id = idx.data()
                except Exception:
                    commande_id = None
        except Exception:
            commande_id = None

        # Valider l'ID obtenu
        if commande_id in (None, '', []):
            QMessageBox.warning(self, "Sélection invalide", "Impossible de récupérer l'identifiant de la commande sélectionnée.")
            self.clear_details()
            return
        
        # Récupérer les détails de la commande
        try:
            commande_details = self.commande_controller.get_commande_details(commande_id, module=commande_module)
            if commande_details:
                self.update_details(commande_details)
            else:
                self.clear_details()
        except Exception as e:
            print(f"Erreur lors de la récupération des détails: {e}")
            self.clear_details()
            
        
    
    def update_details(self, commande):
        """Mettre à jour la zone de détails avec les informations de la commande"""
        def _as_bool(v):
            if isinstance(v, str):
                return v.strip().lower() in ('1', 'true', 'oui', 'yes')
            return bool(v)

        self.detail_numero.setText(str(commande.get('numero_commande') or f"CMD-{commande.get('id')}"))
        
        # Date
        created_at = commande.get('created_at')
        if created_at:
            if isinstance(created_at, str):
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(created_at[:19], "%Y-%m-%d %H:%M:%S")
                    date_str = date_obj.strftime("%d/%m/%Y %H:%M")
                except:
                    date_str = created_at[:16]
            else:
                date_str = created_at.strftime("%d/%m/%Y %H:%M")
        else:
            date_str = "-"
        self.detail_date.setText(date_str)
        
        self.detail_client.setText(str(commande.get('client_name', '-')))
        
        # Afficher le nom de l'utilisateur qui a passé la commande
        user_name = commande.get('user_name') or commande.get('comptoiriste_name') or '-'
        self.detail_utilisateur.setText(str(user_name))
        
        # Si commande restaurant et client non renseigné, afficher fallback
        if commande.get('module') == 'restaurant' and not commande.get('client_name'):
            client_id = commande.get('client_id') or commande.get('client') or None
            if client_id:
                self.detail_client.setText(f"Client #{client_id}")
            else:
                self.detail_client.setText("Client restaurant")
        # Afficher les métadonnées Restaurant si présentes
        if commande.get('module') == 'restaurant':
            self.detail_table.setText(str(commande.get('table_number') or commande.get('table') or '-'))
            self.detail_salle.setText(str(commande.get('salle_name') or commande.get('salle') or '-'))
            # serveuse peut être fournie sous serveuse_name ou waiter_name
            self.detail_serveuse.setText(str(commande.get('serveuse_name') or commande.get('serveuse') or commande.get('waiter_name') or '-'))
        else:
            # Cacher/mettre par défaut pour les commandes boutique
            self.detail_table.setText('-')
            self.detail_salle.setText('-')
            self.detail_serveuse.setText('-')
        self.detail_sous_total.setText(self.format_money(commande.get('subtotal', 0)))
        self.detail_remise.setText(self.format_money(commande.get('remise_amount', 0)))
        self.detail_total.setText(self.format_money(commande.get('total_final', 0)))
        
        montant_paye = commande.get('montant_paye', 0)
        total_final = commande.get('total_final', 0)
        restant = total_final - montant_paye
        is_finalized_locked = _as_bool(commande.get('pret') if commande.get('pret') is not None else commande.get('is_ready')) and _as_bool(commande.get('livre') if commande.get('livre') is not None else commande.get('is_delivered'))
        
        self.detail_paye.setText(self.format_money(montant_paye))
        self.detail_restant.setText(self.format_money(restant))
        
        # Statut de paiement
        if montant_paye >= total_final:
            self.detail_statut.setText("✅ Soldé")
            self.detail_statut.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.pay_button.setEnabled(False)
            self.pay_button.setText("💳 Soldé")
        elif montant_paye > 0:
            self.detail_statut.setText("⏳ Partiellement payé")
            self.detail_statut.setStyleSheet("color: #FF9800; font-weight: bold;")
            self.pay_button.setEnabled(True)
            self.pay_button.setText("💳 Payer le restant")
        else:
            self.detail_statut.setText("❌ Non payé")
            self.detail_statut.setStyleSheet("color: #f44336; font-weight: bold;")
            self.pay_button.setEnabled(True)
            self.pay_button.setText("💳 Payer")
        
        # Produits/Services
        produits_text = commande.get('produits_detail', 'Aucun détail disponible')
        self.products_list.setText(produits_text)
        
        # Notes sur la commande
        notes_value = commande.get('notes')
        notes_text = str(notes_value).strip() if notes_value is not None else ''
        if notes_text:
            self.detail_notes.setText(notes_text)
            self.detail_notes.setStyleSheet("""
                QLabel {
                    padding: 10px;
                    background-color: #f9f9f9;
                    border-radius: 4px;
                    min-height: 60px;
                    font-family: 'Segoe UI', sans-serif;
                    font-size: 11px;
                    color: #333;
                }
            """)
        else:
            self.detail_notes.setText("Aucune note")
            self.detail_notes.setStyleSheet("""
                QLabel {
                    padding: 10px;
                    background-color: #f9f9f9;
                    border-radius: 4px;
                    min-height: 60px;
                    font-family: 'Segoe UI', sans-serif;
                    font-size: 11px;
                    color: #999;
                    font-style: italic;
                }
            """)
        
        # Activer les boutons
        self.print_button.setEnabled(True)
        
        # Gérer le bouton d'annulation selon le statut
        status = commande.get('status', '')
        is_cancelled = status in ('cancelled', 'annule', 'annulé', 'annulee')
        if status == 'cancelled':
            self.cancel_button.setEnabled(False)
            self.cancel_button.setText("❌ Déjà annulée")
            # Désactiver aussi les autres boutons pour une commande annulée
            self.pay_button.setEnabled(False)
            self.pay_button.setText("💳 Annulée")
        elif status == 'annule':
            self.cancel_button.setEnabled(False)
            self.cancel_button.setText("❌ Déjà annulée")
            # Désactiver aussi les autres boutons pour une commande annulée
            self.pay_button.setEnabled(False)
            self.pay_button.setText("💳 Annulée")
        else:
            self.cancel_button.setEnabled(True)
            self.cancel_button.setText("❌ Annuler")

        # Verrouiller uniquement l'annulation pour une commande finalisée (Prêt + Livré)
        # Le paiement reste autorisé : une commande peut être livrée avant paiement complet.
        if is_finalized_locked and not is_cancelled:
            self.cancel_button.setEnabled(False)
            self.cancel_button.setText("❌ Verrouillée")
            
        
        # Stocker l'ID de la commande pour les actions
        self.selected_commande_id = commande.get('id')
        self.selected_commande_module = commande.get('module', 'boutique')
        self.selected_commande_locked = bool(is_finalized_locked)
        
        # =========================
        # Préparer données WhatsApp
        # =========================

        client_id = commande.get('client_id') or commande.get('client')

        self.current_client_phone = None
        self.current_client_name = None
        self.btn_whatsapp.setEnabled(False)

        if client_id:
            try:
                client = self.client_controller.get_infosclient(client_id)
                if client:
                    self.current_client_name = client.get('nom') or client.get('name')
                    self.current_client_phone = client.get('telephone') or client.get('phone')

                    if self.current_client_phone:
                        self.btn_whatsapp.setEnabled(True)
            except Exception as e:
                print("Erreur chargement client WhatsApp :", e)


    def on_commande_double_clicked(self, row, column):
        """Handler double-clic : ouvre un dialogue pour confirmer Prêt / Livré."""
        try:
            # Récupérer l'ID de la commande depuis UserRole si disponible
            item0 = self.commandes_table.item(row, 0)
            commande_id = None
            commande_module = 'boutique'
            if item0 is not None:
                try:
                    data = item0.data(Qt.ItemDataRole.UserRole)
                    if isinstance(data, tuple) and len(data) == 2:
                        commande_id, commande_module = data
                    else:
                        commande_id = data
                except Exception:
                    try:
                        data = item0.data(Qt.ItemDataRole.UserRole)
                        if isinstance(data, tuple) and len(data) == 2:
                            commande_id, commande_module = data
                        else:
                            commande_id = data
                    except Exception:
                        commande_id = None

            if commande_id in (None, ''):
                # tenter d'extraire depuis le texte
                if item0 is not None:
                    txt = item0.text() or ''
                    m = re.search(r"(\d+)", txt)
                    if m:
                        try:
                            commande_id = int(m.group(1))
                        except Exception:
                            pass

            if not commande_id:
                QMessageBox.warning(self, "Erreur", "Impossible de déterminer l'ID de la commande pour modification.")
                return

            # Normaliser l'identifiant pour éviter l'envoi d'un tuple ou d'une chaîne invalide au backend
            try:
                commande_id = int(commande_id)
            except Exception:
                pass

            # Lire valeurs actuelles dans la table
            try:
                pret_item = self.commandes_table.item(row, 9)
                livre_item = self.commandes_table.item(row, 10)
                current_pret = (pret_item.text().strip().lower() == 'oui') if pret_item else False
                current_livre = (livre_item.text().strip().lower() == 'oui') if livre_item else False
            except Exception:
                current_pret = False
                current_livre = False

            # Verrouiller les commandes déjà finalisées (Prêt + Livré)
            if current_pret and current_livre:
                QMessageBox.information(
                    self,
                    "Commande verrouillée",
                    "Cette commande est déjà marquée Prêt et Livré. La modification est bloquée."
                )
                return

            dlg = ConfirmStatusDialog(self, current_pret=current_pret, current_livre=current_livre)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                new_pret, new_livre = dlg.get_values()

                # Essayer d'appeler le contrôleur pour persister les flags
                try:
                    success = True
                    if hasattr(self.commande_controller, 'set_commande_pret_livre'):
                        try:
                            success = self.commande_controller.set_commande_pret_livre(
                                commande_id,
                                bool(new_pret),
                                bool(new_livre),
                                module=commande_module
                            )
                        except Exception as e:
                            print(f"Erreur persistance pret/livre via set_commande_pret_livre: {e}")
                            success = False
                    elif hasattr(self.commande_controller, 'update_commande_flags'):
                        try:
                            res = self.commande_controller.update_commande_flags(commande_id, {'is_ready': bool(new_pret), 'is_delivered': bool(new_livre)})
                            success = res if isinstance(res, bool) else True
                        except Exception as e:
                            print(f"Erreur persistance pret/livre via update_commande_flags: {e}")
                            success = False
                    else:
                        # Pas de méthode sur le contrôleur : log pour debugging
                        print(f"DEBUG: no controller method to persist pret/livre for {commande_id} - values: {new_pret},{new_livre}")
                        success = False
                except Exception as e:
                    print(f"Erreur persistance pret/livre: {e}")
                    success = False

                # Mettre à jour l'affichage de la ligne
                try:
                    if getattr(self, 'commandes_table', None) is not None:
                        try:
                            pret_item = QTableWidgetItem('Oui' if new_pret else 'Non')
                            if new_pret:
                                pret_item.setBackground(QColor('#e8f5e9'))
                        except Exception:
                            pret_item = QTableWidgetItem('Oui' if new_pret else 'Non')
                        try:
                            livre_item = QTableWidgetItem('Oui' if new_livre else 'Non')
                            if new_livre:
                                livre_item.setBackground(QColor('#e3f2fd'))
                        except Exception:
                            livre_item = QTableWidgetItem('Oui' if new_livre else 'Non')

                        try:
                            self.commandes_table.setItem(row, 9, pret_item)
                            self.commandes_table.setItem(row, 10, livre_item)
                        except Exception:
                            pass

                except Exception:
                    pass

                # Recharger les commandes depuis la base pour refléter l'état réel
                try:
                    if success:
                        self.load_commandes()
                    else:
                        QMessageBox.warning(self, "Erreur", "Impossible d'enregistrer l'état Prêt/Livré en base.")
                except Exception as e:
                    print(f"Erreur lors du rechargement des commandes: {e}")

                # Si cette commande est actuellement affichée dans le panneau détails, rafraîchir
                try:
                    if getattr(self, 'selected_commande_id', None) == commande_id:
                        commande_details = self.commande_controller.get_commande_details(commande_id, module=commande_module)
                        if commande_details:
                            self.update_details(commande_details)
                except Exception:
                    pass

        except Exception as e:
            print(f"Erreur on_commande_double_clicked: {e}")
    
    def clear_details(self):
        """Vider la zone de détails"""
        self.detail_numero.setText("-")
        self.detail_date.setText("-")
        self.detail_client.setText("-")
        self.detail_utilisateur.setText("-")  # Vider le champ utilisateur
        self.detail_sous_total.setText("-")
        self.detail_remise.setText("-")
        self.detail_total.setText("-")
        self.detail_paye.setText("-")
        self.detail_restant.setText("-")
        self.detail_statut.setText("-")
        self.detail_statut.setStyleSheet("")
        self.products_list.setText("Sélectionnez une commande pour voir les détails")
        # Vider champs restaurant
        self.detail_table.setText("-")
        self.detail_salle.setText("-")
        self.detail_serveuse.setText("-")
        
        # Vider les notes
        self.detail_notes.setText("Aucune note")
        self.detail_notes.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #f9f9f9;
                border-radius: 4px;
                min-height: 60px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
                color: #999;
                font-style: italic;
            }
        """)
        
        self.pay_button.setEnabled(False)
        self.pay_button.setText("💳 Payer")
        self.print_button.setEnabled(False)
        
        self.selected_commande_id = None
        self.selected_commande_module = None
        self.selected_commande_locked = False
    
    def on_pay_commande(self):
        """Ouvrir la fenêtre de paiement pour une commande existante"""
        if not hasattr(self, 'selected_commande_id') or not self.selected_commande_id:
            QMessageBox.warning(self, "Sélection requise", "Veuillez d'abord sélectionner une commande.")
            return
        
        try:
            # Récupérer les détails de la commande
            selected_module = getattr(self, 'selected_commande_module', None)
            commande_details = self.commande_controller.get_commande_details(self.selected_commande_id, module=selected_module)
            if not commande_details:
                QMessageBox.critical(self, "Erreur", "Impossible de récupérer les détails de la commande.")
                return

            # Calculer le montant restant à payer
            montant_paye = commande_details.get('montant_paye', 0)
            total_final = commande_details.get('total_final', 0)
            montant_restant = total_final - montant_paye
            
            if montant_restant <= 0:
                QMessageBox.information(self, "Paiement complet", "Cette commande est déjà entièrement payée.")
                return
            
            # Créer des éléments de panier fictifs pour la PaymentDialog
            # On crée un élément représentant le paiement restant de la commande
            cart_items = [{
                'name': f"Commande {commande_details.get('numero_commande', self.selected_commande_id)}",
                'unit_price': montant_restant,
                'quantity': 1,
                'total_price': montant_restant
            }]
            
            # Ouvrir le dialogue de paiement avec le montant restant
            payment_dialog = PaymentDialog(self, cart_items, 0, montant_restant)
            if payment_dialog.exec() == QDialog.DialogCode.Accepted:
                # Traiter le paiement
                self.process_commande_payment(payment_dialog.get_payment_data(), commande_details)
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ouverture du paiement: {e}")
    
    def process_commande_payment(self, payment_data, commande_details):
        """Traiter le paiement d'une commande existante"""
        try:
            # Extraire les données de paiement
            payment_method = payment_data.get('method')  # Correction: 'method' au lieu de 'payment_method'
            amount = payment_data.get('amount_received', 0)  # Correction: 'amount_received' au lieu de 'amount'
            
            if not payment_method:
                QMessageBox.warning(self, "Erreur", "Veuillez sélectionner une méthode de paiement.")
                return
            
            # Pour CRÉDIT: montant = 0 est valide (on enregistre juste la dette, pas d'argent reçu)
            # Pour autres méthodes: montant doit être > 0
            if payment_method != 'Crédit' and amount <= 0:
                QMessageBox.warning(self, "Erreur", "Le montant doit être supérieur à 0 pour ce mode de paiement.")
                return
            
            # Pour CRÉDIT: si le montant est < 0, ce n'est pas valide
            if payment_method == 'Crédit' and amount < 0:
                QMessageBox.warning(self, "Erreur", "Montant invalide pour un crédit.")
                return
            
            # Vérifier que le montant ne dépasse pas le restant dû
            montant_paye = commande_details.get('montant_paye', 0)
            total_final = commande_details.get('total_final', 0)
            montant_restant = total_final - montant_paye
            
            if amount > montant_restant:
                QMessageBox.warning(self, "Erreur", f"Le montant saisi ({amount:.0f} {self.get_currency_symbol()}) dépasse le restant dû ({montant_restant:.0f} {self.get_currency_symbol()}).")
                return
            
            # Utiliser le contrôleur approprié selon le module (restaurant vs boutique)
            if commande_details.get('module') == 'restaurant':
                success, message = self.commande_controller.process_restaurant_payment(
                    panier_id=commande_details['id'],
                    payment_method=payment_method,
                    amount=amount,
                    current_user=self.current_user
                )
            else:
                success, message = self.commande_controller.process_commande_payment(
                    commande_id=commande_details['id'],
                    payment_method=payment_method,
                    amount=amount,
                    pos_id=self.boutique_controller.pos_id,
                    current_user=self.current_user
                )
            
            if not success:
                QMessageBox.critical(self, "Erreur", message)
                return
            
            # Rafraîchir l'affichage
            self.load_commandes()
            
            # Si une commande est sélectionnée, rafraîchir les détails
            if hasattr(self, 'selected_commande_id') and self.selected_commande_id:
                commande_details = self.commande_controller.get_commande_details(self.selected_commande_id)
                if commande_details:
                    self.update_details(commande_details)
            
            QMessageBox.information(self, "Succès", message)
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement du paiement: {e}")
    
    def on_print_commande(self):
        """Imprimer une commande avec notes"""
        if not hasattr(self, 'selected_commande_id') or not self.selected_commande_id:
            QMessageBox.warning(self, "Erreur", "Aucune commande sélectionnée")
            return
        
        try:
            # Récupérer les détails complets de la commande
            commande_details = self.commande_controller.get_commande_details(self.selected_commande_id)
            if not commande_details:
                QMessageBox.critical(self, "Erreur", "Impossible de récupérer les détails de la commande.")
                return
            
            # Traduire le statut de la commande
            def translate_etat(status):
                """Traduit l'état du panier en français lisible"""
                status_lower = str(status or '').lower().strip()
                if status_lower in ('cancelled', 'annule', 'annulé', 'annulee'):
                    return "❌ Annulée"
                elif status_lower in ('en_cours', 'en cours', 'pending'):
                    return "⏳ En cours"
                elif status_lower in ('valide', 'validé', 'validated', 'completed'):
                    return "✅ Validée"
                else:
                    return status or '-'
            
            def translate_paiement(montant_paye, total_final):
                """Traduit le statut de paiement"""
                if montant_paye >= total_final and total_final > 0:
                    return "✅ Payée"
                elif montant_paye > 0:
                    return "⏳ Partiellement payée"
                else:
                    return "❌ Non payée"
            
            # Récupérer le nom de l'utilisateur qui a créé la commande
            user_name = commande_details.get('user_name') or commande_details.get('comptoiriste_name') or getattr(self.current_user, 'name', 'Utilisateur')
            
            # Préparer les données de la facture (format similaire au panier)
            montant_paye = commande_details.get('montant_paye', 0)
            total_final = commande_details.get('total_final', 0)
            raw_status = commande_details.get('status', '')
            
            invoice_data = {
                'reference': commande_details.get('numero_commande', f"CMD-{commande_details.get('id')}"),
                'order_date': commande_details.get('created_at'),
                'created_at': commande_details.get('created_at'),
                'status': translate_paiement(montant_paye, total_final),
                'etat': translate_etat(raw_status),
                'client_nom': commande_details.get('client_name', 'Client anonyme'),
                'client_telephone': '',
                'client_email': '',
                'client_adresse': '',
                'items': [],  # À construire à partir des détails produits/services
                'subtotal_ht': commande_details.get('subtotal', 0),
                'tax_amount': 0.0,
                'total_ttc': total_final,
                'discount_amount': commande_details.get('remise_amount', 0),
                'total_net': total_final,
                'notes': commande_details.get('notes', ''),
                'user_name': user_name,
                'payments': [{
                    'payment_date': commande_details.get('created_at'),
                    'amount': montant_paye,
                    'payment_method': commande_details.get('payment_method', ''),
                    'user_name': user_name
                }]
            }
            # Indiquer le module source pour guider l'impression (restaurant vs boutique)
            invoice_data['module'] = commande_details.get('module', 'boutique')
            # Transmettre les métadonnées restaurant si disponibles (pour impression 53mm)
            invoice_data['table'] = commande_details.get('table_number') or commande_details.get('table')
            invoice_data['salle'] = commande_details.get('salle_name') or commande_details.get('salle')
            invoice_data['serveuse'] = commande_details.get('serveuse_name') or commande_details.get('serveuse') or commande_details.get('waiter_name')
            invoice_data['comptoiriste'] = commande_details.get('comptoiriste') or commande_details.get('comptoir')
            
            # Construire la liste des items à partir des détails produits/services
            # Pour simplifier, on utilise les détails textuels existants
            if commande_details.get('produits_detail'):
                # Parser les détails textuels pour créer des items
                produits_detail = commande_details.get('produits_detail', '')
                lines = produits_detail.split('\n')
                for line in lines:
                    if line.strip() and line.startswith('• '):
                        # Extraire le nom et les informations de quantité/prix
                        item_text = line[2:].strip()  # Enlever "• "
                        # Format typique: "Nom produit - 2 x 5000 FC = 10000 FC"
                        if ' - ' in item_text and ' x ' in item_text and ' = ' in item_text:
                            try:
                                name_part, rest = item_text.split(' - ', 1)
                                qty_part, price_part = rest.split(' = ', 1)
                                qty_text, unit_price_text = qty_part.split(' x ')
                                
                                quantity = float(qty_text.strip())
                                unit_price = float(unit_price_text.replace(' FC', '').strip())
                                total_price = float(price_part.replace(' FC', '').strip())
                                
                                invoice_data['items'].append({
                                    'name': name_part.strip(),
                                    'quantity': quantity,
                                    'unit_price': unit_price,
                                    'total_price': total_price
                                })
                            except:
                                # Si le parsing échoue, ajouter comme item simple
                                invoice_data['items'].append({
                                    'name': item_text,
                                    'quantity': 1,
                                    'unit_price': 0,
                                    'total_price': 0
                                })
            
            # Récupérer les informations de paiement
            try:
                panier_id = commande_details.get('id')
                if panier_id:
                    payment_info = self.vente_controller.get_payment_info(panier_id)
                    invoice_data.update({
                        'payment_status': payment_info.get('payment_status', 'NON PAYÉE'),
                        'change': payment_info.get('change', 0.0),
                        'reste_a_payer': payment_info.get('reste_a_payer', 0.0)
                    })
            except Exception as e:
                print(f"Erreur récupération infos paiement: {e}")
                invoice_data.update({
                    'payment_status': 'NON PAYÉE',
                    'change': 0.0,
                    'reste_a_payer': 0.0
                })
            
            # Créer le dialogue d'impression
            receipt_dialog = QDialog(self)
            receipt_dialog.setWindowTitle("🧾 Impression commande")
            receipt_dialog.setFixedSize(500, 400)

            layout = QVBoxLayout(receipt_dialog)

            # Titre
            title_label = QLabel("Impression de la commande")
            title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
            layout.addWidget(title_label)

            # Options d'impression
            options_group = QGroupBox("Options d'impression")
            options_layout = QVBoxLayout(options_group)

            # Format d'impression
            format_layout = QHBoxLayout()
            format_layout.addWidget(QLabel("Format:"))

            print_format_combo = QComboBox()
            print_format_combo.addItems(["Reçu 53mm (ticket)", "Facture A4 (complet)"])
            format_layout.addWidget(print_format_combo)
            options_layout.addLayout(format_layout)

            # Aperçu du contenu
            preview_label = QLabel("Contenu généré:")
            preview_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            options_layout.addWidget(preview_label)

            # Aperçu simplifié (sécuriser notes qui peuvent être None)
            notes_raw = invoice_data.get('notes')
            notes = str(notes_raw) if notes_raw is not None else ''
            if len(notes) > 50:
                notes_preview = f" ({notes[:50]}...)"
            elif notes:
                notes_preview = f" ({notes})"
            else:
                notes_preview = ""
                # Sécuriser l'accès aux paiements (liste attendue)
                payments_list_preview = invoice_data.get('payments') or []
                payment_method_preview = ''
                if payments_list_preview and isinstance(payments_list_preview, list):
                    try:
                        payment_method_preview = payments_list_preview[0].get('payment_method', '')
                    except Exception:
                        payment_method_preview = ''

                preview_text = f"""
N° Commande: {invoice_data.get('reference', '')}
Client: {invoice_data.get('client_nom', '')}
Total: {invoice_data.get('total_ttc', 0):.0f} {self.get_currency_symbol()}
Paiement: {payment_method_preview}
Notes: {notes_preview}
                """.strip()

            preview_display = QTextEdit()
            preview_display.setPlainText(preview_text)
            preview_display.setReadOnly(True)
            preview_display.setMaximumHeight(100)
            preview_display.setStyleSheet("""
                QTextEdit {
                    font-family: 'Courier New', monospace;
                    font-size: 10px;
                    background-color: #f5f5f5;
                    border: 1px solid #ddd;
                }
            """)
            options_layout.addWidget(preview_display)

            layout.addWidget(options_group)

            # Boutons
            buttons_layout = QHBoxLayout()

            print_btn = QPushButton("🖨️ Imprimer")
            print_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            print_btn.clicked.connect(lambda: self._print_commande_invoice(invoice_data, receipt_dialog))
            buttons_layout.addWidget(print_btn)

            close_btn = QPushButton("✅ Fermer")
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            close_btn.clicked.connect(receipt_dialog.accept)
            close_btn.setDefault(True)
            buttons_layout.addWidget(close_btn)

            layout.addLayout(buttons_layout)

            receipt_dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'impression: {e}")
            print(f"❌ Erreur on_print_commande: {e}")
    
    def on_cancel_commande(self):
        """Annuler une commande avec confirmation"""
        if not hasattr(self, 'selected_commande_id') or not self.selected_commande_id:
            QMessageBox.warning(self, "Sélection requise", "Veuillez d'abord sélectionner une commande.")
            return
        
        try:
            # Récupérer les détails de la commande
            selected_module = getattr(self, 'selected_commande_module', None)
            commande_details = self.commande_controller.get_commande_details(self.selected_commande_id, module=selected_module)
            if not commande_details:
                QMessageBox.critical(self, "Erreur", "Impossible de récupérer les détails de la commande.")
                return

            # Bloquer l'annulation d'une commande finalisée
            pret_locked = bool(commande_details.get('pret') or commande_details.get('is_ready'))
            livre_locked = bool(commande_details.get('livre') or commande_details.get('is_delivered'))
            if pret_locked and livre_locked:
                QMessageBox.information(self, "Commande verrouillée", "Cette commande est déjà Prêt et Livré. L'annulation est verrouillée.")
                return
            
            # Vérifier si la commande peut être annulée
            status = commande_details.get('status', '')
            if status == 'cancelled':
                QMessageBox.information(self, "Déjà annulée", "Cette commande est déjà annulée.")
                return
            if status == 'annule':
                QMessageBox.information(self, "Déjà annulée", "Cette commande est déjà annulée.")
                return
            
            # Demander confirmation
            numero_commande = commande_details.get('numero_commande', f"CMD-{self.selected_commande_id}")
            montant_total = commande_details.get('total_final', 0)
            
            reply = QMessageBox.question(
                self, 
                "Confirmation d'annulation",
                f"Êtes-vous sûr de vouloir annuler la commande {numero_commande} ?\n\n"
                f"Montant: {montant_total:.0f} {self.get_currency_symbol()}\n\n"
                f"Cette action est irréversible et annulera toutes les écritures comptables associées.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Déterminer le module et appeler la méthode d'annulation appropriée
                try:
                    if commande_details and commande_details.get('module') == 'restaurant':
                        success, message = self.commande_controller.cancel_restaurant_commande(commande_details['id'], self.current_user)
                    else:
                        success, message = self.vente_controller.cancel_sale(self.selected_commande_id)

                    if success:
                        QMessageBox.information(self, "Succès", message)
                        # Recharger les données
                        self.load_commandes()
                        # Vider les détails
                        self.clear_details()
                    else:
                        QMessageBox.critical(self, "Erreur", f"Échec de l'annulation: {message}")
                except Exception as e:
                    QMessageBox.critical(self, "Erreur", f"Erreur lors de l'annulation: {e}")
                    print(f"❌ Erreur on_cancel_commande inner: {e}")
                    
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'annulation: {e}")
            print(f"❌ Erreur on_cancel_commande: {e}")
    
    def _print_commande_invoice(self, invoice_data, dialog):
        """Imprimer la facture/reçu de commande en utilisant InvoicePrintManager"""
        try:
            from ayanna_erp.modules.boutique.utils.invoice_printer import InvoicePrintManager
            from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
            import tempfile
            import os
            import subprocess
            from datetime import datetime
            
            # Créer l'InvoicePrintManager
            enterprise_controller = EntrepriseController()
            invoice_printer = InvoicePrintManager(enterprise_id=1)  # POS ID par défaut
            
            # Déterminer le format d'impression
            print_format_combo = dialog.findChild(QComboBox)
            format_choice = print_format_combo.currentText() if print_format_combo else "Facture A4 (complet)"
            
            # Générer un nom de fichier avec timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if "53mm" in format_choice:
                # Pour les tickets 53mm : dossier temporaire (pour impression directe)
                temp_dir = tempfile.gettempdir()
                filename = os.path.join(temp_dir, f"receipt_commande_{timestamp}.pdf")
                print_type = "ticket 53mm"
            else:
                # Pour les factures A4 : dossier factures_export
                invoices_dir = os.path.join(os.getcwd(), "factures_export")
                os.makedirs(invoices_dir, exist_ok=True)  # Créer le dossier s'il n'existe pas
                filename = os.path.join(invoices_dir, f"facture_commande_{invoice_data.get('reference', 'UNKNOWN')}_{timestamp}.pdf")
                print_type = "facture A4"
            
            # Générer le document
            if "53mm" in format_choice:
                # Impression ticket 53mm
                payments_list = invoice_data.get('payments', [])
                user_name = invoice_data.get('payments', [{}])[0].get('user_name', 'Utilisateur') if invoice_data.get('payments') else 'Utilisateur'
                
                result = invoice_printer.print_receipt_53mm(invoice_data, payments_list, user_name, filename)
            else:
                # Impression A4
                result = invoice_printer.print_invoice_a4(invoice_data, filename)
            
            if result and os.path.exists(result):
                if "53mm" in format_choice:
                    # Pour les tickets 53mm : ouvrir directement dans le lecteur par défaut
                    try:
                        subprocess.run(['start', '', result], shell=True, check=True)
                        QMessageBox.information(dialog, "Impression lancée", 
                                              f"Le ticket 53mm a été généré et l'impression a été lancée automatiquement !\n\n"
                                              f"Fichier: {result}")
                    except Exception as print_error:
                        QMessageBox.warning(dialog, "Impression manuelle requise",
                                          f"Le ticket 53mm a été généré avec succès !\n\n"
                                          f"Fichier: {result}\n\n"
                                          f"Erreur d'impression automatique: {print_error}\n"
                                          "Veuillez imprimer manuellement depuis votre lecteur PDF.")
                else:
                    # Pour les factures A4 : ouvrir le dossier factures_export
                    try:
                        import os, sys, subprocess
                        opened = False
                        if os.name == 'nt':
                            try:
                                os.startfile(result)
                                opened = True
                            except Exception:
                                opened = False
                        else:
                            try:
                                if sys.platform == 'darwin':
                                    subprocess.run(['open', result], check=True)
                                else:
                                    subprocess.run(['xdg-open', result], check=True)
                                opened = True
                            except Exception:
                                opened = False

                        if opened:
                            QMessageBox.information(dialog, "Export réussi",
                                                  f"La facture A4 a été exportée avec succès !\n\n"
                                                  f"Fichier: {result}\n\n"
                                                  "Le fichier a été ouvert dans l'application par défaut.")
                        else:
                            QMessageBox.information(dialog, "Export réussi",
                                                  f"La facture A4 a été exportée avec succès !\n\n"
                                                  f"Fichier: {result}\n\n"
                                                  "Impossible d'ouvrir automatiquement le fichier. Vous pouvez l'ouvrir manuellement.")
                    except Exception as open_error:
                        QMessageBox.information(dialog, "Export réussi",
                                              f"La facture A4 a été exportée avec succès !\n\n"
                                              f"Fichier: {result}\n\n"
                                              f"Erreur lors de l'ouverture du fichier: {open_error}")
                
                dialog.accept()
            else:
                QMessageBox.warning(dialog, "Erreur", f"Impossible de générer le document {print_type}.")
                
        except Exception as e:
            QMessageBox.critical(dialog, "Erreur", f"Erreur lors de l'impression: {e}")
            print(f"❌ Erreur _print_commande_invoice: {e}")
            
    def export_products_sold(self):
        """Exporter le récapitulatif produits/services vendus pour la période sélectionnée."""
        try:
            date_debut = self.date_debut.date().toPyDate() if hasattr(self, 'date_debut') else None
            date_fin = self.date_fin.date().toPyDate() if hasattr(self, 'date_fin') else None

            if not date_debut or not date_fin:
                QMessageBox.warning(self, "Dates manquantes", "Veuillez sélectionner une période valide.")
                return

            # Récupérer le résumé produits depuis le contrôleur (liste de dicts)
            products = self.commande_controller.get_products_summary(
                date_debut, date_fin, include_services=True,
                module=getattr(self, 'module', None),
                pos_id=getattr(self.boutique_controller, 'pos_id', None)
            )
            if not products:
                QMessageBox.warning(self, "Aucune donnée", "Aucun produit/service vendu pour la période sélectionnée.")
                return

            # Enrichir avec la catégorie puis demander une sélection utilisateur
            products = self._enrich_products_with_categories(products)
            available_categories = sorted({
                str(p.get('category_name') or 'Sans catégorie')
                for p in products
            })

            if not available_categories:
                QMessageBox.warning(self, "Catégories indisponibles", "Impossible de charger les catégories à exporter.")
                return

            category_dialog = CategorySelectionDialog(
                available_categories,
                parent=self,
                title="Sélection des catégories à exporter"
            )
            if category_dialog.exec() != QDialog.DialogCode.Accepted:
                return

            selected_categories = category_dialog.get_selected_categories()
            if not selected_categories:
                QMessageBox.warning(self, "Sélection requise", "Veuillez sélectionner au moins une catégorie.")
                return

            selected_set = set(selected_categories)
            products = [p for p in products if str(p.get('category_name') or 'Sans catégorie') in selected_set]

            if not products:
                QMessageBox.warning(self, "Aucune donnée", "Aucun produit/service ne correspond aux catégories sélectionnées.")
                return

            # Renuméroter après filtrage
            for idx, p in enumerate(products, start=1):
                p['no'] = idx

            # Générer un PDF professionnel pour les produits vendus
            # Choix du format d'export (A4 ou 80mm)
            choice, ok = QInputDialog.getItem(self, "Format d'export", "Choisissez le format:", ["A4", "80mm"], 0, False)
            if not ok:
                return

            pdf_path = None
            if choice == '80mm':
                try:
                    from ayanna_erp.modules.boutique.view.exports_widgets import print_products_report
                    # Pass the already-filtered products list so 80mm matches A4 selection
                    pdf_path = print_products_report(self, date_debut, date_fin, paper='80mm', include_services=True, module=getattr(self, 'module', None), pos_id=getattr(self.boutique_controller, 'pos_id', None), rows=products)
                except Exception as e:
                    print(f"Erreur export 80mm via print_products_report: {e}")
                    pdf_path = None
            else:
                pdf_path = self._generate_products_pdf(products, date_debut, date_fin, selected_categories=selected_categories)
            if pdf_path and os.path.exists(pdf_path):
                try:
                    if os.name == 'nt':
                        os.startfile(pdf_path)
                    else:
                        import subprocess, sys
                        if sys.platform == 'darwin':
                            subprocess.run(['open', pdf_path], check=True)
                        else:
                            subprocess.run(['xdg-open', pdf_path], check=True)

                    QMessageBox.information(self, "Export réussi", f"Export produits généré:\n{pdf_path}")
                except Exception:
                    QMessageBox.information(self, "Export réussi", f"Export produits généré:\n{pdf_path}\n(ouvre manuellement si nécessaire)")
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de générer l'export produits (PDF).")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export: {e}")
            print(f"❌ Erreur export_products_sold: {e}")

    def _enrich_products_with_categories(self, products):
        """Ajoute les informations de catégorie/coût aux lignes produit pour export."""
        from ayanna_erp.modules.core.models import CoreProduct, CoreProductCategory

        product_categories = {}
        product_costs = {}
        try:
            with self.commande_controller.db_manager.get_session() as session:
                all_products = session.query(CoreProduct).all()
                for prod in all_products:
                    product_costs[prod.id] = float(prod.cost or 0)
                    if prod.category_id:
                        cat = session.query(CoreProductCategory).get(prod.category_id)
                        if cat:
                            product_categories[prod.id] = {
                                'category_id': cat.id,
                                'category_name': cat.name
                            }
                        else:
                            product_categories[prod.id] = {
                                'category_id': None,
                                'category_name': 'Sans catégorie'
                            }
                    else:
                        product_categories[prod.id] = {
                            'category_id': None,
                            'category_name': 'Sans catégorie'
                        }
        except Exception as e:
            print(f"⚠️ Erreur enrichissement catégories/coûts: {e}")

        for product in products:
            product_id = product.get('product_id')
            if product.get('is_service'):
                product['category_name'] = 'Services'
                product['category_id'] = None
            elif product_id and product_id in product_categories:
                product['category_name'] = product_categories[product_id]['category_name']
                product['category_id'] = product_categories[product_id]['category_id']
            else:
                product['category_name'] = 'Sans catégorie'
                product['category_id'] = None

            product['cost'] = product_costs.get(product_id, 0)
            product['total_cost'] = product['cost'] * product.get('sold', 0)
            product['marge'] = product.get('total', 0) - product['total_cost']

        return products

    def export_daily_report(self):
        """Exporter un rapport quotidien (tableau) pour la période sélectionnée.
        Calculs harmonisés avec l'export produits et entêtes standardisées."""
        try:
            from ayanna_erp.modules.boutique.view.exports_widgets import export_daily_report as export_daily_report_fn

            date_debut = self.date_debut.date().toPyDate() if hasattr(self, 'date_debut') else None
            date_fin = self.date_fin.date().toPyDate() if hasattr(self, 'date_fin') else None
            if not date_debut or not date_fin:
                QMessageBox.warning(self, "Dates requises", "Veuillez sélectionner une période valide.")
                return

            search_term = self.search_input.text().strip() if hasattr(self, 'search_input') and self.search_input.text().strip() else None
            payment_filter = self.payment_filter.currentText() if hasattr(self, 'payment_filter') else None
            currency_symbol = self.get_currency_symbol()

            # Même logique que l'export produits: sélection des catégories à inclure
            products = self.commande_controller.get_products_summary(
                date_debut, date_fin, include_services=True,
                module=getattr(self, 'module', None),
                pos_id=getattr(self.boutique_controller, 'pos_id', None)
            ) or []
            products = self._enrich_products_with_categories(products)
            available_categories = sorted({
                str(p.get('category_name') or 'Sans catégorie')
                for p in products
            })

            if not available_categories:
                QMessageBox.warning(self, "Catégories indisponibles", "Impossible de charger les catégories pour le rapport.")
                return

            category_dialog = CategorySelectionDialog(
                available_categories,
                parent=self,
                title="Sélection des catégories pour le rapport"
            )
            if category_dialog.exec() != QDialog.DialogCode.Accepted:
                return

            selected_categories = category_dialog.get_selected_categories()
            if not selected_categories:
                QMessageBox.warning(self, "Sélection requise", "Veuillez sélectionner au moins une catégorie.")
                return

            pdf_path = export_daily_report_fn(
                date_debut=date_debut,
                date_fin=date_fin,
                module=getattr(self, 'module', None),
                pos_id=getattr(self.boutique_controller, 'pos_id', None),
                search_term=search_term,
                payment_filter=payment_filter,
                currency_symbol=currency_symbol,
                selected_categories=selected_categories
            )
            if pdf_path and os.path.exists(pdf_path):
                try:
                    os.startfile(pdf_path)
                except Exception:
                    pass
                QMessageBox.information(self, "Succès", f"Rapport exporté: {pdf_path}")
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de générer le rapport PDF.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export du rapport: {e}")

    def export_commandes(self):
        """Exporter les commandes en PDF professionnel"""
        try:
            # Récupérer les commandes actuelles (avec filtres appliqués)
            date_debut = self.date_debut.date().toPyDate() if hasattr(self, 'date_debut') else None
            date_fin = self.date_fin.date().toPyDate() if hasattr(self, 'date_fin') else None
            search_term = self.search_input.text().strip() if hasattr(self, 'search_input') and self.search_input.text().strip() else None
            payment_filter = self.payment_filter.currentText() if hasattr(self, 'payment_filter') else None
            
            commandes = self.commande_controller.get_commandes(
                date_debut=date_debut,
                date_fin=date_fin,
                search_term=search_term,
                payment_filter=payment_filter,
                limit=1000  # Plus de données pour l'export
            )
            
            if not commandes:
                QMessageBox.warning(self, "Aucune donnée", "Aucune commande à exporter avec les filtres actuels.")
                return
            
            # Générer le PDF
            pdf_filename = self._generate_commandes_pdf(commandes, date_debut, date_fin, search_term, payment_filter)
            
            if pdf_filename and os.path.exists(pdf_filename):
                # Ouvrir directement le fichier (pas le dossier)
                try:
                    import sys, subprocess
                    opened = False
                    if os.name == 'nt':
                        try:
                            os.startfile(pdf_filename)
                            opened = True
                        except Exception:
                            opened = False
                    else:
                        try:
                            if sys.platform == 'darwin':
                                subprocess.run(['open', pdf_filename], check=True)
                            else:
                                subprocess.run(['xdg-open', pdf_filename], check=True)
                            opened = True
                        except Exception:
                            opened = False

                    if opened:
                        QMessageBox.information(self, "Export réussi",
                                              f"Les commandes ont été exportées avec succès !\n\n"
                                              f"Fichier: {pdf_filename}\n\n"
                                              "Le fichier a été ouvert dans l'application par défaut.")
                    else:
                        QMessageBox.information(self, "Export réussi",
                                              f"Les commandes ont été exportées avec succès !\n\n"
                                              f"Fichier: {pdf_filename}\n\n"
                                              "Impossible d'ouvrir automatiquement le fichier. Vous pouvez l'ouvrir manuellement.")
                except Exception as open_error:
                    QMessageBox.information(self, "Export réussi",
                                          f"Les commandes ont été exportées avec succès !\n\n"
                                          f"Fichier: {pdf_filename}\n\n"
                                          f"Erreur lors de l'ouverture du fichier: {open_error}")
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de générer le fichier PDF d'export.")
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export PDF: {e}")
            print(f"❌ Erreur export_commandes PDF: {e}")
            import traceback
            traceback.print_exc()
        
    def _generate_commandes_pdf(self, commandes, date_debut, date_fin, search_term, payment_filter):
        """Générer un PDF professionnel d'export des commandes"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch, cm
            from reportlab.lib.colors import HexColor, black, white, gray
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
            from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
            from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
            
            # Créer le dossier d'export s'il n'existe pas
            export_dir = os.path.join(os.getcwd(), "exports_commandes")
            os.makedirs(export_dir, exist_ok=True)
            
            # Générer le nom du fichier
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(export_dir, f"export_commandes_{timestamp}.pdf")

            # Créer le document PDF (A4 portrait)
            doc = SimpleDocTemplate(filename, pagesize=A4)
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
            
            # Informations de l'entreprise
            enterprise_controller = EntrepriseController()
            company_info = enterprise_controller.get_company_info_for_pdf(None)  # POS ID par défaut

            # Variables pour gérer le fichier temporaire du logo
            temp_logo_file = None
            logo_path = None

            # En-tête avec logo et informations entreprise
            header_data = []

            # Logo (si disponible)
            if company_info.get('logo'):
                try:
                    # Créer un fichier temporaire pour le logo (garder ouvert)
                    import tempfile
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
            elements.append(Paragraph("RAPPORT D'EXPORT DES COMMANDES", styles['ReportTitle']))
            
            # Informations sur les filtres appliqués
            filter_info = []
            if date_debut:
                filter_info.append(f"Du: {date_debut.strftime('%d/%m/%Y')}")
            if date_fin:
                filter_info.append(f"Au: {date_fin.strftime('%d/%m/%Y')}")
            if search_term:
                filter_info.append(f"Recherche: '{search_term}'")
            if payment_filter and payment_filter != "Tous":
                filter_info.append(f"Paiement: {payment_filter}")
            
            if filter_info:
                elements.append(Paragraph(f"<b>Filtres appliqués:</b> {' | '.join(filter_info)}", styles['SectionHeader']))
            else:
                elements.append(Paragraph("<b>Période:</b> Toutes les commandes", styles['SectionHeader']))
            
            elements.append(Paragraph(f"<b>Date d'export:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['NormalText']))
            elements.append(Paragraph(f"<b>Nombre de commandes:</b> {len(commandes)}", styles['NormalText']))
            elements.append(Spacer(1, 0.5*cm))
            
            # Statistiques générales (utiliser la source DB pour cohérence)
            # Statistiques filtrées pour l'export PDF
            stats = self.commande_controller.get_period_commandes_stats(date_debut, date_fin, search_term=search_term, payment_filter=payment_filter)
            # helper local: use centralized formatter for PDF exports
            try:
                from ayanna_erp.utils.formatting import format_amount_for_pdf as _fmt_pdf
                currency_lower = self.get_currency_symbol()
                def _fmt_local(val):
                    try:
                        return _fmt_pdf(val, currency_lower)
                    except Exception:
                        return str(val)
            except Exception:
                def _fmt_local(val):
                    try:
                        return str(val)
                    except Exception:
                        return str(val)

            # Ajout du total des dépenses (sorties caisse)
            try:
                from ayanna_erp.modules.salle_fete.controller.entre_sortie_controller import EntreSortieController
                from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaConfig
                entre_sortie_controller = EntreSortieController()
                db_manager = entre_sortie_controller.get_database_manager() if hasattr(entre_sortie_controller, 'get_database_manager') else None
                if db_manager is None:
                    from ayanna_erp.modules.salle_fete.model.salle_fete import get_database_manager
                    db_manager = get_database_manager()
                session = db_manager.get_session()
                config = session.query(ComptaConfig).filter_by(pos_id=1).first()
                compte_caisse_id = getattr(config, 'compte_caisse_id', None)
                session.close()
                total_depenses = 0
                if compte_caisse_id:
                    journal_entries = entre_sortie_controller.load_account_journal(compte_caisse_id, date_from=date_debut, date_to=date_fin)
                    total_depenses = sum(entry.get('montant_sortie', 0) for entry in journal_entries)
            except Exception as e:
                print(f"Erreur récupération dépenses (sorties caisse): {e}")
                total_depenses = 0

            # Calcul des remises totales
            total_remises = 0.0
            try:
                from datetime import datetime as _dt
                from sqlalchemy import text
                
                # Normaliser les dates pour les requêtes
                if isinstance(date_debut, _dt):
                    d1 = date_debut
                else:
                    d1 = _dt.combine(date_debut, _dt.min.time())
                if isinstance(date_fin, _dt):
                    d2 = date_fin
                else:
                    d2 = _dt.combine(date_fin, _dt.max.time())
                
                with self.commande_controller.db_manager.get_session() as session:
                    # Remises boutique
                    shop_remises = session.execute(text("""
                        SELECT COALESCE(SUM(COALESCE(remise_amount, 0)), 0) as total_remise
                        FROM shop_paniers
                        WHERE created_at >= :d1 AND created_at <= :d2
                        AND LOWER(COALESCE(status, '')) NOT IN ('cancelled', 'annule', 'canceled')
                    """), {'d1': d1, 'd2': d2}).scalar() or 0
                    
                    # Remises restaurant
                    restau_remises = session.execute(text("""
                        SELECT COALESCE(SUM(COALESCE(remise_amount, 0)), 0) as total_remise
                        FROM restau_paniers
                        WHERE created_at >= :d1 AND created_at <= :d2
                        AND LOWER(COALESCE(status, '')) NOT IN ('cancelled', 'annule', 'canceled')
                    """), {'d1': d1, 'd2': d2}).scalar() or 0
                    
                    total_remises = float(shop_remises) + float(restau_remises)
            except Exception as e:
                print(f"Erreur récupération remises totales: {e}")
                total_remises = 0.0

            # Calculs finaux
            # total_ca depuis les stats est déjà net (après remises) car basé sur total_final des paniers
            total_ca_net = float(stats.get('total_ca', 0))
            total_ca_brut = total_ca_net + total_remises  # reconstruire le brut avant remises
            total_vente = total_ca_net                    # = total_ca_brut - total_remises
            total_creances = stats.get('total_unpaid', 0)
            solde_net = total_vente - total_creances - total_depenses

            stats_data = [
                ['Statistiques générales', ''],
                ["Chiffre d'affaires brut:", _fmt_local(total_ca_brut)],
                ['Remises:', _fmt_local(total_remises)],
                ['Total vente (après remises):', _fmt_local(total_vente)],
                ['Total payés:', _fmt_local(stats.get('total_paid', 0))],
                ['Créances:', _fmt_local(total_creances)],
                ['Dépenses (sorties caisse):', _fmt_local(total_depenses)],
                ['SOLDE NET:', _fmt_local(solde_net)]
            ]

            stats_table = Table(stats_data, colWidths=[4*cm, 4*cm])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (1, 0), HexColor('#ECF0F1')),
                ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                # Mettre en évidence la ligne SOLDE NET (dernière ligne)
                ('BACKGROUND', (0, -1), (1, -1), HexColor('#D4EDDA')),
                ('FONTNAME', (0, -1), (1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (1, -1), 10),
            ]))
            elements.append(stats_table)
            elements.append(Spacer(1, 0.5*cm))
            
            # Tableau des commandes (sans colonne Produits/Services)
            table_data = [
                ['N° Commande', 'Date/Heure', 'Client', 'Sous-total', 'Remise', 'Total', 'Payé', 'Prêt', 'Livré']
            ]
            canceled_row_indexes = []
            
            for commande in commandes:
                # Formatage de la date
                date_str = ""
                created_at = commande.get('created_at')
                if created_at:
                    if isinstance(created_at, str):
                        try:
                            date_obj = datetime.strptime(created_at[:19], "%Y-%m-%d %H:%M:%S")
                            date_str = date_obj.strftime("%d/%m/%Y\n%H:%M")
                        except:
                            date_str = created_at[:16].replace(' ', '\n')
                    else:
                        date_str = created_at.strftime("%d/%m/%Y\n%H:%M")

                # Formatage des produits/services avec retours à la ligne
                    num_text = str(commande.get('numero_commande') or f"CMD-{commande.get('id')}")
                    status = commande.get('status', '')
                    if status in ('cancelled', 'annule', 'annulé', 'annulee'):
                        num_text = num_text + ' (ANNULÉE)'

                    # Déterminer flags prêt / livré
                    is_pret = False
                    is_livre = False
                    for k in ('is_ready', 'pret', 'ready'):
                        if commande.get(k) is not None:
                            is_pret = bool(commande.get(k))
                            break
                    for k in ('is_delivered', 'livre', 'delivered'):
                        if commande.get(k) is not None:
                            is_livre = bool(commande.get(k))
                            break

                    row = [
                        num_text,
                        date_str,
                        str(commande.get('client_name', '')),
                        _fmt_local(commande.get('subtotal', 0)),
                        _fmt_local(commande.get('remise_amount', 0)),
                        _fmt_local(commande.get('total_final', 0)),
                        _fmt_local(commande.get('montant_paye', 0)),
                        'Oui' if is_pret else 'Non',
                        'Oui' if is_livre else 'Non'
                    ]
                    table_data.append(row)
                    # stocker l'index de la ligne de données (dans le tableau PDF) si annulée
                    if status in ('cancelled', 'annule', 'annulé', 'annulee'):
                        canceled_row_indexes.append(len(table_data)-1)
            
            # Créer le tableau avec des largeurs appropriées (sans produits)
            col_widths = [3*cm, 2*cm, 4*cm, 2*cm, 2*cm, 2*cm, 2*cm, 1.2*cm, 1.2*cm]
            commandes_table = Table(table_data, colWidths=col_widths, repeatRows=1)
            
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
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # N° Commande
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),  # Date
                ('ALIGN', (2, 0), (2, -1), 'LEFT'),    # Client
                ('ALIGN', (3, 0), (3, -1), 'LEFT'),    # Produits
                ('ALIGN', (4, 0), (7, -1), 'RIGHT'),   # Montants
                ('ALIGN', (8, 0), (8, -1), 'CENTER'),  # Statut
                
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
            
            commandes_table.setStyle(table_style)
            # Appliquer style gris aux lignes annulées dans le PDF
            try:
                for ridx in canceled_row_indexes:
                    # texte gris
                    table_style.add('TEXTCOLOR', (0, ridx), (-1, ridx), HexColor('#7f8c8d'))
                    # fond très pâle
                    table_style.add('BACKGROUND', (0, ridx), (-1, ridx), HexColor('#f2f2f2'))
            except Exception:
                pass
            elements.append(commandes_table)
            
            # Pied de page avec informations supplémentaires
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph(f"<i>Developed By Ayanna ERP ©, le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')} - {len(commandes)} commandes exportées</i>", styles['NormalText']))
            
            # Générer le PDF
            doc.build(elements)

            return filename
            
        except Exception as e:
            print(f"❌ Erreur génération PDF: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        finally:
            # Nettoyer le fichier temporaire du logo
            if logo_path and os.path.exists(logo_path):
                try:
                    os.unlink(logo_path)
                except Exception as cleanup_error:
                    print(f"Avertissement nettoyage logo: {cleanup_error}")
    
    def _format_produits_services(self, produits_raw):
        """Formate les produits/services avec des retours à la ligne"""
        if not produits_raw or produits_raw.strip() == '':
            return ''

        # Nettoyer la chaîne d'entrée
        produits_raw = produits_raw.strip()

        # Gérer les cas spéciaux où les virgules sont collées
        produits_raw = produits_raw.replace(',Location', ', Location')
        produits_raw = produits_raw.replace(',Simba', ', Simba')

        # Essayer différents séparateurs pour diviser les produits
        separators = ['\n', '; ', ', ', ',', ' - ', '|']

        items = []
        for sep in separators:
            if sep in produits_raw:
                # Pour les virgules sans espace, diviser et nettoyer
                if sep == ',':
                    temp_items = produits_raw.split(',')
                    items = [item.strip() for item in temp_items if item.strip()]
                else:
                    items = [item.strip() for item in produits_raw.split(sep) if item.strip()]
                break
        else:
            # Si aucun séparateur trouvé, traiter comme un seul élément
            items = [produits_raw]

        # Nettoyer et formater chaque élément
        formatted_items = []
        for item in items:
            item = item.strip()
            if item:
                # Détecter si c'est un service ou un produit
                item_lower = item.lower()
                if any(keyword in item_lower for keyword in ['service', 'prestation', 'location', 'soirée', 'événement', 'fête']):
                    formatted_items.append(f"• Service: {item}")
                else:
                    formatted_items.append(f"• Produit: {item}")

        # Joindre avec des retours à la ligne
        return '\n'.join(formatted_items)

    def _generate_products_pdf(self, products, date_debut, date_fin, selected_categories=None):
    
        """Générer un PDF A4 portrait professionnel listant les produits/services vendus

        products: liste de dicts renvoyée par CommandeController.get_products_summary
        """
        try:
            import os
            from datetime import datetime
            from collections import defaultdict

            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib.colors import HexColor, black, white
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
            )
            from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
            from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController

            # ============================
            # 1) Chemin d'export
            # ============================
            export_dir = os.path.join(os.getcwd(), "exports_products")
            os.makedirs(export_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(export_dir, f"export_produits_{timestamp}.pdf")

            # ============================
            # 2) Document avec marges professionnelles
            # ============================
            doc = SimpleDocTemplate(
                filename,
                pagesize=A4,
                leftMargin=4*cm,
                rightMargin=4*cm,
                topMargin=2*cm,
                bottomMargin=2*cm,
            )

            elements = []

            # ============================
            # 3) Styles
            # ============================
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='CompanyTitle', fontSize=18, fontName='Helvetica-Bold', alignment=TA_LEFT, spaceAfter=6))
            styles.add(ParagraphStyle(name='SmallInfo', fontSize=9, fontName='Helvetica', textColor="grey"))
            styles.add(ParagraphStyle(name='ReportTitle', fontSize=15, fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=10))
            styles.add(ParagraphStyle(name='SectionTitle', fontSize=11, fontName='Helvetica-Bold', spaceAfter=6))
            styles.add(ParagraphStyle(name='CategoryTitle', fontSize=12, fontName='Helvetica-Bold', textColor=HexColor('#1976D2'), spaceAfter=8))
            styles.add(ParagraphStyle(name='NormalText', fontSize=9, fontName='Helvetica'))

            # ============================
            # 4) Infos entreprise + Logo
            # ============================
            enterprise_controller = EntrepriseController()
            company_info = enterprise_controller.get_company_info_for_pdf(None)

            temp_logo = None
            logo_path = None
            header_data = []

            company_text = (
                f"<b>{company_info.get('name','')}</b><br/>{company_info.get('address','')}<br/>"
                f"{company_info.get('city','')}<br/>Tel: {company_info.get('phone','')}"
            )

            # Logo si disponible
            if company_info.get('logo'):
                try:
                    import tempfile
                    temp_logo = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                    temp_logo.write(company_info['logo'])
                    logo_path = temp_logo.name
                    temp_logo.close()
                    logo = Image(logo_path, width=2.3*cm, height=2.3*cm)
                    header_data.append([logo, Paragraph(company_text, styles['NormalText'])])
                except Exception as e:
                    header_data.append([Paragraph(company_text, styles['NormalText']), ''])
            else:
                header_data.append([Paragraph(company_text, styles['NormalText']), ''])

            header_table = Table(header_data, colWidths=[3*cm, 12*cm])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP')
            ]))

            elements.append(header_table)
            elements.append(Spacer(1, 0.6*cm))

            # ============================
            # 5) Titre du rapport
            # ============================
            elements.append(Paragraph("RAPPORT PRODUITS / SERVICES VENDUS", styles['ReportTitle']))

            elements.append(Paragraph(f"Période : <b>{date_debut.strftime('%d/%m/%Y')}</b> - <b>{date_fin.strftime('%d/%m/%Y')}</b>", styles['NormalText']))
            if selected_categories:
                cats_label = ', '.join(selected_categories)
                elements.append(Paragraph(f"Catégories sélectionnées : <b>{cats_label}</b>", styles['NormalText']))

            # ============================
            # 6) Fonction pour formattage monétaire (déplacée ici pour la synthèse)
            # ============================
            try:
                from ayanna_erp.utils.formatting import format_amount_for_pdf as _fmt_pdf
                currency_symbol = self.get_currency_symbol()
                def _fmt_local(v):
                    try: return _fmt_pdf(v, currency_symbol)
                    except: return str(v)
            except:
                def _fmt_local(v): return str(v)

            # ============================
            # Synthèse en haut du PDF (basée sur catégories sélectionnées)
            # ============================
            ca = sum(float(p.get('total', 0) or 0) for p in products)
            
            # Calculer les remises totales pour la période
            total_remises = 0.0
            try:
                from datetime import datetime as _dt
                from sqlalchemy import text
                
                # Normaliser les dates pour les requêtes
                if isinstance(date_debut, _dt):
                    d1 = date_debut
                else:
                    d1 = _dt.combine(date_debut, _dt.min.time())
                if isinstance(date_fin, _dt):
                    d2 = date_fin
                else:
                    d2 = _dt.combine(date_fin, _dt.max.time())
                
                with self.commande_controller.db_manager.get_session() as session:
                    # Remises boutique
                    shop_remises = session.execute(text("""
                        SELECT COALESCE(SUM(COALESCE(remise_amount, 0)), 0) as total_remise
                        FROM shop_paniers
                        WHERE created_at >= :d1 AND created_at <= :d2
                        AND LOWER(COALESCE(status, '')) NOT IN ('cancelled', 'annule', 'canceled')
                    """), {'d1': d1, 'd2': d2}).scalar() or 0
                    
                    # Remises restaurant
                    restau_remises = session.execute(text("""
                        SELECT COALESCE(SUM(COALESCE(remise_amount, 0)), 0) as total_remise
                        FROM restau_paniers
                        WHERE created_at >= :d1 AND created_at <= :d2
                        AND LOWER(COALESCE(status, '')) NOT IN ('cancelled', 'annule', 'canceled')
                    """), {'d1': d1, 'd2': d2}).scalar() or 0
                    
                    total_remises = float(shop_remises) + float(restau_remises)
            except Exception as e:
                print(f"Erreur récupération remises totales: {e}")
                import traceback
                traceback.print_exc()
                total_remises = 0.0
            
            total_vente = ca - total_remises  # CA brut moins remises
            # On garde dépenses, créances, solde net comme avant
            try:
                from ayanna_erp.modules.salle_fete.controller.entre_sortie_controller import EntreSortieController
                from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaConfig
                entre_sortie_controller = EntreSortieController()
                db_manager = entre_sortie_controller.get_database_manager() if hasattr(entre_sortie_controller, 'get_database_manager') else None
                if db_manager is None:
                    from ayanna_erp.modules.salle_fete.model.salle_fete import get_database_manager
                    db_manager = get_database_manager()
                session = db_manager.get_session()
                config = session.query(ComptaConfig).filter_by(pos_id=1).first()
                compte_caisse_id = getattr(config, 'compte_caisse_id', None)
                session.close()
                total_depenses = 0
                if compte_caisse_id:
                    journal_entries = entre_sortie_controller.load_account_journal(compte_caisse_id, date_from=date_debut, date_to=date_fin)
                    total_depenses = sum(entry.get('montant_sortie', 0) for entry in journal_entries)
            except Exception as e:
                print(f"Erreur récupération dépenses (sorties caisse): {e}")
                total_depenses = 0

            # Calculer correctement les créances de la période
            try:
                from ayanna_erp.modules.boutique.controller.commande_controller import CommandeController
                commande_controller = getattr(self, 'commande_controller', None)
                if commande_controller is None:
                    # Fallback si non initialisé
                    commande_controller = CommandeController()
                stats = commande_controller.get_period_commandes_stats(date_debut, date_fin)
                total_creances = stats.get('total_creances', 0)
            except Exception as e:
                print(f"Erreur récupération créances (synthèse): {e}")
                total_creances = 0
            solde_net = total_vente - total_creances - total_depenses
            # Synthèse avec ligne Dépenses
            synthese_data = [
                ["Chiffre d'affaires", "Remises", "Total vente", "Créances", "Dépenses", "Solde net"],
                [
                    _fmt_local(ca),
                    _fmt_local(total_remises),
                    _fmt_local(total_vente),
                    _fmt_local(total_creances),
                    _fmt_local(total_depenses),
                    _fmt_local(solde_net)
                ]
            ]
            synthese_table = Table(synthese_data, colWidths=[2.7*cm, 2.7*cm, 2.7*cm, 2.7*cm, 2.7*cm, 2.7*cm])
            synthese_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#ECF0F1')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(synthese_table)
            elements.append(Spacer(1, 0.5*cm))

            # ============================
            # 6) Fonction pour formattage monétaire
            # ============================
            try:
                from ayanna_erp.utils.formatting import format_amount_for_pdf as _fmt_pdf
                currency_symbol = self.get_currency_symbol()
                def _fmt_local(v):
                    try: return _fmt_pdf(v, currency_symbol)
                    except: return str(v)
            except:
                def _fmt_local(v): return str(v)

            # ============================
            # 7) Enrichir les produits avec les informations de catégorie
            # ============================
            products = self._enrich_products_with_categories(products)

            # ============================
            # 8) Grouper les produits par catégorie
            # ============================
            products_by_category = defaultdict(list)
            for product in products:
                category_name = product.get('category_name', 'Sans catégorie')
                products_by_category[category_name].append(product)

            # Trier les catégories par nom
            sorted_categories = sorted(products_by_category.keys())

            # Détecter si on a des quantités initiales sur la journée (si non, cacher Q.Init et Reste)
            has_initials_day = any((p.get('initial_quantity') is not None) for p in products)

            # ============================
            # 9) Construction des tableaux par catégorie
            # ============================
            total_general = 0
            total_marge = 0
            if has_initials_day:
                col_widths = [0.7*cm, 3.8*cm, 1.4*cm, 1.2*cm, 1.5*cm, 1.2*cm, 1.3*cm, 1.6*cm, 2*cm, 2*cm, 2*cm]
            else:
                col_widths = [0.7*cm, 4.2*cm, 1.4*cm, 1.5*cm, 1.2*cm, 1.6*cm, 2*cm, 2*cm, 2*cm]

            for category_name in sorted_categories:
                category_products = products_by_category[category_name]
                
                # Titre de la catégorie
                elements.append(Paragraph(f"📦 {category_name}", styles['CategoryTitle']))
                elements.append(Spacer(1, 0.3*cm))
                
                # En-tête du tableau (sans colonne Ajustements)
                if has_initials_day:
                    table_data = [[
                        'N°', 'Nom', 'Q. Init', 'Ajouts', 'Total', 'Ventes', 'Reste', 'P.U', 'Total', 'Coût', 'Marge'
                    ]]
                else:
                    table_data = [[
                        'N°', 'Nom', 'Ajouts', 'Total', 'Ventes', 'P.U', 'Total', 'Coût', 'Marge'
                    ]]

                # Total de la catégorie
                total_category = 0
                
                # Ajouter les produits de la catégorie
                for row in category_products:
                    total_category += row.get('total', 0)
                    total_general += row.get('total', 0)
                    total_marge += row.get('marge', 0)
                    total_after = (row.get('initial_quantity', 0) or 0) + row.get('quantity_added', 0)
                    if has_initials_day:
                        table_data.append([
                            row.get('no', ''),
                            row.get('name', ''),
                            f"{(row.get('initial_quantity', None) if row.get('initial_quantity', None) is not None else 0):.0f}",
                            f"{row.get('quantity_added', 0):.0f}",
                            f"{total_after:.0f}",
                            f"{row.get('sold', 0):.0f}",
                            f"{row.get('final_quantity', 0):.0f}",
                            _fmt_local(row.get('unit_price', 0)),
                            _fmt_local(row.get('total', 0)),
                            _fmt_local(row.get('total_cost', 0)),
                            _fmt_local(row.get('marge', 0))
                        ])
                    else:
                        table_data.append([
                            row.get('no', ''),
                            row.get('name', ''),
                            f"{row.get('quantity_added', 0):.0f}",
                            f"{total_after:.0f}",
                            f"{row.get('sold', 0):.0f}",
                            _fmt_local(row.get('unit_price', 0)),
                            _fmt_local(row.get('total', 0)),
                            _fmt_local(row.get('total_cost', 0)),
                            _fmt_local(row.get('marge', 0))
                        ])

                # Créer le tableau
                tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
                tbl.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), HexColor('#2C3E50')),
                    ('TEXTCOLOR', (0,0), (-1,0), white),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('ALIGN', (0,0), (-1,0), 'CENTER'),
                    ('GRID', (0,0), (-1,-1), 0.4, black),
                    ('FONTSIZE', (0,0), (-1,-1), 7),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('ALIGN', (2,1), (9,-1), 'RIGHT'),
                ]))

                elements.append(tbl)
                
                # Sous-totaux CA, coût, marge de la catégorie
                sous_total_ca = sum(p.get('total', 0) for p in category_products)
                sous_total_cout = sum(p.get('total_cost', 0) for p in category_products)
                sous_total_marge = sum(p.get('marge', 0) for p in category_products)
                sous_total_table = Table([
                    ["Sous-total CA", "Sous-total coût", "Sous-total marge"],
                    [
                        _fmt_local(sous_total_ca),
                        _fmt_local(sous_total_cout),
                        _fmt_local(sous_total_marge)
                    ]
                ], colWidths=[4*cm, 4*cm, 4*cm])
                sous_total_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), HexColor('#eaeaea')),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('FONTSIZE', (0,0), (-1,-1), 9),
                    ('GRID', (0,0), (-1,-1), 0.4, black),
                ]))
                elements.append(Spacer(1, 0.3*cm))
                elements.append(sous_total_table)
                elements.append(Spacer(1, 0.5*cm))

            # ============================
            # 10) Total général des ventes
            # ============================
            elements.append(Paragraph("<b>TOTAL GÉNÉRAL DES VENTES :</b> " + _fmt_local(total_general), styles['SectionTitle']))
            elements.append(Spacer(1, 0.6*cm))

            # ============================
            # 10b) Créances, Dépenses, Solde net
            # ============================
            # Récupérer les créances sur la période (même logique que export commandes)
            try:
                from ayanna_erp.modules.boutique.controller.commande_controller import CommandeController
                commande_controller = getattr(self, 'commande_controller', None)
                if commande_controller is None:
                    commande_controller = CommandeController(self.session)
                stats = commande_controller.get_period_commandes_stats(date_debut, date_fin)
                total_creances = stats.get('total_creances', 0)
            except Exception as e:
                print(f"Erreur récupération créances: {e}")
                total_creances = 0

            # Récupérer le total des dépenses (sorties caisse) sur la période via les écritures comptables
            try:
                from ayanna_erp.modules.salle_fete.controller.entre_sortie_controller import EntreSortieController
                from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaConfig
                entre_sortie_controller = EntreSortieController()
                # Récupérer le compte caisse du POS 1 (ou adapter dynamiquement)
                db_manager = entre_sortie_controller.get_database_manager() if hasattr(entre_sortie_controller, 'get_database_manager') else None
                if db_manager is None:
                    from ayanna_erp.modules.salle_fete.model.salle_fete import get_database_manager
                    db_manager = get_database_manager()
                session = db_manager.get_session()
                config = session.query(ComptaConfig).filter_by(pos_id=1).first()
                compte_caisse_id = getattr(config, 'compte_caisse_id', None)
                session.close()
                total_depenses = 0
                if compte_caisse_id:
                    journal_entries = entre_sortie_controller.load_account_journal(compte_caisse_id, date_from=date_debut, date_to=date_fin)
                    total_depenses = sum(entry.get('montant_sortie', 0) for entry in journal_entries)
            except Exception as e:
                print(f"Erreur récupération dépenses (sorties caisse): {e}")
                total_depenses = 0

            solde_net = total_general - total_creances - total_depenses

            elements.append(Paragraph(f"<b>Créances :</b> " + _fmt_local(total_creances), styles['NormalText']))
            # Ajout du total des dépenses (sorties caisse) juste après créances, logique export commandes
            elements.append(Paragraph(f"<b>Dépenses (sorties caisse) :</b> " + _fmt_local(total_depenses), styles['NormalText']))
            elements.append(Paragraph(f"<b>SOLDE NET :</b> " + _fmt_local(solde_net), styles['SectionTitle']))
            elements.append(Paragraph(f"<b>TOTAL MARGE :</b> " + _fmt_local(total_marge), styles['SectionTitle']))
            elements.append(Spacer(1, 0.6*cm))

            # ============================
            # 11) Pied de page
            # ============================
            elements.append(Paragraph(
                f"Developed by Ayanna ERP © le {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                styles['SmallInfo']
            ))

            # ============================
            # 12) Génération
            # ============================
            doc.build(elements)

            return filename

        except Exception as e:
            print(f"❌ Erreur génération PDF produits: {e}")
            import traceback
            traceback.print_exc()
            return None

        finally:
            if 'logo_path' in locals() and logo_path and os.path.exists(logo_path):
                try: os.unlink(logo_path)
                except: pass


    def refresh_data(self):
        """Actualiser les données (interface publique)"""
        self.load_commandes()   
        
    def send_whatsapp_message(self):
        import urllib.parse
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
        
        enterprise_controller = EntrepriseController()
        company_info = enterprise_controller.get_company_info_for_pdf(None)
        company_name = company_info.get('name')

        # ⚠️ Numéro du client (format international sans +)
        # Exemple Cameroun : 237699123456
        phone = self.current_client_phone  # à définir lors du chargement commande

        client = self.detail_client.text()
        numero = self.detail_numero.text()
        sous_total = self.detail_sous_total.text()
        remise = self.detail_remise.text()
        total = self.detail_total.text()
        paye = self.detail_paye.text()
        restant = self.detail_restant.text()

        # Produits / services
        produits = self.products_list.text()

        message = f"""
    Bonjour Mr/Mme {client},

    La commande *N° {numero}* est enregistrée dans votre compte.

    🧾 *Détails de la commande* :
    {produits}

    💰 Sous-total : {sous_total}
    🎁 Remise : {remise}
    ✅ Total : {total}
    💵 Déjà payé : {paye}
    ⏳ Reste à payer : {restant}

    📄 Vous trouverez la facture en format PDF en bas de ce message.

    Cordialement,
    {company_name}

    ---
    Informatisé par *Ayanna*
    📞 0997554905
    """

        encoded_message = urllib.parse.quote(message)
        url = f"https://wa.me/{phone}?text={encoded_message}"

        QDesktopServices.openUrl(QUrl(url))
 

class ConfirmStatusDialog(QDialog):
    """Dialogue simple pour confirmer/mettre à jour les flags 'Prêt' et 'Livré'."""
    def __init__(self, parent=None, current_pret=False, current_livre=False):
        super().__init__(parent)
        self.setWindowTitle("Confirmer Prêt / Livré")
        self.setModal(True)
        self.current_pret = bool(current_pret)
        self.current_livre = bool(current_livre)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        info = QLabel("Cochez les statuts applicables pour cette commande:")
        layout.addWidget(info)

        self.pret_cb = QCheckBox("Prêt")
        self.pret_cb.setChecked(self.current_pret)
        layout.addWidget(self.pret_cb)

        self.livre_cb = QCheckBox("Livré")
        self.livre_cb.setChecked(self.current_livre)
        layout.addWidget(self.livre_cb)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self):
        return (bool(self.pret_cb.isChecked()), bool(self.livre_cb.isChecked()))

    def refresh_data(self):
        """Actualiser les données (interface publique)"""
        self.load_commandes()


class CategorySelectionDialog(QDialog):
    """Dialogue de sélection multiple des catégories à inclure dans l'export."""

    def __init__(self, categories, parent=None, title="Sélection des catégories"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.categories = categories or []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        help_label = QLabel("Cochez les catégories à exporter:")
        layout.addWidget(help_label)

        self.list_widget = QListWidget()
        for category_name in self.categories:
            item = QListWidgetItem(str(category_name))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)

        quick_actions = QHBoxLayout()
        select_all_btn = QPushButton("Tout cocher")
        unselect_all_btn = QPushButton("Tout décocher")
        select_all_btn.clicked.connect(self._select_all)
        unselect_all_btn.clicked.connect(self._unselect_all)
        quick_actions.addWidget(select_all_btn)
        quick_actions.addWidget(unselect_all_btn)
        quick_actions.addStretch()
        layout.addLayout(quick_actions)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _select_all(self):
        for i in range(self.list_widget.count()):
            it = self.list_widget.item(i)
            it.setCheckState(Qt.CheckState.Checked)

    def _unselect_all(self):
        for i in range(self.list_widget.count()):
            it = self.list_widget.item(i)
            it.setCheckState(Qt.CheckState.Unchecked)

    def get_selected_categories(self):
        selected = []
        for i in range(self.list_widget.count()):
            it = self.list_widget.item(i)
            if it.checkState() == Qt.CheckState.Checked:
                selected.append(it.text())
        return selected