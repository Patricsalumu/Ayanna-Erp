"""
Contrôleur pour la gestion des entrepôts avec nouvelle structure simplifiée
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text

from ayanna_erp.database.database_manager import DatabaseManager


class EntrepotController:
    """Contrôleur pour la gestion des entrepôts"""
    
    def __init__(self, entreprise_id: int):
        self.entreprise_id = entreprise_id
        self.db_manager = DatabaseManager()
    
    def get_all_warehouses(self, session: Session) -> List[Dict[str, Any]]:
        """Récupérer tous les entrepôts de l'entreprise"""
        result = session.execute(text("""
            SELECT id, code, name, type, description, address, 
                   contact_person, contact_phone, contact_email,
                   is_default, is_active, capacity_limit, created_at
            FROM stock_warehouses 
            WHERE entreprise_id = :entreprise_id 
            ORDER BY is_default DESC, name
        """), {"entreprise_id": self.entreprise_id})
        
        warehouses = []
        for row in result:
            warehouses.append({
                'id': row[0],
                'code': row[1],
                'name': row[2],
                'type': row[3],
                'description': row[4],
                'address': row[5],
                'contact_person': row[6],
                'contact_phone': row[7],
                'contact_email': row[8],
                'is_default': bool(row[9]),
                'is_active': bool(row[10]),
                'capacity_limit': float(row[11]) if row[11] else None,
                'created_at': row[12]
            })
        
        return warehouses
    
    def get_warehouse_by_id(self, session: Session, warehouse_id: int) -> Optional[Dict[str, Any]]:
        """Récupérer un entrepôt par son ID"""
        result = session.execute(text("""
            SELECT id, code, name, type, description, address,
                   contact_person, contact_phone, contact_email,
                   is_default, is_active, capacity_limit, created_at
            FROM stock_warehouses 
            WHERE id = :warehouse_id AND entreprise_id = :entreprise_id
        """), {"warehouse_id": warehouse_id, "entreprise_id": self.entreprise_id})
        
        row = result.first()
        if row:
            return {
                'id': row[0],
                'code': row[1],
                'name': row[2],
                'type': row[3],
                'description': row[4],
                'address': row[5],
                'contact_person': row[6],
                'contact_phone': row[7],
                'contact_email': row[8],
                'is_default': bool(row[9]),
                'is_active': bool(row[10]),
                'capacity_limit': float(row[11]) if row[11] else None,
                'created_at': row[12]
            }
        return None
    
    def get_warehouse_by_code(self, session: Session, code: str) -> Optional[Dict[str, Any]]:
        """Récupérer un entrepôt par son code"""
        result = session.execute(text("""
            SELECT id, code, name, type, description, address,
                   contact_person, contact_phone, contact_email,
                   is_default, is_active, capacity_limit, created_at
            FROM stock_warehouses 
            WHERE code = :code AND entreprise_id = :entreprise_id
        """), {"code": code, "entreprise_id": self.entreprise_id})
        
        row = result.first()
        if row:
            return {
                'id': row[0],
                'code': row[1],
                'name': row[2],
                'type': row[3],
                'description': row[4],
                'address': row[5],
                'contact_person': row[6],
                'contact_phone': row[7],
                'contact_email': row[8],
                'is_default': bool(row[9]),
                'is_active': bool(row[10]),
                'capacity_limit': float(row[11]) if row[11] else None,
                'created_at': row[12]
            }
        return None
    
    def create_warehouse(self, session: Session, warehouse_data: Dict[str, Any]) -> Dict[str, Any]:
        """Créer un nouvel entrepôt"""
        # Vérifier que le code n'existe pas déjà
        existing = self.get_warehouse_by_code(session, warehouse_data['code'])
        if existing:
            raise ValueError(f"Un entrepôt avec le code '{warehouse_data['code']}' existe déjà")
        
        # Si c'est le premier entrepôt, le mettre par défaut
        warehouses_count = session.execute(text("""
            SELECT COUNT(*) FROM stock_warehouses WHERE entreprise_id = :entreprise_id
        """), {"entreprise_id": self.entreprise_id}).scalar()
        
        is_default = warehouse_data.get('is_default', warehouses_count == 0)
        
        # Si défini par défaut, désactiver les autres
        if is_default:
            session.execute(text("""
                UPDATE stock_warehouses 
                SET is_default = 0 
                WHERE entreprise_id = :entreprise_id
            """), {"entreprise_id": self.entreprise_id})
        
        # Insérer le nouvel entrepôt
        result = session.execute(text("""
            INSERT INTO stock_warehouses 
            (entreprise_id, code, name, type, description, address,
             contact_person, contact_phone, contact_email, is_default, 
             is_active, capacity_limit, created_at)
            VALUES (:entreprise_id, :code, :name, :type, :description, :address,
                    :contact_person, :contact_phone, :contact_email, :is_default,
                    :is_active, :capacity_limit, CURRENT_TIMESTAMP)
        """), {
            "entreprise_id": self.entreprise_id,
            "code": warehouse_data['code'],
            "name": warehouse_data['name'],
            "type": warehouse_data.get('type', 'Principal'),
            "description": warehouse_data.get('description'),
            "address": warehouse_data.get('address'),
            "contact_person": warehouse_data.get('contact_person'),
            "contact_phone": warehouse_data.get('contact_phone'),
            "contact_email": warehouse_data.get('contact_email'),
            "is_default": is_default,
            "is_active": warehouse_data.get('is_active', True),
            "capacity_limit": warehouse_data.get('capacity_limit')
        })
        
        warehouse_id = result.lastrowid
        session.commit()
        
        # Retourner l'entrepôt créé
        return self.get_warehouse_by_id(session, warehouse_id)
    
    def update_warehouse(self, session: Session, warehouse_id: int, warehouse_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Mettre à jour un entrepôt"""
        warehouse = self.get_warehouse_by_id(session, warehouse_id)
        if not warehouse:
            return None
        
        # Vérifier unicité du code si modifié
        if 'code' in warehouse_data and warehouse_data['code'] != warehouse['code']:
            existing = self.get_warehouse_by_code(session, warehouse_data['code'])
            if existing and existing['id'] != warehouse_id:
                raise ValueError(f"Un entrepôt avec le code '{warehouse_data['code']}' existe déjà")
        
        # Si défini par défaut, désactiver les autres
        if warehouse_data.get('is_default'):
            session.execute(text("""
                UPDATE stock_warehouses 
                SET is_default = 0 
                WHERE entreprise_id = :entreprise_id AND id != :warehouse_id
            """), {"entreprise_id": self.entreprise_id, "warehouse_id": warehouse_id})
        
        # Construire la requête de mise à jour
        update_fields = []
        params = {"warehouse_id": warehouse_id}
        
        for field in ['code', 'name', 'type', 'description', 'address', 
                     'contact_person', 'contact_phone', 'contact_email', 
                     'is_default', 'is_active', 'capacity_limit']:
            if field in warehouse_data:
                update_fields.append(f"{field} = :{field}")
                params[field] = warehouse_data[field]
        
        if update_fields:
            session.execute(text(f"""
                UPDATE stock_warehouses 
                SET {', '.join(update_fields)}
                WHERE id = :warehouse_id
            """), params)
            
            session.commit()
        
        return self.get_warehouse_by_id(session, warehouse_id)
    
    def delete_warehouse(self, session: Session, warehouse_id: int) -> bool:
        """Supprimer un entrepôt (vérifier qu'il n'a pas de stocks)"""
        warehouse = self.get_warehouse_by_id(session, warehouse_id)
        if not warehouse:
            return False
        
        # Vérifier s'il y a des stocks
        stock_count = session.execute(text("""
            SELECT COUNT(*) FROM stock_produits_entrepot 
            WHERE warehouse_id = :warehouse_id AND quantity > 0
        """), {"warehouse_id": warehouse_id}).scalar()
        
        if stock_count > 0:
            raise ValueError("Impossible de supprimer un entrepôt qui contient des stocks")
        
        # Supprimer
        session.execute(text("""
            DELETE FROM stock_warehouses WHERE id = :warehouse_id
        """), {"warehouse_id": warehouse_id})
        
        session.commit()
        return True
    
    def get_warehouse_detailed_stats(self, session: Session, warehouse_id: int) -> Dict[str, Any]:
        """Obtenir les statistiques détaillées d'un entrepôt avec valeurs d'achat et de vente"""
        # Statistiques de base
        result = session.execute(text("""
            SELECT 
                COUNT(*) as total_products,
                COUNT(CASE WHEN spe.quantity > 0 THEN 1 END) as products_with_stock,
                COUNT(CASE WHEN spe.quantity = 0 THEN 1 END) as out_of_stock,
                COALESCE(SUM(spe.quantity), 0) as total_quantity,
                COALESCE(SUM(spe.total_cost), 0) as total_cost_value
            FROM stock_produits_entrepot spe
            WHERE spe.warehouse_id = :warehouse_id
        """), {"warehouse_id": warehouse_id}).fetchone()
        
        if result:
            stats = {
                'total_products': result[0] or 0,
                'products_with_stock': result[1] or 0,
                'out_of_stock': result[2] or 0,
                'total_quantity': float(result[3] or 0),
                'total_cost_value': float(result[4] or 0)  # Valeur d'achat
            }
        else:
            stats = {
                'total_products': 0,
                'products_with_stock': 0,
                'out_of_stock': 0,
                'total_quantity': 0.0,
                'total_cost_value': 0.0
            }
        
        # Calculer la valeur de vente en joignant avec les produits boutique
        sale_value_result = session.execute(text("""
            SELECT COALESCE(SUM(spe.quantity * cp.price_unit), 0) as total_sale_value
            FROM stock_produits_entrepot spe
            JOIN core_products sp ON spe.product_id = cp.id
            WHERE spe.warehouse_id = :warehouse_id
        """), {"warehouse_id": warehouse_id}).fetchone()
        
        stats['total_sale_value'] = float(sale_value_result[0] or 0) if sale_value_result else 0.0
        
        return stats
    
    def get_warehouse_products_details(self, session: Session, warehouse_id: int) -> List[Dict[str, Any]]:
        """Obtenir les détails des produits dans un entrepôt"""
        result = session.execute(text("""
            SELECT 
                cp.name as product_name,
                spe.quantity,
                spe.reserved_quantity,
                spe.unit_cost,
                cp.price_unit,
                (spe.quantity * spe.unit_cost) as cost_value,
                (spe.quantity * cp.price_unit) as sale_value
            FROM stock_produits_entrepot spe
            JOIN core_products sp ON spe.product_id = cp.id
            WHERE spe.warehouse_id = :warehouse_id
            ORDER BY cp.name
        """), {"warehouse_id": warehouse_id}).fetchall()
        
        products = []
        for row in result:
            products.append({
                'product_name': row[0],
                'quantity': float(row[1] or 0),
                'reserved_quantity': float(row[2] or 0),
                'unit_cost': float(row[3] or 0),
                'unit_price': float(row[4] or 0),
                'cost_value': float(row[5] or 0),
                'sale_value': float(row[6] or 0)
            })
        
        return products
    
    def get_active_warehouses(self, session: Session) -> List[Dict[str, Any]]:
        """Récupérer uniquement les entrepôts actifs"""
        result = session.execute(text("""
            SELECT id, code, name, type, is_default
            FROM stock_warehouses 
            WHERE entreprise_id = :entreprise_id AND is_active = 1
            ORDER BY is_default DESC, name
        """), {"entreprise_id": self.entreprise_id})
        
        warehouses = []
        for row in result:
            warehouses.append({
                'id': row[0],
                'code': row[1],
                'name': row[2],
                'type': row[3],
                'is_default': bool(row[4])
            })
        
        return warehouses
    
    def get_warehouse_configuration_by_pos(self, session: Session) -> Dict[str, Any]:
        """Obtenir la configuration des entrepôts pour cette entreprise"""
        warehouses = self.get_all_warehouses(session)
        
        default_warehouse = None
        for warehouse in warehouses:
            if warehouse['is_default']:
                default_warehouse = warehouse
                break
        
        return {
            'total_warehouses': len(warehouses),
            'active_warehouses': len([w for w in warehouses if w['is_active']]),
            'default_warehouse': default_warehouse,
            'warehouses_by_type': self._group_warehouses_by_type(warehouses)
        }
    
    def _group_warehouses_by_type(self, warehouses: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Grouper les entrepôts par type"""
        groups = {}
        for warehouse in warehouses:
            warehouse_type = warehouse['type'] or 'Autre'
            if warehouse_type not in groups:
                groups[warehouse_type] = []
            groups[warehouse_type].append(warehouse)
        return groups