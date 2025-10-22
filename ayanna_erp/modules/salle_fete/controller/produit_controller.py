"""
Contrôleur pour la gestion des produits du module Salle de Fête
Gère toutes les opérations CRUD pour les produits et la gestion du stock
"""

import sys
import os
from PyQt6.QtCore import QObject, pyqtSignal
from sqlalchemy.exc import IntegrityError
from datetime import datetime

# Ajouter le chemin vers le modèle
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ayanna_erp.modules.salle_fete.model.salle_fete import (
    EventProduct, EventStockMovement, EventReservation, EventReservationProduct, get_database_manager
)


class ProduitController(QObject):
    """Contrôleur pour la gestion des produits"""
    
    # Signaux pour la communication avec la vue
    product_added = pyqtSignal(object)
    product_updated = pyqtSignal(object)
    product_deleted = pyqtSignal(int)
    products_loaded = pyqtSignal(list)
    stock_movement_added = pyqtSignal(object)
    low_stock_alert = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, pos_id=1):
        super().__init__()
        self.pos_id = pos_id
        
    def set_pos_id(self, pos_id):
        """Définir l'ID de l'entreprise"""
        self.pos_id = pos_id
        
    def create_product(self, product_data):
        """
        Créer un nouveau produit
        
        Args:
            product_data (dict): Données du produit
            
        Returns:
            EventProduct: Le produit créé ou None
        """
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            
            product = EventProduct(
                pos_id=self.pos_id,
                name=product_data.get('name', ''),
                description=product_data.get('description', ''),
                cost=product_data.get('cost', 0.0),
                price_unit=product_data.get('price_unit', 0.0),
                stock_quantity=product_data.get('stock_quantity', 0.0),
                stock_min=product_data.get('stock_min', 0.0),
                unit=product_data.get('unit', 'pièce'),
                category=product_data.get('category', ''),
                compte_produit_id=product_data.get('compte_produit_id'),
                compte_charge_id=product_data.get('compte_charge_id'),
                is_active=product_data.get('is_active', True)
            )
            
            session.add(product)
            session.commit()
            session.refresh(product)
            
            # Créer un mouvement de stock initial si quantité > 0
            if product.stock_quantity > 0:
                self._create_stock_movement(
                    product.id, 'entry', product.stock_quantity,
                    product.cost, 'Stock initial', 'Création du produit'
                )
            
            print(f"✅ Produit créé: {product.name}")
            self.product_added.emit(product)
            return product
            
        except IntegrityError as e:
            session.rollback()
            error_msg = f"Erreur d'intégrité: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
            
        except Exception as e:
            session.rollback()
            error_msg = f"Erreur lors de la création du produit: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
            
        finally:
            db_manager.close_session()
    
    def load_products(self):
        """Charger tous les produits de l'entreprise"""
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            
            # Récupérer tous les produits
            products = session.query(EventProduct).filter(
                EventProduct.pos_id == self.pos_id
            ).order_by(EventProduct.name).all()
            
            print(f"✅ {len(products)} produits chargés")
            self.products_loaded.emit(products)
            return products
            
        except Exception as e:
            error_msg = f"Erreur lors du chargement des produits: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
            
        finally:
            db_manager.close_session()
            
    def get_product(self, product_id):
        """Récupérer un produit par ID"""
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            product = session.query(EventProduct).filter(
                EventProduct.id == product_id,
                EventProduct.pos_id == self.pos_id
            ).first()
            return product
            
        except Exception as e:
            error_msg = f"Erreur lors de la récupération du produit: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
            
        finally:
            db_manager.close_session()
            
    def get_all_products(self, active_only=True, category=None):
        """Récupérer tous les produits avec filtres optionnels"""
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            query = session.query(EventProduct).filter(EventProduct.pos_id == self.pos_id)
            
            if active_only:
                query = query.filter(EventProduct.is_active == True)
            if category:
                query = query.filter(EventProduct.category == category)
                
            products = query.order_by(EventProduct.name).all()
            
            self.products_loaded.emit(products)
            return products
            
        except Exception as e:
            error_msg = f"Erreur lors du chargement des produits: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
            
        finally:
            db_manager.close_session()
            
    def add_product(self, product_data):
        """Ajouter un nouveau produit"""
        try:
            # Utiliser la méthode create_product existante
            product = self.create_product(product_data)
            if product:
                self.product_added.emit(product)
                return True
            return False
            
        except Exception as e:
            error_msg = f"Erreur lors de l'ajout du produit: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
    
    def update_product(self, product_id, product_data):
        """Mettre à jour un produit"""
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            product = session.query(EventProduct).filter(
                EventProduct.id == product_id,
                EventProduct.pos_id == self.pos_id
            ).first()
            
            if not product:
                error_msg = f"Produit avec l'ID {product_id} non trouvé"
                self.error_occurred.emit(error_msg)
                return None
                
            # Mettre à jour les champs
            for field, value in product_data.items():
                if hasattr(product, field):
                    setattr(product, field, value)
                    
            session.commit()
            session.refresh(product)
            
            print(f"✅ Produit modifié: {product.name}")
            self.product_updated.emit(product)
            return product
            
        except Exception as e:
            session.rollback()
            error_msg = f"Erreur lors de la modification du produit: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
            
        finally:
            db_manager.close_session()
            
    def delete_product(self, product_id):
        """Supprimer un produit (suppression logique)"""
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            product = session.query(EventProduct).filter(
                EventProduct.id == product_id,
                EventProduct.pos_id == self.pos_id
            ).first()
            
            if not product:
                error_msg = f"Produit avec l'ID {product_id} non trouvé"
                self.error_occurred.emit(error_msg)
                return False
                
            # Suppression logique
            product.is_active = False
            session.commit()
            
            print(f"✅ Produit désactivé: {product.name}")
            self.product_deleted.emit(product_id)
            return True
            
        except Exception as e:
            session.rollback()
            error_msg = f"Erreur lors de la suppression du produit: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
            
        finally:
            db_manager.close_session()
            
    def adjust_stock(self, product_id, new_quantity, reason="Ajustement manuel", created_by=1):
        """
        Ajuster le stock d'un produit
        
        Args:
            product_id (int): ID du produit
            new_quantity (float): Nouvelle quantité en stock
            reason (str): Raison de l'ajustement
            created_by (int): ID de l'utilisateur
            
        Returns:
            bool: True si succès
        """
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            product = session.query(EventProduct).filter(
                EventProduct.id == product_id,
                EventProduct.pos_id == self.pos_id
            ).first()
            
            if not product:
                error_msg = f"Produit avec l'ID {product_id} non trouvé"
                self.error_occurred.emit(error_msg)
                return False
                
            old_quantity = product.stock_quantity
            movement_quantity = new_quantity - old_quantity
            movement_type = 'entry' if movement_quantity > 0 else 'exit'
            
            # Mettre à jour le stock
            product.stock_quantity = new_quantity
            
            # Créer le mouvement de stock
            movement = self._create_stock_movement(
                product_id, movement_type, abs(movement_quantity),
                product.cost, "ADJUST", reason, created_by
            )
            
            session.commit()
            
            print(f"✅ Stock ajusté pour {product.name}: {old_quantity} → {new_quantity}")
            self.product_updated.emit(product)
            self.stock_movement_added.emit(movement)
            
            # Vérifier le seuil minimum
            if new_quantity <= product.stock_min:
                self.low_stock_alert.emit([product])
                
            return True
            
        except Exception as e:
            session.rollback()
            error_msg = f"Erreur lors de l'ajustement du stock: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
            
        finally:
            db_manager.close_session()
            
    def _create_stock_movement(self, product_id, movement_type, quantity, unit_cost, reference, reason, created_by=1):
        """Créer un mouvement de stock"""
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            
            movement = EventStockMovement(
                product_id=product_id,
                movement_type=movement_type,
                quantity=quantity if movement_type == 'entry' else -quantity,
                unit_cost=unit_cost,
                reference=reference,
                reason=reason,
                created_by=created_by
            )
            
            session.add(movement)
            session.flush()
            return movement
            
        except Exception as e:
            print(f"❌ Erreur lors de la création du mouvement de stock: {e}")
            return None
            
    def get_products_low_stock(self):
        """Récupérer les produits avec un stock faible"""
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            
            products = session.query(EventProduct).filter(
                EventProduct.pos_id == self.pos_id,
                EventProduct.is_active == True,
                EventProduct.stock_quantity <= EventProduct.stock_min
            ).order_by(EventProduct.name).all()
            
            if products:
                self.low_stock_alert.emit(products)
                
            return products
            
        except Exception as e:
            error_msg = f"Erreur lors de la vérification du stock: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
            
        finally:
            db_manager.close_session()
            
    def get_stock_movements(self, product_id=None, limit=50):
        """Récupérer l'historique des mouvements de stock"""
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            query = session.query(EventStockMovement).join(EventProduct).filter(
                EventProduct.pos_id == self.pos_id
            )
            
            if product_id:
                query = query.filter(EventStockMovement.product_id == product_id)
                
            movements = query.order_by(
                EventStockMovement.movement_date.desc()
            ).limit(limit).all()
            
            return movements
            
        except Exception as e:
            error_msg = f"Erreur lors de la récupération des mouvements: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
            
        finally:
            db_manager.close_session()
            
    def search_products(self, search_term):
        """Rechercher des produits par nom, description ou catégorie"""
        try:
            db_manager = get_database_manager(); session = db_manager.get_session()
            search_pattern = f"%{search_term}%"
            
            products = session.query(EventProduct).filter(
                EventProduct.pos_id == self.pos_id,
                EventProduct.is_active == True,
                (EventProduct.name.ilike(search_pattern) |
                 EventProduct.description.ilike(search_pattern) |
                 EventProduct.category.ilike(search_pattern))
            ).order_by(EventProduct.name).all()
            
            self.products_loaded.emit(products)
            return products
            
        except Exception as e:
            error_msg = f"Erreur lors de la recherche: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
            
        finally:
            db_manager.close_session()
    
    def get_product_recent_movements(self, product_id, limit=10):
        """
        Récupère les mouvements de stock récents pour un produit
        Retourne: liste des dernières sorties avec date, client et quantité
        """
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            # Récupération des sorties de stock (ventes) depuis les réservations
            recent_sales = (session.query(
                    EventReservation.event_date,
                    EventReservation.client_nom,
                    EventReservation.client_prenom,
                    EventReservation.client_telephone,
                    EventReservationProduct.quantity,
                    EventReservationProduct.unit_price
                )
                .join(EventReservationProduct, EventReservation.id == EventReservationProduct.reservation_id)
                .filter(EventReservationProduct.product_id == product_id)
                .order_by(EventReservation.event_date.desc())
                .limit(limit)
                .all()
            )
            
            # Formatage des résultats pour les ventes
            movements_list = []
            for sale in recent_sales:
                client_name = f"{sale.client_nom or ''} {sale.client_prenom or ''}".strip() or "Client non spécifié"
                movements_list.append({
                    'type': 'SORTIE',
                    'date': sale.event_date,
                    'client_name': client_name,
                    'client_telephone': sale.client_telephone,
                    'quantity': sale.quantity,
                    'unit_price': sale.unit_price,
                    'total_line': sale.quantity * sale.unit_price,
                    'reason': 'Vente - Réservation'
                })
            
            # Récupération des autres mouvements de stock (entrées, ajustements, etc.)
            stock_movements = (session.query(EventStockMovement)
                             .filter(EventStockMovement.product_id == product_id)
                             .order_by(EventStockMovement.movement_date.desc())
                             .limit(limit)
                             .all())
            
            # Ajouter les mouvements de stock
            for movement in stock_movements:
                movements_list.append({
                    'type': movement.movement_type,
                    'date': movement.movement_date,
                    'client_name': movement.reference or 'Système',
                    'client_telephone': '',
                    'quantity': movement.quantity,
                    'unit_price': 0.0,
                    'total_line': 0.0,
                    'reason': movement.reason or movement.movement_type
                })
            
            # Trier par date (les plus récents en premier)
            movements_list.sort(key=lambda x: x['date'], reverse=True)
            
            return movements_list[:limit]
            
        except Exception as e:
            error_msg = f"Erreur lors de la récupération des mouvements: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return []
            
        finally:
            db_manager.close_session()
    
    def get_product_sales_statistics(self, product_id):
        """
        Récupère les statistiques de vente pour un produit donné
        Retourne: dict avec total_sold, total_revenue, last_sale, average_quantity
        """
        try:
            db_manager = get_database_manager()
            session = db_manager.get_session()
            
            # Jointure pour récupérer les données de vente du produit
            sales_data = (session.query(
                    EventReservationProduct.quantity,
                    (EventReservationProduct.quantity * EventReservationProduct.unit_price).label('revenue'),
                    EventReservation.event_date
                )
                .join(EventReservation, EventReservationProduct.reservation_id == EventReservation.id)
                .filter(EventReservationProduct.product_id == product_id)
                .all()
            )
            
            if not sales_data:
                return {
                    'total_sold': 0,
                    'total_sales': 0,
                    'total_revenue': 0.0,
                    'average_quantity': 0.0,
                    'last_sale': None
                }
            
            # Calcul des statistiques
            total_sales = len(sales_data)  # Nombre de ventes
            total_sold = sum(sale.quantity for sale in sales_data)  # Quantité totale vendue
            total_revenue = sum(float(sale.revenue) for sale in sales_data)  # Revenus totaux
            average_quantity = total_sold / total_sales if total_sales > 0 else 0.0
            last_sale = max(sale.event_date for sale in sales_data)
            
            return {
                'total_sold': total_sold,
                'total_sales': total_sales,
                'total_revenue': total_revenue,
                'average_quantity': round(average_quantity, 2),
                'last_sale': last_sale
            }
            
        except Exception as e:
            error_msg = f"Erreur lors de la récupération des statistiques de vente: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return None
            
        finally:
            db_manager.close_session()
