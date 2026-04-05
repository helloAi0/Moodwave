from sqlalchemy import Column, Integer, String, DateTime
from app.db.session import Base
from datetime import datetime

class SessionLog(Base):
    __tablename__ = "session_logs"

    id = Column(Integer, primary_key=True, index=True)
    emotion = Column(String)
    state = Column(String)
    bpm = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)