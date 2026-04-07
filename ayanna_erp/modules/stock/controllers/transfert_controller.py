"""
Contrôleur pour la gestion des transferts entre entrepôts
Compatible avec la nouvelle architecture stock (4 tables)
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, text

from ayanna_erp.database.database_manager import DatabaseManager


class TransfertController:
    """Contrôleur pour la gestion des transferts entre entrepôts"""
    
    def __init__(self, entreprise_id: int):
        """
        Initialisation du contrôleur
        
        Args:
            entreprise_id: ID de l'entreprise
        """
        self.entreprise_id = entreprise_id
        self.db_manager = DatabaseManager()

    def _local_now(self):
        """Retourne la date/heure locale de la machine (naive datetime, sans tzinfo)."""
        return datetime.now()

    def get_warehouses_for_transfer(self) -> List[Dict[str, Any]]:
        """
        Récupérer les entrepôts disponibles pour les transferts
        
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

    def get_products_in_warehouse(self, warehouse_id: int) -> List[Dict[str, Any]]:
        """
        Récupérer les produits disponibles dans un entrepôt
        
        Args:
            warehouse_id: ID de l'entrepôt
            
        Returns:
            Liste des produits avec stock disponible
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
                        spe.unit_cost,
                        sw.name as warehouse_name
                    FROM stock_produits_entrepot spe
                    JOIN stock_warehouses sw ON spe.warehouse_id = sw.id
                    LEFT JOIN core_products p ON spe.product_id = p.id
                    WHERE spe.warehouse_id = :warehouse_id
                    AND sw.entreprise_id = :entreprise_id
                    AND spe.quantity > COALESCE(spe.reserved_quantity, 0)
                    ORDER BY p.name
                """), {
                    "warehouse_id": warehouse_id,
                    "entreprise_id": self.entreprise_id
                })
                
                products = []
                for row in result:
                    quantity = float(row[3]) if row[3] else 0
                    reserved = float(row[4]) if row[4] else 0
                    available_qty = quantity - reserved
                    
                    if available_qty > 0:
                        products.append({
                            'product_id': row[0],
                            'product_name': row[1] or f"Produit {row[0]}",
                            'product_code': row[2] or "",
                            'total_quantity': quantity,
                            'reserved_quantity': reserved,
                            'available_quantity': available_qty,
                            'unit_cost': float(row[5] or 0),
                            'warehouse_name': row[6]
                        })
                
                return products
                
        except Exception as e:
            print(f"Erreur lors de la récupération des produits: {e}")
            return []

    def create_transfer(self, transfer_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Créer un nouveau transfert
        
        Args:
            transfer_data: Données du transfert
            
        Returns:
            Données du transfert créé ou None si erreur
        """
        try:
            with self.db_manager.get_session() as session:
                # TODO: Implémentation des transferts avec nouvelle architecture
                # Pour l'instant, retournons une structure temporaire
                return {
                    'id': 1,
                    'reference': 'TR-001',
                    'source_warehouse_id': transfer_data.get('source_warehouse_id'),
                    'destination_warehouse_id': transfer_data.get('destination_warehouse_id'),
                    'status': 'pending',
                    'created_date': self._local_now(),
                    'notes': transfer_data.get('notes', ''),
                    'items': []
                }
                
        except Exception as e:
            print(f"Erreur lors de la création du transfert: {e}")
            return None

    def get_transfers(self, status: Optional[str] = None, 
                     limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Récupérer la liste des transferts
        
        Args:
            status: Statut à filtrer (optionnel)
            limit: Nombre maximum de résultats
            
        Returns:
            Liste des transferts
        """
        try:
            # TODO: Implémentation avec nouvelle architecture
            # Pour l'instant, retournons une liste vide
            return []
                
        except Exception as e:
            print(f"Erreur lors de la récupération des transferts: {e}")
            return []

    def get_all_transfers(self, session=None) -> List[Dict[str, Any]]:
        """
        Récupérer tous les transferts (alias pour get_transfers)
        
        Args:
            session: Session SQLAlchemy (ignorée pour compatibilité)
            
        Returns:
            Liste de tous les transferts
        """
        return self.get_transfers()

    def get_recent_transfers(self, session=None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Récupérer les transferts récents
        
        Args:
            session: Session SQLAlchemy (ignorée pour compatibilité)
            limit: Nombre maximum de transferts à récupérer
            
        Returns:
            Liste des transferts récents
        """
        return self.get_transfers(limit=limit)

    def get_transfer_by_id(self, transfer_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupérer un transfert par son ID
        
        Args:
            transfer_id: ID du transfert
            
        Returns:
            Données du transfert ou None si non trouvé
        """
        try:
            # TODO: Implémentation avec nouvelle architecture
            return None
                
        except Exception as e:
            print(f"Erreur lors de la récupération du transfert: {e}")
            return None

    def validate_transfer(self, transfer_id: int) -> bool:
        """
        Valider un transfert (effectuer le mouvement de stock)
        
        Args:
            transfer_id: ID du transfert à valider
            
        Returns:
            True si validation réussie, False sinon
        """
        try:
            # TODO: Implémentation avec nouvelle architecture
            return False
                
        except Exception as e:
            print(f"Erreur lors de la validation du transfert: {e}")
            return False

    def cancel_transfer(self, transfer_id: int) -> bool:
        """
        Annuler un transfert
        
        Args:
            transfer_id: ID du transfert à annuler
            
        Returns:
            True si annulation réussie, False sinon
        """
        try:
            # TODO: Implémentation avec nouvelle architecture
            return False
                
        except Exception as e:
            print(f"Erreur lors de l'annulation du transfert: {e}")
            return False