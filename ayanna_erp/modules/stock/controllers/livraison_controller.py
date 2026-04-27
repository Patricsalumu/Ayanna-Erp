"""
Contrôleur pour la gestion des bons de livraison interne (transfert multi-produits)
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from sqlalchemy import text

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.stock.models import (
    StockLivraison, StockLivraisonItem,
    StockProduitEntrepot, StockWarehouse, StockMovement
)


class LivraisonController:
    """CRUD + logique métier pour les bons de livraison interne"""

    STATUTS = {
        'brouillon':    'Brouillon',
        'livre':        'Livré',
        'receptionne':  'Réceptionné',
        'annule':       'Annulé',
    }

    def __init__(self, entreprise_id: int):
        self.entreprise_id = entreprise_id
        self.db_manager = DatabaseManager()

    # ──────────────────────────────────────────────────────────────────────
    #  Utilitaires
    # ──────────────────────────────────────────────────────────────────────

    def _now(self) -> datetime:
        return datetime.now()

    def _generate_numero(self, session) -> str:
        """Génère un numéro séquentiel BL-YYYY-NNNN"""
        year = self._now().year
        result = session.execute(
            text("SELECT COUNT(*) FROM stock_livraisons WHERE strftime('%Y', date_creation) = :y"),
            {"y": str(year)}
        ).scalar()
        seq = (result or 0) + 1
        return f"BL-{year}-{seq:04d}"

    # ──────────────────────────────────────────────────────────────────────
    #  Entrepôts & produits
    # ──────────────────────────────────────────────────────────────────────

    def get_entrepots(self) -> List[Dict]:
        """Retourne les entrepôts actifs de l'entreprise"""
        try:
            with self.db_manager.get_session() as session:
                rows = session.execute(text("""
                    SELECT id, name, code FROM stock_warehouses
                    WHERE entreprise_id = :eid AND is_active = 1
                    ORDER BY name
                """), {"eid": self.entreprise_id}).fetchall()
                return [{"id": r[0], "name": r[1], "code": r[2]} for r in rows]
        except Exception as e:
            print(f"[LivraisonController] get_entrepots: {e}")
            return []

    def get_produits_entrepot(self, warehouse_id: int) -> List[Dict]:
        """
        Retourne les produits disponibles dans un entrepôt
        (quantité disponible = quantity - reserved_quantity > 0)
        """
        try:
            with self.db_manager.get_session() as session:
                rows = session.execute(text("""
                    SELECT
                        spe.product_id,
                        COALESCE(p.name, 'Produit ' || spe.product_id) AS product_name,
                        COALESCE(p.code, '')                           AS product_code,
                        COALESCE(pc.name, 'Sans catégorie')            AS category_name,
                        spe.quantity,
                        COALESCE(spe.reserved_quantity, 0)             AS reserved,
                        COALESCE(spe.unit_cost, 0)                     AS unit_cost
                    FROM stock_produits_entrepot spe
                    LEFT JOIN core_products p  ON p.id  = spe.product_id
                    LEFT JOIN core_product_categories pc ON pc.id = p.category_id
                    WHERE spe.warehouse_id = :wid
                      AND (spe.quantity - COALESCE(spe.reserved_quantity, 0)) > 0
                    ORDER BY product_name
                """), {"wid": warehouse_id}).fetchall()

                return [{
                    "product_id":    r[0],
                    "product_name":  r[1],
                    "product_code":  r[2],
                    "category_name": r[3],
                    "quantity":      float(r[4] or 0),
                    "reserved":      float(r[5] or 0),
                    "available":     float(r[4] or 0) - float(r[5] or 0),
                    "unit_cost":     float(r[6] or 0),
                } for r in rows]
        except Exception as e:
            print(f"[LivraisonController] get_produits_entrepot: {e}")
            return []

    def get_categories(self) -> List[Dict]:
        """Retourne toutes les catégories de produits actives"""
        try:
            with self.db_manager.get_session() as session:
                rows = session.execute(text("""
                    SELECT id, name FROM core_product_categories
                    WHERE is_active = 1 ORDER BY name
                """)).fetchall()
                return [{"id": r[0], "name": r[1]} for r in rows]
        except Exception as e:
            print(f"[LivraisonController] get_categories: {e}")
            return []

    # ──────────────────────────────────────────────────────────────────────
    #  CRUD Livraisons
    # ──────────────────────────────────────────────────────────────────────

    def create_livraison(self,
                         entrepot_depart_id: int,
                         entrepot_arrivee_id: int,
                         lignes: List[Dict],
                         utilisateur_id: Optional[int] = None,
                         utilisateur_nom: Optional[str] = None,
                         notes: str = "") -> StockLivraison:
        """
        Crée un bon de livraison en statut 'brouillon'.
        lignes = [{"product_id": int, "product_name": str, "product_code": str,
                   "quantite": Decimal, "cout_unitaire": Decimal}, ...]
        """
        if entrepot_depart_id == entrepot_arrivee_id:
            raise ValueError("L'entrepôt de départ et d'arrivée doivent être différents.")
        if not lignes:
            raise ValueError("Le bon de livraison doit contenir au moins une ligne.")

        with self.db_manager.get_session() as session:
            # Vérification des stocks disponibles
            for ligne in lignes:
                dispo = self._get_available(session, ligne["product_id"], entrepot_depart_id)
                qte = Decimal(str(ligne["quantite"]))
                if qte <= 0:
                    raise ValueError(f"La quantité doit être > 0 pour '{ligne['product_name']}'.")
                if qte > dispo:
                    raise ValueError(
                        f"Stock insuffisant pour '{ligne['product_name']}' : "
                        f"demandé {float(qte):.2f}, disponible {float(dispo):.2f}"
                    )

            numero = self._generate_numero(session)

            livraison = StockLivraison(
                numero=numero,
                entreprise_id=self.entreprise_id,
                entrepot_depart_id=entrepot_depart_id,
                entrepot_arrivee_id=entrepot_arrivee_id,
                statut='brouillon',
                utilisateur_id=utilisateur_id,
                utilisateur_nom=utilisateur_nom or "Inconnu",
                date_creation=self._now(),
                notes=notes,
                valeur_totale=Decimal('0'),
            )
            session.add(livraison)
            session.flush()  # obtenir l'id

            valeur_totale = Decimal('0')
            for ligne in lignes:
                qte = Decimal(str(ligne["quantite"]))
                cout = Decimal(str(ligne.get("cout_unitaire", 0)))
                total_l = qte * cout
                valeur_totale += total_l

                item = StockLivraisonItem(
                    livraison_id=livraison.id,
                    product_id=ligne["product_id"],
                    product_name=ligne.get("product_name", ""),
                    product_code=ligne.get("product_code", ""),
                    quantite=qte,
                    cout_unitaire=cout,
                    total_ligne=total_l,
                )
                session.add(item)

            livraison.valeur_totale = valeur_totale
            session.commit()
            session.refresh(livraison)
            return livraison

    def _get_available(self, session, product_id: int, warehouse_id: int) -> Decimal:
        """Quantité disponible (sans réservations) d'un produit dans un entrepôt"""
        row = session.execute(text("""
            SELECT COALESCE(quantity, 0) - COALESCE(reserved_quantity, 0)
            FROM stock_produits_entrepot
            WHERE product_id = :pid AND warehouse_id = :wid
        """), {"pid": product_id, "wid": warehouse_id}).fetchone()
        return Decimal(str(row[0])) if row else Decimal('0')

    def get_livraisons(self,
                       statut: Optional[str] = None,
                       limit: int = 200) -> List[Dict]:
        """Liste des bons de livraison avec filtre optionnel de statut"""
        try:
            with self.db_manager.get_session() as session:
                where = "WHERE l.entreprise_id = :eid"
                params: Dict = {"eid": self.entreprise_id}
                if statut:
                    where += " AND l.statut = :statut"
                    params["statut"] = statut

                rows = session.execute(text(f"""
                    SELECT
                        l.id, l.numero, l.statut,
                        wd.name AS depart, wa.name AS arrivee,
                        l.valeur_totale, l.utilisateur_nom,
                        l.date_creation, l.date_livraison, l.date_reception,
                        l.notes,
                        (SELECT COUNT(*) FROM stock_livraison_items WHERE livraison_id = l.id) AS nb_lignes
                    FROM stock_livraisons l
                    JOIN stock_warehouses wd ON wd.id = l.entrepot_depart_id
                    JOIN stock_warehouses wa ON wa.id = l.entrepot_arrivee_id
                    {where}
                    ORDER BY l.date_creation DESC
                    LIMIT :lim
                """), {**params, "lim": limit}).fetchall()

                return [{
                    "id":             r[0],
                    "numero":         r[1],
                    "statut":         r[2],
                    "statut_label":   self.STATUTS.get(r[2], r[2]),
                    "depart":         r[3],
                    "arrivee":        r[4],
                    "valeur_totale":  float(r[5] or 0),
                    "utilisateur":    r[6],
                    "date_creation":  r[7],
                    "date_livraison": r[8],
                    "date_reception": r[9],
                    "notes":          r[10],
                    "nb_lignes":      r[11],
                } for r in rows]
        except Exception as e:
            print(f"[LivraisonController] get_livraisons: {e}")
            return []

    def get_livraison_detail(self, livraison_id: int) -> Optional[Dict]:
        """Retourne le détail d'un bon de livraison avec ses lignes"""
        try:
            with self.db_manager.get_session() as session:
                row = session.execute(text("""
                    SELECT l.id, l.numero, l.statut,
                           wd.id, wd.name, wa.id, wa.name,
                           l.valeur_totale, l.utilisateur_nom,
                           l.date_creation, l.date_livraison, l.date_reception, l.notes
                    FROM stock_livraisons l
                    JOIN stock_warehouses wd ON wd.id = l.entrepot_depart_id
                    JOIN stock_warehouses wa ON wa.id = l.entrepot_arrivee_id
                    WHERE l.id = :lid
                """), {"lid": livraison_id}).fetchone()

                if not row:
                    return None

                lignes = session.execute(text("""
                    SELECT product_id, product_name, product_code,
                           quantite, cout_unitaire, total_ligne
                    FROM stock_livraison_items
                    WHERE livraison_id = :lid
                    ORDER BY id
                """), {"lid": livraison_id}).fetchall()

                return {
                    "id":                livraison_id,
                    "numero":            row[1],
                    "statut":            row[2],
                    "statut_label":      self.STATUTS.get(row[2], row[2]),
                    "entrepot_depart_id": row[3],
                    "depart":            row[4],
                    "entrepot_arrivee_id": row[5],
                    "arrivee":           row[6],
                    "valeur_totale":     float(row[7] or 0),
                    "utilisateur":       row[8],
                    "date_creation":     row[9],
                    "date_livraison":    row[10],
                    "date_reception":    row[11],
                    "notes":             row[12],
                    "lignes": [{
                        "product_id":   l[0],
                        "product_name": l[1],
                        "product_code": l[2],
                        "quantite":     float(l[3] or 0),
                        "cout_unitaire": float(l[4] or 0),
                        "total_ligne":  float(l[5] or 0),
                    } for l in lignes],
                }
        except Exception as e:
            print(f"[LivraisonController] get_livraison_detail: {e}")
            return None

    # ──────────────────────────────────────────────────────────────────────
    #  Actions métier
    # ──────────────────────────────────────────────────────────────────────

    def livrer(self, livraison_id: int,
               utilisateur_id: Optional[int] = None,
               utilisateur_nom: Optional[str] = None) -> None:
        """
        Passe le bon en statut 'livré' :
        - Soustrait les quantités de l'entrepôt de départ
        - Enregistre les mouvements SORTIE correspondants
        """
        with self.db_manager.get_session() as session:
            liv = session.query(StockLivraison).filter_by(id=livraison_id).first()
            if not liv:
                raise ValueError("Bon de livraison introuvable.")
            if liv.statut != 'brouillon':
                raise ValueError(f"Seul un bon en 'brouillon' peut être livré (statut actuel : {liv.statut}).")

            for item in liv.lignes:
                # Vérification stock au moment de la livraison
                dispo = self._get_available(session, item.product_id, liv.entrepot_depart_id)
                if item.quantite > dispo:
                    raise ValueError(
                        f"Stock insuffisant pour '{item.product_name}' au moment de la livraison "
                        f"(demandé {float(item.quantite):.2f}, disponible {float(dispo):.2f})"
                    )
                # Déduction dans l'entrepôt de départ
                self._adjust_stock(session, item.product_id, liv.entrepot_depart_id,
                                   -item.quantite, item.cout_unitaire)
                # Mouvement SORTIE
                session.add(StockMovement(
                    product_id=item.product_id,
                    warehouse_id=liv.entrepot_depart_id,
                    destination_warehouse_id=liv.entrepot_arrivee_id,
                    movement_type='SORTIE',
                    quantity=-item.quantite,
                    unit_cost=item.cout_unitaire,
                    total_cost=item.total_ligne,
                    reference=liv.numero,
                    description=f"Livraison {liv.numero} vers {liv.entrepot_arrivee.name if liv.entrepot_arrivee else ''}",
                    user_id=utilisateur_id,
                    user_name=utilisateur_nom or "Inconnu",
                    movement_date=self._now(),
                ))

            liv.statut = 'livre'
            liv.date_livraison = self._now()
            session.commit()

    def receptionner(self, livraison_id: int,
                     utilisateur_id: Optional[int] = None,
                     utilisateur_nom: Optional[str] = None) -> None:
        """
        Passe le bon en statut 'réceptionné' :
        - Ajoute les quantités dans l'entrepôt d'arrivée
        - Enregistre les mouvements ENTREE correspondants
        """
        with self.db_manager.get_session() as session:
            liv = session.query(StockLivraison).filter_by(id=livraison_id).first()
            if not liv:
                raise ValueError("Bon de livraison introuvable.")
            if liv.statut != 'livre':
                raise ValueError("Seul un bon 'livré' peut être réceptionné.")

            for item in liv.lignes:
                # Ajout dans l'entrepôt d'arrivée
                self._adjust_stock(session, item.product_id, liv.entrepot_arrivee_id,
                                   +item.quantite, item.cout_unitaire)
                # Mouvement ENTREE
                session.add(StockMovement(
                    product_id=item.product_id,
                    warehouse_id=liv.entrepot_arrivee_id,
                    destination_warehouse_id=None,
                    movement_type='ENTREE',
                    quantity=item.quantite,
                    unit_cost=item.cout_unitaire,
                    total_cost=item.total_ligne,
                    reference=liv.numero,
                    description=f"Réception livraison {liv.numero} depuis {liv.entrepot_depart.name if liv.entrepot_depart else ''}",
                    user_id=utilisateur_id,
                    user_name=utilisateur_nom or "Inconnu",
                    movement_date=self._now(),
                ))

            liv.statut = 'receptionne'
            liv.date_reception = self._now()
            session.commit()

    def annuler(self, livraison_id: int) -> None:
        """Annule un bon en statut 'brouillon' uniquement"""
        with self.db_manager.get_session() as session:
            liv = session.query(StockLivraison).filter_by(id=livraison_id).first()
            if not liv:
                raise ValueError("Bon de livraison introuvable.")
            if liv.statut not in ('brouillon',):
                raise ValueError("Seul un bon en 'brouillon' peut être annulé.")
            liv.statut = 'annule'
            session.commit()

    def supprimer(self, livraison_id: int) -> None:
        """Supprime un bon en statut 'brouillon' ou 'annulé'"""
        with self.db_manager.get_session() as session:
            liv = session.query(StockLivraison).filter_by(id=livraison_id).first()
            if not liv:
                raise ValueError("Bon de livraison introuvable.")
            if liv.statut not in ('brouillon', 'annule'):
                raise ValueError("Seul un bon en brouillon ou annulé peut être supprimé.")
            session.delete(liv)
            session.commit()

    # ──────────────────────────────────────────────────────────────────────
    #  Utilitaire stock bas niveau
    # ──────────────────────────────────────────────────────────────────────

    def _adjust_stock(self, session, product_id: int, warehouse_id: int,
                      delta: Decimal, unit_cost: Decimal) -> None:
        """
        Ajuste la quantité dans stock_produits_entrepot.
        Crée l'entrée si elle n'existe pas (cas de l'entrepôt d'arrivée).
        """
        row = session.query(StockProduitEntrepot).filter_by(
            product_id=product_id, warehouse_id=warehouse_id
        ).first()

        if row:
            row.quantity = (row.quantity or Decimal('0')) + delta
            row.last_movement_date = self._now()
            # Recalcul coût moyen pondéré uniquement sur entrée
            if delta > 0:
                old_qty = (row.quantity or Decimal('0')) - delta
                old_cost = row.unit_cost or Decimal('0')
                if old_qty + delta > 0:
                    row.unit_cost = (old_qty * old_cost + delta * unit_cost) / (old_qty + delta)
            row.total_cost = row.quantity * (row.unit_cost or Decimal('0'))
        else:
            # Créer la ligne si elle n'existe pas (entrepôt destination)
            new_qty = max(delta, Decimal('0'))
            session.add(StockProduitEntrepot(
                product_id=product_id,
                warehouse_id=warehouse_id,
                quantity=new_qty,
                unit_cost=unit_cost,
                total_cost=new_qty * unit_cost,
                last_movement_date=self._now(),
            ))

    # ──────────────────────────────────────────────────────────────────────
    #  Statistiques
    # ──────────────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict:
        """Statistiques rapides pour le header de la liste"""
        try:
            with self.db_manager.get_session() as session:
                row = session.execute(text("""
                    SELECT
                        COUNT(*)                                                  AS total,
                        SUM(CASE WHEN statut='brouillon'   THEN 1 ELSE 0 END)    AS brouillons,
                        SUM(CASE WHEN statut='livre'       THEN 1 ELSE 0 END)    AS livres,
                        SUM(CASE WHEN statut='receptionne' THEN 1 ELSE 0 END)    AS receptionnes,
                        SUM(CASE WHEN statut='annule'      THEN 1 ELSE 0 END)    AS annules
                    FROM stock_livraisons
                    WHERE entreprise_id = :eid
                """), {"eid": self.entreprise_id}).fetchone()
                return {
                    "total":        row[0] or 0,
                    "brouillons":   row[1] or 0,
                    "livres":       row[2] or 0,
                    "receptionnes": row[3] or 0,
                    "annules":      row[4] or 0,
                }
        except Exception as e:
            print(f"[LivraisonController] get_stats: {e}")
            return {"total": 0, "brouillons": 0, "livres": 0, "receptionnes": 0, "annules": 0}
