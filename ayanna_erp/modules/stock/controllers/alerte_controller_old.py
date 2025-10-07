"""
Contrôleur pour la gestion des alertes de stock avec nouvelle structure simplifiée
"""

from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, case, text

from ayanna_erp.database.database_manager import DatabaseManager


class AlerteController:
    """Contrôleur pour la gestion des alertes de stock"""
    
    def __init__(self, entreprise_id: int):
        self.entreprise_id = entreprise_id
        self.db_manager = DatabaseManager()
    
    def get_all_alerts(self, session: Session, warehouse_id: Optional[int] = None,
                      alert_level: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Récupérer toutes les alertes de stock"""
        base_query = session.query(
            ShopProduct.id,
            ShopProduct.name,
            ShopProduct.code,
            ShopWarehouse.id.label('warehouse_id'),
            ShopWarehouse.name.label('warehouse_name'),
            ShopWarehouse.code.label('warehouse_code'),
            ShopWarehouseStock.quantity,
            ShopWarehouseStock.reserved_quantity,
            ShopWarehouseStock.minimum_stock,
            ShopWarehouseStock.maximum_stock,
            ShopWarehouseStock.unit_cost,
            ShopWarehouseStock.updated_at
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
        
        if limit:
            stocks = base_query.limit(limit).all()
        else:
            stocks = base_query.all()
        
        alerts = []
        for stock in stocks:
            alert = self._analyze_stock_alert(stock)
            if alert and (not alert_level or alert['level'] == alert_level):
                alerts.append(alert)
        
        # Trier par niveau de priorité puis par date
        priority_order = {'CRITICAL': 0, 'WARNING': 1, 'INFO': 2}
        alerts.sort(key=lambda x: (priority_order.get(x['level'], 3), x['product_name']))
        
        return alerts
    
    def _analyze_stock_alert(self, stock) -> Optional[Dict[str, Any]]:
        """Analyser un stock et déterminer s'il y a une alerte"""
        quantity = float(stock.quantity)
        reserved_qty = float(stock.reserved_quantity or 0)
        available_qty = quantity - reserved_qty
        min_stock = float(stock.minimum_stock or 0)
        max_stock = float(stock.maximum_stock or 0)
        
        alert = None
        
        # Rupture de stock totale
        if quantity == 0:
            alert = {
                'type': 'RUPTURE_STOCK',
                'level': 'CRITICAL',
                'priority': 1,
                'message': f"Rupture de stock totale",
                'recommendation': "Réapprovisionner immédiatement"
            }
        
        # Stock disponible épuisé (tout est réservé)
        elif available_qty <= 0 and quantity > 0:
            alert = {
                'type': 'STOCK_RESERVE',
                'level': 'CRITICAL',
                'priority': 2,
                'message': f"Stock entièrement réservé",
                'recommendation': "Aucun stock disponible pour nouvelle vente"
            }
        
        # Stock critique (en dessous du minimum)
        elif min_stock > 0 and available_qty < min_stock:
            if available_qty <= min_stock * 0.5:  # Moins de 50% du minimum
                level = 'CRITICAL'
                priority = 3
            else:
                level = 'WARNING'
                priority = 4
            
            alert = {
                'type': 'STOCK_FAIBLE',
                'level': level,
                'priority': priority,
                'message': f"Stock faible ({available_qty} < {min_stock})",
                'recommendation': f"Réapprovisionner avant d'atteindre 0"
            }
        
        # Surstock (au dessus du maximum)
        elif max_stock > 0 and quantity > max_stock:
            excess = quantity - max_stock
            alert = {
                'type': 'SURSTOCK',
                'level': 'INFO',
                'priority': 5,
                'message': f"Surstock détecté (+{excess} unités)",
                'recommendation': "Considérer transfert ou promotion"
            }
        
        # Stock déséquilibré (trop de réservé par rapport au total)
        elif quantity > 0 and (reserved_qty / quantity) > 0.8:
            alert = {
                'type': 'STOCK_DESEQUILIBRE',
                'level': 'WARNING',
                'priority': 6,
                'message': f"Stock fortement réservé ({reserved_qty}/{quantity})",
                'recommendation': "Vérifier les réservations et réapprovisionner"
            }
        
        if alert:
            alert.update({
                'product_id': stock.id,
                'product_name': stock.name,
                'product_code': stock.code,
                'warehouse_id': stock.warehouse_id,
                'warehouse_name': stock.warehouse_name,
                'warehouse_code': stock.warehouse_code,
                'current_quantity': quantity,
                'reserved_quantity': reserved_qty,
                'available_quantity': available_qty,
                'minimum_stock': min_stock,
                'maximum_stock': max_stock,
                'unit_cost': float(stock.unit_cost or 0),
                'stock_value': quantity * float(stock.unit_cost or 0),
                'last_updated': stock.updated_at,
                'alert_date': datetime.now()
            })
        
        return alert
    
    def get_alerts_summary(self, session: Session, warehouse_id: Optional[int] = None) -> Dict[str, Any]:
        """Obtenir un résumé des alertes"""
        alerts = self.get_all_alerts(session, warehouse_id)
        
        summary = {
            'total_alerts': len(alerts),
            'critical_count': len([a for a in alerts if a['level'] == 'CRITICAL']),
            'warning_count': len([a for a in alerts if a['level'] == 'WARNING']),
            'info_count': len([a for a in alerts if a['level'] == 'INFO']),
            'by_type': {},
            'by_warehouse': {},
            'total_value_at_risk': 0
        }
        
        # Grouper par type d'alerte
        for alert in alerts:
            alert_type = alert['type']
            if alert_type not in summary['by_type']:
                summary['by_type'][alert_type] = {
                    'count': 0,
                    'total_value': 0,
                    'products': []
                }
            
            summary['by_type'][alert_type]['count'] += 1
            summary['by_type'][alert_type]['total_value'] += alert['stock_value']
            summary['by_type'][alert_type]['products'].append({
                'product_name': alert['product_name'],
                'warehouse_name': alert['warehouse_name'],
                'quantity': alert['current_quantity']
            })
            
            # Grouper par entrepôt
            warehouse_name = alert['warehouse_name']
            if warehouse_name not in summary['by_warehouse']:
                summary['by_warehouse'][warehouse_name] = {
                    'count': 0,
                    'critical': 0,
                    'warning': 0,
                    'info': 0
                }
            
            summary['by_warehouse'][warehouse_name]['count'] += 1
            summary['by_warehouse'][warehouse_name][alert['level'].lower()] += 1
            
            # Valeur à risque (uniquement pour les alertes critiques et d'avertissement)
            if alert['level'] in ['CRITICAL', 'WARNING']:
                summary['total_value_at_risk'] += alert['stock_value']
        
        return summary
    
    def get_product_detailed_analysis(self, session: Session, product_id: int) -> Dict[str, Any]:
        """Analyser en détail un produit dans tous les entrepôts"""
        product = session.query(ShopProduct).filter(
            and_(
                ShopProduct.id == product_id,
                ShopProduct.pos_id == self.pos_id
            )
        ).first()
        
        if not product:
            raise ValueError(f"Produit {product_id} non trouvé.")
        
        # Récupérer les stocks dans tous les entrepôts
        stocks = session.query(
            ShopWarehouse.id,
            ShopWarehouse.name,
            ShopWarehouse.code,
            ShopWarehouse.type,
            ShopWarehouseStock.quantity,
            ShopWarehouseStock.reserved_quantity,
            ShopWarehouseStock.minimum_stock,
            ShopWarehouseStock.maximum_stock,
            ShopWarehouseStock.unit_cost,
            ShopWarehouseStock.updated_at
        ).join(
            ShopWarehouseStock, ShopWarehouse.id == ShopWarehouseStock.warehouse_id
        ).filter(
            and_(
                ShopWarehouseStock.product_id == product_id,
                ShopWarehouse.pos_id == self.pos_id,
                ShopWarehouse.is_active == True
            )
        ).all()
        
        # Analyser chaque entrepôt
        warehouse_analysis = []
        total_quantity = 0
        total_reserved = 0
        total_available = 0
        total_value = 0
        
        for stock in stocks:
            quantity = float(stock.quantity)
            reserved = float(stock.reserved_quantity or 0)
            available = quantity - reserved
            value = quantity * float(stock.unit_cost or 0)
            
            total_quantity += quantity
            total_reserved += reserved
            total_available += available
            total_value += value
            
            # Créer un objet stock temporaire pour l'analyse
            stock_obj = type('Stock', (), {
                'id': product_id,
                'name': product.name,
                'code': product.code,
                'warehouse_id': stock.id,
                'warehouse_name': stock.name,
                'warehouse_code': stock.code,
                'quantity': stock.quantity,
                'reserved_quantity': stock.reserved_quantity,
                'minimum_stock': stock.minimum_stock,
                'maximum_stock': stock.maximum_stock,
                'unit_cost': stock.unit_cost,
                'updated_at': stock.updated_at
            })()
            
            alert = self._analyze_stock_alert(stock_obj)
            
            warehouse_analysis.append({
                'warehouse_id': stock.id,
                'warehouse_name': stock.name,
                'warehouse_code': stock.code,
                'warehouse_type': stock.type,
                'quantity': quantity,
                'reserved_quantity': reserved,
                'available_quantity': available,
                'minimum_stock': float(stock.minimum_stock or 0),
                'maximum_stock': float(stock.maximum_stock or 0),
                'unit_cost': float(stock.unit_cost or 0),
                'stock_value': value,
                'last_updated': stock.updated_at,
                'alert': alert,
                'status': self._get_warehouse_stock_status(quantity, float(stock.minimum_stock or 0), float(stock.maximum_stock or 0))
            })
        
        # Récupérer les mouvements récents (30 derniers jours)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_movements = session.query(ShopStockMovement).join(
            ShopWarehouse, ShopStockMovement.warehouse_id == ShopWarehouse.id
        ).filter(
            and_(
                ShopStockMovement.product_id == product_id,
                ShopWarehouse.pos_id == self.pos_id,
                ShopStockMovement.movement_date >= thirty_days_ago
            )
        ).order_by(ShopStockMovement.movement_date.desc()).limit(20).all()
        
        movements_data = []
        for movement in recent_movements:
            warehouse = session.query(ShopWarehouse).get(movement.warehouse_id)
            movements_data.append({
                'date': movement.movement_date,
                'warehouse_name': warehouse.name if warehouse else 'Inconnu',
                'type': movement.movement_type,
                'quantity': float(movement.quantity),
                'reference': movement.reference
            })
        
        return {
            'product': {
                'id': product.id,
                'name': product.name,
                'code': product.code,
                'cost_price': float(product.cost_price or 0),
                'sale_price': float(product.sale_price or 0)
            },
            'totals': {
                'total_quantity': total_quantity,
                'total_reserved': total_reserved,
                'total_available': total_available,
                'total_value': total_value,
                'warehouses_count': len(warehouse_analysis)
            },
            'warehouse_analysis': warehouse_analysis,
            'recent_movements': movements_data,
            'recommendations': self._generate_product_recommendations(warehouse_analysis, total_available)
        }
    
    def _get_warehouse_stock_status(self, quantity: float, min_stock: float, max_stock: float) -> str:
        """Déterminer le statut du stock dans un entrepôt"""
        if quantity == 0:
            return 'RUPTURE'
        elif min_stock > 0 and quantity < min_stock:
            return 'FAIBLE'
        elif max_stock > 0 and quantity > max_stock:
            return 'EXCES'
        else:
            return 'NORMAL'
    
    def _generate_product_recommendations(self, warehouse_analysis: List[Dict], total_available: float) -> List[str]:
        """Générer des recommandations pour un produit"""
        recommendations = []
        
        # Analyse globale
        if total_available <= 0:
            recommendations.append("🔴 URGENT: Réapprovisionner immédiatement - Aucun stock disponible")
        
        # Déséquilibres entre entrepôts
        warehouses_with_excess = [w for w in warehouse_analysis if w['status'] == 'EXCES']
        warehouses_with_shortage = [w for w in warehouse_analysis if w['status'] in ['RUPTURE', 'FAIBLE']]
        
        if warehouses_with_excess and warehouses_with_shortage:
            recommendations.append(f"🔄 Envisager des transferts entre entrepôts:")
            for excess in warehouses_with_excess:
                for shortage in warehouses_with_shortage:
                    surplus = excess['quantity'] - excess['maximum_stock'] if excess['maximum_stock'] > 0 else excess['quantity'] * 0.2
                    recommendations.append(f"   • De {excess['warehouse_name']} vers {shortage['warehouse_name']} (jusqu'à {surplus:.0f} unités)")
        
        # Recommandations par entrepôt
        for warehouse in warehouse_analysis:
            if warehouse['alert']:
                if warehouse['alert']['type'] == 'RUPTURE_STOCK':
                    recommendations.append(f"⚠️ {warehouse['warehouse_name']}: Réapprovisionner immédiatement")
                elif warehouse['alert']['type'] == 'STOCK_FAIBLE':
                    needed = warehouse['minimum_stock'] - warehouse['available_quantity']
                    recommendations.append(f"📦 {warehouse['warehouse_name']}: Commander au moins {needed:.0f} unités")
        
        # Optimisation des stocks
        total_warehouses = len(warehouse_analysis)
        active_warehouses = len([w for w in warehouse_analysis if w['quantity'] > 0])
        
        if active_warehouses < total_warehouses * 0.7:
            recommendations.append("📍 Considérer une redistribution pour équilibrer les stocks entre entrepôts")
        
        return recommendations
    
    def get_critical_alerts_for_dashboard(self, session: Session, limit: int = 5) -> List[Dict[str, Any]]:
        """Récupérer les alertes critiques pour le tableau de bord"""
        alerts = self.get_all_alerts(session, alert_level='CRITICAL')
        
        # Trier par valeur du stock pour prioriser les plus importantes
        alerts.sort(key=lambda x: x['stock_value'], reverse=True)
        
        return alerts[:limit]
    
    def generate_stock_alerts_report(self, session: Session, warehouse_id: Optional[int] = None) -> Dict[str, Any]:
        """Générer un rapport complet des alertes de stock"""
        summary = self.get_alerts_summary(session, warehouse_id)
        all_alerts = self.get_all_alerts(session, warehouse_id)
        
        # Tendances (simulation - à améliorer avec des données historiques)
        trends = {
            'increasing_alerts': len([a for a in all_alerts if a['level'] == 'CRITICAL']),
            'new_alerts_today': len([a for a in all_alerts if a['alert_date'].date() == datetime.now().date()]),
            'resolved_alerts': 0  # À implémenter avec un système de suivi
        }
        
        # Recommandations globales
        global_recommendations = []
        
        if summary['critical_count'] > 10:
            global_recommendations.append("🚨 Nombre élevé d'alertes critiques - Réviser la politique de stock")
        
        if summary['total_value_at_risk'] > 10000:  # Exemple de seuil
            global_recommendations.append(f"💰 Valeur à risque élevée ({summary['total_value_at_risk']:.2f}) - Prioriser les actions")
        
        most_problematic_warehouse = max(summary['by_warehouse'].items(), key=lambda x: x[1]['critical']) if summary['by_warehouse'] else None
        if most_problematic_warehouse and most_problematic_warehouse[1]['critical'] > 5:
            global_recommendations.append(f"🏭 Entrepôt {most_problematic_warehouse[0]} nécessite une attention particulière")
        
        return {
            'summary': summary,
            'alerts': all_alerts,
            'trends': trends,
            'global_recommendations': global_recommendations,
            'report_generated_at': datetime.now(),
            'warehouse_filter': warehouse_id
        }
    
    def get_current_alerts(self, session: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Récupérer les alertes actuelles (méthode attendue par les widgets)"""
        return self.get_all_alerts(session, limit=limit)