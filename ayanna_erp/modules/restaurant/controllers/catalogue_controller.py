from typing import List, Optional
from types import SimpleNamespace
from threading import RLock
from ayanna_erp.database.database_manager import get_database_manager
from ayanna_erp.modules.core.controllers.product_controller import CoreProductController
from ayanna_erp.modules.restaurant.controllers.vente_controller import VenteController
from ayanna_erp.modules.restaurant.models.restaurant import RestauProduitPanier, RestauPanier
from datetime import datetime


class CatalogueController:
    """Controller glue between Core products and Restaurant panier logic."""
    _products_cache = {}
    _categories_cache = {}
    _cache_lock = RLock()

    def __init__(self, entreprise_id=1, pos_id: int = 1):
        self.db = get_database_manager()
        self.entreprise_id = entreprise_id
        self.pos_id = pos_id
        # Core product controller expects a pos_id
        self.core_ctrl = CoreProductController(pos_id)
        self.vente_ctrl = VenteController(entreprise_id=entreprise_id)

    def list_products(self, search: Optional[str] = None, category_id: Optional[int] = None, active_only: Optional[bool] = True):
        cache_key = (self.core_ctrl.entreprise_id, self.pos_id, active_only)
        with self._cache_lock:
            products = self._products_cache.get(cache_key)
        if products is None:
            session = self.db.SessionLocal()
            try:
                products = self.core_ctrl.get_products(
                    session=session,
                    active_only=active_only,
                    allowed_types=['finished_good', 'resale_product']
                )
                products = [SimpleNamespace(**{
                    key: value for key, value in product.__dict__.items()
                    if not key.startswith('_')
                }) for product in products]
                with self._cache_lock:
                    self._products_cache[cache_key] = products
            finally:
                session.close()

        search_text = (search or '').strip().lower()
        result = products
        if search_text:
            result = [product for product in products if search_text in str(getattr(product, 'name', '')).lower() or search_text in str(getattr(product, 'description', '') or '').lower()]
        elif category_id:
            result = [product for product in products if getattr(product, 'category_id', None) == category_id]
        return result

    def get_product(self, product_id: int):
        with self._cache_lock:
            for products in self._products_cache.values():
                for product in products:
                    if getattr(product, 'id', None) == product_id:
                        return product
        session = self.db.get_session()
        try:
            p = self.core_ctrl.get_product_by_id(session, product_id)
            return p
        finally:
            self.db.close_session()

    def list_categories(self):
        """Retourne la liste des catégories CoreProductCategory pour l'entreprise du POS."""
        cache_key = (self.core_ctrl.entreprise_id, self.pos_id)
        with self._cache_lock:
            categories = self._categories_cache.get(cache_key)
        if categories is None:
            session = self.db.SessionLocal()
            try:
                categories = self.core_ctrl.get_categories(session)
                categories = [SimpleNamespace(**{
                    key: value for key, value in category.__dict__.items()
                    if not key.startswith('_')
                }) for category in categories]
                with self._cache_lock:
                    self._categories_cache[cache_key] = categories
            finally:
                session.close()
        return categories

    def get_category_name(self, category_id):
        for category in self.list_categories():
            if getattr(category, 'id', None) == category_id:
                return getattr(category, 'name', None)
        return None

    @classmethod
    def clear_catalog_cache(cls):
        with cls._cache_lock:
            cls._products_cache.clear()
            cls._categories_cache.clear()

    @classmethod
    def preload_cache(cls, entreprise_id=1, pos_id=1):
        controller = cls(entreprise_id=entreprise_id, pos_id=pos_id)
        controller.list_categories()
        controller.list_products()

    # Panier helpers (restaurant-specific)
    def get_or_create_panier_for_table(self, table_id: int, client_id: Optional[int] = None, serveuse_id: Optional[int] = None, user_id: Optional[int] = None):
        # Try to find open panier, else create
        panier = self.vente_ctrl.get_open_panier_for_table(table_id)
        if panier:
            return panier
        return self.vente_ctrl.create_panier(table_id=table_id, client_id=client_id, serveuse_id=serveuse_id, user_id=user_id)

    def add_product_to_panier(self, panier_id: int, product_id: int, quantity: float, price: float):
        # If the product already exists in the panier, increment its quantity instead of creating a new line
        session = self.db.get_session()
        try:
            existing = session.query(RestauProduitPanier).filter_by(panier_id=panier_id, product_id=product_id).first()
            if existing:
                existing.quantity = float(existing.quantity) + float(quantity)
                existing.total = float(existing.quantity) * float(existing.price)
                session.flush()
                panier = session.query(RestauPanier).filter_by(id=panier_id).first()
                if panier:
                    panier.subtotal = sum([p.total for p in panier.produits]) if panier.produits else 0.0
                    panier.total_final = panier.subtotal - (panier.remise_amount or 0.0)
                    panier.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(existing)
                return existing
            else:
                # Delegate to VenteController to create a new line
                return self.vente_ctrl.add_product(panier_id, product_id, quantity, price)
        finally:
            self.db.close_session()

    def add_products_to_panier(self, panier_id: int, products):
        """Ajoute plusieurs lignes en une seule transaction SQL."""
        if not products:
            return
        session = self.db.SessionLocal()
        try:
            panier = session.query(RestauPanier).filter_by(id=panier_id).first()
            if not panier:
                raise ValueError('Panier introuvable')
            for product_id, data in products.items():
                quantity = float(data.get('quantity', 0) or 0)
                if quantity <= 0:
                    continue
                line = session.query(RestauProduitPanier).filter_by(
                    panier_id=panier_id, product_id=product_id
                ).first()
                if line:
                    line.quantity = float(line.quantity or 0) + quantity
                    line.total = float(line.quantity) * float(line.price or data.get('price', 0) or 0)
                else:
                    price = float(data.get('price', 0) or 0)
                    session.add(RestauProduitPanier(
                        panier_id=panier_id,
                        product_id=product_id,
                        quantity=quantity,
                        price=price,
                        total=quantity * price,
                    ))
            session.flush()
            panier.subtotal = sum(float(line.total or 0) for line in panier.produits)
            panier.total_final = panier.subtotal - float(panier.remise_amount or 0)
            panier.updated_at = datetime.utcnow()
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def remove_product_from_panier(self, panier_id: int, produit_panier_id: int):
        session = self.db.get_session()
        try:
            lp = session.query(RestauProduitPanier).filter_by(id=produit_panier_id, panier_id=panier_id).first()
            if not lp:
                raise ValueError('Ligne introuvable')
            session.delete(lp)
            # Recalculate totals
            session.flush()
            panier = session.query(RestauPanier).filter_by(id=panier_id).first()
            if panier:
                panier.subtotal = sum([p.total for p in panier.produits]) if panier.produits else 0.0
                panier.total_final = panier.subtotal - (panier.remise_amount or 0.0)
                panier.updated_at = datetime.utcnow()
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            self.db.close_session()

    def update_product_quantity(self, panier_id: int, produit_panier_id: int, new_quantity: float):
        session = self.db.get_session()
        try:
            lp = session.query(RestauProduitPanier).filter_by(id=produit_panier_id, panier_id=panier_id).first()
            if not lp:
                raise ValueError('Ligne introuvable')
            lp.quantity = new_quantity
            lp.total = float(new_quantity) * float(lp.price)
            session.flush()
            panier = session.query(RestauPanier).filter_by(id=panier_id).first()
            if panier:
                panier.subtotal = sum([p.total for p in panier.produits]) if panier.produits else 0.0
                panier.total_final = panier.subtotal - (panier.remise_amount or 0.0)
                panier.updated_at = datetime.utcnow()
            session.commit()
            return lp
        except Exception:
            session.rollback()
            raise
        finally:
            self.db.close_session()

    def list_cart_items(self, panier_id: int):
        session = self.db.get_session()
        try:
            q = session.query(RestauProduitPanier).filter_by(panier_id=panier_id).all()
            return q
        finally:
            self.db.close_session()

    def get_panier_totals(self, panier_id: int):
        return self.vente_ctrl.get_panier_total(panier_id)

    def set_panier_notes(self, panier_id: int, notes: str):
        session = self.db.get_session()
        try:
            panier = session.query(RestauPanier).filter_by(id=panier_id).first()
            if not panier:
                raise ValueError('Panier introuvable')
            panier.notes = notes
            panier.updated_at = datetime.utcnow()
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            self.db.close_session()

    def set_panier_client(self, panier_id: int, client_id: int):
        """Attribue un client au panier et persiste en base."""
        session = self.db.get_session()
        try:
            panier = session.query(RestauPanier).filter_by(id=panier_id).first()
            if not panier:
                raise ValueError('Panier introuvable')
            panier.client_id = int(client_id) if client_id else None
            panier.updated_at = datetime.utcnow()
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            self.db.close_session()

    def set_panier_serveuse(self, panier_id: int, serveuse_id: int):
        """Attribue une serveuse au panier et persiste en base."""
        session = self.db.get_session()
        try:
            panier = session.query(RestauPanier).filter_by(id=panier_id).first()
            if not panier:
                raise ValueError('Panier introuvable')
            panier.serveuse_id = int(serveuse_id) if serveuse_id else None
            panier.updated_at = datetime.utcnow()
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            self.db.close_session()
