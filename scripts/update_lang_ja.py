import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, get_db
from firebase_admin import firestore

# Japanese assignments
JA_MAP = {
    "ストリート系": "ストリートファッション",
    "量産型": "量産型", # Often implies fashion context in recent stats or might be disambig
    "地雷系": "地雷系",
    "ロック系": "パンク・ファッション",
    "サブカル系": "ストリートスナップ", # Alternative? Or ロリータ. Let's try ストリートスナップ for broad coverage or stay generic
    # Re-map Y2K?
    "Y2K": "Y2K_(ファッション)",
    "フレンチガーリー": "ガーリー" # Girly
}

def update_lang():
    with app.app_context():
        db = get_db()
        batch = db.batch()
        col = db.collection('style_wiki_map')
        
        for label, article in JA_MAP.items():
            doc_ref = col.document(label)
            # Update article AND lang
            batch.set(doc_ref, {
                "wiki_article": article,
                "lang": "ja",
                "is_enabled": True,
                "updated_at": firestore.SERVER_TIMESTAMP
            }, merge=True)
            print(f"Updating to JA: {label} -> {article}")
        
        batch.commit()
        print("Done.")

if __name__ == "__main__":
    update_lang()
