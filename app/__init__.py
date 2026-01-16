import os
import pickle
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, make_response, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import json
from .db import get_db, close_db
from .admin import admin_bp
from .stats import record_event
from firebase_admin import firestore
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from itsdangerous import URLSafeTimedSerializer
import time
from .open_meteo import fetch_nagoya_weather
from .wiki_trends import build_wiki_trend_payload

load_dotenv()

app = Flask(__name__)
app.secret_key = "your_secret_key" # In production, use env var
serializer = URLSafeTimedSerializer(app.secret_key)

app.register_blueprint(admin_bp, url_prefix="/admin")

# Template Filter for datetime formatting
@app.template_filter("fmt_dt")
def fmt_dt(v):
    if v is None:
        return ""
    # Firestore Timestamp might have to_datetime()
    if hasattr(v, "to_datetime"):
        v = v.to_datetime()
    if isinstance(v, datetime):
        return v.strftime("%Y/%m/%d %H:%M")
    return str(v)

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


# ... CACHE logic ...

# Path to cache file in instance directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(os.path.dirname(BASE_DIR), 'instance')
if not os.path.exists(INSTANCE_DIR):
    os.makedirs(INSTANCE_DIR)

# --- Weather Cache & Logic ---
WEATHER_CACHE_FILE = os.path.join(INSTANCE_DIR, "weather_cache.json")
WEATHER_TTL_SEC = 60 * 60  # 1 hour

