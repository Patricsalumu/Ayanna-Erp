# -*- coding: utf-8 -*-
"""
Modèle des produits centralisés de l'entreprise
Remplace shop_products avec une logique centralisée par entreprise
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from ayanna_erp.database.base import Base


class CoreProduct(Base):
    """Table centralisée des produits pour toute l'entreprise"""
    __tablename__ = "core_products"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    entreprise_id = Column(Integer, ForeignKey('core_enterprises.id'), nullable=False)  # Changé de pos_id vers entreprise_id
    category_id = Column(Integer, ForeignKey('core_product_categories.id'))
    code = Column(String(50), unique=True)  # Code produit unique dans l'entreprise
    name = Column(String(200), nullable=False)
    description = Column(Text)
    image = Column(Text)  # chemin vers l'image
    barcode = Column(String(100))  # Code-barres
    
    # Prix et coûts
    cost = Column(Numeric(15, 2), default=0.0)  # Coût d'achat
    cost_price = Column(Numeric(15, 2), default=0.0)  # Prix de revient
    price_unit = Column(Numeric(15, 2), default=0.0)  # Prix de vente unitaire
    sale_price = Column(Numeric(15, 2), default=0.0)  # Prix de vente au public
    
    # Informations de stock (informatives, le vrai stock est dans stock_produits_entrepot)
    unit = Column(String(50), default='pièce')  # Unité de mesure
    
    # Comptabilité
    account_id = Column(Integer, ForeignKey('compta_comptes.id'))
    
    # État
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    entreprise = relationship("Entreprise")
    category = relationship("CoreProductCategory", back_populates="products")
    account = relationship("ComptaComptes")
    
    # Relations avec les autres modules (qui utilisent maintenant core_products)
    pos_accesses = relationship("POSProductAccess", back_populates="product")
    # Note: D'autres relations seront ajoutées selon les besoins des modules
    
    def __repr__(self):
        return f"<CoreProduct(id={self.id}, name='{self.name}', entreprise_id={self.entreprise_id})>"


class CoreProductCategory(Base):
    """Catégories de produits centralisées"""
    __tablename__ = "core_product_categories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    entreprise_id = Column(Integer, ForeignKey('core_enterprises.id'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey('core_product_categories.id'))  # Catégorie parente
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    entreprise = relationship("Entreprise")
    products = relationship("CoreProduct", back_populates="category")
    children = relationship("CoreProductCategory", backref='parent', remote_side=[id])
    
    def __repr__(self):
        return f"<CoreProductCategory(id={self.id}, name='{self.name}', entreprise_id={self.entreprise_id})>"


class POSProductAccess(Base):
    """Table de liaison entre POS et produits - définit quels produits sont disponibles pour chaque POS"""
    __tablename__ = "pos_product_access"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pos_id = Column(Integer, ForeignKey('core_pos_points.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('core_products.id'), nullable=False)
    
    # Prix spécifiques au POS (optionnels, sinon utilise le prix du produit)
    custom_price = Column(Numeric(15, 2))  # Prix personnalisé pour ce POS
    custom_cost = Column(Numeric(15, 2))   # Coût personnalisé pour ce POS
    
    # Configuration par POS
    is_available = Column(Boolean, default=True)  # Produit disponible sur ce POS
    display_order = Column(Integer, default=0)    # Ordre d'affichage sur le POS
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    pos = relationship("POSPoint")
    product = relationship("CoreProduct", back_populates="pos_accesses")
    
    def __repr__(self):
        return f"<POSProductAccess(pos_id={self.pos_id}, product_id={self.product_id}, available={self.is_available})>"