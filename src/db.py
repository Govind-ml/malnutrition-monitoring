# src/db.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "malnutrition.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS child_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        child_id TEXT,
        age_months INTEGER,
        sex TEXT,
        weight_kg REAL,
        height_cm REAL,
        district TEXT,
        state TEXT,
        record_date TEXT,
        wasted INTEGER,
        underweight INTEGER,
        stunted INTEGER
    )
    """)
    conn.commit()
    conn.close()
