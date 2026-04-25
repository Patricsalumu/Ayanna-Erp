"""
ORM models for the Hotel module – Ayanna ERP
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from ayanna_erp.database.base import Base


class HotelCategory(Base):
    """Catégories de chambres (Standard, Deluxe, Suite …)"""
    __tablename__ = 'hotel_categories'
    __table_args__ = {'extend_existing': True}

    id           = Column(Integer, primary_key=True, autoincrement=True)
    name         = Column(String(150), nullable=False)
    price_per_night = Column(Float, nullable=False, default=0.0)
    created_at   = Column(DateTime, default=datetime.now)
    deleted      = Column(Integer, default=0)   # 0 = actif, 1 = supprimé

    rooms        = relationship('HotelRoom',        back_populates='category')
    reservations = relationship('HotelReservation', back_populates='category')


class HotelRoom(Base):
    """Chambres de l'hôtel"""
    __tablename__ = 'hotel_rooms'
    __table_args__ = {'extend_existing': True}

    id                 = Column(Integer, primary_key=True, autoincrement=True)
    number             = Column(String(20), nullable=False)
    hotel_category_id  = Column(Integer, ForeignKey('hotel_categories.id'), nullable=False)
    # disponible | occupee | menage | maintenance
    status             = Column(String(50), default='disponible')
    created_at         = Column(DateTime, default=datetime.now)
    deleted            = Column(Integer, default=0)

    category     = relationship('HotelCategory',    back_populates='rooms')
    reservations = relationship('HotelReservation', back_populates='room')


class HotelReservation(Base):
    """Réservations hôtelières"""
    __tablename__ = 'hotel_reservations'
    __table_args__ = {'extend_existing': True}

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    client_id           = Column(Integer, ForeignKey('shop_clients.id'), nullable=False)
    reservation_code    = Column(String(10), unique=True, nullable=False)
    hotel_category_id   = Column(Integer, ForeignKey('hotel_categories.id'), nullable=False)
    room_id             = Column(Integer, ForeignKey('hotel_rooms.id'), nullable=True)

    date_entree_prevue  = Column(DateTime, nullable=False)
    date_sortie_prevue  = Column(DateTime, nullable=False)
    date_entree_reelle  = Column(DateTime, nullable=True)
    date_sortie_reelle  = Column(DateTime, nullable=True)

    # en_attente | confirmee | en_cours | terminee | annulee
    status              = Column(String(50), default='en_attente')
    reduction           = Column(Float, default=0.0)
    # nonpaye | partiel | paye | credit
    statut_paiement     = Column(String(30), default='nonpaye')
    total_amount        = Column(Float, default=0.0)
    notes               = Column(Text, nullable=True)
    created_at          = Column(DateTime, default=datetime.now)
    user_id             = Column(Integer, nullable=True)

    client   = relationship('ShopClient')
    category = relationship('HotelCategory', back_populates='reservations')
    room     = relationship('HotelRoom',     back_populates='reservations')
    payments = relationship('HotelPayment',  back_populates='reservation',
                            cascade='all, delete-orphan')


class HotelPayment(Base):
    """Paiements des réservations"""
    __tablename__ = 'hotel_payments'
    __table_args__ = {'extend_existing': True}

    id             = Column(Integer, primary_key=True, autoincrement=True)
    reservation_id = Column(Integer, ForeignKey('hotel_reservations.id'), nullable=False)
    amount         = Column(Float, nullable=False)
    # cash | mobile_money | carte
    method         = Column(String(50), default='cash')
    reference      = Column(String(200), nullable=True)   # référence transaction mobile/banque
    created_at     = Column(DateTime, default=datetime.now)
    user_id        = Column(Integer, nullable=True)

    reservation = relationship('HotelReservation', back_populates='payments')
