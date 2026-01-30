import argparse
import json
from pathlib import Path
from typing import List

import firebase_admin
from firebase_admin import credentials, firestore

BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = BASE_DIR / "config" / "serviceAccountKey.json"
DATA_DIR = BASE_DIR / "github_pages" / "data"
INSTANCE_DIR = BASE_DIR / "instance"

ITEM_FIELDS = ["name", "price", "image_url", "imageUrl", "shop_url", "detail_url", "category", "styles", "description", "notes"]


def init_firestore():
    if not firebase_admin._apps:
        if not CONFIG_PATH.exists():
            raise FileNotFoundError(f"serviceAccountKey.json not found at {CONFIG_PATH}")
        cred = credentials.Certificate(str(CONFIG_PATH))
        firebase_admin.initialize_app(cred)
    return firestore.client()


def normalize_styles(value) -> List[str]:
    if not value:
        return []
    styles = []
    if isinstance(value, str):
        tokens = value.replace("、", ",").split(",")
        styles = [tok.strip() for tok in tokens if tok.strip()]
    elif isinstance(value, list):
        styles = [str(tok).strip() for tok in value if str(tok).strip()]
    return sorted(set(styles))


def infer_weather_tags(item_dict) -> List[str]:
    corpus = " ".join(str(item_dict.get(field, "")) for field in ITEM_FIELDS).lower()

    def contains(keywords):
        return any(word in corpus for word in keywords)

    tags = []
    if contains(["撥水", "防水", "waterproof", "レイン", "rain"]):
        tags.append("waterproof")
    if contains(["防風", "wind", "シェル", "シェル"]):
        tags.append("windproof")
    if contains(["コート", "アウター", "ジャケット", "ブルゾン"]):
        tags.append("outer")
    if contains(["レイヤ", "layer", "ベスト", "カーデ", "cardigan"]):
        tags.append("layering")
    if contains(["メッシュ", "透け", "breathable", "リネン", "linen", "エアリー"]):
        tags.append("breathable")
    return sorted(set(tags))


def serialize_item(doc):
    data = doc.to_dict() or {}
    styles = normalize_styles(data.get("styles"))
    item = {
        "id": doc.id,
        "name": data.get("name", ""),
        "price": data.get("price"),
        "image_url": data.get("image_url") or data.get("imageUrl"),
        "detail_url": data.get("shop_url") or data.get("detail_url") or "#",
        "styles": styles,
        "weather_tags": infer_weather_tags(data),
        "popularity": data.get("popularity_score") or data.get("popularity", 0)
    }
    return item


def fetch_items(db, limit=None):
    docs = db.collection("items").stream()
    items = [serialize_item(doc) for doc in docs]
    items.sort(key=lambda x: (x.get("popularity") or 0, x.get("name", "")), reverse=True)
    if limit:
        return items[:limit]
    return items


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def export_weather_cache():
    src = INSTANCE_DIR / "weather_cache.json"
    if not src.exists():
        print("[warn] weather_cache.json not found; skipping weather export")
        return
    data = json.loads(src.read_text(encoding="utf-8"))
    write_json(DATA_DIR / "weather.json", data)


def export_wiki_cache():
    src = INSTANCE_DIR / "wiki_trend_cache.json"
    if not src.exists():
        print("[warn] wiki_trend_cache.json not found; skipping wiki export")
        return
    data = json.loads(src.read_text(encoding="utf-8"))
    write_json(DATA_DIR / "wiki_trends.json", data)


def build_history(items, count):
    return items[:count]


def build_saved(items, count):
    offset = count if len(items) > count else 0
    return items[offset:offset + count] if items else []


def main():
    parser = argparse.ArgumentParser(description="Export Firestore + cache data for GitHub Pages build")
    parser.add_argument("--limit", type=int, default=60, help="Max number of items to export")
    parser.add_argument("--history", type=int, default=5, help="Number of items for history.json")
    parser.add_argument("--saved", type=int, default=5, help="Number of items for saved_items.json")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    db = init_firestore()
    items = fetch_items(db, limit=args.limit)
    if not items:
        print("[warn] No items found in Firestore")

    write_json(DATA_DIR / "items.json", items)

    all_styles = sorted({style for item in items for style in item.get("styles", [])})
    write_json(DATA_DIR / "styles.json", {"available_styles": all_styles})

    history_payload = build_history(items, args.history)
    write_json(DATA_DIR / "history.json", history_payload)

    saved_payload = build_saved(items, args.saved)
    write_json(DATA_DIR / "saved_items.json", saved_payload)

    export_weather_cache()
    export_wiki_cache()

    print(f"Export complete. Files written to {DATA_DIR}")


if __name__ == "__main__":
    main()
