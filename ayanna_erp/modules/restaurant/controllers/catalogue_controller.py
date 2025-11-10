from typing import List, Optional
from ayanna_erp.database.database_manager import get_database_manager
from ayanna_erp.modules.core.controllers.product_controller import CoreProductController
from ayanna_erp.modules.restaurant.controllers.vente_controller import VenteController
from ayanna_erp.modules.restaurant.models.restaurant import RestauProduitPanier, RestauPanier
from datetime import datetime


class CatalogueController:
    """Controller glue between Core products and Restaurant panier logic."""
    def __init__(self, entreprise_id=1, pos_id: int = 1):
        self.db = get_database_manager()
        self.entreprise_id = entreprise_id
        self.pos_id = pos_id
        # Core product controller expects a pos_id
        self.core_ctrl = CoreProductController(pos_id)
        self.vente_ctrl = VenteController(entreprise_id=entreprise_id)

    def list_products(self, search: Optional[str] = None, category_id: Optional[int] = None, active_only: Optional[bool] = True):
        session = self.db.get_session()
        try:
            prods = self.core_ctrl.get_products(session=session, category_id=category_id, search_term=search, active_only=active_only)
            return prods
        finally:
            self.db.close_session()

    def get_product(self, product_id: int):
        session = self.db.get_session()
        try:
            p = self.core_ctrl.get_product_by_id(session, product_id)
            return p
        finally:
            self.db.close_session()

    def list_categories(self):
        """Retourne la liste des catégories CoreProductCategory pour l'entreprise du POS."""
        session = self.db.get_session()
        try:
            cats = self.core_ctrl.get_categories(session)
            return cats
        finally:
            self.db.close_session()

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

    def set_panier_note(self, panier_id: int, note: str):
        session = self.db.get_session()
        try:
            panier = session.query(RestauPanier).filter_by(id=panier_id).first()
            if not panier:
                raise ValueError('Panier introuvable')
            panier.note = note
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
