"""
MoodWave FastAPI application entry point.
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import engine, Base

# ── CRITICAL: import all models so SQLAlchemy registers them with Base.metadata
# Without these imports, create_all() produces no tables.
from app.models.user import User          # noqa: F401
from app.models.session_log import SessionLog  # noqa: F401

from app.api.routes import auth, sessions
from app.services.socket_manager import socket_app


# ── Lifespan (replaces deprecated @app.on_event) ──────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup logic, then yield, then run shutdown logic."""
    # ── Startup ──
    print("🚀 MoodWave starting up …")
    retries = 10
    while retries > 0:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("✅ Database tables created / verified.")
            break
        except Exception as exc:
            retries -= 1
            print(f"⏳ Waiting for Postgres … ({retries} retries left) — {exc}")
            await asyncio.sleep(3)

    if retries == 0:
        print("❌ FATAL: Could not connect to database after 10 attempts.")

    yield  # application runs here

    # ── Shutdown ──
    print("🛑 MoodWave shutting down …")
    await engine.dispose()


# ── App factory ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="MoodWave API",
    version="2.5.0",
    description="Emotion-driven adaptive music therapy backend.",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ─────────────────────────────────────────────────────────────────────
app.include_router(auth.router,     prefix="/api/auth",     tags=["Authentication"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Therapy Session"])

# ── Socket.IO (ASGI sub-app) ───────────────────────────────────────────────────
# Mounted at /ws — clients connect with path="/ws/socket.io"
app.mount("/ws", socket_app)


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "MoodWave API", "version": "2.5.0"}
