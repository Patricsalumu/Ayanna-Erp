"""
Widget pour la gestion des fournisseurs
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QTextEdit, QFormLayout, QGroupBox,
    QSplitter, QHeaderView, QMessageBox, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from sqlalchemy.orm import Session

from ayanna_erp.modules.achats.controllers import AchatController
from ayanna_erp.modules.achats.models import CoreFournisseur


class FournisseurDialog(QDialog):
    """Dialog pour créer/modifier un fournisseur"""
    
    def __init__(self, parent=None, fournisseur=None):
        super().__init__(parent)
        self.fournisseur = fournisseur
        self.setWindowTitle("Nouveau Fournisseur" if not fournisseur else "Modifier Fournisseur")
        self.setModal(True)
        self.setMinimumSize(400, 300)
        
        self.setup_ui()
        
        if fournisseur:
            self.load_fournisseur_data()
    
    def setup_ui(self):
        """Configuration de l'interface"""
        layout = QVBoxLayout(self)
        
        # Formulaire
        form_layout = QFormLayout()
        
        self.nom_edit = QLineEdit()
        self.nom_edit.setPlaceholderText("Nom ou raison sociale")
        form_layout.addRow("Nom*:", self.nom_edit)
        
        self.telephone_edit = QLineEdit()
        self.telephone_edit.setPlaceholderText("Numéro de téléphone")
        form_layout.addRow("Téléphone:", self.telephone_edit)
        
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("adresse@email.com")
        form_layout.addRow("Email:", self.email_edit)
        
        self.adresse_edit = QTextEdit()
        self.adresse_edit.setPlaceholderText("Adresse complète")
        self.adresse_edit.setMaximumHeight(80)
        form_layout.addRow("Adresse:", self.adresse_edit)
        
        layout.addLayout(form_layout)
        
        # Boutons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addWidget(buttons)
    
    def load_fournisseur_data(self):
        """Charge les données du fournisseur à modifier"""
        if self.fournisseur:
            self.nom_edit.setText(self.fournisseur.nom or "")
            self.telephone_edit.setText(self.fournisseur.telephone or "")
            self.email_edit.setText(self.fournisseur.email or "")
            self.adresse_edit.setPlainText(self.fournisseur.adresse or "")
    
    def get_data(self):
        """Récupère les données saisies"""
        return {
            'nom': self.nom_edit.text().strip(),
            'telephone': self.telephone_edit.text().strip() or None,
            'email': self.email_edit.text().strip() or None,
            'adresse': self.adresse_edit.toPlainText().strip() or None
        }
    
    def validate_data(self):
        """Valide les données saisies"""
        data = self.get_data()
        if not data['nom']:
            QMessageBox.warning(self, "Erreur", "Le nom est obligatoire")
            return False
        return True


