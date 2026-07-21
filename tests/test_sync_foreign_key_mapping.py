import os
import tempfile
import unittest

from sqlalchemy import text

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.utils.sync_manager import SyncManager


class SyncForeignKeyMappingTest(unittest.TestCase):
    def test_prepare_operation_maps_foreign_ids_to_server_ids(self):
        sm = SyncManager.__new__(SyncManager)

        def fake_get_id_mapping(table_name, local_id=None, server_id=None):
            mapping = {
                ('core_enterprises', '7'): '123e4567-e89b-12d3-a456-426614174000',
                ('core_users', '2'): '123e4567-e89b-12d3-a456-426614174001',
            }
            if server_id is not None:
                return None
            return mapping.get((table_name, str(local_id)))

        sm._get_id_mapping = fake_get_id_mapping
        sm._remember_id_mapping = lambda *args, **kwargs: None

        op = {
            'table': 'core_users',
            'operation': 'INSERT',
            'data': {
                'id': 99,
                'enterprise_id': 7,
                'user_id': 2,
                'name': 'Test',
            },
        }

        prepared = sm._prepare_operation_for_server(op)

        self.assertEqual(prepared['data']['enterprise_id'], '123e4567-e89b-12d3-a456-426614174000')
        self.assertEqual(prepared['data']['user_id'], '123e4567-e89b-12d3-a456-426614174001')

    def test_prepare_operation_maps_pos_id_to_core_pos_points_server_id(self):
        sm = SyncManager.__new__(SyncManager)

        def fake_get_id_mapping(table_name, local_id=None, server_id=None):
            if server_id is not None:
                return None
            if table_name == 'core_pos_points' and str(local_id) == '15':
                return '123e4567-e89b-12d3-a456-426614174010'
            return None

        sm._get_id_mapping = fake_get_id_mapping
        sm._remember_id_mapping = lambda *args, **kwargs: None

        op = {
            'table': 'compta_config',
            'operation': 'INSERT',
            'data': {
                'id': 40,
                'enterprise_id': 7,
                'pos_id': 15,
            },
        }

        prepared = sm._prepare_operation_for_server(op)

        self.assertEqual(prepared['data']['pos_id'], '123e4567-e89b-12d3-a456-426614174010')

    def test_prepare_operation_maps_compta_config_account_ids_to_compta_comptes(self):
        sm = SyncManager.__new__(SyncManager)

        def fake_get_id_mapping(table_name, local_id=None, server_id=None):
            if server_id is not None:
                return None
            if table_name == 'compta_comptes' and str(local_id) == '53':
                return '123e4567-e89b-12d3-a456-426614174053'
            if table_name == 'compta_comptes' and str(local_id) == '49':
                return '123e4567-e89b-12d3-a456-426614174049'
            return None

        sm._get_id_mapping = fake_get_id_mapping
        sm._remember_id_mapping = lambda *args, **kwargs: None

        op = {
            'table': 'compta_config',
            'operation': 'INSERT',
            'data': {
                'id': 10,
                'enterprise_id': 7,
                'pos_id': 15,
                'compte_caisse_id': 53,
                'compte_banque_id': 49,
            },
        }

        prepared = sm._prepare_operation_for_server(op)

        self.assertEqual(prepared['data']['compte_caisse_id'], '123e4567-e89b-12d3-a456-426614174053')
        self.assertEqual(prepared['data']['compte_banque_id'], '123e4567-e89b-12d3-a456-426614174049')

    def test_migrate_updated_at_columns_adds_stock_warehouses_column(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.sqlite')
            manager = DatabaseManager(f'sqlite:///{db_path}')
            try:
                with manager.engine.begin() as conn:
                    conn.execute(text("CREATE TABLE stock_warehouses (id INTEGER PRIMARY KEY, code TEXT)"))

                manager._migrate_updated_at_columns()

                with manager.engine.connect() as conn:
                    cols = [row[1] for row in conn.execute(text('PRAGMA table_info(stock_warehouses)')).fetchall()]

                self.assertIn('updated_at', cols)
            finally:
                manager.engine.dispose()


if __name__ == '__main__':
    unittest.main()
