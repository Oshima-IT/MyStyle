import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import os

# Initialize Firestore
if not firebase_admin._apps:
    if os.path.exists("serviceAccountKey.json"):
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    else:
        print("Error: serviceAccountKey.json not found.")
        exit(1)

db = firestore.client()

def delete_collection(coll_ref, batch_size):
    docs = coll_ref.limit(batch_size).stream()
    deleted = 0

    for doc in docs:
        print(f'Deleting doc {doc.id} => {doc.to_dict().get("name")}')
        doc.reference.delete()
        deleted = deleted + 1

    if deleted >= batch_size:
        return delete_collection(coll_ref, batch_size)

def seed_items():
    # 1. Delete existing items
    print("Deleting existing items...")
    items_ref = db.collection('items')
    delete_collection(items_ref, 10)
    print("Existing items deleted.")

    # 2. Prepare new data
    # Data extracted from init_db.sql
    items_data = [
        # フレンチガーリー
        {'name': 'カーディガン', 'category': 'カーディガン', 'price': 4180, 'styles': 'フレンチガーリー', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=156706254'},
        {'name': 'ポレロ', 'category': 'ボレロ', 'price': 5940, 'styles': 'フレンチガーリー', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=157411305'},
        {'name': 'リボンブラウス', 'category': 'ブラウス', 'price': 5000, 'styles': 'フレンチガーリー', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=157892892'},
        {'name': 'リボンセットアップ', 'category': 'セットアップ', 'price': 8990, 'styles': 'フレンチガーリー', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=143837770'},
        {'name': '小花柄スカート', 'category': 'スカート', 'price': 4490, 'styles': 'フレンチガーリー', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=149563173'},

        # 地雷系
        {'name': '地雷セットアップ', 'category': 'セットアップ', 'price': 12100, 'styles': '地雷系', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=151232569'},
        {'name': '厚底ブーツ', 'category': 'ブーツ', 'price': 6518, 'styles': '地雷系', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=158935282'},
        {'name': 'チョーカー', 'category': 'アクセサリー', 'price': 2750, 'styles': '地雷系', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=147737351'},
        {'name': 'ブラウス', 'category': 'ブラウス', 'price': 5940, 'styles': '地雷系', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=147831739'},
        {'name': '地雷バッグ', 'category': 'バッグ', 'price': 12980, 'styles': '地雷系', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=153993050'},

        # サブカル系
        {'name': 'スウェット', 'category': 'スウェット', 'price': 13970, 'styles': 'サブカル系', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=160622545'},
        {'name': 'ロンT', 'category': 'ロンT', 'price': 5900, 'styles': 'サブカル系', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=150456157'},
        {'name': 'レッグウォーマー', 'category': 'レッグウォーマー', 'price': 2900, 'styles': 'サブカル系', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=150456070'},
        {'name': 'ジャージ', 'category': 'ジャージ', 'price': 12900, 'styles': 'サブカル系', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=150456199'},

        # 量産型
        {'name': '量産ワンピース', 'category': 'ワンピース', 'price': 10990, 'styles': '量産型', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=149817894'},
        {'name': '厚底ローファー', 'category': 'ローファー', 'price': 4389, 'styles': '量産型', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=153623183'},
        {'name': 'リボンヘアアクセ', 'category': 'ヘアアクセ', 'price': 2200, 'styles': '量産型', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=161649089'},
        {'name': 'フレアスカート', 'category': 'スカート', 'price': 5940, 'styles': '量産型', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=147834413'},
        {'name': 'レースタイツ', 'category': 'タイツ', 'price': 2860, 'styles': '量産型', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=141301414'},

        # ストリート系
        {'name': 'オーバーサイズパーカー', 'category': 'パーカー', 'price': 6600, 'styles': 'ストリート系', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=128611533'},
        {'name': 'スニーカー', 'category': 'スニーカー', 'price': 4500, 'styles': 'ストリート系', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=157886056'},
        {'name': 'カーゴパンツ', 'category': 'パンツ', 'price': 6219, 'styles': 'ストリート系', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=131053052'},
        {'name': 'キャップ', 'category': 'キャップ', 'price': 8800, 'styles': 'ストリート系', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=153219106'},
        {'name': 'グラフィックT', 'category': 'Tシャツ', 'price': 3450, 'styles': 'ストリート系', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=133981311'},

        # Y2K
        {'name': 'クロップドトップス', 'category': 'トップス', 'price': 4950, 'styles': 'Y2K', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=143631556'},
        {'name': 'ミニスカート', 'category': 'スカート', 'price': 5170, 'styles': 'Y2K', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=158132706'},
        {'name': 'カラフルサングラス', 'category': 'サングラス', 'price': 1500, 'styles': 'Y2K', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=153620804'},
        {'name': '厚底ブーツ', 'category': 'ブーツ', 'price': 6599, 'styles': 'Y2K', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=156016572'},
        {'name': 'ショルダーバッグ', 'category': 'バッグ', 'price': 5280, 'styles': 'Y2K', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=149189923'},

        # ロック系
        {'name': 'ブルゾン', 'category': 'ブルゾン', 'price': 5990, 'styles': 'ロック系', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=128555163'},
        {'name': 'バンドTシャツ', 'category': 'Tシャツ', 'price': 7990, 'styles': 'ロック系', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=148381520'},
        {'name': 'スタッズブーツ', 'category': 'ブーツ', 'price': 36300, 'styles': 'ロック系', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=154414415'},
        {'name': '黒スキニー', 'category': 'パンツ', 'price': 7480, 'styles': 'ロック系', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=130814163'},
        {'name': 'チェーンベルト', 'category': 'ベルト', 'price': 1340, 'styles': 'ロック系', 'colors': None, 'is_trend': 0, 'image_url': '/static/images/no_image.png', 'shop_url': 'https://zozo.jp/?c=gr&did=148955756'}
    ]

    print(f"Seeding {len(items_data)} items...")
    
    batch = db.batch()
    count = 0
    total_count = 0
    
    for item in items_data:
        item['created_at'] = datetime.now()
        doc_ref = items_ref.document()
        batch.set(doc_ref, item)
        count += 1
        
        # Commit every 500 items (though we have less)
        if count >= 400:
            batch.commit()
            total_count += count
            count = 0
            batch = db.batch()
            
    if count > 0:
        batch.commit()
        total_count += count
        
    print(f"Successfully seeded {total_count} items.")

if __name__ == "__main__":
    seed_items()
