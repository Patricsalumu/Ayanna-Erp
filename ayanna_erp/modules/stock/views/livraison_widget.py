"""
Widget Bons de Livraison — module Stock
Interface complète pour créer, livrer et réceptionner des bons de livraison interne.
"""

from __future__ import annotations

from decimal import Decimal
from datetime import datetime
from typing import List, Optional, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout, QTextEdit,
    QDoubleSpinBox, QFrame, QTabWidget, QGroupBox, QScrollArea,
    QSizePolicy, QAbstractItemView, QCheckBox, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QColor

from ayanna_erp.modules.stock.controllers.livraison_controller import LivraisonController
from ayanna_erp.utils.formatting import format_amount


def _user_id(user) -> int:
    """Retourne l'id de l'utilisateur (objet ORM ou dict)"""
    if user is None:
        return None
    if isinstance(user, dict):
        return user.get("id")
    return getattr(user, "id", None)


def _user_name(user) -> str:
    """Retourne le nom de l'utilisateur (objet ORM ou dict)"""
    if user is None:
        return ""
    if isinstance(user, dict):
        return user.get("name", user.get("username", ""))
    return getattr(user, "name", getattr(user, "username", ""))

# ─────────────────────────────────────────────────────────────────────────────
#  Couleurs de statut
# ─────────────────────────────────────────────────────────────────────────────
STATUT_COLORS = {
    'brouillon':   ('#6C757D', '#FFFFFF'),   # gris
    'livre':       ('#FD7E14', '#FFFFFF'),   # orange
    'receptionne': ('#198754', '#FFFFFF'),   # vert
    'annule':      ('#DC3545', '#FFFFFF'),   # rouge
}


def make_status_label(statut: str, label_text: str) -> QLabel:
    bg, fg = STATUT_COLORS.get(statut, ('#6C757D', '#FFFFFF'))
    lbl = QLabel(label_text)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet(
        f"background-color: {bg}; color: {fg}; border-radius: 4px; padding: 2px 8px; font-weight: bold;"
    )
    lbl.setFixedHeight(24)
    return lbl


# ─────────────────────────────────────────────────────────────────────────────
#  Dialog de sélection de produits
# ─────────────────────────────────────────────────────────────────────────────

class ProductSelectionDialog(QDialog):
    """
    Modal pour sélectionner des produits depuis l'entrepôt de départ.
    Affiche : Code, Nom, Catégorie, Qté Disponible, Prix Achat
    """
    products_selected = pyqtSignal(list)   # liste de dicts

    def __init__(self, products: List[Dict], parent=None):
        super().__init__(parent)
        self.all_products = products
        self.selected_products: List[Dict] = []

        self.setWindowTitle("Sélectionner des produits")
        self.setMinimumSize(820, 550)
        self.setModal(True)

        self._build_ui()
        self._populate_table(self.all_products)

    # ── Construction de l'interface ──────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Filtres
        filter_row = QHBoxLayout()

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍  Rechercher par nom ou code…")
        self.search_edit.textChanged.connect(self._apply_filters)
        filter_row.addWidget(self.search_edit, 2)

        self.cat_combo = QComboBox()
        self.cat_combo.addItem("Toutes les catégories", None)
        cats = sorted({p["category_name"] for p in self.all_products if p.get("category_name")})
        for c in cats:
            self.cat_combo.addItem(c, c)
        self.cat_combo.currentIndexChanged.connect(self._apply_filters)
        filter_row.addWidget(self.cat_combo, 1)

        layout.addLayout(filter_row)

        # Tableau
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["✓", "Code", "Nom", "Catégorie", "Qté Dispo", "Prix Achat"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("QTableWidget { font-size: 13px; }")
        layout.addWidget(self.table)

        # Boutons
        btn_row = QHBoxLayout()
        self.select_all_btn = QPushButton("Tout sélectionner")
        self.select_all_btn.clicked.connect(self._select_all)
        btn_row.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("Tout décocher")
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        btn_row.addWidget(self.deselect_all_btn)

        btn_row.addStretch()

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._confirm)
        btn_box.rejected.connect(self.reject)
        btn_row.addWidget(btn_box)

        layout.addLayout(btn_row)

    # ── Remplissage du tableau ────────────────────────────────────────────────

    def _populate_table(self, products: List[Dict]):
        self.table.setRowCount(0)
        for p in products:
            row = self.table.rowCount()
            self.table.insertRow(row)

            chk = QCheckBox()
            chk.setStyleSheet("QCheckBox { margin-left: 8px; }")
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.addWidget(chk)
            chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 0, chk_widget)

            self.table.setItem(row, 1, QTableWidgetItem(p.get("product_code", "")))
            self.table.setItem(row, 2, QTableWidgetItem(p.get("product_name", "")))
            self.table.setItem(row, 3, QTableWidgetItem(p.get("category_name", "")))
            dispo_item = QTableWidgetItem(f"{p['available']:.2f}")
            dispo_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 4, dispo_item)
            cost_item = QTableWidgetItem(format_amount(p.get("unit_cost", 0)))
            cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 5, cost_item)

            # stocker le dict produit dans le tag
            self.table.item(row, 1).setData(Qt.ItemDataRole.UserRole, p)

    def _apply_filters(self):
        text = self.search_edit.text().lower()
        cat = self.cat_combo.currentData()

        filtered = [
            p for p in self.all_products
            if (not text or text in p["product_name"].lower() or text in (p["product_code"] or "").lower())
            and (not cat or p.get("category_name") == cat)
        ]
        self._populate_table(filtered)

    # ── Actions ──────────────────────────────────────────────────────────────

    def _select_all(self):
        for row in range(self.table.rowCount()):
            w = self.table.cellWidget(row, 0)
            if w:
                chk = w.findChild(QCheckBox)
                if chk:
                    chk.setChecked(True)

    def _deselect_all(self):
        for row in range(self.table.rowCount()):
            w = self.table.cellWidget(row, 0)
            if w:
                chk = w.findChild(QCheckBox)
                if chk:
                    chk.setChecked(False)

    def _confirm(self):
        selected = []
        for row in range(self.table.rowCount()):
            w = self.table.cellWidget(row, 0)
            if w:
                chk = w.findChild(QCheckBox)
                if chk and chk.isChecked():
                    product = self.table.item(row, 1).data(Qt.ItemDataRole.UserRole)
                    if product:
                        selected.append(product)
        if not selected:
            QMessageBox.warning(self, "Sélection vide", "Veuillez sélectionner au moins un produit.")
            return
        self.products_selected.emit(selected)
        self.accept()


# ─────────────────────────────────────────────────────────────────────────────
#  Widget de création d'un nouveau bon de livraison
# ─────────────────────────────────────────────────────────────────────────────

