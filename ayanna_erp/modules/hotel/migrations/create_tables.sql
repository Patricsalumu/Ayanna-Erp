-- Migration : Module Hôtel – Ayanna ERP
-- À exécuter une seule fois lors de l'initialisation du module.

CREATE TABLE IF NOT EXISTS hotel_categories (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    price_per_night REAL    NOT NULL DEFAULT 0.0,
    created_at      TEXT    DEFAULT (datetime('now','localtime')),
    deleted         INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS hotel_rooms (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    number            TEXT    NOT NULL,
    hotel_category_id INTEGER NOT NULL REFERENCES hotel_categories(id),
    status            TEXT    DEFAULT 'disponible',  -- disponible|occupee|menage|maintenance
    created_at        TEXT    DEFAULT (datetime('now','localtime')),
    deleted           INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS hotel_reservations (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id           INTEGER NOT NULL REFERENCES shop_clients(id),
    reservation_code    TEXT    NOT NULL UNIQUE,
    hotel_category_id   INTEGER NOT NULL REFERENCES hotel_categories(id),
    room_id             INTEGER REFERENCES hotel_rooms(id),
    date_entree_prevue  TEXT    NOT NULL,
    date_sortie_prevue  TEXT    NOT NULL,
    date_entree_reelle  TEXT,
    date_sortie_reelle  TEXT,
    status              TEXT    DEFAULT 'en_attente',   -- en_attente|confirmee|en_cours|terminee|annulee
    reduction           REAL    DEFAULT 0.0,
    statut_paiement     TEXT    DEFAULT 'nonpaye',      -- nonpaye|partiel|paye|credit
    total_amount        REAL    DEFAULT 0.0,
    notes               TEXT,
    created_at          TEXT    DEFAULT (datetime('now','localtime')),
    user_id             INTEGER
);

CREATE TABLE IF NOT EXISTS hotel_payments (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    reservation_id INTEGER NOT NULL REFERENCES hotel_reservations(id),
    amount         REAL    NOT NULL,
    method         TEXT    DEFAULT 'cash',   -- cash|mobile_money|carte
    created_at     TEXT    DEFAULT (datetime('now','localtime')),
    user_id        INTEGER
);
