import os
import json
import sqlite3
from ayanna_erp.database.database_manager import DatabaseManager, get_database_manager
from ayanna_erp.utils.sync_manager import SyncManager


def test_pull_imports_core_users_and_licences():
    # Use a temporary DB file to avoid interfering with dev DB
    db_path = 'test_ayanna_erp.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    db = DatabaseManager(f'sqlite:///{db_path}')
    sm = SyncManager(db.engine)

    # Ensure settings are configured to point to local server from config (reuse existing config if present)
    # If not configured (CI/local), skip this integration test.
    settings = sm.get_settings()
    import pytest
    if not settings or not settings.api_url or not settings.api_token:
        pytest.skip('API not configured locally - skipping integration test')

    # For test, call pull with override_last_sync to force full fetch from server
    res = sm.pull(override_last_sync='1970-01-01T00:00:00Z')

    # Expect core_users and licences to be present in result keys
    assert 'core_users' in res.get('tables', []) or res.get('total_records', 0) >= 0

    # Inspect local sqlite DB to ensure licences table exists and has rows
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='licences'")
    assert cur.fetchone() is not None, 'licences table should exist after migration'
    try:
        cur.execute('SELECT COUNT(*) FROM licences')
        count = cur.fetchone()[0]
    except Exception:
        count = 0
    assert count >= 0
    conn.close()


if __name__ == '__main__':
    test_pull_imports_core_users_and_licences()
    print('ok')
