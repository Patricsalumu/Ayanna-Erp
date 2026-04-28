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
from ayanna_erp.modules.hotel.utils.helpers import jours_reels as _jours_reels
from ayanna_erp.modules.hotel.services.hotel_accounting_service import get_hotel_accounting_service

log = logging.getLogger(__name__)
_room_svc = RoomService()
_acc = get_hotel_accounting_service()


def _user_name(session, user_id) -> str:
    """Récupère le nom d'un utilisateur depuis core_users (safe)."""
    if not user_id:
        return '-'
    try:
        from ayanna_erp.database.database_manager import get_database_manager as _gdb
        from sqlalchemy import text
        row = session.execute(
            text("SELECT name FROM core_users WHERE id = :uid"),
            {'uid': user_id}
        ).fetchone()
        return row[0] if row else str(user_id)
    except Exception:
        return str(user_id)


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

            # --- écritures comptables (hors session pour éviter les verrous) ---
            try:
                from ayanna_erp.database.database_manager import get_database_manager as _gdb2
                from ayanna_erp.modules.boutique.model.models import ShopClient
                with _gdb2().session_scope() as _s:
                    _cl = _s.query(ShopClient).filter_by(id=client_id).first()
                    _cname = ((_cl.nom or '') + ' ' + (_cl.prenom or '')).strip() if _cl else str(client_id)
                # Écriture de réservation : D/Clients – C/Produits hôtel
                _acc.on_reservation(res_code, total, _cname, user_id)
                # Écriture de caisse pour l'acompte : D/Caisse – C/Clients
                if acompte and float(acompte) > 0:
                    _acc.on_paiement(res_code, float(acompte), method, _cname, user_id)
            except Exception:
                pass
            # ------------------------------------------------------------------

            return True, f"Réservation {res_code} créée avec succès.", res

        except Exception as e:
            log.exception("Erreur create_reservation")
            return False, f"Erreur : {e}", None

    # ------------------------------------------------------------------
    # Check-in
    # ------------------------------------------------------------------

    def checkin(self, reservation_id: int,
                checkin_date: Optional[datetime] = None,
                user_id: Optional[int] = None,
                force_room_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        Effectue le check-in.
        Si force_room_id est fourni, affecte cette chambre précise
        (utile pour affecter la chambre sur laquelle l'utilisateur a cliqué,
        ou pour un upgrade vers une chambre de catégorie supérieure).
        Sinon, cherche automatiquement une chambre disponible de la bonne catégorie.
        checkin_date : date/heure du check-in (défaut = maintenant).
        """
        try:
            effective_date = checkin_date or datetime.now()
            db = get_database_manager()
            with db.session_scope() as session:
                res = session.query(HotelReservation).filter_by(
                    id=reservation_id).first()
                if not res:
                    return False, "Réservation introuvable."
                if res.status not in ('en_attente', 'confirmee'):
                    return False, f"Impossible de faire le check-in : statut actuel = {res.status}."

                if force_room_id:
                    # Chambre spécifiée explicitement (clic sur la carte ou upgrade)
                    room = session.query(HotelRoom).filter_by(
                        id=force_room_id, deleted=0).first()
                    if not room:
                        return False, "La chambre sélectionnée est introuvable."
                    if room.status != 'disponible':
                        return False, f"La chambre {room.number} n'est pas disponible (statut : {room.status})."
                    # Vérifier absence de conflit de dates sur cette chambre précise
                    conflict = (session.query(HotelReservation)
                                .filter(
                                    HotelReservation.room_id == room.id,
                                    HotelReservation.id != reservation_id,
                                    HotelReservation.status.in_(['confirmee', 'en_cours', 'en_attente']),
                                    HotelReservation.date_entree_prevue < res.date_sortie_prevue,
                                    HotelReservation.date_sortie_prevue > res.date_entree_prevue,
                                ).first())
                    if conflict:
                        return False, f"Conflit de dates sur la chambre {room.number}."
                else:
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
                res.date_entree_reelle = effective_date
                res.status = 'en_cours'

                # Mettre la chambre en occupée
                db_room = session.query(HotelRoom).filter_by(id=room.id).first()
                if db_room:
                    db_room.status = 'occupee'

                upgrade_note = ''
                if force_room_id and room.hotel_category_id != res.hotel_category_id:
                    upgrade_note = ' (UPGRADE)'
                return True, f"Check-in effectué – Chambre {room.number} affectée{upgrade_note}."

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
        Recalcule le total sur la base des jours réellement passés,
        puis autorise le check-out uniquement si statut_paiement = 'paye' ou 'credit'.
        """
        try:
            db = get_database_manager()
            _checkout_msg = None
            _acc_co = None
            with db.session_scope() as session:
                res = session.query(HotelReservation).filter_by(
                    id=reservation_id).first()
                if not res:
                    return False, "Réservation introuvable."
                if res.status != 'en_cours':
                    return False, f"Check-out impossible : statut = {res.status}."

                # --- Recalcul sur jours réels ---
                d_entree = res.date_entree_reelle or res.date_entree_prevue
                jours = _jours_reels(d_entree)
                cat = session.query(HotelCategory).filter_by(
                    id=res.hotel_category_id).first()
                price_per_night = cat.price_per_night if cat else 0.0
                new_total = max(jours * price_per_night - float(res.reduction or 0), 0.0)

                original_total = float(res.total_amount or 0.0)  # avant recalcul

                # Mettre à jour le total et le statut paiement
                res.total_amount = new_total
                self._refresh_payment_status(session, res)
                session.flush()

                paid = sum(p.amount for p in res.payments)
                reste = max(new_total - paid, 0.0)

                if res.statut_paiement not in ('paye', 'credit'):
                    return (
                        False,
                        f"FACTURE NON RÉGLÉE – Check-out impossible !\n\n"
                        f"  • Jours réels de séjour : {jours} jour(s)\n"
                        f"  • Total à payer         : {new_total:,.0f}\n"
                        f"  • Total payé            : {paid:,.0f}\n"
                        f"  • Reste à payer         : {reste:,.0f}\n\n"
                        f"Seul un paiement enregistré en Crédit permet\n"
                        f"le check-out avec solde impayé.\n"
                        f"Veuillez d'abord régler ou enregistrer en Crédit."
                    )

                res.date_sortie_reelle = datetime.now()
                res.status = 'terminee'

                if res.room_id:
                    room = session.query(HotelRoom).filter_by(
                        id=res.room_id).first()
                    if room:
                        room.status = 'disponible'

                _checkout_msg = (
                    True,
                    f"Check-out effectué ({jours} jour(s) réel(s)). "
                    "La chambre est maintenant disponible."
                )
                _acc_co = {
                    'code': res.reservation_code,
                    'client_id': res.client_id,
                    'original_total': original_total,
                    'new_total': new_total,
                }

            # --- écriture comptable checkout (hors session) ---
            if _acc_co:
                try:
                    from ayanna_erp.database.database_manager import get_database_manager as _gdb2
                    from ayanna_erp.modules.boutique.model.models import ShopClient
                    with _gdb2().session_scope() as _s:
                        _cl = _s.query(ShopClient).filter_by(id=_acc_co['client_id']).first()
                        _cname = ((_cl.nom or '') + ' ' + (_cl.prenom or '')).strip() if _cl else ''
                    avoir = _acc_co['original_total'] - _acc_co['new_total']
                    if avoir > 0:
                        _acc.on_checkout_avoir(_acc_co['code'], avoir, _cname, user_id)
                except Exception:
                    pass
            # ---------------------------------------------------

            return _checkout_msg

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
            _extend_msg = None
            _acc_ext = None
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

                old_total = float(res.total_amount or 0.0)
                delta = max(new_total - old_total, 0.0)

                res.date_sortie_prevue = new_date_sortie
                res.date_sortie_reelle = None  # reset – sortie non encore faite
                res.total_amount = new_total

                # Recalculer statut paiement
                self._refresh_payment_status(session, res)

                _extend_msg = f"Séjour prolongé jusqu'au {new_date_sortie.strftime('%d/%m/%Y')}."
                _acc_ext = {'code': res.reservation_code, 'client_id': res.client_id, 'delta': delta}

            # --- écriture comptable prolongement (hors session) ---
            if _acc_ext and _acc_ext['delta'] > 0:
                try:
                    from ayanna_erp.database.database_manager import get_database_manager as _gdb2
                    from ayanna_erp.modules.boutique.model.models import ShopClient
                    with _gdb2().session_scope() as _s:
                        _cl = _s.query(ShopClient).filter_by(id=_acc_ext['client_id']).first()
                        _cname = ((_cl.nom or '') + ' ' + (_cl.prenom or '')).strip() if _cl else ''
                    _acc.on_prolongement(_acc_ext['code'], _acc_ext['delta'], _cname, user_id)
                except Exception:
                    pass
            # -------------------------------------------------------

            return True, _extend_msg

        except Exception as e:
            log.exception("Erreur extend_stay")
            return False, f"Erreur prolongation : {e}"

    # ------------------------------------------------------------------
    # Annulation
    # ------------------------------------------------------------------

    def cancel_reservation(self, reservation_id: int,
                            user_id=None) -> Tuple[bool, str]:
        try:
            db = get_database_manager()
            _cancel_msg = None
            _acc_cancel = None
            with db.session_scope() as session:
                res = session.query(HotelReservation).filter_by(
                    id=reservation_id).first()
                if not res:
                    return False, "Réservation introuvable."
                if res.status in ('terminee', 'annulee'):
                    return False, f"Impossible d'annuler : statut = {res.status}."

                # Calcul du montant réellement encaissé (hors lignes crédit à 0)
                paid_real = sum(
                    p.amount for p in res.payments
                    if p.method != 'credit' and (p.amount or 0) > 0
                )

                _acc_cancel = {
                    'code': res.reservation_code,
                    'client_id': res.client_id,
                    'montant': float(res.total_amount or 0.0),
                    'paid_real': float(paid_real),
                }

                res.status = 'annulee'
                res.statut_paiement = 'rembourse' if paid_real > 0 else res.statut_paiement

                if res.room_id:
                    room = session.query(HotelRoom).filter_by(
                        id=res.room_id).first()
                    if room:
                        room.status = 'disponible'

                # Écriture de remboursement négative si des paiements réels existent
                if paid_real > 0:
                    refund = HotelPayment(
                        reservation_id=reservation_id,
                        amount=-paid_real,
                        method='remboursement',
                        created_at=datetime.now(),
                        user_id=user_id,
                    )
                    session.add(refund)
                    _cancel_msg = (
                        f"Réservation annulée.\n"
                        f"Remboursement enregistré : -{paid_real:,.0f} "
                        f"(visible dans la caisse)."
                    )
                else:
                    _cancel_msg = "Réservation annulée."

            # --- écritures comptables annulation (hors session) ---
            if _acc_cancel:
                try:
                    from ayanna_erp.database.database_manager import get_database_manager as _gdb2
                    from ayanna_erp.modules.boutique.model.models import ShopClient
                    with _gdb2().session_scope() as _s:
                        _cl = _s.query(ShopClient).filter_by(id=_acc_cancel['client_id']).first()
                        _cname = ((_cl.nom or '') + ' ' + (_cl.prenom or '')).strip() if _cl else ''
                    _acc.on_annulation(_acc_cancel['code'], _acc_cancel['montant'], _cname, user_id)
                    if _acc_cancel['paid_real'] > 0:
                        _acc.on_remboursement(_acc_cancel['code'], _acc_cancel['paid_real'], _cname, user_id)
                except Exception:
                    pass
            # -------------------------------------------------------

            return True, _cancel_msg
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
                    HotelReservation.created_at >= _to_datetime(date_from))
            if date_to:
                q = q.filter(
                    HotelReservation.created_at <= datetime(
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
                d_entree_reelle = r.date_entree_reelle
                if r.status == 'en_cours' and d_entree_reelle:
                    jr = max(_jours_reels(d_entree_reelle), 1)
                elif r.status == 'terminee' and r.date_entree_reelle and r.date_sortie_reelle:
                    jr = max(_nb_nuits(r.date_entree_reelle, r.date_sortie_reelle), 1)
                else:
                    jr = 1

                # Nuitées prévues (entrée prévue → sortie prévue)
                nuitees = (
                    max(_nb_nuits(r.date_entree_prevue, r.date_sortie_prevue), 1)
                    if r.date_entree_prevue and r.date_sortie_prevue
                    else 1
                )

                # Montant réel : jours_reels × prix_catégorie − réduction
                price_per_night = r.category.price_per_night if r.category else 0.0
                if r.status == 'en_cours':
                    montant_reel = max(
                        jr * price_per_night - float(r.reduction or 0), 0.0)
                else:
                    # terminée : total_amount déjà recalculé au checkout
                    montant_reel = float(r.total_amount or 0.0)

                # Solde = montant_reel − payé
                # > 0 : client doit encore payer
                # < 0 : client a trop payé (crédit)
                solde = montant_reel - paid

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
                    'jours_reels': jr,
                    'nuitees': nuitees,
                    'montant_reel': montant_reel,
                    'solde': solde,
                    'price_per_night': price_per_night,
                    'pays': (r.client.pays or '') if r.client else '',
                    'carte_identite': (r.client.carte_identite or '') if r.client else '',
                    'created_at': r.created_at,
                    'user_id': r.user_id,
                    'created_by_name': _user_name(session, r.user_id),
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

    # ------------------------------------------------------------------
    # Move room (déménagement de chambre)
    # ------------------------------------------------------------------

    def move_room(self, reservation_id: int, new_room_id: int,
                  user_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        Transfère une réservation en cours vers une autre chambre
        de la MÊME catégorie qui est disponible.
        L'ancienne chambre repasse en statut 'disponible'.
        """
        try:
            db = get_database_manager()
            with db.session_scope() as session:
                res = session.query(HotelReservation).filter_by(
                    id=reservation_id).first()
                if not res:
                    return False, "Réservation introuvable."
                if res.status != 'en_cours':
                    return False, "Déménagement impossible : la réservation n'est pas en cours."

                new_room = session.query(HotelRoom).filter_by(
                    id=new_room_id, deleted=0).first()
                if not new_room:
                    return False, "La chambre de destination est introuvable."
                if new_room.hotel_category_id != res.hotel_category_id:
                    return False, "La chambre de destination n'est pas de la même catégorie."
                if new_room.status != 'disponible':
                    return False, f"La chambre {new_room.number} n'est pas disponible."

                # Vérifier absence de conflit de dates
                conflict = (session.query(HotelReservation)
                            .filter(
                                HotelReservation.room_id == new_room_id,
                                HotelReservation.id != reservation_id,
                                HotelReservation.status.in_(['confirmee', 'en_cours', 'en_attente']),
                                HotelReservation.date_entree_prevue < res.date_sortie_prevue,
                                HotelReservation.date_sortie_prevue > (res.date_entree_reelle or res.date_entree_prevue),
                            ).first())
                if conflict:
                    return False, f"Conflit de dates sur la chambre {new_room.number}."

                old_room_id = res.room_id
                old_room_number = '?'

                # Libérer l'ancienne chambre
                if old_room_id:
                    old_room = session.query(HotelRoom).filter_by(id=old_room_id).first()
                    if old_room:
                        old_room_number = old_room.number
                        old_room.status = 'disponible'

                # Affecter la nouvelle chambre
                res.room_id = new_room_id
                new_room.status = 'occupee'

                return True, (f"Déménagement effectué : chambre {old_room_number} "
                              f"→ chambre {new_room.number}.")

        except Exception as e:
            log.exception("Erreur move_room")
            return False, f"Erreur déménagement : {e}"

    @staticmethod
    def _refresh_payment_status(session, res: HotelReservation):
        """Met à jour statut_paiement à partir des paiements existants.
        
        Si la réservation est en crédit (une ligne method='credit' existe),
        le statut 'credit' est préservé et ne peut pas être écrasé.
        """
        # Préserver le statut crédit
        has_credit = any(p.method == 'credit' for p in res.payments)
        if has_credit:
            res.statut_paiement = 'credit'
            return
        paid = sum(p.amount for p in res.payments)
        total = res.total_amount or 0.0
        if paid <= 0:
            res.statut_paiement = 'nonpaye'
        elif paid < total:
            res.statut_paiement = 'partiel'
        else:
            res.statut_paiement = 'paye'
