# -*- coding: utf-8 -*-
"""
Modèles de données pour le module Boutique
Utilise maintenant core_products (centralisé) au lieu de shop_products
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
    prenom = Column(String(100), nullable=True)  # Prénom optionnel
    telephone = Column(String(20), nullable=True)  # Téléphone optionnel
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
    """Table pivot : Produits dans un panier - UTILISE CORE_PRODUCTS"""
    __tablename__ = 'shop_paniers_products'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    panier_id = Column(Integer, ForeignKey('shop_paniers.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('core_products.id'), nullable=False)  # CHANGÉ: Référence vers core_products
    quantity = Column(Numeric(15, 2), nullable=False)
    price_unit = Column(Numeric(15, 2), nullable=False)  # Prix au moment de l'ajout
    total_price = Column(Numeric(15, 2), nullable=False)  # quantity * price_unit
    
    # Relations
    panier = relationship("ShopPanier", back_populates="products")
    # product sera défini dans core_products

class ShopPanierService(Base):
    """Table pivot : Services dans un panier"""
    __tablename__ = 'shop_paniers_services'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    panier_id = Column(Integer, ForeignKey('shop_paniers.id'), nullable=False)
    service_id = Column(Integer, ForeignKey('shop_services.id'), nullable=False)
    quantity = Column(Numeric(15, 2), default=1.0)
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
    payment_method = Column(String(50), nullable=False)  # especes, carte, cheque, virement
    amount = Column(Numeric(15, 2), nullable=False)
    payment_date = Column(DateTime, default=func.current_timestamp())
    reference = Column(String(100))  # Référence du paiement (numéro chèque, etc.)
    notes = Column(Text)
    
    # Relations
    panier = relationship("ShopPanier", back_populates="payments")

class ShopExpense(Base):
    """Table des dépenses de la boutique"""
    __tablename__ = 'shop_expenses'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pos_id = Column(Integer, nullable=False)
    description = Column(String(200), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    expense_date = Column(DateTime, default=func.current_timestamp())
    category = Column(String(50))  # materiel, personnel, maintenance, etc.
    payment_method = Column(String(50))  # especes, carte, cheque, virement
    reference = Column(String(100))  # Facture, bon de commande, etc.
    notes = Column(Text)
    created_at = Column(DateTime, default=func.current_timestamp())


class ShopComptesConfig(Base):
    """Configuration des comptes et méthodes de paiement"""
    __tablename__ = 'shop_comptes_config'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pos_id = Column(Integer, nullable=False)
    nom = Column(String(100), nullable=False)
    type_compte = Column(String(50), nullable=False)  # bank, cash, mobile, card
    numero_compte = Column(String(100))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.current_timestamp())












