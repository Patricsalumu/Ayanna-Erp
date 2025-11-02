"""Service local de gestion des licences

Fournit l'activation et la vérification locale des clés.
"""
import hashlib
import hmac
import os
import datetime
from ayanna_erp.database.database_manager import get_database_manager
from ayanna_erp.modules.core.models.licence import Licence
from ayanna_erp.core.session_manager import SessionManager
from ayanna_erp.core.config import Config


# Dictionnaire des clés pré-remplies (clé: infos)
LICENCE_KEYS = {
    # Démo (4)
    "Qm3AYO": {"type": "Essai", "duree_jours": 30},
    "LfTR4b": {"type": "Essai", "duree_jours": 30},
    "E4fvGb": {"type": "Essai", "duree_jours": 2},
    "UCVeIW": {"type": "Essai", "duree_jours": 2},

    # Mensuel (exemples)
    "4AoMjg": {"type": "Mensuel", "duree_jours": 30},
    "4M3qNT": {"type": "Mensuel", "duree_jours": 30},
    "Ya8IOE": {"type": "Mensuel", "duree_jours": 30},

    # Annuel (exemples)
    "jt0HX0": {"type": "Annuel", "duree_jours": 365},
    "Dew24z": {"type": "Annuel", "duree_jours": 365},
    "QLjVVm": {"type": "Annuel", "duree_jours": 365},
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

        entreprise_id = SessionManager.get_current_enterprise_id()

        licence = Licence(
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
            return False, "Aucune licence active."

        # Vérifier la signature : on calcule la signature attendue avec HMAC (si secret présent)
        signature_attendue = generer_signature(licence.cle, licence.date_expiration, deja_hash=True)
        if licence.signature != signature_attendue:
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
