"""
Script d'initialisation des données pour le module Boutique
Crée les tables et ajoute des données de base au premier lancement
"""

import logging
from datetime import datetime
from decimal import Decimal

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_boutique_data(db_session):
    """
    Initialise les données de base pour le module Boutique
    
    Args:
        db_session: Session de base de données SQLAlchemy
        
    Returns:
        bool: True si l'initialisation a réussi
    """
    try:
        # Importer tous les modèles pour créer les tables
        from ayanna_erp.modules.boutique.model.models import (
            ShopClient, ShopService, 
            ShopPanier, ShopPanierProduct, ShopPanierService,
            ShopPayment, ShopExpense, ShopComptesConfig
        )
        from ayanna_erp.modules.core.models import CoreProduct, CoreProductCategory, POSProductAccess
        from ayanna_erp.modules.stock.models import StockWarehouse, StockProduitEntrepot, StockMovement
        from ayanna_erp.database.base import Base
        from ayanna_erp.database.database_manager import DatabaseManager
        
        # Obtenir l'engine pour créer les tables
        db_manager = DatabaseManager()
        
        # Créer toutes les tables si elles n'existent pas
        Base.metadata.create_all(db_manager.engine)
        logger.info("Tables du module Boutique créées/vérifiées")
        
        # Vérifier si des catégories existent déjà pour cette entreprise
        existing_categories = db_session.query(CoreProductCategory).filter_by(entreprise_id=1).count()
        if existing_categories > 0:
            logger.info(f"Module Boutique déjà initialisé ({existing_categories} catégories)")
            return True
        
        # Créer des catégories de base
        categories_data = [
            {
                'entreprise_id': 1,
                'name': 'Alimentation',
                'description': 'Produits alimentaires et boissons'
            },
            {
                'entreprise_id': 1,
                'name': 'Électronique',
                'description': 'Appareils électroniques et accessoires'
            },
            {
                'entreprise_id': 1,
                'name': 'Vêtements',
                'description': 'Vêtements et accessoires'
            },
            {
                'entreprise_id': 1,
                'name': 'Maison & Jardin',
                'description': 'Articles pour la maison et le jardin'
            },
            {
                'entreprise_id': 1,
                'name': 'Santé & Beauté',
                'description': 'Produits de santé et de beauté'
            },
            {
                'entreprise_id': 1,
                'name': 'Services',
                'description': 'Services divers'
            }
        ]
        
        # Ajouter les catégories
        categories_created = []
        for cat_data in categories_data:
            category = CoreProductCategory(**cat_data)
            db_session.add(category)
            categories_created.append(category)
        
        db_session.flush()  # Pour obtenir les IDs
        
        # Créer des produits de démonstration
        products_data = [
            # Alimentation
            {
                'entreprise_id': 1,
                'category_id': categories_created[0].id,
                'name': 'Coca Cola 33cl',
                'description': 'Boisson gazeuse rafraîchissante',
                'price_unit': 1.50,
                'cost': 0.80,
                'unit': 'bouteille',
                'initial_stock': 50,  # Stock initial pour le POS
                'min_stock': 10       # Stock minimum pour l'entrepôt
            },
            {
                'entreprise_id': 1,
                'category_id': categories_created[0].id,
                'name': 'Pain Complet',
                'description': 'Pain de mie complet 500g',
                'price_unit': 2.00,
                'cost': 1.20,
                'unit': 'unité',
                'initial_stock': 25,
                'min_stock': 5
            },
            {
                'entreprise_id': 1,
                'category_id': categories_created[0].id,
                'name': 'Eau Minérale 1.5L',
                'description': 'Eau minérale naturelle',
                'price_unit': 0.80,
                'cost': 0.40,
                'unit': 'bouteille',
                'initial_stock': 100,
                'min_stock': 20
            },
            
            # Électronique
            {
                'entreprise_id': 1,
                'category_id': categories_created[1].id,
                'name': 'Chargeur USB-C',
                'description': 'Chargeur rapide USB-C 20W',
                'price_unit': 15.00,
                'cost': 8.00,
                'unit': 'pièce',
                'initial_stock': 20,
                'min_stock': 5
            },
            {
                'entreprise_id': 1,
                'category_id': categories_created[1].id,
                'name': 'Écouteurs Bluetooth',
                'description': 'Écouteurs sans fil Bluetooth 5.0',
                'price_unit': 35.00,
                'cost': 20.00,
                'unit': 'paire',
                'initial_stock': 15,
                'min_stock': 3
            },
            
            # Vêtements
            {
                'entreprise_id': 1,
                'category_id': categories_created[2].id,
                'name': 'T-shirt Unisexe',
                'description': 'T-shirt 100% coton, taille M',
                'price_unit': 12.00,
                'cost': 6.00,
                'unit': 'pièce',
                'initial_stock': 30,
                'min_stock': 5
            }
        ]
        
        # Ajouter les produits
        products_created = []
        for prod_data in products_data:
            # Extraire les données de stock avant de créer le produit
            initial_stock = prod_data.pop('initial_stock', 0.0)
            min_stock = prod_data.pop('min_stock', 0.0)
            
            # S'assurer que prod_data contient 'category_id' et non 'category'
            if 'category' in prod_data:
                prod_data['category_id'] = prod_data.pop('category')
            product = CoreProduct(**prod_data)
            db_session.add(product)
            products_created.append((product, initial_stock, min_stock))
        
        db_session.flush()  # Pour obtenir les IDs des produits
        
        # Initialiser les stocks pour chaque produit
        _initialize_product_stocks(db_session, products_created)
        
        # Créer les liaisons POS-Produit pour le POS Boutique (id=2)
        boutique_pos_id = 2  # ID du POS Boutique Centrale
        for product, _, _ in products_created:  # Décompacter le tuple (product, initial_stock, min_stock)
            pos_access = POSProductAccess(
                pos_id=boutique_pos_id,
                product_id=product.id,
                is_available=True,
                display_order=0
            )
            db_session.add(pos_access)
        
        # Créer des services de base
        services_data = [
            {
                'entreprise_id': 1,
                'name': 'Livraison à domicile',
                'description': 'Service de livraison dans un rayon de 10km',
                'price': 5.00,
                'cost': 2.00
            },
            {
                'entreprise_id': 1,
                'name': 'Emballage cadeau',
                'description': 'Service d\'emballage cadeau personnalisé',
                'price': 3.00,
                'cost': 1.00
            },
            {
                'entreprise_id': 1,
                'name': 'Installation',
                'description': 'Service d\'installation pour équipements électroniques',
                'price': 25.00,
                'cost': 15.00
            }
        ]
        
        # Ajouter les services
        for serv_data in services_data:
            service = ShopService(**serv_data)
            db_session.add(service)
        
        # Créer un client de démonstration
        client_demo = ShopClient(
            pos_id=1,
            nom='Client',
            prenom='Démonstration',
            telephone='+243000000000',
            email='demo@client.com',
            adresse='Adresse de démonstration',
            ville='Kinshasa',
            type_client='Particulier'
        )
        db_session.add(client_demo)
        
        # Créer la configuration des comptes (optionnelle)
        comptes_config = ShopComptesConfig(
            pos_id=1,
            caisse_especes_id=571,  # Compte caisse par défaut
            caisse_mobile_money_id=571,
            caisse_banque_id=521,
            compte_vente_produits_id=701,  # Ventes de marchandises
            compte_vente_services_id=706,  # Services vendus
            compte_client_id=411  # Clients
        )
        db_session.add(comptes_config)
        
        # Valider toutes les modifications
        db_session.commit()
        
        logger.info(f"Module Boutique initialisé avec succès:")
        logger.info(f"  - {len(categories_data)} catégories créées")
        logger.info(f"  - {len(products_data)} produits de démonstration")
        logger.info(f"  - {len(services_data)} services de base")
        logger.info(f"  - 1 client de démonstration")
        logger.info(f"  - Configuration des comptes")
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation du module Boutique: {e}")
        db_session.rollback()
        import traceback
        traceback.print_exc()
        return False


