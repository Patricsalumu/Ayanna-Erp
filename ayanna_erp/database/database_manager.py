from ayanna_erp.database.base import Base
"""
Gestionnaire de base de données pour Ayanna ERP
Utilise SQLAlchemy pour la gestion des modèles et des connexions
"""

import os
import importlib
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, Text, LargeBinary, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import StaticPool
import bcrypt
from contextlib import contextmanager



# Import des modèles comptables pour qu'ils soient inclus dans Base.metadata
try:
    from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaClasses, ComptaComptes, ComptaConfig
except ImportError:
    # Les modèles comptables ne sont pas encore disponibles
    pass
except ImportError:
    pass

# Cartographie des modules vers leurs modules de modèles (import paths)
MODULE_MODEL_PATHS = {
    'SalleFete': 'ayanna_erp.modules.salle_fete.model.salle_fete',
    'Stock': 'ayanna_erp.modules.stock.models',
    'Boutique': 'ayanna_erp.modules.boutique.model.models',
    'Comptabilite': 'ayanna_erp.modules.comptabilite.model.comptabilite',
    'Achats': 'ayanna_erp.modules.achats.models',
    # Ajouter d'autres modules si nécessaire
}

# Ajouter le mapping pour le module Restaurant
MODULE_MODEL_PATHS.update({
    'Restaurant': 'ayanna_erp.modules.restaurant.models.restaurant'
})

# Import des modèles core pour qu'ils soient inclus dans Base.metadata
try:
    from ayanna_erp.modules.core.models import CoreProduct, CoreProductCategory, POSProductAccess
except ImportError:
    # Les modèles core ne sont pas encore disponibles
    pass

# Import des modèles stock pour qu'ils soient inclus dans Base.metadata
try:
    from ayanna_erp.modules.stock.models import (
        StockWarehouse, StockConfig, StockProduitEntrepot, StockMovement,
        StockLivraison, StockLivraisonItem,
    )
except ImportError:
    # Les modèles stock ne sont pas encore disponibles
    pass

# Import des modèles Vente pour qu'ils soient inclus dans Base.metadata
try:
    from ayanna_erp.modules.boutique.model.models import (
        ShopClient, ShopService, ShopPanier, ShopPanierProduct, ShopPanierService,
        ShopPayment, ShopExpense, ShopComptesConfig
    )
except ImportError:
    # Les modèles boutique ne sont pas encore disponibles
    pass

# Import des modèles achats pour qu'ils soient inclus dans Base.metadata
try:
    from ayanna_erp.modules.achats.models import (
        CoreFournisseur, AchatCommande, AchatCommandeLigne, AchatDepense
    )
except ImportError:
    # Les modèles achats ne sont pas encore disponibles
    pass

# Import des modèles hôtel pour qu'ils soient inclus dans Base.metadata
try:
    from ayanna_erp.modules.hotel.models.model import (
        HotelCategory, HotelRoom, HotelReservation, HotelPayment
    )
