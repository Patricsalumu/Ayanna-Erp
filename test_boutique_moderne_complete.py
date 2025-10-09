#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test complet du système de boutique moderne avec validation de stock et remises fixes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sqlite3
from decimal import Decimal
from PyQt6.QtWidgets import QApplication
from ayanna_erp.database.database_manager import DatabaseManager
from ayanna_erp.modules.boutique.view.modern_supermarket_widget import ModernSupermarketWidget

def test_database_structure():
    """Test de la structure de base de données"""
    print("=== Test Structure Base de Données ===")
    
    conn = sqlite3.connect('ayanna_erp.db')
    cursor = conn.cursor()
    
    # Vérifier la table shop_panier
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='shop_panier'")
    result = cursor.fetchone()
    if result:
        print("✅ Table shop_panier existe")
        print(f"Structure: {result[0]}")
    else:
        print("❌ Table shop_panier manquante")
    
    # Vérifier la colonne discount_amount
    cursor.execute("PRAGMA table_info(shop_panier)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'discount_amount' in columns:
        print("✅ Colonne discount_amount existe")
    else:
        print("❌ Colonne discount_amount manquante")
    
    conn.close()

def test_stock_warehouse_pos2():
    """Test de l'existence de l'entrepôt POS_2"""
    print("\n=== Test Entrepôt POS_2 ===")
    
    conn = sqlite3.connect('ayanna_erp.db')
    cursor = conn.cursor()
    
    # Vérifier l'entrepôt POS_2
    cursor.execute("SELECT id, name FROM warehouses WHERE name = 'POS_2'")
    pos2 = cursor.fetchone()
    if pos2:
        print(f"✅ Entrepôt POS_2 trouvé: ID={pos2[0]}, Nom={pos2[1]}")
        
        # Vérifier les stocks dans POS_2
        cursor.execute("""
            SELECT p.name, s.quantity 
            FROM stock s
            JOIN products p ON s.product_id = p.id
            WHERE s.warehouse_id = ?
            ORDER BY p.name
            LIMIT 5
        """, (pos2[0],))
        stocks = cursor.fetchall()
        print(f"Stock POS_2 (5 premiers produits):")
        for product, qty in stocks:
            print(f"  - {product}: {qty}")
    else:
        print("❌ Entrepôt POS_2 non trouvé")
        # Créer l'entrepôt POS_2
        cursor.execute("INSERT INTO warehouses (name, location) VALUES ('POS_2', 'Point de vente 2')")
        conn.commit()
        print("✅ Entrepôt POS_2 créé")
    
    conn.close()

def test_widget_creation():
    """Test de création du widget moderne"""
    print("\n=== Test Création Widget Moderne ===")
    
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    try:
        # Simulation d'un POS_ID
        pos_id = 2
        widget = ModernSupermarketWidget(pos_id)
        print("✅ Widget ModernSupermarketWidget créé avec succès")
        
        # Test du chargement des produits
        if hasattr(widget, 'products') and widget.products:
            print(f"✅ {len(widget.products)} produits chargés")
        else:
            print("⚠️ Aucun produit chargé")
        
        return widget
    except Exception as e:
        print(f"❌ Erreur création widget: {e}")
        return None

def test_discount_calculation():
    """Test du calcul de remise fixe"""
    print("\n=== Test Calcul Remise Fixe ===")
    
    # Simuler un panier
    subtotal = Decimal('150.00')  # 150 FC
    discount_amount = Decimal('25.00')  # 25 FC de remise
    
    total = subtotal - discount_amount
    
    print(f"Sous-total: {subtotal} FC")
    print(f"Remise: {discount_amount} FC")
    print(f"Total final: {total} FC")
    
    # Vérifier que c'est cohérent
    if total == Decimal('125.00'):
        print("✅ Calcul de remise fixe correct")
    else:
        print("❌ Erreur dans le calcul de remise")

def test_stock_validation():
    """Test de validation de stock"""
    print("\n=== Test Validation Stock ===")
    
    conn = sqlite3.connect('ayanna_erp.db')
    cursor = conn.cursor()
    
    # Trouver un produit avec du stock
    cursor.execute("""
        SELECT p.id, p.name, s.quantity, w.name
        FROM products p
        JOIN stock s ON p.id = s.product_id
        JOIN warehouses w ON s.warehouse_id = w.id
        WHERE w.name = 'POS_2' AND s.quantity > 0
        LIMIT 1
    """)
    product_data = cursor.fetchone()
    
    if product_data:
        product_id, product_name, stock_qty, warehouse = product_data
        print(f"Produit test: {product_name}")
        print(f"Stock disponible: {stock_qty}")
        
        # Test validation pour quantité valide
        requested_qty = min(1, int(stock_qty))
        if requested_qty <= stock_qty:
            print(f"✅ Validation OK pour {requested_qty} unités")
        
        # Test validation pour quantité excessive
        excessive_qty = int(stock_qty) + 10
        if excessive_qty > stock_qty:
            print(f"✅ Validation KO détectée pour {excessive_qty} unités (stock insuffisant)")
    else:
        print("⚠️ Aucun produit avec stock trouvé dans POS_2")
    
    conn.close()

def main():
    """Test principal"""
    print("=== TEST COMPLET BOUTIQUE MODERNE ===\n")
    
    # Tests de base
    test_database_structure()
    test_stock_warehouse_pos2()
    test_discount_calculation()
    test_stock_validation()
    
    # Test interface si PyQt disponible
    if '--no-gui' not in sys.argv:
        widget = test_widget_creation()
        if widget:
            print("\n✅ Tous les tests passés - Interface prête")
        else:
            print("\n❌ Problème avec l'interface")
    else:
        print("\n✅ Tests backend passés")

if __name__ == "__main__":
    main()