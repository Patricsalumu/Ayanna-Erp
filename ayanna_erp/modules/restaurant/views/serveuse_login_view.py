from PyQt6.QtWidgets import QDialog, QVBoxLayout, QGridLayout, QPushButton, QLabel, QLineEdit, QMessageBox, QApplication
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve

from ayanna_erp.database.database_manager import DatabaseManager, User
from ayanna_erp.core.session_manager import SessionManager


class ServeuseLoginView(QDialog):
    """Écran de connexion rapide des serveuses via keypad numérique."""

    user_authenticated = pyqtSignal(object)

    def __init__(self, entreprise_id=1, parent=None):
        super().__init__(parent)
        self.entreprise_id = entreprise_id
        self.db = DatabaseManager()
        self.password = ""
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Connexion serveuse")
        self.setFixedSize(420, 520)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setStyleSheet("""
            QWidget {
                background: #f5f7fa;
                color: #1f2937;
            }
            QLabel { color: #111827; }
            QLineEdit {
                background: white;
                border: 2px solid #d1d5db;
                border-radius: 10px;
                padding: 16px 12px;
                font-size: 28px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton {
                background: #ffffff;
                border: 1px solid #d1d5db;
                border-radius: 12px;
                font-size: 22px;
                font-weight: bold;
                color: #111827;
            }
            QPushButton:hover {
                background: #e5e7eb;
            }
            QPushButton#key_submit {
                background: #16a34a;
                color: white;
                border: none;
            }
            QPushButton#key_clear {
                background: #f59e0b;
                color: white;
                border: none;
            }
            QPushButton#key_cancel {
                background: #ef4444;
                color: white;
                border: none;
            }
        """)

        main = QVBoxLayout(self)
        main.setContentsMargins(24, 20, 24, 24)
        main.setSpacing(16)

        title = QLabel("Serveuse - Saisissez votre code")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        main.addWidget(title)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("••••")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setReadOnly(True)
        self.password_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.addWidget(self.password_input)

        keypad = QGridLayout()
        keypad.setHorizontalSpacing(12)
        keypad.setVerticalSpacing(12)

        digits = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
        for idx, digit in enumerate(digits):
            btn = QPushButton(digit)
            btn.setFixedHeight(68)
            btn.clicked.connect(lambda checked=False, val=digit: self._add_digit(val))
            row, col = divmod(idx, 3)
            keypad.addWidget(btn, row, col)

        clear_btn = QPushButton("C")
        clear_btn.setObjectName("key_clear")
        clear_btn.setFixedHeight(68)
        clear_btn.clicked.connect(self._clear_password)
        keypad.addWidget(clear_btn, 3, 0)

        back_btn = QPushButton("⌫")
        back_btn.setFixedHeight(68)
        back_btn.clicked.connect(self._backspace)
        keypad.addWidget(back_btn, 3, 1)

        submit_btn = QPushButton("Connexion")
        submit_btn.setObjectName("key_submit")
        submit_btn.setFixedHeight(68)
        submit_btn.clicked.connect(self._authenticate)
        self.submit_btn = submit_btn
        self.submit_btn.setStyleSheet("""
            QPushButton#key_submit {
                background: #16a34a;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 22px;
                font-weight: bold;
            }
            QPushButton#key_submit:disabled {
                background: #86efac;
                color: rgba(255,255,255,0.85);
            }
        """)
        keypad.addWidget(submit_btn, 3, 2)

        main.addLayout(keypad)

        self.loading_label = QLabel("Connexion...", self)
        self.loading_label.setVisible(False)
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.loading_label.setStyleSheet("""
            QLabel {
                background: rgba(22, 163, 74, 0.10);
                color: #166534;
                border: 1px solid rgba(22, 163, 74, 0.25);
                border-radius: 999px;
                font-size: 12px;
                font-weight: bold;
                padding: 7px 14px;
            }
        """)
        self.loading_label.resize(self.loading_label.sizeHint())
        self.loading_label.move((self.width() - self.loading_label.width()) // 2, 360)

    def _show_loading(self):
        """Affiche un petit indicateur visuel très léger pendant la validation du code."""
        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("Connexion...")
        self.loading_label.setVisible(True)
        self.loading_label.raise_()
        self.loading_label.setWindowOpacity(0.0)
        self.loading_label.move((self.width() - self.loading_label.width()) // 2, 360)

        anim = QPropertyAnimation(self.loading_label, b'windowOpacity')
        anim.setDuration(180)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        anim.start()

    def _hide_loading(self):
        """Masque le petit indicateur visuel après validation."""
        self.submit_btn.setEnabled(True)
        self.submit_btn.setText("Connexion")
        anim = QPropertyAnimation(self.loading_label, b'windowOpacity')
        anim.setDuration(150)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        anim.finished.connect(lambda: self.loading_label.setVisible(False))
        anim.start()

    def _authenticate(self):
        if not self.password:
            QMessageBox.warning(self, "Code requis", "Veuillez saisir le mot de passe de la serveuse.")
            return

        self._show_loading()
        try:
            entered = str(self.password).strip()
            session = self.db.get_session()
            try:
                users = session.query(User).filter(User.enterprise_id == self.entreprise_id).all()
                matches = []
                for user in users:
                    role = str(getattr(user, 'role', '') or '').lower()
                    if role != 'serveuse':
                        continue
                    if user.check_password(entered):
                        matches.append(user)

                if not matches:
                    QMessageBox.warning(self, "Accès refusé", "Code inconnu pour cette serveuse.")
                    self.password = ""
                    self._refresh_password_display()
                    return

                selected_user = matches[0]
                self.user_authenticated.emit(selected_user)
                self.close()
            except Exception as exc:
                QMessageBox.critical(self, "Erreur", f"Impossible de valider le code: {exc}")
            finally:
                try:
                    session.close()
                except Exception:
                    pass
        finally:
            self._hide_loading()

    def _add_digit(self, digit: str):
        if len(self.password) >= 4:
            return
        self.password += str(digit)
        self._refresh_password_display()

    def _backspace(self):
        self.password = self.password[:-1]
        self._refresh_password_display()

    def _clear_password(self):
        self.password = ""
        self._refresh_password_display()

    def _refresh_password_display(self):
        visible = "•" * len(self.password)
        self.password_input.setText(visible)

    def _return_to_main_login(self):
        """Retourne à la fenêtre de connexion principale après confirmation."""
        answer = QMessageBox.question(
            self,
            "Retour à la connexion principale",
            "Voulez-vous vraiment vous déconnecter et revenir à l'écran de connexion principal ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            SessionManager.clear_session()
        except Exception:
            pass

        try:
            if self.parent() is not None:
                self.parent().close()
        except Exception:
            pass

        try:
            self.close()
        except Exception:
            pass

        try:
            from ayanna_erp.ui.login_window import LoginWindow
            app = QApplication.instance()
            login_window = LoginWindow()
            login_window.show()
            login_window.raise_()
            login_window.activateWindow()
            if app is not None:
                app.processEvents()
        except Exception as exc:
            QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir la fenêtre de connexion principale: {exc}")

    def closeEvent(self, event):
        self.password = ""
        self._refresh_password_display()
        super().closeEvent(event)
