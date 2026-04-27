"""
Nouveaux modèles pour la gestion de stock simplifiée
Architecture avec 4 tables essentielles
"""

from sqlalchemy import Column, Integer, String, DateTime, Decimal, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ayanna_erp.database.base import Base


class StockWarehouse(Base):
    """
    Table des entrepôts - liés à l'entreprise (pas au POS)
    """
    __tablename__ = 'stock_warehouses'
    
    id = Column(Integer, primary_key=True)
    entreprise_id = Column(Integer, nullable=False, index=True)  # Changé de pos_id
    code = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False, default='Principal')  # Principal, Transit, Endommagé, etc.
    description = Column(Text)
    address = Column(Text)
    contact_person = Column(String(255))
    contact_phone = Column(String(50))
    contact_email = Column(String(255))
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    capacity_limit = Column(Decimal(15, 2))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<StockWarehouse(code='{self.code}', name='{self.name}', entreprise_id={self.entreprise_id})>"


class StockConfig(Base):
    """
    Configuration des entrepôts par point de vente
    Définit quel entrepôt sera débité lors des ventes
    """
    __tablename__ = 'stock_config'
    
    id = Column(Integer, primary_key=True)
    pos_id = Column(Integer, nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey('stock_warehouses.id'), nullable=False)
    entreprise_id = Column(Integer, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relations
    warehouse = relationship("StockWarehouse", backref="pos_configurations")
    
    def __repr__(self):
        return f"<StockConfig(pos_id={self.pos_id}, warehouse_id={self.warehouse_id})>"


class StockProduitEntrepot(Base):
    """
    Table pivot produit-entrepôt avec quantités
    Simplifiée selon les spécifications
    """
    __tablename__ = 'stock_produits_entrepot'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey('stock_warehouses.id'), nullable=False)
    quantity = Column(Decimal(15, 3), nullable=False, default=0)
    unit_cost = Column(Decimal(15, 2), nullable=False, default=0)
    total_cost = Column(Decimal(15, 2), nullable=False, default=0)
    min_stock_level = Column(Decimal(15, 3), default=0)  # Seuil minimum
    last_movement_date = Column(DateTime, default=func.now())
    reference = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relations
    warehouse = relationship("StockWarehouse", backref="stock_products")
    
    def __repr__(self):
        return f"<StockProduitEntrepot(product_id={self.product_id}, warehouse_id={self.warehouse_id}, quantity={self.quantity})>"


class StockMouvement(Base):
    """
    Enregistrement de tous les mouvements de stock
    """
    __tablename__ = 'stock_mouvements'
    
    id = Column(Integer, primary_key=True)
    
    # Entrepôts source et destination
    warehouse_id_depart = Column(String(50), nullable=False)  # ID entrepôt ou "ACHAT"
    warehouse_id_destination = Column(String(50), nullable=False)  # ID entrepôt ou "VENTE"
    
    # Informations produit
    product_id = Column(Integer, nullable=False, index=True)
    quantity = Column(Decimal(15, 3), nullable=False)
    unit_cost = Column(Decimal(15, 2), nullable=False)
    total_cost = Column(Decimal(15, 2), nullable=False)
    
    # État avant/après mouvement
    quantity_before = Column(Decimal(15, 3), nullable=False, default=0)
    quantity_after = Column(Decimal(15, 3), nullable=False, default=0)
    
    # Traçabilité
    reference_document = Column(String(255))  # Facture, bon de commande, etc.
    mouvement_date = Column(DateTime, default=func.now())
    user_id = Column(Integer, nullable=False)
    
    # Métadonnées
    created_at = Column(DateTime, default=func.now())
    updated_by = Column(Integer)
    
    def __repr__(self):
        return f"<StockMouvement(product_id={self.product_id}, {self.warehouse_id_depart}→{self.warehouse_id_destination}, qty={self.quantity})>"


# Modèles compatibilité (pour transition)
class ShopWarehouse(StockWarehouse):
    """Alias pour compatibilité pendant la transition"""
    __tablename__ = None
    
    @property
    def pos_id(self):
        """Compatibilité : retourne entreprise_id comme pos_id"""
        return self.entreprise_id


class ShopWarehouseStock(StockProduitEntrepot):
    """Alias pour compatibilité pendant la transition"""
    __tablename__ = None