-- Migration: create inventory tables (stock_inventaire, stock_inventaire_item)
-- Usage:
--  - SQLite: use sqlite3 CLI or your DB tool to run this file
--  - PostgreSQL: run inside a transaction (psql)

-- ================
-- SQLite
-- ================
CREATE TABLE IF NOT EXISTS stock_inventaire (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entreprise_id INTEGER NOT NULL,
    reference TEXT UNIQUE NOT NULL,
    session_name TEXT NOT NULL,
    warehouse_id INTEGER NOT NULL,
    inventory_type TEXT DEFAULT 'Complet',
    status TEXT DEFAULT 'DRAFT',
    scheduled_date DATETIME,
    started_date DATETIME,
    completed_date DATETIME,
    notes TEXT,
    total_items INTEGER DEFAULT 0,
    counted_items INTEGER DEFAULT 0,
    total_discrepancies INTEGER DEFAULT 0,
    total_variance_value DECIMAL(15,2) DEFAULT 0.0,
    include_zero_stock BOOLEAN DEFAULT 1,
    auto_freeze_stock BOOLEAN DEFAULT 0,
    send_notifications BOOLEAN DEFAULT 1,
    created_by INTEGER,
    created_by_name TEXT,
    completed_by INTEGER,
    completed_by_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (warehouse_id) REFERENCES stock_warehouses(id)
);

CREATE TABLE IF NOT EXISTS stock_inventaire_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inventory_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    product_name TEXT,
    product_code TEXT,
    system_stock DECIMAL(15,3) DEFAULT 0.0,
    counted_stock DECIMAL(15,3) DEFAULT 0.0,
    variance DECIMAL(15,3) DEFAULT 0.0,
    variance_value DECIMAL(15,2) DEFAULT 0.0,
    unit_cost DECIMAL(15,2) DEFAULT 0.0,
    location TEXT,
    notes TEXT,
    counted_by INTEGER,
    counted_by_name TEXT,
    counted_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (inventory_id) REFERENCES stock_inventaire(id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_stock_inventaire_entreprise_id ON stock_inventaire(entreprise_id);
CREATE INDEX IF NOT EXISTS idx_stock_inventaire_warehouse_id ON stock_inventaire(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_stock_inventaire_status ON stock_inventaire(status);
CREATE INDEX IF NOT EXISTS idx_stock_inventaire_created_at ON stock_inventaire(created_at);

CREATE INDEX IF NOT EXISTS idx_stock_inventaire_item_inventory_id ON stock_inventaire_item(inventory_id);
CREATE INDEX IF NOT EXISTS idx_stock_inventaire_item_product_id ON stock_inventaire_item(product_id);

-- ================
-- PostgreSQL (idempotent)
-- ================
-- BEGIN;
-- CREATE TABLE IF NOT EXISTS stock_inventaire (
--     id SERIAL PRIMARY KEY,
--     entreprise_id INTEGER NOT NULL,
--     reference VARCHAR(100) UNIQUE NOT NULL,
--     session_name VARCHAR(200) NOT NULL,
--     warehouse_id INTEGER NOT NULL REFERENCES stock_warehouses(id),
--     inventory_type VARCHAR(50) DEFAULT 'Complet',
--     status VARCHAR(20) DEFAULT 'DRAFT',
--     scheduled_date TIMESTAMP,
--     started_date TIMESTAMP,
--     completed_date TIMESTAMP,
--     notes TEXT,
--     total_items INTEGER DEFAULT 0,
--     counted_items INTEGER DEFAULT 0,
--     total_discrepancies INTEGER DEFAULT 0,
--     total_variance_value DECIMAL(15,2) DEFAULT 0.0,
--     include_zero_stock BOOLEAN DEFAULT TRUE,
--     auto_freeze_stock BOOLEAN DEFAULT FALSE,
--     send_notifications BOOLEAN DEFAULT TRUE,
--     created_by INTEGER,
--     created_by_name VARCHAR(100),
--     completed_by INTEGER,
--     completed_by_name VARCHAR(100),
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );
-- 
-- CREATE TABLE IF NOT EXISTS stock_inventaire_item (
--     id SERIAL PRIMARY KEY,
--     inventory_id INTEGER NOT NULL REFERENCES stock_inventaire(id) ON DELETE CASCADE,
--     product_id INTEGER NOT NULL,
--     product_name VARCHAR(200),
--     product_code VARCHAR(50),
--     system_stock DECIMAL(15,3) DEFAULT 0.0,
--     counted_stock DECIMAL(15,3) DEFAULT 0.0,
--     variance DECIMAL(15,3) DEFAULT 0.0,
--     variance_value DECIMAL(15,2) DEFAULT 0.0,
--     unit_cost DECIMAL(15,2) DEFAULT 0.0,
--     location VARCHAR(100),
--     notes TEXT,
--     counted_by INTEGER,
--     counted_by_name VARCHAR(100),
--     counted_at TIMESTAMP,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );
-- 
-- CREATE INDEX IF NOT EXISTS idx_stock_inventaire_entreprise_id ON stock_inventaire(entreprise_id);
-- CREATE INDEX IF NOT EXISTS idx_stock_inventaire_warehouse_id ON stock_inventaire(warehouse_id);
-- CREATE INDEX IF NOT EXISTS idx_stock_inventaire_status ON stock_inventaire(status);
-- CREATE INDEX IF NOT EXISTS idx_stock_inventaire_created_at ON stock_inventaire(created_at);
-- 
-- CREATE INDEX IF NOT EXISTS idx_stock_inventaire_item_inventory_id ON stock_inventaire_item(inventory_id);
-- CREATE INDEX IF NOT EXISTS idx_stock_inventaire_item_product_id ON stock_inventaire_item(product_id);
-- COMMIT;

-- Note:
-- - If your DB is not SQLite or PostgreSQL, adapt the CREATE TABLE statements accordingly.
-- - Run this migration after ensuring stock_warehouses table exists.