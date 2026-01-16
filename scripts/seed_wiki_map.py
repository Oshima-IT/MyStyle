import firebase_admin
from firebase_admin import credentials, firestore
import os
import sys

# Add app path to sys.path to load config if needed, but here we just need firebase
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Initialize Firebase (Using the same method as app/__init__.py or app/db.py)
# Assuming serviceAccountKey.json is in a specific location or implicit
# For this script, we'll try to find the key or assume GOOGLE_APPLICATION_CREDENTIALS
# If run locally with same env as app, it should work.

def get_db_standalone():
    if not firebase_admin._apps:
        # Try to locate serviceAccountKey.json in instance or root
        possible_keys = [
            os.path.join(os.path.dirname(__file__), '..', 'config', 'serviceAccountKey.json'),
            'config/serviceAccountKey.json',
            'c:\\Python\\MyStyle\\config\\serviceAccountKey.json'
        ]
        cred_path = None
        for p in possible_keys:
            if os.path.exists(p):
                cred_path = p
                break
        
        if cred_path:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        else:
            # Fallback to default (env var)
            firebase_admin.initialize_app()
            
    return firestore.client()

# Current Hardcoded Mapping
WIKI_STYLE_MAPPING = {
    "ストリート": "Street_fashion",
    "ヴィンテージ": "Vintage_clothing",
    "Y2K": "Y2K_fashion",
    "ミニマリズム": "Minimalism",
    "ゴープコア": "Gorpcore",
    "サステナブル": "Sustainable_fashion",
    "スニーカー": "Sneaker_collecting",
    "モード": "High_fashion",
    "アウトドア": "Outdoor_recreation",
    "スポーツ": "Sportswear",
    "韓国ファッション": "Korean_fashion"
}

def seed_map():
    db = get_db_standalone()
    col_ref = db.collection('style_wiki_map')
    
    print("Seeding style_wiki_map...")
    batch = db.batch()
    
    for label, article in WIKI_STYLE_MAPPING.items():
        doc_id = label.strip() # Key is Japanese Label
        doc_ref = col_ref.document(doc_id)
        
        data = {
            "wiki_article": article,
            "is_enabled": True,
            "updated_at": firestore.SERVER_TIMESTAMP
        }
        
        batch.set(doc_ref, data, merge=True)
        print(f"Prepared: {label} -> {article}")

    batch.commit()
    print("Commit complete.")

if __name__ == "__main__":
    seed_map()
