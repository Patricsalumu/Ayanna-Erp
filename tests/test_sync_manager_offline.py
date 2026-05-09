import os
import sqlite3
import json
import types
from datetime import datetime
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.utils.sync_manager import SyncManager


def test_pull_offline_with_mock(monkeypatch, tmp_path):
    # Prepare temporary DB
    db_file = tmp_path / 'offline_test.db'
    db_path = f'sqlite:///{db_file}'
    if db_file.exists():
        os.remove(db_file)

    db = DatabaseManager(db_path)
    sm = SyncManager(db.engine)

    # Create minimal tables expected by SyncManager upserts
    sqlite_path = str(db_file)
    conn = sqlite3.connect(sqlite_path)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS core_users (
            id TEXT PRIMARY KEY,
            enterprise_id TEXT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT NOT NULL,
            created_at DATETIME,
            updated_at DATETIME,
            deleted_at DATETIME
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS licences (
            id TEXT PRIMARY KEY,
            cle TEXT UNIQUE,
            type TEXT,
            date_activation DATETIME,
            date_expiration DATETIME,
            signature TEXT,
            active INTEGER DEFAULT 1,
            enterprise_id TEXT,
            created_at DATETIME,
            updated_at DATETIME,
            deleted_at DATETIME
        )
    ''')
    conn.commit()
    conn.close()

    # Prepare mocked server payload
    server_time = '2026-05-07T00:00:00Z'
    core_users = [
        {
            'id': '1',
            'enterprise_id': '1',
            'name': 'Mock Admin',
            'email': 'admin@mock.test',
            'password': '$2y$12$MOCKHASHPASSWORD',
            'created_at': '2026-05-07T00:00:00.000000Z',
            'updated_at': '2026-05-07T00:00:00.000000Z',
            'deleted_at': None,
        }
    ]
    licences = [
        {
            'id': '11111111-1111-1111-1111-111111111111',
            'cle': 'OFFLINE-TEST-KEY',
            'type': 'trial',
            'date_activation': '2026-05-07T00:00:00.000000Z',
            'date_expiration': '2026-06-07T00:00:00.000000Z',
            'signature': 'SIGMOCK',
            'active': 1,
            'enterprise_id': None,
            'created_at': '2026-05-07T00:00:00.000000Z',
            'updated_at': '2026-05-07T00:00:00.000000Z',
            'deleted_at': None,
        }
    ]
    payload = {'server_time': server_time, 'data': {'core_users': core_users, 'licences': licences}}

    class MockResp:
        def __init__(self, payload):
            self._payload = payload
            self.status_code = 200
        def raise_for_status(self):
            return None
        def json(self):
            return self._payload

    # Patch settings and requests.get
    fake_settings = types.SimpleNamespace(api_url='http://mock', api_token='token')
    monkeypatch.setattr(sm, 'get_settings', lambda: fake_settings)
    monkeypatch.setattr('requests.get', lambda *a, **k: MockResp(payload))

    # Run pull (should use mocked response)
    res = sm.pull(override_last_sync='1970-01-01T00:00:00Z')

    # Assert licences imported and core_users password preserved
    conn = sqlite3.connect(sqlite_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM licences")
    licence_count = cur.fetchone()[0]
    cur.execute("SELECT password FROM core_users WHERE email=?", ('admin@mock.test',))
    row = cur.fetchone()
    conn.close()

    assert licence_count == 1, 'Licence row should be imported'
    assert row is not None and row[0] == '$2y$12$MOCKHASHPASSWORD', 'Password hash must be stored verbatim'
