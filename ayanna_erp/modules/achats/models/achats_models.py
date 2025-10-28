"""
Modèles pour le module Achats
Gestion des fournisseurs, commandes, lignes de commande et dépenses
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text, Boolean, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ayanna_erp.database.base import Base
import enum


class EtatCommande(enum.Enum):
    """États possibles d'une commande"""
    ENCOURS = "encours"
    ANNULE = "annule" 
    VALIDE = "valide"
    RECEPTIONNE = "receptionne"


class StatutPaiement(enum.Enum):
    """Statut du paiement d'une commande (séparé du statut de la commande)"""
    NON_PAYE = "non_paye"
    PARTIEL = "partiel"
    PAYE = "paye"


class CoreFournisseur(Base):
    """Table des fournisseurs"""
    __tablename__ = 'core_fournisseurs'
    
    id = Column(Integer, primary_key=True)
    nom = Column(String(200), nullable=False)  # Raison sociale
    telephone = Column(String(20), nullable=True)
    adresse = Column(Text, nullable=True)
    email = Column(String(100), nullable=True)
    
    # Métadonnées
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relations
    commandes = relationship("AchatCommande", back_populates="fournisseur")

    def __repr__(self):
        return f"<CoreFournisseur(id={self.id}, nom='{self.nom}')>"


class AchatCommande(Base):
    """Table des commandes d'achat (bons de commande)"""
    __tablename__ = 'achat_commandes'
    
    id = Column(Integer, primary_key=True)
    numero = Column(String(50), nullable=False, unique=True)
    
    # Références
    fournisseur_id = Column(Integer, ForeignKey('core_fournisseurs.id'), nullable=True)
    entrepot_id = Column(Integer, ForeignKey('stock_warehouses.id'), nullable=False)
    utilisateur_id = Column(Integer, ForeignKey('core_users.id'), nullable=False)
    
    # Informations commande
    date_commande = Column(DateTime, default=func.now())
    remise_global = Column(DECIMAL(12, 2), default=0)
    montant_total = Column(DECIMAL(12, 2), nullable=False)
    etat = Column(Enum(EtatCommande), default=EtatCommande.ENCOURS)
    # Statut du paiement (non_paye/partiel/paye) distinct de l'état de la commande
    statut_paiement = Column(String(20), default=StatutPaiement.NON_PAYE.value, nullable=False)
    
    # Métadonnées
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relations
    fournisseur = relationship("CoreFournisseur", back_populates="commandes")
    lignes = relationship("AchatCommandeLigne", back_populates="commande", cascade="all, delete-orphan")
    depenses = relationship("AchatDepense", back_populates="commande", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AchatCommande(id={self.id}, numero='{self.numero}', etat='{self.etat.value}')>"

    def calculer_total(self):
        """Calcule le montant total de la commande"""
        total_lignes = sum(ligne.total_ligne for ligne in self.lignes)
        return total_lignes - self.remise_global

    @property
    def total_paye(self):
        """Somme des paiements enregistrés pour la commande"""
        try:
            return sum(d.montant for d in self.depenses) if self.depenses else 0
        except Exception:
            return 0


class AchatCommandeLigne(Base):
    """Table des lignes de commande d'achat"""
    __tablename__ = 'achat_commande_lignes'
    
    id = Column(Integer, primary_key=True)
    
    # Références
    bon_commande_id = Column(Integer, ForeignKey('achat_commandes.id'), nullable=False)
    produit_id = Column(Integer, ForeignKey('core_products.id'), nullable=False)
    
    # Détails ligne
    quantite = Column(DECIMAL(12, 2), nullable=False)
    prix_unitaire = Column(DECIMAL(12, 2), nullable=False)
    remise_ligne = Column(DECIMAL(12, 2), default=0)
    total_ligne = Column(DECIMAL(12, 2), nullable=False)
    
    # Relations
    commande = relationship("AchatCommande", back_populates="lignes")
    # Relation vers le produit (référence string pour éviter imports circulaires)
    product = relationship("CoreProduct", foreign_keys=[produit_id])
    
    def __repr__(self):
        return f"<AchatCommandeLigne(id={self.id}, produit_id={self.produit_id}, quantite={self.quantite})>"

    def calculer_total_ligne(self):
        """Calcule le total de la ligne"""
        return (self.quantite * self.prix_unitaire) - self.remise_ligne


class AchatDepense(Base):
    """Table des dépenses/paiements liés aux achats"""
    __tablename__ = 'achat_depenses'
    
    id = Column(Integer, primary_key=True)
    
    # Références
    bon_commande_id = Column(Integer, ForeignKey('achat_commandes.id'), nullable=False)
    
    # Détails paiement
    montant = Column(DECIMAL(12, 2), nullable=False)
    mode_paiement = Column(String(50), nullable=True)  # Espèces, Chèque, Virement, etc.
    description = Column(String(100), nullable=True)
    date_paiement = Column(DateTime, default=func.now())
    reference = Column(String(100), nullable=True)
    
    # Relations
    commande = relationship("AchatCommande", back_populates="depenses")
    
    def __repr__(self):
        return f"<AchatDepense(id={self.id}, montant={self.montant}, mode_paiement={self.mode_paiement})>"


__all__ = [
    'CoreFournisseur',
    'AchatCommande', 
    'AchatCommandeLigne',
    'AchatDepense',
    'EtatCommande'
]