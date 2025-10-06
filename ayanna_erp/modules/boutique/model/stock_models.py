"""
Modèles étendus pour la gestion avancée des stocks avec entrepôts
Architecture complète pour gestion multi-entrepôts
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import sys
import os

# Import du gestionnaire de base de données principal
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from ayanna_erp.database.base import Base


class ShopWarehouse(Base):
    """Table des entrepôts/magasins"""
    __tablename__ = 'shop_warehouses'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pos_id = Column(Integer, nullable=False)  # Référence au POS
    code = Column(String(20), nullable=False, unique=True)  # Code unique de l'entrepôt
    name = Column(String(200), nullable=False)  # Nom de l'entrepôt
    type = Column(String(50), default='storage')  # storage, shop, transit, damaged
    description = Column(Text)
    address = Column(Text)  # Adresse de l'entrepôt
    contact_person = Column(String(100))  # Responsable de l'entrepôt
    contact_phone = Column(String(20))
    contact_email = Column(String(150))
    is_default = Column(Boolean, default=False)  # Entrepôt par défaut pour ce POS
    is_active = Column(Boolean, default=True)
    capacity_limit = Column(Numeric(15, 2))  # Capacité limite en unités
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relations
    stocks = relationship("ShopWarehouseStock", back_populates="warehouse")
    transfer_sources = relationship("ShopStockTransfer", foreign_keys="ShopStockTransfer.source_warehouse_id", back_populates="source_warehouse")
    transfer_destinations = relationship("ShopStockTransfer", foreign_keys="ShopStockTransfer.destination_warehouse_id", back_populates="destination_warehouse")
    movements = relationship("ShopStockMovement", back_populates="warehouse")


class ShopWarehouseStock(Base):
    """Table des stocks par entrepôt et produit"""
    __tablename__ = 'shop_warehouse_stocks'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column(Integer, ForeignKey('shop_warehouses.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('shop_products.id'), nullable=False)
    quantity_available = Column(Numeric(15, 2), default=0.0)  # Quantité disponible
    quantity_reserved = Column(Numeric(15, 2), default=0.0)  # Quantité réservée
    quantity_in_transit = Column(Numeric(15, 2), default=0.0)  # Quantité en transit
    min_stock_level = Column(Numeric(15, 2), default=0.0)  # Niveau minimum de stock
    max_stock_level = Column(Numeric(15, 2))  # Niveau maximum de stock
    reorder_point = Column(Numeric(15, 2), default=0.0)  # Point de réapprovisionnement
    last_movement_date = Column(DateTime)  # Date du dernier mouvement
    last_inventory_date = Column(DateTime)  # Date du dernier inventaire
    average_cost = Column(Numeric(15, 2), default=0.0)  # Coût moyen pondéré
    
    # Relations
    warehouse = relationship("ShopWarehouse", back_populates="stocks")
    product = relationship("ShopProduct")
    movements = relationship("ShopStockMovement", back_populates="warehouse_stock")


class ShopStockMovement(Base):
    """Table des mouvements de stock détaillés par entrepôt"""
    __tablename__ = 'shop_stock_movements'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column(Integer, ForeignKey('shop_warehouses.id'), nullable=False)
    warehouse_stock_id = Column(Integer, ForeignKey('shop_warehouse_stocks.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('shop_products.id'), nullable=False)
    movement_type = Column(String(50), nullable=False)  # PURCHASE, SALE, TRANSFER_IN, TRANSFER_OUT, ADJUSTMENT, LOSS, RETURN
    direction = Column(String(10), nullable=False)  # IN, OUT
    quantity = Column(Numeric(15, 2), nullable=False)  # Quantité du mouvement
    unit_cost = Column(Numeric(15, 2), default=0.0)  # Coût unitaire
    total_cost = Column(Numeric(15, 2), default=0.0)  # Coût total
    quantity_before = Column(Numeric(15, 2), default=0.0)  # Quantité avant mouvement
    quantity_after = Column(Numeric(15, 2), default=0.0)  # Quantité après mouvement
    reference_document = Column(String(100))  # Référence du document source
    reference_id = Column(Integer)  # ID de la référence (panier, transfert, etc.)
    lot_number = Column(String(50))  # Numéro de lot
    expiry_date = Column(DateTime)  # Date d'expiration
    reason = Column(String(500))  # Motif du mouvement
    movement_date = Column(DateTime, default=func.current_timestamp())
    user_id = Column(Integer)  # ID de l'utilisateur
    user_name = Column(String(100))  # Nom de l'utilisateur
    validated_by = Column(String(100))  # Validé par
    validation_date = Column(DateTime)  # Date de validation
    is_validated = Column(Boolean, default=False)
    
    # Relations
    warehouse = relationship("ShopWarehouse", back_populates="movements")
    warehouse_stock = relationship("ShopWarehouseStock", back_populates="movements")
    product = relationship("ShopProduct")


class ShopStockTransfer(Base):
    """Table des transferts de stock entre entrepôts"""
    __tablename__ = 'shop_stock_transfers'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    transfer_number = Column(String(50), nullable=False, unique=True)  # Numéro de transfert
    source_warehouse_id = Column(Integer, ForeignKey('shop_warehouses.id'), nullable=False)
    destination_warehouse_id = Column(Integer, ForeignKey('shop_warehouses.id'), nullable=False)
    status = Column(String(20), default='PENDING')  # PENDING, IN_TRANSIT, RECEIVED, CANCELLED
    priority = Column(String(20), default='NORMAL')  # LOW, NORMAL, HIGH, URGENT
    transfer_type = Column(String(30), default='INTERNAL')  # INTERNAL, CUSTOMER, SUPPLIER, LOSS
    requested_by = Column(String(100))  # Demandé par
    requested_date = Column(DateTime, default=func.current_timestamp())
    approved_by = Column(String(100))  # Approuvé par
    approved_date = Column(DateTime)
    shipped_by = Column(String(100))  # Expédié par
    shipped_date = Column(DateTime)
    received_by = Column(String(100))  # Reçu par
    received_date = Column(DateTime)
    notes = Column(Text)  # Notes du transfert
    total_items = Column(Integer, default=0)  # Nombre total d'articles
    total_quantity = Column(Numeric(15, 2), default=0.0)  # Quantité totale transférée
    total_cost = Column(Numeric(15, 2), default=0.0)  # Coût total du transfert
    
    # Relations
    source_warehouse = relationship("ShopWarehouse", foreign_keys=[source_warehouse_id], back_populates="transfer_sources")
    destination_warehouse = relationship("ShopWarehouse", foreign_keys=[destination_warehouse_id], back_populates="transfer_destinations")
    transfer_items = relationship("ShopStockTransferItem", back_populates="transfer")


class ShopStockTransferItem(Base):
    """Table des articles dans un transfert de stock"""
    __tablename__ = 'shop_stock_transfer_items'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    transfer_id = Column(Integer, ForeignKey('shop_stock_transfers.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('shop_products.id'), nullable=False)
    quantity_requested = Column(Numeric(15, 2), nullable=False)  # Quantité demandée
    quantity_shipped = Column(Numeric(15, 2), default=0.0)  # Quantité expédiée
    quantity_received = Column(Numeric(15, 2), default=0.0)  # Quantité reçue
    unit_cost = Column(Numeric(15, 2), default=0.0)  # Coût unitaire
    total_cost = Column(Numeric(15, 2), default=0.0)  # Coût total de la ligne
    lot_number = Column(String(50))  # Numéro de lot
    expiry_date = Column(DateTime)  # Date d'expiration
    notes = Column(Text)  # Notes sur l'article
    
    # Relations
    transfer = relationship("ShopStockTransfer", back_populates="transfer_items")
    product = relationship("ShopProduct")


class ShopInventory(Base):
    """Table des inventaires physiques"""
    __tablename__ = 'shop_inventories'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    inventory_number = Column(String(50), nullable=False, unique=True)  # Numéro d'inventaire
    warehouse_id = Column(Integer, ForeignKey('shop_warehouses.id'), nullable=False)
    inventory_date = Column(DateTime, nullable=False)
    status = Column(String(20), default='DRAFT')  # DRAFT, IN_PROGRESS, COMPLETED, VALIDATED
    inventory_type = Column(String(30), default='FULL')  # FULL, PARTIAL, CYCLE
    reason = Column(String(200))  # Raison de l'inventaire
    started_by = Column(String(100))  # Commencé par
    started_date = Column(DateTime)
    completed_by = Column(String(100))  # Terminé par
    completed_date = Column(DateTime)
    validated_by = Column(String(100))  # Validé par
    validated_date = Column(DateTime)
    notes = Column(Text)
    total_items_counted = Column(Integer, default=0)
    total_discrepancies = Column(Integer, default=0)
    total_variance_cost = Column(Numeric(15, 2), default=0.0)
    
    # Relations
    warehouse = relationship("ShopWarehouse")
    inventory_items = relationship("ShopInventoryItem", back_populates="inventory")


class ShopInventoryItem(Base):
    """Table des articles dans un inventaire"""
    __tablename__ = 'shop_inventory_items'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    inventory_id = Column(Integer, ForeignKey('shop_inventories.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('shop_products.id'), nullable=False)
    expected_quantity = Column(Numeric(15, 2), default=0.0)  # Quantité attendue (système)
    counted_quantity = Column(Numeric(15, 2), default=0.0)  # Quantité comptée
    variance_quantity = Column(Numeric(15, 2), default=0.0)  # Écart en quantité
    unit_cost = Column(Numeric(15, 2), default=0.0)  # Coût unitaire
    variance_cost = Column(Numeric(15, 2), default=0.0)  # Écart en valeur
    lot_number = Column(String(50))  # Numéro de lot compté
    expiry_date = Column(DateTime)  # Date d'expiration
    counted_by = Column(String(100))  # Compté par
    counted_date = Column(DateTime)
    verified_by = Column(String(100))  # Vérifié par
    verified_date = Column(DateTime)
    notes = Column(Text)  # Notes sur l'article
    adjustment_applied = Column(Boolean, default=False)  # Ajustement appliqué
    
    # Relations
    inventory = relationship("ShopInventory", back_populates="inventory_items")
    product = relationship("ShopProduct")


class ShopStockAlert(Base):
    """Table des alertes de stock"""
    __tablename__ = 'shop_stock_alerts'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column(Integer, ForeignKey('shop_warehouses.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('shop_products.id'), nullable=False)
    alert_type = Column(String(30), nullable=False)  # LOW_STOCK, OUT_OF_STOCK, OVERSTOCK, EXPIRY_SOON, EXPIRED
    current_quantity = Column(Numeric(15, 2), default=0.0)
    threshold_quantity = Column(Numeric(15, 2), default=0.0)
    alert_level = Column(String(20), default='INFO')  # INFO, WARNING, CRITICAL
    message = Column(String(500))  # Message d'alerte
    is_acknowledged = Column(Boolean, default=False)  # Alerte acquittée
    acknowledged_by = Column(String(100))  # Acquittée par
    acknowledged_date = Column(DateTime)
    created_date = Column(DateTime, default=func.current_timestamp())
    resolved_date = Column(DateTime)  # Date de résolution
    
    # Relations
    warehouse = relationship("ShopWarehouse")
    product = relationship("ShopProduct")