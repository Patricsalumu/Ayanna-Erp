"""
Contrôleur pour la gestion des alertes de stock
Compatible avec la nouvelle architecture stock (4 tables)
"""

from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, case, text

from ayanna_erp.database.database_manager import DatabaseManager


class AlerteController:
    """Contrôleur pour la gestion des alertes de stock"""
    
    def __init__(self, entreprise_id: int):
        """
        Initialisation du contrôleur
        
        Args:
            entreprise_id: ID de l'entreprise
        """
        self.entreprise_id = entreprise_id
        self.db_manager = DatabaseManager()

    def get_low_stock_alerts(self) -> List[Dict[str, Any]]:
        """
        Récupérer les alertes de stock faible
        
        Returns:
            Liste des produits avec stock faible
        """
        try:
            with self.db_manager.get_session() as session:
                result = session.execute(text("""
                    SELECT 
                        spe.product_id,
                        p.name as product_name,
                        p.code as product_code,
                        spe.quantity,
                        spe.reserved_quantity,
                        spe.min_stock_level,
                        sw.name as warehouse_name,
                        sw.id as warehouse_id,
                        (spe.quantity - COALESCE(spe.reserved_quantity, 0)) as available_quantity
                    FROM stock_produits_entrepot spe
                    JOIN stock_warehouses sw ON spe.warehouse_id = sw.id
                    LEFT JOIN core_products p ON spe.product_id = p.id
                    WHERE sw.entreprise_id = :entreprise_id
                    AND spe.min_stock_level > 0
                    AND (spe.quantity - COALESCE(spe.reserved_quantity, 0)) <= spe.min_stock_level
                    AND sw.is_active = 1
                    ORDER BY (spe.quantity / spe.min_stock_level), sw.name
                """), {"entreprise_id": self.entreprise_id})
                
                alerts = []
                for row in result:
                    quantity = float(row[3]) if row[3] else 0
                    reserved = float(row[4]) if row[4] else 0
                    min_level = float(row[5]) if row[5] else 0
                    available = float(row[8]) if row[8] else 0
                    
                    # Calculer le niveau de criticité
                    if min_level > 0:
                        ratio = available / min_level
                        if ratio <= 0:
                            level = "critical"
                        elif ratio <= 0.25:
                            level = "high"
                        elif ratio <= 0.5:
                            level = "medium"
                        else:
                            level = "low"
                    else:
                        level = "unknown"
                    
                    alerts.append({
                        'product_id': row[0],
                        'product_name': row[1] or f"Produit {row[0]}",
                        'product_code': row[2] or "",
                        'current_quantity': quantity,
                        'reserved_quantity': reserved,
                        'available_quantity': available,
                        'min_stock_level': min_level,
                        'warehouse_name': row[6],
                        'warehouse_id': row[7],
                        'alert_level': level,
                        'ratio': ratio if min_level > 0 else 0
                    })
                
                return alerts
                
        except Exception as e:
            print(f"Erreur lors de la récupération des alertes: {e}")
            return []

    def get_overstock_alerts(self, threshold_multiplier: float = 3.0) -> List[Dict[str, Any]]:
        """
        Récupérer les alertes de surstock
        
        Args:
            threshold_multiplier: Multiplicateur du stock minimum pour détecter le surstock
            
        Returns:
            Liste des produits en surstock
        """
        try:
            with self.db_manager.get_session() as session:
                result = session.execute(text("""
                    SELECT 
                        spe.product_id,
                        p.name as product_name,
                        p.code as product_code,
                        spe.quantity,
                        spe.reserved_quantity,
                        spe.min_stock_level,
                        sw.name as warehouse_name,
                        sw.id as warehouse_id
                    FROM stock_produits_entrepot spe
                    JOIN stock_warehouses sw ON spe.warehouse_id = sw.id
                    LEFT JOIN core_products p ON spe.product_id = p.id
                    WHERE sw.entreprise_id = :entreprise_id
                    AND spe.min_stock_level > 0
                    AND spe.quantity > (spe.min_stock_level * :threshold)
                    AND sw.is_active = 1
                    ORDER BY (spe.quantity / spe.min_stock_level) DESC, sw.name
                """), {
                    "entreprise_id": self.entreprise_id,
                    "threshold": threshold_multiplier
                })
                
                alerts = []
                for row in result:
                    quantity = float(row[3]) if row[3] else 0
                    reserved = float(row[4]) if row[4] else 0
                    min_level = float(row[5]) if row[5] else 0
                    
                    ratio = quantity / min_level if min_level > 0 else 0
                    
                    alerts.append({
                        'product_id': row[0],
                        'product_name': row[1] or f"Produit {row[0]}",
                        'product_code': row[2] or "",
                        'current_quantity': quantity,
                        'reserved_quantity': reserved,
                        'min_stock_level': min_level,
                        'warehouse_name': row[6],
                        'warehouse_id': row[7],
                        'overstock_ratio': ratio,
                        'excess_quantity': quantity - (min_level * threshold_multiplier)
                    })
                
                return alerts
                
        except Exception as e:
            print(f"Erreur lors de la récupération des alertes de surstock: {e}")
            return []

    def get_alert_statistics(self) -> Dict[str, Any]:
        """
        Récupérer les statistiques des alertes
        
        Returns:
            Dictionnaire avec les statistiques
        """
        try:
            # Récupérer les alertes
            low_stock = self.get_low_stock_alerts()
            overstock = self.get_overstock_alerts()
            
            # Compter par niveau de criticité
            critical_count = len([a for a in low_stock if a['alert_level'] == 'critical'])
            high_count = len([a for a in low_stock if a['alert_level'] == 'high'])
            medium_count = len([a for a in low_stock if a['alert_level'] == 'medium'])
            low_count = len([a for a in low_stock if a['alert_level'] == 'low'])
            
            return {
                'total_low_stock': len(low_stock),
                'critical_alerts': critical_count,
                'high_alerts': high_count,
                'medium_alerts': medium_count,
                'low_alerts': low_count,
                'overstock_alerts': len(overstock),
                'last_updated': datetime.now()
            }
                
        except Exception as e:
            print(f"Erreur lors du calcul des statistiques: {e}")
            return {
                'total_low_stock': 0,
                'critical_alerts': 0,
                'high_alerts': 0,
                'medium_alerts': 0,
                'low_alerts': 0,
                'overstock_alerts': 0,
                'last_updated': datetime.now()
            }

    def update_alert_thresholds(self, product_id: int, warehouse_id: int, 
                               min_stock: float, max_stock: Optional[float] = None) -> bool:
        """
        Mettre à jour les seuils d'alerte pour un produit
        
        Args:
            product_id: ID du produit
            warehouse_id: ID de l'entrepôt
            min_stock: Seuil minimum
            max_stock: Seuil maximum (optionnel)
            
        Returns:
            True si mise à jour réussie, False sinon
        """
        try:
            with self.db_manager.get_session() as session:
                # TODO: Implémentation avec nouvelle architecture
                # Mettre à jour min_stock_level dans stock_produits_entrepot
                session.execute(text("""
                    UPDATE stock_produits_entrepot 
                    SET min_stock_level = :min_stock
                    WHERE product_id = :product_id AND warehouse_id = :warehouse_id
                """), {
                    "min_stock": min_stock,
                    "product_id": product_id,
                    "warehouse_id": warehouse_id
                })
                
                session.commit()
                return True
                
        except Exception as e:
            print(f"Erreur lors de la mise à jour des seuils: {e}")
            return False