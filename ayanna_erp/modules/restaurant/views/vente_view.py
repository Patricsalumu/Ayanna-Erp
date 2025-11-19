from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QDialog, QFormLayout, QLineEdit, QSpinBox,
    QMessageBox, QScrollArea, QStackedWidget
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QPoint
from PyQt6.QtGui import QColor

from ayanna_erp.modules.restaurant.controllers.salle_controller import SalleController
from ayanna_erp.modules.restaurant.controllers.vente_controller import VenteController
from ayanna_erp.modules.restaurant.views.catalogue_widget import CatalogueWidget
from ayanna_erp.database.database_manager import get_database_manager, Entreprise
from ayanna_erp.utils.formatting import format_amount, get_currency


# ----------------------------------------------------------------------
# BOUTON TABLE - STYLE TYPE "AYANNA CLOUD"
# ----------------------------------------------------------------------
class TableButton(QPushButton):
    def __init__(self, table_obj, parent_view):
        super().__init__(str(table_obj.number), parent_view.plan_frame)
        self.table_obj = table_obj
        self.table_id = table_obj.id
        self.parent_view = parent_view

        w = int(getattr(table_obj, "width", 80) or 80)
        h = int(getattr(table_obj, "height", 80) or 80)
        self.setFixedSize(w, h)

        self.move(
            int(getattr(table_obj, "pos_x", 0) or 0),
            int(getattr(table_obj, "pos_y", 0) or 0)
        )

        self.apply_style()

    def apply_style(self, occupied=False, selected=False):
        # Couleurs cohérentes avec ton image Ayanna Cloud
        color_border_free = "#28a745"
        color_border_selected = "#1e7e34"
        color_bg_free = "#ffffff"
        color_bg_occupied = "#28a745"   # fond vert vif quand occupée
        color_text = "#222222"

        shape = (getattr(self.table_obj, "shape", "square") or "").lower()
        radius = min(self.width(), self.height()) // 2 if shape in ("round", "circle") else 10

        # Choix des couleurs selon l’état
        bg_color = color_bg_occupied if occupied else color_bg_free
        border_color = color_border_selected if selected else color_border_free
        font_weight = "bold" if selected else "600"

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                border: 3px solid {border_color};
                border-radius: {radius}px;
                color: {color_text};
                font-size: 20px;
                font-weight: {font_weight};
            }}
            QPushButton:hover {{
                border-color: #1e7e34;
            }}
        """)

        # Texte numéro de table centré
        self.setText(str(self.table_obj.number))

        # === Badge montant (ex: 6 000 F) ===
        try:
            montant_text = ''
            if occupied:
                # Distinguish boolean True (occupied with no amount) from numeric amounts.
                try:
                    if isinstance(occupied, bool):
                        # occupied flag only, no badge
                        montant_text = ''
                    elif isinstance(occupied, (int, float)):
                        currency = get_currency(getattr(self.parent_view, 'entreprise_id', None))
                        montant_text = f"{format_amount(occupied)} {currency}"
                    else:
                        # assume string already formatted
                        montant_text = str(occupied)
                except Exception:
                    montant_text = str(occupied)

            if not hasattr(self, '_amount_badge') or self._amount_badge is None:
                self._amount_badge = QLabel(self)
                self._amount_badge.setObjectName('table_amount_badge')
                self._amount_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self._amount_badge.setStyleSheet("""
                    background-color: #E53935;
                    color: white;
                    border-radius: 9px;
                    padding: 1px 6px;
                    font-size: 11px;
                    font-weight: bold;
                """)

            if montant_text:
                self._amount_badge.setText(montant_text)
                self._amount_badge.adjustSize()
                bw = self._amount_badge.width()
                bh = self._amount_badge.height()
                self._amount_badge.move(self.width() - bw - 4, 4)
                self._amount_badge.show()
            else:
                self._amount_badge.hide()
        except Exception:
            pass


    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.parent_view.select_table_button(self)
        self.parent_view.open_table_panel(self.table_id)


# ----------------------------------------------------------------------
# VUE PRINCIPALE RESTAURANT
# ----------------------------------------------------------------------
class VenteView(QWidget):
    def __init__(self, entreprise_id=1, parent=None):
        super().__init__(parent)
        self.entreprise_id = entreprise_id

        self.salle_ctrl = SalleController(entreprise_id=entreprise_id)
        self.vente_ctrl = VenteController(entreprise_id=entreprise_id)

        self.table_buttons = {}
        self.current_salle_id = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        # ----------------------------
        # ✅ BARRE D’ONGLETS DES SALLES (wrap in a widget so we can hide it)
        # ----------------------------
        self.tabs_widget = QWidget()
        self.tabs_layout = QHBoxLayout(self.tabs_widget)
        self.tabs_layout.setSpacing(10)
        layout.addWidget(self.tabs_widget)

        # ----------------------------
        # ✅ ZONE PRINCIPALE (Stack : plan de salle <-> catalogue)
        # ----------------------------
        self.stack = QStackedWidget()

        # Page 0 : plan de salle (conserve self.plan_frame pour compatibilité)
        self.plan_page = QWidget()
        plan_layout = QVBoxLayout(self.plan_page)
        self.plan_frame = QFrame()
        self.plan_frame.setMinimumHeight(500)
        self.plan_frame.setStyleSheet("""
            background-color: #f7f7f7;
            border-radius: 10px;
            padding: 20px;
        """)
        plan_layout.addWidget(self.plan_frame)
        self.stack.addWidget(self.plan_page)

        # Page 1 : catalogue (rempli dynamiquement)
        self.catalogue_page = QWidget()
        cat_layout = QVBoxLayout(self.catalogue_page)
        self.catalogue_container = QWidget()
        cat_layout.addWidget(self.catalogue_container)
        self.stack.addWidget(self.catalogue_page)

        layout.addWidget(self.stack)

        self.load_salles()
        # Charger automatiquement la première salle si disponible
        try:
            self.ensure_first_salle_loaded()
        except Exception:
            pass

    # ------------------------------------------------------------------
    def load_salles(self):
        # vider onglets
        while self.tabs_layout.count():
            w = self.tabs_layout.takeAt(0).widget()
            if w:
                w.deleteLater()

        salles = self.salle_ctrl.list_salles()

        self.salle_buttons = {}

        for s in salles:
            btn = QPushButton(s.name)
            btn.setCheckable(True)
            btn.setProperty("salle_id", s.id)

            btn.setStyleSheet("""
                QPushButton {
                    background-color: #e3e4e6;
                    padding: 8px 20px;
                    border-radius: 6px;
                    font-weight: 600;
                }
                QPushButton:checked {
                    background-color: #28a745;
                    color: white;
                }
            """)

            btn.clicked.connect(lambda checked, sid=s.id, b=btn: self.select_salle(sid, b))

            self.tabs_layout.addWidget(btn)
            self.salle_buttons[s.id] = btn

    # ------------------------------------------------------------------
    def select_salle(self, salle_id, btn):
        if hasattr(self, "active_salle") and self.active_salle:
            self.active_salle.setChecked(False)

        btn.setChecked(True)
        self.active_salle = btn

        self.current_salle_id = salle_id
        self.load_tables_for_salle(salle_id)

    # ------------------------------------------------------------------
    def load_tables_for_salle(self, salle_id):
        # Clear plan
        for b in list(self.table_buttons.values()):
            b.setParent(None)
        self.table_buttons.clear()

        tables = self.salle_ctrl.list_tables_for_salle(salle_id)

        for t in tables:
            btn = TableButton(t, self)

            panier = self.vente_ctrl.get_open_panier_for_table(t.id)

            if panier:
                # If a panier exists we mark the table occupied even when it has no items/amounts.
                try:
                    total, _ = self.vente_ctrl.get_panier_total(panier.id)
                except Exception:
                    total = None

                # If panier exists, mark occupied. Show numeric badge only when total > 0.
                if total is None:
                    occ = True
                else:
                    try:
                        num_total = float(total)
                        if num_total > 0:
                            occ = num_total
                        else:
                            occ = True
                    except Exception:
                        # non-numeric totals: show as-is
                        occ = total

                btn.apply_style(occupied=occ)
            else:
                btn.apply_style(occupied=False)

            btn.show()
            self.table_buttons[t.id] = btn
        btn.setStyleSheet(btn.styleSheet() + "margin: 10px;")

    def ensure_first_salle_loaded(self):
        """Sélectionne la première salle disponible si aucune salle n'est active."""
        try:
            if not getattr(self, 'current_salle_id', None):
                # sélectionner le premier bouton de salle créé
                if hasattr(self, 'salle_buttons') and self.salle_buttons:
                    # prendre le premier id dans l'ordre d'insertion
                    first_id = next(iter(self.salle_buttons.keys()))
                    first_btn = self.salle_buttons.get(first_id)
                    if first_btn:
                        self.select_salle(first_id, first_btn)
        except Exception:
            pass

    # ------------------------------------------------------------------
    def select_table_button(self, table_button):
        if hasattr(self, "active_table_btn") and self.active_table_btn:
            panier = self.vente_ctrl.get_open_panier_for_table(self.active_table_btn.table_id)
            total = None
            if panier:
                try:
                    total, _ = self.vente_ctrl.get_panier_total(panier.id)
                except Exception:
                    total = None

            # decide occupied flag: True if panier exists but no numeric total, numeric otherwise
            if panier:
                # panier exists -> occupied; display numeric badge only if total > 0
                if total is None:
                    occ_prev = True
                else:
                    try:
                        num_total = float(total)
                        occ_prev = num_total if num_total > 0 else True
                    except Exception:
                        occ_prev = total
            else:
                occ_prev = False

            try:
                self.active_table_btn.apply_style(
                    occupied=occ_prev,
                    selected=False
                )
            except Exception:
                self.active_table_btn.apply_style(occupied=occ_prev, selected=False)

        panier = self.vente_ctrl.get_open_panier_for_table(table_button.table_id)
        total = None
        if panier:
            try:
                total, _ = self.vente_ctrl.get_panier_total(panier.id)
            except Exception:
                total = None

        if panier:
            # panier exists -> occupied; display numeric badge only if total > 0
            if total is None:
                occ_new = True
            else:
                try:
                    num_total = float(total)
                    occ_new = num_total if num_total > 0 else True
                except Exception:
                    occ_new = total
        else:
            occ_new = False

        try:
            table_button.apply_style(occupied=occ_new, selected=True)
        except Exception:
            table_button.apply_style(occupied=occ_new, selected=True)
        self.active_table_btn = table_button

    def open_table_panel(self, table_id):
        """Afficher le catalogue EMBARQUÉ dans l'onglet vente (page du QStackedWidget).

        On remplace l'ancien comportement modal par l'affichage dans la page catalogue
        avec une transition animée.
        """
        try:
            # Construire une NOUVELLE page catalogue (on ne réutilise pas l'ancien layout)
            new_cat_page = QWidget()
            new_cat_layout = QVBoxLayout(new_cat_page)

            # bouton retour
            back_btn = QPushButton("⬅ Retour au plan")
            back_btn.setFixedHeight(36)
            back_btn.clicked.connect(self.show_plan_view)
            new_cat_layout.addWidget(back_btn)

            # ajouter le widget catalogue
            current_user = getattr(self, 'current_user', None)
            catalog = CatalogueWidget(table_id=table_id, entreprise_id=self.entreprise_id, pos_id=1, current_user=current_user, parent=new_cat_page)
            new_cat_layout.addWidget(catalog)

            # Remplacer proprement la page catalogue (index 1) du stack
            try:
                old_widget = self.stack.widget(1)
                # retirer et supprimer l'ancien
                self.stack.removeWidget(old_widget)
                try:
                    old_widget.deleteLater()
                except Exception:
                    pass
            except Exception:
                # pas d'ancien widget, on ignore
                pass

            # insérer la nouvelle page en position 1
            self.stack.insertWidget(1, new_cat_page)
            # garder des références
            self.catalogue_page = new_cat_page
            self.catalogue_container = new_cat_page

            # masquer la barre des salles pour que le header du catalogue
            # et le bouton retour puissent occuper cet espace vertical
            try:
                if hasattr(self, 'tabs_widget') and self.tabs_widget:
                    self.tabs_widget.hide()
            except Exception:
                pass

            # animer la transition vers la page catalogue
            self._animate_transition(to_index=1, direction='left')

        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Erreur table panel: {e}")

    def show_plan_view(self):
        # Réafficher la barre des salles puis retourner à la page du plan
        try:
            if hasattr(self, 'tabs_widget') and self.tabs_widget:
                self.tabs_widget.show()
        except Exception:
            pass

        self._animate_transition(to_index=0, direction='right')

    def _animate_transition(self, to_index=0, direction='left'):
        """Animation simple de slide entre pages du QStackedWidget."""
        try:
            from_index = self.stack.currentIndex()
            if from_index == to_index:
                return

            w = self.stack.width()
            h = self.stack.height()

            current_widget = self.stack.widget(from_index)
            next_widget = self.stack.widget(to_index)

            # positionner next_widget en dehors de l'écran
            if direction == 'left':
                next_widget.setGeometry(QRect(w, 0, w, h))
                start_cur = QRect(0, 0, w, h)
                end_cur = QRect(-w, 0, w, h)
                start_next = QRect(w, 0, w, h)
                end_next = QRect(0, 0, w, h)
            else:
                next_widget.setGeometry(QRect(-w, 0, w, h))
                start_cur = QRect(0, 0, w, h)
                end_cur = QRect(w, 0, w, h)
                start_next = QRect(-w, 0, w, h)
                end_next = QRect(0, 0, w, h)

            # make sure next is visible and stacked
            self.stack.setCurrentIndex(to_index)

            anim_cur = QPropertyAnimation(current_widget, b"geometry")
            anim_cur.setDuration(300)
            anim_cur.setStartValue(start_cur)
            anim_cur.setEndValue(end_cur)
            anim_cur.setEasingCurve(QEasingCurve.Type.InOutCubic)

            anim_next = QPropertyAnimation(next_widget, b"geometry")
            anim_next.setDuration(300)
            anim_next.setStartValue(start_next)
            anim_next.setEndValue(end_next)
            anim_next.setEasingCurve(QEasingCurve.Type.InOutCubic)

            # lancer les animations
            anim_cur.start()
            anim_next.start()

            # garder une référence pour éviter GC
            self._last_animations = (anim_cur, anim_next)

            # rafraîchir plan si on revient
            if to_index == 0 and hasattr(self, 'current_salle_id') and self.current_salle_id:
                self.load_tables_for_salle(self.current_salle_id)
        except Exception as e:
            # fallback: changer d'index sans animation
            try:
                self.stack.setCurrentIndex(to_index)
            except Exception:
                pass
            print(f"Animation erreur: {e}")

    def _create_panier_and_close(self, table_id, dlg):
        try:
            p = self.vente_ctrl.create_panier(table_id=table_id)
            dlg.accept()
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Impossible de créer panier: {e}")

    def _add_product_to_panier(self, panier_id, prod_id_text, qty, price_text, dlg):
        try:
            prod_id = int(prod_id_text)
            price = float(price_text)
            self.vente_ctrl.add_product(panier_id, prod_id, qty, price)
            QMessageBox.information(self, 'Succès', 'Produit ajouté')
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Impossible d'ajouter le produit: {e}")

    def _add_payment_to_panier(self, panier_id, amount_text, method_text, dlg):
        try:
            amount = float(amount_text)
            method = method_text or 'Espèces'
            self.vente_ctrl.add_payment(panier_id, amount, method)
            QMessageBox.information(self, 'Succès', 'Paiement enregistré')
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Impossible d'ajouter le paiement: {e}")
