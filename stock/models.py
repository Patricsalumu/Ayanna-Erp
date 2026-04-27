"""
Modèles de données pour le module Stock - Architecture Simplifiée
4 tables optimisées : stock_warehouses, stock_config, stock_produits_entrepot, stock_mouvements
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


class StockWarehouse(Base):
    """Table des entrepôts - Architecture simplifiée"""
    __tablename__ = 'stock_warehouses'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    entreprise_id = Column(Integer, nullable=False)  # Référence à l'entreprise
    code = Column(String(50), unique=True, nullable=False)  # Code unique de l'entrepôt
    name = Column(String(200), nullable=False)  # Nom de l'entrepôt
    type = Column(String(50), default='Standard')  # Principal, POS, Standard
    description = Column(Text)  # Description de l'entrepôt
    address = Column(Text)  # Adresse
    contact_person = Column(String(100))  # Responsable
    contact_phone = Column(String(20))  # Téléphone
    contact_email = Column(String(150))  # Email
    is_default = Column(Boolean, default=False)  # Entrepôt par défaut
    is_active = Column(Boolean, default=True)  # Actif/Inactif
    capacity_limit = Column(Numeric(15, 2))  # Limite de capacité (optionnel)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relations
    products = relationship("StockProduitEntrepot", back_populates="warehouse")
    movements = relationship("StockMovement", foreign_keys="StockMovement.warehouse_id", back_populates="warehouse")
    received_movements = relationship("StockMovement", foreign_keys="StockMovement.destination_warehouse_id")


class StockConfig(Base):
    """Table de configuration du module stock"""
    __tablename__ = 'stock_config'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    entreprise_id = Column(Integer, nullable=False)  # Référence à l'entreprise
    key = Column(String(100), nullable=False)  # Clé de configuration
    value = Column(Text)  # Valeur de configuration
    description = Column(Text)  # Description de la configuration
    category = Column(String(50), default='general')  # Catégorie (general, alerts, reports, etc.)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())


class StockProduitEntrepot(Base):
    """Table de liaison produits-entrepôts avec stock"""
    __tablename__ = 'stock_produits_entrepot'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, nullable=False)  # Référence au produit
    warehouse_id = Column(Integer, ForeignKey('stock_warehouses.id'), nullable=False)  # Référence à l'entrepôt
    quantity = Column(Numeric(15, 3), default=0.0)  # Quantité en stock
    reserved_quantity = Column(Numeric(15, 3), default=0.0)  # Quantité réservée
    unit_cost = Column(Numeric(15, 2), default=0.0)  # Coût unitaire moyen
    total_cost = Column(Numeric(15, 2), default=0.0)  # Coût total (quantity * unit_cost)
    min_stock_level = Column(Numeric(15, 3), default=0.0)  # Seuil minimum de stock
    last_movement_date = Column(DateTime)  # Date du dernier mouvement
    location = Column(String(100))  # Emplacement dans l'entrepôt (optionnel)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relations
    warehouse = relationship("StockWarehouse", back_populates="products")
    movements = relationship("StockMovement", back_populates="product_warehouse")


class StockMovement(Base):
    """Table des mouvements de stock - Architecture simplifiée"""
    __tablename__ = 'stock_mouvements'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, nullable=False)  # Référence au produit
    warehouse_id = Column(Integer, ForeignKey('stock_warehouses.id'), nullable=True)  # Entrepôt source
    product_warehouse_id = Column(Integer, ForeignKey('stock_produits_entrepot.id'))  # Référence à la liaison produit-entrepôt
    movement_type = Column(String(50), nullable=False)  # ENTREE, SORTIE, TRANSFERT, AJUSTEMENT, INVENTAIRE
    quantity = Column(Numeric(15, 3), nullable=False)  # Quantité (+ ou -)
    unit_cost = Column(Numeric(15, 2), default=0.0)  # Coût unitaire
    total_cost = Column(Numeric(15, 2), default=0.0)  # Coût total
    
    # Informations de transfert (si applicable)
    destination_warehouse_id = Column(Integer, ForeignKey('stock_warehouses.id'))  # Entrepôt destination (pour transferts)
    
    # Métadonnées
    reference = Column(String(100))  # Référence externe (bon de livraison, commande, etc.)
    description = Column(Text)  # Description du mouvement
    batch_number = Column(String(50))  # Numéro de lot (optionnel)
    expiry_date = Column(DateTime)  # Date d'expiration (optionnel)
    
    # Traçabilité
    user_id = Column(Integer)  # Utilisateur qui a effectué le mouvement
    user_name = Column(String(100))  # Nom de l'utilisateur
    session_id = Column(String(100))  # ID de session pour grouper les mouvements
    
    # Dates
    movement_date = Column(DateTime, default=func.current_timestamp())  # Date du mouvement
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relations
    warehouse = relationship("StockWarehouse", foreign_keys=[warehouse_id], back_populates="movements")
    destination_warehouse = relationship("StockWarehouse", foreign_keys=[destination_warehouse_id], back_populates="received_movements")
    product_warehouse = relationship("StockProduitEntrepot", back_populates="movements")


class StockInventaire(Base):
    """Table des sessions d'inventaire"""
    __tablename__ = 'stock_inventaire'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    entreprise_id = Column(Integer, nullable=False)  # Référence à l'entreprise
    reference = Column(String(100), unique=True, nullable=False)  # Référence unique (INV-YYYYMMDDHHMMSS)
    session_name = Column(String(200), nullable=False)  # Nom de la session
    warehouse_id = Column(Integer, ForeignKey('stock_warehouses.id'), nullable=False)  # Entrepôt concerné
    inventory_type = Column(String(50), default='Complet')  # Complet, Partiel, Contrôle, Urgent
    status = Column(String(20), default='DRAFT')  # DRAFT, IN_PROGRESS, COMPLETED, CANCELLED
    scheduled_date = Column(DateTime)  # Date prévue
    started_date = Column(DateTime)  # Date de début réel
    completed_date = Column(DateTime)  # Date de fin
    notes = Column(Text)  # Notes générales
    
    # Métadonnées
    total_items = Column(Integer, default=0)  # Nombre total d'articles à compter
    counted_items = Column(Integer, default=0)  # Nombre d'articles comptés
    total_discrepancies = Column(Integer, default=0)  # Nombre d'écarts
    total_variance_value = Column(Numeric(15, 2), default=0.0)  # Valeur totale des écarts
    
    # Options
    include_zero_stock = Column(Boolean, default=True)  # Inclure produits à stock zéro
    auto_freeze_stock = Column(Boolean, default=False)  # Geler mouvements pendant inventaire
    send_notifications = Column(Boolean, default=True)  # Envoyer notifications
    
    # Traçabilité
    created_by = Column(Integer)  # Utilisateur créateur
    created_by_name = Column(String(100))
    completed_by = Column(Integer)  # Utilisateur finalisateur
    completed_by_name = Column(String(100))
    
    # Dates
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relations
    warehouse = relationship("StockWarehouse", backref="inventories")
    items = relationship("StockInventaireItem", back_populates="inventory", cascade="all, delete-orphan")


