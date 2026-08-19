from ayanna_erp.database.database_manager import DatabaseManager


def test_database_manager_accepts_mysql_url():
    manager = DatabaseManager("mysql+pymysql://user:pass@localhost:3306/ayanna_erp")

    assert manager.engine.url.get_backend_name() == "mysql"
    assert manager.engine.pool.__class__.__name__ != "StaticPool"
    assert manager.engine.pool.size() == 5
    assert manager.engine.pool._max_overflow == 2
    assert manager.engine.pool._recycle == 900
    assert manager.engine.pool._pre_ping is True


def test_database_managers_share_engine_for_same_database_url():
    database_url = "sqlite:///:memory:"
    first_manager = DatabaseManager(database_url)
    second_manager = DatabaseManager(database_url)

    assert first_manager.engine is second_manager.engine
