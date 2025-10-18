from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QGroupBox, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QFrame, QHeaderView
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class DashboardTab(QWidget):
    def __init__(self, parent=None, on_new_panier=None):
        super().__init__(parent)
        self.on_new_panier = on_new_panier
        self.setup_ui()
        self.load_dashboard_data()

    def create_card(self, title, value, color):
        """ Crée un widget style 'carte' pour les indicateurs """
        card = QFrame()
        card.setFixedHeight(80)  # Hauteur réduite
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 10px;
                padding: 6px;
            }}
            QLabel {{
                color: white;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        value_lbl = QLabel(value)
        value_lbl.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        layout.addWidget(title_lbl, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(value_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        return card, value_lbl

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)  # Marges réduites
        layout.setSpacing(8)

        dash_layout = QGridLayout()
        dash_layout.setSpacing(8)

        # 🔹 Indicateurs principaux sur une seule ligne
        card1, self.label_total_ventes = self.create_card("Total ventes", "... €", "#27ae60")
        card2, self.label_total_depenses = self.create_card("Dépenses", "... €", "#e74c3c")
        card3, self.label_total_creances = self.create_card("Créances", "... €", "#f39c12")
        card4, self.label_solde = self.create_card("Solde caisse", "... €", "#2980b9")

        dash_layout.addWidget(card1, 0, 0)
        dash_layout.addWidget(card2, 0, 1)
        dash_layout.addWidget(card3, 0, 2)
        dash_layout.addWidget(card4, 0, 3)

        # Top produits
        self.top_products_group = QGroupBox("⭐ Top produits achetés")
        self.top_products_group.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.top_products_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 6px;
                padding: 6px;
            }
        """)
        self.top_products_list = QTableWidget()
        self.top_products_list.setColumnCount(2)
        self.top_products_list.setHorizontalHeaderLabels(["Produit", "Qté"])
        self.top_products_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.top_products_list.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.top_products_list.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.top_products_list.setMaximumHeight(180)
        self.top_products_list.setStyleSheet("""
            QTableWidget {
                font-size: 11px;
                margin: 0px;
                padding: 0px;
            }
            QHeaderView::section {
                font-size: 12px;
                background-color: #ecf0f1;
                padding: 2px;
            }
        """)
        top_prod_layout = QVBoxLayout(self.top_products_group)
        top_prod_layout.setContentsMargins(4, 2, 4, 2)
        top_prod_layout.setSpacing(2)
        top_prod_layout.addWidget(self.top_products_list)
        dash_layout.addWidget(self.top_products_group, 1, 0, 1, 2)

        # Top clients
        self.top_clients_group = QGroupBox("👥 Top clients")
        self.top_clients_group.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.top_clients_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #2ecc71;
                border-radius: 8px;
                margin-top: 6px;
                padding: 6px;
            }
        """)
        self.top_clients_list = QTableWidget()
        self.top_clients_list.setColumnCount(2)
        self.top_clients_list.setHorizontalHeaderLabels(["Client", "Montant (€)"])
        self.top_clients_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.top_clients_list.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.top_clients_list.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.top_clients_list.setMaximumHeight(180)
        self.top_clients_list.setStyleSheet("""
            QTableWidget {
                font-size: 11px;
                margin: 0px;
                padding: 0px;
            }
            QHeaderView::section {
                font-size: 12px;
                background-color: #ecf0f1;
                padding: 2px;
            }
        """)
        top_cli_layout = QVBoxLayout(self.top_clients_group)
        top_cli_layout.setContentsMargins(4, 2, 4, 2)
        top_cli_layout.setSpacing(2)
        top_cli_layout.addWidget(self.top_clients_list)
        dash_layout.addWidget(self.top_clients_group, 1, 2, 1, 2)

        # Bouton ouvrir panier
        self.open_panier_btn = QPushButton("🛒 Ouvrir un nouveau panier")
        self.open_panier_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.open_panier_btn.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad;
                color: white;
                padding: 8px;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #9b59b6;
            }
        """)
        if self.on_new_panier:
            self.open_panier_btn.clicked.connect(self.on_new_panier)
        dash_layout.addWidget(self.open_panier_btn, 2, 0, 1, 4, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addLayout(dash_layout)

    def load_dashboard_data(self):
        # Données fictives pour l'UI
        stats = {
            'ventes': 125000.50,
            'depenses': 32000.00,
            'creances': 15000.00,
            'solde': 78000.50
        }
        self.label_total_ventes.setText(f"{stats['ventes']:.2f} €")
        self.label_total_depenses.setText(f"{stats['depenses']:.2f} €")
        self.label_total_creances.setText(f"{stats['creances']:.2f} €")
        self.label_solde.setText(f"{stats['solde']:.2f} €")

        top_products = [
            {'name': 'Pain', 'qty': 120},
            {'name': 'Lait', 'qty': 85},
            {'name': 'Riz', 'qty': 60},
            {'name': 'Savon', 'qty': 45},
            {'name': 'Sucre', 'qty': 40}
        ]
        self.top_products_list.setRowCount(len(top_products))
        for i, prod in enumerate(top_products):
            self.top_products_list.setItem(i, 0, QTableWidgetItem(prod['name']))
            self.top_products_list.setItem(i, 1, QTableWidgetItem(str(prod['qty'])))

        top_clients = [
            {'name': 'Kabasele Jean', 'amount': 35000.00},
            {'name': 'Mbuyi Marie', 'amount': 27000.00},
            {'name': 'Ngoy Pierre', 'amount': 18000.00},
            {'name': 'Tshibanda Paul', 'amount': 15000.00},
            {'name': 'Client anonyme', 'amount': 12000.00}
        ]
        self.top_clients_list.setRowCount(len(top_clients))
        for i, cli in enumerate(top_clients):
            self.top_clients_list.setItem(i, 0, QTableWidgetItem(cli['name']))
            self.top_clients_list.setItem(i, 1, QTableWidgetItem(f"{cli['amount']:.2f}"))
