"""Service local de gestion des licences

Fournit l'activation et la vérification locale des clés.
"""
import hashlib
import hmac
import os
import datetime
import uuid
from ayanna_erp.database.database_manager import get_database_manager
from ayanna_erp.modules.core.models.licence import Licence
from ayanna_erp.core.session_manager import SessionManager
from ayanna_erp.core.config import Config
from sqlalchemy import text


LICENCE_KEYS = {

    # Mensuel – 30 jours (36)
    "Qm3AYO": {"type": "Mensuel", "duree_jours": 30},
    "LfTR4b": {"type": "Mensuel", "duree_jours": 30},
    "E4fvGb": {"type": "Mensuel", "duree_jours": 30},
    "UCVeIW": {"type": "Mensuel", "duree_jours": 30},
    "4AoMjg": {"type": "Mensuel", "duree_jours": 30},
    "4M3qNT": {"type": "Mensuel", "duree_jours": 30},
    "Ya8IOE": {"type": "Mensuel", "duree_jours": 30},
    "6tQhhF": {"type": "Mensuel", "duree_jours": 30},
    "kI7NGv": {"type": "Mensuel", "duree_jours": 30},
    "6okfnA": {"type": "Mensuel", "duree_jours": 30},
    "XQBUMS": {"type": "Mensuel", "duree_jours": 30},
    "dtYAW3": {"type": "Mensuel", "duree_jours": 30},
    "MpYqYN": {"type": "Mensuel", "duree_jours": 30},
    "qShNwO": {"type": "Mensuel", "duree_jours": 30},
    "wsP3QN": {"type": "Mensuel", "duree_jours": 30},
    "KJksEV": {"type": "Mensuel", "duree_jours": 30},
    "YzlZJw": {"type": "Mensuel", "duree_jours": 30},
    "NskJix": {"type": "Mensuel", "duree_jours": 30},
    "gUvrVQ": {"type": "Mensuel", "duree_jours": 30},
    "ZB7BuU": {"type": "Mensuel", "duree_jours": 30},
    "MaJoNo": {"type": "Mensuel", "duree_jours": 30},
    "WQ7ecb": {"type": "Mensuel", "duree_jours": 30},
    "pm8RBZ": {"type": "Mensuel", "duree_jours": 30},
    "aPCvBK": {"type": "Mensuel", "duree_jours": 30},
    "WajIUb": {"type": "Mensuel", "duree_jours": 30},
    "qOJ1lb": {"type": "Mensuel", "duree_jours": 30},
    "Sl9xVl": {"type": "Mensuel", "duree_jours": 30},
    "FZx9Ad": {"type": "Mensuel", "duree_jours": 30},
    "rTQ8Ym": {"type": "Mensuel", "duree_jours": 30},
    "LkA5eP": {"type": "Mensuel", "duree_jours": 30},
    "EJY7ZB": {"type": "Mensuel", "duree_jours": 30},
    "H6vXKe": {"type": "Mensuel", "duree_jours": 30},
    "bM5YWs": {"type": "Mensuel", "duree_jours": 30},
    "QJd9Aa": {"type": "Mensuel", "duree_jours": 30},
    "sV8mPB": {"type": "Mensuel", "duree_jours": 30},
    "AZy7KQ": {"type": "Mensuel", "duree_jours": 30},

    # Semestriel – 6 mois (180 jours) (20)
    "Sm6KPA": {"type": "Semestriel", "duree_jours": 180},
    "QeY8VA": {"type": "Semestriel", "duree_jours": 180},
    "LpA7QJ": {"type": "Semestriel", "duree_jours": 180},
    "BMK9Ae": {"type": "Semestriel", "duree_jours": 180},
    "yV7EKa": {"type": "Semestriel", "duree_jours": 180},
    "JZq6VP": {"type": "Semestriel", "duree_jours": 180},
    "A9YKeL": {"type": "Semestriel", "duree_jours": 180},
    "xPVB6M": {"type": "Semestriel", "duree_jours": 180},
    "W8sAqB": {"type": "Semestriel", "duree_jours": 180},
    "mKJ6ZA": {"type": "Semestriel", "duree_jours": 180},
    "A7YQPx": {"type": "Semestriel", "duree_jours": 180},
    "6VBPeM": {"type": "Semestriel", "duree_jours": 180},
    "QZK7mA": {"type": "Semestriel", "duree_jours": 180},
    "V9AKYe": {"type": "Semestriel", "duree_jours": 180},
    "MPA6YJ": {"type": "Semestriel", "duree_jours": 180},
    "Z8KAmP": {"type": "Semestriel", "duree_jours": 180},
    "AJP6MY": {"type": "Semestriel", "duree_jours": 180},
    "YKeA7P": {"type": "Semestriel", "duree_jours": 180},
    "mQZ9KA": {"type": "Semestriel", "duree_jours": 180},
    "P7AYKm": {"type": "Semestriel", "duree_jours": 180},

    # Annuel – 365 jours (10)
    "jtHXQ1": {"type": "Annuel", "duree_jours": 365},
    "Dew24Z": {"type": "Annuel", "duree_jours": 365},
    "QLjVVm": {"type": "Annuel", "duree_jours": 365},
    "Csv7wA": {"type": "Annuel", "duree_jours": 365},
    "F5p3hA": {"type": "Annuel", "duree_jours": 365},
    "AKY7PZ": {"type": "Annuel", "duree_jours": 365},
    "MJP6VA": {"type": "Annuel", "duree_jours": 365},
    "ZP9A7K": {"type": "Annuel", "duree_jours": 365},
    "QKAV8P": {"type": "Annuel", "duree_jours": 365},
    "YPA7MK": {"type": "Annuel", "duree_jours": 365},
}


