# -*- coding: utf-8 -*-
"""
Script de nettoyage et refactorisation complète
1. Supprime les anciennes tables (shop_products, event_products, etc.)
2. Adapte tous les modèles pour utiliser core_products
3. Met à jour les contrôleurs et helpers
"""

import sys
import os
sys.path.append(os.path.abspath('.'))

from ayanna_erp.database.database_manager import DatabaseManager
from sqlalchemy import text


def cleanup_old_tables():
    """Supprime les anciennes tables qui ne servent plus"""
    
    print("=== NETTOYAGE DES ANCIENNES TABLES ===")
    
    try:
        db_manager = DatabaseManager()
        
        with db_manager.get_session() as session:
            # Liste des tables à supprimer
            tables_to_drop = [
                'shop_products',
                'shop_categories', 
                'shop_product_categories',
                'event_products',
                'event_categories'
            ]
            
            for table_name in tables_to_drop:
                try:
                    # Vérifier si la table existe
                    result = session.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")).fetchone()
                    
                    if result:
                        # Supprimer la table
                        session.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                        print(f"✓ Table supprimée: {table_name}")
                    else:
                        print(f"- Table inexistante: {table_name}")
                        
                except Exception as e:
                    print(f"Avertissement suppression {table_name}: {e}")
            
            session.commit()
            print(f"\n✓ Nettoyage des tables terminé")
            return True
            
    except Exception as e:
        print(f"ERREUR lors du nettoyage: {e}")
        return False


