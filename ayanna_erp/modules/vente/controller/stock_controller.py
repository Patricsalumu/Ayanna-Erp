"""
Contrôleur pour la gestion avancée des stocks et entrepôts
Fonctionnalités : CRUD entrepôts, transferts, inventaires, alertes
"""

from typing import List, Optional, Dict, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.boutique.model.models import (
    ShopWarehouse, ShopWarehouseStock, ShopStockMovementNew, 
    ShopStockTransfer, ShopStockTransferItem, ShopInventory, 
    ShopInventoryItem, ShopStockAlert, ShopProduct
)


class StockController:
    """Contrôleur pour la gestion des stocks et entrepôts"""
    
    def __init__(self, pos_id: int):
        self.pos_id = pos_id
        self.db_manager = DatabaseManager()
    
    # ==================== GESTION DES ENTREPÔTS ====================
    
    def create_warehouse(self, session: Session, code: str, name: str, 
                        type: str = 'storage', description: str = None,
                        address: str = None, contact_person: str = None,
                        contact_phone: str = None, contact_email: str = None,
                        is_default: bool = False, capacity_limit: Decimal = None) -> ShopWarehouse:
        """Créer un nouvel entrepôt"""
        
        # Si c'est l'entrepôt par défaut, désactiver les autres
        if is_default:
            session.query(ShopWarehouse).filter(
                ShopWarehouse.pos_id == self.pos_id
            ).update({'is_default': False})
        
        warehouse = ShopWarehouse(
            pos_id=self.pos_id,
            code=code,
            name=name,
            type=type,
            description=description,
            address=address,
            contact_person=contact_person,
            contact_phone=contact_phone,
            contact_email=contact_email,
            is_default=is_default,
            capacity_limit=capacity_limit
        )
        
        session.add(warehouse)
        session.commit()
        session.refresh(warehouse)
        
        return warehouse
    
    def get_warehouses(self, session: Session, active_only: bool = True) -> List[ShopWarehouse]:
        """Récupérer la liste des entrepôts"""
        query = session.query(ShopWarehouse).filter(ShopWarehouse.pos_id == self.pos_id)
        
        if active_only:
            query = query.filter(ShopWarehouse.is_active == True)
        
        return query.order_by(ShopWarehouse.is_default.desc(), ShopWarehouse.name).all()
    
    def get_warehouse_by_id(self, session: Session, warehouse_id: int) -> Optional[ShopWarehouse]:
        """Récupérer un entrepôt par son ID"""
        return session.query(ShopWarehouse).filter(
            ShopWarehouse.id == warehouse_id,
            ShopWarehouse.pos_id == self.pos_id
        ).first()
    
    def get_default_warehouse(self, session: Session) -> Optional[ShopWarehouse]:
        """Récupérer l'entrepôt par défaut"""
        return session.query(ShopWarehouse).filter(
            ShopWarehouse.pos_id == self.pos_id,
            ShopWarehouse.is_default == True,
            ShopWarehouse.is_active == True
        ).first()
    
    def update_warehouse(self, session: Session, warehouse_id: int, **kwargs) -> Optional[ShopWarehouse]:
        """Mettre à jour un entrepôt"""
        warehouse = self.get_warehouse_by_id(session, warehouse_id)
        if not warehouse:
            return None
        
        # Si on définit comme défaut, désactiver les autres
        if kwargs.get('is_default', False):
            session.query(ShopWarehouse).filter(
                ShopWarehouse.pos_id == self.pos_id,
                ShopWarehouse.id != warehouse_id
            ).update({'is_default': False})
        
        for key, value in kwargs.items():
            if hasattr(warehouse, key):
                setattr(warehouse, key, value)
        
        session.commit()
        session.refresh(warehouse)
        return warehouse
    
    # ==================== GESTION DES STOCKS PAR ENTREPÔT ====================
    
    def get_or_create_warehouse_stock(self, session: Session, warehouse_id: int, 
                                    product_id: int) -> ShopWarehouseStock:
        """Récupérer ou créer un stock d'entrepôt pour un produit"""
        stock = session.query(ShopWarehouseStock).filter(
            ShopWarehouseStock.warehouse_id == warehouse_id,
            ShopWarehouseStock.product_id == product_id
        ).first()
        
        if not stock:
            stock = ShopWarehouseStock(
                warehouse_id=warehouse_id,
                product_id=product_id
            )
            session.add(stock)
            session.commit()
            session.refresh(stock)
        
        return stock
    
    def get_product_stock_by_warehouse(self, session: Session, product_id: int) -> List[Dict]:
        """Récupérer le stock d'un produit dans tous les entrepôts"""
        results = session.query(
            ShopWarehouse,
            ShopWarehouseStock
        ).outerjoin(
            ShopWarehouseStock,
            and_(
                ShopWarehouseStock.warehouse_id == ShopWarehouse.id,
                ShopWarehouseStock.product_id == product_id
            )
        ).filter(
            ShopWarehouse.pos_id == self.pos_id,
            ShopWarehouse.is_active == True
        ).all()
        
        stocks = []
        for warehouse, stock in results:
            stocks.append({
                'warehouse': warehouse,
                'quantity_available': stock.quantity_available if stock else 0,
                'quantity_reserved': stock.quantity_reserved if stock else 0,
                'quantity_in_transit': stock.quantity_in_transit if stock else 0,
                'total_quantity': (stock.quantity_available if stock else 0) + 
                                (stock.quantity_reserved if stock else 0)
            })
        
        return stocks
    
    def get_total_product_stock(self, session: Session, product_id: int) -> Decimal:
        """Récupérer le stock total d'un produit (tous entrepôts confondus)"""
        result = session.query(
            func.sum(ShopWarehouseStock.quantity_available + ShopWarehouseStock.quantity_reserved)
        ).join(ShopWarehouse).filter(
            ShopWarehouse.pos_id == self.pos_id,
            ShopWarehouse.is_active == True,
            ShopWarehouseStock.product_id == product_id
        ).scalar()
        
        return result or Decimal('0.0')
    
    def get_warehouse_stock_summary(self, session: Session, warehouse_id: int) -> Dict:
        """Résumé des stocks d'un entrepôt"""
        stocks = session.query(ShopWarehouseStock).filter(
            ShopWarehouseStock.warehouse_id == warehouse_id
        ).all()
        
        total_products = len(stocks)
        total_quantity = sum(s.quantity_available + s.quantity_reserved for s in stocks)
        low_stock_count = sum(1 for s in stocks if s.quantity_available <= s.min_stock_level)
        
        return {
            'total_products': total_products,
            'total_quantity': total_quantity,
            'low_stock_count': low_stock_count,
            'stocks': stocks
        }
    
    # ==================== MOUVEMENTS DE STOCK ====================
    
    def add_stock_movement(self, session: Session, warehouse_id: int, product_id: int,
                          movement_type: str, direction: str, quantity: Decimal,
                          unit_cost: Decimal = None, reference_document: str = None,
                          reference_id: int = None, reason: str = None,
                          user_name: str = None, lot_number: str = None,
                          expiry_date: datetime = None) -> ShopStockMovementNew:
        """Ajouter un mouvement de stock"""
        
        # Récupérer ou créer le stock d'entrepôt
        warehouse_stock = self.get_or_create_warehouse_stock(session, warehouse_id, product_id)
        
        # Calculer les quantités avant et après
        quantity_before = warehouse_stock.quantity_available
        
        if direction == 'IN':
            quantity_after = quantity_before + quantity
            warehouse_stock.quantity_available = quantity_after
        else:  # OUT
            quantity_after = quantity_before - quantity
            warehouse_stock.quantity_available = max(Decimal('0.0'), quantity_after)
        
        # Mettre à jour la date du dernier mouvement
        warehouse_stock.last_movement_date = datetime.now()
        
        # Calculer le coût moyen pondéré pour les entrées
        if direction == 'IN' and unit_cost and unit_cost > 0:
            total_value_before = warehouse_stock.average_cost * quantity_before
            total_value_added = unit_cost * quantity
            new_total_quantity = warehouse_stock.quantity_available
            
            if new_total_quantity > 0:
                warehouse_stock.average_cost = (total_value_before + total_value_added) / new_total_quantity
        
        # Créer le mouvement
        movement = ShopStockMovementNew(
            warehouse_id=warehouse_id,
            warehouse_stock_id=warehouse_stock.id,
            product_id=product_id,
            movement_type=movement_type,
            direction=direction,
            quantity=quantity,
            unit_cost=unit_cost or Decimal('0.0'),
            total_cost=(unit_cost or Decimal('0.0')) * quantity,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            reference_document=reference_document,
            reference_id=reference_id,
            reason=reason,
            user_name=user_name,
            lot_number=lot_number,
            expiry_date=expiry_date
        )
        
        session.add(movement)
        session.commit()
        session.refresh(movement)
        
        # Vérifier les alertes de stock
        self._check_stock_alerts(session, warehouse_id, product_id)
        
        return movement
    
    def get_stock_movements(self, session: Session, warehouse_id: int = None,
                           product_id: int = None, movement_type: str = None,
                           start_date: datetime = None, end_date: datetime = None,
                           limit: int = 100) -> List[ShopStockMovementNew]:
        """Récupérer les mouvements de stock avec filtres"""
        query = session.query(ShopStockMovementNew).join(ShopWarehouse).filter(
            ShopWarehouse.pos_id == self.pos_id
        )
        
        if warehouse_id:
            query = query.filter(ShopStockMovementNew.warehouse_id == warehouse_id)
        
        if product_id:
            query = query.filter(ShopStockMovementNew.product_id == product_id)
        
        if movement_type:
            query = query.filter(ShopStockMovementNew.movement_type == movement_type)
        
        if start_date:
            query = query.filter(ShopStockMovementNew.movement_date >= start_date)
        
        if end_date:
            query = query.filter(ShopStockMovementNew.movement_date <= end_date)
        
        return query.order_by(desc(ShopStockMovementNew.movement_date)).limit(limit).all()
    
    # ==================== TRANSFERTS ENTRE ENTREPÔTS ====================
    
    def create_stock_transfer(self, session: Session, source_warehouse_id: int,
                             destination_warehouse_id: int, items: List[Dict],
                             priority: str = 'NORMAL', transfer_type: str = 'INTERNAL',
                             notes: str = None, requested_by: str = None) -> ShopStockTransfer:
        """Créer un transfert de stock entre entrepôts"""
        
        # Générer un numéro de transfert unique
        transfer_number = self._generate_transfer_number(session)
        
        # Créer le transfert
        transfer = ShopStockTransfer(
            transfer_number=transfer_number,
            source_warehouse_id=source_warehouse_id,
            destination_warehouse_id=destination_warehouse_id,
            priority=priority,
            transfer_type=transfer_type,
            notes=notes,
            requested_by=requested_by
        )
        
        session.add(transfer)
        session.flush()  # Pour obtenir l'ID
        
        # Ajouter les articles
        total_items = 0
        total_quantity = Decimal('0.0')
        total_cost = Decimal('0.0')
        
        for item_data in items:
            item = ShopStockTransferItem(
                transfer_id=transfer.id,
                product_id=item_data['product_id'],
                quantity_requested=item_data['quantity'],
                unit_cost=item_data.get('unit_cost', Decimal('0.0')),
                total_cost=item_data['quantity'] * item_data.get('unit_cost', Decimal('0.0')),
                lot_number=item_data.get('lot_number'),
                expiry_date=item_data.get('expiry_date'),
                notes=item_data.get('notes')
            )
            session.add(item)
            
            total_items += 1
            total_quantity += item_data['quantity']
            total_cost += item.total_cost
        
        # Mettre à jour les totaux
        transfer.total_items = total_items
        transfer.total_quantity = total_quantity
        transfer.total_cost = total_cost
        
        session.commit()
        session.refresh(transfer)
        
        return transfer
    
    def process_transfer(self, session: Session, transfer_id: int, action: str,
                        user_name: str = None, items_data: List[Dict] = None) -> bool:
        """Traiter un transfert (approve, ship, receive, cancel)"""
        
        transfer = session.query(ShopStockTransfer).filter(
            ShopStockTransfer.id == transfer_id
        ).first()
        
        if not transfer:
            return False
        
        current_time = datetime.now()
        
        if action == 'APPROVE':
            if transfer.status != 'PENDING':
                return False
            transfer.status = 'APPROVED'
            transfer.approved_by = user_name
            transfer.approved_date = current_time
        
        elif action == 'SHIP':
            if transfer.status != 'APPROVED':
                return False
            
            # Déduire les quantités de l'entrepôt source
            for item in transfer.transfer_items:
                self.add_stock_movement(
                    session=session,
                    warehouse_id=transfer.source_warehouse_id,
                    product_id=item.product_id,
                    movement_type='TRANSFER_OUT',
                    direction='OUT',
                    quantity=item.quantity_requested,
                    unit_cost=item.unit_cost,
                    reference_document=transfer.transfer_number,
                    reference_id=transfer.id,
                    reason=f"Transfert vers entrepôt {transfer.destination_warehouse_id}",
                    user_name=user_name
                )
                
                item.quantity_shipped = item.quantity_requested
            
            transfer.status = 'IN_TRANSIT'
            transfer.shipped_by = user_name
            transfer.shipped_date = current_time
        
        elif action == 'RECEIVE':
            if transfer.status != 'IN_TRANSIT':
                return False
            
            # Ajouter les quantités reçues à l'entrepôt destination
            for item_data in items_data or []:
                item = session.query(ShopStockTransferItem).filter(
                    ShopStockTransferItem.transfer_id == transfer_id,
                    ShopStockTransferItem.product_id == item_data['product_id']
                ).first()
                
                if item:
                    quantity_received = item_data.get('quantity_received', item.quantity_shipped)
                    item.quantity_received = quantity_received
                    
                    self.add_stock_movement(
                        session=session,
                        warehouse_id=transfer.destination_warehouse_id,
                        product_id=item.product_id,
                        movement_type='TRANSFER_IN',
                        direction='IN',
                        quantity=quantity_received,
                        unit_cost=item.unit_cost,
                        reference_document=transfer.transfer_number,
                        reference_id=transfer.id,
                        reason=f"Transfert depuis entrepôt {transfer.source_warehouse_id}",
                        user_name=user_name
                    )
            
            transfer.status = 'RECEIVED'
            transfer.received_by = user_name
            transfer.received_date = current_time
        
        elif action == 'CANCEL':
            if transfer.status in ['RECEIVED', 'CANCELLED']:
                return False
            transfer.status = 'CANCELLED'
        
        session.commit()
        return True
    
    def get_transfers(self, session: Session, warehouse_id: int = None,
                     status: str = None, start_date: datetime = None,
                     end_date: datetime = None) -> List[ShopStockTransfer]:
        """Récupérer les transferts avec filtres"""
        query = session.query(ShopStockTransfer)
        
        if warehouse_id:
            query = query.filter(
                or_(
                    ShopStockTransfer.source_warehouse_id == warehouse_id,
                    ShopStockTransfer.destination_warehouse_id == warehouse_id
                )
            )
        
        if status:
            query = query.filter(ShopStockTransfer.status == status)
        
        if start_date:
            query = query.filter(ShopStockTransfer.requested_date >= start_date)
        
        if end_date:
            query = query.filter(ShopStockTransfer.requested_date <= end_date)
        
        return query.order_by(desc(ShopStockTransfer.requested_date)).all()
    
    # ==================== ALERTES DE STOCK ====================
    
    def _check_stock_alerts(self, session: Session, warehouse_id: int, product_id: int):
        """Vérifier et créer les alertes de stock nécessaires"""
        warehouse_stock = session.query(ShopWarehouseStock).filter(
            ShopWarehouseStock.warehouse_id == warehouse_id,
            ShopWarehouseStock.product_id == product_id
        ).first()
        
        if not warehouse_stock:
            return
        
        current_qty = warehouse_stock.quantity_available
        min_level = warehouse_stock.min_stock_level or Decimal('0.0')
        reorder_point = warehouse_stock.reorder_point or Decimal('0.0')
        
        # Supprimer les anciennes alertes non résolues
        session.query(ShopStockAlert).filter(
            ShopStockAlert.warehouse_id == warehouse_id,
            ShopStockAlert.product_id == product_id,
            ShopStockAlert.resolved_date.is_(None)
        ).delete()
        
        # Vérifier les conditions d'alerte
        if current_qty <= 0:
            self._create_stock_alert(
                session, warehouse_id, product_id, 'OUT_OF_STOCK',
                current_qty, Decimal('0.0'), 'CRITICAL',
                'Produit en rupture de stock'
            )
        elif current_qty <= min_level:
            self._create_stock_alert(
                session, warehouse_id, product_id, 'LOW_STOCK',
                current_qty, min_level, 'WARNING',
                f'Stock faible: {current_qty} (minimum: {min_level})'
            )
        elif current_qty <= reorder_point:
            self._create_stock_alert(
                session, warehouse_id, product_id, 'REORDER_POINT',
                current_qty, reorder_point, 'INFO',
                f'Point de réapprovisionnement atteint: {current_qty}'
            )
    
    def _create_stock_alert(self, session: Session, warehouse_id: int, product_id: int,
                           alert_type: str, current_qty: Decimal, threshold_qty: Decimal,
                           alert_level: str, message: str):
        """Créer une alerte de stock"""
        alert = ShopStockAlert(
            warehouse_id=warehouse_id,
            product_id=product_id,
            alert_type=alert_type,
            current_quantity=current_qty,
            threshold_quantity=threshold_qty,
            alert_level=alert_level,
            message=message
        )
        session.add(alert)
    
    def get_stock_alerts(self, session: Session, warehouse_id: int = None,
                        alert_level: str = None, unresolved_only: bool = True) -> List[ShopStockAlert]:
        """Récupérer les alertes de stock"""
        query = session.query(ShopStockAlert).join(ShopWarehouse).filter(
            ShopWarehouse.pos_id == self.pos_id
        )
        
        if warehouse_id:
            query = query.filter(ShopStockAlert.warehouse_id == warehouse_id)
        
        if alert_level:
            query = query.filter(ShopStockAlert.alert_level == alert_level)
        
        if unresolved_only:
            query = query.filter(ShopStockAlert.resolved_date.is_(None))
        
        return query.order_by(
            ShopStockAlert.alert_level.desc(),
            ShopStockAlert.created_date.desc()
        ).all()
    
    # ==================== MÉTHODES UTILITAIRES ====================
    
    def _generate_transfer_number(self, session: Session) -> str:
        """Générer un numéro de transfert unique"""
        today = datetime.now()
        prefix = f"TR{today.strftime('%Y%m%d')}"
        
        # Compter les transferts du jour
        count = session.query(ShopStockTransfer).filter(
            ShopStockTransfer.transfer_number.like(f"{prefix}%")
        ).count()
        
        return f"{prefix}{count + 1:04d}"
    
    def migrate_existing_stock(self, session: Session):
        """Migrer les stocks existants vers le nouveau système d'entrepôts"""
        # Créer l'entrepôt par défaut s'il n'existe pas
        default_warehouse = self.get_default_warehouse(session)
        if not default_warehouse:
            default_warehouse = self.create_warehouse(
                session=session,
                code=f"POS{self.pos_id}",
                name=f"Entrepôt Point de Vente {self.pos_id}",
                type="shop",
                description="Entrepôt principal du point de vente",
                is_default=True
            )
        
        # Migrer les stocks existants
        products = session.query(ShopProduct).filter(
            ShopProduct.pos_id == self.pos_id
        ).all()
        
        for product in products:
            if product.stock_quantity and product.stock_quantity > 0:
                # Créer le stock d'entrepôt
                warehouse_stock = self.get_or_create_warehouse_stock(
                    session, default_warehouse.id, product.id
                )
                warehouse_stock.quantity_available = product.stock_quantity
                warehouse_stock.min_stock_level = product.stock_min
                
                # Créer un mouvement d'entrée initial
                self.add_stock_movement(
                    session=session,
                    warehouse_id=default_warehouse.id,
                    product_id=product.id,
                    movement_type='INITIAL_STOCK',
                    direction='IN',
                    quantity=product.stock_quantity,
                    reason='Migration du stock existant',
                    user_name='SYSTEM'
                )
        
        session.commit()