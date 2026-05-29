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
    APP_VERSION = "2.0.3"
    
    # Notes de version
    VERSION_NOTES = {
        "2.0.3": {
            "date": "25 Mai 2026",
            "titre": "Restructuration module Salle de Fête & amélioration checkout Hôtel",
            "changements": [
                "AMÉLIORATION: Restructuration complète du module Salle de Fête (filtres, exports, calendrier)",
                "NOUVEAU: Filtre de réservations par date de création (created_at) avec plages précises",
                "NOUVEAU: Export PDF liste des réservations en A4 paysage avec créateur et téléphone",
                "NOUVEAU: Calendrier mensuel PDF paysage avec badges colorés (orange à venir, gris passé)",
                "AMÉLIORATION: Impression réservation A4 compacte sur une page (client + téléphone sur une ligne)",
                "AMÉLIORATION: Section Notes masquée automatiquement si vide dans l'impression réservation",
                "BUGFIX: Correction reconnaissance des anciennes bases de données (colonne modules manquante)",
                "BUGFIX: Migration automatique de la colonne `modules` dans `core_users` au démarrage",
                "AMÉLIORATION: Module Hôtel — heure de checkout configurable"
            ]
        },
        "2.0.2": {
            "date": "18 Mai 2026",
            "titre": "Mise à jour 2.0.2 — Stabilisation et corrections mineures",
            "changements": [
                "BUGFIX: Corrections mineures de stabilité",
                "AMÉLIORATION: Performances générales"
            ]
        },
        "2.0.0": {
            "date": "1er Mai 2026",
            "titre": "Module Hôtel complet, Livraisons et initialisation API",
            "changements": [
                "NOUVEAU: Module Hôtel – tableau de bord, réservations, paiements, chambres, catégories",
                "NOUVEAU: Onglet Clients dans le module Hôtel avec gestion type de carte d'identité",
                "NOUVEAU: Export PDF tableau de bord hôtel avec en-tête entreprise et mention Ayanna ERP",
                "NOUVEAU: Comptabilité hôtel SYSCOHADA – débit du compte lié au mode de paiement",
                "NOUVEAU: Acompte à la réservation avec référence mobile/banque (optionnelle)",
                "NOUVEAU: Fonctionnalité Bons de livraison – ajustement stock et coût moyen pondéré",
                "NOUVEAU: Initialisation de l'API Laravel (routes, config, documentation)",
                "AMÉLIORATION: Champs Pays, Pièce d'identité et Type de carte dans le formulaire client",
                "AMÉLIORATION: Suppression client avec confirmation",
                "AMÉLIORATION: Affichage des chambres du tableau de bord trié par date de création",
                "BUGFIX: Correction valeurs NULL (reserved_quantity) dans stock_produits_entrepot",
                "BUGFIX: Trigger SQLite pour forcer DEFAULT 0 sur les colonnes numériques du stock",
            ]
        },
        "2.0.1": {
            "date": "9 Mai 2026",
            "titre": "Mise à jour 2.0.1 — Exports 80mm, inventaires, accès modules et synchronisation API",
            "changements": [
                "AMÉLIORATION: Export des produits et inventaires au format 80mm (tickets) amélioré",
                "AMÉLIORATION: La quantité initiale d'un produit pour la journée est prise à partir du premier inventaire du jour",
                "AMÉLIORATION: Restrictions d'accès aux modules appliquées par utilisateur (persistées en base de données)",
                "NOUVEAU: Colonne `modules` ajoutée à `core_users` pour stocker l'accès aux modules (JSON)",
                "NOUVEAU: Scaffolding d'une API de synchronisation des données (en cours d'implémentation)",
                "BUGFIX: Divers correctifs mineurs liés aux exports et à l'UI des inventaires"
            ]
        },
        "1.9.1": {
            "date": "23 Avril 2026",
            "titre": "Corrections bugs sur la vente, synthèse export et recherche produit",
            "changements": [
                "BUGFIX: Correction sur la déduction du stock lors de la vente",
                "BUGFIX: Correction sur l'écriture comptable lors de la vente",
                "AMÉLIORATION: prise en compte de la remise dans le calcul de la vente en export produit et commandes",
                "AMÉLIORATION: Correction bugs sur la recherche ",
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
    MODULES_ENABLED = os.getenv("MODULES_ENABLED", "SalleFete,Boutique,Pharmacie,Restaurant,Hotel,Achats,Stock,Comptabilite,Fabrication").split(",")
    
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
