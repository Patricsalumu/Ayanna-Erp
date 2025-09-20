"""
Modèles de comptabilité conforme au système SYSCOHADA
Adapté pour Ayanna ERP
"""
from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ForeignKey, Boolean, func, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from ayanna_erp.database.database_manager import Base
from datetime import datetime


class ComptaClasses(Base):
    """Modèle représentant une classe comptable selon le plan comptable SYSCOHADA"""
    __tablename__ = 'compta_classes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), nullable=False)  # Suppression de unique=True
    nom = Column(String(100), nullable=False)  # Nom court de la classe
    libelle = Column(String(255), nullable=False)  # Libellé complet
    type = Column(String(20), nullable=False)  # actif, passif, charge, produit
    document = Column(String(50), nullable=False)  # bilan ou resultat
    enterprise_id = Column(Integer, ForeignKey('core_enterprises.id'), nullable=False)
    actif = Column(Boolean, default=True)
    date_creation = Column(DateTime, default=func.now(), nullable=False)
    date_modification = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Contrainte d'unicité composite : un code de classe unique par entreprise
    __table_args__ = (
        UniqueConstraint('code', 'enterprise_id', name='uq_classe_code_enterprise'),
    )
    
    # Relations
    comptes = relationship("ComptaComptes", back_populates="classe_comptable")
    enterprise = relationship("Entreprise")
    
    def __repr__(self):
        return f"<ComptaClasses(code='{self.code}', nom='{self.nom}', type='{self.type}')>"


class ComptaComptes(Base):
    """Modèle représentant un compte comptable selon le plan comptable SYSCOHADA"""
    __tablename__ = 'compta_comptes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    numero = Column(String(20), nullable=False)
    nom = Column(String(255), nullable=False)
    libelle = Column(String(255), nullable=False)
    actif = Column(Boolean, default=True)  # Actif ou inactif
    classe_comptable_id = Column(Integer, ForeignKey('compta_classes.id'), nullable=False)
    date_creation = Column(DateTime, default=func.now(), nullable=False)
    date_modification = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relations
    classe_comptable = relationship("ComptaClasses", back_populates="comptes")
    ecritures = relationship("ComptaEcritures", back_populates="compte_comptable")
    
    def __repr__(self):
        return f"<ComptaComptes(numero='{self.numero}', nom='{self.nom}')>"


class ComptaJournaux(Base):
    """Modèle représentant un journal comptable"""
    __tablename__ = 'compta_journaux'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date_operation = Column(DateTime, nullable=False, default=datetime.utcnow)
    libelle = Column(String(255), nullable=False)
    montant = Column(Numeric(15, 2), nullable=False)
    type_operation = Column(String(20), nullable=False)  # entree, sortie, transfert
    reference = Column(String(100))  # Référence externe (facture, reçu, etc.)
    description = Column(Text)  # Description détaillée
    enterprise_id = Column(Integer, ForeignKey('core_enterprises.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('core_users.id'), nullable=False)
    date_creation = Column(DateTime, default=func.now(), nullable=False)
    date_modification = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relations
    enterprise = relationship("Entreprise")
    user = relationship("User")
    ecritures = relationship("ComptaEcritures", back_populates="journal")
    
    def __repr__(self):
        return f"<ComptaJournaux(libelle='{self.libelle}', montant={self.montant})>"


class ComptaEcritures(Base):
    """Modèle représentant une écriture comptable"""
    __tablename__ = 'compta_ecritures'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    journal_id = Column(Integer, ForeignKey('compta_journaux.id'), nullable=False)
    compte_comptable_id = Column(Integer, ForeignKey('compta_comptes.id'), nullable=False)
    debit = Column(Numeric(15, 2), default=0)
    credit = Column(Numeric(15, 2), default=0)
    ordre = Column(Integer, nullable=False)  # 1 pour débit, 2 pour crédit
    libelle = Column(String(255))  # Libellé spécifique à cette écriture
    date_creation = Column(DateTime, default=func.now(), nullable=False)
    
    # Relations
    journal = relationship("ComptaJournaux", back_populates="ecritures")
    compte_comptable = relationship("ComptaComptes", back_populates="ecritures")
    
    def __repr__(self):
        return f"<ComptaEcritures(journal_id={self.journal_id}, compte={self.compte_comptable_id}, debit={self.debit}, credit={self.credit})>"


class ComptaConfig(Base):
    """Configuration comptable par point de vente"""
    __tablename__ = 'compta_config'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    enterprise_id = Column(Integer, ForeignKey('core_enterprises.id'), nullable=False)
    pos_id = Column(Integer, ForeignKey('core_pos_points.id'), nullable=False)  # Point de vente
    compte_caisse_id = Column(Integer, ForeignKey('compta_comptes.id'), nullable=True)   # Compte caisse (classe 5)
    compte_banque_id = Column(Integer, ForeignKey('compta_comptes.id'), nullable=True)   # Compte banque (classe 5)
    compte_client_id = Column(Integer, ForeignKey('compta_comptes.id'), nullable=True)   # Compte client (classe 4)
    compte_fournisseur_id = Column(Integer, ForeignKey('compta_comptes.id'), nullable=True)  # Compte fournisseur (classe 4)
    compte_vente_id = Column(Integer, ForeignKey('compta_comptes.id'), nullable=True)    # Compte vente (classe 7)
    compte_achat_id = Column(Integer, ForeignKey('compta_comptes.id'), nullable=True)    # Compte achat (classe 6)
    compte_tva_id = Column(Integer, ForeignKey('compta_comptes.id'), nullable=True)      # Compte TVA collectée (classe 4)
    compte_remise_id = Column(Integer, ForeignKey('compta_comptes.id'), nullable=True)   # Compte remises accordées (classe 7)
    date_creation = Column(DateTime, default=func.now(), nullable=False)
    date_modification = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Contrainte d'unicité : un seul config par point de vente
    __table_args__ = (
        Index('idx_pos_config', 'pos_id', unique=True),
    )
    
    # Relations
    enterprise = relationship("Entreprise")
    # pos = relationship("POS")  # Relation vers la table POS (à décommenter quand le modèle POS sera disponible)
    compte_caisse = relationship("ComptaComptes", foreign_keys=[compte_caisse_id])
    compte_banque = relationship("ComptaComptes", foreign_keys=[compte_banque_id])
    compte_client = relationship("ComptaComptes", foreign_keys=[compte_client_id])
    compte_fournisseur = relationship("ComptaComptes", foreign_keys=[compte_fournisseur_id])
    compte_vente = relationship("ComptaComptes", foreign_keys=[compte_vente_id])
    compte_achat = relationship("ComptaComptes", foreign_keys=[compte_achat_id])
    compte_tva = relationship("ComptaComptes", foreign_keys=[compte_tva_id])
    compte_remise = relationship("ComptaComptes", foreign_keys=[compte_remise_id])
    
    def __repr__(self):
        return f"<ComptaConfig(enterprise_id={self.enterprise_id}, pos_id={self.pos_id})>"
