"""
Widget pour l'affichage et la gestion des commandes du module Boutique
Vue uniquement - la logique métier est gérée par CommandeController
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                            QTableWidgetItem, QPushButton, QLabel, QDateEdit, 
                            QLineEdit, QComboBox, QGroupBox, QGridLayout, QFormLayout,
                            QHeaderView, QFrame, QSplitter, QMessageBox, QScrollArea, QDialog, QTextEdit)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
from datetime import datetime, timedelta
from decimal import Decimal
from ayanna_erp.modules.boutique.controller.commande_controller import CommandeController
from ayanna_erp.modules.boutique.view.modern_supermarket_widget import PaymentDialog

class CommandesIndexWidget(QWidget):
    """Widget principal pour l'affichage et gestion des commandes"""
    
    # Signaux
    commande_selected = pyqtSignal(int)  # ID de la commande sélectionnée
    
    def __init__(self, boutique_controller, current_user, parent=None):
        super().__init__(parent)
        self.boutique_controller = boutique_controller
        self.current_user = current_user
        self.parent_window = parent
        
        # Initialiser le contrôleur des commandes
        self.commande_controller = CommandeController()
        
        self.init_ui()
        self.load_commandes()
        
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
        self.date_debut = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_debut.setCalendarPopup(True)
        self.date_debut.dateChanged.connect(self.filter_commandes)
        filters_layout.addWidget(self.date_debut, 0, 1)
        
        filters_layout.addWidget(QLabel("Au :"), 0, 2)
        self.date_fin = QDateEdit(QDate.currentDate())
        self.date_fin.setCalendarPopup(True)
        self.date_fin.dateChanged.connect(self.filter_commandes)
        filters_layout.addWidget(self.date_fin, 0, 3)
        
        # Recherche
        filters_layout.addWidget(QLabel("Recherche :"), 1, 0)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Chercher par client, produit, numéro commande...")
        self.search_input.textChanged.connect(self.filter_commandes)
        filters_layout.addWidget(self.search_input, 1, 1, 1, 2)
        
        # Filtre par statut paiement
        filters_layout.addWidget(QLabel("Paiement :"), 1, 3)
        self.payment_filter = QComboBox()
        self.payment_filter.addItems(["Tous", "Espèces", "Crédit", "Carte", "Mobile Money"])
        self.payment_filter.currentTextChanged.connect(self.filter_commandes)
        filters_layout.addWidget(self.payment_filter, 1, 4)
        
        # Boutons d'action
        actions_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.clicked.connect(self.load_commandes)
        refresh_btn.setStyleSheet("QPushButton { padding: 8px 15px; }")
        
        export_btn = QPushButton("📊 Exporter")
        export_btn.clicked.connect(self.export_commandes)
        export_btn.setStyleSheet("QPushButton { padding: 8px 15px; }")
        
        actions_layout.addWidget(refresh_btn)
        actions_layout.addWidget(export_btn)
        actions_layout.addStretch()
        
        filters_layout.addLayout(actions_layout, 2, 0, 1, 5)
        
        layout.addWidget(filters_group)
        
    def create_commandes_table(self):
        """Créer le tableau des commandes"""
        self.commandes_table = QTableWidget()
        self.commandes_table.setColumnCount(8)
        self.commandes_table.setHorizontalHeaderLabels([
            "N° Commande", "Date", "Client", "Produits / Services", 
            "Sous-total", "Remise", "Total", "Payé", "Paiement"
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
        self.commandes_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                background-color: white;
                selection-background-color: #e3f2fd;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                font-weight: bold;
                border: 1px solid #ddd;
            }
        """)
        
        # Connecter les signaux
        self.commandes_table.itemSelectionChanged.connect(self.on_commande_selected)
        
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
        self.detail_sous_total = QLabel("-")
        self.detail_remise = QLabel("-")
        self.detail_total = QLabel("-")
        self.detail_paye = QLabel("-")
        self.detail_restant = QLabel("-")
        self.detail_statut = QLabel("-")
        
        info_layout.addRow("N° Commande:", self.detail_numero)
        info_layout.addRow("Date:", self.detail_date)
        info_layout.addRow("Client:", self.detail_client)
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
        self.commandes_table.setRowCount(len(commandes))
        
        for row, commande in enumerate(commandes):
            # N° Commande
            self.commandes_table.setItem(row, 0, QTableWidgetItem(str(commande.get('numero_commande') or f"CMD-{commande.get('id')}")))

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
            self.commandes_table.setItem(row, 1, QTableWidgetItem(date_str))

            # Client
            self.commandes_table.setItem(row, 2, QTableWidgetItem(str(commande.get('client_name', ''))))

            # Produits et services (déjà concaténés dans commande['produits'])
            items_text = commande.get('produits', 'Aucun produit/service')
            if len(items_text) > 100:
                items_text = items_text[:97] + '...'
            self.commandes_table.setItem(row, 3, QTableWidgetItem(items_text))

            # Sous-total
            self.commandes_table.setItem(row, 4, QTableWidgetItem(f"{commande.get('subtotal', 0):.0f} FC"))

            # Remise
            self.commandes_table.setItem(row, 5, QTableWidgetItem(f"{commande.get('remise_amount', 0):.0f} FC"))

            # Total
            total_item = QTableWidgetItem(f"{commande.get('total_final', 0):.0f} FC")
            if commande.get('payment_method') == 'Crédit':
                total_item.setBackground(QColor("#ffecb3"))
            self.commandes_table.setItem(row, 6, total_item)

            # Payé (montant déjà payé)
            montant_paye = commande.get('montant_paye', 0)
            paye_item = QTableWidgetItem(f"{montant_paye:.0f} FC")
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
            
    def update_statistics(self, commandes):
        """Mettre à jour les statistiques"""
        if not commandes:
            return
            
        # Utiliser le contrôleur pour calculer les statistiques
        stats = self.commande_controller.get_commandes_statistics(commandes)
        
        # Mise à jour des widgets de stats
        if hasattr(self, 'stat_widgets'):
            self.stat_widgets.get('commandes_aujourd\'hui', QLabel()).setText(str(stats['commandes_aujourd_hui']))
            self.stat_widgets.get('total_ca', QLabel()).setText(f"{stats['total_ca']:.0f} FC")
            self.stat_widgets.get('créances', QLabel()).setText(f"{stats['total_creances']:.0f} FC")
            
        self.update_period_stats(commandes)
        
    def update_period_stats(self, commandes=None):
        """Mettre à jour les statistiques de période"""
        if not commandes:
            stats_text = """
Période: Derniers 30 jours
Commandes: 0
Chiffre d'affaires: 0 FC
Créances: 0 FC
Panier moyen: 0 FC
            """
        else:
            # Utiliser le contrôleur pour formater les statistiques
            stats = self.commande_controller.get_commandes_statistics(commandes)
            stats_text = self.commande_controller.format_period_stats(
                stats, self.date_debut.date(), self.date_fin.date()
            )
            
        self.stats_text.setText(stats_text.strip())
        
    def filter_commandes(self):
        """Filtrer les commandes selon les critères"""
        # TODO: Implémenter le filtrage en temps réel
        # Pour l'instant, on recharge tout
        self.load_commandes()
        
    def on_commande_selected(self):
        """Gérer la sélection d'une commande dans le tableau"""
        selected_rows = self.commandes_table.selectionModel().selectedRows()
        if not selected_rows:
            self.clear_details()
            return
            
        row = selected_rows[0].row()
        commande_id = self.commandes_table.item(row, 0).text()
        
        # Récupérer les détails de la commande
        try:
            commande_details = self.commande_controller.get_commande_details(commande_id)
            if commande_details:
                self.update_details(commande_details)
            else:
                self.clear_details()
        except Exception as e:
            print(f"Erreur lors de la récupération des détails: {e}")
            self.clear_details()
    
    def update_details(self, commande):
        """Mettre à jour la zone de détails avec les informations de la commande"""
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
        self.detail_sous_total.setText(f"{commande.get('subtotal', 0):.0f} FC")
        self.detail_remise.setText(f"{commande.get('remise_amount', 0):.0f} FC")
        self.detail_total.setText(f"{commande.get('total_final', 0):.0f} FC")
        
        montant_paye = commande.get('montant_paye', 0)
        total_final = commande.get('total_final', 0)
        restant = total_final - montant_paye
        
        self.detail_paye.setText(f"{montant_paye:.0f} FC")
        self.detail_restant.setText(f"{restant:.0f} FC")
        
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
        
        # Stocker l'ID de la commande pour les actions
        self.selected_commande_id = commande.get('id')
    
    def clear_details(self):
        """Vider la zone de détails"""
        self.detail_numero.setText("-")
        self.detail_date.setText("-")
        self.detail_client.setText("-")
        self.detail_sous_total.setText("-")
        self.detail_remise.setText("-")
        self.detail_total.setText("-")
        self.detail_paye.setText("-")
        self.detail_restant.setText("-")
        self.detail_statut.setText("-")
        self.detail_statut.setStyleSheet("")
        self.products_list.setText("Sélectionnez une commande pour voir les détails")
        
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
    
    def on_pay_commande(self):
        """Ouvrir la fenêtre de paiement pour une commande existante"""
        if not hasattr(self, 'selected_commande_id') or not self.selected_commande_id:
            QMessageBox.warning(self, "Sélection requise", "Veuillez d'abord sélectionner une commande.")
            return
        
        try:
            # Récupérer les détails de la commande
            commande_details = self.commande_controller.get_commande_details(self.selected_commande_id)
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
            
            if amount <= 0:
                QMessageBox.warning(self, "Erreur", "Le montant doit être supérieur à 0.")
                return
            
            # Vérifier que le montant ne dépasse pas le restant dû
            montant_paye = commande_details.get('montant_paye', 0)
            total_final = commande_details.get('total_final', 0)
            montant_restant = total_final - montant_paye
            
            if amount > montant_restant:
                QMessageBox.warning(self, "Erreur", f"Le montant saisi ({amount:.0f} FC) dépasse le restant dû ({montant_restant:.0f} FC).")
                return
            
            # Enregistrer le paiement dans la base de données
            with self.commande_controller.db_manager.get_session() as session:
                from sqlalchemy import text
                
                # Insérer le paiement
                insert_payment = text("""
                    INSERT INTO shop_payments (panier_id, payment_method, amount, payment_date)
                    VALUES (:panier_id, :payment_method, :amount, :payment_date)
                """)
                
                session.execute(insert_payment, {
                    'panier_id': commande_details['id'],
                    'payment_method': payment_method,
                    'amount': amount,
                    'payment_date': datetime.now()
                })
                
                session.commit()
            
            # Rafraîchir l'affichage
            self.load_commandes()
            
            # Si une commande est sélectionnée, rafraîchir les détails
            if hasattr(self, 'selected_commande_id') and self.selected_commande_id:
                commande_details = self.commande_controller.get_commande_details(self.selected_commande_id)
                if commande_details:
                    self.update_details(commande_details)
            
            QMessageBox.information(self, "Succès", f"Paiement de {amount:.0f} FC enregistré avec succès.")
            
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
            
            # Préparer les données de la facture (format similaire au panier)
            invoice_data = {
                'reference': commande_details.get('numero_commande', f"CMD-{commande_details.get('id')}"),
                'order_date': commande_details.get('created_at'),
                'created_at': commande_details.get('created_at'),
                'status': 'Payée' if commande_details.get('montant_paye', 0) >= commande_details.get('total_final', 0) else 'Non payée',
                'client_nom': commande_details.get('client_name', 'Client anonyme'),
                'client_telephone': '',
                'client_email': '',
                'client_adresse': '',
                'items': [],  # À construire à partir des détails produits/services
                'subtotal_ht': commande_details.get('subtotal', 0),
                'tax_amount': 0.0,
                'total_ttc': commande_details.get('total_final', 0),
                'discount_amount': commande_details.get('remise_amount', 0),
                'total_net': commande_details.get('total_final', 0),
                'notes': commande_details.get('notes', ''),
                'payments': [{
                    'payment_date': commande_details.get('created_at'),
                    'amount': commande_details.get('montant_paye', 0),
                    'payment_method': commande_details.get('payment_method', ''),
                    'user_name': 'Utilisateur'
                }]
            }
            
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

            # Aperçu simplifié
            notes_preview = f" ({invoice_data['notes'][:50]}...)" if len(invoice_data['notes']) > 50 else f" ({invoice_data['notes']})" if invoice_data['notes'] else ""
            preview_text = f"""
N° Commande: {invoice_data['reference']}
Client: {invoice_data['client_nom']}
Total: {invoice_data['total_ttc']:.0f} FC
Paiement: {invoice_data['payments'][0]['payment_method']}
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
                        subprocess.run(['explorer', '/select,', result], shell=True, check=True)
                        QMessageBox.information(dialog, "Export réussi",
                                              f"La facture A4 a été exportée avec succès !\n\n"
                                              f"Fichier: {result}\n\n"
                                              "Le dossier contenant la facture a été ouvert.")
                    except Exception as open_error:
                        QMessageBox.information(dialog, "Export réussi",
                                              f"La facture A4 a été exportée avec succès !\n\n"
                                              f"Fichier: {result}\n\n"
                                              f"Erreur ouverture dossier: {open_error}")
                
                dialog.accept()
            else:
                QMessageBox.warning(dialog, "Erreur", f"Impossible de générer le document {print_type}.")
                
        except Exception as e:
            QMessageBox.critical(dialog, "Erreur", f"Erreur lors de l'impression: {e}")
            print(f"❌ Erreur _print_commande_invoice: {e}")
            
    def export_commandes(self):
        """Exporter les commandes"""
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
            
            # Utiliser le contrôleur pour l'export
            result = self.commande_controller.export_commandes(commandes, 'csv')
            QMessageBox.information(self, "Export", result)
            
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de l'export: {e}")
            print(f"❌ Erreur export_commandes: {e}")
        
    def refresh_data(self):
        """Actualiser les données (interface publique)"""
        self.load_commandes()