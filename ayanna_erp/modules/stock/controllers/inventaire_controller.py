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
from ayanna_erp.modules.stock.models import StockInventaire, StockInventaireItem, StockMovement, StockProduitEntrepot


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
                    # Tous les produits actifs de l'entreprise, avec stock dans l'entrepôt spécifique
                    result = session.execute(text("""
                        SELECT 
                            p.id as product_id,
                            p.name as product_name,
                            p.code as product_code,
                            COALESCE(spe.quantity, 0) as quantity,
                            COALESCE(spe.reserved_quantity, 0) as reserved_quantity,
                            COALESCE(spe.unit_cost, p.cost, 0) as unit_cost,
                            COALESCE(spe.min_stock_level, 0) as min_stock_level,
                            sw.name as warehouse_name,
                            sw.id as warehouse_id,
                            p.price_unit as selling_price
                        FROM core_products p
                        CROSS JOIN stock_warehouses sw
                        LEFT JOIN stock_produits_entrepot spe ON spe.product_id = p.id AND spe.warehouse_id = sw.id
                        WHERE sw.id = :warehouse_id
                        AND sw.entreprise_id = :entreprise_id
                        AND p.entreprise_id = :entreprise_id
                        AND p.is_active = 1
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
                            'selling_price': float(row[9]) if row[9] else 0,
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

    def create_inventory_session(self, session: Session, inventory_data: Dict[str, Any]) -> Optional[StockInventaire]:
        """
        Créer et persister une session d'inventaire. Retourne l'objet StockInventaire créé.
        """
        try:
            # Générer un ID simple (timestamp-based) et une référence lisible
            reference = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            warehouse_id = inventory_data.get('warehouse_id')

            # Récupérer la liste initiale des produits selon le type (complet/partiel)
            products = []
            all_products = self.get_products_for_inventory(warehouse_id)

            if inventory_data.get('inventory_type', '').lower().startswith('inventaire partiel'):
                # Si l'appelant a fourni product_ids, filtrer
                selected = inventory_data.get('product_ids') or []
                for p in all_products:
                    if p['product_id'] in selected:
                        products.append({
                            'product_id': p['product_id'],
                            'product_name': p.get('product_name'),
                            'product_code': p.get('product_code'),
                            'system_stock': p.get('current_quantity') if 'current_quantity' in p else p.get('quantity', 0),
                            'unit_cost': p.get('unit_cost', 0),
                            'location': p.get('location', '')
                        })
            else:
                # Inventaire complet ou par défaut: inclure tous
                for p in all_products:
                    products.append({
                        'product_id': p['product_id'],
                        'product_name': p.get('product_name'),
                        'product_code': p.get('product_code'),
                        'system_stock': p.get('current_quantity') if 'current_quantity' in p else p.get('quantity', 0),
                        'unit_cost': p.get('unit_cost', 0),
                        'location': p.get('location', '')
                    })

            # Créer la session d'inventaire
            inventory = StockInventaire(
                entreprise_id=self.entreprise_id,
                reference=reference,
                session_name=inventory_data.get('session_name'),
                warehouse_id=warehouse_id,
                inventory_type=inventory_data.get('inventory_type'),
                status='DRAFT',
                scheduled_date=inventory_data.get('scheduled_date'),
                notes=inventory_data.get('notes'),
                total_items=len(products),
                include_zero_stock=bool(inventory_data.get('include_zero_stock')),
                auto_freeze_stock=bool(inventory_data.get('auto_freeze_stock')),
                send_notifications=bool(inventory_data.get('send_notifications'))
            )
            
            session.add(inventory)
            session.flush()  # Pour obtenir l'ID
            
            # Créer les éléments d'inventaire
            for p in products:
                item = StockInventaireItem(
                    inventory_id=inventory.id,
                    product_id=p['product_id'],
                    product_name=p['product_name'],
                    product_code=p['product_code'],
                    system_stock=float(p['system_stock']),
                    unit_cost=float(p['unit_cost']),
                    location=p.get('location')
                )
                session.add(item)
            
            return inventory
        except Exception as e:
            print(f"Erreur lors de la création de l'inventaire: {e}")
            return None

    def get_inventory_products(self, session: Session, inventory_id: int) -> List[Dict[str, Any]]:
        """Récupérer la liste des produits à compter pour une session existante"""
        try:
            # Récupérer les items d'inventaire
            items = session.query(StockInventaireItem).filter(
                StockInventaireItem.inventory_id == inventory_id
            ).order_by(StockInventaireItem.product_name).all()
            
            # Récupérer les prix de vente pour tous les produits
            product_ids = [item.product_id for item in items]
            if product_ids:
                # Construire paramètres nommés pour la clause IN afin d'utiliser session.execute correctement
                placeholders = ','.join([f":id{i}" for i in range(len(product_ids))])
                query = f"""
                    SELECT id, price_unit FROM core_products 
                    WHERE id IN ({placeholders})
                """
                params = {f"id{i}": pid for i, pid in enumerate(product_ids)}
                # Requête pour récupérer les prix de vente
                price_result = session.execute(text(query), params).fetchall()
                price_map = {row[0]: float(row[1] or 0) for row in price_result}
            else:
                price_map = {}
            
            products = []
            for item in items:
                selling_price = price_map.get(item.product_id, 0.0)
                products.append({
                    'product_id': item.product_id,
                    'product_name': item.product_name,
                    'product_code': item.product_code,
                    'system_stock': float(item.system_stock),
                    'counted_stock': float(item.counted_stock),
                    'variance': float(item.variance),
                    'unit_cost': float(item.unit_cost),
                    'selling_price': selling_price,
                    'variance_value_purchase': float(item.variance_value),  # Écart à l'achat
                    'variance_value_sale': float(item.variance_value_sale),  # Écart à la vente
                    'notes': item.notes or '',
                    'location': item.location
                })
            
            return products
        except Exception as e:
            print(f"Erreur lors de la lecture des produits d'inventaire: {e}")
            return []


    def save_inventory_counts(self, session: Session, inventory_id: int, counting_data: List[Dict[str, Any]]) -> bool:
        """Sauvegarder les comptages pour une session (met à jour les éléments d'inventaire).
        Met aussi à jour les statistiques de l'inventaire.
        """
        try:
            # Récupérer les prix de vente pour tous les produits concernés
            product_ids = [cd.get('product_id') for cd in counting_data if cd.get('product_id')]
            if product_ids:
                placeholders = ','.join([f":id{i}" for i in range(len(product_ids))])
                query = f"""
                    SELECT id, price_unit FROM core_products 
                    WHERE id IN ({placeholders})
                """
                params = {f"id{i}": pid for i, pid in enumerate(product_ids)}
                price_result = session.execute(text(query), params).fetchall()
                price_map = {row[0]: float(row[1] or 0) for row in price_result}
            else:
                price_map = {}
            
            # Mettre à jour les éléments
            for cd in counting_data:
                pid = cd.get('product_id')
                item = session.query(StockInventaireItem).filter(
                    StockInventaireItem.inventory_id == inventory_id,
                    StockInventaireItem.product_id == pid
                ).first()
                
                if item:
                    item.counted_stock = float(cd.get('counted_stock', 0) or 0)
                    item.variance = float(cd.get('variance', 0) or 0)
                    item.variance_value = float(item.variance) * float(item.unit_cost)
                    item.variance_value_sale = float(item.variance) * price_map.get(pid, 0.0)
                    item.notes = cd.get('notes', '')
                    item.counted_at = datetime.now()
            
            # Recalculer les statistiques de l'inventaire
            items = session.query(StockInventaireItem).filter(
                StockInventaireItem.inventory_id == inventory_id
            ).all()
            
            total_counted = sum(1 for item in items if item.counted_stock > 0)
            total_discrepancies = sum(1 for item in items if item.variance != 0)
            total_variance_value = sum(item.variance_value for item in items)
            
            inventory = session.query(StockInventaire).filter(StockInventaire.id == inventory_id).first()
            if inventory:
                inventory.counted_items = total_counted
                inventory.total_discrepancies = total_discrepancies
                inventory.total_variance_value = total_variance_value
            
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des comptages: {e}")
            return False


    

    def get_inventories(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Récupérer la liste des inventaires
        
        Args:
            status: Statut à filtrer (optionnel)
            
        Returns:
            Liste des inventaires
        """
        try:
            with self.db_manager.get_session() as session:
                query = session.query(StockInventaire).filter(
                    StockInventaire.entreprise_id == self.entreprise_id
                )
                
                if status:
                    query = query.filter(StockInventaire.status == status)
                
                inventories = query.order_by(StockInventaire.created_at.desc()).all()
                
                result = []
                for inv in inventories:
                    result.append({
                        'id': inv.id,
                        'reference': inv.reference,
                        'session_name': inv.session_name,
                        'warehouse_id': inv.warehouse_id,
                        'inventory_type': inv.inventory_type,
                        'status': inv.status,
                        'scheduled_date': inv.scheduled_date.isoformat() if inv.scheduled_date else None,
                        'completed_date': inv.completed_date.isoformat() if inv.completed_date else None,
                        'notes': inv.notes,
                        'total_items': inv.total_items,
                        'counted_items': inv.counted_items,
                        'total_discrepancies': inv.total_discrepancies,
                        'total_variance_value': float(inv.total_variance_value),
                        'progress_percentage': (inv.counted_items / inv.total_items * 100) if inv.total_items > 0 else 0,
                        'created_at': inv.created_at.isoformat() if inv.created_at else None
                    })
                
                return result
                
        except Exception as e:
            print(f"Erreur lors de la récupération des inventaires: {e}")
            return []
    def get_all_inventories(self, session: Session = None) -> List[Dict[str, Any]]:
        """Alias compatible: accepte une session optionnelle et retourne toutes les sessions."""
        # Ignorer la session fournie et utiliser la méthode principale
        return self.get_inventories()

    def complete_inventory(self, session: Session, inventory_id: int, performed_by: str = "system") -> bool:
        """Marquer une session d'inventaire comme complétée et appliquer les ajustements de stock.
        Crée des mouvements de stock pour les écarts.
        """
        try:
            inventory = session.query(StockInventaire).filter(StockInventaire.id == inventory_id).first()
            if not inventory:
                raise ValueError("Session d'inventaire introuvable")
            
            # Récupérer les éléments avec écarts
            items_with_variance = session.query(StockInventaireItem).filter(
                StockInventaireItem.inventory_id == inventory_id,
                StockInventaireItem.variance != 0
            ).all()
            
            # Créer les mouvements de stock pour les ajustements
            for item in items_with_variance:
                # Trouver ou créer la liaison produit-entrepôt
                product_warehouse = session.query(StockProduitEntrepot).filter(
                    StockProduitEntrepot.product_id == item.product_id,
                    StockProduitEntrepot.warehouse_id == inventory.warehouse_id
                ).first()
                
                if product_warehouse:
                    # Créer le mouvement d'ajustement
                    movement = StockMovement(
                        product_id=item.product_id,
                        warehouse_id=inventory.warehouse_id,
                        product_warehouse_id=product_warehouse.id,
                        movement_type='AJUSTEMENT',
                        quantity=item.variance,  # Quantité positive ou négative
                        unit_cost=item.unit_cost,
                        total_cost=item.variance_value,
                        reference=f"INV-{inventory.reference}",
                        description=f"Ajustement inventaire {inventory.session_name}",
                        user_name=performed_by
                    )
                    session.add(movement)
                    
                    # Mettre à jour le stock
                    product_warehouse.quantity += item.variance
                    product_warehouse.total_cost = product_warehouse.quantity * product_warehouse.unit_cost
                    product_warehouse.last_movement_date = datetime.now()

            # Comptabiliser la variation totale (création d'une écriture comptable)
            try:
                # Calculer la valeur totale des écarts (à l'achat)
                total_variance_value = sum(float(it.variance_value or 0) for it in items_with_variance)
                # Importer le contrôleur / modèles comptables localement pour éviter dépendances circulaires
                from ayanna_erp.modules.comptabilite.controller.comptabilite_controller import ComptabiliteController
                from ayanna_erp.modules.comptabilite.model.comptabilite import ComptaJournaux as JournalComptable, ComptaEcritures as EcritureComptable

                # Récupérer la configuration des comptes pour l'entreprise (pos_id non fourni)
                compta_ctrl = ComptabiliteController()
                compte_config = compta_ctrl.get_compte_config(inventory.entreprise_id)

                compte_stock_id = None
                compte_achat_id = None
                if compte_config:
                    # Atteindre les noms possibles selon la version du modèle
                    compte_stock_id = getattr(compte_config, 'compte_stock_id', None)
                    compte_achat_id = getattr(compte_config, 'compte_achat_id', None)
                    # Certains schémas utilisent un champ nommé compte_variation_stock_id / compte_variation_id
                    if not compte_achat_id:
                        compte_achat_id = getattr(compte_config, 'compte_variation_stock_id', None) or getattr(compte_config, 'compte_variation_id', None)

                # Ne rien faire si pas de comptes configurés ou montant nul
                if total_variance_value and compte_stock_id and compte_achat_id:
                    montant = abs(float(total_variance_value))

                    # Préparer le journal
                    user_id = inventory.completed_by or inventory.created_by or 1
                    journal = JournalComptable(
                        date_operation=datetime.now(),
                        libelle=f"Ajustement inventaire {inventory.reference}",
                        montant=montant,
                        type_operation="inventaire",
                        reference=inventory.reference,
                        description=f"Ajustement de stock suite à l'inventaire {inventory.session_name}",
                        enterprise_id=inventory.entreprise_id,
                        user_id=user_id
                    )
                    session.add(journal)
                    session.flush()

                    # Si perte (valeur négative), débiter compte charge/achat et créditer compte stock
                    if float(total_variance_value) < 0:
                        e_debit = EcritureComptable(journal_id=journal.id, compte_comptable_id=compte_achat_id, debit=montant, credit=0, ordre=1, libelle=f"Perte inventaire {inventory.reference}")
                        e_credit = EcritureComptable(journal_id=journal.id, compte_comptable_id=compte_stock_id, debit=0, credit=montant, ordre=2, libelle=f"Perte inventaire {inventory.reference}")
                    else:
                        # Surplus : débiter compte stock et créditer compte charge/achat
                        e_debit = EcritureComptable(journal_id=journal.id, compte_comptable_id=compte_stock_id, debit=montant, credit=0, ordre=1, libelle=f"Surplus inventaire {inventory.reference}")
                        e_credit = EcritureComptable(journal_id=journal.id, compte_comptable_id=compte_achat_id, debit=0, credit=montant, ordre=2, libelle=f"Surplus inventaire {inventory.reference}")

                    session.add(e_debit)
                    session.add(e_credit)
                    # Mettre à jour le total de l'inventaire
                    inventory.total_variance_value = total_variance_value
                else:
                    # Si la configuration des comptes est incomplète, on ignore la comptabilisation
                    # Ne pas lever d'exception : simplement logguer
                    # (On pourrait notifier l'utilisateur dans l'UI)
                    pass
            except Exception as e:
                # Ne pas empêcher la finalisation de l'inventaire en cas d'erreur comptable
                print(f"Erreur lors de la création des écritures comptables d'inventaire: {e}")
            
            # Marquer comme complété
            inventory.status = 'COMPLETED'
            inventory.completed_date = datetime.now()
            inventory.completed_by_name = performed_by

            # Retourner un message d'avertissement si la comptabilisation n'a pas été faite
            if 'total_variance_value' in locals():
                # total_variance_value calculé plus haut
                if total_variance_value and (not (compte_stock_id and compte_achat_id)):
                    warn = "Comptes comptables pour la variation de stock non configurés (compte stock / compte achat).\nVeuillez configurer ces comptes dans le module Comptabilité." 
                else:
                    warn = None
            else:
                warn = None

            return True, warn
        except Exception as e:
            print(f"Erreur lors de la finalisation de l'inventaire: {e}")
            return False, str(e)