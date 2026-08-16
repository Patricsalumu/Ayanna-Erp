import json
from collections import defaultdict
from datetime import datetime, time
from types import SimpleNamespace

from ayanna_erp.database.database_manager import get_database_manager
from ayanna_erp.modules.restaurant.models.restaurant import (
    RestauBonCommande,
    RestauPanier,
    RestauProduitPanier,
)
from ayanna_erp.modules.core.models import CoreProduct


class BonCommandeController:
    def __init__(self, entreprise_id=1):
        self.db = get_database_manager()
        self.entreprise_id = entreprise_id

    def _safe_load_snapshot(self, raw_json):
        if not raw_json:
            return []
        try:
            value = json.loads(raw_json)
            if isinstance(value, list):
                return value
            return []
        except Exception:
            return []

    def _get_today_bounds(self):
        today = datetime.now().date()
        start_dt = datetime.combine(today, time.min)
        end_dt = datetime.combine(today, time.max)
        return start_dt, end_dt

    def _compute_sent_quantities(self, panier_id):
        sent = defaultdict(int)
        session = self.db.get_session()
        try:
            rows = (
                session.query(RestauBonCommande)
                .filter(
                    RestauBonCommande.entreprise_id == self.entreprise_id,
                    RestauBonCommande.restau_panier_id == panier_id,
                    RestauBonCommande.statut == 'valide',
                )
                .all()
            )
            for rec in rows:
                for item in self._safe_load_snapshot(getattr(rec, 'produits_json', None)):
                    pid = item.get('produit_id') or item.get('product_id')
                    qty = int(item.get('quantite', item.get('quantity', 0)) or 0)
                    if pid is not None:
                        sent[int(pid)] += qty
        finally:
            self.db.close_session()
        return sent

    def _get_next_numero_bon(self):
        start_dt, end_dt = self._get_today_bounds()
        session = self.db.get_session()
        try:
            last = (
                session.query(RestauBonCommande)
                .filter(
                    RestauBonCommande.entreprise_id == self.entreprise_id,
                    RestauBonCommande.created_at >= start_dt,
                    RestauBonCommande.created_at <= end_dt,
                )
                .order_by(RestauBonCommande.numero_bon.desc())
                .first()
            )
            if not last or getattr(last, 'numero_bon', None) is None:
                return 1
            return int(last.numero_bon) + 1
        finally:
            self.db.close_session()

    def get_pending_bon_items(self, panier_id):
        session = self.db.get_session()
        try:
            panier = session.query(RestauPanier).filter_by(id=panier_id).first()
            if not panier:
                return []
            sent_qty = self._compute_sent_quantities(panier_id)
            current_lines = session.query(RestauProduitPanier).filter_by(panier_id=panier_id).all()

            aggregated = {}
            for line in current_lines:
                pid = int(getattr(line, 'product_id', 0) or 0)
                qty = int(getattr(line, 'quantity', 0) or 0)
                price = float(getattr(line, 'price', 0.0) or 0.0)
                if pid <= 0 or qty <= 0:
                    continue
                if pid not in aggregated:
                    aggregated[pid] = {
                        'produit_id': pid,
                        'nom': None,
                        'quantite': 0,
                        'prix_vente': price,
                    }
                aggregated[pid]['quantite'] += qty
                aggregated[pid]['prix_vente'] = price

            result = []
            for pid, current in aggregated.items():
                already_sent = sent_qty.get(pid, 0)
                diff = int(current['quantite']) - int(already_sent)
                if diff <= 0:
                    continue
                name = str(current.get('nom') or '')
                try:
                    prod = session.query(CoreProduct).filter_by(id=pid).first()
                    if prod and getattr(prod, 'name', None):
                        name = str(prod.name)
                except Exception:
                    pass
                result.append({
                    'produit_id': pid,
                    'nom': name or f'Produit {pid}',
                    'quantite': diff,
                    'prix_vente': float(current.get('prix_vente') or 0.0),
                })
            return result
        finally:
            self.db.close_session()

    def create_bon_commande(self, panier_id, user_id=None, client_id=None, serveuse_id=None):
        if not serveuse_id:
            return False, 'SERVEUSE_REQUIRED', None

        items = self.get_pending_bon_items(panier_id)
        if not items:
            return False, 'NO_NEW_ITEMS', None

        numero_bon = self._get_next_numero_bon()
        produits_json = json.dumps(items, ensure_ascii=False)
        montant_total = sum([float(i['quantite']) * float(i['prix_vente']) for i in items])

        session = self.db.get_session()
        try:
            bon = RestauBonCommande(
                entreprise_id=self.entreprise_id,
                numero_bon=numero_bon,
                restau_panier_id=panier_id,
                serveuse_id=serveuse_id,
                client_id=client_id,
                user_id=user_id,
                produits_json=produits_json,
                montant_total=montant_total,
                statut='valide',
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            session.add(bon)
            session.commit()
            session.refresh(bon)
            return True, bon, items
        except Exception as e:
            try:
                session.rollback()
            except Exception:
                pass
            return False, str(e), None
        finally:
            self.db.close_session()

    def cancel_bon(self, bon_id):
        session = self.db.get_session()
        try:
            bon = session.query(RestauBonCommande).filter_by(id=bon_id).first()
            if not bon:
                return False, 'BON_INEXISTANT'
            if getattr(bon, 'statut', None) == 'annule':
                return False, 'BON_ALREADY_CANCELLED'
            bon.statut = 'annule'
            bon.updated_at = datetime.now()
            session.commit()
            return True, 'OK'
        except Exception as e:
            try:
                session.rollback()
            except Exception:
                pass
            return False, str(e)
        finally:
            self.db.close_session()

    def list_bons_for_date(self, target_date=None, status_filter='all', panier_search=None):
        if isinstance(target_date, datetime):
            selected_date = target_date.date()
        else:
            selected_date = target_date or datetime.now().date()

        start_dt = datetime.combine(selected_date, time.min)
        end_dt = datetime.combine(selected_date, time.max)

        session = self.db.get_session()
        try:
            q = session.query(RestauBonCommande).filter(
                RestauBonCommande.entreprise_id == self.entreprise_id,
                RestauBonCommande.created_at >= start_dt,
                RestauBonCommande.created_at <= end_dt,
            )
            if status_filter and status_filter != 'all':
                q = q.filter(RestauBonCommande.statut == status_filter)
            q = q.order_by(RestauBonCommande.created_at.desc())
            rows = q.all()

            try:
                from ayanna_erp.modules.boutique.model.models import ShopClient
            except Exception:
                ShopClient = None
            try:
                from ayanna_erp.database.database_manager import User as DBUser
            except Exception:
                DBUser = None

            result = []
            for rec in rows:
                panier = None
                if getattr(rec, 'restau_panier_id', None) is not None:
                    panier = session.query(RestauPanier).filter_by(id=rec.restau_panier_id).first()

                customer_name = None
                if getattr(rec, 'client_id', None) and ShopClient is not None:
                    try:
                        c = session.query(ShopClient).filter_by(id=rec.client_id).first()
                        if c:
                            customer_name = ' '.join(filter(None, [getattr(c, 'nom', ''), getattr(c, 'prenom', '')])).strip() or str(c.id)
                    except Exception:
                        customer_name = None
                if not customer_name and getattr(rec, 'client_id', None) is not None:
                    customer_name = str(getattr(rec, 'client_id'))

                serveuse_name = None
                if getattr(rec, 'serveuse_id', None) and DBUser is not None:
                    try:
                        u = session.query(DBUser).filter_by(id=rec.serveuse_id).first()
                        if u:
                            serveuse_name = getattr(u, 'name', None) or getattr(u, 'email', None) or str(u.id)
                    except Exception:
                        serveuse_name = None
                if not serveuse_name and getattr(rec, 'serveuse_id', None) is not None:
                    serveuse_name = str(getattr(rec, 'serveuse_id'))

                products = self._safe_load_snapshot(getattr(rec, 'produits_json', None))
                products_text = ' | '.join(
                    f"{getattr(p, 'nom', p.get('nom') or p.get('name') or '')} x{int(p.get('quantite', p.get('quantity', 0)) or 0)}"
                    if isinstance(p, dict) else ''
                    for p in products
                )
                table_id = getattr(panier, 'table_id', None) if panier else None
                
                # Apply search filter
                if panier_search:
                    search_lower = str(panier_search).lower()
                    # Search in: panier_id, numero_bon, client_name, serveuse_name, products_text, montant_total
                    search_fields = [
                        str(getattr(rec, 'restau_panier_id', '')).lower(),
                        str(getattr(rec, 'numero_bon', '')).lower(),
                        str(customer_name or '').lower(),
                        str(serveuse_name or '').lower(),
                        str(products_text).lower(),
                        str(getattr(rec, 'montant_total', '')).lower(),
                    ]
                    if not any(search_lower in field for field in search_fields):
                        continue
                
                result.append(SimpleNamespace(
                    id=rec.id,
                    numero_bon=getattr(rec, 'numero_bon', None),
                    restau_panier_id=getattr(rec, 'restau_panier_id', None),
                    client_id=getattr(rec, 'client_id', None),
                    client_name=customer_name,
                    serveuse_name=serveuse_name,
                    table_id=table_id,
                    montant_total=getattr(rec, 'montant_total', 0.0),
                    statut=getattr(rec, 'statut', None),
                    created_at=getattr(rec, 'created_at', None),
                    updated_at=getattr(rec, 'updated_at', None),
                    products_text=products_text,
                    products=products,
                ))
            return result
        finally:
            self.db.close_session()
