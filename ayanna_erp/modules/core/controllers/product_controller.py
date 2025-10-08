from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.core.models import CoreProduct, CoreProductCategory
from ayanna_erp.core.entreprise_controller import EntrepriseController
from sqlalchemy.orm import Session
from typing import List, Optional

class CoreProductController:
    """
    Contrôleur centralisé pour la gestion des produits CoreProduct
    Utilisé par tous les modules (Boutique, Salle de Fête, Restaurant, etc.)
    """
    def __init__(self, pos_id: int):
        self.db_manager = DatabaseManager()
        self.pos_id = pos_id
        self.entreprise_ctrl = EntrepriseController()
        
        # Récupérer l'entreprise_id depuis le pos_id
        session = self.db_manager.get_session()
        try:
            from ayanna_erp.database.database_manager import POSPoint
            pos = session.query(POSPoint).filter_by(id=pos_id).first()
            self.entreprise_id = pos.enterprise_id if pos else 1
            
            # Mapping des codes POS basé sur l'ID - selon les entrepôts existants
            pos_code_mapping = {
                1: 'POS_2',  # Boutique → POS_2
                2: 'POS_2',  # Boutique → POS_2  
                3: 'POS_3',  # Pharmacie → POS_3
                4: 'POS_4'   # Restaurant → POS_4
            }
            self.pos_code = pos_code_mapping.get(pos_id, 'POS_2')  # Par défaut boutique
        finally:
            session.close()

    def get_products(self, session: Session, category_id: Optional[int] = None, search_term: Optional[str] = None, active_only: Optional[bool] = None) -> List[CoreProduct]:
        """
        Récupérer tous les produits du POS, filtrés par catégorie, recherche et statut
        """
        query = session.query(CoreProduct).filter(CoreProduct.entreprise_id == self.entreprise_id)
        if category_id:
            query = query.filter(CoreProduct.category_id == category_id)
        if search_term:
            like_term = f"%{search_term}%"
            query = query.filter((CoreProduct.name.ilike(like_term)) | (CoreProduct.description.ilike(like_term)))
        if active_only is not None:
            query = query.filter(CoreProduct.is_active == active_only)
        return query.order_by(CoreProduct.name.asc()).all()

    def get_product_by_id(self, session: Session, product_id: int) -> Optional[CoreProduct]:
        return session.query(CoreProduct).filter(CoreProduct.id == product_id, CoreProduct.entreprise_id == self.entreprise_id).first()

    def create_product(self, session: Session, nom: str, prix, category_id: int, description: Optional[str] = None, unit: str = "pièce", stock_initial: float = 0.0, cost: float = 0.0, barcode: Optional[str] = None, image: Optional[str] = None, stock_min: float = 0.0, account_id: Optional[int] = None, is_active: bool = True) -> CoreProduct:
        """
        Créer un produit et initialiser son stock sur l'entrepôt correspondant au POS
        Le stock initial est toujours 0 - l'approvisionnement vient des achats
        """
        product = CoreProduct(
            entreprise_id=self.entreprise_id,
            name=nom,
            price_unit=prix,
            category_id=category_id,
            description=description,
            unit=unit,
            cost=cost,
            barcode=barcode,
            image=image,
            account_id=account_id,
            is_active=is_active
        )
        session.add(product)
        session.commit()
        
        # Initialiser le stock à 0 avec le seuil minimum
        self._initialize_product_stock(session, product, 0.0, stock_min)
        
        return product

    def _initialize_product_stock(self, session: Session, product: CoreProduct, initial_quantity: float = 0.0, min_stock: float = 0.0):
        """
        Initialise le stock d'un produit sur l'entrepôt correspondant au POS
        Stock initial toujours à 0 - l'approvisionnement vient des achats
        """
        try:
            from ayanna_erp.modules.stock.models import StockWarehouse, StockProduitEntrepot
            from datetime import datetime
            from decimal import Decimal
            
            # Récupérer l'entrepôt correspondant au POS par son code
            pos_warehouse = session.query(StockWarehouse).filter_by(code=self.pos_code).first()
            
            if not pos_warehouse:
                raise Exception(f"Entrepôt {self.pos_code} introuvable pour le POS {self.pos_id}")
            
            # Créer l'entrée stock produit-entrepôt avec stock initial à 0
            stock_quantity = Decimal('0.0')  # Toujours 0 au départ
            unit_cost = Decimal(str(product.cost)) if product.cost else Decimal('0.0')
            
            stock_entry = StockProduitEntrepot(
                product_id=product.id,
                warehouse_id=pos_warehouse.id,
                quantity=stock_quantity,
                reserved_quantity=Decimal('0.0'),
                unit_cost=unit_cost,
                total_cost=Decimal('0.0'),  # Pas de coût initial
                min_stock_level=Decimal(str(min_stock)),
                last_movement_date=datetime.now()
            )
            session.add(stock_entry)
            
            # Pas de mouvement de stock initial car toujours 0
            # L'approvisionnement viendra des achats
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            raise Exception(f"Erreur lors de l'initialisation du stock: {e}")

    def update_product(self, session: Session, product_id: int, **kwargs) -> Optional[CoreProduct]:
        product = self.get_product_by_id(session, product_id)
        if not product:
            return None
        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, key, value)
        session.commit()
        return product

    def delete_product(self, session: Session, product_id: int) -> bool:
        product = self.get_product_by_id(session, product_id)
        if not product:
            return False
        session.delete(product)
        session.commit()
        return True

    def get_categories(self, session: Session) -> List[CoreProductCategory]:
        return session.query(CoreProductCategory).filter(CoreProductCategory.entreprise_id == self.entreprise_id, CoreProductCategory.is_active == True).order_by(CoreProductCategory.name.asc()).all()

    def get_product_stock_info(self, product_id: int):
        """Récupérer les informations de stock d'un produit depuis l'entrepôt du POS"""
        try:
            from ayanna_erp.modules.stock.models import StockProduitEntrepot, StockWarehouse
            session = self.db_manager.get_session()
            
            # Récupérer l'entrepôt correspondant au POS
            pos_warehouse = session.query(StockWarehouse).filter_by(code=self.pos_code).first()
            
            if not pos_warehouse:
                session.close()
                return {
                    'total_stock': 0,
                    'min_stock': 0,
                    'warehouse_name': f'Entrepôt {self.pos_code} introuvable'
                }
            
            # Récupérer le stock pour ce produit dans l'entrepôt du POS
            stock_entry = session.query(StockProduitEntrepot).filter_by(
                product_id=product_id, 
                warehouse_id=pos_warehouse.id
            ).first()
            
            if stock_entry:
                total_stock = float(stock_entry.quantity)
                min_stock = float(stock_entry.min_stock_level)
            else:
                total_stock = 0
                min_stock = 0
            
            session.close()
            
            return {
                'total_stock': total_stock,
                'min_stock': min_stock,
                'warehouse_name': pos_warehouse.name
            }
        except Exception as e:
            print(f"Erreur lors de la récupération du stock: {e}")
            return {
                'total_stock': 0,
                'min_stock': 0,
                'warehouse_name': 'Erreur'
            }