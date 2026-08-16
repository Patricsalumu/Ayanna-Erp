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
from ayanna_erp.core.session_manager import SessionManager


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
                        COALESCE(
                            CONCAT(
                                COALESCE(sc.nom, ''),
                                ' ',
                                COALESCE(sc.prenom, ''),
                                CASE 
                                    WHEN sc.telephone IS NOT NULL AND sc.telephone != '' 
                                        THEN CONCAT(' (', sc.telephone, ')')
                                    ELSE ''
                                END
                            ),
                            'Client anonyme'
                        ) AS client_name,
                        sp.subtotal,
                        sp.remise_amount,
                        sp.total_final,
                        sp.payment_method,
                        sp.status,
                        sp.pret as pret,
                        sp.livre as livre,
                        (
                            SELECT GROUP_CONCAT(CONCAT(COALESCE(cp.name, 'Produit'), ' (x', spp.quantity, ')'))
                            FROM shop_paniers_products spp
                            JOIN core_products cp ON spp.product_id = cp.id
                            WHERE spp.panier_id = sp.id
                        ) as produits,
                        (
                            SELECT GROUP_CONCAT(CONCAT(COALESCE(ss.name, 'Service'), ' (x', sps.quantity, ')'))
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
                    # include pret/livre flags if present
                    commande['pret'] = getattr(c, 'pret', None)
                    commande['livre'] = getattr(c, 'livre', None)
                    processed.append(commande)

                # --- Récupérer également les paniers du module Restaurant (avec mêmes filtres) ---
                try:
                    # Les tables métier sont les tables MySQL standards du projet ; les jointures sont donc toujours actives.
                    client_name_expr = "COALESCE(CONCAT(sc.nom, ' ', COALESCE(sc.prenom, '')), 'Client restaurant')"
                    serveuse_select = "su.name as serveuse_name, scu.name as comptoiriste_name"
                    serveuse_joins = "LEFT JOIN core_users su ON rp.serveuse_id = su.id\n                        LEFT JOIN core_users scu ON rp.user_id = scu.id"
                    client_join = "LEFT JOIN shop_clients sc ON rp.client_id = sc.id"

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
                                rp.pret as pret,
                                rp.livre as livre,
                                rp.serveuse_id,
                            (
                                SELECT GROUP_CONCAT(CONCAT(COALESCE(cp.name, 'Produit'), ' (x', rpp.quantity, ')'))
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

                    prod_concat_join = "LEFT JOIN core_products cp ON rpp.product_id = cp.id"
                    prod_concat_expr = "CONCAT(COALESCE(cp.name, 'Produit'), ' (x', rpp.quantity, ')')"

                    # Injecter l'expression produit dans la requête
                    restau_base = restau_base.replace("FROM restau_produit_panier rpp\n                                LEFT JOIN core_products cp ON rpp.product_id = cp.id\n                                WHERE rpp.panier_id = rp.id",
                                                        f"FROM restau_produit_panier rpp\n                                {prod_concat_join}\n                                WHERE rpp.panier_id = rp.id")

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

                        # Debug removed for production

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
                            'serveuse_id': getattr(r, 'serveuse_id', None),
                            'serveuse_name': getattr(r, 'serveuse_name', None),
                            'comptoiriste_name': getattr(r, 'comptoiriste_name', None)
                        }
                        # include pret/livre flags if present
                        commande['pret'] = getattr(r, 'pret', None)
                        commande['livre'] = getattr(r, 'livre', None)
                        processed.append(commande)
                except Exception as e:
                    # Si la table restau_* n'existe pas ou autre problème, on log l'erreur
                    print(f"⚠️ restau_paniers query failed or other err: {e}")

                return processed
        except Exception as e:
            print(f"❌ Erreur get_commandes: {e}")
            return []

    def set_commande_pret_livre(self, panier_id: Union[int, str], pret: bool, livre: bool, module: str = 'boutique') -> bool:
        """Met à jour les flags 'pret' et 'livre' pour un panier.

        Accepte aussi un identifiant sous forme de tuple `(id, module)` pour compatibilité.

        Retourne True si la mise à jour a réussi, False sinon.
        """
        try:
            # Compatibilité : certains appels transmettent (id, module)
            if isinstance(panier_id, tuple):
                if len(panier_id) >= 1:
                    raw_id = panier_id[0]
                    if len(panier_id) >= 2 and panier_id[1]:
                        module = str(panier_id[1])
                    panier_id = raw_id

            # Normaliser l'identifiant pour sqlite binding
            try:
                panier_id = int(panier_id)
            except Exception:
                pass

            table_name = 'shop_paniers'
            if isinstance(module, str) and module.lower() in ('restaurant', 'restau'):
                table_name = 'restau_paniers'

            with self.db_manager.session_scope() as session:
                now = datetime.now()
                # Empêcher toute modification d'une commande finalisée (prêt + livré)
                lock_query = text(f"""
                    SELECT pret, livre
                    FROM {table_name}
                    WHERE id = :id
                """)
                lock_row = session.execute(lock_query, {'id': panier_id}).fetchone()
                if lock_row is None:
                    print(f"⚠️ set_commande_pret_livre: commande introuvable id={panier_id}, module={module}")
                    return False

                if int(bool(getattr(lock_row, 'pret', 0))) == 1 and int(bool(getattr(lock_row, 'livre', 0))) == 1:
                    print(f"ℹ️ set_commande_pret_livre: commande verrouillée id={panier_id}, module={module}")
                    return False

                # Tentative de mise à jour, gérer l'absence de colonnes par exception
                query = text(f"""
                    UPDATE {table_name}
                    SET pret = :pret, livre = :livre, updated_at = :now
                    WHERE id = :id
                """)
                result = session.execute(query, {'pret': int(bool(pret)), 'livre': int(bool(livre)), 'now': now, 'id': panier_id})
                # Some DB backends may expose rowcount; check to ensure update applied
                try:
                    rc = result.rowcount
                except Exception:
                    rc = None
                if rc is not None and rc == 0:
                    print(f"⚠️ set_commande_pret_livre: aucune ligne affectée pour id={panier_id}, module={module}")
                    return False
                return True
        except Exception as e:
            # Si mise à jour échoue (par ex. colonnes manquantes), log et renvoyer False
            print(f"⚠️ set_commande_pret_livre failed for id={panier_id}, module={module}: {e}")
            return False

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

        # Calculer les créances = somme de MAX(0, total_final - montant_paye)
        # Les créances ne peuvent JAMAIS être négatives
        total_creances = 0.0
        negative_creances = []  # Pour debug

        # Calculer les statistiques de paiement
        commandes_payees = 0
        commandes_non_payees = 0
        commandes_partielles = 0

        for c in commandes:
            montant_paye = float(c.get('montant_paye', 0) or 0)
            total_final = float(c.get('total_final', 0) or 0)

            # créance = MAX(0, total_final - montant_paye)
            # Jamais négatif!
            creance_cmd = max(0.0, total_final - montant_paye)
            total_creances += creance_cmd
            
            # Loguer les cas où montant_paye > total_final (bug potentiel)
            if montant_paye > total_final and total_final > 0:
                negative_creances.append({
                    'id': c.get('id'),
                    'numero': c.get('numero_commande'),
                    'total_final': total_final,
                    'montant_paye': montant_paye,
                    'overpay': montant_paye - total_final
                })

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
        
        # Log les cas problématiques pour debug
        if negative_creances:
            print(f"⚠️ OVERPAYMENTS DETECTED ({len(negative_creances)} cases):")
            for nc in negative_creances:
                print(f"  - Order {nc['numero']} (id={nc['id']}): total={nc['total_final']:.2f}, paid={nc['montant_paye']:.2f}, overpay={nc['overpay']:.2f}")

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
        
        # Sécurité: s'assurer que total_creances ne peut jamais être négatif
        total_creances = max(0.0, total_creances)

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

    def get_period_commandes_stats(self, date_debut, date_fin, search_term: Optional[str] = None, payment_filter: Optional[str] = None) -> Dict[str, Any]:
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
                # Construire conditions dynamiques pour SHOP
                shop_conditions = ["created_at >= :d1", "created_at <= :d2", "LOWER(COALESCE(status,'')) <> 'cancelled'"]
                restau_conditions = ["created_at >= :d1", "created_at <= :d2", "LOWER(COALESCE(status,'')) NOT IN ('annule','annulé', 'cancelled')"]
                params = {'d1': d1, 'd2': d2}

                if payment_filter and payment_filter != 'Tous':
                    shop_conditions.append("payment_method = :payment_method")
                    restau_conditions.append("payment_method = :payment_method")
                    params['payment_method'] = payment_filter

                if search_term:
                    params['search'] = f"%{search_term}%"
                    # SHOP: numero_commande, client, produits, services
                    shop_conditions.append("(numero_commande LIKE :search OR EXISTS (SELECT 1 FROM shop_clients sc WHERE sc.id = shop_paniers.client_id AND (sc.nom LIKE :search OR sc.prenom LIKE :search)) OR EXISTS (SELECT 1 FROM shop_paniers_products spp JOIN core_products cp ON spp.product_id = cp.id WHERE spp.panier_id = shop_paniers.id AND cp.name LIKE :search) OR EXISTS (SELECT 1 FROM shop_paniers_services sps JOIN shop_services ss ON sps.service_id = ss.id WHERE sps.panier_id = shop_paniers.id AND ss.name LIKE :search))")
                    # RESTAU: id, client, produits
                    restau_conditions.append("(CAST(id AS TEXT) LIKE :search OR EXISTS (SELECT 1 FROM shop_clients sc WHERE sc.id = restau_paniers.client_id AND (sc.nom LIKE :search OR sc.prenom LIKE :search)) OR EXISTS (SELECT 1 FROM restau_produit_panier rpp JOIN core_products cp ON rpp.product_id = cp.id WHERE rpp.panier_id = restau_paniers.id AND cp.name LIKE :search))")

                shop_where = " WHERE " + " AND ".join(shop_conditions)
                restau_where = " WHERE " + " AND ".join(restau_conditions)

                # CA total (shop + restau) filtré
                q_ca = text(f"""
                    SELECT
                      COALESCE((SELECT SUM(total_final) FROM shop_paniers {shop_where}),0)
                      + COALESCE((SELECT SUM(total_final) FROM restau_paniers {restau_where}),0)
                      as total_ca
                """)
                ca_row = session.execute(q_ca, params).fetchone()
                total_ca = float(ca_row.total_ca or 0)

                # Helper pour aliaser proprement les conditions sans corrompre les noms de tables
                def _alias_shop_condition(cond: str, alias: str) -> str:
                    c = cond
                    # Remplacer seulement les colonnes, pas les paramètres bind
                    c = c.replace("created_at", f"{alias}.created_at")
                    c = c.replace("status", f"{alias}.status")
                    # Pour payment_method, remplacer seulement la colonne, pas :payment_method
                    c = c.replace("payment_method", f"{alias}.payment_method").replace(f"{alias}.payment_method = :{alias}.payment_method", f"{alias}.payment_method = :payment_method")
                    c = c.replace("numero_commande", f"{alias}.numero_commande")
                    c = c.replace("shop_paniers.client_id", f"{alias}.client_id")
                    c = c.replace("shop_paniers.id", f"{alias}.id")
                    return c

                def _alias_restau_condition(cond: str, alias: str) -> str:
                    c = cond
                    # Remplacer seulement les colonnes, pas les paramètres bind
                    c = c.replace("created_at", f"{alias}.created_at")
                    c = c.replace("status", f"{alias}.status")
                    # Pour payment_method, remplacer seulement la colonne, pas :payment_method
                    c = c.replace("payment_method", f"{alias}.payment_method").replace(f"{alias}.payment_method = :{alias}.payment_method", f"{alias}.payment_method = :payment_method")
                    c = c.replace("CAST(id AS TEXT)", f"CAST({alias}.id AS TEXT)")
                    c = c.replace("restau_paniers.client_id", f"{alias}.client_id")
                    c = c.replace("restau_paniers.id", f"{alias}.id")
                    return c

                shop_where_paid = " WHERE " + " AND ".join(_alias_shop_condition(c, "p") for c in shop_conditions)
                restau_where_paid = " WHERE " + " AND ".join(_alias_restau_condition(c, "r") for c in restau_conditions)

                # Total payé (shop + restau) filtré
                q_paid = text(f"""
                    SELECT
                      COALESCE((SELECT SUM(sp.amount) FROM shop_payments sp JOIN shop_paniers p ON sp.panier_id = p.id {shop_where_paid}),0)
                      + COALESCE((SELECT SUM(rp.amount) FROM restau_payments rp JOIN restau_paniers r ON rp.panier_id = r.id {restau_where_paid}),0)
                      as total_paid
                """)
                paid_row = session.execute(q_paid, params).fetchone()
                total_paid = float(paid_row.total_paid or 0)

                # Total créances filtré (s'assurer que les créances ne sont jamais négatives)
                shop_where_pp = " WHERE " + " AND ".join(_alias_shop_condition(c, "pp") for c in shop_conditions)
                restau_where_rp = " WHERE " + " AND ".join(_alias_restau_condition(c, "rp") for c in restau_conditions)
                q_creances = text(f"""
                    SELECT COALESCE(SUM(CASE WHEN COALESCE(t.total_final,0) - COALESCE(t.montant_paye,0) > 0 THEN COALESCE(t.total_final,0) - COALESCE(t.montant_paye,0) ELSE 0 END),0) as total_creances
                    FROM (
                        SELECT pp.id, COALESCE(pp.total_final,0) as total_final,
                               (SELECT COALESCE(SUM(sp.amount),0) FROM shop_payments sp WHERE sp.panier_id = pp.id) as montant_paye
                        FROM shop_paniers pp
                        {shop_where_pp}
                        UNION ALL
                        SELECT rp.id, COALESCE(rp.total_final,0) as total_final,
                               (SELECT COALESCE(SUM(rpay.amount),0) FROM restau_payments rpay WHERE rpay.panier_id = rp.id) as montant_paye
                        FROM restau_paniers rp
                        {restau_where_rp}
                    ) t
                    WHERE COALESCE(t.montant_paye,0) < COALESCE(t.total_final,0)
                """)
                cre_row = session.execute(q_creances, params).fetchone()
                total_creances = float(cre_row.total_creances or 0)

                # Nombre de créances filtré
                q_nb_creances = text(f"""
                    SELECT COALESCE(SUM(case when COALESCE(t.montant_paye,0) < COALESCE(t.total_final,0) then 1 else 0 end),0) as nb_creances
                    FROM (
                        SELECT pp.id, COALESCE(pp.total_final,0) as total_final,
                               (SELECT COALESCE(SUM(sp.amount),0) FROM shop_payments sp WHERE sp.panier_id = pp.id) as montant_paye
                        FROM shop_paniers pp
                        {shop_where_pp}
                        UNION ALL
                        SELECT rp.id, COALESCE(rp.total_final,0) as total_final,
                               (SELECT COALESCE(SUM(rpay.amount),0) FROM restau_payments rpay WHERE rpay.panier_id = rp.id) as montant_paye
                        FROM restau_paniers rp
                        {restau_where_rp}
                    ) t
                """)
                nb_cre_row = session.execute(q_nb_creances, params).fetchone()
                nb_creances = int(nb_cre_row.nb_creances) if nb_cre_row and nb_cre_row.nb_creances is not None else 0

                total_unpaid = total_ca - total_paid

                # Nombre total de commandes filtré
                q_nb_cmd = text(f"""
                    SELECT
                      COALESCE((SELECT COUNT(1) FROM shop_paniers {shop_where}),0)
                      + COALESCE((SELECT COUNT(1) FROM restau_paniers {restau_where}),0)
                      as nb_commandes
                """)
                nb_row = session.execute(q_nb_cmd, params).fetchone()
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

    def export_products_summary(self, date_debut, date_fin, include_services: bool = True, module: str = 'boutique') -> str:
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
                # Déterminer l'entrepôt global pour cet export (module -> POS code)
                enterprise_id = SessionManager.get_current_enterprise_id() or None
                # module param can be 'boutique' or 'restaurant' (restau)
                if isinstance(module, str) and module.lower() in ('restaurant', 'restau'):
                    wh_code = 'POS_4'
                else:
                    wh_code = 'POS_2'  # default for boutique exports
                wid = None
                try:
                    r_wh = session.execute(text("SELECT id FROM stock_warehouses WHERE code = :code AND entreprise_id = :eid LIMIT 1"), {'code': wh_code, 'eid': enterprise_id}).fetchone()
                    wid = int(r_wh.id) if r_wh else None
                except Exception:
                    wid = None

                # (La recherche d'inventaire se fera par produit dans la boucle ci-dessous)
                # Rassembler ventes produits (boutique)
                q_products = text("""
                    SELECT cp.id as product_id, cp.name as product_name,
                           COALESCE(SUM(spp.quantity),0) as sold_qty,
                           COALESCE(MAX(cp.price_unit),0) as unit_price
                    FROM shop_paniers_products spp
                    LEFT JOIN shop_paniers p ON spp.panier_id = p.id
                    LEFT JOIN core_products cp ON spp.product_id = cp.id
                    WHERE p.created_at >= :d1 AND p.created_at <= :d2
                    AND LOWER(COALESCE(p.status,'')) NOT IN ('cancelled', 'annule', 'canceled')
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
                    AND LOWER(COALESCE(rp.status,'')) NOT IN ('annule', 'cancelled', 'canceled')
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
                        AND LOWER(COALESCE(p.status,'')) NOT IN ('cancelled', 'annule', 'canceled')
                        GROUP BY ss.id, ss.name
                    """)
                    service_map = session.execute(q_services, {'d1': d1, 'd2': d2}).fetchall()

                # Agréger produits (boutique + restaurant) et tracer ventes par canal
                items = {}
                for r in prod_rows:
                    pid = f"P-{r.product_id}"
                    items[pid] = {
                        'name': r.product_name,
                        'sold': float(r.sold_qty or 0),
                        'sold_boutique': float(r.sold_qty or 0),
                        'sold_restau': 0.0,
                        'unit_price': float(r.unit_price or 0),
                        'product_id': r.product_id,
                        'is_service': False
                    }
                for r in restau_rows:
                    pid = f"P-{r.product_id}"
                    if pid in items:
                        items[pid]['sold'] += float(r.sold_qty or 0)
                        items[pid]['sold_restau'] += float(r.sold_qty or 0)
                    else:
                        items[pid] = {
                            'name': r.product_name,
                            'sold': float(r.sold_qty or 0),
                            'sold_boutique': 0.0,
                            'sold_restau': float(r.sold_qty or 0),
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

                # Préparer enterprise context et cache des entrepôts POS
                enterprise_id = SessionManager.get_current_enterprise_id() or None
                warehouse_cache = {}

                # Pour chaque produit/service, calculer quantités stock via stock_mouvements
                rows_out = []
                for idx, (key, it) in enumerate(items.items(), start=1):
                    if it.get('is_service'):
                        # Pas de stock pour les services -> pas d'initial
                        initial_q = None
                        added_q = 0.0
                        purchases_q = 0.0
                    else:
                        pid = it.get('product_id')
                        # quantité initiale : PREMIER inventaire COMPLETED de la journée (start_day -> end_day)
                        initial_q = None
                        try:
                            start_day = datetime.combine(d1.date(), datetime.min.time())
                            end_day = datetime.combine(d1.date(), datetime.max.time())
                            if wid:
                                r_prod_inv = session.execute(text("""
                                    SELECT sii.counted_stock, si.completed_date
                                    FROM stock_inventaire_item sii
                                    JOIN stock_inventaire si ON sii.inventory_id = si.id
                                    WHERE sii.product_id = :pid
                                      AND si.warehouse_id = :wid
                                      AND si.status = 'COMPLETED'
                                      AND si.completed_date >= :start_day
                                      AND si.completed_date <= :end_day
                                    ORDER BY si.completed_date ASC
                                    LIMIT 1
                                """), {'pid': pid, 'wid': wid, 'start_day': start_day, 'end_day': end_day}).fetchone()
                            else:
                                r_prod_inv = session.execute(text("""
                                    SELECT sii.counted_stock, si.completed_date
                                    FROM stock_inventaire_item sii
                                    JOIN stock_inventaire si ON sii.inventory_id = si.id
                                    WHERE sii.product_id = :pid
                                      AND si.status = 'COMPLETED'
                                      AND si.completed_date >= :start_day
                                      AND si.completed_date <= :end_day
                                    ORDER BY si.completed_date ASC
                                    LIMIT 1
                                """), {'pid': pid, 'start_day': start_day, 'end_day': end_day}).fetchone()
                            if r_prod_inv:
                                initial_q = float(r_prod_inv.counted_stock or 0)
                            else:
                                initial_q = None
                        except Exception:
                            initial_q = None

                        # quantité ajoutée pendant l'intervalle (ENTREE, TRANSFERT, AJUSTEMENT)
                        try:
                            if wid:
                                q_added = text("""
                                    SELECT COALESCE(SUM(CASE
                                        WHEN movement_type = 'ENTREE' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity
                                        WHEN movement_type = 'TRANSFERT' AND destination_warehouse_id = :wid THEN ABS(quantity)
                                        WHEN movement_type = 'AJUSTEMENT' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity
                                        ELSE 0 END),0) as qty
                                    FROM stock_mouvements
                                    WHERE product_id = :pid
                                    AND movement_date >= :d1
                                    AND movement_date <= :d2
                                    AND (warehouse_id = :wid OR destination_warehouse_id = :wid)
                                """)
                                r_added = session.execute(q_added, {'pid': pid, 'd1': d1, 'd2': d2, 'wid': wid}).fetchone()
                            else:
                                q_added = text("SELECT COALESCE(SUM(quantity),0) as qty FROM stock_mouvements WHERE product_id = :pid AND movement_date >= :d1 AND movement_date <= :d2 AND movement_type IN ('ENTREE','TRANSFERT','AJUSTEMENT')")
                                r_added = session.execute(q_added, {'pid': pid, 'd1': d1, 'd2': d2}).fetchone()
                            added_q = float(r_added.qty or 0)
                        except Exception:
                            added_q = 0.0

                        # achats/transferts (ENTREE or TRANSFERT)
                        try:
                            if wid:
                                q_purch = text("""
                                    SELECT COALESCE(SUM(CASE
                                        WHEN movement_type = 'ENTREE' AND (warehouse_id = :wid OR destination_warehouse_id = :wid) THEN quantity
                                        WHEN movement_type = 'TRANSFERT' AND destination_warehouse_id = :wid THEN ABS(quantity)
                                        ELSE 0 END),0) as qty
                                    FROM stock_mouvements
                                    WHERE product_id = :pid
                                    AND movement_date >= :d1
                                    AND movement_date <= :d2
                                    AND (warehouse_id = :wid OR destination_warehouse_id = :wid)
                                """)
                                r_purch = session.execute(q_purch, {'pid': pid, 'd1': d1, 'd2': d2, 'wid': wid}).fetchone()
                            else:
                                q_purch = text("SELECT COALESCE(SUM(quantity),0) as qty FROM stock_mouvements WHERE product_id = :pid AND movement_date >= :d1 AND movement_date <= :d2 AND movement_type IN ('ENTREE','TRANSFERT')")
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
                        'product_id': it.get('product_id'),
                        'service_id': it.get('service_id'),
                        'total_initial_plus_added': total_initial_plus,
                        'reste': reste,
                        'sold': sold,
                        'unit_price': unit_price,
                        'total': total_amount
                    })

                # If at least one product has an initial inventory counted (not None),
                # then set initial_quantity to 0 for other products so the column is shown.
                any_initial = any((r.get('initial_quantity') is not None) for r in rows_out)
                if any_initial:
                    for r in rows_out:
                        if r.get('initial_quantity') is None:
                            r['initial_quantity'] = 0.0

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

    def get_products_summary(self, date_debut, date_fin, include_services: bool = True, module: str = None, pos_id: int = None):
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
                    AND LOWER(COALESCE(p.status,'')) NOT IN ('cancelled', 'annule', 'canceled')
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
                    AND LOWER(COALESCE(rp.status,'')) NOT IN ('annule', 'cancelled', 'canceled')
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
                        AND LOWER(COALESCE(p.status,'')) NOT IN ('cancelled', 'annule', 'canceled')
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

                # Si on a un pos_id (ou un module connu), tenter de résoudre l'entrepôt ciblé
                warehouse_id = None
                try:
                    if pos_id:
                        from ayanna_erp.modules.core.controllers.product_controller import CoreProductController
                        from ayanna_erp.modules.stock.models import StockWarehouse
                        core_ctrl = CoreProductController(pos_id)
                        pos_code = getattr(core_ctrl, 'pos_code', None)
                        if pos_code:
                            wh = session.query(StockWarehouse).filter_by(code=pos_code).first()
                            if wh:
                                warehouse_id = wh.id
                    elif module:
                        # Heuristiques: si module == 'restaurant' -> pos_id 4
                        if module == 'restaurant':
                            from ayanna_erp.modules.core.controllers.product_controller import CoreProductController
                            from ayanna_erp.modules.stock.models import StockWarehouse
                            core_ctrl = CoreProductController(4)
                            pos_code = getattr(core_ctrl, 'pos_code', None)
                            if pos_code:
                                wh = session.query(StockWarehouse).filter_by(code=pos_code).first()
                                if wh:
                                    warehouse_id = wh.id
                except Exception:
                    warehouse_id = None

                # AJOUTER TOUS LES PRODUITS ACTIFS (même non vendus) pour avoir une vue complète
                # Récupérer tous les produits actifs
                q_all_products = text("""
                    SELECT id as product_id, name as product_name, price_unit
                    FROM core_products
                    WHERE is_active = 1
                    ORDER BY name
                """)
                all_products_rows = session.execute(q_all_products).fetchall()
                
                # Ajouter les produits non vendus à items
                for prod in all_products_rows:
                    pid = f"P-{prod.product_id}"
                    if pid not in items:
                        # Produit actif mais non vendu pendant la période
                        items[pid] = {
                            'name': prod.product_name,
                            'sold': 0.0,
                            'unit_price': float(prod.price_unit or 0),
                            'product_id': prod.product_id,
                            'is_service': False
                        }

                # Pour chaque produit/service, calculer quantités stock via stock_mouvements
                rows_out = []
                for idx, (key, it) in enumerate(items.items(), start=1):
                    if it.get('is_service'):
                        # Pas de stock pour les services -> pas d'initial
                        initial_q = None
                        added_q = 0.0
                        adjustments_q = 0.0
                    else:
                        pid = it.get('product_id')
                        # QUANTITÉ INITIALE = PREMIER inventaire COMPLETED de la journée (start_day..end_day)
                        # Si aucun inventaire COMPLETED le jour-même, ne pas calculer initial (None)
                        try:
                            start_day = datetime.combine(d1.date(), datetime.min.time())
                            end_day = datetime.combine(d1.date(), datetime.max.time())
                            if warehouse_id:
                                r_prod_inv = session.execute(text("""
                                    SELECT sii.counted_stock, si.completed_date
                                    FROM stock_inventaire_item sii
                                    JOIN stock_inventaire si ON sii.inventory_id = si.id
                                    WHERE sii.product_id = :pid
                                      AND si.warehouse_id = :wid
                                      AND si.status = 'COMPLETED'
                                      AND si.completed_date >= :start_day
                                      AND si.completed_date <= :end_day
                                    ORDER BY si.completed_date ASC
                                    LIMIT 1
                                """), {'pid': pid, 'wid': warehouse_id, 'start_day': start_day, 'end_day': end_day}).fetchone()
                            else:
                                r_prod_inv = session.execute(text("""
                                    SELECT sii.counted_stock, si.completed_date
                                    FROM stock_inventaire_item sii
                                    JOIN stock_inventaire si ON sii.inventory_id = si.id
                                    WHERE sii.product_id = :pid
                                      AND si.status = 'COMPLETED'
                                      AND si.completed_date >= :start_day
                                      AND si.completed_date <= :end_day
                                    ORDER BY si.completed_date ASC
                                    LIMIT 1
                                """), {'pid': pid, 'start_day': start_day, 'end_day': end_day}).fetchone()
                            if r_prod_inv:
                                initial_q = float(r_prod_inv.counted_stock or 0)
                            else:
                                initial_q = None
                        except Exception as e:
                            print(f"⚠️ Erreur calcul Q initiale pour produit {pid}: {e}")
                            initial_q = None

                        # AJOUTS DU JOUR = ENTREE + TRANSFERT IN (reçus uniquement)
                        # On ne compte que les entrées réelles (achats) et les transferts entrants
                        if warehouse_id:
                            q_added_sql = text("""
                                SELECT COALESCE(SUM(CASE 
                                    WHEN movement_type = 'ENTREE' AND warehouse_id = :wid THEN quantity
                                    WHEN movement_type = 'ENTREE' AND destination_warehouse_id = :wid THEN quantity
                                        WHEN movement_type = 'TRANSFERT' AND destination_warehouse_id = :wid THEN ABS(quantity)
                                    ELSE 0
                                END), 0) as qty
                                FROM stock_mouvements
                                WHERE product_id = :pid 
                                AND movement_date >= :d1 
                                AND movement_date <= :d2
                                AND (warehouse_id = :wid OR destination_warehouse_id = :wid)
                            """)
                        else:
                            q_added_sql = text("""
                                SELECT COALESCE(SUM(CASE 
                                    WHEN movement_type = 'ENTREE' THEN quantity
                                        WHEN movement_type = 'TRANSFERT' THEN 0
                                    ELSE 0
                                END), 0) as qty
                                FROM stock_mouvements
                                WHERE product_id = :pid 
                                AND movement_date >= :d1 
                                AND movement_date <= :d2
                            """)
                        
                        try:
                            params_added = {'pid': pid, 'd1': d1, 'd2': d2}
                            if warehouse_id:
                                params_added['wid'] = warehouse_id
                            r_added = session.execute(q_added_sql, params_added).fetchone()
                            added_q = float(r_added.qty or 0)
                        except Exception as e:
                            print(f"⚠️ Erreur calcul ajouts pour produit {pid}: {e}")
                            added_q = 0.0

                        # AJUSTEMENTS = Corrections d'inventaire (peuvent être + ou -)
                        if warehouse_id:
                            q_adj_sql = text("""
                                SELECT COALESCE(SUM(quantity), 0) as qty
                                FROM stock_mouvements
                                WHERE product_id = :pid 
                                AND movement_date >= :d1 
                                AND movement_date <= :d2
                                AND movement_type = 'AJUSTEMENT'
                                AND (warehouse_id = :wid OR destination_warehouse_id = :wid)
                            """)
                        else:
                            q_adj_sql = text("""
                                SELECT COALESCE(SUM(quantity), 0) as qty
                                FROM stock_mouvements
                                WHERE product_id = :pid 
                                AND movement_date >= :d1 
                                AND movement_date <= :d2
                                AND movement_type = 'AJUSTEMENT'
                            """)
                        
                        try:
                            params_adj = {'pid': pid, 'd1': d1, 'd2': d2}
                            if warehouse_id:
                                params_adj['wid'] = warehouse_id
                            r_adj = session.execute(q_adj_sql, params_adj).fetchone()
                            adjustments_q = float(r_adj.qty or 0)
                        except Exception as e:
                            print(f"⚠️ Erreur calcul ajustements pour produit {pid}: {e}")
                            adjustments_q = 0.0

                    sold = float(it.get('sold', 0.0))
                    # Quantité finale (reste) = Q_initiale + Ajouts - Ventes (par spec)
                    _initial_for_calc = initial_q if initial_q is not None else 0.0
                    final_q = _initial_for_calc + added_q - sold
                    unit_price = float(it.get('unit_price', 0.0))
                    total_amount = sold * unit_price

                    rows_out.append({
                        'no': idx,
                        'name': it['name'],
                        'initial_quantity': initial_q,
                        'quantity_added': added_q,
                        'adjustments': adjustments_q,
                        'product_id': it.get('product_id'),
                        'service_id': it.get('service_id'),
                        'sold': sold,
                        'final_quantity': final_q,
                        'unit_price': unit_price,
                        'total': total_amount
                    })

                return rows_out

        except Exception as e:
            print(f"❌ Erreur get_products_summary: {e}")
            return []

    def get_commande_details(self, commande_id: Union[int, str], module: str = None) -> Optional[Dict[str, Any]]:
        # debug entry removed
        """
        Récupérer les détails d'une commande spécifique

        Args:
            commande_id: ID entier ou numéro de commande (string)
            module: 'boutique' ou 'restaurant' - pour prioriser la bonne table en cas d'ID dupliquées

        Returns:
            Détails de la commande ou None si non trouvée
        """
        # Entry debug removed
        try:
            with self.db_manager.get_session() as session:
                # Si le module est spécifié, chercher directement dans la bonne table
                if module == 'restaurant':
                    try:
                        serveuse_select = "su.name as serveuse_name, scu.name as comptoiriste_name, scu.name as user_name"
                        serveuse_joins = "LEFT JOIN core_users su ON rp.serveuse_id = su.id\n                            LEFT JOIN core_users scu ON rp.user_id = scu.id"
                        client_join = "LEFT JOIN shop_clients sc ON rp.client_id = sc.id"
                        client_name_select = "COALESCE(CONCAT(sc.nom, ' ', COALESCE(sc.prenom, '')), 'Client restaurant') as client_name"

                        r_base = f"""
                            SELECT rp.*, rt.number as table_number, rs.name as salle_name,
                                   {serveuse_select},
                                   {client_name_select}
                            FROM restau_paniers rp
                            LEFT JOIN restau_tables rt ON rp.table_id = rt.id
                            LEFT JOIN restau_salles rs ON rt.salle_id = rs.id
                            {serveuse_joins}
                            {client_join}
                            WHERE rp.id = :commande_id
                        """
                        r_query = text(r_base)
                        r_res = session.execute(r_query, {'commande_id': commande_id}).fetchone()
                    except Exception:
                        r_res = None

                    if r_res:
                        try:
                            if not getattr(r_res, 'created_at', None):
                                now = datetime.now()
                                session.execute(text("UPDATE restau_paniers SET created_at = :now, updated_at = :now WHERE id = :id"), {'now': now, 'id': r_res.id})
                                session.flush()
                                r_res = session.execute(r_query, {'commande_id': commande_id}).fetchone()
                        except Exception:
                            pass

                        r_dict = dict(r_res._asdict())
                        if not r_dict.get('client_name'):
                            r_dict['client_name'] = 'Client restaurant'

                        payments_query = text("""
                            SELECT COALESCE(SUM(amount), 0) as montant_paye
                            FROM restau_payments
                            WHERE panier_id = :panier_id
                        """)
                        payments_row = session.execute(payments_query, {'panier_id': r_dict['id']}).fetchone()
                        r_dict['montant_paye'] = payments_row.montant_paye if payments_row else 0

                        products_query = text("""
                            SELECT rpp.*, cp.name as product_name, rpp.price as unit_price, rpp.total as total_price
                            FROM restau_produit_panier rpp
                            LEFT JOIN core_products cp ON rpp.product_id = cp.id
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
                        r_dict['table_number'] = r_dict.get('table_number')
                        r_dict['salle_name'] = r_dict.get('salle_name')
                        r_dict['serveuse_name'] = r_dict.get('serveuse_name')
                        r_dict['comptoiriste_name'] = r_dict.get('comptoiriste_name')
                        r_dict['module'] = 'restaurant'

                        return r_dict
                
                # Déterminer si c'est un ID entier ou un numéro de commande
                if isinstance(commande_id, str) and not commande_id.isdigit():
                    # C'est un numéro de commande, rechercher par numero_commande
                    # Numero string debug removed
                    query = text("""
                        SELECT
                            sp.*,
                            COALESCE(CONCAT(sc.nom, ' ', COALESCE(sc.prenom, '')), 'Client anonyme') as client_name,
                            COALESCE(cu.name, 'Utilisateur') as user_name
                        FROM shop_paniers sp
                        LEFT JOIN shop_clients sc ON sp.client_id = sc.id
                        LEFT JOIN core_users cu ON sp.user_id = cu.id
                        WHERE sp.numero_commande = :commande_id
                    """)
                else:
                    # C'est un ID entier
                    # ID integer debug removed
                    commande_id_int = int(commande_id)
                    query = text("""
                        SELECT
                            sp.*,
                            COALESCE(CONCAT(sc.nom, ' ', COALESCE(sc.prenom, '')), 'Client anonyme') as client_name,
                            COALESCE(cu.name, 'Utilisateur') as user_name
                        FROM shop_paniers sp
                        LEFT JOIN shop_clients sc ON sp.client_id = sc.id
                        LEFT JOIN core_users cu ON sp.user_id = cu.id
                        WHERE sp.id = :commande_id
                    """)
                    commande_id = commande_id_int

                # Exécuter la requête shop_paniers ; si la table est absente, continuer vers restau
                try:
                    result = session.execute(query, {'commande_id': commande_id})
                    commande = result.fetchone()
                    # Shop paniers debug removed
                except Exception as e:
                    print(f"⚠️ shop_paniers query failed in get_commande_details, will try restaurant: {e}")
                    commande = None

                if not commande:
                    try:
                        serveuse_select = "su.name as serveuse_name, scu.name as comptoiriste_name, scu.name as user_name"
                        serveuse_joins = "LEFT JOIN core_users su ON rp.serveuse_id = su.id\n                            LEFT JOIN core_users scu ON rp.user_id = scu.id"
                        client_join = "LEFT JOIN shop_clients sc ON rp.client_id = sc.id"
                        client_name_select = "COALESCE(CONCAT(sc.nom, ' ', COALESCE(sc.prenom, '')), 'Client restaurant') as client_name"

                        r_base = f"""
                            SELECT rp.*, rt.number as table_number, rs.name as salle_name,
                                   {serveuse_select},
                                   {client_name_select}
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

                        try:
                            if not getattr(r_res, 'created_at', None):
                                now = datetime.now()
                                session.execute(text("UPDATE restau_paniers SET created_at = :now, updated_at = :now WHERE id = :id"), {'now': now, 'id': r_res.id})
                                session.flush()
                                r_res = session.execute(r_query, {'commande_id': commande_id}).fetchone()
                        except Exception:
                            pass

                        r_dict = dict(r_res._asdict())
                        if not r_dict.get('client_name'):
                            r_dict['client_name'] = 'Client restaurant'

                        payments_query = text("""
                            SELECT COALESCE(SUM(amount), 0) as montant_paye
                            FROM restau_payments
                            WHERE panier_id = :panier_id
                        """)
                        payments_row = session.execute(payments_query, {'panier_id': r_dict['id']}).fetchone()
                        r_dict['montant_paye'] = payments_row.montant_paye if payments_row else 0

                        products_query = text("""
                            SELECT rpp.*, cp.name as product_name, rpp.price as unit_price, rpp.total as total_price
                            FROM restau_produit_panier rpp
                            LEFT JOIN core_products cp ON rpp.product_id = cp.id
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
                        r_dict['table_number'] = r_dict.get('table_number')
                        r_dict['salle_name'] = r_dict.get('salle_name')
                        r_dict['serveuse_name'] = r_dict.get('serveuse_name')
                        r_dict['comptoiriste_name'] = r_dict.get('comptoiriste_name')
                        r_dict['module'] = 'restaurant'

                        return r_dict
                    except Exception as e:
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
                    SELECT id, numero_commande, total_final, created_at,
                           (SELECT COALESCE(SUM(amount), 0) FROM shop_payments WHERE panier_id = sp.id) as montant_paye,
                           (SELECT CONCAT(COALESCE(sc.nom, ''), ' ', COALESCE(sc.prenom, '')) FROM shop_clients sc WHERE sc.id = sp.client_id) as client_name
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
                        # Compte caisse du mode de paiement sélectionné
                        pm_row = session.execute(text("""
                            SELECT compte_id FROM core_payment_modes
                            WHERE enterprise_id = 1 AND is_active = 1
                            AND (label = :pm OR code = :pm_lower)
                            LIMIT 1
                        """), {'pm': payment_method, 'pm_lower': (payment_method or '').lower()}).fetchone()
                        compte_caisse_paiement_id = (pm_row[0] if pm_row and pm_row[0] else None) or compte_caisse_id

                        # Créer le journal de paiement
                        numero_commande = commande.numero_commande or f"CMD-{commande.id}"
                        facture_date = getattr(commande, 'created_at', None)
                        facture_date_label = ""
                        if facture_date:
                            if hasattr(facture_date, 'strftime'):
                                facture_date_label = facture_date.strftime('%d/%m/%Y')
                            else:
                                try:
                                    facture_date_label = datetime.fromisoformat(str(facture_date)).strftime('%d/%m/%Y')
                                except Exception:
                                    facture_date_label = str(facture_date)

                        libelle_journal = f"Encaissement antérieur {numero_commande}"
                        if facture_date_label:
                            libelle_journal = f"{libelle_journal} du {facture_date_label}"

                        journal_payment_result = session.execute(text("""
                            INSERT INTO compta_journaux
                            (date_operation, libelle, montant, type_operation, reference, description,
                             enterprise_id, user_id, date_creation, date_modification, valide)
                            VALUES (:date_operation, :libelle, :montant, :type_operation, :reference,
                                    :description, :enterprise_id, :user_id, :date_creation, :date_modification, :valide)
                        """), {
                            'date_operation': datetime.now(),
                            'libelle': libelle_journal,
                            'montant': amount,
                            'type_operation': 'Caisse',
                            'reference': f"PAI-{numero_commande}",
                            'description': f"Paiement commande - {payment_method}",
                            'enterprise_id': 1,  # TODO: Récupérer dynamiquement
                            'user_id': getattr(current_user, 'id', 1),
                            'date_creation': datetime.now(),
                            'date_modification': datetime.now(),
                            'valide': 0
                        })
                        
                        session.flush()
                        journal_payment_id = db.get_last_insert_id(session)
                        
                        # Écriture débit : Compte de caisse du mode de paiement (augmente la trésorerie)
                        session.execute(text("""
                            INSERT INTO compta_ecritures
                            (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                            VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
                        """), {
                            'journal_id': journal_payment_id,
                            'compte_id': compte_caisse_paiement_id,
                            'debit': amount,
                            'credit': 0,
                            'ordre': 1,
                            'libelle': f"Encaissement antérieur {numero_commande} - {payment_method}",
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
                            'libelle': f"Règlement client - {commande.client_name or 'Client anonyme'} - {payment_method}",
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
                q = text("SELECT id, total_final, created_at FROM restau_paniers WHERE id = :pid")
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
                        # Compte caisse du mode de paiement sélectionné
                        pm_row2 = session.execute(text("""
                            SELECT compte_id FROM core_payment_modes
                            WHERE enterprise_id = 1 AND is_active = 1
                            AND (label = :pm OR code = :pm_lower)
                            LIMIT 1
                        """), {'pm': payment_method, 'pm_lower': (payment_method or '').lower()}).fetchone()
                        compte_caisse_paiement_id = (pm_row2[0] if pm_row2 and pm_row2[0] else None) or compte_caisse_id

                        # journal
                        numero = f"-{panier_id}"
                        facture_date = getattr(res, 'created_at', None)
                        facture_date_label = ""
                        if facture_date:
                            if hasattr(facture_date, 'strftime'):
                                facture_date_label = facture_date.strftime('%d/%m/%Y')
                            else:
                                try:
                                    facture_date_label = datetime.fromisoformat(str(facture_date)).strftime('%d/%m/%Y')
                                except Exception:
                                    facture_date_label = str(facture_date)

                        libelle_journal = f"Encaissement antérieur Facture {numero}"
                        if facture_date_label:
                            libelle_journal = f"{libelle_journal} du {facture_date_label}"

                        session.execute(text("""
                            INSERT INTO compta_journaux
                            (date_operation, libelle, montant, type_operation, reference, description, enterprise_id, user_id, date_creation, date_modification, valide)
                            VALUES (:date_operation, :libelle, :montant, :type_operation, :reference, :description, :enterprise_id, :user_id, :date_creation, :date_modification, :valide)
                        """), {
                            'date_operation': datetime.now(),
                            'libelle': libelle_journal,
                            'montant': amount,
                            'type_operation': 'Caisse',
                            'reference': f"PAI-{numero}",
                            'description': f"Paiement - {payment_method}",
                            'enterprise_id': 1,
                            'user_id': getattr(current_user, 'id', 1),
                            'date_creation': datetime.now(),
                            'date_modification': datetime.now(),
                            'valide': 0
                        })
                        session.flush()
                        journal_id = db.get_last_insert_id(session)
                        session.execute(text("""
                            INSERT INTO compta_ecritures (journal_id, compte_comptable_id, debit, credit, ordre, libelle, date_creation)
                            VALUES (:journal_id, :compte_id, :debit, :credit, :ordre, :libelle, :date_creation)
                        """), {
                            'journal_id': journal_id,
                            'compte_id': compte_caisse_paiement_id,
                            'debit': amount,
                            'credit': 0,
                            'ordre': 1,
                            'libelle': libelle_journal,
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
        Annuler une commande du restaurant en mettant à jour le statut du panier restau
        et en remettant le stock des produits.
        """
        try:
            with self.db_manager.session_scope() as session:
                res = session.execute(text("SELECT id, status FROM restau_paniers WHERE id = :pid"), {'pid': panier_id}).fetchone()
                if not res:
                    return False, "Panier restaurant introuvable"
                current_status = (res.status or '').lower()
                if current_status in ('cancelled', 'annule', 'annulé'):
                    return False, "Le panier est déjà annulé"

                # Récupérer les produits du panier pour remettre le stock
                produits = session.execute(text("""
                    SELECT product_id, quantity
                    FROM restau_produit_panier
                    WHERE panier_id = :pid
                """), {'pid': panier_id}).fetchall()

                # Trouver l'entrepôt restaurant (POS_4 ou autre)
                warehouse_id = None
                try:
                    from ayanna_erp.modules.stock.helpers.pos_warehouse_helper import POSWarehouseHelper
                    # Essayer de trouver l'entrepôt du module restaurant
                    warehouse_result = session.execute(text("""
                        SELECT sw.id FROM stock_warehouses sw
                        WHERE sw.name LIKE '%Restaurant%' AND sw.is_active = 1
                        LIMIT 1
                    """))
                    warehouse_row = warehouse_result.fetchone()
                    if warehouse_row:
                        warehouse_id = warehouse_row[0]
                except Exception as e:
                    print(f"⚠️ Erreur recherche entrepôt restaurant: {e}")

                # Fallback sur POS_4
                if not warehouse_id:
                    warehouse_result = session.execute(text("""
                        SELECT id FROM stock_warehouses
                        WHERE code = 'POS_4' AND is_active = 1
                        LIMIT 1
                    """))
                    warehouse_row = warehouse_result.fetchone()
                    if warehouse_row:
                        warehouse_id = warehouse_row[0]

                # Si toujours pas trouvé, chercher n'importe quel entrepôt de type Point de Vente
                if not warehouse_id:
                    warehouse_result = session.execute(text("""
                        SELECT id FROM stock_warehouses
                        WHERE type = 'Point de Vente' AND is_active = 1
                        LIMIT 1
                    """))
                    warehouse_row = warehouse_result.fetchone()
                    if warehouse_row:
                        warehouse_id = warehouse_row[0]

                # Remettre le stock pour chaque produit
                if warehouse_id and produits:
                    from datetime import datetime
                    for produit in produits:
                        product_id = produit.product_id
                        quantity_to_return = produit.quantity

                        # Récupérer le stock actuel
                        stock_row = session.execute(text("""
                            SELECT quantity FROM stock_produits_entrepot
                            WHERE product_id = :product_id AND warehouse_id = :warehouse_id
                            LIMIT 1
                        """), {'product_id': product_id, 'warehouse_id': warehouse_id}).fetchone()

                        current_stock = float(stock_row[0]) if stock_row else 0
                        new_stock = current_stock + float(quantity_to_return)

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

                        # Créer le mouvement de stock d'annulation
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
                            'movement_type': 'ANNULATION',
                            'quantity': quantity_to_return,
                            'unit_cost': 0,
                            'total_cost': 0,
                            'destination_warehouse_id': warehouse_id,
                            'reference': f"ANN-REST-{panier_id}",
                            'description': f"Annulation commande restaurant - {panier_id}",
                            'user_id': current_user.id if current_user else 1,
                            'movement_date': datetime.now(),
                            'created_at': datetime.now()
                        })

                        print(f"📦 Stock remis (Restaurant) - Produit {product_id}: {current_stock} → {new_stock}")

                # Annulation automatique de tous les journaux liés à la commande restaurant (libellé ou référence contient le panier_id)
                journaux = session.execute(text("""
                    SELECT id, date_operation, libelle, montant, type_operation, reference, description, enterprise_id, user_id
                    FROM compta_journaux
                    WHERE libelle LIKE :cmd OR reference LIKE :cmd
                """), {'cmd': f'%{panier_id}%'}).fetchall()

                for journal in journaux:
                    journal_id = journal.id
                    # Supprimer les écritures associées au journal
                    session.execute(text("DELETE FROM compta_ecritures WHERE journal_id = :jid"), {'jid': journal_id})
                    # Supprimer le journal lui-même
                    session.execute(text("DELETE FROM compta_journaux WHERE id = :jid"), {'jid': journal_id})

                # Mettre à jour le statut du panier
                session.execute(text("UPDATE restau_paniers SET status = :st WHERE id = :pid"), {'st': 'cancelled', 'pid': panier_id})
                return True, "Commande restaurant annulée avec succès et stock remis."
        except Exception as e:
            print(f"❌ Erreur cancel_restaurant_commande: {e}")
            return False, f"Erreur lors de l'annulation: {e}"