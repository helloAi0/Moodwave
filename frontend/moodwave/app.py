"""
app.py  —  MoodWave Desktop (Iriun / any webcam — lag-free MJPEG)
Run:   python app.py
Open:  http://localhost:5000

Fix summary vs previous version:
  1. CAMERA_SOURCE is now an integer index (Iriun virtual webcam driver)
     — change to a URL string if you ever go back to DroidCam HTTP stream
  2. JPEG encoding happens ONCE in camera_loop -> stored as last_jpeg_bytes
     generate_frames() just hands those bytes to Flask, zero re-encoding
  3. Removed time.sleep() from generate_frames() — let the OS scheduler breathe
  4. cv2.CAP_DSHOW backend on Windows = much faster frame delivery
  5. cap.set(BUFFERSIZE, 1) = always get the freshest frame, no queue buildup
"""

import threading
import time
import cv2
import numpy as np
from flask import Flask, render_template, Response
from flask_socketio import SocketIO

from emotion_engine import EmotionEngine
from music_player   import MusicPlayer
from database       import init_db, log_mood, get_weekly_summary

# ── App setup ────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY'] = 'moodwave-secret'
io  = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

engine = EmotionEngine()
player = MusicPlayer()
db     = init_db()

# ─────────────────────────────────────────────────────────────────────────────
# CAMERA SOURCE — edit this one value:
#   Iriun (virtual webcam):  integer, e.g. 0, 1, or 2
#   DroidCam (HTTP stream):  string,  e.g. "http://192.168.1.x:4747/video"
#   Regular USB webcam:      0
#
# Run  python find_camera.py  to discover which index Iriun is on your PC.
# ─────────────────────────────────────────────────────────────────────────────
CAMERA_SOURCE  = 0          # <-- change this after running find_camera.py
JPEG_QUALITY   = 75         # lower = faster stream, higher = sharper image
DETECT_EVERY_N = 10         # run DeepFace every N frames

# ── Shared state (Producer -> Consumers) ─────────────────────────────────────
last_jpeg_bytes = None      # pre-encoded JPEG bytes — ready to stream instantly
jpeg_lock       = threading.Lock()
_running        = False


# ── Placeholder frame (shown before camera connects) ─────────────────────────
def _make_placeholder(message="Connecting to camera…"):
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(img, message, (60, 240),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (70, 70, 70), 2)
    _, buf = cv2.imencode('.jpg', img)
    return buf.tobytes()


# ── Producer thread ───────────────────────────────────────────────────────────
def camera_loop():
    """
    Single thread that:
      - Opens the camera ONCE (avoids dual-client errors)
      - Encodes every frame to JPEG once -> last_jpeg_bytes
      - Every DETECT_EVERY_N frames: runs DeepFace + emits SocketIO event
    """
    global last_jpeg_bytes, _running

    # Use DirectShow on Windows for lowest latency
    backend = cv2.CAP_DSHOW if isinstance(CAMERA_SOURCE, int) else cv2.CAP_ANY
    cap = cv2.VideoCapture(CAMERA_SOURCE, backend)

    if not cap.isOpened():
        print(f"[Camera] ERROR: Cannot open source '{CAMERA_SOURCE}'")
        print("[Camera] Tip: run  python find_camera.py  to find the right index.")
        with jpeg_lock:
            last_jpeg_bytes = _make_placeholder("Camera not found. Check index.")
        _running = False
        return

    # Minimise internal buffer so we always get the LATEST frame
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    # Request 720p — Iriun supports it; falls back gracefully if not
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[Camera] Opened '{CAMERA_SOURCE}' at {w}x{h}")

    frame_n    = 0
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]

    while _running:
        ret, frame = cap.read()
        if not ret or frame is None:
            time.sleep(0.05)
            continue

        frame_n += 1

        # ── Encode ONCE, store for the MJPEG consumer ─────────────────────
        ret_enc, buf = cv2.imencode('.jpg', frame, encode_params)
        if ret_enc:
            with jpeg_lock:
                last_jpeg_bytes = buf.tobytes()

        # ── AI detection every N frames ───────────────────────────────────
        if frame_n % DETECT_EVERY_N == 0:
            mood     = engine.detect(frame)
            track    = engine.get_next_track(mood)
            progress = engine.get_transition_progress()

            player.play(track)
            log_mood(db, mood, track, progress)

            io.emit('mood_update', {
                'mood':     mood,
                'track':    track,
                'progress': round(progress * 100),
            })

    cap.release()
    print("[Camera] Stream closed.")


# ── MJPEG consumer — just hands out pre-built bytes ───────────────────────────
def generate_frames():
    """
    Yields pre-encoded JPEG bytes as an MJPEG stream.
    No encoding work here — camera_loop already did it.
    """
    placeholder = _make_placeholder()

    while True:
        with jpeg_lock:
            data = last_jpeg_bytes or placeholder

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               data +
               b'\r\n')

        # Yield to other threads briefly; browser will pull at its own pace
        time.sleep(0.01)


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/history')
def history():
    return {'weekly': get_weekly_summary(db)}


# ── SocketIO ──────────────────────────────────────────────────────────────────
@io.on('connect')
def on_connect():
    global _running
    if not _running:
        _running = True
        threading.Thread(target=camera_loop, daemon=True).start()
        print("[SocketIO] Client connected — camera loop started.")

@io.on('disconnect')
def on_disconnect():
    print("[SocketIO] Client disconnected.")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 52)
    print("  MoodWave Desktop")
    print(f"  Camera source : {CAMERA_SOURCE}  (edit CAMERA_SOURCE in app.py)")
    print("  Open browser  : http://localhost:5000")
    print("  Find cam index: python find_camera.py")
    print("=" * 52)
    try:
        io.run(app, host='0.0.0.0', port=5000, debug=False)
    finally:
        _running = False
        player.stop()
        if db:
            db.close()