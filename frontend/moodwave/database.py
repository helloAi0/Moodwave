"""
database.py — Thread-safe SQLite database for session history.
"""
import sqlite3
import threading
from datetime import datetime, timedelta
from collections import defaultdict


class ThreadSafeDatabase:
    """
    Thread-safe SQLite wrapper.
    Each thread gets its own connection to avoid conflicts.
    """

    def __init__(self, db_path="moodwave.db"):
        self.db_path = db_path
        self.local = threading.local()
        self._init_schema()

    def _get_connection(self):
        """Get thread-local database connection."""
        if not hasattr(self.local, "conn") or self.local.conn is None:
            self.local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.local.conn.isolation_level = None  # autocommit mode
        return self.local.conn

    def _init_schema(self):
        """Initialize database schema."""
        conn = self._get_connection()
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

    def log_mood(self, emotion: str, track: str, progress: float) -> None:
        """Log a mood detection event (thread-safe)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO mood_log (timestamp, emotion, track, progress)
            VALUES (?, ?, ?, ?)
        """,
            (datetime.now(), emotion, track, progress),
        )
        conn.commit()

    def get_weekly_summary(self) -> dict:
        """
        Return emotion frequency for the past 7 days.
        Used by frontend to render weekly chart.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
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

    def close(self):
        """Close database connection."""
        if hasattr(self.local, "conn") and self.local.conn:
            self.local.conn.close()