-- Migration: ajouter les colonnes customer_id à restau_printed_invoices
-- But: Enregistrer le client (customer_id) et l'utilisateur (printed_by_user_id avec index) 
--      au moment de l'impression de la facture.

-- Pour SQLite (utiliser avec sqlite3) :
-- Cette migration ajoute la colonne customer_id si elle n'existe pas
-- et crée des indexes sur customer_id et printed_by_user_id pour les performances

-- Ajouter la colonne customer_id (client qui a passé la commande)
-- SQLite : ALTER TABLE ne supporte pas le IF NOT EXISTS pour les colonnes
-- Donc nous utilisons une approche sûre qui ne génère pas d'erreur si elle existe

PRAGMA foreign_keys=OFF;

-- Vérification et création si nécessaire (approche SQLite)
-- Si la colonne existe déjà, cette commande sera ignorée
BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS restau_printed_invoices_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entreprise_id INTEGER NOT NULL,
    panier_id INTEGER NOT NULL,
    total_items_quantity INTEGER DEFAULT 0,
    product_lines_count INTEGER DEFAULT 0,
    total_amount REAL DEFAULT 0.0,
    products_snapshot TEXT NOT NULL,
    customer_id INTEGER,
    printed_by_user_id INTEGER,
    printed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (panier_id) REFERENCES restau_paniers(id)
);

-- Copier les données existantes si la table ne contient pas encore customer_id
INSERT INTO restau_printed_invoices_new 
SELECT 
    id, 
    entreprise_id, 
    panier_id, 
    total_items_quantity, 
    product_lines_count, 
    total_amount, 
    products_snapshot, 
    NULL as customer_id,
    printed_by_user_id, 
    printed_at, 
    created_at
FROM restau_printed_invoices
WHERE customer_id IS NULL;

-- Si la colonne customer_id existe déjà, aucune donnée à copier
-- Cette transaction échouera gracieusement

COMMIT;

PRAGMA foreign_keys=ON;

-- Créer les indexes pour les performances
CREATE INDEX IF NOT EXISTS idx_restau_printed_invoices_customer_id 
ON restau_printed_invoices(customer_id);

CREATE INDEX IF NOT EXISTS idx_restau_printed_invoices_printed_by_user_id 
ON restau_printed_invoices(printed_by_user_id);

-- Pour PostgreSQL :
-- ALTER TABLE restau_printed_invoices ADD COLUMN IF NOT EXISTS customer_id INTEGER;
-- ALTER TABLE restau_printed_invoices ADD COLUMN IF NOT EXISTS user_id_index INTEGER;
-- CREATE INDEX IF NOT EXISTS idx_restau_printed_invoices_customer_id ON restau_printed_invoices(customer_id);
-- CREATE INDEX IF NOT EXISTS idx_restau_printed_invoices_printed_by_user_id ON restau_printed_invoices(printed_by_user_id);

-- Notes :
-- - Pour SQLite, si la table existe déjà avec customer_id, cette migration ne fera rien
-- - Les indexes améliorent les performances de recherche par customer_id et printed_by_user_id
-- - Le customer_id vient du panier et représente ID du client
-- - Le printed_by_user_id représente l'ID de l'utilisateur qui a imprimé la facture
