"""
Fenêtre de connexion pour Ayanna ERP
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                            QLineEdit, QPushButton, QLabel, QMessageBox, 
                            QFrame, QApplication, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPalette, QColor, QIcon
from ayanna_erp.database.database_manager import DatabaseManager, User, Entreprise


class LoginWindow(QWidget):
    """Fenêtre de connexion principale"""
    
    # Signal émis lors d'une connexion réussie
    login_success = pyqtSignal(object)  # Émet l'objet User connecté
    
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.current_user = None
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        self.setWindowTitle("Ayanna ERP - Connexion")
        self.setFixedSize(600, 700)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Frame principal avec style
        main_frame = QFrame()
        main_frame.setObjectName("mainFrame")
        main_frame.setStyleSheet("""
            QFrame#mainFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2C3E50, stop:1 #34495E);
                border-radius: 10px;
            }
        """)
        
        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(40, 40, 40, 40)
        frame_layout.setSpacing(30)
        
        # En-tête avec logo et titre
        self.setup_header(frame_layout)
        
        # Formulaire de connexion
        self.setup_form(frame_layout)
        
        # Boutons
        self.setup_buttons(frame_layout)
        
        # Pied de page
        self.setup_footer(frame_layout)
        
        main_layout.addWidget(main_frame)
        self.setLayout(main_layout)
        
        # Centrer la fenêtre
        self.center_window()
    
    def setup_header(self, layout):
        """Configuration de l'en-tête"""
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Titre principal
        title_label = QLabel("AYANNA ERP")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            color: white;
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 10px;
        """)
        
        # Sous-titre
        subtitle_label = QLabel("Système de Gestion Intégré")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("""
            color: #BDC3C7;
            font-size: 14px;
            margin-bottom: 20px;
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        
        layout.addLayout(header_layout)
    
    def setup_form(self, layout):
        """Configuration du formulaire de connexion"""
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(15)
        
        # Champ email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Adresse email")
        self.email_input.setStyleSheet(self.get_input_style())
        
        # Champ mot de passe
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mot de passe")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(self.get_input_style())
        
        # Labels
        email_label = QLabel("Email:")
        email_label.setStyleSheet("color: white; font-weight: bold;")
        
        password_label = QLabel("Mot de passe:")
        password_label.setStyleSheet("color: white; font-weight: bold;")
        
        form_layout.addRow(email_label, self.email_input)
        form_layout.addRow(password_label, self.password_input)
        
        layout.addWidget(form_frame)
    
    def setup_buttons(self, layout):
        """Configuration des boutons"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # Bouton de connexion
        self.login_button = QPushButton("Se connecter")
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
            QPushButton:pressed {
                background-color: #21618C;
            }
        """)
        
        # Bouton quitter
        self.quit_button = QPushButton("Quitter")
        self.quit_button.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
            QPushButton:pressed {
                background-color: #A93226;
            }
        """)
        
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.quit_button)
        
        layout.addLayout(button_layout)
    
    def setup_footer(self, layout):
        """Configuration du pied de page"""
        footer_label = QLabel("© 2018 Congo Mémoire - Tous droits réservés")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_label.setStyleSheet("""
            color: #BDC3C7;
            font-size: 12px;
            margin-top: 20px;
        """)
        
        layout.addWidget(footer_label)
    
    def get_input_style(self):
        """Style pour les champs de saisie"""
        return """
            QLineEdit {
                background-color: white;
                border: 2px solid #BDC3C7;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498DB;
            }
        """
    
    def setup_connections(self):
        """Configuration des connexions de signaux"""
        self.login_button.clicked.connect(self.handle_login)
        self.quit_button.clicked.connect(self.close)
        self.password_input.returnPressed.connect(self.handle_login)
        self.email_input.returnPressed.connect(self.password_input.setFocus)
    
    def handle_login(self):
        """Gérer la tentative de connexion"""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if not email or not password:
            self.show_error("Veuillez saisir votre email et votre mot de passe.")
            return
        
        # Vérifier les identifiants
        if self.authenticate_user(email, password):
            self.show_main_window()
        else:
            self.show_error("Email ou mot de passe incorrect.")
            self.password_input.clear()
            self.password_input.setFocus()
    
    def authenticate_user(self, email, password):
        """Authentifier l'utilisateur et initialiser la session"""
        try:
            session = self.db_manager.get_session()
            user = session.query(User).filter_by(email=email).first()
            
            if user and user.check_password(password):
                self.current_user = user
                # Enregistrer l'utilisateur et l'entreprise dans DatabaseManager
                # Suppression de l'appel obsolète à set_current_user (gestion centralisée)
                self.db_manager.set_current_enterprise(user.enterprise_id)
                # Importer et initialiser le SessionManager
                from ayanna_erp.core.session_manager import SessionManager
                SessionManager.set_current_user(user)
                return True
            return False
            
        except Exception as e:
            print(f"Erreur lors de l'authentification: {e}")
            return False
    
    def show_main_window(self):
        """Afficher la fenêtre principale"""
        from ayanna_erp.ui.main_window import MainWindow
        
        self.main_window = MainWindow(self.current_user)
        self.main_window.show()
        self.hide()
    
    def show_error(self, message):
        """Afficher un message d'erreur"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("Erreur de connexion")
        msg_box.setText(message)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QMessageBox QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
            }
        """)
        msg_box.exec()
    
    def center_window(self):
        """Centrer la fenêtre sur l'écran"""
        screen_geometry = QApplication.primaryScreen().geometry()
        window_geometry = self.geometry()
        
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        
        self.move(x, y)
    
    def closeEvent(self, event):
        """Gérer la fermeture de la fenêtre"""
        self.db_manager.close_session()
        event.accept()
