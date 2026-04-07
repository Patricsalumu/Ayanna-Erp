from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.core.models.core_products import CoreProductCategory, CoreProduct
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
		# Récupérer l'entreprise_id depuis le pos_id
		session = self.db_manager.get_session()
		try:
			from ayanna_erp.database.database_manager import POSPoint
			pos = session.query(POSPoint).filter_by(id=pos_id).first()
			self.entreprise_id = pos.enterprise_id if pos else 1
		finally:
			session.close()

	def get_categories(self, session: Session, active_only: Optional[bool] = None) -> List[CoreProductCategory]:
		query = session.query(CoreProductCategory).filter(CoreProductCategory.entreprise_id == self.entreprise_id)
		if active_only is not None:
			query = query.filter(CoreProductCategory.is_active == active_only)
		return query.order_by(CoreProductCategory.name.asc()).all()

	def get_category_by_id(self, session: Session, category_id: int) -> Optional[CoreProductCategory]:
		return session.query(CoreProductCategory).filter(CoreProductCategory.id == category_id, CoreProductCategory.entreprise_id == self.entreprise_id).first()

	def create_category(self, session: Session, nom: str, description: Optional[str] = None, is_active: bool = True) -> CoreProductCategory:
		category = CoreProductCategory(
			entreprise_id=self.entreprise_id,
			name=nom,
			description=description,
			is_active=is_active
		)
		session.add(category)
		session.commit()
		return category

	def update_category(self, session: Session, category_id: int, **kwargs) -> Optional[CoreProductCategory]:
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

	def get_category_products(self, session: Session, category_id: int) -> List[CoreProduct]:
		return session.query(CoreProduct).filter(CoreProduct.category_id == category_id, CoreProduct.entreprise_id == self.entreprise_id).all()
