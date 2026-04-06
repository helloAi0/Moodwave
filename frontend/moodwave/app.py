"""
app.py — MoodWave Desktop Frontend (Iriun / any webcam)
"""
import threading
import time
import cv2
import numpy as np
import requests
from flask import Flask, render_template, Response, jsonify
from flask_socketio import SocketIO

from emotion_engine import EmotionEngine
from music_player import MusicPlayer
from database import ThreadSafeDatabase

# ── App setup ───────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = "moodwave-secret"
io = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

engine = EmotionEngine()
player = MusicPlayer()
db = ThreadSafeDatabase()

# ────────────────────────────────────────────────────────────────────────
CAMERA_SOURCE = 0
JPEG_QUALITY = 75
DETECT_EVERY_N = 15

# ── Shared state ─────────────────────────────────────────────────────────
last_jpeg_bytes = None
jpeg_lock = threading.Lock()
_running = False

# ── Backend API connection ────────────────────────────────────────────────
BACKEND_URL = "http://localhost:8000"


# ── Placeholder frame ─────────────────────────────────────────────────
def _make_placeholder(message="Connecting to camera…"):
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(
        img,
        message,
        (60, 240),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (70, 70, 70),
        2,
    )
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


# ── Camera loop ───────────────────────────────────────────────────────
def camera_loop():
    """Capture frames and detect emotions."""
    global last_jpeg_bytes, _running

    backend = cv2.CAP_DSHOW if isinstance(CAMERA_SOURCE, int) else cv2.CAP_ANY
    cap = cv2.VideoCapture(CAMERA_SOURCE, backend)

    if not cap.isOpened():
        print(f"[Camera] ❌ Cannot open camera {CAMERA_SOURCE}")
        with jpeg_lock:
            last_jpeg_bytes = _make_placeholder("Camera not found")
        _running = False
        return

    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[Camera] ✅ Opened at {w}×{h}")

    frame_n = 0
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
    last_emotion = "neutral"

    try:
        while _running:
            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(0.05)
                continue

            frame_n += 1

            # Encode frame
            ret_enc, buf = cv2.imencode(".jpg", frame, encode_params)
            if ret_enc:
                with jpeg_lock:
                    last_jpeg_bytes = buf.tobytes()

            # Detect emotion every N frames
            if frame_n % DETECT_EVERY_N == 0:
                try:
                    mood = engine.detect(frame)
                    
                    if mood != last_emotion:
                        last_emotion = mood
                        print(f"[Emotion] {mood}")

                        # Try backend
                        try:
                            resp = requests.post(
                                f"{BACKEND_URL}/api/sessions/analyze",
                                json={"emotion": mood},
                                timeout=2.0,
                            )
                            if resp.status_code == 200:
                                result = resp.json()
                                track = result.get("track", "unknown")
                                progress = result.get("progress", 0)
                                player.play(track)
                                db.log_mood(mood, track, progress)
                                io.emit("mood_update", {
                                    "mood": mood,
                                    "track": track,
                                    "progress": round(progress * 100),
                                })
                        except:
                            # Fallback to local
                            track = engine.get_next_track(mood)
                            progress = engine.get_transition_progress()
                            player.play(track)
                            db.log_mood(mood, track, progress)
                            io.emit("mood_update", {
                                "mood": mood,
                                "track": track,
                                "progress": round(progress * 100),
                            })
                except Exception as e:
                    print(f"[AI] Error: {e}")

    finally:
        cap.release()
        print("[Camera] 🛑 Closed")


def generate_frames():
    """Generate MJPEG stream."""
    placeholder = _make_placeholder()
    while True:
        with jpeg_lock:
            data = last_jpeg_bytes or placeholder
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + data + b"\r\n"
        )
        time.sleep(0.01)


# ── Routes ──────────────────────────────────���────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/history")
def history():
    return jsonify({"weekly": db.get_weekly_summary()})


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# ── SocketIO ───────────────────────────────────────────────────────
@io.on("connect")
def on_connect():
    global _running
    if not _running:
        _running = True
        threading.Thread(target=camera_loop, daemon=True).start()
        print("[SocketIO] 🔌 Connected")


@io.on("disconnect")
def on_disconnect():
    print("[SocketIO] 🔌 Disconnected")


# ── Entry point ───────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  🌊 MoodWave Desktop")
    print(f"  Camera: {CAMERA_SOURCE}")
    print(f"  Browser: http://localhost:5000")
    print(f"  Backend: {BACKEND_URL}")
    print("=" * 60)
    try:
        io.run(app, host="0.0.0.0", port=5000, debug=False)
    finally:
        _running = False
        player.stop()