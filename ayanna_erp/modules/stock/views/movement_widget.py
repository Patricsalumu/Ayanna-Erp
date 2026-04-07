"""
Widget pour la gestion des mouvements de stock
Affiche tous les mouvements et permet les transferts entre entrepôts
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy import text
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton, 
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, 
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout, QTextEdit, 
    QDoubleSpinBox, QSpinBox, QCheckBox, QTabWidget, QTreeWidget, 
    QTreeWidgetItem, QSplitter, QProgressBar, QFrame, QDateEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QDate
from PyQt6.QtGui import QFont, QColor, QPixmap, QIcon

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.stock.controllers.stock_controller import StockController
from ayanna_erp.modules.stock.models import StockWarehouse


class TransferDialog(QDialog):
    """Dialog simple pour effectuer un transfert entre entrepôts"""
    
    def __init__(self, parent=None, entreprise_id=None):
        super().__init__(parent)
        self.entreprise_id = entreprise_id
        self.db_manager = DatabaseManager()
        self.controller = StockController(self.entreprise_id)
        
        self.setWindowTitle("Transfert entre Entrepôts")
        self.setFixedSize(500, 400)
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # Titre
        title = QLabel("Transférer un Produit entre Entrepôts")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Formulaire
        form_layout = QFormLayout()
        
        # Produit
        self.product_combo = QComboBox()
        self.product_combo.setEditable(True)
        form_layout.addRow("Produit*:", self.product_combo)
        
        # Entrepôt source
        self.source_warehouse_combo = QComboBox()
        self.source_warehouse_combo.currentTextChanged.connect(self.update_available_quantity)
        form_layout.addRow("Entrepôt Source*:", self.source_warehouse_combo)
        
        # Entrepôt destination
        self.dest_warehouse_combo = QComboBox()
        form_layout.addRow("Entrepôt Destination*:", self.dest_warehouse_combo)
        
        # Quantité disponible (info)
        self.available_label = QLabel("Quantité disponible: 0")
        self.available_label.setStyleSheet("color: #666; font-style: italic;")
        form_layout.addRow("", self.available_label)
        
        # Quantité à transférer
        self.quantity_spinbox = QDoubleSpinBox()
        self.quantity_spinbox.setRange(0.01, 999999)
        self.quantity_spinbox.setDecimals(2)
        self.quantity_spinbox.setSuffix(" unités")
        form_layout.addRow("Quantité à Transférer*:", self.quantity_spinbox)
        
        # Référence
        self.reference_edit = QLineEdit()
        self.reference_edit.setPlaceholderText("Référence du transfert (optionnel)")
        form_layout.addRow("Référence:", self.reference_edit)
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Notes ou commentaires (optionnel)")
        form_layout.addRow("Notes:", self.notes_edit)
        
        layout.addLayout(form_layout)
        
        # Boutons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_data(self):
        """Charger les données (produits et entrepôts)"""
        try:
            with self.db_manager.get_session() as session:
                # Charger les produits (avec stock > 0)
                products_result = session.execute(text("""
                    SELECT DISTINCT cp.id, cp.name, cp.code
                    FROM core_products cp
                    JOIN stock_produits_entrepot spe ON cp.id = spe.product_id
                    WHERE spe.quantity > 0
                    ORDER BY cp.name
                """))
                
                self.product_combo.clear()
                self.product_combo.addItem("-- Sélectionner un produit --", 0)
                for row in products_result:
                    self.product_combo.addItem(f"{row[1]} ({row[2]})", row[0])
                
                # Charger les entrepôts (actifs seulement)
                warehouses_result = session.execute(text("""
                    SELECT id, name, code
                    FROM stock_warehouses 
                    WHERE entreprise_id = :entreprise_id AND is_active = 1
                    ORDER BY name
                """), {"entreprise_id": self.entreprise_id})
                
                warehouses = [(row[0], f"{row[1]} ({row[2]})") for row in warehouses_result]
                
                # Remplir les combos d'entrepôts
                for combo in [self.source_warehouse_combo, self.dest_warehouse_combo]:
                    combo.clear()
                    combo.addItem("-- Sélectionner un entrepôt --", 0)
                    for warehouse_id, warehouse_name in warehouses:
                        combo.addItem(warehouse_name, warehouse_id)
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des données: {str(e)}")
    
    def update_available_quantity(self):
        """Mettre à jour la quantité disponible selon le produit et l'entrepôt source"""
        product_id = self.product_combo.currentData()
        warehouse_id = self.source_warehouse_combo.currentData()
        
        if product_id and warehouse_id and product_id > 0 and warehouse_id > 0:
            try:
                with self.db_manager.get_session() as session:
                    result = session.execute(text("""
                        SELECT quantity FROM stock_produits_entrepot
                        WHERE product_id = :product_id AND warehouse_id = :warehouse_id
                    """), {"product_id": product_id, "warehouse_id": warehouse_id})
                    
                    row = result.first()
                    quantity = float(row[0]) if row and row[0] else 0
                    self.available_label.setText(f"Quantité disponible: {quantity:.2f}")
                    self.quantity_spinbox.setMaximum(quantity)
            except Exception as e:
                self.available_label.setText("Erreur lors de la vérification")
        else:
            self.available_label.setText("Quantité disponible: 0")
            self.quantity_spinbox.setMaximum(0)
    
    def validate_and_accept(self):
        """Valider le formulaire avant de l'accepter"""
        product_id = self.product_combo.currentData()
        source_id = self.source_warehouse_combo.currentData()
        dest_id = self.dest_warehouse_combo.currentData()
        quantity = self.quantity_spinbox.value()
        
        # Validation
        if not product_id or product_id <= 0:
            QMessageBox.warning(self, "Validation", "Veuillez sélectionner un produit.")
            return
        
        if not source_id or source_id <= 0:
            QMessageBox.warning(self, "Validation", "Veuillez sélectionner un entrepôt source.")
            return
        
        if not dest_id or dest_id <= 0:
            QMessageBox.warning(self, "Validation", "Veuillez sélectionner un entrepôt destination.")
            return
        
        if source_id == dest_id:
            QMessageBox.warning(self, "Validation", "L'entrepôt source et destination doivent être différents.")
            return
        
        if quantity <= 0:
            QMessageBox.warning(self, "Validation", "La quantité doit être supérieure à 0.")
            return
        
        self.accept()
    
    def get_transfer_data(self):
        """Récupérer les données du transfert"""
        return {
            'product_id': self.product_combo.currentData(),
            'source_warehouse_id': self.source_warehouse_combo.currentData(),
            'dest_warehouse_id': self.dest_warehouse_combo.currentData(),
            'quantity': Decimal(str(self.quantity_spinbox.value())),
            'reference': self.reference_edit.text().strip() or None,
            'notes': self.notes_edit.toPlainText().strip() or None
        }


