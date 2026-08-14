import os
import unittest
from pathlib import Path

from sqlalchemy import text

from ayanna_erp.database.database_manager import DatabaseManager
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


if __name__ == "__main__":
    unittest.main()
