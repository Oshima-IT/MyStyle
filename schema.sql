PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS item_shops;
DROP TABLE IF EXISTS items;
DROP TABLE IF EXISTS shops;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    preferred_styles TEXT,
    preferred_colors TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE shops (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT NOT NULL,
    site_url TEXT
);

CREATE TABLE items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    image_url  TEXT,
    category   TEXT,
    price      INTEGER, /* price_min/max was in suggestion but app uses price currently. kept 'price' for compatibility */
    styles     TEXT,
    colors     TEXT,
    is_trend   INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE item_shops (
    item_id INTEGER NOT NULL,
    shop_id INTEGER NOT NULL,
    PRIMARY KEY (item_id, shop_id),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE
);