class MovementWidget(QWidget):
    """Widget principal pour la gestion des mouvements de stock"""
    
    # Signaux
    movement_created = pyqtSignal()
    movement_updated = pyqtSignal()
    
    def __init__(self, entreprise_id: int, current_user: dict = None):
        super().__init__()
        self.entreprise_id = entreprise_id
        # Gérer le cas où current_user est un objet User ou un dict
        if hasattr(current_user, 'id'):
            # Objet User
            self.current_user = {"id": current_user.id, "name": getattr(current_user, 'name', 'Utilisateur')}
        else:
            # Dict ou None
            self.current_user = current_user or {"id": 1, "name": "Utilisateur"}
        self.db_manager = DatabaseManager()
        self.controller = StockController(self.entreprise_id)
        
        self.setup_ui()
        self.load_movements()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # Titre et actions
        header_layout = QHBoxLayout()
        
        title = QLabel("📋 Mouvements de Stock")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Bouton pour nouveau transfert
        transfer_btn = QPushButton("🔄 Nouveau Transfert")
        transfer_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        transfer_btn.clicked.connect(self.show_transfer_dialog)
        header_layout.addWidget(transfer_btn)
        
        # Bouton de rafraîchissement
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.clicked.connect(self.load_movements)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Filtres
        filters_group = QGroupBox("Filtres")
        filters_layout = QHBoxLayout(filters_group)
        
        # Filtre par type
        filters_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Tous", "ENTREE", "SORTIE", "TRANSFERT", "AJUSTEMENT", "INVENTAIRE"
        ])
        self.type_combo.currentTextChanged.connect(self.load_movements)
        filters_layout.addWidget(self.type_combo)
        
        # Filtre par recherche
        filters_layout.addWidget(QLabel("Recherche:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Produit, référence, description...")
        self.search_edit.textChanged.connect(self.load_movements)
        filters_layout.addWidget(self.search_edit)
        
        filters_layout.addStretch()
        layout.addWidget(filters_group)
        
        # Tableau des mouvements
        self.movements_table = QTableWidget()
        self.movements_table.setColumnCount(11)
        self.movements_table.setHorizontalHeaderLabels([
            "Date", "Type", "Produit", "Entrepôt Origine", "Entrepôt Destination", 
            "Quantité", "Coût Unit.", "Coût Total", "Référence", "Description", "Utilisateur"
        ])
        
        # Configuration du tableau
        self.movements_table.setAlternatingRowColors(True)
        self.movements_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.movements_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.movements_table)
        
        # Statistiques en bas
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("Chargement...")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
    
    def show_transfer_dialog(self):
        """Afficher le dialog de transfert"""
        dialog = TransferDialog(self, self.entreprise_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            transfer_data = dialog.get_transfer_data()
            self.process_transfer(transfer_data)
    
    def process_transfer(self, transfer_data):
        """Traiter un transfert entre entrepôts"""
        try:
            with self.db_manager.get_session() as session:
                # Vérifier la quantité disponible
                source_result = session.execute(text("""
                    SELECT quantity FROM stock_produits_entrepot
                    WHERE product_id = :product_id AND warehouse_id = :warehouse_id
                """), {
                    "product_id": transfer_data['product_id'],
                    "warehouse_id": transfer_data['source_warehouse_id']
                })
                
                source_row = source_result.first()
                available_qty = float(source_row[0]) if source_row and source_row[0] else 0
                
                if available_qty < float(transfer_data['quantity']):
                    QMessageBox.warning(self, "Erreur", 
                                      f"Quantité insuffisante. Disponible: {available_qty:.2f}")
                    return
                
                # Décrémenter le stock source
                new_source_qty = available_qty - float(transfer_data['quantity'])
                session.execute(text("""
                    UPDATE stock_produits_entrepot 
                    SET quantity = :quantity, last_movement_date = CURRENT_TIMESTAMP
                    WHERE product_id = :product_id AND warehouse_id = :warehouse_id
                """), {
                    "quantity": new_source_qty,
                    "product_id": transfer_data['product_id'],
                    "warehouse_id": transfer_data['source_warehouse_id']
                })
                
                # Incrémenter le stock destination (ou créer l'entrée)
                dest_result = session.execute(text("""
                    SELECT quantity, unit_cost FROM stock_produits_entrepot
                    WHERE product_id = :product_id AND warehouse_id = :warehouse_id
                """), {
                    "product_id": transfer_data['product_id'],
                    "warehouse_id": transfer_data['dest_warehouse_id']
                })
                
                dest_row = dest_result.first()
                if dest_row:
                    # Mettre à jour le stock existant
                    new_dest_qty = float(dest_row[0]) + float(transfer_data['quantity'])
                    session.execute(text("""
                        UPDATE stock_produits_entrepot 
                        SET quantity = :quantity, last_movement_date = CURRENT_TIMESTAMP
                        WHERE product_id = :product_id AND warehouse_id = :warehouse_id
                    """), {
                        "quantity": new_dest_qty,
                        "product_id": transfer_data['product_id'],
                        "warehouse_id": transfer_data['dest_warehouse_id']
                    })
                    unit_cost = float(dest_row[1]) if dest_row[1] else 0
                else:
                    # Créer une nouvelle entrée (récupérer le coût depuis la source)
                    source_cost_result = session.execute(text("""
                        SELECT unit_cost FROM stock_produits_entrepot
                        WHERE product_id = :product_id AND warehouse_id = :warehouse_id
                    """), {
                        "product_id": transfer_data['product_id'],
                        "warehouse_id": transfer_data['source_warehouse_id']
                    })
                    
                    source_cost_row = source_cost_result.first()
                    unit_cost = float(source_cost_row[0]) if source_cost_row and source_cost_row[0] else 0
                    
                    session.execute(text("""
                        INSERT INTO stock_produits_entrepot 
                        (product_id, warehouse_id, quantity, unit_cost, total_cost, last_movement_date)
                        VALUES (:product_id, :warehouse_id, :quantity, :unit_cost, :total_cost, CURRENT_TIMESTAMP)
                    """), {
                        "product_id": transfer_data['product_id'],
                        "warehouse_id": transfer_data['dest_warehouse_id'],
                        "quantity": float(transfer_data['quantity']),
                        "unit_cost": unit_cost,
                        "total_cost": float(transfer_data['quantity']) * unit_cost
                    })
                
                # Enregistrer le mouvement de sortie (source)
                session.execute(text("""
                    INSERT INTO stock_mouvements 
                    (product_id, warehouse_id, destination_warehouse_id, movement_type, quantity, 
                     unit_cost, total_cost, reference, description, movement_date, user_id)
                    VALUES (:product_id, :warehouse_id, :dest_warehouse_id, 'TRANSFERT', :quantity,
                            :unit_cost, :total_cost, :reference, :description, CURRENT_TIMESTAMP, :user_id)
                """), {
                    "product_id": transfer_data['product_id'],
                    "warehouse_id": transfer_data['source_warehouse_id'],
                    "dest_warehouse_id": transfer_data['dest_warehouse_id'],
                    "quantity": -float(transfer_data['quantity']),  # Négatif pour sortie
                    "unit_cost": unit_cost,
                    "total_cost": -float(transfer_data['quantity']) * unit_cost,
                    "reference": transfer_data['reference'],
                    "description": f"Transfert vers entrepôt {transfer_data['dest_warehouse_id']}. {transfer_data['notes'] or ''}",
                    "user_id": self.current_user['id']
                })
                
                # Enregistrer le mouvement d'entrée (destination)
                session.execute(text("""
                    INSERT INTO stock_mouvements 
                    (product_id, warehouse_id, destination_warehouse_id, movement_type, quantity, 
                     unit_cost, total_cost, reference, description, movement_date, user_id)
                    VALUES (:product_id, :dest_warehouse_id, NULL, 'TRANSFERT', :quantity,
                            :unit_cost, :total_cost, :reference, :description, CURRENT_TIMESTAMP, :user_id)
                """), {
                    "product_id": transfer_data['product_id'],
                    "dest_warehouse_id": transfer_data['dest_warehouse_id'],
                    "quantity": float(transfer_data['quantity']),  # Positif pour entrée
                    "unit_cost": unit_cost,
                    "total_cost": float(transfer_data['quantity']) * unit_cost,
                    "reference": transfer_data['reference'],
                    "description": f"Transfert depuis entrepôt {transfer_data['source_warehouse_id']}. {transfer_data['notes'] or ''}",
                    "user_id": self.current_user['id']
                })
                
                session.commit()
                
                QMessageBox.information(self, "Succès", 
                                      f"Transfert de {transfer_data['quantity']} unités effectué avec succès!")
                
                # Rafraîchir l'affichage
                self.load_movements()
                self.movement_created.emit()
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du transfert: {str(e)}")
            print(f"Erreur transfert détaillée: {e}")
    
    def load_movements(self):
        """Charger tous les mouvements de stock"""
        try:
            with self.db_manager.get_session() as session:
                # Construire la requête avec filtres
                type_filter = self.type_combo.currentText()
                search_text = self.search_edit.text().strip()
                
                where_conditions = []
                params = {"entreprise_id": self.entreprise_id}
                
                if type_filter != "Tous":
                    where_conditions.append("sm.movement_type = :movement_type")
                    params["movement_type"] = type_filter
                
                if search_text:
                    where_conditions.append("""
                        (cp.name LIKE :search OR cp.code LIKE :search OR 
                         sm.reference LIKE :search OR sm.description LIKE :search)
                    """)
                    params["search"] = f"%{search_text}%"
                
                where_clause = " AND " + " AND ".join(where_conditions) if where_conditions else ""
                
                query = f"""
                    SELECT 
                        sm.movement_date,
                        sm.movement_type,
                        cp.name as product_name,
                        CASE 
                            WHEN sm.destination_warehouse_id IS NULL THEN 
                                CASE WHEN sm.movement_type = 'ENTREE' THEN 'Achat' ELSE sw_origin.name END
                            ELSE sw_origin.name 
                        END as origin_warehouse,
                        CASE 
                            WHEN sm.destination_warehouse_id IS NULL THEN sw_origin.name
                            ELSE sw_dest.name 
                        END as dest_warehouse,
                        sm.quantity,
                        sm.unit_cost,
                        sm.total_cost,
                        sm.reference,
                        sm.description,
                        'Utilisateur ' || COALESCE(sm.user_id, 0) as user_name
                    FROM stock_mouvements sm
                    LEFT JOIN core_products cp ON sm.product_id = cp.id
                    LEFT JOIN stock_warehouses sw_origin ON sm.warehouse_id = sw_origin.id
                    LEFT JOIN stock_warehouses sw_dest ON sm.destination_warehouse_id = sw_dest.id
                    WHERE sw_origin.entreprise_id = :entreprise_id
                    AND sw_origin.is_active = 1{where_clause}
                    ORDER BY sm.movement_date DESC
                    LIMIT 1000
                """
                
                result = session.execute(text(query), params)
                movements = result.fetchall()
                
                # Remplir le tableau
                self.movements_table.setRowCount(len(movements))
                
                for row, movement in enumerate(movements):
                    # Date - gérer les strings et datetime avec plus de robustesse
                    date_value = movement[0]
                    if date_value:
                        try:
                            if hasattr(date_value, 'strftime'):
                                # C'est un objet datetime
                                date_str = date_value.strftime("%d/%m/%Y %H:%M")
                            else:
                                # C'est probablement une string, essayons de la convertir
                                from datetime import datetime
                                if isinstance(date_value, str):
                                    # Essayer de parser la date string
                                    try:
                                        parsed_date = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                                        date_str = parsed_date.strftime("%d/%m/%Y %H:%M")
                                    except:
                                        # Si ça ne marche pas, utiliser la string telle quelle
                                        date_str = str(date_value)[:16]  # Limiter la longueur
                                else:
                                    date_str = str(date_value)
                        except Exception as e:
                            print(f"Erreur formatage date {date_value}: {e}")
                            date_str = str(date_value) if date_value else ""
                    else:
                        date_str = ""
                    
                    date_item = QTableWidgetItem(date_str)
                    self.movements_table.setItem(row, 0, date_item)
                    
                    # Type
                    type_item = QTableWidgetItem(movement[1] or "")
                    # Coloration par type
                    type_colors = {
                        'ENTREE': QColor("#E8F5E8"),     # Vert
                        'SORTIE': QColor("#F8D7DA"),     # Rouge
                        'TRANSFERT': QColor("#D1ECF1"),  # Bleu
                        'AJUSTEMENT': QColor("#FFF3CD"), # Jaune
                        'INVENTAIRE': QColor("#E2E3E5")  # Gris
                    }
                    if movement[1] in type_colors:
                        type_item.setBackground(type_colors[movement[1]])
                    self.movements_table.setItem(row, 1, type_item)
                    
                    # Produit
                    product_item = QTableWidgetItem(movement[2] or "")
                    self.movements_table.setItem(row, 2, product_item)
                    
                    # Entrepôt origine
                    origin_item = QTableWidgetItem(movement[3] or "")
                    self.movements_table.setItem(row, 3, origin_item)
                    
                    # Entrepôt destination
                    dest_item = QTableWidgetItem(movement[4] or "")
                    self.movements_table.setItem(row, 4, dest_item)
                    
                    # Quantité
                    qty_item = QTableWidgetItem(f"{movement[5]:.2f}" if movement[5] else "0")
                    qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.movements_table.setItem(row, 5, qty_item)
                    
                    # Coût unitaire
                    cost_item = QTableWidgetItem(f"{movement[6]:.2f}" if movement[6] else "0")
                    cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.movements_table.setItem(row, 6, cost_item)
                    
                    # Coût total
                    total_item = QTableWidgetItem(f"{movement[7]:.2f}" if movement[7] else "0")
                    total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.movements_table.setItem(row, 7, total_item)
                    
                    # Référence
                    ref_item = QTableWidgetItem(movement[8] or "")
                    self.movements_table.setItem(row, 8, ref_item)
                    
                    # Description
                    desc_item = QTableWidgetItem(movement[9] or "")
                    self.movements_table.setItem(row, 9, desc_item)
                    
                    # Utilisateur
                    user_item = QTableWidgetItem(movement[10] or "")
                    self.movements_table.setItem(row, 10, user_item)
                
                # Ajuster les colonnes
                self.movements_table.resizeColumnsToContents()
                
                # Mettre à jour les statistiques
                self.stats_label.setText(f"📊 {len(movements)} mouvements affichés")
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Erreur chargement mouvements: {e}")
            print(f"Détails de l'erreur: {error_details}")
            
            # Initialiser un tableau vide en cas d'erreur
            self.movements_table.setRowCount(0)
            self.stats_label.setText("❌ Erreur lors du chargement des mouvements")
            
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des mouvements: {str(e)}")


# Alias pour compatibilité
TransfertWidget = MovementWidget