import sys
import traceback
sys.path.append(r'c:\Ayanna ERP\Ayanna-Erp')

from ayanna_erp.modules.boutique.controller.commande_controller import CommandeController

c = CommandeController()

print('--- get_commandes (dernieres) ---')
cmds = c.get_commandes(limit=10)
print('Found', len(cmds), 'commandes')
for i,cmd in enumerate(cmds[:5],1):
    print(i, cmd.get('id'), cmd.get('numero_commande'), cmd.get('module'))

# Attempt to pay panier id 1
try:
    panier_id = 1
    print('\n--- process_restaurant_payment on panier', panier_id)
    ok, msg = c.process_restaurant_payment(panier_id=panier_id, payment_method='Cash', amount=100, current_user=type('U',(object,),{'id':1})())
    print('Result:', ok, msg)
except Exception as e:
    traceback.print_exc()

# Attempt to cancel panier id 2
try:
    panier_cancel = 2
    print('\n--- cancel_restaurant_commande on panier', panier_cancel)
    ok2, msg2 = c.cancel_restaurant_commande(panier_cancel, current_user=type('U',(object,),{'id':1})())
    print('Result:', ok2, msg2)
except Exception as e:
    traceback.print_exc()

print('\nDone')
