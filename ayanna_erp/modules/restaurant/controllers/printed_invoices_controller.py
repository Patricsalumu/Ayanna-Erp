"""
Controller for printed restaurant invoices history.
"""
import json
from datetime import datetime, date, time
from types import SimpleNamespace
from sqlalchemy import inspect

from ayanna_erp.database.database_manager import get_database_manager
from ayanna_erp.modules.core.models import CoreProduct
from ayanna_erp.modules.restaurant.models.restaurant import (
    RestauPanier,
    RestauPrintedInvoice,
)


class PrintedInvoicesController:
    def __init__(self, entreprise_id=1):
        self.db = get_database_manager()
        self.entreprise_id = entreprise_id
        # Exécuter automatiquement la migration si nécessaire
        self._auto_migrate()

    def _table_available(self):
        try:
            inspector = inspect(self.db.engine)
            return inspector.has_table('restau_printed_invoices')
        except Exception:
            return False

    def _column_exists(self, column_name):
        """Vérifie si une colonne existe dans la table restau_printed_invoices"""
        try:
            inspector = inspect(self.db.engine)
            if not inspector.has_table('restau_printed_invoices'):
                return False
            
            columns = {col['name'] for col in inspector.get_columns('restau_printed_invoices')}
            return column_name in columns
        except Exception:
            return False

    def _auto_migrate(self):
        """Exécute automatiquement la migration si les colonnes manquent"""
        try:
            if not self._table_available():
                return
            
            # Vérifier si les colonnes manquent
            if not self._column_exists('customer_id'):
                print("⏳ Migration automatique: ajout de la colonne customer_id...")
                session = self.db.get_session()
                try:
                    # Utiliser SQLAlchemy pour exécuter du SQL brut
                    from sqlalchemy import text
                    
                    # Ajouter la colonne customer_id
                    session.execute(text("""
                        ALTER TABLE restau_printed_invoices 
                        ADD COLUMN customer_id INTEGER
                    """))
                    
                    # Créer les indexes
                    session.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_restau_printed_invoices_customer_id 
                        ON restau_printed_invoices(customer_id)
                    """))
                    
                    # Ajouter un index sur printed_by_user_id s'il ne l'est pas déjà
                    session.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_restau_printed_invoices_printed_by_user_id 
                        ON restau_printed_invoices(printed_by_user_id)
                    """))
                    
                    session.commit()
                    print("✅ Migration automatique complétée: customer_id ajouté avec indexes")
                except Exception as e:
                    session.rollback()
                    # Si la colonne existe déjà, ignorer gracieusement
                    if 'duplicate column' in str(e) or 'already exists' in str(e):
                        print("✅ Migration: colonnes déjà présentes")
                    else:
                        print(f"⚠️  Migration: {e}")
                finally:
                    session.close()
        except Exception as e:
            print(f"⚠️  Erreur lors de la migration automatique: {e}")
            # Continuer même si la migration échoue

    def _serialize_products(self, session, panier):
        snapshot = []
        total_qty = 0
        for line in getattr(panier, 'produits', []) or []:
            qty = int(getattr(line, 'quantity', 0) or 0)
            unit_price = float(getattr(line, 'price', 0.0) or 0.0)
            line_total = float(getattr(line, 'total', qty * unit_price) or (qty * unit_price))
            product_name = str(getattr(line, 'product_id', ''))

            try:
                prod = session.query(CoreProduct).filter_by(id=getattr(line, 'product_id', None)).first()
                if prod and getattr(prod, 'name', None):
                    product_name = str(prod.name)
            except Exception:
                pass

            snapshot.append({
                'product_id': getattr(line, 'product_id', None),
                'name': product_name,
                'quantity': qty,
                'unit_price': unit_price,
                'line_total': line_total,
            })
            total_qty += qty

        return snapshot, total_qty

    def record_printed_invoice(self, panier_id, printed_by_user_id=None):
        """
        Enregistre une impression de facture pour un panier.
        Retourne: (success: bool, message_or_id: str|int)
        """
        if not self._table_available():
            return False, 'TABLE_RESTAU_PRINTED_INVOICES_MISSING'

        session = self.db.get_session()
        try:
            panier = (
                session.query(RestauPanier)
                .filter(
                    RestauPanier.id == panier_id,
                    RestauPanier.entreprise_id == self.entreprise_id,
                )
                .first()
            )
            if not panier:
                return False, f'Panier introuvable: {panier_id}'

            products_snapshot, total_qty = self._serialize_products(session, panier)
            lines_count = len(products_snapshot)

            try:
                total_amount = float(getattr(panier, 'total_final', 0.0) or 0.0)
            except Exception:
                total_amount = 0.0

            rec = RestauPrintedInvoice(
                entreprise_id=self.entreprise_id,
                panier_id=panier.id,
                total_items_quantity=total_qty,
                product_lines_count=lines_count,
                total_amount=total_amount,
                products_snapshot=json.dumps(products_snapshot, ensure_ascii=False),
                customer_id=getattr(panier, 'client_id', None),  # Récupérer le client du panier
                printed_by_user_id=printed_by_user_id or getattr(panier, 'user_id', None),
                printed_at=datetime.now(),
                created_at=datetime.now(),
            )
            session.add(rec)
            session.commit()
            return True, rec.id
        except Exception as e:
            try:
                session.rollback()
            except Exception:
                pass
            return False, str(e)
        finally:
            self.db.close_session()

    def _safe_load_snapshot(self, raw_value):
        if not raw_value:
            return []
        try:
            val = json.loads(raw_value)
            if isinstance(val, list):
                return val
            return []
        except Exception:
            return []

    def _build_products_text(self, snapshot_rows):
        parts = []
        for row in snapshot_rows:
            name = str(row.get('name') or row.get('product_id') or '')
            qty = int(row.get('quantity') or 0)
            parts.append(f"{name} x{qty}")
        return ' | '.join(parts)

    def list_printed_invoices_for_date(
        self,
        target_date,
        product_search=None,
        panier_search=None,
        panier_status_filter='all',
        amount_change_filter='all',
    ):
        """
        Liste les factures imprimees pour une journee donnee avec filtres.

        - panier_status_filter: all | en_cours | valide | annule
        - amount_change_filter: all | changed | unchanged
        """
        if not self._table_available():
            return [], 'TABLE_RESTAU_PRINTED_INVOICES_MISSING'

        if isinstance(target_date, datetime):
            d = target_date.date()
        elif isinstance(target_date, date):
            d = target_date
        else:
            d = datetime.now().date()

        start_dt = datetime.combine(d, time.min)
        end_dt = datetime.combine(d, time.max)

        product_term = (product_search or '').strip().lower()
        panier_term = (panier_search or '').strip().lower()

        session = self.db.get_session()
        try:
            try:
                from ayanna_erp.modules.boutique.model.models import ShopClient
            except Exception:
                ShopClient = None

            try:
                from ayanna_erp.database.database_manager import User as DBUser
            except Exception:
                DBUser = None

            rows = (
                session.query(RestauPrintedInvoice)
                .filter(
                    RestauPrintedInvoice.entreprise_id == self.entreprise_id,
                    RestauPrintedInvoice.printed_at >= start_dt,
                    RestauPrintedInvoice.printed_at <= end_dt,
                )
                .order_by(RestauPrintedInvoice.printed_at.desc(), RestauPrintedInvoice.id.desc())
                .all()
            )

            result = []
            for rec in rows:
                snapshot_rows = self._safe_load_snapshot(getattr(rec, 'products_snapshot', None))
                products_text = self._build_products_text(snapshot_rows)

                if product_term:
                    if product_term not in products_text.lower():
                        continue

                if panier_term and panier_term not in str(getattr(rec, 'panier_id', '')).lower():
                    continue

                panier = (
                    session.query(RestauPanier)
                    .filter(
                        RestauPanier.id == rec.panier_id,
                        RestauPanier.entreprise_id == self.entreprise_id,
                    )
                    .first()
                )

                panier_exists = panier is not None
                current_status = getattr(panier, 'status', None) if panier else None

                try:
                    current_total = float(getattr(panier, 'total_final', 0.0) or 0.0) if panier else None
                except Exception:
                    current_total = None

                try:
                    printed_total = float(getattr(rec, 'total_amount', 0.0) or 0.0)
                except Exception:
                    printed_total = 0.0

                amount_changed = False
                if panier_exists and current_status == 'valide' and current_total is not None:
                    amount_changed = abs(current_total - printed_total) > 0.009

                if panier_status_filter != 'all':
                    if not panier_exists:
                        continue
                    if str(current_status or '').strip().lower() != str(panier_status_filter).strip().lower():
                        continue

                if amount_change_filter == 'changed' and not amount_changed:
                    continue
                if amount_change_filter == 'unchanged' and amount_changed:
                    continue

                customer_id = getattr(rec, 'customer_id', None) or getattr(panier, 'client_id', None)
                printed_by_user_id = getattr(rec, 'printed_by_user_id', None) or getattr(panier, 'user_id', None)

                customer_name = None
                if customer_id and ShopClient is not None:
                    try:
                        c = session.query(ShopClient).filter_by(id=customer_id).first()
                        if c:
                            nom = str(getattr(c, 'nom', '') or '').strip()
                            prenom = str(getattr(c, 'prenom', '') or '').strip()
                            display = f"{nom} {prenom}".strip()
                            customer_name = display or str(getattr(c, 'name', '') or '').strip() or str(customer_id)
                    except Exception:
                        customer_name = str(customer_id)
                elif customer_id:
                    customer_name = str(customer_id)

                printed_by_user_name = None
                if printed_by_user_id and DBUser is not None:
                    try:
                        u = session.query(DBUser).filter_by(id=printed_by_user_id).first()
                        if u:
                            printed_by_user_name = (
                                str(getattr(u, 'name', '') or '').strip()
                                or str(getattr(u, 'email', '') or '').strip()
                                or str(printed_by_user_id)
                            )
                    except Exception:
                        printed_by_user_name = str(printed_by_user_id)
                elif printed_by_user_id:
                    printed_by_user_name = str(printed_by_user_id)

                result.append(
                    SimpleNamespace(
                        id=rec.id,
                        printed_at=rec.printed_at,
                        panier_id=rec.panier_id,
                        customer_id=customer_id,
                        printed_by_user_id=printed_by_user_id,
                        customer_name=customer_name,
                        printed_by_user_name=printed_by_user_name,
                        total_items_quantity=int(getattr(rec, 'total_items_quantity', 0) or 0),
                        product_lines_count=int(getattr(rec, 'product_lines_count', 0) or 0),
                        total_amount=printed_total,
                        products_text=products_text,
                        panier_exists=panier_exists,
                        current_status=current_status,
                        current_total=current_total,
                        amount_changed=amount_changed,
                    )
                )

            return result, None
        finally:
            self.db.close_session()
