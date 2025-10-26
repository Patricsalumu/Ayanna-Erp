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
        stock_info = self.get_product_stock_info(product_id)
        return stock_info['total_stock']

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

            # Récupérer l'entrepôt POS_2
            pos_warehouse = session.query(StockWarehouse).filter_by(code='POS_2').first()

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
            # Mouvements où l'entrepôt POS_2 est soit source soit destination
            from sqlalchemy import or_
            recent_movements = session.query(StockMovement)\
                .filter(
                    StockMovement.product_id == product_id,
                    or_(
                        StockMovement.warehouse_id == pos_warehouse.id,  # Sorties de POS_2 (ventes)
                        StockMovement.destination_warehouse_id == pos_warehouse.id  # Entrées vers POS_2 (achats/réceptions)
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
                
                # Déterminer le type de mouvement basé sur les entrepôts source/destination
                if movement.warehouse_id ==pos_warehouse.id and movement.destination_warehouse_id == None:
                    # Achat/réception : warehouse_id null, destination_warehouse_id = POS_2
                    movement_type_display = "ACHAT"
                    source_display = ""
                    quantity_display = f"+{float(movement.quantity):.2f}"
                elif movement.warehouse_id == pos_warehouse.id and movement.destination_warehouse_id ==pos_warehouse.id:
                    # Vente : warehouse_id = POS_2, destination_warehouse_id null
                    movement_type_display = "VENTE"
                    source_display = ""
                    quantity_display = f"{float(movement.quantity):.2f}"
                elif movement.movement_type =='TRANSFERT':
                    # Transfert entre entrepôts
                    if movement.warehouse_id == pos_warehouse.id:
                        # Sortie de POS_2 vers un autre entrepôt
                        dest_warehouse = session.query(StockWarehouse).get(movement.destination_warehouse_id)
                        movement_type_display = "TRANSFERT"
                        source_display = f"Vers {dest_warehouse.name if dest_warehouse else 'Entrepôt inconnu'}"
                        quantity_display = f"{float(movement.quantity):.2f}"
                    else:
                        # Entrée vers POS_2 depuis un autre entrepôt
                        source_warehouse = session.query(StockWarehouse).get(movement.warehouse_id)
                        movement_type_display = "TRANSFERT ENTRÉE"
                        source_display = f"Depuis {source_warehouse.name if source_warehouse else 'Entrepôt inconnu'}"
                        quantity_display = f"+{float(movement.quantity):.2f}"
                else:
                    # Autre type de mouvement
                    movement_type_display = movement.movement_type or "INCONNU"
                    source_display = movement.reference or "Non spécifié"
                    quantity_display = f"{float(movement.quantity):+.2f}"

                movements_list.append({
                    'date': movement.created_at,
                    'quantity': quantity_display,
                    'movement_type': movement_type_display,
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