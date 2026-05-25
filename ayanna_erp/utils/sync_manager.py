"""
Gestionnaire de synchronisation API pour Ayanna ERP
====================================================
Gere la table core_sync (journal local) et la communication
push/pull avec le serveur Laravel (POST /api/sync/push,
GET /api/sync/pull).

TIMEZONE
--------
Le serveur stocke toutes les dates en UTC.
L'application locale travaille en UTC+1 (fuseau Afrique
centrale / Afrique de l'Ouest).
- Chaque entree core_sync est horodatee en UTC+1.
- Le champ last_sync est stocke en UTC+1 pour affichage.
- Avant tout appel API, last_sync est converti en UTC.
- Les dates recues lors d'un pull sont converties UTC -> UTC+1
  avant insertion dans SQLite local.
"""

import json
import os
from pathlib import Path
import requests
from datetime import datetime, timezone, timedelta
from contextlib import contextmanager

from sqlalchemy import Column, Integer, String, Text, text
from sqlalchemy.orm import sessionmaker

from ayanna_erp.database.base import Base

# ---------------------------------------------------------------------------
# Chiffrement Fernet (AES-128-CBC + HMAC-SHA256)
# La cle est generee une seule fois et stockee dans data/sync.key
# ---------------------------------------------------------------------------
try:
    from cryptography.fernet import Fernet as _Fernet
    _CRYPTO_AVAILABLE = True
except ImportError:
    _CRYPTO_AVAILABLE = False

_KEY_FILE = Path(__file__).parent.parent.parent / 'data' / 'sync.key'


def _get_fernet():
    """Charge ou genere la cle Fernet pour le chiffrement local."""
    if not _CRYPTO_AVAILABLE:
        return None
    _KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if _KEY_FILE.exists():
        key = _KEY_FILE.read_bytes().strip()
    else:
        key = _Fernet.generate_key()
        _KEY_FILE.write_bytes(key)
    return _Fernet(key)


def _encrypt(value: str) -> str:
    """Chiffre une chaine avec Fernet. Retourne '' si vide ou crypto absent."""
    if not value:
        return ''
    f = _get_fernet()
    if f is None:
        return value  # fallback si cryptography absent
    return f.encrypt(value.encode('utf-8')).decode('utf-8')


def _decrypt(value: str) -> str:
    """Dechiffre une chaine Fernet. Retourne '' en cas d'erreur."""
    if not value:
        return ''
    f = _get_fernet()
    if f is None:
        return value  # fallback si cryptography absent
    try:
        return f.decrypt(value.encode('utf-8')).decode('utf-8')
    except Exception:
        return ''  # Cle changee ou donnee corrompue

# ---------------------------------------------------------------------------
# Fuseau horaire local : UTC+1
# ---------------------------------------------------------------------------

TZ_UTC1 = timezone(timedelta(hours=1))

_DATETIME_FIELDS = frozenset({
    'created_at', 'updated_at', 'deleted_at', 'synced_at',
    'date_activation', 'date_expiration', 'date_vente',
    'date_commande', 'date_reception', 'date_livraison',
    'date_naissance', 'date_inventaire', 'date_validation',
    'date_operation', 'date_mouvement', 'date_debut', 'date_fin',
    'check_in', 'check_out',
})


def _utc_now() -> datetime:
    """Heure courante en UTC."""
    return datetime.now(timezone.utc)


def _local_now() -> datetime:
    """Heure courante en UTC+1."""
    return datetime.now(TZ_UTC1)


def _local_now_iso() -> str:
    """Heure courante UTC+1 en ISO 8601 sans micro-secondes."""
    return _local_now().strftime('%Y-%m-%dT%H:%M:%S+01:00')


def _utc_to_local(dt: datetime) -> datetime:
    """Convertit un datetime UTC en UTC+1."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(TZ_UTC1)


def _local_to_utc(dt: datetime) -> datetime:
    """Convertit un datetime UTC+1 en UTC."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ_UTC1)
    return dt.astimezone(timezone.utc)


