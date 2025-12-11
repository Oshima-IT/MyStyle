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
    conn.close()
    print("DB initialized with schema.")

if __name__ == "__main__":
    init_db()