class StockInventaireItem(Base):
    """Table des éléments d'inventaire (comptages par produit)"""
    __tablename__ = 'stock_inventaire_item'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    inventory_id = Column(Integer, ForeignKey('stock_inventaire.id'), nullable=False)  # Session d'inventaire
    product_id = Column(Integer, nullable=False)  # Référence au produit
    product_name = Column(String(200))  # Nom du produit (snapshot)
    product_code = Column(String(50))  # Code du produit (snapshot)
    
    # Stocks
    system_stock = Column(Numeric(15, 3), default=0.0)  # Stock système au moment de l'inventaire
    counted_stock = Column(Numeric(15, 3), default=0.0)  # Stock compté
    variance = Column(Numeric(15, 3), default=0.0)  # Écart (counted - system)
    variance_value = Column(Numeric(15, 2), default=0.0)  # Valeur de l'écart à l'achat (variance * unit_cost)
    variance_value_sale = Column(Numeric(15, 2), default=0.0)  # Valeur de l'écart à la vente (variance * sale_price)
    
    # Informations produit
    unit_cost = Column(Numeric(15, 2), default=0.0)  # Coût unitaire au moment de l'inventaire
    location = Column(String(100))  # Emplacement dans l'entrepôt
    
    # Métadonnées
    notes = Column(Text)  # Notes du compteur
    counted_by = Column(Integer)  # Utilisateur qui a compté
    counted_by_name = Column(String(100))
    counted_at = Column(DateTime)  # Date/heure du comptage
    
    # Dates
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relations
    inventory = relationship("StockInventaire", back_populates="items")


# Export des modèles pour faciliter les imports
__all__ = [
    'StockWarehouse',
    'StockConfig', 
    'StockProduitEntrepot',
    'StockMovement',
    'StockInventaire',
    'StockInventaireItem'
]