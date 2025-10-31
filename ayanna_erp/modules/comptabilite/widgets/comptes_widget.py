"""
ComptesWidget - Onglet Comptes Comptables
CRUD sur les comptes, export PDF.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableView, QPushButton, QHBoxLayout, QLabel, QFrame, QLineEdit
from PyQt6.QtGui import QStandardItemModel

class ComptesWidget(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.session = getattr(controller, 'session', None)
        self.entreprise_id = getattr(parent, 'entreprise_id', None) if parent is not None else None
        # Pré-charger la devise de l'entreprise via le parent
        if parent and hasattr(parent, 'get_currency_symbol'):
            try:
                self.devise = parent.get_currency_symbol()
            except Exception as e:
                print(f"[DEBUG] ComptesWidget: Erreur lors de l'obtention de la devise: {e}")
                self.devise = "€"  # Fallback
        else:
            print(f"[DEBUG] ComptesWidget: parent sans get_currency_symbol(), devise par défaut")
            self.devise = "€"  # Fallback
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12,12,12,12)

        # Header
        header = QFrame()
        header.setStyleSheet('''
            QFrame { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #8E44AD, stop:1 #1565C0); border-radius:8px; padding:6px }
            QLabel { color: white; font-weight: bold }
        ''')
        h_layout = QHBoxLayout(header)
        title = QLabel("📚 Comptes comptables")
        title.setStyleSheet('font-size:16px')
        h_layout.addWidget(title)
        h_layout.addStretch()
        self.layout.addWidget(header)

        # Search + actions
        action_frame = QFrame()
        a_layout = QHBoxLayout(action_frame)
        a_layout.setContentsMargins(0,6,0,6)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher numéro, nom, libellé...")
        self.search_input.textChanged.connect(self.load_data)
        a_layout.addWidget(self.search_input)
        refresh_btn = QPushButton("🔄")
        refresh_btn.clicked.connect(self.load_data)
        a_layout.addWidget(refresh_btn)

        self.layout.addWidget(action_frame)

        self.table = QTableView()
        self.model = QStandardItemModel()
        self.table.setModel(self.model)
        # Style uniforme
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(header.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        self.table.setStyleSheet('''
            QHeaderView::section {
                background-color: #8E44AD;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                padding: 8px 4px;
            }
            QTableView::item:selected {
                background-color: #e3f2fd;
                color: #8E44AD;
            }
        ''')
        self.layout.addWidget(self.table)
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Ajouter")
        self.edit_btn = QPushButton("Modifier")
        self.delete_btn = QPushButton("Supprimer")
        self.config_btn = QPushButton("Configurer comptes spéciaux")
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.config_btn)
        self.layout.addLayout(btn_layout)
        self.add_btn.clicked.connect(self.add_compte)
        self.edit_btn.clicked.connect(self.edit_compte)
        self.delete_btn.clicked.connect(self.delete_compte)
        self.config_btn.clicked.connect(self.open_config_dialog)
        self.load_data()

    def load_data(self):
        """Charge les comptes via le controller"""
        if not self.entreprise_id:
            return
        self._id_map = []
        data = self.controller.get_comptes(self.entreprise_id)
        # Filtrage local si une recherche est fournie
        try:
            query = self.search_input.text().strip().lower()
            if query:
                data = [d for d in data if query in str(d.get('numero','')).lower() or query in str(d.get('nom','')).lower() or query in str(d.get('libelle','')).lower()]
        except Exception:
            pass
        headers = ["Numéro", "Nom", "Libellé", "Classe"]
        self.model.clear()
        self.model.setHorizontalHeaderLabels(headers)
        for row in data:
            items = [
                self._item(str(row.get("numero", ""))),
                self._item(str(row.get("nom", ""))),
                self._item(str(row.get("libelle", ""))),
                self._item(str(row.get("classe", ""))),
            ]
            for item in items:
                item.setEditable(False)
            self.model.appendRow(items)
            self._id_map.append(row.get("id"))
        # Largeurs par défaut
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(1, 180)
        self.table.setColumnWidth(2, 250)
        self.table.setColumnWidth(3, 120)

    def _item(self, value):
        from PyQt6.QtGui import QStandardItem
        return QStandardItem(value)

    def add_compte(self):
        from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QComboBox, QDialogButtonBox, QMessageBox, QLabel
        from PyQt6.QtCore import Qt
        from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ClasseComptable
        dialog = QDialog(self)
        dialog.setWindowTitle("Ajouter un compte comptable")
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet('''
            QDialog { background: #fafafa; }
            QLineEdit, QComboBox { padding: 6px; font-size: 15px; border-radius: 4px; border: 1px solid #bdbdbd; }
            QLabel { font-weight: bold; font-size: 14px; }
        ''')
        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        numero_edit = QLineEdit()
        numero_edit.setPlaceholderText("Numéro de compte")
        nom_edit = QLineEdit()
        nom_edit.setPlaceholderText("Nom du compte")
        libelle_edit = QLineEdit()
        libelle_edit.setPlaceholderText("Libellé (description)")
        classe_combo = QComboBox()
        # Utiliser self.session pour récupérer les classes
        classes = self.session.query(ClasseComptable).filter(ClasseComptable.enterprise_id == self.entreprise_id).all()
        for c in classes:
            classe_combo.addItem(f"{c.code} - {c.nom}", c.id)
        layout.addRow(QLabel("Numéro :"), numero_edit)
        layout.addRow(QLabel("Nom :"), nom_edit)
        layout.addRow(QLabel("Libellé :"), libelle_edit)
        layout.addRow(QLabel("Classe :"), classe_combo)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addRow(btns)
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            numero = numero_edit.text().strip()
            nom = nom_edit.text().strip()
            libelle = libelle_edit.text().strip()
            if not numero:
                QMessageBox.critical(self, "Erreur", "Le champ 'Numéro' est obligatoire.")
                return self.add_compte()
            if not nom:
                QMessageBox.critical(self, "Erreur", "Le champ 'Nom' est obligatoire.")
                return self.add_compte()
            if not libelle:
                QMessageBox.critical(self, "Erreur", "Le champ 'Libellé' est obligatoire.")
                return self.add_compte()
            try:
                data = {
                    "numero": numero,
                    "nom": nom,
                    "libelle": libelle,
                    "classe_comptable_id": classe_combo.currentData(),
                }
                self.controller.add_compte(data)
                self.load_data()
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Succès", "Le compte comptable a été créé avec succès.")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def edit_compte(self):
        from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QComboBox, QDialogButtonBox, QMessageBox, QLabel
        from PyQt6.QtCore import Qt
        from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ClasseComptable
        index = self.table.currentIndex().row()
        if index < 0:
            return
        compte_id = self._id_map[index]
        comptes = self.controller.get_comptes(self.entreprise_id)
        compte = next((c for c in comptes if c["id"] == compte_id), None)
        if not compte:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Modifier le compte comptable")
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet('''
            QDialog { background: #fafafa; }
            QLineEdit, QComboBox { padding: 6px; font-size: 15px; border-radius: 4px; border: 1px solid #bdbdbd; }
            QLabel { font-weight: bold; font-size: 14px; }
        ''')
        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        numero_edit = QLineEdit(compte["numero"])
        nom_edit = QLineEdit(compte["nom"])
        libelle_edit = QLineEdit(compte.get("libelle", ""))
        classe_combo = QComboBox()
        classes = self.session.query(ClasseComptable).all()
        for c in classes:
            classe_combo.addItem(f"{c.code} - {c.nom}", c.id)
            if c.nom == compte["classe"]:
                classe_combo.setCurrentIndex(classe_combo.count()-1)
        layout.addRow(QLabel("Numéro :"), numero_edit)
        layout.addRow(QLabel("Nom :"), nom_edit)
        layout.addRow(QLabel("Libellé :"), libelle_edit)
        layout.addRow(QLabel("Classe :"), classe_combo)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addRow(btns)
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = {
                    "numero": numero_edit.text(),
                    "nom": nom_edit.text(),
                    "libelle": libelle_edit.text(),
                    "classe_comptable_id": classe_combo.currentData(),
                }
                self.controller.update_compte(compte_id, data)
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def delete_compte(self):
        from PyQt6.QtWidgets import QMessageBox
        index = self.table.currentIndex().row()
        if index < 0:
            return
        compte_id = self._id_map[index]
        confirm = QMessageBox.question(self, "Supprimer", "Supprimer ce compte ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.controller.delete_compte(compte_id)
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))


    def open_config_dialog(self):
        from PyQt6.QtWidgets import QDialog, QFormLayout, QComboBox, QDialogButtonBox, QMessageBox, QLabel
        from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import CompteComptable, ClasseComptable
        
        if not self.entreprise_id:
            QMessageBox.warning(self, "Erreur", "Aucune entreprise sélectionnée.")
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle("Configurer les comptes par point de vente")
        dialog.setMinimumWidth(500)
        dialog.setStyleSheet('''
            QDialog { background: #fafafa; }
            QComboBox { padding: 6px; font-size: 15px; border-radius: 4px; border: 1px solid #bdbdbd; }
            QLabel { font-weight: bold; font-size: 14px; }
        ''')
        
        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Sélection du point de vente
        pos_combo = QComboBox()
        pos_points = self.controller.get_pos_points(self.entreprise_id)
        for pos in pos_points:
            pos_combo.addItem(f"{pos.name}", pos.id)
        layout.addRow(QLabel("Point de vente :"), pos_combo)
        
        # Préparer les comptes par classe using controller methods
        comptes_caisse = self.controller.get_comptes_par_classe(self.entreprise_id, '5')  # Classe 5: Caisse/Banque
        comptes_client = self.controller.get_comptes_par_classe(self.entreprise_id, '4')  # Classe 4: Clients/Fournisseurs
        comptes_tva = self.controller.get_comptes_par_classe(self.entreprise_id, '44')    # Classe 44: TVA
        comptes_achat = self.controller.get_comptes_par_classe(self.entreprise_id, '6')   # Classe 6: Achats/Charges
        comptes_vente = self.controller.get_comptes_par_classe(self.entreprise_id, '7')   # Classe 7: Ventes/Produits/Remises
        compte_remise = self.controller.get_comptes_par_classe(self.entreprise_id, '6')  # Classe 6 aussi pour remises
        compte_stock = self.controller.get_comptes_par_classe(self.entreprise_id, '3')  # Classe 3: Stocks
        
        
        # Créer les ComboBox pour chaque type de compte
        caisse_combo = QComboBox()
        caisse_combo.addItem("-- Sélectionner --", None)
        for c in comptes_caisse:
            caisse_combo.addItem(f"{c.numero} - {c.nom}", c.id)
            
        banque_combo = QComboBox()
        banque_combo.addItem("-- Sélectionner --", None)
        for c in comptes_caisse:  # Classe 5 aussi pour banque
            banque_combo.addItem(f"{c.numero} - {c.nom}", c.id)
            
        client_combo = QComboBox()
        client_combo.addItem("-- Sélectionner --", None)
        for c in comptes_client:
            if str(c.numero).startswith('41'):  # Clients généralement 411
                client_combo.addItem(f"{c.numero} - {c.nom}", c.id)
        
        stock_combo = QComboBox()
        stock_combo.addItem("-- Sélectionner --", None)
        for c in compte_stock:
            if str(c.numero).startswith('3'):  # Stocks généralement 3xx
                stock_combo.addItem(f"{c.numero} - {c.nom}", c.id)
                
        fournisseur_combo = QComboBox()
        fournisseur_combo.addItem("-- Sélectionner --", None)
        for c in comptes_client:
            if str(c.numero).startswith('40'):  # Fournisseurs généralement 401
                fournisseur_combo.addItem(f"{c.numero} - {c.nom}", c.id)
                
        tva_combo = QComboBox()
        tva_combo.addItem("-- Sélectionner --", None)
        for c in comptes_tva:
            tva_combo.addItem(f"{c.numero} - {c.nom}", c.id)
            
        achat_combo = QComboBox()
        achat_combo.addItem("-- Sélectionner --", None)
        for c in comptes_achat:
            achat_combo.addItem(f"{c.numero} - {c.nom}", c.id)
            
        remise_combo = QComboBox()
        remise_combo.addItem("-- Sélectionner --", None)
        for c in compte_remise:
                remise_combo.addItem(f"{c.numero} - {c.nom}", c.id)
                
        vente_combo = QComboBox()
        vente_combo.addItem("-- Sélectionner --", None)
        for c in comptes_vente:
            vente_combo.addItem(f"{c.numero} - {c.nom}", c.id)
        
        # Ajouter les champs au formulaire
        layout.addRow(QLabel("Compte caisse (classe 5) :"), caisse_combo)
        layout.addRow(QLabel("Compte banque (classe 5) :"), banque_combo)
        layout.addRow(QLabel("Compte client (classe 4) :"), client_combo)
        layout.addRow(QLabel("Compte fournisseur (classe 4) :"), fournisseur_combo)
        layout.addRow(QLabel("Compte TVA (classe 44) :"), tva_combo)
        layout.addRow(QLabel("Compte achat (classe 6) :"), achat_combo)
        layout.addRow(QLabel("Compte remise (classe 6) :"), remise_combo)
        layout.addRow(QLabel("Compte stock (classe 3) :"), stock_combo)
        layout.addRow(QLabel("Compte Vente (Classe 7) :"), vente_combo)
        
        # Fonction pour charger la configuration d'un POS
        def load_config_for_pos():
            pos_id = pos_combo.currentData()
            if pos_id:
                config = self.controller.get_compte_config(self.entreprise_id, pos_id)
                if config:
                    # Sélectionner les valeurs existantes
                    self._set_combo_value(caisse_combo, config.compte_caisse_id)
                    self._set_combo_value(banque_combo, config.compte_banque_id)
                    self._set_combo_value(client_combo, config.compte_client_id)
                    self._set_combo_value(fournisseur_combo, config.compte_fournisseur_id)
                    self._set_combo_value(tva_combo, config.compte_tva_id)
                    self._set_combo_value(achat_combo, config.compte_achat_id)
                    self._set_combo_value(remise_combo, config.compte_remise_id)
                    self._set_combo_value(stock_combo, config.compte_stock_id)
                    self._set_combo_value(vente_combo, config.compte_vente_id)
                else:
                    # Remettre à zéro si pas de config
                    for combo in [caisse_combo, banque_combo, client_combo, fournisseur_combo, tva_combo, achat_combo, stock_combo, vente_combo, remise_combo]:
                        combo.setCurrentIndex(0)  # "-- Sélectionner --"
        
        # Connecter le changement de POS
        pos_combo.currentIndexChanged.connect(load_config_for_pos)
        
        # Charger la config du premier POS si disponible
        if pos_combo.count() > 0:
            load_config_for_pos()
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addRow(btns)
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            pos_id = pos_combo.currentData()
            if not pos_id:
                QMessageBox.critical(self, "Erreur", "Veuillez sélectionner un point de vente.")
                return self.open_config_dialog()
                
            try:
                self.controller.set_compte_config(
                    self.entreprise_id, 
                    pos_id,
                    compte_caisse_id=caisse_combo.currentData(),
                    compte_banque_id=banque_combo.currentData(),
                    compte_client_id=client_combo.currentData(),
                    compte_fournisseur_id=fournisseur_combo.currentData(),
                    compte_tva_id=tva_combo.currentData(),
                    compte_achat_id=achat_combo.currentData(),
                    compte_remise_id=remise_combo.currentData(),
                    compte_stock_id=stock_combo.currentData(),
                    compte_vente_id=vente_combo.currentData() 
                )
                QMessageBox.information(self, "Configuration enregistrée", 
                                      f"La configuration des comptes pour le point de vente '{pos_combo.currentText()}' a bien été enregistrée.")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))
    
    def _set_combo_value(self, combo, value):
        """Utilitaire pour sélectionner une valeur dans un ComboBox"""
        if value is not None:
            for i in range(combo.count()):
                if combo.itemData(i) == value:
                    combo.setCurrentIndex(i)
                    return
        combo.setCurrentIndex(0)  # "-- Sélectionner --" par défaut


