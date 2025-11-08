"""
Controller for listing and updating restaurant commandes
"""
from ayanna_erp.database.database_manager import get_database_manager
from ayanna_erp.modules.restaurant.models.restaurant import RestauPanier


class CommandesController:
    def __init__(self, entreprise_id=1):
        self.db = get_database_manager()
        self.entreprise_id = entreprise_id

    def list_commandes(self, date_from=None, date_to=None, status=None, payment_method=None):
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
            return q.all()
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
