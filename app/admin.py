from datetime import datetime, timezone, timedelta
import json
from flask import Blueprint, current_app, g, redirect, render_template, request, url_for, flash, session, abort, jsonify
from werkzeug.security import generate_password_hash
from .db import get_db
from .stats import get_popularity_summary
import requests
import os
from firebase_admin import firestore

admin_bp = Blueprint("admin", __name__)

API_LIMIT = 100

def get_all_unique_categories(db):
    """Firestoreの全アイテムから一意なカテゴリリストを取得する"""
    items = db.collection('items').stream()
    categories = set()
    for doc in items:
        cat = doc.to_dict().get('category')
        if cat:
            categories.add(cat)
    return sorted(list(categories))

def get_all_unique_styles(db):
    """Fetch all unique styles from items."""
    items_ref = db.collection('items')
    # Optimization: If items many, this is slow. For now it's fine.
    docs = items_ref.stream()
    existing_styles = set()
    
    for doc in docs:
        d = doc.to_dict()
        raw_styles = d.get('styles')
        if raw_styles:
            if isinstance(raw_styles, str):
                parts = [s.strip() for s in raw_styles.split(',') if s.strip()]
                existing_styles.update(parts)
            elif isinstance(raw_styles, list):
                existing_styles.update([s for s in raw_styles if s])
    
    return sorted(list(existing_styles))

class QuotaManager:
    @staticmethod
    def get_quota_date_str():
        """
        Returns YYYYMMDD string based on 17:00 JST reset.
        If current time < 17:00 JST, belongs to 'today' (starts prev day 17:00).
        Actually, simpler logic:
        Day starts at 17:00 JST (08:00 UTC).
        If current UTC < 08:00, it's part of the 'previous' Japan day?
        Let's stick to simple logic as requested: "Reset at 17:00 JST".
        Means a new bucket starts at 17:00 JST.
        The bucket name can be formatted date of that start time.
        Current JST = UTC + 9.
        If we shift -17 hours, the date changes exactly at 17:00.
        """
        utcnow = datetime.now(timezone.utc)
        # Shift so that 17:00 JST (08:00 UTC) becomes 00:00 of the "logical" day
        # 08:00 UTC - 8 hours = 00:00
        # So effective date changes at 08:00 UTC.
        logical_date = utcnow - timedelta(hours=8)
        return logical_date.strftime("%Y%m%d")

    @staticmethod
    def get_usage():
        db = get_db()
        date_str = QuotaManager.get_quota_date_str()
        doc_ref = db.collection('api_stats').document(date_str)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict().get("request_count", 0)
        return 0

    @staticmethod
    def increment_usage():
        db = get_db()
        date_str = QuotaManager.get_quota_date_str()
        doc_ref = db.collection('api_stats').document(date_str)

        try:
            # Atomic increment
            if doc_ref.get().exists:
                doc_ref.update({"request_count": firestore.Increment(1)})
            else:
                doc_ref.set({"request_count": 1, "created_at": datetime.now().isoformat()})
        except Exception as e:
            print(f"[Quota] Error incrementing: {e}")

def google_image_search(query: str, num=5):
    api_key = os.environ.get("GOOGLE_API_KEY")
    cx = os.environ.get("GOOGLE_CX")

    if not api_key or not cx:
        print("[Google Search] Error: API key or CX not set.")
        return []

    # Use query as-is (Caller is responsible for keywords)
    search_query = query
    url = "https://www.googleapis.com/customsearch/v1"

    params = {
        "key": api_key,
        "cx": cx,
        "q": search_query,
        "searchType": "image",
        "num": num,
        "safe": "active"
    }

    try:
        response = requests.get(url, params=params)

        if response.status_code == 200:
            # Success - Increment Quota
            QuotaManager.increment_usage()

            data = response.json()
            items = data.get("items", [])
            return [item["link"] for item in items if "link" in item]
        elif response.status_code in [403, 429]:
             print(f"[Google Search] Quota exceeded or permission denied: {response.text}")
             # Return empty list or handle gracefully
             return []
        else:
             print(f"[Google Search] Error {response.status_code}: {response.text}")
             return []

    except Exception as e:
        print(f"[Google Search] Exception: {e}")
        return []