except ImportError:
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
        self.current_enterprise_id = None
        # Migration automatique des nouvelles tables au premier accès à la DB
        try:
            self._migrate_livraison_tables()
        except Exception:
            pass  # Ne jamais bloquer le démarrage

    def set_current_enterprise(self, enterprise_id):
        """Définit l'entreprise actuellement sélectionnée (ID)"""
        self.current_enterprise_id = enterprise_id

    def get_current_enterprise_id(self):
        """Retourne l'ID de l'entreprise actuellement sélectionnée"""
        return self.current_enterprise_id
    
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

    @contextmanager
    def session_scope(self):
        """Context manager that yields a new SessionLocal() and handles commit/rollback/close.

        Use this for atomic operations that should not interfere with the shared session.
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            try:
                session.rollback()
            except Exception:
                pass
            raise
        finally:
            try:
                session.close()
            except Exception:
                pass
    
    def initialize_database(self):
        """Initialiser la base de données avec les tables et données par défaut"""
        try:
            # Créer toutes les tables de base (sans les modules)
            Base.metadata.create_all(bind=self.engine)
            
            # Insérer les données par défaut
            self._insert_default_data()
            # Initialiser les tables spécifiques aux modules (générique)
            try:
                self.initialize_modules()
            except Exception as e:
                print(f"⚠️ Erreur lors de l'initialisation des modules : {e}")
            
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
                {"name": "Vente", "description": "Gestion des ventes des Produits et services"},
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
                "Vente": "POS Vente Centrale", 
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
            
            # Créer automatiquement les entrepôts par défaut pour chaque POS
            self._create_default_warehouses_for_enterprise(session, enterprise_id)
            
        except Exception as e:
            raise
    
    def _create_default_warehouses_for_enterprise(self, session, enterprise_id):
        """Créer automatiquement les entrepôts par défaut pour une entreprise"""
        try:
            from ayanna_erp.modules.stock.models import StockWarehouse
            
            # Modules qui ont besoin d'entrepôts
            modules_with_warehouses = {"Vente", "Pharmacie", "Restaurant"}
            
            # Récupérer les POS de l'entreprise avec leurs modules
            pos_points = session.query(POSPoint).join(Module).filter(
                POSPoint.enterprise_id == enterprise_id,
                Module.name.in_(modules_with_warehouses)
            ).all()
            
            for pos in pos_points:
                # Récupérer le nom du module pour ce POS
                module = session.query(Module).filter_by(id=pos.module_id).first()
                
                # Créer entrepôt principal pour chaque POS qui en a besoin
                main_warehouse = StockWarehouse(
                    entreprise_id=enterprise_id,
                    code=f"MAIN_{pos.id}",
                    name=f"Entrepôt Principal - {pos.name}",
                    type="Principal",
                    description="Entrepôt principal - Point d'entrée pour tous les produits",
                    is_default=True,
                    is_active=True
                )
                session.add(main_warehouse)
                
                # Créer entrepôt point de vente pour chaque POS qui en a besoin
                pos_warehouse = StockWarehouse(
                    entreprise_id=enterprise_id,
                    code=f"POS_{pos.id}",
                    name=f"Entrepôt Point de Vente - {pos.name}",
                    type="Point de Vente",
                    description="Entrepôt point de vente - Produits destinés à la vente",
                    is_default=False,
                    is_active=True
                )
                session.add(pos_warehouse)
                
   
            
            # Afficher les modules qui n'ont pas d'entrepôts
            all_pos_points = session.query(POSPoint).join(Module).filter(
                POSPoint.enterprise_id == enterprise_id
            ).all()
            
            for pos in all_pos_points:
                module = session.query(Module).filter_by(id=pos.module_id).first()
                if module.name not in modules_with_warehouses:
                    pass
            
            session.flush()  # S'assurer que les entrepôts sont persistés
            
        except Exception as e:
            raise

    def initialize_modules(self):
        """Initialiser (créer) les tables pour les modules connus en réutilisant l'engine.

        Pour chaque module listé dans MODULE_MODEL_PATHS, on tente d'importer
        le module de modèles, on collecte les classes qui exposent `__table__`
        et on appelle `Base.metadata.create_all(..., tables=...)`.
        Les erreurs d'import sont tolérées et logguées.
        """
        created_count = 0
        for mod_name, import_path in MODULE_MODEL_PATHS.items():
            try:
                mod = importlib.import_module(import_path)
            except Exception as e:
                print(f"⚠️ Module '{mod_name}' non importable ({import_path}): {e}")
                continue

            tables = []
            for attr_name in dir(mod):
                try:
                    attr = getattr(mod, attr_name)
                    if hasattr(attr, '__table__'):
                        tables.append(attr.__table__)
                except Exception:
                    continue

            if tables:
                try:
                    Base.metadata.create_all(bind=self.engine, tables=tables, checkfirst=True)
                    created_count += len(tables)
                    print(f"✅ {len(tables)} tables créées pour le module '{mod_name}'")
                except Exception as e:
                    print(f"⚠️ Erreur lors de la création des tables pour '{mod_name}': {e}")
            else:
                print(f"ℹ️ Aucun modèle détecté pour le module '{mod_name}' ({import_path})")

        print(f"✅ Initialisation de modules terminée. Total de tables traitées: {created_count}")

        # Migration automatique des tables de livraison (idempotente)
        self._migrate_livraison_tables()

    def _migrate_livraison_tables(self):
        """
        Crée les tables stock_livraisons et stock_livraison_items si elles
        n'existent pas encore. Méthode idempotente : sans effet si les tables
        sont déjà présentes. Appelée automatiquement à chaque démarrage.
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS stock_livraisons (
                        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                        numero              TEXT    NOT NULL UNIQUE,
                        entreprise_id       INTEGER NOT NULL,
                        entrepot_depart_id  INTEGER NOT NULL
                            REFERENCES stock_warehouses(id),
                        entrepot_arrivee_id INTEGER NOT NULL
                            REFERENCES stock_warehouses(id),
                        statut              TEXT    NOT NULL DEFAULT 'brouillon',
                        valeur_totale       REAL    NOT NULL DEFAULT 0,
                        utilisateur_id      INTEGER,
                        utilisateur_nom     TEXT,
                        date_creation       DATETIME DEFAULT CURRENT_TIMESTAMP,
                        date_livraison      DATETIME,
                        date_reception      DATETIME,
                        notes               TEXT
                    )
                """))
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS stock_livraison_items (
                        id            INTEGER PRIMARY KEY AUTOINCREMENT,
                        livraison_id  INTEGER NOT NULL
                            REFERENCES stock_livraisons(id) ON DELETE CASCADE,
                        product_id    INTEGER NOT NULL,
                        product_name  TEXT,
                        product_code  TEXT,
                        quantite      REAL    NOT NULL,
                        cout_unitaire REAL    DEFAULT 0,
                        total_ligne   REAL    DEFAULT 0
                    )
                """))
                conn.commit()
                print("✅ Migration livraison : tables OK (créées ou déjà présentes)")
        except Exception as e:
            print(f"⚠️ Migration livraison : {e}")
    
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
                {"code": "8", "nom": "COMPTES DES AUTRES CHARGES ET DES AUTRES PRODUITS", "libelle": "Autres charges et produits", "type": "mixte", "document": "resultat"},
                {"code": "44", "nom": "COMPTES DE TAXES", "libelle": "Comptes de taxes", "type": "mixte", "document": "bilan"},
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
                {"numero": "100", "nom": "Capital social", "libelle": "Capital Social", "classe": "1"},
                {"numero": "101", "nom": "Apport des assosiés", "libelle": "Apports des associés", "classe": "1"},
                
                # Classe 4 - Comptes de tiers
                {"numero": "411", "nom": "Clients", "libelle": "Clients ordinaires", "classe": "4"},
                {"numero": "401", "nom": "Fournisseurs", "libelle": "Fournisseurs ordinaires", "classe": "4"},
                
                # Classe 3 - Comptes de stocks
                {"numero": "304", "nom": "Stocks des marchandises", "libelle": "Stocks des marchandises", "classe": "3"},
                
                # Classe 5 - Comptes de trésorerie
                {"numero": "57", "nom": "Caisse", "libelle": "Caisse générale", "classe": "5"},
                {"numero": "521", "nom": "Banque", "libelle": "Banque locale", "classe": "5"},
                
                # Classe 6 - Comptes de charges
                {"numero": "601", "nom": "Achats stockés - matières premières", "libelle": "Achats de matières premières", "classe": "6"},
                {"numero": "604", "nom": "Achats Marchandises - ", "libelle": "Marchandises consomables", "classe": "6"},
                {"numero": "622", "nom": "Rémunérations intermédiaires et honoraires", "libelle": "Rémunérations d'intermédiaires et honoraires", "classe": "6"},
                {"numero": "624", "nom": "Transports", "libelle": "Transports sur achats et ventes", "classe": "6"},
                {"numero": "680", "nom": "Remises", "libelle": "Compte des remises", "classe": "6"},
                
                # Classe 7 - Comptes de produits
                {"numero": "701", "nom": "Ventes marchandises", "libelle": "Ventes de marchandises", "classe": "7"},
                {"numero": "706", "nom": "Services vendus", "libelle": "Services vendus", "classe": "7"},
                {"numero": "758", "nom": "Produits divers", "libelle": "Produits divers vendus", "classe": "7"},
                
                # Classe 44 - Comptes de taxes (TVA)
                {"numero": "4431", "nom": "TVA collectée", "libelle": "TVA collectée sur ventes", "classe": "44"},
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
                        compte_achat_id=comptes_created.get("601").id if comptes_created.get("601") else None,
                        compte_stock_id=comptes_created.get("304").id if comptes_created.get("304") else None,
                        compte_variation_stock_id=comptes_created.get("604").id if comptes_created.get("604") else None,
                        compte_tva_id=comptes_created.get("4431").id if comptes_created.get("4431") else None,
                        compte_remise_id =comptes_created.get("680").id if comptes_created.get("680") else None
                        
                    )
                    session.add(config)
                    print(f"✅ Configuration comptable créée pour POS: {pos.name}")
            
            if not pos_list:
                print("⚠️  Aucun POS trouvé pour l'entreprise, configuration comptable non créée")
            
            session.flush()
            
        except Exception as e:
            print(f"❌ Erreur lors de l'insertion des données comptables: {e}")
            raise
    
    def _insert_default_services_and_products(self, session, enterprise_id):
        """Insérer les services et produits par défaut pour une nouvelle entreprise"""
        try:
            # Import des modèles nécessaires avec gestion des erreurs
            EventService = None
            EventProduct = None
            ShopService = None
            ShopProduct = None
            ShopProductCategory = None
            
            # Import sécurisé des modèles Salle de Fête
            try:
                from ayanna_erp.modules.salle_fete.model.salle_fete import EventService, EventProduct
                print("✅ Modèles Salle de Fête importés avec succès")
            except Exception as e:
                print(f"⚠️ Impossible d'importer les modèles Salle de Fête: {e}")
            
            # Import sécurisé des modèles Boutique (nouvelle architecture organisée)
            try:
                from ayanna_erp.modules.boutique.model.models import ShopService, ShopProduct
                print("✅ Modèles Ventes importés avec succès (nouvelle architecture organisée)")
            except Exception as e:
                print(f"⚠️ Impossible d'importer les modèles Vente: {e}")
                print(f"   Détail: {type(e).__name__}: {str(e)}")
            
            # Récupérer les POS de cette entreprise
            pos_list = session.query(POSPoint).filter_by(enterprise_id=enterprise_id).all()
            
            if not pos_list:
                print("⚠️ Aucun POS trouvé pour créer les services/produits par défaut")
                return
            session.flush()
            
        except Exception as e:
            print(f"❌ Erreur lors de l'insertion des services/produits: {e}")
            raise
    
    def create_pos_for_new_enterprise(self, enterprise_id):
        """Créer tous les POS pour une nouvelle entreprise (méthode publique)"""
        session = self.get_session()
        try:
            # Créer les POS
            self._create_pos_for_enterprise(session, enterprise_id)
            
            # Créer également les données comptables par défaut pour la nouvelle entreprise
            print(f"🔄 Création des comptes comptables par défaut pour l'entreprise {enterprise_id}...")
            self._insert_default_accounting_data(session, enterprise_id)
            print(f"✅ Comptes comptables créés pour l'entreprise {enterprise_id}")
            
            # Créer les services et produits par défaut pour la nouvelle entreprise
            print(f"🔄 Création des services et produits par défaut pour l'entreprise {enterprise_id}...")
            self._insert_default_services_and_products(session, enterprise_id)
            print(f"✅ Services et produits par défaut créés pour l'entreprise {enterprise_id}")
            
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
            module_name (str): Nom du module (ex: 'SalleFete', 'Vente', etc.)
            
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
    taux_de_change = Column(Numeric(12, 4), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    users = relationship("User", back_populates="enterprise")
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
