from ayanna_erp.utils.sync_manager import SyncManager

sm = SyncManager.__new__(SyncManager)

def fake_get_id_mapping(table_name, local_id=None, server_id=None):
    print('called fake_get_id_mapping', table_name, local_id, server_id)
    if server_id is not None:
        return None
    mapping = {('core_enterprises','7'): 'enterprise-uuid', ('core_users','2'): 'user-uuid'}
    return mapping.get((table_name, str(local_id)))

sm._get_id_mapping = fake_get_id_mapping
sm._remember_id_mapping = lambda *args, **kwargs: None
op = {
    'table': 'core_users',
    'operation': 'INSERT',
    'data': {'id': 99, 'enterprise_id': 7, 'user_id': 2, 'name': 'Test'},
}
prepared = sm._prepare_operation_for_server(op)
print('prepared', prepared)
