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
from ..model.models import ShopClient, ShopPanier, ShopService


class VenteController:
    """Contrôleur gérant la logique de vente et comptabilité"""

    def __init__(self, pos_id: int, current_user=None):
        self.pos_id = pos_id
        self.current_user = current_user
        self.db_manager = DatabaseManager()

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

                # Générer numéro de commande unique
                import random
                numero_commande = f"CMD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}"

                # 1. Créer le panier (toujours, même si pas payé)
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
                    'status': 'completed' if amount_received >= total_amount else 'pending',
                    'payment_method': payment_data['method'] if amount_received > 0 else 'Credit',
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
                        self._update_pos_stock(session, product_id, quantity)

                    elif item.get('type') == 'service':
                        quantity = item.get('quantity')
                        unit_price = item.get('unit_price')
                        line_total = unit_price * quantity

                        # Déterminer l'ID du ShopService
                        service_id = None
                        if item.get('source') == 'shop':
                            service_id = item.get('id')
                        elif item.get('source') == 'event':
                            # Chercher ShopService existant par nom
                            svc = session.query(ShopService).filter(ShopService.name == item.get('name')).first()
                            if not svc:
                                svc = ShopService(
                                    pos_id=self.pos_id,
                                    name=item.get('name'),
                                    description='',
                                    cost=0.0,
                                    price=unit_price,
                                    is_active=True
                                )
                                session.add(svc)
                                session.flush()
                                session.refresh(svc)
                            service_id = svc.id

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
                    'amount_received': amount_received,
                    'payment_method': payment_data['method'] if amount_received > 0 else None,
                    'sale_date': datetime.now(),
                    'client_id': sale_data.get('client_id'),
                    'cart_items': cart_items
                }

                success, message = self._create_advanced_sale_accounting_entries(session, accounting_data)
                if not success:
                    return False, f"Erreur comptable: {message}", None

                # 4. Traiter les écritures comptables de paiement seulement si il y a eu un paiement
                if amount_received > 0:
                    # Enregistrer le paiement
                    session.execute(text("""
                        INSERT INTO shop_payments
                        (panier_id, amount, payment_method, payment_date, reference)
                        VALUES (:panier_id, :amount, :payment_method, :payment_date, :reference)
                    """), {
                        'panier_id': panier_id,
                        'amount': amount_received,
                        'payment_method': payment_data['method'],
                        'payment_date': datetime.now(),
                        'reference': numero_commande
                    })

                # Valider la transaction
                session.commit()

                # Message de succès
                if amount_received == 0:
                    message = f"✅ Commande #{numero_commande} enregistrée (non payée) - {total_amount:.0f} FC"
                elif amount_received >= total_amount:
                    message = f"✅ Vente #{numero_commande} complétée - {total_amount:.0f} FC"
                else:
                    message = f"✅ Vente #{numero_commande} partiellement payée - {amount_received:.0f}/{total_amount:.0f} FC"

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

    def _update_pos_stock(self, session: Session, product_id: int, quantity_sold: int):
        """Met à jour le stock POS (soustraction automatique depuis l'entrepôt POS_2)"""
        try:
            # Récupérer le stock actuel
            stock_result = session.execute(text("""
                SELECT quantity FROM stock_produits_entrepot
                WHERE product_id = :product_id AND warehouse_id = (
                    SELECT id FROM stock_warehouses WHERE code = 'POS_2' LIMIT 1
                )
                LIMIT 1
            """), {'product_id': product_id})

            current_stock_row = stock_result.fetchone()
            if current_stock_row:
                current_stock = current_stock_row[0]
                new_stock = max(0, current_stock - quantity_sold)  # Ne pas aller en négatif

                # Mettre à jour le stock
                session.execute(text("""
                    UPDATE shop_stock
                    SET quantity = :new_quantity, updated_at = :updated_at
                    WHERE product_id = :product_id AND warehouse_id = (
                        SELECT id FROM core_warehouses WHERE code = 'POS_2' LIMIT 1
                    )
                """), {
                    'product_id': product_id,
                    'new_quantity': new_stock,
                    'updated_at': datetime.now()
                })

                print(f"📦 Stock mis à jour - Produit {product_id}: {current_stock} → {new_stock}")

            else:
                print(f"⚠️ Aucun stock trouvé pour le produit {product_id} dans POS_2")

        except Exception as e:
            print(f"❌ Erreur mise à jour stock: {e}")
            # Ne pas faire échouer la vente pour un problème de stock

    def _create_advanced_sale_accounting_entries(self, session: Session, sale_data: Dict) -> Tuple[bool, str]:
        """Crée les écritures comptables avancées avec répartition proportionnelle"""
        try:
            panier_id = sale_data['panier_id']
            numero_commande = sale_data['numero_commande']
            total_amount = sale_data['total_amount']
            amount_received = sale_data['amount_received']
            discount_amount = sale_data['discount_amount']
            cart_items = sale_data['cart_items']
            client_id = sale_data['client_id']

            # Récupérer la configuration comptable
            config_result = session.execute(text("""
                SELECT compte_vente_id, compte_caisse_id, compte_client_id, compte_remise_id
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

            # Validation : si remise et pas de compte remise configuré, refuser
            if discount_amount > 0 and not compte_remise_id:
                return False, "Une remise a été appliquée mais aucun compte remise n'est configuré pour ce point de vente. Veuillez configurer le compte remise dans les paramètres comptables."

            # Calculer le poids de chaque article dans le panier
            total_cart_weight = sum(item['unit_price'] * item['quantity'] for item in cart_items)
            if total_cart_weight == 0:
                return False, "Panier vide"

            # 3. Créer les écritures de VENTE (toujours, même pour paiement partiel)
            # Journal de vente
            journal_sale_result = session.execute(text("""
                INSERT INTO compta_journaux
                (date_operation, libelle, montant, type_operation, reference, description,
                 enterprise_id, user_id, date_creation, date_modification)
                VALUES (:date_operation, :libelle, :montant, :type_operation, :reference,
                        :description, :enterprise_id, :user_id, :date_creation, :date_modification)
            """), {
                'date_operation': sale_data['sale_date'],
                'libelle': f"Vente {numero_commande}",
                'montant': total_amount,
                'type_operation': 'entree',
                'reference': numero_commande,
                'description': f"Vente boutique - {len(cart_items)} articles",
                'enterprise_id': 1,  # TODO: Récupérer dynamiquement
                'user_id': getattr(self.current_user, 'id', 1),
                'date_creation': datetime.now(),
                'date_modification': datetime.now()
            })

            session.flush()
            journal_sale_id_result = session.execute(text("SELECT last_insert_rowid()"))
            journal_sale_id = journal_sale_id_result.fetchone()[0]

            ordre = 1

            # Écritures de vente : créditer TOUJOURS les comptes produits/services de leur sous-total complet
            for item in cart_items:
                item_total = item['unit_price'] * item['quantity']

                # TOUJOURS créditer le montant complet de l'item (logique simplifiée)
                item_sale_amount = item_total

                # Déterminer le compte comptable pour cet article
                compte_item_id = None

                if item.get('type') == 'product':
                    # Récupérer le compte produit depuis la base
                    product_result = session.execute(text("""
                        SELECT compte_produit_id FROM core_products
                        WHERE id = :product_id
                    """), {'product_id': item['id']})
                    product_row = product_result.fetchone()
                    compte_item_id = product_row[0] if product_row and product_row[0] else compte_vente_id

                    # Validation: si pas de compte_produit_id et pas de compte_vente_id, erreur
                    if not compte_item_id:
                        return False, f"Produit '{item.get('name', 'N/A')}' n'a pas de compte comptable configuré et aucun compte de vente par défaut n'est défini."

                elif item.get('type') == 'service':
                    # Pour les services, utiliser le compte de vente par défaut
                    compte_item_id = compte_vente_id
                    if not compte_item_id:
                        return False, f"Service '{item.get('name', 'N/A')}' : aucun compte de vente par défaut configuré."

                if compte_item_id:
                    # Écriture crédit : Compte produit/service
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
                    'debit': discount_amount,  # Débiter le compte remise
                    'credit': 0,
                    'ordre': ordre,
                    'libelle': f"Remise accordée {numero_commande}",
                    'date_creation': datetime.now()
                })
                ordre += 1

            # 4. Créer les écritures de PAIEMENT (seulement si paiement reçu)
            payment_method = sale_data.get('payment_method')
            if amount_received > 0 and payment_method:
                # Journal de paiement
                journal_payment_result = session.execute(text("""
                    INSERT INTO compta_journaux
                    (date_operation, libelle, montant, type_operation, reference, description,
                     enterprise_id, user_id, date_creation, date_modification)
                    VALUES (:date_operation, :libelle, :montant, :type_operation, :reference,
                            :description, :enterprise_id, :user_id, :date_creation, :date_modification)
                """), {
                    'date_operation': sale_data['sale_date'],
                    'libelle': f"Paiement {numero_commande}",
                    'montant': amount_received,
                    'type_operation': 'entree',
                    'reference': f"PAI-{numero_commande}",
                    'description': f"Paiement vente - {sale_data['payment_method']}",
                    'enterprise_id': 1,
                    'user_id': getattr(self.current_user, 'id', 1),
                    'date_creation': datetime.now(),
                    'date_modification': datetime.now()
                })

                session.flush()
                journal_payment_id_result = session.execute(text("SELECT last_insert_rowid()"))
                journal_payment_id = journal_payment_id_result.fetchone()[0]

                # Écriture débit : Compte de caisse
                session.execute(text("""
                    INSERT INTO compta_ecritures
                    (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                    VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
                """), {
                    'journal_id': journal_payment_id,
                    'compte_id': compte_caisse_id,
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

    def _update_pos_stock(self, session: Session, product_id: int, quantity_sold: int):
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
                    (product_id, warehouse_id, quantity, created_at, updated_at)
                    VALUES (:product_id, :warehouse_id, :quantity, :created_at, :updated_at)
                """), {
                    'product_id': product_id,
                    'warehouse_id': warehouse_id,
                    'quantity': new_stock,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
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