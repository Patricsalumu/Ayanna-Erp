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
            ShopClient, ShopCategory, ShopProduct, ShopService, 
            ShopPanier, ShopPanierProduct, ShopPanierService,
            ShopPayment, ShopExpense, ShopComptesConfig
        )
        from ayanna_erp.database.base import Base
        from ayanna_erp.database.database_manager import DatabaseManager
        
        # Obtenir l'engine pour créer les tables
        db_manager = DatabaseManager()
        
        # Créer toutes les tables si elles n'existent pas
        Base.metadata.create_all(db_manager.engine)
        logger.info("Tables du module Boutique créées/vérifiées")
        
        # Vérifier si des catégories existent déjà
        existing_categories = db_session.query(ShopCategory).count()
        if existing_categories > 0:
            logger.info(f"Module Boutique déjà initialisé ({existing_categories} catégories)")
            return True
        
        # Créer des catégories de base
        categories_data = [
            {
                'pos_id': 1,
                'name': 'Alimentation',
                'description': 'Produits alimentaires et boissons',
                'color': '#4CAF50',
                'order_display': 1
            },
            {
                'pos_id': 1,
                'name': 'Électronique',
                'description': 'Appareils électroniques et accessoires',
                'color': '#2196F3',
                'order_display': 2
            },
            {
                'pos_id': 1,
                'name': 'Vêtements',
                'description': 'Vêtements et accessoires',
                'color': '#E91E63',
                'order_display': 3
            },
            {
                'pos_id': 1,
                'name': 'Maison & Jardin',
                'description': 'Articles pour la maison et le jardin',
                'color': '#FF9800',
                'order_display': 4
            },
            {
                'pos_id': 1,
                'name': 'Santé & Beauté',
                'description': 'Produits de santé et de beauté',
                'color': '#9C27B0',
                'order_display': 5
            },
            {
                'pos_id': 1,
                'name': 'Services',
                'description': 'Services divers',
                'color': '#607D8B',
                'order_display': 6
            }
        ]
        
        # Ajouter les catégories
        categories_created = []
        for cat_data in categories_data:
            category = ShopCategory(**cat_data)
            db_session.add(category)
            categories_created.append(category)
        
        db_session.flush()  # Pour obtenir les IDs
        
        # Créer des produits de démonstration
        products_data = [
            # Alimentation
            {
                'pos_id': 1,
                'category_id': categories_created[0].id,
                'name': 'Coca Cola 33cl',
                'description': 'Boisson gazeuse rafraîchissante',
                'price_unit': 1.50,
                'cost': 0.80,
                'stock_quantity': 50,
                'stock_min': 10,
                'unit': 'bouteille'
            },
            {
                'pos_id': 1,
                'category_id': categories_created[0].id,
                'name': 'Pain Complet',
                'description': 'Pain de mie complet 500g',
                'price_unit': 2.00,
                'cost': 1.20,
                'stock_quantity': 25,
                'stock_min': 5,
                'unit': 'unité'
            },
            {
                'pos_id': 1,
                'category_id': categories_created[0].id,
                'name': 'Eau Minérale 1.5L',
                'description': 'Eau minérale naturelle',
                'price_unit': 0.80,
                'cost': 0.40,
                'stock_quantity': 100,
                'stock_min': 20,
                'unit': 'bouteille'
            },
            
            # Électronique
            {
                'pos_id': 1,
                'category_id': categories_created[1].id,
                'name': 'Chargeur USB-C',
                'description': 'Chargeur rapide USB-C 20W',
                'price_unit': 15.00,
                'cost': 8.00,
                'stock_quantity': 20,
                'stock_min': 5,
                'unit': 'pièce'
            },
            {
                'pos_id': 1,
                'category_id': categories_created[1].id,
                'name': 'Écouteurs Bluetooth',
                'description': 'Écouteurs sans fil Bluetooth 5.0',
                'price_unit': 35.00,
                'cost': 20.00,
                'stock_quantity': 15,
                'stock_min': 3,
                'unit': 'paire'
            },
            
            # Vêtements
            {
                'pos_id': 1,
                'category_id': categories_created[2].id,
                'name': 'T-shirt Unisexe',
                'description': 'T-shirt 100% coton, taille M',
                'price_unit': 12.00,
                'cost': 6.00,
                'stock_quantity': 30,
                'stock_min': 5,
                'unit': 'pièce'
            }
        ]
        
        # Ajouter les produits
        for prod_data in products_data:
            # S'assurer que prod_data contient 'category_id' et non 'category'
            if 'category' in prod_data:
                prod_data['category_id'] = prod_data.pop('category')
            product = ShopProduct(**prod_data)
            db_session.add(product)
        
        # Créer des services de base
        services_data = [
            {
                'pos_id': 1,
                'name': 'Livraison à domicile',
                'description': 'Service de livraison dans un rayon de 10km',
                'price': 5.00,
                'cost': 2.00
            },
            {
                'pos_id': 1,
                'name': 'Emballage cadeau',
                'description': 'Service d\'emballage cadeau personnalisé',
                'price': 3.00,
                'cost': 1.00
            },
            {
                'pos_id': 1,
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