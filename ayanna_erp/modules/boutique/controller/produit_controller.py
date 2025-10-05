from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.boutique.model.models import ShopProduct, ShopCategory
from ayanna_erp.core.entreprise_controller import EntrepriseController
from sqlalchemy.orm import Session
from typing import List, Optional

class ProduitController:
	"""
	Contrôleur pour la gestion des produits de la boutique
	"""
	def __init__(self, pos_id: int):
		self.db_manager = DatabaseManager()
		self.pos_id = pos_id
		self.entreprise_ctrl = EntrepriseController()

	def get_products(self, session: Session, category_id: Optional[int] = None, search_term: Optional[str] = None, active_only: Optional[bool] = None) -> List[ShopProduct]:
		"""
		Récupérer tous les produits du POS, filtrés par catégorie, recherche et statut
		"""
		query = session.query(ShopProduct).filter(ShopProduct.pos_id == self.pos_id)
		if category_id:
			query = query.filter(ShopProduct.category_id == category_id)
		if search_term:
			like_term = f"%{search_term}%"
			query = query.filter((ShopProduct.name.ilike(like_term)) | (ShopProduct.description.ilike(like_term)))
		if active_only is not None:
			query = query.filter(ShopProduct.is_active == active_only)
		return query.order_by(ShopProduct.name.asc()).all()

	def get_product_by_id(self, session: Session, product_id: int) -> Optional[ShopProduct]:
		return session.query(ShopProduct).filter(ShopProduct.id == product_id, ShopProduct.pos_id == self.pos_id).first()

	def create_product(self, session: Session, nom: str, prix, category_id: int, description: Optional[str] = None, unit: str = "pièce", stock_initial: float = 0.0, cost: float = 0.0, barcode: Optional[str] = None, image: Optional[str] = None, stock_min: float = 0.0, account_id: Optional[int] = None, is_active: bool = True) -> ShopProduct:
		product = ShopProduct(
			pos_id=self.pos_id,
			name=nom,
			price_unit=prix,
			category_id=category_id,
			description=description,
			unit=unit,
			stock_quantity=stock_initial,
			cost=cost,
			barcode=barcode,
			image=image,
			stock_min=stock_min,
			account_id=account_id,
			is_active=is_active
		)
		session.add(product)
		session.commit()
		return product

	def update_product(self, session: Session, product_id: int, **kwargs) -> Optional[ShopProduct]:
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

	def get_categories(self, session: Session) -> List[ShopCategory]:
		return session.query(ShopCategory).filter(ShopCategory.pos_id == self.pos_id, ShopCategory.is_active == True).order_by(ShopCategory.order_display.asc()).all()

	def get_product_stock_total(self, session: Session, product_id: int) -> float:
		product = self.get_product_by_id(session, product_id)
		if not product:
			return 0.0
		return float(product.stock_quantity)
