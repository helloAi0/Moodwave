from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.session_log import SessionLog 
from app.services.iso_engine_v2 import IsoEngineV2
from app.services.socket_manager import sio # Use sio directly as requested

router = APIRouter()

# Global instance of the Iso-Principle engine
engine = IsoEngineV2()

@router.post("/target")
async def set_target(mood: str, current_user: User = Depends(get_current_user)):
    """Allows authenticated users to update the therapy target."""
    engine.set_target(mood)
    return {
        "status": "target_updated", 
        "new_target": mood,
        "user": current_user.email
    }

@router.post("/analyze")
async def analyze(
    raw_emotion: str, 
    db: AsyncSession = Depends(get_db),
    # Optional: current_user: User = Depends(get_current_user) 
    # Add back if you want to ensure only logged-in users can trigger analysis
):
    """
    Receives emotion, updates engine, saves to Postgres, and emits via Socket.io.
    """
    clean_emotion = str(raw_emotion).strip().lower()
    result = engine.update(clean_emotion)

    # 💾 SAVE DATA TO POSTGRES
    # We log the history here so you can view charts later
    new_log = SessionLog(
        emotion=clean_emotion,
        state=result["state"],
        bpm=result["audio"]["bpm"]
    )
    db.add(new_log)
    await db.commit()

    # 🔥 THE SHOUT: Push to the Frontend Dashboard
    # This matches the 'audio_update' listener in your Dashboard/page.tsx
    await sio.emit("audio_update", {
        "bpm": result["audio"]["bpm"],
        "freq": result["audio"]["freq"],
        "state": result["state"]
    })

    return result

@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns the last 20 entries for the Dashboard charts.
    """
    # Fetch logs from Postgres
    query = select(SessionLog).order_by(SessionLog.id.desc()).limit(20)
    db_result = await db.execute(query)
    logs = db_result.scalars().all()
    
    # Return formatted for the frontend (reversed to show chronological order)
    return [{"bpm": s.bpm, "state": s.state, "emotion": s.emotion} for s in reversed(logs)]

@router.get("/status")
async def get_status(current_user: User = Depends(get_current_user)):
    """Returns the current mathematical state of the engine."""
    return {
        "user": current_user.email,
        "state": engine.get_audio_params(),
        "progress": getattr(engine, 'progress', 0) 
    }