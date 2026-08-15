"""
ORM models for the Restaurant module

Les IDs ne sont plus générés côté Python : la base doit attribuer l'ID final
et le garder stable. Cela évite les UUID inutiles quand il n'y a pas de
synchronisation multicentres.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum, func
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
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

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
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    salle = relationship('RestauSalle', back_populates='tables')


class RestauPanier(Base):
    __tablename__ = 'restau_paniers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    entreprise_id = Column(Integer, nullable=False)
    client_id = Column(Integer, nullable=True)
    serveuse_id = Column(Integer, nullable=True)
    table_id = Column(Integer, ForeignKey('restau_tables.id'), nullable=True)
    status = Column(String(50), default='en_cours')
    payment_method = Column(String(100), default='non_paye')
    subtotal = Column(Float, default=0.0)
    remise_amount = Column(Float, default=0.0)
    total_final = Column(Float, default=0.0)
    user_id = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Statut logistique
    pret = Column(Integer, default=0)   # 0 = non prêt, 1 = prêt
    livre = Column(Integer, default=0)  # 0 = non livré, 1 = livré

    produits = relationship('RestauProduitPanier', back_populates='panier', cascade='all, delete-orphan')
    payments = relationship('RestauPayment', back_populates='panier', cascade='all, delete-orphan')
    # Historique d'impression: ne pas supprimer les traces si le panier est supprime.
    printed_invoices = relationship('RestauPrintedInvoice', back_populates='panier')
    bon_commandes = relationship('RestauBonCommande', back_populates='panier', cascade='all, delete-orphan')
    table = relationship('RestauTable')


class RestauProduitPanier(Base):
    __tablename__ = 'restau_produit_panier'

    id = Column(Integer, primary_key=True, autoincrement=True)
    panier_id = Column(Integer, ForeignKey('restau_paniers.id'), nullable=False)
    product_id = Column(Integer, nullable=False)
    quantity = Column(Integer, default=1)
    price = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    panier = relationship('RestauPanier', back_populates='produits')


class RestauPayment(Base):
    __tablename__ = 'restau_payments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    panier_id = Column(Integer, ForeignKey('restau_paniers.id'), nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(100))
    user_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    panier = relationship('RestauPanier', back_populates='payments')


class RestauExpense(Base):
    __tablename__ = 'restau_expenses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    entreprise_id = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class RestauPrintedInvoice(Base):
    __tablename__ = 'restau_printed_invoices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    entreprise_id = Column(Integer, nullable=False, index=True)
    panier_id = Column(Integer, ForeignKey('restau_paniers.id'), nullable=False, index=True)

    total_items_quantity = Column(Integer, default=0)
    product_lines_count = Column(Integer, default=0)
    total_amount = Column(Float, default=0.0)
    products_snapshot = Column(Text, nullable=False)

    customer_id = Column(Integer, nullable=True, index=True)
    printed_by_user_id = Column(Integer, nullable=True, index=True)
    printed_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    panier = relationship('RestauPanier', back_populates='printed_invoices')


class RestauBonCommande(Base):
    __tablename__ = 'restau_bon_commandes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    entreprise_id = Column(Integer, nullable=False, index=True)
    numero_bon = Column(Integer, nullable=False)
    restau_panier_id = Column(Integer, ForeignKey('restau_paniers.id'), nullable=False, index=True)
    serveuse_id = Column(Integer, nullable=True)
    client_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=True)
    produits_json = Column(Text, nullable=False)
    montant_total = Column(Float, default=0.0)
    statut = Column(String(50), default='valide')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    panier = relationship('RestauPanier', back_populates='bon_commandes')


# Helper to initialize tables programmatically if needed
def initialize_restaurant_tables():
    from ayanna_erp.database.database_manager import get_database_manager
    db = get_database_manager()
    tables = [
        RestauSalle.__table__, RestauTable.__table__, RestauPanier.__table__,
        RestauProduitPanier.__table__, RestauPayment.__table__, RestauExpense.__table__,
        RestauPrintedInvoice.__table__, RestauBonCommande.__table__
    ]
    for t in tables:
        t.create(bind=db.engine, checkfirst=True)
    return True
