from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db, close_db

from admin import admin_bp

app = Flask(__name__)
app.secret_key = "your_secret_key"

# アプリ終了時にDB接続を閉じる
app.teardown_appcontext(close_db)

app.register_blueprint(admin_bp, url_prefix="/admin")

@app.route('/')
def index():
    return redirect(url_for('home'))


# ------------------------
# ログイン
# ------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session["logged_in"] = True
            session["user_id"] = user["id"]

            styles = user["preferred_styles"].split(",") if user["preferred_styles"] else []
            session["user_styles"] = styles

            return redirect(url_for("home"))

        return render_template("login.html", error="メールアドレスまたはパスワードが違います")

    return render_template("login.html")


# ------------------------
# 新規登録 (スペル修正: /acount -> /account)
# ------------------------
@app.route('/account', methods=['GET', 'POST'])
def account_registration():
    if request.method == 'POST':
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if password != confirm:
            return render_template("account.html", error="確認用パスワードが一致していません")

        conn = get_db()
        exists = conn.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone()

        if exists:
            return render_template("account.html", error="このメールアドレスはすでに登録されています")

        # パスワードをハッシュ化して保存
        password_hash = generate_password_hash(password)

        conn.execute(
            "INSERT INTO users (email, password_hash, preferred_styles, preferred_colors, created_at, updated_at) "
            "VALUES (?, ?, '', '', datetime('now'), datetime('now'))",
            (email, password_hash)
        )
        conn.commit()

        return redirect(url_for("login"))

    return render_template("account.html")


# ------------------------
# ログアウト
# ------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login"))


# ------------------------
# ホーム画面
# ------------------------
@app.route('/home')
def home():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    styles = session.get("user_styles", [])

    conn = get_db()

    # 系統が設定されていれば推薦で styles カラムを絞り込み
    if styles:
        like_query = " OR ".join(["styles LIKE ?" for _ in styles])
        params = [f"%{s}%" for s in styles]
        items = conn.execute(
            f"SELECT * FROM items WHERE {like_query}",
            params
        ).fetchall()
    else:
        items = conn.execute("SELECT * FROM items").fetchall()

    return render_template("home.html", current_styles=styles, items=items)


# ------------------------
# 詳細ページ
# ------------------------
@app.route('/detail/<int:item_id>')
def detail(item_id):
    conn = get_db()
    item = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()

    shops = conn.execute(
        "SELECT s.name, s.site_url FROM shops s "
        "JOIN item_shops is2 ON s.id = is2.shop_id WHERE is2.item_id=?",
        (item_id,)
    ) .fetchall()

    return render_template("detail.html", item=item, shops=shops)


# ------------------------
# 系統設定
# ------------------------
@app.route('/setting', methods=['GET', 'POST'])
def setting():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    if request.method == "POST":
        selected_styles = request.form.getlist("style")
        styles_str = ",".join(selected_styles)

        conn = get_db()
        conn.execute(
            "UPDATE users SET preferred_styles=?, updated_at=datetime('now') WHERE id=?",
            (styles_str, session["user_id"])
        )
        conn.commit()

        session["user_styles"] = selected_styles

        return redirect(url_for("home"))

    ALL_STYLES = [
        "カジュアル", "きれいめ", "ストリート", "モード",
        "フェミニン", "韓国風", "アメカジ", "トラッド",
        "古着", "スポーティー", "コンサバ", "ナチュラル"
    ]

    # 管理者判定
    conn = get_db()
    user = conn.execute("SELECT email FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    is_admin = False
    if user and user["email"].lower() == "admin@example.com":
        is_admin = True

    return render_template("setting.html", available_styles=ALL_STYLES, is_admin=is_admin)


if __name__ == '__main__':
    app.run(debug=True)
