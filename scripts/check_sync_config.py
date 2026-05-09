from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.utils.sync_manager import SyncManager
import traceback

if __name__ == '__main__':
    db = DatabaseManager(database_url='sqlite:///ayanna_erp.db')
    sm = SyncManager(db.engine)
    cfg = sm.get_config()
    print('CONFIG:', cfg)
    s = sm.get_settings()
    if s:
        print('SETTINGS.api_url:', s.api_url)
        print('SETTINGS.has_token:', bool(s.api_token))
    else:
        print('SETTINGS: None')

    try:
        token = sm.login()
        print('LOGIN OK, token length:', len(token))
    except Exception as e:
        print('LOGIN FAILED:', repr(e))
        traceback.print_exc()
