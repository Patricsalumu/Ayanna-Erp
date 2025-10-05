from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.boutique.model.models import ShopCategory, ShopProduct
from ayanna_erp.core.entreprise_controller import EntrepriseController
from sqlalchemy.orm import Session
from typing import List, Optional

class CategorieController:
	"""
	Contrôleur pour la gestion des catégories de produits de la boutique
	"""
	def __init__(self, pos_id: int):
		self.db_manager = DatabaseManager()
		self.pos_id = pos_id
		self.entreprise_ctrl = EntrepriseController()

	def get_categories(self, session: Session, active_only: Optional[bool] = None) -> List[ShopCategory]:
		query = session.query(ShopCategory).filter(ShopCategory.pos_id == self.pos_id)
		if active_only is not None:
			query = query.filter(ShopCategory.is_active == active_only)
		return query.order_by(ShopCategory.name.asc()).all()

	def get_category_by_id(self, session: Session, category_id: int) -> Optional[ShopCategory]:
		return session.query(ShopCategory).filter(ShopCategory.id == category_id, ShopCategory.pos_id == self.pos_id).first()

	def create_category(self, session: Session, nom: str, description: Optional[str] = None, is_active: bool = True) -> ShopCategory:
		category = ShopCategory(
			pos_id=self.pos_id,
			name=nom,
			description=description,
			is_active=is_active
		)
		session.add(category)
		session.commit()
		return category

	def update_category(self, session: Session, category_id: int, **kwargs) -> Optional[ShopCategory]:
		category = self.get_category_by_id(session, category_id)
		if not category:
			return None
		for key, value in kwargs.items():
			if hasattr(category, key):
				setattr(category, key, value)
		session.commit()
		return category

	def delete_category(self, session: Session, category_id: int) -> bool:
		category = self.get_category_by_id(session, category_id)
		if not category:
			return False
		session.delete(category)
		session.commit()
		return True

	def get_category_products(self, session: Session, category_id: int) -> List[ShopProduct]:
		return session.query(ShopProduct).filter(ShopProduct.category_id == category_id, ShopProduct.pos_id == self.pos_id).all()
