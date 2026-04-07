# -*- coding: utf-8 -*-
"""
Helper pour la gestion des stocks dans le module Boutique
Utilise les nouveaux modèles CoreProduct (centralisés par entreprise)
"""

from sqlalchemy import and_
from ayanna_erp.modules.stock.models import StockProduitEntrepot, StockWarehouse
from ayanna_erp.modules.core.models import CoreProduct, POSProductAccess
from ayanna_erp.modules.stock.helpers import POSWarehouseHelper
from ayanna_erp.database.database_manager import DatabaseManager


class BoutiqueStockHelper:
    """Helper pour gérer les stocks du module Boutique via le système centralisé CoreProduct"""
    
    @staticmethod
    def get_product_stock_for_pos(pos_id, product_id=None):
        """
        Récupère les quantités en stock pour les produits d'un POS Boutique
        Utilise CoreProduct (centralisé) + POSProductAccess (liaison POS-Produit)
        
        Args:
            pos_id (int): ID du point de vente Boutique
            product_id (int, optional): ID du produit spécifique, sinon tous les produits
            
        Returns:
            dict|list: Stock info pour un produit ou liste des stocks
        """
        try:
            db_manager = DatabaseManager()
            
            with db_manager.get_session() as session:
                # 1. Identifier l'entrepôt associé au POS
                warehouse = POSWarehouseHelper.get_main_warehouse_for_pos(pos_id)
                if not warehouse:
                    # Fallback: essayer l'entrepôt POS
                    warehouse = POSWarehouseHelper.get_pos_warehouse(pos_id)
                    
                if not warehouse:
                    return {
                        'error': f'Aucun entrepôt trouvé pour le POS {pos_id}',
                        'stocks': []
                    }
                
                # 2. Construire la requête de base avec CoreProduct + POSProductAccess
                query = session.query(
                    CoreProduct.id.label('product_id'),
                    CoreProduct.name.label('product_name'),
                    CoreProduct.price_unit.label('price_unit'),
                    CoreProduct.cost.label('cost'),
                    CoreProduct.code.label('product_code'),
                    CoreProduct.unit.label('product_unit'),
                    StockProduitEntrepot.quantity.label('stock_quantity'),
                    StockProduitEntrepot.min_stock_level.label('stock_min'),
                    StockProduitEntrepot.reserved_quantity.label('reserved_quantity'),
                    POSProductAccess.custom_price.label('pos_custom_price'),
                    POSProductAccess.is_available.label('pos_available')
                ).join(
                    POSProductAccess,
                    and_(
                        POSProductAccess.product_id == CoreProduct.id,
                        POSProductAccess.pos_id == pos_id,
                        POSProductAccess.is_available == True
                    )
                ).outerjoin(
                    StockProduitEntrepot,
                    and_(
                        StockProduitEntrepot.product_id == CoreProduct.id,
                        StockProduitEntrepot.warehouse_id == warehouse.id
                    )
                ).filter(
                    CoreProduct.is_active == True
                )
                
                # 3. Filtrer par produit spécifique si demandé
                if product_id:
                    query = query.filter(CoreProduct.id == product_id)
                    result = query.first()
                    
                    if result:
                        # Prix effectif (custom_price du POS ou prix du produit)
                        effective_price = float(result.pos_custom_price) if result.pos_custom_price else float(result.price_unit or 0)
                        
                        return {
                            'error': None,
                            'warehouse_info': {
                                'id': warehouse.id,
                                'name': warehouse.name,
                                'code': warehouse.code
                            },
                            'product': {
                                'id': result.product_id,
                                'name': result.product_name,
                                'code': result.product_code,
                                'unit': result.product_unit,
                                'price_unit': effective_price,
                                'cost': float(result.cost) if result.cost else 0.0,
                                'stock_quantity': float(result.stock_quantity) if result.stock_quantity else 0.0,
                                'stock_min': float(result.stock_min) if result.stock_min else 0.0,
                                'reserved_quantity': float(result.reserved_quantity) if result.reserved_quantity else 0.0,
                                'pos_available': result.pos_available,
                                'stock_status': BoutiqueStockHelper._get_stock_status(
                                    result.stock_quantity or 0,
                                    result.stock_min or 0
                                )
                            }
                        }
                    else:
                        return {
                            'error': f'Produit {product_id} non trouvé ou non disponible sur POS {pos_id}',
                            'product': None
                        }
                else:
                    # Tous les produits
                    results = query.all()
                    
                    products = []
                    for result in results:
                        stock_qty = float(result.stock_quantity) if result.stock_quantity else 0.0
                        stock_min = float(result.stock_min) if result.stock_min else 0.0
                        
                        # Prix effectif (custom_price du POS ou prix du produit)
                        effective_price = float(result.pos_custom_price) if result.pos_custom_price else float(result.price_unit or 0)
                        
                        products.append({
                            'id': result.product_id,
                            'name': result.product_name,
                            'code': result.product_code,
                            'unit': result.product_unit,
                            'price_unit': effective_price,
                            'cost': float(result.cost) if result.cost else 0.0,
                            'stock_quantity': stock_qty,
                            'stock_min': stock_min,
                            'reserved_quantity': float(result.reserved_quantity) if result.reserved_quantity else 0.0,
                            'pos_available': result.pos_available,
                            'stock_status': BoutiqueStockHelper._get_stock_status(stock_qty, stock_min)
                        })
                    
                    return {
                        'error': None,
                        'warehouse_info': {
                            'id': warehouse.id,
                            'name': warehouse.name,
                            'code': warehouse.code
                        },
                        'products': products,
                        'total_products': len(products),
                        'low_stock_count': len([p for p in products if p['stock_status'] == 'low']),
                        'out_of_stock_count': len([p for p in products if p['stock_status'] == 'out'])
                    }
                    
        except Exception as e:
            return {
                'error': f'Erreur lors de la récupération des stocks: {e}',
                'products': [] if not product_id else None
            }
    
    @staticmethod
    def _get_stock_status(stock_quantity, stock_min):
        """Détermine le statut du stock"""
        if stock_quantity <= 0:
            return 'out'  # Rupture de stock
        elif stock_quantity <= stock_min:
            return 'low'  # Stock faible
        else:
            return 'ok'   # Stock normal
    
    @staticmethod
    def get_available_products_for_pos(pos_id, include_zero_stock=False):
        """
        Récupère tous les produits disponibles pour un POS
        
        Args:
            pos_id (int): ID du point de vente
            include_zero_stock (bool): Inclure les produits avec stock à zéro
            
        Returns:
            list: Liste des produits disponibles
        """
        try:
            result = BoutiqueStockHelper.get_product_stock_for_pos(pos_id)
            
            if result.get('error'):
                return []
                
            products = result.get('products', [])
            
            if not include_zero_stock:
                products = [p for p in products if p['stock_quantity'] > 0]
                
            return products
            
        except Exception as e:
            print(f"Erreur lors de la récupération des produits disponibles: {e}")
            return []