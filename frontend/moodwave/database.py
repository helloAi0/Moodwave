"""
database.py
Local SQLite persistence for mood logs and analytics.
Privacy-first: everything stays on device.
"""
import sqlite3
import datetime

DB_PATH = "moodwave.db"

def init_db(path=DB_PATH):
    """Create database and table if they don't exist. Returns connection."""
    # THE FIX IS HERE: Added check_same_thread=False
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mood_log (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp     TEXT    NOT NULL,
            mood          TEXT    NOT NULL,
            bpm_track     TEXT    NOT NULL,
            tier_progress REAL    NOT NULL DEFAULT 0.0
        )
    """)
    conn.commit()
    return conn

def log_mood(conn, mood, track, progress):
    """Insert a single mood observation into the database."""
    conn.execute(
        "INSERT INTO mood_log (timestamp, mood, bpm_track, tier_progress) "
        "VALUES (?, ?, ?, ?)",
        (datetime.datetime.now().isoformat(), mood, track, round(progress, 3))
    )
    conn.commit()

def get_weekly_summary(conn):
    """
    Returns a dict {mood: count} for the last 7 days.
    Useful for the analytics dashboard.
    """
    rows = conn.execute("""
        SELECT mood, COUNT(*) AS cnt
        FROM mood_log
        WHERE timestamp >= date('now', '-7 days')
        GROUP BY mood
        ORDER BY cnt DESC
    """).fetchall()
    return {row[0]: row[1] for row in rows}

def get_mood_timeline(conn, limit=200):
    """
    Returns the most recent N mood log rows as list of dicts.
    Feed directly into a Kivy chart widget.
    """
    rows = conn.execute("""
        SELECT timestamp, mood, bpm_track, tier_progress
        FROM mood_log
        ORDER BY id DESC
        LIMIT ?
    """, (limit,)).fetchall()
    return [
        {"ts": r[0], "mood": r[1], "track": r[2], "progress": r[3]}
        for r in reversed(rows)
    ]