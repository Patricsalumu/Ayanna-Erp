# -*- coding: utf-8 -*-
"""
Contrôleur pour la gestion des commandes du module Boutique
Gère la logique métier des commandes : récupération, statistiques, filtrage, export
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional, Union
from sqlalchemy import text
from ayanna_erp.database.database_manager import DatabaseManager


class CommandeController:
    """Contrôleur pour la gestion des commandes"""

    def __init__(self):
        self.db_manager = DatabaseManager()

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
            with self.db_manager.get_session() as session:
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
                            JOIN shop_services ss ON sps.service_id = ss.id
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
                    WHERE sp.status = 'completed'
                """

                conditions = []
                params = {}

                # Filtrage par dates
                if date_debut:
                    conditions.append("sp.created_at >= :date_debut")
                    params['date_debut'] = date_debut
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
                    base_query += " AND " + " AND ".join(conditions)

                # Tri et limite
                base_query += " ORDER BY sp.created_at DESC LIMIT :limit"
                params['limit'] = limit

                query = text(base_query)
                result = session.execute(query, params)
                commandes = result.fetchall()

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
        if not commandes:
            return {
                'total_ca': 0,
                'total_creances': 0,
                'commandes_aujourd_hui': 0,
                'nb_commandes': 0,
                'panier_moyen': 0
            }

        total_ca = sum(c['total_final'] for c in commandes)
        total_creances = sum(c['total_final'] for c in commandes if c['payment_method'] == 'Crédit')

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
        panier_moyen = total_ca / nb_commandes if nb_commandes > 0 else 0

        return {
            'total_ca': total_ca,
            'total_creances': total_creances,
            'commandes_aujourd_hui': commandes_aujourd_hui,
            'nb_commandes': nb_commandes,
            'panier_moyen': panier_moyen
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
            return """
Période: Derniers 30 jours
Commandes: 0
Chiffre d'affaires: 0 FC
Créances: 0 FC
Panier moyen: 0 FC
            """

        return f"""
Période: {date_debut.toString('dd/MM/yyyy')} - {date_fin.toString('dd/MM/yyyy')}
Commandes: {stats['nb_commandes']}
Chiffre d'affaires: {stats['total_ca']:.0f} FC
Créances: {stats['total_creances']:.0f} FC
Panier moyen: {stats['panier_moyen']:.0f} FC
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

    def get_commande_details(self, commande_id: Union[int, str]) -> Optional[Dict[str, Any]]:
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

                result = session.execute(query, {'commande_id': commande_id})
                commande = result.fetchone()

                if not commande:
                    return None

                commande_dict = dict(commande._asdict())

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

                products_result = session.execute(products_query, {'commande_id': commande_id})
                products = products_result.fetchall()

                # Récupérer les services de la commande
                services_query = text("""
                    SELECT
                        sps.*,
                        ss.name as service_name,
                        sps.price_unit as unit_price
                    FROM shop_paniers_services sps
                    LEFT JOIN shop_services ss ON sps.service_id = ss.id
                    WHERE sps.panier_id = :commande_id
                """)

                services_result = session.execute(services_query, {'commande_id': commande_id})
                services = services_result.fetchall()

                # Construire le détail des produits/services
                produits_detail = []
                for product in products:
                    product_dict = dict(product._asdict())
                    produits_detail.append(
                        f"• {product_dict.get('product_name', 'Produit inconnu')} - {product_dict.get('quantity', 0)} x {product_dict.get('unit_price', 0):.0f} FC = {product_dict.get('total_price', 0):.0f} FC"
                    )

                for service in services:
                    service_dict = dict(service._asdict())
                    produits_detail.append(
                        f"• {service_dict.get('service_name', 'Service inconnu')} - {service_dict.get('quantity', 0)} x {service_dict.get('unit_price', 0):.0f} FC = {service_dict.get('total_price', 0):.0f} FC"
                    )

                commande_dict['produits_detail'] = '\n'.join(produits_detail) if produits_detail else 'Aucun produit/service'

                return commande_dict

        except Exception as e:
            print(f"❌ Erreur get_commande_details: {e}")
            return None