from ayanna_erp.database.database_manager import DatabaseManager
from sqlalchemy import text
import bcrypt
from ayanna_erp.core.services.licence_service import hash_cle, generer_signature
from datetime import datetime

CANDIDATE_PASSWORDS = ['admin123']
CANDIDATE_LICENSES = ['Q4444Q','Q588666','Qm3ayq','Qm3AYu','Qm3AYO','Qmllla']


def normalize_bcrypt(stored: str) -> str:
    if not stored:
        return ''
    if stored.startswith('$2y$'):
        return '$2b$' + stored[4:]
    return stored


def check_password(email, candidate, conn):
    r = conn.execute(text("SELECT password FROM core_users WHERE email = :email"), {'email': email}).fetchone()
    if not r:
        return False, 'user not found'
    stored = r[0] or ''
    stored_norm = normalize_bcrypt(stored)
    try:
        ok = bcrypt.checkpw(candidate.encode('utf-8'), stored_norm.encode('utf-8'))
    except Exception:
        ok = False
    return ok, stored


def check_licenses(candidates, conn):
    rows = conn.execute(text('SELECT id, cle, signature, date_expiration FROM licences')).fetchall()
    results = []
    for row in rows:
        lid, cle_stored, signature_stored, date_exp = row
        # date_exp may be string; parse to datetime
        try:
            if isinstance(date_exp, str):
                date_exp_dt = datetime.fromisoformat(date_exp)
            else:
                date_exp_dt = date_exp
        except Exception:
            date_exp_dt = None
        for cand in candidates:
            cand_hash = hash_cle(cand)
            match = False
            reasons = []
            if cle_stored and cand_hash == cle_stored:
                match = True
                reasons.append('cle_hash_match')
            # compare signatures if date_exp known
            if date_exp_dt and signature_stored:
                try:
                    sig_from_hash = generer_signature(cand_hash, date_exp_dt, deja_hash=True)
                    sig_from_raw = generer_signature(cand, date_exp_dt, deja_hash=False)
                    if signature_stored == sig_from_hash:
                        match = True
                        reasons.append('signature_from_hash')
                    if signature_stored == sig_from_raw:
                        match = True
                        reasons.append('signature_from_raw')
                except Exception:
                    pass
            if match:
                results.append({'licence_id': lid, 'candidate': cand, 'reasons': reasons, 'stored_cle': cle_stored, 'stored_signature': signature_stored})
    return results


if __name__ == '__main__':
    db = DatabaseManager('sqlite:///ayanna_erp.db')
    conn = db.engine.connect()
    print('Checking password candidates for admin@ayanna.com')
    for p in CANDIDATE_PASSWORDS:
        ok, stored = check_password('admin@ayanna.com', p, conn)
        print(f"password_candidate='{p}' -> match={ok}")
    print('\nChecking licence candidates:')
    lic_results = check_licenses(CANDIDATE_LICENSES, conn)
    if not lic_results:
        print('No candidate matched any stored licence.')
    else:
        for r in lic_results:
            print(f"Matched candidate '{r['candidate']}' -> licence id={r['licence_id']} reasons={r['reasons']}")
    conn.close()
