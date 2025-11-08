"""
Simple commandes view listing restau paniers
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel, QPushButton
from ayanna_erp.modules.restaurant.controllers.commandes_controller import CommandesController


class CommandesView(QWidget):
    def __init__(self, entreprise_id=1, parent=None):
        super().__init__(parent)
        self.entreprise_id = entreprise_id
        self.controller = CommandesController(entreprise_id=self.entreprise_id)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Commandes restaurant'))
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        refresh_btn = QPushButton('Charger commandes')
        refresh_btn.clicked.connect(self.load_commandes)
        layout.addWidget(refresh_btn)
        self.load_commandes()

    def load_commandes(self):
        self.list_widget.clear()
        try:
            commandes = self.controller.list_commandes()
            for c in commandes:
                li = QListWidgetItem(f"#{c.id} - Table:{c.table_id} - {c.status} - {c.total_final:.2f}")
                self.list_widget.addItem(li)
        except Exception as e:
            print(f"Erreur load_commandes: {e}")