def hash_cle(cle: str) -> str:
    """Hash SHA256 d'une clé pour stockage et comparaison."""
    return hashlib.sha256(cle.encode('utf-8')).hexdigest()


def generer_signature(cle_ou_hash: str, date_expiration: datetime.datetime, deja_hash: bool = False) -> str:
    """Génère une signature numérique à partir du hash de la clé et de la date de fin.

    Si deja_hash=True, cle_ou_hash est le hash déjà stocké.
    """
    # Utilise HMAC-SHA256 avec une CLE_SECRETE (depuis l'environnement ou Config)
    cle_hash = cle_ou_hash if deja_hash else hash_cle(cle_ou_hash)
    base = f"{cle_hash}:{date_expiration.isoformat()}"
    secret = os.getenv('LICENCE_SECRET', None)
    if not secret:
        # essayer Config si défini
        secret = getattr(Config, 'LICENCE_SECRET', None)

    if secret:
        return hmac.new(secret.encode('utf-8'), base.encode('utf-8'), hashlib.sha256).hexdigest()
    # Fallback: simple SHA256 (ancienne méthode)
    return hashlib.sha256(base.encode('utf-8')).hexdigest()


def _now_utc():
    return datetime.datetime.utcnow()


def _normalize(dt: datetime.datetime) -> datetime.datetime:
    return dt.replace(microsecond=0)


def activer_licence(cle: str):
    """Active une licence si la clé est valide et non utilisée.

    Retourne (True, message) ou (False, message).
    """
    infos = LICENCE_KEYS.get(cle)
    if not infos:
        return False, "Clé de licence invalide."

    db_manager = get_database_manager()
    session = db_manager.get_session()
    try:
        cle_hash = hash_cle(cle)
        exist = session.query(Licence).filter_by(cle=cle_hash).first()
        if exist:
            return False, "Cette clé a déjà été utilisée sur cette machine."

        now = _now_utc()
        date_exp = now + datetime.timedelta(days=infos["duree_jours"])
        signature = generer_signature(cle, date_exp)

        # Générer un UUID pour la licence (correspond au schéma serveur)
        local_id = str(uuid.uuid4())

        entreprise_id = SessionManager.get_current_enterprise_id()

        licence = Licence(
            id=local_id,
            cle=cle_hash,
            type=infos["type"],
            date_activation=now,
            date_expiration=date_exp,
            signature=signature,
            active=True,
            entreprise_id=entreprise_id,
        )
        session.add(licence)
        session.commit()
        return True, "Licence activée avec succès."
    except Exception as e:
        session.rollback()
        return False, f"Erreur lors de l'activation: {e}"
    finally:
        session.close()


