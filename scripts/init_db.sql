BEGIN TRANSACTION;

-- Items seed
INSERT INTO items (name, category, price, styles, colors, is_trend, image_url, shop_url, created_at) VALUES
-- フレンチガーリー
('フリルリボンカーディガン', 'カーディガン', 4180, 'フレンチガーリー', NULL, 0, 'https://c.imgz.jp/549/97641549/97641549b_38_d_500.jpg', 'https://zozo.jp/?c=gr&did=156706254', CURRENT_TIMESTAMP),
('チェックフリルカーディガン', 'カーディガン', 5940, 'フレンチガーリー', NULL, 0, 'https://c.imgz.jp/891/98468891/98468891b_18_d_500.jpg', 'https://zozo.jp/?c=gr&did=157411305', CURRENT_TIMESTAMP),
('シンプルボウタイシャツブラウス', 'ブラウス', 5000, 'フレンチガーリー', NULL, 0, 'https://c.imgz.jp/602/83195602/83195602b_151_d_500.jpg', 'https://zozo.jp/?c=gr&did=157892892', CURRENT_TIMESTAMP),
('ラメツイードビッグリボンセットアップ', 'セットアップ', 8990, 'フレンチガーリー', NULL, 0, 'https://c.imgz.jp/671/89860671/89860671b_20_d_500.jpg', 'https://zozo.jp/?c=gr&did=143837770', CURRENT_TIMESTAMP),
('ドロストギャザーフレアミニスカート', 'スカート', 4490, 'フレンチガーリー', NULL, 0, 'https://c.imgz.jp/090/93450090/93450090b_173_d_500.jpg', 'https://zozo.jp/?c=gr&did=149563173', CURRENT_TIMESTAMP),

-- 地雷系
('クロス刺繍３段フリルセットアップ', 'セットアップ', 12100, '地雷系', NULL, 0, 'https://c.imgz.jp/514/92467514/92467514b_2_d_500.jpg', 'https://zozo.jp/?c=gr&did=151232569', CURRENT_TIMESTAMP),
('超厚底×美脚レッグカバーSETブーツ', 'ブーツ', 6518, '地雷系', NULL, 0, 'https://c.imgz.jp/414/97496414/97496414b_1_d_500.jpg', 'https://zozo.jp/?c=gr&did=158935282', CURRENT_TIMESTAMP),
('ハートロックチャーム×チェーンチョーカー', 'チョーカー', 2750, '地雷系', NULL, 0, 'https://c.imgz.jp/426/92427426/92427426b_8_d_500.jpg', 'https://zozo.jp/?c=gr&did=147737351', CURRENT_TIMESTAMP),
('ハートクロススタッズバックパック', 'バッグ', 12980, '地雷系', NULL, 0, 'https://c.imgz.jp/452/96371452/96371452b_8_d_500.jpg', 'https://zozo.jp/?c=gr&did=153993050', CURRENT_TIMESTAMP),

-- サブカル系
('スウェットトレーナー', 'スウェット', 13970, 'サブカル系', NULL, 0, 'https://c.imgz.jp/102/100491102/100491102b_8_d_500.jpg', 'https://zozo.jp/?c=gr&did=160622545', CURRENT_TIMESTAMP),
('悪魔ちゃんBIGロンTEE', 'カットソー', 5900, 'サブカル系', NULL, 0, 'https://c.imgz.jp/449/93999449/93999449b_8_d_500.jpg', 'https://zozo.jp/?c=gr&did=150456157', CURRENT_TIMESTAMP),
('最強もこもこレッグウォーマー', 'レッグウォーマー', 2900, 'サブカル系', NULL, 0, 'https://c.imgz.jp/392/93999392/93999392b_38_d_500.jpg', 'https://zozo.jp/?c=gr&did=150456070', CURRENT_TIMESTAMP),
('新！ネ申おジャージ参上！', 'ジャージ', 12900, 'サブカル系', NULL, 0, 'https://c.imgz.jp/479/93999479/93999479b_8_d_500.jpg', 'https://zozo.jp/?c=gr&did=150456199', CURRENT_TIMESTAMP),

-- 量産型
('ドッキンジャスカ風ワンピース', 'ワンピース', 10990, '量産型', NULL, 0, 'https://c.imgz.jp/028/93616028/93616028b_173_d_500.jpg', 'https://zozo.jp/?c=gr&did=149817894', CURRENT_TIMESTAMP),
('ハートバックルマニッシュシューズ', 'ローファー', 4389, '量産型', NULL, 0, 'https://c.imgz.jp/008/96141008/96141008b_8_d_500.jpg', 'https://zozo.jp/?c=gr&did=153623183', CURRENT_TIMESTAMP),
('ハートチャームサテンリボンペア', 'ヘアクリップ', 2200, '量産型', NULL, 0, 'https://c.imgz.jp/603/101189603/101189603b_8_d_500.jpg', 'https://zozo.jp/?c=gr&did=161649089', CURRENT_TIMESTAMP),
('ハイウエストスピンドルボリュームスカパン', 'スカート', 5940, '量産型', NULL, 0, 'https://c.imgz.jp/473/92467473/92467473b_8_d_500.jpg', 'https://zozo.jp/?c=gr&did=147834413', CURRENT_TIMESTAMP),
('フラワーレースタイツ', 'タイツ', 2860, '量産型', NULL, 0, 'https://c.imgz.jp/755/88089755/88089755b_8_d_500.jpg', 'https://zozo.jp/?c=gr&did=141301414', CURRENT_TIMESTAMP),

