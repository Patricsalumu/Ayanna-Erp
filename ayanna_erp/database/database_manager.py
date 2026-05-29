from ayanna_erp.database.base import Base
"""
Gestionnaire de base de données pour Ayanna ERP
Utilise SQLAlchemy pour la gestion des modèles et des connexions
"""

# Import du gestionnaire de synchronisation API
try:
    from ayanna_erp.utils.sync_manager import CoreSync, CoreSyncSettings, SyncManager, _local_now_iso
    _SYNC_AVAILABLE = True
except ImportError:
    _SYNC_AVAILABLE = False

import os
import json
import importlib
import threading
from datetime import datetime
import re
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, Text, LargeBinary, text, event
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

# Mapping for Fabrication module
MODULE_MODEL_PATHS.update({
    'Fabrication': 'ayanna_erp.modules.fabrication.models'
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


# =============================================================================
# Auto-journalisation SQLAlchemy → core_sync
# =============================================================================

# Tables qui ne doivent jamais être journalisées (internes sync + locales uniquement)
_SYNC_EXCLUDED_TABLES = frozenset({
    'core_sync', 'core_sync_settings', 'core_configsync', 'core_sync_history',
    'modules',
    'licence',
    'shop_comptes_config',
    'alembic_version',
})

# Flag thread-local pour éviter la journalisation récursive
# (record_change() écrit dans core_sync → déclenche le listener → boucle infinie)
_sync_writing = threading.local()


def _obj_to_sync_dict(obj) -> dict | None:
    """Convertit une instance ORM SQLAlchemy en dict JSON-sérialisable.
    Retourne None si l'objet ne possède pas __table__."""
    try:
        result = {}
        for col in obj.__table__.columns:
            val = getattr(obj, col.name, None)
            if isinstance(val, bytes):
                val = None          # ignorer les BLOBs (logo, etc.)
            elif hasattr(val, 'isoformat'):
                val = val.isoformat()
            result[col.name] = val
        return result
    except Exception:
        return None


def _register_sync_listener(db_manager: 'DatabaseManager') -> None:
    """Enregistre les listeners after_flush / after_commit / after_rollback
    sur db_manager.SessionLocal pour journaliser automatiquement tout
    INSERT/UPDATE ORM dans core_sync.

    Mécanisme en 2 temps (évite les transactions imbriquées sur SQLite) :
      1. after_flush  → capture les objets new/dirty dans session.info['_sync_pending']
      2. after_commit → vide le buffer et appelle SyncManager.record_change()
         (la session principale est déjà commitée → pas de conflit SQLite)
    """
    if not _SYNC_AVAILABLE:
        return

    def _after_flush(session, flush_context):
        """Capture les objets nouveaux/modifiés dans un buffer attaché à la session."""
        # Ne pas capturer si on est déjà en train d'écrire dans core_sync
        if getattr(_sync_writing, 'active', False):
            return

        pending = session.info.setdefault('_sync_pending', [])

        for obj in list(session.new):
            try:
                tbl = obj.__tablename__
                if tbl in _SYNC_EXCLUDED_TABLES:
                    continue
                d = _obj_to_sync_dict(obj)
                if d and d.get('id') is not None:
                    pending.append((tbl, 'INSERT', str(d['id']), d))
            except Exception:
                pass

        for obj in list(session.dirty):
            try:
                tbl = obj.__tablename__
                if tbl in _SYNC_EXCLUDED_TABLES:
                    continue
                d = _obj_to_sync_dict(obj)
                if d and d.get('id') is not None:
                    pending.append((tbl, 'UPDATE', str(d['id']), d))
            except Exception:
                pass

    def _after_commit(session):
        """Écrit les changements bufférisés dans core_sync après le commit."""
        pending = session.info.pop('_sync_pending', [])
        if not pending:
            return

        sm = db_manager.sync_manager
        if sm is None:
            return

        _sync_writing.active = True
        try:
            for tbl, op, record_id, data in pending:
                try:
                    sm.record_change(tbl, op, record_id, data)
                except Exception:
                    pass
        finally:
            _sync_writing.active = False

    def _after_rollback(session):
        """Vide le buffer en cas de rollback (les changements ne sont pas persistés)."""
        session.info.pop('_sync_pending', None)

    event.listen(db_manager.SessionLocal, 'after_flush',    _after_flush)
    event.listen(db_manager.SessionLocal, 'after_commit',   _after_commit)
    event.listen(db_manager.SessionLocal, 'after_rollback', _after_rollback)


class DatabaseManager:
    """Gestionnaire principal de la base de données"""
    # Prevent running automatic migrations multiple times per process
    _migrations_executed = False
    
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
        # Exécuter une seule fois par processus pour éviter les logs/migrations répétées
        if not DatabaseManager._migrations_executed:
            try:
                try:
                    self._migrate_livraison_tables()
                except Exception:
                    pass  # Ne jamais bloquer le démarrage
                try:
                    self._migrate_payment_modes_table()
                except Exception:
                    pass  # Silencieux si la table core_enterprises n'existe pas encore (premier demarrage)
                try:
                    self._migrate_compta_is_default_column()
                except Exception:
                    pass
                try:
                    self._migrate_compta_journal_validation()
                except Exception:
                    pass
                try:
                    self._migrate_compta_config_fournisseur_debiteur()
                except Exception:
                    pass
                try:
                    self._migrate_user_modules_column()
                except Exception:
                    pass
                try:
                    self._migrate_core_sync_tables()
                except Exception:
                    pass
                try:
                    self._migrate_updated_at_columns()
                except Exception:
                    pass
                try:
                    self._migrate_compta_timestamps()
                except Exception:
                    pass
                try:
                    self._migrate_licences_table()
                except Exception:
                    pass
                try:
                    self._migrate_init_compta_configs()
                except Exception:
                    pass
                try:
                    self._migrate_core_products_columns()
                except Exception:
                    pass
            finally:
                DatabaseManager._migrations_executed = True
        # Initialiser le gestionnaire de synchronisation
        self._sync_manager = None
        # Enregistrer le listener de journalisation automatique (after_flush/after_commit)
        # Toute opération ORM INSERT/UPDATE sera capturée et envoyée dans core_sync.
        _register_sync_listener(self)

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
    
    def create_all_tables(self):
        """Crée toutes les tables (base + modules) sans insérer de données par défaut.

        Méthode idempotente — sans effet si les tables existent déjà.
        Utilisée au premier démarrage pour pouvoir appeler is_first_run() avant
        que les données par défaut ne soient insérées.
        """
        Base.metadata.create_all(bind=self.engine)
        try:
            self.initialize_modules()
        except Exception as e:
            print(f"⚠️ create_all_tables / initialize_modules : {e}")

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

            # Journaliser toutes les données par défaut dans core_sync
            # (statut : jamais synchronisé — sera poussé au 1er sync serveur)
            try:
                self._journal_default_data()
            except Exception as e:
                print(f"⚠️ Journalisation initiale core_sync : {e}")

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
            
            # Insérer les modules par défaut (toujours)
            modules_default = [
                {"name": "SalleFete", "description": "Gestion des salles de fête et événements"},
                {"name": "Vente", "description": "Gestion des ventes des Produits et services"},
                {"name": "Pharmacie", "description": "Gestion de pharmacie"},
                {"name": "Restaurant", "description": "Gestion de restaurant et bar"},
                {"name": "Hotel", "description": "Gestion d'hôtel"},
                {"name": "Achats", "description": "Gestion des achats fournisseurs"},
                {"name": "Stock", "description": "Gestion des stocks et inventaires"},
                {"name": "Comptabilite", "description": "Comptabilité SYSCOHADA"},
                {"name": "Fabrication", "description": "Gestion de la production et fabrication"}
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

            # Créer les modes de paiement par défaut
            self._insert_default_payment_modes(session, default_enterprise.id)

            session.commit()
            
        except Exception as e:
            session.rollback()
        finally:
            session.close()

    def _journal_default_data(self):
        """
        Insere dans core_sync toutes les donnees par defaut creees lors de
        l'initialisation locale, avec synced=0 (jamais synchronise).

        Ces entrees seront poussees vers le serveur la premiere fois que
        l'utilisateur configurera la synchronisation.

        Tables journalisees :
          core_enterprises, core_users, modules, core_pos_points,
          core_payment_modes
        """
        if not _SYNC_AVAILABLE:
            return

        sm = self.sync_manager
        if sm is None:
            return

        CREATED_BY = 'system:init'

        def _row_to_dict(obj):
            """Convertit un objet SQLAlchemy en dictionnaire serialisable."""
            d = {}
            for col in obj.__table__.columns:
                val = getattr(obj, col.name, None)
                if isinstance(val, bytes):
                    val = None  # exclure les BLOB (logo...)
                elif hasattr(val, 'isoformat'):
                    val = val.isoformat()
                d[col.name] = val
            return d

        with self.session_scope() as session:
            # Tables a journaliser avec leur modele et colonne PK
            targets = [
                (Entreprise,   'core_enterprises'),
                (User,         'core_users'),
                (Module,       'modules'),
                (POSPoint,     'core_pos_points'),
                (PaymentMode,  'core_payment_modes'),
                (ComptaClasses, 'compta_classes'),
                (ComptaComptes, 'compta_comptes'),
            ]
            total = 0
            for model_cls, table_name in targets:
                try:
                    rows = session.query(model_cls).all()
                    for row in rows:
                        # Verifier si une entree existe deja pour cet enregistrement
                        already = session.query(CoreSync).filter_by(
                            table_name=table_name,
                            record_id=str(row.id),
                        ).first()
                        if already:
                            continue
                        entry = CoreSync(
                            table_name=table_name,
                            operation='INSERT',
                            record_id=str(row.id),
                            data_json=json.dumps(
                                _row_to_dict(row),
                                ensure_ascii=False,
                                default=str,
                            ),
                            synced=0,
                            created_at=_local_now_iso(),
                            created_by=CREATED_BY,
                        )
                        session.add(entry)
                        total += 1
                except Exception as exc:
                    print(f"  ⚠️ _journal_default_data / {table_name} : {exc}")

        print(f"✅ Journal initial : {total} enregistrement(s) en attente de synchronisation dans core_sync.")

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

    def _insert_default_payment_modes(self, session, enterprise_id: int):
        """Crée les 4 modes de paiement par défaut pour l'entreprise si absents."""
        defaults = [
            {'code': 'cash',         'label': 'Espèces',       'sort_order': 1},
            {'code': 'banque',       'label': 'Banque',         'sort_order': 2},
            {'code': 'mobile_money', 'label': 'Mobile Money',   'sort_order': 3},
            {'code': 'credit',       'label': 'Crédit',        'sort_order': 4},
        ]
        for d in defaults:
            existing = session.query(PaymentMode).filter_by(
                enterprise_id=enterprise_id, code=d['code']).first()
            if not existing:
                session.add(PaymentMode(
                    enterprise_id=enterprise_id,
                    code=d['code'],
                    label=d['label'],
                    sort_order=d['sort_order'],
                    is_default=1,
                    is_active=1,
                ))
        session.flush()

    def _migrate_payment_modes_table(self):
        """Crée la table core_payment_modes si elle n'existe pas encore,
        puis seed les modes par défaut pour chaque entreprise existante."""
        try:
            Base.metadata.create_all(
                bind=self.engine,
                tables=[PaymentMode.__table__],
                checkfirst=True,
            )
            # Seed pour les entreprises existantes (idempotent).
            # Si la table core_enterprises n'existe pas encore (premier demarrage),
            # on sort silencieusement ; le seed sera fait par _insert_default_data().
            with self.engine.connect() as conn:
                tables = conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name='core_enterprises'")
                ).fetchall()
                if not tables:
                    return
            with self.session_scope() as session:
                enterprises = session.query(Entreprise).all()
                for ent in enterprises:
                    self._insert_default_payment_modes(session, ent.id)
        except Exception as e:
            print(f"⚠️ _migrate_payment_modes_table : {e}")

    def _migrate_compta_is_default_column(self):
        """Ajoute la colonne is_default à compta_comptes si absente (migration idempotente)."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text(
                    "ALTER TABLE compta_comptes ADD COLUMN is_default INTEGER NOT NULL DEFAULT 0"
                ))
                conn.commit()
                print("✅ Migration : colonne is_default ajoutée à compta_comptes")
        except Exception:
            pass  # La colonne existe déjà

    def _migrate_compta_journal_validation(self):
        """Ajoute les colonnes valide, valide_by et date_validation à compta_journaux (idempotent)."""
        cols = [
            "ALTER TABLE compta_journaux ADD COLUMN valide INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE compta_journaux ADD COLUMN valide_by TEXT",
            "ALTER TABLE compta_journaux ADD COLUMN date_validation DATETIME",
        ]
        with self.engine.connect() as conn:
            for sql in cols:
                try:
                    conn.execute(text(sql))
                except Exception:
                    pass  # colonne déjà présente
            conn.commit()
        print("✅ Migration : colonnes valide/valide_by/date_validation ajoutées à compta_journaux")

    def _migrate_compta_config_fournisseur_debiteur(self):
        """Ajoute la colonne compte_fournisseur_debiteur_id à compta_config (idempotent)."""
        with self.engine.connect() as conn:
            try:
                conn.execute(text(
                    "ALTER TABLE compta_config ADD COLUMN compte_fournisseur_debiteur_id INTEGER "
                    "REFERENCES compta_comptes(id)"
                ))
                conn.commit()
            except Exception:
                pass  # colonne déjà présente
        print("✅ Migration : colonne compte_fournisseur_debiteur_id ajoutée à compta_config")

    def _migrate_user_modules_column(self):
        """
        Ajoute la colonne modules à core_users si elle est absente.
        Cette colonne (TEXT nullable) stocke la liste JSON des modules
        accessibles par l'utilisateur. Elle a été ajoutée lors du travail
        sur l'API et peut manquer dans les anciennes bases de données.
        """
        with self.engine.connect() as conn:
            exists = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='core_users'")
            ).fetchone()
            if not exists:
                return
            cols = [row[1] for row in conn.execute(text("PRAGMA table_info(core_users)")).fetchall()]
            if 'modules' not in cols:
                conn.execute(text("ALTER TABLE core_users ADD COLUMN modules TEXT"))
                conn.commit()
                print("✅ Migration : colonne modules ajoutée à core_users")

    def _migrate_core_sync_tables(self):
        """
        Cree les tables core_sync et core_sync_settings si elles
        n'existent pas encore. Methode idempotente.
        """
        if not _SYNC_AVAILABLE:
            return
        try:
            Base.metadata.create_all(
                bind=self.engine,
                tables=[CoreSync.__table__, CoreSyncSettings.__table__],
                checkfirst=True,
            )
            print("✅ Migration sync : tables core_sync et core_sync_settings OK")
        except Exception as e:
            print(f"⚠️ _migrate_core_sync_tables : {e}")

    def _migrate_updated_at_columns(self):
        """
        Ajoute la colonne updated_at aux tables de base si elle est absente.
        Le serveur Laravel retourne toujours updated_at (timestamps()) ;
        sans cette colonne le PULL echoue avec OperationalError.
        Tables concernees : core_enterprises, core_users, modules,
                            core_pos_points, core_payment_modes.
        """
        tables = [
            'core_enterprises',
            'core_users',
            'modules',
            'core_pos_points',
            'core_payment_modes',
        ]
        with self.engine.connect() as conn:
            for tbl in tables:
                # Verifier si la table existe
                exists = conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name=:t"),
                    {'t': tbl}
                ).fetchone()
                if not exists:
                    continue
                # Verifier si updated_at existe deja
                cols = [row[1] for row in conn.execute(text(f"PRAGMA table_info({tbl})")).fetchall()]
                if 'updated_at' not in cols:
                    try:
                        conn.execute(text(
                            f"ALTER TABLE {tbl} ADD COLUMN updated_at DATETIME"
                        ))
                        print(f"✅ Migration : colonne updated_at ajoutee a {tbl}")
                    except Exception as e:
                        print(f"⚠️ updated_at / {tbl} : {e}")
            conn.commit()

    def _migrate_compta_timestamps(self):
        """
        Ajoute created_at et updated_at a compta_classes et compta_comptes
        si ces colonnes sont absentes (le serveur Laravel les retourne toujours).
        """
        tables = ['compta_classes', 'compta_comptes']
        with self.engine.connect() as conn:
            for tbl in tables:
                exists = conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name=:t"),
                    {'t': tbl}
                ).fetchone()
                if not exists:
                    continue
                cols = [row[1] for row in conn.execute(text(f"PRAGMA table_info({tbl})")).fetchall()]
                for col in ['created_at', 'updated_at']:
                    if col not in cols:
                        try:
                            conn.execute(text(
                                f"ALTER TABLE {tbl} ADD COLUMN {col} DATETIME"
                            ))
                            print(f"✅ Migration : colonne {col} ajoutée à {tbl}")
                        except Exception as e:
                            print(f"⚠️ {col} / {tbl} : {e}")
            conn.commit()

    def _migrate_core_products_columns(self):
        """
        Ajoute les colonnes `product_type` et `stock_account_id` à la table `core_products`
        si elles sont absentes (migration idempotente).
        """
        try:
            with self.engine.connect() as conn:
                exists = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='core_products'")).fetchone()
                if not exists:
                    return
                res = conn.execute(text("PRAGMA table_info('core_products')")).fetchall()
                cols = {r[1] for r in res}

                if 'product_type' not in cols:
                    try:
                        conn.execute(text("ALTER TABLE core_products ADD COLUMN product_type TEXT DEFAULT 'resale_product'"))
                    except Exception:
                        pass
                if 'stock_account_id' not in cols:
                    try:
                        conn.execute(text("ALTER TABLE core_products ADD COLUMN stock_account_id INTEGER"))
                    except Exception:
                        pass
                conn.commit()
            print("✅ Migration : colonnes product_type et stock_account_id ajoutées à core_products (si nécessaire)")
        except Exception as e:
            print(f"⚠️ _migrate_core_products_columns : {e}")

    @property
    def sync_manager(self) -> 'SyncManager | None':
        """
        Retourne l'instance SyncManager partagee pour cette base de donnees.
        Cree l'instance a la premiere demande (lazy init).
        Retourne None si le module de synchronisation n'est pas disponible.
        """
        if not _SYNC_AVAILABLE:
            return None
        if self._sync_manager is None:
            self._sync_manager = SyncManager(self.engine)
        return self._sync_manager

    def is_first_run(self) -> bool:
        """
        Retourne True si la base de données est vide (aucun utilisateur créé).
        Utilisé pour déclencher l'assistant de premier démarrage.
        """
        try:
            session = self.get_session()
            count = session.query(User).count()
            session.close()
            return count == 0
        except Exception:
            return True

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
                    try:
                        print(f"Classe comptable créée: {classe.code} - {classe.nom}")
                    except Exception:
                        pass
                else:
                    classes_created[classe_data["code"]] = existing

            # Plan comptable SYSCOHADA - (truncated list kept same as prior)
            comptes_default = [
                {"numero": "101",  "nom": "Capital social",                              "libelle": "Capital social souscrit et appelé",                         "classe": "1"},
                {"numero": "102",  "nom": "Apports des associés",                        "libelle": "Comptes courants d'associés et apports en compte",          "classe": "1"},
                {"numero": "111",  "nom": "Réserve légale",                              "libelle": "Réserve légale constituée (5% du bénéfice)",                 "classe": "1"},
                {"numero": "120",  "nom": "Report à nouveau (créditeur)",               "libelle": "Report à nouveau bénéficiaire",                              "classe": "1"},
                {"numero": "129",  "nom": "Report à nouveau (débiteur)",                "libelle": "Report à nouveau déficitaire",                               "classe": "1"},
                {"numero": "130",  "nom": "Résultat net - Bénéfice",                    "libelle": "Résultat net de l'exercice (bénéfice)",                       "classe": "1"},
                {"numero": "139",  "nom": "Résultat net - Perte",                       "libelle": "Résultat net de l'exercice (perte)",                          "classe": "1"},
                {"numero": "162",  "nom": "Emprunts bancaires",                          "libelle": "Emprunts auprès des établissements de crédit",                "classe": "1"},
                {"numero": "164",  "nom": "Comptes courants d'associés",                "libelle": "Avances et prêts des associés à la société",                  "classe": "1"},
                {"numero": "211",  "nom": "Terrains",                                    "libelle": "Terrains nus, agricoles et de plantation",                   "classe": "2"},
                {"numero": "213",  "nom": "Bâtiments (terrain propre)",                 "libelle": "Bâtiments et constructions sur terrain propre",              "classe": "2"},
                {"numero": "2135", "nom": "Bâtiments (terrain d'autrui)",               "libelle": "Bâtiments construits sur terrain d'autrui",                  "classe": "2"},
                {"numero": "228",  "nom": "Aménagements et installations de bureau",    "libelle": "Aménagements, installations et agencements de bureaux",      "classe": "2"},
                {"numero": "231",  "nom": "Matériel de transport",                      "libelle": "Véhicules, motocycles et matériel de transport",              "classe": "2"},
                {"numero": "241",  "nom": "Mobilier de bureau",                         "libelle": "Meubles, armoires, rayonnages corporels de bureau",           "classe": "2"},
                {"numero": "2442", "nom": "Matériel de bureau (chaises et tables)",     "libelle": "Chaises, tables et sièges de bureau",                        "classe": "2"},
                {"numero": "2443", "nom": "Matériel informatique",                      "libelle": "Ordinateurs, imprimantes, serveurs et périphériques",         "classe": "2"},
                {"numero": "2444", "nom": "Logiciels et site web",                      "libelle": "Logiciels, progiciels, site web (immobilisations incorporelles)","classe": "2"},
                {"numero": "245",  "nom": "Brevets et licences",                        "libelle": "Brevets, licences, marques et droits similaires",             "classe": "2"},
                {"numero": "246",  "nom": "Congélateurs et équipements frigorigènes",   "libelle": "Congélateurs, réfrigérateurs et équipements de froid",        "classe": "2"},
                {"numero": "247",  "nom": "Chaises et tables de terrasse",              "libelle": "Mobilier de terrasse et d'espace client",                    "classe": "2"},
                {"numero": "2813", "nom": "Amortissement des bâtiments",               "libelle": "Amortissements cumulés des bâtiments",                       "classe": "2"},
                {"numero": "2831", "nom": "Amortissement du matériel de transport",     "libelle": "Amortissements cumulés du matériel de transport",             "classe": "2"},
                {"numero": "2841", "nom": "Amortissement du mobilier de bureau",        "libelle": "Amortissements cumulés du mobilier de bureau",                "classe": "2"},
                {"numero": "2843", "nom": "Amortissement du matériel informatique",     "libelle": "Amortissements cumulés du matériel informatique",             "classe": "2"},
                {"numero": "2844", "nom": "Amortissement des logiciels",               "libelle": "Amortissements cumulés des logiciels et site web",             "classe": "2"},
                {"numero": "2846", "nom": "Amortissement des congélateurs",            "libelle": "Amortissements cumulés des congélateurs et équipements de froid","classe": "2"},
                {"numero": "301",  "nom": "Stocks de marchandises",                     "libelle": "Stocks de marchandises destinées à la revente",              "classe": "3"},
                {"numero": "321",  "nom": "Matières premières",                         "libelle": "Matières premières et fournitures liées à la production",    "classe": "3"},
                {"numero": "341",  "nom": "Produits finis",                              "libelle": "Produits finis issus de la production propre",                "classe": "3"},
                {"numero": "401",  "nom": "Fournisseurs (créditeurs)",                  "libelle": "Dettes fournisseurs et comptes rattachés",                   "classe": "4"},
                {"numero": "409",  "nom": "Fournisseurs débiteurs (avances)",           "libelle": "Avances et acomptes versés sur commandes fournisseurs",      "classe": "4"},
                {"numero": "411",  "nom": "Clients débiteurs",                          "libelle": "Créances clients et comptes rattachés",                      "classe": "4"},
                {"numero": "419",  "nom": "Clients créditeurs (avances reçues)",        "libelle": "Avances et acomptes reçus sur commandes clients",            "classe": "4"},
                {"numero": "421",  "nom": "Personnel - Rémunérations dues",             "libelle": "Salaires et traitements dus au personnel",                   "classe": "4"},
                {"numero": "431",  "nom": "Sécurité sociale (INSS/CNSS)",              "libelle": "Cotisations de sécurité sociale et charges INSS",            "classe": "4"},
                {"numero": "441",  "nom": "État - Impôts et taxes divers",              "libelle": "Impôts directs, taxes et contributions diverses",             "classe": "4"},
                {"numero": "4431", "nom": "TVA collectée",                              "libelle": "TVA collectée sur les ventes",                               "classe": "4"},
                {"numero": "4432", "nom": "TVA déductible",                             "libelle": "TVA déductible sur les achats",                              "classe": "4"},
                {"numero": "444",  "nom": "État - Impôt sur les bénéfices (IBP)",       "libelle": "Impôt sur les bénéfices professionnels (IBP/IS)",            "classe": "4"},
                {"numero": "461",  "nom": "Associé - Compte courant débiteur",          "libelle": "Associé ayant reçu une avance ou pris de l'argent",           "classe": "4"},
                {"numero": "462",  "nom": "Associé - Compte courant créditeur",         "libelle": "Associé ayant prêté de l'argent à l'entreprise",             "classe": "4"},
                {"numero": "465",  "nom": "Avances reçues - Associés",                  "libelle": "Avances et acomptes reçus des associés",                      "classe": "4"},
                {"numero": "466",  "nom": "Avances versées - Associés",                 "libelle": "Avances et acomptes versés aux associés",                     "classe": "4"},
                {"numero": "471",  "nom": "Débiteurs divers",                           "libelle": "Autres débiteurs divers",                                    "classe": "4"},
                {"numero": "472",  "nom": "Créditeurs divers",                          "libelle": "Autres créditeurs divers",                                   "classe": "4"},
                {"numero": "477",  "nom": "Dépôts et cautionnements reçus",             "libelle": "Cautions et garanties reçues de tiers",                       "classe": "4"},
                {"numero": "478",  "nom": "Dépôts et cautionnements versés",            "libelle": "Cautions et garanties versées à des tiers",                   "classe": "4"},
                {"numero": "521",  "nom": "Banque USD (compte courant)",               "libelle": "Compte courant bancaire en dollars américains (USD)",         "classe": "5"},
                {"numero": "522",  "nom": "Banque CDF (compte courant)",               "libelle": "Compte courant bancaire en francs congolais (CDF)",           "classe": "5"},
                {"numero": "531",  "nom": "Mobile Money",                               "libelle": "M-Pesa, Airtel Money, Orange Money et autres",                "classe": "5"},
                {"numero": "542",  "nom": "Chèques et virements à encaisser",          "libelle": "Chèques reçus en attente d'encaissement",                     "classe": "5"},
                {"numero": "571",  "nom": "Caisse principale USD",                      "libelle": "Caisse en espèces dollars américains",                        "classe": "5"},
                {"numero": "572",  "nom": "Caisse principale CDF",                      "libelle": "Caisse en espèces francs congolais",                          "classe": "5"},
                {"numero": "601",  "nom": "Achats de marchandises",                     "libelle": "Achats de marchandises destinées à la revente",              "classe": "6"},
                {"numero": "602",  "nom": "Achats de matières premières",               "libelle": "Achats de matières premières et fournitures de production",   "classe": "6"},
                {"numero": "605",  "nom": "Achats de carburant et lubrifiants",         "libelle": "Carburant, huiles moteur et lubrifiants",                     "classe": "6"},
                {"numero": "606",  "nom": "Achats de crédit téléphonique",              "libelle": "Achats de crédit téléphonique et recharges",                  "classe": "6"},
                {"numero": "611",  "nom": "Frais de transport",                         "libelle": "Transport sur achats, ventes et déplacements",                "classe": "6"},
                {"numero": "621",  "nom": "Salaires et traitements du personnel",       "libelle": "Rémunérations brutes du personnel (salaires fixes)",          "classe": "6"},
                {"numero": "622",  "nom": "Honoraires et services externes",            "libelle": "Honoraires, rémunérations d'intermédiaires et consultants",   "classe": "6"},
                {"numero": "623",  "nom": "Formation du personnel",                     "libelle": "Frais de formation et perfectionnement du personnel",          "classe": "6"},
                {"numero": "626",  "nom": "Connexion internet et téléphonie",           "libelle": "Abonnements internet, mobile et téléphonie fixe",             "classe": "6"},
                {"numero": "6271", "nom": "Électricité (SNEL)",                         "libelle": "Charges d'électricité (SNEL/fournisseur électricité)",         "classe": "6"},
                {"numero": "6272", "nom": "Eau (REGIDESO)",                             "libelle": "Charges d'eau (REGIDESO/fournisseur d'eau)",                   "classe": "6"},
                {"numero": "629",  "nom": "Produits d'entretien et nettoyage",          "libelle": "Produits d'entretien, ménage et nettoyage des locaux",        "classe": "6"},
                {"numero": "631",  "nom": "Frais et commissions bancaires",             "libelle": "Frais de tenue de compte et commissions bancaires",           "classe": "6"},
                {"numero": "632",  "nom": "Intérêts bancaires",                         "libelle": "Intérêts sur retraits, dépôts et tenue de compte bancaire",   "classe": "6"},
                {"numero": "641",  "nom": "Charges sociales patronales (INSS)",         "libelle": "Cotisations patronales INSS/CNSS à la charge de l'entreprise", "classe": "6"},
                {"numero": "651",  "nom": "Pertes sur créances / Abandons",             "libelle": "Abandon de créances clients et pertes sur créances irrécouvrables","classe": "6"},
                {"numero": "661",  "nom": "Charges imprévues et exceptionnelles",       "libelle": "Dépenses imprévues, extraordinaires et exceptionnelles",       "classe": "6"},
                {"numero": "671",  "nom": "Dotations aux amortissements",               "libelle": "Dotations aux amortissements et dépréciations des immobilisations","classe": "6"},
                {"numero": "681",  "nom": "Marketing et publicité",                     "libelle": "Frais de marketing, publicité et communication",               "classe": "6"},
                {"numero": "682",  "nom": "Remises accordées aux clients",              "libelle": "Remises, ristournes et rabais accordés aux clients",            "classe": "6"},
                {"numero": "683",  "nom": "Maintenance et réparations",                 "libelle": "Entretien, maintenance et réparations des équipements",         "classe": "6"},
                {"numero": "691",  "nom": "Impôts et taxes (IBP, DI, patente)",         "libelle": "Impôts sur bénéfices, droits d'entrée et patentes diverses",   "classe": "6"},
                {"numero": "701",  "nom": "Ventes de marchandises",                     "libelle": "Chiffre d'affaires - Ventes de marchandises",                 "classe": "7"},
                {"numero": "706",  "nom": "Prestations de services",                    "libelle": "Chiffre d'affaires - Prestations de services facturées",       "classe": "7"},
                {"numero": "711",  "nom": "Variation de stocks de produits finis",      "libelle": "Variation des stocks de produits finis et en-cours",           "classe": "7"},
                {"numero": "770",  "nom": "Produits financiers (intérêts reçus)",       "libelle": "Intérêts créditeurs et produits financiers reçus de la banque","classe": "7"},
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
                            is_default=True,
                            **compte_data
                        )
                        session.add(compte)
                        session.flush()  # Pour obtenir l'ID
                        comptes_created[compte_data["numero"]] = compte
                        try:
                            print(f"Compte comptable créé: {compte.numero} - {compte.nom}")
                        except Exception:
                            pass
                    else:
                        if not getattr(existing, 'is_default', False):
                            try:
                                existing.is_default = True
                            except Exception:
                                pass
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
                        compte_caisse_id=comptes_created.get("571").id if comptes_created.get("571") else None,
                        compte_banque_id=comptes_created.get("521").id if comptes_created.get("521") else None,
                        compte_client_id=comptes_created.get("411").id if comptes_created.get("411") else None,
                        compte_fournisseur_id=comptes_created.get("401").id if comptes_created.get("401") else None,
                        compte_fournisseur_debiteur_id=comptes_created.get("409").id if comptes_created.get("409") else None,
                        compte_vente_id=comptes_created.get("701").id if comptes_created.get("701") else None,
                        compte_achat_id=comptes_created.get("601").id if comptes_created.get("601") else None,
                        compte_stock_id=comptes_created.get("301").id if comptes_created.get("301") else None,
                        compte_tva_id=comptes_created.get("4431").id if comptes_created.get("4431") else None,
                        compte_remise_id=comptes_created.get("682").id if comptes_created.get("682") else None,
                    )
                    session.add(config)
                    try:
                        print(f"Configuration comptable créée pour POS: {pos.name}")
                    except Exception:
                        pass
            
            if not pos_list:
                try:
                    print("Aucun POS trouvé pour l'entreprise, configuration comptable non créée")
                except Exception:
                    pass
            
            session.flush()
            
        except Exception as e:
            print(f"❌ Erreur lors de l'insertion des données comptables: {e}")
            raise

    def _migrate_licences_table(self):
        """
        Crée la table `licences` si elle n'existe pas encore (idempotent).
        Structure compatible avec le schéma serveur (id TEXT UUID, cle, type,
        date_activation, date_expiration, signature, active, enterprise_id,
        timestamps, deleted_at).
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS licences (
                        id TEXT PRIMARY KEY,
                        cle TEXT UNIQUE,
                        type TEXT,
                        date_activation DATETIME,
                        date_expiration DATETIME,
                        signature TEXT,
                        active INTEGER DEFAULT 1,
                        entreprise_id TEXT,
                        created_at DATETIME,
                        updated_at DATETIME,
                        deleted_at DATETIME
                    )
                """))
                conn.commit()
                # Ensure compatibility column name `entreprise_id` exists (some DBs used `enterprise_id`)
                cols = [r[1] for r in conn.execute(text("PRAGMA table_info('licences')")).fetchall()]
                if 'entreprise_id' not in cols:
                    try:
                        conn.execute(text("ALTER TABLE licences ADD COLUMN entreprise_id TEXT"))
                        # copy values if enterprise_id exists
                        if 'enterprise_id' in cols:
                            conn.execute(text("UPDATE licences SET entreprise_id = enterprise_id WHERE entreprise_id IS NULL OR entreprise_id = ''"))
                        conn.commit()
                        print('Migrated licences table: added entreprise_id column')
                    except Exception:
                        pass
            print("✅ Migration : table licences OK (created if missing)")
        except Exception as e:
            print(f"⚠️ _migrate_licences_table : {e}")
        # If an older singular `licence` table exists (legacy schema), copy its rows
        # into the new `licences` table so both schemas remain compatible.
        try:
            with self.engine.connect() as conn:
                res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='licence'"))
                row = res.fetchone()
                if row:
                    # Only copy if licences is empty (avoid duplicate imports)
                    count = conn.execute(text("SELECT COUNT(*) FROM licences")).fetchone()[0]
                    if count == 0:
                        print("ℹ️ Found legacy table `licence`, migrating rows to `licences`...")
                        # Copy rows; generate a textual id to avoid PK collisions with UUIDs
                        conn.execute(text("INSERT INTO licences (id, cle, type, date_activation, date_expiration, signature, active, enterprise_id, created_at, updated_at) \nSELECT 'local-' || id, cle, type, date_activation, date_expiration, signature, active, entreprise_id, date_activation, date_activation FROM licence"))
                        conn.commit()
                        print("✅ Migration: copied legacy `licence` -> `licences` (ids prefixed with 'local-')")
                    else:
                        print("ℹ️ Legacy `licence` detected but `licences` already contains data; skipping copy")
        except Exception as e:
            print(f"⚠️ _migrate_licences_table (legacy copy) : {e}")

    def _migrate_init_compta_configs(self):
        """Migration idempotente : crée un ComptaConfig par défaut pour tout POS
        qui n'en possède pas encore, en utilisant les comptes par défaut (is_default=True)
        déjà présents dans la base."""
        try:
            with self.session_scope() as session:
                enterprises = session.query(Entreprise).all()
                for enterprise in enterprises:
                    pos_list = session.query(POSPoint).filter_by(enterprise_id=enterprise.id).all()
                    for pos in pos_list:
                        existing = session.query(ComptaConfig).filter_by(
                            enterprise_id=enterprise.id,
                            pos_id=pos.id
                        ).first()
                        if existing:
                            continue

                        def _default_compte(numero):
                            compte = (
                                session.query(ComptaComptes)
                                .join(ComptaClasses)
                                .filter(
                                    ComptaClasses.enterprise_id == enterprise.id,
                                    ComptaComptes.numero == numero
                                )
                                .first()
                            )
                            return compte.id if compte else None

                        config = ComptaConfig(
                            enterprise_id=enterprise.id,
                            pos_id=pos.id,
                            compte_caisse_id=_default_compte("571"),
                            compte_banque_id=_default_compte("521"),
                            compte_client_id=_default_compte("411"),
                            compte_fournisseur_id=_default_compte("401"),
                            compte_fournisseur_debiteur_id=_default_compte("409"),
                            compte_vente_id=_default_compte("701"),
                            compte_achat_id=_default_compte("601"),
                            compte_stock_id=_default_compte("301"),
                            compte_tva_id=_default_compte("4431"),
                            compte_remise_id=_default_compte("682"),
                        )
                        session.add(config)
                        try:
                            print(f"✅ ComptaConfig initialisé pour POS: {pos.name} (entreprise {enterprise.id})")
                        except Exception:
                            pass
        except Exception as e:
            print(f"⚠️ _migrate_init_compta_configs : {e}")

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
    # Modules accessibles pour l'utilisateur (JSON list stored as TEXT)
    modules = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    enterprise = relationship("Entreprise", back_populates="users")
    
    def set_password(self, password):
        """Hasher le mot de passe"""
        # If the provided value already looks like a bcrypt hash, store it verbatim
        # to avoid double-hashing when applying server-provided hashes.
        try:
            if isinstance(password, str) and re.match(r'^\$2[aby]\$.{56}$', password):
                # Normalize $2y$ -> $2b$ for local bcrypt compatibility but keep the hash
                if password.startswith('$2y$'):
                    self.password = '$2b$' + password[4:]
                else:
                    self.password = password
                return
        except Exception:
            pass

        # Otherwise hash the plaintext password
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Vérifier le mot de passe"""
        # Some servers (PHP bcrypt) emit hashes with the $2y$ prefix.
        # Python's bcrypt expects $2b$ in many distributions — normalize for verification
        stored = (self.password or '')
        try:
            if stored.startswith('$2y$'):
                stored_norm = '$2b$' + stored[4:]
            else:
                stored_norm = stored
            return bcrypt.checkpw(password.encode('utf-8'), stored_norm.encode('utf-8'))
        except Exception:
            # Fallback: try raw stored value (in case normalization unnecessary)
            try:
                return bcrypt.checkpw(password.encode('utf-8'), stored.encode('utf-8'))
            except Exception:
                return False

    # Helper accessors for modules list (stored as JSON in Text column)
    def get_modules_list(self):
        try:
            if not self.modules:
                return []
            return json.loads(self.modules)
        except Exception:
            return []

    def set_modules_list(self, modules_list):
        try:
            if modules_list is None:
                self.modules = None
            else:
                # ensure serializable list of strings
                self.modules = json.dumps([str(m) for m in modules_list])
        except Exception:
            # fallback: store as str
            try:
                self.modules = str(modules_list)
            except Exception:
                self.modules = None



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


class PaymentMode(Base):
    """Modes de paiement configurables par entreprise.

    Les 4 modes par défaut (Espèces, Banque, Mobile Money, Crédit) sont
    protégés contre la suppression (is_default=True).
    Chaque mode peut être associé à un compte comptable de caisse/trésorerie
    qui sera débité à l'encaissement et crédité au décaissement.
    """
    __tablename__ = "core_payment_modes"
    __table_args__ = {'extend_existing': True}

    id              = Column(Integer, primary_key=True, autoincrement=True)
    enterprise_id   = Column(Integer, ForeignKey('core_enterprises.id'), nullable=False)
    code            = Column(String(50), nullable=False)          # ex: cash, banque, mobile_money, credit
    label           = Column(String(150), nullable=False)         # libellé affiché
    # Sous-label / description libre (ex: noms des opérateurs mobiles)
    description     = Column(Text, nullable=True)
    # Compte comptable associé (ID de compta_comptes)
    compte_id       = Column(Integer, nullable=True)
    # Libellé du compte pour affichage rapide sans jointure
    compte_label    = Column(String(200), nullable=True)
    is_default      = Column(Integer, default=0)   # 1 = mode protégé, non supprimable
    is_active       = Column(Integer, default=1)   # 0 = désactivé
    sort_order      = Column(Integer, default=0)
    created_at      = Column(DateTime, default=datetime.utcnow)



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
