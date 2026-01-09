from datetime import datetime, timedelta
from google.cloud import firestore
from .db import get_db

# Weights
WEIGHTS = {
    "views": 1,
    "clicks": 3,
    "saves": 7
}

def record_event(item_id, event_type, amount=1):
    """
    Increments (or decrements if amount < 0) the count for a specific event type on a specific day.
    Recalculates the popularity score and cleans up old data.
    """
    db = get_db()
    item_ref = db.collection('items').document(str(item_id))
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # field_path = f"stats.{event_type}.{today}"
    
    try:
        # We need to make sure the bucket exists before incrementing negatively might cause issues
        # Actually Increment(-1) works fine in Firestore if the field exists.
        # If it doesn't exist, we might get a negative number from 0 which is also fine for logic.
        item_ref.update({
            f"stats.{event_type}.{today}": firestore.Increment(amount)
        })
    except Exception:
        if amount > 0:
            item_ref.set({
                "stats": {
                    event_type: {
                        today: amount
                    }
                }
            }, merge=True)

    # After recording, recalculate score
    _update_item_score(item_ref)

def _update_item_score(item_ref):
    """
    Reads stats, calculates popularity_score (7-day window), and cleans up old keys.
    """
    doc = item_ref.get()
    if not doc.exists:
        return
    
    item = doc.to_dict()
    stats = item.get("stats", {})
    
    today_dt = datetime.now()
    valid_days = [(today_dt - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    
    total_score = 0
    new_stats = {}
    
    for e_type, weights in WEIGHTS.items():
        type_stats = stats.get(e_type, {})
        new_type_stats = {}
        type_7d_total = 0
        
        for date_str, count in type_stats.items():
            if date_str in valid_days:
                new_type_stats[date_str] = count
                type_7d_total += count
            # Dates older than 10 days are dropped (cleanup)
            elif (today_dt - datetime.strptime(date_str, "%Y-%m-%d")).days < 14:
                # Keep some buffer (14 days) but don't count in score
                new_type_stats[date_str] = count
        
        total_score += type_7d_total * weights
        new_stats[e_type] = new_type_stats

    # Update the document with new score and cleaned stats
    item_ref.update({
        "popularity_score": total_score,
        "stats": new_stats
    })

def get_popularity_summary(item_dict):
    """
    Returns a string like 'Score: 120 (V:100, C:5, S:1)' for display.
    """
    score = item_dict.get("popularity_score", 0)
    stats = item_dict.get("stats", {})
    
    today_dt = datetime.now()
    valid_days = [(today_dt - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    
    totals = {}
    for etype in WEIGHTS.keys():
        t_stats = stats.get(etype, {})
        totals[etype] = sum(count for d, count in t_stats.items() if d in valid_days)
        
    return {
        "score": score,
        "views": totals["views"],
        "clicks": totals["clicks"],
        "saves": totals["saves"]
    }
