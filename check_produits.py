import sys
sys.path.append('.')
from ayanna_erp.modules.boutique.controller.commande_controller import CommandeController

controller = CommandeController()
commandes = controller.get_commandes(limit=2)

for i, cmd in enumerate(commandes):
    print(f'Commande {i+1}:')
    produits = cmd.get('produits', '')
    print(f'  Produits: {repr(produits)}')
    print(f'  Type: {type(produits)}')

    # Essayer de parser les produits
    if isinstance(produits, str) and produits:
        # Essayer de diviser par des séparateurs courants
        if '\n' in produits:
            items = produits.split('\n')
        elif ', ' in produits:
            items = produits.split(', ')
        elif ';' in produits:
            items = produits.split(';')
        else:
            items = [produits]

        print(f'  Items parsés: {items}')
    print()