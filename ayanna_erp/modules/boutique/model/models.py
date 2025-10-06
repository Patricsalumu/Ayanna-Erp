"""
Modèles de données pour le module Boutique
Architecture basée sur le système de panier (au lieu de réservation)
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


class ShopClient(Base):
    """Table des clients pour la boutique"""
    __tablename__ = 'shop_clients'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pos_id = Column(Integer, nullable=False)  # Référence au POS
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    telephone = Column(String(20), nullable=False)
    email = Column(String(150))
    adresse = Column(Text)
    ville = Column(String(100))
    code_postal = Column(String(10))
    date_naissance = Column(DateTime)
    type_client = Column(String(50), default='Particulier')  # Particulier, Entreprise
    credit_limit = Column(Numeric(15, 2), default=0.0)  # Limite de crédit
    balance = Column(Numeric(15, 2), default=0.0)  # Solde du compte client
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relations
    paniers = relationship("ShopPanier", back_populates="client")


class ShopCategory(Base):
    """Table des catégories de produits"""
    __tablename__ = 'shop_categories'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pos_id = Column(Integer, nullable=False)  # Référence au POS
    name = Column(String(100), nullable=False)  # Nom de la catégorie
    description = Column(Text)  # Description de la catégorie
    image = Column(Text)  # Image de la catégorie (optionnelle)
    color = Column(String(20))  # Couleur pour l'affichage (hex code)
    order_display = Column(Integer, default=0)  # Ordre d'affichage
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relations
    products = relationship("ShopProduct", back_populates="category_rel")


class ShopProduct(Base):
    """Table des produits de la boutique"""
    __tablename__ = 'shop_products'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pos_id = Column(Integer, nullable=False)  # Référence au POS
    category_id = Column(Integer, ForeignKey('shop_categories.id'))  # Référence à la catégorie
    code = Column(String(50), unique=True)  # Code unique du produit
    name = Column(String(200), nullable=False)
    description = Column(Text)
    image = Column(Text)  # Chemin vers l'image du produit
    barcode = Column(String(100))  # Code-barres
    cost = Column(Numeric(15, 2), default=0.0)  # Coût d'achat
    cost_price = Column(Numeric(15, 2), default=0.0)  # Alias pour compatibilité (même que cost)
    price_unit = Column(Numeric(15, 2), default=0.0)  # Prix unitaire de vente
    sale_price = Column(Numeric(15, 2), default=0.0)  # Alias pour compatibilité (même que price_unit)
    stock_quantity = Column(Numeric(15, 2), default=0.0)  # Quantité en stock
    stock_min = Column(Numeric(15, 2), default=0.0)  # Seuil minimum de stock
    unit = Column(String(50), default='pièce')  # Unité de mesure
    account_id = Column(Integer)  # Compte comptable
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relations
    category_rel = relationship("ShopCategory", back_populates="products")
    panier_products = relationship("ShopPanierProduct", back_populates="product")
    stock_movements = relationship("ShopStock", back_populates="product")


class ShopService(Base):
    """Table des services de la boutique"""
    __tablename__ = 'shop_services'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pos_id = Column(Integer, nullable=False)  # Référence au POS
    name = Column(String(200), nullable=False)
    description = Column(Text)
    image = Column(Text)  # Image du service
    cost = Column(Numeric(15, 2), default=0.0)  # Coût du service
    price = Column(Numeric(15, 2), default=0.0)  # Prix de vente
    account_id = Column(Integer)  # Compte comptable
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relations
    panier_services = relationship("ShopPanierService", back_populates="service")


class ShopPanier(Base):
    """Table des paniers (équivalent des réservations en Salle de Fête)"""
    __tablename__ = 'shop_paniers'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pos_id = Column(Integer, nullable=False)  # Référence au POS
    client_id = Column(Integer, ForeignKey('shop_clients.id'))  # Client optionnel
    numero_commande = Column(String(50), unique=True)  # Numéro de commande auto-généré
    status = Column(String(50), default='en_cours')  # en_cours, validé, payé, annulé
    
    # Totaux
    subtotal = Column(Numeric(15, 2), default=0.0)  # Sous-total HT
    remise_percent = Column(Numeric(5, 2), default=0.0)  # Remise en %
    remise_amount = Column(Numeric(15, 2), default=0.0)  # Montant de la remise
    total_final = Column(Numeric(15, 2), default=0.0)  # Total final à payer
    
    # Informations de validation
    validated_at = Column(DateTime)  # Date de validation
    validated_by = Column(String(100))  # Utilisateur qui a validé
    
    # Dates
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relations
    client = relationship("ShopClient", back_populates="paniers")
    products = relationship("ShopPanierProduct", back_populates="panier", cascade="all, delete-orphan")
    services = relationship("ShopPanierService", back_populates="panier", cascade="all, delete-orphan")
    payments = relationship("ShopPayment", back_populates="panier", cascade="all, delete-orphan")


class ShopPanierProduct(Base):
    """Table pivot : Produits dans un panier"""
    __tablename__ = 'shop_paniers_products'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    panier_id = Column(Integer, ForeignKey('shop_paniers.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('shop_products.id'), nullable=False)
    quantity = Column(Numeric(15, 2), nullable=False)
    price_unit = Column(Numeric(15, 2), nullable=False)  # Prix au moment de l'ajout
    total_price = Column(Numeric(15, 2), nullable=False)  # quantity * price_unit
    
    # Relations
    panier = relationship("ShopPanier", back_populates="products")
    product = relationship("ShopProduct", back_populates="panier_products")


class ShopPanierService(Base):
    """Table pivot : Services dans un panier"""
    __tablename__ = 'shop_paniers_services'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    panier_id = Column(Integer, ForeignKey('shop_paniers.id'), nullable=False)
    service_id = Column(Integer, ForeignKey('shop_services.id'), nullable=False)
    quantity = Column(Numeric(15, 2), default=1.0)  # Quantité de services
    price_unit = Column(Numeric(15, 2), nullable=False)  # Prix au moment de l'ajout
    total_price = Column(Numeric(15, 2), nullable=False)  # quantity * price_unit
    
    # Relations
    panier = relationship("ShopPanier", back_populates="services")
    service = relationship("ShopService", back_populates="panier_services")


class ShopPayment(Base):
    """Table des paiements pour les paniers"""
    __tablename__ = 'shop_payments'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    panier_id = Column(Integer, ForeignKey('shop_paniers.id'), nullable=False)
    payment_method = Column(String(50), nullable=False)  # especes, mobile_money, banque, compte_client
    amount = Column(Numeric(15, 2), nullable=False)
    reference = Column(String(100))  # Référence de transaction
    payment_date = Column(DateTime, default=func.current_timestamp())
    caisse_debit_account_id = Column(Integer)  # Compte de caisse de débit selon méthode
    notes = Column(Text)
    
    # Relations
    panier = relationship("ShopPanier", back_populates="payments")


class ShopStock(Base):
    """Table des mouvements de stock"""
    __tablename__ = 'shop_stock'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pos_id = Column(Integer, nullable=False)  # Référence au POS
    product_id = Column(Integer, ForeignKey('shop_products.id'), nullable=False)
    movement_type = Column(String(50), nullable=False)  # entree, sortie, ajustement, vente
    quantity = Column(Numeric(15, 2), nullable=False)  # Quantité (positive pour entrée, négative pour sortie)
    unit_cost = Column(Numeric(15, 2), default=0.0)  # Coût unitaire
    total_cost = Column(Numeric(15, 2), default=0.0)  # Coût total du mouvement
    reference = Column(String(100))  # Référence (numéro panier, bon de livraison, etc.)
    reason = Column(String(200))  # Motif du mouvement
    movement_date = Column(DateTime, default=func.current_timestamp())
    user_name = Column(String(100))  # Utilisateur qui a fait le mouvement
    
    # Relations
    product = relationship("ShopProduct", back_populates="stock_movements")


class ShopExpense(Base):
    """Table des dépenses de la boutique"""
    __tablename__ = 'shop_expenses'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pos_id = Column(Integer, nullable=False)  # Référence au POS
    expense_type = Column(String(100), nullable=False)  # achat_stock, frais_generaux, salaire, etc.
    description = Column(String(200), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)  # especes, banque, mobile_money
    supplier_name = Column(String(200))  # Nom du fournisseur
    invoice_number = Column(String(100))  # Numéro de facture
    expense_date = Column(DateTime, default=func.current_timestamp())
    account_id = Column(Integer)  # Compte comptable de charge
    caisse_credit_account_id = Column(Integer)  # Compte de caisse de crédit
    notes = Column(Text)
    user_name = Column(String(100))  # Utilisateur qui a saisi la dépense


class ShopComptesConfig(Base):
    """Configuration des comptes par méthode de paiement pour chaque POS boutique"""
    __tablename__ = 'shop_comptes_config'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pos_id = Column(Integer, nullable=False, unique=True)  # Un seul config par POS
    
    # Comptes de caisse pour les différents moyens de paiement (DÉBIT lors des ventes)
    caisse_especes_id = Column(Integer)  # Compte caisse espèces
    caisse_mobile_money_id = Column(Integer)  # Compte caisse mobile money
    caisse_banque_id = Column(Integer)  # Compte caisse banque
    
    # Comptes pour les ventes
    compte_vente_produits_id = Column(Integer)  # Compte produit de vente de marchandises
    compte_vente_services_id = Column(Integer)  # Compte produit de vente de services
    compte_remise_id = Column(Integer)  # Compte de remise accordée
    
    # Comptes pour les achats et stocks
    compte_stock_id = Column(Integer)  # Compte de stock
    compte_achat_id = Column(Integer)  # Compte d'achat de marchandises
    
    # Comptes clients
    compte_client_id = Column(Integer)  # Compte client (pour ventes à crédit)
    
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())


# ==========================================
# SYSTÈME DE STOCK AVANCÉ - MULTI-ENTREPÔTS
# ==========================================

class ShopWarehouse(Base):
    """Table des entrepôts/magasins"""
    __tablename__ = 'shop_warehouses'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pos_id = Column(Integer, nullable=False)  # Référence au POS
    code = Column(String(20), nullable=False, unique=True)  # Code unique de l'entrepôt
    name = Column(String(200), nullable=False)  # Nom de l'entrepôt
    type = Column(String(50))  # shop, storage, transit, damaged
    description = Column(Text)  # Description de l'entrepôt
    address = Column(Text)  # Adresse de l'entrepôt
    contact_person = Column(String(100))  # Responsable
    contact_phone = Column(String(20))  # Téléphone
    contact_email = Column(String(150))  # Email
    is_default = Column(Boolean, default=False)  # Entrepôt par défaut
    is_active = Column(Boolean, default=True)  # Entrepôt actif
    capacity_limit = Column(Numeric(15, 2))  # Capacité maximale
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relations
    warehouse_stocks = relationship("ShopWarehouseStock", back_populates="warehouse", cascade="all, delete-orphan")
    stock_movements = relationship("ShopStockMovementNew", back_populates="warehouse", cascade="all, delete-orphan")
    source_transfers = relationship("ShopStockTransfer", back_populates="source_warehouse", foreign_keys="ShopStockTransfer.source_warehouse_id")
    destination_transfers = relationship("ShopStockTransfer", back_populates="destination_warehouse", foreign_keys="ShopStockTransfer.destination_warehouse_id")
    inventories = relationship("ShopInventory", back_populates="warehouse", cascade="all, delete-orphan")
    stock_alerts = relationship("ShopStockAlert", back_populates="warehouse", cascade="all, delete-orphan")


class ShopWarehouseStock(Base):
    """Table des stocks par entrepôt et produit"""
    __tablename__ = 'shop_warehouse_stocks'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column(Integer, ForeignKey('shop_warehouses.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('shop_products.id'), nullable=False)
    quantity_available = Column(Numeric(15, 2), default=0.0)  # Quantité disponible
    quantity = Column(Numeric(15, 2), default=0.0)  # Alias pour compatibilité (même que quantity_available)
    quantity_reserved = Column(Numeric(15, 2), default=0.0)  # Quantité réservée
    reserved_quantity = Column(Numeric(15, 2), default=0.0)  # Alias pour compatibilité
    quantity_in_transit = Column(Numeric(15, 2), default=0.0)  # Quantité en transit
    min_stock_level = Column(Numeric(15, 2), default=0.0)  # Niveau minimum de stock
    minimum_stock = Column(Numeric(15, 2), default=0.0)  # Alias pour compatibilité
    max_stock_level = Column(Numeric(15, 2), default=0.0)  # Niveau maximum de stock
    maximum_stock = Column(Numeric(15, 2), default=0.0)  # Alias pour compatibilité
    reorder_point = Column(Numeric(15, 2), default=0.0)  # Point de réapprovisionnement
    last_movement_date = Column(DateTime)  # Date du dernier mouvement
    last_inventory_date = Column(DateTime)  # Date du dernier inventaire
    updated_at = Column(DateTime, default=func.current_timestamp())  # Date de mise à jour
    average_cost = Column(Numeric(15, 2), default=0.0)  # Coût moyen pondéré
    unit_cost = Column(Numeric(15, 2), default=0.0)  # Alias pour compatibilité
    
    # Relations
    warehouse = relationship("ShopWarehouse", back_populates="warehouse_stocks")
    product = relationship("ShopProduct")
    stock_movements = relationship("ShopStockMovementNew", back_populates="warehouse_stock")


class ShopStockMovementNew(Base):
    """Table des mouvements de stock avancés"""
    __tablename__ = 'shop_stock_movements_new'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column(Integer, ForeignKey('shop_warehouses.id'), nullable=False)
    warehouse_stock_id = Column(Integer, ForeignKey('shop_warehouse_stocks.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('shop_products.id'), nullable=False)
    movement_type = Column(String(50), nullable=False)  # purchase, sale, transfer_in, transfer_out, adjustment, loss
    direction = Column(String(10), nullable=False)  # in, out
    quantity = Column(Numeric(15, 2), nullable=False)  # Quantité du mouvement
    unit_cost = Column(Numeric(15, 2))  # Coût unitaire
    total_cost = Column(Numeric(15, 2))  # Coût total
    quantity_before = Column(Numeric(15, 2), default=0.0)  # Quantité avant mouvement
    quantity_after = Column(Numeric(15, 2), default=0.0)  # Quantité après mouvement
    reference_type = Column(String(30))  # invoice, order, transfer, adjustment
    reference_number = Column(String(100))  # Numéro de référence
    batch_number = Column(String(50))  # Numéro de lot
    expiry_date = Column(DateTime)  # Date d'expiration
    supplier_id = Column(Integer)  # ID du fournisseur
    customer_id = Column(Integer)  # ID du client
    notes = Column(Text)  # Notes du mouvement
    movement_date = Column(DateTime, default=func.current_timestamp())
    created_by = Column(String(100))  # Utilisateur qui a créé le mouvement
    approved_by = Column(String(100))  # Utilisateur qui a approuvé
    is_approved = Column(Boolean, default=False)  # Mouvement approuvé
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relations
    warehouse = relationship("ShopWarehouse", back_populates="stock_movements")
    warehouse_stock = relationship("ShopWarehouseStock", back_populates="stock_movements")
    product = relationship("ShopProduct")


class ShopStockTransfer(Base):
    """Table des transferts entre entrepôts"""
    __tablename__ = 'shop_stock_transfers'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    transfer_number = Column(String(50), nullable=False, unique=True)  # Numéro unique de transfert
    source_warehouse_id = Column(Integer, ForeignKey('shop_warehouses.id'), nullable=False)
    destination_warehouse_id = Column(Integer, ForeignKey('shop_warehouses.id'), nullable=False)
    status = Column(String(20), default='pending')  # pending, approved, shipped, received, cancelled
    priority = Column(String(20), default='normal')  # low, normal, high, urgent
    transfer_type = Column(String(30), default='regular')  # regular, emergency, return
    requested_by = Column(String(100))  # Utilisateur qui a demandé
    requested_date = Column(DateTime, default=func.current_timestamp())
    expected_date = Column(DateTime)  # Date prévue pour le transfert
    approved_by = Column(String(100))  # Utilisateur qui a approuvé
    approved_date = Column(DateTime)
    shipped_by = Column(String(100))  # Utilisateur qui a expédié
    shipped_date = Column(DateTime)
    received_by = Column(String(100))  # Utilisateur qui a reçu
    received_date = Column(DateTime)
    notes = Column(Text)  # Notes du transfert
    total_items = Column(Integer, default=0)  # Nombre total d'articles
    total_quantity = Column(Numeric(15, 2), default=0.0)  # Quantité totale
    total_cost = Column(Numeric(15, 2), default=0.0)  # Coût total
    created_at = Column(DateTime, default=func.current_timestamp())  # Date de création
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())  # Date de mise à jour
    
    # Relations
    source_warehouse = relationship("ShopWarehouse", back_populates="source_transfers", foreign_keys=[source_warehouse_id])
    destination_warehouse = relationship("ShopWarehouse", back_populates="destination_transfers", foreign_keys=[destination_warehouse_id])
    transfer_items = relationship("ShopStockTransferItem", back_populates="transfer", cascade="all, delete-orphan")


class ShopStockTransferItem(Base):
    """Table des articles dans un transfert"""
    __tablename__ = 'shop_stock_transfer_items'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    transfer_id = Column(Integer, ForeignKey('shop_stock_transfers.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('shop_products.id'), nullable=False)
    quantity_requested = Column(Numeric(15, 2), nullable=False)  # Quantité demandée
    quantity_shipped = Column(Numeric(15, 2), default=0.0)  # Quantité expédiée
    quantity_received = Column(Numeric(15, 2), default=0.0)  # Quantité reçue
    unit_cost = Column(Numeric(15, 2))  # Coût unitaire
    total_cost = Column(Numeric(15, 2))  # Coût total
    lot_number = Column(String(50))  # Numéro de lot
    expiry_date = Column(DateTime)  # Date d'expiration
    notes = Column(Text)  # Notes de l'article
    
    # Relations
    transfer = relationship("ShopStockTransfer", back_populates="transfer_items")
    product = relationship("ShopProduct")


class ShopInventory(Base):
    """Table des inventaires physiques"""
    __tablename__ = 'shop_inventories'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    inventory_number = Column(String(50), nullable=False, unique=True)  # Numéro unique d'inventaire
    warehouse_id = Column(Integer, ForeignKey('shop_warehouses.id'), nullable=False)
    inventory_date = Column(DateTime, nullable=False)  # Date de l'inventaire
    status = Column(String(20), default='planned')  # planned, in_progress, completed, cancelled
    inventory_type = Column(String(30), default='full')  # full, partial, cycle
    reason = Column(String(200))  # Raison de l'inventaire
    started_by = Column(String(100))  # Utilisateur qui a commencé
    started_date = Column(DateTime)
    completed_by = Column(String(100))  # Utilisateur qui a terminé
    completed_date = Column(DateTime)
    validated_by = Column(String(100))  # Utilisateur qui a validé
    validated_date = Column(DateTime)
    notes = Column(Text)  # Notes de l'inventaire
    total_items_counted = Column(Integer, default=0)  # Nombre d'articles comptés
    total_discrepancies = Column(Integer, default=0)  # Nombre de discordances
    total_variance_cost = Column(Numeric(15, 2), default=0.0)  # Coût total des écarts
    
    # Relations
    warehouse = relationship("ShopWarehouse", back_populates="inventories")
    inventory_items = relationship("ShopInventoryItem", back_populates="inventory", cascade="all, delete-orphan")


class ShopInventoryItem(Base):
    """Table des articles inventoriés"""
    __tablename__ = 'shop_inventory_items'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    inventory_id = Column(Integer, ForeignKey('shop_inventories.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('shop_products.id'), nullable=False)
    expected_quantity = Column(Numeric(15, 2), default=0.0)  # Quantité attendue (système)
    counted_quantity = Column(Numeric(15, 2), default=0.0)  # Quantité comptée
    variance_quantity = Column(Numeric(15, 2), default=0.0)  # Écart de quantité
    unit_cost = Column(Numeric(15, 2))  # Coût unitaire
    variance_cost = Column(Numeric(15, 2), default=0.0)  # Coût de l'écart
    lot_number = Column(String(50))  # Numéro de lot
    expiry_date = Column(DateTime)  # Date d'expiration
    counted_by = Column(String(100))  # Utilisateur qui a compté
    counted_date = Column(DateTime)
    verified_by = Column(String(100))  # Utilisateur qui a vérifié
    verified_date = Column(DateTime)
    notes = Column(Text)  # Notes de l'article
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
    alert_type = Column(String(30), nullable=False)  # low_stock, out_of_stock, overstock, expiry
    current_quantity = Column(Numeric(15, 2))  # Quantité actuelle
    threshold_quantity = Column(Numeric(15, 2))  # Seuil d'alerte
    alert_level = Column(String(20), default='warning')  # info, warning, critical
    message = Column(String(500))  # Message d'alerte
    is_acknowledged = Column(Boolean, default=False)  # Alerte acquittée
    acknowledged_by = Column(String(100))  # Utilisateur qui a acquitté
    acknowledged_date = Column(DateTime)  # Date d'acquittement
    created_date = Column(DateTime, default=func.current_timestamp())
    resolved_date = Column(DateTime)  # Date de résolution
    
    # Relations
    warehouse = relationship("ShopWarehouse", back_populates="stock_alerts")
    product = relationship("ShopProduct")


class ShopStockMovement(Base):
    """Table des mouvements de stock (compatible avec module stock)"""
    __tablename__ = 'shop_stock_movements'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column(Integer, ForeignKey('shop_warehouses.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('shop_products.id'), nullable=False)
    movement_type = Column(String(50), nullable=False)  # PURCHASE, SALE, TRANSFER_IN, TRANSFER_OUT, ADJUSTMENT
    direction = Column(String(10), nullable=False)  # IN, OUT
    quantity = Column(Numeric(15, 2), nullable=False)  # Quantité du mouvement
    unit_cost = Column(Numeric(15, 2), default=0.0)  # Coût unitaire
    total_cost = Column(Numeric(15, 2), default=0.0)  # Coût total
    quantity_before = Column(Numeric(15, 2), default=0.0)  # Quantité avant mouvement
    quantity_after = Column(Numeric(15, 2), default=0.0)  # Quantité après mouvement
    reference_type = Column(String(30))  # invoice, order, transfer, adjustment
    reference_number = Column(String(100))  # Numéro de référence
    batch_number = Column(String(50))  # Numéro de lot
    expiry_date = Column(DateTime)  # Date d'expiration
    supplier_id = Column(Integer)  # ID du fournisseur
    customer_id = Column(Integer)  # ID du client
    notes = Column(Text)  # Notes du mouvement
    movement_date = Column(DateTime, default=func.current_timestamp())
    created_by = Column(String(100))  # Utilisateur qui a créé le mouvement
    approved_by = Column(String(100))  # Utilisateur qui a approuvé
    is_approved = Column(Boolean, default=True)  # Mouvement approuvé par défaut
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relations
    warehouse = relationship("ShopWarehouse")
    product = relationship("ShopProduct")