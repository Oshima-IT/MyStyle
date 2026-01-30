import firebase_admin
from firebase_admin import credentials, firestore
from werkzeug.security import generate_password_hash
from datetime import datetime
import os
import sys

# Ensure we can import from parent if needed (though we only need external libs)
# Initialize Firestore
if not firebase_admin._apps:
    # Look for key in config directory relative to this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    key_path = os.path.join(current_dir, "..", "config", "serviceAccountKey.json")
    
    if os.path.exists(key_path):
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred)
    elif os.path.exists("serviceAccountKey.json"): # Fallback
         cred = credentials.Certificate("serviceAccountKey.json")
         firebase_admin.initialize_app(cred)
    else:
        print(f"Error: serviceAccountKey.json not found at {key_path}")
        sys.exit(1)

db = firestore.client()

def create_admin():
    email = "admin@example.com"
    password = "admin" # Simple default password
    pw_hash = generate_password_hash(password)

    users_ref = db.collection('users')
    query = users_ref.where('email', '==', email).limit(1).stream()

    existing_doc = None
    for d in query:
        existing_doc = d
        break

    if existing_doc:
        print(f"User {email} already exists. Updating password to '{password}'...")
        existing_doc.reference.update({
            "password_hash": pw_hash,
            "updated_at": datetime.now().isoformat()
        })
        print("Update complete.")
    else:
        print(f"Creating user {email} with password '{password}'...")
        users_ref.add({
            "email": email,
            "password_hash": pw_hash,
            "preferred_styles": "",
            "preferred_colors": "",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        })
        print("Creation complete.")

if __name__ == "__main__":
    create_admin()
