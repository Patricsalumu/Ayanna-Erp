# -*- coding: utf-8 -*-
"""
Contrôleur pour la gestion des commandes du module Boutique
Gère la logique métier des commandes : récupération, statistiques, filtrage, export
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Union
from sqlalchemy import text
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.core.controllers.entreprise_controller import EntrepriseController


db = DatabaseManager()


class CommandeController:
    """Contrôleur pour la gestion des commandes"""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.entreprise_controller = EntrepriseController()
    
    def get_currency_symbol(self):
        """Récupère le symbole de devise depuis l'entreprise"""
        try:
            return self.entreprise_controller.get_currency_symbol()
        except Exception:
            return "FC"  # Fallback

    def get_commandes(self, date_debut=None, date_fin=None, search_term=None,
                     payment_filter=None, limit=100) -> List[Dict[str, Any]]:
        """
        Récupérer les commandes avec leurs détails

        Args:
            date_debut: Date de début pour le filtrage
            date_fin: Date de fin pour le filtrage
            search_term: Terme de recherche
            payment_filter: Filtre par méthode de paiement
            limit: Nombre maximum de commandes à récupérer

        Returns:
            Liste des commandes avec leurs détails
        """
        try:
            with self.db_manager.session_scope() as session:
                # Construction de la requête de base
                base_query = """
                    SELECT
                        sp.id,
                        sp.numero_commande,
                        sp.created_at,
                        COALESCE(sc.nom || ' ' || COALESCE(sc.prenom, ''), 'Client anonyme') as client_name,
                        sp.subtotal,
                        sp.remise_amount,
                        sp.total_final,
                        sp.payment_method,
                        sp.status,
                        (
                            SELECT GROUP_CONCAT(cp.name || ' (x' || spp.quantity || ')')
                            FROM shop_paniers_products spp
                            JOIN core_products cp ON spp.product_id = cp.id
                            WHERE spp.panier_id = sp.id
                        ) as produits,
                        (
                            SELECT GROUP_CONCAT(ss.name || ' (x' || sps.quantity || ')')
                            FROM shop_paniers_services sps
                            JOIN event_services ss ON sps.service_id = ss.id
                            WHERE sps.panier_id = sp.id
                        ) as services,
                        (
                            COALESCE(
                                (SELECT SUM(spp.quantity) FROM shop_paniers_products spp WHERE spp.panier_id = sp.id), 0
                            ) + COALESCE(
                                (SELECT SUM(sps.quantity) FROM shop_paniers_services sps WHERE sps.panier_id = sp.id), 0
                            )
                        ) as total_quantity,
                        (
                            COALESCE(
                                (SELECT SUM(spay.amount) FROM shop_payments spay WHERE spay.panier_id = sp.id), 0
                            )
                        ) as montant_paye
                    FROM shop_paniers sp
                    LEFT JOIN shop_clients sc ON sp.client_id = sc.id
                """

                conditions = []
                params = {}

                # Filtrage par dates
                if date_debut:
                    # normalize date_debut to start of day for datetime comparisons
                    date_debut_dt = datetime.combine(date_debut, datetime.min.time()) if not isinstance(date_debut, datetime) else date_debut
                    conditions.append("sp.created_at >= :date_debut")
                    params['date_debut'] = date_debut_dt
                if date_fin:
                    # Ajouter 23:59:59 à la date de fin pour inclure toute la journée
                    date_fin_end = datetime.combine(date_fin, datetime.max.time())
                    conditions.append("sp.created_at <= :date_fin")
                    params['date_fin'] = date_fin_end

                # Filtrage par méthode de paiement
                if payment_filter and payment_filter != "Tous":
                    conditions.append("sp.payment_method = :payment_method")
                    params['payment_method'] = payment_filter

                # Recherche textuelle
                if search_term:
                    search_conditions = [
                        "sp.numero_commande LIKE :search",
                        "sc.nom LIKE :search",
                        "sc.prenom LIKE :search",
                        "sp.payment_method LIKE :search",
                        # Recherche dans les produits
                        "EXISTS (SELECT 1 FROM shop_paniers_products spp JOIN core_products cp ON spp.product_id = cp.id WHERE spp.panier_id = sp.id AND cp.name LIKE :search)",
                        # Recherche dans les services
                        "EXISTS (SELECT 1 FROM shop_paniers_services sps JOIN shop_services ss ON sps.service_id = ss.id WHERE sps.panier_id = sp.id AND ss.name LIKE :search)"
                        
                    ]
                    conditions.append("(" + " OR ".join(search_conditions) + ")")
                    params['search'] = f"%{search_term}%"

                # Ajouter les conditions à la requête
                if conditions:
                    base_query += " WHERE " + " AND ".join(conditions)

                # Tri et limite
                base_query += " ORDER BY sp.created_at DESC LIMIT :limit"
                params['limit'] = limit

                query = text(base_query)
                try:
                    result = session.execute(query, params)
                    commandes = result.fetchall()
                except Exception as e:
                    # Si la table shop_paniers n'existe pas ou autre erreur, log et continuer
                    print(f"⚠️ shop_paniers query failed, continuing with restaurant only: {e}")
                    commandes = []

                # Post-process each row to combine products+services into a single items field
                processed = []
                for c in commandes:
                    prod = c.produits or ''
                    serv = c.services or ''
                    if prod and serv:
                        items = prod + ', ' + serv
                    else:
                        items = prod or serv or 'Aucun produit/service'

                    # Créer un objet commande avec tous les attributs nécessaires
                    commande = {
                        'id': c.id,
                        'numero_commande': c.numero_commande,
                        'created_at': c.created_at,
                        'client_name': c.client_name,
                        'subtotal': c.subtotal,
                        'remise_amount': c.remise_amount,
                        'total_final': c.total_final,
                        'payment_method': c.payment_method,
                        'status': c.status,
                        'produits': items,
                        'services': c.services,  # Garder séparé pour populate_table
                        'total_quantity': c.total_quantity,
                        'montant_paye': c.montant_paye
                    }
                    processed.append(commande)

                # --- Récupérer également les paniers du module Restaurant (avec mêmes filtres) ---
                try:
                    # Vérifier si certaines tables optionnelles existent (core_users, shop_clients)
                    has_core_users = False
                    has_shop_clients = False
                    try:
                        tbl = session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name=:t"), {'t': 'core_users'}).fetchone()
                        has_core_users = tbl is not None
                    except Exception:
                        has_core_users = False

                    try:
                        tbl2 = session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name=:t"), {'t': 'shop_clients'}).fetchone()
                        has_shop_clients = tbl2 is not None
                    except Exception:
                        has_shop_clients = False

                    # Construire dynamiquement la sélection et les jointures en fonction des tables disponibles
                    client_name_expr = "COALESCE(sc.nom || ' ' || COALESCE(sc.prenom, ''), 'Client restaurant')" if has_shop_clients else "'Client restaurant'"
                    serveuse_select = "su.name as serveuse_name, scu.name as comptoiriste_name" if has_core_users else "NULL as serveuse_name, NULL as comptoiriste_name"
                    serveuse_joins = "LEFT JOIN core_users su ON rp.serveuse_id = su.id\n                        LEFT JOIN core_users scu ON rp.user_id = scu.id" if has_core_users else ""
                    client_join = "LEFT JOIN shop_clients sc ON rp.client_id = sc.id" if has_shop_clients else ""

                    restau_base = f"""
                        SELECT
                            rp.id,
                            rp.id as numero_commande,
                            rp.created_at,
                            {client_name_expr} as client_name,
                            rp.subtotal,
                            rp.remise_amount,
                            rp.total_final,
                            rp.payment_method,
                            rp.status,
                            (
                                SELECT GROUP_CONCAT(cp.name || ' (x' || rpp.quantity || ')')
                                FROM restau_produit_panier rpp
                                LEFT JOIN core_products cp ON rpp.product_id = cp.id
                                WHERE rpp.panier_id = rp.id
                            ) as produits,
                            NULL as services,
                            (
                                COALESCE((SELECT SUM(rpp.quantity) FROM restau_produit_panier rpp WHERE rpp.panier_id = rp.id), 0)
                            ) as total_quantity,
                            (
                                COALESCE((SELECT SUM(rpays.amount) FROM restau_payments rpays WHERE rpays.panier_id = rp.id), 0)
                            ) as montant_paye,
                            rt.number as table_number,
                            rs.name as salle_name,
                            {serveuse_select}
                        FROM restau_paniers rp
                        LEFT JOIN restau_tables rt ON rp.table_id = rt.id
                        LEFT JOIN restau_salles rs ON rt.salle_id = rs.id
                        {serveuse_joins}
                        {client_join}
                    """

                    restau_conditions = []
                    # réutiliser params construits plus haut
                    if 'date_debut' in params:
                        restau_conditions.append("rp.created_at >= :date_debut")
                    if 'date_fin' in params:
                        restau_conditions.append("rp.created_at <= :date_fin")
                    if payment_filter and payment_filter != "Tous":
                        restau_conditions.append("rp.payment_method = :payment_method")
                    if search_term:
                        # rechercher par id panier, nom client ou produit dans les lignes restau
                        restau_conditions.append(
                            "(CAST(rp.id AS TEXT) LIKE :search OR sc.nom LIKE :search OR sc.prenom LIKE :search OR EXISTS (SELECT 1 FROM restau_produit_panier rpp LEFT JOIN core_products cp ON rpp.product_id = cp.id WHERE rpp.panier_id = rp.id AND (cp.name LIKE :search OR CAST(rpp.product_id AS TEXT) LIKE :search)))"
                        )

                    if restau_conditions:
                        restau_base += " WHERE " + " AND ".join(restau_conditions)

                    restau_base += " ORDER BY rp.created_at DESC LIMIT :limit"
                    params['limit'] = limit

                    # Vérifier si la table core_products existe (pour afficher les noms produits)
                    has_core_products = False
                    try:
                        tbl3 = session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name=:t"), {'t': 'core_products'}).fetchone()
                        has_core_products = tbl3 is not None
                    except Exception:
                        has_core_products = False

                    # Construire l'expression pour les produits (nom si core_products dispo, sinon id)
                    if has_core_products:
                        prod_concat_join = "LEFT JOIN core_products cp ON rpp.product_id = cp.id"
                        prod_concat_expr = "cp.name"
                    else:
                        prod_concat_join = ""
                        prod_concat_expr = "('Produit #' || rpp.product_id)"

                    # Injecter l'expression produit dans la requête
                    restau_base = restau_base.replace("FROM restau_produit_panier rpp\n                                LEFT JOIN core_products cp ON rpp.product_id = cp.id\n                                WHERE rpp.panier_id = rp.id",
                                                        f"FROM restau_produit_panier rpp\n                                {prod_concat_join}\n                                WHERE rpp.panier_id = rp.id")

                    restau_base = restau_base.replace("SELECT GROUP_CONCAT(cp.name || ' (x' || rpp.quantity || ')')",
                                                        f"SELECT GROUP_CONCAT({prod_concat_expr} || ' (x' || rpp.quantity || ')')")

                    restau_query = text(restau_base)
                    restau_rows = session.execute(restau_query, params).fetchall()
                    for r in restau_rows:
                        # Si created_at absent ou null dans la table, forcer l'horloge machine maintenant
                        try:
                            if not getattr(r, 'created_at', None):
                                now = datetime.now()
                                session.execute(text("UPDATE restau_paniers SET created_at = :now, updated_at = :now WHERE id = :id"), {'now': now, 'id': r.id})
                                # recharger la valeur locale pour affichage
                                r = session.execute(text("SELECT * FROM restau_paniers WHERE id = :id"), {'id': r.id}).fetchone()
                        except Exception:
                            # si la mise à jour échoue (schéma différent), continuer sans interrompre
                            pass
                        prod = r.produits or ''
                        serv = r.services or ''
                        if prod and serv:
                            items = prod + ', ' + serv
                        else:
                            items = prod or serv or 'Aucun produit/service'

                        commande = {
                            'id': r.id,
                            # For restaurant we use the panier id as "numero_commande"
                            'numero_commande': str(r.numero_commande),
                            'created_at': r.created_at,
                            'client_name': r.client_name,
                            'subtotal': r.subtotal,
                            'remise_amount': r.remise_amount,
                            'total_final': r.total_final,
                            'payment_method': r.payment_method,
                            'status': r.status,
                            'produits': items,
                            'services': r.services,
                            'total_quantity': r.total_quantity,
                            'montant_paye': r.montant_paye,
                            'module': 'restaurant',
                            'table_number': getattr(r, 'table_number', None),
                            'salle_name': getattr(r, 'salle_name', None),
                            'serveuse_name': getattr(r, 'serveuse_name', None),
                            'comptoiriste_name': getattr(r, 'comptoiriste_name', None)
                        }
                        processed.append(commande)
                except Exception as e:
                    # Si la table restau_* n'existe pas ou autre problème, on log l'erreur
                    print(f"⚠️ restau_paniers query failed or other err: {e}")

                return processed

        except Exception as e:
            print(f"❌ Erreur get_commandes: {e}")
            raise

    def get_commandes_statistics(self, commandes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculer les statistiques des commandes

        Args:
            commandes: Liste des commandes

        Returns:
            Dictionnaire des statistiques
        """
        # Si la liste est vide, renvoyer des zéros
        if not commandes:
            return {
                'total_ca': 0,
                'total_creances': 0,
                'commandes_aujourd_hui': 0,
                'nb_commandes': 0,
                'panier_moyen': 0,
                'commandes_payees': 0,
                'commandes_non_payees': 0,
                'commandes_partielles': 0
            }

        # total du CA (somme des total_final)
        total_ca = sum(float(c.get('total_final', 0) or 0) for c in commandes)

        # Calculer les créances = somme de (total_final - montant_paye) pour les paniers où paid < total
        total_creances = 0.0

        # Calculer les statistiques de paiement
        commandes_payees = 0
        commandes_non_payees = 0
        commandes_partielles = 0

        for c in commandes:
            montant_paye = float(c.get('montant_paye', 0) or 0)
            total_final = float(c.get('total_final', 0) or 0)

            # créance partielle sur cette commande
            if total_final > montant_paye:
                total_creances += (total_final - montant_paye)

            # classifier paiement
            if montant_paye >= total_final and total_final > 0:
                commandes_payees += 1
            elif montant_paye > 0 and montant_paye < total_final:
                commandes_partielles += 1
            else:
                # montant_paye == 0 OR total_final == 0
                # considérer comme non payée si total_final > 0
                if total_final > 0:
                    commandes_non_payees += 1

        # Calculer les commandes d'aujourd'hui
        commandes_aujourd_hui = 0
        today = datetime.now().date()

        for c in commandes:
            if c['created_at']:
                try:
                    if isinstance(c['created_at'], str):
                        # Parser la chaîne de date
                        date_obj = datetime.strptime(c['created_at'][:19], "%Y-%m-%d %H:%M:%S")
                        if date_obj.date() == today:
                            commandes_aujourd_hui += 1
                    else:
                        # Objet datetime
                        if c['created_at'].date() == today:
                            commandes_aujourd_hui += 1
                except:
                    pass  # Ignorer les dates mal formatées

        nb_commandes = len(commandes)
        panier_moyen = (total_ca / nb_commandes) if nb_commandes > 0 else 0

        return {
            'total_ca': total_ca,
            'total_creances': total_creances,
            'commandes_payees': commandes_payees,
            'commandes_non_payees': commandes_non_payees,
            'commandes_partielles': commandes_partielles,
            'commandes_aujourd_hui': commandes_aujourd_hui,
            'nb_commandes': nb_commandes,
            'panier_moyen': panier_moyen
        }

    def get_period_commandes_stats(self, date_debut, date_fin) -> Dict[str, Any]:
        """
        Calculer les statistiques des commandes pour une période donnée (depuis la base).

        Règles :
        - n'inclut pas les commandes dont status = 'cancelled'
        - chiffre d'affaires = somme des total_final des commandes de la période
        - total_paid = somme des paiements (shop_payments.amount) liés aux commandes de la période
        - total_unpaid = chiffre d'affaires - total_paid
        - total_creances = somme des montants restants pour les commandes où montant_paye < total_final
        """
        try:
            # Normaliser les bornes (inclusives)
            from datetime import datetime, time
            if isinstance(date_debut, datetime):
                d1 = date_debut
            else:
                d1 = datetime.combine(date_debut, time.min)
            if isinstance(date_fin, datetime):
                d2 = date_fin
            else:
                d2 = datetime.combine(date_fin, time.max)

            with self.db_manager.get_session() as session:
                # Calculer CA total (shop + restau) en excluant les statuts annulés
                q_ca = text("""
                    SELECT
                      COALESCE((SELECT SUM(total_final) FROM shop_paniers WHERE created_at >= :d1 AND created_at <= :d2 AND LOWER(COALESCE(status,'')) <> 'cancelled'),0)
                      + COALESCE((SELECT SUM(total_final) FROM restau_paniers WHERE created_at >= :d1 AND created_at <= :d2 AND LOWER(COALESCE(status,'')) NOT IN ('annule','annulé', 'cancelled')),0)
                      as total_ca
                """)
                ca_row = session.execute(q_ca, {'d1': d1, 'd2': d2}).fetchone()
                total_ca = float(ca_row.total_ca or 0)

                # Total payé : sommes des paiements shop + restau pour paniers valides
                q_paid = text("""
                    SELECT
                      COALESCE((SELECT SUM(sp.amount) FROM shop_payments sp JOIN shop_paniers p ON sp.panier_id = p.id WHERE p.created_at >= :d1 AND p.created_at <= :d2 AND LOWER(COALESCE(p.status,'')) <> 'cancelled'),0)
                      + COALESCE((SELECT SUM(rp.amount) FROM restau_payments rp JOIN restau_paniers r ON rp.panier_id = r.id WHERE r.created_at >= :d1 AND r.created_at <= :d2 AND LOWER(COALESCE(r.status,'')) NOT IN ('annule','annulé', 'cancelled')),0)
                      as total_paid
                """)
                paid_row = session.execute(q_paid, {'d1': d1, 'd2': d2}).fetchone()
                total_paid = float(paid_row.total_paid or 0)

                # Total créances : somme des (total_final - montant_paye) pour les paniers (shop + restau) où montant_paye < total_final
                q_creances = text("""
                    SELECT COALESCE(SUM(t.total_final - COALESCE(t.montant_paye,0)),0) as total_creances
                    FROM (
                        SELECT pp.id, COALESCE(pp.total_final,0) as total_final,
                               (SELECT COALESCE(SUM(sp.amount),0) FROM shop_payments sp WHERE sp.panier_id = pp.id) as montant_paye
                        FROM shop_paniers pp
                        WHERE pp.created_at >= :d1 AND pp.created_at <= :d2
                        AND LOWER(COALESCE(pp.status,'')) <> 'cancelled'
                        UNION ALL
                        SELECT rp.id, COALESCE(rp.total_final,0) as total_final,
                               (SELECT COALESCE(SUM(rpay.amount),0) FROM restau_payments rpay WHERE rpay.panier_id = rp.id) as montant_paye
                        FROM restau_paniers rp
                        WHERE rp.created_at >= :d1 AND rp.created_at <= :d2
                        AND LOWER(COALESCE(rp.status,'')) NOT IN ('annule','annulé', 'cancelled')
                    ) t
                    WHERE COALESCE(t.montant_paye,0) < COALESCE(t.total_final,0)
                """)
                cre_row = session.execute(q_creances, {'d1': d1, 'd2': d2}).fetchone()
                total_creances = float(cre_row.total_creances or 0)

                # Nombre de créances (nombre de commandes où montant_paye < total_final)
                q_nb_creances = text("""
                    SELECT COALESCE(SUM(case when COALESCE(t.montant_paye,0) < COALESCE(t.total_final,0) then 1 else 0 end),0) as nb_creances
                    FROM (
                        SELECT pp.id, COALESCE(pp.total_final,0) as total_final,
                               (SELECT COALESCE(SUM(sp.amount),0) FROM shop_payments sp WHERE sp.panier_id = pp.id) as montant_paye
                        FROM shop_paniers pp
                        WHERE pp.created_at >= :d1 AND pp.created_at <= :d2
                        AND LOWER(COALESCE(pp.status,'')) <> 'cancelled'
                        UNION ALL
                        SELECT rp.id, COALESCE(rp.total_final,0) as total_final,
                               (SELECT COALESCE(SUM(rpay.amount),0) FROM restau_payments rpay WHERE rpay.panier_id = rp.id) as montant_paye
                        FROM restau_paniers rp
                        WHERE rp.created_at >= :d1 AND rp.created_at <= :d2
                        AND LOWER(COALESCE(rp.status,'')) NOT IN ('annule','annulé', 'cancelled')
                    ) t
                """)
                nb_cre_row = session.execute(q_nb_creances, {'d1': d1, 'd2': d2}).fetchone()
                nb_creances = int(nb_cre_row.nb_creances) if nb_cre_row and nb_cre_row.nb_creances is not None else 0

                total_unpaid = total_ca - total_paid

                # Nombre total de commandes (shop + restau)
                q_nb_cmd = text("""
                    SELECT
                      COALESCE((SELECT COUNT(1) FROM shop_paniers WHERE created_at >= :d1 AND created_at <= :d2 AND LOWER(COALESCE(status,'')) <> 'cancelled'),0)
                      + COALESCE((SELECT COUNT(1) FROM restau_paniers WHERE created_at >= :d1 AND created_at <= :d2 AND LOWER(COALESCE(status,'')) NOT IN ('annule','annulé', 'cancelled')),0)
                      as nb_commandes
                """)
                nb_row = session.execute(q_nb_cmd, {'d1': d1, 'd2': d2}).fetchone()
                nb_commandes = int(nb_row.nb_commandes) if nb_row and nb_row.nb_commandes is not None else 0

                panier_moyen = (total_ca / nb_commandes) if nb_commandes > 0 else 0

                return {
                    'total_ca': total_ca,
                    'total_paid': total_paid,
                    'total_unpaid': total_unpaid,
                    'total_creances': total_creances,
                    'nb_creances': nb_creances,
                    'nb_commandes': nb_commandes,
                    'panier_moyen': panier_moyen,
                }
        except Exception as e:
            print(f"❌ Erreur get_period_commandes_stats: {e}")
            return {
                'total_ca': 0,
                'total_paid': 0,
                'total_unpaid': 0,
                'total_creances': 0,
                'nb_commandes': 0,
                'panier_moyen': 0,
            }

    def format_period_stats(self, stats: Dict[str, Any], date_debut, date_fin) -> str:
        """
        Formater les statistiques de période

        Args:
            stats: Statistiques calculées
            date_debut: Date de début
            date_fin: Date de fin

        Returns:
            Texte formaté des statistiques
        """
        if not stats or stats['nb_commandes'] == 0:
            return f"""
Période: Derniers 30 jours
Commandes: 0
Chiffre d'affaires: 0 {self.get_currency_symbol()}
Créances: 0 {self.get_currency_symbol()}
Panier moyen: 0 {self.get_currency_symbol()}
            """

        return f"""
Période: {date_debut.toString('dd/MM/yyyy')} - {date_fin.toString('dd/MM/yyyy')}
Commandes: {stats['nb_commandes']}
Chiffre d'affaires: {stats['total_ca']:.0f} {self.get_currency_symbol()}
Créances: {stats['total_creances']:.0f} {self.get_currency_symbol()}
Panier moyen: {stats['panier_moyen']:.0f} {self.get_currency_symbol()}
        """

    def export_commandes(self, commandes: List[Dict[str, Any]], format_type: str = 'csv') -> str:
        """
        Exporter les commandes

        Args:
            commandes: Liste des commandes à exporter
            format_type: Format d'export ('csv', 'excel')

        Returns:
            Chemin du fichier exporté ou contenu CSV
        """
        # TODO: Implémenter l'export CSV/Excel
        # Pour l'instant, retourner un message
        return f"Export {format_type} non implémenté. {len(commandes)} commandes à exporter."

    def export_products_summary(self, date_debut, date_fin, include_services: bool = True) -> str:
        """
        Génère un fichier CSV listant chaque produit/service vendu sur la période avec colonnes:
        No, name, quantite_initiale, quantite_ajoutee, quantite_achats_transferts, total_initial_plus_ajoute,
        reste, vendu, prix_unitaire, total

        Hypothèses raisonnables:
        - Les ventes produits sont issues de `shop_paniers_products` (boutique) et `restau_produit_panier` (restaurant).
        - Les services viennent de `shop_paniers_services`.
        - Les mouvements de stock sont pris depuis `stock_mouvements` pour calculer quantités initiales et ajouts.
        - Si la table des mouvements ou des stocks est absente, les valeurs liées au stock seront à 0.

        Retourne le chemin du fichier CSV généré.
        """
        import os
        from datetime import datetime

        # Normaliser bornes
        from datetime import datetime as _dt
        if isinstance(date_debut, _dt):
            d1 = date_debut
        else:
            d1 = datetime.combine(date_debut, datetime.min.time())
        if isinstance(date_fin, _dt):
            d2 = date_fin
        else:
            d2 = datetime.combine(date_fin, datetime.max.time())

        try:
            with self.db_manager.get_session() as session:
                # Rassembler ventes produits (boutique)
                q_products = text("""
                    SELECT cp.id as product_id, cp.name as product_name,
                           COALESCE(SUM(spp.quantity),0) as sold_qty,
                           COALESCE(MAX(cp.price_unit),0) as unit_price
                    FROM shop_paniers_products spp
                    LEFT JOIN shop_paniers p ON spp.panier_id = p.id
                    LEFT JOIN core_products cp ON spp.product_id = cp.id
                    WHERE p.created_at >= :d1 AND p.created_at <= :d2
                    AND LOWER(COALESCE(p.status,'')) <> 'cancelled'
                    GROUP BY cp.id, cp.name
                """)
                prod_rows = session.execute(q_products, {'d1': d1, 'd2': d2}).fetchall()

                # Ventes restaurant
                q_restau = text("""
                    SELECT cp.id as product_id, cp.name as product_name,
                           COALESCE(SUM(rpp.quantity),0) as sold_qty,
                           COALESCE(MAX(cp.price_unit),0) as unit_price
                    FROM restau_produit_panier rpp
                    LEFT JOIN restau_paniers rp ON rpp.panier_id = rp.id
                    LEFT JOIN core_products cp ON rpp.product_id = cp.id
                    WHERE rp.created_at >= :d1 AND rp.created_at <= :d2
                    AND LOWER(COALESCE(rp.status,'')) <> 'annule'
                    GROUP BY cp.id, cp.name
                """)
                restau_rows = session.execute(q_restau, {'d1': d1, 'd2': d2}).fetchall()

                # Services (shop)
                service_map = []
                if include_services:
                    q_services = text("""
                        SELECT ss.id as service_id, ss.name as service_name,
                               COALESCE(SUM(sps.quantity),0) as sold_qty,
                               COALESCE(MAX(ss.price),0) as unit_price
                        FROM shop_paniers_services sps
                        LEFT JOIN shop_paniers p ON sps.panier_id = p.id
                        LEFT JOIN shop_services ss ON sps.service_id = ss.id
                        WHERE p.created_at >= :d1 AND p.created_at <= :d2
                        AND LOWER(COALESCE(p.status,'')) <> 'cancelled'
                        GROUP BY ss.id, ss.name
                    """)
                    service_map = session.execute(q_services, {'d1': d1, 'd2': d2}).fetchall()

                # Agréger produits (boutique + restaurant)
                items = {}
                for r in prod_rows:
                    pid = f"P-{r.product_id}"
                    items[pid] = {
                        'name': r.product_name,
                        'sold': float(r.sold_qty or 0),
                        'unit_price': float(r.unit_price or 0),
                        'product_id': r.product_id,
                        'is_service': False
                    }
                for r in restau_rows:
                    pid = f"P-{r.product_id}"
                    if pid in items:
                        items[pid]['sold'] += float(r.sold_qty or 0)
                    else:
                        items[pid] = {
                            'name': r.product_name,
                            'sold': float(r.sold_qty or 0),
                            'unit_price': float(r.unit_price or 0),
                            'product_id': r.product_id,
                            'is_service': False
                        }
                # Services
                for s in service_map:
                    sid = f"S-{s.service_id}"
                    items[sid] = {
                        'name': s.service_name,
                        'sold': float(s.sold_qty or 0),
                        'unit_price': float(s.unit_price or 0),
                        'service_id': s.service_id,
                        'is_service': True
                    }

                # Pour chaque produit/service, calculer quantités stock via stock_mouvements
                rows_out = []
                for idx, (key, it) in enumerate(items.items(), start=1):
                    if it.get('is_service'):
                        # Pas de stock pour les services
                        initial_q = 0.0
                        added_q = 0.0
                        purchases_q = 0.0
                    else:
                        pid = it.get('product_id')
                        # quantité initiale = somme des mouvements avant d1
                        q_init = text("SELECT COALESCE(SUM(quantity),0) as qty FROM stock_mouvements WHERE product_id = :pid AND movement_date < :d1")
                        try:
                            r_init = session.execute(q_init, {'pid': pid, 'd1': d1}).fetchone()
                            initial_q = float(r_init.qty or 0)
                        except Exception:
                            initial_q = 0.0

                        # quantité ajoutée pendant l'intervalle (ENTREE, TRANSFERT, AJUSTEMENT)
                        q_added = text("SELECT COALESCE(SUM(quantity),0) as qty FROM stock_mouvements WHERE product_id = :pid AND movement_date >= :d1 AND movement_date <= :d2 AND movement_type IN ('ENTREE','TRANSFERT','AJUSTEMENT')")
                        try:
                            r_added = session.execute(q_added, {'pid': pid, 'd1': d1, 'd2': d2}).fetchone()
                            added_q = float(r_added.qty or 0)
                        except Exception:
                            added_q = 0.0

                        # achats/transferts (ENTREE or TRANSFERT)
                        q_purch = text("SELECT COALESCE(SUM(quantity),0) as qty FROM stock_mouvements WHERE product_id = :pid AND movement_date >= :d1 AND movement_date <= :d2 AND movement_type IN ('ENTREE','TRANSFERT')")
                        try:
                            r_purch = session.execute(q_purch, {'pid': pid, 'd1': d1, 'd2': d2}).fetchone()
                            purchases_q = float(r_purch.qty or 0)
                        except Exception:
                            purchases_q = 0.0

                    sold = float(it.get('sold', 0.0))
                    total_initial_plus = initial_q + added_q
                    reste = total_initial_plus - sold
                    unit_price = float(it.get('unit_price', 0.0))
                    total_amount = sold * unit_price

                    rows_out.append({
                        'no': idx,
                        'name': it['name'],
                        'initial_quantity': initial_q,
                        'quantity_added': added_q,
                        'purchases_transfers': purchases_q,
                        'total_initial_plus_added': total_initial_plus,
                        'reste': reste,
                        'sold': sold,
                        'unit_price': unit_price,
                        'total': total_amount
                    })

                # Générer CSV
                export_dir = os.path.join(os.getcwd(), 'exports')
                os.makedirs(export_dir, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"produits_vendus_{timestamp}.csv"
                path = os.path.join(export_dir, filename)
                import csv
                with open(path, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['No', 'Name', 'Initial Quantity', 'Quantity Added', 'Purchases/Transfers', 'Total Initial+Added', 'Remaining', 'Sold', 'Unit Price', 'Total']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    total_row = { 'Initial Quantity':0, 'Quantity Added':0, 'Purchases/Transfers':0, 'Total Initial+Added':0, 'Remaining':0, 'Sold':0, 'Total':0 }
                    for r in rows_out:
                        writer.writerow({
                            'No': r['no'],
                            'Name': r['name'],
                            'Initial Quantity': f"{r['initial_quantity']:.3f}",
                            'Quantity Added': f"{r['quantity_added']:.3f}",
                            'Purchases/Transfers': f"{r['purchases_transfers']:.3f}",
                            'Total Initial+Added': f"{r['total_initial_plus_added']:.3f}",
                            'Remaining': f"{r['reste']:.3f}",
                            'Sold': f"{r['sold']:.3f}",
                            'Unit Price': f"{r['unit_price']:.2f}",
                            'Total': f"{r['total']:.2f}"
                        })
                        total_row['Initial Quantity'] += r['initial_quantity']
                        total_row['Quantity Added'] += r['quantity_added']
                        total_row['Purchases/Transfers'] += r['purchases_transfers']
                        total_row['Total Initial+Added'] += r['total_initial_plus_added']
                        total_row['Remaining'] += r['reste']
                        total_row['Sold'] += r['sold']
                        total_row['Total'] += r['total']

                    # Totals line
                    writer.writerow({})
                    writer.writerow({
                        'No': '',
                        'Name': 'TOTALS',
                        'Initial Quantity': f"{total_row['Initial Quantity']:.3f}",
                        'Quantity Added': f"{total_row['Quantity Added']:.3f}",
                        'Purchases/Transfers': f"{total_row['Purchases/Transfers']:.3f}",
                        'Total Initial+Added': f"{total_row['Total Initial+Added']:.3f}",
                        'Remaining': f"{total_row['Remaining']:.3f}",
                        'Sold': f"{total_row['Sold']:.3f}",
                        'Unit Price': '',
                        'Total': f"{total_row['Total']:.2f}"
                    })

                return path

        except Exception as e:
            print(f"❌ Erreur export_products_summary: {e}")
            return ''

    def get_products_summary(self, date_debut, date_fin, include_services: bool = True):
        """
        Retourne la liste des produits/services vendus (rows_out) pour la période donnée.
        Même logique qu'export_products_summary mais renvoie les lignes au lieu d'écrire un CSV.
        """
        from datetime import datetime as _dt
        # Normaliser bornes
        if isinstance(date_debut, _dt):
            d1 = date_debut
        else:
            d1 = datetime.combine(date_debut, datetime.min.time())
        if isinstance(date_fin, _dt):
            d2 = date_fin
        else:
            d2 = datetime.combine(date_fin, datetime.max.time())

        try:
            with self.db_manager.get_session() as session:
                # Rassembler ventes produits (boutique)
                q_products = text("""
                    SELECT cp.id as product_id, cp.name as product_name,
                           COALESCE(SUM(spp.quantity),0) as sold_qty,
                           COALESCE(MAX(cp.price_unit),0) as unit_price
                    FROM shop_paniers_products spp
                    LEFT JOIN shop_paniers p ON spp.panier_id = p.id
                    LEFT JOIN core_products cp ON spp.product_id = cp.id
                    WHERE p.created_at >= :d1 AND p.created_at <= :d2
                    AND LOWER(COALESCE(p.status,'')) <> 'cancelled'
                    GROUP BY cp.id, cp.name
                """)
                prod_rows = session.execute(q_products, {'d1': d1, 'd2': d2}).fetchall()

                # Ventes restaurant
                q_restau = text("""
                    SELECT cp.id as product_id, cp.name as product_name,
                           COALESCE(SUM(rpp.quantity),0) as sold_qty,
                           COALESCE(MAX(cp.price_unit),0) as unit_price
                    FROM restau_produit_panier rpp
                    LEFT JOIN restau_paniers rp ON rpp.panier_id = rp.id
                    LEFT JOIN core_products cp ON rpp.product_id = cp.id
                    WHERE rp.created_at >= :d1 AND rp.created_at <= :d2
                    AND LOWER(COALESCE(rp.status,'')) <> 'annule'
                    GROUP BY cp.id, cp.name
                """)
                restau_rows = session.execute(q_restau, {'d1': d1, 'd2': d2}).fetchall()

                # Services (shop)
                service_map = []
                if include_services:
                    q_services = text("""
                        SELECT ss.id as service_id, ss.name as service_name,
                               COALESCE(SUM(sps.quantity),0) as sold_qty,
                               COALESCE(MAX(ss.price),0) as unit_price
                        FROM shop_paniers_services sps
                        LEFT JOIN shop_paniers p ON sps.panier_id = p.id
                        LEFT JOIN shop_services ss ON sps.service_id = ss.id
                        WHERE p.created_at >= :d1 AND p.created_at <= :d2
                        AND LOWER(COALESCE(p.status,'')) <> 'cancelled'
                        GROUP BY ss.id, ss.name
                    """)
                    service_map = session.execute(q_services, {'d1': d1, 'd2': d2}).fetchall()

                # Agréger produits (boutique + restaurant)
                items = {}
                for r in prod_rows:
                    pid = f"P-{r.product_id}"
                    items[pid] = {
                        'name': r.product_name,
                        'sold': float(r.sold_qty or 0),
                        'unit_price': float(r.unit_price or 0),
                        'product_id': r.product_id,
                        'is_service': False
                    }
                for r in restau_rows:
                    pid = f"P-{r.product_id}"
                    if pid in items:
                        items[pid]['sold'] += float(r.sold_qty or 0)
                    else:
                        items[pid] = {
                            'name': r.product_name,
                            'sold': float(r.sold_qty or 0),
                            'unit_price': float(r.unit_price or 0),
                            'product_id': r.product_id,
                            'is_service': False
                        }
                # Services
                for s in service_map:
                    sid = f"S-{s.service_id}"
                    items[sid] = {
                        'name': s.service_name,
                        'sold': float(s.sold_qty or 0),
                        'unit_price': float(s.unit_price or 0),
                        'service_id': s.service_id,
                        'is_service': True
                    }

                # Pour chaque produit/service, calculer quantités stock via stock_mouvements
                rows_out = []
                for idx, (key, it) in enumerate(items.items(), start=1):
                    if it.get('is_service'):
                        # Pas de stock pour les services
                        initial_q = 0.0
                        added_q = 0.0
                        purchases_q = 0.0
                    else:
                        pid = it.get('product_id')
                        # quantité initiale = somme des mouvements avant d1
                        q_init = text("SELECT COALESCE(SUM(quantity),0) as qty FROM stock_mouvements WHERE product_id = :pid AND movement_date < :d1")
                        try:
                            r_init = session.execute(q_init, {'pid': pid, 'd1': d1}).fetchone()
                            initial_q = float(r_init.qty or 0)
                        except Exception:
                            initial_q = 0.0

                        # quantité ajoutée pendant l'intervalle (ENTREE, TRANSFERT, AJUSTEMENT)
                        q_added = text("SELECT COALESCE(SUM(quantity),0) as qty FROM stock_mouvements WHERE product_id = :pid AND movement_date >= :d1 AND movement_date <= :d2 AND movement_type IN ('ENTREE','TRANSFERT','AJUSTEMENT')")
                        try:
                            r_added = session.execute(q_added, {'pid': pid, 'd1': d1, 'd2': d2}).fetchone()
                            added_q = float(r_added.qty or 0)
                        except Exception:
                            added_q = 0.0

                        # achats/transferts (ENTREE or TRANSFERT)
                        q_purch = text("SELECT COALESCE(SUM(quantity),0) as qty FROM stock_mouvements WHERE product_id = :pid AND movement_date >= :d1 AND movement_date <= :d2 AND movement_type IN ('ENTREE','TRANSFERT')")
                        try:
                            r_purch = session.execute(q_purch, {'pid': pid, 'd1': d1, 'd2': d2}).fetchone()
                            purchases_q = float(r_purch.qty or 0)
                        except Exception:
                            purchases_q = 0.0

                    sold = float(it.get('sold', 0.0))
                    total_initial_plus = initial_q + added_q
                    reste = total_initial_plus - sold
                    unit_price = float(it.get('unit_price', 0.0))
                    total_amount = sold * unit_price

                    rows_out.append({
                        'no': idx,
                        'name': it['name'],
                        'initial_quantity': initial_q,
                        'quantity_added': added_q,
                        'purchases_transfers': purchases_q,
                        'total_initial_plus_added': total_initial_plus,
                        'reste': reste,
                        'sold': sold,
                        'unit_price': unit_price,
                        'total': total_amount
                    })

                return rows_out

        except Exception as e:
            print(f"❌ Erreur get_products_summary: {e}")
            return []

    def get_commande_details(self, commande_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        # debug entry removed
        """
        Récupérer les détails d'une commande spécifique

        Args:
            commande_id: ID entier ou numéro de commande (string)

        Returns:
            Détails de la commande ou None si non trouvée
        """
        try:
            with self.db_manager.get_session() as session:
                # Déterminer si c'est un ID entier ou un numéro de commande
                if isinstance(commande_id, str) and not commande_id.isdigit():
                    # C'est un numéro de commande, rechercher par numero_commande
                    query = text("""
                        SELECT
                            sp.*,
                            COALESCE(sc.nom || ' ' || COALESCE(sc.prenom, ''), 'Client anonyme') as client_name
                        FROM shop_paniers sp
                        LEFT JOIN shop_clients sc ON sp.client_id = sc.id
                        WHERE sp.numero_commande = :commande_id
                    """)
                else:
                    # C'est un ID entier
                    commande_id_int = int(commande_id)
                    query = text("""
                        SELECT
                            sp.*,
                            COALESCE(sc.nom || ' ' || COALESCE(sc.prenom, ''), 'Client anonyme') as client_name
                        FROM shop_paniers sp
                        LEFT JOIN shop_clients sc ON sp.client_id = sc.id
                        WHERE sp.id = :commande_id
                    """)
                    commande_id = commande_id_int

                # Exécuter la requête shop_paniers ; si la table est absente, continuer vers restau
                try:
                    result = session.execute(query, {'commande_id': commande_id})
                    commande = result.fetchone()
                except Exception as e:
                    print(f"⚠️ shop_paniers query failed in get_commande_details, will try restaurant: {e}")
                    commande = None

                if not commande:
                    # Si pas trouvé dans shop_paniers, tenter restau_paniers (module restaurant)
                    try:
                        # Vérifier l'existence des tables optionnelles
                        has_core_users = False
                        has_shop_clients = False
                        try:
                            tbl = session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name=:t"), {'t': 'core_users'}).fetchone()
                            has_core_users = tbl is not None
                        except Exception:
                            has_core_users = False

                        try:
                            tbl2 = session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name=:t"), {'t': 'shop_clients'}).fetchone()
                            has_shop_clients = tbl2 is not None
                        except Exception:
                            has_shop_clients = False

                        # Construire dynamiquement la sélection et les jointures
                        serveuse_select = "su.name as serveuse_name, scu.name as comptoiriste_name" if has_core_users else "NULL as serveuse_name, NULL as comptoiriste_name"
                        serveuse_joins = "LEFT JOIN core_users su ON rp.serveuse_id = su.id\n                            LEFT JOIN core_users scu ON rp.user_id = scu.id" if has_core_users else ""
                        client_join = "LEFT JOIN shop_clients sc ON rp.client_id = sc.id" if has_shop_clients else ""

                        r_base = f"""
                            SELECT rp.*, rt.number as table_number, rs.name as salle_name,
                                   {serveuse_select}
                            FROM restau_paniers rp
                            LEFT JOIN restau_tables rt ON rp.table_id = rt.id
                            LEFT JOIN restau_salles rs ON rt.salle_id = rs.id
                            {serveuse_joins}
                            {client_join}
                            WHERE rp.id = :commande_id
                        """
                        r_query = text(r_base)
                        r_res = session.execute(r_query, {'commande_id': commande_id}).fetchone()
                        if not r_res:
                            return None

                        # if created_at is missing in db, set it to machine time
                        try:
                            if not getattr(r_res, 'created_at', None):
                                now = datetime.now()
                                session.execute(text("UPDATE restau_paniers SET created_at = :now, updated_at = :now WHERE id = :id"), {'now': now, 'id': r_res.id})
                                session.flush()
                                r_res = session.execute(r_query, {'commande_id': commande_id}).fetchone()
                        except Exception:
                            pass

                        r_dict = dict(r_res._asdict())

                        # Calculer montant_paye pour restau
                        payments_query = text("""
                            SELECT COALESCE(SUM(amount), 0) as montant_paye
                            FROM restau_payments
                            WHERE panier_id = :panier_id
                        """)
                        payments_row = session.execute(payments_query, {'panier_id': r_dict['id']}).fetchone()
                        r_dict['montant_paye'] = payments_row.montant_paye if payments_row else 0

                        # Récupérer produits restau (table restau_produit_panier)
                        # Construire la requête produits en prenant en compte l'existence de core_products
                        has_core_products = False
                        try:
                            tbl3 = session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name=:t"), {'t': 'core_products'}).fetchone()
                            has_core_products = tbl3 is not None
                        except Exception:
                            has_core_products = False

                        if has_core_products:
                            products_query = text("""
                                SELECT rpp.*, cp.name as product_name, rpp.price as unit_price, rpp.total as total_price
                                FROM restau_produit_panier rpp
                                LEFT JOIN core_products cp ON rpp.product_id = cp.id
                                WHERE rpp.panier_id = :commande_id
                            """)
                        else:
                            products_query = text("""
                                SELECT rpp.*, rpp.product_id as product_name, rpp.price as unit_price, rpp.total as total_price
                                FROM restau_produit_panier rpp
                                WHERE rpp.panier_id = :commande_id
                            """)
                        products_result = session.execute(products_query, {'commande_id': r_dict['id']})
                        products = products_result.fetchall()

                        produits_detail = []
                        for product in products:
                            product_dict = dict(product._asdict())
                            produits_detail.append(
                                f"• {product_dict.get('product_name', 'Produit inconnu')} - {product_dict.get('quantity', 0)} x {product_dict.get('unit_price', 0):.0f} {self.get_currency_symbol()} = {product_dict.get('total_price', 0):.0f} {self.get_currency_symbol()}"
                            )

                        r_dict['produits_detail'] = '\n'.join(produits_detail) if produits_detail else 'Aucun produit/service'

                        # Ajouter métadonnées table/serveuse/comptoiriste au dict
                        r_dict['table_number'] = r_dict.get('table_number')
                        r_dict['salle_name'] = r_dict.get('salle_name')
                        r_dict['serveuse_name'] = r_dict.get('serveuse_name')
                        r_dict['comptoiriste_name'] = r_dict.get('comptoiriste_name')
                        r_dict['module'] = 'restaurant'

                        return r_dict
                    except Exception as e:
                        # Ne pas masquer l'erreur ici : relancer pour permettre le debug
                        raise

                commande_dict = dict(commande._asdict())
                
                # S'assurer que les valeurs string sont bien des strings (pas None)
                for key, value in commande_dict.items():
                    if value is None:
                        if key in ['numero_commande', 'notes', 'payment_method']:
                            commande_dict[key] = ''
                        elif key in ['client_name']:
                            commande_dict[key] = 'Client anonyme'
                        elif key in ['subtotal', 'remise_amount', 'total_final', 'montant_paye']:
                            commande_dict[key] = 0.0

                # Récupérer l'ID réel de la commande pour les requêtes suivantes
                real_commande_id = commande_dict['id']

                # Calculer le montant payé
                payments_query = text("""
                    SELECT COALESCE(SUM(amount), 0) as montant_paye
                    FROM shop_payments
                    WHERE panier_id = :panier_id
                """)

                payments_result = session.execute(payments_query, {'panier_id': commande_dict['id']})
                payments_row = payments_result.fetchone()
                commande_dict['montant_paye'] = payments_row.montant_paye if payments_row else 0

                # Récupérer les produits de la commande
                products_query = text("""
                    SELECT
                        spp.*,
                        cp.name as product_name,
                        spp.price_unit as unit_price
                    FROM shop_paniers_products spp
                    LEFT JOIN core_products cp ON spp.product_id = cp.id
                    WHERE spp.panier_id = :commande_id
                """)

                products_result = session.execute(products_query, {'commande_id': real_commande_id})
                products = products_result.fetchall()

                # Récupérer les services de la commande
                services_query = text("""
                    SELECT
                        sps.*,
                        es.name as service_name,
                        sps.price_unit as unit_price
                    FROM shop_paniers_services sps
                    LEFT JOIN event_services es ON sps.service_id = es.id
                    WHERE sps.panier_id = :commande_id
                """)

                services_result = session.execute(services_query, {'commande_id': real_commande_id})
                services = services_result.fetchall()

                # Construire le détail des produits/services
                produits_detail = []
                for product in products:
                    product_dict = dict(product._asdict())
                    produits_detail.append(
                        f"• {product_dict.get('product_name', 'Produit inconnu')} - {product_dict.get('quantity', 0)} x {product_dict.get('unit_price', 0):.0f} {self.get_currency_symbol()} = {product_dict.get('total_price', 0):.0f} {self.get_currency_symbol()}"
                    )

                for service in services:
                    service_dict = dict(service._asdict())
                    produits_detail.append(
                        f"• {service_dict.get('service_name', 'Service inconnu')} - {service_dict.get('quantity', 0)} x {service_dict.get('unit_price', 0):.0f} {self.get_currency_symbol()} = {service_dict.get('total_price', 0):.0f} {self.get_currency_symbol()}"
                    )

                commande_dict['produits_detail'] = '\n'.join(produits_detail) if produits_detail else 'Aucun produit/service'

                # debug return removed
                return commande_dict

        except Exception as e:
            # Remonter l'exception pour faciliter le debug (ne pas masquer)
            print(f"❌ Erreur get_commande_details: {e}")
            raise

    def get_serveuses(self) -> List[Dict[str, Any]]:
        """
        Retourne la liste des utilisateurs (id, nom, prenom) — utile pour charger/filtrer les serveuses
        """
        try:
            with self.db_manager.get_session() as session:
                q = text("SELECT id, name FROM core_users ORDER BY name")
                res = session.execute(q).fetchall()
                return [{'id': r.id, 'name': r.name} for r in res]
        except Exception:
            return []

    def process_commande_payment(self, commande_id: int, payment_method: str, amount: float, 
                                pos_id: int, current_user) -> tuple[bool, str]:
        """
        Traiter le paiement d'une commande existante avec logique comptable
        
        Args:
            commande_id: ID de la commande
            payment_method: Méthode de paiement
            amount: Montant payé
            pos_id: ID du point de vente
            current_user: Utilisateur actuel
            
        Returns:
            Tuple (succès, message)
        """
        try:
            with self.db_manager.get_session() as session:
                # Vérifier que la commande existe
                commande_result = session.execute(text("""
                    SELECT id, numero_commande, total_final, 
                           (SELECT COALESCE(SUM(amount), 0) FROM shop_payments WHERE panier_id = sp.id) as montant_paye,
                           (SELECT sc.nom || ' ' || COALESCE(sc.prenom, '') FROM shop_clients sc WHERE sc.id = sp.client_id) as client_name
                    FROM shop_paniers sp 
                    WHERE id = :commande_id
                """), {'commande_id': commande_id})
                
                commande = commande_result.fetchone()
                if not commande:
                    return False, "Commande introuvable"
                
                montant_paye = commande.montant_paye or 0
                total_final = commande.total_final or 0
                montant_restant = total_final - montant_paye
                
                # Vérifier que le montant ne dépasse pas le restant dû
                if amount > montant_restant:
                    return False, f"Le montant saisi ({amount:.0f} {self.get_currency_symbol()}) dépasse le restant dû ({montant_restant:.0f} {self.get_currency_symbol()})."
                
                # Insérer le paiement
                insert_payment = text("""
                    INSERT INTO shop_payments (panier_id, payment_method, amount, payment_date)
                    VALUES (:panier_id, :payment_method, :amount, :payment_date)
                """)
                
                session.execute(insert_payment, {
                    'panier_id': commande_id,
                    'payment_method': payment_method,
                    'amount': amount,
                    'payment_date': datetime.now()
                })
                
                # === LOGIQUE COMPTABLE POUR PAIEMENT DE COMMANDE ===
                # Récupérer la configuration comptable pour ce POS
                config_result = session.execute(text("""
                    SELECT compte_caisse_id, compte_client_id
                    FROM compta_config
                    WHERE pos_id = :pos_id
                    LIMIT 1
                """), {'pos_id': pos_id})
                
                config_row = config_result.fetchone()
                if config_row:
                    compte_caisse_id = config_row[0]
                    compte_client_id = config_row[1]
                    
                    if compte_caisse_id and compte_client_id:
                        # Créer le journal de paiement
                        numero_commande = commande.numero_commande or f"CMD-{commande.id}"
                        journal_payment_result = session.execute(text("""
                            INSERT INTO compta_journaux
                            (date_operation, libelle, montant, type_operation, reference, description,
                             enterprise_id, user_id, date_creation, date_modification)
                            VALUES (:date_operation, :libelle, :montant, :type_operation, :reference,
                                    :description, :enterprise_id, :user_id, :date_creation, :date_modification)
                        """), {
                            'date_operation': datetime.now(),
                            'libelle': f"Paiement commande {numero_commande}",
                            'montant': amount,
                            'type_operation': 'paiement',
                            'reference': f"PAI-{numero_commande}",
                            'description': f"Paiement commande - {payment_method}",
                            'enterprise_id': 1,  # TODO: Récupérer dynamiquement
                            'user_id': getattr(current_user, 'id', 1),
                            'date_creation': datetime.now(),
                            'date_modification': datetime.now()
                        })
                        
                        session.flush()
                        journal_payment_id_result = session.execute(text("SELECT last_insert_rowid()"))
                        journal_payment_id = journal_payment_id_result.fetchone()[0]
                        
                        # Écriture débit : Compte de caisse (augmente la trésorerie)
                        session.execute(text("""
                            INSERT INTO compta_ecritures
                            (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                            VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
                        """), {
                            'journal_id': journal_payment_id,
                            'compte_id': compte_caisse_id,
                            'debit': amount,
                            'credit': 0,
                            'ordre': 1,
                            'libelle': f"Paiement commande {numero_commande}",
                            'date_creation': datetime.now()
                        })
                        
                        # Écriture crédit : Compte client (diminue la dette du client)
                        session.execute(text("""
                            INSERT INTO compta_ecritures
                            (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                            VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
                        """), {
                            'journal_id': journal_payment_id,
                            'compte_id': compte_client_id,
                            'debit': 0,
                            'credit': amount,
                            'ordre': 2,
                            'libelle': f"Règlement client - {commande.client_name or 'Client anonyme'}",
                            'date_creation': datetime.now()
                        })
                
                session.commit()
                return True, f"Paiement de {amount:.0f} {self.get_currency_symbol()} enregistré avec succès."
                
        except Exception as e:
            print(f"❌ Erreur process_commande_payment: {e}")
            return False, f"Erreur lors de l'enregistrement du paiement: {str(e)}"

    def process_restaurant_payment(self, panier_id: int, payment_method: str, amount: float, current_user) -> tuple[bool, str]:
        """
        Enregistrer un paiement pour un panier restaurant (restau_payments) et créer les écritures comptables si configurées.
        """
        try:
            with self.db_manager.get_session() as session:
                # Vérifier que le panier restaurant existe
                q = text("SELECT id, total_final FROM restau_paniers WHERE id = :pid")
                res = session.execute(q, {'pid': panier_id}).fetchone()
                if not res:
                    return False, "Panier restaurant introuvable"

                total_final = res.total_final or 0
                # Calculer montant déjà payé
                paid_row = session.execute(text("SELECT COALESCE(SUM(amount),0) as montant_paye FROM restau_payments WHERE panier_id = :pid"), {'pid': panier_id}).fetchone()
                montant_paye = paid_row.montant_paye if paid_row else 0
                montant_restant = total_final - montant_paye

                if amount > montant_restant:
                    return False, f"Le montant saisi ({amount:.0f} {self.get_currency_symbol()}) dépasse le restant dû ({montant_restant:.0f} {self.get_currency_symbol()})."

                # Insérer paiement
                session.execute(text("""
                    INSERT INTO restau_payments (panier_id, amount, payment_method, user_id, created_at)
                    VALUES (:panier_id, :amount, :payment_method, :user_id, :created_at)
                """), {
                    'panier_id': panier_id,
                    'amount': amount,
                    'payment_method': payment_method,
                    'user_id': getattr(current_user, 'id', None) or 1,
                    'created_at': datetime.now()
                })

                # Comptabilité : réutiliser la même config compta (si présente)
                config_result = session.execute(text("""
                    SELECT compte_caisse_id, compte_client_id
                    FROM compta_config
                    WHERE pos_id = :pos_id
                    LIMIT 1
                """), {'pos_id': 1})
                config_row = config_result.fetchone()
                if config_row:
                    compte_caisse_id = config_row[0]
                    compte_client_id = config_row[1]
                    if compte_caisse_id and compte_client_id:
                        # journal
                        numero = f"-{panier_id}"
                        session.execute(text("""
                            INSERT INTO compta_journaux
                            (date_operation, libelle, montant, type_operation, reference, description, enterprise_id, user_id, date_creation, date_modification)
                            VALUES (:date_operation, :libelle, :montant, :type_operation, :reference, :description, :enterprise_id, :user_id, :date_creation, :date_modification)
                        """), {
                            'date_operation': datetime.now(),
                            'libelle': f"Paiement CMD {numero}",
                            'montant': amount,
                            'type_operation': 'paiement',
                            'reference': f"PAI-{numero}",
                            'description': f"Paiement - {payment_method}",
                            'enterprise_id': 1,
                            'user_id': getattr(current_user, 'id', 1),
                            'date_creation': datetime.now(),
                            'date_modification': datetime.now()
                        })
                        session.flush()
                        journal_id = session.execute(text("SELECT last_insert_rowid()")).fetchone()[0]
                        session.execute(text("""
                            INSERT INTO compta_ecritures (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                            VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
                        """), {
                            'journal_id': journal_id,
                            'compte_id': compte_caisse_id,
                            'debit': amount,
                            'credit': 0,
                            'ordre': 1,
                            'libelle': f"Paiement CMD {numero}",
                            'date_creation': datetime.now()
                        })
                        session.execute(text("""
                            INSERT INTO compta_ecritures (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                            VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
                        """), {
                            'journal_id': journal_id,
                            'compte_id': compte_client_id,
                            'debit': 0,
                            'credit': amount,
                            'ordre': 2,
                            'libelle': f"Règlement client - REST {panier_id}",
                            'date_creation': datetime.now()
                        })

                session.commit()
                return True, f"Paiement de {amount:.0f} {self.get_currency_symbol()} enregistré pour le panier restaurant."

        except Exception as e:
            print(f"❌ Erreur process_restaurant_payment: {e}")
            return False, f"Erreur lors de l'enregistrement du paiement restaurant: {e}"

    def cancel_restaurant_commande(self, panier_id: int, current_user) -> tuple[bool, str]:
        """
        Annuler une commande du restaurant en mettant à jour le statut du panier restau.
        """
        try:
            with self.db_manager.session_scope() as session:
                res = session.execute(text("SELECT id, status FROM restau_paniers WHERE id = :pid"), {'pid': panier_id}).fetchone()
                if not res:
                    return False, "Panier restaurant introuvable"
                current_status = (res.status or '').lower()
                if current_status in ('cancelled', 'annule', 'annulé'):
                    return False, "Le panier est déjà annulé"

                # Si la commande était validée, il faut :
                # - inverser les paiements (mettre les montants à 0 et créer écritures comptables inverses)
                # - recréer des mouvements de stock d'entrée pour remettre les quantités
                if current_status == 'valide':
                    # 1) Récupérer total des paiements
                    paid_row = session.execute(text("SELECT COALESCE(SUM(amount),0) as s FROM restau_payments WHERE panier_id = :pid"), {'pid': panier_id}).fetchone()
                    total_paid = paid_row.s if paid_row else 0

                    # Config comptable (si présente)
                    try:
                        cfg = session.execute(text("SELECT compte_caisse_id, compte_client_id FROM compta_config WHERE pos_id = :pos_id LIMIT 1"), {'pos_id': 1}).fetchone()
                    except Exception:
                        cfg = None

                    if total_paid and total_paid > 0:
                        # Créer écritures comptables inverses si les comptes sont configurés
                        if cfg and cfg[0] and cfg[1]:
                            compte_caisse_id = cfg[0]
                            compte_client_id = cfg[1]
                            numero = f"ANN-REST-{panier_id}"
                            session.execute(text("""
                                INSERT INTO compta_journaux
                                (date_operation, libelle, montant, type_operation, reference, description, enterprise_id, user_id, date_creation, date_modification)
                                VALUES (:date_operation, :libelle, :montant, :type_operation, :reference, :description, :enterprise_id, :user_id, :date_creation, :date_modification)
                            """), {
                                'date_operation': datetime.now(),
                                'libelle': f"Annulation paiement restaurant {numero}",
                                'montant': total_paid,
                                'type_operation': 'annulation',
                                'reference': f"ANN-{numero}",
                                'description': f"Annulation paiement restaurant - panier {panier_id}",
                                'enterprise_id': 1,
                                'user_id': getattr(current_user, 'id', 1),
                                'date_creation': datetime.now(),
                                'date_modification': datetime.now()
                            })
                            session.flush()
                            journal_id = session.execute(text("SELECT last_insert_rowid()")).fetchone()[0]

                            # Écritures inverses : débit client, crédit caisse
                            session.execute(text("""
                                INSERT INTO compta_ecritures (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                                VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
                            """), {
                                'journal_id': journal_id,
                                'compte_id': compte_client_id,
                                'debit': total_paid,
                                'credit': 0,
                                'ordre': 1,
                                'libelle': f"Annulation règlement client - REST {panier_id}",
                                'date_creation': datetime.now()
                            })

                            session.execute(text("""
                                INSERT INTO compta_ecritures (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                                VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
                            """), {
                                'journal_id': journal_id,
                                'compte_id': compte_caisse_id,
                                'debit': 0,
                                'credit': total_paid,
                                'ordre': 2,
                                'libelle': f"Annulation paiement caisse - REST {panier_id}",
                                'date_creation': datetime.now()
                            })

                        # Mettre à zéro les paiements enregistrés pour ce panier
                        try:
                            session.execute(text("UPDATE restau_payments SET amount = 0 WHERE panier_id = :pid"), {'pid': panier_id})
                        except Exception:
                            # Si la table ou colonne n'existe pas, on ignore
                            pass

                    # 2) Restaurer le stock pour chaque produit du panier (si des mouvements de sortie existent)
                    try:
                        produits = session.execute(text("SELECT product_id, quantity, price FROM restau_produit_panier WHERE panier_id = :pid"), {'pid': panier_id}).fetchall()
                        if produits:
                            # chercher l'entrepot POS_4 utilisé pour les sorties restaurant
                            wh_row = session.execute(text("SELECT id FROM stock_warehouses WHERE code = 'POS_4' AND is_active = 1 LIMIT 1")).fetchone()
                            warehouse_id = wh_row[0] if wh_row else None
                            for p in produits:
                                product_id = p.product_id
                                qty = p.quantity or 0
                                unit_price = p.price or 0
                                total_cost = (unit_price * qty)

                                if warehouse_id:
                                    # Mettre à jour quantité en entrepot
                                    stock_row = session.execute(text("SELECT quantity FROM stock_produits_entrepot WHERE product_id = :pid AND warehouse_id = :wid LIMIT 1"), {'pid': product_id, 'wid': warehouse_id}).fetchone()
                                    current_stock = stock_row[0] if stock_row else 0
                                    new_stock = int(current_stock) + int(qty)
                                    if stock_row:
                                        session.execute(text("UPDATE stock_produits_entrepot SET quantity = :new_quantity, updated_at = :updated_at WHERE product_id = :pid AND warehouse_id = :wid"), {'new_quantity': new_stock, 'updated_at': datetime.now(), 'pid': product_id, 'wid': warehouse_id})
                                    else:
                                        session.execute(text("INSERT INTO stock_produits_entrepot (product_id, warehouse_id, quantity, created_at, updated_at) VALUES (:pid, :wid, :qty, :created_at, :updated_at)"), {'pid': product_id, 'wid': warehouse_id, 'qty': new_stock, 'created_at': datetime.now(), 'updated_at': datetime.now()})

                                    # Insérer un mouvement d'entrée pour annulation
                                    session.execute(text("""
                                        INSERT INTO stock_mouvements(
                                            product_id, warehouse_id, movement_type, quantity, unit_cost, total_cost,
                                            destination_warehouse_id, reference, description, user_id, movement_date, created_at
                                        ) VALUES (
                                            :product_id, :warehouse_id, :movement_type, :quantity, :unit_cost, :total_cost,
                                            :destination_warehouse_id, :reference, :description, :user_id, :movement_date, :created_at
                                        )
                                    """), {
                                        'product_id': product_id,
                                        'warehouse_id': warehouse_id,
                                        'movement_type': 'ENTREE',
                                        'quantity': qty,
                                        'unit_cost': unit_price,
                                        'total_cost': total_cost,
                                        'destination_warehouse_id': warehouse_id,
                                        'reference': f"ANN-REST-{panier_id}",
                                        'description': f"Annulation vente restaurant - {panier_id}",
                                        'user_id': getattr(current_user, 'id', 1),
                                        'movement_date': datetime.now(),
                                        'created_at': datetime.now()
                                    })
                    except Exception:
                        # Si les tables de stock ne sont pas présentes, ignorer la restauration
                        pass

                    # 3) Inverser également les journaux de vente et de stock créés lors de la finalisation de la vente
                    try:
                        # journal de vente (type 'vente', reference PANIER-{id})
                        sale_j = session.execute(text("SELECT id, montant FROM compta_journaux WHERE reference = :ref AND type_operation = 'vente' LIMIT 1"), {'ref': f"PANIER-{panier_id}"}).fetchone()
                        if sale_j:
                            orig_jid = sale_j.id if hasattr(sale_j, 'id') else sale_j[0]
                            montant_sale = sale_j.montant if hasattr(sale_j, 'montant') else (sale_j[1] if len(sale_j) > 1 else 0)
                            session.execute(text("""
                                INSERT INTO compta_journaux
                                (date_operation, libelle, montant, type_operation, reference, description, enterprise_id, user_id, date_creation, date_modification)
                                VALUES (:date_operation, :libelle, :montant, :type_operation, :reference, :description, :enterprise_id, :user_id, :date_creation, :date_modification)
                            """), {
                                'date_operation': datetime.now(),
                                'libelle': f"Annulation vente PANIER-{panier_id}",
                                'montant': montant_sale or 0,
                                'type_operation': 'annulation',
                                'reference': f"ANN-PANIER-{panier_id}-VENTE",
                                'description': f"Annulation vente restaurant - panier {panier_id}",
                                'enterprise_id': 1,
                                'user_id': getattr(current_user, 'id', 1),
                                'date_creation': datetime.now(),
                                'date_modification': datetime.now()
                            })
                            session.flush()
                            new_jid = session.execute(text("SELECT last_insert_rowid()")).fetchone()[0]

                            # inverser les écritures du journal original
                            entries = session.execute(text("SELECT compte_comptable_id, debit, credit, ordre, libelle FROM compta_ecritures WHERE journal_id = :jid ORDER BY ordre"), {'jid': orig_jid}).fetchall()
                            ordre = 1
                            for e in entries:
                                compte_id = e.compte_comptable_id if hasattr(e, 'compte_comptable_id') else e[0]
                                debit = e.debit if hasattr(e, 'debit') else e[1]
                                credit = e.credit if hasattr(e, 'credit') else e[2]
                                libelle = e.libelle if hasattr(e, 'libelle') else (e[4] if len(e) > 4 else '')
                                session.execute(text("""
                                    INSERT INTO compta_ecritures (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                                    VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
                                """), {
                                    'journal_id': new_jid,
                                    'compte_id': compte_id,
                                    'debit': credit or 0,
                                    'credit': debit or 0,
                                    'ordre': ordre,
                                    'libelle': f"Annulation - {libelle}",
                                    'date_creation': datetime.now()
                                })
                                ordre += 1

                        # journal stock (type 'stock', reference PANIER-{id})
                        stock_j = session.execute(text("SELECT id, montant FROM compta_journaux WHERE reference = :ref AND type_operation = 'stock' LIMIT 1"), {'ref': f"PANIER-{panier_id}"}).fetchone()
                        if stock_j:
                            orig_jid = stock_j.id if hasattr(stock_j, 'id') else stock_j[0]
                            montant_stock = stock_j.montant if hasattr(stock_j, 'montant') else (stock_j[1] if len(stock_j) > 1 else 0)
                            session.execute(text("""
                                INSERT INTO compta_journaux
                                (date_operation, libelle, montant, type_operation, reference, description, enterprise_id, user_id, date_creation, date_modification)
                                VALUES (:date_operation, :libelle, :montant, :type_operation, :reference, :description, :enterprise_id, :user_id, :date_creation, :date_modification)
                            """), {
                                'date_operation': datetime.now(),
                                'libelle': f"Annulation sortie stock PANIER-{panier_id}",
                                'montant': montant_stock or 0,
                                'type_operation': 'annulation',
                                'reference': f"ANN-PANIER-{panier_id}-STOCK",
                                'description': f"Annulation sortie stock restaurant - panier {panier_id}",
                                'enterprise_id': 1,
                                'user_id': getattr(current_user, 'id', 1),
                                'date_creation': datetime.now(),
                                'date_modification': datetime.now()
                            })
                            session.flush()
                            new_jid = session.execute(text("SELECT last_insert_rowid()")).fetchone()[0]

                            entries = session.execute(text("SELECT compte_comptable_id, debit, credit, ordre, libelle FROM compta_ecritures WHERE journal_id = :jid ORDER BY ordre"), {'jid': orig_jid}).fetchall()
                            ordre = 1
                            for e in entries:
                                compte_id = e.compte_comptable_id if hasattr(e, 'compte_comptable_id') else e[0]
                                debit = e.debit if hasattr(e, 'debit') else e[1]
                                credit = e.credit if hasattr(e, 'credit') else e[2]
                                libelle = e.libelle if hasattr(e, 'libelle') else (e[4] if len(e) > 4 else '')
                                session.execute(text("""
                                    INSERT INTO compta_ecritures (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                                    VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
                                """), {
                                    'journal_id': new_jid,
                                    'compte_id': compte_id,
                                    'debit': credit or 0,
                                    'credit': debit or 0,
                                    'ordre': ordre,
                                    'libelle': f"Annulation - {libelle}",
                                    'date_creation': datetime.now()
                                })
                                ordre += 1
                    except Exception as e:
                        # Si les tables comptables n'existent pas ou autre erreur, on ignore l'annulation comptable additionnelle
                        print(f"⚠️ Impossible d'inverser journaux vente/stock pour panier {panier_id}: {e}")
                # Mettre à jour le statut du panier (quel que soit l'état précédent)
                session.execute(text("UPDATE restau_paniers SET status = :st WHERE id = :pid"), {'st': 'cancelled', 'pid': panier_id})
                return True, "Commande restaurant annulée avec succès."
        except Exception as e:
            print(f"❌ Erreur cancel_restaurant_commande: {e}")
            return False, f"Erreur lors de l'annulation: {e}"