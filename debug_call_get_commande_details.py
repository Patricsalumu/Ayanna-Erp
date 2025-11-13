import sys
sys.path.append(r'c:\Ayanna ERP\Ayanna-Erp')
from ayanna_erp.modules.boutique.controller.commande_controller import CommandeController

c = CommandeController()
print('Appel get_commandes()...')
cmds = c.get_commandes(limit=10)
print('Found', len(cmds), 'commandes')
restau_cmds = [cmd for cmd in cmds if cmd.get('module')=='restaurant']
print('Restaurant commandes:', len(restau_cmds))
if restau_cmds:
    cid = restau_cmds[0]['id']
    print('Appel get_commande_details pour id=', cid)
    details = c.get_commande_details(cid)
    print('Détails:', details)
else:
    print('Aucune commande restaurant trouvée; créer une via le test si besoin')
