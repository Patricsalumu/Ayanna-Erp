from ayanna_erp.database.database_manager import DatabaseManager


def test_database_manager_accepts_mysql_url():
    manager = DatabaseManager("mysql+pymysql://user:pass@localhost:3306/ayanna_erp")

    assert manager.engine.url.get_backend_name() == "mysql"
    assert manager.engine.pool.__class__.__name__ != "StaticPool"
