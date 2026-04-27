"""
Helper pour identifier les entrepôts associés aux points de vente (POS)
"""

from sqlalchemy import and_
from ayanna_erp.modules.stock.models import StockWarehouse
from ayanna_erp.database.database_manager import DatabaseManager, POSPoint


class POSWarehouseHelper:
    """Helper pour gérer la liaison entre POS et entrepôts"""
    
    @staticmethod
    def get_main_warehouse_for_pos(pos_id):
        """
        Récupère l'entrepôt principal associé à un POS donné
        
        Args:
            pos_id (int): ID du point de vente
            
        Returns:
            StockWarehouse|None: Entrepôt principal du POS ou None si non trouvé
        """
        try:
            db_manager = DatabaseManager()
            
            with db_manager.get_session() as session:
                # Récupérer les infos du POS
                pos = session.query(POSPoint).filter_by(id=pos_id).first()
                if not pos:
                    return None
                
                # Méthode 1: Recherche par module et type "Principal"
                if pos.module:
                    # Chercher l'entrepôt principal correspondant au module du POS
                    main_warehouse = session.query(StockWarehouse).filter(
                        and_(
                            StockWarehouse.entreprise_id == pos.enterprise_id,
                            StockWarehouse.name.contains(pos.module.name),
                            StockWarehouse.type == "Principal",
                            StockWarehouse.is_active == True
                        )
                    ).first()
                    
                    if main_warehouse:
                        return main_warehouse
                
                # Méthode 2: Fallback - entrepôt par défaut de l'entreprise
                default_warehouse = session.query(StockWarehouse).filter(
                    and_(
                        StockWarehouse.entreprise_id == pos.enterprise_id,
                        StockWarehouse.is_default == True,
                        StockWarehouse.is_active == True
                    )
                ).first()
                
                return default_warehouse
                
        except Exception as e:
            print(f"Erreur lors de la récupération de l'entrepôt principal: {e}")
            return None
    
    @staticmethod
    def get_pos_warehouse(pos_id):
        """
        Récupère l'entrepôt POS (Point de Vente) associé à un POS donné
        
        Args:
            pos_id (int): ID du point de vente
            
        Returns:
            StockWarehouse|None: Entrepôt POS ou None si non trouvé
        """
        try:
            db_manager = DatabaseManager()
            
            with db_manager.get_session() as session:
                # Récupérer les infos du POS
                pos = session.query(POSPoint).filter_by(id=pos_id).first()
                if not pos:
                    return None
                
                # Chercher l'entrepôt de type "Point de Vente" correspondant au module
                if pos.module:
                    pos_warehouse = session.query(StockWarehouse).filter(
                        and_(
                            StockWarehouse.entreprise_id == pos.enterprise_id,
                            StockWarehouse.name.contains(pos.module.name),
                            StockWarehouse.type == "Point de Vente",
                            StockWarehouse.is_active == True
                        )
                    ).first()
                    
                    return pos_warehouse
                
                return None
                
        except Exception as e:
            print(f"Erreur lors de la récupération de l'entrepôt POS: {e}")
            return None
    
    @staticmethod
    def get_warehouse_info_for_pos(pos_id):
        """
        Récupère toutes les informations d'entrepôts pour un POS donné
        
        Args:
            pos_id (int): ID du point de vente
            
        Returns:
            dict: Informations complètes sur les entrepôts associés au POS
        """
        try:
            db_manager = DatabaseManager()
            
            with db_manager.get_session() as session:
                # Récupérer les infos du POS
                pos = session.query(POSPoint).filter_by(id=pos_id).first()
                if not pos:
                    return {
                        'error': f"POS avec ID {pos_id} non trouvé",
                        'pos_info': None,
                        'main_warehouse': None,
                        'pos_warehouse': None,
                        'all_warehouses': []
                    }
                
                # Récupérer tous les entrepôts de l'entreprise
                all_warehouses = session.query(StockWarehouse).filter(
                    and_(
                        StockWarehouse.entreprise_id == pos.enterprise_id,
                        StockWarehouse.is_active == True
                    )
                ).all()
                
                # Identifier les entrepôts spécifiques
                main_warehouse = None
                pos_warehouse = None
                
                if pos.module:
                    for warehouse in all_warehouses:
                        if pos.module.name.lower() in warehouse.name.lower():
                            if warehouse.type == "Principal":
                                main_warehouse = warehouse
                            elif warehouse.type == "Point de Vente":
                                pos_warehouse = warehouse
                
                # Si aucun entrepôt principal trouvé, prendre celui par défaut
                if not main_warehouse:
                    main_warehouse = next(
                        (w for w in all_warehouses if w.is_default), 
                        None
                    )
                
                return {
                    'error': None,
                    'pos_info': {
                        'id': pos.id,
                        'name': pos.name,
                        'module': pos.module.name if pos.module else None,
                        'enterprise_id': pos.enterprise_id
                    },
                    'main_warehouse': {
                        'id': main_warehouse.id,
                        'name': main_warehouse.name,
                        'code': main_warehouse.code,
                        'type': main_warehouse.type
                    } if main_warehouse else None,
                    'pos_warehouse': {
                        'id': pos_warehouse.id,
                        'name': pos_warehouse.name,
                        'code': pos_warehouse.code,
                        'type': pos_warehouse.type
                    } if pos_warehouse else None,
                    'all_warehouses': [
                        {
                            'id': w.id,
                            'name': w.name,
                            'code': w.code,
                            'type': w.type,
                            'is_default': w.is_default
                        } for w in all_warehouses
                    ]
                }
                
        except Exception as e:
            return {
                'error': f"Erreur: {e}",
                'pos_info': None,
                'main_warehouse': None,
                'pos_warehouse': None,
                'all_warehouses': []
            }
    
    @staticmethod
    def create_warehouse_for_pos(pos_id, warehouse_type="Point de Vente"):
        """
        Crée automatiquement un entrepôt pour un POS si il n'en existe pas
        
        Args:
            pos_id (int): ID du point de vente
            warehouse_type (str): Type d'entrepôt à créer ("Principal" ou "Point de Vente")
            
        Returns:
            StockWarehouse|None: Nouvel entrepôt créé ou None si erreur
        """
        try:
            db_manager = DatabaseManager()
            
            with db_manager.get_session() as session:
                # Récupérer les infos du POS
                pos = session.query(POSPoint).filter_by(id=pos_id).first()
                if not pos:
                    return None
                
                # Vérifier si l'entrepôt existe déjà
                existing = session.query(StockWarehouse).filter(
                    and_(
                        StockWarehouse.entreprise_id == pos.enterprise_id,
                        StockWarehouse.name.contains(pos.module.name if pos.module else pos.name),
                        StockWarehouse.type == warehouse_type
                    )
                ).first()
                
                if existing:
                    return existing
                
                # Créer le nouveau code
                prefix = "MAIN" if warehouse_type == "Principal" else "POS"
                code = f"{prefix}_{pos_id}"
                
                # Créer le nouveau nom
                module_name = pos.module.name if pos.module else "POS"
                name = f"Entrepôt {warehouse_type} - {pos.name}"
                
                # Créer l'entrepôt
                new_warehouse = StockWarehouse(
                    entreprise_id=pos.enterprise_id,
                    code=code,
                    name=name,
                    type=warehouse_type,
                    description=f"Entrepôt automatiquement créé pour {pos.name}",
                    is_default=(warehouse_type == "Principal"),
                    is_active=True,
                    capacity_limit=1000.0  # Valeur par défaut
                )
                
                session.add(new_warehouse)
                session.commit()
                
                return new_warehouse
                
        except Exception as e:
            print(f"Erreur lors de la création de l'entrepôt: {e}")
            return None