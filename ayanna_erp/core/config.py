"""
Configuration centralisée pour Ayanna ERP
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


class Config:
    """Classe de configuration centralisée pour Ayanna ERP"""
    
    # Chemins de base (DOIT être défini en premier)
    BASE_DIR = Path(__file__).parent.parent.parent  # Racine du projet
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    
    # Version de l'application
    APP_NAME = "Ayanna ERP"
    APP_VERSION = "1.9"
    
    # Notes de version
    VERSION_NOTES = {
        "1.9": {
            "date": "10 Avril 2026",
            "titre": "Corrections et Améliorations d'Export",
            "changements": [
                "BUGFIX: Correction de l'affichage des remises dans l'export produits",
                "BUGFIX: Correction du calcul du montant en espèce dans le rapport quotidien",
                "AMÉLIORATION: Ajout du solde et des remises dans l'export des commandes",
                "AMÉLIORATION: Meilleure visibilité globale de l'activité via les documents d'export",
                "AMÉLIORATION: Affichage de la version sur le login et main window",
                "AMÉLIORATION: Diminution de la taille de la fenêtre modale création produit"
                "AMELIORATION: Fenetre modale selection produit aggrandie, avec filtre par categorie et quantite stock"
                "BUGFIX: Chargement des commandes limités à 25"
                "AMELIORATION: Geration des numero commande unique"
            ]
        },
        "1.8": {
            "date": "Mars 2026",
            "titre": "Stabilisation",
            "changements": [
                "Amélioration des performances",
                "Corrections mineures"
            ]
        }
    }
    
    # Configuration de la base de données
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/ayanna_erp.db")
    
    # Debug mode
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    # Configuration de la comptabilité
    DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "USD")
    ENABLE_ACCOUNTING = os.getenv("ENABLE_ACCOUNTING", "True").lower() == "true"
    
    # Configuration des modules
    MODULES_ENABLED = os.getenv("MODULES_ENABLED", "SalleFete,Boutique,Pharmacie,Restaurant,Hotel,Achats,Stock,Comptabilite").split(",")
    
    # Configuration UI
    WINDOW_MIN_WIDTH = 1200
    WINDOW_MIN_HEIGHT = 800
    ICON_SIZE = 48
    
    # Configuration de sécurité
    SESSION_TIMEOUT = 3600  # 1 heure en secondes
    PASSWORD_MIN_LENGTH = 6
    
    # Configuration des rapports
    REPORTS_DIR = DATA_DIR / "reports"
    
    # Configuration des logs
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = LOGS_DIR / "ayanna_erp.log"

    # Secret pour signatures de licences (HMAC)
    LICENCE_SECRET = os.getenv("LICENCE_SECRET", None)
    
    # Styles CSS pour l'application
    STYLES = {
        "primary_color": "#3498DB",
        "secondary_color": "#2C3E50", 
        "success_color": "#27AE60",
        "warning_color": "#F39C12",
        "danger_color": "#E74C3C",
        "info_color": "#17A2B8",
        "light_color": "#ECF0F1",
        "dark_color": "#2C3E50"
    }
    
    # Messages de l'application
    MESSAGES = {
        "login_success": "Connexion réussie",
        "login_failed": "Identifiants incorrects",
        "logout_success": "Déconnexion réussie",
        "save_success": "Enregistrement réussi",
        "save_failed": "Erreur lors de l'enregistrement",
        "delete_success": "Suppression réussie",
        "delete_failed": "Erreur lors de la suppression",
        "validation_error": "Erreur de validation des données"
    }
    
    @classmethod
    def initialize(cls):
        """Initialise les dossiers nécessaires"""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)
        cls.REPORTS_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def get_database_path(cls):
        """Retourne le chemin vers la base de données"""
        return str(cls.BASE_DIR / "ayanna_erp.db")


# Initialisation automatique
Config.initialize()

# Rétrocompatibilité - variables globales
BASE_DIR = Config.BASE_DIR
DATA_DIR = Config.DATA_DIR
LOGS_DIR = Config.LOGS_DIR
APP_NAME = Config.APP_NAME
APP_VERSION = Config.APP_VERSION
DEBUG = Config.DEBUG
DATABASE_URL = Config.DATABASE_URL
DEFAULT_CURRENCY = Config.DEFAULT_CURRENCY
ENABLE_ACCOUNTING = Config.ENABLE_ACCOUNTING
MODULES_ENABLED = Config.MODULES_ENABLED
WINDOW_MIN_WIDTH = Config.WINDOW_MIN_WIDTH
WINDOW_MIN_HEIGHT = Config.WINDOW_MIN_HEIGHT
ICON_SIZE = Config.ICON_SIZE
SESSION_TIMEOUT = Config.SESSION_TIMEOUT
PASSWORD_MIN_LENGTH = Config.PASSWORD_MIN_LENGTH
REPORTS_DIR = Config.REPORTS_DIR
LOG_LEVEL = Config.LOG_LEVEL
LOG_FILE = Config.LOG_FILE
STYLES = Config.STYLES
MESSAGES = Config.MESSAGES
