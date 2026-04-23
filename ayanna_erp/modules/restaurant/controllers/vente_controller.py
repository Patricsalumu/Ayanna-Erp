"""
Controller for restaurant sales (panier, add products, payments)
"""
from decimal import Decimal
from datetime import datetime
from types import SimpleNamespace
from ayanna_erp.database.database_manager import get_database_manager
from sqlalchemy import text
from sqlalchemy.orm.exc import DetachedInstanceError
from ayanna_erp.modules.restaurant.models.restaurant import (
    RestauPanier, RestauProduitPanier, RestauPayment, RestauTable
)


class VenteController:
    def __init__(self, entreprise_id=1):
        self.db = get_database_manager()
        self.entreprise_id = entreprise_id

    def _calculate_payment_status(self, total_paid, total_final):
        """
        Calcule le statut de paiement et les montants de change/reste
        
        Retourne: (statut, change, reste_a_payer)
        - statut: "NON PAYÉE" | "PARTIELLEMENT PAYÉE" | "PAYÉE"
        - change: Montant rendu (si reçu > total)
        - reste_a_payer: Reste à payer (si reçu < total)
        """
        total_paid = float(total_paid or 0.0)
        total_final = float(total_final or 0.0)
        
        if total_paid <= 0:
            return "NON PAYÉE", 0.0, total_final
        elif total_paid < total_final:
            reste = total_final - total_paid
            return "PARTIELLEMENT PAYÉE", 0.0, reste
        elif total_paid >= total_final:
            change = total_paid - total_final
            return "PAYÉE", change, 0.0
        
        return "NON PAYÉE", 0.0, total_final

    def create_panier(self, table_id=None, client_id=None, serveuse_id=None, user_id=None):
        with self.db.session_scope() as session:
            panier = RestauPanier(
                entreprise_id=self.entreprise_id,
                table_id=table_id,
                client_id=client_id,
                serveuse_id=serveuse_id,
                user_id=user_id,
                payment_method='Crédit',
                status='en_cours',
                subtotal=0.0,
                remise_amount=0.0,
                total_final=0.0,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            session.add(panier)
            session.flush()
            # detach safe lightweight object to avoid Session-bound attribute refresh errors
            session.refresh(panier)
            return SimpleNamespace(
                id=panier.id,
                table_id=panier.table_id,
                client_id=panier.client_id,
                serveuse_id=panier.serveuse_id,
                user_id=panier.user_id,
                status=panier.status,
                subtotal=panier.subtotal,
                remise_amount=panier.remise_amount,
                total_final=panier.total_final,
                created_at=panier.created_at,
                updated_at=panier.updated_at
            )

    def add_product(self, panier_id, product_id, quantity, price):
        with self.db.session_scope() as session:
            panier = session.query(RestauPanier).filter_by(id=panier_id).first()
            if not panier:
                raise ValueError("Panier introuvable")
            total = float(quantity) * float(price)
            ligne = RestauProduitPanier(
                panier_id=panier_id,
                product_id=product_id,
                quantity=quantity,
                price=price,
                total=total
            )
            session.add(ligne)
            # forcer les timestamps locaux sur la ligne de panier
            try:
                ligne.created_at = datetime.now()
                ligne.updated_at = datetime.now()
            except Exception:
                # si le modèle n'expose pas ces champs, on ignore
                pass
            # Recalculer totaux
            session.flush()
            subtotal = sum([p.total for p in panier.produits])
            panier.subtotal = subtotal
            panier.total_final = subtotal - (panier.remise_amount or 0.0)
            panier.updated_at = datetime.now()
            session.refresh(ligne)
            return SimpleNamespace(
                id=ligne.id,
                panier_id=ligne.panier_id,
                product_id=ligne.product_id,
                quantity=ligne.quantity,
                price=ligne.price,
                total=ligne.total
            )

    def add_payment(self, panier_id, amount, payment_method, user_id=None):
        with self.db.session_scope() as session:
            panier = session.query(RestauPanier).filter_by(id=panier_id).first()
            if not panier:
                raise ValueError("Panier introuvable")
            # Vérifier disponibilité du stock dans l'entrepôt POS_4 avant d'enregistrer le paiement
            insufficient = []
            try:
                for ligne in getattr(panier, 'produits', []) or []:
                    pid = getattr(ligne, 'product_id', None)
                    qty_needed = float(getattr(ligne, 'quantity', 0) or 0)
                    if not pid:
                        continue
                    stock_row = session.execute(
                        text("""
                        SELECT spe.quantity FROM stock_produits_entrepot spe
                        JOIN stock_warehouses w ON w.id = spe.warehouse_id
                        WHERE spe.product_id = :pid AND w.code = 'POS_4' AND w.is_active = 1
                        LIMIT 1
                        """),
                        {'pid': pid}
                    ).fetchone()
                    available = float(stock_row[0]) if stock_row else 0.0
                    if qty_needed > available:
                        insufficient.append((pid, qty_needed, available))
            except Exception:
                # si la vérification échoue pour une raison technique, ne pas bloquer le paiement
                insufficient = []

            if insufficient:
                msgs = []
                for p, q, a in insufficient:
                    try:
                        prod_row = session.execute(text("SELECT name FROM core_products WHERE id = :pid LIMIT 1"), {'pid': p}).fetchone()
                        prod_name = prod_row[0] if prod_row and prod_row[0] else f'Produit {p}'
                    except Exception:
                        prod_name = f'Produit {p}'
                    msgs.append(f"{prod_name}: demandé {q}, disponible {a}")
                raise ValueError("Stock insuffisant: " + "; ".join(msgs))
            
            # Récupérer le total à payer
            try:
                total_final = float(panier.total_final or 0.0)
            except Exception:
                total_final = 0.0
            
            # Récupérer le total déjà payé
            total_already_paid = sum([p.amount for p in panier.payments]) if panier.payments else 0.0
            
            # Limiter le paiement au montant restant à payer
            # payment_amount = min(amount reçu, montant restant à payer)
            remaining_to_pay = max(0.0, total_final - total_already_paid)
            payment_amount = min(float(amount), remaining_to_pay)
            
            # Validation : accepter 0 pour crédit, > 0 pour autres méthodes
            if payment_method == 'Crédit':
                # Crédit = enregistre une dette, amount peut être 0
                if payment_amount < 0:
                    raise ValueError(f"Montant invalide pour crédit")
            else:
                # Autres méthodes = argent reçu, must be > 0
                if payment_amount <= 0:
                    raise ValueError(f"Aucun montant à payer (reste: {remaining_to_pay:.2f})")
            
            pay = RestauPayment(
                panier_id=panier_id,
                amount=payment_amount,  # Utilise le montant limité
                payment_method=payment_method,
                user_id=user_id
            )
            # assurer que la date enregistrée vient de l'horloge locale
            try:
                pay.created_at = datetime.now()
            except Exception:
                # modèle sans attribut created_at -> ignorer
                pass
            session.add(pay)
            session.flush()
            # capture id now so we can re-query safely after commit if needed
            pay_id = getattr(pay, 'id', None)
            
            # Recalculer le total payé en incluant ce nouveau paiement
            # Important: total_already_paid a été calculé avant d'ajouter ce paiement
            total_paid = total_already_paid + payment_amount
            try:
                total_final = float(panier.total_final or 0.0)
            except Exception:
                total_final = 0.0

            # Sauvegarder le statut original avant modification (pour détecter la première finalisation)
            original_status = getattr(panier, 'status', 'en_cours')

            # Logique de détermination du payment_method final
            # Si Crédit pur (amount=0) → enregistrer comme Crédit
            # Si paiement partiel (total_paid < total_final) → convertir en Crédit pour la partie impayée
            # Sinon → garder le payment_method choisi par l'utilisateur
            if total_paid < total_final:
                # Paiement partiel = convertir en crédit (même si espèces/carte choisi)
                # Les espèces/carte paient partiellement, le reste devient une dette
                panier.payment_method = 'Crédit'
            else:
                # Paiement complet avec la méthode choisie
                panier.payment_method = payment_method

            panier.status = 'valide'
            panier.updated_at = datetime.now()
            # try to refresh the payment instance; if it's detached for any reason, re-query it
            try:
                session.refresh(pay)
            except Exception:
                # try to recover by querying the payment by id from the same session
                pay = None
                if pay_id:
                    try:
                        pay = session.query(RestauPayment).filter_by(id=pay_id).first()
                    except Exception:
                        pay = None
                # if still not available, return a lightweight object built from known values
                if not pay:
                    return SimpleNamespace(
                        id=pay_id,
                        panier_id=panier_id,
                        amount=amount,
                        payment_method=payment_method,
                        user_id=user_id,
                        created_at=datetime.now()
                    )
            # Finaliser la vente (écritures comptables + stock) uniquement lors du premier passage à 'valide'
            # Si le panier était déjà 'valide', finalize_sale a déjà été appelé et a traité la vente.
            try:
                if original_status != 'valide':
                    try:
                        # IMPORTANT: Commit avant finalize_sale (ouvre sa propre session et lit depuis la DB)
                        session.commit()
                        ok, msg = self.finalize_sale(panier_id, amount, payment_method=payment_method, user_id=user_id)
                        print(f"DEBUG: finalize_sale result for panier {panier_id}: {ok} - {msg}")
                    except Exception as e:
                        print(f"DEBUG: Erreur finalize_sale pour panier {panier_id}: {e}")
            except Exception:
                pass

            # Calculer les statuts et montants
            total_paid = sum([p.amount for p in panier.payments]) if panier.payments else 0.0
            total_final = float(panier.total_final or 0.0)
            payment_status, change, reste = self._calculate_payment_status(total_paid, total_final)

            return SimpleNamespace(
                id=pay.id if pay is not None else pay_id,
                panier_id=pay.panier_id if pay is not None else panier_id,
                amount=pay.amount if pay is not None else amount,
                payment_method=panier.payment_method,
                user_id=pay.user_id if pay is not None else user_id,
                created_at=pay.created_at if pay is not None else datetime.now(),
                payment_status=payment_status,
                change=change,
                reste_a_payer=reste,
                total_paid=total_paid,
                total_final=total_final
            )

    def get_panier(self, panier_id):
        with self.db.session_scope() as session:
            panier = session.query(RestauPanier).filter_by(id=panier_id).first()
            if not panier:
                return None
            # return lightweight detached object
            session.refresh(panier)
            # Calculer les infos de paiement
            total_paid = sum([p.amount for p in panier.payments]) if panier.payments else 0.0
            total_final = float(panier.total_final or 0.0)
            payment_status, change, reste = self._calculate_payment_status(total_paid, total_final)
            
            return SimpleNamespace(
                id=panier.id,
                table_id=panier.table_id,
                client_id=panier.client_id,
                serveuse_id=panier.serveuse_id,
                user_id=panier.user_id,
                status=panier.status,
                subtotal=panier.subtotal,
                remise_amount=panier.remise_amount,
                total_final=panier.total_final,
                created_at=panier.created_at,
                updated_at=panier.updated_at,
                payment_status=payment_status,
                change=change,
                reste_a_payer=reste,
                total_paid=total_paid
            )

    def get_open_panier_for_table(self, table_id):
        """Retourne le panier en cours (status 'en_cours') pour une table donnée"""
        with self.db.session_scope() as session:
            panier = session.query(RestauPanier).filter_by(table_id=table_id, status='en_cours').first()
            if not panier:
                return None
            session.refresh(panier)
            # Calculer les infos de paiement
            total_paid = sum([p.amount for p in panier.payments]) if panier.payments else 0.0
            total_final = float(panier.total_final or 0.0)
            payment_status, change, reste = self._calculate_payment_status(total_paid, total_final)
            
            return SimpleNamespace(
                id=panier.id,
                table_id=panier.table_id,
                client_id=panier.client_id,
                serveuse_id=panier.serveuse_id,
                user_id=panier.user_id,
                status=panier.status,
                subtotal=panier.subtotal,
                remise_amount=panier.remise_amount,
                total_final=panier.total_final,
                created_at=panier.created_at,
                updated_at=panier.updated_at,
                payment_status=payment_status,
                change=change,
                reste_a_payer=reste,
                total_paid=total_paid
            )

    def get_panier_total(self, panier_id):
        """Calcule le total payé et le total final du panier"""
        with self.db.session_scope() as session:
            panier = session.query(RestauPanier).filter_by(id=panier_id).first()
            if not panier:
                return 0.0, 0.0
            total_lines = sum([p.total for p in panier.produits]) if panier.produits else 0.0
            total_paid = sum([p.amount for p in panier.payments]) if panier.payments else 0.0
            return float(total_lines), float(total_paid)

    def get_payment_info(self, panier_id):
        """
        Récupère les informations de paiement d'un panier
        
        Retourne un dictionnaire avec:
        - payment_status: "NON PAYÉE" | "PARTIELLEMENT PAYÉE" | "PAYÉE"
        - change: Montant de change (si overpayment)
        - reste_a_payer: Reste à payer (si underpayment)
        - total_paid: Total payé
        - total_final: Total à payer
        """
        try:
            with self.db.session_scope() as session:
                panier = session.query(RestauPanier).filter_by(id=panier_id).first()
                if not panier:
                    return {
                        'payment_status': 'NON PAYÉE',
                        'change': 0.0,
                        'reste_a_payer': 0.0,
                        'total_paid': 0.0,
                        'total_final': 0.0
                    }
                
                total_final = float(panier.total_final or 0.0)
                total_paid = sum([p.amount for p in panier.payments]) if panier.payments else 0.0
                
                payment_status, change, reste = self._calculate_payment_status(total_paid, total_final)
                
                return {
                    'payment_status': payment_status,
                    'change': change,
                    'reste_a_payer': reste,
                    'total_paid': total_paid,
                    'total_final': total_final
                }
        except Exception as e:
            print(f"Erreur récupération infos paiement: {e}")
            return {
                'payment_status': 'NON PAYÉE',
                'change': 0.0,
                'reste_a_payer': 0.0,
                'total_paid': 0.0,
                'total_final': 0.0
            }

    def list_paniers(self, date_from=None, date_to=None, status=None):
        with self.db.session_scope() as session:
            q = session.query(RestauPanier).filter_by(entreprise_id=self.entreprise_id)
            if status:
                q = q.filter(RestauPanier.status == status)
            if date_from:
                q = q.filter(RestauPanier.created_at >= date_from)
            if date_to:
                q = q.filter(RestauPanier.created_at <= date_to)
            return q.all()

    def finalize_sale(self, panier_id, amount_received=0.0, payment_method=None, user_id=None):
        """
        Finalise une vente: vérifie le stock dans l'entrepôt POS_4, crée les écritures comptables
        (journal de vente, journal stock, journal encaissement si paiement), et met à jour le stock.

        Retourne (True, message) si succès ou (False, message) si échec (par ex. stock insuffisant).
        """
        session = self.db.get_session()
        try:
            # Charger le panier
            panier = session.query(RestauPanier).filter_by(id=panier_id).first()
            if not panier:
                return False, f"Panier {panier_id} introuvable"

            # Rassembler les lignes
            lignes = getattr(panier, 'produits', []) or []
            if not lignes:
                return False, "Panier vide"

            # Vérifier disponibilité stock dans POS_4
            insufficient = []
            for ligne in lignes:
                pid = getattr(ligne, 'product_id', None)
                qty_needed = float(getattr(ligne, 'quantity', 0) or 0)
                if not pid:
                    continue
                # récupérer quantité disponible dans stock_produits_entrepot pour entrepôt code 'POS_4'
                stock_row = session.execute(text("""
                    SELECT spe.quantity FROM stock_produits_entrepot spe
                    JOIN stock_warehouses w ON w.id = spe.warehouse_id
                    WHERE spe.product_id = :pid AND w.code = 'POS_4' AND w.is_active = 1
                    LIMIT 1
                """), {'pid': pid}).fetchone()
                available = float(stock_row[0]) if stock_row else 0.0
                if qty_needed > available:
                    insufficient.append((pid, qty_needed, available))

            if insufficient:
                msgs = []
                for p, q, a in insufficient:
                    try:
                        prod_row = session.execute(text("SELECT name FROM core_products WHERE id = :pid LIMIT 1"), {'pid': p}).fetchone()
                        prod_name = prod_row[0] if prod_row and prod_row[0] else f'Produit {p}'
                    except Exception:
                        prod_name = f'Produit {p}'
                    msgs.append(f"{prod_name}: demandé {q}, disponible {a}")
                return False, "Stock insuffisant: " + "; ".join(msgs)

            # user id fallback: prefer provided user_id, then controller.user_id, then panier.user_id, else 1
            uid = user_id or getattr(self, 'user_id', None) or getattr(panier, 'user_id', None) or 1

            # Récupérer configuration comptable
            cfg = session.execute(text("SELECT compte_vente_id, compte_caisse_id, compte_client_id, compte_remise_id, compte_stock_id, compte_variation_stock_id, compte_achat_id FROM compta_config WHERE enterprise_id = :ent LIMIT 1"), {'ent': self.entreprise_id}).fetchone()
            if not cfg:
                # fallback: try without filter
                cfg = session.execute(text("SELECT compte_vente_id, compte_caisse_id, compte_client_id, compte_remise_id, compte_stock_id, compte_variation_stock_id, compte_achat_id FROM compta_config LIMIT 1")).fetchone()
            if not cfg:
                return False, "Configuration comptable introuvable"

            compte_vente_id, compte_caisse_id, compte_client_id, compte_remise_id, compte_stock_id, compte_variation_stock_id, compte_achat_id = cfg

            # Eviter le double traitement : vérifier que le journal de vente ET les mouvements de stock existent.
            # Si le journal existe mais pas les mouvements (échec partiel précédent), on relance le traitement complet.
            existing_journal = session.execute(text(
                "SELECT COUNT(1) FROM compta_journaux WHERE reference = :ref AND type_operation = 'Vente'"
            ), {'ref': f"CMD-{panier.id}"}).fetchone()
            existing_stock = session.execute(text(
                "SELECT COUNT(1) FROM stock_mouvements WHERE reference = :ref AND movement_type = 'SORTIE'"
            ), {'ref': f"CMD-{panier.id}"}).fetchone()
            already_journalized = existing_journal and int(existing_journal[0]) > 0
            already_stocked = existing_stock and int(existing_stock[0]) > 0
            if already_journalized and already_stocked:
                return True, f"Vente CMD-{panier.id} déjà traitée"

            # 1) Journal de vente
            total_amount = float(panier.total_final or 0.0)
            journal_sale = session.execute(text(
                """
                INSERT INTO compta_journaux
                (date_operation, libelle, montant, type_operation, reference, description,
                 enterprise_id, user_id, date_creation, date_modification)
                VALUES (:date_operation, :libelle, :montant, :type_operation, :reference,
                        :description, :enterprise_id, :user_id, :date_creation, :date_modification)
                """),
                {
                    'date_operation': datetime.now(),
                    'libelle': f"Vente - CMD-{panier.id}",
                    'montant': total_amount,
                    'type_operation': 'Vente',
                    'reference': f"CMD-{panier.id}",
                    'description': f"Vente - {len(lignes)} articles",
                    'enterprise_id': self.entreprise_id,
                    'user_id': uid,
                    'date_creation': datetime.now(),
                    'date_modification': datetime.now()
                }
            )
            session.flush()
            journal_sale_id = session.execute(text("SELECT last_insert_rowid()")).fetchone()[0]

            ordre = 1
            # Écritures produits (crédit revenus)
            for ligne in lignes:
                item_total = float(getattr(ligne, 'total', 0.0) or 0.0)
                compte_item = compte_vente_id or None
                pid = getattr(ligne, 'product_id', None)
                
                product_result = session.execute(text("""
                        SELECT compte_produit_id FROM core_products
                        WHERE id = :product_id
                    """), {'product_id':pid})
                product_row = product_result.fetchone()
                if product_row and product_row[0]:
                    compte_item = product_row[0]
                    
                # Debug log
                session.execute(text(
                    """
                    INSERT INTO compta_ecritures
                    (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                    VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
                    """),
                    {
                        'journal_id': journal_sale_id,
                        'compte_id': compte_item,
                        'debit': 0,
                        'credit': item_total,
                        'ordre': ordre,
                        'libelle': f"Vente produit {getattr(ligne, 'product_id', '')} (x{getattr(ligne, 'quantity', 0)})",
                        'date_creation': datetime.now()
                    }
                )
                session.flush()
                ordre += 1

            # Débit compte client
            if compte_client_id:
                session.execute(text(
                    """
                    INSERT INTO compta_ecritures
                    (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                    VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
                    """),
                    {
                        'journal_id': journal_sale_id,
                        'compte_id': compte_client_id,
                        'debit': total_amount,
                        'credit': 0,
                        'ordre': ordre,
                        'libelle': f"Client - Vente CMD-{panier.id}",
                        'date_creation': datetime.now()
                    }
                )
                session.flush()
                ordre += 1

            # Remise si applicable
            remise_val = float(getattr(panier, 'remise_amount', 0.0) or 0.0)
            if remise_val and compte_remise_id:
                session.execute(text(
                    """
                    INSERT INTO compta_ecritures
                    (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                    VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
                    """),
                    {
                        'journal_id': journal_sale_id,
                        'compte_id': compte_remise_id,
                        'debit': remise_val,
                        'credit': 0,
                        'ordre': ordre,
                        'libelle': f"Remise CMD-{panier.id}",
                        'date_creation': datetime.now()
                    }
                )
                session.flush()
                print(f"DEBUG: Created remise entry amount {remise_val} in journal {journal_sale_id}")
                ordre += 1

            # 2) Journal stock (déduction de stock)
            journal_stock = session.execute(text(
                """
                INSERT INTO compta_journaux
                (date_operation, libelle, montant, type_operation, reference, description,
                 enterprise_id, user_id, date_creation, date_modification)
                VALUES (:date_operation, :libelle, :montant, :type_operation, :reference,
                        :description, :enterprise_id, :user_id, :date_creation, :date_modification)
                """),
                {
                    'date_operation': datetime.now(),
                    'libelle': f"Sortie stock - CMD-{panier.id}",
                    'montant': total_amount,
                    'type_operation': 'OD',
                    'reference': f"CMD-{panier.id}",
                    'description': f"Sortie stock  - {len(lignes)} articles",
                    'enterprise_id': self.entreprise_id,
                    'user_id': uid,
                    'date_creation': datetime.now(),
                    'date_modification': datetime.now()
                }
            )
            session.flush()
            journal_stock_id = session.execute(text("SELECT last_insert_rowid()")).fetchone()[0]

            ordre_stock = 1
            for ligne in lignes:
                item_total = float(getattr(ligne, 'total', 0.0) or 0.0)
                qty = float(getattr(ligne, 'quantity', 0) or 0)
                pid = getattr(ligne, 'product_id', None)

                # Calculer coût moyen d'achat depuis mouvements d'entrée pour ce produit (POS_4 env.)
                avg_cost_row = session.execute(text("""
                    SELECT AVG(unit_cost) FROM stock_mouvements
                    WHERE product_id = :product_id AND unit_cost IS NOT NULL AND unit_cost > 0 AND movement_type = 'ENTREE'
                """), {'product_id': pid}).fetchone()
                avg_unit_cost = float(avg_cost_row[0]) if avg_cost_row and avg_cost_row[0] is not None else 0.0


                # Enfin fallback sur le champ cost du produit
                product_meta = session.execute(text("""
                    SELECT cost, name, compte_charge_id FROM core_products
                    WHERE id = :product_id
                """), {'product_id': pid}).fetchone()

                product_cost_field = float(product_meta[0]) if product_meta and product_meta[0] is not None else 0.0
                product_name = product_meta[1]
                product_compte_charge_id = product_meta[2] if product_meta and len(product_meta) > 2 and product_meta[2] is not None else None

                unit_cost = avg_unit_cost if avg_unit_cost > 0 else product_cost_field

                # Déterminer le compte charge à utiliser (hiérarchie: compte_charge_id produit > compte_achat_id config > compte_variation_stock_id)
                compte_charge_id = product_compte_charge_id or compte_achat_id
                

                # débit: compte achat (COGS), crédit: compte stock — utiliser unité moyenne            
                session.execute(text(
                    """
                    INSERT INTO compta_ecritures
                    (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                    VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
                    """),
                    {
                        'journal_id': journal_stock_id,
                        'compte_id': compte_charge_id,
                        'debit': unit_cost * qty,
                        'credit': 0,
                        'ordre': ordre_stock,
                        'libelle': f"COGS {product_name} (x{qty})",
                        'date_creation': datetime.now()
                    }
                )
                session.flush()
                ordre_stock += 1
            
                session.execute(text(
                    """
                    INSERT INTO compta_ecritures
                    (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                    VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
                    """),
                    {
                        'journal_id': journal_stock_id,
                        'compte_id': compte_stock_id,
                        'debit': 0,
                        'credit': unit_cost * qty,
                        'ordre': ordre_stock,
                        'libelle': f"Sortie stock {product_name} (x{qty})",
                        'date_creation': datetime.now()
                    }
                )
                session.flush()
                ordre_stock += 1

                # Mettre à jour le stock réel dans l'entrepôt POS_4 (pour chaque ligne)
                try:
                    self._update_pos_stock_restaurant(session, getattr(ligne, 'product_id', None), int(qty), getattr(ligne, 'price', 0.0), item_total, f"CMD-{panier.id}")
                except Exception as e:
                    print(f"DEBUG: Erreur mise à jour stock pour produit {getattr(ligne, 'product_id', None)}: {e}")

            # 3) Journal encaissement (si paiement)
            if float(amount_received or 0.0) > 0 and compte_caisse_id:
                journal_pay = session.execute(text(
                    """
                    INSERT INTO compta_journaux
                    (date_operation, libelle, montant, type_operation, reference, description,
                     enterprise_id, user_id, date_creation, date_modification)
                    VALUES (:date_operation, :libelle, :montant, :type_operation, :reference,
                            :description, :enterprise_id, :user_id, :date_creation, :date_modification)
                    """),
                    {
                        'date_operation': datetime.now(),
                        'libelle': f"Paiement CMD-{panier.id}",
                        'montant': float(amount_received),
                        'type_operation': 'Caisse',
                        'reference': f"CMD-{panier.id}",
                        'description': f"Encaissement vente - {payment_method}",
                        'enterprise_id': self.entreprise_id,
                        'user_id': uid,
                        'date_creation': datetime.now(),
                        'date_modification': datetime.now()
                    }
                )
                session.flush()
                journal_pay_id = session.execute(text("SELECT last_insert_rowid()")).fetchone()[0]

                # Débit caisse
                session.execute(text(
                    """
                    INSERT INTO compta_ecritures
                    (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                    VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
                    """),
                    {
                        'journal_id': journal_pay_id,
                        'compte_id': compte_caisse_id,
                        'debit': float(amount_received),
                        'credit': 0,
                        'ordre': 1,
                        'libelle': f"Encaissement {payment_method} CMD-{panier.id}",
                        'date_creation': datetime.now()
                    }
                )
                session.flush()

                # Crédit client
                if compte_client_id:
                    session.execute(text(
                        """
                        INSERT INTO compta_ecritures
                        (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                        VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
                        """),
                        {
                            'journal_id': journal_pay_id,
                            'compte_id': compte_client_id,
                            'debit': 0,
                            'credit': float(amount_received),
                            'ordre': 2,
                            'libelle': f"Règlement client CMD-{panier.id}",
                            'date_creation': datetime.now()
                        }
                    )
                    session.flush()

            # Mettre à jour le statut du panier
            try:
                # Logique de détermination du payment_method final
                # Si Crédit pur (amount=0) → enregistrer comme Crédit
                # Si paiement partiel (amount_received < total_final) → convertir en Crédit
                # Sinon → garder le payment_method choisi
                amount_received_val = float(amount_received or 0.0)
                total_final_val = float(panier.total_final or 0.0)
                
                print(f"DEBUGG MISE A JOUR PANIER TEST PAYMENT METHOD AVANT {payment_method}")
                print(f"AMOUNT RECEIVED VAl {amount_received_val}")
                print(f"TOTAL FINAL VAl {total_final_val}")
                
                
                if payment_method == 'Crédit' and amount_received_val <= 0:
                    # Pur crédit = enregistre une dette
                    panier.payment_method = 'Crédit'
                    print(f"DEBUG CREDIT 1 RETENU")
                elif amount_received_val < total_final_val:
                    # Paiement partiel = convertir en crédit (même si espèces/carte choisi)
                    # Les espèces/carte paient partiellement, le reste devient une dette
                    panier.payment_method = 'Crédit'
                    print(f"DEBUG CREDIT 2 RETENU")
                else:
                    # Paiement complet avec la méthode choisie
                    panier.payment_method = payment_method
                    print(f"DEBUG {payment_method} RETENU")
                
                panier.status = 'valide'
                panier.updated_at = datetime.now()
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Erreur mise a jour status panier: {e}")

            return True, f"Vente finalisée et écritures créées pour panier {panier.id}"
        except Exception as e:
            session.rollback()
            return False, f"Erreur finalisation vente: {e}"
        finally:
            try:
                session.close()
            except Exception:
                pass

    def _update_pos_stock_restaurant(self, session, product_id, quantity_sold, unit_price, line_total, numero_commande):
        """
        Met à jour le stock pour le module restaurant en utilisant l'entrepôt code 'POS_4'.
        Ce helper reçoit la session SQLAlchemy déjà ouverte.
        """
        try:
            # Chercher l'entrepôt POS_4
            warehouse_row = session.execute(text("SELECT id FROM stock_warehouses WHERE code = 'POS_4' AND is_active = 1 LIMIT 1")).fetchone()
            if not warehouse_row:
                print(f"⚠️ Entrepôt POS_4 non trouvé pour le produit {product_id}")
                return
            warehouse_id = warehouse_row[0]

            # Récupérer le stock actuel
            stock_row = session.execute(
                text("SELECT quantity FROM stock_produits_entrepot WHERE product_id = :product_id AND warehouse_id = :warehouse_id LIMIT 1"),
                {'product_id': product_id, 'warehouse_id': warehouse_id}
            ).fetchone()
            current_stock = stock_row[0] if stock_row else 0

            new_stock = max(0, int(current_stock) - int(quantity_sold))

            if stock_row:
                session.execute(
                    text("UPDATE stock_produits_entrepot SET quantity = :new_quantity, updated_at = :updated_at WHERE product_id = :product_id AND warehouse_id = :warehouse_id"),
                    {'product_id': product_id, 'new_quantity': new_stock, 'warehouse_id': warehouse_id, 'updated_at': datetime.now()}
                )
            else:
                session.execute(
                    text("INSERT INTO stock_produits_entrepot (product_id, warehouse_id, quantity, created_at, updated_at) VALUES (:product_id, :warehouse_id, :quantity, :created_at, :updated_at)"),
                    {'product_id': product_id, 'warehouse_id': warehouse_id, 'quantity': new_stock, 'created_at': datetime.now(), 'updated_at': datetime.now()}
                )

            # Insert mouvement stock
            session.execute(
                text("""
                INSERT INTO stock_mouvements(
                    product_id, warehouse_id, movement_type, quantity, unit_cost, total_cost,
                    destination_warehouse_id, reference, description, user_id, movement_date, created_at
                ) VALUES (
                    :product_id, :warehouse_id, :movement_type, :quantity, :unit_cost, :total_cost,
                    :destination_warehouse_id, :reference, :description, :user_id, :movement_date, :created_at
                )
                """),
                {
                    'product_id': product_id,
                    'warehouse_id': warehouse_id,
                    'movement_type': 'SORTIE',
                    'quantity': quantity_sold,
                    'unit_cost': unit_price,
                    'total_cost': line_total,
                    'destination_warehouse_id': warehouse_id,
                    'reference': numero_commande,
                    'description': "Vente Restaurant - " + str(numero_commande),
                    'user_id': 1,
                    'movement_date': datetime.now(),
                    'created_at': datetime.now()
                }
            )
            print(f"📦 Stock mis à jour (POS_4) - Produit {product_id}: {current_stock} → {new_stock}")
        except Exception as e:
            print(f"❌ Erreur mise à jour stock (POS_4): {e}")
