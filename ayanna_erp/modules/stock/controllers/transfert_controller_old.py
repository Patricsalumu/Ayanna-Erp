"""
Contrôleur pour la gestion des transferts entre entrepôts
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.boutique.model.models import (
    ShopWarehouse, ShopProduct, ShopWarehouseStock, ShopStockTransfer,
    ShopStockTransferItem, ShopStockMovement
)


class TransfertController:
    """Contrôleur pour la gestion des transferts entre entrepôts"""
    
    def __init__(self, pos_id: int):
        self.pos_id = pos_id
        self.db_manager = DatabaseManager()
    
    def get_all_transfers(self, session: Session, status: Optional[str] = None, 
                         limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Récupérer tous les transferts avec possibilité de filtrage"""
        query = session.query(ShopStockTransfer).join(
            ShopWarehouse, ShopStockTransfer.source_warehouse_id == ShopWarehouse.id
        ).filter(
            ShopWarehouse.pos_id == self.pos_id
        )
        
        if status:
            query = query.filter(ShopStockTransfer.status == status)
        
        query = query.order_by(desc(ShopStockTransfer.requested_date))
        
        if limit:
            query = query.limit(limit)
        
        transfers = query.all()
        
        return [self._format_transfer_data(session, transfer) for transfer in transfers]
    
    def _format_transfer_data(self, session: Session, transfer: ShopStockTransfer) -> Dict[str, Any]:
        """Formater les données d'un transfert"""
        # Récupérer les entrepôts source et destination
        source_warehouse = session.query(ShopWarehouse).get(transfer.source_warehouse_id)
        dest_warehouse = session.query(ShopWarehouse).get(transfer.destination_warehouse_id)
        
        # Compter les articles
        items_count = session.query(ShopStockTransferItem).filter(
            ShopStockTransferItem.transfer_id == transfer.id
        ).count()
        
        # Extraire le libellé des notes si présent
        label = ""
        notes = transfer.notes or ""
        if "Libellé:" in notes:
            try:
                parts = notes.split("Libellé:", 1)[1].split("\n", 1)
                label = parts[0].strip()
                notes = parts[1].strip() if len(parts) > 1 else ""
            except:
                label = notes
        
        return {
            'id': transfer.id,
            'transfer_number': transfer.transfer_number,
            'source_warehouse': {
                'id': source_warehouse.id if source_warehouse else None,
                'name': source_warehouse.name if source_warehouse else 'Inconnu',
                'code': source_warehouse.code if source_warehouse else 'N/A'
            },
            'destination_warehouse': {
                'id': dest_warehouse.id if dest_warehouse else None,
                'name': dest_warehouse.name if dest_warehouse else 'Inconnu',
                'code': dest_warehouse.code if dest_warehouse else 'N/A'
            },
            'status': transfer.status,
            'label': label,
            'notes': notes,
            'items_count': items_count,
            'requested_by': transfer.requested_by,
            'created_at': transfer.requested_date,
            'expected_date': transfer.expected_date,
            'shipped_date': transfer.shipped_date,
            'received_date': transfer.received_date,
            'priority': getattr(transfer, 'priority', 'NORMAL')
        }
    
    def get_transfer_by_id(self, session: Session, transfer_id: int) -> Optional[Dict[str, Any]]:
        """Récupérer un transfert par son ID avec ses articles"""
        transfer = session.query(ShopStockTransfer).filter(
            ShopStockTransfer.id == transfer_id
        ).first()
        
        if not transfer:
            return None
        
        # Vérifier que le transfert appartient à ce POS
        source_warehouse = session.query(ShopWarehouse).get(transfer.source_warehouse_id)
        if not source_warehouse or source_warehouse.pos_id != self.pos_id:
            return None
        
        transfer_data = self._format_transfer_data(session, transfer)
        
        # Récupérer les articles du transfert
        items = session.query(ShopStockTransferItem).join(
            ShopProduct, ShopStockTransferItem.product_id == ShopProduct.id
        ).filter(
            ShopStockTransferItem.transfer_id == transfer_id
        ).all()
        
        transfer_items = []
        for item in items:
            transfer_items.append({
                'id': item.id,
                'product_id': item.product_id,
                'product_name': item.product.name,
                'product_code': item.product.code,
                'quantity_requested': float(item.quantity_requested),
                'quantity_shipped': float(item.quantity_shipped or 0),
                'quantity_received': float(item.quantity_received or 0),
                'unit_cost': float(item.unit_cost),
                'notes': item.notes
            })
        
        transfer_data['items'] = transfer_items
        
        return transfer_data
    
    def create_transfer(self, session: Session, source_warehouse_id: int, 
                       destination_warehouse_id: int, items: List[Dict[str, Any]], 
                       label: str, notes: Optional[str] = None, 
                       expected_date: Optional[date] = None, 
                       requested_by: str = "Système") -> ShopStockTransfer:
        """Créer un nouveau transfert"""
        
        # Vérifier que les entrepôts existent et appartiennent au bon POS
        source_warehouse = session.query(ShopWarehouse).filter(
            and_(
                ShopWarehouse.id == source_warehouse_id,
                ShopWarehouse.pos_id == self.pos_id
            )
        ).first()
        
        dest_warehouse = session.query(ShopWarehouse).filter(
            and_(
                ShopWarehouse.id == destination_warehouse_id,
                ShopWarehouse.pos_id == self.pos_id
            )
        ).first()
        
        if not source_warehouse:
            raise ValueError("Entrepôt source non trouvé ou non autorisé.")
        
        if not dest_warehouse:
            raise ValueError("Entrepôt de destination non trouvé ou non autorisé.")
        
        if source_warehouse_id == destination_warehouse_id:
            raise ValueError("L'entrepôt source et destination doivent être différents.")
        
        # Générer un numéro de transfert unique
        transfer_number = self._generate_transfer_number(session)
        
        # Combiner le libellé et les notes
        combined_notes = f"Libellé: {label.strip()}"
        if notes and notes.strip():
            combined_notes += f"\n{notes.strip()}"
        
        # Créer le transfert
        transfer = ShopStockTransfer(
            transfer_number=transfer_number,
            source_warehouse_id=source_warehouse_id,
            destination_warehouse_id=destination_warehouse_id,
            status='PENDING',
            notes=combined_notes,
            requested_by=requested_by,
            expected_date=expected_date or datetime.now().date(),
            created_at=datetime.now()
        )
        
        session.add(transfer)
        session.flush()  # Pour obtenir l'ID
        
        # Ajouter les articles
        for item_data in items:
            # Vérifier la disponibilité du stock
            stock = session.query(ShopWarehouseStock).filter(
                and_(
                    ShopWarehouseStock.warehouse_id == source_warehouse_id,
                    ShopWarehouseStock.product_id == item_data['product_id']
                )
            ).first()
            
            if not stock:
                raise ValueError(f"Produit {item_data['product_id']} non trouvé dans l'entrepôt source.")
            
            available_qty = stock.quantity - (stock.reserved_quantity or Decimal('0'))
            if available_qty < item_data['quantity']:
                product = session.query(ShopProduct).get(item_data['product_id'])
                raise ValueError(f"Stock insuffisant pour {product.name}. Disponible: {available_qty}")
            
            # Créer l'article de transfert
            transfer_item = ShopStockTransferItem(
                transfer_id=transfer.id,
                product_id=item_data['product_id'],
                quantity_requested=item_data['quantity'],
                unit_cost=item_data.get('unit_cost', stock.unit_cost),
                notes=item_data.get('notes', '')
            )
            session.add(transfer_item)
            
            # Réserver le stock
            stock.reserved_quantity = (stock.reserved_quantity or Decimal('0')) + Decimal(str(item_data['quantity']))
            stock.updated_at = datetime.now()
        
        return transfer
    
    def _generate_transfer_number(self, session: Session) -> str:
        """Générer un numéro de transfert unique"""
        today = datetime.now()
        prefix = f"TR{today.year}{today.month:02d}{today.day:02d}"
        
        # Trouver le dernier numéro de la journée
        last_transfer = session.query(ShopStockTransfer).filter(
            ShopStockTransfer.transfer_number.like(f"{prefix}%")
        ).order_by(desc(ShopStockTransfer.transfer_number)).first()
        
        if last_transfer:
            try:
                last_sequence = int(last_transfer.transfer_number[-4:])
                sequence = last_sequence + 1
            except:
                sequence = 1
        else:
            sequence = 1
        
        return f"{prefix}{sequence:04d}"
    
    def update_transfer_status(self, session: Session, transfer_id: int, 
                              new_status: str, user: str = "Système") -> ShopStockTransfer:
        """Mettre à jour le statut d'un transfert"""
        transfer = session.query(ShopStockTransfer).get(transfer_id)
        if not transfer:
            raise ValueError(f"Transfert {transfer_id} non trouvé.")
        
        # Vérifier que le transfert appartient à ce POS
        source_warehouse = session.query(ShopWarehouse).get(transfer.source_warehouse_id)
        if not source_warehouse or source_warehouse.pos_id != self.pos_id:
            raise ValueError("Transfert non autorisé pour ce point de vente.")
        
        old_status = transfer.status
        transfer.status = new_status
        
        # Gérer les changements de statut
        if new_status == 'IN_TRANSIT' and old_status == 'PENDING':
            transfer.shipped_date = datetime.now()
            self._process_transfer_shipment(session, transfer)
        
        elif new_status == 'RECEIVED' and old_status == 'IN_TRANSIT':
            transfer.received_date = datetime.now()
            self._process_transfer_reception(session, transfer)
        
        elif new_status == 'CANCELLED':
            self._cancel_transfer(session, transfer)
        
        return transfer
    
    def _process_transfer_shipment(self, session: Session, transfer: ShopStockTransfer):
        """Traiter l'expédition d'un transfert"""
        items = session.query(ShopStockTransferItem).filter(
            ShopStockTransferItem.transfer_id == transfer.id
        ).all()
        
        for item in items:
            # Marquer la quantité comme expédiée
            item.quantity_shipped = item.quantity_requested
            
            # Retirer du stock source
            source_stock = session.query(ShopWarehouseStock).filter(
                and_(
                    ShopWarehouseStock.warehouse_id == transfer.source_warehouse_id,
                    ShopWarehouseStock.product_id == item.product_id
                )
            ).first()
            
            if source_stock:
                source_stock.quantity -= item.quantity_requested
                source_stock.reserved_quantity -= item.quantity_requested
                source_stock.updated_at = datetime.now()
                
                # Créer un mouvement de stock sortant
                self._create_stock_movement(
                    session, transfer.source_warehouse_id, item.product_id,
                    'TRANSFER_OUT', float(item.quantity_requested), float(item.unit_cost),
                    f"Transfert sortant: {transfer.transfer_number}"
                )
    
    def _process_transfer_reception(self, session: Session, transfer: ShopStockTransfer):
        """Traiter la réception d'un transfert"""
        items = session.query(ShopStockTransferItem).filter(
            ShopStockTransferItem.transfer_id == transfer.id
        ).all()
        
        for item in items:
            # Marquer la quantité comme reçue (par défaut = expédiée)
            item.quantity_received = item.quantity_shipped or item.quantity_requested
            
            # Ajouter au stock destination
            dest_stock = session.query(ShopWarehouseStock).filter(
                and_(
                    ShopWarehouseStock.warehouse_id == transfer.destination_warehouse_id,
                    ShopWarehouseStock.product_id == item.product_id
                )
            ).first()
            
            if dest_stock:
                dest_stock.quantity += item.quantity_received
                dest_stock.updated_at = datetime.now()
            else:
                # Créer le stock dans l'entrepôt de destination s'il n'existe pas
                product = session.query(ShopProduct).get(item.product_id)
                dest_stock = ShopWarehouseStock(
                    warehouse_id=transfer.destination_warehouse_id,
                    product_id=item.product_id,
                    quantity=item.quantity_received,
                    reserved_quantity=Decimal('0'),
                    unit_cost=item.unit_cost,
                    minimum_stock=product.minimum_stock or Decimal('0'),
                    maximum_stock=product.maximum_stock or Decimal('0'),
                    created_at=datetime.now()
                )
                session.add(dest_stock)
            
            # Créer un mouvement de stock entrant
            self._create_stock_movement(
                session, transfer.destination_warehouse_id, item.product_id,
                'TRANSFER_IN', float(item.quantity_received), float(item.unit_cost),
                f"Transfert entrant: {transfer.transfer_number}"
            )
    
    def _cancel_transfer(self, session: Session, transfer: ShopStockTransfer):
        """Annuler un transfert"""
        if transfer.status == 'PENDING':
            # Libérer les réservations
            items = session.query(ShopStockTransferItem).filter(
                ShopStockTransferItem.transfer_id == transfer.id
            ).all()
            
            for item in items:
                source_stock = session.query(ShopWarehouseStock).filter(
                    and_(
                        ShopWarehouseStock.warehouse_id == transfer.source_warehouse_id,
                        ShopWarehouseStock.product_id == item.product_id
                    )
                ).first()
                
                if source_stock:
                    source_stock.reserved_quantity -= item.quantity_requested
                    source_stock.updated_at = datetime.now()
    
    def _create_stock_movement(self, session: Session, warehouse_id: int, product_id: int,
                              movement_type: str, quantity: float, unit_cost: float, reference: str):
        """Créer un mouvement de stock"""
        movement = ShopStockMovement(
            warehouse_id=warehouse_id,
            product_id=product_id,
            movement_type=movement_type,
            quantity=Decimal(str(quantity)),
            unit_cost=Decimal(str(unit_cost)),
            reference=reference,
            movement_date=datetime.now(),
            created_at=datetime.now()
        )
        session.add(movement)
    
    def get_recent_transfers(self, session: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Récupérer les transferts récents"""
        return self.get_all_transfers(session, limit=limit)
    
    def get_transfers_by_status(self, session: Session, status: str) -> List[Dict[str, Any]]:
        """Récupérer les transferts par statut"""
        return self.get_all_transfers(session, status=status)
    
    def get_transfer_statistics(self, session: Session, start_date: Optional[date] = None,
                               end_date: Optional[date] = None) -> Dict[str, Any]:
        """Obtenir des statistiques sur les transferts"""
        base_query = session.query(ShopStockTransfer).join(
            ShopWarehouse, ShopStockTransfer.source_warehouse_id == ShopWarehouse.id
        ).filter(
            ShopWarehouse.pos_id == self.pos_id
        )
        
        if start_date:
            base_query = base_query.filter(ShopStockTransfer.requested_date >= start_date)
        
        if end_date:
            base_query = base_query.filter(ShopStockTransfer.requested_date <= end_date)
        
        # Statistiques par statut
        status_stats = {}
        for status in ['PENDING', 'IN_TRANSIT', 'RECEIVED', 'CANCELLED']:
            count = base_query.filter(ShopStockTransfer.status == status).count()
            status_stats[status] = count
        
        # Statistiques générales
        total_transfers = base_query.count()
        
        # Transferts du jour
        today = datetime.now().date()
        today_transfers = base_query.filter(
            func.date(ShopStockTransfer.requested_date) == today
        ).count()
        
        return {
            'total_transfers': total_transfers,
            'today_transfers': today_transfers,
            'status_breakdown': status_stats,
            'completion_rate': (status_stats.get('RECEIVED', 0) / total_transfers * 100) if total_transfers > 0 else 0
        }
    
    def search_transfers(self, session: Session, search_term: str) -> List[Dict[str, Any]]:
        """Rechercher des transferts par numéro ou notes"""
        transfers = session.query(ShopStockTransfer).join(
            ShopWarehouse, ShopStockTransfer.source_warehouse_id == ShopWarehouse.id
        ).filter(
            and_(
                ShopWarehouse.pos_id == self.pos_id,
                or_(
                    ShopStockTransfer.transfer_number.contains(search_term),
                    ShopStockTransfer.notes.contains(search_term)
                )
            )
        ).order_by(desc(ShopStockTransfer.requested_date)).all()
        
        return [self._format_transfer_data(session, transfer) for transfer in transfers]