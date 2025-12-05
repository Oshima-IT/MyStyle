from datetime import datetime
import sqlite3
from pathlib import Path
from flask import Blueprint, current_app, g, redirect, render_template, request, url_for, flash

admin_bp = Blueprint("admin", __name__)

def get_db():
    if "db" not in g:
        db_path = current_app.config.get("DB_PATH", Path("fassion.db"))
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 行をdict風で扱う
        g.db = conn
    return g.db

@admin_bp.teardown_app_request
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()

@admin_bp.route("/")
def index():
    return redirect(url_for("admin.admin_items"))

# --- Items ---
@admin_bp.route("/admin/items", methods=["GET", "POST"])
def admin_items():
    db = get_db()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        image_url = request.form.get("image_url", "").strip()
        category = request.form.get("category", "").strip()
        styles = request.form.get("styles", "").strip()
        colors = request.form.get("colors", "").strip()
        is_trend = 1 if request.form.get("is_trend") else 0
        price = request.form.get("price")
        created_at = datetime.now().date().isoformat()

        if not name:
            flash("name は必須です", "error")
        else:
            db.execute(
                """
                INSERT INTO items (name, image_url, category, price, styles, colors, is_trend, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    image_url or None,
                    category or None,
                    int(price) if price else None,
                    styles or None,
                    colors or None,
                    is_trend,
                    created_at,
                ),
            )
            db.commit()
            flash("item を追加しました", "success")
            return redirect(url_for("admin.admin_items"))

    items = db.execute(
        "SELECT id, name, category, price, styles, colors, is_trend, created_at FROM items ORDER BY id DESC"
    ).fetchall()
    return render_template("admin/items_list.html", items=items)


@admin_bp.route("/admin/items/<int:item_id>/edit", methods=["GET", "POST"])
def admin_item_edit(item_id: int):
    db = get_db()
    item = db.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if item is None:
        flash("item が存在しません", "error")
        return redirect(url_for("admin.admin_items"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        image_url = request.form.get("image_url", "").strip()
        category = request.form.get("category", "").strip()
        styles = request.form.get("styles", "").strip()
        colors = request.form.get("colors", "").strip()
        is_trend = 1 if request.form.get("is_trend") else 0
        price = request.form.get("price")

        if not name:
            flash("name は必須です", "error")
        else:
            db.execute(
                """
                UPDATE items
                SET name=?, image_url=?, category=?, price=?, styles=?, colors=?, is_trend=?
                WHERE id=?
                """,
                (
                    name,
                    image_url or None,
                    category or None,
                    int(price) if price else None,
                    styles or None,
                    colors or None,
                    is_trend,
                    item_id,
                ),
            )
            db.commit()
            flash("item を更新しました", "success")
            return redirect(url_for("admin.admin_items"))

    return render_template("admin/item_edit.html", item=item)

@admin_bp.route("/admin/items/<int:item_id>/delete", methods=["POST"])
def admin_item_delete(item_id: int):
    db = get_db()
    db.execute("DELETE FROM items WHERE id = ?", (item_id,))
    db.commit()
    flash("item を削除しました", "success")
    return redirect(url_for("admin.admin_items"))

# --- Shops ---
@admin_bp.route("/admin/shops", methods=["GET", "POST"])
def admin_shops():
    db = get_db()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        site_url = request.form.get("site_url", "").strip()
        if not name:
            flash("name は必須です", "error")
        else:
            db.execute(
                "INSERT INTO shops (name, site_url) VALUES (?, ?)",
                (name, site_url or None),
            )
            db.commit()
            flash("shop を追加しました", "success")
            return redirect(url_for("admin.admin_shops"))

    shops = db.execute("SELECT id, name, site_url FROM shops ORDER BY id DESC").fetchall()
    return render_template("admin/shops_list.html", shops=shops)


@admin_bp.route("/admin/shops/<int:shop_id>/edit", methods=["GET", "POST"])
def admin_shop_edit(shop_id: int):
    db = get_db()
    shop = db.execute("SELECT * FROM shops WHERE id = ?", (shop_id,)).fetchone()
    if shop is None:
        flash("shop が存在しません", "error")
        return redirect(url_for("admin.admin_shops"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        site_url = request.form.get("site_url", "").strip()
        if not name:
            flash("name は必須です", "error")
        else:
            db.execute(
                "UPDATE shops SET name=?, site_url=? WHERE id=?",
                (name, site_url or None, shop_id),
            )
            db.commit()
            flash("shop を更新しました", "success")
            return redirect(url_for("admin.admin_shops"))

    return render_template("admin/shop_edit.html", shop=shop)


@admin_bp.route("/admin/shops/<int:shop_id>/delete", methods=["POST"])
def admin_shop_delete(shop_id: int):
    db = get_db()
    db.execute("DELETE FROM shops WHERE id = ?", (shop_id,))
    db.commit()
    flash("shop を削除しました", "success")
    return redirect(url_for("admin.admin_shops"))

# --- Users ---
@admin_bp.route("/admin/users", methods=["GET", "POST"])
def admin_users():
    db = get_db()
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password_hash = request.form.get("password_hash", "").strip()
        preferred_styles = request.form.get("preferred_styles", "").strip()
        preferred_colors = request.form.get("preferred_colors", "").strip()
        now = datetime.now().isoformat(timespec="seconds")

        if not email or not password_hash:
            flash("email と password_hash は必須です", "error")
        else:
            db.execute(
                """
                INSERT INTO users (email, password_hash, preferred_styles, preferred_colors, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    email,
                    password_hash,
                    preferred_styles or None,
                    preferred_colors or None,
                    now,
                    now,
                ),
            )
            db.commit()
            flash("user を追加しました", "success")
            return redirect(url_for("admin.admin_users"))

    users = db.execute(
        "SELECT id, email, preferred_styles, preferred_colors, created_at, updated_at FROM users ORDER BY id DESC"
    ).fetchall()
    return render_template("admin/users_list.html", users=users)

@admin_bp.route("/admin/users/<int:user_id>/edit", methods=["GET", "POST"])
def admin_user_edit(user_id: int):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if user is None:
        flash("user が存在しません", "error")
        return redirect(url_for("admin.admin_users"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password_hash = request.form.get("password_hash", "").strip()
        preferred_styles = request.form.get("preferred_styles", "").strip()
        preferred_colors = request.form.get("preferred_colors", "").strip()
        now = datetime.now().isoformat(timespec="seconds")

        if not email or not password_hash:
            flash("email と password_hash は必須です", "error")
        else:
            db.execute(
                """
                UPDATE users
                SET email=?, password_hash=?, preferred_styles=?, preferred_colors=?, updated_at=?
                WHERE id=?
                """,
                (
                    email,
                    password_hash,
                    preferred_styles or None,
                    preferred_colors or None,
                    now,
                    user_id,
                ),
            )
            db.commit()
            flash("user を更新しました", "success")
            return redirect(url_for("admin.admin_users"))

    return render_template("admin/user_edit.html", user=user)

@admin_bp.route("/admin/users/<int:user_id>/delete", methods=["POST"])
def admin_user_delete(user_id: int):
    db = get_db()
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    flash("user を削除しました", "success")
    return redirect(url_for("admin.admin_users"))
