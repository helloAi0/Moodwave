import socketio

# ASGI compatible Socket.IO server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio)

@sio.event
async def connect(sid, environ):
    print(f"🚀 Client Connected: {sid}")
    await sio.emit('status', {'msg': 'Connected to MoodWave Engine'}, to=sid)

@sio.event
async def set_therapy_target(sid, data):
    target = data.get("target", "calm")
    print(f"🎯 Target updated to {target} for session {sid}")

async def broadcast_mood(data: dict):
    """
    Pushes live data to the UI.
    'data' should contain the engine results (BPM, Mood, etc.)
    """
    # 1. Send the raw analysis (for charts/labels)
    await sio.emit('mood_update', data)
    
    # 2. Send the specific audio triggers (for Tone.js)
    # We use 'audio_update' so the frontend knows to change the sound
    if "audio" in data:
        await sio.emit('audio_update', data["audio"])
    else:
        # Fallback if the engine returns the whole dict
        await sio.emit('audio_update', data)