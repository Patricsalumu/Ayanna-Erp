"""
Script d'initialisation des données pour le module Stock
Crée les entrepôts de base au premier lancement
"""

import logging
from datetime import datetime

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.stock.models import StockWarehouse

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_stock_data(db_session=None):
    """
    Initialise les données de base pour le module Stock
    
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
        
        logger.info("📦 Initialisation du module Stock...")
        
        # Vérifier si les entrepôts existent déjà
        existing_warehouses = session.query(StockWarehouse).count()
        
        if existing_warehouses == 0:
            logger.info("Création des entrepôts de base...")
            
            # Entrepôts de base selon les POS
            warehouses_data = [
                {
                    'code': 'POS_2',
                    'name': 'Entrepôt Boutique',
                    'type': 'Principal',
                    'description': 'Entrepôt principal pour la boutique',
                    'is_default': True,
                    'is_active': True,
                    'entreprise_id': 1
                },
                {
                    'code': 'POS_3', 
                    'name': 'Entrepôt Pharmacie',
                    'type': 'Principal',
                    'description': 'Entrepôt principal pour la pharmacie',
                    'is_default': False,
                    'is_active': True,
                    'entreprise_id': 1
                },
                {
                    'code': 'POS_4',
                    'name': 'Entrepôt Restaurant', 
                    'type': 'Principal',
                    'description': 'Entrepôt principal pour le restaurant',
                    'is_default': False,
                    'is_active': True,
                    'entreprise_id': 1
                }
            ]
            
            for warehouse_data in warehouses_data:
                warehouse = StockWarehouse(
                    code=warehouse_data['code'],
                    name=warehouse_data['name'],
                    type=warehouse_data['type'],
                    description=warehouse_data['description'],
                    is_default=warehouse_data['is_default'],
                    is_active=warehouse_data['is_active'],
                    entreprise_id=warehouse_data['entreprise_id'],
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(warehouse)
                logger.info(f"✅ Entrepôt créé: {warehouse.name} ({warehouse.code})")
            
            session.commit()
            logger.info(f"✅ {len(warehouses_data)} entrepôts créés avec succès")
        else:
            logger.info(f"ℹ️  {existing_warehouses} entrepôt(s) déjà existant(s)")
        
        if session_created:
            session.close()
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation du module Stock: {e}")
        if session_created and session:
            session.rollback()
            session.close()
        return False


if __name__ == "__main__":
    # Test du script d'initialisation
    success = init_stock_data()
    if success:
        print("✅ Initialisation du module Stock réussie")
    else:
        print("❌ Échec de l'initialisation du module Stock")
