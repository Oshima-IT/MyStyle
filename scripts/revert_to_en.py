import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, get_db
from firebase_admin import firestore

# Revert to English Mappings
EN_MAP = {
    "ストリート系": "Street_fashion",
    "フレンチガーリー": "Girly_girl", 
    "モード系": "High_fashion",
    "古着": "Vintage_clothing",
    "韓国ストリート": "Korean_fashion",
    "ロック系": "Punk_fashion",
    "量産型": "Girly_girl",
    "地雷系": "Goth_subculture",
    "サブカル系": "Japanese_street_fashion",
    "Y2K": "Y2K_fashion",
    # Initial seeds also need to be ensured as EN
    "ストリート": "Street_fashion",
    "ヴィンテージ": "Vintage_clothing",
    "ミニマリズム": "Minimalism",
    "ゴープコア": "Gorpcore",
    "サステナブル": "Sustainable_fashion",
    "スニーカー": "Sneaker_collecting",
    "モード": "High_fashion",
    "アウトドア": "Outdoor_recreation",
    "スポーツ": "Sportswear",
    "韓国ファッション": "Korean_fashion"
}

def revert_to_en():
    with app.app_context():
        db = get_db()
        batch = db.batch()
        col = db.collection('style_wiki_map')
        
        for label, article in EN_MAP.items():
            doc_ref = col.document(label)
            batch.set(doc_ref, {
                "wiki_article": article,
                "lang": "en",
                "is_enabled": True,
                "updated_at": firestore.SERVER_TIMESTAMP
            }, merge=True)
            print(f"Reverting to EN: {label} -> {article}")
        
        batch.commit()
        print("Done.")

if __name__ == "__main__":
    revert_to_en()
