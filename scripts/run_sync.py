from ayanna_erp.database.database_manager import get_database_manager
from ayanna_erp.utils.sync_manager import SyncManager
import json, traceback

if __name__ == '__main__':
    dbm = get_database_manager()
    sm = SyncManager(dbm.engine)
    try:
        res = sm.synchronize()
        print(json.dumps(res, ensure_ascii=False, indent=2))
    except Exception as e:
        print('EXCEPTION:', e)
        traceback.print_exc()