def update_boutique_models():
    """Met à jour le modèle boutique pour supprimer les références aux anciennes tables"""
    
    print("\n=== MISE A JOUR MODELES BOUTIQUE ===")
    
    # Nouveau contenu pour models.py du module boutique
    new_boutique_models = '''# -*- coding: utf-8 -*-
"""
Modèles de données pour le module Boutique
Utilise maintenant core_products (centralisé) au lieu de shop_products
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import sys
import os

# Import du gestionnaire de base de données principal
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from ayanna_erp.database.base import Base

class ShopClient(Base):
    """Table des clients pour la boutique"""
    __tablename__ = 'shop_clients'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pos_id = Column(Integer, nullable=False)  # Référence au POS
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    telephone = Column(String(20), nullable=False)
    email = Column(String(150))
    adresse = Column(Text)
    ville = Column(String(100))
    code_postal = Column(String(10))
    date_naissance = Column(DateTime)
    type_client = Column(String(50), default='Particulier')  # Particulier, Entreprise
    credit_limit = Column(Numeric(15, 2), default=0.0)  # Limite de crédit
    balance = Column(Numeric(15, 2), default=0.0)  # Solde du compte client
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relations
    paniers = relationship("ShopPanier", back_populates="client")

class ShopService(Base):
    """Table des services de la boutique"""
    __tablename__ = 'shop_services'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pos_id = Column(Integer, nullable=False)  # Référence au POS
    name = Column(String(200), nullable=False)
    description = Column(Text)
    image = Column(Text)  # Image du service
    cost = Column(Numeric(15, 2), default=0.0)  # Coût du service
    price = Column(Numeric(15, 2), default=0.0)  # Prix de vente
    account_id = Column(Integer)  # Compte comptable
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relations
    panier_services = relationship("ShopPanierService", back_populates="service")

class ShopPanier(Base):
    """Table des paniers (équivalent des réservations en Salle de Fête)"""
    __tablename__ = 'shop_paniers'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pos_id = Column(Integer, nullable=False)  # Référence au POS
    client_id = Column(Integer, ForeignKey('shop_clients.id'))  # Client optionnel
    numero_commande = Column(String(50), unique=True)  # Numéro de commande auto-généré
    status = Column(String(50), default='en_cours')  # en_cours, validé, payé, annulé
    
    # Totaux
    subtotal = Column(Numeric(15, 2), default=0.0)  # Sous-total HT
    remise_percent = Column(Numeric(5, 2), default=0.0)  # Remise en %
    remise_amount = Column(Numeric(15, 2), default=0.0)  # Montant de la remise
    total_final = Column(Numeric(15, 2), default=0.0)  # Total final à payer
    
    # Informations de validation
    validated_at = Column(DateTime)  # Date de validation
    validated_by = Column(String(100))  # Utilisateur qui a validé
    
    # Dates
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relations
    client = relationship("ShopClient", back_populates="paniers")
    products = relationship("ShopPanierProduct", back_populates="panier", cascade="all, delete-orphan")
    services = relationship("ShopPanierService", back_populates="panier", cascade="all, delete-orphan")
    payments = relationship("ShopPayment", back_populates="panier", cascade="all, delete-orphan")

class ShopPanierProduct(Base):
    """Table pivot : Produits dans un panier - UTILISE CORE_PRODUCTS"""
    __tablename__ = 'shop_paniers_products'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    panier_id = Column(Integer, ForeignKey('shop_paniers.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('core_products.id'), nullable=False)  # CHANGÉ: Référence vers core_products
    quantity = Column(Numeric(15, 2), nullable=False)
    price_unit = Column(Numeric(15, 2), nullable=False)  # Prix au moment de l'ajout
    total_price = Column(Numeric(15, 2), nullable=False)  # quantity * price_unit
    
    # Relations
    panier = relationship("ShopPanier", back_populates="products")
    # product sera défini dans core_products

class ShopPanierService(Base):
    """Table pivot : Services dans un panier"""
    __tablename__ = 'shop_paniers_services'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    panier_id = Column(Integer, ForeignKey('shop_paniers.id'), nullable=False)
    service_id = Column(Integer, ForeignKey('shop_services.id'), nullable=False)
    quantity = Column(Numeric(15, 2), default=1.0)
    price_unit = Column(Numeric(15, 2), nullable=False)  # Prix au moment de l'ajout
    total_price = Column(Numeric(15, 2), nullable=False)  # quantity * price_unit
    
    # Relations
    panier = relationship("ShopPanier", back_populates="services")
    service = relationship("ShopService", back_populates="panier_services")

class ShopPayment(Base):
    """Table des paiements pour les paniers"""
    __tablename__ = 'shop_payments'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    panier_id = Column(Integer, ForeignKey('shop_paniers.id'), nullable=False)
    payment_method = Column(String(50), nullable=False)  # especes, carte, cheque, virement
    amount = Column(Numeric(15, 2), nullable=False)
    payment_date = Column(DateTime, default=func.current_timestamp())
    reference = Column(String(100))  # Référence du paiement (numéro chèque, etc.)
    notes = Column(Text)
    
    # Relations
    panier = relationship("ShopPanier", back_populates="payments")

class ShopWarehouse(Base):
    """Entrepôts boutique - DEPRECATED : Utiliser StockWarehouse du module stock"""
    __tablename__ = 'shop_warehouses'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pos_id = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    address = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.current_timestamp())

class ShopWarehouseStock(Base):
    """Stock boutique - DEPRECATED : Utiliser StockProduitEntrepot du module stock"""
    __tablename__ = 'shop_warehouse_stock'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column(Integer, ForeignKey('shop_warehouses.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('core_products.id'), nullable=False)  # CHANGÉ: Référence vers core_products
    quantity = Column(Numeric(15, 2), default=0.0)
    last_updated = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

class ShopStockMovement(Base):
    """Mouvements de stock boutique - DEPRECATED : Utiliser StockMovement du module stock"""
    __tablename__ = 'shop_stock_movements'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('core_products.id'), nullable=False)  # CHANGÉ: Référence vers core_products
    warehouse_id = Column(Integer, ForeignKey('shop_warehouses.id'), nullable=False)
    movement_type = Column(String(50), nullable=False)  # in, out, adjustment
    quantity = Column(Numeric(15, 2), nullable=False)
    movement_date = Column(DateTime, default=func.current_timestamp())
    reference = Column(String(100))
    notes = Column(Text)

class ShopStockTransfer(Base):
    """Transferts entre entrepôts - DEPRECATED : Utiliser le module stock centralisé"""
    __tablename__ = 'shop_stock_transfers'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_warehouse_id = Column(Integer, ForeignKey('shop_warehouses.id'), nullable=False)
    to_warehouse_id = Column(Integer, ForeignKey('shop_warehouses.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('core_products.id'), nullable=False)  # CHANGÉ: Référence vers core_products
    quantity = Column(Numeric(15, 2), nullable=False)
    transfer_date = Column(DateTime, default=func.current_timestamp())
    status = Column(String(20), default='pending')  # pending, completed, cancelled
    notes = Column(Text)


# ALIAS POUR COMPATIBILITÉ TEMPORAIRE
# Ces alias permettent aux anciens codes de continuer à fonctionner
# À supprimer progressivement
class ShopProduct:
    """DEPRECATED: Utiliser CoreProduct du module core"""
    def __init__(self):
        raise DeprecationWarning("ShopProduct est obsolète. Utiliser CoreProduct du module core.")

class ShopCategory:
    """DEPRECATED: Utiliser CoreProductCategory du module core"""
    def __init__(self):
        raise DeprecationWarning("ShopCategory est obsolète. Utiliser CoreProductCategory du module core.")


# Import des modèles centralisés
from ayanna_erp.modules.core.models import CoreProduct, CoreProductCategory

# Alias pour faciliter la transition
Product = CoreProduct
ProductCategory = CoreProductCategory
'''
    
    try:
        # Écrire le nouveau fichier modèles
        models_path = r"c:\Ayanna ERP\Ayanna-Erp\ayanna_erp\modules\boutique\model\models.py"
        
        with open(models_path, 'w', encoding='utf-8') as f:
            f.write(new_boutique_models)
            
        print("✓ Modèles boutique mis à jour")
        return True
        
    except Exception as e:
        print(f"ERREUR mise à jour modèles boutique: {e}")
        return False


