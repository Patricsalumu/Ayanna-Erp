"""
Contrôleur pour la génération de rapports de stock
"""

from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, case, text

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.boutique.model.models import (
    ShopWarehouse, ShopProduct, ShopWarehouseStock, ShopStockMovement, ShopStockTransfer
)


class RapportController:
    """Contrôleur pour la génération de rapports de stock"""
    
    def __init__(self, pos_id: int):
        self.pos_id = pos_id
        self.db_manager = DatabaseManager()
    
    def generate_stock_valuation_report(self, session: Session, warehouse_id: Optional[int] = None,
                                       valuation_date: Optional[date] = None) -> Dict[str, Any]:
        """Générer un rapport de valorisation des stocks"""
        
        if not valuation_date:
            valuation_date = datetime.now().date()
        
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
        
        stocks = base_query.order_by(ShopWarehouse.name, ShopProduct.name).all()
        
        # Calculs de valorisation
        total_cost_value = 0
        total_sale_value = 0
        total_quantity = 0
        items_by_warehouse = {}
        
        for stock in stocks:
            quantity = float(stock.quantity)
            cost_price = float(stock.unit_cost or stock.cost_price or 0)
            sale_price = float(stock.sale_price or 0)
            
            cost_value = quantity * cost_price
            sale_value = quantity * sale_price
            potential_margin = sale_value - cost_value
            
            total_cost_value += cost_value
            total_sale_value += sale_value
            total_quantity += quantity
            
            warehouse_name = stock.warehouse_name
            if warehouse_name not in items_by_warehouse:
                items_by_warehouse[warehouse_name] = {
                    'warehouse_id': stock.warehouse_id,
                    'warehouse_code': stock.warehouse_code,
                    'products': [],
                    'total_cost_value': 0,
                    'total_sale_value': 0,
                    'total_quantity': 0
                }
            
            items_by_warehouse[warehouse_name]['products'].append({
                'product_id': stock.id,
                'product_name': stock.name,
                'product_code': stock.code,
                'quantity': quantity,
                'unit_cost': cost_price,
                'unit_sale_price': sale_price,
                'cost_value': cost_value,
                'sale_value': sale_value,
                'potential_margin': potential_margin,
                'margin_percentage': (potential_margin / sale_value * 100) if sale_value > 0 else 0
            })
            
            items_by_warehouse[warehouse_name]['total_cost_value'] += cost_value
            items_by_warehouse[warehouse_name]['total_sale_value'] += sale_value
            items_by_warehouse[warehouse_name]['total_quantity'] += quantity
        
        return {
            'report_info': {
                'title': 'Rapport de Valorisation des Stocks',
                'valuation_date': valuation_date,
                'generated_at': datetime.now(),
                'warehouse_filter': warehouse_id
            },
            'summary': {
                'total_cost_value': total_cost_value,
                'total_sale_value': total_sale_value,
                'total_potential_margin': total_sale_value - total_cost_value,
                'total_quantity': total_quantity,
                'average_margin_percentage': ((total_sale_value - total_cost_value) / total_sale_value * 100) if total_sale_value > 0 else 0,
                'warehouses_count': len(items_by_warehouse),
                'products_count': len(stocks)
            },
            'by_warehouse': items_by_warehouse
        }
    
    def generate_movement_analysis_report(self, session: Session, start_date: date, end_date: date,
                                        warehouse_id: Optional[int] = None,
                                        product_id: Optional[int] = None) -> Dict[str, Any]:
        """Générer un rapport d'analyse des mouvements de stock"""
        
        base_query = session.query(ShopStockMovement).join(
            ShopWarehouse, ShopStockMovement.warehouse_id == ShopWarehouse.id
        ).join(
            ShopProduct, ShopStockMovement.product_id == ShopProduct.id
        ).filter(
            and_(
                ShopWarehouse.pos_id == self.pos_id,
                ShopStockMovement.movement_date >= start_date,
                ShopStockMovement.movement_date <= end_date
            )
        )
        
        if warehouse_id:
            base_query = base_query.filter(ShopWarehouse.id == warehouse_id)
        
        if product_id:
            base_query = base_query.filter(ShopProduct.id == product_id)
        
        movements = base_query.order_by(ShopStockMovement.movement_date.desc()).all()
        
        # Analyse des mouvements
        movements_by_type = {}
        movements_by_day = {}
        movements_by_warehouse = {}
        movements_by_product = {}
        
        total_in_quantity = 0
        total_out_quantity = 0
        total_in_value = 0
        total_out_value = 0
        
        for movement in movements:
            movement_type = movement.movement_type
            quantity = float(movement.quantity)
            unit_cost = float(movement.unit_cost)
            value = quantity * unit_cost
            day = movement.movement_date.date()
            
            # Par type de mouvement
            if movement_type not in movements_by_type:
                movements_by_type[movement_type] = {
                    'count': 0,
                    'total_quantity': 0,
                    'total_value': 0,
                    'movements': []
                }
            
            movements_by_type[movement_type]['count'] += 1
            movements_by_type[movement_type]['total_quantity'] += quantity
            movements_by_type[movement_type]['total_value'] += value
            movements_by_type[movement_type]['movements'].append({
                'date': movement.movement_date,
                'warehouse_name': movement.warehouse.name,
                'product_name': movement.product.name,
                'quantity': quantity,
                'unit_cost': unit_cost,
                'value': value,
                'reference': movement.reference
            })
            
            # Par jour
            if day not in movements_by_day:
                movements_by_day[day] = {
                    'total_movements': 0,
                    'total_in': 0,
                    'total_out': 0,
                    'net_movement': 0
                }
            
            movements_by_day[day]['total_movements'] += 1
            
            # Déterminer si c'est une entrée ou sortie
            if movement_type in ['PURCHASE', 'TRANSFER_IN', 'INVENTORY_ADJUSTMENT_IN']:
                movements_by_day[day]['total_in'] += quantity
                total_in_quantity += quantity
                total_in_value += value
            else:
                movements_by_day[day]['total_out'] += quantity
                total_out_quantity += quantity
                total_out_value += value
            
            movements_by_day[day]['net_movement'] = movements_by_day[day]['total_in'] - movements_by_day[day]['total_out']
            
            # Par entrepôt
            warehouse_name = movement.warehouse.name
            if warehouse_name not in movements_by_warehouse:
                movements_by_warehouse[warehouse_name] = {
                    'warehouse_id': movement.warehouse_id,
                    'total_movements': 0,
                    'total_value': 0
                }
            
            movements_by_warehouse[warehouse_name]['total_movements'] += 1
            movements_by_warehouse[warehouse_name]['total_value'] += value
            
            # Par produit
            product_name = movement.product.name
            if product_name not in movements_by_product:
                movements_by_product[product_name] = {
                    'product_id': movement.product_id,
                    'total_movements': 0,
                    'total_quantity': 0,
                    'total_value': 0
                }
            
            movements_by_product[product_name]['total_movements'] += 1
            movements_by_product[product_name]['total_quantity'] += quantity
            movements_by_product[product_name]['total_value'] += value
        
        return {
            'report_info': {
                'title': 'Rapport d\'Analyse des Mouvements',
                'period': f"{start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}",
                'generated_at': datetime.now(),
                'warehouse_filter': warehouse_id,
                'product_filter': product_id
            },
            'summary': {
                'total_movements': len(movements),
                'total_in_quantity': total_in_quantity,
                'total_out_quantity': total_out_quantity,
                'net_quantity': total_in_quantity - total_out_quantity,
                'total_in_value': total_in_value,
                'total_out_value': total_out_value,
                'net_value': total_in_value - total_out_value
            },
            'by_type': movements_by_type,
            'by_day': dict(sorted(movements_by_day.items(), reverse=True)),
            'by_warehouse': movements_by_warehouse,
            'by_product': movements_by_product
        }
    
    def generate_turnover_analysis_report(self, session: Session, analysis_period_days: int = 90,
                                        warehouse_id: Optional[int] = None) -> Dict[str, Any]:
        """Générer un rapport d'analyse de rotation des stocks"""
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=analysis_period_days)
        
        # Récupérer les mouvements de sortie (ventes) sur la période
        outbound_movements = session.query(
            ShopStockMovement.product_id,
            func.sum(ShopStockMovement.quantity).label('total_sold'),
            func.avg(ShopStockMovement.unit_cost).label('avg_cost')
        ).join(
            ShopWarehouse, ShopStockMovement.warehouse_id == ShopWarehouse.id
        ).filter(
            and_(
                ShopWarehouse.pos_id == self.pos_id,
                ShopStockMovement.movement_type.in_(['SALE', 'TRANSFER_OUT']),
                ShopStockMovement.movement_date >= start_date,
                ShopStockMovement.movement_date <= end_date
            )
        )
        
        if warehouse_id:
            outbound_movements = outbound_movements.filter(ShopWarehouse.id == warehouse_id)
        
        outbound_movements = outbound_movements.group_by(ShopStockMovement.product_id).all()
        
        # Récupérer les stocks actuels
        current_stocks = session.query(
            ShopProduct.id,
            ShopProduct.name,
            ShopProduct.code,
            ShopWarehouse.name.label('warehouse_name'),
            ShopWarehouseStock.quantity,
            ShopWarehouseStock.unit_cost
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
            current_stocks = current_stocks.filter(ShopWarehouse.id == warehouse_id)
        
        current_stocks = current_stocks.all()
        
        # Calculer les ratios de rotation
        turnover_analysis = []
        sold_products = {movement.product_id: movement for movement in outbound_movements}
        
        for stock in current_stocks:
            product_id = stock.id
            current_qty = float(stock.quantity)
            
            if product_id in sold_products:
                sold_data = sold_products[product_id]
                total_sold = float(sold_data.total_sold)
                
                # Calcul du taux de rotation (sur base annuelle)
                annual_sold = (total_sold / analysis_period_days) * 365
                turnover_ratio = annual_sold / current_qty if current_qty > 0 else 0
                
                # Calcul des jours de stock restant
                daily_sales = total_sold / analysis_period_days
                days_of_stock = current_qty / daily_sales if daily_sales > 0 else float('inf')
                
                # Classification
                if turnover_ratio >= 12:  # Plus de 12 rotations par an
                    classification = 'ROTATION_RAPIDE'
                elif turnover_ratio >= 4:  # 4-12 rotations par an
                    classification = 'ROTATION_NORMALE'
                elif turnover_ratio >= 1:  # 1-4 rotations par an
                    classification = 'ROTATION_LENTE'
                else:  # Moins d'1 rotation par an
                    classification = 'ROTATION_TRES_LENTE'
            else:
                # Produit non vendu sur la période
                total_sold = 0
                annual_sold = 0
                turnover_ratio = 0
                days_of_stock = float('inf')
                classification = 'NON_VENDU'
            
            turnover_analysis.append({
                'product_id': product_id,
                'product_name': stock.name,
                'product_code': stock.code,
                'warehouse_name': stock.warehouse_name,
                'current_quantity': current_qty,
                'sold_quantity': total_sold,
                'turnover_ratio': turnover_ratio,
                'days_of_stock': days_of_stock if days_of_stock != float('inf') else None,
                'classification': classification,
                'stock_value': current_qty * float(stock.unit_cost or 0)
            })
        
        # Statistiques globales
        total_products = len(turnover_analysis)
        classifications = {}
        total_stock_value = 0
        
        for item in turnover_analysis:
            classification = item['classification']
            if classification not in classifications:
                classifications[classification] = {
                    'count': 0,
                    'total_value': 0,
                    'products': []
                }
            
            classifications[classification]['count'] += 1
            classifications[classification]['total_value'] += item['stock_value']
            classifications[classification]['products'].append(item['product_name'])
            total_stock_value += item['stock_value']
        
        return {
            'report_info': {
                'title': 'Rapport d\'Analyse de Rotation des Stocks',
                'analysis_period': f"{analysis_period_days} jours",
                'period_start': start_date,
                'period_end': end_date,
                'generated_at': datetime.now(),
                'warehouse_filter': warehouse_id
            },
            'summary': {
                'total_products': total_products,
                'total_stock_value': total_stock_value,
                'classifications_breakdown': {k: v['count'] for k, v in classifications.items()},
                'value_by_classification': {k: v['total_value'] for k, v in classifications.items()}
            },
            'detailed_analysis': turnover_analysis,
            'classifications': classifications,
            'recommendations': self._generate_turnover_recommendations(classifications, total_stock_value)
        }
    
    def _generate_turnover_recommendations(self, classifications: Dict, total_value: float) -> List[str]:
        """Générer des recommandations basées sur l'analyse de rotation"""
        recommendations = []
        
        # Produits non vendus
        if 'NON_VENDU' in classifications:
            non_sold_count = classifications['NON_VENDU']['count']
            non_sold_value = classifications['NON_VENDU']['total_value']
            if non_sold_count > 0:
                recommendations.append(
                    f"🔴 {non_sold_count} produits non vendus (valeur: {non_sold_value:.2f}) - "
                    f"Considérer promotions ou déstockage"
                )
        
        # Rotation très lente
        if 'ROTATION_TRES_LENTE' in classifications:
            slow_count = classifications['ROTATION_TRES_LENTE']['count']
            slow_value = classifications['ROTATION_TRES_LENTE']['total_value']
            recommendations.append(
                f"🟡 {slow_count} produits à rotation très lente (valeur: {slow_value:.2f}) - "
                f"Réviser les quantités commandées"
            )
        
        # Rotation rapide
        if 'ROTATION_RAPIDE' in classifications:
            fast_count = classifications['ROTATION_RAPIDE']['count']
            fast_value = classifications['ROTATION_RAPIDE']['total_value']
            recommendations.append(
                f"🟢 {fast_count} produits à rotation rapide (valeur: {fast_value:.2f}) - "
                f"Assurer un réapprovisionnement régulier"
            )
        
        # Analyse globale
        slow_value_percentage = 0
        if 'ROTATION_TRES_LENTE' in classifications and 'NON_VENDU' in classifications:
            slow_total = classifications['ROTATION_TRES_LENTE']['total_value'] + classifications['NON_VENDU']['total_value']
            slow_value_percentage = (slow_total / total_value * 100) if total_value > 0 else 0
        
        if slow_value_percentage > 30:
            recommendations.append(
                f"⚠️ {slow_value_percentage:.1f}% de la valeur stock en produits lents - "
                f"Réviser la stratégie d'achat"
            )
        
        return recommendations
    
    def generate_abc_analysis_report(self, session: Session, analysis_period_days: int = 90) -> Dict[str, Any]:
        """Générer un rapport d'analyse ABC des produits"""
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=analysis_period_days)
        
        # Récupérer les ventes par produit
        sales_data = session.query(
            ShopProduct.id,
            ShopProduct.name,
            ShopProduct.code,
            func.sum(ShopStockMovement.quantity).label('total_quantity_sold'),
            func.sum(ShopStockMovement.quantity * ShopStockMovement.unit_cost).label('total_value_sold'),
            func.count(ShopStockMovement.id).label('transaction_count')
        ).join(
            ShopStockMovement, ShopProduct.id == ShopStockMovement.product_id
        ).join(
            ShopWarehouse, ShopStockMovement.warehouse_id == ShopWarehouse.id
        ).filter(
            and_(
                ShopWarehouse.pos_id == self.pos_id,
                ShopStockMovement.movement_type == 'SALE',
                ShopStockMovement.movement_date >= start_date,
                ShopStockMovement.movement_date <= end_date
            )
        ).group_by(
            ShopProduct.id, ShopProduct.name, ShopProduct.code
        ).order_by(
            func.sum(ShopStockMovement.quantity * ShopStockMovement.unit_cost).desc()
        ).all()
        
        if not sales_data:
            return {
                'report_info': {
                    'title': 'Analyse ABC des Produits',
                    'period': f"{start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}",
                    'generated_at': datetime.now()
                },
                'message': 'Aucune donnée de vente trouvée pour la période sélectionnée.'
            }
        
        # Calculer les cumuls
        total_value = sum(float(item.total_value_sold) for item in sales_data)
        products_with_cumul = []
        cumulative_value = 0
        
        for i, item in enumerate(sales_data):
            value_sold = float(item.total_value_sold)
            cumulative_value += value_sold
            cumulative_percentage = (cumulative_value / total_value * 100) if total_value > 0 else 0
            
            products_with_cumul.append({
                'rank': i + 1,
                'product_id': item.id,
                'product_name': item.name,
                'product_code': item.code,
                'quantity_sold': float(item.total_quantity_sold),
                'value_sold': value_sold,
                'value_percentage': (value_sold / total_value * 100) if total_value > 0 else 0,
                'cumulative_percentage': cumulative_percentage,
                'transaction_count': item.transaction_count
            })
        
        # Classification ABC
        abc_classification = {'A': [], 'B': [], 'C': []}
        
        for product in products_with_cumul:
            if product['cumulative_percentage'] <= 80:
                product['category'] = 'A'
                abc_classification['A'].append(product)
            elif product['cumulative_percentage'] <= 95:
                product['category'] = 'B'
                abc_classification['B'].append(product)
            else:
                product['category'] = 'C'
                abc_classification['C'].append(product)
        
        return {
            'report_info': {
                'title': 'Analyse ABC des Produits',
                'period': f"{start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}",
                'generated_at': datetime.now(),
                'total_products_analyzed': len(products_with_cumul)
            },
            'summary': {
                'total_value_sold': total_value,
                'category_A_count': len(abc_classification['A']),
                'category_B_count': len(abc_classification['B']),
                'category_C_count': len(abc_classification['C']),
                'category_A_value': sum(p['value_sold'] for p in abc_classification['A']),
                'category_B_value': sum(p['value_sold'] for p in abc_classification['B']),
                'category_C_value': sum(p['value_sold'] for p in abc_classification['C'])
            },
            'products': products_with_cumul,
            'abc_classification': abc_classification,
            'recommendations': self._generate_abc_recommendations(abc_classification)
        }
    
    def _generate_abc_recommendations(self, abc_classification: Dict) -> List[str]:
        """Générer des recommandations basées sur l'analyse ABC"""
        recommendations = []
        
        # Catégorie A (80% de la valeur)
        category_a_count = len(abc_classification['A'])
        recommendations.append(
            f"🔥 Catégorie A ({category_a_count} produits): Priorité maximale - "
            f"Surveillance quotidienne des stocks, réapprovisionnement rapide"
        )
        
        # Catégorie B (15% de la valeur)
        category_b_count = len(abc_classification['B'])
        recommendations.append(
            f"📊 Catégorie B ({category_b_count} produits): Importance moyenne - "
            f"Surveillance hebdomadaire, réapprovisionnement régulier"
        )
        
        # Catégorie C (5% de la valeur)
        category_c_count = len(abc_classification['C'])
        recommendations.append(
            f"📉 Catégorie C ({category_c_count} produits): Faible priorité - "
            f"Surveillance mensuelle, stocks de sécurité réduits"
        )
        
        if category_c_count > category_a_count * 3:
            recommendations.append(
                "⚠️ Nombre élevé de produits en catégorie C - "
                "Considérer une réduction de l'assortiment"
            )
        
        return recommendations
    
    def export_report_data(self, report_data: Dict[str, Any], format_type: str = 'dict') -> Dict[str, Any]:
        """Exporter les données de rapport dans différents formats"""
        
        export_info = {
            'exported_at': datetime.now(),
            'format': format_type,
            'source_report': report_data.get('report_info', {}).get('title', 'Rapport Inconnu')
        }
        
        if format_type == 'csv_ready':
            # Préparer les données pour export CSV
            if 'by_warehouse' in report_data:
                # Rapport de valorisation
                csv_data = []
                for warehouse_name, warehouse_data in report_data['by_warehouse'].items():
                    for product in warehouse_data['products']:
                        csv_data.append({
                            'Entrepôt': warehouse_name,
                            'Code Produit': product['product_code'],
                            'Nom Produit': product['product_name'],
                            'Quantité': product['quantity'],
                            'Coût Unitaire': product['unit_cost'],
                            'Prix Vente': product['unit_sale_price'],
                            'Valeur Coût': product['cost_value'],
                            'Valeur Vente': product['sale_value'],
                            'Marge Potentielle': product['potential_margin']
                        })
                return {'export_info': export_info, 'csv_data': csv_data}
            
            elif 'products' in report_data:
                # Rapport ABC
                csv_data = []
                for product in report_data['products']:
                    csv_data.append({
                        'Rang': product['rank'],
                        'Catégorie ABC': product['category'],
                        'Code Produit': product['product_code'],
                        'Nom Produit': product['product_name'],
                        'Quantité Vendue': product['quantity_sold'],
                        'Valeur Vendue': product['value_sold'],
                        '% Valeur': product['value_percentage'],
                        '% Cumulé': product['cumulative_percentage']
                    })
                return {'export_info': export_info, 'csv_data': csv_data}
        
        return {'export_info': export_info, 'data': report_data}
    
    def get_recent_reports(self, session: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Récupérer les rapports récents (méthode attendue par les widgets)"""
        try:
            # Simuler des rapports récents (en attendant l'implémentation d'un système de sauvegarde)
            recent_reports = []
            
            # Générer quelques rapports d'exemple avec des dates récentes
            current_date = datetime.now()
            
            for i in range(min(limit, 5)):  # Limiter à 5 rapports d'exemple
                days_ago = i
                report_date = current_date - timedelta(days=days_ago)
                
                if i == 0:
                    report_type = "Valorisation des stocks"
                    status = "Généré"
                elif i == 1:
                    report_type = "Analyse ABC"
                    status = "En cours"
                elif i == 2:
                    report_type = "Mouvements de stock"
                    status = "Généré"
                elif i == 3:
                    report_type = "Rapport d'alertes"
                    status = "Généré"
                else:
                    report_type = "Rapport d'inventaire"
                    status = "Archivé"
                
                recent_reports.append({
                    'id': i + 1,
                    'title': f"{report_type} - {report_date.strftime('%d/%m/%Y')}",
                    'type': report_type,
                    'status': status,
                    'created_date': report_date,
                    'created_by': 'Système',
                    'description': f"Rapport automatique généré le {report_date.strftime('%d/%m/%Y à %H:%M')}",
                    'file_size': f"{50 + i * 10}KB",
                    'format': 'PDF/Excel',
                    # Informations d'affichage
                    'status_color': {
                        'Généré': '#28a745',
                        'En cours': '#ffc107',
                        'Archivé': '#6c757d'
                    }.get(status, '#007bff'),
                    'type_icon': {
                        'Valorisation des stocks': '💰',
                        'Analyse ABC': '📊',
                        'Mouvements de stock': '📦',
                        'Rapport d\'alertes': '⚠️',
                        'Rapport d\'inventaire': '📋'
                    }.get(report_type, '📄'),
                    'can_download': status == 'Généré',
                    'can_view': True,
                    'can_regenerate': status in ['Généré', 'Archivé']
                })
            
            return recent_reports
            
        except Exception as e:
            print(f"Erreur lors de la récupération des rapports récents: {e}")
            return []