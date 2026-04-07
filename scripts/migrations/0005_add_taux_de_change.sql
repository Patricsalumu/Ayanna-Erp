-- Migration 0005: ajouter la colonne taux_de_change à core_enterprises
-- Date: 2026-03-21
--
-- Cette colonne stocke le taux de change configuré par l'utilisateur.
-- Exemple : 2200 signifie 1 USD = 2200 FC.
-- La valeur NULL signifie que la correspondance de devise est désactivée sur les tickets.
--
-- ================
-- SQLite (simple ALTER TABLE — NULL par défaut, compatible)
-- ================
ALTER TABLE core_enterprises ADD COLUMN taux_de_change REAL;

-- ================
-- PostgreSQL (idempotent)
-- ================
-- BEGIN;
-- ALTER TABLE IF EXISTS core_enterprises ADD COLUMN IF NOT EXISTS taux_de_change NUMERIC(12,4);
-- COMMIT;
