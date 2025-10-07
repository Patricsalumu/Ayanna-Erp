"""
Helper pour l'intégration des stocks entre le module Boutique et le module Stock
Permet au module Boutique d'utiliser les nouveaux modèles stock
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from ayanna_erp.modules.stock.models import StockWarehouse, StockProduitEntrepot, StockMovement


class BoutiqueStockHelper:
    """Helper pour gérer les stocks boutique avec la nouvelle architecture"""
    
    def __init__(self, pos_id: int = None, entreprise_id: int = None):
        self.pos_id = pos_id
        self.entreprise_id = entreprise_id
        self._boutique_warehouse_id = None
    
    def get_boutique_warehouse_id(self, session: Session) -> Optional[int]:
        """Récupère l'ID de l'entrepôt Point de Vente de la boutique"""
        if self._boutique_warehouse_id:
            return self._boutique_warehouse_id
            
        # Chercher l'entrepôt Point de Vente de la boutique
        warehouse = session.query(StockWarehouse).filter(
            StockWarehouse.entreprise_id == self.entreprise_id,
            StockWarehouse.name.like('%Boutique%'),
            StockWarehouse.type == 'Point de Vente',
            StockWarehouse.is_active == True
        ).first()
        
        if warehouse:
            self._boutique_warehouse_id = warehouse.id
            return warehouse.id
        
        return None
    
    def get_product_stock_total(self, session: Session, product_id: int) -> Decimal:
        """Calcule le stock total disponible pour un produit dans l'entrepôt boutique"""
        warehouse_id = self.get_boutique_warehouse_id(session)
        if not warehouse_id:
            return Decimal('0')
        
        stock = session.query(StockProduitEntrepot).filter(
            StockProduitEntrepot.product_id == product_id,
            StockProduitEntrepot.warehouse_id == warehouse_id
        ).first()
        
        if stock:
            available = stock.quantity - (stock.reserved_quantity or Decimal('0'))
            return max(available, Decimal('0'))
        
        return Decimal('0')
    
    def add_stock_entry(self, session: Session, product_id: int, quantite: Decimal, 
                       prix_unitaire: Decimal, description: str = "Entrée stock boutique") -> bool:
        """Ajoute du stock pour un produit dans l'entrepôt boutique"""
        warehouse_id = self.get_boutique_warehouse_id(session)
        if not warehouse_id:
            return False
        
        try:
            # Récupérer ou créer l'entrée stock produit-entrepôt
            stock = session.query(StockProduitEntrepot).filter(
                StockProduitEntrepot.product_id == product_id,
                StockProduitEntrepot.warehouse_id == warehouse_id
            ).first()
            
            if not stock:
                # Créer nouvelle entrée
                stock = StockProduitEntrepot(
                    product_id=product_id,
                    warehouse_id=warehouse_id,
                    quantity=quantite,
                    unit_cost=prix_unitaire,
                    total_cost=quantite * prix_unitaire,
                    last_movement_date=datetime.now()
                )
                session.add(stock)
            else:
                # Mettre à jour stock existant (moyenne pondérée pour le coût)
                old_total_cost = stock.quantity * stock.unit_cost
                new_total_cost = quantite * prix_unitaire
                total_quantity = stock.quantity + quantite
                
                if total_quantity > 0:
                    stock.unit_cost = (old_total_cost + new_total_cost) / total_quantity
                
                stock.quantity = total_quantity
                stock.total_cost = total_quantity * stock.unit_cost
                stock.last_movement_date = datetime.now()
            
            # Créer mouvement de stock
            movement = StockMovement(
                product_id=product_id,
                warehouse_id=warehouse_id,
                product_warehouse_id=stock.id,
                movement_type='ENTREE',
                quantity=quantite,
                unit_cost=prix_unitaire,
                total_cost=quantite * prix_unitaire,
                description=description,
                user_name="Système Boutique",
                movement_date=datetime.now()
            )
            session.add(movement)
            
            session.flush()
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'ajout de stock: {e}")
            return False
    
    def decrement_stock(self, session: Session, product_id: int, quantite: Decimal, 
                       description: str = "Vente boutique") -> bool:
        """Décrémente le stock d'un produit (FIFO)"""
        warehouse_id = self.get_boutique_warehouse_id(session)
        if not warehouse_id:
            return False
        
        try:
            stock = session.query(StockProduitEntrepot).filter(
                StockProduitEntrepot.product_id == product_id,
                StockProduitEntrepot.warehouse_id == warehouse_id
            ).first()
            
            if not stock or stock.quantity < quantite:
                return False  # Stock insuffisant
            
            # Mettre à jour le stock
            stock.quantity -= quantite
            stock.total_cost = stock.quantity * stock.unit_cost
            stock.last_movement_date = datetime.now()
            
            # Créer mouvement de stock
            movement = StockMovement(
                product_id=product_id,
                warehouse_id=warehouse_id,
                product_warehouse_id=stock.id,
                movement_type='SORTIE',
                quantity=-quantite,  # Négatif pour sortie
                unit_cost=stock.unit_cost,
                total_cost=-(quantite * stock.unit_cost),
                description=description,
                user_name="Système Boutique",
                movement_date=datetime.now()
            )
            session.add(movement)
            
            session.flush()
            return True
            
        except Exception as e:
            print(f"Erreur lors de la décrémentation de stock: {e}")
            return False
    
    def create_product_stock_in_all_warehouses(self, session: Session, product_id: int, 
                                              initial_stock: Decimal = Decimal('0')) -> bool:
        """Crée des entrées stock pour un produit dans TOUS les entrepôts de l'entreprise"""
        try:
            # Récupérer tous les entrepôts actifs de l'entreprise
            warehouses = session.query(StockWarehouse).filter(
                StockWarehouse.entreprise_id == self.entreprise_id,
                StockWarehouse.is_active == True
            ).all()
            
            for warehouse in warehouses:
                # Vérifier si l'entrée existe déjà
                existing_stock = session.query(StockProduitEntrepot).filter(
                    StockProduitEntrepot.product_id == product_id,
                    StockProduitEntrepot.warehouse_id == warehouse.id
                ).first()
                
                if not existing_stock:
                    # Créer entrée avec quantité 0 (ou initial_stock si spécifié)
                    stock_entry = StockProduitEntrepot(
                        product_id=product_id,
                        warehouse_id=warehouse.id,
                        quantity=initial_stock,
                        reserved_quantity=Decimal('0'),
                        unit_cost=Decimal('0'),
                        total_cost=Decimal('0'),
                        min_stock_level=Decimal('0'),
                        last_movement_date=datetime.now() if initial_stock > 0 else None
                    )
                    session.add(stock_entry)
                    
                    # Si stock initial > 0, créer un mouvement d'entrée
                    if initial_stock > 0 and warehouse.id == self.get_boutique_warehouse_id(session):
                        movement = StockMovement(
                            product_id=product_id,
                            warehouse_id=warehouse.id,
                            product_warehouse_id=stock_entry.id,
                            movement_type='ENTREE',
                            quantity=initial_stock,
                            unit_cost=Decimal('0'),
                            total_cost=Decimal('0'),
                            description=f"Stock initial produit ID {product_id}",
                            user_name="Système Boutique",
                            movement_date=datetime.now()
                        )
                        session.add(movement)
            
            session.flush()
            return True
            
        except Exception as e:
            print(f"Erreur lors de la création des stocks dans tous les entrepôts: {e}")
            return False
    
    def get_products_with_stock(self, session: Session) -> List[Dict[str, Any]]:
        """Récupère tous les produits avec leur stock dans l'entrepôt boutique"""
        warehouse_id = self.get_boutique_warehouse_id(session)
        if not warehouse_id:
            return []
        
        # Jointure entre StockProduitEntrepot et ShopProduct pour avoir les infos produit
        from ayanna_erp.modules.boutique.model.models import ShopProduct
        
        query = session.query(StockProduitEntrepot, ShopProduct).join(
            ShopProduct, StockProduitEntrepot.product_id == ShopProduct.id
        ).filter(
            StockProduitEntrepot.warehouse_id == warehouse_id,
            ShopProduct.is_active == True
        ).all()
        
        result = []
        for stock, product in query:
            available = stock.quantity - (stock.reserved_quantity or Decimal('0'))
            result.append({
                'product_id': stock.product_id,
                'product_name': product.name,
                'product_price': float(product.price_unit) if product.price_unit else 0.0,
                'quantite': float(available),
                'quantite_reservee': float(stock.reserved_quantity or Decimal('0')),
                'prix_unitaire': float(stock.unit_cost),
                'total_cost': float(stock.total_cost),
                'last_movement_date': stock.last_movement_date,
                'min_stock_level': float(stock.min_stock_level),
                'warehouse_id': warehouse_id
            })
        
        return result
    
    def get_all_products_for_display(self, session: Session) -> List[Dict[str, Any]]:
        """Récupère TOUS les produits avec leur stock dans l'entrepôt boutique (même ceux à 0)"""
        warehouse_id = self.get_boutique_warehouse_id(session)
        if not warehouse_id:
            return []
        
        from ayanna_erp.modules.boutique.model.models import ShopProduct
        
        # Récupérer tous les produits actifs
        products = session.query(ShopProduct).filter(ShopProduct.is_active == True).all()
        
        result = []
        for product in products:
            # Récupérer le stock pour ce produit dans l'entrepôt boutique
            stock = session.query(StockProduitEntrepot).filter(
                StockProduitEntrepot.product_id == product.id,
                StockProduitEntrepot.warehouse_id == warehouse_id
            ).first()
            
            if stock:
                available = stock.quantity - (stock.reserved_quantity or Decimal('0'))
                result.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'product_price': float(product.price_unit) if product.price_unit else 0.0,
                    'quantite': float(available),
                    'quantite_reservee': float(stock.reserved_quantity or Decimal('0')),
                    'prix_unitaire': float(stock.unit_cost),
                    'total_cost': float(stock.total_cost),
                    'last_movement_date': stock.last_movement_date,
                    'min_stock_level': float(stock.min_stock_level),
                    'warehouse_id': warehouse_id,
                    'category_id': product.category_id,
                    'description': product.description,
                    'unit': product.unit
                })
            else:
                # Si pas de stock trouvé, afficher avec quantité 0
                result.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'product_price': float(product.price_unit) if product.price_unit else 0.0,
                    'quantite': 0.0,
                    'quantite_reservee': 0.0,
                    'prix_unitaire': float(product.price_unit) if product.price_unit else 0.0,
                    'total_cost': 0.0,
                    'last_movement_date': None,
                    'min_stock_level': 0.0,
                    'warehouse_id': warehouse_id,
                    'category_id': product.category_id,
                    'description': product.description,
                    'unit': product.unit
                })
        
        return result