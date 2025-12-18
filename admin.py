from datetime import datetime
import json
from flask import Blueprint, current_app, g, redirect, render_template, request, url_for, flash, session, abort, jsonify
from db import get_db
import requests
from duckduckgo_search import DDGS
from firebase_admin import firestore

admin_bp = Blueprint("admin", __name__)

def duckduckgo_image_search(query: str, max_results=8):
    try:
        with DDGS() as ddgs:
            results = ddgs.images(
                query,
                region="jp-jp",
                safesearch="off",
                max_results=max_results
            )
            return [r["image"] for r in results]
    except Exception as e:
        print(f"[DDG] Error: {e}")
        return []

@admin_bp.route("/items/suggest_images", methods=["POST"])
def suggest_images():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"images": []})
    
    images = duckduckgo_image_search(name)
    return jsonify({"images": images})

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
                "is_trend": 1 if request.form.get("is_trend") else 0,
                "created_at": datetime.now().date().isoformat()
            }
            items_ref.add(new_item)
            flash("item を追加しました", "success")
            return redirect(url_for("admin.admin_items"))

    # List items
    docs = items_ref.order_by('created_at', direction=firestore.Query.DESCENDING).stream()
    items = []
    for d in docs:
        i = d.to_dict()
        i['id'] = d.id
        items.append(i)
        
    return render_template("admin/items_list.html", items=items)


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
                "is_trend": 1 if request.form.get("is_trend") else 0
            })
            flash("item を更新しました", "success")
            return redirect(url_for("admin.admin_items"))

    return render_template("admin/item_edit.html", item=item)

@admin_bp.route("/items/<item_id>/delete", methods=["POST"])
def admin_item_delete(item_id):
    db = get_db()
    db.collection('items').document(str(item_id)).delete()
    flash("item を削除しました", "success")
    return redirect(url_for("admin.admin_items"))

# --- Shops ---
@admin_bp.route("/shops", methods=["GET", "POST"])
def admin_shops():
    db = get_db()
    shops_ref = db.collection('shops')
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        site_url = request.form.get("site_url", "").strip()
        if not name:
            flash("name は必須です", "error")
        else:
            shops_ref.add({
                "name": name, 
                "site_url": site_url or None
            })
            flash("shop を追加しました", "success")
            return redirect(url_for("admin.admin_shops"))

    docs = shops_ref.stream()
    shops = []
    for d in docs:
        s = d.to_dict()
        s['id'] = d.id
        shops.append(s)
        
    return render_template("admin/shops_list.html", shops=shops)


@admin_bp.route("/shops/<shop_id>/edit", methods=["GET", "POST"])
def admin_shop_edit(shop_id):
    db = get_db()
    shop_ref = db.collection('shops').document(str(shop_id))
    doc = shop_ref.get()
    
    if not doc.exists:
        flash("shop が存在しません", "error")
        return redirect(url_for("admin.admin_shops"))
        
    shop = doc.to_dict()
    shop['id'] = doc.id

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        site_url = request.form.get("site_url", "").strip()
        if not name:
            flash("name は必須です", "error")
        else:
            shop_ref.update({
                "name": name,
                "site_url": site_url or None
            })
            flash("shop を更新しました", "success")
            return redirect(url_for("admin.admin_shops"))

    return render_template("admin/shop_edit.html", shop=shop)


@admin_bp.route("/shops/<shop_id>/delete", methods=["POST"])
def admin_shop_delete(shop_id):
    db = get_db()
    db.collection('shops').document(str(shop_id)).delete()
    flash("shop を削除しました", "success")
    return redirect(url_for("admin.admin_shops"))

# --- Users ---
@admin_bp.route("/users", methods=["GET", "POST"])
def admin_users():
    db = get_db()
    users_ref = db.collection('users')
    
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password_hash = request.form.get("password_hash", "").strip()
        now = datetime.now().isoformat()

        if not email or not password_hash:
            flash("email と password_hash は必須です", "error")
        else:
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
        
    return render_template("admin/users_list.html", users=users)

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
