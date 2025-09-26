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
from ayanna_erp.database.database_manager import Base


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
    name = Column(String(200), nullable=False)
    description = Column(Text)
    image = Column(Text)  # Chemin vers l'image du produit
    barcode = Column(String(100))  # Code-barres
    cost = Column(Numeric(15, 2), default=0.0)  # Coût d'achat
    price_unit = Column(Numeric(15, 2), default=0.0)  # Prix unitaire de vente
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