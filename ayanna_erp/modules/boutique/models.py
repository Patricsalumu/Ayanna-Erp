"""
Modèles de données pour le module Boutique/Pharmacie
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from ayanna_erp.database.database_manager import Base


class ShopProductCategory(Base):
    __tablename__ = "shop_product_categories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pos_id = Column(Integer, ForeignKey('core_pos_points.id'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    products = relationship("ShopProduct", back_populates="category")


class ShopProduct(Base):
    __tablename__ = "shop_products"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pos_id = Column(Integer, ForeignKey('core_pos_points.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    image = Column(Text)  # chemin vers l'image
    cost = Column(Numeric(15, 2), default=0.0)
    price_unit = Column(Numeric(15, 2), default=0.0)
    stock_quantity = Column(Numeric(15, 2), default=0.0)
    account_id = Column(Integer, ForeignKey('comptes_comptables.id'))
    category_id = Column(Integer, ForeignKey('shop_product_categories.id'))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    pos = relationship("POSPoint")
    account = relationship("CompteComptable")
    category = relationship("ShopProductCategory", back_populates="products")
    sale_lines = relationship("ShopSaleLineProduct", back_populates="product")


class ShopService(Base):
    __tablename__ = "shop_services"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pos_id = Column(Integer, ForeignKey('core_pos_points.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    cost = Column(Numeric(15, 2), default=0.0)
    price = Column(Numeric(15, 2), default=0.0)
    account_id = Column(Integer, ForeignKey('comptes_comptables.id'))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    pos = relationship("POSPoint")
    account = relationship("CompteComptable")
    sale_lines = relationship("ShopSaleLineService", back_populates="service")


class ShopSale(Base):
    __tablename__ = "shop_sales"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pos_id = Column(Integer, ForeignKey('core_pos_points.id'), nullable=False)
    partner_id = Column(Integer, ForeignKey('core_partners.id'))
    reference = Column(String(100))
    status = Column(String(20), default='draft')  # draft, confirmed, paid, cancelled
    total_services = Column(Numeric(15, 2), default=0.0)
    total_products = Column(Numeric(15, 2), default=0.0)
    total_amount = Column(Numeric(15, 2), default=0.0)
    total_cost = Column(Numeric(15, 2), default=0.0)
    created_by = Column(Integer, ForeignKey('core_users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime)
    
    # Relations
    pos = relationship("POSPoint")
    partner = relationship("Partner")
    created_by_user = relationship("User")
    product_lines = relationship("ShopSaleLineProduct", back_populates="sale", cascade="all, delete-orphan")
    service_lines = relationship("ShopSaleLineService", back_populates="sale", cascade="all, delete-orphan")
    payments = relationship("ShopPayment", back_populates="sale", cascade="all, delete-orphan")
    
    def calculate_totals(self):
        """Calculer les totaux de la vente"""
        self.total_products = sum(line.line_total for line in self.product_lines)
        self.total_services = sum(line.line_total for line in self.service_lines)
        self.total_amount = self.total_products + self.total_services
        self.total_cost = sum(line.line_cost for line in self.product_lines) + sum(line.line_cost for line in self.service_lines)


class ShopSaleLineProduct(Base):
    __tablename__ = "shop_sale_lines_products"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sale_id = Column(Integer, ForeignKey('shop_sales.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('shop_products.id'), nullable=False)
    quantity = Column(Numeric(15, 2), default=1)
    line_total = Column(Numeric(15, 2), default=0.0)
    line_cost = Column(Numeric(15, 2), default=0.0)
    
    # Relations
    sale = relationship("ShopSale", back_populates="product_lines")
    product = relationship("ShopProduct", back_populates="sale_lines")


class ShopSaleLineService(Base):
    __tablename__ = "shop_sale_lines_services"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sale_id = Column(Integer, ForeignKey('shop_sales.id'), nullable=False)
    service_id = Column(Integer, ForeignKey('shop_services.id'), nullable=False)
    quantity = Column(Numeric(15, 2), default=1)
    line_total = Column(Numeric(15, 2), default=0.0)
    line_cost = Column(Numeric(15, 2), default=0.0)
    
    # Relations
    sale = relationship("ShopSale", back_populates="service_lines")
    service = relationship("ShopService", back_populates="sale_lines")


class ShopPayment(Base):
    __tablename__ = "shop_payments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sale_id = Column(Integer, ForeignKey('shop_sales.id'), nullable=False)
    payment_method_id = Column(Integer, ForeignKey('module_payment_methods.id'), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    payment_date = Column(DateTime, default=datetime.utcnow)
    journal_id = Column(Integer, ForeignKey('journal_comptables.id'))
    
    # Relations
    sale = relationship("ShopSale", back_populates="payments")
    payment_method = relationship("PaymentMethod")
    journal = relationship("JournalComptable")