def _initialize_product_stocks(db_session, products_created):
    """
    Initialise les stocks pour les produits créés
    
    Args:
        db_session: Session de base de données
        products_created: Liste de tuples (product, initial_stock, min_stock)
    """
    from ayanna_erp.modules.stock.models import StockWarehouse, StockProduitEntrepot, StockMovement
    from decimal import Decimal
    
    try:
        # Récupérer l'entrepôt POS Boutique par son code
        pos_warehouse = db_session.query(StockWarehouse).filter_by(code='POS_2').first()
        
        if not pos_warehouse:
            logger.error("Entrepôt POS Boutique (POS_2) introuvable")
            return
        
        # Initialiser les stocks pour chaque produit uniquement sur l'entrepôt POS Boutique
        for product, initial_stock, min_stock in products_created:
            # Créer l'entrée stock produit-entrepôt
            stock_quantity = Decimal(str(initial_stock))
            unit_cost = Decimal(str(product.cost)) if product.cost else Decimal('0.0')
            
            stock_entry = StockProduitEntrepot(
                product_id=product.id,
                warehouse_id=pos_warehouse.id,
                quantity=stock_quantity,
                reserved_quantity=Decimal('0.0'),
                unit_cost=unit_cost,
                total_cost=stock_quantity * unit_cost,
                min_stock_level=Decimal(str(min_stock)),
                last_movement_date=datetime.now()
            )
            db_session.add(stock_entry)
            
            # Si il y a un stock initial, créer un mouvement d'entrée
            if initial_stock > 0:
                movement = StockMovement(
                    product_id=product.id,
                    warehouse_id=pos_warehouse.id,
                    movement_type='ENTREE',
                    quantity=stock_quantity,
                    unit_cost=unit_cost,
                    total_cost=stock_quantity * unit_cost,
                    reference=f'INIT-{product.id}',
                    description=f'Stock initial pour {product.name}',
                    movement_date=datetime.now(),
                    user_id=1  # Utilisateur système
                )
                db_session.add(movement)
        
        db_session.flush()
        logger.info(f"Stocks initialisés pour tous les produits sur l'entrepôt POS Boutique (ID: {pos_warehouse.id})")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation des stocks: {e}")
        raise


def initialize_data(db_session):
    """Point d'entrée pour l'initialisation du module Boutique"""
    return init_boutique_data(db_session)


def initialize_boutique_data():
    """Fonction de compatibilité pour l'ancienne API"""
    from ayanna_erp.database.database_manager import DatabaseManager
    
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    try:
        return init_boutique_data(session)
    finally:
        session.close()


if __name__ == "__main__":
    # Test de l'initialisation
    success = initialize_boutique_data()
    if success:
        print("✅ Initialisation du module Boutique réussie")
    else:
        print("❌ Échec de l'initialisation du module Boutique")