def _parse_iso(value: str) -> datetime | None:
    """Parse une chaine ISO 8601 en datetime (avec tzinfo)."""
    try:
        clean = value.replace('Z', '+00:00')
        dt = datetime.fromisoformat(clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Modele SQLAlchemy : core_sync
# ---------------------------------------------------------------------------

class CoreSync(Base):
    """
    Journal des modifications locales en attente de synchronisation.

    Chaque INSERT ou UPDATE effectue dans l'application locale
    doit etre enregistre ici via SyncManager.record_change().
    Le champ synced indique si l'operation a ete envoyee au serveur :
        0 = en attente
        1 = synchronisee
    """
    __tablename__ = 'core_sync'

    id          = Column(Integer, primary_key=True, autoincrement=True)
    table_name  = Column(String(100), nullable=False)
    operation   = Column(String(10),  nullable=False)   # INSERT | UPDATE
    record_id   = Column(Text,        nullable=False)   # UUID de la ligne modifiee
    data_json   = Column(Text,        nullable=False)   # Snapshot JSON complet
    synced      = Column(Integer,     nullable=False, default=0)
    sync_error  = Column(Text,        nullable=True)    # Erreur du dernier essai
    created_at  = Column(Text,        nullable=False)   # UTC+1 ISO 8601
    created_by  = Column(Text,        nullable=True)    # Nom utilisateur
    synced_at   = Column(Text,        nullable=True)    # Date sync UTC+1


# ---------------------------------------------------------------------------
# Modele SQLAlchemy : core_sync_settings (conserve pour compatibilite)
# ---------------------------------------------------------------------------

class CoreSyncSettings(Base):
    """
    Parametres internes de synchronisation (token Bearer + last_sync).
    Usage interne uniquement. La configuration utilisateur est dans CoreConfigSync.
    """
    __tablename__ = 'core_sync_settings'

    id                 = Column(Integer, primary_key=True, default=1)
    api_url            = Column(Text, nullable=True)
    api_token          = Column(Text, nullable=True)
    last_sync          = Column(Text, nullable=True)   # UTC+1 ISO 8601
    last_sync_status   = Column(String(20), nullable=True)
    last_sync_message  = Column(Text, nullable=True)


# ---------------------------------------------------------------------------
# Modele SQLAlchemy : core_configsync  (configuration utilisateur chiffree)
# ---------------------------------------------------------------------------

class CoreConfigSync(Base):
    """
    Configuration de la connexion au serveur et historique des synchronisations.

    Les champs server_url, server_email, server_password et api_token
    sont chiffres en base avec Fernet (AES-128-CBC + HMAC).
    La cle de chiffrement est dans data/sync.key (non versionnee).

    Un seul enregistrement (id=1) est maintenu dans cette table.
    """
    __tablename__ = 'core_configsync'

    id               = Column(Integer, primary_key=True, default=1)
    # Champs chiffres
    server_url       = Column(Text, nullable=True)   # chiffre
    server_email     = Column(Text, nullable=True)   # chiffre
    server_password  = Column(Text, nullable=True)   # chiffre
    api_token        = Column(Text, nullable=True)   # chiffre
    # Historique de la derniere synchronisation
    last_sync_at     = Column(Text, nullable=True)   # UTC+1 ISO 8601
    last_sync_by     = Column(Text, nullable=True)   # nom/email utilisateur
    last_sync_status = Column(String(20), nullable=True)   # success|partial|error
    last_sync_message= Column(Text, nullable=True)


# ---------------------------------------------------------------------------
# Modele SQLAlchemy : core_sync_history  (historique push / pull)
# ---------------------------------------------------------------------------

class CoreSyncHistory(Base):
    """
    Historique des operations de synchronisation.

    Un enregistrement est cree apres chaque push ou pull reussi.
    Permet d'afficher dans l'UI l'historique complet des echanges
    avec le serveur (direction, tables touchees, volume, statut).
    """
    __tablename__ = 'core_sync_history'

    id              = Column(Integer, primary_key=True, autoincrement=True)
    direction       = Column(String(10),  nullable=False)   # push | pull
    tables_affected = Column(Text,        nullable=True)    # JSON {table: count}
    records_count   = Column(Integer,     nullable=False, default=0)
    push_sent       = Column(Integer,     nullable=True)    # push uniquement
    push_success    = Column(Integer,     nullable=True)    # push uniquement
    push_errors     = Column(Integer,     nullable=True)    # push uniquement
    status          = Column(String(20),  nullable=False)   # success|partial|error
    triggered_by    = Column(Text,        nullable=True)    # utilisateur
    error_message   = Column(Text,        nullable=True)
    created_at      = Column(Text,        nullable=False)   # UTC+1 ISO 8601


# ---------------------------------------------------------------------------
# SyncManager
# ---------------------------------------------------------------------------

class SyncManager:
    """
    Gestionnaire de synchronisation bidirectionnelle.

    Usage typique :
        sm = SyncManager(engine)
        sm.save_settings('http://192.168.1.10:8000')
        sm.login('admin@ayanna.com', 'motdepasse')
        # ... apres chaque INSERT/UPDATE local :
        sm.record_change('shop_clients', 'INSERT', client_id, client_dict)
        # ... pour synchroniser :
        result = sm.synchronize()
    """

    def __init__(self, engine):
        self.engine = engine
        self.SessionLocal = sessionmaker(
            bind=engine, autocommit=False, autoflush=False
        )
        # Creer les tables si elles n'existent pas encore
        Base.metadata.create_all(
            bind=engine,
            tables=[
                CoreSync.__table__,
                CoreSyncSettings.__table__,
                CoreConfigSync.__table__,
                CoreSyncHistory.__table__,
            ],
            checkfirst=True,
        )

    # -----------------------------------------------------------------------
    # Context manager de session
    # -----------------------------------------------------------------------

    @contextmanager
    def _session_scope(self):
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # -----------------------------------------------------------------------
    # Parametres API
    # -----------------------------------------------------------------------

    def get_settings(self):
        """Retourne les parametres de synchronisation (ligne unique id=1).

        Retourne un SimpleNamespace avec les memes attributs que CoreSyncSettings
        (api_url, api_token, last_sync, last_sync_status, last_sync_message) ou
        None si aucune ligne n'existe.  Les valeurs sont copiees pendant que la
        session est encore ouverte pour eviter les DetachedInstanceError.
        """
        import types
        with self._session_scope() as session:
            row = session.query(CoreSyncSettings).filter_by(id=1).first()
            if row is None:
                return None
            return types.SimpleNamespace(
                id=row.id,
                api_url=row.api_url,
                api_token=row.api_token,
                last_sync=row.last_sync,
                last_sync_status=row.last_sync_status,
                last_sync_message=row.last_sync_message,
            )

    def save_settings(self, api_url: str, api_token: str = None):
        """Cree ou met a jour l'URL et (optionnellement) le token."""
        with self._session_scope() as session:
            settings = session.query(CoreSyncSettings).filter_by(id=1).first()
            if settings is None:
                settings = CoreSyncSettings(id=1, api_url=api_url, api_token=api_token)
                session.add(settings)
            else:
                settings.api_url = api_url
                if api_token is not None:
                    settings.api_token = api_token

    def save_token(self, api_token: str):
        """Met a jour uniquement le token Bearer."""
        with self._session_scope() as session:
            settings = session.query(CoreSyncSettings).filter_by(id=1).first()
            if settings is None:
                settings = CoreSyncSettings(id=1, api_token=api_token)
                session.add(settings)
            else:
                settings.api_token = api_token

    def is_configured(self) -> bool:
        """Retourne True si l'URL et le token sont configures."""
        cfg = self.get_config()
        if cfg and cfg.get('server_url') and cfg.get('api_token'):
            return True
        settings = self.get_settings()
        return bool(settings and settings.api_url and settings.api_token)

    # -----------------------------------------------------------------------
    # Configuration chiffree (core_configsync)
    # -----------------------------------------------------------------------

    def save_config(
        self,
        server_url: str,
        server_email: str,
        server_password: str,
        last_sync_by: str = None,
    ):
        """
        Sauvegarde la configuration de connexion dans core_configsync.
        L'URL, l'email et le mot de passe sont chiffres avec Fernet.

        Args:
            server_url:      URL du serveur (ex: http://192.168.1.10:8000).
            server_email:    Adresse e-mail de connexion.
            server_password: Mot de passe en clair (sera chiffre avant stockage).
            last_sync_by:    Nom de l'utilisateur (optionnel).
        """
        with self._session_scope() as session:
            cfg = session.query(CoreConfigSync).filter_by(id=1).first()
            if cfg is None:
                cfg = CoreConfigSync(id=1)
                session.add(cfg)
            cfg.server_url      = _encrypt(server_url.strip())
            cfg.server_email    = _encrypt(server_email.strip())
            cfg.server_password = _encrypt(server_password)
            if last_sync_by:
                cfg.last_sync_by = last_sync_by
        # Mettre a jour aussi core_sync_settings pour compatibilite
        self.save_settings(server_url.strip())

    def get_config(self) -> dict | None:
        """
        Retourne la configuration dechiffree sous forme de dictionnaire ::

            {
                'server_url':       str,
                'server_email':     str,
                'server_password':  str,
                'api_token':        str | None,
                'last_sync_at':     str | None,
                'last_sync_by':     str | None,
                'last_sync_status': str | None,
                'last_sync_message':str | None,
            }

        Retourne None si aucune configuration n'a ete sauvegardee.
        """
        with self._session_scope() as session:
            cfg = session.query(CoreConfigSync).filter_by(id=1).first()
            if cfg is None:
                return None
            return {
                'server_url':        _decrypt(cfg.server_url or ''),
                'server_email':      _decrypt(cfg.server_email or ''),
                'server_password':   _decrypt(cfg.server_password or ''),
                'api_token':         _decrypt(cfg.api_token or ''),
                'last_sync_at':      cfg.last_sync_at,
                'last_sync_by':      cfg.last_sync_by,
                'last_sync_status':  cfg.last_sync_status,
                'last_sync_message': cfg.last_sync_message,
            }

    def _update_config_after_sync(
        self,
        status: str,
        message: str,
        synced_by: str = None,
        token: str = None,
    ):
        """Met a jour core_configsync apres une synchronisation."""
        now = _local_now_iso()
        with self._session_scope() as session:
            cfg = session.query(CoreConfigSync).filter_by(id=1).first()
            if cfg:
                cfg.last_sync_at     = now
                cfg.last_sync_status = status
                cfg.last_sync_message= message
                if synced_by:
                    cfg.last_sync_by = synced_by
                if token:
                    cfg.api_token = _encrypt(token)

    # -----------------------------------------------------------------------
    # Authentification
    # -----------------------------------------------------------------------

    def login(self, email: str = None, password: str = None) -> str:
        """
        S'authentifie aupres du serveur et sauvegarde le token Bearer.

        Si email et password ne sont pas fournis, utilise les identifiants
        stockes dans core_configsync (chiffres).

        Returns:
            Token Bearer sous forme de chaine.
        Raises:
            RuntimeError si api_url ou les identifiants sont manquants.
            requests.HTTPError en cas d'echec HTTP.
        """
        # Charger depuis la config chiffree si non fournis
        if email is None or password is None:
            cfg = self.get_config()
            if cfg:
                email    = email    or cfg.get('server_email', '')
                password = password or cfg.get('server_password', '')

        settings = self.get_settings()
        # Priorite : CoreConfigSync.server_url > CoreSyncSettings.api_url
        cfg = self.get_config()
        api_url = (cfg.get('server_url') if cfg else None) or (
            settings.api_url if settings else None
        )
        if not api_url:
            raise RuntimeError(
                "URL serveur non configuree. Ouvrir Configuration > Synchronisation."
            )
        if not email or not password:
            raise RuntimeError(
                "Identifiants manquants. Ouvrir Configuration > Synchronisation."
            )

        resp = requests.post(
            f"{api_url.rstrip('/')}/api/auth/login",
            json={'email': email, 'password': password},
            headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
            timeout=15,
        )
        resp.raise_for_status()
        token = resp.json()['token']
        self.save_token(token)
        # Sauvegarder le token chiffre dans core_configsync aussi
        self._update_config_after_sync(
            status='token_ok',
            message='Authentification reussie',
            token=token,
        )
        print('[SyncManager] Authentification reussie. Token sauvegarde.')
        return token

    def register_server_user(
        self,
        name: str,
        email: str,
        password: str,
        role: str = 'admin',
    ) -> str:
        """
        Cree un premier compte utilisateur sur le serveur via POST /api/auth/register.

        Utile au premier demarrage quand la base serveur est vide.
        Sauvegarde automatiquement le token retourne.

        Args:
            name:     Nom complet (ex: 'Admin Ayanna').
            email:    Adresse e-mail.
            password: Mot de passe (min 8 caracteres).
            role:     Role sur le serveur (defaut 'admin').

        Returns:
            Token Bearer sous forme de chaine.
        Raises:
            RuntimeError si l'URL serveur n'est pas configuree.
            requests.HTTPError en cas d'erreur HTTP (ex: email deja pris).
        """
        cfg = self.get_config()
        settings = self.get_settings()
        api_url = (cfg.get('server_url') if cfg else None) or (
            settings.api_url if settings else None
        )
        if not api_url:
            raise RuntimeError(
                "URL serveur non configuree. Enregistrer d'abord la configuration."
            )

        resp = requests.post(
            f"{api_url.rstrip('/')}/api/auth/register",
            json={
                'name':                  name,
                'email':                 email,
                'password':              password,
                'password_confirmation': password,
                'role':                  role,
            },
            headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
            timeout=15,
        )
        if not resp.ok:
            # Extraire le detail de l'erreur depuis la reponse JSON si possible
            try:
                err_body = resp.json()
                detail = err_body.get('message') or err_body.get('error') or str(err_body)
            except Exception:
                detail = resp.text[:300] if resp.text else resp.reason
            raise RuntimeError(
                f"Erreur serveur ({resp.status_code}) lors de la creation du compte : {detail}"
            )
        resp.raise_for_status()
        token = resp.json()['token']
        self.save_token(token)
        self._update_config_after_sync(
            status='token_ok',
            message=f'Compte serveur cree : {email}',
            token=token,
        )
        print(f'[SyncManager] Compte serveur cree pour {email}. Token sauvegarde.')
        return token

    # -----------------------------------------------------------------------
    # Enregistrement des changements locaux
    # -----------------------------------------------------------------------

    def record_change(
        self,
        table_name: str,
        operation: str,
        record_id,
        data: dict,
        created_by: str = None,
    ):
        """
        Enregistre un INSERT ou UPDATE local dans core_sync.

        A appeler apres chaque creation ou modification d'un enregistrement
        dans l'application locale.

        Args:
            table_name:  Nom de la table SQLite concernee (ex: 'shop_clients').
            operation:   'INSERT' ou 'UPDATE'.
            record_id:   Identifiant (UUID) de la ligne modifiee.
            data:        Dictionnaire complet de l'enregistrement.
            created_by:  Nom ou email de l'utilisateur connecte (optionnel).

        Raises:
            ValueError si operation n'est pas 'INSERT' ou 'UPDATE'.
        """
        if operation not in ('INSERT', 'UPDATE'):
            raise ValueError(
                f"operation doit etre 'INSERT' ou 'UPDATE', recu: {operation!r}"
            )

        with self._session_scope() as session:
            entry = CoreSync(
                table_name=table_name,
                operation=operation,
                record_id=str(record_id),
                data_json=json.dumps(data, ensure_ascii=False, default=str),
                synced=0,
                created_at=_local_now_iso(),
                created_by=created_by or '',
            )
            session.add(entry)

    # -----------------------------------------------------------------------
    # Operations en attente
    # -----------------------------------------------------------------------

    def get_pending_operations(self) -> list[dict]:
        """
        Retourne la liste des entrees core_sync non synchronisees,
        triees par date croissante, sous la forme attendue par l'API.
        """
        with self._session_scope() as session:
            entries = (
                session.query(CoreSync)
                .filter(CoreSync.synced == 0)
                .order_by(CoreSync.created_at)
                .all()
            )
            result = []
            for e in entries:
                try:
                    data = json.loads(e.data_json)
                except Exception:
                    data = {}
                # Le serveur Laravel valide data.id comme string (UUID)
                # → forcer la conversion pour eviter un 422
                if 'id' in data:
                    data['id'] = str(data['id'])
                # Do not push password hashes to server (avoid server double-hashing)
                if e.table_name == 'core_users' and 'password' in data:
                    try:
                        del data['password']
                    except Exception:
                        pass
                result.append({
                    '_sync_id':  e.id,           # usage interne uniquement
                    'table':     e.table_name,
                    'operation': e.operation,
                    'data':      data,
                    'client_updated_at': e.created_at,
                })
            return result

    def pending_count(self) -> int:
        """Retourne le nombre d'operations locales en attente."""
        with self._session_scope() as session:
            return session.query(CoreSync).filter(CoreSync.synced == 0).count()

    # -----------------------------------------------------------------------
    # PUSH
    # -----------------------------------------------------------------------

    def push(self, triggered_by: str = None) -> dict:
        """
        Envoie au serveur toutes les operations locales en attente.

        Appelle POST /api/sync/push avec un lot d'operations.
        Marque synced=1 les entrees reussies.
        Les entrees en erreur conservent synced=0 et recoivent sync_error.

        Returns:
            {'sent': int, 'success': int, 'errors': list}
        Raises:
            RuntimeError si les parametres API sont manquants.
            requests.HTTPError en cas d'erreur HTTP non recuperable.
        """
        settings = self.get_settings()
        if not settings or not settings.api_url or not settings.api_token:
            raise RuntimeError(
                "Parametres API manquants. Configurer api_url et api_token."
            )

        pending = self.get_pending_operations()
        if not pending:
            print("[SyncManager] PUSH : aucune operation en attente.")
            return {'sent': 0, 'success': 0, 'errors': []}

        # Calculer les tables touchees
        tables_affected: dict[str, int] = {}
        for op in pending:
            t = op['table']
            tables_affected[t] = tables_affected.get(t, 0) + 1

        # Construire le payload sans le champ interne _sync_id
        operations = [
            {k: v for k, v in op.items() if k != '_sync_id'}
            for op in pending
        ]
        sync_ids = [op['_sync_id'] for op in pending]

        headers = {
            'Authorization': f"Bearer {settings.api_token}",
            'Content-Type':  'application/json',
            'Accept':        'application/json',
        }

        resp = requests.post(
            f"{settings.api_url.rstrip('/')}/api/sync/push",
            json={'operations': operations},
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()

        # Identifier les record_id en erreur renvoyees par le serveur
        error_by_id: dict[str, str] = {}
        for err in result.get('errors', []):
            rid = str(err.get('id', ''))
            if rid:
                error_by_id[rid] = err.get('error', 'Erreur inconnue')

        now_iso = _local_now_iso()

        with self._session_scope() as session:
            for op, sync_id in zip(pending, sync_ids):
                entry = session.query(CoreSync).filter_by(id=sync_id).first()
                if entry is None:
                    continue
                rid = str(op['data'].get('id', ''))
                if rid in error_by_id:
                    entry.sync_error = error_by_id[rid]
                    # synced reste 0 → sera retente au prochain cycle
                else:
                    entry.synced    = 1
                    entry.synced_at = now_iso
                    entry.sync_error = None

        sent = len(pending)
        success = result.get('success', sent - len(error_by_id))
        errors_list = result.get('errors', [])
        print(
            f"[SyncManager] PUSH : {sent} envoyes, "
            f"{success} reussis, {len(errors_list)} erreurs."
        )
        self._log_history(
            direction='push',
            tables_affected=tables_affected,
            records_count=sent,
            status='partial' if errors_list else 'success',
            triggered_by=triggered_by,
            push_sent=sent,
            push_success=success,
            push_errors=len(errors_list),
        )
        return {'sent': sent, 'success': success, 'errors': errors_list}

    # -----------------------------------------------------------------------
    # PULL
    # -----------------------------------------------------------------------

    def pull(self, triggered_by: str = None, override_last_sync: str = None) -> dict:
        """
        Recupere du serveur tous les enregistrements modifies depuis last_sync
        et les applique dans la base locale (upsert ou suppression douce).

        - Les dates serveur (UTC) sont converties en UTC+1 avant insertion locale.
        - server_time est converti en UTC+1 et sauvegarde comme nouveau last_sync.
        - override_last_sync : si fourni, utilise ce timestamp au lieu de settings.last_sync
          (utile pour eviter l'echo des enregistrements venant d'etre pousse).

        Returns:
            {'server_time': str, 'tables': list, 'total_records': int}
        Raises:
            RuntimeError si les parametres API sont manquants.
        """
        settings = self.get_settings()
        if not settings or not settings.api_url or not settings.api_token:
            raise RuntimeError("Parametres API manquants.")

        headers = {
            'Authorization': f"Bearer {settings.api_token}",
            'Accept':        'application/json',
        }

        # Determiner last_sync effectif : override > settings.last_sync
        effective_last_sync = override_last_sync or settings.last_sync

        params = {}
        if effective_last_sync:
            # last_sync est stocke en UTC+1 -> convertir en UTC pour l'API
            dt_local = _parse_iso(effective_last_sync)
            if dt_local:
                params['last_sync'] = _local_to_utc(dt_local).strftime(
                    '%Y-%m-%dT%H:%M:%SZ'
                )
            else:
                params['last_sync'] = effective_last_sync

        resp = requests.get(
            f"{settings.api_url.rstrip('/')}/api/sync/pull",
            params=params,
            headers=headers,
            timeout=60,
        )
        resp.raise_for_status()
        payload = resp.json()

        server_time_raw = payload.get('server_time', _utc_now().isoformat())
        data            = payload.get('data', {})

        total_records   = 0
        tables_updated  = []
        tables_counts: dict[str, int] = {}

        # Appliquer les donnees dans SQLite local
        with self.engine.connect() as conn:
            # Cache du type de la colonne id par table (INTEGER ou autre)
            _id_type_cache: dict[str, str] = {}

            def _get_id_col_type(table: str) -> str:
                if table not in _id_type_cache:
                    try:
                        rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
                        for row in rows:
                            if row[1] == 'id':
                                _id_type_cache[table] = (row[2] or '').upper()
                                break
                        else:
                            _id_type_cache[table] = 'TEXT'
                    except Exception:
                        _id_type_cache[table] = 'TEXT'
                return _id_type_cache[table]
            for table_name, records in data.items():
                if not records:
                    continue
                tables_updated.append(table_name)

                for record in records:
                    if not isinstance(record, dict):
                        continue
                    total_records += 1
                    tables_counts[table_name] = tables_counts.get(table_name, 0) + 1

                    # Conversion UTC -> UTC+1 sur les champs datetime
                    record = self._convert_timestamps(record)

                    # Injecter des valeurs par defaut pour certaines colonnes locales
                    # qui sont NOT NULL mais peuvent etre absentes du payload serveur.
                    # Pour `core_users.password` : conserver le hash envoyé par le
                    # serveur si present. Si absent, tenter de reutiliser le password
                    # local existant (si la ligne existe), sinon generer un hash bcrypt
                    # aléatoire en dernier recours pour satisfaire la contrainte NOT NULL.
                    defaults_map = {
                        'compta_classes': {
                            'date_creation': lambda r: r.get('created_at') or _local_now().strftime('%Y-%m-%d %H:%M:%S'),
                            'date_modification': lambda r: r.get('updated_at') or _local_now().strftime('%Y-%m-%d %H:%M:%S'),
                        },
                        'compta_comptes': {
                            'date_creation': lambda r: r.get('created_at') or _local_now().strftime('%Y-%m-%d %H:%M:%S'),
                            'date_modification': lambda r: r.get('updated_at') or _local_now().strftime('%Y-%m-%d %H:%M:%S'),
                        },
                    }
                    if table_name in defaults_map:
                        for col, fn in defaults_map[table_name].items():
                            try:
                                if col not in record or record.get(col) is None:
                                    record[col] = fn(record)
                                    print(f"[SyncManager] Injected default {col} for {table_name}/{record.get('id')}")
                            except Exception:
                                pass

                    # Respecter strictement le mot de passe envoye par le serveur.
                    # Ne pas generer/reutiliser de mot de passe local si absent.
                    if table_name == 'core_users':
                        pw = record.get('password', None)
                        if pw in (None, ''):
                            print(f"[SyncManager] Warning: core_users/{record.get('email') or record.get('id')} has no password in server payload — will not inject defaults.")

                    if record.get('deleted_at'):
                        # Suppression douce locale
                        try:
                            conn.execute(
                                text(f"DELETE FROM {table_name} WHERE id = :id"),
                                {'id': record['id']},
                            )
                        except Exception as e:
                            print(
                                f"[SyncManager] PULL DELETE {table_name}/"
                                f"{record.get('id')}: {e}"
                            )
                    else:
                        # Upsert SQLite
                        # Recompute cols AFTER potential mapping/pop of 'id'
                        # (mapping code above may have removed 'id').
                        # We'll compute cols and record_id below, after mapping.

                        # Si l'id serveur est un UUID (chaine avec tirets) et la colonne
                        # id locale est INTEGER, tenter de faire un mapping sur une
                        # cle naturelle (ex: email pour core_users, name/email pour
                        # core_enterprises). Sinon supprimer 'id' pour laisser
                        # l'INTEGER autoincrement local creer une nouvelle ligne.
                        orig_id = record.get('id')
                        if isinstance(orig_id, str) and '-' in orig_id:
                            id_type = _get_id_col_type(table_name)
                            if 'INT' in id_type:
                                try:
                                    if table_name == 'core_users' and record.get('email'):
                                        res = conn.execute(
                                            text("SELECT id FROM core_users WHERE email = :email"),
                                            {'email': record.get('email')}
                                        ).fetchone()
                                        if res:
                                            record['id'] = res[0]
                                            print(f"[SyncManager] Mapped UUID id -> local id {res[0]} for core_users/{record.get('email')}")
                                        else:
                                            record.pop('id', None)
                                            print(f"[SyncManager] Dropped UUID id for core_users/{record.get('email')} to allow local autoincrement")
                                    elif table_name == 'core_enterprises':
                                        key = record.get('email') or record.get('name')
                                        if key:
                                            res = conn.execute(
                                                text("SELECT id FROM core_enterprises WHERE email = :email OR name = :name"),
                                                {'email': record.get('email') or '', 'name': record.get('name') or ''}
                                            ).fetchone()
                                            if res:
                                                record['id'] = res[0]
                                                print(f"[SyncManager] Mapped UUID id -> local id {res[0]} for core_enterprises/{key}")
                                            else:
                                                record.pop('id', None)
                                                print(f"[SyncManager] Dropped UUID id for core_enterprises/{key} to allow local autoincrement")
                                        else:
                                            record.pop('id', None)
                                    else:
                                        # Aucun mapping connu -> supprimer l'id pour inserer
                                        record.pop('id', None)
                                except Exception:
                                    # En cas d'erreur lors du mapping, tomber en safe-mode
                                    record.pop('id', None)
                            # Map licences' enterprise_id: if missing or null, assign the first local enterprise id
                            if table_name in ('licences', 'licence'):
                                try:
                                    ent = conn.execute(text("SELECT id FROM core_enterprises ORDER BY id LIMIT 1")).fetchone()
                                    if ent and not record.get('enterprise_id') and not record.get('entreprise_id'):
                                        # Use server field enterprise_id but map to local 'entreprise_id'
                                        record['entreprise_id'] = ent[0]
                                        print(f"[SyncManager] Assigned local entreprise_id {ent[0]} for {table_name}/{record.get('id')}")
                                except Exception:
                                    pass

                        # Note: certains champs obligatoires peuvent avoir ete
                        # injectes ci-dessus (ex: core_users.password,
                        # compta_*.date_creation). Les colonnes utilisees pour
                        # l'INSERT/UPDATE sont celles presentes dans le dict.

                        # Recompute columns now that record may have changed
                        # Map server-side column names to local column names when needed
                        if table_name in ('licences', 'licence') and 'enterprise_id' in record and 'entreprise_id' not in record:
                            try:
                                record['entreprise_id'] = record.pop('enterprise_id')
                            except Exception:
                                pass

                        cols  = [c for c in record.keys() if record[c] is not None]
                        record_id = record.get('id') if 'id' in cols else None

                        vals         = {c: record[c] for c in cols}
                        cols_str     = ', '.join(cols)
                        placeholders = ', '.join([f':{c}' for c in cols])
                        updates      = ', '.join(
                            [f'{c} = :{c}' for c in cols if c != 'id']
                        )
                        if record_id is None:
                            # Pas d'id fourni (ou supprimé pour autoincrement) -> simple INSERT
                            sql = f"INSERT OR IGNORE INTO {table_name} ({cols_str}) VALUES ({placeholders})"
                        else:
                            if not updates:
                                # Rien a mettre a jour (id seulement)
                                sql = (
                                    f"INSERT OR IGNORE INTO {table_name} ({cols_str}) "
                                    f"VALUES ({placeholders})"
                                )
                            else:
                                sql = (
                                    f"INSERT INTO {table_name} ({cols_str}) "
                                    f"VALUES ({placeholders}) "
                                    f"ON CONFLICT(id) DO UPDATE SET {updates}"
                                )
                        try:
                            conn.execute(text(sql), vals)
                        except Exception as e:
                            err_text = str(e)
                            print(
                                f"[SyncManager] PULL UPSERT {table_name}/"
                                f"{record.get('id')}: {e}"
                            )
                            # 1) Handle missing column -> apply migrations and retry
                            if 'has no column named' in err_text or 'no such column' in err_text:
                                try:
                                    print('[SyncManager] Detected missing column error — applying local migrations and retrying upsert...')
                                    try:
                                        from ayanna_erp.database.database_manager import get_database_manager
                                        dbm = get_database_manager()
                                        for fn in (
                                            '_migrate_updated_at_columns',
                                            '_migrate_compta_timestamps',
                                            '_migrate_payment_modes_table',
                                            '_migrate_compta_journal_validation',
                                            '_migrate_compta_config_fournisseur_debiteur',
                                            '_migrate_livraison_tables',
                                        ):
                                            try:
                                                if hasattr(dbm, fn):
                                                    getattr(dbm, fn)()
                                            except Exception:
                                                pass
                                    except Exception:
                                        pass

                                    try:
                                        conn.execute(text(sql), vals)
                                    except Exception as e2:
                                        print(f"[SyncManager] Retried upsert failed for {table_name}/{record.get('id')}: {e2}")
                                except Exception:
                                    pass
                            # 2) Handle NOT NULL constraint failures by injecting defaults and retrying once
                            elif 'NOT NULL constraint failed' in err_text:
                                try:
                                    # Parse column name from message: '... failed: schema.table.column' or '... failed: table.column'
                                    parts = err_text.split(':')[-1].strip().split('.')
                                    missing_col = parts[-1] if parts else None
                                    if missing_col:
                                        # Simple default rules
                                        if missing_col in ('date_creation', 'date_modification', 'date_validation') or missing_col.endswith('_at') or missing_col.startswith('date'):
                                            record[missing_col] = record.get('updated_at') or record.get('created_at') or _local_now().strftime('%Y-%m-%d %H:%M:%S')
                                        elif missing_col == 'password':
                                            # Do not inject default password; server must provide the hash.
                                            print(f"[SyncManager] NOT NULL failure on password for {table_name}/{record.get('id')} — server must provide password hash. Skipping retry.")
                                            # Skip retry for this record
                                            continue
                                        else:
                                            # fallback to empty string
                                            record[missing_col] = ''
                                        print(f"[SyncManager] Injected default {missing_col} for {table_name}/{record.get('id')} after NOT NULL failure")

                                        # Rebuild cols/vals/sql then retry once
                                        # Rebuild cols/vals/sql after injecting default
                                        cols  = [c for c in record.keys() if record[c] is not None]
                                        record_id = record.get('id') if 'id' in cols else None
                                        vals         = {c: record[c] for c in cols}
                                        cols_str     = ', '.join(cols)
                                        placeholders = ', '.join([f':{c}' for c in cols])
                                        updates      = ', '.join([f'{c} = :{c}' for c in cols if c != 'id'])
                                        if record_id is None:
                                            retry_sql = f"INSERT OR IGNORE INTO {table_name} ({cols_str}) VALUES ({placeholders})"
                                        else:
                                            if not updates:
                                                retry_sql = f"INSERT OR IGNORE INTO {table_name} ({cols_str}) VALUES ({placeholders})"
                                            else:
                                                retry_sql = (
                                                    f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders}) ON CONFLICT(id) DO UPDATE SET {updates}"
                                                )
                                        try:
                                            conn.execute(text(retry_sql), vals)
                                        except Exception as e3:
                                            print(f"[SyncManager] Retry after NOT NULL injection failed for {table_name}/{record.get('id')}: {e3}")
                                except Exception:
                                    pass
            conn.commit()

        # Calculer new_last_sync en UTC+1
        dt_server = _parse_iso(server_time_raw)
        if dt_server:
            new_last_sync = _utc_to_local(dt_server).strftime('%Y-%m-%dT%H:%M:%S+01:00')
        else:
            new_last_sync = _local_now_iso()

        # Sauvegarder le nouveau last_sync
        with self._session_scope() as session:
            s = session.query(CoreSyncSettings).filter_by(id=1).first()
            if s:
                s.last_sync = new_last_sync
                s.last_sync_status  = 'success'
                s.last_sync_message = (
                    f"{total_records} enregistrement(s) recus de "
                    f"{len(tables_updated)} table(s)"
                )

        print(
            f"[SyncManager] PULL : {total_records} enregistrements recus "
            f"({'|'.join(tables_updated) or 'aucune modification'}). "
            f"last_sync = {new_last_sync}"
        )
        self._log_history(
            direction='pull',
            tables_affected=tables_counts,
            records_count=total_records,
            status='success',
            triggered_by=triggered_by,
        )
        return {
            'server_time':   new_last_sync,
            'tables':        tables_updated,
            'total_records': total_records,
        }

    # -----------------------------------------------------------------------
    # Synchronisation complete
    # -----------------------------------------------------------------------

    def synchronize(self, synced_by: str = None) -> dict:
        """
        Cycle complet : PUSH puis PULL.

        Les erreurs de PUSH n'empechent pas le PULL.

        Args:
            synced_by: Nom/email de l'utilisateur qui lance la sync.
                       Si None, recupere depuis SessionManager.

        Returns:
            {'push': dict, 'pull': dict}
        """
        # Recuperer l'utilisateur courant si non fourni
        if synced_by is None:
            try:
                from ayanna_erp.core.session_manager import SessionManager
                user = SessionManager.get_current_user()
                if user:
                    synced_by = getattr(user, 'name', None) or getattr(user, 'email', None)
            except Exception:
                pass

        push_result = {'sent': 0, 'success': 0, 'errors': []}
        pull_result = {'server_time': None, 'tables': [], 'total_records': 0}
        final_status  = 'success'
        final_message = ''

        # Capturer le timestamp AVANT le push pour l'utiliser comme last_sync du pull.
        # Cela evite que le serveur renvoie en pull les enregistrements
        # qu'on vient de lui envoyer en push (echo).
        pre_push_time = _local_now_iso()

        # 1. PUSH
        try:
            push_result = self.push(triggered_by=synced_by)
            if push_result.get('errors'):
                final_status = 'partial'
        except Exception as e:
            print(f'[SyncManager] PUSH echoue : {e}')
            self._save_status('error', f'PUSH echoue : {e}')
            final_status  = 'error'
            final_message = f'PUSH echoue : {e}'

        # 2. PULL
        # On utilise toujours pre_push_time comme borne inférieure du pull :
        #   - évite que le serveur renvoie en echo les enregistrements qu'on vient
        #     de lui pousser (ils ont updated_at >= début du push)
        #   - les changements serveur arrivés AVANT pre_push_time sont couverts
        #     par le last_sync précédent ; ceux arrivés APRÈS seront inclus dans
        #     ce pull car server_time (capturé avant la requête côté serveur) sera
        #     légèrement en avance sur pre_push_time.
        # Exception : première sync (pas de last_sync) — on prend aussi pre_push_time
        # pour ne pas rapatrier toute la base du serveur en boucle.
        pull_override = pre_push_time
        try:
            pull_result = self.pull(triggered_by=synced_by, override_last_sync=pull_override)
        except Exception as e:
            print(f'[SyncManager] PULL echoue : {e}')
            self._save_status('error', f'PULL echoue : {e}')
            if final_status != 'error':
                final_status  = 'error'
                final_message = f'PULL echoue : {e}'

        if not final_message:
            p = push_result
            r = pull_result
            final_message = (
                f"Push : {p.get('success', 0)}/{p.get('sent', 0)} envoyes. "
                f"Pull : {r.get('total_records', 0)} enregistrements recus."
            )

        # Mettre a jour core_configsync
        self._update_config_after_sync(
            status=final_status,
            message=final_message,
            synced_by=synced_by,
        )

        return {'push': push_result, 'pull': pull_result}

    # -----------------------------------------------------------------------
    # Initialisation du journal local (premier demarrage)
    # -----------------------------------------------------------------------

    # Tables internes au moteur de sync — exclues de l'initialisation
    _SYNC_INTERNAL_TABLES = frozenset({
        'core_sync', 'core_sync_settings', 'core_configsync',
        'core_sync_history', 'licence', 'modules',
    })

    def initialize_sync(
        self,
        created_by: str = None,
        extra_exclude: set = None,
    ) -> dict:
        """
        Enfile toutes les donnees locales existantes dans core_sync comme
        INSERT en attente (synced=0).

        A appeler UNE seule fois au premier demarrage, avant le premier push,
        pour que toutes les donnees locales soient envoyees au serveur.

        Les lignes deja presentes dans core_sync (meme record_id + table)
        ne sont PAS re-enfilees pour eviter les doublons.

        Args:
            created_by:    Nom de l'utilisateur (optionnel).
            extra_exclude: Ensemble de noms de tables supplementaires a ignorer.

        Returns:
            {'tables': {table_name: nb_enqueued}, 'total': int}
        """
        from sqlalchemy import inspect as sa_inspect, text as sa_text

        exclude = self._SYNC_INTERNAL_TABLES.copy()
        if extra_exclude:
            exclude.update(extra_exclude)

        inspector  = sa_inspect(self.engine)
        all_tables = inspector.get_table_names()
        now        = _local_now_iso()
        by         = created_by or ''

        tables_result: dict[str, int] = {}
        total = 0

        with self.engine.connect() as conn:
            # Recup les (table_name, record_id) deja presents dans core_sync
            existing_rows = conn.execute(
                sa_text("SELECT table_name, record_id FROM core_sync")
            ).fetchall()
            existing_keys: set[tuple] = {(r[0], str(r[1])) for r in existing_rows}

            for table in all_tables:
                if table in exclude or table.startswith('sqlite_'):
                    continue

                # Verifier que la table a une colonne 'id'
                cols = [c['name'] for c in inspector.get_columns(table)]
                if 'id' not in cols:
                    continue

                rows = conn.execute(sa_text(f"SELECT * FROM {table}")).fetchall()
                if not rows:
                    continue

                enqueued = 0
                for row in rows:
                    row_dict = dict(zip(cols, row))
                    rid = str(row_dict.get('id', ''))
                    if not rid:
                        continue
                    if (table, rid) in existing_keys:
                        continue  # deja en queue, on saute

                    conn.execute(
                        sa_text(
                            "INSERT INTO core_sync "
                            "(table_name, operation, record_id, data_json, "
                            " synced, created_at, created_by) "
                            "VALUES (:tbl, 'INSERT', :rid, :data, 0, :ts, :by)"
                        ),
                        {
                            'tbl':  table,
                            'rid':  rid,
                            'data': __import__('json').dumps(
                                row_dict, ensure_ascii=False, default=str
                            ),
                            'ts':   now,
                            'by':   by,
                        },
                    )
                    existing_keys.add((table, rid))
                    enqueued += 1

                if enqueued:
                    tables_result[table] = enqueued
                    total += enqueued

            conn.commit()

        print(
            f"[SyncManager] initialize_sync : {total} enregistrement(s) enfiles "
            f"depuis {len(tables_result)} table(s)."
        )
        return {'tables': tables_result, 'total': total}

    # -----------------------------------------------------------------------
    # Statistiques
    # -----------------------------------------------------------------------

    def get_stats(self) -> dict:
        """Retourne des statistiques sur l'etat de la synchronisation."""
        with self._session_scope() as session:
            total   = session.query(CoreSync).count()
            pending = session.query(CoreSync).filter(CoreSync.synced == 0).count()
            synced  = session.query(CoreSync).filter(CoreSync.synced == 1).count()
            failed  = session.query(CoreSync).filter(
                CoreSync.synced == 0,
                CoreSync.sync_error.isnot(None),
            ).count()
            settings = session.query(CoreSyncSettings).filter_by(id=1).first()
            cfg      = session.query(CoreConfigSync).filter_by(id=1).first()
            # Priorite aux donnees de CoreConfigSync
            last_sync_at  = (cfg.last_sync_at     if cfg else None) or (settings.last_sync if settings else None)
            last_status   = (cfg.last_sync_status  if cfg else None) or (settings.last_sync_status  if settings else None)
            last_message  = (cfg.last_sync_message if cfg else None) or (settings.last_sync_message if settings else None)
            api_configured = bool(
                (cfg and cfg.server_url and cfg.api_token)
                or (settings and settings.api_url and settings.api_token)
            )
            return {
                'total':             total,
                'pending':           pending,
                'synced':            synced,
                'failed':            failed,
                'last_sync':         last_sync_at,
                'last_sync_at':      last_sync_at,
                'last_sync_by':      cfg.last_sync_by if cfg else None,
                'last_sync_status':  last_status,
                'last_sync_message': last_message,
                'api_configured':    api_configured,
            }

    # -----------------------------------------------------------------------
    # Helpers internes
    # -----------------------------------------------------------------------

    def _save_status(self, status: str, message: str):
        try:
            with self._session_scope() as session:
                s = session.query(CoreSyncSettings).filter_by(id=1).first()
                if s:
                    s.last_sync_status  = status
                    s.last_sync_message = message
        except Exception:
            pass

    @staticmethod
    def _convert_timestamps(record: dict) -> dict:
        """
        Convertit les champs datetime UTC en UTC+1 dans un dict de donnees.
        Les champs dont le nom se termine par _at ou appartiennent a la liste
        _DATETIME_FIELDS sont traites.
        """
        result = {}
        for key, value in record.items():
            if (
                value
                and isinstance(value, str)
                and (key in _DATETIME_FIELDS or key.endswith('_at'))
            ):
                dt = _parse_iso(value)
                if dt is not None:
                    result[key] = _utc_to_local(dt).strftime('%Y-%m-%d %H:%M:%S')
                    continue
            result[key] = value
        return result

    def _log_history(
        self,
        direction: str,
        tables_affected: dict,
        records_count: int,
        status: str,
        triggered_by: str = None,
        error_message: str = None,
        push_sent: int = None,
        push_success: int = None,
        push_errors: int = None,
    ):
        """Enregistre une entree dans core_sync_history."""
        try:
            with self._session_scope() as session:
                entry = CoreSyncHistory(
                    direction=direction,
                    tables_affected=json.dumps(tables_affected, ensure_ascii=False),
                    records_count=records_count,
                    push_sent=push_sent,
                    push_success=push_success,
                    push_errors=push_errors,
                    status=status,
                    triggered_by=triggered_by,
                    error_message=error_message,
                    created_at=_local_now_iso(),
                )
                session.add(entry)
        except Exception as e:
            print(f'[SyncManager] _log_history echoue : {e}')

    # -----------------------------------------------------------------------
    # Historique des synchronisations
    # -----------------------------------------------------------------------

    def get_history(self, limit: int = 50) -> list[dict]:
        """
        Retourne les dernieres entrees de core_sync_history, triees par date desc.

        Args:
            limit: Nombre maximum d'entrees a retourner (defaut 50).

        Returns:
            Liste de dicts avec les champs ::

                {
                    'id':             int,
                    'direction':      'push' | 'pull',
                    'tables_affected': {table: count, ...},
                    'records_count':  int,
                    'push_sent':      int | None,
                    'push_success':   int | None,
                    'push_errors':    int | None,
                    'status':         'success' | 'partial' | 'error',
                    'triggered_by':   str | None,
                    'error_message':  str | None,
                    'created_at':     str,  # UTC+1 ISO 8601
                }
        """
        with self._session_scope() as session:
            entries = (
                session.query(CoreSyncHistory)
                .order_by(CoreSyncHistory.id.desc())
                .limit(limit)
                .all()
            )
            result = []
            for e in entries:
                try:
                    tables = json.loads(e.tables_affected or '{}')
                except Exception:
                    tables = {}
                result.append({
                    'id':              e.id,
                    'direction':       e.direction,
                    'tables_affected': tables,
                    'records_count':   e.records_count,
                    'push_sent':       e.push_sent,
                    'push_success':    e.push_success,
                    'push_errors':     e.push_errors,
                    'status':          e.status,
                    'triggered_by':    e.triggered_by,
                    'error_message':   e.error_message,
                    'created_at':      e.created_at,
                })
            return result
