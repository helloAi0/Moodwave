"""
app.py — MoodWave Desktop Frontend (Iriun / any webcam — lag-free MJPEG)

Run:   python app.py
Open:  http://localhost:5000

Key features:
  1. CAMERA_SOURCE is an integer index (Iriun virtual webcam driver)
  2. JPEG encoding happens ONCE in camera_loop -> stored as last_jpeg_bytes
  3. generate_frames() just yields pre-encoded bytes (zero re-encoding)
  4. cv2.CAP_DSHOW backend on Windows = much faster frame delivery
  5. cap.set(BUFFERSIZE, 1) = always get the freshest frame
"""

import threading
import time
import cv2
import numpy as np
import requests
from flask import Flask, render_template, Response
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
# CAMERA SOURCE — edit this one value:
#   Iriun (virtual webcam):  integer, e.g. 0, 1, or 2
#   Regular USB webcam:      0
#
# Run  python find_camera.py  to discover which index Iriun is on your PC.
# ────────────────────────────────────────────────────────────────────────
CAMERA_SOURCE = 0  # <-- change this after running find_camera.py
JPEG_QUALITY = 75  # lower = faster stream, higher = sharper image
DETECT_EVERY_N = 15  # run emotion detection every N frames

# ── Shared state (Producer -> Consumers) ─────────────────────────────────
last_jpeg_bytes = None  # pre-encoded JPEG bytes — ready to stream instantly
jpeg_lock = threading.Lock()
_running = False

# ── Backend API connection ────────────────────────────────────────────────
BACKEND_URL = "http://localhost:8000"  # Change if backend is on different host


# ── Placeholder frame (shown before camera connects) ─────────────────────
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


# ── Producer thread ─────────────────────────────────────────────────────
def camera_loop():
    """
    Single thread that:
      - Opens the camera ONCE (avoids dual-client errors)
      - Encodes every frame to JPEG once -> last_jpeg_bytes
      - Every DETECT_EVERY_N frames: detects emotion + sends to backend
    """
    global last_jpeg_bytes, _running

    # Use DirectShow on Windows for lowest latency
    backend = cv2.CAP_DSHOW if isinstance(CAMERA_SOURCE, int) else cv2.CAP_ANY
    cap = cv2.VideoCapture(CAMERA_SOURCE, backend)

    if not cap.isOpened():
        print(f"[Camera] ❌ ERROR: Cannot open source '{CAMERA_SOURCE}'")
        print("[Camera] Tip: run  python find_camera.py  to find the right index.")
        with jpeg_lock:
            last_jpeg_bytes = _make_placeholder("Camera not found. Check index.")
        _running = False
        return

    # Minimise internal buffer so we always get the LATEST frame
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    # ⚠️ IMPORTANT: Don't set resolution — let camera auto-detect
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[Camera] ✅ Opened source {CAMERA_SOURCE} at {w}×{h}")
    print(f"[Camera] Detecting emotion every {DETECT_EVERY_N} frames")

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

            # ── Encode ONCE, store for the MJPEG consumer ─────────────────────
            ret_enc, buf = cv2.imencode(".jpg", frame, encode_params)
            if ret_enc:
                with jpeg_lock:
                    last_jpeg_bytes = buf.tobytes()

            # ── AI detection every N frames ───────────────────────────────────
            if frame_n % DETECT_EVERY_N == 0:
                try:
                    # Detect emotion locally
                    mood = engine.detect(frame)
                    
                    if mood != last_emotion:
                        last_emotion = mood
                        print(f"[Emotion] Detected: {mood}")

                        # Send to backend for Iso engine processing
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

                                # Play music locally
                                player.play(track)

                                # Log to local DB (thread-safe)
                                db.log_mood(mood, track, progress)

                                # Emit to UI via SocketIO
                                io.emit(
                                    "mood_update",
                                    {
                                        "mood": mood,
                                        "track": track,
                                        "progress": round(progress * 100),
                                    },
                                )
                                print(f"[Backend] ✅ Sent emotion & received: {track}")
                            else:
                                print(f"[Backend] ⚠ Error: {resp.status_code}")
                        except requests.exceptions.RequestException as e:
                            print(f"[Backend] ⚠ Unreachable: {e}")
                            # Fall back to local engine
                            track = engine.get_next_track(mood)
                            progress = engine.get_transition_progress()
                            player.play(track)
                            db.log_mood(mood, track, progress)
                            io.emit(
                                "mood_update",
                                {
                                    "mood": mood,
                                    "track": track,
                                    "progress": round(progress * 100),
                                },
                            )

                except Exception as exc:
                    print(f"[AI] ⚠ Error: {exc}")

    finally:
        cap.release()
        print("[Camera] 🛑 Stream closed.")


# ── MJPEG consumer — just hands out pre-built bytes ───────────────────────
def generate_frames():
    """
    Yields pre-encoded JPEG bytes as an MJPEG stream.
    No encoding work here — camera_loop already did it.
    """
    placeholder = _make_placeholder()

    while True:
        with jpeg_lock:
            data = last_jpeg_bytes or placeholder

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + data + b"\r\n"
        )

        # Yield to other threads briefly; browser will pull at its own pace
        time.sleep(0.01)


# ── Routes ───────────────────────────────────────────────────────────
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
    return {"weekly": db.get_weekly_summary()}


# ── SocketIO ───────────────────────────────────────────────────────────
@io.on("connect")
def on_connect():
    global _running
    if not _running:
        _running = True
        threading.Thread(target=camera_loop, daemon=True).start()
        print("[SocketIO] 🔌 Client connected — camera loop started.")


@io.on("disconnect")
def on_disconnect():
    print("[SocketIO] 🔌 Client disconnected.")


# ── Entry point ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 52)
    print("  MoodWave Desktop")
    print(
        f"  Camera source : {CAMERA_SOURCE}  (edit CAMERA_SOURCE in app.py)"
    )
    print("  Open browser  : http://localhost:5000")
    print("  Find cam index: python find_camera.py")
    print(f"  Backend URL   : {BACKEND_URL}")
    print("=" * 52)
    try:
        io.run(app, host="0.0.0.0", port=5000, debug=False)
    finally:
        _running = False
        player.stop()