def load_weather_cache():
    try:
        if os.path.exists(WEATHER_CACHE_FILE):
            with open(WEATHER_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None

def save_weather_cache(payload):
    try:
        with open(WEATHER_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving weather cache: {e}")

def update_weather_cache(force=False):
    # Check TTL
    if not force and os.path.exists(WEATHER_CACHE_FILE):
        try:
            age = time.time() - os.path.getmtime(WEATHER_CACHE_FILE)
            if age < WEATHER_TTL_SEC:
                return
        except:
            pass

    try:
        print("Updating weather data...")
        payload = fetch_nagoya_weather()
        payload["ok"] = True
        save_weather_cache(payload)
        print("Weather data updated successfully.")
    except Exception as e:
        print(f"Error updating weather data: {e}")
        old = load_weather_cache()
        if old:
            old["ok"] = True
            old["stale"] = True
            old["error"] = str(e)
            save_weather_cache(old)
        else:
            save_weather_cache({
                "ok": False,
                "source": "Open-Meteo",
                "location": {"name": "Nagoya"},
                "error": str(e),
            })

# --- Wiki Trends Cache & Logic ---
WIKI_CACHE_FILE = os.path.join(INSTANCE_DIR, "wiki_trend_cache.json")
WIKI_TTL_SEC = 6 * 60 * 60  # 6 hours

# 表示ラベル → Wikipedia記事（英語）
# WIKI_STYLE_MAPPING removed in favor of DB style_wiki_map
# However, we keep it temporarily or rely on DB. 
# The user wants DB only.

def load_wiki_cache():
    try:
        with open(WIKI_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def save_wiki_cache(payload):
    try:
        with open(WIKI_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving wiki cache: {e}")

def update_wiki_cache(force=False):
    # Check TTL
    if not force and os.path.exists(WIKI_CACHE_FILE):
        try:
            age = time.time() - os.path.getmtime(WIKI_CACHE_FILE)
            if age < WIKI_TTL_SEC:
                return
        except:
            pass

    try:
        print("Updating wiki trends data (DB-Driven)...")
        # Need a DB connection. Since this runs in scheduler (thread), 'g' is not available.
        # We can use firestore.client() if app is initialized, or get_db() if context pushed.
        # Assuming app is initialized globally in this file.
        # Ideally: with app.app_context(): db = get_db()
        # But 'app' might be defined later. 'firestore.client()' works if firebase_admin is initialized.
        
        # Use get_db() which handles initialization safely
        db = get_db()

        # 1. Aggregate Tags from Items
        # NOTE: With large datasets, avoid reading all. For now (demonstration/MVP), reading all items is accepted.
        items_ref = db.collection('items').stream()
        tag_counts = {}
        for doc in items_ref:
            # Assuming 'styles' is list or CSV string
            data = doc.to_dict()
            styles = data.get('styles')
            if not styles:
                continue
            
            if isinstance(styles, str):
                tags = [s.strip() for s in styles.split(',')]
            elif isinstance(styles, list):
                tags = [str(s).strip() for s in styles]
            else:
                continue
            
            for t in tags:
                if t:
                    tag_counts[t] = tag_counts.get(t, 0) + 1
        
        # Sort by count desc and take top 20
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        top_tags = [t[0] for t in sorted_tags[:20]]
        print(f"Top tags from DB: {top_tags}")

        # 2. Fetch Mapping
        # Fetch all enabled mappings (assuming map size is small)
        map_docs = db.collection('style_wiki_map').where('is_enabled', '==', True).stream()
        mapping_dict = {} # Label -> Article
        
        # Helper to normalize for matching (simple lowercase check)
        # Firestore keys are case sensitive. Our seed normalized to Japanese label as key.
        # We will load all into memory.
        for d in map_docs:
            data = d.to_dict()
            label = d.id # The Tag Name
            article = data.get('wiki_article')
            lang = data.get('lang', 'en') # Default to English
            
            if label and article:
                mapping_dict[label] = {"article": article, "lang": lang}
        
        # 3. Intersect
        target_mapping = {}
        for tag in top_tags:
            # Try direct match
            if tag in mapping_dict:
                target_mapping[tag] = mapping_dict[tag]
            else:
                # Optional: Try fuzzy or case insensitive? 
                # For now, strict match per design requirement A.
                pass
        
        if not target_mapping:
            print("No matching wiki articles found for top tags. Fallback to full map or empty?")
            # Fallback: If intersection is empty, maybe use top mapped items regardless of popularity?
            # Or just use the top mapped items from the map itself if items are empty?
            # Let's trust the logic: if no items match, trend is empty.
            if not top_tags and mapping_dict:
                 # Cold start fallback: use all mapped
                 target_mapping = mapping_dict
        
        print(f"Target Mapping for API: {target_mapping.keys()}")

        # 4. Build Payload
        payload = build_wiki_trend_payload(target_mapping)
        payload["ok"] = True
        save_wiki_cache(payload)
        print("Wiki trends updated successfully.")

    except Exception as e:
        print(f"Error updating wiki trends: {e}")
        # logic for stale fall back
        old = load_wiki_cache()
        if old:
            old["ok"] = False # Mark as failed/stale
            old["stale"] = True
            old["error"] = str(e)
            save_wiki_cache(old)
            print("Fallback to stale wiki data.")
        else:
            save_wiki_cache({"ok": False, "error": str(e), "source": "Wikimedia Pageviews"})

# Initialize Scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Add weather update to scheduler
scheduler.add_job(func=update_weather_cache, trigger="interval", minutes=60)
# Add wiki update to scheduler
scheduler.add_job(func=update_wiki_cache, trigger="interval", hours=6)

# Run weather initially if needed
if not os.path.exists(WEATHER_CACHE_FILE):
    try:
        update_weather_cache(force=True)
    except:
        pass

# Run wiki initially if needed
if not os.path.exists(WIKI_CACHE_FILE):
    # Run in background via thread or just sync for simple start?
    # Sync for demo so data appears immediately
    try:
        print("Initial Wiki Trends update...")
        update_wiki_cache(force=True)
    except Exception as e:
        print(f"Initial Wiki Update failed: {e}")

def build_weather_rules(weather):
    fired = []
    score_w = {
        "waterproof": 0,
        "outer": 0,
        "windproof": 0,
        "layering": 0,
        "breathable": 0,
    }

    if not weather: 
        return score_w, fired

    p = weather.get("precip_prob_max")
    tmax = weather.get("today_max")
    tmin = weather.get("today_min")
    wind = weather.get("wind_max")

    if p is not None and p >= 40:
        score_w["waterproof"] += 3
        fired.append(f"降水確率が高い（{p}%）→ 防水/撥水を優先")

    if tmax is not None and tmax <= 12:
        score_w["outer"] += 3
        fired.append(f"最高気温が低い（{tmax}℃）→ アウターを優先")

    if wind is not None and wind >= 8:
        score_w["windproof"] += 2
        fired.append(f"風が強い（{wind}m/s）→ 防風を優先")

    if tmax is not None and tmin is not None and (tmax - tmin) >= 8:
        score_w["layering"] += 2
        fired.append(f"寒暖差が大きい（{tmax - tmin}℃）→ 重ね着向きを優先")

    if tmax is not None and tmax >= 25:
        score_w["breathable"] += 2
        fired.append(f"暑い（最高{tmax}℃）→ 通気性を優先")

    return score_w, fired

def score_item_by_weather(item, w_scores):
    # Normalize tags/styles to check against rules
    # styles is csv string or list
    raw_styles = item.get("styles")
    tags = set()
    if raw_styles:
        if isinstance(raw_styles, str):
            tags.update([s.strip().lower() for s in raw_styles.split(',')])
        elif isinstance(raw_styles, list):
            tags.update([str(s).lower() for s in raw_styles])
    
    # Also check 'category' or 'name' if tags are missing, 
    # but for now let's stick to styles tags mapping or loose matching
    # Map Japanese keywords to internal keys if needed, OR just match keys if they exist in tags
    # Let's add basic mapping for demo if tags are Japanese
    # This is a heuristic mapping
    # Ensure all components are strings before concatenation
    name_str = str(item.get("name") or "")
    cat_str = str(item.get("category") or "")
    style_str = str(item.get("styles") or "")
    
    text_to_check = (name_str + " " + cat_str + " " + style_str).lower()
    
    s = 0
    # Simple keyword matching for demo
    if w_scores["waterproof"] > 0 and any(x in text_to_check for x in ["防水", "撥水", "ナイロン", "waterproof", "rain"]):
        s += w_scores["waterproof"]
    if w_scores["outer"] > 0 and any(x in text_to_check for x in ["コート", "ダウン", "ジャケット", "アウター", "outer", "jacket"]):
        s += w_scores["outer"]
    if w_scores["windproof"] > 0 and any(x in text_to_check for x in ["防風", "ウィンド", "wind", "レザー"]):
        s += w_scores["windproof"]
    if w_scores["layering"] > 0 and any(x in text_to_check for x in ["カーディガン", "ベスト", "シャツ", "layer", "cardigan"]):
        s += w_scores["layering"]
    if w_scores["breathable"] > 0 and any(x in text_to_check for x in ["リネン", "麻", "メッシュ", "半袖", "breathable", "cool"]):
        s += w_scores["breathable"]
        
    return s

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
                        item_id = str(e.get("item_id") or "").strip()
                        viewed_at_raw = e.get("viewed_at")
                        
                        if not item_id:
                            continue

                        # Cookie ISO format -> datetime or ServerTimestamp
                        dt = None
                        if viewed_at_raw:
                            try:
                                dt = datetime.fromisoformat(viewed_at_raw)
                            except Exception:
                                dt = None
                                
                        doc_ref = history_ref.document(item_id)
                        batch.set(doc_ref, {
                            "item_id": item_id,
                            "viewed_at": dt if dt else datetime.now()
                        }, merge=True)
                        
                    batch.commit()
                except Exception as e:
                    import traceback
                    traceback.print_exc()
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
    
    # Sort items by popularity_score (descending), then by name
    # Items without popularity_score will be treated as 0
    items.sort(key=lambda x: (x.get('popularity_score') or 0, x.get('name', '')), reverse=True)
    
    # Recent history
    recent_history = []
    saved_items = []
    user_id = session.get("user_id")

    if user_id:
        try:
            # Fetch History
            history_ref = db.collection('users').document(user_id).collection('history')
            # Fetch ALL history to ensure we sort correctly in Python.
            # Firestore sort is unreliable with mixed types (String/Timestamp), and limit() without sort
            # arbitrarily cuts off documents by ID, hiding recently viewed items.
            h_docs = history_ref.stream() 
            
            # Helper to parse time for sorting
            def parse_time(val):
                if not val: return datetime.min
                if hasattr(val, 'to_datetime'): return val.to_datetime().replace(tzinfo=None)
                if isinstance(val, datetime): return val.replace(tzinfo=None)
                try: return datetime.fromisoformat(str(val)).replace(tzinfo=None)
                except: return datetime.min

            # Load into list and sort python-side
            loaded_history = []
            for h in h_docs:
                hd = h.to_dict()
                loaded_history.append(hd)
            
            # Sort desc
            loaded_history.sort(key=lambda x: parse_time(x.get('viewed_at')), reverse=True)

            seen_item_ids = set()
            for hd in loaded_history:
                item_id = str(hd.get('item_id') or "")
                if item_id in all_items_map and item_id not in seen_item_ids:
                    recent_history.append(all_items_map[item_id])
                    seen_item_ids.add(item_id)
                if len(recent_history) >= 10:
                    break
            
            # 2. Fetch Bookmarks
            bookmark_ref = db.collection('users').document(user_id).collection('bookmarks')
            b_docs = bookmark_ref.order_by('saved_at', direction=firestore.Query.DESCENDING).limit(10).stream()
            for b in b_docs:
                item_id = str(b.id)
                if item_id in all_items_map:
                    saved_items.append(all_items_map[item_id])
        except Exception as e:
            print(f"Error fetching history/bookmarks: {e}")
    else:
        # For guests (Cookies)
        try:
            # History from cookie
            anon_h = json.loads(request.cookies.get("anon_history", "[]"))
            seen_h = set()
            for entry in anon_h:
                iid = entry.get("item_id")
                if iid in all_items_map and iid not in seen_h:
                    recent_history.append(all_items_map[iid])
                    seen_h.add(iid)
                if len(recent_history) >= 10: break

            # Bookmarks from cookie
            anon_b = json.loads(request.cookies.get("bookmarks", "[]"))
            for iid in reversed(anon_b): # Show newest first if stored as list
                if iid in all_items_map:
                    saved_items.append(all_items_map[iid])
                if len(saved_items) >= 10: break
        except Exception as e:
            print(f"Error fetching guest data: {e}")

    return render_template("home.html", 
                           current_styles=styles, 
                           items=items, 
                           recent_history=recent_history, 
                           saved_items=saved_items,
                           available_styles=available_styles_list)

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

    # Record View Event
    record_event(item_id, 'views')
    
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
            # Use item_id as document ID to prevent duplicates
            h_ref = db.collection('users').document(session["user_id"]).collection('history').document(str(item_id))
            h_ref.set({
                "item_id": str(item_id),
                "viewed_at": datetime.now()
            }, merge=True)
            print(f"DEBUG: Saved history for {item_id}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error saving history: {e}")

    # Check if bookmarked
    is_bookmarked = False
    if session.get("logged_in") and session.get("user_id"):
        try:
            bookmark_doc = db.collection('users').document(session["user_id"]).collection('bookmarks').document(str(item_id)).get()
            is_bookmarked = bookmark_doc.exists
        except:
            pass
    else:
        # Check from cookie for guests
        try:
            bookmarks = json.loads(request.cookies.get("bookmarks", "[]"))
            is_bookmarked = item_id in bookmarks
        except:
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
        
        resp = make_response(render_template("detail.html", item=item, shops=shops, is_bookmarked=is_bookmarked))
        resp.set_cookie("anon_history", json.dumps(arr, ensure_ascii=False), max_age=30*24*3600, httponly=True)
        return resp

    return render_template("detail.html", item=item, shops=shops, is_bookmarked=is_bookmarked)

@app.route('/items/<item_id>/click')
def item_click(item_id):
    db = get_db()
    item_ref = db.collection('items').document(str(item_id))
    doc = item_ref.get()
    
    if not doc.exists:
        return "Item not found", 404
        
    item = doc.to_dict()
    shop_url = item.get("shop_url")
    
    # Record Click Event
    record_event(item_id, 'clicks')
    
    if not shop_url:
        return redirect(url_for('detail', item_id=item_id))
        
    return redirect(shop_url)

@app.route('/items/<item_id>/save', methods=['POST'])
def item_save(item_id):
    db = get_db()
    is_bookmarked = False
    
    if session.get("logged_in") and session.get("user_id"):
        user_id = session["user_id"]
        bookmark_ref = db.collection('users').document(user_id).collection('bookmarks').document(str(item_id))
        doc = bookmark_ref.get()
        if doc.exists:
            bookmark_ref.delete()
            record_event(item_id, 'saves', amount=-1)
            is_bookmarked = False
        else:
            bookmark_ref.set({"saved_at": datetime.now().isoformat()})
            record_event(item_id, 'saves', amount=1)
            is_bookmarked = True
        return jsonify({"status": "ok", "is_bookmarked": is_bookmarked})
    else:
        # For guests using cookies
        try:
            bookmarks = json.loads(request.cookies.get("bookmarks", "[]"))
        except:
            bookmarks = []
            
        if item_id in bookmarks:
            bookmarks.remove(item_id)
            record_event(item_id, 'saves', amount=-1)
            is_bookmarked = False
        else:
            bookmarks.append(item_id)
            record_event(item_id, 'saves', amount=1)
            is_bookmarked = True
            
        resp = jsonify({"status": "ok", "is_bookmarked": is_bookmarked})
        resp.set_cookie("bookmarks", json.dumps(bookmarks), max_age=30*24*3600, httponly=True)
        return resp

@app.route('/history')
def history():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    db = get_db()
    user_id = session["user_id"]
    rows = []
    try:
        h_ref = db.collection('users').document(user_id).collection('history')
        # Fetch up to 50 recent items
        h_docs = list(h_ref.order_by('viewed_at', direction=firestore.Query.DESCENDING).limit(50).stream())
        
        item_ids = []
        history_map = {} # item_id -> viewed_at

        for h in h_docs:
            hd = h.to_dict()
            item_id = str(hd.get('item_id') or "").strip()
            if not item_id:
               continue
            
            # If duplicates somehow exist in query results (unlikely with docID=itemID but good safety)
            if item_id not in history_map:
                item_ids.append(item_id)
                history_map[item_id] = hd.get('viewed_at')

        if item_ids:
            # Batch fetch items
            # Create references
            # Note: Firestore 'IN' query is limited to 10 or 30. get_all is better for batch retrieval by ID.
            item_refs = [db.collection('items').document(iid) for iid in item_ids]
            item_docs = db.get_all(item_refs)
            
            for doc in item_docs:
                if doc.exists:
                    iid = doc.id
                    i_data = doc.to_dict()
                    rows.append({
                        "id": iid, # Using item_id as row id
                        "item_id": iid,
                        "viewed_at": history_map.get(iid),
                        "name": i_data.get('name'),
                        "price": i_data.get('price'),
                        "image_url": i_data.get('image_url')
                    })
            
            # Sort again by viewed_at because get_all might not preserve order
            rows.sort(key=lambda x: x['viewed_at'] if x['viewed_at'] else datetime.min, reverse=True)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error fetching history: {e}")

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

    db = get_db()
    # Assuming 'trends' collection exists (Legacy DB trends)
    trends_ref = db.collection('trends')
    docs = trends_ref.order_by('created_at', direction=firestore.Query.DESCENDING).stream()
    trend_list = [d.to_dict() for d in docs]

    # Wiki Trends
    wiki = load_wiki_cache() or {"ok": False}
    
    # Enrich Wiki Trends with actual items
    if wiki.get("ok") and wiki.get("trends"):
        # Fetch a pool of items (limit to prevent scale issues, e.g. 300 recent)
        items_ref = db.collection('items').limit(300)
        i_docs = items_ref.stream()
        item_pool = []
        for d in i_docs:
            dic = d.to_dict()
            dic['id'] = d.id
            # Normalize styles for matching
            styles = dic.get('styles')
            tags = set()
            if isinstance(styles, str):
                tags.update([s.strip() for s in styles.split(',')])
            elif isinstance(styles, list):
                tags.update([str(s).strip() for s in styles])
            dic['_tags'] = tags
            item_pool.append(dic)
            
        # Attach items to each trend
        for tr in wiki["trends"]:
            label = tr.get("label")
            # Find items containing this label (exact match on tag)
            matched = [it for it in item_pool if label in it['_tags']]
            # Take top 20
            tr["trend_items"] = matched[:20]

    return render_template("trends.html", trends=trend_list, wiki=wiki)

@app.route('/weather')
def weather():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
        
    db = get_db()
    
    # Weather Logic
    weather_data = load_weather_cache() or {}
    if not weather_data:
        weather_data = {"ok": False, "error": "weather cache missing"}
    
    w_scores, fired_rules = build_weather_rules(weather_data if weather_data.get("ok") else {})
    
    # Fetch Items for Recommendation
    items_ref = db.collection('items')
    i_docs = items_ref.stream()
    all_items = []
    for d in i_docs:
        dic = d.to_dict()
        dic['id'] = d.id
        all_items.append(dic)
        
    # Score items
    weather_recommended = []
    if w_scores and any(v > 0 for v in w_scores.values()):
        scored = []
        for it in all_items:
            # Ensure all components are strings before concatenation
            name_str = str(it.get("name") or "")
            cat_str = str(it.get("category") or "")
            style_str = str(it.get("styles") or "")
            
            text_to_check = (name_str + " " + cat_str + " " + style_str).lower()
            
            s = 0
            if w_scores["waterproof"] > 0 and any(x in text_to_check for x in ["防水", "撥水", "ナイロン", "waterproof", "rain"]):
                s += w_scores["waterproof"]
            if w_scores["outer"] > 0 and any(x in text_to_check for x in ["コート", "ダウン", "ジャケット", "アウター", "outer", "jacket"]):
                s += w_scores["outer"]
            if w_scores["windproof"] > 0 and any(x in text_to_check for x in ["防風", "ウィンド", "wind", "レザー"]):
                s += w_scores["windproof"]
            if w_scores["layering"] > 0 and any(x in text_to_check for x in ["カーディガン", "ベスト", "シャツ", "layer", "cardigan"]):
                s += w_scores["layering"]
            if w_scores["breathable"] > 0 and any(x in text_to_check for x in ["リネン", "麻", "メッシュ", "半袖", "breathable", "cool"]):
                s += w_scores["breathable"]
            
            scored.append((s, it))
        # Sort by score desc
        scored.sort(key=lambda x: x[0], reverse=True)
        # Take top 10 if score > 0
        weather_recommended = [it for score, it in scored if score > 0][:10]

    return render_template("weather.html", 
                           weather=weather_data,
                           weather_rules=fired_rules,
                           weather_recommended=weather_recommended)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
