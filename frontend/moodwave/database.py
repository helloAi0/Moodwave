"""
database.py — Local SQLite database for session history.
"""
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict


def init_db():
    """Initialize local SQLite database."""
    conn = sqlite3.connect("moodwave.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS mood_log (
            id INTEGER PRIMARY KEY,
            timestamp DATETIME,
            emotion TEXT,
            track TEXT,
            progress REAL
        )
    """
    )
    conn.commit()
    return conn


def log_mood(db, emotion: str, track: str, progress: float) -> None:
    """Log a mood detection event."""
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO mood_log (timestamp, emotion, track, progress)
        VALUES (?, ?, ?, ?)
    """,
        (datetime.now(), emotion, track, progress),
    )
    db.commit()


def get_weekly_summary(db) -> dict:
    """
    Return emotion frequency for the past 7 days.
    Used by frontend to render weekly chart.
    """
    cursor = db.cursor()
    week_ago = datetime.now() - timedelta(days=7)

    cursor.execute(
        """
        SELECT emotion, COUNT(*) as count
        FROM mood_log
        WHERE timestamp > ?
        GROUP BY emotion
    """,
        (week_ago,),
    )

    result = defaultdict(int)
    for emotion, count in cursor.fetchall():
        result[emotion] = count

    # Ensure all emotions are present
    for emotion in ["angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"]:
        if emotion not in result:
            result[emotion] = 0

    return dict(result)