"""
Diagnostic login script for Sync API.
Usage:
  python scripts/login_debug.py            # uses saved config
  python scripts/login_debug.py email pw   # use explicit credentials

Prints request/response details to help debug 4xx/5xx and auth failures.
"""
import sys
import json
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.utils.sync_manager import SyncManager
import requests


def run_with_config():
    db = DatabaseManager(database_url='sqlite:///ayanna_erp.db')
    sm = SyncManager(db.engine)
    cfg = sm.get_config()
    if not cfg or not cfg.get('server_url'):
        print('No saved server_url in configuration')
        return
    email = cfg.get('server_email')
    pw = cfg.get('server_password')
    return try_login(cfg.get('server_url'), email, pw)


def try_login(server_url, email, password):
    url = server_url.rstrip('/') + '/api/auth/login'
    print('POST', url)
    payload = {'email': email, 'password': password}
    print('Payload:', payload)
    try:
        resp = requests.post(url, json=payload, headers={'Accept': 'application/json'}, timeout=15)
        print('Status:', resp.status_code)
        try:
            print('JSON response:', json.dumps(resp.json(), ensure_ascii=False, indent=2))
        except Exception:
            print('Response text:', resp.text[:1000])
        print('Headers:', dict(resp.headers))
        resp.raise_for_status()
        print('Login OK')
        return resp
    except requests.exceptions.HTTPError as e:
        resp = e.response
        print('HTTPError:', e)
        if resp is not None:
            print('Status:', resp.status_code)
            try:
                print('JSON:', json.dumps(resp.json(), ensure_ascii=False, indent=2))
            except Exception:
                print('Body:', resp.text[:2000])
        raise
    except Exception as e:
        print('Error:', e)
        raise


if __name__ == '__main__':
    if len(sys.argv) >= 3:
        _, email, pw = sys.argv[:3]
        db = DatabaseManager(database_url='sqlite:///ayanna_erp.db')
        sm = SyncManager(db.engine)
        settings = sm.get_settings()
        server_url = (sm.get_config() or {}).get('server_url') or (settings.api_url if settings else None)
        if not server_url:
            print('Server URL not configured. Use save_config or provide full URL.')
        else:
            try_login(server_url, email, pw)
    else:
        run_with_config()
