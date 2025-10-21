import sys
sys.path.insert(0, r'c:\Ayanna ERP\Ayanna-Erp')
from ayanna_erp.modules.salle_fete.controller.service_controller import ServiceController

controller = ServiceController()
try:
    result = controller.get_service_recent_usage(1, 5)
    print(f'Success: {len(result)} usages trouvés')
    for usage in result[:2]:
        print(f'Date: {usage["event_date"]}, Client: {usage["client_name"]}, Source: {usage["source"]}')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()