"""
Widget de l'onglet Catégories - Gestion des catégories de produits
"""

from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton, 
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, 
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout, QTextEdit, 
    QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from ayanna_erp.database.database_manager import DatabaseManager
from ..model.models import ShopCategory


class CategorieIndex(QWidget):
    """Widget de gestion des catégories"""
    
    # Signaux
    category_updated = pyqtSignal()
    
    def __init__(self, boutique_controller, current_user):
        super().__init__()
        self.boutique_controller = boutique_controller
        self.current_user = current_user
        self.db_manager = DatabaseManager()
        
        self.setup_ui()
        self.load_categories()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # === HEADER ET ACTIONS ===
        header_group = QGroupBox("📂 Gestion des Catégories")
        header_layout = QVBoxLayout(header_group)
        
        # Ligne d'actions principales
        actions_layout = QHBoxLayout()
        
        self.new_category_btn = QPushButton("➕ Nouvelle Catégorie")
        self.new_category_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.new_category_btn.clicked.connect(self.create_new_category)
        actions_layout.addWidget(self.new_category_btn)
        
        actions_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.clicked.connect(self.load_categories)
        actions_layout.addWidget(refresh_btn)
        
        header_layout.addLayout(actions_layout)
        
        # Ligne de statistiques
        stats_layout = QHBoxLayout()
        
        self.total_categories_label = QLabel("Total: 0 catégories")
        self.total_categories_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        stats_layout.addWidget(self.total_categories_label)
        
        stats_layout.addStretch()
        
        self.active_categories_label = QLabel("Actives: 0")
        self.active_categories_label.setStyleSheet("color: #27AE60; font-weight: bold;")
        stats_layout.addWidget(self.active_categories_label)
        
        self.inactive_categories_label = QLabel("Inactives: 0")
        self.inactive_categories_label.setStyleSheet("color: #E74C3C; font-weight: bold;")
        stats_layout.addWidget(self.inactive_categories_label)
        
        header_layout.addLayout(stats_layout)
        main_layout.addWidget(header_group)
        
        # === TABLEAU DES CATÉGORIES ===
        self.categories_table = QTableWidget()
        self.categories_table.setColumnCount(6)
        self.categories_table.setHorizontalHeaderLabels([
            "ID", "Nom", "Description", "Nb Produits", "Statut", "Actions"
        ])
        
        # Configuration des colonnes
        header = self.categories_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Nom
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Description
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Nb Produits
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Statut
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Actions
        
        self.categories_table.setAlternatingRowColors(True)
        self.categories_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        main_layout.addWidget(self.categories_table)
    
    def load_categories(self):
        """Charger et afficher les catégories"""
        try:
            with self.db_manager.get_session() as session:
                # Récupérer toutes les catégories (actives et inactives)
                categories = session.query(ShopCategory).order_by(ShopCategory.name).all()
                
                self.populate_categories_table(categories)
                self.update_statistics(categories)
                
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des catégories: {str(e)}")
    
    def populate_categories_table(self, categories: List[ShopCategory]):
        """Peupler le tableau des catégories"""
        self.categories_table.setRowCount(len(categories))

        for row, category in enumerate(categories):
            # ID
            id_item = QTableWidgetItem(str(category.id))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.categories_table.setItem(row, 0, id_item)

            # Nom
            nom_item = QTableWidgetItem(category.name)
            if not category.is_active:
                nom_item.setForeground(QColor("#7F8C8D"))  # Gris pour les inactives
            self.categories_table.setItem(row, 1, nom_item)

            # Description
            description = category.description if category.description else "Aucune description"
            desc_item = QTableWidgetItem(description)
            if not category.is_active:
                desc_item.setForeground(QColor("#7F8C8D"))
            self.categories_table.setItem(row, 2, desc_item)

            # Nombre de produits
            try:
                products_count = len(category.products) if category.products else 0
                count_item = QTableWidgetItem(str(products_count))
                count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Colorer selon le nombre de produits
                if products_count == 0:
                    count_item.setBackground(QColor("#F39C12"))  # Orange
                    count_item.setForeground(QColor("white"))
                else:
                    count_item.setBackground(QColor("#27AE60"))  # Vert
                    count_item.setForeground(QColor("white"))

                self.categories_table.setItem(row, 3, count_item)
            except Exception:
                count_item = QTableWidgetItem("Err")
                count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.categories_table.setItem(row, 3, count_item)

            # Statut
            status_item = QTableWidgetItem("Actif" if category.is_active else "Inactif")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if category.is_active:
                status_item.setBackground(QColor("#27AE60"))  # Vert
                status_item.setForeground(QColor("white"))
            else:
                status_item.setBackground(QColor("#E74C3C"))  # Rouge
                status_item.setForeground(QColor("white"))
            self.categories_table.setItem(row, 4, status_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            # Bouton modifier
            edit_btn = QPushButton("✏️")
            edit_btn.setToolTip("Modifier la catégorie")
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498DB;
                    color: white;
                    font-weight: bold;
                    padding: 5px;
                    border: none;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #2980B9;
                }
            """)
            edit_btn.clicked.connect(lambda checked, c=category: self.edit_category(c))
            actions_layout.addWidget(edit_btn)
            
            # Bouton activer/désactiver
            toggle_btn = QPushButton("🔴" if category.is_active else "🟢")
            toggle_btn.setToolTip("Désactiver" if category.is_active else "Activer")
            toggle_btn.clicked.connect(lambda checked, c=category: self.toggle_category_status(c))
            actions_layout.addWidget(toggle_btn)
            
            # Bouton voir les produits
            if hasattr(category, 'products') and category.products:
                products_btn = QPushButton("👁️")
                products_btn.setToolTip("Voir les produits")
                products_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #9B59B6;
                        color: white;
                        font-weight: bold;
                        padding: 5px;
                        border: none;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #8E44AD;
                    }
                """)
                products_btn.clicked.connect(lambda checked, c=category: self.view_category_products(c))
                actions_layout.addWidget(products_btn)
            
            self.categories_table.setCellWidget(row, 5, actions_widget)
    
    def update_statistics(self, categories: List[ShopCategory]):
        """Mettre à jour les statistiques affichées"""
        total = len(categories)
        active = sum(1 for c in categories if c.is_active)
        inactive = total - active
        
        self.total_categories_label.setText(f"Total: {total} catégories")
        self.active_categories_label.setText(f"Actives: {active}")
        self.inactive_categories_label.setText(f"Inactives: {inactive}")
    
    def create_new_category(self):
        """Créer une nouvelle catégorie"""
        dialog = CategoryFormDialog(self, self.boutique_controller)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            category_data = dialog.get_category_data()
            
            try:
                with self.db_manager.get_session() as session:
                    new_category = self.boutique_controller.create_category(
                        session,
                        nom=category_data["nom"],
                        description=category_data.get("description")
                    )
                    
                    QMessageBox.information(self, "Succès", f"Catégorie '{new_category.name}' créée avec succès!")
                    self.load_categories()
                    self.category_updated.emit()
                    
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la création de la catégorie: {str(e)}")
    
    def edit_category(self, category: ShopCategory):
        """Modifier une catégorie existante"""
        dialog = CategoryFormDialog(self, self.boutique_controller, category)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            category_data = dialog.get_category_data()
            
            try:
                with self.db_manager.get_session() as session:
                    updated_category = self.boutique_controller.update_category(
                        session,
                        category.id,
                        nom=category_data["nom"],
                        description=category_data.get("description")
                    )
                    
                    QMessageBox.information(self, "Succès", f"Catégorie '{updated_category.name}' mise à jour avec succès!")
                    self.load_categories()
                    self.category_updated.emit()
                    
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la mise à jour de la catégorie: {str(e)}")
    
    def toggle_category_status(self, category: ShopCategory):
        """Activer/Désactiver une catégorie"""
        new_status = not category.is_active
        action = "activer" if new_status else "désactiver"
        
        # Vérifier s'il y a des produits dans cette catégorie
        products_count = len(category.products) if category.products else 0
        
        warning_text = f"Êtes-vous sûr de vouloir {action} la catégorie '{category.name}' ?"
        if not new_status and products_count > 0:
            warning_text += f"\n\nAttention: Cette catégorie contient {products_count} produit(s). "
            warning_text += "Les produits ne seront pas supprimés mais pourraient ne plus être visibles dans certains filtres."
        
        reply = QMessageBox.question(
            self, "Confirmation", 
            warning_text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with self.db_manager.get_session() as session:
                    updated_category = self.boutique_controller.update_category(
                        session, category.id, is_active=new_status
                    )
                    
                    QMessageBox.information(self, "Succès", f"Catégorie {action}ée avec succès!")
                    self.load_categories()
                    self.category_updated.emit()
                    
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la modification du statut: {str(e)}")
    
    def view_category_products(self, category: ShopCategory):
        """Afficher les produits d'une catégorie"""
        try:
            with self.db_manager.get_session() as session:
                products = self.boutique_controller.get_products(session, category_id=category.id)
                
                if not products:
                    QMessageBox.information(
                        self, "Aucun produit", 
                        f"Aucun produit trouvé dans la catégorie '{category.name}'."
                    )
                    return
                
                # Créer une liste des produits pour affichage
                products_list = []
                for product in products:
                    status = "Actif" if product.is_active else "Inactif"
                    products_list.append(f"• {product.name} - {product.price_unit:.2f}€ ({status})")
                
                products_text = "\n".join(products_list)
                
                QMessageBox.information(
                    self, f"Produits - {category.name}", 
                    f"Produits dans la catégorie '{category.name}':\n\n{products_text}"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'affichage des produits: {str(e)}")


class CategoryFormDialog(QDialog):
    """Dialog pour créer/modifier une catégorie"""
    
    def __init__(self, parent=None, boutique_controller=None, category: ShopCategory = None):
        super().__init__(parent)
        self.boutique_controller = boutique_controller
        self.category = category
        
        # Mode édition ou création
        self.is_editing = category is not None
        
        title = "Modifier la Catégorie" if self.is_editing else "Nouvelle Catégorie"
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(400, 300)
        
        self.setup_ui()
        
        if self.is_editing:
            self.load_category_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Formulaire
        form_layout = QFormLayout()
        
        # Nom de la catégorie
        self.nom_input = QLineEdit()
        self.nom_input.setPlaceholderText("Nom de la catégorie (obligatoire)")
        form_layout.addRow("Nom *:", self.nom_input)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        self.description_input.setPlaceholderText("Description de la catégorie (optionnel)")
        form_layout.addRow("Description:", self.description_input)
        
        # Statut (seulement en mode édition)
        if self.is_editing:
            self.active_checkbox = QCheckBox("Catégorie active")
            self.active_checkbox.setChecked(True)
            form_layout.addRow("Statut:", self.active_checkbox)
        
        layout.addLayout(form_layout)
        
        # Note d'aide
        help_text = QLabel(
            "💡 Astuce: Les catégories permettent d'organiser vos produits "
            "et de faciliter la navigation dans le catalogue."
        )
        help_text.setStyleSheet("""
            QLabel {
                background-color: #EBF5FB;
                border: 1px solid #3498DB;
                border-radius: 5px;
                padding: 8px;
                color: #1B4F72;
            }
        """)
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
        
        # Boutons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Validation
        buttons.button(QDialogButtonBox.StandardButton.Ok).clicked.connect(self.validate_form)
    
    def load_category_data(self):
        """Charger les données de la catégorie pour l'édition"""
        if self.category:
            self.nom_input.setText(self.category.name)
            
            if self.category.description:
                self.description_input.setPlainText(self.category.description)
            
            if hasattr(self, 'active_checkbox'):
                self.active_checkbox.setChecked(self.category.is_active)
    
    def validate_form(self):
        """Valider le formulaire avant acceptation"""
        if not self.nom_input.text().strip():
            QMessageBox.warning(self, "Erreur", "Le nom de la catégorie est obligatoire.")
            return False
        
        return True
    
    def get_category_data(self):
        """Récupérer les données de la catégorie"""
        data = {
            "nom": self.nom_input.text().strip(),
            "description": self.description_input.toPlainText().strip() or None
        }
        
        # Statut seulement en mode édition
        if self.is_editing and hasattr(self, 'active_checkbox'):
            data["is_active"] = self.active_checkbox.isChecked()
        
        return data
    
    def accept(self):
        """Accepter le dialog après validation"""
        if self.validate_form():
            super().accept()