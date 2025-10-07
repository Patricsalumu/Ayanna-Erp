"""
Contrôleur pour la génération de rapports de stock
Compatible avec la nouvelle architecture stock (4 tables)
"""

from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, case, text

from ayanna_erp.database.database_manager import DatabaseManager


class RapportController:
    """Contrôleur pour la génération de rapports de stock"""
    
    def __init__(self, entreprise_id: int):
        """
        Initialisation du contrôleur
        
        Args:
            entreprise_id: ID de l'entreprise
        """
        self.entreprise_id = entreprise_id
        self.db_manager = DatabaseManager()

    def get_stock_valuation_report(self, warehouse_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Générer un rapport de valorisation du stock
        
        Args:
            warehouse_id: ID de l'entrepôt (optionnel, sinon global)
            
        Returns:
            Rapport de valorisation
        """
        try:
            with self.db_manager.get_session() as session:
                if warehouse_id:
                    # Rapport pour un entrepôt spécifique
                    result = session.execute(text("""
                        SELECT 
                            spe.product_id,
                            p.name as product_name,
                            p.code as product_code,
                            spe.quantity,
                            spe.unit_cost,
                            spe.total_cost,
                            sw.name as warehouse_name
                        FROM stock_produits_entrepot spe
                        JOIN stock_warehouses sw ON spe.warehouse_id = sw.id
                        LEFT JOIN shop_products p ON spe.product_id = p.id
                        WHERE spe.warehouse_id = :warehouse_id
                        AND sw.entreprise_id = :entreprise_id
                        ORDER BY spe.total_cost DESC
                    """), {
                        "warehouse_id": warehouse_id,
                        "entreprise_id": self.entreprise_id
                    })
                else:
                    # Rapport global
                    result = session.execute(text("""
                        SELECT 
                            spe.product_id,
                            p.name as product_name,
                            p.code as product_code,
                            SUM(spe.quantity) as total_quantity,
                            AVG(spe.unit_cost) as avg_unit_cost,
                            SUM(spe.total_cost) as total_value
                        FROM stock_produits_entrepot spe
                        JOIN stock_warehouses sw ON spe.warehouse_id = sw.id
                        LEFT JOIN shop_products p ON spe.product_id = p.id
                        WHERE sw.entreprise_id = :entreprise_id
                        GROUP BY spe.product_id, p.name, p.code
                        ORDER BY total_value DESC
                    """), {"entreprise_id": self.entreprise_id})
                
                products = []
                total_value = 0
                
                for row in result:
                    if warehouse_id:
                        quantity = float(row[3]) if row[3] else 0
                        unit_cost = float(row[4]) if row[4] else 0
                        total_cost = float(row[5]) if row[5] else 0
                        
                        products.append({
                            'product_id': row[0],
                            'product_name': row[1] or f"Produit {row[0]}",
                            'product_code': row[2] or "",
                            'quantity': quantity,
                            'unit_cost': unit_cost,
                            'total_value': total_cost,
                            'warehouse_name': row[6]
                        })
                        total_value += total_cost
                    else:
                        quantity = float(row[3]) if row[3] else 0
                        unit_cost = float(row[4]) if row[4] else 0
                        total_cost = float(row[5]) if row[5] else 0
                        
                        products.append({
                            'product_id': row[0],
                            'product_name': row[1] or f"Produit {row[0]}",
                            'product_code': row[2] or "",
                            'quantity': quantity,
                            'unit_cost': unit_cost,
                            'total_value': total_cost
                        })
                        total_value += total_cost
                
                return {
                    'products': products,
                    'total_value': total_value,
                    'product_count': len(products),
                    'warehouse_id': warehouse_id,
                    'generated_at': datetime.now()
                }
                
        except Exception as e:
            print(f"Erreur lors de la génération du rapport de valorisation: {e}")
            return {
                'products': [],
                'total_value': 0,
                'product_count': 0,
                'warehouse_id': warehouse_id,
                'generated_at': datetime.now()
            }

    def get_movement_report(self, start_date: date, end_date: date, 
                           warehouse_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Générer un rapport des mouvements de stock
        
        Args:
            start_date: Date de début
            end_date: Date de fin
            warehouse_id: ID de l'entrepôt (optionnel)
            
        Returns:
            Rapport des mouvements
        """
        try:
            # TODO: Implémentation avec la table stock_mouvements
            # Pour l'instant, retournons un rapport vide
            return {
                'movements': [],
                'total_entries': 0,
                'total_exits': 0,
                'start_date': start_date,
                'end_date': end_date,
                'warehouse_id': warehouse_id,
                'generated_at': datetime.now()
            }
                
        except Exception as e:
            print(f"Erreur lors de la génération du rapport de mouvements: {e}")
            return {
                'movements': [],
                'total_entries': 0,
                'total_exits': 0,
                'start_date': start_date,
                'end_date': end_date,
                'warehouse_id': warehouse_id,
                'generated_at': datetime.now()
            }

    def get_inventory_summary(self) -> Dict[str, Any]:
        """
        Générer un résumé général des stocks
        
        Returns:
            Résumé des stocks par entrepôt
        """
        try:
            with self.db_manager.get_session() as session:
                # Résumé par entrepôt
                result = session.execute(text("""
                    SELECT 
                        sw.id,
                        sw.name,
                        sw.type,
                        COUNT(DISTINCT spe.product_id) as product_count,
                        SUM(spe.quantity) as total_quantity,
                        SUM(spe.total_cost) as total_value,
                        AVG(spe.unit_cost) as avg_unit_cost
                    FROM stock_warehouses sw
                    LEFT JOIN stock_produits_entrepot spe ON sw.id = spe.warehouse_id
                    WHERE sw.entreprise_id = :entreprise_id
                    AND sw.is_active = 1
                    GROUP BY sw.id, sw.name, sw.type
                    ORDER BY sw.name
                """), {"entreprise_id": self.entreprise_id})
                
                warehouses = []
                global_stats = {
                    'total_warehouses': 0,
                    'total_products': 0,
                    'total_quantity': 0,
                    'total_value': 0
                }
                
                for row in result:
                    product_count = row[3] if row[3] else 0
                    total_quantity = float(row[4]) if row[4] else 0
                    total_value = float(row[5]) if row[5] else 0
                    avg_cost = float(row[6]) if row[6] else 0
                    
                    warehouses.append({
                        'warehouse_id': row[0],
                        'warehouse_name': row[1],
                        'warehouse_type': row[2],
                        'product_count': product_count,
                        'total_quantity': total_quantity,
                        'total_value': total_value,
                        'avg_unit_cost': avg_cost
                    })
                    
                    global_stats['total_warehouses'] += 1
                    global_stats['total_products'] += product_count
                    global_stats['total_quantity'] += total_quantity
                    global_stats['total_value'] += total_value
                
                return {
                    'warehouses': warehouses,
                    'global_stats': global_stats,
                    'generated_at': datetime.now()
                }
                
        except Exception as e:
            print(f"Erreur lors de la génération du résumé: {e}")
            return {
                'warehouses': [],
                'global_stats': {
                    'total_warehouses': 0,
                    'total_products': 0,
                    'total_quantity': 0,
                    'total_value': 0
                },
                'generated_at': datetime.now()
            }

    def export_stock_to_excel(self, warehouse_id: Optional[int] = None) -> Optional[str]:
        """
        Exporter les données de stock vers Excel
        
        Args:
            warehouse_id: ID de l'entrepôt (optionnel)
            
        Returns:
            Chemin du fichier Excel généré ou None si erreur
        """
        try:
            # TODO: Implémentation de l'export Excel
            # Pour l'instant, retournons None
            return None
                
        except Exception as e:
            print(f"Erreur lors de l'export Excel: {e}")
            return None