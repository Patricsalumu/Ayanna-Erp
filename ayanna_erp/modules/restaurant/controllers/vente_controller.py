"""
Controller for restaurant sales (panier, add products, payments)
"""
from decimal import Decimal
from datetime import datetime
from types import SimpleNamespace
from ayanna_erp.database.database_manager import get_database_manager
from ayanna_erp.modules.restaurant.models.restaurant import (
    RestauPanier, RestauProduitPanier, RestauPayment, RestauTable
)


class VenteController:
    def __init__(self, entreprise_id=1):
        self.db = get_database_manager()
        self.entreprise_id = entreprise_id

    def create_panier(self, table_id=None, client_id=None, serveuse_id=None, user_id=None):
        session = self.db.get_session()
        try:
            panier = RestauPanier(
                entreprise_id=self.entreprise_id,
                table_id=table_id,
                client_id=client_id,
                serveuse_id=serveuse_id,
                user_id=user_id,
                payment_method='non_paye',
                status='en_cours',
                subtotal=0.0,
                remise_amount=0.0,
                total_final=0.0
            )
            session.add(panier)
            session.flush()
            session.commit()
            # detach safe lightweight object to avoid Session-bound attribute refresh errors
            session.refresh(panier)
            return SimpleNamespace(
                id=panier.id,
                table_id=panier.table_id,
                client_id=panier.client_id,
                serveuse_id=panier.serveuse_id,
                user_id=panier.user_id,
                status=panier.status,
                subtotal=panier.subtotal,
                remise_amount=panier.remise_amount,
                total_final=panier.total_final,
                created_at=panier.created_at,
                updated_at=panier.updated_at
            )
        except Exception as e:
            session.rollback()
            raise
        finally:
            self.db.close_session()

    def add_product(self, panier_id, product_id, quantity, price):
        session = self.db.get_session()
        try:
            panier = session.query(RestauPanier).filter_by(id=panier_id).first()
            if not panier:
                raise ValueError("Panier introuvable")
            total = float(quantity) * float(price)
            ligne = RestauProduitPanier(
                panier_id=panier_id,
                product_id=product_id,
                quantity=quantity,
                price=price,
                total=total
            )
            session.add(ligne)
            # Recalculer totaux
            session.flush()
            subtotal = sum([p.total for p in panier.produits])
            panier.subtotal = subtotal
            panier.total_final = subtotal - (panier.remise_amount or 0.0)
            panier.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(ligne)
            return SimpleNamespace(
                id=ligne.id,
                panier_id=ligne.panier_id,
                product_id=ligne.product_id,
                quantity=ligne.quantity,
                price=ligne.price,
                total=ligne.total
            )
        except Exception:
            session.rollback()
            raise
        finally:
            self.db.close_session()

    def add_payment(self, panier_id, amount, payment_method, user_id=None):
        session = self.db.get_session()
        try:
            panier = session.query(RestauPanier).filter_by(id=panier_id).first()
            if not panier:
                raise ValueError("Panier introuvable")
            pay = RestauPayment(
                panier_id=panier_id,
                amount=amount,
                payment_method=payment_method,
                user_id=user_id
            )
            session.add(pay)
            session.flush()
            # recalculer total payé et mettre à jour le statut de paiement dans payment_method
            total_paid = sum([p.amount for p in panier.payments])
            try:
                total_final = float(panier.total_final or 0.0)
            except Exception:
                total_final = 0.0
            if total_paid <= 0:
                panier.payment_method = 'non_paye'
            elif total_paid < total_final:
                panier.payment_method = 'partiel'
                panier.status = 'valide'
            else:
                panier.payment_method = 'paye'
                # si réglé complètement, marquer la commande comme validée
                panier.status = 'valide'
            panier.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(pay)
            return SimpleNamespace(
                id=pay.id,
                panier_id=pay.panier_id,
                amount=pay.amount,
                payment_method=pay.payment_method,
                user_id=pay.user_id,
                created_at=pay.created_at
            )
        except Exception:
            session.rollback()
            raise
        finally:
            self.db.close_session()

    def get_panier(self, panier_id):
        session = self.db.get_session()
        try:
            panier = session.query(RestauPanier).filter_by(id=panier_id).first()
            if not panier:
                return None
            # return lightweight detached object
            session.refresh(panier)
            return SimpleNamespace(
                id=panier.id,
                table_id=panier.table_id,
                client_id=panier.client_id,
                serveuse_id=panier.serveuse_id,
                user_id=panier.user_id,
                status=panier.status,
                subtotal=panier.subtotal,
                remise_amount=panier.remise_amount,
                total_final=panier.total_final,
                created_at=panier.created_at,
                updated_at=panier.updated_at
            )
        finally:
            self.db.close_session()

    def get_open_panier_for_table(self, table_id):
        """Retourne le panier en cours (status 'en_cours') pour une table donnée"""
        session = self.db.get_session()
        try:
            panier = session.query(RestauPanier).filter_by(table_id=table_id, status='en_cours').first()
            if not panier:
                return None
            session.refresh(panier)
            return SimpleNamespace(
                id=panier.id,
                table_id=panier.table_id,
                client_id=panier.client_id,
                serveuse_id=panier.serveuse_id,
                user_id=panier.user_id,
                status=panier.status,
                subtotal=panier.subtotal,
                remise_amount=panier.remise_amount,
                total_final=panier.total_final,
                created_at=panier.created_at,
                updated_at=panier.updated_at
            )
        finally:
            self.db.close_session()

    def get_panier_total(self, panier_id):
        """Calcule le total payé et le total final du panier"""
        session = self.db.get_session()
        try:
            panier = session.query(RestauPanier).filter_by(id=panier_id).first()
            if not panier:
                return 0.0, 0.0
            total_lines = sum([p.total for p in panier.produits]) if panier.produits else 0.0
            total_paid = sum([p.amount for p in panier.payments]) if panier.payments else 0.0
            return float(total_lines), float(total_paid)
        finally:
            self.db.close_session()

    def list_paniers(self, date_from=None, date_to=None, status=None):
        session = self.db.get_session()
        try:
            q = session.query(RestauPanier).filter_by(entreprise_id=self.entreprise_id)
            if status:
                q = q.filter(RestauPanier.status == status)
            if date_from:
                q = q.filter(RestauPanier.created_at >= date_from)
            if date_to:
                q = q.filter(RestauPanier.created_at <= date_to)
            return q.all()
        finally:
            self.db.close_session()
