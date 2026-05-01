"""
RoomService – gestion des chambres et catégories (CRUD + disponibilité).
Toute la logique métier passe par ce service ; les vues n'accèdent jamais
directement à la base de données.
"""
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import joinedload
from ayanna_erp.database.database_manager import get_database_manager
from ayanna_erp.modules.hotel.models.model import HotelCategory, HotelRoom, HotelReservation

log = logging.getLogger(__name__)


class RoomService:
    # ------------------------------------------------------------------
    # Catégories
    # ------------------------------------------------------------------

    def get_all_categories(self) -> List[HotelCategory]:
        """Retourne les catégories actives."""
        db = get_database_manager()
        with db.session_scope() as session:
            cats = (session.query(HotelCategory)
                    .filter(HotelCategory.deleted == 0)
                    .order_by(HotelCategory.name)
                    .all())
            session.expunge_all()
            return cats

    def create_category(self, name: str, price_per_night: float) -> HotelCategory:
        db = get_database_manager()
        with db.session_scope() as session:
            cat = HotelCategory(name=name.strip(),
                                price_per_night=float(price_per_night),
                                created_at=datetime.now())
            session.add(cat)
            session.flush()
            session.refresh(cat)
            session.expunge(cat)
            return cat

    def update_category(self, cat_id: int, name: str, price_per_night: float) -> bool:
        db = get_database_manager()
        with db.session_scope() as session:
            cat = session.query(HotelCategory).filter_by(id=cat_id).first()
            if not cat:
                return False
            cat.name = name.strip()
            cat.price_per_night = float(price_per_night)
            return True

    def delete_category(self, cat_id: int) -> bool:
        db = get_database_manager()
        with db.session_scope() as session:
            cat = session.query(HotelCategory).filter_by(id=cat_id).first()
            if not cat:
                return False
            cat.deleted = 1
            return True

    # ------------------------------------------------------------------
    # Chambres
    # ------------------------------------------------------------------

    def get_all_rooms(self, category_id: Optional[int] = None) -> List[HotelRoom]:
        db = get_database_manager()
        with db.session_scope() as session:
            q = session.query(HotelRoom).filter(HotelRoom.deleted == 0)
            if category_id is not None:
                q = q.filter(HotelRoom.hotel_category_id == category_id)
            rooms = q.order_by(HotelRoom.id).all()
            for r in rooms:
                # eager-load lightweight attrs
                _ = r.category.name if r.category else None
            session.expunge_all()
            return rooms

    def create_room(self, number: str, category_id: int) -> HotelRoom:
        db = get_database_manager()
        with db.session_scope() as session:
            room = HotelRoom(number=number.strip(),
                             hotel_category_id=category_id,
                             status='disponible',
                             created_at=datetime.now())
            session.add(room)
            session.flush()
            session.refresh(room)
            session.expunge(room)
            return room

    def update_room(self, room_id: int, number: str,
                    category_id: int, status: str) -> bool:
        db = get_database_manager()
        with db.session_scope() as session:
            room = session.query(HotelRoom).filter_by(id=room_id).first()
            if not room:
                return False
            room.number = number.strip()
            room.hotel_category_id = category_id
            room.status = status
            return True

    def delete_room(self, room_id: int) -> bool:
        db = get_database_manager()
        with db.session_scope() as session:
            room = session.query(HotelRoom).filter_by(id=room_id).first()
            if not room:
                return False
            room.deleted = 1
            return True

    def set_room_status(self, room_id: int, status: str) -> bool:
        db = get_database_manager()
        with db.session_scope() as session:
            room = session.query(HotelRoom).filter_by(id=room_id).first()
            if not room:
                return False
            room.status = status
            return True

    # ------------------------------------------------------------------
    # Disponibilité
    # ------------------------------------------------------------------

    def find_available_room(self, category_id: int,
                            date_entree: datetime,
                            date_sortie: datetime,
                            exclude_reservation_id: Optional[int] = None) -> Optional[HotelRoom]:
        """
        Trouve une chambre disponible pour une catégorie et des dates données.
        Une chambre est disponible si elle est en statut 'disponible' et si
        aucune réservation active ne chevauche les dates demandées.
        """
        db = get_database_manager()
        with db.session_scope() as session:
            rooms = (session.query(HotelRoom)
                     .filter(HotelRoom.hotel_category_id == category_id,
                             HotelRoom.deleted == 0,
                             HotelRoom.status == 'disponible')
                     .all())
            for room in rooms:
                q = (session.query(HotelReservation)
                     .filter(
                         HotelReservation.room_id == room.id,
                         HotelReservation.status.in_(
                             ['confirmee', 'en_cours', 'en_attente']),
                         HotelReservation.date_entree_prevue < date_sortie,
                         HotelReservation.date_sortie_prevue > date_entree,
                     ))
                if exclude_reservation_id:
                    q = q.filter(
                        HotelReservation.id != exclude_reservation_id)
                conflict = q.first()
                if not conflict:
                    session.expunge(room)
                    return room
            return None

    def is_category_available(self, category_id: int,
                               date_entree: datetime,
                               date_sortie: datetime) -> bool:
        """Vérifie qu'au moins une chambre est disponible pour cette catégorie/dates."""
        return self.find_available_room(category_id, date_entree, date_sortie) is not None

    def get_room_with_active_reservation(self, room_id: int):
        """Retourne la réservation en cours pour une chambre (ou None)."""
        db = get_database_manager()
        with db.session_scope() as session:
            res = (session.query(HotelReservation)
                   .options(joinedload(HotelReservation.client))
                   .filter(HotelReservation.room_id == room_id,
                           HotelReservation.status == 'en_cours')
                   .first())
            if res:
                # Pre-load all attributes needed by the view
                if res.client:
                    _ = res.client.nom
                    _ = res.client.prenom
                session.expunge_all()
            return res
