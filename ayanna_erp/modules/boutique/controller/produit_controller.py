from ayanna_erp.modules.core.controllers.product_controller import CoreProductController
from sqlalchemy import text, desc, or_
from datetime import datetime

class ProduitController(CoreProductController):
    """
    Contrôleur pour la gestion des produits de la boutique
    Hérite du contrôleur centralisé CoreProductController
    """
    def __init__(self, pos_id: int):
        super().__init__(pos_id)  # Utilise l'entrepôt POS_2 pour la boutique

    def get_product_stock_total(self, session, product_id: int) -> float:
        """Méthode spécifique à la boutique pour la compatibilité"""
        try:
            from ayanna_erp.modules.stock.models import StockProduitEntrepot, StockWarehouse
            # déterminer l'entrepôt via self.pos_code
            warehouse_code = getattr(self, 'pos_code', 'POS_2')
            pos_warehouse = session.query(StockWarehouse).filter_by(code=warehouse_code).first()
            if not pos_warehouse:
                return 0.0
            stock_entry = session.query(StockProduitEntrepot).filter_by(product_id=product_id, warehouse_id=pos_warehouse.id).first()
            return float(stock_entry.quantity) if stock_entry else 0.0
        except Exception:
            return 0.0

    def get_product_sales_statistics(self, session, product_id: int) -> dict:
        """
        Retourne les statistiques des ventes pour un produit

        Args:
            session: Session de base de données
            product_id: ID du produit

        Returns:
            Dictionnaire contenant :
            - sales_count: Nombre de fois que le produit a été vendu
            - total_quantity_sold: Quantité totale vendue
            - last_sale_date: Date de dernière vente
            - total_revenue: Chiffre d'affaires généré (quantité * prix_vente)
            - total_profit: Bénéfice généré (CA - coût total d'achat)
        """
        try:
            # Récupérer les informations du produit (prix de vente et coût)
            product = self.get_product_by_id(session, product_id)
            if not product:
                return {
                    'sales_count': 0,
                    'total_quantity_sold': 0,
                    'last_sale_date': None,
                    'total_revenue': 0,
                    'total_profit': 0
                }

            # Calculer les statistiques de vente avec une requête SQL
            sales_query = text("""
                SELECT
                    COUNT(*) as sales_count,
                    COALESCE(SUM(spp.quantity), 0) as total_quantity,
                    MAX(sp.created_at) as last_sale_date
                FROM shop_paniers_products spp
                JOIN shop_paniers sp ON spp.panier_id = sp.id
                WHERE spp.product_id = :product_id
                AND sp.status != 'Annulle' 
                AND sp.pos_id = :pos_id
            """)

            result = session.execute(sales_query, {'product_id': product_id, 'pos_id': self.pos_id})
            sales_stats = result.fetchone()

            sales_count = sales_stats.sales_count or 0
            total_quantity_sold = float(sales_stats.total_quantity or 0)
            last_sale_date = sales_stats.last_sale_date

            # Calculer le chiffre d'affaires (quantité * prix_vente)
            total_revenue = total_quantity_sold * float(product.price_unit)

            # Calculer le bénéfice (CA - coût total d'achat)
            total_cost = total_quantity_sold * float(product.cost or 0)
            total_profit = total_revenue - total_cost

            return {
                'sales_count': sales_count,
                'total_quantity_sold': total_quantity_sold,
                'last_sale_date': last_sale_date,
                'total_revenue': total_revenue,
                'total_profit': total_profit
            }

        except Exception as e:
            print(f"Erreur lors de la récupération des statistiques de vente: {e}")
            return {
                'sales_count': 0,
                'total_quantity_sold': 0,
                'last_sale_date': None,
                'total_revenue': 0,
                'total_profit': 0
            }

    def get_product_stock_details(self, session, product_id: int) -> dict:
        """
        Retourne les détails de stock pour un produit dans le POS_2

        Args:
            session: Session de base de données
            product_id: ID du produit

        Returns:
            Dictionnaire contenant :
            - current_stock: Quantité en stock disponible
            - min_stock_level: Niveau de stock minimum
            - warehouse_name: Nom de l'entrepôt
            - recent_movements: Liste des derniers mouvements de stock
        """
        try:
            from ayanna_erp.modules.stock.models import StockProduitEntrepot, StockWarehouse, StockMovement
            from sqlalchemy import desc

            # Récupérer l'entrepôt correspondant au POS (utilise self.pos_code défini dans CoreProductController)
            warehouse_code = getattr(self, 'pos_code', 'POS_2')
            pos_warehouse = session.query(StockWarehouse).filter_by(code=warehouse_code).first()

            if not pos_warehouse:
                return {
                    'current_stock': 0,
                    'min_stock_level': 0,
                    'warehouse_name': 'Entrepôt POS_2 introuvable',
                    'recent_movements': []
                }

            # Récupérer les informations de stock actuel
            stock_entry = session.query(StockProduitEntrepot).filter_by(
                product_id=product_id,
                warehouse_id=pos_warehouse.id
            ).first()

            current_stock = float(stock_entry.quantity) if stock_entry else 0
            min_stock_level = float(stock_entry.min_stock_level) if stock_entry else 0
            warehouse_name = pos_warehouse.name

            # Récupérer les derniers mouvements de stock (10 plus récents)
            # Mouvements impliquant l'entrepôt du POS en source ou destination
            from sqlalchemy import or_
            recent_movements = session.query(StockMovement)\
                .filter(
                    StockMovement.product_id == product_id,
                    or_(
                        StockMovement.warehouse_id == pos_warehouse.id,
                        StockMovement.destination_warehouse_id == pos_warehouse.id
                    )
                )\
                .order_by(desc(StockMovement.created_at))\
                .limit(10)\
                .all()

            # Formater les mouvements avec la logique expliquée
            movements_list = []
            processed_movement_ids = set()  # Pour éviter les doublons
            
            for movement in recent_movements:
                # Éviter les doublons
                if movement.id in processed_movement_ids:
                    continue
                processed_movement_ids.add(movement.id)
                
                # Lire le type tel qu'enregistré en base (texte original)
                movement_type_db = movement.movement_type or ''
                # Utiliser une version en MAJUSCULE pour les comparaisons internes
                movement_type_upper = movement_type_db.upper()
                # Cas: entrée vers l'entrepôt (destination = pos)
                if getattr(movement, 'destination_warehouse_id', None) == pos_warehouse.id and (getattr(movement, 'warehouse_id', None) is None or movement.warehouse_id != pos_warehouse.id):
                    normalized_type = 'ENTREE'
                    source_warehouse = session.query(StockWarehouse).get(movement.warehouse_id) if movement.warehouse_id else None
                    source_display = f"Depuis {source_warehouse.name}" if source_warehouse else "Achat/Réception"
                    quantity_display = f"+{float(movement.quantity):.2f}"
                # Cas: sortie depuis l'entrepôt (source = pos)
                elif getattr(movement, 'warehouse_id', None) == pos_warehouse.id and (getattr(movement, 'destination_warehouse_id', None) is None or movement.destination_warehouse_id != pos_warehouse.id):
                    normalized_type = 'SORTIE'
                    dest_warehouse = session.query(StockWarehouse).get(movement.destination_warehouse_id) if movement.destination_warehouse_id else None
                    source_display = f"Vers {dest_warehouse.name}" if dest_warehouse else "Vente/Sortie"
                    quantity_display = f"-{float(movement.quantity):.2f}"
                # Cas: transfert — déterminer sens par rapport à l'entrepôt
                elif getattr(movement, 'movement_type', None) == 'TRANSFERT':
                    if movement.warehouse_id == pos_warehouse.id:
                        normalized_type = 'SORTIE'
                        dest_warehouse = session.query(StockWarehouse).get(movement.destination_warehouse_id)
                        source_display = f"Vers {dest_warehouse.name if dest_warehouse else 'Entrepôt inconnu'}"
                        quantity_display = f"-{float(movement.quantity):.2f}"
                    else:
                        normalized_type = 'ENTREE'
                        source_warehouse = session.query(StockWarehouse).get(movement.warehouse_id)
                        source_display = f"Depuis {source_warehouse.name if source_warehouse else 'Entrepôt inconnu'}"
                        quantity_display = f"+{float(movement.quantity):.2f}"
                else:
                    # Autres types: décider par signe de la quantité ou par type original
                    try:
                        q = float(movement.quantity)
                        normalized_type = 'ENTREE' if q > 0 else 'SORTIE'
                        quantity_display = f"{q:+.2f}"
                        source_display = movement.reference or (movement.description or 'Non spécifié')
                    except Exception:
                        normalized_type = 'ENTREE'
                        quantity_display = f"{float(movement.quantity):+.2f}"
                        source_display = movement.reference or (movement.description or 'Non spécifié')

                movements_list.append({
                    'date': movement.created_at,
                    'quantity': quantity_display,
                    # Afficher textuellement la valeur stockée en base dans la colonne movement_type
                    'movement_type': movement_type_db,
                    # Garder aussi une version normalisée si besoin pour tri/logique
                    'normalized_type': normalized_type,
                    'source': source_display,
                    'reference': movement.reference or '',
                    'notes': movement.description or ''
                })

            # Trier les mouvements par date décroissante (plus récent en premier)
            movements_list.sort(key=lambda x: x['date'] or datetime.min, reverse=True)

            return {
                'current_stock': current_stock,
                'min_stock_level': min_stock_level,
                'warehouse_name': warehouse_name,
                'recent_movements': movements_list
            }

        except Exception as e:
            print(f"Erreur lors de la récupération des détails de stock: {e}")
            return {
                'current_stock': 0,
                'min_stock_level': 0,
                'warehouse_name': 'Erreur',
                'recent_movements': []
            }