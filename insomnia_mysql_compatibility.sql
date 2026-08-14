USE insomnia;

SET foreign_key_checks = 0;

-- ============================================
-- Compatibilité MySQL pour Ayanna ERP Python
-- ============================================
-- Ce script corrige les colonnes et alias de tables
-- attendus par les modèles Python / ORM, quand MySQL
-- est la base de référence du projet.
--
-- À exécuter après un migrate:fresh ou sur une base
-- déjà créée si des colonnes manquent encore.
--
-- Commande d'import :
-- mysql -u root -p insomnia < insomnia_mysql_compatibility.sql
-- ============================================

-- core_product_categories
ALTER TABLE core_product_categories
  ADD COLUMN IF NOT EXISTS entreprise_id INT NULL AFTER id;

-- core_products
ALTER TABLE core_products
  ADD COLUMN IF NOT EXISTS entreprise_id CHAR(36) NULL AFTER id;

UPDATE core_products
SET `entreprise_id` = `enterprise_id`
WHERE `entreprise_id` IS NULL AND `enterprise_id` IS NOT NULL;

-- shop_clients
ALTER TABLE shop_clients
  ADD COLUMN IF NOT EXISTS notes TEXT NULL AFTER balance,
  ADD COLUMN IF NOT EXISTS pays VARCHAR(100) NULL AFTER notes,
  ADD COLUMN IF NOT EXISTS carte_identite VARCHAR(100) NULL AFTER pays,
  ADD COLUMN IF NOT EXISTS type_carte VARCHAR(50) NULL AFTER carte_identite;

-- shop_paniers
ALTER TABLE shop_paniers
  ADD COLUMN IF NOT EXISTS numero_commande VARCHAR(50) NULL AFTER client_id,
  ADD COLUMN IF NOT EXISTS status VARCHAR(50) NULL AFTER numero_commande,
  ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50) NULL AFTER status,
  ADD COLUMN IF NOT EXISTS subtotal DECIMAL(15,2) NOT NULL DEFAULT 0 AFTER payment_method,
  ADD COLUMN IF NOT EXISTS remise_amount DECIMAL(15,2) NOT NULL DEFAULT 0 AFTER subtotal,
  ADD COLUMN IF NOT EXISTS total_final DECIMAL(15,2) NOT NULL DEFAULT 0 AFTER remise_amount,
  ADD COLUMN IF NOT EXISTS pret TINYINT(1) NOT NULL DEFAULT 0 AFTER total_final,
  ADD COLUMN IF NOT EXISTS livre TINYINT(1) NOT NULL DEFAULT 0 AFTER pret,
  ADD COLUMN IF NOT EXISTS notes TEXT NULL AFTER livre,
  ADD COLUMN IF NOT EXISTS validated_at DATETIME NULL AFTER notes;

-- remplir les valeurs de compatibilité si les anciennes colonnes existent
UPDATE shop_paniers
SET numero_commande = reference
WHERE numero_commande IS NULL AND reference IS NOT NULL;

UPDATE shop_paniers
SET status = statut
WHERE status IS NULL AND statut IS NOT NULL;

UPDATE shop_paniers
SET notes = note
WHERE notes IS NULL AND note IS NOT NULL;

UPDATE shop_paniers
SET subtotal = montant_total
WHERE subtotal = 0 AND montant_total IS NOT NULL;

UPDATE shop_paniers
SET remise_amount = remise
WHERE remise_amount = 0 AND remise IS NOT NULL;

UPDATE shop_paniers
SET total_final = (montant_total - remise)
WHERE total_final = 0 AND montant_total IS NOT NULL;

UPDATE shop_paniers
SET payment_method = 'non_paye'
WHERE payment_method IS NULL;

