"""
Fetch /api/sync/pull payload and print core_users and licence sections.
"""
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.utils.sync_manager import SyncManager
import requests, json, sys

DB_URL = 'sqlite:///ayanna_erp.db'

def main():
    db = DatabaseManager(DB_URL)
    sm = SyncManager(db.engine)
    cfg = sm.get_config() or {}
    settings = sm.get_settings()
    api_url = cfg.get('server_url') or (settings.api_url if settings else None)
    api_token = cfg.get('api_token') or (settings.api_token if settings else None)
    if not api_url or not api_token:
        print('No api_url or api_token found in local settings')
        return
    try:
        resp = requests.get(api_url.rstrip('/') + '/api/sync/pull', headers={'Authorization':f'Bearer {api_token}', 'Accept':'application/json'}, params={'last_sync':'full'}, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        data = payload.get('data', {})
        print('--- core_users payload ---')
        print(json.dumps(data.get('core_users', []), ensure_ascii=False, indent=2))
        print('\n--- licence payload ---')
        print(json.dumps(data.get('licence', []), ensure_ascii=False, indent=2))
        print('\n--- top-level keys ---')
        print(list(data.keys()))
    except Exception as e:
        print('Request failed:', repr(e))
        try:
            print('Response text:', resp.text)
        except Exception:
            pass

if __name__ == '__main__':
    main()
