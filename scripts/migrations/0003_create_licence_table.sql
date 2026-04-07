-- Migration 0003: créer la table licence
-- Compatible SQLite / SQLAlchemy basic types

CREATE TABLE IF NOT EXISTS licence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cle TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL,
    date_activation DATETIME NOT NULL,
    date_expiration DATETIME NOT NULL,
    signature TEXT NOT NULL,
    active INTEGER DEFAULT 1,
    entreprise_id INTEGER,
    FOREIGN KEY (entreprise_id) REFERENCES core_enterprises(id)
);
