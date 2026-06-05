-- Populate historical total_counted_purchase_value for all inventories
-- Run this once against your database (e.g., sqlite3 or psql)

BEGIN;

UPDATE stock_inventaire SET total_counted_purchase_value = (
    SELECT COALESCE(SUM(COALESCE(counted_stock,0) * COALESCE(unit_cost,0)),0)
    FROM stock_inventaire_item
    WHERE inventory_id = stock_inventaire.id
);

COMMIT;

-- Optionally verify:
-- SELECT id, total_counted_purchase_value FROM stock_inventaire ORDER BY id DESC LIMIT 20;
