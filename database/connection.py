from pathlib import Path
import sqlite3

DB_PATH = "database/library.db"  # project root /library.db

def get_db_connection(db_name=None):
    path = str(db_name or DB_PATH)
    print("Opening DB:", db_name or DB_PATH)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn
