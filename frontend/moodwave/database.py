"""
database.py — Thread-safe SQLite database for session history.
"""
import sqlite3
import threading
from datetime import datetime, timedelta
from collections import defaultdict


class ThreadSafeDatabase:
    """Thread-safe SQLite wrapper."""

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
        """Initialize database schema with migration."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='mood_log';"
        )
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            # Check if emotion column exists
            cursor.execute("PRAGMA table_info(mood_log);")
            columns = [row[1] for row in cursor.fetchall()]
            if "emotion" not in columns:
                # Migrate: add missing column
                print("[DB] Migrating: adding emotion column...")
                cursor.execute("ALTER TABLE mood_log ADD COLUMN emotion TEXT DEFAULT 'neutral';")
                conn.commit()
        else:
            # Create fresh table
            print("[DB] Creating new mood_log table...")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS mood_log (
                    id INTEGER PRIMARY KEY,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    emotion TEXT NOT NULL DEFAULT 'neutral',
                    track TEXT DEFAULT 'unknown',
                    progress REAL DEFAULT 0.0
                )
            """
            )
            conn.commit()

    def log_mood(self, emotion: str, track: str, progress: float) -> None:
        """Log a mood detection event (thread-safe)."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO mood_log (timestamp, emotion, track, progress)
                VALUES (?, ?, ?, ?)
            """,
                (datetime.now(), emotion or "neutral", track or "unknown", progress or 0.0),
            )
            conn.commit()
        except Exception as e:
            print(f"[DB] Error logging mood: {e}")

    def get_weekly_summary(self) -> dict:
        """Return emotion frequency for the past 7 days."""
        try:
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
        except Exception as e:
            print(f"[DB] Error getting summary: {e}")
            return {
                "angry": 0, "disgust": 0, "fear": 0, "happy": 0,
                "neutral": 0, "sad": 0, "surprise": 0
            }

    def close(self):
        """Close database connection."""
        if hasattr(self.local, "conn") and self.local.conn:
            self.local.conn.close()