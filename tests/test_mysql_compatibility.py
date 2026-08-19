import os
import unittest
from pathlib import Path

from sqlalchemy import text

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.boutique.controller.commande_controller import CommandeController
from ayanna_erp.modules.restaurant.views.catalogue_widget import can_user_perform_restaurant_action
from main import _get_database_configuration_from_env, _database_config_path, _save_database_config


class MySQLCompatibilityTests(unittest.TestCase):
    def test_mysql_url_is_accepted(self):
        db = DatabaseManager("mysql+pymysql://user:pass@localhost:3306/insomnia")
        self.assertEqual(db.engine.url.get_backend_name(), "mysql")

    def test_detects_tables_and_columns_without_sqlite_specific_calls(self):
        db = DatabaseManager("sqlite:///:memory:")
        with db.engine.begin() as conn:
            conn.execute(text("CREATE TABLE demo (id INTEGER PRIMARY KEY, name TEXT)"))

        self.assertTrue(db.table_exists("demo"))
        self.assertTrue(db.column_exists("demo", "name"))
        self.assertFalse(db.table_exists("missing_table"))

    def test_first_run_switches_to_false_after_default_seed(self):
        db = DatabaseManager("sqlite:///:memory:")

        self.assertTrue(db.is_first_run())
        self.assertTrue(db.seed_default_data())
        self.assertFalse(db.is_first_run())

    def test_existing_database_url_does_not_prompt(self):
        original = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = "mysql+pymysql://ayanna_user:ChangeThisPassword@127.0.0.1:3306/insomnia"
        try:
            config = _get_database_configuration_from_env()
            self.assertIsNotNone(config)
            self.assertEqual(config[0], "mysql+pymysql://ayanna_user:ChangeThisPassword@127.0.0.1:3306/insomnia")
            self.assertEqual(config[1], "127.0.0.1")
            self.assertEqual(config[2], "insomnia")
        finally:
            if original is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = original

    def test_database_config_file_is_used_for_first_launch_state(self):
        config_path = _database_config_path()
        original = config_path.read_text(encoding='utf-8') if config_path.exists() else None
        try:
            _save_database_config('localhost', 'insomnia', 'ayanna_user', 'secret')
            config = _get_database_configuration_from_env()
            self.assertIsNotNone(config)
            self.assertEqual(config[1], 'localhost')
            self.assertEqual(config[2], 'insomnia')
            self.assertIn('localhost', config[0])
        finally:
            if original is None:
                if config_path.exists():
                    config_path.unlink()
            else:
                config_path.write_text(original, encoding='utf-8')

    def test_database_config_is_stored_outside_the_project_directory(self):
        config_path = _database_config_path()
        project_root = Path(__file__).resolve().parents[1]
        self.assertNotEqual(config_path, project_root / 'database_config.txt')
        self.assertTrue(config_path.name == 'database_config.txt')
        self.assertIn('Ayanna ERP', str(config_path))

    def test_restaurant_permissions_follow_role_rules(self):
        self.assertTrue(can_user_perform_restaurant_action('super_admin', 'commande'))
        self.assertTrue(can_user_perform_restaurant_action('super_admin', 'facturer'))
        self.assertTrue(can_user_perform_restaurant_action('super_admin', 'payer'))
        self.assertTrue(can_user_perform_restaurant_action('super_admin', 'annuler'))

        self.assertTrue(can_user_perform_restaurant_action('serveuse', 'commande'))
        self.assertTrue(can_user_perform_restaurant_action('serveuse', 'facturer'))
        self.assertTrue(can_user_perform_restaurant_action('serveuse', 'payer'))
        self.assertFalse(can_user_perform_restaurant_action('serveuse', 'annuler'))

        self.assertFalse(can_user_perform_restaurant_action('caissier', 'commande'))
        self.assertFalse(can_user_perform_restaurant_action('caissier', 'facturer'))
        self.assertFalse(can_user_perform_restaurant_action('caissier', 'annuler'))
        self.assertTrue(can_user_perform_restaurant_action('caissier', 'payer'))

    def test_mysql_safe_cast_uses_char_instead_of_text(self):
        cast_sql = CommandeController._mysql_safe_cast('rp.id')
        self.assertEqual(cast_sql, 'CAST(rp.id AS CHAR)')
        self.assertNotIn('AS TEXT', cast_sql)

    def test_sales_summary_tables_are_detected_on_empty_database(self):
        db = DatabaseManager("sqlite:///:memory:")
        with db.session_scope() as session:
            tables = CommandeController._sales_summary_tables(session)
            self.assertFalse(tables['shop_paniers'])
            self.assertFalse(tables['restau_paniers'])
            self.assertFalse(tables['core_products'])


if __name__ == "__main__":
    unittest.main()
