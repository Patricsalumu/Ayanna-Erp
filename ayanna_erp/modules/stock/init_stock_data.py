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
        # Créer les tables si elles n'existent pas (utilise l'engine du DatabaseManager)
        from ayanna_erp.database.base import Base

        db_manager = DatabaseManager()
        Base.metadata.create_all(db_manager.engine)

        logger.info("📦 Initialisation du module Stock...")

        # Si une session est fournie, l'utiliser directement, sinon ouvrir une session contextuelle
        if db_session is None:
            # Utiliser le context manager fourni par DatabaseManager.get_session()
            with db_manager.get_session() as session:
                existing_warehouses = session.query(StockWarehouse).count()

                if existing_warehouses == 0:
                    logger.info("Création des entrepôts de base...")

                    # Entrepôts de base selon les POS
                    warehouses_data = [
                {
                    'code': 'POS_2',
                    'name': 'Entrepôt Vente',
                    'type': 'Principal',
                    'description': 'Entrepôt principal pour la vente',
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

                return True
        else:
            # On utilise la session fournie par l'appelant (on suppose un objet Session actif)
            session = db_session
            existing_warehouses = session.query(StockWarehouse).count()

            if existing_warehouses == 0:
                logger.info("Création des entrepôts de base...")

                warehouses_data = [
                    {
                        'code': 'POS_2',
                        'name': 'Entrepôt Vente',
                        'type': 'Principal',
                        'description': 'Entrepôt principal pour la vente',
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

            return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation du module Stock: {e}")
        # Pas sûr si session existe dans ce scope; tenter de rollback si possible
        try:
            if 'session' in locals() and session is not None:
                session.rollback()
        except Exception:
            pass
        return False


if __name__ == "__main__":
    # Test du script d'initialisation
    success = init_stock_data()
    if success:
        print("✅ Initialisation du module Stock réussie")
    else:
        print("❌ Échec de l'initialisation du module Stock")
