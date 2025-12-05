PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

-- Drop existing tables to allow re-run
DROP TABLE IF EXISTS item_shops;
DROP TABLE IF EXISTS shops;
DROP TABLE IF EXISTS items;
DROP TABLE IF EXISTS users;

-- Users
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    preferred_styles TEXT,   -- e.g. "street,vintage"
    preferred_colors TEXT,   -- e.g. "black,white"
    created_at TEXT,
    updated_at TEXT
);

-- Items
CREATE TABLE items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    image_url TEXT,
    category TEXT,           -- e.g. "tops", "pants"
    price INTEGER,           -- yen
    styles TEXT,             -- e.g. "street,korean"
    colors TEXT,             -- e.g. "black,gray"
    is_trend INTEGER DEFAULT 0,  -- 0 or 1
    created_at TEXT
);

-- Shops
CREATE TABLE shops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    site_url TEXT
);

-- Item-Shop mapping
CREATE TABLE item_shops (
    item_id INTEGER NOT NULL,
    shop_id INTEGER NOT NULL,
    PRIMARY KEY (item_id, shop_id),
    FOREIGN KEY (item_id) REFERENCES items(id),
    FOREIGN KEY (shop_id) REFERENCES shops(id)
);

-- Seed data
INSERT INTO users (id, email, password_hash, preferred_styles, preferred_colors, created_at, updated_at)
VALUES (1, 'test@example.com', 'hashed_password_example', 'street,vintage', 'black,blue', '2025-07-17', '2025-07-17');

INSERT INTO items (id, name, image_url, category, price, styles, colors, is_trend, created_at)
VALUES (1, 'Wide Denim', 'https://example.com/denim.jpg', 'pants', 3000, 'street', 'blue', 1, '2025-07-17');

INSERT INTO items (name, category, price, styles, colors, is_trend, image_url, created_at) VALUES
('カジュアルシャツ', 'トップス', 9800, 'カジュアル', '白,青', 0, 'https://lh3.googleusercontent.com/gg/AIJ2gl-aOj9Su7KmMNxCncvOanexnxQh6dMP3Nrj7t-9tGOXR8iUMeOYhb-I8bibzZv-S2NuAMmxUc247NC0I3T8EIeNhFk3KZHzifaPnvW9ySkXVUK7s0-UhXzRrhyuphDCFC8RMzNNIENJI_awDftjRpoLqMLs-83T7e1eVK8bDfZpuQbS8F1Q=s1024-rj', '2025-07-17'),
('フォーマルジャケット', 'アウター', 15000, 'フォーマル,きれいめ', '黒,グレー', 0, 'https://lh3.googleusercontent.com/gg/AIJ2gl9uscsCrhXFlJQUzKIX2GLcq2UQfmA-Jeu_K_vPHmu7u9Ih5DbBQoSdVxsPJWqfMy8BRDjhvT5DofQTqGVtnXzLw24aPRl6UQ_akv6ZTf4vJ156blj6K8LCRu1Qxry3Hb5Kl_TZ39QDT9h8R9IG2r-qihTXVAQzovH6wHY69bjQyankWn98=s1024-rj', '2025-07-17'),
('スポーティースニーカー', 'シューズ', 7500, 'ストリート,スポーツ', '白,黒', 1, 'https://lh3.googleusercontent.com/gg/AIJ2gl8WAZOxaS251Jkuwb5RxXPerErbQXYQ514Pf7yBsfQ6N7lKrz3ut9-6DgNkoo_pYudt_AMB0QxPPoRt1n2H7c-Kf4bZrPUT46jO8_xjyY_2_OuEEic4Sgj8qe1SP6cILknuqSunHzR6CweOGHjEgx_d28VZ4eFSKtV3g6rYyXacI8GQgo2F=s1024-rj', '2025-07-17'),
('モダンレザーハンドバッグ', 'バッグ', 12400, 'モダン,きれいめ', '黒,茶', 0, 'https://lh3.googleusercontent.com/gg/AIJ2gl_4_PyKAv85BmfhvqmtDbCwybOYxpygrp-InB8tLj2P3gCTkS9Fyp4F34R33AOxQ-D3YNZps6zfo-yKEQstgra7Z7AFNrtuAlrEuNL6hVWPcws0vDTvtr_w0bgav9IbyXXEIfQVtezGWsQGyZf5V9rKKNEXG2bQJkQBNQibQd1iOaZQw9v9=s1024-rj', '2025-07-17'),
('シルバーウォッチ', 'アクセサリー', 5800, 'モダン,フォーマル', 'シルバー', 0, 'https://lh3.googleusercontent.com/gg/AIJ2gl-z5gC2zdOnlBgxUiNa9q27lrAcwwAxxszNReZP_b3blFqTchMXbMm4y-hO7nWW_mHKUtwic9I6kpQ0tGFTWeeh2167gvbMkWA-ugiHYA6JJI4G47EwSlBGzUo8GCjyMC8846fKZrUbmPp8Nxw1NRja5l7_hc5ZxpPj0beMj4RRPf2SW3Vu=s1024-rj', '2025-07-17');

INSERT INTO shops (id, name, site_url)
VALUES (1, 'ZOZOTOWN', 'https://zozo.jp/');

INSERT INTO item_shops (item_id, shop_id)
VALUES (1, 1);

COMMIT;
PRAGMA foreign_keys = ON;
