"""
Central configuration — reads from environment variables (or .env via python-dotenv).
All secrets live here; never hardcode them elsewhere.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:moodwave_pass@db:5432/moodwave_db"

    # ── JWT / Security ────────────────────────────────────────────────────
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_USE_openssl_rand_hex_32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # ── Spotify OAuth (optional - currently not used, but accept if in .env) ─────────────────────────────────
    SPOTIFY_CLIENT_ID: str = ""
    SPOTIFY_CLIENT_SECRET: str = ""
    SPOTIFY_REDIRECT_URI: str = "http://127.0.0.1:8000/api/auth/callback"
    FRONTEND_DASHBOARD: str = "http://localhost:3000/dashboard"
    FRONTEND_BASE: str = "http://localhost:3000"

    # ── CORS ───────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "http://localhost:8000",
    ]

    # ── Redis ─────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # ← THIS IS KEY: Ignore extra env variables


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()