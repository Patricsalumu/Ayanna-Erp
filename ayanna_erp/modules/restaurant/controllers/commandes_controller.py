"""
Controller for listing and updating restaurant commandes
"""
from types import SimpleNamespace
from ayanna_erp.database.database_manager import get_database_manager
from ayanna_erp.modules.restaurant.models.restaurant import RestauPanier, RestauProduitPanier
from ayanna_erp.modules.core.models import CoreProduct


class CommandesController:
    def __init__(self, entreprise_id=1):
        self.db = get_database_manager()
        self.entreprise_id = entreprise_id

    def list_commandes(self, date_from=None, date_to=None, status=None, payment_method=None, product_search: str = None, product_id: int = None):
        """Lister les paniers (commandes).

        Options de filtrage:
        - status, payment_method, date_from/date_to
        - product_search: cherche par nom de produit (CoreProduct.name)
        - product_id: filtre par id de produit présent dans la commande
        Retourne une liste d'objets SimpleNamespace détachés (safe pour l'UI).
        """
        session = self.db.get_session()
        try:
            q = session.query(RestauPanier).filter_by(entreprise_id=self.entreprise_id)
            if status:
                q = q.filter(RestauPanier.status == status)
            if payment_method:
                q = q.filter(RestauPanier.payment_method == payment_method)
            if date_from:
                q = q.filter(RestauPanier.created_at >= date_from)
            if date_to:
                q = q.filter(RestauPanier.created_at <= date_to)

            # Filtre par produit: joindre les lignes panier et le produit core
            if product_search or product_id:
                q = q.join(RestauProduitPanier, RestauProduitPanier.panier_id == RestauPanier.id)
                q = q.join(CoreProduct, CoreProduct.id == RestauProduitPanier.product_id)
                if product_id:
                    q = q.filter(CoreProduct.id == int(product_id))
                if product_search:
                    like_term = f"%{product_search}%"
                    q = q.filter(CoreProduct.name.ilike(like_term))

            # éviter doublons si jointures
            q = q.distinct()

            rows = q.order_by(RestauPanier.created_at.desc()).all()

            # convertir en objets détachés
            result = []
            for p in rows:
                result.append(SimpleNamespace(
                    id=p.id,
                    table_id=p.table_id,
                    client_id=p.client_id,
                    status=p.status,
                    subtotal=p.subtotal,
                    total_final=p.total_final,
                    created_at=p.created_at,
                    updated_at=p.updated_at
                ))
            return result
        finally:
            self.db.close_session()

    def change_status(self, panier_id, new_status):
        session = self.db.get_session()
        try:
            panier = session.query(RestauPanier).filter_by(id=panier_id).first()
            if not panier:
                return False, "Panier introuvable"
            panier.status = new_status
            session.commit()
            return True, "OK"
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            self.db.close_session()

    def inspect_recent_product_ids(self, limit: int = 20):
        """Diagnostic helper: retourne les dernières lignes de restau_produit_panier
        et tente de résoudre le product_id vers CoreProduct ou ShopProduct.
        Retourne une liste de dicts pour inspection.
        """
        session = self.db.get_session()
        try:
            rows = session.query(RestauProduitPanier).order_by(RestauProduitPanier.id.desc()).limit(limit).all()
            results = []
            # lazy import for ShopProduct (boutique)
            try:
                from ayanna_erp.modules.boutique.model.models import ShopPanierProduct, ShopProduct
            except Exception:
                ShopProduct = None

            for r in rows:
                pid = r.product_id
                resolved = {'ligne_id': r.id, 'panier_id': r.panier_id, 'product_id': pid, 'core_name': None, 'shop_name': None}
                try:
                    cp = session.query(CoreProduct).filter(CoreProduct.id == pid).first()
                    if cp:
                        resolved['core_name'] = cp.name
                except Exception:
                    resolved['core_name'] = None
                if ShopProduct is not None:
                    try:
                        sp = session.query(ShopProduct).filter(ShopProduct.id == pid).first()
                        if sp:
                            # ShopProduct may have 'name' or 'nom'
                            resolved['shop_name'] = getattr(sp, 'name', getattr(sp, 'nom', None))
                    except Exception:
                        resolved['shop_name'] = None
                results.append(resolved)
            return results
        finally:
            self.db.close_session()
