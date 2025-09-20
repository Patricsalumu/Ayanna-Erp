"""
Gestionnaire de base de données pour Ayanna ERP
Utilise SQLAlchemy pour la gestion des modèles et des connexions
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, Text, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import StaticPool
import bcrypt


Base = declarative_base()

# Import des modèles comptables pour qu'ils soient inclus dans Base.metadata
try:
    from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaClasses, ComptaComptes, ComptaConfig
except ImportError:
    # Les modèles comptables ne sont pas encore disponibles
    pass


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
            
            # Initialiser les données comptables par défaut
            self._insert_default_accounting_data(session, default_enterprise.id)
            
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
    
    def _insert_default_accounting_data(self, session, enterprise_id):
        """Insérer les données comptables par défaut SYSCOHADA"""
        try:
            # Insérer les classes comptables SYSCOHADA par défaut
            classes_comptables_default = [
                {"code": "1", "nom": "COMPTES DE RESSOURCES DURABLES", "libelle": "Comptes de ressources durables", "type": "passif", "document": "bilan"},
                {"code": "2", "nom": "COMPTES D'ACTIF IMMOBILISE", "libelle": "Comptes d'actif immobilisé", "type": "actif", "document": "bilan"},
                {"code": "3", "nom": "COMPTES DE STOCKS", "libelle": "Comptes de stocks", "type": "actif", "document": "bilan"},
                {"code": "4", "nom": "COMPTES DE TIERS", "libelle": "Comptes de tiers", "type": "mixte", "document": "bilan"},
                {"code": "5", "nom": "COMPTES DE TRESORERIE", "libelle": "Comptes de trésorerie", "type": "actif", "document": "bilan"},
                {"code": "6", "nom": "COMPTES DE CHARGES", "libelle": "Comptes de charges", "type": "charge", "document": "resultat"},
                {"code": "7", "nom": "COMPTES DE PRODUITS", "libelle": "Comptes de produits", "type": "produit", "document": "resultat"},
                {"code": "8", "nom": "COMPTES DES AUTRES CHARGES ET DES AUTRES PRODUITS", "libelle": "Autres charges et produits", "type": "mixte", "document": "resultat"}
            ]
            
            classes_created = {}
            for classe_data in classes_comptables_default:
                existing = session.query(ComptaClasses).filter_by(
                    code=classe_data["code"], 
                    enterprise_id=enterprise_id
                ).first()
                if not existing:
                    classe = ComptaClasses(
                        enterprise_id=enterprise_id,
                        **classe_data
                    )
                    session.add(classe)
                    session.flush()  # Pour obtenir l'ID
                    classes_created[classe_data["code"]] = classe
                    print(f"✅ Classe comptable créée: {classe.code} - {classe.nom}")
                else:
                    classes_created[classe_data["code"]] = existing
            
            # Insérer quelques comptes de base essentiels
            comptes_default = [
                # Classe 4 - Comptes de tiers
                {"numero": "411", "nom": "Clients", "libelle": "Clients ordinaires", "classe": "4"},
                {"numero": "401", "nom": "Fournisseurs", "libelle": "Fournisseurs ordinaires", "classe": "4"},
                
                # Classe 5 - Comptes de trésorerie
                {"numero": "57", "nom": "Caisse", "libelle": "Caisse générale", "classe": "5"},
                {"numero": "521", "nom": "Banque", "libelle": "Banque locale", "classe": "5"},
                
                # Classe 6 - Comptes de charges
                {"numero": "601", "nom": "Achats stockés - matières premières", "libelle": "Achats de matières premières", "classe": "6"},
                {"numero": "604", "nom": "Achats stockés - matières consommables", "libelle": "Achats de matières et fournitures consommables", "classe": "6"},
                {"numero": "622", "nom": "Rémunérations intermédiaires et honoraires", "libelle": "Rémunérations d'intermédiaires et honoraires", "classe": "6"},
                {"numero": "624", "nom": "Transports", "libelle": "Transports sur achats et ventes", "classe": "6"},
                
                # Classe 7 - Comptes de produits
                {"numero": "701", "nom": "Ventes marchandises", "libelle": "Ventes de marchandises dans la région", "classe": "7"},
                {"numero": "706", "nom": "Services vendus", "libelle": "Services vendus dans la région", "classe": "7"},
                {"numero": "758", "nom": "Produits divers", "libelle": "Produits divers de gestion courante", "classe": "7"}
            ]
            
            comptes_created = {}
            for compte_data in comptes_default:
                classe_code = compte_data.pop("classe")
                classe = classes_created.get(classe_code)
                
                if classe:
                    existing = session.query(ComptaComptes).filter_by(
                        numero=compte_data["numero"]
                    ).join(ComptaClasses).filter(ComptaClasses.enterprise_id == enterprise_id).first()
                    
                    if not existing:
                        compte = ComptaComptes(
                            classe_comptable_id=classe.id,
                            **compte_data
                        )
                        session.add(compte)
                        session.flush()  # Pour obtenir l'ID
                        comptes_created[compte_data["numero"]] = compte
                        print(f"✅ Compte comptable créé: {compte.numero} - {compte.nom}")
                    else:
                        comptes_created[compte_data["numero"]] = existing
            
            # Créer une configuration comptable pour chaque POS de l'entreprise
            pos_list = session.query(POSPoint).filter_by(enterprise_id=enterprise_id).all()
            
            for pos in pos_list:
                existing_config = session.query(ComptaConfig).filter_by(
                    enterprise_id=enterprise_id, 
                    pos_id=pos.id
                ).first()
                
                if not existing_config:
                    config = ComptaConfig(
                        enterprise_id=enterprise_id,
                        pos_id=pos.id,
                        compte_caisse_id=comptes_created.get("57").id if comptes_created.get("57") else None,
                        compte_banque_id=comptes_created.get("521").id if comptes_created.get("521") else None,
                        compte_client_id=comptes_created.get("411").id if comptes_created.get("411") else None,
                        compte_fournisseur_id=comptes_created.get("401").id if comptes_created.get("401") else None,
                        compte_vente_id=comptes_created.get("701").id if comptes_created.get("701") else None,
                        compte_achat_id=comptes_created.get("601").id if comptes_created.get("601") else None
                    )
                    session.add(config)
                    print(f"✅ Configuration comptable créée pour POS: {pos.name}")
            
            if not pos_list:
                print("⚠️  Aucun POS trouvé pour l'entreprise, configuration comptable non créée")
            
            session.flush()
            
        except Exception as e:
            print(f"❌ Erreur lors de l'insertion des données comptables: {e}")
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
    
    def get_pos_id_for_enterprise_module(self, enterprise_id, module_name):
        """
        Récupérer le pos_id pour une entreprise et un module spécifique
        
        Args:
            enterprise_id (int): ID de l'entreprise
            module_name (str): Nom du module (ex: 'SalleFete', 'Boutique', etc.)
            
        Returns:
            int: ID du POS pour ce module et cette entreprise, ou None si non trouvé
        """
        session = self.get_session()
        try:
            # Trouver le module par son nom
            module = session.query(Module).filter_by(name=module_name).first()
            if not module:
                print(f"⚠️  Module '{module_name}' non trouvé")
                return None
            
            # Trouver le POS pour cette entreprise et ce module
            pos = session.query(POSPoint).filter_by(
                enterprise_id=enterprise_id,
                module_id=module.id
            ).first()
            
            if pos:
                return pos.id
            else:
                print(f"⚠️  Aucun POS trouvé pour l'entreprise {enterprise_id} et le module {module_name}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur lors de la récupération du pos_id: {e}")
            return None
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
    logo = Column(LargeBinary)  # stockage du logo en BLOB
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


class PaymentMethod(Base):
    __tablename__ = "module_payment_methods"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    module_id = Column(Integer, ForeignKey('modules.id'), nullable=False)
    pos_id = Column(Integer, ForeignKey('core_pos_points.id'), nullable=False)
    name = Column(String(100), nullable=False)
    account_id = Column(Integer, ForeignKey('compta_comptes.id'))
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
