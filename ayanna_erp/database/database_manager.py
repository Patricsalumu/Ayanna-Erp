"""
Gestionnaire de base de données pour Ayanna ERP
Utilise SQLAlchemy pour la gestion des modèles et des connexions
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import StaticPool
import bcrypt


Base = declarative_base()


class DatabaseManager:
    """Gestionnaire principal de la base de données"""
    
    def __init__(self, database_url=None):
        if database_url is None:
            database_url = "sqlite:///ayanna_erp.db"
        
        self.engine = create_engine(
            database_url,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
            echo=False
        )
        
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.session = None
    
    def get_session(self):
        """Obtenir une session de base de données"""
        if not self.session:
            self.session = self.SessionLocal()
        return self.session
    
    def close_session(self):
        """Fermer la session de base de données"""
        if self.session:
            self.session.close()
            self.session = None
    
    def initialize_database(self):
        """Initialiser la base de données avec les tables et données par défaut"""
        try:
            # Créer toutes les tables de base (sans les modules)
            Base.metadata.create_all(bind=self.engine)
            
            # Insérer les données par défaut
            self._insert_default_data()
            
            return True
        except Exception as e:
            print(f"Erreur lors de l'initialisation de la base de données: {e}")
            return False
    
    def _insert_default_data(self):
        """Insérer les données par défaut"""
        session = self.get_session()
        
        try:
            # Créer une entreprise par défaut si elle n'existe pas
            default_enterprise = session.query(Entreprise).first()
            if not default_enterprise:
                default_enterprise = Entreprise(
                    name="Ayanna Solutions",
                    address="Adresse par défaut",
                    phone="+243 000 000 000",
                    email="contact@ayanna.com",
                    currency="USD",
                    slogan="Excellence en gestion d'entreprise"
                )
                session.add(default_enterprise)
                session.flush()  # Pour obtenir l'ID
            
            # Créer un utilisateur administrateur par défaut
            admin_user = session.query(User).filter_by(email="admin@ayanna.com").first()
            if not admin_user:
                admin_user = User(
                    enterprise_id=default_enterprise.id,
                    name="Super Administrateur",
                    email="admin@ayanna.com",
                    role="super_admin"
                )
                admin_user.set_password("admin123")
                session.add(admin_user)
                print("✅ Utilisateur administrateur créé:")
                print("   Email: admin@ayanna.com")
                print("   Mot de passe: admin123")
                print("   Rôle: super_admin")
            
            # Insérer les modules par défaut
            modules_default = [
                {"name": "SalleFete", "description": "Gestion des salles de fête et événements"},
                {"name": "Boutique", "description": "Gestion de boutique générale"},
                {"name": "Pharmacie", "description": "Gestion de pharmacie"},
                {"name": "Restaurant", "description": "Gestion de restaurant et bar"},
                {"name": "Hotel", "description": "Gestion d'hôtel"},
                {"name": "Achats", "description": "Gestion des achats fournisseurs"},
                {"name": "Stock", "description": "Gestion des stocks et inventaires"},
                {"name": "Comptabilite", "description": "Comptabilité SYSCOHADA"}
            ]
            
            for module_data in modules_default:
                existing = session.query(Module).filter_by(name=module_data["name"]).first()
                if not existing:
                    module = Module(**module_data)
                    session.add(module)
            
            # S'assurer que les modules sont persistés avant de créer les POS
            session.flush()
            
            # Créer automatiquement des POS pour chaque module de l'entreprise par défaut
            self._create_pos_for_enterprise(session, default_enterprise.id)
            
            # Insérer les classes comptables SYSCOHADA par défaut
            classes_comptables_default = [
                {"code": "1", "nom": "COMPTES DE RESSOURCES DURABLES", "libelle": "Comptes de ressources durables", "type": "passif", "document": "bilan"},
                {"code": "2", "nom": "COMPTES D'ACTIF IMMOBILISE", "libelle": "Comptes d'actif immobilisé", "type": "actif", "document": "bilan"},
                {"code": "3", "nom": "COMPTES DE STOCKS", "libelle": "Comptes de stocks", "type": "actif", "document": "bilan"},
                {"code": "4", "nom": "COMPTES DE TIERS", "libelle": "Comptes de tiers", "type": "actif", "document": "bilan"},
                {"code": "5", "nom": "COMPTES DE TRESORERIE", "libelle": "Comptes de trésorerie", "type": "actif", "document": "bilan"},
                {"code": "6", "nom": "COMPTES DE CHARGES", "libelle": "Comptes de charges", "type": "charge", "document": "resultat"},
                {"code": "7", "nom": "COMPTES DE PRODUITS", "libelle": "Comptes de produits", "type": "produit", "document": "resultat"},
                {"code": "8", "nom": "COMPTES DES AUTRES CHARGES ET DES AUTRES PRODUITS", "libelle": "Autres charges et produits", "type": "charge", "document": "resultat"}
            ]
            
            for classe_data in classes_comptables_default:
                existing = session.query(ClasseComptable).filter_by(code=classe_data["code"]).first()
                if not existing:
                    classe = ClasseComptable(**classe_data)
                    session.add(classe)
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            print(f"Erreur lors de l'insertion des données par défaut: {e}")
        finally:
            session.close()
    
    def _create_pos_for_enterprise(self, session, enterprise_id):
        """Créer automatiquement tous les POS pour une entreprise"""
        try:
            # Récupérer tous les modules
            modules = session.query(Module).all()
            
            # Noms des POS par défaut pour chaque module
            pos_names = {
                "SalleFete": "POS Salle de Fête Principale",
                "Boutique": "POS Boutique Centrale", 
                "Pharmacie": "POS Pharmacie",
                "Restaurant": "POS Restaurant Principal",
                "Hotel": "POS Hôtel",
                "Achats": "POS Achats",
                "Stock": "POS Stock Central",
                "Comptabilite": "POS Comptabilité"
            }
            
            for module in modules:
                # Vérifier si un POS existe déjà pour ce module et cette entreprise
                existing_pos = session.query(POSPoint).filter_by(
                    enterprise_id=enterprise_id,
                    module_id=module.id
                ).first()
                
                if not existing_pos:
                    pos = POSPoint(
                        enterprise_id=enterprise_id,
                        module_id=module.id,
                        name=pos_names.get(module.name, f"POS {module.name}")
                    )
                    session.add(pos)
                    print(f"✅ POS créé: {pos.name} pour le module {module.name}")
            
            session.flush()  # S'assurer que les POS sont persistés
            
        except Exception as e:
            print(f"❌ Erreur lors de la création des POS: {e}")
            raise
    
    def create_pos_for_new_enterprise(self, enterprise_id):
        """Créer tous les POS pour une nouvelle entreprise (méthode publique)"""
        session = self.get_session()
        try:
            self._create_pos_for_enterprise(session, enterprise_id)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"❌ Erreur lors de la création des POS pour l'entreprise {enterprise_id}: {e}")
            return False
        finally:
            session.close()


# ====================================================
# MODÈLES DE BASE DE DONNÉES
# ====================================================

class Entreprise(Base):
    __tablename__ = "core_enterprises"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    address = Column(Text)
    phone = Column(String(50))
    email = Column(String(100))
    rccm = Column(String(100))
    id_nat = Column(String(100))
    logo = Column(Text)  # chemin vers le logo
    slogan = Column(Text)
    currency = Column(String(10), default='USD')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    users = relationship("User", back_populates="enterprise")
    partners = relationship("Partner", back_populates="enterprise")
    pos_points = relationship("POSPoint", back_populates="enterprise")


class User(Base):
    __tablename__ = "core_users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    enterprise_id = Column(Integer, ForeignKey('core_enterprises.id'), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    role = Column(String(50), default='admin')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    enterprise = relationship("Entreprise", back_populates="users")
    
    def set_password(self, password):
        """Hasher le mot de passe"""
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Vérifier le mot de passe"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))


class Partner(Base):
    __tablename__ = "core_partners"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    enterprise_id = Column(Integer, ForeignKey('core_enterprises.id'), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(100))
    phone = Column(String(50))
    address = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    enterprise = relationship("Entreprise", back_populates="partners")


class Module(Base):
    __tablename__ = "modules"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    pos_points = relationship("POSPoint", back_populates="module")


class POSPoint(Base):
    __tablename__ = "core_pos_points"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    enterprise_id = Column(Integer, ForeignKey('core_enterprises.id'), nullable=False)
    module_id = Column(Integer, ForeignKey('modules.id'), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    enterprise = relationship("Entreprise", back_populates="pos_points")
    module = relationship("Module", back_populates="pos_points")


class ClasseComptable(Base):
    __tablename__ = "classes_comptables"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10))
    nom = Column(String(100), nullable=False)
    libelle = Column(String(255), nullable=False)
    type = Column(String(20), nullable=False)  # actif, passif, charge, produit
    entreprise_id = Column(Integer, ForeignKey('core_enterprises.id'))
    document = Column(String(255))  # bilan ou resultat
    
    # Relations
    comptes = relationship("CompteComptable", back_populates="classe_comptable")


class CompteComptable(Base):
    __tablename__ = "comptes_comptables"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False)
    nom = Column(String(255), nullable=False)
    libelle = Column(String(255), nullable=False)
    classe_comptable_id = Column(Integer, ForeignKey('classes_comptables.id'), nullable=False)
    
    # Relations
    classe_comptable = relationship("ClasseComptable", back_populates="comptes")
    ecritures = relationship("EcritureComptable", back_populates="compte_comptable")


class JournalComptable(Base):
    __tablename__ = "journal_comptables"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    libelle = Column(String(255), nullable=False)
    montant = Column(Numeric(15, 2), nullable=False)
    type_operation = Column(String(20), nullable=False)  # paiement, depense, transfert
    entreprise_id = Column(Integer, ForeignKey('core_enterprises.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    ecritures = relationship("EcritureComptable", back_populates="journal")


class EcritureComptable(Base):
    __tablename__ = "ecritures_comptables"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    journal_id = Column(Integer, ForeignKey('journal_comptables.id'), nullable=False)
    compte_comptable_id = Column(Integer, ForeignKey('comptes_comptables.id'), nullable=False)
    debit = Column(Numeric(15, 2), default=0)
    credit = Column(Numeric(15, 2), default=0)
    ordre = Column(Integer, nullable=False)  # 1 pour débit, 2 pour crédit
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    journal = relationship("JournalComptable", back_populates="ecritures")
    compte_comptable = relationship("CompteComptable", back_populates="ecritures")


class PaymentMethod(Base):
    __tablename__ = "module_payment_methods"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    module_id = Column(Integer, ForeignKey('modules.id'), nullable=False)
    pos_id = Column(Integer, ForeignKey('core_pos_points.id'), nullable=False)
    name = Column(String(100), nullable=False)
    account_id = Column(Integer, ForeignKey('comptes_comptables.id'))
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# Instance globale du gestionnaire de base de données
_db_manager = None


def get_database_manager():
    """Retourne l'instance globale du gestionnaire de base de données"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def set_database_manager(manager):
    """Définit l'instance globale du gestionnaire de base de données"""
    global _db_manager
    _db_manager = manager
