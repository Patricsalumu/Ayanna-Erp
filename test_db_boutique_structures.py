# Test des structures de base de données boutique
import sqlite3
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=== TEST STRUCTURES BASE DE DONNÉES BOUTIQUE ===\n")

try:
    # Vérifier les tables nécessaires
    conn = sqlite3.connect('ayanna_erp.db')
    cursor = conn.cursor()
    
    tables_required = [
        'shop_panier',
        'shop_panier_items', 
        'stock_warehouses',
        'stock_produits_entrepot',
        'stock_mouvements',
        'compta_config',
        'compta_journaux',
        'compta_ecritures'
    ]
    
    print("1. Vérification des tables...")
    existing_tables = []
    missing_tables = []
    
    for table in tables_required:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            existing_tables.append(table)
            print(f"✅ {table}: {count} enregistrements")
        except sqlite3.OperationalError:
            missing_tables.append(table)
            print(f"❌ {table}: Table manquante")
    
    if missing_tables:
        print(f"\n⚠️ Tables manquantes: {missing_tables}")
        print("Création des tables manquantes...")
        
        # Créer shop_panier si manquante
        if 'shop_panier' in missing_tables:
            cursor.execute("""
                CREATE TABLE shop_panier (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pos_id INTEGER NOT NULL,
                    client_id INTEGER,
                    user_id INTEGER,
                    total_amount DECIMAL(15,2) DEFAULT 0.00,
                    discount_percent DECIMAL(5,2) DEFAULT 0.00,
                    payment_method VARCHAR(50),
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Table shop_panier créée")
        
        # Créer shop_panier_items si manquante
        if 'shop_panier_items' in missing_tables:
            cursor.execute("""
                CREATE TABLE shop_panier_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    panier_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity DECIMAL(10,3) NOT NULL,
                    unit_price DECIMAL(15,2) NOT NULL,
                    total_price DECIMAL(15,2) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (panier_id) REFERENCES shop_panier(id),
                    FOREIGN KEY (product_id) REFERENCES core_products(id)
                )
            """)
            print("✅ Table shop_panier_items créée")
        
        conn.commit()
    
    print("\n2. Vérification des données de test...")
    
    # Vérifier l'entrepôt boutique POS_2
    cursor.execute("""
        SELECT w.id, w.name, w.code, w.entreprise_id, w.is_active, w.is_default
        FROM stock_warehouses w 
        WHERE w.code = 'POS_2'
    """)
    pos2_warehouse = cursor.fetchone()
    
    if pos2_warehouse:
        print(f"✅ Entrepôt boutique (POS_2) trouvé:")
        print(f"    ID: {pos2_warehouse[0]}, Nom: {pos2_warehouse[1]}, Code: {pos2_warehouse[2]}")
        print(f"    Entreprise: {pos2_warehouse[3]}, Actif: {pos2_warehouse[4]}, Défaut: {pos2_warehouse[5]}")
    else:
        print("❌ Entrepôt boutique (POS_2) non trouvé")
        print("Création de l'entrepôt boutique POS_2...")
        
        cursor.execute("""
            INSERT INTO stock_warehouses 
            (name, code, address, entreprise_id, is_active, is_default, type, description)
            VALUES ('Entrepôt Boutique', 'POS_2', 'Magasin de vente', 1, 1, 0, 'Retail', 'Entrepôt dédié aux ventes boutique')
        """)
        print("✅ Entrepôt boutique POS_2 créé")
        conn.commit()
        
        # Récupérer l'ID créé
        cursor.execute("SELECT id FROM stock_warehouses WHERE code = 'POS_2'")
        new_warehouse = cursor.fetchone()
        warehouse_id = new_warehouse[0] if new_warehouse else None
        
        # Ajouter du stock initial pour les produits existants
        if warehouse_id:
            cursor.execute("SELECT id FROM core_products WHERE is_active = 1")
            products = cursor.fetchall()
            
            for product in products:
                cursor.execute("""
                    INSERT INTO stock_produits_entrepot 
                    (product_id, warehouse_id, quantity, unit_cost, total_cost, min_stock_level, last_movement_date)
                    VALUES (?, ?, 100, 0, 0, 10, CURRENT_TIMESTAMP)
                """, (product[0], warehouse_id))
            
            print(f"✅ Stock initial ajouté pour {len(products)} produits dans POS_2")
            conn.commit()
    
    # Vérifier tous les entrepôts actifs
    cursor.execute("""
        SELECT w.id, w.name, w.code, w.entreprise_id, w.is_active
        FROM stock_warehouses w 
        WHERE w.is_active = 1
        ORDER BY w.code
    """)
    all_warehouses = cursor.fetchall()
    
    if all_warehouses:
        print(f"\n✅ Tous les entrepôts actifs ({len(all_warehouses)}):")
        for w in all_warehouses:
            print(f"    {w[2] or 'N/A'} - {w[1]} (ID: {w[0]}, Entreprise: {w[3]})")
    else:
        print("\n❌ Aucun entrepôt actif trouvé")
    
    # Vérifier les produits avec stock
    cursor.execute("""
        SELECT p.id, p.name, spe.quantity, spe.warehouse_id
        FROM core_products p
        LEFT JOIN stock_produits_entrepot spe ON p.id = spe.product_id
        WHERE p.is_active = 1
        LIMIT 5
    """)
    products_stock = cursor.fetchall()
    
    print(f"\n✅ Produits avec stock (exemple):")
    for ps in products_stock:
        stock = ps[2] if ps[2] is not None else "Aucun stock"
        print(f"    {ps[1]}: {stock} (Entrepôt: {ps[3] or 'N/A'})")
    
    # Vérifier la configuration comptable
    cursor.execute("""
        SELECT enterprise_id, compte_vente_id, compte_caisse_id
        FROM compta_config
        LIMIT 1
    """)
    compta_config = cursor.fetchone()
    
    if compta_config:
        print(f"\n✅ Configuration comptable: Entreprise {compta_config[0]}, Vente: {compta_config[1]}, Caisse: {compta_config[2]}")
    else:
        print("\n⚠️ Aucune configuration comptable trouvée")
    
    conn.close()
    
    print("\n" + "="*60)
    print("✅ VÉRIFICATION TERMINÉE")
    print("="*60)
    
    print("\n📊 RÉSUMÉ:")
    print(f"  • Tables existantes: {len(existing_tables)}/{len(tables_required)}")
    print(f"  • Tables manquantes: {len(missing_tables)}")
    print(f"  • Entrepôts actifs: {len(all_warehouses)}")
    print(f"  • Configuration comptable: {'✅' if compta_config else '❌'}")
    
    if not missing_tables:
        print("\n🎉 Toutes les structures nécessaires sont en place!")
        print("La nouvelle interface boutique est prête à fonctionner.")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()