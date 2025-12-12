from flask import Flask, render_template, request, redirect, url_for, session, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import json
from db import get_db, close_db
from datetime import datetime
from google_trends import get_trends, get_related_queries
from admin import admin_bp

app = Flask(__name__)
app.secret_key = "your_secret_key"

# 利用可能な系統一覧をグローバルで定義
ALL_STYLES = [
    "カジュアル", "きれいめ", "ストリート", "モード",
    "フェミニン", "韓国風", "アメカジ", "トラッド",
    "古着", "スポーティー", "コンサバ", "ナチュラル"
]

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

            # 匿名で見ていた履歴がクッキーにあればDBへ移行してクッキーを消す
            anon = request.cookies.get("anon_history")
            if anon:
                try:
                    entries = json.loads(anon)
                    conn = get_db()
                    for e in entries:
                        item_id = e.get("item_id")
                        viewed_at = e.get("viewed_at")
                        if item_id and viewed_at:
                            conn.execute(
                                "INSERT INTO history (user_id, item_id, viewed_at) VALUES (?, ?, ?)",
                                (user["id"], item_id, viewed_at),
                            )
                    conn.commit()
                except Exception:
                    pass

                resp = make_response(redirect(url_for("home")))
                resp.delete_cookie("anon_history")
                return resp

            return redirect(url_for("home"))

        return render_template("login.html", error="メールアドレスまたはパスワードが違います")

    return render_template("login.html")


# ------------------------
# 新規登録 (/account)
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

    if styles:
        like_query = " OR ".join(["styles LIKE ?" for _ in styles])
        params = [f"%{s}%" for s in styles]
        items = conn.execute(
            f"SELECT * FROM items WHERE {like_query}",
            params
        ).fetchall()
    else:
        items = conn.execute("SELECT * FROM items").fetchall()

    # ログインユーザーの直近閲覧履歴（最大10件）を取得して渡す
    recent_history = []
    try:
        recent_history = conn.execute(
            """
            SELECT h.item_id, h.viewed_at, i.name, i.price, i.image_url
            FROM history h
            LEFT JOIN items i ON h.item_id = i.id
            WHERE h.user_id = ?
            ORDER BY h.viewed_at DESC
            LIMIT 10
            """,
            (session["user_id"],),
        ).fetchall()
    except Exception:
        recent_history = []

    return render_template("home.html", current_styles=styles, items=items, recent_history=recent_history, available_styles=ALL_STYLES)


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
    ).fetchall()

    # ログイン中のユーザーがいれば閲覧履歴を記録する
    if session.get("logged_in") and session.get("user_id"):
        try:
            conn.execute(
                "INSERT INTO history (user_id, item_id, viewed_at) VALUES (?, ?, ?)",
                (session["user_id"], item_id, datetime.now().isoformat()),
            )
            conn.commit()
        except Exception:
            # 履歴記録に失敗しても詳細表示は継続
            pass

    # 未ログイン時はクッキーに一時保存しておく（ログイン時にDBへ移行）
    if not session.get("logged_in") or not session.get("user_id"):
        try:
            anon = request.cookies.get("anon_history")
            arr = json.loads(anon) if anon else []
        except Exception:
            arr = []

        # 同じitem_idの古いエントリを除き先頭挿入、最大20件
        arr = [e for e in arr if e.get("item_id") != item_id]
        arr.insert(0, {"item_id": item_id, "viewed_at": datetime.now().isoformat()})
        arr = arr[:20]

        resp = make_response(render_template("detail.html", item=item, shops=shops))
        # 日本語名などを扱うため ensure_ascii=False
        resp.set_cookie("anon_history", json.dumps(arr, ensure_ascii=False), max_age=30*24*3600, httponly=True)
        return resp

    return render_template("detail.html", item=item, shops=shops)


@app.route('/history')
def history():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    conn = get_db()
    rows = conn.execute(
        """
        SELECT h.id, h.item_id, h.viewed_at, i.name, i.price, i.image_url
        FROM history h
        LEFT JOIN items i ON h.item_id = i.id
        WHERE h.user_id = ?
        ORDER BY h.viewed_at DESC
        LIMIT 50
        """,
        (session["user_id"],),
    ).fetchall()

    return render_template("history.html", history=rows)
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

    # 管理者判定
    ALL_STYLES = [
        "カジュアル", "きれいめ", "ストリート", "モード",
        "フェミニン", "韓国風", "アメカジ", "トラッド",
        "古着", "スポーティー", "コンサバ", "ナチュラル"
    ]

    conn = get_db()
    user = conn.execute("SELECT email FROM users WHERE id = ?", (session["user_id"],)).fetchone()

    is_admin = False
    if user and user["email"].lower() == "admin@example.com":
        is_admin = True

    return render_template("setting.html", available_styles=ALL_STYLES, is_admin=is_admin)


# ------------------------
# ★ 新規追加：トレンド情報画面（DBから取得）
# ------------------------
@app.route('/trends')
def trends():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    conn = get_db()
    trend_list = conn.execute(
        "SELECT * FROM trends ORDER BY created_at DESC"
    ).fetchall()

    # Googleトレンド情報を取得
    try:
        google_trend_df = get_trends("ファッション")
        google_trend = None
        if not google_trend_df.empty:
            last_row = google_trend_df.tail(1)
            date = last_row.index[0].strftime('%Y-%m-%d')
            value = int(last_row.iloc[0][0])
            google_trend = {"date": date, "value": value}
        else:
            google_trend = None
        # 関連キーワードも取得
        related_df = get_related_queries("ファッション")
        related_keywords = []
        if related_df is not None:
            for _, row in related_df.iterrows():
                related_keywords.append({
                    "keyword": row["query"],
                    "value": row["value"]
                })
        else:
            related_keywords = []
    except Exception as e:
        google_trend = None
        related_keywords = []

    return render_template("trends.html", trends=trend_list, google_trend=google_trend, related_keywords=related_keywords)


# ------------------------
if __name__ == '__main__':
    # 起動時に history テーブルがなければ作成しておく
    try:
        with app.app_context():
            conn = get_db()
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    item_id INTEGER NOT NULL,
                    viewed_at TEXT NOT NULL
                )
                """
            )
            conn.commit()
    except Exception:
        pass

    app.run(host="0.0.0.0", port=5000, debug=True)

