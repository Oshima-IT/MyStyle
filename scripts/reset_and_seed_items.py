import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import os

# Initialize Firestore
if not firebase_admin._apps:
    # Look for key in config directory relative to this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    key_path = os.path.join(current_dir, "..", "config", "serviceAccountKey.json")
    
    if os.path.exists(key_path):
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred)
    elif os.path.exists("serviceAccountKey.json"): # Fallback for old way
         cred = credentials.Certificate("serviceAccountKey.json")
         firebase_admin.initialize_app(cred)
    else:
        print(f"Error: serviceAccountKey.json not found at {key_path}")
        exit(1)

db = firestore.client()

def delete_collection(coll_ref, batch_size):
    docs = coll_ref.limit(batch_size).stream()
    deleted = 0

    for doc in docs:
        print(f'Deleting doc {doc.id} => {doc.to_dict().get("name")}')
        doc.reference.delete()
        deleted = deleted + 1

    if deleted >= batch_size:
        return delete_collection(coll_ref, batch_size)

import re

# ... existing code ...

def parse_init_db():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sql_path = os.path.join(current_dir, "init_db.sql")
    
    with open(sql_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove SQL comments (-- ...)
    content = re.sub(r"--.*", "", content)

    # Regex to capture values inside VALUES (...), (...), ...
    # This is a simplified regex assuming standard SQL format in init_db.sql
    # It looks for patterns like ('name', 'category', price, 'styles', 'colors' or NULL, is_trend, 'url', 'url', ...)
    
    # First, find the INSERT INTO items ... VALUES part
    match = re.search(r"INSERT INTO items\s+\([^)]+\)\s+VALUES\s+(.*);", content, re.DOTALL | re.IGNORECASE)
    if not match:
        print("Could not find INSERT statement in init_db.sql")
        return []

    values_str = match.group(1)
    
    # Split by ),\n or ), to get individual rows
    # This might be fragile if strings contain ');' but for this valid SQL file it should work
    # A robust parser would be better but regex is sufficient for this controlled file
    raw_rows = re.split(r"\),\s*\(", values_str)
    
    items = []
    
    for row in raw_rows:
        # Clean up leading/trailing parens if they exist (only for first and last items)
        row = row.strip().lstrip('(').rstrip(')')
        
        # Split by comma, respecting quotes is hard with simple split. 
        # But our data is simple. Let's use ast.literal_eval for safety if possible or simple CSV parsing
        # The SQL string literal uses single quotes.
        
        # Simple manual parse state machine or using a library would be best. 
        # Given the format: key='value', num, ... 
        
        # Let's try a regex to find all values
        # This matches: 'string' OR number OR NULL
        vals = []
        parts = re.split(r",\s*(?=(?:[^']*'[^']*')*[^']*$)", row)
        
        cleaned_parts = []
        for p in parts:
            p = p.strip()
            if p.upper() == "NULL":
                cleaned_parts.append(None)
            elif p.startswith("'") and p.endswith("'"):
                cleaned_parts.append(p[1:-1]) # Strip quotes
            else:
                try:
                    cleaned_parts.append(int(p))
                except:
                    try:
                        cleaned_parts.append(float(p))
                    except:
                         cleaned_parts.append(p) # Fallback
        
        # Map to dict
        # Columns: name, category, price, styles, colors, is_trend, image_url, shop_url, created_at
        if len(cleaned_parts) >= 8:
            item = {
                'name': cleaned_parts[0],
                'category': cleaned_parts[1],
                'price': cleaned_parts[2],
                'styles': cleaned_parts[3],
                'colors': cleaned_parts[4],
                'is_trend': cleaned_parts[5],
                'image_url': cleaned_parts[6],
                'shop_url': cleaned_parts[7],
                # created_at is usually current_timestamp in SQL, we generate valid datetime here
                'created_at': datetime.now() 
            }
            items.append(item)
            
    return items

def seed_items():
    # 1. Delete existing items
    print("Deleting existing items...")
    items_ref = db.collection('items')
    delete_collection(items_ref, 10)
    print("Existing items deleted.")

    # 2. Prepare new data
    items_data = parse_init_db()

    print(f"Seeding {len(items_data)} items from init_db.sql...")
    
    batch = db.batch()
    count = 0
    total_count = 0
    
    for item in items_data:
        doc_ref = items_ref.document()
        # Ensure price is int
        if item.get("price"):
            try:
                item["price"] = int(item["price"])
            except:
                pass
                
        batch.set(doc_ref, item)
        count += 1
        
        # Commit every 400 items
        if count >= 400:
            batch.commit()
            total_count += count
            count = 0
            batch = db.batch()
            
    if count > 0:
        batch.commit()
        total_count += count
        
    print(f"Successfully seeded {total_count} items.")

if __name__ == "__main__":
    seed_items()

