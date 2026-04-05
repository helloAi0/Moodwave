from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    target_mood: Mapped[str] = mapped_column(String, default="calm")  # ✅ ADD THIS