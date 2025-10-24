-- Migration: add compte_variation_id to compta_config
-- Usage:
--  - SQLite: use sqlite3 CLI or your DB tool to run this file
--  - PostgreSQL: run inside a transaction (psql)

-- ================
-- SQLite (simple ALTER TABLE)
-- ================
-- SQLite allows adding a new column with a default NULL value.
ALTER TABLE compta_config ADD COLUMN compte_variation_id INTEGER;

-- ================
-- PostgreSQL (idempotent)
-- ================
-- BEGIN;
-- ALTER TABLE IF EXISTS compta_config ADD COLUMN IF NOT EXISTS compte_variation_id integer;
-- COMMIT;

-- Note:
-- - If your DB is not SQLite or PostgreSQL, adapt the ALTER TABLE statement accordingly.
-- - If you need a NOT NULL column, provide a DEFAULT or populate values before adding the constraint.
-- - After adding the column, update your compta_config rows to set the appropriate account ids.