-- ストリート系
('オーバーサイズパーカー', 'パーカー', 6600, 'ストリート系', NULL, 0, 'https://c.imgz.jp/429/77687429/77687429b_10031_d_500.jpg', 'https://zozo.jp/?c=gr&did=128611533', CURRENT_TIMESTAMP),
('メッシュ厚底スニーカー', 'スニーカー', 4500, 'ストリート系', NULL, 0, 'https://c.imgz.jp/244/98746244/98746244b_29_d_500.jpg', 'https://zozo.jp/?c=gr&did=157886056', CURRENT_TIMESTAMP),
('デニムカーゴパンツ', 'パンツ', 6219, 'ストリート系', NULL, 0, 'https://c.imgz.jp/056/81485056/81485056b_24_d_500.jpg', 'https://zozo.jp/?c=gr&did=131053052', CURRENT_TIMESTAMP),
('ベースボールキャップ', 'キャップ', 8800, 'ストリート系', NULL, 0, 'https://c.imgz.jp/641/92874641/92874641b_422_d_500.jpg', 'https://zozo.jp/?c=gr&did=153219106', CURRENT_TIMESTAMP),
('グラフィックT', 'Tシャツ', 3450, 'ストリート系', NULL, 0, 'https://c.imgz.jp/112/83300112/83300112b_1_d_500.jpg', 'https://zozo.jp/?c=gr&did=133981311', CURRENT_TIMESTAMP),

-- Y2K
('ジップアップクロップドニットカーディガン', 'カーディガン', 4950, 'Y2K', NULL, 0, 'https://c.imgz.jp/960/89699960/89699960b_16_d_500.jpg', 'https://zozo.jp/?c=gr&did=143631556', CURRENT_TIMESTAMP),
('ビンテージウォッシュ加工のデニムミニスカート', 'スカート', 5170, 'Y2K', NULL, 0, 'https://c.imgz.jp/400/98909400/98909400b_17_d_500.jpg', 'https://zozo.jp/?c=gr&did=158132706', CURRENT_TIMESTAMP),
('クリアレンズサングラス ユニセックス', 'サングラス', 1500, 'Y2K', NULL, 0, 'https://c.imgz.jp/327/96140327/96140327b_29_d_500.jpg', 'https://zozo.jp/?c=gr&did=153620804', CURRENT_TIMESTAMP),
('厚底カバーベルトミドルブーツ', 'ブーツ', 6599, 'Y2K', NULL, 0, 'https://c.imgz.jp/163/97563163/97563163b_17_d_500.jpg', 'https://zozo.jp/?c=gr&did=156016572', CURRENT_TIMESTAMP),
('ショルダーバッグ', 'バッグ', 5280, 'Y2K', NULL, 0, 'https://c.imgz.jp/584/93187584/93187584b_8_d_500.jpg', 'https://zozo.jp/?c=gr&did=149189923', CURRENT_TIMESTAMP),

-- ロック系
('2WAYカラーショート丈フェイクレザーブルゾン', 'ブルゾン', 5990, 'ロック系', NULL, 0, 'https://c.imgz.jp/971/79705971/79705971b_8_d_500.jpg', 'https://zozo.jp/?c=gr&did=128555163', CURRENT_TIMESTAMP),
('バンドTシャツ', 'Tシャツ', 7990, 'ロック系', NULL, 0, 'https://c.imgz.jp/981/92732981/92732981b_8_d_500.jpg', 'https://zozo.jp/?c=gr&did=148381520', CURRENT_TIMESTAMP),
('アンクル ブーツ', 'ブーツ', 36300, 'ロック系', NULL, 0, 'https://c.imgz.jp/617/96633617/96633617b_8_d_500.jpg', 'https://zozo.jp/?c=gr&did=154414415', CURRENT_TIMESTAMP),
('ヘムシャーリングギャザーストレッチフレアパンツ', 'パンツ', 7480, 'ロック系', NULL, 0, 'https://c.imgz.jp/492/81321492/81321492b_8_d_500.jpg', 'https://zozo.jp/?c=gr&did=130814163', CURRENT_TIMESTAMP),
('ダブルロック太めパンクベルト', 'ベルト', 1340, 'ロック系', NULL, 0, 'https://c.imgz.jp/862/93048862/93048862b_8_d_500.jpg', 'https://zozo.jp/?c=gr&did=148955756', CURRENT_TIMESTAMP);

COMMIT;
