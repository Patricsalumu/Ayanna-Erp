"""
Contrôleur pour la gestion des entrepôts
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.boutique.model.models import ShopWarehouse, ShopProduct, ShopWarehouseStock


class EntrepotController:
    """Contrôleur pour la gestion des entrepôts"""
    
    def __init__(self, pos_id: int):
        self.pos_id = pos_id
        self.db_manager = DatabaseManager()
    
    def get_all_warehouses(self, session: Session) -> List[ShopWarehouse]:
        """Récupérer tous les entrepôts du point de vente"""
        return session.query(ShopWarehouse).filter(
            ShopWarehouse.pos_id == self.pos_id
        ).order_by(ShopWarehouse.is_default.desc(), ShopWarehouse.name).all()
    
    def get_warehouse_by_id(self, session: Session, warehouse_id: int) -> Optional[ShopWarehouse]:
        """Récupérer un entrepôt par son ID"""
        return session.query(ShopWarehouse).filter(
            and_(
                ShopWarehouse.id == warehouse_id,
                ShopWarehouse.pos_id == self.pos_id
            )
        ).first()
    
    def get_warehouse_by_code(self, session: Session, code: str) -> Optional[ShopWarehouse]:
        """Récupérer un entrepôt par son code"""
        return session.query(ShopWarehouse).filter(
            and_(
                ShopWarehouse.code == code,
                ShopWarehouse.pos_id == self.pos_id
            )
        ).first()
    
    def create_warehouse(self, session: Session, warehouse_data: Dict[str, Any]) -> ShopWarehouse:
        """Créer un nouvel entrepôt"""
        # Vérifier que le code n'existe pas déjà
        existing = self.get_warehouse_by_code(session, warehouse_data['code'])
        if existing:
            raise ValueError(f"Un entrepôt avec le code '{warehouse_data['code']}' existe déjà.")
        
        # Si c'est l'entrepôt par défaut, retirer le statut des autres
        if warehouse_data.get('is_default', False):
            session.query(ShopWarehouse).filter(
                ShopWarehouse.pos_id == self.pos_id
            ).update({'is_default': False})
        
        # Créer le nouvel entrepôt
        warehouse = ShopWarehouse(
            pos_id=self.pos_id,
            code=warehouse_data['code'],
            name=warehouse_data['name'],
            type=warehouse_data.get('type', 'Principal'),
            description=warehouse_data.get('description'),
            address=warehouse_data.get('address'),
            capacity_limit=warehouse_data.get('capacity_limit'),
            contact_person=warehouse_data.get('contact_person'),
            contact_phone=warehouse_data.get('contact_phone'),
            contact_email=warehouse_data.get('contact_email'),
            is_default=warehouse_data.get('is_default', False),
            is_active=True
            # created_at=datetime.now()  # Colonne pas encore créée en DB
        )
        
        session.add(warehouse)
        session.flush()  # Pour obtenir l'ID
        
        return warehouse
    
    def update_warehouse(self, session: Session, warehouse_id: int, warehouse_data: Dict[str, Any]) -> ShopWarehouse:
        """Mettre à jour un entrepôt"""
        warehouse = self.get_warehouse_by_id(session, warehouse_id)
        if not warehouse:
            raise ValueError(f"Entrepôt avec l'ID {warehouse_id} non trouvé.")
        
        # Vérifier que le code n'existe pas déjà (si changé)
        if 'code' in warehouse_data and warehouse_data['code'] != warehouse.code:
            existing = self.get_warehouse_by_code(session, warehouse_data['code'])
            if existing:
                raise ValueError(f"Un entrepôt avec le code '{warehouse_data['code']}' existe déjà.")
        
        # Si c'est l'entrepôt par défaut, retirer le statut des autres
        if warehouse_data.get('is_default', False) and not warehouse.is_default:
            session.query(ShopWarehouse).filter(
                and_(
                    ShopWarehouse.pos_id == self.pos_id,
                    ShopWarehouse.id != warehouse_id
                )
            ).update({'is_default': False})
        
        # Mettre à jour les champs
        for key, value in warehouse_data.items():
            if hasattr(warehouse, key):
                setattr(warehouse, key, value)
        
        warehouse.updated_at = datetime.now()
        
        return warehouse
    
    def delete_warehouse(self, session: Session, warehouse_id: int) -> bool:
        """Supprimer un entrepôt (vérifier qu'il n'a pas de stock)"""
        warehouse = self.get_warehouse_by_id(session, warehouse_id)
        if not warehouse:
            raise ValueError(f"Entrepôt avec l'ID {warehouse_id} non trouvé.")
        
        # Vérifier qu'il n'y a pas de stock
        stock_count = session.query(ShopWarehouseStock).filter(
            and_(
                ShopWarehouseStock.warehouse_id == warehouse_id,
                ShopWarehouseStock.quantity > 0
            )
        ).count()
        
        if stock_count > 0:
            raise ValueError("Impossible de supprimer un entrepôt contenant du stock.")
        
        # Supprimer les enregistrements de stock à 0
        session.query(ShopWarehouseStock).filter(
            ShopWarehouseStock.warehouse_id == warehouse_id
        ).delete()
        
        # Supprimer l'entrepôt
        session.delete(warehouse)
        
        return True
    
    def get_warehouse_statistics(self, session: Session, warehouse_id: int) -> Dict[str, Any]:
        """Obtenir les statistiques d'un entrepôt"""
        warehouse = self.get_warehouse_by_id(session, warehouse_id)
        if not warehouse:
            raise ValueError(f"Entrepôt avec l'ID {warehouse_id} non trouvé.")
        
        # Compter les produits et les quantités
        stats = session.query(
            func.count(ShopWarehouseStock.id).label('total_products'),
            func.sum(ShopWarehouseStock.quantity).label('total_quantity'),
            func.sum(ShopWarehouseStock.quantity * ShopWarehouseStock.unit_cost).label('total_value')
        ).filter(
            ShopWarehouseStock.warehouse_id == warehouse_id
        ).first()
        
        # Produits avec stock > 0
        products_with_stock = session.query(ShopWarehouseStock).filter(
            and_(
                ShopWarehouseStock.warehouse_id == warehouse_id,
                ShopWarehouseStock.quantity > 0
            )
        ).count()
        
        # Produits en rupture (stock = 0)
        out_of_stock = session.query(ShopWarehouseStock).filter(
            and_(
                ShopWarehouseStock.warehouse_id == warehouse_id,
                ShopWarehouseStock.quantity == 0
            )
        ).count()
        
        return {
            'warehouse': warehouse,
            'total_products': stats.total_products or 0,
            'products_with_stock': products_with_stock,
            'out_of_stock': out_of_stock,
            'total_quantity': float(stats.total_quantity or 0),
            'total_value': float(stats.total_value or 0),
            'capacity_used_percentage': self._calculate_capacity_percentage(warehouse, stats.total_quantity or 0)
        }
    
    def _calculate_capacity_percentage(self, warehouse: ShopWarehouse, current_quantity: Decimal) -> Optional[float]:
        """Calculer le pourcentage de capacité utilisée"""
        if not warehouse.capacity_limit or warehouse.capacity_limit <= 0:
            return None
        
        return min(100.0, (float(current_quantity) / warehouse.capacity_limit) * 100)
    
    def link_all_products_to_warehouses(self, session: Session) -> Dict[str, int]:
        """Lier tous les produits à tous les entrepôts avec quantité 0"""
        # Récupérer tous les produits et entrepôts
        products = session.query(ShopProduct).filter(ShopProduct.pos_id == self.pos_id).all()
        warehouses = self.get_all_warehouses(session)
        
        created_count = 0
        updated_count = 0
        
        for product in products:
            for warehouse in warehouses:
                # Vérifier si l'association existe déjà
                existing_stock = session.query(ShopWarehouseStock).filter(
                    and_(
                        ShopWarehouseStock.product_id == product.id,
                        ShopWarehouseStock.warehouse_id == warehouse.id
                    )
                ).first()
                
                if not existing_stock:
                    # Créer une nouvelle association avec quantité 0
                    stock = ShopWarehouseStock(
                        product_id=product.id,
                        warehouse_id=warehouse.id,
                        quantity=Decimal('0.00'),
                        reserved_quantity=Decimal('0.00'),
                        unit_cost=product.cost_price or Decimal('0.00'),
                        minimum_stock=product.minimum_stock or Decimal('0.00'),
                        maximum_stock=product.maximum_stock or Decimal('0.00')
                        # created_at=datetime.now()  # Colonne pas encore créée en DB
                    )
                    session.add(stock)
                    created_count += 1
                else:
                    # Mettre à jour les informations si nécessaire
                    if existing_stock.unit_cost != (product.cost_price or Decimal('0.00')):
                        existing_stock.unit_cost = product.cost_price or Decimal('0.00')
                        existing_stock.updated_at = datetime.now()
                        updated_count += 1
        
        return {
            'products_count': len(products),
            'warehouses_count': len(warehouses),
            'associations_created': created_count,
            'associations_updated': updated_count
        }
    
    def get_warehouse_configuration_by_pos(self, session: Session) -> Dict[str, Any]:
        """Obtenir la configuration des entrepôts pour ce point de vente"""
        warehouses = self.get_all_warehouses(session)
        
        default_warehouse = None
        for warehouse in warehouses:
            if warehouse.is_default:
                default_warehouse = warehouse
                break
        
        return {
            'total_warehouses': len(warehouses),
            'active_warehouses': len([w for w in warehouses if w.is_active]),
            'default_warehouse': default_warehouse,
            'warehouses_by_type': self._group_warehouses_by_type(warehouses)
        }
    
    def _group_warehouses_by_type(self, warehouses: List[ShopWarehouse]) -> Dict[str, List[ShopWarehouse]]:
        """Grouper les entrepôts par type"""
        groups = {}
        for warehouse in warehouses:
            warehouse_type = warehouse.type or 'Autre'
            if warehouse_type not in groups:
                groups[warehouse_type] = []
            groups[warehouse_type].append(warehouse)
        return groups
    
    def set_default_warehouse(self, session: Session, warehouse_id: int) -> ShopWarehouse:
        """Définir un entrepôt comme étant celui par défaut"""
        # Retirer le statut par défaut de tous les entrepôts
        session.query(ShopWarehouse).filter(
            ShopWarehouse.pos_id == self.pos_id
        ).update({'is_default': False})
        
        # Définir le nouvel entrepôt par défaut
        warehouse = self.get_warehouse_by_id(session, warehouse_id)
        if not warehouse:
            raise ValueError(f"Entrepôt avec l'ID {warehouse_id} non trouvé.")
        
        warehouse.is_default = True
        warehouse.updated_at = datetime.now()
        
        return warehouse
    
    def toggle_warehouse_status(self, session: Session, warehouse_id: int) -> ShopWarehouse:
        """Activer/désactiver un entrepôt"""
        warehouse = self.get_warehouse_by_id(session, warehouse_id)
        if not warehouse:
            raise ValueError(f"Entrepôt avec l'ID {warehouse_id} non trouvé.")
        
        warehouse.is_active = not warehouse.is_active
        warehouse.updated_at = datetime.now()
        
        return warehouse