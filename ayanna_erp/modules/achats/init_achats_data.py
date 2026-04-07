"""
Script d'initialisation des données pour le module Achats
Crée les tables et ajoute des données de test au premier lancement
"""

import logging
from datetime import datetime
from decimal import Decimal

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.achats.models import (
    CoreFournisseur, AchatCommande, AchatCommandeLigne, AchatDepense
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_achats_data(db_session=None):
    """
    Initialise les données de base pour le module Achats
    
    Args:
        db_session: Session de base de données SQLAlchemy
        
    Returns:
        bool: True si l'initialisation a réussi
    """
    try:
        # Utiliser la session fournie ou en créer une nouvelle
        session = db_session
        session_created = False
        
        if session is None:
            db_manager = DatabaseManager()
            session = db_manager.get_session()
            session_created = True
        
        # Créer les tables si elles n'existent pas
        from ayanna_erp.database.base import Base
        from ayanna_erp.database.database_manager import DatabaseManager
        
        db_manager = DatabaseManager()
        Base.metadata.create_all(db_manager.engine)
        
        logger.info("🏪 Initialisation du module Achats...")
        
        # Vérifier si les données existent déjà
        existing_fournisseurs = session.query(CoreFournisseur).count()
        if existing_fournisseurs > 0:
            logger.info("✅ Données déjà initialisées pour le module Achats")
            return True
        
        # Créer des fournisseurs de test
        fournisseurs_data = [
            {
                'nom': 'SARL TechFournisseur',
                'telephone': '+243 99 123 4567',
                'email': 'contact@techfournisseur.cd',
                'adresse': '123 Avenue Kasavubu, Kinshasa, RDC'
            },
            {
                'nom': 'Grossiste Central',
                'telephone': '+243 81 987 6543',
                'email': 'commandes@grossistecentral.cd',
                'adresse': '456 Boulevard du 30 Juin, Lubumbashi, RDC'
            },
            {
                'nom': 'Import Export Plus',
                'telephone': '+243 97 555 0123',
                'email': 'info@importexportplus.cd',
                'adresse': '789 Rue de la Paix, Goma, RDC'
            },
            {
                'nom': 'Fournitures Modernes',
                'telephone': '+243 85 444 9876',
                'email': 'ventes@fournituresmodernes.cd',
                'adresse': '321 Avenue Mobutu, Mbuji-Mayi, RDC'
            }
        ]
        
        fournisseurs_created = []
        for fournisseur_data in fournisseurs_data:
            fournisseur = CoreFournisseur(**fournisseur_data)
            session.add(fournisseur)
            fournisseurs_created.append(fournisseur)
        
        session.commit()
        
        # Actualiser les objets pour obtenir les IDs
        for fournisseur in fournisseurs_created:
            session.refresh(fournisseur)
        
        logger.info(f"✅ {len(fournisseurs_created)} fournisseurs créés")
        
        # Fermer la session si elle a été créée ici
        if session_created:
            session.close()
        
        logger.info("✅ Initialisation du module Achats terminée avec succès!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation du module Achats: {e}")
        if session_created and session:
            session.rollback()
            session.close()
        return False


def initialize_achats_data():
    """Fonction de compatibilité pour l'ancienne API"""
    return init_achats_data()


if __name__ == "__main__":
    # Test de l'initialisation
    success = initialize_achats_data()
    if success:
        print("✅ Initialisation du module Achats réussie")
    else:
        print("❌ Échec de l'initialisation du module Achats")