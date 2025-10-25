"""
Contrôleur pour la gestion des stocks avec nouvelle structure simplifiée
"""

from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text

from ayanna_erp.database.database_manager import DatabaseManager


class StockController:
    """Contrôleur pour la gestion des stocks"""
    
    def __init__(self, entreprise_id: int):
        self.entreprise_id = entreprise_id
        self.db_manager = DatabaseManager()
    
    def get_stock_overview(self, session: Session, warehouse_id: Optional[int] = None) -> Dict[str, Any]:
        """Obtenir une vue d'ensemble des stocks"""
        if warehouse_id:
            # Stock pour un entrepôt spécifique avec informations produit
            result = session.execute(text("""
                SELECT 
                    spe.product_id,
                    p.name as product_name,
                    p.code as product_code,
                    spe.quantity,
                    spe.unit_cost,
                    spe.total_cost,
                    spe.min_stock_level,
                    spe.reserved_quantity,
                    sw.name as warehouse_name,
                    sw.code as warehouse_code
                FROM stock_produits_entrepot spe
                JOIN stock_warehouses sw ON spe.warehouse_id = sw.id
                LEFT JOIN core_products p ON spe.product_id = p.id
                WHERE spe.warehouse_id = :warehouse_id
                AND sw.entreprise_id = :entreprise_id
                AND sw.is_active = 1
                ORDER BY spe.quantity DESC
            """), {"warehouse_id": warehouse_id, "entreprise_id": self.entreprise_id})
        else:
            # Vue globale de tous les entrepôts avec informations produit
            result = session.execute(text("""
                SELECT 
                    spe.product_id,
                    p.name as product_name,
                    p.code as product_code,
                    SUM(spe.quantity) as total_quantity,
                    AVG(spe.unit_cost) as avg_unit_cost,
                    SUM(spe.total_cost) as total_value,
                    MIN(spe.min_stock_level) as min_stock_level,
                    SUM(spe.reserved_quantity) as total_reserved_quantity,
                    COUNT(DISTINCT spe.warehouse_id) as warehouse_count
                FROM stock_produits_entrepot spe
                JOIN stock_warehouses sw ON spe.warehouse_id = sw.id
                LEFT JOIN core_products p ON spe.product_id = p.id
                WHERE sw.entreprise_id = :entreprise_id
                AND sw.is_active = 1
                GROUP BY spe.product_id, p.name, p.code
                ORDER BY total_quantity DESC
            """), {"entreprise_id": self.entreprise_id})
        
        stocks = []
        for row in result:
            if warehouse_id:
                quantity = float(row[3]) if row[3] else 0
                reserved = float(row[7]) if row[7] else 0
                min_stock = float(row[6]) if row[6] else 0
                available_quantity = quantity - reserved
                
                # Calcul du statut basé sur les niveaux de stock
                if available_quantity <= 0:
                    status = "Rupture"
                elif available_quantity <= min_stock:
                    status = "Faible"
                elif available_quantity <= min_stock * 1.5:
                    status = "Alerte"
                else:
                    status = "Normal"
                
                stocks.append({
                    'product_id': row[0],
                    'product_name': row[1] or f"Produit {row[0]}",
                    'product_code': row[2] or "",
                    'quantity': quantity,
                    'unit_cost': float(row[4]) if row[4] else 0,
                    'total_cost': float(row[5]) if row[5] else 0,
                    'stock_value': quantity * (float(row[4]) if row[4] else 0),  # Valeur du stock
                    'min_stock_level': min_stock,
                    'minimum_stock': min_stock,  # Alias pour compatibilité
                    'reserved_quantity': reserved,
                    'available_quantity': available_quantity,
                    'status': status,  # Statut du stock
                    'warehouse_name': row[8],
                    'warehouse_code': row[9]
                })
            else:
                quantity = float(row[3]) if row[3] else 0
                reserved = float(row[7]) if row[7] else 0
                min_stock = float(row[6]) if row[6] else 0
                available_quantity = quantity - reserved
                
                # Calcul du statut basé sur les niveaux de stock
                if available_quantity <= 0:
                    status = "Rupture"
                elif available_quantity <= min_stock:
                    status = "Faible"
                elif available_quantity <= min_stock * 1.5:
                    status = "Alerte"
                else:
                    status = "Normal"
                
                stocks.append({
                    'product_id': row[0],
                    'product_name': row[1] or f"Produit {row[0]}",
                    'product_code': row[2] or "",
                    'quantity': quantity,
                    'unit_cost': float(row[4]) if row[4] else 0,
                    'total_cost': float(row[5]) if row[5] else 0,
                    'stock_value': quantity * (float(row[4]) if row[4] else 0),  # Valeur du stock
                    'min_stock_level': min_stock,
                    'minimum_stock': min_stock,  # Alias pour compatibilité
                    'reserved_quantity': reserved,
                    'available_quantity': available_quantity,
                    'status': status,  # Statut du stock
                    'warehouse_count': row[8] if row[8] else 1,
                    'warehouse_name': 'Global',  # Vue globale
                    'warehouse_code': 'ALL'  # Code pour vue globale
                })
        
        # Calculer le résumé
        total_quantity = sum(stock['quantity'] for stock in stocks)
        total_reserved = sum(stock['reserved_quantity'] for stock in stocks)
        total_available = sum(stock['available_quantity'] for stock in stocks)
        total_value = sum(stock['stock_value'] for stock in stocks)
        
        # Compter les entrepôts distincts
        if warehouse_id:
            warehouse_count = 1
        else:
            warehouse_count = len(set(stock['warehouse_name'] for stock in stocks if stock['warehouse_name'] != 'Global'))
        
        summary = {
            'total_products': len(stocks),
            'total_items': len(stocks),  # Nombre total de références produits
            'total_quantity': total_quantity,
            'total_reserved': total_reserved,
            'total_available': total_available,
            'total_value': total_value,
            'total_warehouses': warehouse_count,  # Nombre total d'entrepôts
            'warehouse_count': warehouse_count
        }
        
        return {
            'stocks': stocks,
            'summary': summary,
            'total_items': len(stocks),
            'warehouse_id': warehouse_id
        }
    
    def get_product_stock_details(self, session: Session, product_id: int) -> Dict[str, Any]:
        """Obtenir les détails de stock d'un produit dans tous les entrepôts"""
        result = session.execute(text("""
            SELECT 
                sw.id as warehouse_id,
                sw.name as warehouse_name,
                sw.code as warehouse_code,
                sw.type as warehouse_type,
                spe.quantity,
                spe.unit_cost,
                spe.total_cost,
                spe.reserved_quantity,
                spe.min_stock_level,
                spe.last_movement_date,
                p.name as product_name,
                p.code as product_code
            FROM stock_warehouses sw
            LEFT JOIN stock_produits_entrepot spe ON sw.id = spe.warehouse_id AND spe.product_id = :product_id
            LEFT JOIN core_products p ON spe.product_id = p.id
            WHERE sw.entreprise_id = :entreprise_id AND sw.is_active = 1
            ORDER BY sw.is_default DESC, sw.name
        """), {"product_id": product_id, "entreprise_id": self.entreprise_id})
        
        warehouses = []
        total_quantity = 0
        total_value = 0
        product_name = None
        product_code = None
        
        for row in result:
            quantity = float(row[4]) if row[4] else 0
            unit_cost = float(row[5]) if row[5] else 0
            total_cost = float(row[6]) if row[6] else 0
            reserved = float(row[7]) if row[7] else 0
            min_stock_level = float(row[8]) if row[8] else 0
            last_movement = row[9]

            # Récupérer les infos produit depuis la première ligne
            if product_name is None and row[10]:
                product_name = row[10]
                product_code = row[11]

            total_quantity += quantity
            total_value += total_cost

            available = quantity - reserved

            # Calculer le statut pour chaque entrepôt
            if available <= 0:
                status = 'RUPTURE'
            elif available <= min_stock_level:
                status = 'FAIBLE'
            elif available <= min_stock_level * 1.5:
                status = 'ALERTE'
            else:
                status = 'NORMAL'

            warehouses.append({
                'warehouse_id': row[0],
                'warehouse_name': row[1],
                'warehouse_code': row[2],
                'warehouse_type': row[3],
                'quantity': quantity,
                'reserved_quantity': reserved,
                'available_quantity': available,
                'unit_cost': unit_cost,
                'total_cost': total_cost,
                'min_stock_level': min_stock_level,
                'last_movement_date': last_movement,
                'status': status
            })
        
        return {
            'product_id': product_id,
            'product_name': product_name or f"Produit {product_id}",
            'product_code': product_code or "",
            'warehouses': warehouses,
            'total_quantity': total_quantity,
            'total_value': total_value,
            'average_unit_cost': total_value / total_quantity if total_quantity > 0 else 0
        }
    
    def get_product_stock_by_warehouses(self, session: Session, product_id: int) -> Dict[str, Any]:
        """Méthode alias pour get_product_stock_details - retourne les détails de stock d'un produit par entrepôt"""
        details = self.get_product_stock_details(session, product_id)
        # Reformater pour correspondre au format attendu par le widget
        # Normaliser les clés : 'warehouse_stocks' et 'totals' avec reserved/available
        warehouse_stocks = []
        total_reserved = 0
        total_available = 0
        for wh in details.get('warehouses', []):
            # 'warehouses' devrait déjà contenir reserved_quantity et available_quantity (si get_product_stock_details a été mis à jour)
            reserved = wh.get('reserved_quantity', 0)
            available = wh.get('available_quantity', wh.get('quantity', 0) - reserved)
            total_reserved += reserved
            total_available += available
            warehouse_stocks.append(wh)

        totals = {
            'total_quantity': details.get('total_quantity', 0),
            'total_reserved': total_reserved,
            'total_available': total_available,
            'total_value': details.get('total_value', 0),
            'average_unit_cost': details.get('average_unit_cost', 0)
        }

        return {
            'product': {
                'id': details['product_id'],
                'name': details['product_name'],
                'code': details['product_code']
            },
            'warehouse_stocks': warehouse_stocks,
            'totals': totals
        }
    
    def update_stock(self, session: Session, product_id: int, warehouse_id: int, 
                    new_quantity: Decimal, unit_cost: Decimal, 
                    reference: Optional[str] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Mettre à jour le stock d'un produit dans un entrepôt"""
        # Récupérer l'ancien stock
        old_stock = session.execute(text("""
            SELECT quantity, unit_cost, total_cost 
            FROM stock_produits_entrepot 
            WHERE product_id = :product_id AND warehouse_id = :warehouse_id
        """), {"product_id": product_id, "warehouse_id": warehouse_id}).first()
        
        old_quantity = float(old_stock[0]) if old_stock and old_stock[0] else 0
        old_unit_cost = float(old_stock[1]) if old_stock and old_stock[1] else 0
        
        new_total_cost = float(new_quantity) * float(unit_cost)
        
        # Mettre à jour ou créer le stock
        if old_stock:
            session.execute(text("""
                UPDATE stock_produits_entrepot 
                SET quantity = :quantity, 
                    unit_cost = :unit_cost, 
                    total_cost = :total_cost,
                    last_movement_date = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE product_id = :product_id AND warehouse_id = :warehouse_id
            """), {
                "quantity": float(new_quantity),
                "unit_cost": float(unit_cost),
                "total_cost": new_total_cost,
                "product_id": product_id,
                "warehouse_id": warehouse_id
            })
        else:
            session.execute(text("""
                INSERT INTO stock_produits_entrepot 
                (product_id, warehouse_id, quantity, unit_cost, total_cost, 
                 last_movement_date, created_at, updated_at)
                VALUES (:product_id, :warehouse_id, :quantity, :unit_cost, :total_cost,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """), {
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "quantity": float(new_quantity),
                "unit_cost": float(unit_cost),
                "total_cost": new_total_cost
            })
        
        # Enregistrer le mouvement de stock
        self._record_stock_movement(
            session, product_id, warehouse_id, warehouse_id,
            float(new_quantity) - old_quantity, float(unit_cost),
            old_quantity, float(new_quantity), reference, user_id
        )
        
        session.commit()
        
        return {
            'product_id': product_id,
            'warehouse_id': warehouse_id,
            'old_quantity': old_quantity,
            'new_quantity': float(new_quantity),
            'quantity_change': float(new_quantity) - old_quantity,
            'unit_cost': float(unit_cost),
            'total_cost': new_total_cost
        }
    
    def transfer_stock(self, session: Session, product_id: int, 
                      warehouse_from_id: int, warehouse_to_id: int,
                      quantity: Decimal, reference: Optional[str] = None,
                      user_id: Optional[int] = None) -> Dict[str, Any]:
        """Transférer du stock entre entrepôts"""
        # Vérifier le stock source
        source_stock = session.execute(text("""
            SELECT quantity, unit_cost 
            FROM stock_produits_entrepot 
            WHERE product_id = :product_id AND warehouse_id = :warehouse_id
        """), {"product_id": product_id, "warehouse_id": warehouse_from_id}).first()
        
        if not source_stock or float(source_stock[0]) < float(quantity):
            raise ValueError("Stock insuffisant dans l'entrepôt source")
        
        source_quantity = float(source_stock[0])
        unit_cost = float(source_stock[1])
        
        # Réduire le stock source
        new_source_quantity = source_quantity - float(quantity)
        session.execute(text("""
            UPDATE stock_produits_entrepot 
            SET quantity = :quantity, 
                total_cost = :total_cost,
                last_movement_date = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE product_id = :product_id AND warehouse_id = :warehouse_id
        """), {
            "quantity": new_source_quantity,
            "total_cost": new_source_quantity * unit_cost,
            "product_id": product_id,
            "warehouse_id": warehouse_from_id
        })
        
        # Augmenter le stock destination
        dest_stock = session.execute(text("""
            SELECT quantity FROM stock_produits_entrepot 
            WHERE product_id = :product_id AND warehouse_id = :warehouse_id
        """), {"product_id": product_id, "warehouse_id": warehouse_to_id}).first()
        
        dest_quantity = float(dest_stock[0]) if dest_stock else 0
        new_dest_quantity = dest_quantity + float(quantity)
        
        if dest_stock:
            session.execute(text("""
                UPDATE stock_produits_entrepot 
                SET quantity = :quantity, 
                    total_cost = :total_cost,
                    last_movement_date = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE product_id = :product_id AND warehouse_id = :warehouse_id
            """), {
                "quantity": new_dest_quantity,
                "total_cost": new_dest_quantity * unit_cost,
                "product_id": product_id,
                "warehouse_id": warehouse_to_id
            })
        else:
            session.execute(text("""
                INSERT INTO stock_produits_entrepot 
                (product_id, warehouse_id, quantity, unit_cost, total_cost,
                 last_movement_date, created_at, updated_at)
                VALUES (:product_id, :warehouse_id, :quantity, :unit_cost, :total_cost,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """), {
                "product_id": product_id,
                "warehouse_id": warehouse_to_id,
                "quantity": new_dest_quantity,
                "unit_cost": unit_cost,
                "total_cost": new_dest_quantity * unit_cost
            })
        
        # Enregistrer le mouvement
        self._record_stock_movement(
            session, product_id, warehouse_from_id, warehouse_to_id,
            float(quantity), unit_cost, source_quantity, new_source_quantity,
            reference, user_id
        )
        
        session.commit()
        
        return {
            'product_id': product_id,
            'warehouse_from_id': warehouse_from_id,
            'warehouse_to_id': warehouse_to_id,
            'quantity_transferred': float(quantity),
            'unit_cost': unit_cost,
            'source_new_quantity': new_source_quantity,
            'dest_new_quantity': new_dest_quantity
        }
    
    def get_stock_movements(self, session: Session, product_id: Optional[int] = None,
                           warehouse_id: Optional[int] = None, 
                           limit: int = 100) -> List[Dict[str, Any]]:
        """Récupérer l'historique des mouvements de stock"""
        conditions = []
        params = {"entreprise_id": self.entreprise_id}
        
        if product_id:
            conditions.append("sm.product_id = :product_id")
            params["product_id"] = product_id
        
        if warehouse_id:
            conditions.append("(sm.warehouse_id_depart = :warehouse_id OR sm.warehouse_id_destination = :warehouse_id)")
            params["warehouse_id"] = str(warehouse_id)
        
        where_clause = " AND " + " AND ".join(conditions) if conditions else ""
        
        result = session.execute(text(f"""
            SELECT 
                sm.id,
                sm.product_id,
                sm.warehouse_id_depart,
                sm.warehouse_id_destination,
                sm.quantity,
                sm.unit_cost,
                sm.total_cost,
                sm.quantity_before,
                sm.quantity_after,
                sm.reference_document,
                sm.mouvement_date,
                sm.user_id
            FROM stock_mouvements sm
            WHERE 1=1 {where_clause}
            ORDER BY sm.mouvement_date DESC
            LIMIT :limit
        """), {**params, "limit": limit})
        
        movements = []
        for row in result:
            movements.append({
                'id': row[0],
                'product_id': row[1],
                'warehouse_from': row[2],
                'warehouse_to': row[3],
                'quantity': float(row[4]),
                'unit_cost': float(row[5]),
                'total_cost': float(row[6]),
                'quantity_before': float(row[7]),
                'quantity_after': float(row[8]),
                'reference': row[9],
                'movement_date': row[10],
                'user_id': row[11]
            })
        
        return movements
    
    def _record_stock_movement(self, session: Session, product_id: int,
                              warehouse_from_id: int, warehouse_to_id: int,
                              quantity: float, unit_cost: float,
                              quantity_before: float, quantity_after: float,
                              reference: Optional[str] = None,
                              user_id: Optional[int] = None):
        """Enregistrer un mouvement de stock"""
        session.execute(text("""
            INSERT INTO stock_mouvements 
            (warehouse_id_depart, warehouse_id_destination, product_id, quantity,
             unit_cost, total_cost, quantity_before, quantity_after,
             reference_document, user_id, mouvement_date, created_at)
            VALUES (:warehouse_from, :warehouse_to, :product_id, :quantity,
                    :unit_cost, :total_cost, :quantity_before, :quantity_after,
                    :reference, :user_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """), {
            "warehouse_from": str(warehouse_from_id),
            "warehouse_to": str(warehouse_to_id),
            "product_id": product_id,
            "quantity": quantity,
            "unit_cost": unit_cost,
            "total_cost": quantity * unit_cost,
            "quantity_before": quantity_before,
            "quantity_after": quantity_after,
            "reference": reference,
            "user_id": user_id
        })
    
    def get_low_stock_alerts(self, session: Session, warehouse_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Récupérer les alertes de stock faible"""
        conditions = ["sw.entreprise_id = :entreprise_id", "sw.is_active = 1"]
        params = {"entreprise_id": self.entreprise_id}
        
        if warehouse_id:
            conditions.append("spe.warehouse_id = :warehouse_id")
            params["warehouse_id"] = warehouse_id
        
        where_clause = " AND ".join(conditions)
        
        result = session.execute(text(f"""
            SELECT 
                spe.product_id,
                spe.warehouse_id,
                sw.name as warehouse_name,
                sw.code as warehouse_code,
                spe.quantity,
                spe.min_stock_level,
                spe.unit_cost
            FROM stock_produits_entrepot spe
            JOIN stock_warehouses sw ON spe.warehouse_id = sw.id
            WHERE {where_clause}
            AND spe.min_stock_level > 0
            AND spe.quantity <= spe.min_stock_level
            ORDER BY (spe.quantity / spe.min_stock_level), sw.name
        """), params)
        
        alerts = []
        for row in result:
            alerts.append({
                'product_id': row[0],
                'warehouse_id': row[1],
                'warehouse_name': row[2],
                'warehouse_code': row[3],
                'current_quantity': float(row[4]),
                'min_stock_level': float(row[5]),
                'unit_cost': float(row[6]),
                'shortage': float(row[5]) - float(row[4])
            })
        
        return alerts
    
    def get_stock_statistics(self, session: Session) -> Dict[str, Any]:
        """Obtenir les statistiques globales des stocks"""
        # Valeur totale des stocks
        total_value = session.execute(text("""
            SELECT COALESCE(SUM(spe.total_cost), 0) 
            FROM stock_produits_entrepot spe
            JOIN stock_warehouses sw ON spe.warehouse_id = sw.id
            WHERE sw.entreprise_id = :entreprise_id AND sw.is_active = 1
        """), {"entreprise_id": self.entreprise_id}).scalar()
        
        # Nombre de produits différents
        unique_products = session.execute(text("""
            SELECT COUNT(DISTINCT spe.product_id) 
            FROM stock_produits_entrepot spe
            JOIN stock_warehouses sw ON spe.warehouse_id = sw.id
            WHERE sw.entreprise_id = :entreprise_id AND sw.is_active = 1
        """), {"entreprise_id": self.entreprise_id}).scalar()
        
        # Produits en rupture
        out_of_stock = session.execute(text("""
            SELECT COUNT(DISTINCT spe.product_id) 
            FROM stock_produits_entrepot spe
            JOIN stock_warehouses sw ON spe.warehouse_id = sw.id
            WHERE sw.entreprise_id = :entreprise_id AND sw.is_active = 1 AND spe.quantity = 0
        """), {"entreprise_id": self.entreprise_id}).scalar()
        
        # Alertes stock faible
        low_stock_count = len(self.get_low_stock_alerts(session))
        
        return {
            'total_value': float(total_value or 0),
            'unique_products': unique_products or 0,
            'out_of_stock_products': out_of_stock or 0,
            'low_stock_alerts': low_stock_count
        }