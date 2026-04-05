import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import engine, Base
from app.api.routes import auth, sessions
from app.services.socket_manager import socket_app

app = FastAPI(title="MoodWave API")

# --- 1. CORS CONFIGURATION ---
# Allows your Next.js frontend (127.0.0.1:3000) to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. ROUTE REGISTRATION ---
# 🎯 This includes your /register, /login, and the NEW /callback route
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Therapy"])

# --- 3. SOCKET.IO MOUNTING ---
# Mounts the real-time engine to /ws (e.g., http://127.0.0.1:8000/ws)
app.mount("/ws", socket_app)

# --- 4. STARTUP SEQUENCE (Database Migration) ---
@app.on_event("startup")
async def startup():
    """
    Ensures the database is ready and tables are created before the app starts.
    Includes a retry loop for Docker environments.
    """
    print("🚀 MoodWave Startup sequence initiated...")
    retries = 10
    while retries > 0:
        try:
            async with engine.begin() as conn:
                # Creates tables based on your SQLAlchemy models (User, SessionLog, etc.)
                await conn.run_sync(Base.metadata.create_all)
            print("✅ SUCCESS: Database tables created/verified.")
            break
        except Exception as e:
            retries -= 1
            print(f"🔄 Waiting for Postgres... ({retries} retries left)")
            await asyncio.sleep(3)
    
    if retries == 0:
        print("❌ FATAL: Could not connect to database after 10 attempts.")

@app.get("/")
async def root():
    return {"message": "MoodWave API is Live", "version": "2.4.12"}