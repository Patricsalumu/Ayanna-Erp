"""
Contrôleur principal pour le module boutique.
Gère la logique métier des produits, services, panier et paiements.
"""

from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import or_
from PyQt6.QtCore import QObject, pyqtSignal

from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.core.models import CoreProduct, CoreProductCategory
from ..model.models import (
    ShopClient, ShopService,
    ShopPanier, ShopPanierProduct, ShopPanierService,
    ShopPayment, ShopExpense, ShopComptesConfig
)
from ..helpers.stock_helper import BoutiqueStockHelper


class BoutiqueController(QObject):
    """Contrôleur principal pour la gestion de la boutique."""
    
    # Signaux pour la communication avec l'interface
    panier_updated = pyqtSignal()
    payment_completed = pyqtSignal(int)  # ID du paiement
    stock_updated = pyqtSignal(int)  # ID du produit
    
    def __init__(self, pos_id: int = None, entreprise_id: int = None):
        super().__init__()
        self.db_manager = DatabaseManager()
        
        # Crée une session persistante pour widgets/controllers
        self.session = self.db_manager.get_session()  # instance de sqlalchemy.orm.Session
        
        self._panier_actuel: Optional[ShopPanier] = None
        self._initialized = False
        self.pos_id = pos_id

        # Récupérer l'ID de l'entreprise de l'utilisateur connecté
        from ayanna_erp.core.session_manager import SessionManager
        if entreprise_id:
            self.entreprise_id = entreprise_id
        else:
            # Récupérer l'entreprise de l'utilisateur connecté
            connected_enterprise_id = SessionManager.get_current_enterprise_id()
            self.entreprise_id = connected_enterprise_id if connected_enterprise_id else 1
            
        self.stock_helper = BoutiqueStockHelper(pos_id=pos_id, entreprise_id=self.entreprise_id)
    
    def _ensure_initialized(self, session: Session) -> bool:
        """Garantit que le module Boutique est initialisé (tables et données de base)."""
        if self._initialized:
            return True
            
        try:
            # Essayer de compter les catégories pour vérifier si les tables existent
            try:
                categories_count = session.query(CoreProductCategory).count()
                needs_initialization = (categories_count == 0)
            except Exception:
                # Les tables n'existent pas encore
                needs_initialization = True
            
            if needs_initialization:
                # Lancer l'initialisation complète
                print("🔄 Initialisation du module Boutique...")
                from ..init_boutique_data import init_boutique_data
                success = init_boutique_data(session)
                
                if success:
                    print("✅ Module Boutique initialisé avec succès")
                    self._initialized = True
                    return True
                else:
                    print("❌ Échec de l'initialisation du module Boutique")
                    return False
            else:
                # Le module est déjà initialisé
                self._initialized = True
                return True
                
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation du module Boutique: {e}")
            return False
        
    # =================== GESTION DES CATÉGORIES ===================
    
    def get_categories(self, session: Session) -> List[CoreProductCategory]:
        """Récupère toutes les catégories actives."""
        # Assurer l'initialisation du module au premier accès
        if not self._ensure_initialized(session):
            return []
            
        return session.query(CoreProductCategory).filter(CoreProductCategory.is_active == True).order_by(CoreProductCategory.name).all()
    
    def create_category(self, session: Session, nom: str, description: str = None) -> CoreProductCategory:
        """Crée une nouvelle catégorie."""
        category = CoreProductCategory(
            pos_id=self.pos_id,  # Ajouter le pos_id manquant
            name=nom,
            description=description,
            is_active=True
        )
        session.add(category)
        session.commit()
        session.refresh(category)
        return category
    
    def update_category(self, session: Session, category_id: int, nom: str = None, 
                       description: str = None, is_active: bool = None) -> CoreProductCategory:
        """Met à jour une catégorie."""
        category = session.query(CoreProductCategory).filter(CoreProductCategory.id == category_id).first()
        if not category:
            raise ValueError(f"Catégorie avec l'ID {category_id} introuvable")
        
        if nom is not None:
            category.name = nom
        if description is not None:
            category.description = description
        if is_active is not None:
            category.is_active = is_active
            
        session.commit()
        session.refresh(category)
        return category
    
    # =================== GESTION DES PRODUITS ===================
    
    def get_products(self, session: Session, category_id: Optional[int] = None, 
                    search_term: str = None, active_only: bool = True) -> List[CoreProduct]:
        """Récupère les produits avec filtres optionnels."""
        # Assurer l'initialisation du module au premier accès
        if not self._ensure_initialized(session):
            return []
            
        query = session.query(CoreProduct)
        
        if active_only:
            query = query.filter(CoreProduct.is_active == True)
        
        if category_id:
            query = query.filter(CoreProduct.category_id == category_id)
        
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(
                (CoreProduct.name.ilike(search_pattern)) |
                (CoreProduct.description.ilike(search_pattern))
            )
        
        return query.order_by(CoreProduct.name).all()
    
    def get_product_by_id(self, session: Session, product_id: int) -> Optional[CoreProduct]:
        """Récupère un produit par son ID."""
        return session.query(CoreProduct).filter(CoreProduct.id == product_id).first()
    
    def create_product(self, session: Session, nom: str, prix: Decimal, category_id: int,
                      description: str = None, unit: str = "unité", 
                      stock_initial: int = 0) -> CoreProduct:
        """Crée un nouveau produit avec stock initial."""
        # Vérifier que la catégorie existe
        category = session.query(CoreProductCategory).filter(CoreProductCategory.id == category_id).first()
        if not category:
            raise ValueError(f"Catégorie avec l'ID {category_id} introuvable")
        
        product = CoreProduct(
            pos_id=self.pos_id,  # Ajouter le pos_id manquant
            name=nom,
            description=description,
            price_unit=prix,
            unit=unit,
            category_id=category_id,
            is_active=True
        )
        session.add(product)
        session.flush()  # Pour obtenir l'ID
        
        # Créer les entrées stock dans TOUS les entrepôts de l'entreprise
        self.stock_helper.create_product_stock_in_all_warehouses(
            session=session,
            product_id=product.id,
            initial_stock=stock_initial
        )
        
        session.commit()
        session.refresh(product)
        return product
    
    def get_product_stock_total(self, session: Session, product_id: int) -> int:
        """Calcule le stock total disponible pour un produit."""
        stock_total = self.stock_helper.get_product_stock_total(session, product_id)
        return int(stock_total)
    
    # =================== GESTION DES SERVICES ===================
    
    def get_services(self, session: Session, search_term: str = None, 
                    active_only: bool = True) -> List[ShopService]:
        """Récupère les services avec filtres optionnels."""
        query = session.query(ShopService)
        
        if active_only:
            query = query.filter(ShopService.is_active == True)
        
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(
                (ShopService.name.ilike(search_pattern)) |
                (ShopService.description.ilike(search_pattern))
            )
        
        return query.order_by(ShopService.name).all()
    
    def create_service(self, session: Session, nom: str, prix: Decimal,
                      description: str = None, duree_estimee: int = None) -> ShopService:
        """Crée un nouveau service."""
        service = ShopService(
            pos_id=self.pos_id,  # Ajouter le pos_id manquant
            nom=nom,
            description=description,
            prix=prix,
            duree_estimee=duree_estimee,
            is_active=True
        )
        session.add(service)
        session.commit()
        session.refresh(service)
        return service
    
    # =================== GESTION DU PANIER ===================
    
    def create_panier(self, session: Session, client_id: Optional[int] = None) -> ShopPanier:
        """Crée un nouveau panier."""
        panier = ShopPanier(
            pos_id=self.pos_id,  # Ajouter le pos_id manquant
            client_id=client_id,
            status="ouvert",
            total=Decimal('0.00')
        )
        session.add(panier)
        session.commit()
        session.refresh(panier)
        self._panier_actuel = panier
        return panier
    
    def get_panier_actuel(self, session: Session) -> Optional[ShopPanier]:
        """Récupère le panier actuellement ouvert."""
        if self._panier_actuel:
            session.refresh(self._panier_actuel)
            return self._panier_actuel
        
        # Chercher un panier ouvert
        panier = session.query(ShopPanier).filter(
            ShopPanier.status == "ouvert"
    ).order_by(ShopPanier.created_at.desc()).first()
        
        self._panier_actuel = panier
        return panier
    
    def add_product_to_panier(self, session: Session, product_id: int, 
                             quantite: int = 1) -> Tuple[bool, str]:
        """Ajoute un produit au panier actuel."""
        # Vérifier le produit
        product = self.get_product_by_id(session, product_id)
        if not product or not product.is_active:
            return False, "Produit introuvable ou inactif"
        
        # Vérifier le stock
        stock_disponible = self.get_product_stock_total(session, product_id)
        if stock_disponible < quantite:
            return False, f"Stock insuffisant. Disponible: {stock_disponible}"
        
        # Récupérer ou créer le panier
        panier = self.get_panier_actuel(session)
        if not panier:
            panier = self.create_panier(session)
        
        # Vérifier si le produit existe déjà dans le panier
        existing_item = session.query(ShopPanierProduct).filter(
            ShopPanierProduct.panier_id == panier.id,
            ShopPanierProduct.product_id == product_id
        ).first()
        
        if existing_item:
            # Vérifier que la nouvelle quantité ne dépasse pas le stock
            nouvelle_quantite = existing_item.quantite + quantite
            if stock_disponible < nouvelle_quantite:
                return False, f"Stock insuffisant. Disponible: {stock_disponible}, demandé: {nouvelle_quantite}"
            
            existing_item.quantite = nouvelle_quantite
            existing_item.sous_total = existing_item.quantite * product.prix
        else:
            # Créer une nouvelle ligne
            panier_product = ShopPanierProduct(
                panier_id=panier.id,
                product_id=product_id,
                quantite=quantite,
                prix_unitaire=product.prix,
                sous_total=quantite * product.prix
            )
            session.add(panier_product)
        
        # Recalculer le total du panier
        self._recalculate_panier_total(session, panier.id)
        session.commit()
        
        self.panier_updated.emit()
        return True, "Produit ajouté au panier"
    
    def add_service_to_panier(self, session: Session, service_id: int, 
                             quantite: int = 1) -> Tuple[bool, str]:
        """Ajoute un service au panier actuel."""
        # Vérifier le service
        service = session.query(ShopService).filter(
            ShopService.id == service_id,
            ShopService.is_active == True
        ).first()
        
        if not service:
            return False, "Service introuvable ou inactif"
        
        # Récupérer ou créer le panier
        panier = self.get_panier_actuel(session)
        if not panier:
            panier = self.create_panier(session)
        
        # Vérifier si le service existe déjà dans le panier
        existing_item = session.query(ShopPanierService).filter(
            ShopPanierService.panier_id == panier.id,
            ShopPanierService.service_id == service_id
        ).first()
        
        if existing_item:
            existing_item.quantite += quantite
            existing_item.sous_total = existing_item.quantite * service.prix
        else:
            # Créer une nouvelle ligne
            panier_service = ShopPanierService(
                panier_id=panier.id,
                service_id=service_id,
                quantite=quantite,
                prix_unitaire=service.prix,
                sous_total=quantite * service.prix
            )
            session.add(panier_service)
        
        # Recalculer le total du panier
        self._recalculate_panier_total(session, panier.id)
        session.commit()
        
        self.panier_updated.emit()
        return True, "Service ajouté au panier"
    
    def remove_item_from_panier(self, session: Session, item_type: str, 
                               item_id: int) -> Tuple[bool, str]:
        """Supprime un article du panier (product ou service)."""
        panier = self.get_panier_actuel(session)
        if not panier:
            return False, "Aucun panier ouvert"
        
        if item_type == "product":
            item = session.query(ShopPanierProduct).filter(
                ShopPanierProduct.panier_id == panier.id,
                ShopPanierProduct.id == item_id
            ).first()
        elif item_type == "service":
            item = session.query(ShopPanierService).filter(
                ShopPanierService.panier_id == panier.id,
                ShopPanierService.id == item_id
            ).first()
        else:
            return False, "Type d'article invalide"
        
        if not item:
            return False, "Article introuvable dans le panier"
        
        session.delete(item)
        
        # Recalculer le total du panier
        self._recalculate_panier_total(session, panier.id)
        session.commit()
        
        self.panier_updated.emit()
        return True, "Article supprimé du panier"
    
    def get_panier_content(self, session: Session) -> Dict[str, Any]:
        """Récupère le contenu complet du panier actuel."""
        panier = self.get_panier_actuel(session)
        if not panier:
            return {
                "panier": None,
                "products": [],
                "services": [],
                "total": Decimal('0.00')
            }
        
        # Récupérer les produits du panier
        panier_products = session.query(ShopPanierProduct).filter(
            ShopPanierProduct.panier_id == panier.id
        ).all()
        
        # Récupérer les services du panier
        panier_services = session.query(ShopPanierService).filter(
            ShopPanierService.panier_id == panier.id
        ).all()
        
        return {
            "panier": panier,
            "products": panier_products,
            "services": panier_services,
            "total": panier.total
        }
    
    def _recalculate_panier_total(self, session: Session, panier_id: int):
        """Recalcule le total du panier."""
        # Calculer le total des produits
        total_products = session.query(
            session.execute(
                'SELECT COALESCE(SUM(sous_total), 0) FROM shop_panier_products WHERE panier_id = :panier_id',
                {"panier_id": panier_id}
            ).scalar()
        ).scalar() or Decimal('0.00')
        
        # Calculer le total des services
        total_services = session.query(
            session.execute(
                'SELECT COALESCE(SUM(sous_total), 0) FROM shop_panier_services WHERE panier_id = :panier_id',
                {"panier_id": panier_id}
            ).scalar()
        ).scalar() or Decimal('0.00')
        
        # Mettre à jour le panier
        panier = session.query(ShopPanier).filter(ShopPanier.id == panier_id).first()
        if panier:
            panier.total = total_products + total_services
    
    def clear_panier(self, session: Session) -> Tuple[bool, str]:
        """Vide complètement le panier actuel."""
        panier = self.get_panier_actuel(session)
        if not panier:
            return False, "Aucun panier ouvert"
        
        # Supprimer tous les produits et services du panier
        session.query(ShopPanierProduct).filter(ShopPanierProduct.panier_id == panier.id).delete()
        session.query(ShopPanierService).filter(ShopPanierService.panier_id == panier.id).delete()
        
        # Remettre le total à zéro
        panier.total = Decimal('0.00')
        session.commit()
        
        self.panier_updated.emit()
        return True, "Panier vidé"
    
    # =================== GESTION DES PAIEMENTS ===================
    
    def get_payment_methods(self, session: Session) -> List[ShopComptesConfig]:
        """Récupère tous les moyens de paiement configurés."""
        return session.query(ShopComptesConfig).filter(
            ShopComptesConfig.is_active == True
        ).order_by(ShopComptesConfig.nom).all()
    
    def process_payment(self, session: Session, montant_total: Decimal,
                       payments_data: List[Dict[str, Any]], 
                       notes: str = None) -> Tuple[bool, str, Optional[int]]:
        """
        Traite un paiement avec possibilité de paiement multiple.
        
        Args:
            montant_total: Montant total à payer
            payments_data: Liste des paiements [{compte_config_id, montant}, ...]
            notes: Notes optionnelles
            
        Returns:
            Tuple (success, message, payment_id)
        """
        panier = self.get_panier_actuel(session)
        if not panier:
            return False, "Aucun panier ouvert", None
        
        # Vérifier que le montant total correspond
        total_payments = sum(Decimal(str(p.get('montant', 0))) for p in payments_data)
        if abs(total_payments - montant_total) > Decimal('0.01'):
            return False, f"Le total des paiements ({total_payments}) ne correspond pas au montant à payer ({montant_total})", None
        
        try:
            # Créer l'enregistrement de paiement principal
            payment = ShopPayment(
                panier_id=panier.id,
                montant_total=montant_total,
                status="payé",
                notes=notes
            )
            session.add(payment)
            session.flush()  # Pour obtenir l'ID
            
            # Créer les détails de paiement pour chaque méthode
            for payment_data in payments_data:
                compte_config_id = payment_data.get('compte_config_id')
                montant = Decimal(str(payment_data.get('montant', 0)))
                
                if montant <= 0:
                    continue
                
                # Vérifier que le compte de configuration existe
                compte_config = session.query(ShopComptesConfig).filter(
                    ShopComptesConfig.id == compte_config_id
                ).first()
                
                if not compte_config:
                    raise ValueError(f"Compte de configuration {compte_config_id} introuvable")
                
                # Ici, on pourrait ajouter une table ShopPaymentDetails si nécessaire
                # Pour l'instant, on stocke les détails dans les notes
                if payment.notes:
                    payment.notes += f"\n{compte_config.nom}: {montant}€"
                else:
                    payment.notes = f"{compte_config.nom}: {montant}€"
            
            # Marquer le panier comme fermé
            panier.status = "payé"
            
            # Décrémenter le stock des produits vendus
            panier_products = session.query(ShopPanierProduct).filter(
                ShopPanierProduct.panier_id == panier.id
            ).all()
            
            for panier_product in panier_products:
                self._decrement_stock(session, panier_product.product_id, panier_product.quantite)
            
            session.commit()
            session.refresh(payment)
            
            # Réinitialiser le panier actuel
            self._panier_actuel = None
            
            self.payment_completed.emit(payment.id)
            return True, f"Paiement de {montant_total}€ effectué avec succès", payment.id
            
        except Exception as e:
            session.rollback()
            return False, f"Erreur lors du paiement: {str(e)}", None
    
    def _decrement_stock(self, session: Session, product_id: int, quantite: int):
        """Décrémente le stock d'un produit."""
        success = self.stock_helper.decrement_stock(
            session=session,
            product_id=product_id,
            quantite=quantite,
            description="Vente boutique"
        )
        
        if not success:
            raise ValueError(f"Stock insuffisant pour le produit {product_id}")
        
        self.stock_updated.emit(product_id)
    
    # =================== GESTION DES CLIENTS ===================
    
    def get_clients(self, session: Session, search_term: str = None, limit: int = None, offset: int = 0):
        """Récupère les clients avec recherche optionnelle et pagination.

        Retourne un tuple `(clients, total)` lorsque `limit` est fourni (pagination).
        Si `limit` est None, retourne `(clients, total)` pour compatibilité.
        """
        query = session.query(ShopClient)

        if search_term:
            search_pattern = f"%{search_term}%"
            # Construire dynamiquement les conditions pour éviter d'évaluer des ClauseElement en bool
            conditions = [
                ShopClient.nom.ilike(search_pattern),
                ShopClient.prenom.ilike(search_pattern),
                ShopClient.email.ilike(search_pattern),
                ShopClient.telephone.ilike(search_pattern),
            ]
            # Ajouter les champs optionnels si présents sur le modèle
            if hasattr(ShopClient, 'adresse'):
                conditions.append(ShopClient.adresse.ilike(search_pattern))
            if hasattr(ShopClient, 'ville'):
                conditions.append(ShopClient.ville.ilike(search_pattern))
            if hasattr(ShopClient, 'pays'):
                conditions.append(ShopClient.pays.ilike(search_pattern))
            if hasattr(ShopClient, 'type_carte'):
                conditions.append(ShopClient.type_carte.ilike(search_pattern))
            if hasattr(ShopClient, 'carte_identite'):
                conditions.append(ShopClient.carte_identite.ilike(search_pattern))
            if hasattr(ShopClient, 'notes'):
                conditions.append(ShopClient.notes.ilike(search_pattern))

            query = query.filter(or_(*conditions))

        # Total pour pagination
        try:
            total = query.count()
        except Exception:
            total = 0

        query = query.order_by(ShopClient.nom, ShopClient.prenom)

        if limit is not None:
            query = query.offset(offset).limit(limit)

        clients = query.all()
        return clients, total
    
    def create_client(self, session: Session, nom: str, prenom: str = None,
                     email: str = None, telephone: str = None, 
                     adresse: str = None, pays: str = None,
                     carte_identite: str = None, type_carte: str = None) -> ShopClient:
        """Crée un nouveau client."""
        client = ShopClient(
            pos_id=self.pos_id,  # Ajouter le pos_id manquant
            nom=nom,
            prenom=prenom,
            email=email,
            telephone=telephone,
            adresse=adresse,
            pays=pays,
            carte_identite=carte_identite,
            type_carte=type_carte,
        )
        session.add(client)
        session.commit()
        session.refresh(client)
        return client
    
    def set_panier_client(self, session: Session, client_id: int) -> Tuple[bool, str]:
        """Associe un client au panier actuel."""
        panier = self.get_panier_actuel(session)
        if not panier:
            return False, "Aucun panier ouvert"
        
        client = session.query(ShopClient).filter(ShopClient.id == client_id).first()
        if not client:
            return False, "Client introuvable"
        
        panier.client_id = client_id
        session.commit()
        
        return True, f"Client {client.nom} {client.prenom or ''} associé au panier"