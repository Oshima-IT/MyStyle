import sys
import os

# Append project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, update_wiki_cache

try:
    with app.app_context():
        print("Forcing wiki trend update (DB-Driven)...")
        update_wiki_cache(force=True)
        print("Done.")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
