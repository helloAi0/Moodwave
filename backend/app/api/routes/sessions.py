"""
Session / therapy routes:
  POST /api/sessions/analyze  — receive emotion, update engine, emit via socket
  POST /api/sessions/target   — change therapy target mood
  GET  /api/sessions/stats    — last 20 BPM/state entries
  GET  /api/sessions/status   — current engine state
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.session_log import SessionLog
from app.services.iso_engine_v2 import IsoEngineV2
from app.services.socket_manager import sio

router = APIRouter()

# One global engine instance is fine for a single-process deployment.
# For multi-worker setups, move this to Redis or a shared cache.
_engine = IsoEngineV2()


# ── Request schemas ────────────────────────────────────────────────────────────
class EmotionPayload(BaseModel):
    emotion: str


class TargetPayload(BaseModel):
    mood: str


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/target")
async def set_target(
    payload: TargetPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Allow an authenticated user to change the therapy target mood."""
    valid_targets = {"calm", "focus", "happy", "sleep", "energy"}
    if payload.mood not in valid_targets:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"mood must be one of {valid_targets}",
        )
    _engine.set_target(payload.mood)

    # Persist the preference on the user record
    current_user.target_mood = payload.mood
    await db.commit()

    return {"status": "target_updated", "new_target": payload.mood}


@router.post("/analyze")
async def analyze(
    payload: EmotionPayload,
    db: AsyncSession = Depends(get_db),
    # Un-comment the line below to require JWT on this route too:
    # current_user: User = Depends(get_current_user),
):
    """
    Receives a dominant emotion string from the sensor script,
    runs it through the Iso engine, persists to Postgres, and
    emits live data to all connected dashboard clients.
    """
    VALID_EMOTIONS = {"angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"}
    clean_emotion = payload.emotion.strip().lower()

    if clean_emotion not in VALID_EMOTIONS:
        # Gracefully fall back to neutral instead of crashing
        clean_emotion = "neutral"

    result = _engine.update(clean_emotion)

    # Persist session log
    log = SessionLog(
        emotion=clean_emotion,
        state=result["state"],
        bpm=result["audio"]["bpm"],
    )
    db.add(log)
    await db.commit()

    # Broadcast to all dashboard WebSocket clients
    await sio.emit(
        "audio_update",
        {
            "bpm": result["audio"]["bpm"],
            "freq": result["audio"]["freq"],
            "state": result["state"],
            "progress": result["progress"],
        },
    )

    return result


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the last 20 session-log entries (chronological order) for charts."""
    query = select(SessionLog).order_by(SessionLog.id.desc()).limit(20)
    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        {
            "bpm": s.bpm,
            "state": s.state,
            "emotion": s.emotion,
            "timestamp": s.timestamp.isoformat() if s.timestamp else None,
        }
        for s in reversed(logs)
    ]


@router.get("/status")
async def get_status(current_user: User = Depends(get_current_user)):
    """Return the current mathematical state of the Iso engine."""
    return {
        "user": current_user.email,
        "target_mood": current_user.target_mood,
        "audio": _engine.get_audio_params(),
        "progress": round(_engine.transition_progress, 2),
    }
