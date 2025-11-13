"""
Test automatique: panier restaurant -> paiement partiel -> vérification restau_payments -> annulation -> vérification statut
Exécuter: python tests/test_restaurant_flow.py
"""
import sys
import traceback
from datetime import datetime

sys.path.append(r'c:\Ayanna ERP\Ayanna-Erp')

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.restaurant.models.restaurant import RestauPanier, RestauProduitPanier, RestauPayment
from ayanna_erp.modules.boutique.controller.commande_controller import CommandeController
from sqlalchemy import text

# Ensure compta_config table exists to avoid OperationalError in environments without full accounting setup
try:
    from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaConfig
    DB_tmp = DatabaseManager()
    ComptaConfig.__table__.create(bind=DB_tmp.engine, checkfirst=True)
except Exception:
    # If comptabilite module is not available, continue — process_restaurant_payment will still work but may skip accounting
    pass

DB = DatabaseManager()
controller = CommandeController()

SUCCESS = True
errors = []

try:
    with DB.session_scope() as session:
        # Créer un panier restaurant test
        panier = RestauPanier(entreprise_id=1, subtotal=100.0, remise_amount=0.0, total_final=100.0, status='en_cours', user_id=1, notes='Test automatisé')
        session.add(panier)
        session.flush()  # pour obtenir id
        panier_id = panier.id

        # ajouter ligne produit
        prod = RestauProduitPanier(panier_id=panier_id, product_id=1, quantity=1, price=100.0, total=100.0)
        session.add(prod)

        session.commit()

    print(f"Panier créé id={panier_id}")

    # Paiement partiel
    paiement_amount = 40.0
    ok, msg = controller.process_restaurant_payment(panier_id=panier_id, payment_method='Cash', amount=paiement_amount, current_user=type('U',(object,),{'id':1})())
    print('process_restaurant_payment ->', ok, msg)
    if not ok:
        SUCCESS = False
        errors.append(f"process_restaurant_payment failed: {msg}")

    # Vérifier insertion dans restau_payments
    with DB.session_scope() as session:
        res = session.execute(text("SELECT COALESCE(SUM(amount),0) as s FROM restau_payments WHERE panier_id = :pid"), {'pid': panier_id}).fetchone()
        total_paid = res.s if res else 0
        print('Total payé (db):', total_paid)
        if abs(total_paid - paiement_amount) > 0.001:
            SUCCESS = False
            errors.append(f"Restau payments mismatch: expected {paiement_amount}, got {total_paid}")

    # Annuler le panier
    ok2, msg2 = controller.cancel_restaurant_commande(panier_id, current_user=type('U',(object,),{'id':1})())
    print('cancel_restaurant_commande ->', ok2, msg2)
    if not ok2:
        SUCCESS = False
        errors.append(f"cancel_restaurant_commande failed: {msg2}")

    # Vérifier statut
    with DB.session_scope() as session:
        row = session.execute(text("SELECT status FROM restau_paniers WHERE id = :pid"), {'pid': panier_id}).fetchone()
        status = row.status if row else None
        print('Statut après annulation:', status)
        if status is None or status.lower() != 'cancelled':
            SUCCESS = False
            errors.append(f"Statut inattendu après annulation: {status}")

    # --- Impression 53mm : générer un ticket pour le panier restaurant et vérifier le PDF ---
    try:
        import tempfile
        import os
        from ayanna_erp.modules.boutique.utils.invoice_printer import InvoicePrintManager

        # Construire des données minimales d'invoice similaires à l'UI
        invoice_data = {
            'module': 'restaurant',
            'reference': f"PANIER-{panier_id}",
            'client_nom': 'Client test',
            'order_date': datetime.now(),
            'items': [{
                'name': 'Produit test',
                'quantity': 1,
                'unit_price': 100.0
            }],
            'subtotal_ht': 100.0,
            'total_net': 100.0,
            'total_ttc': 100.0,
            'discount_amount': 0.0,
            'notes': 'Impression test 53mm',
            # Restaurant-specific metadata
            'table': '1',
            'salle': 'Salle A',
            'serveuse': 'Serveuse Test',
            'comptoiriste': 'Comptoir Test',
            'payments': [{
                'payment_date': datetime.now(),
                'amount': paiement_amount,
                'payment_method': 'Cash',
                'user_name': 'TestUser'
            }]
        }

        tmpf = tempfile.NamedTemporaryFile(prefix='test_receipt_', suffix='.pdf', delete=False)
        tmpf.close()
        mgr = InvoicePrintManager(enterprise_id=1)
        result_file = mgr.print_receipt_53mm(invoice_data, invoice_data.get('payments', []), 'TestUser', tmpf.name)
        print('print_receipt_53mm returned:', result_file)
        if not result_file or not os.path.exists(result_file):
            SUCCESS = False
            errors.append(f"Impression 53mm a échoué, fichier non créé: {result_file}")
        else:
            print('Ticket 53mm généré:', result_file)
            # Optionnel : supprimer le fichier de test
            try:
                os.unlink(result_file)
            except Exception:
                pass
    except Exception as e:
        SUCCESS = False
        errors.append(f"Erreur impression 53mm: {e}")

except Exception as e:
    SUCCESS = False
    traceback.print_exc()
    errors.append(str(e))

print('\n=== Résultat du test ===')
if SUCCESS:
    print('TEST OK')
    sys.exit(0)
else:
    print('TEST FAILED')
    for err in errors:
        print('-', err)
    sys.exit(2)
