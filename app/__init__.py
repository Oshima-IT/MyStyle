import os
import pickle
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, make_response, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import json
from .db import get_db, close_db
from .google_trends import get_trends, get_related_queries
from .admin import admin_bp
from firebase_admin import firestore
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

load_dotenv()

app = Flask(__name__)
app.secret_key = "your_secret_key"

app.register_blueprint(admin_bp, url_prefix="/admin")

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
    """Background task to update Google Trends data."""
    print("Updating trend data...")
    now = datetime.now()
    google_trend = None
    google_trend_error = None
    related_keywords = []

    try:
        google_trend_df = get_trends("ファッション")
        if not google_trend_df.empty:
            last_row = google_trend_df.tail(1)
            date = last_row.index[0].strftime('%Y-%m-%d')
            value = int(last_row.iloc[0][0])
            google_trend = {"date": date, "value": value}
        else:
            google_trend_error = "No data"
        
        related_df = get_related_queries("ファッション")
        if related_df is not None:
            for _, row in related_df.iterrows():
                related_keywords.append({
                    "keyword": row["query"],
                    "value": row["value"]
                })
        
        save_trend_cache({
            "time": now,
            "google_trend": google_trend,
            "related_keywords": related_keywords,
            "google_trend_error": google_trend_error
        })
        print("Trend data updated successfully.")
    except Exception as e:
        print(f"Error updating trend data: {e}")
        # If error, maybe we don't save or save error state
        # For now, let's not overwrite with error if we have old data? 
        # But we need to update time. Let's save error state.
        save_trend_cache({
            "time": now,
            "google_trend": None,
            "related_keywords": [],
            "google_trend_error": str(e)
        })

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
    
    for doc in docs:
        d = doc.to_dict()
        d['id'] = doc.id
        
        # Collect styles for filter UI
        raw_styles = d.get('styles')
        if raw_styles:
            if isinstance(raw_styles, str):
                parts = [s.strip() for s in raw_styles.split(',') if s.strip()]
                existing_styles.update(parts)
            elif isinstance(raw_styles, list):
                existing_styles.update([s for s in raw_styles if s])

        # Simple client-side filter for MVP if styles match any
        if styles:
            item_styles = d.get('styles', "")
            if item_styles:
                # check if any user style is in item styles
                # item_styles could be list or string, handle both for filter check
                if isinstance(item_styles, list):
                    match = any(s in item_styles for s in styles)
                else:
                    match = any(s in item_styles for s in styles)
                
                if match:
                    items.append(d)
                else:
                    # Optional: Include everything if no exact match? 
                    # Original logic was "OR LIKE", so basically filter.
                    pass 
            else:
                # If item has no style, maybe don't show? or show?
                # SQL was: styles LIKE %s%...
                pass
        else:
            items.append(d)
    
    # Filter available styles based on what is actually in DB
    available_styles_list = sorted(list(existing_styles))

    # If filtered result is empty (or user has no styles), logic might differ. 
    # Original: if styles else all.
    if not styles:
        # Re-fetch all because loop above filtered incorrectly if styles was empty
        pass # The loop above appends all if !styles, so it's fine.
    
    # If styles existed but no items found, maybe show all as fallback?
    if styles and not items:
         # Fallback to all items?
         # For now, let's just show what we found. 
         pass


    # Recent history
    recent_history = []
    user_id = session.get("user_id")
    if user_id:
        try:
            history_ref = db.collection('users').document(user_id).collection('history')
            h_docs = history_ref.order_by('viewed_at', direction=firestore.Query.DESCENDING).limit(10).stream()
            
            for h in h_docs:
                hd = h.to_dict()
                item_id = hd.get('item_id')
                # Fetch item details
                # This N+1 query is not ideal but okay for 10 items.
                if item_id:
                    item_doc = items_ref.document(str(item_id)).get()
                    if item_doc.exists:
                        i_data = item_doc.to_dict()
                        recent_history.append({
                            "item_id": item_id,
                            "viewed_at": hd.get('viewed_at'),
                            "name": i_data.get('name'),
                            "price": i_data.get('price'),
                            "image_url": i_data.get('image_url')
                        })
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
        # Limit 50
        h_docs = h_ref.order_by('viewed_at', direction=firestore.Query.DESCENDING).limit(50).stream()
        
        for h in h_docs:
            hd = h.to_dict()
            item_id = hd.get('item_id')
            if item_id:
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

    db = get_db()
    # Assuming 'trends' collection exists
    trends_ref = db.collection('trends')
    docs = trends_ref.order_by('created_at', direction=firestore.Query.DESCENDING).stream()
    trend_list = [d.to_dict() for d in docs]

    # Just load from cache
    google_trend = None
    google_trend_error = None
    related_keywords = []
    
    cache = load_trend_cache()
    if cache:
        google_trend = cache.get("google_trend")
        related_keywords = cache.get("related_keywords", [])
        google_trend_error = cache.get("google_trend_error")
    else:
        # If no cache (e.g. startup failed to fetch), show error or try fetching sync?
        # Let's show "Updating..." or error
        google_trend_error = "Data updating..."

    return render_template("trends.html", trends=trend_list, google_trend=google_trend, related_keywords=related_keywords, google_trend_error=google_trend_error)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