class FournisseursWidget(QWidget):
    """Widget principal pour la gestion des fournisseurs"""
    
    fournisseur_created = pyqtSignal(int)
    fournisseur_updated = pyqtSignal(int)
    fournisseur_selected = pyqtSignal(int)
    
    def __init__(self, achat_controller: AchatController):
        super().__init__()
        self.achat_controller = achat_controller
        self.current_fournisseurs = []
        
        self.setup_ui()
        self.refresh_data()
    
    def setup_ui(self):
        """Configuration de l'interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # En-tête avec boutons d'action
        header_layout = QHBoxLayout()
        
        title_label = QLabel("👥 Gestion des Fournisseurs")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2C3E50;")
        
        # Barre de recherche
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Rechercher un fournisseur...")
        self.search_edit.textChanged.connect(self.on_search_changed)
        self.search_edit.setMaximumWidth(300)
        
        # Boutons d'action
        self.new_btn = QPushButton("➕ Nouveau")
        self.new_btn.clicked.connect(self.show_new_form)
        self.new_btn.setStyleSheet("""
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
        
        self.edit_btn = QPushButton("✏️ Modifier")
        self.edit_btn.clicked.connect(self.edit_selected)
        self.edit_btn.setEnabled(False)
        
        self.delete_btn = QPushButton("🗑️ Supprimer")
        self.delete_btn.clicked.connect(self.delete_selected)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
            QPushButton:disabled {
                background-color: #BDC3C7;
            }
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.search_edit)
        header_layout.addWidget(self.new_btn)
        header_layout.addWidget(self.edit_btn)
        header_layout.addWidget(self.delete_btn)
        
        layout.addLayout(header_layout)
        
        # Table des fournisseurs
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nom", "Téléphone", "Email", "Date création"
        ])
        
        # Configuration de la table
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.table.doubleClicked.connect(self.edit_selected)
        
        layout.addWidget(self.table)
    
    def refresh_data(self):
        """Actualise la liste des fournisseurs"""
        try:
            session = self.achat_controller.db_manager.get_session()
            self.current_fournisseurs = self.achat_controller.get_fournisseurs(
                session, 
                search=self.search_edit.text() if hasattr(self, 'search_edit') else None
            )
            self.populate_table()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement: {str(e)}")
        finally:
            session.close()
    
    def populate_table(self):
        """Remplit la table avec les données des fournisseurs"""
        self.table.setRowCount(len(self.current_fournisseurs))
        
        for row, fournisseur in enumerate(self.current_fournisseurs):
            # ID
            self.table.setItem(row, 0, QTableWidgetItem(str(fournisseur.id)))
            
            # Nom
            self.table.setItem(row, 1, QTableWidgetItem(fournisseur.nom or ""))
            
            # Téléphone
            self.table.setItem(row, 2, QTableWidgetItem(fournisseur.telephone or ""))
            
            # Email
            self.table.setItem(row, 3, QTableWidgetItem(fournisseur.email or ""))
            
            # Date création
            date_str = fournisseur.created_at.strftime("%d/%m/%Y") if fournisseur.created_at else ""
            self.table.setItem(row, 4, QTableWidgetItem(date_str))
    
    def on_search_changed(self):
        """Recherche en temps réel"""
        self.refresh_data()
    
    def on_selection_changed(self):
        """Gestion de la sélection dans la table"""
        has_selection = len(self.table.selectionModel().selectedRows()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        
        if has_selection:
            row = self.table.selectionModel().selectedRows()[0].row()
            fournisseur = self.current_fournisseurs[row]
            self.fournisseur_selected.emit(fournisseur.id)
    
    def show_new_form(self):
        """Affiche le formulaire de création d'un nouveau fournisseur"""
        dialog = FournisseurDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if dialog.validate_data():
                self.create_fournisseur(dialog.get_data())
    
    def edit_selected(self):
        """Modifie le fournisseur sélectionné"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        fournisseur = self.current_fournisseurs[row]
        
        dialog = FournisseurDialog(self, fournisseur)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if dialog.validate_data():
                self.update_fournisseur(fournisseur.id, dialog.get_data())
    
    def delete_selected(self):
        """Supprime le fournisseur sélectionné"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        fournisseur = self.current_fournisseurs[row]
        
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            f"Êtes-vous sûr de vouloir supprimer le fournisseur '{fournisseur.nom}' ?\n\n"
            "Cette action est irréversible.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_fournisseur(fournisseur.id)
    
    def create_fournisseur(self, data):
        """Crée un nouveau fournisseur"""
        try:
            session = self.achat_controller.db_manager.get_session()
            fournisseur = self.achat_controller.create_fournisseur(session, **data)
            self.refresh_data()
            self.fournisseur_created.emit(fournisseur.id)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la création: {str(e)}")
        finally:
            session.close()
    
    def update_fournisseur(self, fournisseur_id, data):
        """Met à jour un fournisseur"""
        try:
            session = self.achat_controller.db_manager.get_session()
            self.achat_controller.update_fournisseur(session, fournisseur_id, **data)
            self.refresh_data()
            self.fournisseur_updated.emit(fournisseur_id)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la modification: {str(e)}")
        finally:
            session.close()
    
    def delete_fournisseur(self, fournisseur_id):
        """Supprime un fournisseur"""
        try:
            session = self.achat_controller.db_manager.get_session()
            fournisseur = session.query(CoreFournisseur).get(fournisseur_id)
            if fournisseur:
                session.delete(fournisseur)
                session.commit()
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression: {str(e)}")
        finally:
            session.close()