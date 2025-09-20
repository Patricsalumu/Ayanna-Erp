from PyQt6.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout, QLabel

class ComptabiliteWindow(QMainWindow):
    """
    ComptabiliteWindow - Fenêtre principale pour le module Comptabilité

    Contient un QTabWidget avec 7 sous-onglets :
    - Journal comptable
    - Grand livre
    - Balance comptable
    - Compte de résultat
    - Bilan
    - Comptes comptables
    - Classes comptables
    """
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        
        # Configuration de la fenêtre
        self.setWindowTitle("Ayanna ERP - Module Comptabilité")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        self.tabs = QTabWidget()
        
        # Initialiser la session et l'entreprise depuis l'utilisateur
        from ayanna_erp.database.database_manager import DatabaseManager
        from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
        self.db_manager = DatabaseManager()
        self.session = self.db_manager.get_session()
        self.entreprise_id = self.current_user.enterprise_id
        
        # Initialiser le contrôleur entreprise pour les devises
        self.entreprise_controller = EntrepriseController()
        
        # Import du controller corrigé
        try:
            from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ComptabiliteController
            self.controller = ComptabiliteController()
        except ImportError:
            # Fallback si le controller n'existe pas encore
            self.controller = None

        # Chargement progressif des onglets avec gestion d'erreur
        self._load_tabs()
        layout.addWidget(self.tabs)

    def get_currency_symbol(self):
        """Récupère le symbole de devise depuis l'entreprise"""
        try:
            return self.entreprise_controller.get_currency_symbol()
        except:
            return "€"  # Fallback

    def format_amount(self, amount):
        """Formate un montant avec la devise de l'entreprise"""
        try:
            return self.entreprise_controller.format_amount(amount)
        except:
            return f"{amount:.2f} €"  # Fallback

    def _load_tabs(self):
        """Charge les onglets un par un avec gestion d'erreur"""
        tabs_config = [
            ("Journal comptable", self._create_journal_tab),
            ("Grand livre", self._create_grand_livre_tab),
            ("Compte de résultat", self._create_compte_resultat_tab),
            ("Bilan", self._create_bilan_tab),
            ("Comptes comptables", self._create_comptes_tab),
            ("Classes comptables", self._create_classes_tab),
        ]
        
        for tab_name, create_method in tabs_config:
            try:
                widget = create_method()
                self.tabs.addTab(widget, tab_name)
            except Exception as e:
                # Ajoute un onglet d'erreur
                error_widget = QWidget()
                error_layout = QVBoxLayout(error_widget)
                error_label = QLabel(f"Erreur de chargement: {str(e)}")
                error_layout.addWidget(error_label)
                self.tabs.addTab(error_widget, f"{tab_name} (Erreur)")

    def _create_journal_tab(self):
        """Crée l'onglet Journal comptable"""
        try:
            from .widgets.journal_widget import JournalWidget
            return JournalWidget(self.controller, parent=self)
        except ImportError:
            return QLabel("Widget Journal non disponible")

    def _create_grand_livre_tab(self):
        """Crée l'onglet Grand livre"""
        try:
            from .widgets.grand_livre_widget import GrandLivreWidget
            return GrandLivreWidget(self.controller, parent=self)
        except ImportError:
            return QLabel("Widget Grand livre non disponible")

    def _create_balance_tab(self):
        """Crée l'onglet Balance comptable"""
        try:
            from .widgets.balance_widget import BalanceWidget
            return BalanceWidget(self.controller, parent=self)
        except ImportError:
            return QLabel("Widget Balance non disponible")

    def _create_compte_resultat_tab(self):
        """Crée l'onglet Compte de résultat"""
        try:
            from .widgets.compte_resultat_widget import CompteResultatWidget
            return CompteResultatWidget(self.controller, parent=self)
        except ImportError:
            return QLabel("Widget Compte de résultat non disponible")

    def _create_bilan_tab(self):
        """Crée l'onglet Bilan"""
        try:
            from .widgets.bilan_widget import BilanWidget
            return BilanWidget(self.controller, parent=self)
        except ImportError:
            return QLabel("Widget Bilan non disponible")

    def _create_comptes_tab(self):
        """Crée l'onglet Comptes comptables"""
        try:
            from .widgets.comptes_widget import ComptesWidget
            return ComptesWidget(self.controller, parent=self)
        except ImportError:
            return QLabel("Widget Comptes non disponible")

    def _create_classes_tab(self):
        """Crée l'onglet Classes comptables"""
        try:
            from .widgets.classes_widget import ClassesWidget
            return ClassesWidget(self.controller, parent=self)
        except ImportError:
            return QLabel("Widget Classes non disponible")


# Alias pour compatibilité
ComptabiliteTab = ComptabiliteWindow
