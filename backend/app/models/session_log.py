"""
session_log.py — Log entry for each emotion detection event.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.db.session import Base


class SessionLog(Base):
    """Session log entry (one per emotion detection)."""

    __tablename__ = "session_logs"

    id = Column(Integer, primary_key=True, index=True)
    emotion = Column(String)
    state = Column(String)
    bpm = Column(Integer)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())