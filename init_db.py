import sqlite3
import os

DB_FILENAME = "fassion.db"
SCHEMA_FILENAME = "schema.sql"

def init_db():
    if os.path.exists(DB_FILENAME):
        os.remove(DB_FILENAME)
        print(f"Existing {DB_FILENAME} removed.")

    conn = sqlite3.connect(DB_FILENAME)
    with open(SCHEMA_FILENAME, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    
    if os.path.exists("init_db.sql"):
        with open("init_db.sql", "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        print("DB seeded with init_db.sql.")
    
    conn.close()
    print("DB initialized with schema.")

if __name__ == "__main__":
    init_db()
