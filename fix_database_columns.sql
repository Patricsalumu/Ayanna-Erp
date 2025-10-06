-- Script SQL pour ajouter les colonnes manquantes
-- Exécutez ces commandes dans votre gestionnaire de base de données SQLite

-- 1. Ajouter created_at à shop_stock_transfers
ALTER TABLE shop_stock_transfers ADD COLUMN created_at DATETIME;

-- 2. Ajouter updated_at à shop_stock_transfers  
ALTER TABLE shop_stock_transfers ADD COLUMN updated_at DATETIME;

-- 3. Ajouter cost_price à shop_products
ALTER TABLE shop_products ADD COLUMN cost_price DECIMAL(15,2) DEFAULT 0.0;

-- 4. Mettre à jour les valeurs par défaut pour created_at
UPDATE shop_stock_transfers 
SET created_at = requested_date 
WHERE created_at IS NULL AND requested_date IS NOT NULL;

UPDATE shop_stock_transfers 
SET created_at = '2024-01-01 00:00:00' 
WHERE created_at IS NULL;

-- 5. Mettre à jour les valeurs par défaut pour updated_at
UPDATE shop_stock_transfers 
SET updated_at = COALESCE(received_date, shipped_date, approved_date, requested_date, '2024-01-01 00:00:00')
WHERE updated_at IS NULL;

-- 6. Copier les valeurs de cost vers cost_price
UPDATE shop_products 
SET cost_price = cost 
WHERE cost_price IS NULL OR cost_price = 0;

-- 7. Vérification des colonnes ajoutées
-- Commandes de vérification (à exécuter séparément)
-- PRAGMA table_info(shop_stock_transfers);
-- PRAGMA table_info(shop_products);
-- SELECT COUNT(*) FROM shop_stock_transfers WHERE created_at IS NOT NULL;
-- SELECT COUNT(*) FROM shop_products WHERE cost_price > 0;