@admin_bp.context_processor
def inject_api_stats():
    return dict(
        api_usage=QuotaManager.get_usage(),
        api_limit=API_LIMIT
    )

@admin_bp.route("/items/suggest_images", methods=["POST"])
def suggest_images():
    data = request.get_json() or {}
    
    # Check for direct custom query (Frontend verified)
    if data.get("custom_query"):
        images = google_image_search(data["custom_query"])
        return jsonify({
            "images": images,
            "usage": QuotaManager.get_usage(),
            "limit": API_LIMIT
        })

    # Fallback Logic (if not verified on frontend)
    # 1. Sanitize Name
    raw_name = data.get("name") or ""
    # Zenkaku space to Hankaku, strip
    name = raw_name.replace("　", " ").strip()
    
    if not name:
        return jsonify({"images": [], "usage": QuotaManager.get_usage(), "limit": API_LIMIT})
    
    # 2. Build Dynamic Query
    # Get optional fields
    category = (data.get("category") or "").replace("　", " ").strip()
    styles = (data.get("styles") or "").replace("　", " ").strip()
    colors = (data.get("colors") or "").replace("　", " ").strip()
    
    # Base parts
    query_parts = [name]
    
    if colors:
        query_parts.append(colors.replace(",", " ")) # "Black, Red" -> "Black Red"
    if styles:
        query_parts.append(styles.replace(",", " "))
    if category:
        query_parts.append(category)
        
    # Add optimization keywords
    # "Fashion Item" is good, but "white background ecommerce" is requested high quality suffix
    query_parts.append("ファッション")
    query_parts.append("アイテム") # Was added by google_image_search
    query_parts.append("white background ecommerce")
    
    # Join with single spaces
    composed_query = " ".join(part for part in query_parts if part)
    
    images = google_image_search(composed_query)

    return jsonify({
        "images": images,
        "usage": QuotaManager.get_usage(),
        "limit": API_LIMIT
    })

@admin_bp.before_request
def restrict_admin_access():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))
    
    db = get_db()
    # In Firestore, we get document by ID
    user_ref = db.collection('users').document(user_id)
    doc = user_ref.get()
    
    if not doc.exists:
        abort(403)
    
    user_data = doc.to_dict()
    if user_data.get("email", "").lower() != "admin@example.com":
       abort(403)
    pass

@admin_bp.route("/")
def index():
    return redirect(url_for("admin.admin_items"))

# --- Items ---
@admin_bp.route("/items", methods=["GET", "POST"])
def admin_items():
    db = get_db()
    items_ref = db.collection('items')

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price = request.form.get("price")
        
        if not name:
            flash("name は必須です", "error")
        else:
            new_item = {
                "name": name,
                "image_url": request.form.get("image_url", "").strip() or None,
                "shop_url": request.form.get("shop_url", "").strip() or None,
                "category": request.form.get("category", "").strip() or None,
                "price": int(price) if price else None,
                "styles": request.form.get("styles", "").strip() or None,
                "colors": request.form.get("colors", "").strip() or None,
                "popularity_score": 0,
                "stats": {},
                "created_at": datetime.now().date().isoformat()
            }
            items_ref.add(new_item)
            flash("item を追加しました", "success")
            return redirect(url_for("admin.admin_items"))

    # Sort and Pagination logic
    sort_by = request.args.get('sort', 'date')  # 'score' or 'date'
    order = request.args.get('order', 'desc')   # 'asc' or 'desc'
    direction = firestore.Query.DESCENDING if order == 'desc' else firestore.Query.ASCENDING

    page = request.args.get('page', 1, type=int)
    per_page = 5
    
    # 1. Build Query
    query = items_ref
    if sort_by == 'score':
        # Simplify to single sort to avoid requiring composite index
        query = query.order_by('popularity_score', direction=direction)
    else:
        # Default: date
        query = query.order_by('created_at', direction=direction)

    # 2. Get total count for pagination UI
    total_count_query = items_ref.count()
    total_items = total_count_query.get()[0][0].value
    total_pages = (total_items + per_page - 1) // per_page

    # 3. Fetch paginated items
    docs = query.limit(per_page)\
                .offset((page - 1) * per_page)\
                .stream()
    
    items = []
    for d in docs:
        i = d.to_dict()
        i['id'] = d.id
        i['stats_summary'] = get_popularity_summary(i)
        items.append(i)
        
    available_styles = get_all_unique_styles(db)
    available_categories = get_all_unique_categories(db)
    return render_template("admin/items_list.html", 
                           items=items, 
                           page=page, 
                           total_pages=total_pages,
                           total_items=total_items,
                           per_page=per_page,
                           available_styles=available_styles,
                           available_categories=available_categories,
                           sort_by=sort_by,
                           order=order)