def verifier_licence():
    """Vérifie la présence d'une licence active locale et l'intégrité de sa signature.

    Retourne (True, message) si valide, sinon (False, message).
    """
    db_manager = get_database_manager()
    session = db_manager.get_session()
    try:
        # Chercher une licence active
        licence = session.query(Licence).filter_by(active=True).order_by(Licence.date_activation.desc()).first()

        # Si aucune licence active trouvée, chercher une licence non expirée
        if not licence:
            now = _normalize(_now_utc())
            licence = session.query(Licence).filter(Licence.date_expiration >= now).order_by(Licence.date_activation.desc()).first()
            if licence:
                licence.active = True
                session.commit()

        if not licence:
            # Fallback: the ORM mapping might not load rows when PK types differ
            # Query the table directly as a last resort.
            try:
                dbm = get_database_manager()
                with dbm.engine.connect() as conn:
                    now = _normalize(_now_utc())
                    row = conn.execute(text("SELECT id, cle, signature, active, date_activation, date_expiration FROM licences WHERE active=1 ORDER BY date_activation DESC LIMIT 1")).fetchone()
                    if not row:
                        # try non-expired
                        row = conn.execute(text("SELECT id, cle, signature, active, date_activation, date_expiration FROM licences WHERE date_expiration >= :now ORDER BY date_activation DESC LIMIT 1"), {"now": now}).fetchone()
                    if not row:
                        return False, "Aucune licence active."
                    # Build a lightweight object-like dict to reuse validation logic below
                    licence = type('L', (), {})()
                    licence.id = row[0]
                    licence.cle = row[1]
                    licence.signature = row[2]
                    licence.active = bool(row[3])
                    from datetime import datetime as _dt
                    licence.date_activation = row[4]
                    de = row[5]
                    if isinstance(de, str):
                        try:
                            licence.date_expiration = _dt.fromisoformat(de)
                        except Exception:
                            try:
                                licence.date_expiration = _dt.strptime(de.split('.')[0], '%Y-%m-%d %H:%M:%S')
                            except Exception:
                                licence.date_expiration = de
                    else:
                        licence.date_expiration = de
                    # Also keep a DB session to persist potential fixes
                    session = dbm.get_session()
            except Exception:
                return False, "Aucune licence active."

        # Vérifier la signature : on calcule la signature attendue avec HMAC (si secret présent)
        signature_attendue = generer_signature(licence.cle, licence.date_expiration, deja_hash=True)
        if licence.signature != signature_attendue:
            # The server may have sent the raw key instead of its stored hash.
            # Try regenerating the signature treating `licence.cle` as raw (not hashed).
            try_alternate = generer_signature(licence.cle, licence.date_expiration, deja_hash=False)
            if licence.signature == try_alternate:
                # Convert stored cle to its hashed form for future checks
                try:
                    cle_hash = hash_cle(licence.cle)
                    licence.cle = cle_hash
                    session.commit()
                except Exception:
                    session.rollback()
            else:
                # Fallback backward-compat: essayer ancienne méthode (SHA256 sans secret)
                base = f"{licence.cle}:{licence.date_expiration.isoformat()}"
                ancienne = hashlib.sha256(base.encode('utf-8')).hexdigest()
                if licence.signature != ancienne:
                    # Si la signature ne correspond pas, on marque la licence inactive (possible modification de la date)
                    licence.active = False
                    session.commit()
                    return False, "Intégrité de la licence compromise (signature invalide)."

        # Vérifier expiration
        now = _normalize(_now_utc())
        if _normalize(licence.date_expiration) < now:
            licence.active = False
            session.commit()
            return False, "La licence a expiré."

        return True, "Licence valide."
    except Exception as e:
        return False, f"Erreur lors de la vérification: {e}"
    finally:
        session.close()
