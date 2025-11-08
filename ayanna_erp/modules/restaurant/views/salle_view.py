"""
View to manage salles and place tables (simple CRUD + list)
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QLineEdit, QHBoxLayout,
    QFrame, QMenu, QSpinBox, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QAction

from ayanna_erp.modules.restaurant.controllers.salle_controller import SalleController


class DraggableTable(QPushButton):
    """Représentation visuelle d'une table dans le plan: draggable et cliquable."""
    class ResizeHandle(QWidget):
        """Petit widget carré utilisé pour redimensionner une table par glisser."""
        def __init__(self, table):
            super().__init__(table)
            self.table = table
            self.setFixedSize(12, 12)
            self.setStyleSheet("background-color:#bdc3c7; border:1px solid #7f8c8d; border-radius:2px;")
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            self._resizing = False
            self._start_pos = None
            self._start_size = None

        def mousePressEvent(self, event):
            if event.button() == Qt.MouseButton.LeftButton:
                self._resizing = True
                # coord globales
                try:
                    self._start_pos = event.globalPosition().toPoint()
                except Exception:
                    self._start_pos = event.globalPos()
                self._start_size = self.table.size()
            super().mousePressEvent(event)

        def mouseMoveEvent(self, event):
            if not self._resizing:
                return super().mouseMoveEvent(event)
            try:
                current = event.globalPosition().toPoint()
            except Exception:
                current = event.globalPos()
            dx = current.x() - self._start_pos.x()
            dy = current.y() - self._start_pos.y()
            new_w = max(30, self._start_size.width() + dx)
            new_h = max(30, self._start_size.height() + dy)
            # Clamp inside parent plan
            plan = self.table.parent_view.plan_frame
            max_w = max(30, plan.width() - self.table.x())
            max_h = max(30, plan.height() - self.table.y())
            new_w = min(new_w, max_w)
            new_h = min(new_h, max_h)
            self.table.setFixedSize(int(new_w), int(new_h))
            self.table.apply_style()
            self.table.update_handle_position()

        def mouseReleaseEvent(self, event):
            if self._resizing:
                self._resizing = False
                # sauvegarder la nouvelle taille via le controller
                try:
                    self.table.parent_view.ctrl.update_table(self.table.table_id, width=int(self.table.width()), height=int(self.table.height()))
                except Exception as e:
                    print(f"Erreur sauvegarde resize: {e}")
            super().mouseReleaseEvent(event)

    def __init__(self, table_obj, parent_view):
        super().__init__(str(table_obj.number), parent_view.plan_frame)
        self.table_obj = table_obj
        self.table_id = table_obj.id
        self.parent_view = parent_view
        w = int(getattr(table_obj, 'width', 80) or 80)
        h = int(getattr(table_obj, 'height', 80) or 80)
        self.setFixedSize(w, h)
        self.move(int(getattr(table_obj, 'pos_x', 0) or 0), int(getattr(table_obj, 'pos_y', 0) or 0))
        # Appliquer style selon la forme et le thème restaurant
        self.apply_style()
        # resize handle
        self.handle = DraggableTable.ResizeHandle(self)
        self.update_handle_position()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self._dragging = False
        self._drag_offset = QPoint(0, 0)

    def apply_style(self):
        # Thème restaurant
        primary = '#F39C12'  # warm orange
        accent = '#D35400'
        free_bg = '#ecf3ea'
        border = '#7f8c8d'
        shape = str(getattr(self.table_obj, 'shape', '') or '').lower()
        w = int(getattr(self.table_obj, 'width', 80) or 80)
        h = int(getattr(self.table_obj, 'height', 80) or 80)
        if shape in ('round', 'circle'):
            radius = min(w, h) // 2
            style = f"background-color: {free_bg}; border: 2px solid {accent}; border-radius: {radius}px; font-weight: bold;"
        else:
            style = f"background-color: {free_bg}; border: 2px solid {border}; border-radius: 6px; font-weight: bold;"
        self.setStyleSheet(style)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_offset = event.pos()
            self.parent_view.select_table(self.table_id)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging:
            new_pos = self.mapToParent(event.pos() - self._drag_offset)
            # Clamp inside parent
            pw = self.parent_view.plan_frame.width() - self.width()
            ph = self.parent_view.plan_frame.height() - self.height()
            x = max(0, min(new_pos.x(), pw))
            y = max(0, min(new_pos.y(), ph))
            self.move(x, y)
            # move handle along with widget
            try:
                self.update_handle_position()
            except Exception:
                pass
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._dragging:
            self._dragging = False
            # Sauvegarder la nouvelle position
            pos = self.pos()
            try:
                self.parent_view.save_table_position(self.table_id, pos.x(), pos.y())
            except Exception as e:
                print(f"Erreur sauvegarde position table: {e}")
        super().mouseReleaseEvent(event)

    def _show_context_menu(self, point):
        menu = QMenu(self)
        delete_action = QAction('Supprimer', self)
        delete_action.triggered.connect(lambda: self.parent_view.delete_table(self.table_id))
        menu.addAction(delete_action)
        menu.exec(self.mapToGlobal(point))

    def update_handle_position(self):
        """Positionne le handle en bas à droite du widget."""
        if not hasattr(self, 'handle') or self.handle is None:
            return
        hw = self.handle.width()
        hh = self.handle.height()
        # offset so the handle sits slightly outside corner
        x = max(0, self.width() - hw // 2)
        y = max(0, self.height() - hh // 2)
        self.handle.move(int(x), int(y))


class SalleView(QWidget):
    def __init__(self, entreprise_id=1, parent=None):
        super().__init__(parent)
        self.entreprise_id = entreprise_id
        self.ctrl = SalleController(entreprise_id=self.entreprise_id)
        self.selected_table_id = None
        self.table_widgets = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        # Palette et style simple pour module Restaurant
        self.setStyleSheet('''
            QWidget { background-color: #fffdf8; color: #2c3e50; }
            QLabel { color: #2c3e50; font-weight: 600; }
            QPushButton { background-color: #F39C12; color: white; border: none; padding: 6px; border-radius: 6px; }
            QPushButton[secondary="true"] { background-color: #95A5A6; }
        ''')
        layout.addWidget(QLabel('Gestion des salles'))

        # Création salle
        top_layout = QHBoxLayout()
        self.salle_name = QLineEdit()
        self.salle_name.setPlaceholderText('Nom de la salle')
        add_btn = QPushButton('Ajouter salle')
        add_btn.clicked.connect(self.add_salle)
        top_layout.addWidget(self.salle_name)
        top_layout.addWidget(add_btn)
        layout.addLayout(top_layout)

        # Liste des salles
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.on_salle_selected)
        layout.addWidget(self.list_widget)

        # Plan + controls
        controls_layout = QHBoxLayout()

        # Plan
        self.plan_frame = QFrame()
        self.plan_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.plan_frame.setFixedSize(800, 480)
        # Ne pas appeler setLayout(None) — laisser l'objet sans layout pour positionnement absolu
        controls_layout.addWidget(self.plan_frame, 3)

        # Right controls: add table + edit
        right = QVBoxLayout()
        right.addWidget(QLabel('Ajouter une table'))
        self.table_number = QLineEdit()
        self.table_number.setPlaceholderText('Numéro table')
        right.addWidget(self.table_number)
        # Choix de la forme lors de la création
        right.addWidget(QLabel('Forme de la table'))
        from PyQt6.QtWidgets import QComboBox
        self.new_table_shape = QComboBox()
        self.new_table_shape.addItems(['rectangle', 'round'])
        right.addWidget(self.new_table_shape)
        add_table_btn = QPushButton('Ajouter table')
        add_table_btn.clicked.connect(self.add_table_from_ui)
        right.addWidget(add_table_btn)
        delete_btn = QPushButton('Supprimer table sélectionnée')
        delete_btn.clicked.connect(self.delete_selected_table)
        right.addWidget(delete_btn)

        # Editeur pour la table sélectionnée
        right.addWidget(QLabel('--- Édition table sélectionnée ---'))
        right.addWidget(QLabel('Numéro'))
        self.edit_number = QLineEdit()
        right.addWidget(self.edit_number)

        right.addWidget(QLabel('Largeur'))
        self.edit_width = QSpinBox()
        self.edit_width.setRange(10, 1000)
        self.edit_width.setValue(80)
        right.addWidget(self.edit_width)

        right.addWidget(QLabel('Hauteur'))
        self.edit_height = QSpinBox()
        self.edit_height.setRange(10, 1000)
        self.edit_height.setValue(80)
        right.addWidget(self.edit_height)

        right.addWidget(QLabel('Forme'))
        # Utiliser QComboBox pour l'édition (même choix que la création)
        self.edit_shape = QComboBox()
        self.edit_shape.addItems(['rectangle', 'round'])
        right.addWidget(self.edit_shape)

        save_edit_btn = QPushButton('Sauvegarder modifications')
        save_edit_btn.clicked.connect(self.save_selected_table_edits)
        save_edit_btn.setProperty('secondary', True)
        right.addWidget(save_edit_btn)

        right.addStretch()
        controls_layout.addLayout(right, 1)

        layout.addLayout(controls_layout)

        # Charger
        self.refresh_btn = QPushButton('Charger')
        self.refresh_btn.clicked.connect(self.load_salles)
        layout.addWidget(self.refresh_btn)
        self.load_salles()

    def add_salle(self):
        name = self.salle_name.text().strip()
        if not name:
            return
        try:
            self.ctrl.create_salle(name)
            self.salle_name.setText('')
            self.load_salles()
        except Exception as e:
            print(f"Erreur add_salle: {e}")

    def load_salles(self):
        self.list_widget.clear()
        try:
            salles = self.ctrl.list_salles()
            for s in salles:
                self.list_widget.addItem(f"{s.id} - {s.name}")
        except Exception as e:
            print(f"Erreur load_salles: {e}")

    def on_salle_selected(self, item):
        # Extraire id
        try:
            sid = int(str(item.text()).split(' - ')[0])
        except Exception:
            return
        self.current_salle_id = sid
        self.load_tables_for_salle(sid)

    def load_tables_for_salle(self, salle_id):
        # Vider plan
        for w in list(self.table_widgets.values()):
            w.setParent(None)
        self.table_widgets.clear()
        try:
            tables = self.ctrl.list_tables_for_salle(salle_id)
            for t in tables:
                widget = DraggableTable(t, self)
                widget.show()
                self.table_widgets[t.id] = widget
        except Exception as e:
            print(f"Erreur load_tables_for_salle: {e}")

    def add_table_from_ui(self):
        number = self.table_number.text().strip() or 'T'
        try:
            if not getattr(self, 'current_salle_id', None):
                QMessageBox.warning(self, 'Sélectionnez une salle', 'Veuillez sélectionner une salle avant d\'ajouter une table')
                return
            # Default position at 10,10
            shape = str(self.new_table_shape.currentText() or 'rectangle')
            t = self.ctrl.create_table(self.current_salle_id, number, pos_x=10, pos_y=10, shape=shape)
            self.table_number.setText('')
            # recharger l'affichage pour assurer cohérence
            self.load_tables_for_salle(self.current_salle_id)
        except Exception as e:
            print(f"Erreur add_table_from_ui: {e}")

    def save_table_position(self, table_id, x, y):
        try:
            t = self.ctrl.update_table(table_id, pos_x=x, pos_y=y)
            # Mettre à jour le widget local si présent
            if table_id in self.table_widgets:
                w = self.table_widgets[table_id]
                w.table_obj.pos_x = int(x)
                w.table_obj.pos_y = int(y)
                w.move(int(x), int(y))
                # pas besoin de changer le style sauf si shape/size changent
        except Exception as e:
            print(f"Erreur save_table_position: {e}")

    def select_table(self, table_id):
        self.selected_table_id = table_id
        # afficher propriétés dans panneau d'édition
        try:
            t = self.ctrl.get_table(table_id)
            if t:
                self.edit_number.setText(str(t.number))
                self.edit_width.setValue(int(t.width or 80))
                self.edit_height.setValue(int(t.height or 80))
                # QComboBox: utiliser setCurrentText pour sélectionner la forme
                try:
                    self.edit_shape.setCurrentText(str(t.shape or ''))
                except Exception:
                    # fallback: trouver l'index
                    idx = self.edit_shape.findText(str(t.shape or ''))
                    if idx >= 0:
                        self.edit_shape.setCurrentIndex(idx)
        except Exception as e:
            print(f"Erreur load table for edit: {e}")

    def delete_table(self, table_id):
        try:
            ok = self.ctrl.delete_table(table_id)
            if ok and table_id in self.table_widgets:
                w = self.table_widgets.pop(table_id)
                w.setParent(None)
        except Exception as e:
            print(f"Erreur delete_table: {e}")

    def delete_selected_table(self):
        if not getattr(self, 'selected_table_id', None):
            return
        self.delete_table(self.selected_table_id)

    def save_selected_table_edits(self):
        if not getattr(self, 'selected_table_id', None):
            QMessageBox.warning(self, 'Aucune sélection', 'Aucune table sélectionnée')
            return
        try:
            num = self.edit_number.text().strip() or None
            w = int(self.edit_width.value())
            h = int(self.edit_height.value())
            # QComboBox: récupérer la valeur via currentText()
            try:
                shape = str(self.edit_shape.currentText()).strip() or None
            except Exception:
                # fallback si widget inattendu
                shape = None
            t = self.ctrl.update_table(self.selected_table_id, width=w, height=h, number=num, shape=shape)
            # Update widget size/appearance
            if t and t.id in self.table_widgets:
                widget = self.table_widgets[t.id]
                widget.setFixedSize(t.width or 80, t.height or 80)
                widget.setText(str(t.number))
                # mettre à jour l'objet interne et le style
                widget.table_obj.width = int(t.width or 80)
                widget.table_obj.height = int(t.height or 80)
                widget.table_obj.number = t.number
                widget.table_obj.shape = t.shape
                widget.apply_style()
            QMessageBox.information(self, 'Succès', 'Table mise à jour')
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Impossible de sauver la table: {e}")
