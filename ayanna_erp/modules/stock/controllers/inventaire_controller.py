"""
Contrôleur pour la gestion des inventaires
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.boutique.model.models import (
    ShopWarehouse, ShopProduct, ShopWarehouseStock, ShopStockMovement
)


class InventaireController:
    """Contrôleur pour la gestion des inventaires physiques"""
    
    def __init__(self, pos_id: int):
        self.pos_id = pos_id
        self.db_manager = DatabaseManager()
    
    def get_inventory_data_for_warehouse(self, session: Session, warehouse_id: int) -> Dict[str, Any]:
        """Récupérer les données d'inventaire pour un entrepôt"""
        
        # Vérifier que l'entrepôt existe et appartient au POS
        warehouse = session.query(ShopWarehouse).filter(
            and_(
                ShopWarehouse.id == warehouse_id,
                ShopWarehouse.pos_id == self.pos_id,
                ShopWarehouse.is_active == True
            )
        ).first()
        
        if not warehouse:
            raise ValueError(f"Entrepôt {warehouse_id} non trouvé ou non autorisé.")
        
        # Récupérer tous les produits avec leur stock théorique
        products_stock = session.query(
            ShopProduct.id,
            ShopProduct.name,
            ShopProduct.code,
            ShopProduct.cost_price,
            ShopProduct.sale_price,
            ShopWarehouseStock.quantity,
            ShopWarehouseStock.reserved_quantity,
            ShopWarehouseStock.unit_cost,
            ShopWarehouseStock.minimum_stock,
            ShopWarehouseStock.maximum_stock
        ).join(
            ShopWarehouseStock, ShopProduct.id == ShopWarehouseStock.product_id
        ).filter(
            and_(
                ShopProduct.pos_id == self.pos_id,
                ShopWarehouseStock.warehouse_id == warehouse_id
            )
        ).order_by(ShopProduct.name).all()
        
        inventory_items = []
        total_theoretical_value = 0
        
        for item in products_stock:
            theoretical_qty = float(item.quantity)
            unit_cost = float(item.unit_cost or item.cost_price or 0)
            theoretical_value = theoretical_qty * unit_cost
            total_theoretical_value += theoretical_value
            
            inventory_items.append({
                'product_id': item.id,
                'product_name': item.name,
                'product_code': item.code,
                'theoretical_quantity': theoretical_qty,
                'physical_quantity': theoretical_qty,  # Par défaut = théorique
                'unit_cost': unit_cost,
                'cost_price': float(item.cost_price or 0),
                'sale_price': float(item.sale_price or 0),
                'theoretical_value': theoretical_value,
                'gap': 0.0,  # Écart initial
                'gap_value': 0.0,  # Valeur de l'écart
                'reserved_quantity': float(item.reserved_quantity or 0),
                'minimum_stock': float(item.minimum_stock or 0),
                'maximum_stock': float(item.maximum_stock or 0),
                'status': 'NOT_CHECKED'  # Statut de vérification
            })
        
        return {
            'warehouse': {
                'id': warehouse.id,
                'name': warehouse.name,
                'code': warehouse.code,
                'type': warehouse.type
            },
            'inventory_items': inventory_items,
            'summary': {
                'total_products': len(inventory_items),
                'total_theoretical_value': total_theoretical_value,
                'products_to_check': len(inventory_items)
            }
        }
    
    def calculate_inventory_gaps(self, inventory_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculer les écarts d'inventaire"""
        
        total_gaps = 0
        total_gap_value = 0
        positive_gaps = 0
        negative_gaps = 0
        exact_counts = 0
        
        for item in inventory_items:
            theoretical = item['theoretical_quantity']
            physical = item['physical_quantity']
            unit_cost = item['unit_cost']
            
            gap = physical - theoretical
            gap_value = gap * unit_cost
            
            item['gap'] = gap
            item['gap_value'] = gap_value
            
            # Mise à jour des totaux
            total_gap_value += gap_value
            
            if gap > 0:
                positive_gaps += 1
            elif gap < 0:
                negative_gaps += 1
                total_gaps += 1
            else:
                exact_counts += 1
            
            # Déterminer le statut
            if gap == 0:
                item['status'] = 'EXACT'
            elif abs(gap) <= theoretical * 0.05:  # Écart de moins de 5%
                item['status'] = 'MINOR_GAP'
            elif gap > 0:
                item['status'] = 'SURPLUS'
            else:
                item['status'] = 'SHORTAGE'
        
        return {
            'total_products': len(inventory_items),
            'exact_counts': exact_counts,
            'positive_gaps': positive_gaps,
            'negative_gaps': negative_gaps,
            'accuracy_rate': (exact_counts / len(inventory_items) * 100) if inventory_items else 0,
            'total_gap_value': total_gap_value,
            'items_with_gaps': positive_gaps + negative_gaps,
            'gap_percentage': ((positive_gaps + negative_gaps) / len(inventory_items) * 100) if inventory_items else 0
        }
    
    def save_inventory_adjustments(self, session: Session, warehouse_id: int, 
                                  inventory_items: List[Dict[str, Any]], 
                                  inventory_notes: str = "", 
                                  user: str = "Système") -> Dict[str, Any]:
        """Sauvegarder les ajustements d'inventaire"""
        
        # Vérifier l'entrepôt
        warehouse = session.query(ShopWarehouse).filter(
            and_(
                ShopWarehouse.id == warehouse_id,
                ShopWarehouse.pos_id == self.pos_id
            )
        ).first()
        
        if not warehouse:
            raise ValueError(f"Entrepôt {warehouse_id} non trouvé.")
        
        adjustments_made = []
        total_adjustments = 0
        
        for item in inventory_items:
            if item['gap'] != 0:  # Seulement si il y a un écart
                product_id = item['product_id']
                gap = item['gap']
                unit_cost = item['unit_cost']
                
                # Mettre à jour le stock dans la base
                stock = session.query(ShopWarehouseStock).filter(
                    and_(
                        ShopWarehouseStock.warehouse_id == warehouse_id,
                        ShopWarehouseStock.product_id == product_id
                    )
                ).first()
                
                if stock:
                    old_quantity = float(stock.quantity)
                    new_quantity = item['physical_quantity']
                    
                    stock.quantity = Decimal(str(new_quantity))
                    stock.updated_at = datetime.now()
                    
                    # Créer un mouvement de stock pour l'ajustement
                    movement_type = 'INVENTORY_ADJUSTMENT_IN' if gap > 0 else 'INVENTORY_ADJUSTMENT_OUT'
                    movement_reference = f"Inventaire du {datetime.now().strftime('%d/%m/%Y')}"
                    if inventory_notes:
                        movement_reference += f" - {inventory_notes}"
                    
                    movement = ShopStockMovement(
                        warehouse_id=warehouse_id,
                        product_id=product_id,
                        movement_type=movement_type,
                        quantity=Decimal(str(abs(gap))),
                        unit_cost=Decimal(str(unit_cost)),
                        reference=movement_reference,
                        movement_date=datetime.now()
                        # created_at=datetime.now()  # Colonne pas encore créée en DB
                    )
                    session.add(movement)
                    
                    adjustments_made.append({
                        'product_id': product_id,
                        'product_name': item['product_name'],
                        'old_quantity': old_quantity,
                        'new_quantity': new_quantity,
                        'gap': gap,
                        'gap_value': item['gap_value'],
                        'movement_type': movement_type
                    })
                    
                    total_adjustments += 1
        
        # Calculer les statistiques finales
        statistics = self.calculate_inventory_gaps(inventory_items)
        
        return {
            'warehouse_id': warehouse_id,
            'warehouse_name': warehouse.name,
            'inventory_date': datetime.now(),
            'total_products_checked': len(inventory_items),
            'adjustments_made': total_adjustments,
            'adjustments_details': adjustments_made,
            'statistics': statistics,
            'notes': inventory_notes,
            'performed_by': user
        }
    
    def get_inventory_history(self, session: Session, warehouse_id: Optional[int] = None,
                             start_date: Optional[date] = None, 
                             end_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """Récupérer l'historique des inventaires (basé sur les mouvements d'ajustement)"""
        
        base_query = session.query(ShopStockMovement).join(
            ShopWarehouse, ShopStockMovement.warehouse_id == ShopWarehouse.id
        ).join(
            ShopProduct, ShopStockMovement.product_id == ShopProduct.id
        ).filter(
            and_(
                ShopWarehouse.pos_id == self.pos_id,
                ShopStockMovement.movement_type.in_(['INVENTORY_ADJUSTMENT_IN', 'INVENTORY_ADJUSTMENT_OUT'])
            )
        )
        
        if warehouse_id:
            base_query = base_query.filter(ShopWarehouse.id == warehouse_id)
        
        if start_date:
            base_query = base_query.filter(ShopStockMovement.movement_date >= start_date)
        
        if end_date:
            base_query = base_query.filter(ShopStockMovement.movement_date <= end_date)
        
        movements = base_query.order_by(ShopStockMovement.movement_date.desc()).all()
        
        # Grouper par date d'inventaire
        inventories_by_date = {}
        
        for movement in movements:
            inventory_date = movement.movement_date.date()
            warehouse_name = movement.warehouse.name
            key = f"{inventory_date}_{warehouse_name}"
            
            if key not in inventories_by_date:
                inventories_by_date[key] = {
                    'date': inventory_date,
                    'warehouse_id': movement.warehouse_id,
                    'warehouse_name': warehouse_name,
                    'adjustments': [],
                    'total_products': 0,
                    'total_positive_adjustments': 0,
                    'total_negative_adjustments': 0,
                    'total_value_impact': 0
                }
            
            inventory = inventories_by_date[key]
            quantity = float(movement.quantity)
            value_impact = quantity * float(movement.unit_cost)
            
            inventory['adjustments'].append({
                'product_name': movement.product.name,
                'product_code': movement.product.code,
                'adjustment_type': movement.movement_type,
                'quantity': quantity,
                'unit_cost': float(movement.unit_cost),
                'value_impact': value_impact
            })
            
            inventory['total_products'] += 1
            
            if movement.movement_type == 'INVENTORY_ADJUSTMENT_IN':
                inventory['total_positive_adjustments'] += quantity
                inventory['total_value_impact'] += value_impact
            else:
                inventory['total_negative_adjustments'] += quantity
                inventory['total_value_impact'] -= value_impact
        
        # Convertir en liste et trier
        inventory_history = list(inventories_by_date.values())
        inventory_history.sort(key=lambda x: x['date'], reverse=True)
        
        return inventory_history
    
    def generate_inventory_preparation_sheet(self, session: Session, warehouse_id: int) -> Dict[str, Any]:
        """Générer une feuille de préparation d'inventaire"""
        
        inventory_data = self.get_inventory_data_for_warehouse(session, warehouse_id)
        
        # Organiser les produits par catégorie ou alphabétiquement
        items_by_category = {}
        
        for item in inventory_data['inventory_items']:
            # Pour l'instant, on groupe par première lettre du nom
            # Dans une vraie application, on utiliserait les catégories de produits
            first_letter = item['product_name'][0].upper() if item['product_name'] else 'Z'
            
            if first_letter not in items_by_category:
                items_by_category[first_letter] = []
            
            items_by_category[first_letter].append({
                'product_code': item['product_code'],
                'product_name': item['product_name'],
                'theoretical_quantity': item['theoretical_quantity'],
                'unit_cost': item['unit_cost'],
                'location': f"Zone {first_letter}",  # Simulation d'emplacement
                'physical_quantity_counted': None,  # À remplir pendant l'inventaire
                'notes': ""
            })
        
        # Trier les catégories
        sorted_categories = sorted(items_by_category.items())
        
        return {
            'warehouse': inventory_data['warehouse'],
            'preparation_date': datetime.now(),
            'items_by_category': sorted_categories,
            'total_products': inventory_data['summary']['total_products'],
            'inventory_instructions': [
                "1. Vérifiez chaque produit physiquement",
                "2. Comptez les quantités exactes",
                "3. Notez toute anomalie ou produit endommagé",
                "4. Signez chaque section une fois terminée",
                "5. Reportez les quantités dans le système"
            ],
            'estimated_duration': self._estimate_inventory_duration(inventory_data['summary']['total_products'])
        }
    
    def _estimate_inventory_duration(self, total_products: int) -> str:
        """Estimer la durée d'inventaire basée sur le nombre de produits"""
        # Estimation approximative: 2 minutes par produit pour une personne
        minutes_per_product = 2
        total_minutes = total_products * minutes_per_product
        
        hours = total_minutes // 60
        minutes = total_minutes % 60
        
        if hours > 0:
            return f"Environ {hours}h{minutes:02d} pour une personne"
        else:
            return f"Environ {minutes} minutes pour une personne"
    
    def validate_inventory_data(self, inventory_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Valider les données d'inventaire avant sauvegarde"""
        
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        items_checked = 0
        large_discrepancies = 0
        negative_quantities = 0
        
        for item in inventory_items:
            theoretical = item['theoretical_quantity']
            physical = item['physical_quantity']
            
            # Vérifications
            if physical < 0:
                validation_results['errors'].append(
                    f"Quantité physique négative pour {item['product_name']}: {physical}"
                )
                negative_quantities += 1
                validation_results['is_valid'] = False
            
            # Vérifier les gros écarts (plus de 50% de différence)
            if theoretical > 0:
                discrepancy_percentage = abs(physical - theoretical) / theoretical * 100
                if discrepancy_percentage > 50:
                    validation_results['warnings'].append(
                        f"Gros écart pour {item['product_name']}: {discrepancy_percentage:.1f}% d'écart"
                    )
                    large_discrepancies += 1
            
            # Vérifier si la quantité physique a été modifiée (inventaire effectué)
            if physical != theoretical:
                items_checked += 1
        
        # Statistiques de validation
        validation_results['statistics'] = {
            'total_items': len(inventory_items),
            'items_checked': items_checked,
            'items_unchanged': len(inventory_items) - items_checked,
            'large_discrepancies': large_discrepancies,
            'negative_quantities': negative_quantities,
            'completion_rate': (items_checked / len(inventory_items) * 100) if inventory_items else 0
        }
        
        # Avertissements supplémentaires
        if items_checked == 0:
            validation_results['warnings'].append("Aucun produit n'a été vérifié physiquement")
        
        if validation_results['statistics']['completion_rate'] < 50:
            validation_results['warnings'].append(
                f"Inventaire incomplet: seulement {validation_results['statistics']['completion_rate']:.1f}% des produits vérifiés"
            )
        
        return validation_results
    
    def export_inventory_report(self, session: Session, warehouse_id: int, 
                               inventory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Exporter un rapport d'inventaire"""
        
        warehouse = session.query(ShopWarehouse).get(warehouse_id)
        
        export_data = {
            'report_info': {
                'title': f'Rapport d\'Inventaire - {warehouse.name}',
                'warehouse_id': warehouse_id,
                'warehouse_name': warehouse.name,
                'generated_at': datetime.now(),
                'generated_by': 'Système'
            },
            'summary': inventory_data.get('statistics', {}),
            'items': []
        }
        
        # Préparer les données des articles pour export
        for item in inventory_data.get('inventory_items', []):
            export_data['items'].append({
                'Code Produit': item['product_code'],
                'Nom Produit': item['product_name'],
                'Quantité Théorique': item['theoretical_quantity'],
                'Quantité Physique': item['physical_quantity'],
                'Écart': item['gap'],
                'Coût Unitaire': item['unit_cost'],
                'Valeur Écart': item['gap_value'],
                'Statut': item['status']
            })
        
        return export_data
    
    def get_all_inventories(self, session: Session, limit: int = 20) -> List[Dict[str, Any]]:
        """Récupérer tous les inventaires (méthode attendue par les widgets)"""
        try:
            from ayanna_erp.modules.boutique.model.models import ShopInventory, ShopWarehouse
            
            # Récupérer les inventaires avec leurs entrepôts
            query = session.query(ShopInventory).join(
                ShopWarehouse, ShopInventory.warehouse_id == ShopWarehouse.id
            ).filter(
                ShopWarehouse.pos_id == self.pos_id
            ).order_by(ShopInventory.inventory_date.desc())
            
            if limit:
                query = query.limit(limit)
            
            inventories = query.all()
            
            result = []
            for inventory in inventories:
                warehouse = inventory.warehouse
                
                result.append({
                    'id': inventory.id,
                    'inventory_number': inventory.inventory_number,
                    'warehouse_id': inventory.warehouse_id,
                    'warehouse_name': warehouse.name,
                    'inventory_date': inventory.inventory_date,
                    'status': inventory.status,
                    'inventory_type': inventory.inventory_type,
                    'reason': inventory.reason,
                    'started_by': inventory.started_by,
                    'started_date': inventory.started_date,
                    'completed_by': inventory.completed_by,
                    'completed_date': inventory.completed_date,
                    'validated_by': inventory.validated_by,
                    'validated_date': inventory.validated_date,
                    'total_items_counted': inventory.total_items_counted,
                    'total_discrepancies': inventory.total_discrepancies,
                    'total_variance_cost': float(inventory.total_variance_cost or 0),
                    'notes': inventory.notes,
                    # Statut formaté pour affichage
                    'status_display': {
                        'planned': 'Planifié',
                        'in_progress': 'En cours',
                        'completed': 'Terminé',
                        'cancelled': 'Annulé'
                    }.get(inventory.status, inventory.status),
                    # Type formaté pour affichage
                    'type_display': {
                        'full': 'Inventaire complet',
                        'partial': 'Inventaire partiel',
                        'cycle': 'Inventaire cyclique'
                    }.get(inventory.inventory_type, inventory.inventory_type)
                })
            
            return result
            
        except Exception as e:
            print(f"Erreur lors de la récupération des inventaires: {e}")
            return []