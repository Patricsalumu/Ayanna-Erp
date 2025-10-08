"""
Contrôleur pour la gestion des inventaires
Compatible avec la nouvelle architecture stock (4 tables)
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text

from ayanna_erp.database.database_manager import DatabaseManager


class InventaireController:
    """Contrôleur pour la gestion des inventaires"""
    
    def __init__(self, entreprise_id: int):
        """
        Initialisation du contrôleur
        
        Args:
            entreprise_id: ID de l'entreprise
        """
        self.entreprise_id = entreprise_id
        self.db_manager = DatabaseManager()

    def get_warehouses_for_inventory(self) -> List[Dict[str, Any]]:
        """
        Récupérer les entrepôts disponibles pour l'inventaire
        
        Returns:
            Liste des entrepôts actifs
        """
        try:
            with self.db_manager.get_session() as session:
                result = session.execute(text("""
                    SELECT 
                        id,
                        name,
                        code,
                        type,
                        address,
                        is_active,
                        is_default
                    FROM stock_warehouses 
                    WHERE entreprise_id = :entreprise_id 
                    AND is_active = 1
                    ORDER BY name
                """), {"entreprise_id": self.entreprise_id})
                
                warehouses = []
                for row in result:
                    warehouses.append({
                        'id': row[0],
                        'name': row[1],
                        'code': row[2],
                        'type': row[3],
                        'address': row[4],
                        'is_active': bool(row[5]),
                        'is_default': bool(row[6])
                    })
                
                return warehouses
                
        except Exception as e:
            print(f"Erreur lors de la récupération des entrepôts: {e}")
            return []

    def get_products_for_inventory(self, warehouse_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Récupérer les produits pour l'inventaire
        
        Args:
            warehouse_id: ID de l'entrepôt (optionnel, sinon tous)
            
        Returns:
            Liste des produits avec leurs stocks actuels
        """
        try:
            with self.db_manager.get_session() as session:
                if warehouse_id:
                    # Produits d'un entrepôt spécifique
                    result = session.execute(text("""
                        SELECT 
                            spe.product_id,
                            p.name as product_name,
                            p.code as product_code,
                            spe.quantity,
                            spe.reserved_quantity,
                            spe.unit_cost,
                            spe.min_stock_level,
                            sw.name as warehouse_name,
                            sw.id as warehouse_id
                        FROM stock_produits_entrepot spe
                        JOIN stock_warehouses sw ON spe.warehouse_id = sw.id
                        LEFT JOIN core_products p ON spe.product_id = p.id
                        WHERE spe.warehouse_id = :warehouse_id
                        AND sw.entreprise_id = :entreprise_id
                        ORDER BY p.name
                    """), {
                        "warehouse_id": warehouse_id,
                        "entreprise_id": self.entreprise_id
                    })
                else:
                    # Tous les produits de tous les entrepôts
                    result = session.execute(text("""
                        SELECT 
                            spe.product_id,
                            p.name as product_name,
                            p.code as product_code,
                            SUM(spe.quantity) as total_quantity,
                            SUM(spe.reserved_quantity) as total_reserved,
                            AVG(spe.unit_cost) as avg_unit_cost,
                            MIN(spe.min_stock_level) as min_stock_level,
                            COUNT(DISTINCT sw.id) as warehouse_count
                        FROM stock_produits_entrepot spe
                        JOIN stock_warehouses sw ON spe.warehouse_id = sw.id
                        LEFT JOIN core_products p ON spe.product_id = p.id
                        WHERE sw.entreprise_id = :entreprise_id
                        GROUP BY spe.product_id, p.name, p.code
                        ORDER BY p.name
                    """), {"entreprise_id": self.entreprise_id})
                
                products = []
                for row in result:
                    if warehouse_id:
                        products.append({
                            'product_id': row[0],
                            'product_name': row[1] or f"Produit {row[0]}",
                            'product_code': row[2] or "",
                            'current_quantity': float(row[3]) if row[3] else 0,
                            'reserved_quantity': float(row[4]) if row[4] else 0,
                            'unit_cost': float(row[5]) if row[5] else 0,
                            'min_stock_level': float(row[6]) if row[6] else 0,
                            'warehouse_name': row[7],
                            'warehouse_id': row[8],
                            'counted_quantity': 0.0,  # À remplir lors de l'inventaire
                            'variance': 0.0  # Différence entre compté et théorique
                        })
                    else:
                        products.append({
                            'product_id': row[0],
                            'product_name': row[1] or f"Produit {row[0]}",
                            'product_code': row[2] or "",
                            'current_quantity': float(row[3]) if row[3] else 0,
                            'reserved_quantity': float(row[4]) if row[4] else 0,
                            'unit_cost': float(row[5]) if row[5] else 0,
                            'min_stock_level': float(row[6]) if row[6] else 0,
                            'warehouse_count': row[7] if row[7] else 0,
                            'counted_quantity': 0.0,
                            'variance': 0.0
                        })
                
                return products
                
        except Exception as e:
            print(f"Erreur lors de la récupération des produits: {e}")
            return []

    def create_inventory(self, inventory_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Créer un nouvel inventaire
        
        Args:
            inventory_data: Données de l'inventaire
            
        Returns:
            Données de l'inventaire créé ou None si erreur
        """
        try:
            # TODO: Implémentation avec nouvelle architecture
            # Pour l'instant, retournons une structure temporaire
            return {
                'id': 1,
                'reference': 'INV-001',
                'warehouse_id': inventory_data.get('warehouse_id'),
                'status': 'draft',
                'created_date': datetime.now(),
                'notes': inventory_data.get('notes', ''),
                'items': []
            }
                
        except Exception as e:
            print(f"Erreur lors de la création de l'inventaire: {e}")
            return None

    def get_inventories(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Récupérer la liste des inventaires
        
        Args:
            status: Statut à filtrer (optionnel)
            
        Returns:
            Liste des inventaires
        """
        try:
            # TODO: Implémentation avec nouvelle architecture
            return []
                
        except Exception as e:
            print(f"Erreur lors de la récupération des inventaires: {e}")
            return []

    def validate_inventory(self, inventory_id: int) -> bool:
        """
        Valider un inventaire (ajuster les stocks)
        
        Args:
            inventory_id: ID de l'inventaire à valider
            
        Returns:
            True si validation réussie, False sinon
        """
        try:
            # TODO: Implémentation avec nouvelle architecture
            return False
                
        except Exception as e:
            print(f"Erreur lors de la validation de l'inventaire: {e}")
            return False