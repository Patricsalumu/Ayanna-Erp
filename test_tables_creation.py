#!/usr/bin/env python3
"""
Test de création de toutes les tables lors de l'initialisation
"""

import sys
import os
sys.path.append(os.path.abspath('.'))

print("=== TEST CREATION TABLES INITIALISATION ===")

try:
    from ayanna_erp.database.database_manager import DatabaseManager
    from sqlalchemy import text
    
    # Initialiser le gestionnaire de base de données
    db_manager = DatabaseManager()
    
    print("✅ DatabaseManager initialisé")
    
    # Créer toutes les tables
    db_manager.initialize_database()
    print("✅ initialize_database() exécuté")
    
    # Vérifier les tables créées
    with db_manager.get_session() as session:
        # Lister toutes les tables
        tables_result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")).fetchall()
        table_names = [row[0] for row in tables_result]
        
        print(f"\n=== TABLES CREEES ({len(table_names)}) ===")
        
        # Vérifier les tables par module
        modules_tables = {
            'Core': ['core_products', 'core_product_categories', 'pos_product_access'],
            'Stock': ['stock_warehouses', 'stock_produits_entrepot', 'stock_movements', 'stock_configs'],
            'Boutique': [
                'shop_clients', 'shop_services', 'shop_paniers', 'shop_panier_products',
                'shop_panier_services', 'shop_payments', 'shop_expenses', 
                'shop_comptes_config', 'shop_warehouses', 'shop_warehouse_stocks',
                'shop_stock_movements', 'shop_stock_transfers'
            ],
            'Salle de Fête': [
                'event_clients', 'event_services', 'event_reservations',
                'event_reservation_services', 'event_reservation_products',
                'event_payments', 'event_stock_movements', 'event_expenses'
            ],
            'Comptabilité': ['compta_classes', 'compta_comptes', 'compta_configs'],
            'Système': ['users', 'enterprises', 'modules', 'pos']
        }
        
        for module_name, expected_tables in modules_tables.items():
            print(f"\n📋 Module {module_name}:")
            found_count = 0
            for table in expected_tables:
                if table in table_names:
                    print(f"  ✅ {table}")
                    found_count += 1
                else:
                    print(f"  ❌ {table} MANQUANTE")
            
            print(f"  → {found_count}/{len(expected_tables)} tables trouvées")
        
        print(f"\n=== TOUTES LES TABLES PRESENTES ===")
        for table in sorted(table_names):
            print(f"  • {table}")
    
    print(f"\n🎉 TEST TERMINE - {len(table_names)} tables créées au total")
    
except Exception as e:
    print(f"ERREUR: {e}")
    import traceback
    traceback.print_exc()