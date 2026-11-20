import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("dengue.db")

def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            district TEXT NOT NULL,
            area TEXT NOT NULL,
            report_date TEXT NOT NULL,
            affected INTEGER NOT NULL DEFAULT 0,
            deaths INTEGER NOT NULL DEFAULT 0,
            recovered INTEGER NOT NULL DEFAULT 0,
            active_cases INTEGER NOT NULL DEFAULT 0,
            source TEXT DEFAULT '',
            notes TEXT DEFAULT ''
        )
    """)
    count = db.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    if count == 0:
        # Illustrative sample data only; replace with verified official data.
        sample = [
            ("Dhaka", "Dhaka North", "2026-11-18", 420, 5, 360, 55, "Demo data", "Illustrative sample"),
            ("Chattogram", "Panchlaish", "2026-11-18", 185, 2, 150, 33, "Demo data", "Illustrative sample"),
            ("Chattogram", "Kotwali", "2026-11-17", 132, 1, 110, 21, "Demo data", "Illustrative sample"),
            ("Khulna", "Sonadanga", "2026-11-17", 96, 1, 80, 15, "Demo data", "Illustrative sample"),
            ("Rajshahi", "Boalia", "2026-11-16", 72, 0, 60, 12, "Demo data", "Illustrative sample"),
            ("Barishal", "Sadar", "2026-11-16", 88, 1, 70, 17, "Demo data", "Illustrative sample")
        ]
        db.executemany("""
            INSERT INTO reports (district, area, report_date, affected, deaths, recovered,
            active_cases, source, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample)
    db.commit()
    db.close()
