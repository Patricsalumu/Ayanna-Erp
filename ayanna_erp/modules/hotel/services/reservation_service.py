"""
ReservationService – création, check-in, check-out, prolongation,
annulation et consultation des réservations.
"""
import logging
import random
import string
from datetime import datetime, date
from typing import List, Optional, Tuple, Dict, Any

from ayanna_erp.database.database_manager import get_database_manager
from ayanna_erp.modules.hotel.models.model import (
    HotelReservation, HotelRoom, HotelCategory, HotelPayment
)
from ayanna_erp.modules.hotel.services.room_service import RoomService

log = logging.getLogger(__name__)
_room_svc = RoomService()


def _gen_code() -> str:
    """Génère un code de réservation unique de 6 caractères alpha-numériques."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=6))


def _unique_code(session) -> str:
    for _ in range(20):
        code = _gen_code()
        if not session.query(HotelReservation).filter_by(
                reservation_code=code).first():
            return code
    raise RuntimeError("Impossible de générer un code unique après 20 tentatives.")


def _nb_nuits(d_entree: datetime, d_sortie: datetime) -> int:
    delta = (d_sortie.date() - d_entree.date()).days
    return max(delta, 1)


def _to_datetime(v) -> datetime:
    if isinstance(v, datetime):
        return v
    if isinstance(v, date):
        return datetime(v.year, v.month, v.day)
    raise ValueError(f"Type non supporté : {type(v)}")


class ReservationService:

    # ------------------------------------------------------------------
    # Création
    # ------------------------------------------------------------------

    def create_reservation(
        self,
        client_id: int,
        category_id: int,
        date_entree: datetime,
        date_sortie: datetime,
        reduction: float = 0.0,
        notes: str = '',
        user_id: Optional[int] = None,
        acompte: float = 0.0,
        method: str = 'cash',
    ) -> Tuple[bool, str, Optional[HotelReservation]]:
        """
        Crée une réservation.
        Retourne (succès, message, objet_réservation).
        """
        try:
            date_entree = _to_datetime(date_entree)
            date_sortie = _to_datetime(date_sortie)

            if not client_id:
                return False, "Un client est obligatoire.", None
            if date_sortie <= date_entree:
                return False, "La date de sortie doit être après la date d'entrée.", None

            db = get_database_manager()
            with db.session_scope() as session:
                # Vérifier disponibilité par catégorie
                cat = session.query(HotelCategory).filter_by(
                    id=category_id, deleted=0).first()
                if not cat:
                    return False, "Catégorie introuvable.", None

                nuits = _nb_nuits(date_entree, date_sortie)
                total = nuits * cat.price_per_night - float(reduction or 0.0)
                total = max(total, 0.0)

                code = _unique_code(session)
                res = HotelReservation(
                    client_id=client_id,
                    reservation_code=code,
                    hotel_category_id=category_id,
                    room_id=None,
                    date_entree_prevue=date_entree,
                    date_sortie_prevue=date_sortie,
                    status='en_attente',
                    reduction=float(reduction or 0.0),
                    statut_paiement='nonpaye',
                    total_amount=total,
                    notes=notes or '',
                    created_at=datetime.now(),
                    user_id=user_id,
                )
                session.add(res)
                session.flush()

                # Acompte éventuel
                if acompte and float(acompte) > 0:
                    pay = HotelPayment(
                        reservation_id=res.id,
                        amount=float(acompte),
                        method=method,
                        created_at=datetime.now(),
                        user_id=user_id,
                    )
                    session.add(pay)
                    session.flush()
                    self._refresh_payment_status(session, res)

                session.refresh(res)
                res_id = res.id
                res_code = res.reservation_code

            log.info(f"Réservation {res_code} créée (id={res_id}).")
            return True, f"Réservation {res_code} créée avec succès.", res

        except Exception as e:
            log.exception("Erreur create_reservation")
            return False, f"Erreur : {e}", None

    # ------------------------------------------------------------------
    # Check-in
    # ------------------------------------------------------------------

    def checkin(self, reservation_id: int,
                user_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        Effectue le check-in : affecte une chambre disponible,
        met à jour les statuts et enregistre la date d'entrée réelle.
        """
        try:
            db = get_database_manager()
            with db.session_scope() as session:
                res = session.query(HotelReservation).filter_by(
                    id=reservation_id).first()
                if not res:
                    return False, "Réservation introuvable."
                if res.status not in ('en_attente', 'confirmee'):
                    return False, f"Impossible de faire le check-in : statut actuel = {res.status}."

                room = _room_svc.find_available_room(
                    res.hotel_category_id,
                    res.date_entree_prevue,
                    res.date_sortie_prevue,
                    exclude_reservation_id=reservation_id,
                )
                if not room:
                    return (False,
                            "Aucune chambre disponible pour cette catégorie "
                            "sur les dates demandées. "
                            "Veuillez choisir d'autres dates ou une autre catégorie.")

                # Affecter la chambre
                res.room_id = room.id
                res.date_entree_reelle = datetime.now()
                res.status = 'en_cours'

                # Mettre la chambre en occupée
                db_room = session.query(HotelRoom).filter_by(id=room.id).first()
                if db_room:
                    db_room.status = 'occupee'

                return True, f"Check-in effectué – Chambre {room.number} affectée."

        except Exception as e:
            log.exception("Erreur checkin")
            return False, f"Erreur check-in : {e}"

    # ------------------------------------------------------------------
    # Check-out
    # ------------------------------------------------------------------

    def checkout(self, reservation_id: int,
                 user_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        Effectue le check-out.
        Autorisé uniquement si statut_paiement = 'paye' ou 'credit'.
        """
        try:
            db = get_database_manager()
            with db.session_scope() as session:
                res = session.query(HotelReservation).filter_by(
                    id=reservation_id).first()
                if not res:
                    return False, "Réservation introuvable."
                if res.status != 'en_cours':
                    return False, f"Check-out impossible : statut = {res.status}."
                if res.statut_paiement not in ('paye', 'credit'):
                    return (False,
                            "Check-out refusé : le solde doit être intégralement "
                            "réglé ou mis en crédit avant de libérer la chambre.")

                res.date_sortie_reelle = datetime.now()
                res.status = 'terminee'

                if res.room_id:
                    room = session.query(HotelRoom).filter_by(
                        id=res.room_id).first()
                    if room:
                        room.status = 'menage'   # chambre passe en ménage

                return True, "Check-out effectué. La chambre est passée en ménage."

        except Exception as e:
            log.exception("Erreur checkout")
            return False, f"Erreur check-out : {e}"

    # ------------------------------------------------------------------
    # Prolongation
    # ------------------------------------------------------------------

    def extend_stay(self, reservation_id: int,
                    new_date_sortie: datetime,
                    user_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        Prolonge le séjour jusqu'à une nouvelle date de sortie.
        Vérifie la disponibilité de la chambre déjà affectée.
        """
        try:
            new_date_sortie = _to_datetime(new_date_sortie)
            db = get_database_manager()
            with db.session_scope() as session:
                res = session.query(HotelReservation).filter_by(
                    id=reservation_id).first()
                if not res:
                    return False, "Réservation introuvable."
                if res.status != 'en_cours':
                    return False, "Prolongation impossible : la réservation n'est pas en cours."
                if new_date_sortie <= res.date_entree_reelle:
                    return False, "La nouvelle date doit être après la date d'entrée réelle."

                # Vérifier qu'aucun autre séjour ne bloque la chambre
                if res.room_id:
                    conflict = (session.query(HotelReservation)
                                .filter(
                                    HotelReservation.room_id == res.room_id,
                                    HotelReservation.id != res.id,
                                    HotelReservation.status.in_(
                                        ['confirmee', 'en_cours', 'en_attente']),
                                    HotelReservation.date_entree_prevue < new_date_sortie,
                                    HotelReservation.date_sortie_prevue > (
                                        res.date_sortie_reelle or
                                        res.date_sortie_prevue),
                                ).first())
                    if conflict:
                        return (False,
                                "Prolongation impossible : conflit avec une autre réservation.")

                cat = session.query(HotelCategory).filter_by(
                    id=res.hotel_category_id).first()
                d_entree = res.date_entree_reelle or res.date_entree_prevue
                nuits = _nb_nuits(d_entree, new_date_sortie)
                new_total = nuits * cat.price_per_night - res.reduction
                new_total = max(new_total, 0.0)

                res.date_sortie_prevue = new_date_sortie
                res.date_sortie_reelle = None  # reset – sortie non encore faite
                res.total_amount = new_total

                # Recalculer statut paiement
                self._refresh_payment_status(session, res)

                return True, f"Séjour prolongé jusqu'au {new_date_sortie.strftime('%d/%m/%Y')}."

        except Exception as e:
            log.exception("Erreur extend_stay")
            return False, f"Erreur prolongation : {e}"

    # ------------------------------------------------------------------
    # Annulation
    # ------------------------------------------------------------------

    def cancel_reservation(self, reservation_id: int) -> Tuple[bool, str]:
        try:
            db = get_database_manager()
            with db.session_scope() as session:
                res = session.query(HotelReservation).filter_by(
                    id=reservation_id).first()
                if not res:
                    return False, "Réservation introuvable."
                if res.status in ('terminee', 'annulee'):
                    return False, f"Impossible d'annuler : statut = {res.status}."
                res.status = 'annulee'
                if res.room_id:
                    room = session.query(HotelRoom).filter_by(
                        id=res.room_id).first()
                    if room:
                        room.status = 'disponible'
                return True, "Réservation annulée."
        except Exception as e:
            log.exception("Erreur cancel_reservation")
            return False, f"Erreur annulation : {e}"

    # ------------------------------------------------------------------
    # Consultation
    # ------------------------------------------------------------------

    def get_all_reservations(self,
                              search: str = '',
                              date_from: Optional[date] = None,
                              date_to: Optional[date] = None,
                              status: Optional[str] = None) -> List[Dict[str, Any]]:
        db = get_database_manager()
        with db.session_scope() as session:
            q = session.query(HotelReservation)
            if status:
                q = q.filter(HotelReservation.status == status)
            if date_from:
                q = q.filter(
                    HotelReservation.date_entree_prevue >= _to_datetime(date_from))
            if date_to:
                q = q.filter(
                    HotelReservation.date_sortie_prevue <= datetime(
                        date_to.year, date_to.month, date_to.day, 23, 59, 59))
            reservations = q.order_by(
                HotelReservation.created_at.desc()).all()
            result = []
            for r in reservations:
                paid = sum(p.amount for p in r.payments)
                client_name = ''
                if r.client:
                    client_name = (r.client.nom or '') + ' ' + (
                        r.client.prenom or '')
                room_number = r.room.number if r.room else '-'
                cat_name = r.category.name if r.category else '-'
                row = {
                    'id': r.id,
                    'code': r.reservation_code,
                    'client_id': r.client_id,
                    'client_name': client_name.strip(),
                    'category': cat_name,
                    'room': room_number,
                    'date_entree_prevue': r.date_entree_prevue,
                    'date_sortie_prevue': r.date_sortie_prevue,
                    'date_entree_reelle': r.date_entree_reelle,
                    'date_sortie_reelle': r.date_sortie_reelle,
                    'status': r.status,
                    'statut_paiement': r.statut_paiement,
                    'total': r.total_amount,
                    'paid': paid,
                    'reste': max(r.total_amount - paid, 0.0),
                    'notes': r.notes or '',
                    'reduction': r.reduction,
                }
                if search:
                    s = search.lower()
                    if (s not in row['code'].lower()
                            and s not in row['client_name'].lower()
                            and s not in row['room'].lower()):
                        continue
                result.append(row)
            return result

    def get_reservation_by_id(self, res_id: int) -> Optional[Dict[str, Any]]:
        results = self.get_all_reservations()
        for r in results:
            if r['id'] == res_id:
                return r
        return None

    # ------------------------------------------------------------------
    # Helpers internes
    # ------------------------------------------------------------------

    @staticmethod
    def _refresh_payment_status(session, res: HotelReservation):
        """Met à jour statut_paiement à partir des paiements existants."""
        paid = sum(p.amount for p in res.payments)
        total = res.total_amount or 0.0
        if paid <= 0:
            res.statut_paiement = 'nonpaye'
        elif paid < total:
            res.statut_paiement = 'partiel'
        else:
            res.statut_paiement = 'paye'
