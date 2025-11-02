from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QHBoxLayout, QFrame, QSpacerItem, QSizePolicy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from ayanna_erp.core.services.licence_service import activer_licence


class LicenceActivationDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Activation de la licence Ayanna Erp")
        self.setFixedSize(670, 550)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(12)

        # Branding et titre
        title = QLabel("Activation de la licence")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Explication générale
        explication = QLabel(
            "<b>Qu'est-ce qu'une clé de licence ?</b><br>"
            "Une clé de licence est un code unique qui permet d'activer et d'utiliser légalement le logiciel <b>Ayanna ERP</b> sur cet ordinateur.\n"
            "<br><br>"
            "<b>Comment obtenir une clé ?</b><br>"
            "Contactez l'équipe <b>Ayanna Tech</b> pour acheter ou demander une clé d'essaie.\n"
            "<br>Développeur : <b>Ayanna Tech</b>\n"
            "<br>Téléphone : <b>+243997554905</b>\n"
            "<br><br>"
            "<span style='color:#666'>Entrez la clé reçue ci-dessous pour activer votre logiciel.</span>"
        )
        explication.setWordWrap(True)
        explication.setAlignment(Qt.AlignmentFlag.AlignLeft)
        explication.setStyleSheet("font-size: 13px; margin-bottom: 8px;")
        layout.addWidget(explication)

        # Avertissement très visible
        avert = QLabel("⚠️ <b style='color:#b71c1c;'>Attention :</b> L'utilisation d'une clé de licence non autorisée, partagée ou toute autre forme de piratage expose votre établissement à des poursuites judiciaires.")
        avert.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avert.setWordWrap(True)
        avert.setStyleSheet("color: #b71c1c; font-size: 15px; font-weight: bold; margin: 12px 0 12px 0; border: 1.5px solid #b71c1c; border-radius: 8px; background: #fff3f0; padding: 8px 10px;")
        layout.addWidget(avert)

        # Ligne séparatrice
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # Champ de saisie
        self.input = QLineEdit()
        self.input.setPlaceholderText("Exemple : DEMO-AYANNA-2025-01")
        self.input.setMinimumHeight(38)
        self.input.setFont(QFont("Segoe UI", 13))
        layout.addWidget(self.input)

        # Bouton activer centré
        btn_layout = QHBoxLayout()
        btn_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.activate_btn = QPushButton("Activer la licence")
        self.activate_btn.setMinimumHeight(38)
        self.activate_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.activate_btn.clicked.connect(self.activate)
        btn_layout.addWidget(self.activate_btn)
        btn_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        layout.addLayout(btn_layout)

        # Footer branding
        footer = QLabel("Développé par <b>Ayanna Tech</b>  |  Contact : <b>+243997554905</b>")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: #888; font-size: 12px; margin-top: 18px;")
        layout.addWidget(footer)

        self.setLayout(layout)
        self.input.returnPressed.connect(self.activate)
        self.input.setFocus()

        # Style moderne
        self.setStyleSheet('''
            QDialog { background: #f9f5f0; }
            QLabel { color: #3e2723; }
            QLineEdit {
                border: 2px solid #a1887f;
                border-radius: 8px;
                padding: 8px 12px;
                background: #fff;
            }
            QLineEdit:focus { border-color: #6d4c41; }
            QPushButton {
                background: #6d4c41;
                color: #fff;
                border-radius: 8px;
                padding: 8px 24px;
            }
            QPushButton:hover { background: #8d6e63; }
        ''')

    def activate(self):
        cle = self.input.text().strip()
        if not cle:
            QMessageBox.warning(self, "Erreur", "Veuillez saisir une clé de licence.")
            return
        ok, msg = activer_licence(cle)
        if ok:
            QMessageBox.information(self, "Succès", msg)
            self.accept()
        else:
            # Fournir des messages d'erreur plus explicites selon le cas
            detail = msg
            if "déjà été utilisée" in msg or "déjà été" in msg:
                detail = msg + "\n\nSi vous pensez que c'est une erreur, contactez le support avec votre référence de commande et l'ID machine."
            elif "Clé de licence invalide" in msg:
                detail = msg + "\n\nVérifiez que vous avez copié la clé correctement (sans espaces) ou contactez le fournisseur pour obtenir une clé valide."
            elif "Erreur lors de l'activation" in msg:
                detail = msg + "\n\nUne erreur interne s'est produite lors de l'activation. Consultez les logs et contactez le support si nécessaire."
            elif "Intégrité" in msg or "signature" in msg:
                detail = msg + "\n\nLa licence semble avoir été modifiée (date ou signature). Veuillez contacter le support."

            QMessageBox.critical(self, "Erreur d'activation", detail)
            self.input.selectAll()
            self.input.setFocus()