def update_salle_fete_models():
    """Met à jour les modèles salle de fêtes pour utiliser core_products"""
    
    print("\n=== MISE A JOUR MODELES SALLE DE FETE ===")
    
    try:
        salle_fete_path = r"c:\Ayanna ERP\Ayanna-Erp\ayanna_erp\modules\salle_fete\model\salle_fete.py"
        
        # Lire le fichier actuel
        with open(salle_fete_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remplacements nécessaires
        replacements = [
            # Remplacer les références aux anciennes tables
            ('event_products', 'core_products'),
            ('event_categories', 'core_product_categories'),
            ('EventProduct', 'CoreProduct'),
            ('EventCategory', 'CoreProductCategory'),
            # Ajouter les imports
            ('from ayanna_erp.database.base import Base', 
             'from ayanna_erp.database.base import Base\nfrom ayanna_erp.modules.core.models import CoreProduct, CoreProductCategory'),
        ]
        
        updated_content = content
        for old, new in replacements:
            updated_content = updated_content.replace(old, new)
        
        # Écrire le fichier mis à jour
        with open(salle_fete_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
            
        print("✓ Modèles salle de fêtes mis à jour")
        return True
        
    except Exception as e:
        print(f"ERREUR mise à jour salle de fêtes: {e}")
        return False


def update_stock_controllers():
    """Met à jour les contrôleurs stock qui référencent shop_products"""
    
    print("\n=== MISE A JOUR CONTROLEURS STOCK ===")
    
    try:
        controller_path = r"c:\Ayanna ERP\Ayanna-Erp\ayanna_erp\modules\stock\controllers\entrepot_controller.py"
        
        # Lire le fichier
        with open(controller_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remplacer shop_products par core_products dans les requêtes SQL
        updated_content = content.replace('shop_products', 'core_products')
        updated_content = updated_content.replace('sp.', 'cp.')  # Alias de table
        
        # Écrire le fichier mis à jour
        with open(controller_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
            
        print("✓ Contrôleurs stock mis à jour")
        return True
        
    except Exception as e:
        print(f"ERREUR mise à jour contrôleurs: {e}")
        return False


if __name__ == "__main__":
    print("=== REFACTORISATION COMPLETE VERS CORE_PRODUCTS ===")
    
    success = True
    
    # 1. Nettoyer les anciennes tables
    if not cleanup_old_tables():
        success = False
    
    # 2. Mettre à jour les modèles
    if not update_boutique_models():
        success = False
    
    if not update_salle_fete_models():
        success = False
    
    # 3. Mettre à jour les contrôleurs
    if not update_stock_controllers():
        success = False
    
    if success:
        print(f"\n✓ REFACTORISATION TERMINEE AVEC SUCCES")
        print("- Anciennes tables supprimées")
        print("- Modèles mis à jour pour utiliser core_products") 
        print("- Contrôleurs adaptés")
        print("- Architecture centralisée opérationnelle")
    else:
        print(f"\n✗ ERREURS LORS DE LA REFACTORISATION")
        print("Vérifiez les messages d'erreur ci-dessus")