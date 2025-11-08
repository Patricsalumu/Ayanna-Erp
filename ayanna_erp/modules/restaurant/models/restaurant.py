"""
ORM models for the Restaurant module
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from ayanna_erp.database.base import Base

# Simple enums as strings
STATUS_ENUM = ('en_cours', 'valide', 'annule')


class RestauSalle(Base):
    __tablename__ = 'restau_salles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    entreprise_id = Column(Integer, nullable=False)
    name = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    tables = relationship('RestauTable', back_populates='salle', cascade='all, delete-orphan')


class RestauTable(Base):
    __tablename__ = 'restau_tables'

    id = Column(Integer, primary_key=True, autoincrement=True)
    salle_id = Column(Integer, ForeignKey('restau_salles.id'), nullable=False)
    number = Column(String(50), nullable=False)
    pos_x = Column(Integer, default=0)
    pos_y = Column(Integer, default=0)
    width = Column(Integer, default=80)
    height = Column(Integer, default=80)
    shape = Column(String(50), default='rectangle')
    created_at = Column(DateTime, default=datetime.utcnow)

    salle = relationship('RestauSalle', back_populates='tables')


class RestauPanier(Base):
    __tablename__ = 'restau_paniers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    entreprise_id = Column(Integer, nullable=False)
    client_id = Column(Integer, nullable=True)
    serveuse_id = Column(Integer, nullable=True)
    table_id = Column(Integer, ForeignKey('restau_tables.id'), nullable=True)
    status = Column(String(50), default='en_cours')
    payment_method = Column(String(100))
    subtotal = Column(Float, default=0.0)
    remise_amount = Column(Float, default=0.0)
    total_final = Column(Float, default=0.0)
    user_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    produits = relationship('RestauProduitPanier', back_populates='panier', cascade='all, delete-orphan')
    payments = relationship('RestauPayment', back_populates='panier', cascade='all, delete-orphan')
    table = relationship('RestauTable')


class RestauProduitPanier(Base):
    __tablename__ = 'restau_produit_panier'

    id = Column(Integer, primary_key=True, autoincrement=True)
    panier_id = Column(Integer, ForeignKey('restau_paniers.id'), nullable=False)
    product_id = Column(Integer, nullable=False)
    quantity = Column(Integer, default=1)
    price = Column(Float, default=0.0)
    total = Column(Float, default=0.0)

    panier = relationship('RestauPanier', back_populates='produits')


class RestauPayment(Base):
    __tablename__ = 'restau_payments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    panier_id = Column(Integer, ForeignKey('restau_paniers.id'), nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(100))
    user_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    panier = relationship('RestauPanier', back_populates='payments')


class RestauExpense(Base):
    __tablename__ = 'restau_expenses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    entreprise_id = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, nullable=True)


# Helper to initialize tables programmatically if needed
def initialize_restaurant_tables():
    from ayanna_erp.database.database_manager import get_database_manager
    db = get_database_manager()
    tables = [
        RestauSalle.__table__, RestauTable.__table__, RestauPanier.__table__,
        RestauProduitPanier.__table__, RestauPayment.__table__, RestauExpense.__table__
    ]
    for t in tables:
        t.create(bind=db.engine, checkfirst=True)
    return True
