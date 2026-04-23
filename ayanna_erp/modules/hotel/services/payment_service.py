"""
PaymentService – enregistrement des paiements et gestion du statut crédit.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from ayanna_erp.database.database_manager import get_database_manager
from ayanna_erp.modules.hotel.models.model import HotelPayment, HotelReservation

log = logging.getLogger(__name__)


class PaymentService:

    def add_payment(
        self,
        reservation_id: int,
        amount: float,
        method: str = 'cash',
        user_id: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """
        Enregistre un paiement et met à jour le statut de paiement.
        method='credit' → aucun paiement créé, statut = 'credit'.
        """
        try:
            db = get_database_manager()
            with db.session_scope() as session:
                res = session.query(HotelReservation).filter_by(
                    id=reservation_id).first()
                if not res:
                    return False, "Réservation introuvable."
                if res.status in ('annulee', 'terminee'):
                    return False, "Impossible d'ajouter un paiement à une réservation terminée/annulée."

                # Cas crédit : on marque sans créer de ligne paiement
                if method == 'credit':
                    res.statut_paiement = 'credit'
                    return True, "Réservation enregistrée en crédit."

                amount = float(amount or 0.0)
                if amount <= 0:
                    return False, "Le montant doit être supérieur à 0."

                pay = HotelPayment(
                    reservation_id=reservation_id,
                    amount=amount,
                    method=method,
                    created_at=datetime.now(),
                    user_id=user_id,
                )
                session.add(pay)
                session.flush()

                # Recalculer statut
                paid = sum(p.amount for p in res.payments)
                total = res.total_amount or 0.0
                if paid <= 0:
                    res.statut_paiement = 'nonpaye'
                elif paid < total:
                    res.statut_paiement = 'partiel'
                else:
                    res.statut_paiement = 'paye'

                return True, f"Paiement de {amount:,.0f} enregistré."

        except Exception as e:
            log.exception("Erreur add_payment")
            return False, f"Erreur paiement : {e}"

    def get_payments_for_reservation(
            self, reservation_id: int) -> List[Dict[str, Any]]:
        db = get_database_manager()
        with db.session_scope() as session:
            pays = (session.query(HotelPayment)
                    .filter_by(reservation_id=reservation_id)
                    .order_by(HotelPayment.created_at)
                    .all())
            from sqlalchemy import text
            def _uname(uid):
                if not uid:
                    return '-'
                try:
                    row = session.execute(
                        text("SELECT name FROM core_users WHERE id = :uid"),
                        {'uid': uid}).fetchone()
                    return row[0] if row else str(uid)
                except Exception:
                    return str(uid)
            result = [
                {
                    'id': p.id,
                    'amount': p.amount,
                    'method': p.method,
                    'created_at': p.created_at,
                    'user_id': p.user_id,
                    'user_name': _uname(p.user_id),
                }
                for p in pays
            ]
            return result

    def get_daily_payments(
            self, target_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Retourne tous les paiements d'une journée donnée (aujourd'hui par défaut)."""
        db = get_database_manager()
        target_date = target_date or datetime.now()
        d_start = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0)
        d_end   = datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59)
        with db.session_scope() as session:
            pays = (session.query(HotelPayment)
                    .filter(HotelPayment.created_at >= d_start,
                            HotelPayment.created_at <= d_end)
                    .order_by(HotelPayment.created_at.desc())
                    .all())
            result = []
            for p in pays:
                res = p.reservation
                code = res.reservation_code if res else '-'
                client_name = ''
                if res and res.client:
                    client_name = (res.client.nom or '') + ' ' + (
                        res.client.prenom or '')
                result.append({
                    'id': p.id,
                    'reservation_code': code,
                    'client': client_name.strip(),
                    'amount': p.amount,
                    'method': p.method,
                    'created_at': p.created_at,
                })
            return result
