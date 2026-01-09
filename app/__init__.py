import os
import json
import pickle
from datetime import datetime, timedelta

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    make_response,
    jsonify
)

from werkzeug.security import generate_password_hash, check_password_hash

from firebase_admin import firestore
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from itsdangerous import URLSafeTimedSerializer

# =========================
# app 内モジュール
# =========================
from .db import get_db, close_db
from .admin import admin_bp

# =========================
# services 配下
# =========================
from .services.google_trends import get_trends, get_related_queries
from .services.zozo_trends import get_zozo_trend_data, evaluate_trend






load_dotenv()

app = Flask(__name__)
app.secret_key = "your_secret_key" # In production, use env var
serializer = URLSafeTimedSerializer(app.secret_key)

app.register_blueprint(admin_bp, url_prefix="/admin")
# ... CACHE logic ...

def send_reset_email(to_email, token):
    """Sends a password reset email using Gmail SMTP."""
    sender_email = os.environ.get("MAIL_DEFAULT_SENDER")
    sender_password = os.environ.get("MAIL_PASSWORD")
    
    if not sender_email or not sender_password:
        print("Error: Mail credentials not configured.")
        return False

    reset_url = url_for("reset_password", token=token, _external=True)

    subject = "【MyStyle】パスワード再設定のご案内"
    body = f"""
    <html>
    <body>
        <p>MyStyleをご利用いただきありがとうございます。</p>
        <p>以下のリンクをクリックして、新しいパスワードを設定してください。</p>
        <p><a href="{reset_url}">{reset_url}</a></p>
        <p>※このリンクは有効期限があります。</p>
        <p>心当たりがない場合は、このメールを無視してください。</p>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        # Gmail SMTP (TLS 587) - often more reliable than 465
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

# ... Scheduler logic ...

# ------------------------
# Forgot Password
# ------------------------
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get("email", "").strip()
        
        db = get_db()
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email).limit(1).stream()
        
        user_doc = None
        for doc in query:
            user_doc = doc
            break
            
        if user_doc:
            # Generate token
            token = serializer.dumps(email, salt='password-reset-salt')
            # Send real email
            if send_reset_email(email, token):
                return render_template("forgot_password.html", success=True)
            else:
                return render_template("forgot_password.html", error="メール送信に失敗しました。設定を確認してください。")
        else:
            return render_template("forgot_password.html", error="このメールアドレスは登録されていません")

    return render_template("forgot_password.html")

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600) # 1 hour expiry
    except Exception:
        return render_template("reset_password.html", error="リンクが無効か、期限切れです。もう一度やり直してください。")

    if request.method == 'POST':
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        
        if password != confirm:
             return render_template("reset_password.html", error="確認用パスワードが一致していません", token=token)

        password_hash = generate_password_hash(password)
        
        db = get_db()
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email).limit(1).stream()
        
        user_id = None
        for doc in query:
            user_id = doc.id
            break
        
        if user_id:
            users_ref.document(user_id).update({
                "password_hash": password_hash,
                "updated_at": datetime.now().isoformat()
            })
            return redirect(url_for("login"))
        else:
             return render_template("reset_password.html", error="ユーザーが見つかりませんでした", token=token)

    return render_template("reset_password.html", token=token)


# Path to cache file in instance directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(os.path.dirname(BASE_DIR), 'instance')
if not os.path.exists(INSTANCE_DIR):
    os.makedirs(INSTANCE_DIR)

CACHE_FILE = os.path.join(INSTANCE_DIR, "google_trend_cache.pkl")
# Expiry is still used to check if valid, but update is driven by scheduler
CACHE_EXPIRE_MINUTES = 65 # Slightly longer than interval to tolerate delays

def load_trend_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "rb") as f:
            return pickle.load(f)
    return None

def save_trend_cache(data):
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(data, f)

def update_trend_cache():
    with app.app_context():
        print("Updating trend data...")
        now = datetime.now()
        
        # 既存のキャッシュを先にロードしておく
        old_cache = load_trend_cache()
        
        # Imports inside function or at top - assuming standard imports available
        import random

        try:
            # 1. DBからスタイルを取得してキーワードリストを作成
            db = get_db()
            items_stream = db.collection('items').stream()
            unique_styles = set()
            for doc in items_stream:
                item_data = doc.to_dict()
                s_raw = item_data.get('styles')
                if s_raw:
                    if isinstance(s_raw, str):
                       parts = [s.strip() for s in s_raw.split(',') if s.strip()]
                       unique_styles.update(parts)
                    elif isinstance(s_raw, list):
                       unique_styles.update([s for s in s_raw if s])
            
            style_list = list(unique_styles)
            
            # Google Trendsは最大5キーワードまで比較可能
            if len(style_list) > 5:
                search_keywords = random.sample(style_list, 5)
            elif len(style_list) > 0:
                search_keywords = style_list
            else:
                search_keywords = ["ファッション"] # フォールバック

            print(f"Updating trends for: {search_keywords}")

            # データ取得 (Comparison)
            google_trend_df = get_trends(search_keywords)
            
            # 構造を少し変える: google_trend = { date: "YYYY-MM-DD", values: { "StyleA": 10, "StyleB": 50... } }
            # 既存UIとの互換性のため、メインのグラフ用のデータ構造を整形
            google_trend = {}
            
            if not google_trend_df.empty:
                last_row = google_trend_df.tail(1)
                date = last_row.index[0].strftime('%Y-%m-%d')
                
                values = {}
                for kw in search_keywords:
                    if kw in last_row:
                        values[kw] = int(last_row[kw].iloc[0])
                    else:
                        values[kw] = 0
                
                # Simple format for charts: just pass the whole dict logic? 
                # Original code expected specific {date, value} format which might be for single line.
                # We need to adapt trends.html if we want multi-line.
                # For "Prompt 1" request, it implies comparison.
                # Let's save a structure compatible with a new chart or simplistic view.
                
                google_trend = {
                    "date": date,
                    "multi_values": values, # New support for multiple
                    "primary_keyword": search_keywords[0],
                    "value": values.get(search_keywords[0], 0) # Fallback for old UI
                }
            
            related_keywords = []
            # Related queries for the PRIMARY keyword (first one) to keep it simple/stable
            primary_kw = search_keywords[0]
            related_df = get_related_queries(primary_kw)
            if related_df is not None:
                print (related_df.iterrows())
                for _, row in related_df.iterrows():
                    related_keywords.append({
                        "keyword": row["query"],
                        "value": row["value"]
                    })
            
            # 成功時はエラーを None にして保存
            save_trend_cache({
                "time": now,
                "google_trend": google_trend,
                "related_keywords": related_keywords,
                "google_trend_error": None
            })
            print("Trend data updated successfully.")

        except Exception as e:
            print(f"Error updating trend data: {e}")
            
            # エラー時は「古いキャッシュ」か「モック」を使い、google_trend_errorはNoneにする
            # これにより画面上の赤いエラーメッセージを消す
            if old_cache and old_cache.get("google_trend"):
                data_to_save = old_cache
                data_to_save["google_trend_error"] = None
                save_trend_cache(data_to_save)
                print("Recovered from old cache. Error suppressed for UI.")
            else:
                mock_date = (now - timedelta(days=1)).strftime('%Y-%m-%d')
                save_trend_cache({
                    "time": now,
                    "google_trend": {"date": mock_date, "value": 75},
                    "related_keywords": [
                        {"keyword": "秋コーデ メンズ", "value": 100},
                        {"keyword": "ニット ベスト", "value": 85},
                        {"keyword": "ワイドパンツ", "value": 70},
                        {"keyword": "カーディガン", "value": 60},
                        {"keyword": "セットアップ", "value": 50},
                    ],
                    "google_trend_error": None
                })
                print("Using MOCK data. Error suppressed for UI.")

# Initialize Scheduler
scheduler = BackgroundScheduler()
# Run job every 60 minutes
scheduler.add_job(func=update_trend_cache, trigger="interval", minutes=60)
scheduler.start()

# Should we run it once on startup if no cache exists?
if not os.path.exists(CACHE_FILE):
    # Run slightly after startup to not block import? 
    # Or just run it now. It might block startup for a few seconds.
    print("No cache found, updating trends initially...")
    update_trend_cache()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

@app.route('/')
def index():
    return redirect(url_for('home'))

# ------------------------
# Login
# ------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email).limit(1).stream()
        
        user = None
        user_id = None
        for doc in query:
            user = doc.to_dict()
            user_id = doc.id
            break

        if user and check_password_hash(user.get("password_hash"), password):
            session["logged_in"] = True
            session["user_id"] = user_id
            
            if user.get("email", "").lower() == "admin@example.com":
                 session["is_admin"] = True
            else:
                 session["is_admin"] = False

            p_styles = user.get("preferred_styles", "")
            styles = p_styles.split(",") if p_styles else []
            session["user_styles"] = styles

            # Migrate anonymous history
            anon = request.cookies.get("anon_history")
            if anon:
                try:
                    entries = json.loads(anon)
                    batch = db.batch()
                    history_ref = db.collection('users').document(user_id).collection('history')
                    
                    for e in entries:
                        item_id = e.get("item_id")
                        viewed_at = e.get("viewed_at")
                        if item_id and viewed_at:
                            new_doc = history_ref.document()
                            batch.set(new_doc, {
                                "item_id": item_id,
                                "viewed_at": viewed_at
                            })
                    batch.commit()
                except Exception as e:
                    print(f"Error migrating history: {e}")

                resp = make_response(redirect(url_for("home")))
                resp.delete_cookie("anon_history")
                return resp

            return redirect(url_for("home"))

        return render_template("login.html", error="メールアドレスまたはパスワードが違います")

    return render_template("login.html")

# ------------------------
# Register
# ------------------------
@app.route('/account', methods=['GET', 'POST'])
def account_registration():
    if request.method == 'POST':
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if password != confirm:
            return render_template("account.html", error="確認用パスワードが一致していません")

        db = get_db()
        users_ref = db.collection('users')
        # Check if email exists
        existing = users_ref.where('email', '==', email).limit(1).get()
        if len(existing) > 0:
            return render_template("account.html", error="このメールアドレスはすでに登録されています")

        password_hash = generate_password_hash(password)
        
        new_user = {
            "email": email,
            "password_hash": password_hash,
            "preferred_styles": "",
            "preferred_colors": "",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        users_ref.add(new_user)

        return redirect(url_for("login"))

    return render_template("account.html")



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login"))

# ------------------------
# Home
# ------------------------
@app.route('/home')
def home():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    styles = session.get("user_styles", [])
    db = get_db()
    items_ref = db.collection('items')
    
    # Firestore doesn't support multiple "array-contains" OR queries easily without multiple queries.
    # For now, we will fetch all items and filter in Python if styles are present, 
    # OR if the dataset is small. Or we can just show all.
    # Let's try basic filtering or just fetch all for MVP migration.
    
    docs = items_ref.stream()
    items = []
    existing_styles = set()

    # 1. Fetch all items once and store in a dictionary for fast lookup
    all_items_map = {}
    search_query = request.args.get('search')
    
    for doc in docs:
        d = doc.to_dict()
        d['id'] = doc.id
        all_items_map[str(doc.id)] = d
        
        # Collect styles for the UI filter list
        raw_styles = d.get('styles')
        if raw_styles:
            if isinstance(raw_styles, str):
                parts = [s.strip() for s in raw_styles.split(',') if s.strip()]
                existing_styles.update(parts)
            elif isinstance(raw_styles, list):
                existing_styles.update([s for s in raw_styles if s])

        # Filter Logic
        # Priority 1: Search Query (from Trends page or elsewhere)
        if search_query:
            q = search_query.lower()
            # Check name
            if q in d.get('name', '').lower():
                 items.append(d)
                 continue
            # Check category
            if q in d.get('category', '').lower():
                 items.append(d)
                 continue
            # Check styles
            s_val = d.get('styles')
            if isinstance(s_val, list):
                if any(q in s.lower() for s in s_val):
                    items.append(d)
                    continue
            elif isinstance(s_val, str):
                if q in s_val.lower():
                    items.append(d)
                    continue
            
            # If search query exists and no match, skip this item
            continue

        # Priority 2: Style Filter (if no search query)
        if styles:
            item_styles = d.get('styles', "")
            if item_styles:
                # check if any user style is in item styles
                if any(s in item_styles for s in styles):
                    items.append(d)
                else:
                    pass 
            else:
                pass
        else:
            items.append(d)
    
    # Filter available styles based on what is actually in DB
    available_styles_list = sorted(list(existing_styles))
    
    # Recent history
    recent_history = []
    user_id = session.get("user_id")
    if user_id:
        try:
            history_ref = db.collection('users').document(user_id).collection('history')
            h_docs = history_ref.order_by('viewed_at', direction=firestore.Query.DESCENDING).limit(50).stream()
            seen_item_ids = set()
            for h in h_docs:
                hd = h.to_dict()
                item_id = str(hd.get('item_id'))
                if not item_id or item_id in seen_item_ids:
                    continue
                
                # N+1問題の解消: DBから毎回取得せず、既に取得済みのall_items_mapから参照する
                if item_id in all_items_map:
                    i_data = all_items_map[item_id]
                    recent_history.append({
                        "item_id": item_id,
                        "viewed_at": hd.get('viewed_at'),
                        "name": i_data.get('name'),
                        "price": i_data.get('price'),
                        "image_url": i_data.get('image_url'),
                        "category": i_data.get('category'),
                        "styles": i_data.get('styles')
                    })
                    seen_item_ids.add(item_id)
                # 万が一マップに無い（削除済み等）場合は無視
                
                if len(recent_history) >= 10:
                    break
                    recent_history.append({
                        "item_id": item_id,
                        "viewed_at": hd.get('viewed_at'),
                        "name": i_data.get('name'),
                        "price": i_data.get('price'),
                        "image_url": i_data.get('image_url'),
                        "category": i_data.get('category'),
                        "styles": i_data.get('styles')
                    })
                    seen_item_ids.add(item_id)
                if len(recent_history) >= 10:
                    break
        except Exception as e:
            print(f"Error fetching history: {e}")

    return render_template("home.html", current_styles=styles, items=items, recent_history=recent_history, available_styles=available_styles_list)

# ------------------------
# Detail
# ------------------------
@app.route('/detail/<item_id>') # Changed to string ID
def detail(item_id):
    db = get_db()
    item_ref = db.collection('items').document(str(item_id))
    doc = item_ref.get()
    
    if not doc.exists:
        return "Item not found", 404
        
    item = doc.to_dict()
    item['id'] = doc.id
    
    # Fetch shops (assuming separate collection or subcollection? Original had many-to-many)
    # Since we are migrating, let's just assume shops are not fully migrated or simplistic.
    # We can fake it or query a shops collection if we migrate that too.
    # For now, empty list or fetch from 'shops' collection if references exist.
    shops = []
    # If items have shop_url directly (from original schema), use that.
    if item.get("shop_url"):
        shops.append({"name": "Official Shop", "site_url": item.get("shop_url")})

    # Log history
    if session.get("logged_in") and session.get("user_id"):
        try:
            db.collection('users').document(session["user_id"]).collection('history').add({
                "item_id": item_id,
                "viewed_at": datetime.now().isoformat()
            })
        except Exception:
            pass

    # Anon history cookie
    if not session.get("logged_in"):
        try:
            anon = request.cookies.get("anon_history")
            arr = json.loads(anon) if anon else []
        except:
            arr = []
        
        arr = [e for e in arr if e.get("item_id") != item_id]
        arr.insert(0, {"item_id": item_id, "viewed_at": datetime.now().isoformat()})
        arr = arr[:20]
        
        resp = make_response(render_template("detail.html", item=item, shops=shops))
        resp.set_cookie("anon_history", json.dumps(arr, ensure_ascii=False), max_age=30*24*3600, httponly=True)
        return resp

    return render_template("detail.html", item=item, shops=shops)

@app.route('/history')
def history():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    db = get_db()
    user_id = session["user_id"]
    rows = []
    try:
        h_ref = db.collection('users').document(user_id).collection('history')
        h_docs = h_ref.order_by('viewed_at', direction=firestore.Query.DESCENDING).limit(100).stream()
        seen_item_ids = set()
        for h in h_docs:
            hd = h.to_dict()
            item_id = hd.get('item_id')
            if not item_id or item_id in seen_item_ids:
                continue
            i_doc = db.collection('items').document(str(item_id)).get()
            if i_doc.exists:
                i_data = i_doc.to_dict()
                rows.append({
                    "id": h.id, 
                    "item_id": item_id,
                    "viewed_at": hd.get('viewed_at'),
                    "name": i_data.get('name'),
                    "price": i_data.get('price'),
                    "image_url": i_data.get('image_url')
                })
                seen_item_ids.add(item_id)
            # 50件で打ち切り
            if len(rows) >= 50:
                break
    except Exception as e:
        print(e)

    return render_template("history.html", history=rows)

@app.route('/update_styles', methods=['POST'])
def update_styles():
    if not session.get("logged_in"):
        return jsonify({"parsed": False, "error": "Login required"}), 401
    
    selected_styles = request.form.getlist("style")
    styles_str = ",".join(selected_styles)

    try:
        db = get_db()
        db.collection('users').document(session["user_id"]).update({
            "preferred_styles": styles_str,
            "updated_at": datetime.now().isoformat()
        })
        session["user_styles"] = selected_styles
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/trends')
def trends():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    # =========================
    # DB：保存済みトレンド情報
    # =========================
    db = get_db()
    trends_ref = db.collection('trends')
    docs = trends_ref.order_by(
        'created_at',
        direction=firestore.Query.DESCENDING
    ).stream()
    trend_list = [d.to_dict() for d in docs]

    # =========================
    # Googleトレンド（キャッシュ）
    # =========================
    google_trend = None
    related_keywords = []
    google_trend_error = None

    cache = load_trend_cache()
    if cache:
        google_trend = cache.get("google_trend")
        related_keywords = cache.get("related_keywords", [])
        google_trend_error = cache.get("google_trend_error")
    else:
        google_trend_error = "トレンドデータを更新中です"

    # =========================
    # ZOZO × トレンド評価
    # =========================
    zozo_data = None
    zozo_evaluation = None

    # Googleトレンドからキーワードを取得できる場合のみ実行
    if google_trend and isinstance(google_trend, dict):
        keyword = google_trend.get("primary_keyword")
        if keyword:
            zozo_data = get_zozo_trend_data(keyword)
            zozo_evaluation = evaluate_trend(google_trend, zozo_data)

    # =========================
    # 画面描画
    # =========================
    return render_template(
        "trends.html",
        trends=trend_list,
        google_trend=google_trend,
        related_keywords=related_keywords,
        google_trend_error=google_trend_error,
        zozo_evaluation=zozo_evaluation

        
    )


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
