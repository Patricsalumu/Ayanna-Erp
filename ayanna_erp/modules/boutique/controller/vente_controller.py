"""
Contrôleur de vente pour le module Boutique
Gère toute la logique de paiement et comptabilité
"""

from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.orm import Session

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController
from ..model.models import ShopClient, ShopPanier, ShopService


class VenteController:
    """Contrôleur gérant la logique de vente et comptabilité"""

    def __init__(self, pos_id: int, current_user=None):
        self.pos_id = pos_id
        self.current_user = current_user
        self.db_manager = DatabaseManager()
        self.entreprise_controller = EntrepriseController()

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

    def get_payment_info(self, panier_id: int) -> Dict:
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
            with self.db_manager.get_session() as session:
                panier_result = session.execute(text("""
                    SELECT total_final FROM shop_paniers WHERE id = :panier_id LIMIT 1
                """), {'panier_id': panier_id}).fetchone()
                
                total_final = float(panier_result[0]) if panier_result else 0.0
                
                payment_sum = session.execute(text("""
                    SELECT COALESCE(SUM(amount), 0) FROM shop_payments WHERE panier_id = :panier_id
                """), {'panier_id': panier_id}).fetchone()
                
                total_paid = float(payment_sum[0]) if payment_sum else 0.0
                
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

    def get_currency_symbol(self):
        """Récupère le symbole de devise depuis l'entreprise"""
        return self.entreprise_controller.get_currency_symbol()

    def format_amount(self, amount):
        """Formate un montant avec la devise de l'entreprise"""
        return self.entreprise_controller.format_amount(amount)

    def process_sale(self, sale_data: Dict) -> Tuple[bool, str, Optional[int]]:
        """
        Traite une vente complète avec logique comptable avancée

        Args:
            sale_data: Données de la vente contenant cart_items, payment_data, client_id, etc.

        Returns:
            Tuple[bool, str, Optional[int]]: (succès, message, panier_id)
        """
        try:
            with self.db_manager.get_session() as session:
                # Validation des comptes comptables avant traitement
                validation_result = self._validate_accounting_config(session)
                if not validation_result[0]:
                    return validation_result[0], validation_result[1], None

                # Calculer les totaux
                cart_items = sale_data['cart_items']
                discount_amount = sale_data.get('discount_amount', 0.0)
                payment_data = sale_data['payment_data']

                subtotal = float(sum(item['unit_price'] * item['quantity'] for item in cart_items))
                total_amount = float(subtotal - discount_amount)
                amount_received = float(payment_data['amount_received'])
                
                # Limiter le paiement au montant net à payer (pas de surpaiement enregistré)
                payment_amount = min(float(amount_received), total_amount) if amount_received > 0 else 0.0

                # Générer numéro de commande unique
                import random
                numero_commande = "TEMP"

                # 1. Créer le panier (toujours, même si pas payé)
                print("Debug: Insertion panier avec total_amount =", total_amount, "et payment_amount =", payment_amount)
                panier_result = session.execute(text("""
                    INSERT INTO shop_paniers 
                    (pos_id, client_id, numero_commande, status, payment_method, 
                     subtotal, remise_amount, total_final, user_id, created_at, updated_at, notes)
                    VALUES (:pos_id, :client_id, :numero_commande, :status, :payment_method,
                            :subtotal, :remise_amount, :total_final, :user_id, :created_at, :updated_at, :notes)
                """), {
                    'pos_id': self.pos_id,
                    'client_id': sale_data.get('client_id'),
                    'numero_commande': numero_commande,
                    'status': 'completed' if payment_amount >= total_amount else 'pending',
                    'payment_method': (payment_data['method'] if payment_amount >= total_amount 
                                       else ('Crédit')),
                    'subtotal': subtotal,
                    'remise_amount': discount_amount,
                    'total_final': total_amount,
                    'user_id': getattr(self.current_user, 'id', 1),
                    'created_at': datetime.now(),
                    'updated_at': datetime.now(),
                    'notes': sale_data.get('notes', '').strip()
                })
                
                session.flush()
                panier_id_result = session.execute(text("SELECT last_insert_rowid()"))
                panier_id = panier_id_result.fetchone()[0]
                numero_commande = f"FAC-{datetime.now().strftime('%Y%m%d')}-{panier_id}"
                
                # Mise à jour du panier avec un numero de commande
                session.execute(text("""
                    UPDATE shop_paniers
                    SET numero_commande = :numero_commande
                    WHERE id = :id
                """), {
                    'numero_commande': numero_commande,
                    'id': panier_id
                })

                # 2. Créer les lignes de vente et gérer le stock
                for item in cart_items:
                    if item.get('type') == 'product':
                        product_id = item.get('id')
                        quantity = item.get('quantity')
                        unit_price = item.get('unit_price')
                        line_total = unit_price * quantity

                        # Créer la ligne de panier produits
                        session.execute(text("""
                            INSERT INTO shop_paniers_products
                            (panier_id, product_id, quantity, price_unit, total_price)
                            VALUES (:panier_id, :product_id, :quantity, :price_unit, :total_price)
                        """), {
                            'panier_id': panier_id,
                            'product_id': product_id,
                            'quantity': quantity,
                            'price_unit': float(unit_price),
                            'total_price': float(line_total)
                        })

                        # Mettre à jour le stock (toujours, même si pas payé)
                        self._update_pos_stock(session, product_id, quantity, unit_price, line_total, numero_commande)

                    elif item.get('type') == 'service':
                        service_id = item.get('id')
                        quantity = item.get('quantity')
                        unit_price = item.get('unit_price')
                        line_total = unit_price * quantity
                        
                        # Insérer la ligne de service
                        session.execute(text("""
                            INSERT INTO shop_paniers_services
                            (panier_id, service_id, quantity, price_unit, total_price)
                            VALUES (:panier_id, :service_id, :quantity, :price_unit, :total_price)
                        """), {
                            'panier_id': panier_id,
                            'service_id': service_id,
                            'quantity': quantity,
                            'price_unit': float(unit_price),
                            'total_price': float(line_total)
                        })

                # 3. Créer TOUJOURS les écritures comptables de vente (même sans paiement)
                accounting_data = {
                    'panier_id': panier_id,
                    'numero_commande': numero_commande,
                    'subtotal': subtotal,
                    'discount_amount': discount_amount,
                    'total_amount': total_amount,
                    'amount_received': payment_amount,  # Utiliser le montant limité enregistré
                    'payment_method': (payment_data['method'] if payment_amount >= total_amount 
                                       else ('Crédit' if payment_amount > 0 else None)),
                    'sale_date': datetime.now(),
                    'client_id': sale_data.get('client_id'),
                    'cart_items': cart_items
                }

                
                success, message = self._create_advanced_sale_accounting_entries(session, accounting_data)
                if not success:
                    return False, f"Erreur comptable: {message}", None

                # 4. Traiter les écritures comptables de paiement seulement si il y a eu un paiement
                if payment_amount > 0:
                    # Enregistrer le paiement limité au montant net à payer
                    session.execute(text("""
                        INSERT INTO shop_payments
                        (panier_id, amount, payment_method, payment_date, reference)
                        VALUES (:panier_id, :amount, :payment_method, :payment_date, :reference)
                    """), {
                        'panier_id': panier_id,
                        'amount': payment_amount,
                        'payment_method': (payment_data['method'] if payment_amount >= total_amount 
                                          else 'Crédit'),
                        'payment_date': datetime.now(),
                        'reference': numero_commande
                    })

                # Valider la transaction
                session.commit()

                # Message de succès avec affichage monnaie/reste
                currency = self.get_currency_symbol()
                if payment_amount == 0:
                    message = f"✅ Commande #{numero_commande} enregistrée (non payée) - {total_amount:.0f} {currency}"
                elif payment_amount >= total_amount:
                    # Vente complétée
                    change = amount_received - payment_amount
                    if change > 0:
                        message = f"✅ Vente #{numero_commande} - {total_amount:.0f} {currency} | Monnaie: {change:.0f} {currency}"
                    else:
                        message = f"✅ Vente #{numero_commande} complétée - {total_amount:.0f} {currency}"
                else:
                    # Paiement partiel
                    reste = total_amount - payment_amount
                    message = f"✅ Vente #{numero_commande} - {payment_amount:.0f}/{total_amount:.0f} {currency} | Reste: {reste:.0f} {currency}"

                return True, message, panier_id

        except Exception as e:
            return False, f"Erreur lors du traitement de la vente: {str(e)}", None

    def _validate_accounting_config(self, session: Session) -> Tuple[bool, str]:
        """
        Valide la configuration comptable

        Returns:
            Tuple[bool, str]: (valide, message_erreur)
        """
        try:
            config_result = session.execute(text("""
                SELECT compte_vente_id, compte_caisse_id, compte_client_id, compte_remise_id
                FROM compta_config
                WHERE pos_id = :pos_id
                LIMIT 1
            """), {'pos_id': self.pos_id})

            config_row = config_result.fetchone()

            if not config_row or not config_row[0]:
                return False, "Configuration comptable manquante. Veuillez configurer les comptes de vente dans les paramètres comptables."

            compte_vente_id = config_row[0]
            compte_caisse_id = config_row[1]
            compte_client_id = config_row[2]
            compte_remise_id = config_row[3]

            if not compte_vente_id:
                return False, "Le compte de vente n'est pas configuré. Veuillez le définir dans les paramètres comptables."

            if not compte_caisse_id:
                return False, "Le compte de caisse n'est pas configuré. Veuillez le définir dans les paramètres comptables."

            if not compte_client_id:
                return False, "Le compte client n'est pas configuré. Veuillez le définir dans les paramètres comptables."

            return True, "Configuration valide"

        except Exception as e:
            return False, f"Erreur lors de la validation de la configuration comptable: {str(e)}"

    def _create_advanced_sale_accounting_entries(self, session: Session, sale_data: Dict) -> Tuple[bool, str]:
        """Crée les écritures comptables avancées avec répartition proportionnelle"""
        try:
            panier_id = sale_data['panier_id']
            numero_commande = sale_data['numero_commande']
            total_amount = sale_data['total_amount']
            amount_received = sale_data['amount_received']
            discount_amount = sale_data['discount_amount']
            cart_items = sale_data['cart_items']
            # Sous-total fourni par le caller (prix unitaires * quantités)
            subtotal = sale_data.get('subtotal', float(sum(item['unit_price'] * item['quantity'] for item in cart_items)))
            client_id = sale_data['client_id']

            # Récupérer la configuration comptable (incluant compte stock et compte charge pour inventaire permanent)
            config_result = session.execute(text("""
                SELECT compte_vente_id, compte_caisse_id, compte_client_id, compte_remise_id, compte_stock_id, compte_variation_stock_id, compte_achat_id
                FROM compta_config
                WHERE pos_id = :pos_id
                LIMIT 1
            """), {'pos_id': self.pos_id})

            config_row = config_result.fetchone()
            if not config_row:
                return False, "Configuration comptable introuvable"

            compte_vente_id = config_row[0]
            compte_caisse_id = config_row[1]
            compte_client_id = config_row[2]
            compte_remise_id = config_row[3]
            compte_stock_id = config_row[4]
            compte_variation_stock_id = config_row[5]
            compte_achat_id = config_row[6]

            # Validation : si remise et pas de compte remise configuré, refuser
            if discount_amount > 0 and not compte_remise_id:
                return False, "Une remise a été appliquée mais aucun compte remise n'est configuré pour ce point de vente. Veuillez configurer le compte remise dans les paramètres comptables."


            # Si on a des produits physiques, s'assurer que les comptes stock/charge sont configurés
            has_product_items = any(item.get('type') == 'product' for item in cart_items)
            # if has_product_items and (not compte_stock_id or not compte_variation_stock_id):
            #     return False, "Inventaire permanent requis: configurez les comptes stock et compte_variation_stock_id (compte_stock_id, compte_variation_stock_id) dans la configuration comptable."

            # 3. Créer les écritures de VENTE (journal de vente) - toujours, même si paiement partiel
            # Journal de vente
            journal_sale_result = session.execute(text("""
                INSERT INTO compta_journaux
                (date_operation, libelle, montant, type_operation, reference, description,
                 enterprise_id, user_id, date_creation, date_modification, valide)
                VALUES (:date_operation, :libelle, :montant, :type_operation, :reference,
                        :description, :enterprise_id, :user_id, :date_creation, :date_modification, :valide)
            """), {
                'date_operation': sale_data['sale_date'],
                'libelle': f"Vente -{numero_commande}",
                'montant': total_amount,
                'type_operation': 'Vente',
                'reference': numero_commande,
                'description': f"Vente boutique - {len(cart_items)} articles",
                'enterprise_id': 1,  # TODO: Récupérer dynamiquement
                'user_id': getattr(self.current_user, 'id', 1),
                'date_creation': datetime.now(),
                'date_modification': datetime.now(),
                'valide': 0
            })

            session.flush()
            journal_sale_id_result = session.execute(text("SELECT last_insert_rowid()"))
            journal_sale_id = journal_sale_id_result.fetchone()[0]

            ordre = 1

            # Écritures de vente : créditer les comptes produits/services (revenus)
            for item in cart_items:
                item_total = item['unit_price'] * item['quantity']
                # montant de la ligne (revenu) — garder en float pour insertion SQL
                item_sale_amount = float(item_total)


                # Par défaut, utiliser le compte de vente général
                compte_item_id = compte_vente_id

                # Si c'est un produit et qu'un compte spécifique est configuré, l'utiliser
                if item.get('type') == 'product':
                    product_result = session.execute(text("""
                        SELECT compte_produit_id FROM core_products
                        WHERE id = :product_id
                    """), {'product_id': item['id']})
                    product_row = product_result.fetchone()
                    if product_row and product_row[0]:
                        compte_item_id = product_row[0]

                # Si c'est un service, tenter de récupérer un compte spécifique (ex: table event_services)
                elif item.get('type') == 'service':
                    # Cas fréquent : services provenant d'un évènement (table event_services) qui peut contenir compte_produit_id
                    evt_result = session.execute(text("""
                        SELECT compte_produit_id FROM event_services
                        WHERE id = :service_id
                    """), {'service_id': item['id']})
                    evt_row = evt_result.fetchone()
                    if evt_row and evt_row[0]:
                        compte_item_id = evt_row[0]
                    print(f'Debugg Compte produit service {compte_item_id} pour service {item['id']}')

                # Vérification finale : s'il n'y a toujours pas de compte, erreur
                if not compte_item_id:
                    return False, f"Article '{item.get('name', 'N/A')}' n'a pas de compte comptable configuré et aucun compte de vente par défaut n'est défini."

                # Insérer l'écriture crédit (revenu)
                session.execute(text("""
                    INSERT INTO compta_ecritures
                    (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                    VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
                """), {
                    'journal_id': journal_sale_id,
                    'compte_id': compte_item_id,
                    'debit': 0,
                    'credit': item_sale_amount,
                    'ordre': ordre,
                    'libelle': f"Vente {item.get('name', 'Article')} (x{item['quantity']})",
                    'date_creation': datetime.now()
                })
                ordre += 1

            # Écriture débit : Compte client (montant total de la vente)
            if compte_client_id:
                session.execute(text("""
                    INSERT INTO compta_ecritures
                    (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                    VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
                """), {
                    'journal_id': journal_sale_id,
                    'compte_id': compte_client_id,
                    'debit': total_amount,
                    'credit': 0,
                    'ordre': ordre,
                    'libelle': f"Client - Vente {numero_commande}",
                    'date_creation': datetime.now()
                })
                ordre += 1

            # Si remise, débiter le compte remise (validation déjà faite plus haut)
            if discount_amount > 0 and compte_remise_id:
                session.execute(text("""
                    INSERT INTO compta_ecritures
                    (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                    VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
                """), {
                    'journal_id': journal_sale_id,
                    'compte_id': compte_remise_id,
                    'debit': discount_amount,
                    'credit': 0,
                    'ordre': ordre,
                    'libelle': f"Remise accordée {numero_commande}",
                    'date_creation': datetime.now()
                })
                ordre += 1

            # 4. Créer un journal de sortie stock (inventaire permanent) et écrire les mouvements COGS / Stock
            if has_product_items:
                journal_stock_result = session.execute(text("""
                    INSERT INTO compta_journaux
                    (date_operation, libelle, montant, type_operation, reference, description,
                     enterprise_id, user_id, date_creation, date_modification, valide)
                    VALUES (:date_operation, :libelle, :montant, :type_operation, :reference,
                            :description, :enterprise_id, :user_id, :date_creation, :date_modification, :valide)
                """), {
                    'date_operation': sale_data['sale_date'],
                    'libelle': f"Sortie stock -{numero_commande}",
                    'montant': subtotal,
                    'type_operation': 'OD',
                    'reference': numero_commande,
                    'description': f"Sortie stock (COGS) - {len([i for i in cart_items if i.get('type')=='product'])} produits",
                    'enterprise_id': 1,
                    'user_id': getattr(self.current_user, 'id', 1),
                    'date_creation': datetime.now(),
                    'date_modification': datetime.now(),
                    'valide': 0
                })

                session.flush()
                journal_stock_id_result = session.execute(text("SELECT last_insert_rowid()"))
                journal_stock_id = journal_stock_id_result.fetchone()[0]

                ordre_stock = 1
                # Pour chaque produit, débiter compte charge (COGS) et créditer compte stock
                for item in cart_items:
                    if item.get('type') != 'product':
                        continue

                    product_id = item.get('id')
                    qty = item.get('quantity', 0)

                    # Récupérer le prix d'achat (cost) et le compte charge du produit
                    # Récupérer le coût d'achat moyen : privilégier la moyenne des mouvements d'entrée
                    avg_cost_row = session.execute(text("""
                        SELECT AVG(unit_cost) FROM stock_mouvements
                        WHERE product_id = :product_id AND unit_cost IS NOT NULL AND unit_cost > 0 AND movement_type = 'ENTREE'
                    """), {'product_id': product_id}).fetchone()
                    avg_unit_cost = float(avg_cost_row[0]) if avg_cost_row and avg_cost_row[0] is not None else 0.0


                    # Enfin fallback sur le champ cost du produit
                    product_meta = session.execute(text("""
                        SELECT cost, name, compte_charge_id, stock_account_id FROM core_products
                        WHERE id = :product_id
                    """), {'product_id': product_id}).fetchone()
                    product_cost_field = float(product_meta[0]) if product_meta and product_meta[0] is not None else 0.0
                    product_name = product_meta[1] if product_meta and len(product_meta) > 1 else item.get('name', f'Produit {product_id}')
                    product_compte_charge_id = product_meta[2] if product_meta and len(product_meta) > 2 and product_meta[2] is not None else None

                    unit_cost = avg_unit_cost if avg_unit_cost > 0 else product_cost_field

                    # Déterminer le compte charge à utiliser (hiérarchie: compte_charge_id produit > compte_achat_id config > compte_variation_stock_id)
                    compte_charge_id = product_compte_charge_id or compte_achat_id

                    # cogs basé sur coût moyen d'achat
                    cogs_amount = unit_cost * qty
            
                    # Débit : Compte charge (COGS) - utiliser le compte déterminé selon la hiérarchie
                    session.execute(text("""
                        INSERT INTO compta_ecritures
                        (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                        VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
                    """), {
                        'journal_id': journal_stock_id,
                        'compte_id': compte_charge_id,
                        'debit': cogs_amount,
                        'credit': 0,
                        'ordre': ordre_stock,
                        'libelle': f"Charge {product_name} (x{qty})",
                        'date_creation': datetime.now()
                    })
                    ordre_stock += 1

                    # Crédit : Compte stock spécifique au produit (réduction de l'actif stock)
                    # Utiliser stock_account_id du produit s'il existe, sinon fallback au compte stock global
                    compte_stock_produit = product_meta[3] if product_meta and len(product_meta) > 3 and product_meta[3] is not None else compte_stock_id
                    
                    session.execute(text("""
                        INSERT INTO compta_ecritures
                        (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                        VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
                    """), {
                        'journal_id': journal_stock_id,
                        'compte_id': compte_stock_produit,
                        'debit': 0,
                        'credit': cogs_amount,
                        'ordre': ordre_stock,
                        'libelle': f"Sortie stock {product_name} (x{qty})",
                        'date_creation': datetime.now()
                    })
                    ordre_stock += 1

            # 4. Créer les écritures de PAIEMENT (seulement si paiement reçu)
            payment_method = sale_data.get('payment_method')
            if amount_received > 0 and payment_method:
                # Chercher le compte caisse lié au mode de paiement sélectionné
                pm_row = session.execute(text("""
                    SELECT compte_id FROM core_payment_modes
                    WHERE enterprise_id = 1 AND is_active = 1
                    AND (label = :pm OR code = :pm_lower)
                    LIMIT 1
                """), {'pm': payment_method, 'pm_lower': payment_method.lower()}).fetchone()
                compte_caisse_paiement_id = (pm_row[0] if pm_row and pm_row[0] else None) or compte_caisse_id

                # Journal de paiement
                journal_payment_result = session.execute(text("""
                    INSERT INTO compta_journaux
                    (date_operation, libelle, montant, type_operation, reference, description,
                     enterprise_id, user_id, date_creation, date_modification, valide)
                    VALUES (:date_operation, :libelle, :montant, :type_operation, :reference,
                            :description, :enterprise_id, :user_id, :date_creation, :date_modification, :valide)
                """), {
                    'date_operation': sale_data['sale_date'],
                    'libelle': f"Paiement {numero_commande}",
                    'montant': amount_received,
                    'type_operation': 'Caisse',
                    'reference': f"PAI-{numero_commande}",
                    'description': f"Paiement vente - {sale_data['payment_method']}",
                    'enterprise_id': 1,
                    'user_id': getattr(self.current_user, 'id', 1),
                    'date_creation': datetime.now(),
                    'date_modification': datetime.now(),
                    'valide': 0
                })

                session.flush()
                journal_payment_id_result = session.execute(text("SELECT last_insert_rowid()"))
                journal_payment_id = journal_payment_id_result.fetchone()[0]

                # Écriture débit : Compte de caisse du mode de paiement
                session.execute(text("""
                    INSERT INTO compta_ecritures
                    (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                    VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
                """), {
                    'journal_id': journal_payment_id,
                    'compte_id': compte_caisse_paiement_id,
                    'debit': amount_received,
                    'credit': 0,
                    'ordre': 1,
                    'libelle': f"Encaissement {sale_data['payment_method']} - {numero_commande}",
                    'date_creation': datetime.now()
                })

                # Écriture crédit : Compte client
                if compte_client_id:
                    session.execute(text("""
                        INSERT INTO compta_ecritures
                        (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                        VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
                    """), {
                        'journal_id': journal_payment_id,
                        'compte_id': compte_client_id,
                        'debit': 0,
                        'credit': amount_received,
                        'ordre': 2,
                        'libelle': f"Règlement client - {numero_commande}",
                        'date_creation': datetime.now()
                    })

            return True, f"Écritures comptables créées - Vente: {journal_sale_id}" + \
                        (f", Paiement: {journal_payment_id}" if amount_received > 0 else "")

        except Exception as e:
            return False, f"Erreur écritures comptables avancées: {str(e)}"

    def _update_pos_stock(self, session: Session, product_id: int, quantity_sold: int, unit_price, line_total, numero_commande):
        """Met à jour le stock POS (soustraction automatique depuis l'entrepôt POS_2)"""
        try:
            # Chercher l'entrepôt avec le code POS_2 (entrepôt boutique)
            warehouse_result = session.execute(text("""
                SELECT id FROM stock_warehouses
                WHERE code = 'POS_2' AND is_active = 1
                LIMIT 1
            """))

            warehouse_row = warehouse_result.fetchone()
            if not warehouse_row:
                print(f"⚠️ Entrepôt POS_2 non trouvé pour le produit {product_id}")
                return

            warehouse_id = warehouse_row[0]

            # Récupérer le stock actuel
            stock_result = session.execute(text("""
                SELECT quantity FROM stock_produits_entrepot
                WHERE product_id = :product_id AND warehouse_id = :warehouse_id
                LIMIT 1
            """), {'product_id': product_id, 'warehouse_id': warehouse_id})

            stock_row = stock_result.fetchone()
            current_stock = stock_row[0] if stock_row else 0

            # Calculer le nouveau stock (ne pas aller en négatif)
            new_stock = max(0, current_stock - quantity_sold)

            # Mettre à jour ou insérer le stock
            if stock_row:
                # Mettre à jour
                session.execute(text("""
                    UPDATE stock_produits_entrepot
                    SET quantity = :new_quantity, updated_at = :updated_at
                    WHERE product_id = :product_id AND warehouse_id = :warehouse_id
                """), {
                    'product_id': product_id,
                    'new_quantity': new_stock,
                    'warehouse_id': warehouse_id,
                    'updated_at': datetime.now()
                })
            else:
                # Insérer (si pas de stock existant)
                session.execute(text("""
                    INSERT INTO stock_produits_entrepot
                    (product_id, warehouse_id, quantity, reserved_quantity, unit_cost, total_cost, min_stock_level, created_at, updated_at)
                    VALUES (:product_id, :warehouse_id, :quantity, 0, 0, 0, 0, :created_at, :updated_at)
                """), {
                    'product_id': product_id,
                    'warehouse_id': warehouse_id,
                    'quantity': new_stock,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                })
            #insertion dans mouvement stock
            session.execute(text("""
                        INSERT INTO stock_mouvements(
                            product_id, warehouse_id, movement_type, quantity, unit_cost, total_cost, 
                            destination_warehouse_id, reference, description, user_id, movement_date, created_at
                        )VALUES(
                            :product_id, :warehouse_id, :movement_type, :quantity, :unit_cost, :total_cost,
                            :destination_warehouse_id, :reference, :description, :user_id, :movement_date, :created_at
                        )"""), {
                            'product_id': product_id,
                            'warehouse_id': 2,
                            'movement_type': 'SORTIE',
                            'quantity':quantity_sold,
                            'unit_cost': unit_price,
                            'total_cost':line_total,
                            'destination_warehouse_id':warehouse_id,
                            'reference':numero_commande,
                            'description':"Vente Commande - " + numero_commande,
                            'user_id':1, # TODO A implemnter
                            'movement_date':datetime.now(),
                            'created_at': datetime.now()
                            
                        })

            print(f"📦 Stock mis à jour - Produit {product_id}: {current_stock} → {new_stock}")

        except Exception as e:
            print(f"❌ Erreur mise à jour stock: {e}")
            # Ne pas faire échouer la vente pour un problème de stock

    def validate_stock_availability(self, cart_items: List[Dict]) -> Tuple[bool, str]:
        """
        Valide que tous les produits du panier sont disponibles en stock

        Args:
            cart_items: Liste des articles du panier

        Returns:
            Tuple[bool, str]: (valide, message_erreur)
        """
        try:
            with self.db_manager.get_session() as session:
                insufficient_stock = []

                for item in cart_items:
                    if item.get('type') == 'product':
                        product_id = item['id']
                        requested_quantity = item['quantity']

                        # Récupérer le stock disponible
                        stock_result = session.execute(text("""
                            SELECT quantity FROM stock_produits_entrepot
                            WHERE product_id = :product_id AND warehouse_id = (
                                SELECT id FROM stock_warehouses WHERE code = 'POS_2' LIMIT 1
                            )
                            LIMIT 1
                        """), {'product_id': product_id})

                        stock_row = stock_result.fetchone()
                        available_stock = stock_row[0] if stock_row else 0

                        if available_stock < requested_quantity:
                            product_name = item.get('name', f'Produit {product_id}')
                            insufficient_stock.append(
                                f"{product_name}: {available_stock} disponible, {requested_quantity} demandé"
                            )

                if insufficient_stock:
                    return False, "Stock insuffisant:\\n" + "\\n".join(insufficient_stock)

                return True, "Stock disponible"

        except Exception as e:
            return False, f"Erreur lors de la validation du stock: {str(e)}"

    def cancel_sale(self, panier_id: int) -> Tuple[bool, str]:
        """
        Annule une vente avec logique comptable d'annulation

        Args:
            panier_id (int): ID du panier à annuler

        Returns:
            Tuple[bool, str]: (succès, message)
        """

        try:
            with self.db_manager.get_session() as session:
                # 0. Récupérer la configuration comptable
                config_result = session.execute(text("""
                    SELECT compte_vente_id, compte_caisse_id, compte_client_id, compte_remise_id, compte_stock_id, compte_variation_stock_id, compte_achat_id
                    FROM compta_config
                    WHERE pos_id = :pos_id
                    LIMIT 1
                """), {'pos_id': self.pos_id})

                config_row = config_result.fetchone()
                if not config_row:
                    return False, "Configuration comptable introuvable"

                compte_vente_id = config_row[0]
                compte_caisse_id = config_row[1]
                compte_client_id = config_row[2]
                compte_remise_id = config_row[3]
                compte_stock_id = config_row[4]
                compte_variation_stock_id = config_row[5]
                compte_achat_id = config_row[6]

                # 1. Récupérer les informations du panier
                panier_result = session.execute(text("""
                    SELECT id, numero_commande, status, total_final, client_id, payment_method
                    FROM shop_paniers
                    WHERE id = :panier_id
                """), {'panier_id': panier_id})

                panier_row = panier_result.fetchone()
                if not panier_row:
                    return False, "Panier introuvable"

                numero_commande = panier_row[1]
                current_status = panier_row[2]
                total_amount = float(panier_row[3])
                client_id = panier_row[4]
                payment_method = panier_row[5]

                if current_status == 'cancelled':
                    return False, "Cette commande est déjà annulée"

                # 0bis. Récupérer le total payé pour ce panier
                payment_sum_result = session.execute(text("""
                    SELECT COALESCE(SUM(amount), 0)
                    FROM shop_payments
                    WHERE panier_id = :panier_id
                """), {'panier_id': panier_id})
                amount_paid = float(payment_sum_result.fetchone()[0] or 0)

                # 1bis. Annulation automatique de tous les journaux liés à la commande
                # Chercher tous les journaux dont le libellé ou la référence contient le numéro de commande
                journaux = session.execute(text("""
                    SELECT id, date_operation, libelle, montant, type_operation, reference, description, enterprise_id, user_id
                    FROM compta_journaux
                    WHERE libelle LIKE :cmd OR reference LIKE :cmd
                """), {'cmd': f'%{numero_commande}%'}).fetchall()

                for journal in journaux:
                    journal_id = journal.id
                    # Créer un journal d'annulation
                    ann_libelle = f"Annulation automatique - {journal.libelle}"
                    ann_reference = f"ANN-{journal.reference}" if journal.reference else None
                    ann_journal_id = session.execute(text("""
                        INSERT INTO compta_journaux
                        (date_operation, libelle, montant, type_operation, reference, description, enterprise_id, user_id, date_creation, date_modification, valide)
                        VALUES (:date_operation, :libelle, :montant, :type_operation, :reference, :description, :enterprise_id, :user_id, :date_creation, :date_modification, :valide)
                    """), {
                        'date_operation': journal.date_operation,
                        'libelle': ann_libelle,
                        'montant': journal.montant,
                        'type_operation': 'annulation',
                        'reference': ann_reference,
                        'description': f"Annulation automatique du journal lié à la commande {numero_commande}",
                        'enterprise_id': journal.enterprise_id,
                        'user_id': journal.user_id,
                        'date_creation': datetime.now(),
                        'date_modification': datetime.now(),
                        'valide': 0
                    })
                    session.flush()
                    ann_journal_id_val = session.execute(text("SELECT last_insert_rowid()")).fetchone()[0]

                    # Récupérer toutes les écritures du journal d'origine
                    ecritures = session.execute(text("""
                        SELECT compte_comptable_id, debit, credit, ordre, libelle
                        FROM compta_ecritures
                        WHERE journal_id = :jid
                    """), {'jid': journal_id}).fetchall()
                    for ecriture in ecritures:
                        # Inverser débit/credit
                        session.execute(text("""
                            INSERT INTO compta_ecritures
                            (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                            VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
                        """), {
                            'journal_id': ann_journal_id_val,
                            'compte_id': ecriture.compte_comptable_id,
                            'debit': ecriture.credit,
                            'credit': ecriture.debit,
                            'ordre': ecriture.ordre,
                            'libelle': f"Annulation automatique - {ecriture.libelle}",
                            'date_creation': datetime.now()
                        })

                # ...existing code...

                # 4. Récupérer les articles du panier (pour remise stock)
                cart_items = []
                # Produits
                products_result = session.execute(text("""
                    SELECT sp.product_id, sp.quantity, sp.price_unit, sp.total_price, cp.name, cp.compte_charge_id
                    FROM shop_paniers_products sp
                    JOIN core_products cp ON sp.product_id = cp.id
                    WHERE sp.panier_id = :panier_id
                """), {'panier_id': panier_id})

                for row in products_result:
                    cart_items.append({
                        'type': 'product',
                        'id': row[0],
                        'quantity': row[1],
                        'unit_price': float(row[2]),
                        'total_price': float(row[3]),
                        'name': row[4],
                        'compte_charge_id': row[5]
                    })

                # Services
                services_result = session.execute(text("""
                    SELECT ss.service_id, ss.quantity, ss.price_unit, ss.total_price, s.name, s.id as service_source_id
                    FROM shop_paniers_services ss
                    JOIN shop_services s ON ss.service_id = s.id
                    WHERE ss.panier_id = :panier_id
                """), {'panier_id': panier_id})

                for row in services_result:
                    cart_items.append({
                        'type': 'service',
                        'id': row[0],
                        'quantity': row[1],
                        'unit_price': float(row[2]),
                        'total_price': float(row[3]),
                        'name': row[4],
                        'source': 'shop'
                    })

                # 5. Si c'était un inventaire permanent, supprimer les journaux de sortie stock (et remettre le stock)
                if cart_items and any(item.get('type') == 'product' for item in cart_items):
                    # Supprimer les journaux de stock liés à la commande
                    stock_journaux = session.execute(text("""
                        SELECT id FROM compta_journaux
                        WHERE (libelle LIKE :cmd OR reference LIKE :cmd) AND type_operation = 'stock'
                    """), {'cmd': f'%{numero_commande}%'}).fetchall()
                    for sj in stock_journaux:
                        session.execute(text("DELETE FROM compta_ecritures WHERE journal_id = :jid"), {'jid': sj.id})
                        session.execute(text("DELETE FROM compta_journaux WHERE id = :jid"), {'jid': sj.id})

                    # Pour chaque produit, remettre le stock
                    for item in cart_items:
                        if item.get('type') != 'product':
                            continue

                        product_id = item.get('id')
                        qty = item.get('quantity', 0)

                        # Récupérer le coût du produit
                        cost_result = session.execute(text("""
                            SELECT cost FROM core_products
                            WHERE id = :product_id
                        """), {'product_id': product_id})
                        cost_row = cost_result.fetchone()
                        unit_cost = float(cost_row[0]) if cost_row and cost_row[0] is not None else 0.0

                        # Déterminer le compte charge utilisé lors de la vente
                        compte_charge_id = item.get('compte_charge_id') or compte_achat_id or compte_variation_stock_id

                        cogs_amount = unit_cost * qty
                        if cogs_amount <= 0:
                            continue

                # 6. Si il y avait un paiement, supprimer les journaux/écritures de paiement
                if amount_paid > 0 and payment_method and compte_caisse_id:
                    pay_journaux = session.execute(text("""
                        SELECT id FROM compta_journaux
                        WHERE libelle LIKE :cmd OR reference LIKE :cmd
                    """), {'cmd': f'%{numero_commande}%'}).fetchall()
                    for pj in pay_journaux:
                        session.execute(text("DELETE FROM compta_ecritures WHERE journal_id = :jid"), {'jid': pj.id})
                        session.execute(text("DELETE FROM compta_journaux WHERE id = :jid"), {'jid': pj.id})

                # 9. Mettre à jour le statut du panier
                session.execute(text("""
                    UPDATE shop_paniers
                    SET status = 'cancelled', updated_at = :updated_at
                    WHERE id = :panier_id
                """), {
                    'panier_id': panier_id,
                    'updated_at': datetime.now()
                })

                # 10. Remettre le paiement à 0 (logique métier)
                if amount_paid > 0:
                    session.execute(text("""
                        UPDATE shop_payments
                        SET amount = 0
                        WHERE panier_id = :panier_id
                    """), {
                        'panier_id': panier_id
                    })

                # 10bis. Supprimer les journaux et écritures d'origine liés à la commande
                for journal in journaux:
                    # Supprimer les écritures associées au journal original
                    session.execute(text("""
                        DELETE FROM compta_ecritures
                        WHERE journal_id = :jid
                    """), {'jid': journal.id})
                    # Supprimer le journal original
                    session.execute(text("""
                        DELETE FROM compta_journaux
                        WHERE id = :jid
                    """), {'jid': journal.id})

                # 11. Remettre le stock (logique inverse de la vente)
                for item in cart_items:
                    if item.get('type') == 'product':
                        self._update_pos_stock_cancel(session, item['id'], item['quantity'], numero_commande)

                # Valider la transaction
                session.commit()

                return True, f"✅ Commande {numero_commande} annulée avec succès"

        except Exception as e:
            return False, f"Erreur lors de l'annulation: {str(e)}"

    def _update_pos_stock_cancel(self, session: Session, product_id: int, quantity_returned: int, numero_commande: str):
        """Remet le stock lors d'une annulation (inverse de _update_pos_stock)"""
        try:
            # D'abord, essayer de récupérer l'entrepôt via le POSWarehouseHelper
            warehouse_id = None
            try:
                from ayanna_erp.modules.stock.helpers.pos_warehouse_helper import POSWarehouseHelper
                pos_warehouse = POSWarehouseHelper.get_pos_warehouse(self.pos_id)
                if pos_warehouse:
                    warehouse_id = pos_warehouse.id
                    print(f"📍 Entrepôt trouvé via POSWarehouseHelper: {pos_warehouse.name} (id={warehouse_id})")
            except Exception as e:
                print(f"⚠️ Erreur POSWarehouseHelper: {e}")
            
            # Si pas trouvé, chercher l'entrepôt POS_2 (fallback)
            if not warehouse_id:
                warehouse_result = session.execute(text("""
                    SELECT id FROM stock_warehouses
                    WHERE code = 'POS_2' AND is_active = 1
                    LIMIT 1
                """))
                warehouse_row = warehouse_result.fetchone()
                if warehouse_row:
                    warehouse_id = warehouse_row[0]
                    print(f"📍 Entrepôt fallback POS_2 trouvé (id={warehouse_id})")
            
            # Si toujours pas trouvé, chercher n'importe quel entrepôt de type Point de Vente
            if not warehouse_id:
                warehouse_result = session.execute(text("""
                    SELECT id, name FROM stock_warehouses
                    WHERE type = 'Point de Vente' AND is_active = 1
                    LIMIT 1
                """))
                warehouse_row = warehouse_result.fetchone()
                if warehouse_row:
                    warehouse_id = warehouse_row[0]
                    print(f"📍 Entrepôt Point de Vente trouvé: {warehouse_row[1]} (id={warehouse_id})")

            if not warehouse_id:
                print(f"⚠️ Aucun entrepôt trouvé pour l'annulation du produit {product_id}")
                return

            # Récupérer le stock actuel
            stock_result = session.execute(text("""
                SELECT quantity FROM stock_produits_entrepot
                WHERE product_id = :product_id AND warehouse_id = :warehouse_id
                LIMIT 1
            """), {'product_id': product_id, 'warehouse_id': warehouse_id})

            stock_row = stock_result.fetchone()
            current_stock = stock_row[0] if stock_row else 0

            # Remettre le stock (ajouter la quantité)
            new_stock = current_stock + quantity_returned

            # Mettre à jour ou insérer le stock
            if stock_row:
                session.execute(text("""
                    UPDATE stock_produits_entrepot
                    SET quantity = :new_quantity, updated_at = :updated_at
                    WHERE product_id = :product_id AND warehouse_id = :warehouse_id
                """), {
                    'product_id': product_id,
                    'new_quantity': new_stock,
                    'warehouse_id': warehouse_id,
                    'updated_at': datetime.now()
                })
            else:
                session.execute(text("""
                    INSERT INTO stock_produits_entrepot
                    (product_id, warehouse_id, quantity, reserved_quantity, unit_cost, total_cost, min_stock_level, created_at, updated_at)
                    VALUES (:product_id, :warehouse_id, :quantity, 0, 0, 0, 0, :created_at, :updated_at)
                """), {
                    'product_id': product_id,
                    'warehouse_id': warehouse_id,
                    'quantity': new_stock,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                })

            # Mouvement de stock pour annulation
            session.execute(text("""
                        INSERT INTO stock_mouvements(
                            product_id, warehouse_id, movement_type, quantity, unit_cost, total_cost,
                            destination_warehouse_id, reference, description, user_id, movement_date, created_at
                        )VALUES(
                            :product_id, :warehouse_id, :movement_type, :quantity, :unit_cost, :total_cost,
                            :destination_warehouse_id, :reference, :description, :user_id, :movement_date, :created_at
                        )"""), {
                            'product_id': product_id,
                            'warehouse_id': warehouse_id,
                            'movement_type': 'ANNULATION',
                            'quantity': quantity_returned,
                            'unit_cost': 0,  # Pas de coût pour l'annulation
                            'total_cost': 0,
                            'destination_warehouse_id': warehouse_id,
                            'reference': "ANN-FAC- " + numero_commande,
                            'description': "Annulation vente - " + numero_commande,
                            'user_id': 1,
                            'movement_date': datetime.now(),
                            'created_at': datetime.now()

                        })

            print(f"📦 Stock remis - Produit {product_id}: {current_stock} → {new_stock}")

        except Exception as e:
            print(f"❌ Erreur remise stock annulation: {e}")