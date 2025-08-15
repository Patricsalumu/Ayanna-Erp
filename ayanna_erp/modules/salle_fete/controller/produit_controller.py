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
from model.salle_fete import EventProduct, EventStockMovement, get_database_manager


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
                account_id=product_data.get('account_id'),
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
            
            # Convertir en dictionnaires pour la vue
            products_data = []
            for product in products:
                products_data.append({
                    'id': product.id,
                    'name': product.name or '',
                    'description': product.description or '',
                    'category': product.category or '',
                    'unit': product.unit or 'pièce',
                    'cost': float(product.cost or 0),
                    'price_unit': float(product.price_unit or 0),
                    'stock_quantity': float(product.stock_quantity or 0),
                    'stock_min': float(product.stock_min or 0),
                    'is_active': product.is_active,
                    'created_at': product.created_at
                })
            
            print(f"✅ {len(products_data)} produits chargés")
            self.products_loaded.emit(products_data)
            return products_data
            
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
