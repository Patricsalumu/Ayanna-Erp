"""
Contrôleur pour la gestion des stocks
"""

from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.boutique.model.models import (
    ShopWarehouse, ShopProduct, ShopWarehouseStock, ShopStockMovement
)


class StockController:
    """Contrôleur pour la gestion des stocks"""
    
    def __init__(self, pos_id: int):
        self.pos_id = pos_id
        self.db_manager = DatabaseManager()
    
    def get_stock_overview(self, session: Session, warehouse_id: Optional[int] = None) -> Dict[str, Any]:
        """Obtenir une vue d'ensemble des stocks"""
        base_query = session.query(
            ShopProduct.id,
            ShopProduct.name,
            ShopProduct.code,
            ShopProduct.cost_price,
            ShopProduct.sale_price,
            ShopWarehouse.id.label('warehouse_id'),
            ShopWarehouse.name.label('warehouse_name'),
            ShopWarehouse.code.label('warehouse_code'),
            ShopWarehouseStock.quantity,
            ShopWarehouseStock.reserved_quantity,
            ShopWarehouseStock.unit_cost,
            ShopWarehouseStock.minimum_stock,
            ShopWarehouseStock.maximum_stock
        ).join(
            ShopWarehouseStock, ShopProduct.id == ShopWarehouseStock.product_id
        ).join(
            ShopWarehouse, ShopWarehouseStock.warehouse_id == ShopWarehouse.id
        ).filter(
            and_(
                ShopProduct.pos_id == self.pos_id,
                ShopWarehouse.pos_id == self.pos_id,
                ShopWarehouse.is_active == True
            )
        )
        
        if warehouse_id:
            base_query = base_query.filter(ShopWarehouse.id == warehouse_id)
        
        stocks = base_query.order_by(
            ShopProduct.name, ShopWarehouse.name
        ).all()
        
        return self._format_stock_data(stocks)
    
    def _format_stock_data(self, stocks) -> Dict[str, Any]:
        """Formater les données de stock"""
        formatted_stocks = []
        total_value = 0
        total_products = set()
        warehouses = set()
        
        for stock in stocks:
            available_qty = float(stock.quantity) - float(stock.reserved_quantity or 0)
            stock_value = float(stock.quantity) * float(stock.unit_cost or 0)
            total_value += stock_value
            
            # Déterminer le statut du stock
            status = self._get_stock_status(
                float(stock.quantity), 
                float(stock.minimum_stock or 0), 
                float(stock.maximum_stock or 0)
            )
            
            formatted_stocks.append({
                'product_id': stock.id,
                'product_name': stock.name,
                'product_code': stock.code,
                'warehouse_id': stock.warehouse_id,
                'warehouse_name': stock.warehouse_name,
                'warehouse_code': stock.warehouse_code,
                'quantity': float(stock.quantity),
                'reserved_quantity': float(stock.reserved_quantity or 0),
                'available_quantity': available_qty,
                'unit_cost': float(stock.unit_cost or 0),
                'stock_value': stock_value,
                'minimum_stock': float(stock.minimum_stock or 0),
                'maximum_stock': float(stock.maximum_stock or 0),
                'cost_price': float(stock.cost_price or 0),
                'sale_price': float(stock.sale_price or 0),
                'status': status
            })
            
            total_products.add(stock.id)
            warehouses.add(stock.warehouse_id)
        
        return {
            'stocks': formatted_stocks,
            'summary': {
                'total_products': len(total_products),
                'total_warehouses': len(warehouses),
                'total_value': total_value,
                'total_items': len(formatted_stocks)
            }
        }
    
    def _get_stock_status(self, quantity: float, min_stock: float, max_stock: float) -> str:
        """Déterminer le statut du stock"""
        if quantity == 0:
            return 'RUPTURE'
        elif quantity < min_stock:
            return 'FAIBLE'
        elif max_stock > 0 and quantity > max_stock:
            return 'EXCES'
        else:
            return 'NORMAL'
    
    def get_product_stock_by_warehouses(self, session: Session, product_id: int) -> Dict[str, Any]:
        """Obtenir le stock d'un produit dans tous les entrepôts"""
        product = session.query(ShopProduct).filter(
            and_(
                ShopProduct.id == product_id,
                ShopProduct.pos_id == self.pos_id
            )
        ).first()
        
        if not product:
            raise ValueError(f"Produit avec l'ID {product_id} non trouvé.")
        
        stocks = session.query(
            ShopWarehouse.id,
            ShopWarehouse.name,
            ShopWarehouse.code,
            ShopWarehouse.type,
            ShopWarehouseStock.quantity,
            ShopWarehouseStock.reserved_quantity,
            ShopWarehouseStock.unit_cost,
            ShopWarehouseStock.minimum_stock,
            ShopWarehouseStock.maximum_stock
        ).join(
            ShopWarehouseStock, ShopWarehouse.id == ShopWarehouseStock.warehouse_id
        ).filter(
            and_(
                ShopWarehouseStock.product_id == product_id,
                ShopWarehouse.pos_id == self.pos_id,
                ShopWarehouse.is_active == True
            )
        ).order_by(ShopWarehouse.name).all()
        
        total_quantity = sum(float(stock.quantity) for stock in stocks)
        total_reserved = sum(float(stock.reserved_quantity or 0) for stock in stocks)
        total_available = total_quantity - total_reserved
        
        warehouse_stocks = []
        for stock in stocks:
            available_qty = float(stock.quantity) - float(stock.reserved_quantity or 0)
            
            warehouse_stocks.append({
                'warehouse_id': stock.id,
                'warehouse_name': stock.name,
                'warehouse_code': stock.code,
                'warehouse_type': stock.type,
                'quantity': float(stock.quantity),
                'reserved_quantity': float(stock.reserved_quantity or 0),
                'available_quantity': available_qty,
                'unit_cost': float(stock.unit_cost or 0),
                'minimum_stock': float(stock.minimum_stock or 0),
                'maximum_stock': float(stock.maximum_stock or 0),
                'status': self._get_stock_status(
                    float(stock.quantity),
                    float(stock.minimum_stock or 0),
                    float(stock.maximum_stock or 0)
                )
            })
        
        return {
            'product': {
                'id': product.id,
                'name': product.name,
                'code': product.code,
                'cost_price': float(product.cost_price or 0),
                'sale_price': float(product.sale_price or 0)
            },
            'warehouse_stocks': warehouse_stocks,
            'totals': {
                'total_quantity': total_quantity,
                'total_reserved': total_reserved,
                'total_available': total_available,
                'total_warehouses': len(warehouse_stocks)
            }
        }
    
    def search_products_with_stock(self, session: Session, search_term: str, warehouse_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Rechercher des produits avec leur stock"""
        base_query = session.query(
            ShopProduct.id,
            ShopProduct.name,
            ShopProduct.code,
            func.sum(ShopWarehouseStock.quantity).label('total_quantity'),
            func.sum(ShopWarehouseStock.reserved_quantity).label('total_reserved')
        ).join(
            ShopWarehouseStock, ShopProduct.id == ShopWarehouseStock.product_id
        ).join(
            ShopWarehouse, ShopWarehouseStock.warehouse_id == ShopWarehouse.id
        ).filter(
            and_(
                ShopProduct.pos_id == self.pos_id,
                ShopWarehouse.pos_id == self.pos_id,
                ShopWarehouse.is_active == True,
                or_(
                    ShopProduct.name.contains(search_term),
                    ShopProduct.code.contains(search_term)
                )
            )
        )
        
        if warehouse_id:
            base_query = base_query.filter(ShopWarehouse.id == warehouse_id)
        
        results = base_query.group_by(
            ShopProduct.id, ShopProduct.name, ShopProduct.code
        ).all()
        
        products = []
        for result in results:
            total_available = float(result.total_quantity or 0) - float(result.total_reserved or 0)
            
            products.append({
                'product_id': result.id,
                'product_name': result.name,
                'product_code': result.code,
                'total_quantity': float(result.total_quantity or 0),
                'total_reserved': float(result.total_reserved or 0),
                'total_available': total_available
            })
        
        return products
    
    def update_stock_levels(self, session: Session, warehouse_id: int, product_id: int, 
                           new_min: Optional[float] = None, new_max: Optional[float] = None) -> bool:
        """Mettre à jour les niveaux de stock minimum et maximum"""
        stock = session.query(ShopWarehouseStock).filter(
            and_(
                ShopWarehouseStock.warehouse_id == warehouse_id,
                ShopWarehouseStock.product_id == product_id
            )
        ).first()
        
        if not stock:
            raise ValueError("Stock non trouvé pour ce produit dans cet entrepôt.")
        
        if new_min is not None:
            stock.minimum_stock = Decimal(str(new_min))
        
        if new_max is not None:
            stock.maximum_stock = Decimal(str(new_max))
        
        stock.updated_at = datetime.now()
        
        return True
    
    def get_stock_alerts(self, session: Session, warehouse_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Obtenir les alertes de stock"""
        base_query = session.query(
            ShopProduct.id,
            ShopProduct.name,
            ShopProduct.code,
            ShopWarehouse.id.label('warehouse_id'),
            ShopWarehouse.name.label('warehouse_name'),
            ShopWarehouseStock.quantity,
            ShopWarehouseStock.minimum_stock,
            ShopWarehouseStock.maximum_stock
        ).join(
            ShopWarehouseStock, ShopProduct.id == ShopWarehouseStock.product_id
        ).join(
            ShopWarehouse, ShopWarehouseStock.warehouse_id == ShopWarehouse.id
        ).filter(
            and_(
                ShopProduct.pos_id == self.pos_id,
                ShopWarehouse.pos_id == self.pos_id,
                ShopWarehouse.is_active == True
            )
        )
        
        if warehouse_id:
            base_query = base_query.filter(ShopWarehouse.id == warehouse_id)
        
        stocks = base_query.all()
        
        alerts = []
        for stock in stocks:
            quantity = float(stock.quantity)
            min_stock = float(stock.minimum_stock or 0)
            max_stock = float(stock.maximum_stock or 0)
            
            # Rupture de stock
            if quantity == 0:
                alerts.append({
                    'type': 'RUPTURE',
                    'level': 'CRITICAL',
                    'product_id': stock.id,
                    'product_name': stock.name,
                    'product_code': stock.code,
                    'warehouse_id': stock.warehouse_id,
                    'warehouse_name': stock.warehouse_name,
                    'current_quantity': quantity,
                    'minimum_stock': min_stock,
                    'maximum_stock': max_stock,
                    'message': f"Rupture de stock pour {stock.name} dans {stock.warehouse_name}"
                })
            
            # Stock faible
            elif min_stock > 0 and quantity < min_stock:
                alerts.append({
                    'type': 'STOCK_FAIBLE',
                    'level': 'WARNING',
                    'product_id': stock.id,
                    'product_name': stock.name,
                    'product_code': stock.code,
                    'warehouse_id': stock.warehouse_id,
                    'warehouse_name': stock.warehouse_name,
                    'current_quantity': quantity,
                    'minimum_stock': min_stock,
                    'maximum_stock': max_stock,
                    'message': f"Stock faible pour {stock.name} dans {stock.warehouse_name} ({quantity} < {min_stock})"
                })
            
            # Surstock
            elif max_stock > 0 and quantity > max_stock:
                alerts.append({
                    'type': 'SURSTOCK',
                    'level': 'INFO',
                    'product_id': stock.id,
                    'product_name': stock.name,
                    'product_code': stock.code,
                    'warehouse_id': stock.warehouse_id,
                    'warehouse_name': stock.warehouse_name,
                    'current_quantity': quantity,
                    'minimum_stock': min_stock,
                    'maximum_stock': max_stock,
                    'message': f"Surstock pour {stock.name} dans {stock.warehouse_name} ({quantity} > {max_stock})"
                })
        
        return sorted(alerts, key=lambda x: {'CRITICAL': 0, 'WARNING': 1, 'INFO': 2}[x['level']])
    
    def get_stock_summary_statistics(self, session: Session) -> Dict[str, Any]:
        """Obtenir des statistiques résumées des stocks"""
        # Statistiques globales
        total_stats = session.query(
            func.count(ShopWarehouseStock.id).label('total_stock_entries'),
            func.sum(ShopWarehouseStock.quantity).label('total_quantity'),
            func.sum(ShopWarehouseStock.quantity * ShopWarehouseStock.unit_cost).label('total_value')
        ).join(
            ShopWarehouse, ShopWarehouseStock.warehouse_id == ShopWarehouse.id
        ).filter(
            ShopWarehouse.pos_id == self.pos_id
        ).first()
        
        # Produits uniques
        unique_products = session.query(ShopProduct.id).join(
            ShopWarehouseStock, ShopProduct.id == ShopWarehouseStock.product_id
        ).join(
            ShopWarehouse, ShopWarehouseStock.warehouse_id == ShopWarehouse.id
        ).filter(
            and_(
                ShopProduct.pos_id == self.pos_id,
                ShopWarehouse.pos_id == self.pos_id
            )
        ).distinct().count()
        
        # Entrepôts actifs
        active_warehouses = session.query(ShopWarehouse).filter(
            and_(
                ShopWarehouse.pos_id == self.pos_id,
                ShopWarehouse.is_active == True
            )
        ).count()
        
        # Produits en rupture
        out_of_stock = session.query(ShopWarehouseStock).join(
            ShopWarehouse, ShopWarehouseStock.warehouse_id == ShopWarehouse.id
        ).filter(
            and_(
                ShopWarehouse.pos_id == self.pos_id,
                ShopWarehouseStock.quantity == 0
            )
        ).count()
        
        # Produits avec stock faible
        low_stock = session.query(ShopWarehouseStock).join(
            ShopWarehouse, ShopWarehouseStock.warehouse_id == ShopWarehouse.id
        ).filter(
            and_(
                ShopWarehouse.pos_id == self.pos_id,
                ShopWarehouseStock.quantity > 0,
                ShopWarehouseStock.quantity < ShopWarehouseStock.minimum_stock,
                ShopWarehouseStock.minimum_stock > 0
            )
        ).count()
        
        return {
            'total_stock_entries': total_stats.total_stock_entries or 0,
            'total_quantity': float(total_stats.total_quantity or 0),
            'total_value': float(total_stats.total_value or 0),
            'unique_products': unique_products,
            'active_warehouses': active_warehouses,
            'out_of_stock_count': out_of_stock,
            'low_stock_count': low_stock
        }
    
    def export_stock_data(self, session: Session, warehouse_id: Optional[int] = None, 
                         format_type: str = 'csv') -> Dict[str, Any]:
        """Exporter les données de stock"""
        stock_data = self.get_stock_overview(session, warehouse_id)
        
        # Préparer les données pour l'export
        export_data = []
        for stock in stock_data['stocks']:
            export_data.append({
                'Code Produit': stock['product_code'],
                'Nom Produit': stock['product_name'],
                'Code Entrepôt': stock['warehouse_code'],
                'Nom Entrepôt': stock['warehouse_name'],
                'Quantité': stock['quantity'],
                'Quantité Réservée': stock['reserved_quantity'],
                'Quantité Disponible': stock['available_quantity'],
                'Coût Unitaire': stock['unit_cost'],
                'Valeur Stock': stock['stock_value'],
                'Stock Minimum': stock['minimum_stock'],
                'Stock Maximum': stock['maximum_stock'],
                'Statut': stock['status']
            })
        
        return {
            'data': export_data,
            'summary': stock_data['summary'],
            'export_info': {
                'format': format_type,
                'timestamp': datetime.now().isoformat(),
                'warehouse_filter': warehouse_id,
                'total_rows': len(export_data)
            }
        }
    
    def get_global_statistics(self, session: Session) -> Dict[str, Any]:
        """Récupérer les statistiques globales (méthode attendue par le dashboard)"""
        try:
            # Utiliser les statistiques existantes
            stats = self.get_stock_summary_statistics(session)
            
            # Ajouter quelques statistiques supplémentaires pour le dashboard
            global_stats = {
                'total_products': stats['unique_products'],
                'total_warehouses': stats['active_warehouses'],
                'total_stock_value': stats['total_value'],
                'total_quantity': stats['total_quantity'],
                'out_of_stock': stats['out_of_stock_count'],
                'low_stock': stats['low_stock_count'],
                'stock_entries': stats['total_stock_entries'],
                
                # Calculs supplémentaires
                'average_value_per_product': (
                    stats['total_value'] / stats['unique_products'] 
                    if stats['unique_products'] > 0 else 0
                ),
                'stock_health_percentage': (
                    max(0, 100 - (stats['out_of_stock_count'] + stats['low_stock_count']) * 2)
                    if stats['unique_products'] > 0 else 100
                ),
                
                # Indicateurs pour le dashboard
                'indicators': {
                    'healthy_stock': max(0, stats['unique_products'] - stats['out_of_stock_count'] - stats['low_stock_count']),
                    'needs_attention': stats['low_stock_count'],
                    'critical': stats['out_of_stock_count'],
                    'total_movements_today': 0  # À implémenter avec des données réelles
                }
            }
            
            return global_stats
            
        except Exception as e:
            print(f"Erreur lors de la récupération des statistiques globales: {e}")
            # Retourner des valeurs par défaut en cas d'erreur
            return {
                'total_products': 0,
                'total_warehouses': 0,
                'total_stock_value': 0.0,
                'total_quantity': 0.0,
                'out_of_stock': 0,
                'low_stock': 0,
                'stock_entries': 0,
                'average_value_per_product': 0.0,
                'stock_health_percentage': 100.0,
                'indicators': {
                    'healthy_stock': 0,
                    'needs_attention': 0,
                    'critical': 0,
                    'total_movements_today': 0
                }
            }