@admin_bp.route("/items/<item_id>/edit", methods=["GET", "POST"]) # String ID
def admin_item_edit(item_id):
    db = get_db()
    item_ref = db.collection('items').document(str(item_id))
    doc = item_ref.get()
    
    if not doc.exists:
        flash("item が存在しません", "error")
        return redirect(url_for("admin.admin_items"))
        
    item = doc.to_dict()
    item['id'] = doc.id

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price = request.form.get("price")

        if not name:
            flash("name は必須です", "error")
        else:
            item_ref.update({
                "name": name,
                "image_url": request.form.get("image_url", "").strip() or None,
                "shop_url": request.form.get("shop_url", "").strip() or None,
                "category": request.form.get("category", "").strip() or None,
                "price": int(price) if price else None,
                "styles": request.form.get("styles", "").strip() or None,
                "colors": request.form.get("colors", "").strip() or None,
                "popularity_score": int(request.form.get("popularity_score", 0))
            })
            flash("item を更新しました", "success")
            return redirect(url_for("admin.admin_items"))

    available_styles = get_all_unique_styles(db)
    return render_template("admin/item_edit.html", item=item, available_styles=available_styles)

@admin_bp.route("/items/<item_id>/delete", methods=["POST"])
def admin_item_delete(item_id):
    db = get_db()
    db.collection('items').document(str(item_id)).delete()
    flash("item を削除しました", "success")
    return redirect(url_for("admin.admin_items"))


# --- Users ---
@admin_bp.route("/users", methods=["GET", "POST"])
def admin_users():
    db = get_db()
    users_ref = db.collection('users')
    
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        now = datetime.now().isoformat()

        if not email or not password:
            flash("email と password は必須です", "error")
        else:
            # Hash the password before storing
            password_hash = generate_password_hash(password)
            
            users_ref.add({
                "email": email,
                "password_hash": password_hash,
                "preferred_styles": request.form.get("preferred_styles", "").strip() or None,
                "preferred_colors": request.form.get("preferred_colors", "").strip() or None,
                "created_at": now,
                "updated_at": now
            })
            flash("user を追加しました", "success")
            return redirect(url_for("admin.admin_users"))

    docs = users_ref.order_by("created_at", direction=firestore.Query.DESCENDING).stream()
    users = []
    for d in docs:
        u = d.to_dict()
        u['id'] = d.id
        users.append(u)
        
    available_styles = get_all_unique_styles(db)
    return render_template("admin/users_list.html", users=users, available_styles=available_styles)

@admin_bp.route("/users/<user_id>/edit", methods=["GET", "POST"])
def admin_user_edit(user_id):
    db = get_db()
    user_ref = db.collection('users').document(str(user_id))
    doc = user_ref.get()
    
    if not doc.exists:
        flash("user が存在しません", "error")
        return redirect(url_for("admin.admin_users"))
    
    user = doc.to_dict()
    user['id'] = doc.id

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password_hash = request.form.get("password_hash", "").strip()
        now = datetime.now().isoformat()

        if not email or not password_hash:
            flash("email と password_hash は必須です", "error")
        else:
            user_ref.update({
                "email": email,
                "password_hash": password_hash,
                "preferred_styles": request.form.get("preferred_styles", "").strip() or None,
                "preferred_colors": request.form.get("preferred_colors", "").strip() or None,
                "updated_at": now
            })
            flash("user を更新しました", "success")
            return redirect(url_for("admin.admin_users"))

    return render_template("admin/user_edit.html", user=user)

@admin_bp.route("/users/<user_id>/delete", methods=["POST"])
def admin_user_delete(user_id):
    db = get_db()
    db.collection('users').document(str(user_id)).delete()
    flash("user を削除しました", "success")
    return redirect(url_for("admin.admin_users"))
