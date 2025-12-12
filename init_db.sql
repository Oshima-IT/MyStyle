BEGIN TRANSACTION;

-- Items seed
INSERT INTO items (name, category, price, styles, colors, is_trend, image_url, shop_url, created_at) VALUES
-- フレンチガーリー
('カーディガン', 'カーディガン', 4180, 'フレンチガーリー', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=156706254', CURRENT_TIMESTAMP),
('ポレロ', 'ボレロ', 5940, 'フレンチガーリー', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=157411305', CURRENT_TIMESTAMP),
('リボンブラウス', 'ブラウス', 5000, 'フレンチガーリー', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=157892892', CURRENT_TIMESTAMP),
('リボンセットアップ', 'セットアップ', 8990, 'フレンチガーリー', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=143837770', CURRENT_TIMESTAMP),
('小花柄スカート', 'スカート', 4490, 'フレンチガーリー', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=149563173', CURRENT_TIMESTAMP),

-- 地雷系
('地雷セットアップ', 'セットアップ', 12100, '地雷系', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=151232569', CURRENT_TIMESTAMP),
('厚底ブーツ', 'ブーツ', 6518, '地雷系', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=158935282', CURRENT_TIMESTAMP),
('チョーカー', 'アクセサリー', 2750, '地雷系', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=147737351', CURRENT_TIMESTAMP),
('ブラウス', 'ブラウス', 5940, '地雷系', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=147831739', CURRENT_TIMESTAMP),
('地雷バッグ', 'バッグ', 12980, '地雷系', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=153993050', CURRENT_TIMESTAMP),

-- サブカル系
('スウェット', 'スウェット', 13970, 'サブカル系', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=160622545', CURRENT_TIMESTAMP),
('ロンT', 'ロンT', 5900, 'サブカル系', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=150456157', CURRENT_TIMESTAMP),
('レッグウォーマー', 'レッグウォーマー', 2900, 'サブカル系', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=150456070', CURRENT_TIMESTAMP),
('ジャージ', 'ジャージ', 12900, 'サブカル系', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=150456199', CURRENT_TIMESTAMP),

-- 量産型
('量産ワンピース', 'ワンピース', 10990, '量産型', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=149817894', CURRENT_TIMESTAMP),
('厚底ローファー', 'ローファー', 4389, '量産型', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=153623183', CURRENT_TIMESTAMP),
('リボンヘアアクセ', 'ヘアアクセ', 2200, '量産型', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=161649089', CURRENT_TIMESTAMP),
('フレアスカート', 'スカート', 5940, '量産型', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=147834413', CURRENT_TIMESTAMP),
('レースタイツ', 'タイツ', 2860, '量産型', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=141301414', CURRENT_TIMESTAMP),

-- ストリート系
('オーバーサイズパーカー', 'パーカー', 6600, 'ストリート系', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=128611533', CURRENT_TIMESTAMP),
('スニーカー', 'スニーカー', 4500, 'ストリート系', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=157886056', CURRENT_TIMESTAMP),
('カーゴパンツ', 'パンツ', 6219, 'ストリート系', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=131053052', CURRENT_TIMESTAMP),
('キャップ', 'キャップ', 8800, 'ストリート系', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=153219106', CURRENT_TIMESTAMP),
('グラフィックT', 'Tシャツ', 3450, 'ストリート系', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=133981311', CURRENT_TIMESTAMP),

-- Y2K
('クロップドトップス', 'トップス', 4950, 'Y2K', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=143631556', CURRENT_TIMESTAMP),
('ミニスカート', 'スカート', 5170, 'Y2K', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=158132706', CURRENT_TIMESTAMP),
('カラフルサングラス', 'サングラス', 1500, 'Y2K', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=153620804', CURRENT_TIMESTAMP),
('厚底ブーツ', 'ブーツ', 6599, 'Y2K', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=156016572', CURRENT_TIMESTAMP),
('ショルダーバッグ', 'バッグ', 5280, 'Y2K', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=149189923', CURRENT_TIMESTAMP),

-- ロック系
('ブルゾン', 'ブルゾン', 5990, 'ロック系', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=128555163', CURRENT_TIMESTAMP),
('バンドTシャツ', 'Tシャツ', 7990, 'ロック系', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=148381520', CURRENT_TIMESTAMP),
('スタッズブーツ', 'ブーツ', 36300, 'ロック系', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=154414415', CURRENT_TIMESTAMP),
('黒スキニー', 'パンツ', 7480, 'ロック系', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=130814163', CURRENT_TIMESTAMP),
('チェーンベルト', 'ベルト', 1340, 'ロック系', NULL, 0, '/static/images/no_image.png', 'https://zozo.jp/?c=gr&did=148955756', CURRENT_TIMESTAMP);

COMMIT;