class NouvelleLivraisonWidget(QWidget):
    """
    Formulaire de création d'un bon de livraison.
    Layout identique à NouvelleCommandeWidget :
      - Colonne gauche  : infos (entrepôts, date, notes)
      - Colonne droite  : lignes produits (tableau éditable)
    """
    livraison_created = pyqtSignal(int)   # ID du bon créé
    cancel_requested  = pyqtSignal()      # retour à la liste

    def __init__(self, entreprise_id: int, current_user: dict, parent=None):
        super().__init__(parent)
        self.entreprise_id = entreprise_id
        self.current_user  = current_user
        self.controller    = LivraisonController(entreprise_id)
        self.entrepots: List[Dict] = []
        self.lignes:    List[Dict] = []   # lignes du bon en cours de saisie
        self._build_ui()
        self._load_entrepots()

    # ── Construction ─────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # En-tête
        hdr = QLabel("📦 Nouveau Bon de Livraison")
        hdr.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        hdr.setStyleSheet("color: #2C3E50; padding-bottom: 4px;")
        root.addWidget(hdr)

        # Corps : 2 colonnes
        body = QHBoxLayout()
        body.setSpacing(12)

        # ── Colonne gauche : infos ───────────────────────────────────────────
        left = QGroupBox("Informations du bon")
        left.setMaximumWidth(340)
        left_layout = QFormLayout(left)
        left_layout.setSpacing(10)

        self.depart_combo = QComboBox()
        self.depart_combo.currentIndexChanged.connect(self._on_entrepot_changed)
        left_layout.addRow("Entrepôt de départ *:", self.depart_combo)

        self.arrivee_combo = QComboBox()
        left_layout.addRow("Entrepôt d'arrivée *:", self.arrivee_combo)

        self.date_label = QLabel(datetime.now().strftime("%d/%m/%Y"))
        self.date_label.setStyleSheet("font-weight: bold; color: #495057;")
        left_layout.addRow("Date :", self.date_label)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Notes (optionnel)…")
        self.notes_edit.setMaximumHeight(80)
        left_layout.addRow("Notes :", self.notes_edit)

        # Bouton ajouter produits
        self.add_products_btn = QPushButton("➕  Ajouter des produits")
        self.add_products_btn.setStyleSheet(
            "QPushButton { background-color: #3498DB; color: white; padding: 8px 14px; "
            "border-radius: 4px; font-weight: bold; } "
            "QPushButton:hover { background-color: #2980B9; }"
        )
        self.add_products_btn.clicked.connect(self._open_product_dialog)
        left_layout.addRow(self.add_products_btn)

        body.addWidget(left)

        # ── Colonne droite : tableau des lignes ──────────────────────────────
        right = QGroupBox("Lignes du bon de livraison")
        right_layout = QVBoxLayout(right)

        self.lines_table = QTableWidget(0, 7)
        self.lines_table.setHorizontalHeaderLabels(
            ["Code", "Produit", "Qté Dispo", "Quantité", "Prix Achat", "Total", "Action"]
        )
        hh = self.lines_table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.lines_table.verticalHeader().setVisible(False)
        self.lines_table.setAlternatingRowColors(True)
        self.lines_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.lines_table.setStyleSheet("QTableWidget { font-size: 13px; }")
        right_layout.addWidget(self.lines_table)

        # Total
        total_row = QHBoxLayout()
        total_row.addStretch()
        self.total_label = QLabel("Valeur totale : <b>0</b>")
        self.total_label.setStyleSheet("font-size: 15px; color: #2C3E50;")
        total_row.addWidget(self.total_label)
        right_layout.addLayout(total_row)

        body.addWidget(right, 1)
        root.addLayout(body, 1)

        # ── Boutons de bas de page ───────────────────────────────────────────
        footer = QHBoxLayout()
        footer.addStretch()

        cancel_btn = QPushButton("Annuler")
        cancel_btn.setStyleSheet(
            "QPushButton { background-color: #6C757D; color: white; padding: 8px 18px; "
            "border-radius: 4px; font-weight: bold; } "
            "QPushButton:hover { background-color: #5A6268; }"
        )
        cancel_btn.clicked.connect(self.cancel_requested.emit)
        footer.addWidget(cancel_btn)

        save_btn = QPushButton("💾  Enregistrer le bon")
        save_btn.setStyleSheet(
            "QPushButton { background-color: #27AE60; color: white; padding: 8px 18px; "
            "border-radius: 4px; font-weight: bold; } "
            "QPushButton:hover { background-color: #1E8449; }"
        )
        save_btn.clicked.connect(self._save_livraison)
        footer.addWidget(save_btn)

        root.addLayout(footer)

    # ── Données ──────────────────────────────────────────────────────────────

    def _load_entrepots(self):
        self.entrepots = self.controller.get_entrepots()
        for combo in (self.depart_combo, self.arrivee_combo):
            combo.blockSignals(True)
            combo.clear()
            for e in self.entrepots:
                combo.addItem(f"{e['name']} ({e['code']})", e['id'])
            combo.blockSignals(False)
        # Si au moins 2 entrepôts, mettre l'arrivée sur le 2e
        if len(self.entrepots) >= 2:
            self.arrivee_combo.setCurrentIndex(1)

    def _on_entrepot_changed(self):
        """Vide les lignes si l'entrepôt de départ change"""
        if self.lignes:
            rep = QMessageBox.question(
                self, "Changer d'entrepôt",
                "Changer d'entrepôt de départ va supprimer toutes les lignes actuelles. Continuer ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if rep == QMessageBox.StandardButton.Yes:
                self.lignes.clear()
                self._refresh_lines_table()

    def _open_product_dialog(self):
        depart_id = self.depart_combo.currentData()
        if not depart_id:
            QMessageBox.warning(self, "Entrepôt manquant", "Veuillez sélectionner un entrepôt de départ.")
            return

        products = self.controller.get_produits_entrepot(depart_id)
        if not products:
            QMessageBox.information(
                self, "Aucun produit disponible",
                "L'entrepôt de départ ne contient aucun produit disponible."
            )
            return

        dlg = ProductSelectionDialog(products, self)
        dlg.products_selected.connect(self._add_products_to_lines)
        dlg.exec()

    def _add_products_to_lines(self, products: List[Dict]):
        """Ajoute les produits sélectionnés comme nouvelles lignes (sans doublons)"""
        existing_ids = {l["product_id"] for l in self.lignes}
        for p in products:
            if p["product_id"] not in existing_ids:
                self.lignes.append({
                    "product_id":    p["product_id"],
                    "product_name":  p["product_name"],
                    "product_code":  p["product_code"],
                    "available":     p["available"],
                    "quantite":      1.0,
                    "cout_unitaire": p["unit_cost"],
                    "total_ligne":   p["unit_cost"],
                })
                existing_ids.add(p["product_id"])
        self._refresh_lines_table()

    # ── Tableau de lignes ─────────────────────────────────────────────────────

    def _refresh_lines_table(self):
        self.lines_table.setRowCount(0)
        for idx, ligne in enumerate(self.lignes):
            self.lines_table.insertRow(idx)

            self.lines_table.setItem(idx, 0, QTableWidgetItem(ligne["product_code"]))
            self.lines_table.setItem(idx, 1, QTableWidgetItem(ligne["product_name"]))
            dispo_item = QTableWidgetItem(f"{ligne['available']:.2f}")
            dispo_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.lines_table.setItem(idx, 2, dispo_item)

            # Quantité — spinbox éditable
            qty_spin = QDoubleSpinBox()
            qty_spin.setRange(0.01, ligne["available"])
            qty_spin.setDecimals(2)
            qty_spin.setValue(ligne["quantite"])
            qty_spin.setStyleSheet("QDoubleSpinBox { padding: 2px 4px; }")
            qty_spin.valueChanged.connect(lambda v, i=idx: self._on_qty_changed(i, v))
            self.lines_table.setCellWidget(idx, 3, qty_spin)

            cost_item = QTableWidgetItem(format_amount(ligne["cout_unitaire"]))
            cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.lines_table.setItem(idx, 4, cost_item)

            total_item = QTableWidgetItem(format_amount(ligne["total_ligne"]))
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.lines_table.setItem(idx, 5, total_item)

            # Bouton supprimer
            del_btn = QPushButton("🗑")
            del_btn.setFixedWidth(36)
            del_btn.setStyleSheet(
                "QPushButton { background: #E74C3C; color: white; border-radius: 4px; }"
                "QPushButton:hover { background: #C0392B; }"
            )
            del_btn.clicked.connect(lambda _, i=idx: self._delete_line(i))
            self.lines_table.setCellWidget(idx, 6, del_btn)

        self._update_total()

    def _on_qty_changed(self, idx: int, value: float):
        if 0 <= idx < len(self.lignes):
            self.lignes[idx]["quantite"]    = value
            self.lignes[idx]["total_ligne"] = value * self.lignes[idx]["cout_unitaire"]
            # Mettre à jour la cellule total
            total_item = self.lines_table.item(idx, 5)
            if total_item:
                total_item.setText(format_amount(self.lignes[idx]["total_ligne"]))
            self._update_total()

    def _delete_line(self, idx: int):
        if 0 <= idx < len(self.lignes):
            self.lignes.pop(idx)
            self._refresh_lines_table()

    def _update_total(self):
        total = sum(l["total_ligne"] for l in self.lignes)
        self.total_label.setText(f"Valeur totale : <b>{format_amount(total)}</b>")

    # ── Sauvegarde ────────────────────────────────────────────────────────────

    def _save_livraison(self):
        depart_id  = self.depart_combo.currentData()
        arrivee_id = self.arrivee_combo.currentData()
        notes      = self.notes_edit.toPlainText().strip()

        if not depart_id:
            QMessageBox.warning(self, "Champ manquant", "Veuillez sélectionner l'entrepôt de départ.")
            return
        if not arrivee_id:
            QMessageBox.warning(self, "Champ manquant", "Veuillez sélectionner l'entrepôt d'arrivée.")
            return
        if depart_id == arrivee_id:
            QMessageBox.warning(self, "Erreur", "L'entrepôt de départ et d'arrivée doivent être différents.")
            return
        if not self.lignes:
            QMessageBox.warning(self, "Lignes vides", "Ajoutez au moins un produit au bon.")
            return

        try:
            livraison = self.controller.create_livraison(
                entrepot_depart_id=depart_id,
                entrepot_arrivee_id=arrivee_id,
                lignes=self.lignes,
                utilisateur_id=_user_id(self.current_user),
                utilisateur_nom=_user_name(self.current_user),
                notes=notes,
            )
            QMessageBox.information(
                self, "Bon créé",
                f"✅ Bon de livraison {livraison.numero} créé avec succès en statut Brouillon."
            )
            self.livraison_created.emit(livraison.id)

        except ValueError as e:
            QMessageBox.warning(self, "Erreur de validation", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de créer le bon :\n{e}")

    # ── Réinitialisation ──────────────────────────────────────────────────────

    def reset(self):
        self.depart_combo.setCurrentIndex(0)
        if len(self.entrepots) >= 2:
            self.arrivee_combo.setCurrentIndex(1)
        self.notes_edit.clear()
        self.lignes.clear()
        self._refresh_lines_table()


# ─────────────────────────────────────────────────────────────────────────────
#  Dialog de modification d'un bon de livraison (brouillon uniquement)
# ─────────────────────────────────────────────────────────────────────────────

class ModifierLivraisonDialog(QDialog):
    """
    Permet de modifier un bon de livraison en statut 'brouillon' :
    - Changer les entrepôts de départ / arrivée
    - Ajouter, supprimer ou modifier la quantité de chaque ligne
    """

    livraison_modified = pyqtSignal(int)

    def __init__(self, livraison_id: int, controller, entreprise_id: int,
                 current_user, parent=None):
        super().__init__(parent)
        self.livraison_id  = livraison_id
        self.controller    = controller
        self.entreprise_id = entreprise_id
        self.current_user  = current_user
        self.lignes: List[Dict] = []
        self.entrepots: List[Dict] = []
        self._produits_cache: Dict[int, List[Dict]] = {}

        self.setWindowTitle("Modifier le bon de livraison")
        self.setMinimumSize(960, 620)
        self.setModal(True)
        self._build_ui()
        self._load_data()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        hdr = QLabel("✏  Modifier le Bon de Livraison")
        hdr.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        hdr.setStyleSheet("color: #2C3E50; padding-bottom: 4px;")
        root.addWidget(hdr)

        body = QHBoxLayout()
        body.setSpacing(12)

        # ── Gauche : infos ───────────────────────────────────────────────────
        left = QGroupBox("Informations du bon")
        left.setMaximumWidth(340)
        left_layout = QFormLayout(left)
        left_layout.setSpacing(10)

        self.depart_combo = QComboBox()
        self.depart_combo.currentIndexChanged.connect(self._on_depart_changed)
        left_layout.addRow("Entrepôt de départ *:", self.depart_combo)

        self.arrivee_combo = QComboBox()
        left_layout.addRow("Entrepôt d'arrivée *:", self.arrivee_combo)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Notes (optionnel)…")
        self.notes_edit.setMaximumHeight(80)
        left_layout.addRow("Notes :", self.notes_edit)

        add_btn = QPushButton("➕  Ajouter des produits")
        add_btn.setStyleSheet(
            "QPushButton { background-color: #3498DB; color: white; padding: 8px 14px; "
            "border-radius: 4px; font-weight: bold; } "
            "QPushButton:hover { background-color: #2980B9; }"
        )
        add_btn.clicked.connect(self._open_product_dialog)
        left_layout.addRow(add_btn)

        body.addWidget(left)

        # ── Droite : tableau des lignes ──────────────────────────────────────
        right = QGroupBox("Lignes du bon")
        right_layout = QVBoxLayout(right)

        self.lines_table = QTableWidget(0, 7)
        self.lines_table.setHorizontalHeaderLabels(
            ["Code", "Produit", "Qté Dispo", "Quantité", "Prix Achat", "Total", "Action"]
        )
        hh = self.lines_table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.lines_table.verticalHeader().setVisible(False)
        self.lines_table.setAlternatingRowColors(True)
        self.lines_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.lines_table.setStyleSheet("QTableWidget { font-size: 13px; }")
        right_layout.addWidget(self.lines_table)

        total_row = QHBoxLayout()
        total_row.addStretch()
        self.total_label = QLabel("Valeur totale : <b>0</b>")
        self.total_label.setStyleSheet("font-size: 15px; color: #2C3E50;")
        total_row.addWidget(self.total_label)
        right_layout.addLayout(total_row)

        body.addWidget(right, 1)
        root.addLayout(body, 1)

        # ── Boutons du bas ───────────────────────────────────────────────────
        footer = QHBoxLayout()
        footer.addStretch()

        cancel_btn = QPushButton("Annuler")
        cancel_btn.setStyleSheet(
            "QPushButton { background-color: #6C757D; color: white; padding: 8px 18px; "
            "border-radius: 4px; font-weight: bold; } "
            "QPushButton:hover { background-color: #5A6268; }"
        )
        cancel_btn.clicked.connect(self.reject)
        footer.addWidget(cancel_btn)

        save_btn = QPushButton("💾  Enregistrer les modifications")
        save_btn.setStyleSheet(
            "QPushButton { background-color: #27AE60; color: white; padding: 8px 18px; "
            "border-radius: 4px; font-weight: bold; } "
            "QPushButton:hover { background-color: #1E8449; }"
        )
        save_btn.clicked.connect(self._save)
        footer.addWidget(save_btn)

        root.addLayout(footer)

    # ── Données ───────────────────────────────────────────────────────────────

    def _load_data(self):
        """Charge les entrepôts puis pré-remplit avec les données du bon existant."""
        self.entrepots = self.controller.get_entrepots()

        for combo in (self.depart_combo, self.arrivee_combo):
            combo.blockSignals(True)
            combo.clear()
            for e in self.entrepots:
                combo.addItem(f"{e['name']} ({e['code']})", e['id'])
            combo.blockSignals(False)

        detail = self.controller.get_livraison_detail(self.livraison_id)
        if not detail:
            return

        for i, e in enumerate(self.entrepots):
            if e['id'] == detail['entrepot_depart_id']:
                self.depart_combo.blockSignals(True)
                self.depart_combo.setCurrentIndex(i)
                self.depart_combo.blockSignals(False)
            if e['id'] == detail['entrepot_arrivee_id']:
                self.arrivee_combo.setCurrentIndex(i)

        self.notes_edit.setPlainText(detail.get('notes') or '')

        depart_id = detail['entrepot_depart_id']
        produits_by_id = {p['product_id']: p for p in self._get_produits(depart_id)}

        self.lignes = []
        for l in detail['lignes']:
            prod = produits_by_id.get(l['product_id'], {})
            # Le stock n'a pas encore été déduit (brouillon) donc available est la valeur réelle
            available = prod.get('available', l['quantite'])
            # S'assurer que la quantité actuelle est au moins l'upper bound du spinbox
            available = max(available, l['quantite'])
            self.lignes.append({
                'product_id':    l['product_id'],
                'product_name':  l['product_name'],
                'product_code':  l['product_code'],
                'available':     available,
                'quantite':      l['quantite'],
                'cout_unitaire': l['cout_unitaire'],
                'total_ligne':   l['total_ligne'],
            })

        self._refresh_lines_table()

    def _get_produits(self, warehouse_id: int) -> List[Dict]:
        if warehouse_id not in self._produits_cache:
            self._produits_cache[warehouse_id] = self.controller.get_produits_entrepot(warehouse_id)
        return self._produits_cache[warehouse_id]

    def _on_depart_changed(self):
        if self.lignes:
            rep = QMessageBox.question(
                self, "Changer d'entrepôt",
                "Changer l'entrepôt de départ va supprimer toutes les lignes actuelles. Continuer ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if rep == QMessageBox.StandardButton.Yes:
                self.lignes.clear()
                self._produits_cache.clear()
                self._refresh_lines_table()

    def _open_product_dialog(self):
        depart_id = self.depart_combo.currentData()
        if not depart_id:
            QMessageBox.warning(self, "Entrepôt manquant", "Veuillez sélectionner un entrepôt de départ.")
            return
        products = self._get_produits(depart_id)
        if not products:
            QMessageBox.information(self, "Aucun produit disponible",
                                    "L'entrepôt de départ ne contient aucun produit disponible.")
            return
        dlg = ProductSelectionDialog(products, self)
        dlg.products_selected.connect(self._add_products_to_lines)
        dlg.exec()

    def _add_products_to_lines(self, products: List[Dict]):
        existing_ids = {l['product_id'] for l in self.lignes}
        for p in products:
            if p['product_id'] not in existing_ids:
                self.lignes.append({
                    'product_id':    p['product_id'],
                    'product_name':  p['product_name'],
                    'product_code':  p['product_code'],
                    'available':     p['available'],
                    'quantite':      1.0,
                    'cout_unitaire': p['unit_cost'],
                    'total_ligne':   p['unit_cost'],
                })
                existing_ids.add(p['product_id'])
        self._refresh_lines_table()

    # ── Tableau des lignes ────────────────────────────────────────────────────

    def _refresh_lines_table(self):
        self.lines_table.setRowCount(0)
        for idx, ligne in enumerate(self.lignes):
            self.lines_table.insertRow(idx)

            self.lines_table.setItem(idx, 0, QTableWidgetItem(ligne['product_code'] or ''))
            self.lines_table.setItem(idx, 1, QTableWidgetItem(ligne['product_name'] or ''))

            dispo_item = QTableWidgetItem(f"{ligne['available']:.2f}")
            dispo_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.lines_table.setItem(idx, 2, dispo_item)

            qty_spin = QDoubleSpinBox()
            qty_spin.setRange(0.01, max(ligne['available'], ligne['quantite']))
            qty_spin.setDecimals(2)
            qty_spin.setValue(ligne['quantite'])
            qty_spin.setStyleSheet("QDoubleSpinBox { padding: 2px 4px; }")
            qty_spin.valueChanged.connect(lambda v, i=idx: self._on_qty_changed(i, v))
            self.lines_table.setCellWidget(idx, 3, qty_spin)

            cost_item = QTableWidgetItem(format_amount(ligne['cout_unitaire']))
            cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.lines_table.setItem(idx, 4, cost_item)

            total_item = QTableWidgetItem(format_amount(ligne['total_ligne']))
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.lines_table.setItem(idx, 5, total_item)

            del_btn = QPushButton("🗑")
            del_btn.setFixedWidth(36)
            del_btn.setStyleSheet(
                "QPushButton { background: #E74C3C; color: white; border-radius: 4px; }"
                "QPushButton:hover { background: #C0392B; }"
            )
            del_btn.clicked.connect(lambda _, i=idx: self._delete_line(i))
            self.lines_table.setCellWidget(idx, 6, del_btn)

        self._update_total()

    def _on_qty_changed(self, idx: int, value: float):
        if 0 <= idx < len(self.lignes):
            self.lignes[idx]['quantite']    = value
            self.lignes[idx]['total_ligne'] = value * self.lignes[idx]['cout_unitaire']
            total_item = self.lines_table.item(idx, 5)
            if total_item:
                total_item.setText(format_amount(self.lignes[idx]['total_ligne']))
            self._update_total()

    def _delete_line(self, idx: int):
        if 0 <= idx < len(self.lignes):
            self.lignes.pop(idx)
            self._refresh_lines_table()

    def _update_total(self):
        total = sum(l['total_ligne'] for l in self.lignes)
        self.total_label.setText(f"Valeur totale : <b>{format_amount(total)}</b>")

    # ── Sauvegarde ────────────────────────────────────────────────────────────

    def _save(self):
        depart_id  = self.depart_combo.currentData()
        arrivee_id = self.arrivee_combo.currentData()
        notes      = self.notes_edit.toPlainText().strip()

        if not depart_id:
            QMessageBox.warning(self, "Champ manquant", "Veuillez sélectionner l'entrepôt de départ.")
            return
        if not arrivee_id:
            QMessageBox.warning(self, "Champ manquant", "Veuillez sélectionner l'entrepôt d'arrivée.")
            return
        if depart_id == arrivee_id:
            QMessageBox.warning(self, "Erreur", "L'entrepôt de départ et d'arrivée doivent être différents.")
            return
        if not self.lignes:
            QMessageBox.warning(self, "Lignes vides", "Ajoutez au moins un produit au bon.")
            return

        try:
            self.controller.modifier_livraison(
                livraison_id=self.livraison_id,
                entrepot_depart_id=depart_id,
                entrepot_arrivee_id=arrivee_id,
                lignes=self.lignes,
                notes=notes,
            )
            QMessageBox.information(self, "Succès", "✅ Bon de livraison modifié avec succès.")
            self.livraison_modified.emit(self.livraison_id)
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Erreur de validation", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de modifier le bon :\n{e}")


# ─────────────────────────────────────────────────────────────────────────────
#  Widget principal — Liste des bons de livraison
# ─────────────────────────────────────────────────────────────────────────────

class LivraisonWidget(QWidget):
    """
    Widget principal du module Livraisons.
    - Onglet "Liste"         : tableau de tous les bons + actions
    - Onglet "Nouveau bon"   : formulaire de création
    """

    def __init__(self, entreprise_id: int, current_user: dict, parent=None):
        super().__init__(parent)
        self.entreprise_id = entreprise_id
        self.current_user  = current_user
        self.controller    = LivraisonController(entreprise_id)
        self._build_ui()
        self._load_list()

    # ── Construction ─────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Statistiques
        self.stats_frame = self._build_stats_frame()
        root.addWidget(self.stats_frame)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #C0C0C0; background: white; }
            QTabBar::tab { background: #E0E0E0; padding: 8px 18px; margin-right: 2px;
                           border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #3498DB; color: white; font-weight: bold; }
            QTabBar::tab:hover { background: #BDC3C7; }
        """)
        root.addWidget(self.tabs, 1)

        # ── Onglet 1 : liste ────────────────────────────────────────────────
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(10, 10, 10, 10)

        # Barre d'outils liste
        toolbar = QHBoxLayout()

        self.filter_statut = QComboBox()
        self.filter_statut.addItem("Tous les statuts", None)
        for key, label in LivraisonController.STATUTS.items():
            self.filter_statut.addItem(label, key)
        self.filter_statut.currentIndexChanged.connect(self._load_list)
        toolbar.addWidget(QLabel("Statut :"))
        toolbar.addWidget(self.filter_statut)

        self.filter_search = QLineEdit()
        self.filter_search.setPlaceholderText("🔍  N° bon, entrepôt…")
        self.filter_search.textChanged.connect(self._apply_search_filter)
        toolbar.addWidget(self.filter_search, 1)

        refresh_btn = QPushButton("🔄  Actualiser")
        refresh_btn.clicked.connect(self._load_list)
        refresh_btn.setStyleSheet(
            "QPushButton { background: #3498DB; color: white; padding: 6px 14px; border-radius: 4px; }"
            "QPushButton:hover { background: #2980B9; }"
        )
        toolbar.addWidget(refresh_btn)

        new_btn = QPushButton("➕  Nouveau bon")
        new_btn.setStyleSheet(
            "QPushButton { background: #27AE60; color: white; padding: 6px 14px; border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background: #1E8449; }"
        )
        new_btn.clicked.connect(self._goto_new)
        toolbar.addWidget(new_btn)

        list_layout.addLayout(toolbar)

        # Tableau de la liste
        self.list_table = QTableWidget(0, 9)
        self.list_table.setHorizontalHeaderLabels(
            ["N° Bon", "Statut", "Départ", "Arrivée", "Lignes", "Valeur", "Créé le", "Utilisateur", "Actions"]
        )
        hh = self.list_table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self.list_table.setColumnWidth(8, 340)
        self.list_table.verticalHeader().setVisible(False)
        self.list_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.list_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.list_table.setAlternatingRowColors(True)
        self.list_table.setStyleSheet("QTableWidget { font-size: 13px; }")
        list_layout.addWidget(self.list_table)

        self.tabs.addTab(list_widget, "📋  Liste des bons")

        # ── Onglet 2 : nouveau bon ───────────────────────────────────────────
        self.nouvelle_widget = NouvelleLivraisonWidget(
            self.entreprise_id, self.current_user, self
        )
        self.nouvelle_widget.livraison_created.connect(self._on_livraison_created)
        self.nouvelle_widget.cancel_requested.connect(lambda: self.tabs.setCurrentIndex(0))
        self.tabs.addTab(self.nouvelle_widget, "➕  Nouveau bon")

    def _build_stats_frame(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame { background: #F8F9FA; border-bottom: 1px solid #DEE2E6; }
            QLabel { font-size: 12px; }
        """)
        frame.setMaximumHeight(54)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(14, 6, 14, 6)

        self.stats_labels: Dict[str, QLabel] = {}
        for key, label, color in [
            ("total",        "Total",         "#495057"),
            ("brouillons",   "Brouillons",     "#6C757D"),
            ("livres",       "Livrés",         "#FD7E14"),
            ("receptionnes", "Réceptionnés",   "#198754"),
            ("annules",      "Annulés",        "#DC3545"),
        ]:
            lbl = QLabel("0")
            lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14px;")
            layout.addWidget(QLabel(f"{label} :"))
            layout.addWidget(lbl)
            layout.addSpacing(18)
            self.stats_labels[key] = lbl

        layout.addStretch()
        return frame

    # ── Données ──────────────────────────────────────────────────────────────

    def _load_list(self):
        statut = self.filter_statut.currentData()
        self._all_rows = self.controller.get_livraisons(statut=statut)
        self._populate_table(self._all_rows)
        self._update_stats()

    def _apply_search_filter(self):
        text = self.filter_search.text().lower()
        if not text:
            self._populate_table(self._all_rows)
            return
        filtered = [
            r for r in self._all_rows
            if text in (r["numero"] or "").lower()
            or text in (r["depart"] or "").lower()
            or text in (r["arrivee"] or "").lower()
        ]
        self._populate_table(filtered)

    def _populate_table(self, rows: List[Dict]):
        self.list_table.setRowCount(0)
        for r in rows:
            row = self.list_table.rowCount()
            self.list_table.insertRow(row)

            self.list_table.setItem(row, 0, QTableWidgetItem(r["numero"] or ""))
            
            # Statut coloré
            st_label = make_status_label(r["statut"], r["statut_label"])
            st_widget = QWidget()
            st_layout = QHBoxLayout(st_widget)
            st_layout.addWidget(st_label)
            st_layout.setContentsMargins(4, 2, 4, 2)
            self.list_table.setCellWidget(row, 1, st_widget)

            self.list_table.setItem(row, 2, QTableWidgetItem(r["depart"] or ""))
            self.list_table.setItem(row, 3, QTableWidgetItem(r["arrivee"] or ""))

            nb_item = QTableWidgetItem(str(r["nb_lignes"]))
            nb_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_table.setItem(row, 4, nb_item)

            val_item = QTableWidgetItem(format_amount(r["valeur_totale"]))
            val_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.list_table.setItem(row, 5, val_item)

            date_str = ""
            if r["date_creation"]:
                try:
                    if isinstance(r["date_creation"], str):
                        date_str = r["date_creation"][:16]
                    else:
                        date_str = r["date_creation"].strftime("%d/%m/%Y %H:%M")
                except Exception:
                    date_str = str(r["date_creation"])[:16]
            self.list_table.setItem(row, 6, QTableWidgetItem(date_str))
            self.list_table.setItem(row, 7, QTableWidgetItem(r["utilisateur"] or ""))

            # Boutons d'action
            actions_widget = self._build_actions(r)
            self.list_table.setCellWidget(row, 8, actions_widget)
            self.list_table.setRowHeight(row, 42)

    def _build_actions(self, r: Dict) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        statut = r["statut"]
        lid = r["id"]

        if statut == 'brouillon':
            livrer_btn = QPushButton("✈ Livrer")
            livrer_btn.setFixedHeight(28)
            livrer_btn.setStyleSheet(
                "QPushButton { background: #FD7E14; color: white; border-radius: 3px; padding: 0 8px; font-size: 12px; }"
                "QPushButton:hover { background: #E96B00; }"
            )
            livrer_btn.clicked.connect(lambda _, i=lid: self._action_livrer(i))
            layout.addWidget(livrer_btn)

        if statut == 'livre':
            recept_btn = QPushButton("✅ Réceptionner")
            recept_btn.setFixedHeight(28)
            recept_btn.setStyleSheet(
                "QPushButton { background: #198754; color: white; border-radius: 3px; padding: 0 8px; font-size: 12px; }"
                "QPushButton:hover { background: #146C43; }"
            )
            recept_btn.clicked.connect(lambda _, i=lid: self._action_receptionner(i))
            layout.addWidget(recept_btn)

        # Annuler — brouillon ou livré
        if statut in ('brouillon', 'livre'):
            annuler_btn = QPushButton("✕ Annuler")
            annuler_btn.setFixedHeight(28)
            annuler_btn.setStyleSheet(
                "QPushButton { background: #DC3545; color: white; border-radius: 3px; padding: 0 8px; font-size: 12px; }"
                "QPushButton:hover { background: #B02A37; }"
            )
            annuler_btn.clicked.connect(lambda _, i=lid: self._action_annuler(i))
            layout.addWidget(annuler_btn)

        # Imprimer — tous sauf annulé
        if statut in ('brouillon', 'livre', 'receptionne'):
            print_btn = QPushButton("🖨 Imprimer")
            print_btn.setFixedHeight(28)
            print_btn.setStyleSheet(
                "QPushButton { background: #6C757D; color: white; border-radius: 3px; padding: 0 8px; font-size: 12px; }"
                "QPushButton:hover { background: #5A6268; }"
            )
            print_btn.clicked.connect(lambda _, i=lid: self._action_imprimer(i))
            layout.addWidget(print_btn)

        # Modifier — brouillon ou livré
        if statut in ('brouillon', 'livre'):
            mod_btn = QPushButton("✏ Modifier")
            mod_btn.setFixedHeight(28)
            mod_btn.setStyleSheet(
                "QPushButton { background: #17A2B8; color: white; border-radius: 3px; padding: 0 8px; font-size: 12px; }"
                "QPushButton:hover { background: #138496; }"
            )
            mod_btn.clicked.connect(lambda _, i=lid: self._action_modifier(i))
            layout.addWidget(mod_btn)

        layout.addStretch()
        return w

    def _update_stats(self):
        stats = self.controller.get_stats()
        for key, lbl in self.stats_labels.items():
            lbl.setText(str(stats.get(key, 0)))

    # ── Navigation ────────────────────────────────────────────────────────────

    def _goto_new(self):
        self.nouvelle_widget.reset()
        self.tabs.setCurrentIndex(1)

    def _on_livraison_created(self, livraison_id: int):
        self.tabs.setCurrentIndex(0)
        self._load_list()

    # ── Actions métier ────────────────────────────────────────────────────────

    def _action_livrer(self, lid: int):
        rep = QMessageBox.question(
            self, "Confirmer la livraison",
            "Êtes-vous sûr de vouloir passer ce bon en statut LIVRÉ ?\n"
            "Cette action va déduire les quantités de l'entrepôt de départ.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if rep != QMessageBox.StandardButton.Yes:
            return
        try:
            self.controller.livrer(
                lid,
                utilisateur_id=_user_id(self.current_user),
                utilisateur_nom=_user_name(self.current_user),
            )
            QMessageBox.information(self, "Succès", "✅ Bon de livraison passé en statut LIVRÉ.")
            self._load_list()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def _action_receptionner(self, lid: int):
        rep = QMessageBox.question(
            self, "Confirmer la réception",
            "Êtes-vous sûr de vouloir réceptionner ce bon ?\n"
            "Cette action va ajouter les quantités dans l'entrepôt d'arrivée.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if rep != QMessageBox.StandardButton.Yes:
            return
        try:
            self.controller.receptionner(
                lid,
                utilisateur_id=_user_id(self.current_user),
                utilisateur_nom=_user_name(self.current_user),
            )
            QMessageBox.information(self, "Succès", "✅ Bon réceptionné avec succès.")
            self._load_list()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def _action_annuler(self, lid: int):
        detail = self.controller.get_livraison_detail(lid)
        msg = "Êtes-vous sûr de vouloir annuler ce bon de livraison ?"
        if detail and detail.get('statut') == 'livre':
            msg = (
                "Ce bon est déjà LIVRÉ.\n"
                "L'annulation va réintégrer les quantités dans l'entrepôt de départ.\n\n"
                "Êtes-vous sûr de vouloir annuler ce bon ?"
            )
        rep = QMessageBox.question(
            self, "Annuler le bon", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if rep != QMessageBox.StandardButton.Yes:
            return
        try:
            self.controller.annuler(lid)
            QMessageBox.information(self, "Succès", "Bon de livraison annulé.")
            self._load_list()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def _action_modifier(self, lid: int):
        dlg = ModifierLivraisonDialog(
            lid, self.controller, self.entreprise_id, self.current_user, self
        )
        dlg.livraison_modified.connect(lambda _: self._load_list())
        dlg.exec()

    def _action_imprimer(self, lid: int):
        detail = self.controller.get_livraison_detail(lid)
        if not detail:
            QMessageBox.warning(self, "Erreur", "Bon introuvable.")
            return

        # Dialogue de choix du format d'impression
        dlg = QDialog(self)
        dlg.setWindowTitle("Format d'impression")
        dlg.setFixedSize(320, 140)
        dlg_layout = QVBoxLayout(dlg)
        dlg_layout.setSpacing(12)
        dlg_layout.setContentsMargins(20, 16, 20, 16)

        dlg_layout.addWidget(QLabel("Choisissez le format d'impression :"))

        btn_row = QHBoxLayout()

        btn_a4 = QPushButton("📄  Format A4")
        btn_a4.setFixedHeight(40)
        btn_a4.setStyleSheet(
            "QPushButton { background: #3498DB; color: white; border-radius: 5px; "
            "font-size: 13px; font-weight: bold; }"
            "QPushButton:hover { background: #2980B9; }"
        )
        btn_a4.clicked.connect(lambda: (dlg.accept(), self._print_bon(detail, format="a4")))
        btn_row.addWidget(btn_a4)

        btn_80 = QPushButton("🧾  Format 80mm")
        btn_80.setFixedHeight(40)
        btn_80.setStyleSheet(
            "QPushButton { background: #27AE60; color: white; border-radius: 5px; "
            "font-size: 13px; font-weight: bold; }"
            "QPushButton:hover { background: #1E8449; }"
        )
        btn_80.clicked.connect(lambda: (dlg.accept(), self._print_bon(detail, format="80mm")))
        btn_row.addWidget(btn_80)

        dlg_layout.addLayout(btn_row)

        btn_cancel = QPushButton("Annuler")
        btn_cancel.setStyleSheet("color: #6C757D;")
        btn_cancel.clicked.connect(dlg.reject)
        dlg_layout.addWidget(btn_cancel, alignment=Qt.AlignmentFlag.AlignRight)

        dlg.exec()

    # ── Impression ────────────────────────────────────────────────────────────

    def _print_bon(self, detail: Dict, format: str = "a4"):
        """
        Génère un PDF du bon de livraison via reportlab (même modèle que export_widgets.py).
        format = 'a4'   → A4 portrait, entête entreprise + logo, tableau, signatures
        format = '80mm' → Ticket thermique 80mm, entête compact, liste produits
        """
        import os, tempfile, subprocess
        from datetime import datetime as _dt

        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm, mm
        from reportlab.lib.colors import HexColor, black, white, grey
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, HRFlowable
        )
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

        from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
        from ayanna_erp.utils.formatting import format_amount_for_pdf

        # ── Infos entreprise ─────────────────────────────────────────────────
        ec = EntrepriseController()
        company = ec.get_company_info_for_pdf(self.entreprise_id)
        company_name = company.get('name') or 'Ayanna ERP'
        currency = ec.get_currency_symbol(self.entreprise_id)

        # ── Infos bon ────────────────────────────────────────────────────────
        date_str = ""
        dc = detail.get("date_creation")
        if dc:
            try:
                date_str = dc[:16] if isinstance(dc, str) else dc.strftime("%d/%m/%Y %H:%M")
            except Exception:
                date_str = str(dc)[:16]

        def fmt(amount):
            try:
                return format_amount_for_pdf(amount, currency)
            except Exception:
                return format_amount(amount)

        # ── Fichier de sortie ────────────────────────────────────────────────
        export_dir = os.path.join(os.getcwd(), "exports_commandes")
        os.makedirs(export_dir, exist_ok=True)
        ts = _dt.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(export_dir, f"bon_livraison_{detail['numero']}_{ts}.pdf")

        # ════════════════════════════════════════════════════════════════════
        #  FORMAT A4 PORTRAIT
        # ════════════════════════════════════════════════════════════════════
        if format == "a4":
            doc = SimpleDocTemplate(
                filename,
                pagesize=A4,
                leftMargin=2*cm, rightMargin=2*cm,
                topMargin=2*cm,  bottomMargin=2*cm,
            )
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle('BLTitle',  fontSize=14, fontName='Helvetica-Bold',
                                      alignment=TA_CENTER, spaceAfter=8,
                                      textColor=HexColor('#2C3E50')))
            styles.add(ParagraphStyle('BLSubtitle', fontSize=9, fontName='Helvetica',
                                      textColor=HexColor('#555555')))
            styles.add(ParagraphStyle('BLSmall', fontSize=8, fontName='Helvetica',
                                      textColor=HexColor('#777777')))
            styles.add(ParagraphStyle('BLRight', fontSize=9, fontName='Helvetica',
                                      alignment=TA_RIGHT))

            story = []
            logo_path = None

            # ── En-tête entreprise (même pattern que export_widgets.py) ──────
            company_text = (
                f"<b>{company.get('name', '')}</b><br/>"
                f"{company.get('address', '')}<br/>"
                f"{company.get('city', '')}<br/>"
                f"Tél : {company.get('phone', '')}"
            )
            if company.get('rccm'):
                company_text += f"<br/>RCCM : {company['rccm']}"
            if company.get('id_nat'):
                company_text += f"<br/>ID Nat : {company['id_nat']}"

            header_data = []
            if company.get('logo'):
                try:
                    tmp_logo = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                    tmp_logo.write(company['logo'])
                    logo_path = tmp_logo.name
                    tmp_logo.close()
                    logo_img = Image(logo_path, width=2.3*cm, height=2.3*cm)
                    header_data.append([logo_img, Paragraph(company_text, styles['Normal'])])
                except Exception:
                    header_data.append([Paragraph(company_text, styles['Normal']), ''])
            else:
                header_data.append([Paragraph(company_text, styles['Normal']), ''])

            header_tbl = Table(header_data, colWidths=[3*cm, 14*cm])
            header_tbl.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
            story.append(header_tbl)
            story.append(Spacer(1, 0.5*cm))
            story.append(HRFlowable(width='100%', thickness=1, color=HexColor('#3498DB')))
            story.append(Spacer(1, 0.3*cm))

            # ── Titre ─────────────────────────────────────────────────────────
            story.append(Paragraph("BON DE LIVRAISON INTERNE", styles['BLTitle']))
            story.append(Spacer(1, 0.3*cm))

            # ── Bloc infos bon ────────────────────────────────────────────────
            statut_colors = {
                'brouillon':   '#6C757D',
                'livre':       '#FD7E14',
                'receptionne': '#198754',
                'annule':      '#DC3545',
            }
            statut_color = statut_colors.get(detail['statut'], '#6C757D')

            info_data = [
                [
                    Paragraph(f"<b>N° Bon :</b> {detail['numero']}", styles['Normal']),
                    Paragraph(f"<b>Date :</b> {date_str}", styles['Normal']),
                ],
                [
                    Paragraph(f"<b>Entrepôt de départ :</b> {detail['depart']}", styles['Normal']),
                    Paragraph(f"<b>Entrepôt d'arrivée :</b> {detail['arrivee']}", styles['Normal']),
                ],
                [
                    Paragraph(
                        f"<b>Statut :</b> <font color='{statut_color}'><b>{detail['statut_label'].upper()}</b></font>",
                        styles['Normal']
                    ),
                    Paragraph(f"<b>Créé par :</b> {detail.get('utilisateur', '')}", styles['Normal']),
                ],
            ]
            if detail.get('notes'):
                info_data.append([
                    Paragraph(f"<b>Notes :</b> {detail['notes']}", styles['Normal']), ''
                ])

            info_tbl = Table(info_data, colWidths=[8.5*cm, 8.5*cm])
            info_tbl.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), HexColor('#F8F9FA')),
                ('BOX',        (0,0), (-1,-1), 0.5, HexColor('#DEE2E6')),
                ('INNERGRID',  (0,0), (-1,-1), 0.3, HexColor('#DEE2E6')),
                ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('LEFTPADDING',   (0,0), (-1,-1), 8),
            ]))
            story.append(info_tbl)
            story.append(Spacer(1, 0.4*cm))

            # ── Tableau des lignes ────────────────────────────────────────────
            col_headers = ['Code', 'Produit', 'Quantité', 'Prix Achat', 'Total']
            tbl_data = [col_headers]
            for l in detail['lignes']:
                tbl_data.append([
                    l['product_code'] or '',
                    l['product_name'] or '',
                    f"{l['quantite']:.2f}",
                    fmt(l['cout_unitaire']),
                    fmt(l['total_ligne']),
                ])
            tbl_data.append(['', '', '', 'TOTAL', fmt(detail['valeur_totale'])])

            n = len(tbl_data)
            lignes_tbl = Table(tbl_data, colWidths=[2.5*cm, 8*cm, 2.5*cm, 3*cm, 3*cm])
            lignes_tbl.setStyle(TableStyle([
                # En-tête
                ('BACKGROUND',    (0, 0), (-1, 0), HexColor('#2C3E50')),
                ('TEXTCOLOR',     (0, 0), (-1, 0), white),
                ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE',      (0, 0), (-1, 0), 9),
                ('ALIGN',         (0, 0), (-1, 0), 'CENTER'),
                # Corps
                ('FONTSIZE',      (0, 1), (-1, -2), 9),
                ('ROWBACKGROUNDS',(0, 1), (-1, -2), [white, HexColor('#F8F9FA')]),
                ('ALIGN',         (2, 1), (-1, -1), 'RIGHT'),
                ('ALIGN',         (0, 1), (1, -1),  'LEFT'),
                # Ligne total
                ('BACKGROUND',    (0, n-1), (-1, n-1), HexColor('#EBF5FB')),
                ('FONTNAME',      (0, n-1), (-1, n-1), 'Helvetica-Bold'),
                ('FONTSIZE',      (0, n-1), (-1, n-1), 9),
                ('LINEABOVE',     (0, n-1), (-1, n-1), 1, HexColor('#3498DB')),
                # Grille
                ('GRID',          (0, 0),  (-1, -1), 0.4, HexColor('#CCCCCC')),
                ('VALIGN',        (0, 0),  (-1, -1), 'MIDDLE'),
                ('TOPPADDING',    (0, 0),  (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0),  (-1, -1), 4),
                ('LEFTPADDING',   (0, 0),  (-1, -1), 6),
                ('RIGHTPADDING',  (0, 0),  (-1, -1), 6),
            ]))
            story.append(lignes_tbl)
            story.append(Spacer(1, 1*cm))

            # ── Zones de signature ────────────────────────────────────────────
            sig_data = [[
                Paragraph("<b>Signature livreur</b>", styles['Normal']),
                Paragraph("<b>Signature réceptionnaire</b>", styles['Normal']),
            ]]
            sig_tbl = Table(sig_data, colWidths=[8.5*cm, 8.5*cm])
            sig_tbl.setStyle(TableStyle([
                ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
                ('TOPPADDING',    (0, 0), (-1, -1), 40),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('BOX',           (0, 0), (0,  0),  0.5, black),
                ('BOX',           (1, 0), (1,  0),  0.5, black),
            ]))
            story.append(sig_tbl)
            story.append(Spacer(1, 0.5*cm))

            # ── Pied de page ──────────────────────────────────────────────────
            story.append(HRFlowable(width='100%', thickness=0.5, color=HexColor('#CCCCCC')))
            story.append(Spacer(1, 0.2*cm))
            story.append(Paragraph(
                f"Généré par {company_name} — {_dt.now().strftime('%d/%m/%Y %H:%M')}",
                styles['BLSmall']
            ))

            doc.build(story)

            if logo_path and os.path.exists(logo_path):
                try:
                    os.unlink(logo_path)
                except Exception:
                    pass

        # ════════════════════════════════════════════════════════════════════
        #  FORMAT 80mm (ticket thermique)
        # ════════════════════════════════════════════════════════════════════
        else:
            PAGE_W = 80 * mm
            doc = SimpleDocTemplate(
                filename,
                pagesize=(PAGE_W, 400*mm),   # hauteur auto
                leftMargin=3*mm, rightMargin=3*mm,
                topMargin=3*mm,  bottomMargin=3*mm,
            )
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle('T_Center', fontSize=11, fontName='Helvetica-Bold', alignment=TA_CENTER))
            styles.add(ParagraphStyle('T_Normal', fontSize=10, fontName='Helvetica'))
            styles.add(ParagraphStyle('T_Bold',   fontSize=10, fontName='Helvetica-Bold'))
            styles.add(ParagraphStyle('T_Small',  fontSize=9,  fontName='Helvetica',
                                      textColor=HexColor('#555555')))
            col_w = PAGE_W - 6*mm

            story = []

            # En-tête compact
            story.append(Paragraph(company_name.upper(), styles['T_Center']))
            if company.get('address'):
                story.append(Paragraph(company['address'], styles['T_Center']))
            if company.get('phone'):
                story.append(Paragraph(f"Tél : {company['phone']}", styles['T_Center']))
            story.append(HRFlowable(width=col_w, thickness=0.5, color=black, dash=(2,2)))
            story.append(Paragraph("BON DE LIVRAISON", styles['T_Center']))
            story.append(Paragraph(detail['numero'], styles['T_Center']))
            story.append(HRFlowable(width=col_w, thickness=0.5, color=black, dash=(2,2)))

            story.append(Paragraph(f"Date    : {date_str}", styles['T_Normal']))
            story.append(Paragraph(f"Départ  : {detail['depart']}", styles['T_Normal']))
            story.append(Paragraph(f"Arrivée : {detail['arrivee']}", styles['T_Normal']))
            story.append(Paragraph(f"Statut  : {detail['statut_label']}", styles['T_Bold']))
            if detail.get('notes'):
                story.append(Paragraph(f"Notes   : {detail['notes']}", styles['T_Normal']))

            story.append(HRFlowable(width=col_w, thickness=0.5, color=black, dash=(2,2)))

            # Tableau lignes compact
            t_data = [['Produit', 'Qté', 'Total']]
            for l in detail['lignes']:
                nom = (l['product_name'] or '')[:20]
                t_data.append([nom, f"{l['quantite']:.2f}", fmt(l['total_ligne'])])
            t_data.append(['', 'TOTAL', fmt(detail['valeur_totale'])])

            n80 = len(t_data)
            t_tbl = Table(t_data, colWidths=[col_w*0.50, col_w*0.20, col_w*0.30])
            t_tbl.setStyle(TableStyle([
                ('FONTNAME',      (0, 0),    (-1, 0),    'Helvetica-Bold'),
                ('FONTSIZE',      (0, 0),    (-1, -1),   9),
                ('ALIGN',         (1, 0),    (-1, -1),   'RIGHT'),
                ('ALIGN',         (0, 0),    (0, -1),    'LEFT'),
                ('FONTNAME',      (0, n80-1),(-1, n80-1),'Helvetica-Bold'),
                ('LINEABOVE',     (0, n80-1),(-1, n80-1), 0.5, black),
                ('LINEBELOW',     (0, 0),    (-1, 0),    0.5, black),
                ('TOPPADDING',    (0, 0),    (-1, -1),   1),
                ('BOTTOMPADDING', (0, 0),    (-1, -1),   1),
                ('LEFTPADDING',   (0, 0),    (-1, -1),   2),
                ('RIGHTPADDING',  (0, 0),    (-1, -1),   2),
            ]))
            story.append(t_tbl)
            story.append(HRFlowable(width=col_w, thickness=0.5, color=black, dash=(2,2)))

            # ── Cases de signature ────────────────────────────────────────────
            story.append(Spacer(1, 3*mm))
            sig80_data = [[
                Paragraph("<b>Signature livreur</b>", styles['T_Bold']),
                Paragraph("<b>Signature réceptionnaire</b>", styles['T_Bold']),
            ]]
            sig80_tbl = Table(sig80_data, colWidths=[col_w*0.50, col_w*0.50])
            sig80_tbl.setStyle(TableStyle([
                ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
                ('FONTSIZE',      (0, 0), (-1, -1), 10),
                ('TOPPADDING',    (0, 0), (-1, -1), 25),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('BOX',           (0, 0), (0,  0),  0.5, black),
                ('BOX',           (1, 0), (1,  0),  0.5, black),
            ]))
            story.append(sig80_tbl)
            story.append(Spacer(1, 2*mm))
            story.append(HRFlowable(width=col_w, thickness=0.5, color=black, dash=(2,2)))
            story.append(Paragraph(
                f"Généré par {company_name}",
                styles['T_Small']
            ))
            story.append(Paragraph(_dt.now().strftime('%d/%m/%Y %H:%M'), styles['T_Small']))

            doc.build(story)

        # ── Ouvrir le PDF ─────────────────────────────────────────────────────
        try:
            if os.name == 'nt':
                os.startfile(filename)
            else:
                subprocess.Popen(['xdg-open', filename])
        except Exception as e:
            QMessageBox.information(
                self, "PDF généré",
                f"Le bon a été exporté :\n{filename}"
            )


