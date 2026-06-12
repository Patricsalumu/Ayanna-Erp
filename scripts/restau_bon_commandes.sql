-- =========================================================================
-- MIGRATION: Table restau_bon_commandes - Améliorée
-- =========================================================================
-- Script SQL pour créer la table restau_bon_commandes dans SQLite
-- Compatible avec tous les fichiers .db et .sqbpro du projet

-- Créer la table avec contraintes complètes
CREATE TABLE IF NOT EXISTS restau_bon_commandes (
    -- Colonnes principales
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entreprise_id INTEGER NOT NULL,
    numero_bon INTEGER NOT NULL,
    restau_panier_id INTEGER NOT NULL,
    
    -- Références utilisateurs
    serveuse_id INTEGER,
    user_id INTEGER,
    client_id INTEGER NOT NULL,
    
    -- Données métier
    produits_json TEXT NOT NULL,
    montant_total FLOAT DEFAULT 0.0,
    statut VARCHAR(50) DEFAULT 'valide',
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Contraintes de clés étrangères
    FOREIGN KEY(restau_panier_id) REFERENCES restau_paniers(id) ON DELETE CASCADE,
    FOREIGN KEY(entreprise_id) REFERENCES entreprises(id) ON DELETE CASCADE,
    FOREIGN KEY(serveuse_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY(client_id) REFERENCES shop_clients(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL,
    
    -- Contrainte d'unicité sur le numéro de bon par entreprise
    UNIQUE(entreprise_id, numero_bon)
);

-- =========================================================================
-- INDICES POUR OPTIMISER LES PERFORMANCES
-- =========================================================================

-- Index sur la clé étrangère restau_panier_id
CREATE INDEX IF NOT EXISTS idx_restau_bon_commandes_restau_panier_id 
    ON restau_bon_commandes(restau_panier_id);

-- Index sur l'entreprise (pour filtrer par entreprise)
CREATE INDEX IF NOT EXISTS idx_restau_bon_commandes_entreprise_id 
    ON restau_bon_commandes(entreprise_id);

-- Index sur le statut (pour filtrer par statut)
CREATE INDEX IF NOT EXISTS idx_restau_bon_commandes_statut 
    ON restau_bon_commandes(statut);

-- Index sur le client (pour voir les bons d'un client)
CREATE INDEX IF NOT EXISTS idx_restau_bon_commandes_client_id 
    ON restau_bon_commandes(client_id);

-- Index sur la date de création (pour trier les récents)
CREATE INDEX IF NOT EXISTS idx_restau_bon_commandes_created_at 
    ON restau_bon_commandes(created_at);

-- Index composite sur entreprise + statut (requête courante)
CREATE INDEX IF NOT EXISTS idx_restau_bon_commandes_entreprise_statut 
    ON restau_bon_commandes(entreprise_id, statut);

-- =========================================================================
-- COMMENTAIRES / DOCUMENTATION
-- =========================================================================
/*
STRUCTURE DE LA TABLE:

- id: Identifiant unique (auto-incrément)
- entreprise_id: Lien vers l'entreprise (NOT NULL)
- numero_bon: Numéro séquentiel du bon pour l'entreprise
- restau_panier_id: Lien vers le panier restaurant associé
- serveuse_id: ID de la serveuse (nullable)
- user_id: ID de l'utilisateur qui a créé le bon
- client_id: ID du client associé au bon
- produits_json: JSON avec la liste des produits commandés
- montant_total: Total du bon (défaut 0.0)
- statut: 'valide' ou 'annule' (défaut 'valide')
- created_at: Date de création (auto-défini)
- updated_at: Date de mise à jour (auto-défini)

PARTICULARITÉS:
- Clé unique (entreprise_id, numero_bon) pour éviter les doublons
- ON DELETE CASCADE pour entreprise_id et client_id (supprimer le bon si entreprise/client supprimé)
- ON DELETE SET NULL pour serveuse_id et user_id (garder le bon mais vider la référence)
- Indices créés pour les requêtes fréquentes

UTILISATION:
1. Via le script Python: python scripts/migrate_restau_bon_commandes.py
2. Via SQLite directement: sqlite3 database.db < scripts/restau_bon_commandes.sql
3. Via l'interface DB Manager
*/
