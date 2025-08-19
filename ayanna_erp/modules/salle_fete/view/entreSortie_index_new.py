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
                            QDateTimeEdit, QHeaderView, QDateEdit, QDialog)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDateTime, QDate
from PyQt6.QtGui import QFont, QPixmap, QIcon, QAction
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from decimal import Decimal
from datetime import datetime, timedelta, date
import json


class DepenseDialog(QDialog):
    """Dialog pour enregistrer une dépense"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enregistrer une dépense")
        self.setModal(True)
        self.resize(400, 300)
        self.setup_ui()
    
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
        self.montant_spinbox.setRange(0.01, 999999.99)
        self.montant_spinbox.setDecimals(2)
        self.montant_spinbox.setSuffix(" €")
        form_layout.addRow("Montant *:", self.montant_spinbox)
        
        # Catégorie
        self.categorie_combo = QComboBox()
        self.categorie_combo.addItems([
            "Achat matériel",
            "Achat nourriture/boisson", 
            "Transport",
            "Service externe",
            "Maintenance",
            "Salaire personnel",
            "Frais généraux",
            "Autre"
        ])
        self.categorie_combo.setEditable(True)
        form_layout.addRow("Catégorie:", self.categorie_combo)
        
        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Description détaillée (optionnel)")
        form_layout.addRow("Description:", self.description_edit)
        
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
    
    def validate_and_accept(self):
        if not self.libelle_edit.text().strip():
            QMessageBox.warning(self, "Erreur", "Le libellé est obligatoire.")
            return
        if self.montant_spinbox.value() <= 0:
            QMessageBox.warning(self, "Erreur", "Le montant doit être supérieur à 0.")
            return
        self.accept()
    
    def get_data(self):
        return {
            'libelle': self.libelle_edit.text().strip(),
            'montant': self.montant_spinbox.value(),
            'categorie': self.categorie_combo.currentText().strip(),
            'description': self.description_edit.toPlainText().strip()
        }


class EntreeSortieIndex(QWidget):
    """Journal de Caisse - Gestion des entrées et sorties d'argent"""
    
    def __init__(self, main_controller, current_user):
        super().__init__(self)
        self.main_controller = main_controller
        self.current_user = current_user
        self.journal_data = []
        
        self.setup_ui()
        self.load_journal_data()
    
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
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # === FILTRES ===
        filters_group = QGroupBox("Filtres et Recherche")
        filters_layout = QHBoxLayout(filters_group)
        
        # Filtre par date
        filters_layout.addWidget(QLabel("Date:"))
        self.date_filter = QDateEdit()
        self.date_filter.setDate(QDate.currentDate())
        self.date_filter.setCalendarPopup(True)
        self.date_filter.setStyleSheet("""
            QDateEdit {
                padding: 8px;
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                background-color: white;
            }
        """)
        filters_layout.addWidget(self.date_filter)
        
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
        
        layout.addWidget(filters_group)
        
        # === TABLEAU DU JOURNAL ===
        table_group = QGroupBox("Journal des Opérations")
        table_layout = QVBoxLayout(table_group)
        
        self.journal_table = QTableWidget()
        self.journal_table.setColumnCount(7)
        self.journal_table.setHorizontalHeaderLabels([
            "Date/Heure", "Type", "Libellé", "Catégorie", "Entrée (€)", "Sortie (€)", "Utilisateur"
        ])
        
        # Configuration du tableau
        self.journal_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.journal_table.setAlternatingRowColors(True)
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
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Catégorie
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Entrée
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Sortie
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Utilisateur
        
        table_layout.addWidget(self.journal_table)
        layout.addWidget(table_group)
        
        # === STATISTIQUES ===
        stats_group = QGroupBox("Résumé de la journée")
        stats_layout = QHBoxLayout(stats_group)
        
        # Total Entrées
        self.total_entrees_label = QLabel("Total Entrées: 0.00 €")
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
        self.total_sorties_label = QLabel("Total Sorties: 0.00 €")
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
        self.solde_label = QLabel("Solde: 0.00 €")
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
        self.date_filter.dateChanged.connect(self.filter_journal)
        self.type_filter.currentTextChanged.connect(self.filter_journal)
        self.search_edit.textChanged.connect(self.filter_journal)
    
    def load_journal_data(self):
        """Charger les données du journal depuis la base de données"""
        try:
            # Charger les paiements reçus (entrées)
            from ayanna_erp.modules.salle_fete.controller.paiement_controller import PaiementController
            paiement_controller = PaiementController()
            
            # Obtenir la date sélectionnée
            selected_date = self.date_filter.date().toPython() if hasattr(self, 'date_filter') else date.today()
            
            # Récupérer les paiements du jour
            paiements = paiement_controller.get_payments_by_date(selected_date)
            
            # Convertir les paiements en entrées de journal
            self.journal_data = []
            
            for paiement in paiements:
                entry = {
                    'id': f"PAY_{paiement.id}",
                    'datetime': paiement.date_paiement,
                    'type': 'Entrée',
                    'libelle': f"Paiement réservation #{paiement.reservation_id}",
                    'categorie': 'Paiement client',
                    'montant_entree': float(paiement.montant),
                    'montant_sortie': 0.0,
                    'utilisateur': paiement.user_nom if hasattr(paiement, 'user_nom') else 'Système',
                    'description': f"Mode: {paiement.mode_paiement}"
                }
                self.journal_data.append(entry)
            
            # Charger les dépenses depuis un fichier JSON temporaire
            # (À remplacer par une vraie table de base de données plus tard)
            try:
                import json
                import os
                
                # Fichier temporaire pour stocker les dépenses
                depenses_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'depenses.json')
                
                if os.path.exists(depenses_file):
                    with open(depenses_file, 'r', encoding='utf-8') as f:
                        depenses = json.load(f)
                    
                    for depense in depenses:
                        # Filtrer par date si nécessaire
                        depense_date = datetime.fromisoformat(depense['datetime']).date()
                        if depense_date == selected_date:
                            entry = {
                                'id': depense['id'],
                                'datetime': datetime.fromisoformat(depense['datetime']),
                                'type': 'Sortie',
                                'libelle': depense['libelle'],
                                'categorie': depense['categorie'],
                                'montant_entree': 0.0,
                                'montant_sortie': depense['montant'],
                                'utilisateur': depense.get('utilisateur', self.current_user['nom']),
                                'description': depense.get('description', '')
                            }
                            self.journal_data.append(entry)
            
            except Exception as e:
                print(f"Erreur lors du chargement des dépenses: {e}")
            
            # Trier par date/heure décroissante
            self.journal_data.sort(key=lambda x: x['datetime'], reverse=True)
            
            # Mettre à jour l'affichage
            self.update_journal_display()
            
        except Exception as e:
            print(f"Erreur lors du chargement du journal: {e}")
            QMessageBox.warning(self, "Erreur", f"Impossible de charger les données: {str(e)}")
    
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
            if entry['type'] == 'Entrée':
                type_item.setBackground(Qt.GlobalColor.green)
                type_item.setForeground(Qt.GlobalColor.white)
            else:
                type_item.setBackground(Qt.GlobalColor.red)
                type_item.setForeground(Qt.GlobalColor.white)
            self.journal_table.setItem(row, 1, type_item)
            
            # Libellé
            self.journal_table.setItem(row, 2, QTableWidgetItem(entry['libelle']))
            
            # Catégorie
            self.journal_table.setItem(row, 3, QTableWidgetItem(entry['categorie']))
            
            # Montant Entrée
            if entry['montant_entree'] > 0:
                entree_item = QTableWidgetItem(f"{entry['montant_entree']:.2f}")
                entree_item.setForeground(Qt.GlobalColor.darkGreen)
                entree_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            else:
                entree_item = QTableWidgetItem("-")
                entree_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.journal_table.setItem(row, 4, entree_item)
            
            # Montant Sortie
            if entry['montant_sortie'] > 0:
                sortie_item = QTableWidgetItem(f"{entry['montant_sortie']:.2f}")
                sortie_item.setForeground(Qt.GlobalColor.darkRed)
                sortie_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            else:
                sortie_item = QTableWidgetItem("-")
                sortie_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.journal_table.setItem(row, 5, sortie_item)
            
            # Utilisateur
            self.journal_table.setItem(row, 6, QTableWidgetItem(entry['utilisateur']))
        
        # Mettre à jour les statistiques
        self.update_statistics(filtered_data)
    
    def get_filtered_data(self):
        """Obtenir les données filtrées selon les critères"""
        filtered_data = self.journal_data.copy()
        
        # Filtre par date
        if hasattr(self, 'date_filter'):
            selected_date = self.date_filter.date().toPython()
            filtered_data = [entry for entry in filtered_data 
                           if entry['datetime'].date() == selected_date]
        
        # Filtre par type
        if hasattr(self, 'type_filter'):
            type_filter = self.type_filter.currentText()
            if type_filter == "Entrées":
                filtered_data = [entry for entry in filtered_data if entry['type'] == 'Entrée']
            elif type_filter == "Sorties":
                filtered_data = [entry for entry in filtered_data if entry['type'] == 'Sortie']
        
        # Filtre par recherche
        if hasattr(self, 'search_edit'):
            search_text = self.search_edit.text().lower()
            if search_text:
                filtered_data = [entry for entry in filtered_data 
                               if search_text in entry['libelle'].lower() or 
                                  search_text in entry['categorie'].lower()]
        
        return filtered_data
    
    def update_statistics(self, data):
        """Mettre à jour les statistiques affichées"""
        total_entrees = sum(entry['montant_entree'] for entry in data)
        total_sorties = sum(entry['montant_sortie'] for entry in data)
        solde = total_entrees - total_sorties
        
        # Mettre à jour les labels
        self.total_entrees_label.setText(f"Total Entrées: {total_entrees:.2f} €")
        self.total_sorties_label.setText(f"Total Sorties: {total_sorties:.2f} €")
        
        # Couleur du solde selon le signe
        if solde >= 0:
            self.solde_label.setText(f"Solde: +{solde:.2f} €")
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
            self.solde_label.setText(f"Solde: {solde:.2f} €")
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
        self.load_journal_data()
    
    def show_depense_dialog(self):
        """Afficher le dialog pour enregistrer une dépense"""
        dialog = DepenseDialog(self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.save_depense(data)
    
    def save_depense(self, depense_data):
        """Sauvegarder une nouvelle dépense"""
        try:
            import json
            import os
            import uuid
            
            # Créer le dossier data s'il n'existe pas
            data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
            os.makedirs(data_dir, exist_ok=True)
            
            # Fichier temporaire pour stocker les dépenses
            depenses_file = os.path.join(data_dir, 'depenses.json')
            
            # Charger les dépenses existantes
            depenses = []
            if os.path.exists(depenses_file):
                with open(depenses_file, 'r', encoding='utf-8') as f:
                    depenses = json.load(f)
            
            # Ajouter la nouvelle dépense
            nouvelle_depense = {
                'id': f"DEP_{uuid.uuid4().hex[:8]}",
                'datetime': datetime.now().isoformat(),
                'libelle': depense_data['libelle'],
                'montant': depense_data['montant'],
                'categorie': depense_data['categorie'],
                'description': depense_data['description'],
                'utilisateur': self.current_user.get('nom', 'Utilisateur'),
                'user_id': self.current_user.get('id', 1)
            }
            
            depenses.append(nouvelle_depense)
            
            # Sauvegarder dans le fichier
            with open(depenses_file, 'w', encoding='utf-8') as f:
                json.dump(depenses, f, ensure_ascii=False, indent=2)
            
            # Recharger les données
            self.load_journal_data()
            
            QMessageBox.information(self, "Succès", "Dépense enregistrée avec succès!")
            
        except Exception as e:
            print(f"Erreur lors de la sauvegarde: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible d'enregistrer la dépense: {str(e)}")
    
    def export_to_pdf(self):
        """Exporter le journal en PDF"""
        try:
            from reportlab.lib.pagesizes import A4, letter
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.units import inch
            import os
            
            # Nom du fichier
            selected_date = self.date_filter.date().toPython()
            filename = f"journal_caisse_{selected_date.strftime('%Y%m%d')}.pdf"
            
            # Créer le document
            doc = SimpleDocTemplate(filename, pagesize=A4)
            story = []
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=1  # Center
            )
            
            # Titre
            title = Paragraph(f"Journal de Caisse - {selected_date.strftime('%d/%m/%Y')}", title_style)
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Données filtrées
            filtered_data = self.get_filtered_data()
            
            # Créer le tableau
            data = [["Date/Heure", "Type", "Libellé", "Catégorie", "Entrée (€)", "Sortie (€)", "Utilisateur"]]
            
            for entry in filtered_data:
                row = [
                    entry['datetime'].strftime("%d/%m/%Y %H:%M"),
                    entry['type'],
                    entry['libelle'][:30] + "..." if len(entry['libelle']) > 30 else entry['libelle'],
                    entry['categorie'],
                    f"{entry['montant_entree']:.2f}" if entry['montant_entree'] > 0 else "-",
                    f"{entry['montant_sortie']:.2f}" if entry['montant_sortie'] > 0 else "-",
                    entry['utilisateur']
                ]
                data.append(row)
            
            # Style du tableau
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
            story.append(Spacer(1, 20))
            
            # Statistiques
            total_entrees = sum(entry['montant_entree'] for entry in filtered_data)
            total_sorties = sum(entry['montant_sortie'] for entry in filtered_data)
            solde = total_entrees - total_sorties
            
            stats_data = [
                ["Total Entrées", f"{total_entrees:.2f} €"],
                ["Total Sorties", f"{total_sorties:.2f} €"],
                ["Solde", f"{solde:.2f} €"]
            ]
            
            stats_table = Table(stats_data)
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(stats_table)
            
            # Générer le PDF
            doc.build(story)
            
            QMessageBox.information(self, "Export réussi", f"Journal exporté vers: {filename}")
            
        except ImportError:
            QMessageBox.warning(self, "Erreur", "La bibliothèque reportlab n'est pas installée.\nInstallez-la avec: pip install reportlab")
        except Exception as e:
            print(f"Erreur lors de l'export PDF: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible d'exporter le PDF: {str(e)}")
