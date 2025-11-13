"""
Simple commandes view listing restau paniers
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel, QPushButton, QLineEdit, QHBoxLayout, QMessageBox
from ayanna_erp.modules.restaurant.controllers.commandes_controller import CommandesController


class CommandesView(QWidget):
    def __init__(self, entreprise_id=1, parent=None):
        super().__init__(parent)
        self.entreprise_id = entreprise_id
        self.controller = CommandesController(entreprise_id=self.entreprise_id)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        header_h = QHBoxLayout()
        header_h.addWidget(QLabel('Commandes restaurant'))
        # recherche par produit
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText('Rechercher produit...')
        self.search_edit.textChanged.connect(self.load_commandes)
        header_h.addStretch()
        header_h.addWidget(self.search_edit)
        layout.addLayout(header_h)
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        refresh_btn = QPushButton('Charger commandes')
        refresh_btn.clicked.connect(self.load_commandes)
        layout.addWidget(refresh_btn)
        self.load_commandes()

    def load_commandes(self):
        self.list_widget.clear()
        try:
            search_text = None
            try:
                t = self.search_edit.text().strip()
                if t:
                    search_text = t
            except Exception:
                search_text = None
            commandes = self.controller.list_commandes(product_search=search_text)
            # if user searched and nothing found, provide diagnostic info
            if search_text and not commandes:
                try:
                    diag = self.controller.inspect_recent_product_ids(limit=100)
                    # find any diag rows matching the search
                    matches = [d for d in diag if d.get('core_name') and search_text.lower() in d.get('core_name','').lower()]
                    if matches:
                        sample = matches[0]
                        QMessageBox.information(self, 'Diagnostic recherche',
                                                f"Produit trouvé dans les lignes (exemple): ligne_id={sample['ligne_id']}, panier_id={sample['panier_id']}, core_name={sample['core_name']}\n\nSi la recherche ne retourne rien, vérifie le scope entreprise_id.")
                    else:
                        QMessageBox.information(self, 'Diagnostic recherche',
                                                "Aucun produit correspondant trouvé dans les dernières lignes de restau_produit_panier."
                                                )
                except Exception as e:
                    print('Diag failed', e)
            for c in commandes:
                li = QListWidgetItem(f"#{c.id} - Table:{c.table_id} - {c.status} - {c.total_final:.2f}")
                self.list_widget.addItem(li)
        except Exception as e:
            print(f"Erreur load_commandes: {e}")