-- compatibilité des tables détaillées de panier boutique
CREATE TABLE IF NOT EXISTS shop_paniers_products (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  panier_id BIGINT UNSIGNED NULL,
  product_id BIGINT UNSIGNED NULL,
  quantity DECIMAL(15,2) NOT NULL DEFAULT 1,
  price_unit DECIMAL(15,2) NOT NULL DEFAULT 0,
  total_price DECIMAL(15,2) NOT NULL DEFAULT 0,
  created_at TIMESTAMP NULL DEFAULT NULL,
  updated_at TIMESTAMP NULL DEFAULT NULL,
  PRIMARY KEY (id),
  KEY idx_shop_paniers_products_panier (panier_id),
  KEY idx_shop_paniers_products_product (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE shop_payments
  ADD COLUMN IF NOT EXISTS amount DECIMAL(15,2) NOT NULL DEFAULT 0 AFTER payment_mode_id,
  ADD COLUMN IF NOT EXISTS payment_date TIMESTAMP NULL AFTER amount;

UPDATE shop_payments
SET amount = montant
WHERE amount = 0 AND montant IS NOT NULL;

UPDATE shop_payments
SET payment_date = date_paiement
WHERE payment_date IS NULL AND date_paiement IS NOT NULL;

CREATE TABLE IF NOT EXISTS shop_paniers_services (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  panier_id BIGINT UNSIGNED NULL,
  service_id BIGINT UNSIGNED NULL,
  quantity DECIMAL(15,2) NOT NULL DEFAULT 1,
  price_unit DECIMAL(15,2) NOT NULL DEFAULT 0,
  total_price DECIMAL(15,2) NOT NULL DEFAULT 0,
  created_at TIMESTAMP NULL DEFAULT NULL,
  updated_at TIMESTAMP NULL DEFAULT NULL,
  PRIMARY KEY (id),
  KEY idx_shop_paniers_services_panier (panier_id),
  KEY idx_shop_paniers_services_service (service_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO shop_paniers_products (panier_id, product_id, quantity, price_unit, total_price, created_at, updated_at)
SELECT panier_id, product_id, quantite, prix_unitaire, total, created_at, updated_at
FROM shop_panier_products
WHERE NOT EXISTS (
  SELECT 1 FROM shop_paniers_products s2 WHERE s2.panier_id = shop_panier_products.panier_id AND s2.product_id = shop_panier_products.product_id
);

INSERT INTO shop_paniers_services (panier_id, service_id, quantity, price_unit, total_price, created_at, updated_at)
SELECT panier_id, service_id, quantite, prix_unitaire, total, created_at, updated_at
FROM shop_panier_services
WHERE NOT EXISTS (
  SELECT 1 FROM shop_paniers_services s2 WHERE s2.panier_id = shop_panier_services.panier_id AND s2.service_id = shop_panier_services.service_id
);

-- restaurant / salles / paniers / printed invoices
ALTER TABLE restau_salles
  ADD COLUMN IF NOT EXISTS entreprise_id INT NULL AFTER id,
  ADD COLUMN IF NOT EXISTS name VARCHAR(200) NULL AFTER id;

UPDATE restau_salles
SET entreprise_id = 1
WHERE entreprise_id IS NULL;

ALTER TABLE restau_tables
  ADD COLUMN IF NOT EXISTS number VARCHAR(50) NULL AFTER salle_id,
  ADD COLUMN IF NOT EXISTS name VARCHAR(200) NULL AFTER number,
  ADD COLUMN IF NOT EXISTS pos_x INT NOT NULL DEFAULT 0 AFTER name,
  ADD COLUMN IF NOT EXISTS pos_y INT NOT NULL DEFAULT 0 AFTER pos_x,
  ADD COLUMN IF NOT EXISTS width INT NOT NULL DEFAULT 80 AFTER pos_y,
  ADD COLUMN IF NOT EXISTS height INT NOT NULL DEFAULT 80 AFTER width,
  ADD COLUMN IF NOT EXISTS shape VARCHAR(50) NOT NULL DEFAULT 'rectangle' AFTER height;

UPDATE restau_tables
SET number = numero
WHERE number IS NULL AND numero IS NOT NULL;

UPDATE restau_tables
SET name = nom
WHERE name IS NULL AND nom IS NOT NULL;

ALTER TABLE restau_paniers
  ADD COLUMN IF NOT EXISTS subtotal DECIMAL(15,2) NOT NULL DEFAULT 0 AFTER user_id,
  ADD COLUMN IF NOT EXISTS remise_amount DECIMAL(15,2) NOT NULL DEFAULT 0 AFTER subtotal,
  ADD COLUMN IF NOT EXISTS total_final DECIMAL(15,2) NOT NULL DEFAULT 0 AFTER remise_amount,
  ADD COLUMN IF NOT EXISTS payment_method VARCHAR(100) NULL AFTER total_final,
  ADD COLUMN IF NOT EXISTS status VARCHAR(50) NULL AFTER payment_method,
  ADD COLUMN IF NOT EXISTS pret TINYINT(1) NOT NULL DEFAULT 0 AFTER status,
  ADD COLUMN IF NOT EXISTS livre TINYINT(1) NOT NULL DEFAULT 0 AFTER pret,
  ADD COLUMN IF NOT EXISTS notes TEXT NULL AFTER livre;

UPDATE restau_paniers
SET subtotal = montant_total
WHERE subtotal = 0 AND montant_total IS NOT NULL;

UPDATE restau_paniers
SET remise_amount = remise
WHERE remise_amount = 0 AND remise IS NOT NULL;

UPDATE restau_paniers
SET total_final = (montant_total - remise)
WHERE total_final = 0 AND montant_total IS NOT NULL;

UPDATE restau_paniers
SET status = statut
WHERE status IS NULL AND statut IS NOT NULL;

UPDATE restau_paniers
SET notes = note
WHERE notes IS NULL AND note IS NOT NULL;

UPDATE restau_paniers
SET payment_method = 'non_paye'
WHERE payment_method IS NULL;

ALTER TABLE restau_produit_panier
  ADD COLUMN IF NOT EXISTS quantity DECIMAL(15,3) NOT NULL DEFAULT 1 AFTER product_id,
  ADD COLUMN IF NOT EXISTS price_unit DECIMAL(15,2) NOT NULL DEFAULT 0 AFTER quantity,
  ADD COLUMN IF NOT EXISTS total_price DECIMAL(15,2) NOT NULL DEFAULT 0 AFTER price_unit;

UPDATE restau_produit_panier
SET quantity = quantite
WHERE quantity = 1 AND quantite IS NOT NULL;

UPDATE restau_produit_panier
SET price_unit = prix_unitaire
WHERE price_unit = 0 AND prix_unitaire IS NOT NULL;

UPDATE restau_produit_panier
SET total_price = total
WHERE total_price = 0 AND total IS NOT NULL;

ALTER TABLE restau_payments
  ADD COLUMN IF NOT EXISTS amount DECIMAL(15,2) NOT NULL DEFAULT 0 AFTER payment_mode_id,
  ADD COLUMN IF NOT EXISTS payment_method VARCHAR(100) NULL AFTER amount,
  ADD COLUMN IF NOT EXISTS user_id CHAR(36) NULL AFTER payment_method,
  ADD COLUMN IF NOT EXISTS payment_date TIMESTAMP NULL AFTER user_id;

UPDATE restau_payments
SET amount = montant
WHERE amount = 0 AND montant IS NOT NULL;

UPDATE restau_payments
SET payment_method = payment_mode_id
WHERE payment_method IS NULL AND payment_mode_id IS NOT NULL;

UPDATE restau_payments
SET payment_date = date_paiement
WHERE payment_date IS NULL AND date_paiement IS NOT NULL;

ALTER TABLE restau_printed_invoices
  ADD COLUMN IF NOT EXISTS entreprise_id INT NULL AFTER id,
  ADD COLUMN IF NOT EXISTS total_items_quantity INT NOT NULL DEFAULT 0 AFTER entreprise_id,
  ADD COLUMN IF NOT EXISTS product_lines_count INT NOT NULL DEFAULT 0 AFTER total_items_quantity,
  ADD COLUMN IF NOT EXISTS total_amount DECIMAL(15,2) NOT NULL DEFAULT 0 AFTER product_lines_count,
  ADD COLUMN IF NOT EXISTS products_snapshot TEXT NULL AFTER total_amount,
  ADD COLUMN IF NOT EXISTS printed_by_user_id CHAR(36) NULL AFTER products_snapshot,
  ADD COLUMN IF NOT EXISTS printed_at TIMESTAMP NULL AFTER printed_by_user_id;

UPDATE restau_printed_invoices
SET entreprise_id = 1
WHERE entreprise_id IS NULL;

-- salle de fête
ALTER TABLE event_services
  ADD COLUMN IF NOT EXISTS name VARCHAR(200) NULL AFTER id,
  ADD COLUMN IF NOT EXISTS cost DECIMAL(15,2) NOT NULL DEFAULT 0 AFTER description,
  ADD COLUMN IF NOT EXISTS price DECIMAL(15,2) NOT NULL DEFAULT 0 AFTER cost;

UPDATE event_services
SET name = nom
WHERE name IS NULL AND nom IS NOT NULL;

UPDATE event_services
SET cost = prix
WHERE cost = 0 AND prix IS NOT NULL;

UPDATE event_services
SET price = prix
WHERE price = 0 AND prix IS NOT NULL;

-- stock
ALTER TABLE stock_mouvements
  ADD COLUMN IF NOT EXISTS movement_type VARCHAR(50) NULL AFTER user_id,
  ADD COLUMN IF NOT EXISTS movement_date DATETIME NULL AFTER movement_type;

UPDATE stock_mouvements
SET movement_type = type_mouvement
WHERE movement_type IS NULL AND type_mouvement IS NOT NULL;

UPDATE stock_mouvements
SET movement_type = 'AJUSTEMENT'
WHERE movement_type IS NULL;

UPDATE stock_mouvements
SET movement_date = COALESCE(date_mouvement, created_at)
WHERE movement_date IS NULL;

-- comptabilité
ALTER TABLE compta_classes
  ADD COLUMN IF NOT EXISTS date_creation DATETIME NULL AFTER enterprise_id,
  ADD COLUMN IF NOT EXISTS date_modification DATETIME NULL AFTER date_creation;

UPDATE compta_classes
SET date_creation = created_at
WHERE date_creation IS NULL AND created_at IS NOT NULL;

UPDATE compta_classes
SET date_modification = updated_at
WHERE date_modification IS NULL AND updated_at IS NOT NULL;

ALTER TABLE compta_comptes
  ADD COLUMN IF NOT EXISTS date_creation DATETIME NULL AFTER classe_comptable_id,
  ADD COLUMN IF NOT EXISTS date_modification DATETIME NULL AFTER date_creation;

UPDATE compta_comptes
SET date_creation = created_at
WHERE date_creation IS NULL AND created_at IS NOT NULL;

UPDATE compta_comptes
SET date_modification = updated_at
WHERE date_modification IS NULL AND updated_at IS NOT NULL;

ALTER TABLE compta_journaux
  ADD COLUMN IF NOT EXISTS date_creation DATETIME NULL AFTER user_id,
  ADD COLUMN IF NOT EXISTS date_modification DATETIME NULL AFTER date_creation;

UPDATE compta_journaux
SET date_creation = created_at
WHERE date_creation IS NULL AND created_at IS NOT NULL;

UPDATE compta_journaux
SET date_modification = updated_at
WHERE date_modification IS NULL AND updated_at IS NOT NULL;

SET foreign_key_checks = 1;
